"""Authored overlapping geometry verifies depth tests independently of depth writes."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
from PIL import Image


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
    reports = []
    for depth_mode in ('d32', 'd16'):
        for write in (0, 1):
            scene = bytearray(b'MW34SCN3' + struct.pack('<4I', 8, 8, 1, 2)
                              + bytes((0, 0, 0, 255))*64 + struct.pack('<64f', *([0]*64))
                              + struct.pack('<2I', 1, 1) + bytes((255, 255, 255, 255)))
            for depth, color, depth_write in ((.75, 0xffff0000, write), (.5, 0xff0000ff, 1)):
                scene += struct.pack('<11I', 0, 6, 2, 1, 0, 0, 3, 3, 0, 0, depth_write)
                for x, y in ((-.5,-.5),(7.5,-.5),(7.5,7.5),(-.5,-.5),(7.5,7.5),(-.5,7.5)):
                    scene += struct.pack('<4fII2f', x, y, depth, 1, color, 0, .5, .5)
            name = f'{depth_mode}-write-{write}'
            package, output = args.output / f'{name}.replay', args.output / f'{name}.ppm'
            package.write_bytes(scene)
            process = subprocess.run([str(args.executable.resolve()), str(package.resolve()),
                                      str(args.shaders.resolve()), str(output.resolve()), '0.5',
                                      'captured', '1', depth_mode], env=environment,
                                     capture_output=True, text=True, timeout=30)
            (args.output / f'{name}-run.txt').write_text(process.stdout + process.stderr)
            if process.returncode or 'zero validation warnings/errors' not in process.stdout:
                raise ValueError(f'Depth fixture render failed: {name}')
            expected = bytes((255,0,0) if write else (0,0,255))*64
            if Image.open(output).convert('RGB').tobytes() != expected:
                raise ValueError(f'Depth-write behavior incorrect: {name}')
            reports.append({'depth_format': depth_mode, 'first_draw_depth_write': write,
                            'expected_color': 'red' if write else 'blue', 'exact_pixels': 64})
    report = {'scope': 'Authored independent depth-write/depth-test fixtures; no game equivalence claim', 'cases': reports}
    (args.output / 'verification.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
