"""Bounded ordinary-only diagnostic; no source execution or acceptance policy."""
from pathlib import Path
import hashlib,json,struct,sys
R=Path(__file__).resolve().parents[2]
O=R/'reports/m4-original141-fp-review/env-readiness-r1'
assert not O.exists();O.mkdir(parents=True)
pins={}
def pin(p):
 p=Path(p).resolve()
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 pins[str(p)]=h;return p
def read(p):return json.loads(pin(R/p).read_text())
obs=read('reports/m4-original141/root-capture-validation-r3/widget-GDI-observations.json')
assert len(obs)==1788
mismatch=[];candidate=[]
for i in range(0,len(obs),2):
 b,a=obs[i:i+2]
 assert b['side']==0 and a['side']==1
 assert all(b[k]==a[k] for k in ('sequence','phase','root','API'))
 assert len(bytes.fromhex(b['FX512_hex']))==512 and len(bytes.fromhex(b['ENV28_hex']))==28
 assert b['FX512_hex']==a['FX512_hex']
 be,ae=bytes.fromhex(b['ENV28_hex']),bytes.fromhex(a['ENV28_hex'])
 if be!=ae:
  predicted=be[:12]+bytes(14)+be[26:]
  assert predicted==ae
  mismatch.append(dict(pair_ordinal=i//2,identity={k:b[k] for k in ('sequence','phase','root','API','index')},before_ENV28_hex=be.hex(),after_ENV28_hex=ae.hex(),FX512_hex=b['FX512_hex'],FX512_sha256=hashlib.sha256(bytes.fromhex(b['FX512_hex'])).hexdigest(),differing_byte_offsets=[j for j in range(28)if be[j]!=ae[j]],before_decoded=dict(FIP=hex(struct.unpack_from('<I',be,12)[0]),FCS=hex(struct.unpack_from('<H',be,16)[0]),FOP=hex(struct.unpack_from('<H',be,18)[0]),FDP=hex(struct.unpack_from('<I',be,20)[0]),FDS=hex(struct.unpack_from('<H',be,24)[0])),before_header=b['header'],after_header=a['header'],before_CPU=b['CPU'],after_CPU=a['CPU'],arguments=b['arguments'],candidate_equation='computed own ENV-before[0:12] + fourteen zero bytes + own ENV-before[26:28]',candidate_matches_all_28_actual_bytes=True))
assert len(mismatch)==1 and mismatch[0]['identity']==dict(sequence=0,phase=137,root=0x5a3c30,API='CreateFontA',index=36)
files=['reports/m4-original141/source-preparation-r6/report.json','reports/m4-original141/source-preparation-r6/widget_observer_x86.asm','reports/m4-original141/source-preparation-r6/widget_observer.hpp','reports/m4-original141/build-r2/build.json','reports/m4-original141/build-r2/build-x86/mw34_joint_startup124_original.dir/Release/widget_observer_x86.obj','reports/m4-original141-source/source-r5/report.json','reports/m4-original141-source/source-r5-widgets/report.json','tools/m4-original141-source/widget_source141_v3.py','tools/m4-widget-source/compare_original_v3.py','tools/m4-fps-original/compare_source_v3.py','tools/m4-widget-growth-review/persistent_gdi.py','tools/m4-joint-startup131/acceptance.py','docs/m4-development-workflow.md','tools/m4-crt-fdiv-reference/observe_reference.py','reports/m4-crt-fdiv-reference/observations-r1/report.json']
for f in files:pin(R/f)
asm=(R/files[1]).read_text()
for proc in ('widget_create_entry','widget_create_return'):
 body=asm.split(proc+' PROC',1)[1].split(proc+' ENDP',1)[0]
 assert 'fnstenv widget_env\n fldenv widget_env\n call widget_observe\n fxrstor widget_fx\n fldenv widget_env' in body
pin(__file__);pin(sys.executable)
report=dict(passed=True,scope='Bounded sealed ordinary GDI observation diagnostic and current source policy inspection; compiled object physically pinned but no new linked disassembly review',pairs_inspected=894,whole_FX512_equal_pairs=894,whole_ENV28_equal_pairs=893,nonconserved_pairs=mismatch,wrapper_findings=dict(entry_capture_lines=[216,217,218,219,220,221],return_capture_lines=[258,259,260,261,262,263],full_ENV_restored_after_observe=True,missing_FLDENV_cause_supported=False,actual_API_internal_instruction_cause_proven=False),policy_findings=dict(older_five_widget_policy='compare_original_v3.py:109 consumes typed measured FP responses after exact CALL/frame/input joins; this is scoped component precedent, not current native carry equivalence',current_141_policy='widget_source141_v3.py:170 explicitly requires whole FX and ENV conservation; current failure is genuine under that predicate',current_FPS_policy='compare_source_v3.py:131 likewise requires whole FX and ENV conservation',native_policy='persistent_gdi.py:231 preserves whole guest FX512 and does not transport original ENV28; ENV shadow relation requires an explicit independently reviewed source/native API projection',acceptance131='acceptance.py retains MFC whole caller FX512/ENV28 criterion; it contains no GDI predicate authorizing this new widget effect',workflow='m4-development-workflow.md:30 requires independent prediction from original pre-execution state and source bytes then comparison of full storage'),recommendation='Do not silently remove conservation. If independently admitted, add one finite opaque typed CreateFontA metadata-clear effect at exact retained event identity, full own BEFORE ENV and FX/input/frame/module joins; compute all 28 predicted ENV bytes with the displayed equation and compare entire actual AFTER. Preserve whole FX, full 28-byte conservation on other 893 pairs and all current memory/CPU/call/resource gates. Require native guest ENV shadow projection and paired relation review, with explicit new policy scope; do not claim Win32 API body or WOW64 instruction proof.',remaining_gaps=['Internal CreateFontA/system transition responsible for metadata clear is not traced','Current native guest ENV/API projection and actual original/native equivalence of the finite effect are not established by this diagnostic','The retained older component typed FP response policy is not an acceptance allowance for current141'],source_executed=False,native_executed=False,worker_launched=False,archive_reader_opened=False,AFTER_state_seed=False,checker_modified=False,acceptance_credit=0,files=pins)
q=O/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),pairs=894,ENV_mismatches=1)))
