"""Run the prepared native fixture with an unquoted, measured process path."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(arguments):
    if len(arguments) != 7:
        raise ValueError('Exact prepared fixture command required')
    executable = Path(arguments[0]).absolute()
    directory = Path(arguments[-1]).absolute()
    base = ROOT / 'reports/m4-crt-heap-mode-review'
    if (executable.name != 'controls.exe' or executable.parent.name not in ('O0', 'O2')
            or executable.parent.parent.parent != base
            or not executable.parent.parent.name.startswith('compiled-')
            or directory != executable.parent / 'actual' or directory.exists()
            or str(executable)[0].upper() != 'D' or ' ' in str(executable)):
        raise ValueError('Fresh exact native fixture in measured D-leading path required')
    receipt = executable.parent / 'native-command.json'
    log = executable.parent / 'controls.log'
    if receipt.exists() or log.exists():
        raise ValueError('Fresh native command receipt required')
    before = digest(executable)
    started = time.perf_counter_ns()
    result = subprocess.run(arguments, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    finished = time.perf_counter_ns()
    log.write_bytes(result.stdout)
    sys.stdout.buffer.write(result.stdout)
    record = dict(argv=arguments, exit_code=result.returncode,
                  worker_path=str(executable), worker_sha256=before,
                  worker_unchanged=digest(executable) == before,
                  direct_argv=True, command_line=subprocess.list2cmdline(arguments),
                  monotonic_start_ns=started, monotonic_end_ns=finished,
                  duration_seconds=(finished - started) / 1e9,
                  stdout_sha256=hashlib.sha256(result.stdout).hexdigest(),
                  stdout_path=str(log),
                  original_executed=False, ordinary_game_launched=False)
    receipt.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    if not record['worker_unchanged']:
        raise ValueError('Native fixture executable changed during execution')
    return result.returncode


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
