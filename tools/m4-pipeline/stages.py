"""Monotonic command timing, fresh logs and explicit artifact provenance."""
import hashlib
import json
import math
import ntpath
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
import paths
from paths import ROOT, publish_bytes, workspace_path


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def run_stage(argv, out_dir, timeout_seconds=60, required_outputs=(), cwd=None, inputs=()):
    if not isinstance(argv, (list, tuple)) or not argv or any(not isinstance(v, str) or '\x00' in v for v in argv):
        raise ValueError('A direct command argument vector is required')
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 600:
        raise ValueError('A bounded positive timeout is required')
    output = workspace_path(out_dir, reports=True)
    if output.exists():
        raise FileExistsError(output)
    work = ROOT if cwd is None or Path(cwd).absolute() == ROOT else workspace_path(cwd)
    if not work.is_dir():
        raise ValueError('A workspace working directory is required')
    tool = shutil.which(argv[0])
    if tool is None:
        raise FileNotFoundError(argv[0])
    tool = str(Path(tool).absolute())
    watched = {str(Path(p).absolute()): sha(p) for p in inputs}
    watched[tool] = sha(tool)
    for path in (__file__, paths.__file__, sys.executable):
        watched[str(Path(path).absolute())] = sha(path)
    required = [workspace_path(p, reports=True) for p in required_outputs]
    keys = [ntpath.normcase(ntpath.normpath(str(p))) for p in required]
    if len(set(keys)) != len(required) or any(p.exists() for p in required):
        raise ValueError('Required artifacts must be unique fresh output paths')
    output.mkdir(parents=True)
    command = [tool, *argv[1:]]
    start = time.perf_counter_ns()
    wall_started = time.time_ns()
    status = 'launch_failure'
    exit_code = None
    stdout = b''
    stderr = b''
    launch_error = None
    child = None
    try:
        child = subprocess.Popen(command, cwd=work, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=0x08000000 if os.name == 'nt' else 0)
        try:
            stdout, stderr = child.communicate(timeout=timeout_seconds)
            exit_code = child.returncode
            status = 'success' if exit_code == 0 else 'nonzero_exit'
        except subprocess.TimeoutExpired as error:
            child.kill()
            try:
                stdout, stderr = child.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                stdout, stderr = error.output or b'', error.stderr or b''
                child.stdout.close()
                child.stderr.close()
            exit_code = child.returncode
            status = 'timeout'
    except Exception as error:
        launch_error = repr(error)
        if child is not None and child.poll() is None:
            child.kill()
            child.wait(timeout=5)
    ended = time.perf_counter_ns()
    publish_bytes(output / 'stdout.bin', stdout)
    publish_bytes(output / 'stderr.bin', stderr)
    current = {}
    for path in watched:
        current[path] = sha(path) if Path(path).is_file() else None
    inputs_stable = watched == current
    artifacts = {}
    invalid = {}
    for path in required:
        try:
            workspace_path(path, reports=True)
            if path.is_file():
                artifacts[str(path)] = sha(path)
        except (ValueError, OSError) as error:
            invalid[str(path)] = repr(error)
    missing = [str(path) for path in required if str(path) not in artifacts]
    if status == 'success' and not inputs_stable:
        status = 'input_changed'
    if status == 'success' and invalid:
        status = 'invalid_output'
    if status == 'success' and missing:
        status = 'missing_output'
    value = dict(passed=status == 'success', format='mw34.stage.v1', status=status,
        argv=command, cwd=str(work), start_monotonic_ns=start, end_monotonic_ns=ended,
        elapsed_seconds=(ended - start) / 1e9, started_unix_ns=wall_started,
        timeout_seconds=timeout_seconds, exit_code=exit_code, launch_error=launch_error,
        input_sha256=watched, final_input_sha256=current, inputs_stable=inputs_stable,
        required_outputs=list(map(str, required)), missing_outputs=missing, invalid_outputs=invalid,
        artifact_sha256=artifacts,
        stdout_sha256=sha(output / 'stdout.bin'), stderr_sha256=sha(output / 'stderr.bin'),
        environment_dumped=False, command_shell_used=False,
        timeout_descendant_tree_termination_claimed=False,
        process_file_open_attestation=False,
        stage_source_path=str(Path(__file__).absolute()),
        stage_source_sha256=watched[str(Path(__file__).absolute())],
        python_path=str(Path(sys.executable).absolute()),
        python_sha256=watched[str(Path(sys.executable).absolute())])
    publish_bytes(output / 'stage.json', (json.dumps(value, indent=2) + '\n').encode('utf-8'))
    return value


