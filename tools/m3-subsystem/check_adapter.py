"""Authored full-CFG AF controls and exact private image/IR mutation controls."""
import argparse
import ctypes as c
import hashlib
import json
from pathlib import Path
import tempfile
from adapt_subsystem import (LLVM, ROOT, adapt, prove_af, admit_extraction, digest)

AUTHORED = '''define ptr @sub_55a560(ptr noalias %state, i32 %program_counter, ptr noalias %memory) {
  %af = getelementptr i8, ptr %state, i32 2069
  %v1 = call zeroext i8 @__remill_undefined_8()
  store i8 %v1, ptr %af, align 1
  %v2 = call zeroext i8 @__remill_undefined_8()
  store i8 %v2, ptr %af, align 1
  %v3 = call zeroext i8 @__remill_undefined_8()
  store i8 %v3, ptr %af, align 1
  %v4 = call zeroext i8 @__remill_undefined_8()
  store i8 %v4, ptr %af, align 1
  %v5 = call zeroext i8 @__remill_undefined_8()
  store i8 %v5, ptr %af, align 1
  br label %loop
loop:
  %choice = icmp ne i32 %program_counter, 0
  br i1 %choice, label %loop, label %cleanup
cleanup:
  %old_sp = add i32 %program_counter, 0
  %new_sp = add i32 8, %old_sp
  %a = xor i32 %new_sp, %old_sp
  %b = xor i32 %a, 8
  %c = trunc i32 %b to i8
  %d = lshr i8 %c, 4
  %af_defined = and i8 %d, 1
  store i8 %af_defined, ptr %af, align 1
  br label %exit
exit:
  %returned = call ptr @__remill_function_return(ptr %state, i32 %program_counter, ptr %memory)
  ret ptr %returned
}
declare zeroext i8 @__remill_undefined_8()
declare ptr @__remill_function_return(ptr, i32, ptr)
'''
FINAL = ('cleanup', 'store i8 %af_defined, ptr %af, align 1', '%new_sp = add i32 8, %old_sp')


def verify_authored(dll, path):
    api = LLVM(dll);context = api.ContextCreate();module, buffer, error = c.c_void_p(), c.c_void_p(), c.c_void_p()
    try:
        api.check(api.CreateMemoryBufferWithContentsOfFile(str(path.resolve()).encode(), c.byref(buffer), c.byref(error)), error)
        api.check(api.ParseIRInContext(context, buffer, c.byref(module), c.byref(error)), error)
        api.check(api.VerifyModule(module, 2, c.byref(error)), error)
    finally:
        if module.value: api.DisposeModule(module)
        api.ContextDispose(context)


