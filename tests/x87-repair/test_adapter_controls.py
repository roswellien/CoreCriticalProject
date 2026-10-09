"""Actual LLVM mutation controls for both repaired control-word profiles."""
import argparse
import json
from pathlib import Path
import re
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/x87-repair'))
from adapt_control import adapt


def run(dll, store, load_store, output):
    output.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(dir=output) as directory:
        root = Path(directory)
        for kind, guest in (('store', store), ('load-store', load_store)):
            source = guest.read_text()
            injection = 'ptr noalias %memory) {\n'
            adapt(dll, guest, root / (kind + '.ll'), root / (kind + '.json'), kind)
            mutations = {
                'unknown_external': source.replace('__remill_write_memory_16', '__mw34_unknown_write'),
                'pointer_integer': source.replace(injection, injection + '  %bad = ptrtoint ptr %state to i64\n'),
                'undefined': source.replace(injection, injection + '  %bad = add i32 undef, 0\n'),
                'floating': source.replace(injection, injection + '  %bad = fadd double 1.0, 2.0\n'),
                'extra_entry': source + '\ndefine i32 @extra() { ret i32 0 }\n',
                'rounding_getter': source.replace(injection, injection + '  %bad = call i32 @__remill_fpu_get_rounding()\n')
                                  + '\ndeclare i32 @__remill_fpu_get_rounding()\n',
                'varargs_write': source.replace('i16 noundef zeroext)', 'i16 noundef zeroext, ...)'),
                'missing_return_bridge': re.sub(r'(%\w+) = tail call ptr @__remill_function_return\([^\n]+\)',
                                                r'\1 = getelementptr i8, ptr %memory, i32 0', source),
            }
            if kind == 'load-store':
                mutations['varargs_setter'] = source.replace(
                    'declare dso_local void @__remill_fpu_set_rounding(i32 noundef)',
                    'declare dso_local void @__remill_fpu_set_rounding(i32 noundef, ...)')
            for name, changed in mutations.items():
                if changed == source:
                    raise ValueError('Mutation changed no source: ' + kind + '/' + name)
                candidate = root / (kind + '-' + name + '.ll')
                candidate.write_text(changed)
                try:
                    adapt(dll, candidate, root / 'rejected-host.ll', root / 'rejected.json', kind)
                except ValueError as error:
                    results.append({'kind': kind, 'control': name, 'rejected': True, 'reason': str(error)})
                else:
                    raise ValueError('Adapter admitted mutation: ' + kind + '/' + name)
            opposite = 'load-store' if kind == 'store' else 'store'
            try:
                adapt(dll, guest, root / 'wrong-profile.ll', root / 'wrong-profile.json', opposite)
            except ValueError as error:
                results.append({'kind': kind, 'control': 'wrong_profile', 'rejected': True, 'reason': str(error)})
            else:
                raise ValueError('Adapter admitted wrong profile: ' + kind)
    report = {'schema_version': 1, 'positive_profiles': 2, 'negative_control_count': len(results),
              'negative_controls': results}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Two adapter profiles and {len(results)} LLVM mutation controls passed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('llvm-dll', 'store-guest', 'load-store-guest', 'output-dir'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    run(args.llvm_dll, args.store_guest, args.load_store_guest, args.output_dir)
