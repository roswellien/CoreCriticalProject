"""Public authored IR controls for the bounded dead arithmetic flag policy."""

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('mw34_host_adapter', ROOT / 'tools/lifting/host_adapter.py')
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


def authored_ir(profile='shift'):
    entry = adapter.PROFILES[profile]
    return f'''define ptr @sub_{entry:x}(ptr noalias %state, i32 %program_counter, ptr noalias %memory) {{
  %af = getelementptr inbounds nuw i8, ptr %state, i32 2069
  %of = getelementptr inbounds nuw i8, ptr %state, i32 2077
  %u0 = call zeroext i8 @__remill_undefined_8()
  %u1 = call zeroext i8 @__remill_undefined_8()
  %b = icmp ne i8 %u0, 0
  %v = zext i1 %b to i8
  store i8 %u1, ptr %af, align 1
  store i8 %v, ptr %of, align 1
  br label %finish
finish:
  store i8 0, ptr %af, align 1
  store i8 1, ptr %of, align 1
  ret ptr %memory
}}
declare zeroext i8 @__remill_undefined_8()
'''


class DeadFlagProofTests(unittest.TestCase):
    def reject(self, source, profile='shift', offsets=None):
        with self.assertRaises(ValueError):
            adapter.prove_dead_flags(source, profile, offsets)

    def test_explicit_profiles_prove_two_exact_overwrites(self):
        for profile in ('shift', 'mw3-helper'):
            with self.subTest(profile=profile):
                proof = adapter.prove_dead_flags(authored_ir(profile), profile)
                self.assertEqual(proof['undefined_calls'], 2)
                self.assertEqual(proof['flag_offsets'], [2069, 2077])
                self.assertEqual(proof['observable_undefined_values'], 0)
                self.assertEqual(len(proof['overwrites']), 2)
                self.assertEqual(proof['blocks'], ['entry', 'finish'])

    def test_fixture_profile_and_wrong_entry_are_rejected(self):
        self.reject(authored_ir(), profile='fixture')
        self.reject(authored_ir(), profile='mw3-helper')

    def test_missing_overwrite_and_tainted_overwrite_are_rejected(self):
        self.reject(authored_ir().replace('  store i8 1, ptr %of, align 1\n', ''))
        self.reject(authored_ir().replace('store i8 1, ptr %of', 'store i8 %u0, ptr %of'))

    def test_literal_undefined_or_poison_is_not_a_defined_overwrite(self):
        for value in ('undef', 'poison'):
            self.reject(authored_ir().replace('store i8 0, ptr %af', f'store i8 {value}, ptr %af'))

    def test_direct_and_overlapping_flag_loads_are_rejected(self):
        for insert in ('%read = load i8, ptr %af, align 1',
                       '%base = getelementptr inbounds i8, ptr %state, i32 2064\n'
                       '  %read = load i64, ptr %base, align 8',
                       '%base = getelementptr inbounds i8, ptr %state, i32 2068\n'
                       '  %read = load i16, ptr %base, align 1'):
            self.reject(authored_ir().replace('finish:\n', f'finish:\n  {insert}\n'))

    def test_checked_typed_gep_overlap_is_rejected(self):
        insert = ('%typed = getelementptr inbounds %struct.State, ptr %state, i32 0, i32 0\n'
                  '  %read = load i16, ptr %typed, align 1')
        source = authored_ir().replace('finish:\n', f'finish:\n  {insert}\n')
        self.reject(source, offsets={'%typed': 2068})
        self.reject(source)

    def test_nested_or_dynamic_alias_is_rejected(self):
        for gep in ('%nested = getelementptr inbounds i8, ptr %af, i32 0',
                    '%nested = getelementptr inbounds i8, ptr %state, i32 %program_counter'):
            self.reject(authored_ir().replace('finish:\n', f'finish:\n  {gep}\n'))

    def test_state_spill_reload_and_call_alias_are_rejected(self):
        spill = ('%local = alloca ptr, align 4\n  store ptr %state, ptr %local, align 4\n'
                 '  %alias = load ptr, ptr %local, align 4')
        self.reject(authored_ir().replace('finish:\n', f'finish:\n  {spill}\n'))
        self.reject(authored_ir().replace('finish:\n', f'finish:\n  {spill.replace("load ptr", "load i32")}\n'))
        leak = '%read = call i32 @__remill_read_memory_32(ptr %af, i32 0)'
        self.reject(authored_ir().replace('finish:\n', f'finish:\n  {leak}\n'))

    def test_tainted_extra_register_memory_and_call_uses_are_rejected(self):
        insertions = ['%reg = getelementptr inbounds i8, ptr %state, i32 2216\n'
                      '  store i8 %u0, ptr %reg, align 1',
                      '%escaped = call ptr @__remill_write_memory_32(ptr %memory, i32 0, i32 %u0)',
                      '%extra = icmp ne i8 %u0, 0\n  %unused = zext i1 %extra to i8']
        for insert in insertions:
            self.reject(authored_ir().replace('  br label %finish', f'  {insert}\n  br label %finish'))

    def test_conditional_cfg_loop_and_unreachable_block_are_rejected(self):
        self.reject(authored_ir().replace('br label %finish', 'br i1 %b, label %finish, label %other'))
        self.reject(authored_ir().replace('ret ptr %memory', 'br label %finish'))
        self.reject(authored_ir().replace('\n}\n', '\nother:\n  ret ptr %memory\n}\n'))
        self.reject(authored_ir().replace('  br label %finish', '  br label %finish\n  br label %finish'))

    def test_wrong_flags_broad_overwrite_and_volatile_are_rejected(self):
        self.reject(authored_ir().replace('i32 2069', 'i32 2065'))
        self.reject(authored_ir().replace('store i8 0, ptr %af', 'store i16 0, ptr %af'))
        self.reject(authored_ir().replace('store i8 0, ptr %af', 'store volatile i8 0, ptr %af'))

    def test_unknown_call_undefined_signature_and_external_use_are_rejected(self):
        self.reject(authored_ir().replace('finish:\n', 'finish:\n  %side = call i32 @unknown()\n'))
        self.reject(authored_ir().replace('call zeroext i8 @__remill_undefined_8()',
                                         'call zeroext i16 @__remill_undefined_8()', 1))
        self.reject(authored_ir() + '@leak = global ptr @__remill_undefined_8\n')
        self.reject(authored_ir().replace('declare zeroext i8 @__remill_undefined_8()',
                                         'declare zeroext i8 @__remill_undefined_8(...)'))

    def test_unrelated_scalar_call_and_memory_read_preserve_proof(self):
        insert = ('%value = call i32 @__remill_read_memory_32(ptr %memory, i32 0)\n'
                  '  %flag = call zeroext i1 @__remill_flag_computation_zero(i1 false)')
        proof = adapter.prove_dead_flags(authored_ir().replace('finish:\n', f'finish:\n  {insert}\n'), 'shift')
        self.assertEqual(proof['undefined_calls'], 2)