def controls(dll, directory, record):
    private = (ROOT / 'reports/m3-subsystem').resolve()
    if not all(path.resolve().is_relative_to(private) for path in (directory, record)):
        raise ValueError('Private controls must remain under ignored subsystem reports')
    ledger = []
    def rejects(name, action, diagnostic):
        try:
            action()
        except (ValueError, KeyError, FileNotFoundError) as error:
            if diagnostic not in str(error): raise AssertionError(name + ': unexpected diagnostic: ' + str(error)) from error
            ledger.append({'name': name, 'outcome': 'rejected', 'diagnostic': str(error)})
        else:
            raise AssertionError('Unsafe control admitted: ' + name)
    with tempfile.TemporaryDirectory(prefix='adapter-controls-', dir=directory) as name:
        temporary = Path(name)
        authored = temporary / 'authored.ll';authored.write_text(AUTHORED)
        verify_authored(dll, authored)
        policy = prove_af(AUTHORED, 'consumer', {'%af': 2069}, authored_final_add=FINAL)
        ledger.append({'name': 'authored_loop_CFG_final_AF_dominance', 'outcome': 'admitted',
                       'LLVM_verified': True, 'input_sha256': hashlib.sha256(AUTHORED.encode()).hexdigest(),
                       'undefined_calls': policy['undefined_calls']})
        mutations = [
            ('return_bypasses_final_ADD', 'label %loop, label %cleanup', 'label %cleanup, label %exit', 'bypasses'),
            ('missing_final_AF_store', FINAL[1], '; removed final AF store', 'Missing/altered'),
            ('wrong_final_ADD', FINAL[2], '%new_sp = add i32 4, %old_sp', 'cleanup ADD'),
            ('defined_flag_leak', '  br label %loop', '  %leak = add i8 %v1, 1\n  br label %loop', 'leaks'),
            ('branch_taint_leak', '  br label %loop', '  %leak = icmp ne i8 %v1, 0\n  br label %loop', 'leaks'),
            ('address_taint_leak', '  br label %loop', '  %leak = getelementptr i8, ptr %memory, i8 %v1\n  br label %loop', 'leaks'),
            ('memory_value_leak', '  br label %loop', '  store i8 %v1, ptr %memory, align 1\n  br label %loop', 'leaks'),
            ('AF_load_before_overwrite', '  br label %loop', '  %leak = load i8, ptr %af, align 1\n  br label %loop', 'loaded/aliased'),
            ('AF_alias_escape', '  br label %loop', '  store ptr %af, ptr %memory, align 1\n  br label %loop', 'loaded/aliased'),
            ('unknown_State_observer', '  br label %loop', '  %leak = call ptr @rogue(ptr %state)\n  br label %loop', 'observer/helper'),
            ('early_return_bridge', '  br label %loop', '  %leak = call ptr @__remill_function_return(ptr %state, i32 %program_counter, ptr %memory)\n  br label %loop', 'escapes before'),
            ('State_pointer_escape', '  br label %loop', '  store ptr %state, ptr %memory, align 4\n  br label %loop', 'pointer escapes'),
            ('AF_modified_after_final_ADD', '  br label %exit', '  store i8 0, ptr %af, align 1\n  br label %exit', 'modified after'),
            ('AF_volatile_store', 'store i8 %v1', 'store volatile i8 %v1', 'Unsupported'),
            ('AF_wrong_store_width', 'store i8 %v1', 'store i32 %v1', 'adjacent reviewed'),
            ('unreachable_CFG_block', '\n}\ndeclare', '\nrogue:\n  ret ptr %memory\n}\ndeclare', 'Unreachable'),
        ]
        for name, old, new, diagnostic in mutations:
            changed = AUTHORED.replace(old, new)
            rejects(name, lambda changed=changed: prove_af(changed, 'consumer', {'%af': 2069}, authored_final_add=FINAL), diagnostic)
        rejects('wrong_AF_field', lambda: prove_af(AUTHORED, 'consumer', {'%af': 2067}, authored_final_add=FINAL), 'reviewed AF byte')
        for kind in ('setter', 'consumer'):
            guest = directory / (kind + '-guest.ll');host = directory / (kind + '-host.ll')
            source = guest.read_bytes()
            entry = b'@sub_558290' if kind == 'setter' else b'@sub_55a560'
            changes = [('entry', source.replace(entry, b'@sub_00000000', 1)),
                       ('helper', source.replace(b'__remill_undefined_8', b'__remill_undefined_16')),
                       ('State_layout', source.replace(b'[32 x %union.VectorReg]', b'[31 x %union.VectorReg]')),
                       ('unknown_declaration', source + b'\ndeclare i32 @rogue()\n'),
                       ('bridge', source.replace(b'__remill_read_memory_32', b'__remill_read_memory_64'))]
            if kind == 'consumer':
                changes += [('missing_final_AF', source.replace(b'store i8 %653, ptr %654, align 1', b'store i8 0, ptr %654, align 1')),
                            ('branch_target', source.replace(b'label %634', b'label %671')),
                            ('DX_width', source.replace(b'store i16', b'store i32'))]
            for label, changed in changes:
                if changed == source: raise AssertionError('Mutation did not alter actual input: ' + label)
                path = temporary / (kind + '-' + label + '.ll');path.write_bytes(changed)
                rejects(kind + '_exact_IR_' + label, lambda path=path, kind=kind: adapt(dll, path, temporary/'host.ll', temporary/'layout.json', directory/'extraction.json', kind), 'guest IR identity')
            ledger.append({'name': kind + '_actual_exact_IR_positive', 'outcome': 'admitted',
                           'guest_ir_sha256': digest(guest), 'host_ir_sha256': digest(host)})
        extraction = json.loads((directory/'extraction.json').read_text())
        for kind in ('setter', 'consumer'):
            for key, changed in [('sha256', '0'*64), ('bytes', 1), ('entry', 0), ('offset', 0)]:
                altered = json.loads(json.dumps(extraction));altered['functions'][kind][key] = changed
                path = temporary / ('bad-' + kind + key + '.json');path.write_text(json.dumps(altered))
                rejects(kind + '_extraction_' + key, lambda path=path, kind=kind: admit_extraction(path, kind), 'binding differs')
    report = {'schema_version': 1, 'profile': 'm3-connected-buffer-admission',
              'adapter_sha256': digest(Path(__file__).with_name('adapt_subsystem.py')),
              'controls_source_sha256': digest(Path(__file__)), 'extraction_sha256': digest(directory/'extraction.json'),
              'controls': ledger, 'negative_controls': sum(row['outcome']=='rejected' for row in ledger),
              'positive_controls': sum(row['outcome']=='admitted' for row in ledger)}
    record.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: report[key] for key in ('negative_controls', 'positive_controls')}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('llvm-dll', 'directory', 'record'): parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args();controls(args.llvm_dll, args.directory, args.record)
