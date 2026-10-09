"""Directed admission, provider, compiled routing and complete-record controls."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m2-boundary-extension'))
from build import OUT, LLVM, sha
from adapt import adapt, BLOCKS
from compare import cases, expected, HEADER, REQ, RES_SIZE, read_results, validate_build, verify
import compare
import live

COUNTS={'adapter_positive':0,'adapter_negative':0,'worker_rejections':0,
        'saved_record_rejections':0,'provenance_rejections':0,'live_observation_rejections':0}

class AdapterControls(unittest.TestCase):
    def test_all_reviewed_blocks(self):
        with tempfile.TemporaryDirectory(dir=OUT) as temp:
            for name in BLOCKS:
                with self.subTest(block=name):
                    report=adapt(LLVM/'LLVM-C.dll',OUT/f'{name}-guest.ll',Path(temp)/f'{name}.ll',Path(temp)/f'{name}.json',name)
                    self.assertTrue(report['guest_ir_identity_reviewed']);COUNTS['adapter_positive']+=1
    def test_unsafe_authored_ir_variants_rejected(self):
        entry=(OUT/'entry-guest.ll').read_text();direct=(OUT/'direct-guest.ll').read_text()
        variants={
            'wrong_entry':('entry',entry.replace('define ptr @sub_10000000','define ptr @sub_10000001',1)),
            'wide_pc':('entry',entry.replace('i32 %program_counter','i64 %program_counter',1)),
            'unknown_direct_target':('entry',entry.replace('sub_10000200','sub_deadbeef')),
            'widened_bridge':('entry',entry.replace('i32 noundef %7','i64 noundef %7',1)),
            'state_layout':('entry',entry.replace('%struct.State = type { %struct.X86State }','%struct.State = type { %struct.X86State, i64 }')),
            'unknown_helper':('entry',entry.replace('__remill_read_memory_32','__remill_unknown_helper')),
            'changed_return_continuation':('entry',entry.replace('%28 = add i32 %27, 5','%28 = add i32 %27, 6',1)),
            'host_pointer_cast':('entry',entry.replace('  %ECX =','  %bad = inttoptr i32 17 to ptr\n  %ECX =',1)),
            'removed_poison':('entry',entry.replace('store i32 -1515851763, ptr %EAX','store i32 0, ptr %EAX',1)),
            'wrong_stack_argument':('direct',direct.replace('%60 = add i32 %58, 4','%60 = add i32 %58, 8',1)),
        }
        with tempfile.TemporaryDirectory(dir=OUT) as temp:
            folder=Path(temp)
            for label,(name,source) in variants.items():
                with self.subTest(control=label):
                    guest=folder/f'{label}.ll';guest.write_text(source)
                    self.assertNotEqual(sha(guest),sha(OUT/f'{name}-guest.ll'))
                    with self.assertRaisesRegex(ValueError,'identity'):adapt(LLVM/'LLVM-C.dll',guest,folder/'host.ll',folder/'layout.json',name)
                    self.assertFalse((folder/'host.ll').exists());COUNTS['adapter_negative']+=1
    def test_unknown_profile_rejected(self):
        with self.assertRaisesRegex(ValueError,'Unknown admitted block'):adapt(LLVM/'LLVM-C.dll',OUT/'entry-guest.ll',OUT/'never.ll',OUT/'never.json','unknown')
        COUNTS['adapter_negative']+=1

class WorkerControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.build=json.loads((OUT/'build.json').read_text())
    def test_compiled_context_controls(self):
        for kind in ('O0','O2'):
            child=subprocess.run([self.build['workers'][kind]['path'],'--check-context'],capture_output=True,text=True)
            self.assertEqual(child.returncode,0,child.stderr);self.assertIn('Context controls passed: 27',child.stdout)
    def test_logical_fp_vector_state_preserved(self):
        for kind in ('O0','O2'):
            child=subprocess.run([self.build['workers'][kind]['path'],'--check-state-preservation'],capture_output=True,text=True)
            self.assertEqual(child.returncode,0,child.stderr);self.assertIn('preservation checks passed: 96',child.stdout)
    def test_unknown_target_rejected_through_actual_generated_call(self):
        for kind in ('O0','O2'):
            child=subprocess.run([self.build['workers'][kind]['path'],'--check-unknown-call'],capture_output=True,text=True)
            self.assertEqual(child.returncode,1);self.assertIn('Unknown/non-call guest target pc=',child.stderr)
            self.assertIn('target=3735928559',child.stderr);COUNTS['worker_rejections']+=1
    def reject_matrix(self,records,raw=None,fixture=None,live_mode=False,message=''):
        if raw is None:raw=HEADER.pack(b'MW34BEXQ',1,len(records),REQ.size,32)+b''.join(REQ.pack(*q) for q in records)
        with tempfile.TemporaryDirectory(dir=OUT) as temp:
            folder=Path(temp);request=folder/'input.bin';code=folder/'fixture.bin';request.write_bytes(raw)
            code.write_bytes((OUT/'calls.bin').read_bytes() if fixture is None else fixture)
            for kind,worker in self.build['workers'].items():
                with self.subTest(worker=kind,message=message):
                    output=folder/f'{kind}.bin';output.write_bytes(b'KEEP')
                    argv=[worker['path']]+(['--live-timer'] if live_mode else [])+[str(request),str(output),str(code)]
                    child=subprocess.run(argv,capture_output=True,text=True)
                    self.assertEqual(child.returncode,1,child.stderr);self.assertIn(message,child.stderr)
                    self.assertEqual(output.read_bytes(),b'KEEP','Admission modified an existing output')
                    COUNTS['worker_rejections']+=1
    def test_malformed_protocol_before_output(self):
        q=cases()[0];good=HEADER.pack(b'MW34BEXQ',1,1,REQ.size,32)+REQ.pack(*q)
        headers=[(b'BADMAGIC',1,1,60,32),(b'MW34BEXQ',2,1,60,32),(b'MW34BEXQ',1,1,61,32),
                 (b'MW34BEXQ',1,1,60,64),(b'MW34BEXQ',1,0,60,32),(b'MW34BEXQ',1,100001,60,32)]
        for h in headers:self.reject_matrix([q],raw=HEADER.pack(*h)+REQ.pack(*q),message='Invalid M2 header')
        for raw in (good[:23],good[:-1]):self.reject_matrix([q],raw=raw,message='Truncated input')
        self.reject_matrix([q],raw=good+b'X',message='Trailing input')
    def test_unsafe_and_late_records_before_output(self):
        q=cases()[0]
        for index,value in ((4,0x20001004),(4,0x20002000),(4,0xfffffffc),(8,0x302),(8,0),(9,0x10000001),(13,2)):
            invalid=list(q);invalid[index]=value
            self.reject_matrix([q,invalid],message='Unsafe entry/frame/selector')
        self.reject_matrix([q],raw=HEADER.pack(b'MW34BEXQ',1,2,60,32)+REQ.pack(*q),message='Truncated input')
    def test_fixture_identity_before_output(self):
        raw=bytearray((OUT/'calls.bin').read_bytes());raw[4]^=1
        for fixture in (raw,raw[:-1],raw+b'X'):self.reject_matrix([cases()[0]],fixture=fixture,message='Fixture identity mismatch')
    def test_live_admission_before_provider_and_output(self):
        qs=live.cases()
        self.reject_matrix(qs[:-1],live_mode=True,message='Live matrix requires eight records')
        for index,value in ((8,0x602),(12,1),(13,2)):
            altered=[list(q) for q in qs];altered[-1][index]=value
            self.reject_matrix(altered,live_mode=True,message='Unsafe entry/frame/selector' if index==13 else 'Live provider requires DF0 and zero unused timer input')
        self.reject_matrix(qs,raw=HEADER.pack(b'MW34BEXQ',1,8,60,32)+b''.join(REQ.pack(*q) for q in qs)+b'X',live_mode=True,message='Trailing input')
    def test_saved_record_cpu_counter_trace_page_corruption(self):
        q=cases()[0];correct=expected(q)
        with tempfile.TemporaryDirectory(dir=OUT) as temp:
            path=Path(temp)/'result.bin'
            for offset in (0,4,16,32,36,40,44,48,52,56,60,64,64+4096+0x40,64+4096+0x60,64+8191):
                corrupted=bytearray(correct);corrupted[offset]^=1
                path.write_bytes(HEADER.pack(b'MW34BEXR',1,1,RES_SIZE,64)+corrupted)
                with self.assertRaises(ValueError):verify([q],path,64)
                COUNTS['saved_record_rejections']+=1
    def test_saved_result_extent_headers(self):
        good=HEADER.pack(b'MW34BEXR',1,1,RES_SIZE,64)+expected(cases()[0])
        with tempfile.TemporaryDirectory(dir=OUT) as temp:
            path=Path(temp)/'result.bin'
            for raw in (good[:-1],good+b'X',HEADER.pack(b'MW34BEXR',1,1,RES_SIZE,32)+good[24:]):
                path.write_bytes(raw)
                with self.assertRaises(ValueError):read_results(path,1,64)
                COUNTS['saved_record_rejections']+=1
    def test_provenance_hash_corruption_rejected(self):
        paths=[ROOT/'tools/m2-boundary-extension/context.hpp',OUT/'entry-host.ll',Path(self.build['workers']['O0']['path']),
               LLVM/'llc.exe',ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/build/bin/lift/remill-lift-21.exe',
               ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/build/lib/Arch/X86/Runtime/x86.bc',
               ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/X86/Runtime/State.h',
               OUT/'observed-import.json',ROOT/'MW3/Mech3.exe',ROOT/'games/mw3/docs/imports-mw3-us-1-2-retail.csv',
               Path(self.build['original_link_map']['path']),OUT/'worker-O0-pe.txt']
        for target in paths:
            def corrupted(path):return '0'*64 if Path(path).resolve()==target.resolve() else sha(path)
            with patch.object(compare,'sha',corrupted):
                with self.assertRaises(ValueError):validate_build()
            COUNTS['provenance_rejections']+=1
    def test_live_counter_result_progress_and_metadata_corruptions(self):
        qs=live.cases();raw=(OUT/'live-results-O0.bin').read_bytes();meta=json.loads((OUT/'live-worker-O0.json').read_text())
        with tempfile.TemporaryDirectory(dir=OUT) as temp:
            path=Path(temp)/'live.bin'
            for offset in (24+52,24+56,24+60,24+64+4096+0x60):
                altered=bytearray(raw);altered[offset]^=1;path.write_bytes(altered)
                with self.assertRaises(ValueError):live.verify(qs,path,64,meta,self.build['original_shim_rva'])
                COUNTS['live_observation_rejections']+=1
            constant=[expected(q,actual_timer=123) for q in qs]
            path.write_bytes(HEADER.pack(b'MW34BEXR',1,8,RES_SIZE,64)+b''.join(constant))
            with self.assertRaisesRegex(ValueError,'progress'):live.verify(qs,path,64,meta,self.build['original_shim_rva'])
            COUNTS['live_observation_rejections']+=1
            path.write_bytes(raw)
            for key,value in (('provider','unknown'),('provider_calls',0),('bridge_calls',0),('guest_iat_target',0x12345678)):
                changed={**meta,key:value}
                with self.assertRaises(ValueError):live.verify(qs,path,64,changed,self.build['original_shim_rva'])
                COUNTS['live_observation_rejections']+=1

if __name__=='__main__':unittest.main(verbosity=2)
