"""Prepare exact current141 writer/structural derivatives, never execute them."""
from pathlib import Path
import ast,hashlib,json,sys,textwrap
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];T=R/'tools/m4-startup141-root';O=R/'reports/m4-138-validation-review/full141-controller-preparation-r1';files={};changes={}
def need(v,m):
 if not v:raise ValueError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p,h=None):
 p=Path(p);v=sha(p);need(h is None or v==h,'Exact preparation input '+str(p));files[str(p)]=v;return p
def put(p,s):need(not p.exists(),'Fresh derivative '+str(p));ast.parse(s);p.write_text(s);return pin(p)
need(not O.exists()and not T.exists(),'Fresh controller namespace');T.mkdir()
review=pin(R/'reports/m4-138-validation-review/full141-prelaunch-r1/report.json','2dbca8bbba5b42b880d1751b7adac916870c7919fb3252bd12593f7105952bda')
old=pin(R/'tools/m4-constructor-native/run_fixture_v4.py').read_text();writer=old;deltas=[]
def replace(a,b):
 global writer
 need(a in writer,'Exact writer inherited binding '+a);writer=writer.replace(a,b);deltas.append((a,b))
for a,b in [('0f5761af58092ef55ccd265ed0acf5a0bbdead40fab96cdb87eccb79f99f1d18','0c00c2fe8857e9785043c6946920287644521efafe4830a75787f1f6b26f6032'),('f0dfc1427c9cca0c1b920be6fc030c6b9bb7e53ef631946abcbf4ddf215001a0','92b9ef5628be17e61070a3570d6faf8c0ff3235b1087210ed58a279e135f572c'),('reports/m4-constructor-native/fixture-build-r10/build.json','reports/m4-startup141-runway/build-r2/build.json'),('reports/m4-constructor-native/fixture-preparation-r6/report.json','reports/m4-startup141-runway/preparation-r2/report.json'),("out=R/'reports/m4-constructor-native'/name","out=R/'reports/m4-startup141-root'/name"),('from stages import run_stage,verify_stage','from stages_capture_storage import run_stage,verify_stage\nfrom paths_capture_storage import STORAGE_ROOT,workspace_path'),('capture=out/level','capture=workspace_path(STORAGE_ROOT/\'reports/m4-startup141-root\'/name/level,reports=True);need(not capture.exists(),\'Fresh configured capture destination\')'),('timeout_seconds=300','timeout_seconds=420'),('required_outputs=[capture/\'transport.json\'],inputs=list(files)','required_outputs=[capture/\'transport.json\'],inputs=list(files),cwd=STORAGE_ROOT'),("pin(R/'tools/m4-pipeline/stages.py')","pin(R/'tools/m4-pipeline/stages_capture_storage.py');pin(R/'tools/m4-pipeline/paths_capture_storage.py')"),('Actual constructor37','Actual full141'),('bounded37 writers','bounded141 writers'),('admitted constructor37 workers','admitted full141 workers')]:replace(a,b)
anchor="  a=json.loads(pin(review,digest).read_bytes());"
replace(anchor,"  need(review.resolve()==R/'reports/m4-138-validation-review/full141-prelaunch-r1/report.json'and digest=='2dbca8bbba5b42b880d1751b7adac916870c7919fb3252bd12593f7105952bda','Exact independent current141 review only');"+anchor.strip())
reverse=writer
for a,b in reversed(deltas):reverse=reverse.replace(b,a)
need(reverse==old,'Whole writer exact inverse')
put(T/'run_v1.py',writer);changes['writer_exact_inverse']=deltas
# Preserve the constructor37 source/resource checks as a reusable per-sequence
# helper. Only schedule-wide registrations/projection domain and replay count
# differ in the actual full141 Context; all constructor-specific guards remain.
parent=pin(R/'tools/m4-constructor-native/validate_fixture_v5.py').read_text()
prefix=parent[:parent.index('def main(')]
block=parent[parent.index("     final=prefix+"):parent.index('     results.append(')]
block=textwrap.dedent(block);original_block=block;helper_changes=[]
def hb(a,b):
 global block
 need(a in block,'Exact constructor helper scope binding');block=block.replace(a,b);helper_changes.append((a,b))
