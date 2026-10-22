"""Replay observed flip-interval draws; never grants complete-frame acceptance."""
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys

from PIL import Image
from describe_capture import decode_rgb
from compare_replay import compare
from verify_capture import verify_presentation_diagnostic


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--draws-only', action='store_true', help='Same-capture diagnostic baseline omitting surface commands')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[2]
    receipt = verify_presentation_diagnostic(args.capture)
    scene = args.output / 'scene.replay'
    packaging = subprocess.run([sys.executable, str(Path(__file__).with_name('package_replay.py')),
                               str(args.capture), str(scene), '--filter-source', 'legacy',
                               '--diagnostic-presentation', *(['--draws-only'] if args.draws_only else [])], capture_output=True, text=True)
    (args.output / 'package.log').write_text(packaging.stdout + packaging.stderr)
    if packaging.returncode: raise ValueError('Diagnostic packaging rejected')
    rows = [json.loads(line) for line in (args.capture / 'capture.jsonl').read_text().splitlines()]
    for role in ('initial_target', 'final_target'):
        info = next(row['surface'] for row in rows if row['event'] == role)
        rgba = decode_rgb(info, (args.capture / info['file']).read_bytes())
        Image.frombytes('RGBA', (info['width'], info['height']), rgba).save(args.output / (role + '.png'))
    executable = root / 'build/vulkan-replay/Release/mw34_vulkan_replay.exe'
    shaders = root / 'build/vulkan-replay'
    env = os.environ.copy()
    env['VK_LAYER_PATH'] = str(root / 'local/tools/vulkan-sdk-portable/Bin')
    env['VK_IMPLICIT_LAYER_PATH'] = str(root / 'local/tools/empty-implicit-layers')
    candidate = args.output / 'vulkan.ppm'
    command = [str(executable), str(scene.resolve()), str(shaders), str(candidate.resolve()),
               '0.5', 'captured', '1', 'd32', 'rgba8']
    result = subprocess.run(command, capture_output=True, text=True, env=env, timeout=60)
    log = result.stdout + result.stderr
    (args.output / 'replay.log').write_text(log)
    if result.returncode or 'zero validation warnings/errors' not in log:
        raise ValueError('GPU replay or validation failed')
    comparison = compare(args.output / 'final_target.png', candidate, args.output / 'difference.png',
                         False, None, args.output / 'initial_target.png')
    Image.open(candidate).save(args.output / 'vulkan.png')
    sources = [Path(__file__), Path(__file__).with_name('package_replay.py'),
              Path(__file__).with_name('verify_capture.py'), Path(__file__).with_name('describe_capture.py'),
              Path(__file__).with_name('compare_replay.py')]
    source_directory = args.output / 'sources'
    source_directory.mkdir()
    for source in sources:
        shutil.copyfile(source, source_directory / source.name)
    inputs = [*(source_directory / source.name for source in sources), executable, scene, candidate,
              args.output / 'initial_target.png', args.output / 'final_target.png', args.output / 'vulkan.png',
              args.capture / 'capture.jsonl', *args.capture.glob('*.bin'), *shaders.glob('*.spv')]
    report = {'scope': 'Diagnostic image comparison; no full-frame acceptance',
              'omitted_observed_surface_commands': args.draws_only,
              'command_coverage_complete': False, 'capture': receipt, 'command': command,
              'comparison': comparison,
              'files': {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs}}
    (args.output / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(comparison, indent=2))


if __name__ == '__main__':
    main()
