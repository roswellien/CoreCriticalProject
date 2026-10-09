"""Independent full-frame oracle for the authored Vulkan raster experiment."""
import argparse
import hashlib
import json
from pathlib import Path


def verify(path, mode):
    data = path.read_bytes()
    header = b"P6\n256 256\n255\n"
    if not data.startswith(header) or len(data) != len(header) + 256 * 256 * 3:
        raise ValueError("Invalid PPM header or exact payload length")
    pixels = data[len(header):]
    maximum = 0
    for y in range(256):
        for x in range(256):
            quadrant = (y >= 128) * 2 + (x >= 128)
            texture = ((1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 1))[quadrant]
            alpha = 1.0 if mode == "opaque-front" else 0.5
            fog = 0.0 if mode == "fog-off" else 0.5
            destination = (0, 0, 0) if mode == "depth-off" else texture
            expected = [round(255 * (alpha * ((1 - fog) * t + fog * 0.25) + (1 - alpha) * d))
                        for t, d in zip(texture, destination)]
            offset = (y * 256 + x) * 3
            errors = [abs(a - b) for a, b in zip(pixels[offset:offset + 3], expected)]
            maximum = max(maximum, *errors)
            if max(errors) > 1:
                raise ValueError(f"Pixel ({x},{y}) mismatch: {list(pixels[offset:offset+3])}, expected {expected}")
    return {"mode": mode, "pixels_verified": 65536, "max_channel_error": maximum,
            "channel_tolerance": 1, "sha256": hashlib.sha256(data).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ppm", type=Path)
    parser.add_argument("--mode", choices=("default", "depth-off", "fog-off", "opaque-front"), default="default")
    args = parser.parse_args()
    print(json.dumps(verify(args.ppm, args.mode), indent=2))


if __name__ == "__main__":
    main()