def verify_stage(out_dir, expected_sha256):
    from manifests import digest, unique_object
    output = workspace_path(out_dir, reports=True)
    receipt = output / 'stage.json'
    if sha(receipt) != digest(expected_sha256):
        raise ValueError('External stage receipt hash mismatch')
    value = json.loads(receipt.read_text(encoding='utf-8'), object_pairs_hook=unique_object)
    keys = {'passed', 'format', 'status', 'argv', 'cwd', 'start_monotonic_ns', 'end_monotonic_ns',
        'elapsed_seconds', 'started_unix_ns', 'timeout_seconds', 'exit_code', 'launch_error',
        'input_sha256', 'final_input_sha256', 'inputs_stable', 'required_outputs', 'missing_outputs',
        'invalid_outputs', 'artifact_sha256', 'stdout_sha256', 'stderr_sha256',
        'environment_dumped', 'command_shell_used', 'timeout_descendant_tree_termination_claimed',
        'process_file_open_attestation', 'stage_source_path', 'stage_source_sha256', 'python_path', 'python_sha256'}
    statuses = {'success', 'nonzero_exit', 'timeout', 'input_changed', 'missing_output', 'invalid_output', 'launch_failure'}
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError('Unexpected stage receipt schema')
    if (value['format'] != 'mw34.stage.v1' or value['status'] not in statuses
            or type(value['passed']) is not bool or value['passed'] != (value['status'] == 'success')):
        raise ValueError('Invalid stage status')
    if any(type(value[k]) is not bool for k in ('inputs_stable', 'environment_dumped',
            'command_shell_used', 'timeout_descendant_tree_termination_claimed', 'process_file_open_attestation')):
        raise ValueError('Invalid stage Boolean metadata')
    if any(value[k] for k in ('environment_dumped', 'command_shell_used',
            'timeout_descendant_tree_termination_claimed', 'process_file_open_attestation')):
        raise ValueError('Unsupported stage provenance claim')
    if (not isinstance(value['argv'], list) or not value['argv']
            or any(not isinstance(v, str) or '\x00' in v for v in value['argv'])):
        raise ValueError('Invalid recorded command vector')
    if Path(value['cwd']).absolute() != ROOT:
        workspace_path(value['cwd'])
    for key in ('input_sha256', 'final_input_sha256', 'artifact_sha256', 'invalid_outputs'):
        if not isinstance(value[key], dict):
            raise ValueError('Invalid stage association mapping')
    before, after = value['input_sha256'], value['final_input_sha256']
    if not before or set(before) != set(after) or value['inputs_stable'] != (before == after):
        raise ValueError('Inconsistent stage input closure')
    for name in before:
        if not isinstance(name, str) or not Path(name).is_absolute():
            raise ValueError('Stage inputs must use absolute paths')
        digest(before[name])
        if after[name] is not None:
            digest(after[name])
        elif Path(name).exists():
            raise ValueError('Previously missing stage input exists')
    if value['argv'][0] not in before:
        raise ValueError('Executable missing from stage provenance')
    for path_key, digest_key in (('stage_source_path', 'stage_source_sha256'), ('python_path', 'python_sha256')):
        if not isinstance(value[path_key], str) or value[path_key] not in before or digest(value[digest_key]) != before[value[path_key]]:
            raise ValueError('Stage source/interpreter association mismatch')
    for key in ('required_outputs', 'missing_outputs'):
        if not isinstance(value[key], list) or any(not isinstance(p, str) for p in value[key]) or len(set(value[key])) != len(value[key]):
            raise ValueError('Invalid stage output list')
        normalized = [ntpath.normcase(ntpath.normpath(p)) for p in value[key]]
        if len(set(normalized)) != len(normalized):
            raise ValueError('Duplicate normalized stage output')
    required, artifacts = set(value['required_outputs']), set(value['artifact_sha256'])
    if artifacts - required or set(value['missing_outputs']) != required - artifacts or set(value['invalid_outputs']) - set(value['missing_outputs']):
        raise ValueError('Inconsistent stage output closure')
    for name in required:
        workspace_path(name, reports=True)
    if any(not isinstance(reason, str) for reason in value['invalid_outputs'].values()):
        raise ValueError('Invalid stage output diagnostics')
    start, end = value['start_monotonic_ns'], value['end_monotonic_ns']
    if (type(start) is not int or type(end) is not int or start < 0 or end < start
            or type(value['elapsed_seconds']) not in (int, float) or not math.isfinite(value['elapsed_seconds'])
            or value['elapsed_seconds'] != (end - start) / 1e9
            or type(value['started_unix_ns']) is not int or value['started_unix_ns'] <= 0
            or type(value['timeout_seconds']) not in (int, float) or not math.isfinite(value['timeout_seconds'])
            or not 0 < value['timeout_seconds'] <= 600):
        raise ValueError('Invalid stage timing')
    if value['exit_code'] is not None and type(value['exit_code']) is not int:
        raise ValueError('Invalid stage exit code')
    if value['launch_error'] is not None and not isinstance(value['launch_error'], str):
        raise ValueError('Invalid stage launch error')
    if value['status'] in ('success', 'input_changed', 'missing_output', 'invalid_output') and (value['exit_code'] != 0 or value['launch_error'] is not None):
        raise ValueError('Contradictory successful command metadata')
    if value['status'] == 'nonzero_exit' and (value['exit_code'] in (None, 0) or value['launch_error'] is not None):
        raise ValueError('Contradictory failed command metadata')
    if value['status'] == 'launch_failure' and value['launch_error'] is None:
        raise ValueError('Missing launch failure diagnostic')
    if sha(output / 'stdout.bin') != digest(value['stdout_sha256']) or sha(output / 'stderr.bin') != digest(value['stderr_sha256']):
        raise ValueError('Stage output log hash mismatch')
    for path, expected in value['artifact_sha256'].items():
        workspace_path(path, reports=True)
        if sha(path) != digest(expected):
            raise ValueError('Stage artifact hash mismatch')
    for path, expected in value['final_input_sha256'].items():
        if expected is not None and sha(path) != digest(expected):
            raise ValueError('Stage input/tool hash mismatch')
    if value['passed'] and (value['exit_code'] != 0 or not value['inputs_stable']
            or value['input_sha256'] != value['final_input_sha256'] or value['missing_outputs']
            or value['invalid_outputs'] or set(value['required_outputs']) != set(value['artifact_sha256'])):
        raise ValueError('Unsupported successful stage')
    return dict(passed=True, recorded_stage_passed=value['passed'], status=value['status'],
        elapsed_seconds=value['elapsed_seconds'], process_file_open_attestation=False)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output')
    parser.add_argument('--timeout', type=float, default=60)
    parser.add_argument('--input', action='append', default=[])
    parser.add_argument('--require', action='append', default=[])
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    report = run_stage(command, args.output, args.timeout, args.require, inputs=args.input)
    print(json.dumps(report, indent=2))
    sys.exit(0 if report['passed'] else 1)
