"""Supplementary exact-image/IR admission and authored final-AF leak controls."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
from adapt_slice import adapt, admit_slice_record, prove_final_af, digest

AUTHORED = '''define ptr @sub_558290(ptr noalias %state, i32 %program_counter, ptr noalias %memory) {
  %af = getelementptr i8, ptr %state, i32 2069
  %v = call zeroext i8 @__remill_undefined_8()
  store i8 %v, ptr %af, align 1
  br label %end
end:
  %r = call ptr @__remill_function_return(ptr %state, i32 %program_counter, ptr %memory)
  ret ptr %r
}
'''


def controls(dll, guest, host, slice_record, record):
    ledger = []
    def rejects(name, action, expected):
        try:
            action()
        except (ValueError, KeyError, FileNotFoundError) as exc:
            if expected not in str(exc):
                raise AssertionError(f'{name}: unexpected diagnostic {exc}') from exc
            ledger.append({'name': name, 'outcome': 'rejected', 'diagnostic': str(exc)})
        else:
            raise AssertionError(name + ': unsafe admission accepted')
    prove_final_af(AUTHORED, {'%af': 2069})
    ledger.append({'name': 'authored_final_AF_store_only_positive', 'outcome': 'admitted',
                   'input_sha256': hashlib.sha256(AUTHORED.encode()).hexdigest()})
    changes = [
        ('undefined_arithmetic_leak', '  br label %end', '  %leak = add i8 %v, 1\n  br label %end', 'leaks'),
        ('undefined_memory_leak', '  br label %end', '  store i8 %v, ptr %memory, align 1\n  br label %end', 'leaks'),
        ('undefined_address_leak', '  br label %end', '  %leak = getelementptr i8, ptr %memory, i8 %v\n  br label %end', 'leaks'),
        ('undefined_return_leak', '  br label %end', '  %leak = call ptr @rogue(i8 %v)\n  br label %end', 'leaks'),
        ('conditional_continuation', '  br label %end', '  br i1 true, label %end, label %end', 'control flow'),
        ('cyclic_continuation', '  ret ptr %r', '  br label %end', 'Cyclic'),
        ('after_store_AF_load', '  br label %end', '  %leak = load i8, ptr %af, align 1\n  br label %end', 'read/aliased'),
        ('after_store_alias_escape', '  br label %end', '  %leak = call ptr @rogue(ptr %af)\n  br label %end', 'read/aliased'),
        ('unreviewed_observer', '  br label %end', '  %leak = call ptr @rogue(ptr %state)\n  br label %end', 'observer'),
        ('volatile_AF_store', 'store i8 %v', 'store volatile i8 %v', 'Unsupported'),
        ('poison_AF_store', 'store i8 %v', 'store i8 poison', 'Unsupported'),
        ('AF_store_width', 'store i8 %v', 'store i32 %v', 'destination'),
        ('second_undefined_call', '  br label %end', '  %v2 = call zeroext i8 @__remill_undefined_8()\n  br label %end', 'exactly one'),
        ('wrong_entry', '@sub_558290', '@sub_558291', 'entry/signature'),
    ]
    for name, old, new, expected in changes:
        changed = AUTHORED.replace(old, new)
        rejects(name, lambda changed=changed: prove_final_af(changed, {'%af': 2069}), expected)
    rejects('wrong_AF_destination', lambda: prove_final_af(AUTHORED, {'%af': 2067}), 'destination')
    rejects('unreachable_block', lambda: prove_final_af(AUTHORED.replace('\n}', '\nrogue:\n  ret ptr %memory\n}'), {'%af': 2069}), 'Unreachable')
    source = guest.read_bytes()
    # These altered copies still contain private lifted game IR, so their
    # temporary directory remains within ignored local M3 reports.
    private_root = Path(__file__).resolve().parents[2] / 'reports/m3-slice'
    if not record.resolve().is_relative_to(private_root.resolve()):
        raise ValueError('Private admission report must remain in ignored M3 reports')
    record.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='admission-', dir=record.parent) as name:
        folder = Path(name)
        for label, changed in [
            ('altered_entry_IR', source.replace(b'@sub_558290(', b'@sub_558291(', 1)),
            ('altered_defined_flag_IR', source.replace(b'store i8 0, ptr %119', b'store i8 1, ptr %119', 1)),
            ('altered_AF_helper_IR', source.replace(b'__remill_undefined_8', b'__remill_undefined_16')),
            ('altered_memory_target_IR', source.replace(b'7520756', b'7520760', 1)),
            ('altered_bridge_IR', source.replace(b'__remill_read_memory_32', b'__remill_read_memory_64')),
            ('altered_State_layout_IR', source.replace(b'[32 x %union.VectorReg]', b'[31 x %union.VectorReg]', 1)),
            ('extra_unused_helper_IR', source + b'\ndeclare i32 @rogue()\n'),
        ]:
            if changed == source:
                raise AssertionError('Mutation failed to alter input: ' + label)
            mutated = folder / (label + '.ll')
            mutated.write_bytes(changed)
            rejects(label, lambda mutated=mutated: adapt(dll, mutated, folder/'host.ll', folder/'layout.json', slice_record), 'exact reviewed')
        original = json.loads(slice_record.read_text(encoding='utf-8-sig'))
        for label, key, value in [('wrong_image_identity', 'image_sha256', '0'*64),
                                  ('wrong_code_identity', 'code_sha256', '0'*64),
                                  ('wrong_entry_identity', 'entry_va', 0x558291),
                                  ('partial_function_extent', 'code_bytes', 42)]:
            changed = deepcopy(original)
            changed[key] = value
            mutated = folder / (label + '.json')
            mutated.write_text(json.dumps(changed))
            rejects(label, lambda mutated=mutated: admit_slice_record(mutated), 'binding differs')
        changed = deepcopy(original)
        changed['image_path'] = str(folder/'absent.exe')
        mutated = folder/'missing-image.json'
        mutated.write_text(json.dumps(changed))
        rejects('missing_actual_image', lambda: admit_slice_record(mutated), 'absent.exe')
        changed = deepcopy(original)
        wrong_page = folder/'bad-global.bin'
        wrong_page.write_bytes(bytes(4095)+b'\1')
        changed['global_page']['initial_path'] = str(wrong_page)
        mutated = folder/'wrong-global.json'
        mutated.write_text(json.dumps(changed))
        rejects('wrong_global_page_zero_fill', lambda: admit_slice_record(mutated), 'zero-fill')
    report = {'schema_version': 1, 'profile': 'm3-whole-function-558290',
              'guest_ir_sha256': digest(guest), 'host_ir_sha256': digest(host),
              'slice_record_sha256': digest(slice_record), 'adapter_sha256': digest(Path(__file__).with_name('adapt_slice.py')),
              'controls_source_sha256': digest(Path(__file__)), 'controls': ledger,
              'negative_controls': sum(item['outcome']=='rejected' for item in ledger),
              'positive_controls': sum(item['outcome']=='admitted' for item in ledger),
              'scope': 'Exact image/IR identity plus directed authored final-AF use/control proof; no broader IR or unsupported-domain admission'}
    record.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: report[key] for key in ('negative_controls', 'positive_controls')}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('llvm-dll', 'guest', 'host', 'slice-record', 'record'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    controls(args.llvm_dll, args.guest, args.host, args.slice_record, args.record)