hb("selected_summary[9]==start[9]+25","selected_summary[9]==start[9]+111")
hb("new_registrations=[v for v in projection if v[0]==9];need(new_registrations==", "all_onexit=[v for v in projection if v[0]==9];need(len(all_onexit)==10 and {v[1]for v in all_onexit}==set(roots)|set(widget_roots),'Exact complete ten-root current union API projection domain');new_registrations=[v for v in all_onexit if v[1]in roots];need(new_registrations==")
hb("need(data.data(prefix+'growth-replay-count.bin')==bytes(4),'No replay or growth admitted in measured37 chronology')","need(1<=data.words(prefix+'growth-replay-count.bin',1)[0]<=512,'Inherited full141 genuine source growth is required and bounded')")
reverse=block
for a,b in reversed(helper_changes):reverse=reverse.replace(b,a)
need(reverse==original_block,'Whole constructor helper exact inverse')
helper=prefix+"\ndef validate_sequence(data,seq,roots,widget_roots,source,cold,expectedcalls):\n prefix=f'sequence-{seq}/'\n"+textwrap.indent(block,' ')+"\n return dict(source_operands=len(access),private_mirror_records=len(mirror),FS_events=len(FS),allocations=6,NULL_calls=2,getters=2)\n"
put(T/'constructor_structural_v1.py',helper);changes['constructor_body_exact_inverse']=helper_changes
# Extract every existing full138 structural gate intact; writer stages are
# separated so both native workers terminate before canonical readers begin.
parent138=pin(R/'tools/m4-joint-startup138/run_v3.py').read_text()
start=parent138.index("    need(records.words('native-header.bin'");end=parent138.index(';rows.append(',start);block138=textwrap.dedent(parent138[start:end]);old138block=block138;full_changes=[]
def fb(a,b):
 global block138
 need(a in block138,'Exact full138 structural geometry');block138=block138.replace(a,b);full_changes.append((a,b))
