"""Asset-free context/admission controls; no proprietary bytes are required."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('slice_admission',ROOT/'tools/m2-slice-admission/admission.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)


class AdmissionControls(unittest.TestCase):
    def setUp(self):
        self.context=a.fixture_context();self.evidence=a.reviewed_evidence()

    def reject_context(self,name,value,reason):
        q=copy.deepcopy(self.context);q[name]=value
        with self.assertRaisesRegex(a.AdmissionError,reason):a.admit_context(q,self.evidence)

    def test_context_is_admitted_only_for_planning(self):
        result=a.admit_context(self.context,self.evidence)
        self.assertTrue(result['context_contract_admitted']);self.assertFalse(result['execution_allowed'])
        with self.assertRaisesRegex(a.AdmissionError,'execution_blocked:missing_exact_translation'):
            a.admit_context(self.context,self.evidence,execute=True)

    def test_evidence_controls(self):
        for key,value,reason in (
            ('image_sha256','0'*64,'wrong_image'),('entry_va',a.ENTRY+1,'wrong_complete'),
            ('size_bytes',a.SIZE-1,'wrong_complete'),('code_sha256','1'*64,'wrong_complete'),
            ('global_va',a.GLOBAL_START+4,'wrong_global'),('global_size',16,'wrong_global'),
            ('global_initial_sha256','2'*64,'wrong_global'),('global_permissions','r','wrong_global'),
            ('global_zero_fill',False,'wrong_global'),('direct_targets',[0x5995b0],'unknown_callee'),
            ('indirect_targets',[0x599620],'unknown_callee'),('dependencies',['fild64'],'unsupported_instruction'),
            ('static_incoming_edge',{'return_pc':0x5995e3},'wrong_observed')):
            with self.subTest(key=key):
                evidence=copy.deepcopy(self.evidence);evidence[key]=value
                with self.assertRaisesRegex(a.AdmissionError,reason):a.admit_context(self.context,evidence)

    def test_context_identity_route_and_policy_controls(self):
        q=copy.deepcopy(self.context);q['unreviewed_FS_dependency']=0
        with self.assertRaisesRegex(a.AdmissionError,'unknown_or_missing_context'):a.admit_context(q,self.evidence)
        evidence=copy.deepcopy(self.evidence);evidence['claimed_translation']=True
        with self.assertRaisesRegex(a.AdmissionError,'unknown_or_missing_dependency'):a.admit_context(self.context,evidence)
        for key,value,reason in (
            ('image_sha256','0'*64,'wrong_image'),('entry_va',0x5996d0,'wrong_entry'),
            ('eip',a.ENTRY+1,'wrong_entry'),('state_bytes',3500,'wrong_guest_state'),
            ('address_bits',64,'wrong_guest_state'),('flags',0x302,'invalid_entry_flags'),
            ('cw',0x37e,'unsupported_or_unmasked'),('cw',0x17f,'unsupported_or_unmasked'),
            ('sw',0x80,'invalid_SW'),('top',1,'invalid_SW'),('physical_ftw',256,'invalid_SW'),
            ('physical_full_tags',0,'inconsistent_physical'),('stack_permissions','r','wrong_stack'),
            ('global_base',a.GLOBAL+4,'wrong_global'),('global_permissions','r','wrong_global'),
            ('global_bytes',('01'+'00'*4095),'wrong_global_initial'),('return_pc',a.RETURN+4,'wrong_return'),
            ('return_cleanup_bytes',4,'wrong_return'),('return_route','generated_unknown','wrong_return'),
            ('route_image_sha256','0'*64,'wrong_route'),('route_entry_va',0x5996d0,'wrong_route'),
            ('route_code_sha256','0'*64,'wrong_route'),('route_frozen',False,'unfrozen'),
            ('route_selection','replacement','unfrozen'),('original_route_selection','replacement','unfrozen'),
            ('direct_targets',[0x5995b0],'unknown_callee'),('indirect_targets',[0x1234],'unknown_callee'),
            ('object_mappings',[{}],'unsupported_object'),('import_mappings',[{'symbol':'timeGetTime'}],'unsupported_object'),
            ('thread_id',-1,'invalid_thread'),('context_id','','invalid_thread'),
            ('thread_policy','shared','invalid_thread'),('host_abi','x86_host','wrong_host'),
            ('host_fp_policy','none','wrong_host'),('translation_evidence',{'fake':'passed'},'unreviewed_translation')):
            with self.subTest(key=key):self.reject_context(key,value,reason)
        for policy in ('callbacks','seh','tls_fs','reentrancy','concurrency','host_pointer_in_guest'):
            with self.subTest(policy=policy):self.reject_context(policy,True,'unsupported_'+policy)

    def test_register_pointer_stack_return_and_storage_controls(self):
        for index,value in ((0,2**32),(4,a.STACK+4090),(4,a.STACK-4)):
            q=copy.deepcopy(self.context);q['registers'][index]=value
            with self.subTest(index=index,value=value):
                with self.assertRaises(a.AdmissionError):a.admit_context(q,self.evidence)
        q=copy.deepcopy(self.context);stack=bytearray.fromhex(q['stack_bytes']);stack[256]^=1;q['stack_bytes']=stack.hex()
        with self.assertRaisesRegex(a.AdmissionError,'wrong_return'):a.admit_context(q,self.evidence)
        for key,size,reason in (('stack_bytes',4095,'invalid_stack'),('global_bytes',4095,'invalid_global'),
                               ('vector_bytes',2047,'invalid_vector'),('mmx_bytes',127,'invalid_MMX')):
            with self.subTest(key=key):self.reject_context(key,'00'*size,reason)
        self.reject_context('logical_raw80',['00'*9]*8,'invalid_raw80')
        q=copy.deepcopy(self.context);q['logical_raw80'][0]=(0x8000000000000001).to_bytes(8,'little').hex()+'ff7f'
        with self.assertRaisesRegex(a.AdmissionError,'unsupported_occupied_raw80'):a.admit_context(q,self.evidence)
        q=copy.deepcopy(self.context);q['logical_raw80'][0]='01'+'00'*9
        with self.assertRaisesRegex(a.AdmissionError,'unsupported_occupied_raw80'):a.admit_context(q,self.evidence)

    def test_full_physical_mapping_and_preserved_context_domain(self):
        # Planning accepts every TOP/tag-hole shape when independently coherent.
        for top in range(8):
            for ftw in range(256):
                q=copy.deepcopy(self.context);q['top']=top;q['sw']=top<<11;q['physical_ftw']=ftw
                slots=[bytes.fromhex(s) for s in q['logical_raw80']]
                q['physical_full_tags']=a.full_tags(top,ftw,slots)
                self.assertFalse(a.admit_context(q,self.evidence)['execution_allowed'])
        for cw in a.CWS:
            for df in (0,0x400):
                q=copy.deepcopy(self.context);q['cw']=cw;q['flags']=0x202|df
                self.assertTrue(a.admit_context(q,self.evidence)['context_contract_admitted'])
        # Physical tags must classify zero/special independently of occupancy.
        q=copy.deepcopy(self.context);q['top']=7;q['sw']=7<<11|0x241;q['physical_ftw']=0x83
        values=[bytes.fromhex(v) for v in q['logical_raw80']]
        values[0]=bytes(10);values[1]=(1<<63).to_bytes(8,'little')+bytes.fromhex('ff7f')
        values[2]=(0xc00000000000beef).to_bytes(8,'little')+bytes.fromhex('ffff')
        q['logical_raw80']=[v.hex() for v in values];q['physical_full_tags']=a.full_tags(7,0x83,values)
        q['vector_bytes']=bytes(i&255 for i in range(2048)).hex();q['mmx_bytes']=bytes((i*37)&255 for i in range(128)).hex()
        self.assertTrue(a.admit_context(q,self.evidence)['context_contract_admitted'])

    def test_missing_or_wrong_actual_image_is_failure(self):
        directory=ROOT/'reports/m2-slice-admission/control-inputs';directory.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=directory) as tmp:
            tmp=Path(tmp);wrong=tmp/'authored-not-game.bin';wrong.write_bytes(b'authored wrong identity')
            for path in (tmp/'missing.exe',wrong):
                with self.subTest(path=path.name):
                    output=tmp/('output-'+path.name)
                    child=subprocess.run([sys.executable,str(ROOT/'tools/m2-slice-admission/inspect_image.py'),
                                          '--image',str(path),'--output',str(output)],capture_output=True,text=True)
                    self.assertNotEqual(child.returncode,0);self.assertFalse((output/'actual-image.json').exists())


if __name__=='__main__':unittest.main()
