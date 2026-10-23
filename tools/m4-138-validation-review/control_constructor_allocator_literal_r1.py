"""Finite literal CRT fragments and rejected family/provenance controls."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];O=R/'reports/m4-138-validation-review/constructor-allocator-literal-controls-r1'
def need(v,m):
 if not v:raise ValueError(m)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 s=importlib.util.spec_from_file_location('constructor_allocator_controls',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
need(not O.exists(),'Fresh immutable control namespace')
m=load(R/'tools/m4-constructor-native/game_model_v4.py');p,c=m.source_program(R/'reports/m4-constructor-native/source-comparison-preparation-r1/report.json')
def machine():
 st=bytearray(3504)
 for a,v in [(m.I.REG['esp'],0x20001800),(m.I.REG['ebp'],0x12345678),(m.I.BASE['fs'],0x10000000),(2472,0x4103f0)]:struct.pack_into('<I',st,a,v)
 cpu=struct.pack('<10I',0,0,0,0,0x20001800,0x12345678,0,0,0x202,0x4103f0)
 mem={0x10000000:struct.pack('<I',0xffffffff)+bytes(4092),0x20001000:bytes(4096)}
 x=m.Machine(bytes(st),bytes(512),cpu,mem,program=copy.deepcopy(p),callbacks=c,owner_roles=[],source_imports={});x.begin_constructor(0x4103f0);return x
def fragment(x,start,end):
 x.cursor=start
 while x.cursor!=end:x.step()
def installed():
 x=machine();fragment(x,0x780012e3,0x78001300);return x
results=[]
for name,start,end,restore,finish in [('malloc',0x780012e3,0x78001300,0x78001367,0x78001371),('free',0x78001390,0x780013ad,0x78001416,0x78001420)]:
 x=machine();fragment(x,start,end);frame=x.constructor_FS[-1]['frame'];fragment(x,restore,finish);x.end_constructor()
 need(not x.constructor_FS and int.from_bytes(x.bytes(0x10000000,4),'little')==0xffffffff,'Exact source normal head restore')
 results.append(dict(name=name+'-normal-source-fragment',passed=True,events=x.constructor_FS_events,accesses=x.accesses,scope_frame=frame,full_root_execution=False))
def rejected(name,fn):
 try:fn()
 except ValueError as e:results.append(dict(name=name,passed=True,rejected=True,reason=str(e)));return
 raise ValueError('Negative control did not reject '+name)
def cross_family():
 x=installed();fragment(x,0x78001416,0x78001420)
def arbitrary():
 x=installed();x.word(2472,0x780012e4);x.write(0x10000000,0xffffffff)
def wrong_saved():
 x=installed();x.store_bytes(x.constructor_FS[-1]['frame'],struct.pack('<I',0xabcdef01));fragment(x,0x78001367,0x78001371)
def missing_push():
 x=machine();x.cursor=0x780012f9;x.step()
def unbalanced():installed().end_constructor()
def intervening():
 x=installed();x.cursor=0x78001367;x.step();x.accesses.append((0x780012e4,0x20001000,0,4,1));x.step()
for name,fn in [('cross-family-restore',cross_family),('arbitrary-provider-FS-write',arbitrary),('corrupt-saved-head',wrong_saved),('missing-source-read-push',missing_push),('unbalanced-scope',unbalanced),('intervening-access-before-restore',intervening)]:rejected(name,fn)
old=(R/'tools/m4-constructor-native/derive_source_v3.py').read_text();new=old.replace('game_model_v3.py','game_model_v4.py').replace('constructor_source_exact_v3','constructor_source_exact_v4')
need(new.replace('game_model_v4.py','game_model_v3.py').replace('constructor_source_exact_v4','constructor_source_exact_v3')==old,'Exact derivative inverse')
dp=R/'tools/m4-constructor-native/derive_source_v4.py';need(not dp.exists(),'Fresh derivation');ast.parse(new);dp.write_text(new)
O.mkdir(parents=True)
files={str(q):sha(q)for q in [Path(__file__),R/'tools/m4-constructor-native/game_model_v3.py',R/'tools/m4-constructor-native/game_model_v4.py',R/'tools/m4-constructor-native/derive_source_v3.py',dp,R/'reports/m4-138-validation-review/constructor-allocator-literal-preparation-r1/report.json']}
d=dict(passed=True,scope='Finite own synthetic BEFORE literal CRT source fragments; no actual root source equality',controls=results,positive_controls=2,negative_controls=6,exact_derivation_inverse=True,inherited_semantics_preserved=True,source_AFTER_seed=False,whole_source_comparison_pending=True,input_adapter_pending=True,archive_reader_opened=False,native_executed=False,initializer_credit=0,files=files)
q=O/'report.json';q.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(passed=True,report=str(q),sha256=sha(q))))
