"""Bounded synthetic/adverse own-memory controls; no retained payload reader."""
from pathlib import Path
import copy,hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];p=R/'tools/m4-138-controls-review/widget_byteflow.py';spec=importlib.util.spec_from_file_location('bounded_widget_byteflow_controls',p);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
def digest(b):return hashlib.sha256(b).hexdigest()
data={};before=b'\x01\0\0\0'+bytes(28);after=b'\x02\0\0\0'+bytes(28);tib=struct.pack('<5I',0x7ffde000,0xffffffff,0x20002000,0x20001000,0x7ffde000)
for stem,raw in(('before/',before),('after/',after)):
 data[stem+'game-region-4194304.bin']=raw;data[stem+'stack.bin']=bytes(4096);data[stem+'TIB.bin']=tib
data['sequence-0/phase-15-before-page-2013483008.bin']=bytes(4096)
geometry=dict(whole_State_bytes=3504,whole_CPU_bytes=40,whole_FX_bytes=512,whole_stack_bytes=4096,provider_pages=[],source_equality_only=True)
row=dict(sequence=0,whole_carried_before=dict(geometry,prefix='before/',Game_regions=[[0x400000,32,digest(before)]]),whole_carried_after=dict(geometry,prefix='after/',Game_regions=[[0x400000,32,digest(after)]]),borrowed_provider=dict(callback=0x40e420),source_accesses=[[0x400100,0x400000,1,4,0],[0x400104,0x400000,2,4,1],[0x400108,0x400000,2,4,0],[0x78004a67,0x31000038,0x40e420,4,1]])
cases=[]
def check(name,r,values,expected):
 try:M.verify(r,values.__getitem__,15);passed=True
 except(ValueError,KeyError):passed=False
 assert passed==expected,(name,passed);cases.append(dict(name=name,expected_pass=expected,observed_pass=passed))
check('positive complete own BEFORE read/write/endpoints',row,data,True)
for name,index,value in [('read witness cannot initialize missing bytes',0,3),('write cannot bypass endpoint comparison',1,3),('callback value must be literal current callback',3,0x40e421)]:
 r=copy.deepcopy(row);r['source_accesses'][index][2]=value;check(name,r,data,False)
r=copy.deepcopy(row);r['source_accesses'][0][1]=0x600000;check('unowned read rejected',r,data,False)
r=copy.deepcopy(row);r['source_accesses'][1][1]=0x600000;check('arbitrary unknown write rejected',r,data,False)
r=copy.deepcopy(row);r['whole_carried_before']['source_equality_only']=False;check('unauthenticated BEFORE denied',r,data,False)
r=copy.deepcopy(row);r['source_accesses'].append(r['source_accesses'][-1]);check('duplicate registry callback store denied',r,data,False)
v=dict(data);v['before/game-region-4194304.bin']=bytes(32);check('whole BEFORE hash mismatch denied',row,v,False)
v=dict(data);v['after/game-region-4194304.bin']=bytes(32);check('AFTER cannot seed memory',row,v,False)
out=R/'reports/m4-138-controls-review/source6-widget-byteflow-preflight-r1';assert not out.exists();out.mkdir(parents=True)
files={str(q.resolve()):digest(q.read_bytes())for q in(p,Path(__file__))};r=dict(passed=True,scope='10 bounded synthetic/adverse pure memory byteflow controls; actual84 source exports not read',cases=cases,files=files,archive_reader_opened=False,retained_payload_reader_opened=False,initializer_credit=0)
f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=digest(f.read_bytes()),cases=len(cases))))
