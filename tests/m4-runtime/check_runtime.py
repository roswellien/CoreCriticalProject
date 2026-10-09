"""Observe actual admitted-image metadata and intended unresolved-path denials."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def bind(path):
    return {'path': str(path.resolve()), 'size_bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(exist_ok=False)
    host, image = args.host.resolve(), args.image.resolve()
    records = []

    def run(name, arguments, expected_exit, diagnostic=None):
        command = [str(host), *map(str, arguments)]
        process = subprocess.run(command, capture_output=True, timeout=30)
        stdout, stderr = out / (name + '.stdout'), out / (name + '.stderr')
        stdout.write_bytes(process.stdout); stderr.write_bytes(process.stderr)
        if process.returncode != expected_exit:
            raise ValueError('Actual runtime control wrong exit: ' + name)
        if diagnostic is not None and (process.stdout or diagnostic not in process.stderr.decode()):
            raise ValueError('Actual runtime control missed intended diagnostic: ' + name)
        records.append({'name': name, 'command': command, 'exit_code': process.returncode,
                        'intended_diagnostic': diagnostic, 'stdout': bind(stdout), 'stderr': bind(stderr)})
        return process

    inspection = run('actual-inspection', ['--inspect', image], 0)
    if inspection.stderr:
        raise ValueError('Actual inspection produced unexpected diagnostics')
    observed = json.loads(inspection.stdout)
    expected = {'domain': 'admitted_game', 'image_sha256': '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf',
                'entry': 0x5ac3a0, 'imports': 474, 'initializer_slots': 145, 'nonzero_initializers': 144,
                'early_initializer_slots': 1, 'translations': 0, 'services': 0,
                'guest_esp': 0x20100000, 'guest_fs_base': 0x7ffde000, 'guest_exception_head': 0xffffffff,
                'guest_stack_base': 0x20100000, 'guest_stack_limit': 0x20000000,
                'guest_tib_self': 0x7ffde000, 'remill_state_bytes': 3504, 'remill_state_seeded': False,
                'guest_code_executed': False, 'CRT_SEH_MFC_startup_complete': False, 'native_menus_complete': False}
    if any(observed.get(key) != value for key, value in expected.items()):
        raise ValueError('Actual owned image/table/thread metadata differs')
    run('required-startup', ['--startup', image], 3,
        'unresolved_translation site=0x005ac3a0 target=0x005ac3a0: Required guest function')
    run('required-initializer', ['--initializers', image], 3,
        'unresolved_translation site=0x005ac3a0 target=0x0040ffe0: Required guest function')
    run('missing-input', ['--inspect', out / 'missing.exe'], 1, 'Missing M4 image input')
    altered = out / 'changed-actual-image.exe'
    data = bytearray(image.read_bytes()); data[-1] ^= 1; altered.write_bytes(data)
    run('changed-image', ['--inspect', altered], 1, 'Wrong M4 image identity')
    run('bad-mode', ['--unexpected', image], 2, 'Usage: mw34_m4_runtime_host')
    report = {'schema_version': 1, 'passed': True, 'scope': 'Actual image/thread/table inspection and intended startup/initializer denials only',
              'host': bind(host), 'image': bind(image), 'modified_actual_image': bind(altered),
              'inspection': observed, 'controls': records,
              'original_x86_executed': False, 'game_native_translation_executed': False,
              'native_startup_or_menus_complete': False}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Actual runtime metadata/causal controls:', len(records))


if __name__ == '__main__':
    main()
