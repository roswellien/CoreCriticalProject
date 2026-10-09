"""Fail-closed mutation controls for the isolated x87 adapter."""
import argparse
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/x87-probe'))
from adapt_control import adapt


def run(dll, guest, output):
    source = guest.read_text()
    injection = 'ptr noalias %memory) {\n'
    mutations = {
        'unknown_external': source.replace('__remill_fpu_get_rounding', '__mw34_unreviewed_rounding'),
        'widened_rounding': source.replace('i32 @__remill_fpu_get_rounding', 'i64 @__remill_fpu_get_rounding')
                                  .replace('trunc i32 %11', 'trunc i64 %11'),
        'varargs_rounding': source.replace('declare dso_local i32 @__remill_fpu_get_rounding()',
                                          'declare dso_local i32 @__remill_fpu_get_rounding(...)'),
        'pointer_integer': source.replace(injection, injection + '  %bad = ptrtoint ptr %state to i64\n'),
        'duplicate_bridge_call': source.replace(injection, injection + '  %bad = call i32 @__remill_fpu_get_rounding()\n'),
        'undefined_value': source.replace(injection, injection + '  %bad = add i32 undef, 0\n'),
        'floating_operation': source.replace(injection, injection + '  %bad = fadd double 1.0, 2.0\n'),
        'extra_entry': source + '\ndefine i32 @extra() { ret i32 0 }\n',
    }
    output.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(dir=output) as directory:
        root = Path(directory)
        adapt(dll, guest, root / 'valid.ll', root / 'valid.json')
        for name, mutated in mutations.items():
            if mutated == source:
                raise ValueError('Control mutation did not change source: ' + name)
            path = root / (name + '.ll')
            path.write_text(mutated)
            try:
                adapt(dll, path, root / (name + '-host.ll'), root / (name + '.json'))
            except ValueError as error:
                results.append({'control': name, 'rejected': True, 'reason': str(error)})
            else:
                raise ValueError('Mutation was accepted: ' + name)
    report = {'schema_version': 1, 'valid_adaptation': True, 'negative_controls': results}
    (output / 'adapter-controls.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Adapter positive and eight mutation controls passed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--llvm-dll', type=Path, required=True)
    parser.add_argument('--guest', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    run(args.llvm_dll, args.guest, args.output_dir)
