"""Directed authored admission, routing and saved-record corruption controls."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m2-integration'))
from build import OUT, LLVM, sha
from adapt import adapt, BLOCKS
from compare import cases, expected, HEADER, REQ, RES_SIZE, read_results, validate_build, verify
import compare

class AdapterControls(unittest.TestCase):
    def test_all_reviewed_blocks(self):
        with tempfile.TemporaryDirectory(dir=OUT) as temp:
            for name in BLOCKS:
                with self.subTest(block=name):
                    report=adapt(LLVM/'LLVM-C.dll',OUT/f'{name}-guest.ll',Path(temp)/f'{name}.ll',Path(temp)/f'{name}.json',name)
                    self.assertTrue(report['guest_ir_identity_reviewed'])
    def test_unsafe_authored_ir_variants_rejected(self):
        source=(OUT/'entry-guest.ll').read_text()
        variants={
            'wrong_entry':source.replace('define ptr @sub_10000000','define ptr @sub_10000001',1),
            'wide_pc':source.replace('i32 %program_counter','i64 %program_counter',1),
            'unknown_direct_target':source.replace('sub_10000200','sub_deadbeef'),
            'widened_bridge':source.replace('i32 noundef %7','i64 noundef %7',1),
            'state_layout':source.replace('%struct.State = type { %struct.X86State }','%struct.State = type { %struct.X86State, i64 }'),
            'unknown_helper':source.replace('__remill_read_memory_32','__remill_unknown_helper'),
            'changed_return_continuation':source.replace('add i32 %11, 5','add i32 %11, 6'),
            'host_pointer_cast':source.replace('  %ECX =','  %bad = inttoptr i32 17 to ptr\n  %ECX =',1),
        }
        with tempfile.TemporaryDirectory(dir=OUT) as temp:
            folder=Path(temp)
            for name,source in variants.items():
                with self.subTest(control=name):
                    guest=folder/f'{name}.ll';guest.write_text(source)
                    self.assertNotEqual(sha(guest),sha(OUT/'entry-guest.ll'))
                    with self.assertRaises(ValueError):adapt(LLVM/'LLVM-C.dll',guest,folder/'host.ll',folder/'layout.json','entry')
                    self.assertFalse((folder/'host.ll').exists())
    def test_unknown_profile_rejected(self):
        with self.assertRaises(ValueError):adapt(LLVM/'LLVM-C.dll',OUT/'entry-guest.ll',OUT/'never.ll',OUT/'never.json','unknown')

class WorkerControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.build=json.loads((OUT/'build.json').read_text())
    def test_compiled_context_controls(self):
        for kind in ('O0','O2'):
            with self.subTest(worker=kind):
                child=subprocess.run([self.build['workers'][kind]['path'],'--check-context'],capture_output=True,text=True)
                self.assertEqual(child.returncode,0,child.stderr)
                self.assertIn('Context controls passed: 19',child.stdout)
    def test_logical_fp_vector_state_preserved(self):
        for kind in ('O0','O2'):
            with self.subTest(worker=kind):
                child=subprocess.run([self.build['workers'][kind]['path'],'--check-state-preservation'],capture_output=True,text=True)
                self.assertEqual(child.returncode,0,child.stderr)
                self.assertIn('Logical guest FP/SIMD preservation checks passed: 96',child.stdout)
    def test_unknown_target_rejected_through_generated_call(self):
        self.worker_rejection('unknown_target',choice=2,message='Unknown/non-call guest target',native_only=True)
    def test_reference_unknown_target_not_executed(self):
        self.worker_rejection('unknown_reference',choice=2,message='Unsafe entry/frame/selector',reference_only=True)
    def test_changed_fixture_rejected(self):self.worker_rejection('fixture',mutate_fixture=True,message='Fixture identity mismatch')
    def test_malformed_header_rejected(self):self.worker_rejection('header',bad_header=True,message='Invalid M2 header')
    def test_unsafe_frame_rejected(self):self.worker_rejection('frame',bad_frame=True,message='Unsafe entry/frame/selector')
    def worker_rejection(self,name,choice=None,message='',native_only=False,reference_only=False,mutate_fixture=False,bad_header=False,bad_frame=False):
        q=list(cases()[0])
        if choice is not None:q[13]=choice
        if bad_frame:q[4]=0x20001004
        with tempfile.TemporaryDirectory(dir=OUT) as temp:
            folder=Path(temp);request=folder/'request.bin';fixture=folder/'fixture.bin'
            h=HEADER.pack(b'MW34M2Q1',1,1,REQ.size,64 if bad_header else 32)
            request.write_bytes(h+REQ.pack(*q));raw=bytearray((OUT/'calls.bin').read_bytes())
            if mutate_fixture:raw[4]^=1
            fixture.write_bytes(raw)
            for kind,worker in self.build['workers'].items():
                if native_only and kind=='reference' or reference_only and kind!='reference':continue
                with self.subTest(worker=kind,control=name):
                    result=subprocess.run([worker['path'],str(request),str(folder/'result.bin'),str(fixture)],capture_output=True,text=True)
                    self.assertEqual(result.returncode,1,result.stderr)
                    self.assertIn(message,result.stderr)
    def test_saved_record_memory_register_flag_trace_corruption(self):
        q=cases()[0];correct=expected(q)
        with tempfile.TemporaryDirectory(dir=OUT) as temp:
            path=Path(temp)/'result.bin'
            for offset in (0,16,32,36,44,48,52,52+4096+0x40,52+8191):
                with self.subTest(offset=offset):
                    corrupted=bytearray(correct);corrupted[offset]^=1
                    path.write_bytes(HEADER.pack(b'MW34M2R1',1,1,RES_SIZE,64)+corrupted)
                    with self.assertRaises(ValueError):verify([q],path,64)
    def test_result_header_rejected(self):
        with tempfile.TemporaryDirectory(dir=OUT) as temp:
            path=Path(temp)/'result.bin';path.write_bytes(HEADER.pack(b'MW34M2R1',1,1,RES_SIZE,32)+expected(cases()[0]))
            with self.assertRaises(ValueError):read_results(path,1,64)
    def test_provenance_hash_corruption_rejected(self):
        paths=[ROOT/'tools/m2-integration/context.hpp',OUT/'entry-host.ll',Path(self.build['workers']['O0']['path']),
               LLVM/'llc.exe',ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/build/bin/lift/remill-lift-21.exe',
               ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/build/lib/Arch/X86/Runtime/x86.bc',
               ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/X86/Runtime/State.h',
               OUT/'observed-import.json',ROOT/'MW3/Mech3.exe',ROOT/'games/mw3/docs/imports-mw3-us-1-2-retail.csv']
        for target in paths:
            with self.subTest(path=target.name):
                def corrupted(path):return '0'*64 if Path(path).resolve()==target.resolve() else sha(path)
                with patch.object(compare,'sha',corrupted):
                    with self.assertRaises(ValueError):validate_build()

if __name__=='__main__':unittest.main(verbosity=2)