@unittest.skipUnless(os.environ.get('MW34_NATIVE_ADAPTER_TESTS') == '1',
                     'Set MW34_NATIVE_ADAPTER_TESTS=1 for pinned LLVM checks')
class NativeAdapterTests(unittest.TestCase):
    """Optional LLVM verification against generated, project-authored shift IR."""

    def test_authored_native_profile_and_rejection_controls(self):
        dll = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/LLVM-C.dll'
        fixture = ROOT / 'reports/fixture-shift-lift/fixture-guest.ll'
        if not dll.exists() or not fixture.exists():
            self.skipTest('Pinned LLVM and generated authored shift fixture are required')
        text = fixture.read_text()
        boundary = '37:                                               ; preds = %10\n'
        self.assertIn(boundary, text)
        mutations = {
            'AF load': text.replace(boundary, boundary + '  %test_read = load i8, ptr %27, align 1\n'),
            'OF load': text.replace(boundary, boundary + '  %test_read = load i8, ptr %35, align 1\n'),
            'overlapping load': text.replace(boundary, boundary +
                '  %test_ptr = getelementptr inbounds i8, ptr %state, i32 2068\n'
                '  %test_read = load i16, ptr %test_ptr, align 1\n'),
            'nested alias': text.replace(boundary, boundary +
                '  %test_ptr = getelementptr inbounds i8, ptr %27, i32 0\n'),
            'State spill reload': text.replace(boundary, boundary +
                '  %test_local = alloca ptr, align 4\n'
                '  store ptr %state, ptr %test_local, align 4\n'
                '  %test_alias = load ptr, ptr %test_local, align 4\n'),
            'missing overwrite': text.replace('  store i8 %77, ptr %78, align 1\n', ''),
            'tainted overwrite': text.replace('store i8 %61, ptr %62', 'store i8 %28, ptr %62'),
            'literal poison': text.replace('store i8 %61, ptr %62', 'store i8 poison, ptr %62'),
            'wrong flag': text.replace('i32 2077', 'i32 2079'),
            'bridge receives State': text.replace(
                '@__remill_read_memory_32(ptr noundef %45,',
                '@__remill_read_memory_32(ptr noundef %state,'),
            'global helper escape': text + '\n@test_global = global ptr @__remill_undefined_8\n',
        }
        report_root = (ROOT / 'reports').resolve()
        self.assertTrue(report_root.is_relative_to(ROOT.resolve()))
        with tempfile.TemporaryDirectory(prefix='adapter-controls-', dir=report_root) as directory:
            directory = Path(directory)
            self.assertTrue(directory.resolve().is_relative_to(report_root))
            guest, host, record = (directory / name for name in ('guest.ll', 'host.ll', 'layout.json'))
            guest.write_text(text)
            adapter.adapt(dll, guest, host, record, profile='shift')
            self.assertTrue(host.exists())
            for profile in ('fixture', 'mw3-helper'):
                with self.subTest(profile=profile), self.assertRaises(ValueError):
                    adapter.adapt(dll, guest, host, record, profile=profile)
            for name, mutation in mutations.items():
                self.assertNotEqual(mutation, text, name)
                guest.write_text(mutation)
                with self.subTest(control=name), self.assertRaises(ValueError):
                    adapter.adapt(dll, guest, host, record, profile='shift')


if __name__ == '__main__':
    unittest.main()
