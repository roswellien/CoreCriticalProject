"""Reject unreviewed native symbols before the Windows linker can supply them."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

BRIDGES = {'__remill_read_memory_f64', '__remill_write_memory_f64', '__remill_read_memory_32',
           '__remill_function_return', '__remill_fpu_exception_clear', '__remill_fpu_exception_test'}
EXPECTED = {name: set(BRIDGES) for name in ('mul64', 'div64', 'mul-special', 'div-special')}
# Compiler-generated Windows stack probe and floating-code marker; neither
# exchanges a scalar extended value with the Microsoft C runtime.
HOST_RUNTIME = {'_fltused', '__chkstk'}


def check(names, kind):
    if not EXPECTED[kind].issubset(names) or names - EXPECTED[kind] - HOST_RUNTIME:
        raise ValueError('Unreviewed native symbols: ' + repr(sorted(names)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=EXPECTED, required=True)
    parser.add_argument('--nm', type=Path, required=True)
    parser.add_argument('--object', type=Path, required=True)
    parser.add_argument('--record', type=Path, required=True)
    args = parser.parse_args()
    run = subprocess.run([str(args.nm.resolve()), '--undefined-only', str(args.object.resolve())],
                         check=True, capture_output=True, text=True, timeout=30)
    names = set()
    for line in run.stdout.splitlines():
        match = re.fullmatch(r'\s*U\s+([\w.$]+)\s*', line)
        if not match: raise ValueError('Unreviewed nm output')
        names.add(match[1])
    check(names, args.kind)
    for symbol in ('nearbyintl', 'nearbyint', 'external_callback'):
        try: check(names | {symbol}, args.kind)
        except ValueError: pass
        else: raise ValueError('Symbol gate accepted an unknown floating/indirect dependency')
    result = {'status': 'passed', 'kind': args.kind, 'undefined_symbols': sorted(names),
              'object_sha256': hashlib.sha256(args.object.read_bytes()).hexdigest(),
              'nm_sha256': hashlib.sha256(args.nm.read_bytes()).hexdigest(), 'negative_controls': 3}
    args.record.write_text(json.dumps(result, indent=2) + '\n')
    print(f'Native symbol gate {args.kind}: reviewed dependencies, three rejection controls')


if __name__ == '__main__':
    main()
