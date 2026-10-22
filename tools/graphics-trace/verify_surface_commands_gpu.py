"""Exercise observer-produced depth/CPU-write commands through actual Vulkan."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
from PIL import Image
from describe_capture import decode_rgb
from verify_capture import cpu_write_regions, depth_fill_command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixture', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    depth_path = args.fixture / 'depth-command/depth-command-fixture.jsonl'
    cpu_path = args.fixture / 'cpu-command/cpu-command-fixture.jsonl'
    depth_row = json.loads(depth_path.read_text().strip())
    cpu_row = json.loads(cpu_path.read_text().strip())
    effects = args.fixture / 'depth-command' / depth_row['effects']
    before_path, after_path = [args.fixture / 'cpu-command' / cpu_row[key] for key in ('before', 'after')]
    before, after = before_path.read_bytes(), after_path.read_bytes()
    clear = depth_fill_command(depth_row, 2, 2, effects.read_bytes())
    regions = cpu_write_regions(cpu_row, 2, 2, before, after)
    if clear != (2, 2, 0, 0, 2, 2, 0, 0, 0, 0) or regions != [(1, 0, 1, 1)] or after != bytes.fromhex('0000e00700000000'):
        raise ValueError('Unexpected authored fixture domain')
    info = {'flags': 64, 'bits': 16, 'r_mask': 0xf800, 'g_mask': 0x7e0, 'b_mask': 0x1f, 'a_mask': 0}
    blob = bytearray(b'MW34SCN4' + struct.pack('<4I', 2, 2, 2, 2))
    blob += bytes((0, 0, 255, 255))*4 + struct.pack('<4f', *([1]*4))
    blob += struct.pack('<2I', 1, 1) + bytes((255, 255, 255, 255))
    blob += struct.pack('<2I', 2, 2) + decode_rgb(info, after)
    for z, color in ((.75, 0xffff0000), (.5, 0xff0000ff)):
        blob += struct.pack('<11I', 0, 6, 2, 1, 0, 0, 3, 3, 0, 0, 1)
        for x, y in ((-.5, -.5), (1.5, -.5), (1.5, 1.5), (-.5, -.5), (1.5, 1.5), (-.5, 1.5)):
            blob += struct.pack('<4fII2f', x, y, z, 1, color, 0, .5, .5)
    commands = [clear, (1, 0, 0, 0, 0, 0, 0, 0, 0, 0)]
    commands += [(3, 1, x, y, x, y, w, h, 0, 0) for x, y, w, h in regions]
    commands += [(1, 1, 0, 0, 0, 0, 0, 0, 0, 0)]
    blob += struct.pack('<I', len(commands))
    for command in commands:
        blob += struct.pack('<10I', *command)
    scene = args.output / 'observer-commands.replay'
    scene.write_bytes(blob)
    root = Path(__file__).resolve().parents[2]
    executable = root / 'build/vulkan-replay/Release/mw34_vulkan_replay.exe'
    shaders = root / 'build/vulkan-replay'
    env = os.environ.copy()
    env['VK_LAYER_PATH'] = str(root / 'local/tools/vulkan-sdk-portable/Bin')
    env['VK_IMPLICIT_LAYER_PATH'] = str(root / 'local/tools/empty-implicit-layers')
    cases = []
    for depth in ('d16', 'd32'):
        for scale in (1, 3):
            name = f'{depth}-{scale}'
            image = args.output / (name + '.ppm')
            result = subprocess.run([str(executable), str(scene.resolve()), str(shaders), str(image.resolve()),
                                     '0.5', 'captured', str(scale), depth, 'rgba8'], env=env, capture_output=True, text=True, timeout=30)
            (args.output / (name + '.log')).write_text(result.stdout + result.stderr)
            if result.returncode or 'zero validation warnings/errors' not in result.stdout:
                raise ValueError('GPU replay/validation failed')
            # The depth clear allows the red draw. The one changed CPU pixel is
            # green; unchanged black snapshot pixels must leave red intact.
            # The lower-Z blue draw must stay rejected after the surface copy.
            expected = bytes(channel for y in range(2*scale) for x in range(2*scale)
                             for channel in ((0, 255, 0) if x//scale == 1 and y//scale == 0 else (255, 0, 0)))
            if Image.open(image).convert('RGB').tobytes() != expected:
                raise ValueError('Depth/copy ordering or unchanged-pixel preservation failed')
            cases.append({'case': name, 'exact_pixels': 4*scale*scale})
    inputs = [Path(__file__), Path(__file__).with_name('verify_capture.py'), Path(__file__).with_name('describe_capture.py'),
              depth_path, cpu_path, effects, before_path, after_path, executable, scene, *shaders.glob('*.spv')]
    report = {'scope': 'Observer-produced authored depth/CPU-write commands on Vulkan; no live-frame equivalence',
              'cases': cases, 'exact_pixels': sum(case['exact_pixels'] for case in cases),
              'files': {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}}
    (args.output / 'verification.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({'cases': cases, 'exact_pixels': report['exact_pixels']}, indent=2))


if __name__ == '__main__':
    main()
