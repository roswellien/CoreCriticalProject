"""Authored color-lane, initial-target and alpha-blend checks; no game assets."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
from PIL import Image


def quantize(rgb, mode):
    if mode == 'rgba8':
        return rgb
    return tuple(((value * levels + 127) // 255 * 255 + levels // 2) // levels
                 for value, levels in zip(rgb, (31, 63, 31)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('shaders', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[2]
    environment = os.environ.copy()
    environment['VK_LAYER_PATH'] = str(root / 'local/tools/vulkan-sdk-portable/Bin')
    environment['VK_IMPLICIT_LAYER_PATH'] = str(root / 'local/tools/empty-implicit-layers')
    cases = [('red', (255, 0, 0), 255), ('green', (0, 255, 0), 255),
             ('blue', (0, 0, 255), 255), ('blend-red', (255, 0, 0), 128)]
    results = []
    for mode in ('rgba8', 'rgb565'):
        for name, rgb, alpha in cases:
            # Left half is drawn; the right half must retain initial blue.
            diffuse = (alpha << 24) | (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]
            coordinates = [(-.5, -.5), (3.5, -.5), (3.5, 7.5),
                           (-.5, -.5), (3.5, 7.5), (-.5, 7.5)]
            vertices = b''.join(struct.pack('<4fII2f', x, y, .5, 1, diffuse, 0, .5, .5)
                                for x, y in coordinates)
            scene = (b'MW34SCN2' + struct.pack('<4I', 8, 8, 1, 1)
                     + bytes((0, 0, 255, 255)) * 64 + struct.pack('<64f', *([0] * 64))
                     + struct.pack('<2I', 1, 1) + bytes((255, 255, 255, 255))
                     + struct.pack('<10I', 0, 6, 2, 1, 0, int(alpha != 255), 3, 3, 0, 0)
                     + vertices)
            package = args.output / f'{mode}-{name}.replay'
            package.write_bytes(scene)
            candidate = args.output / f'{mode}-{name}.ppm'
            process = subprocess.run([str(args.executable.resolve()), str(package.resolve()),
                                      str(args.shaders.resolve()), str(candidate.resolve()),
                                      '0.5', 'captured', '1', 'd32', mode], env=environment,
                                     capture_output=True, text=True, timeout=30)
            (args.output / f'{mode}-{name}-run.txt').write_text(process.stdout + process.stderr)
            if process.returncode or 'zero validation warnings/errors' not in process.stdout:
                raise ValueError(f'Render/validation failed: {mode}-{name}')
            pixels = Image.open(candidate).convert('RGB')
            blended = tuple((rgb[c] * alpha + (255 if c == 2 else 0) * (255 - alpha) + 127) // 255
                            for c in range(3))
            foreground, background = quantize(blended, mode), (0, 0, 255)
            maximum = 0
            for y in range(8):
                for x in range(8):
                    expected = foreground if x < 4 else background
                    maximum = max(maximum, max(abs(a - b) for a, b in zip(pixels.getpixel((x, y)), expected)))
            if maximum > 1:
                raise ValueError(f'Authored pixel check failed: {mode}-{name}: {maximum}')
            results.append({'mode': mode, 'case': name, 'pixels_checked': 64,
                            'maximum_channel_error': maximum})
    report = {'scope': 'Authored target color and blend verification; no live game equivalence claim',
              'executable_sha256': hashlib.sha256(args.executable.read_bytes()).hexdigest(),
              'verifier_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'shader_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in sorted(args.shaders.glob('replay*.spv'))}, 'cases': results}
    (args.output / 'verification.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
