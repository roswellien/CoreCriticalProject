"""Invoke the actual worker's shared staging admission on an external sentinel."""
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
    parser.add_argument('--worker', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    sentinel = output.with_suffix('.sentinel.bin')
    result = output.with_suffix('.result.bin')
    log = output.with_suffix('.worker.log')
    if any(path.exists() for path in (output, sentinel, result, log)):
        raise ValueError('Staging preservation controls require fresh paths')
    # Authored by this external process, before the worker acquires any owner.
    marker = b'MW34 external staging evidence\x00\xff\r\n' + bytes(range(256))
    sentinel.write_bytes(marker)
    before = bind(sentinel)
    command = [str(args.worker.resolve()), '--stage-collision-control',
               str(result), str(sentinel)]
    run = subprocess.run(command, capture_output=True, timeout=30)
    log.write_bytes(run.stdout + run.stderr)
    if run.returncode != 1 or run.stderr.strip() != b'Output staging file already exists':
        raise ValueError('Actual shared stage admission missed its intended rejection')
    if run.stdout or result.exists() or not sentinel.exists() or sentinel.read_bytes() != marker:
        raise ValueError('Actual rejected stage admission mutated external evidence/output')
    after = bind(sentinel)
    record = {'schema_version': 1, 'passed': True, 'controls': 1,
              'scope': 'Actual compiled worker invokes the same ownership helper as its result writer; no guest body execution',
              'command': command, 'worker': bind(args.worker.resolve()),
              'exit_code': run.returncode,
              'intended_diagnostic': 'Output staging file already exists',
              'result_path': str(result), 'result_exists': False,
              'sentinel_before': before, 'sentinel_after': after, 'log': bind(log)}
    output.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print('Actual staging preservation controls: 1')


if __name__ == '__main__':
    main()
