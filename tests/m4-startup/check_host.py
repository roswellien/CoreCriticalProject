"""Asset-free public CLI/admission checks for the native M4 image host."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(host, out):
    if out.exists():
        raise ValueError('Refusing to overwrite M4 host control evidence')
    if not host.is_file():
        raise ValueError('Missing required native host; checks may not be skipped')
    out.mkdir(parents=True)
    small = out/'small-input.bin'
    small.write_bytes(b'MZ')
    same_size = out/'unsupported-same-size.bin'
    same_size.write_bytes(bytes(2384384))
    controls = [
        ('no_arguments', [], 64, 'expected exactly'),
        ('unknown_option', ['--run-game', str(small)], 64, 'expected exactly'),
        ('missing_argument', ['--image'], 64, 'expected exactly'),
        ('extra_argument', ['--inspect-image', str(small), 'extra'], 64, 'expected exactly'),
        ('duplicate_modes', ['--image', '--inspect-image', str(small)], 64, 'expected exactly'),
        ('missing_file', ['--inspect-image', str(out/'absent.exe')], 1, 'Missing M4 image input'),
        ('wrong_size', ['--inspect-image', str(small)], 1, 'Wrong M4 image size'),
        ('wrong_identity_inspect', ['--inspect-image', str(same_size)], 1, 'Wrong M4 image identity'),
        ('wrong_identity_startup', ['--image', str(same_size)], 1, 'Wrong M4 image identity'),
    ]
    records = []
    for name, args, expected_exit, reason in controls:
        run = subprocess.run([str(host), *args], capture_output=True, timeout=30)
        (out/(name+'.stdout')).write_bytes(run.stdout)
        (out/(name+'.stderr')).write_bytes(run.stderr)
        passed = run.returncode == expected_exit and not run.stdout and reason.encode() in run.stderr
        records.append({'name': name, 'passed': passed, 'exit_code': run.returncode,
                        'expected_diagnostic': reason, 'stdout_sha256': sha(run.stdout),
                        'stderr_sha256': sha(run.stderr)})
        if not passed:
            raise ValueError('M4 public host rejection failed: '+name)
    selfcheck = subprocess.run([str(host), '--check-admission'], capture_output=True, timeout=30)
    (out/'selfcheck.stdout').write_bytes(selfcheck.stdout)
    (out/'selfcheck.stderr').write_bytes(selfcheck.stderr)
    data = json.loads(selfcheck.stdout)
    if selfcheck.returncode or selfcheck.stderr or data != {
            'passed': True, 'admission_controls': 5, 'native_pointer_bits': 64,
            'original_x86_executed': False}:
        raise ValueError('M4 native SHA/admission controls differ')
    help_run = subprocess.run([str(host), '--help'], capture_output=True, timeout=30)
    (out/'help.stdout').write_bytes(help_run.stdout)
    (out/'help.stderr').write_bytes(help_run.stderr)
    if help_run.returncode or help_run.stderr or b'Usage:' not in help_run.stdout:
        raise ValueError('M4 public usage failed')
    report = {'schema_version': 1, 'passed': True, 'host_path': str(host),
              'host_sha256': sha(host.read_bytes()), 'script_sha256': sha(Path(__file__).read_bytes()),
              'public_rejections': records, 'public_rejection_count': len(records),
              'native_admission_controls': 5, 'help_control': True,
              'game_input_used': False, 'original_x86_executed': False,
              'files': {str(p.resolve()): sha(p.read_bytes()) for p in out.iterdir() if p.is_file()}}
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check(args.host.resolve(), args.out.resolve())
        print(json.dumps({'passed': result['passed'], 'public_rejections': result['public_rejection_count'],
                          'native_admission_controls': result['native_admission_controls']}))
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        raise SystemExit('M4 public host checks rejected: '+str(error))
