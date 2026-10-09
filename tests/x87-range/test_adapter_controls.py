"""Adversarial source changes must not cross the exact arithmetic adapter gate."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--llvm-dll', type=Path, required=True)
    parser.add_argument('--kind', choices=('mul64', 'div64'), required=True)
    parser.add_argument('--guest', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('range_adapter', args.root / 'tools/x87-range/adapt_range.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    source = args.guest.read_text()
    op = 'fmul' if args.kind.startswith('mul') else 'fdiv'
    other = 'fdiv' if op == 'fmul' else 'fmul'
    mutations = {
        'fast_math': source.replace(op + ' x86_fp80', op + ' fast x86_fp80', 1),
        'wrong_arithmetic': source.replace(op + ' x86_fp80', other + ' x86_fp80', 1),
        'widened_guest_bridge': source.replace('i32 noundef %6)', 'i64 noundef 536875008)', 1),
        'invalid_flag_visible': source.replace('i32 2755', 'i32 2065', 1),
        'wrong_entry': source.replace('sub_10000000', 'sub_10000001'),
        'modified_stack': source.replace('i32 2770', 'i32 2772', 1),
        'unreviewed_call': source.replace('__remill_read_memory_f64', 'unreviewed_read'),
        'wrong_constant': source.replace('i32 noundef 127', 'i32 noundef 63', 1),
    }
    controls = []
    for name, text in mutations.items():
        if text == source:
            raise RuntimeError('Mutation did not change the authored IR: ' + name)
        path = args.output_dir / (name + '.ll')
        path.write_text(text)
        host = args.output_dir / (name + '-host.ll')
        record = args.output_dir / (name + '.json')
        try:
            module.adapt(args.llvm_dll, path, host, record, args.kind)
        except ValueError as error:
            if host.exists() or record.exists():
                raise RuntimeError('Rejected IR emitted accepted artifacts')
            controls.append({'name': name, 'status': 'rejected', 'reason': str(error),
                             'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        else:
            raise RuntimeError('Changed arithmetic IR accepted: ' + name)
    output = {'schema_version': 1, 'accepted_original_profile': module.SPEC[args.kind]['sha256'],
              'mutation_controls': len(controls), 'controls': controls}
    (args.output_dir / 'report.json').write_text(json.dumps(output, indent=2) + '\n')
    print(f'Numeric adapter: {len(controls)} altered profiles rejected before emission')


if __name__ == '__main__':
    main()
