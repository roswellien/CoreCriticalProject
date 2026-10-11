"""Exercise SCN4 clear/copy commands through the window and CPU pixel oracle."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    args.output.mkdir(parents=True, exist_ok=False)
    oracle = module('command_oracle', root / 'tools/vulkan-probe/verify_ordered_commands.py')
    pixels = module('presentation_oracle', Path(__file__).with_name('verify.py'))
    ops = [oracle.command(1, 0), oracle.command(3, 1, 1, 1, 3, 3, 2, 2),
           oracle.command(2, 3, 4, 4, 1, 1, 0xffffff00, oracle.depth_bits(0)),
           oracle.command(1, 1)]
    scene = args.output / 'scene.replay'
    scene.write_bytes(oracle.package(ops))
    output = args.output / 'replay.ppm'
    executable = args.build / 'Release/mw34_vulkan_windowed.exe'
    env = os.environ.copy()
    env['VK_LAYER_PATH'] = str(root / 'local/tools/vulkan-sdk-portable/Bin')
    env['VK_IMPLICIT_LAYER_PATH'] = str(root / 'local/tools/empty-implicit-layers')
    completed = subprocess.run([str(executable.resolve()), str(scene.resolve()),
                               str(args.build.resolve()), str(output.resolve()), '6', 'self-test'],
                              env=env, capture_output=True, text=True, timeout=30)
    log = completed.stdout + completed.stderr
    (args.output / 'run.txt').write_text(log)
    if completed.returncode or 'VALIDATION:' in log:
        raise ValueError('Windowed replay or Vulkan validation failed')
    result = [json.loads(line.removeprefix('WINDOWED_RESULT: ')) for line in log.splitlines()
              if line.startswith('WINDOWED_RESULT: ')]
    if len(result) != 1 or result[0]['validation_messages'] != 0:
        raise ValueError('Missing clean runtime receipt')
    source = (8, 8, oracle.oracle(ops, 1))
    if pixels.ppm(output) != source:
        raise ValueError('Ordered command raster differs from CPU oracle')
    witnesses = sorted(args.output.glob('replay.ppm.presented-*.ppm'))
    if len(witnesses) < 4:
        raise ValueError('Missing resize/minimize/restore witnesses')
    checked = [dict(file=str(path.resolve()), **pixels.check_pixels(source, pixels.ppm(path)))
               for path in witnesses]
    inputs = [executable, scene, Path(__file__), root / 'tools/vulkan-probe/ordered_commands.inc',
              root / 'tools/vulkan-probe/replay_scene.hpp', root / 'tools/vulkan-probe/verify_ordered_commands.py',
              Path(__file__).with_name('viewer.cpp'), Path(__file__).with_name('presenter.hpp'),
              Path(__file__).with_name('verify.py'), *args.build.glob('*.spv')]
    report = {'scope': 'Authored ordered clears/copies in window; no live MW3 equivalence',
              'result': result[0], 'raster_exact_pixels': 64, 'witnesses': checked,
              'files': {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}}
    (args.output / 'verification.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({'passed': True, 'witnesses': len(checked), 'result': result[0]}, indent=2))


if __name__ == '__main__':
    main()
