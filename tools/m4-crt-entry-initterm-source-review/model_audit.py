"""Read-only source audit receipt for a completed root BEFORE-only proof.

Does not import, execute, rerun or modify either root model/observer. It checks
the completed physical receipt and records the reviewed partial-state domain.
"""
import importlib.util, json, re, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('own_exact_initterm_source_contract',HERE/'review.py')
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
ROOT,BASE=R.ROOT,R.BASE
FROZEN={
 'tools/m4-crt-entry-control-root/model.py':'da9c2cf73fdc0db5832412bd66f3fd128c4366cc70485ddf4d5bde30f687110f',
 'tools/m4-crt-entry-control-root/observe.py':'aaee1da9ef938d9d8bb176bb2b26944c02fcdf8f881447fe568b5f5d11056e60',
 'tools/m4-crt-entry-matherr-root/model.py':'5bd21ddfc1ffef390a88891f60821ff055c32d73610fba7740d1f94688e0da32',
 'tools/m4-crt-entry-matherr-root/observe.py':'8a55f96c298f19ff1ccbe6c24a449378064b678cea07da3fd6aa83a79a58445f',
 'tools/m4-crt-entry-data-review/observe.py':'6f65958d1c7603e4c508ef560dcc443437f0ab551319989f926723bcecbe486e',
 'tools/m4-crt-control-independent/review.py':'49eea1a0c6615d685acad629c4ef10bab32c6f14aa960a0c1e1d01c6750f6e61',
 'tools/m4-crt-fdiv-independent/replay_model.py':'eb77c8cf6b0f533b2cd2b50b3ce6d3bbb2c26be2ea5e844278a45ca5cb297b35',
 'tools/m4-crt-fdiv-independent/native_model.py':'8eada91041660b2e3d149cc8df89c01c3a13c5e0d925b21f0bca0af69d2bed6b',
 'tools/m4-crt-entry/observe_prefix.py':'c45c54dc62a805113b5e56142d577f4a46a89790c68acda339bbb5f4a2915af1',
 'tools/m4-crt-entry/observe_first_fault.py':'a8c5d9baabd0ec26d89618c29bde8f647458133338c601107143dbe9418a7e33',
}

