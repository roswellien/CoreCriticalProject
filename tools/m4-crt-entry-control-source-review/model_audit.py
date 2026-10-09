"""Seal the independent read-only review of the final root source observer.

This records a code/contract audit; it does not rerun the model, execute native
code, or claim to be a second whole-State numerical architecture oracle.
"""
import hashlib, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-entry-control'
PINS={}

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def pin(p,want=None):
 p=Path(p).resolve();h=sha(p)
 assert want is None or want==h,str(p)
 assert str(p)not in PINS or PINS[str(p)]==h
 PINS[str(p)]=h;return p

def main():
 out=BASE/'independent-root-model-audit-r1'
 assert not out.exists();out.mkdir()
 proof=pin(BASE/'root-model-r3/report.json','91d4f8129c39317498c3a56f963121854f9c434bb8d3b4725857c59a9da945ed')
 receipt=json.loads(proof.read_text())
 assert receipt['passed']and receipt['positive_records']==48 and receipt['causal_records']==72
 assert receipt['control_source_accesses']==2496 and len(receipt['observer_corruption_denials'])==51574
 assert receipt['whole_State_bytes']==3504 and receipt['whole_FX_bytes']==512 and receipt['whole_pages']==14 and receipt['source_identity_bytes']==900
 assert not receipt['author_model_imported']and not receipt['full_CRT']and not receipt['whole_M4_complete']
 pp=pin(BASE/'root-model-r3/pins.json');bindings=json.loads(pp.read_text())['files']
 model=pin(ROOT/'tools/m4-crt-entry-control-root/model.py',bindings[str(ROOT/'tools/m4-crt-entry-control-root/model.py')])
 observer=pin(ROOT/'tools/m4-crt-entry-control-root/observe.py',bindings[str(ROOT/'tools/m4-crt-entry-control-root/observe.py')])
 frozen={
 'tools/m4-crt-entry-matherr-root/model.py':'5bd21ddfc1ffef390a88891f60821ff055c32d73610fba7740d1f94688e0da32',
 'tools/m4-crt-entry-matherr-root/observe.py':'8a55f96c298f19ff1ccbe6c24a449378064b678cea07da3fd6aa83a79a58445f',
 'tools/m4-crt-entry-data-review/observe.py':'6f65958d1c7603e4c508ef560dcc443437f0ab551319989f926723bcecbe486e',
 'tools/m4-crt-control-independent/review.py':'49eea1a0c6615d685acad629c4ef10bab32c6f14aa960a0c1e1d01c6750f6e61',
 'tools/m4-crt-fdiv-independent/replay_model.py':'eb77c8cf6b0f533b2cd2b50b3ce6d3bbb2c26be2ea5e844278a45ca5cb297b35',
 'tools/m4-crt-fdiv-independent/native_model.py':'8eada91041660b2e3d149cc8df89c01c3a13c5e0d925b21f0bca0af69d2bed6b',
 'tools/analysis/pe.py':'bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638',
 'MW3/Mech3.exe':'95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf',
 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL':'2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7',
 'tools/m4-runtime/runtime.cpp':'48865157011deaa151dccbb598da3f5a8ed16ea1944d048549f97f66f32308f7',
 'reports/m4-crt-control-integration/research-r1/host.ll':'45de8ae06bda09bfbd7a734f4be67eeca6fc5a9f68161e614a89b2871a7b569a',
 }
 for p,h in frozen.items():pin(ROOT/p,h)
 for p in ('tools/m4-crt-entry-data-review/observe.py','tools/m4-crt-entry-prefix-independent/source_review.py','tools/m4-crt-control-integration-independent/original_model.py','tools/m4-crt-fdiv/registry.cpp','tools/m4-crt-entry-control/control_binding.inc','reports/m4-crt-entry-control/preparation-r5/control_context.hpp','reports/m4-crt-entry-control/preparation-r5/control.ll','reports/m4-crt-entry-control/preparation-r5/composition.cpp','reports/m4-crt-entry-control/preparation-r5/main_v2.inc','reports/m4-crt-entry-control/root-model-r2/failure.txt'):
  path=ROOT/p
  if path.exists():pin(path,bindings.get(str(path)))
 text=model.read_text();obs=observer.read_text();ir=(ROOT/'reports/m4-crt-entry-control/preparation-r5/control.ll').read_text()
 assert "address=(self.r['esp']-4)&0xffffffff\n        self.store(address,value,4);self.r['esp']=address;self.commit()"in text
 assert '%43 = call noundef ptr @__remill_write_memory_32' in ir and 'store i32 %39, ptr %37' in ir
 assert ir.index('%43 = call noundef ptr @__remill_write_memory_32')<ir.index('store i32 %39, ptr %37')
 assert "original[:24]"in obs and "payloads=[R.project(v) for v in original[:24]]"in obs
 assert "D.equal(altered,files"in obs and "for name in ('control-wrapper.bin','control-thunk.bin','control-hot.bin','control-cold.bin')"in obs
 report={
  'passed':True,
  'scope':'Independent read-only contract/code audit of final root source observer and its completed root whole-State proof receipt; no model or native execution rerun',
  'root_model_path':str(model),'root_model_sha256':sha(model),'root_observer_path':str(observer),'root_observer_sha256':sha(observer),
  'root_proof_path':str(proof),'root_proof_sha256':sha(proof),'root_proof_pins_path':str(pp),'root_proof_pins_sha256':sha(pp),
  'root_positive_records':48,'root_causal_records':72,'root_control_accesses':2496,'root_observer_corruption_denials':51574,
  'whole_State_bytes':3504,'whole_FX_bytes':512,'whole_pages':14,'source_identity_bytes':900,
  'checks':[
   {'name':'BEFORE-only origin and independent source imports','passed':True,'finding':'24 payloads independently project preserved original BEFORE rows; all imported expectation code is frozen independently authored source observers. Native AFTER is compared evidence, not seed or expectation.'},
   {'name':'Provider operand/access order and carried projections','passed':True,'finding':'Source memory reads and stores emit exactly the observed global bridge tuples; supervisors and frame guards remain outside source access counts. GPR lower DWORDs/aflag/PC updates preserve opaque State; flat flags project only at declared CPU boundaries; CW changes only State and RuntimeFX word.'},
   {'name':'PUSH denied store partial State follows actual preserved IR','passed':True,'finding':'At 780042EA the checked store occurs before publishing new ESP. Corrected root model retains prior StateESP1868 when control33 write is denied. Failed root-model-r2 observer trace is retained.'},
   {'name':'Current causal failure phases and first attribution','passed':True,'finding':'28/29 reject earlier FDIV full-page integrity at real game data resolve; 30 rejects typed FNSTCW incoherence; 31/32 reject FWAIT status/tag domain; 35 retains updated RET StatePC/ESP but stale completed-provider RuntimeCPU and failed wrapper frame. Terminal retry comparisons retain exact stopped bytes.'},
   {'name':'Whole observation and shared corruption validators','passed':True,'finding':'Checkpoint inventory and every file compare through frozen D.equal; event/status/call records use the same exact equality validator exercised by corruption probes. Added control source identity files have first/last byte challenges at positive0 and each new causal checkpoint.'},
  ],
  'findings':[],
  'no_additional_blocker_for_current_bounded_corpus':True,
  'limitations':['No failed provider POP-read or after-read observer case is in this root corpus. Root Provider.pop uses architectural read-before-increment, while preserved lifted POP publishes ESP before the checked read; current successful POP observations match, and no partial POP-read equivalence is credited.','Twelve masked original incoming CW words, empty guest TOP0/SW0/FTW0/status and checked serial mappings remain the guest domain. The independent rich-host/compiled review is separate.','No callback execution, full CRT attach/SEH, initializer-table caller, native frontend/menu or complete game acceptance. Undefined AF remains its explicit retained representative.'],
  'full_CRT':False,'whole_M4_complete':False,
 }
 rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');pin(rp)
 pin(Path(__file__));(out/'model_audit.py').write_bytes(Path(__file__).read_bytes());pin(out/'model_audit.py')
 (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
 print(json.dumps(dict(passed=True,files=len(PINS),model_sha256=sha(model),observer_sha256=sha(observer),report_sha256=sha(rp),pins_sha256=sha(out/'pins.json'))))

if __name__=='__main__':main()
