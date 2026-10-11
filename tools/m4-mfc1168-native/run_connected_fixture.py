"""Admitted current-Context O0/O2 chronological14 writers and strict transport.

No current131 or source credit comes from this structural run. Both fresh
workers must finish before their bounded canonical observations are opened.
"""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'tools/m4-pipeline'))
from stages import run_stage,verify_stage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(build,digest,review,review_sha,name):
 out=R/'reports/m4-mfc1168-native'/name;need(not out.exists(),'Fresh connected execution');out.mkdir();pins={};runs={};levels=[];passed=False;launched=0;closed=True
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact current input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable current input');pins[str(p)]=v;return p
 try:
  admission=json.loads(pin(review,review_sha).read_bytes());need(admission['passed'],'Passed exact independent prelaunch')
  b=json.loads(pin(build,digest).read_bytes());need(b['passed'],'Both actual linked workers');p=json.loads(pin(b['preparation'],b['preparation_sha256']).read_bytes());need(p['passed'],'Passed BEFORE-only preparation')
  need(admission['build_sha256']==digest and admission['preparation_sha256']==b['preparation_sha256'],'Admission binds exact current build/preparation')
  need(len(p['selected_order'])==14 and p['selected_order'][-1]=={'entry':0x5ae3e4,'slot':0x5e0040},'Exact chronological first13/MFC root')
  for q,h in b['files'].items():pin(q,h)
  game=pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');provider=pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a');crt=pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');mfc=pin(R/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8');pin(__file__);pin(sys.executable)
  # No capture readers exist while either process is active.
  for level in('O0','O2'):
   worker=pin(b['workers'][level]['path'],b['workers'][level]['sha256']);capture=out/level;stage=out/(level+'-stage');args=list(map(str,(worker,game,provider,crt,mfc,capture)));launched+=1
   st=run_stage(args,stage,timeout_seconds=90,required_outputs=[capture/'transport.json'],inputs=list(pins));pin(stage/'stage.json');verify_stage(stage,sha(stage/'stage.json'));runs[level]=dict(worker=str(worker),arguments=args,stage=str(stage/'stage.json'),stage_sha256=sha(stage/'stage.json'),capture=str(capture/'transport.json'),elapsed_seconds=st['elapsed_seconds']);print(json.dumps(dict(level=level,stage_passed=st['passed'])),flush=True);need(st['passed'],'Actual '+level+' worker terminal success')
  path=pin(R/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('mfc_connected_strict',path);ds=importlib.util.module_from_spec(spec);spec.loader.exec_module(ds)
  for level in('O0','O2'):
   records=ds.DirectSet(Path(runs[level]['capture']),pin);closed=False
   try:
    need(records.words('native-header.bin',6)==(1,1,14,14,17,159716),'Current Native159716 header');need(records.words('sequences-header.bin',4)==(1,1,147400,17),'Current Sequence147400 header');need(records.words('selected-table.bin',14)==tuple(x['entry']for x in p['selected_order']),'Exact chronological source table');need(records.words('registration-roots.bin',101)==tuple(json.loads(pin(p['parent_preparation']).read_bytes())['registration_roots']),'All inherited current callbacks retained')
    tags=struct.unpack_from('<12I',records.data('sequence-0/summary.bin'));need(tags==(0,0,0x7f,0,1,14,0,0,0,0,0,0),'Complete current14 success/current finite CW-TOP')
    for phase,row in enumerate(p['selected_order']):
     record=records.data(f'sequence-0/phase-{phase}.bin');need(len(record)==159716,'Whole unchanged phase ABI');words=struct.unpack_from('<9I',record);need(words[:7]==(0,0,phase,row['slot'],row['entry'],0x7f,0) and words[7]==0,'Exact current root/phase/entry tags')
    stem='sequence-0/MFC/';need(len(records.data(stem+'before/State.bin'))==3504 and len(records.data(stem+'after/State.bin'))==3504,'Complete actual connected component State');need(len(records.data(stem+'after/accesses.bin'))==113*24 and len(records.data(stem+'after/APIs.bin'))==4*352,'Actual finite operand/API extents');need(records.words(stem+'cleaned/resource-context.bin',12,'Q')[2:7]==(0,0,0,0,0),'Both actual owned resources cleaned')
    need(records.data('COMPLETE.txt')==b'One genuine-domain persistent14-root native prefix and owned cleanup complete; fullM4 incomplete\n','Actual exact completion')
    levels.append(dict(**runs[level],level=level,logical_files=len(records.entries),payload_bytes=records.value['payload_bytes']));print(json.dumps(dict(level=level,structural_passed=True,logical_files=len(records.entries))),flush=True)
   finally:records.close();del records;closed=True
  for q,h in pins.items():need(sha(q)==h,'Stable current input after both workers/readers')
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  result=dict(passed=passed,scope='Current130 Context O0/O2 genuine-domain first13 plus nonregistering MFC root; strict structural writer result, complete literal/source/provider comparison separate',build=str(build),build_sha256=digest,admission_review=str(review),admission_review_sha256=review_sha,runs=runs,levels=levels,files=pins,actual_workers_launched=launched,all_workers_terminal=True,all_bounded_readers_closed=closed,initializer_credit=0,current131_acceptance=False)
  (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])
