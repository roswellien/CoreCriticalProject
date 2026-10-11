"""Explicit loaded source input / native resource / semantic CS ABI contract."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=ROOT/'reports/m4-lockit-source'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 p=pin(ROOT/'reports/m4-lockit-native/preparation-r3/report.json','4c28406fb33cc34976b754ceedd0203540be80535c557a79b322407aae342b7d');r=json.loads(p.read_bytes());pin(r['loaded_original_bootstrap_report'],r['loaded_original_bootstrap_sha256']);rw=pin(r['loaded_input_page'],r['loaded_input_page_sha256']).read_bytes();iat=pin(r['loaded_IAT_page'],r['loaded_IAT_page_sha256']).read_bytes();assert len(rw)==len(iat)==4096
 assert int.from_bytes(rw[0x658:0x65c],'little')==2
 entries=[]
 for site,slot,name,frame_offset in((0x7810a30b,0x78146198,'EnterCriticalSection',-16),(0x7810a35e,0x78146184,'LeaveCriticalSection',-8)):
  target=int.from_bytes(iat[slot&4095:(slot&4095)+4],'little');assert target==r['named_original_API_targets'][name];entries.append(dict(source_CALL_PC=site,source_IAT=slot,raw_loaded_x86_API_target=target,name=name,source_API_frame_offset=frame_offset,argument_count=1,guest_argument=0x78145640,native_resource_bytes=40,guest_semantic_payload_bytes=24,void_EAX_preserved=True,opaque_full_native_memory_copy=False))
 contract=dict(genuine_loaded_original_state=dict(address=0x78145658,value=2,seeded=False),source_CS=dict(address=0x78145640,bytes=24,genuine_original_before_hex=rw[0x640:0x658].hex(),opaque_preserved_offsets=[0,16,20],semantic_fields=[dict(name='LockCount',guest_offset=4,native_offset=8,width=4,rule='Native observed DWORD; admitted serial domain unheld FFFFFFFF, held FFFFFFFE'),dict(name='RecursionCount',guest_offset=8,native_offset=12,width=4,rule='Independently source-derived Enter minus Leave, compared with actual native DWORD'),dict(name='OwningThread',guest_offset=12,native_offset=16,width=4,rule='Actual native full pointer denotes current serial thread when held; semantic guest DWORD equals actual thread ID, zero when unheld')]),API_contracts=entries,resource_association=dict(lifecycle_index=5,marker_IAT=0x78146190,marker_raw_PE=0x866ce,marker_is_source_CALL=False,InitializeCriticalSection_executed_natively=True,source_DLL_DllMain_executed_natively=False,source_DLL_lifecycle_replaced=False,guest_State_CPU_FX_pages_change=False,generation=6,fifth_resource=True),source_opaque_native_CS_copy=False,source_typed_semantic_CS_output=True,admitted_domain='Serial initialized state2, no contention; original measured recursive probe supports depths0..2; ordinary candidate roots use0..1',cold_state0_state1_admitted=False,source_computation='The independent response adapter derives complete CS24 from original baseline and source depth/thread then checks actual API output and genuine nativeCS40 separately')
 for q in('capture.py','responses.py','game_model.py','compare_connected_v2.py'):pin(ROOT/'tools/m4-lockit-source'/q)
 pin(__file__);f=out/'association-contract.json';f.write_text(json.dumps(contract,indent=2)+'\n');pin(f);report=dict(passed=True,scope='Explicit ABI/input/resource association contract; no initializer or execution acceptance',clarifies_prior_interface='guest_CS_structure_transport=False means no opaque native40 copy. Typed semantic CS24 API output is explicitly allowed and independently derived.',contract=str(f),initializer_credit=False,files=pins);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
