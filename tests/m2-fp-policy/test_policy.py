"""Asset-free tests of consolidated exclusions and exact authored domains."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('fp_policy',ROOT/'tools/m2-fp-policy/policy.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)


class FloatingPolicyControls(unittest.TestCase):
    def test_every_exact_profile_mode_vector(self):
        data=p.profiles()
        for name,profile in data['profiles'].items():
            self.assertEqual(len(profile['vectors'])*12,profile['cases'])
            self.assertEqual(len({tuple(v) for v in profile['vectors']}),profile['vectors_per_CW'])
            for cw in data['control_words']:
                for vector in profile['vectors']:
                    result=p.admit(name,cw,vector,profile['fixture_hex'])
                    self.assertTrue(result['profile_admitted']);self.assertFalse(result['general_execution_allowed'])
        for a in data['control_words']:
            self.assertTrue(p.admit('control-store',a,[a],'d939c3')['profile_admitted'])
            for b in data['control_words']:
                self.assertTrue(p.admit('control-load-store',a,[b],'d929d93ac3')['profile_admitted'])

    def test_excluded_conversion_classes(self):
        for bits in (0x7fefffffffffffff,0xffefffffffffffff,0x41e0000000000000,0xc1e0000000200000,
                     0x7ff0000000000000,0xfff0000000000000,0x7ff8000000001234,0xfff8000000004321,
                     0x7ff0000000001234,0xfff0000000004321,1,0x8000000000000001):
            with self.subTest(bits=hex(bits)):
                with self.assertRaises(p.PolicyError):p.admit('fistp32',0x37f,[bits,0],'dd01db1ac3')

    def test_two_nan_and_unlisted_payloads(self):
        for profile,code in (('mul-special','dd01dc4908dd1ac3'),('div-special','dd01dc7108dd1ac3')):
            for a,b in ((0x7ff8000000001234,0xfff8000000004321),(0x7ff0000000001234,0xfff0000000004321),
                        (0x7ff8000000001234,0xfff0000000004321)):
                with self.subTest(profile=profile,operands=(a,b)):
                    with self.assertRaisesRegex(p.PolicyError,'excluded_two_NaN'):p.admit(profile,0x37f,[a,b],code)
            for a,b in ((0x7ff800000000abcd,0x3ff0000000000000),(0x3ff0000000000000,0x7ff800000000abcd),
                        (0x7ff000000000abcd,0x3ff0000000000000),(0x3ff0000000000000,0x7ff000000000abcd)):
                with self.subTest(profile=profile,operands=(a,b)):
                    with self.assertRaisesRegex(p.PolicyError,'unlisted'):p.admit(profile,0x37f,[a,b],code)

    def test_mask_state_and_instruction_exclusions(self):
        data=p.profiles()
        for name,profile in data['profiles'].items():
            vector=profile['vectors'][0];code=profile['fixture_hex']
            for cw in (0x37e,0x37d,0x37b,0x377,0x36f,0x35f,0x17f,0x137f):
                with self.subTest(profile=name,cw=hex(cw)):
                    with self.assertRaisesRegex(p.PolicyError,'unmasked_or_unsupported'):p.admit(name,cw,vector,code)
            for prefix in ('dbe2','dbe3','df29'):
                with self.subTest(profile=name,instruction=prefix):
                    with self.assertRaisesRegex(p.PolicyError,'unsupported_instruction_sequence'):p.admit(name,0x37f,vector,prefix+code)
            for kwargs in ({'guest_clear':True},{'guest_trap_delivery':True},{'exceptional_exit':True},
                           {'entry_status':0x22},{'entry_stack_empty':False},{'other_instructions':('FNCLEX',)}):
                with self.subTest(profile=name,policy=kwargs):
                    with self.assertRaises(p.PolicyError):p.admit(name,0x37f,vector,code,**kwargs)

    def test_live_state_remains_pending(self):
        for profile,code in p.LIVE.items():
            with self.subTest(profile=profile):
                with self.assertRaisesRegex(p.PolicyError,'pending_live_state'):p.admit(profile,0x37f,[],code)
        with self.assertRaisesRegex(p.PolicyError,'unsupported_instruction_profile'):p.admit('FILD64',0x37f,[0,0],'df29c3')
        with self.assertRaisesRegex(p.PolicyError,'unsupported_operand_encoding'):p.admit('fistp32',0x37f,[-1,0],'dd01db1ac3')
        with self.assertRaisesRegex(p.PolicyError,'unsupported_operand_encoding'):p.admit('fistp32',0x37f,[2**64,0],'dd01db1ac3')

    def test_changed_domain_identity_rejected(self):
        target=ROOT/'reports/m2-fp-policy/domain-controls';target.mkdir(parents=True,exist_ok=True)
        original=p.DATA
        with tempfile.TemporaryDirectory(dir=target) as directory:
            path=Path(directory)/'authored-changed-domain.json';path.write_bytes(original.read_bytes()+b' ')
            try:
                p.DATA=path
                with self.assertRaisesRegex(p.PolicyError,'profile_domain_identity_changed'):p.profiles()
            finally:p.DATA=original


if __name__=='__main__':unittest.main()