for a,b in [('(1,6,138,828,17,159716)','(1,6,141,846,17,159716)'),("records.words('selected-table.bin',138)","records.words('selected-table.bin',141)"),('(1,138,0,0,0,0,0,0)','(1,141,0,0,0,0,0,0)'),('persistent138-root sequences','persistent141-root sequences')]:fb(a,b)
reverse=block138
for a,b in reversed(full_changes):reverse=reverse.replace(b,a)
need(reverse==old138block,'Entire full138 reader gate exact inverse')
changes['full138_reader_exact_inverse']=full_changes
validator='''"""Exact current141 complete inherited138 plus constructor structural gate."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
BUILD='0c00c2fe8857e9785043c6946920287644521efafe4830a75787f1f6b26f6032'
PREP='92b9ef5628be17e61070a3570d6faf8c0ff3235b1087210ed58a279e135f572c'
REVIEW='2dbca8bbba5b42b880d1751b7adac916870c7919fb3252bd12593f7105952bda'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(execution,digest,name):
 out=R/'reports/m4-startup141-root'/name;need(not out.exists(),'Fresh strict141 structural namespace');out.mkdir(parents=True);pins={};passed=False;closed=True;rows=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact141 structural input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable141 physical input');pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  e=read(execution,digest);need(e['passed']and e['actual_workers_launched']==2 and e['all_workers_terminal']and e['build_sha256']==BUILD and e['preparation_sha256']==PREP and e['admission_review_sha256']==REVIEW,'Two terminal current141 writers with exact reviewed artifacts')
  p=read(R/'reports/m4-startup141-runway/preparation-r2/report.json',PREP);b=read(R/'reports/m4-startup141-runway/build-r2/build.json',BUILD);a=read(R/'reports/m4-138-validation-review/full141-prelaunch-r1/report.json',REVIEW);need(p['passed']and b['passed']and a['passed'],'Exact current141 source/link prelaunch')
  for q,h in e['files'].items():pin(q,h)
  prepdir=Path(b['preparation']).parent;phase_map=read(R/'reports/m4-startup141-runway/widget-phase-correction-r1/widget-phase-map141.json');old_map=read(prepdir/'widget-phase-map.json');need(len(phase_map)==len(old_map)==7,'Exact inherited seven widgets')
  for current,old in zip(phase_map,old_map):
   actual=next(i for i,x in enumerate(p['selected_order'])if x==dict(entry=current['root'],slot=current['slot']));need(current['phase']==actual and {k:v for k,v in current.items()if k!='phase'}=={k:v for k,v in old.items()if k!='phase'},'Exact physical141 widget phase with every old identity retained')
  page_map=read(prepdir/'source-page-union.json');registration=pin(prepdir/'registration_contract.hpp').read_text();expected_roots=tuple(int(v,16)for v in re.search(r'registration_roots\\{([^}]+)',registration)[1].split(','));need(len(expected_roots)==108,'Inherited108 registration observation identities')
  C=load(R/'tools/m4-startup141-root/constructor_structural_v1.py','current141_constructor_structural');source={v['pc']:v for v in read(R/'reports/m4-constructor-source/preparation-r1/source-instructions.json')};cold={pc for pc in source if 0x56fea0<=pc<0x56ff00};roots=[0x4103f0,0x410440,0x459b40];expectedcalls=[(roots[0],0x58af12,0x5abd26,12),(roots[0],0x58af6a,0x5abd26,4),(roots[0],0x58af9a,0x5abd1a,0),(roots[1],0x58af12,0x5abd26,12),(roots[1],0x58af6a,0x5abd26,4),(roots[1],0x58af9a,0x5abd1a,0),(roots[2],0x58f2a2,0x5abd26,12),(roots[2],0x45b80e,0x5abd26,12)]
  DS=load(R/'tools/m4-crt-allocation-root/run_storage.py','current141_canonical_storage');pin(__file__);pin(sys.executable)
  for level in('O0','O2'):
   records=DS.DirectSet(Path(e['runs'][level]['capture']),pin);closed=False
   try:
'''
validator+=textwrap.indent(block138,'    ')+'\n'
validator+='''    cases=[(0,0x7f,0),(0,0x37f,7),(0,0xf7f,0),(1,0x47f,7),(1,0xa7f,0),(1,0xe7f,7)]
    for seq,(repeat,cw,top)in enumerate(cases):
     prefix=f'sequence-{seq}/';C.host(records.data(prefix+'MFC-caller-hardware.bin'));C.host(records.data(prefix+'Widget/font-cleanup-caller-hardware.bin'))
     for phase,row in enumerate(p['selected_order']):
      raw=records.data(prefix+f'phase-{phase}.bin');tags=struct.unpack_from('<9I',raw);need(tags[:7]==(seq,repeat,phase,row['slot'],row['entry'],cw,top)and tags[7]==0,'All141 exact physical root/CW/TOP identities');need(struct.unpack_from('<2I',raw,148580)==(1,0),'Every141 source State seeded and no domain error');before=struct.unpack_from('<10I',raw,36);after=struct.unpack_from('<10I',raw,76);need(before[4]==0x20001800 and before[9]==row['entry']and after[4]==0x20001804 and after[9]==0x410a80,'Every genuine root CALL/RET frame')
      for side in('before','after'):need(len(records.data(prefix+f'phase-{phase}-{side}-constructor-global5F2000.bin'))==4096,'Additional entire carried constructor global5F2000 page')
     need(records.words(prefix+'selected/constructor-FS-source-scope.bin',2)==(0,0)and records.words(prefix+'cleaned/constructor-FS-source-scope.bin',2)==(0,0),'Balanced private current constructor source/FS scopes')
     result=C.validate_sequence(records,seq,roots,[v['root']for v in phase_map],source,cold,expectedcalls);rows.append(dict(level=level,sequence=seq,phases=141,**result))
   finally:records.close();del records;closed=True
  need(len(rows)==12,'Both native levels and all six carried141 domains');passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for q,h in pins.items():need(sha(q)==h,'Current141 structural conservation')
  d=dict(passed=passed,scope='Full141 strict structural/actual constructor source/frame/owner/resource/caller observations only; literal/provider/paired/refusal acceptance separate',execution_path=str(execution),execution_sha256=digest,build_sha256=BUILD,preparation_sha256=PREP,cases=rows,reader_closed=closed,initializer_credit=0,current141_acceptance=False,source_AFTER_seed=False,files=pins);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\\n');print(json.dumps(dict(passed=passed,reader_closed=closed,sha256=sha(q))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
'''
put(T/'validate_v1.py',validator)
for q in (R/'tools/m4-crt-allocation-root/run_storage.py',R/'tools/m4-pipeline/capture_bundle_storage.py',R/'tools/m4-pipeline/paths_capture_storage.py',R/'tools/m4-pipeline/stages_capture_storage.py',R/'reports/m4-startup141-runway/widget-phase-correction-r1/report.json',R/'reports/m4-startup141-runway/widget-phase-correction-r1/widget-phase-map141.json',Path(__file__)):pin(q)
O.mkdir(parents=True);q=O/'exact-derivative-relations.json';q.write_text(json.dumps(changes,indent=2)+'\n');pin(q)
report=dict(passed=True,scope='Unexecuted exact current141 writer and strict structural derivatives; raw12B independent helper and synthetic/import preflight pending',review_sha256=sha(review),writer=str(T/'run_v1.py'),validator=str(T/'validate_v1.py'),writer_exact_inverse=True,inherited_full138_gate_exact_inverse=True,constructor37_helper_exact_inverse=True,canonical_reader_unmodified=True,storage_root='G:/Projects/MW34Recomp-Captures',all_native_writers_terminal_before_any_canonical_reader=True,raw12B_independent_helper_pending=True,preflight_pending=True,archive_reader_opened=False,actual_worker_launches=0,initializer_credit=0,files=files)
q=O/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report=str(q),sha256=sha(q))))