def main():
 R.need(len(sys.argv)==3,'model_audit.py fresh-audit-directory passed-root-proof-directory')
 out,proof=map(lambda s:Path(s).resolve(),sys.argv[1:]);R.need(out.parent==BASE and out.name.startswith('independent-root-model-audit-')and not out.exists(),'Fresh independent read-only audit directory');out.mkdir(parents=True)
 (out/'model_audit.py').write_bytes(Path(__file__).read_bytes());R.pin(out/'model_audit.py')
 try:
  root_model=ROOT/'tools/m4-crt-entry-initterm-root/model.py';root_observer=ROOT/'tools/m4-crt-entry-initterm-root/observe.py';model=R.text(root_model);observer=R.text(root_observer)
  report=R.read(proof/'report.json');proof_pins=R.read(proof/'pins.json')['files']
  R.need(report['passed']and report['positive_records']==48 and report['causal_records']==96,'Completed root full-corpus proof required before audit seal')
  R.need(report['whole_State_bytes']==3504 and report['whole_FX_bytes']==512 and report['whole_pages']==16 and report['source_identity_bytes']==934,'Entire source/State/FX/page proof scope')
  R.need(report['initterm_accesses']==384 and report['initterm_route_events']==288,'All positive null-route accesses/events included')
  for path in(root_model,root_observer):R.pin(path,proof_pins[str(path.resolve())])
  for rel,want in R.FROZEN.items():R.pin(ROOT/rel,want)
  for rel,want in FROZEN.items():
   path=ROOT/rel
   if not path.exists() and rel.endswith('observe_prefix.py'):path=ROOT/'tools/m4-crt-entry/observe_prefix.py'
   R.pin(path,want)
  for rel in('reports/m4-crt-entry-initterm/provider-preparation-r3/guest.ll','reports/m4-crt-entry-initterm/provider-preparation-r3/host.ll','reports/m4-crt-entry-initterm/preparation-r3/initterm_context.hpp','reports/m4-crt-entry-initterm/preparation-r3/initterm_binding.inc','reports/m4-crt-entry-initterm/preparation-r3/composition.cpp','reports/m4-crt-entry-initterm/preparation-r3/crt_services.cpp','reports/m4-crt-entry-initterm/root-execution-r1/execution.json','reports/m4-crt-entry-initterm/root-execution-r1/pins.json','reports/m4-crt-entry-initterm/independent-source-r1/report.json','reports/m4-crt-entry-initterm/independent-source-r3/report.json','reports/m4-crt-entry-initterm/independent-source-r3/pins.json'):
   R.pin(ROOT/rel)
  R.need('author_model_imported' in report and not report['author_model_imported']and 'author-model'not in model+observer and 'Session::initterm'not in model+observer,'No candidate handwritten model used for native credit')
  R.need('payloads=[R.project(v) for v in original[:24]]'in observer and 'writer_result(row,payload' in observer,'Input derives only from frozen original BEFORE projection')
  frozen_project=R.text(ROOT/'tools/m4-crt-fdiv-independent/replay_model.py').split('def project(original):',1)[1].split('\ndef seed',1)[0]
  R.need('tags,row,stack,_=original'in frozen_project and 'row[188:700]'in frozen_project and 'row[2236:2264]'in frozen_project and 'stack_after'not in frozen_project,'BEFORE CPU/FX/ENV/stack sources exclude original AFTER')
  R.need('self.init_write(address,value);self.r[\'esp\']=address'in model,'PUSH checked store before ESP publication')
  R.need('address=self.r[\'esp\'];self.r[\'esp\']+=4;self.init_commit()'in model and 'self.r[args[0]]=self.init_read(address)'in model,'POP ESP commits before checked read and ESI publication')
  R.need('value=self.init_read(self.r[\'esp\']);self.r[\'esp\']+=4;self.init_pc=value;self.init_commit()'in model,'RET pre-read guard then ESP/PC publication before closure')
  R.need('if self.control==43 and pc==0x780014f9:'in model and 'self.r[\'esp\']=0x20001ffc;self.init_commit()'in model,'Late MOV read-hook ESP mutation survives original SSA destination')
  R.need('if self.control==48 and pc==0x78001502 and self.init_step==3:self.raw_store(self.init_frame+8,END+4)'in model,'Late first-CMP end memory mutation preserves read SSA value')
  R.need('self.init_write(address,nxt);self.r[\'esp\']=address;self.init_pc=target;self.init_commit()'in model,'Actual callback CALL partial store/ESP/PC publication occurs before terminal rejection')
  R.need("if self.control==43 and self.init_pc==0x78001502 and self.init_level=='O2':address=self.init_frame+8"in model,'Only explicit mode43/O2 fixture follows independently reviewed cached operand')
  R.need(report.get('mode43_generalized_source_equivalence')is False,'Observer mutation not generalized as source-equivalence credit')
  ir=R.text(ROOT/'reports/m4-crt-entry-initterm/provider-preparation-r3/host.ll')
  R.need('define ptr @sub_780014f8(ptr noalias %state, i32 %program_counter, ptr noalias %memory)'in ir,'Preserved provider noalias State/token contract')
  for level in('O0','O2'):R.pin(ROOT/f'reports/m4-crt-entry-initterm/provider-preparation-r3/provider-{level}.obj')
  zero=R.text(BASE/'independent-source-r3/O0-provider-body.txt');optimized=R.text(BASE/'independent-source-r3/O2-provider-body.txt')
  R.need(all(x in zero for x in('171:','219:','21d:','232:')) and 'mov\tedx, dword ptr [rcx]'in zero and 'add\tedx, 0xc'in zero,'O0 actual COFF reloads StateESP after MOV bridge before CMP operand bridge')
  R.need(all(x in optimized for x in('2d:','34:','37:','64:','11a:','11e:','124:')) and 'mov\tr12d, dword ptr [rcx + 0x908]'in optimized and 'lea\tedx, [r15 + r14]'in optimized,'O2 actual COFF retains post-PUSH ESP operand across MOV bridge before first CMP')
  R.need('self.runtime_cpu=struct.pack' in model and 'self.project(0x5ac445,flat=True)'in model and 'registers[4]+=4'in model,'Explicit stale Runtime CPU and flat State projection at call supervision')
  R.need('OLD.OLD.check_stages(row,phases)'in observer and 'OLD.OLD.evidence_equal'in observer and 'D.equal(altered,files' in observer,'Production whole-stage validator reused by corruption probes')
  R.need("for offset in (0,len(files[name])-1):"in observer and "initterm-thunk.bin','initterm-provider.bin'"in observer,'Both ends of added source identities checked by same validator')
  R.need('for control in range(1,49):'in observer and all(v in observer for v in('if control<=12:','elif control<=24:','elif control<=36:','unused_init(row)')),'All inherited and new causal prefixes retained with inactive-route evidence')
  positives=report['positives'];R.need(len(positives)==48 and all(p['game_events']==48 and p['initterm_accesses']==8 and p['initterm_routes']==6 for p in positives),'Positive whole-source counts agree with exact source contract')
  causals=report['causals'];R.need(len(causals)==96 and {(v['level'],v['control'])for v in causals}=={(l,c)for l in('O0','O2')for c in range(1,49)},'Complete inherited/new causal domain')
  fixture=[v for v in causals if v['control']==43];R.need(len(fixture)==2 and all(v['artifact_specific_injected_operand']and not v['architectural_source_equivalence_credited']for v in fixture),'Both mode43 cases explicitly retain artifact-fixture scope')
  R.need({v['level']:v['initterm_job'][-1]for v in fixture}=={'O0':0x20002008,'O2':0x20001874},'Artifact operands independently supported by original compiled COFFs')
  failed=BASE/'root-model-r1/failure.txt';R.pin(failed)
  result=dict(passed=True,scope='Independent read-only root model/observer audit of the completed 48-positive/96-causal proof; mode43 is a separately reviewed artifact observer fixture',model_sha256=R.sha(root_model),observer_sha256=R.sha(root_observer),root_proof_sha256=R.sha(proof/'report.json'),root_proof_pins_sha256=R.sha(proof/'pins.json'),BEFORE_only=True,candidate_model_imported=False,whole_State_bytes=3504,whole_FX_bytes=512,whole_pages=16,source_identity_bytes=934,positive_records=48,causal_records=96,causal_source_expectations_excluding_mode43=94,causal_mode43_artifact_fixtures=2,mode43_source_equivalence_credited=False,mode43_operands={'O0':0x20002008,'O2':0x20001874},mode43_independent_basis='Preserved noalias provider IR and freshly decoded unchanged O0/O2 COFFs: O0 reloads StateESP, O2 retains post-PUSH register SSA before first CMP read; current-State guard rejects both before reading/ALU',corrected_root_attempt_trace=str(failed),initterm_accesses=384,initterm_route_events=288,source_partial_order=['PUSH/CALL store before ESP publication','POP ESP before read before ESI publication','RET pre-read guard before PC/ESP publication before nonvolatile closure','MOV43 injected ESP survives ESI store; next CMP operand follows actual per-level artifact','CMP48 end change after read leaves captured CMP operand unchanged'],persistent_FP_carry=True,old_Root_components_frozen=True,same_validator_corruption_probe_denials=len(report['observer_corruption_denials']),findings=[],limitations=['Actual admitted masked empty guest FP corpus and exact first null-only interval','Mode43 observer State mutation is outside original guest/noalias source-equivalence domain; no cross-level architectural equivalence claim','No arbitrary mapping/thread or unobserved partial-fault path equivalence claim','Historical standalone callback and later 144-entry initializer interval not executed','Successful callback/continuation and native application/menu not admitted'],full_CRT=False,native_menu=False,selected_initializer_count_unchanged=27,whole_M4_complete=False)
  (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');R.pin(out/'report.json');R.pin(Path(__file__));R.pin(HERE/'review.py')
  (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(R.PINS.items()))),indent=2)+'\n')
  print(json.dumps(dict(passed=True,files=len(R.PINS),report_sha256=R.sha(out/'report.json'),pins_sha256=R.sha(out/'pins.json'))))
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
