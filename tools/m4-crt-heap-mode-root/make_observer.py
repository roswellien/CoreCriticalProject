"""Derive only the archive orchestration from a pinned successful observer."""
import hashlib
from pathlib import Path
ROOT = Path(__file__).absolute().parents[2]
source = ROOT/'tools/m4-crt-heap-create-root/observe.py'
if hashlib.sha256(source.read_bytes()).hexdigest() != 'a07423c042f91c04b2472a64198003b6e634b99bdf5429fcb2e8fafef76cc918':
    raise ValueError('Frozen accepted archive orchestration')
text = source.read_text(encoding='utf-8')
text = text.replace('heap-create continuation','heap-mode selector/probe')
text = text.replace('m4-crt-heap-create-root','m4-crt-heap-mode-root')
text = text.replace('m4-crt-heap-init-root/root-acceptance-r1','m4-crt-heap-create-root/root-acceptance-r1')
text = text.replace('a9a549d0acf1e8cd3a0015b4b7cdd2d61876ded33e0c69610c37bf9bc60b001d',
                    'e40df22e7b6263f75d9215cdaeadeb6a30030a4b07008c58442d8512d10c4326')
text = text.replace('Required genuine CRT heap mode selector remains unresolved','Required genuine CRT GetVersionExA remains unresolved')
text = text.replace('index+97','index+109')
text = text.replace('Delegated heap-creation author','Delegated heap-mode selector/probe author')
text = text.replace('whole_pages=18','whole_pages=20')
text = text.replace('source_identity_bytes=1940,new_compiled_source_bytes=84,new_guarded_source_bytes=84,executed_source_bytes=48,new_guest_objects=0,prior_guest_objects_preserved=26',
    'source_identity_bytes=2026,new_compiled_source_bytes=86,new_guarded_source_bytes=86,reused_heap_source_bytes=84,executed_source_bytes=132,new_guest_objects=4,prior_guest_objects_preserved=26')
text = text.replace('source_PCs=13,source_accesses=10,actual_source_CALLs=3,distinct_API_return_reads=1',
    'source_PCs=39,source_accesses=24,actual_source_CALLs=5,genuine_stack_probe_RET=1,distinct_API_return_reads=1')
text = text.replace("defined_final_arithmetic_flags='TEST opaque48450001: all6zero; AF generated representative0'",
    "defined_final_arithmetic_flags='TEST declared lower stack DWORD & oldSP20001848; ordinaryzero44; AF generated representative0'")
text = text.replace('source_RET_executed=False,locale_executed=False',
    'source_RET_executed=True,heap_initializer_RET=False,GetVersionExA_executed=False,heap_mode_selected=False,locale_executed=False')
text = text.replace("scope='Original BEFORE/source composition plus declared real HeapCreate ownership witness and finite guest API ABI model'",
    "scope='Original BEFORE plus declared owned lower-stack input; genuine selector/probe/query source and separate actual HeapCreate ownership witness'")
text = text.replace('original_x86_API_internals_equivalence=False,files=F.PHYSICAL',
    'original_x86_API_internals_equivalence=False,lower_stack_original_observed=False,original_guard_stack_growth_proved=False,TIB_and_Policy_changed=False,files=F.PHYSICAL')
destination = Path(__file__).with_name('observe.py')
if destination.exists():
    raise FileExistsError(destination)
destination.write_text(text,encoding='utf-8')
print('Fresh observer orchestration derived; new source/ownership/positive model imported independently')
