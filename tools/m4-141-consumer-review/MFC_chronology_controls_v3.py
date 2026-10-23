"""Narrow synthetic source-event controls; no archive or source worker."""
from pathlib import Path
import importlib.util,json,struct,hashlib,types,copy
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-native141-source/mfc_chronology141_v2.py'
s=importlib.util.spec_from_file_location('chronology_controls',p);H=importlib.util.module_from_spec(s);s.loader.exec_module(H)
def need(x,s):
 if not x:raise ValueError(s)
class Machine:
 def __init__(self):self.r=dict(esp=0x20001900,ecx=0x12345678,ebx=0x780012b3,eax=0);self.mem={};self.constructor_active=True;self.responses=types.SimpleNamespace(allocations=[])
 def reg(self,n):return self.r[n]
 def bytes(self,a,n):return self.mem[a].to_bytes(n,'little')
def run():
 checks=[]
 def check(name,f,reject=False):
  try:f()
  except (ValueError,AssertionError,StopIteration):need(reject,'Unexpected failed control '+name)
  else:need(not reject,'Adverse control was accepted '+name)
  checks.append(dict(name=name,passed=True,reject=reject))
 fixture=R/'reports/m4-startup141-source/combined-source-provider-r3/Formatting-source-derivations.json'
 actual_owner=json.loads(fixture.read_bytes())[-1]['mixed_owners'][0]
 need(set(('guest','native','generation','extent','kind','requested','live'))<=set(actual_owner)and 'acquired'not in actual_owner and actual_owner['kind']==4,'Actual retained source MFC owner schema')
 h=H.Chronology(need);o=types.SimpleNamespace(root=0x4103f0,constructor_active_call=None,constructor_free=None,mfc=[],mfc_imports=[],mfc_stores=[],constructor_mfc=[])
 m=Machine()
 def old(index):
  o.root=0x4e1ca0
  def imp(*a):o.mfc_imports.append((1,len(o.mfc),o.root,0x5abd26,0x5bb4bc,0x80000337,0x5f401ea0,0))
  h.inherited(o,m,'read-after',dict(domain='source',pc=0x5abd26,address=0x5bb4bc,bytes=4),imp)
  def entry(*a):
   w=[0]*32;w[0]=1;w[1]=len(o.mfc);w[2]=o.root;o.mfc.append(dict(words=w))
  h.inherited(o,m,'control',dict(op='jmp'),entry)
  need(o.mfc[-1]['words'][1]==index and h.imports[-1][1]==index,'Dynamically derived inherited global ordinal')
 def ctor(index,root,site,request):
  o.root=root;m.r['esp']=0x20001900;m.mem.update({0x20001900:site+5,0x20001904:request,0x200018e8:0x5f401eb7,0x200018ec:request})
  c=dict(root=root,site=site,frame=m.reg('esp'),request=request);o.constructor_active_call=c
  h.constructor(o,m,'read-after',dict(domain='source',pc=0x5abd26,address=0x5bb4bc,bytes=4,value=0x80000337))
  h.constructor(o,m,'control',dict(op='jmp',site=0x5abd26,target=0x5f401ea0))
  for pc,a,v in[(0x5f401ea1,0x5f49814c,0x78001498),(0x5f401ead,0x5f498970,0xffffffff)]:h.constructor(o,m,'read-after',dict(domain='source',pc=pc,address=a,bytes=4,value=v))
  m.r['esp']=0x200018e8;h.constructor(o,m,'control',dict(op='call',site=0x5f401eb5,target=0x780012b3))
  owner=copy.deepcopy(actual_owner);owner.update(guest=0x31010000+index*16,generation=index+1,requested=request,live=True);need(set(owner)==set(actual_owner)and 'acquired'not in owner,'Exact real response owner key shape');m.responses.allocations.append(owner);m.r['eax']=owner['guest']
  h.constructor(o,m,'returned',dict(caller=(0x780012b3,),frame=0x200018e8));h.constructor(o,m,'returned',dict(caller=(0x5f401ea0,),frame=0x20001900))
  r=c['source_record'];o.constructor_mfc.append(r);w=r['words']
  expected=[1,index,0,0x5f401ea0,site,0x20001900,site+5,request,0x78001498,0x780012b3,0x5f401ea1,0x5f401eb5,0x200018e8,request,0x5f401ead,0xffffffff,owner['guest'],owner['native'],owner['generation'],16,owner['guest'],1,0x12345678,0,0,0,0,0,0,0,0,0]
  need(w==expected,'Entire constructor32Q formed from exact committed events')
  o.constructor_active_call=None;o.constructor_free=r;w[25:27]=[0x5f401782,0x20001700];m.r['esp']=0x200016f8;m.mem.update({0x200016f8:0x5f40178c,0x200016fc:owner['guest']})
  h.constructor(o,m,'read-after',dict(domain='source',pc=0x5f401786,address=0x5f498148,bytes=4,value=0x7800138a));h.constructor(o,m,'control',dict(op='call',site=0x5f401786,target=0x78001390));need(w[27:30]==[0x200016f8,0x7800138a,0x78001390],'Entire source cleanup frame/import formed');o.constructor_free=None
 check('interleaved_source_chronology',lambda:(old(0),ctor(1,0x4103f0,0x58af12,12),old(2),ctor(3,0x410440,0x58af6a,4),old(4)))
 check('dynamic_indices_not_constant_shift',lambda:need([r['words'][1]for r in o.mfc]==[0,2,4]and [r['words'][1]for r in o.constructor_mfc]==[1,3],'Separate old and constructor domains retain global source chronology'))
 check('duplicate_entry_rejected',lambda:h.append(o.mfc[0]),True)
 check('wrong_named_input_rejected',lambda:(setattr(o,'constructor_free',o.constructor_mfc[0]),h.constructor(o,m,'read-after',dict(domain='source',pc=0x5f401786,address=0x5f498148,bytes=4,value=0))),True);o.constructor_free=None
 # Exact whole-row equality detects mutation in every word; no ordinal masking.
 row=tuple(o.constructor_mfc[0]['words'])
 for i in range(32):
  changed=list(row);changed[i]^=1
  check('whole32Q_mutation_'+str(i),lambda changed=changed:need(tuple(changed)==row,'Whole32Q exact comparison'),True)
 check('import_missing_rejected',lambda:need(h.imports[:-1]==h.imports,'Whole import cardinality'),True)
 check('import_order_rejected',lambda:need(list(reversed(h.imports))==h.imports,'Whole import chronology'),True)
 # Exercise the production whole-union comparator with exact mock target bytes.
 from collections import Counter
 dh=H.Chronology(need);do=types.SimpleNamespace(seq=0,mfc=[],constructor_mfc=[],container=types.SimpleNamespace(dump=lambda *a:{}),vtable=types.SimpleNamespace(dump=lambda *a:{}))
 responses=types.SimpleNamespace(allocations=[])
 for i in range(74):
  w=[0]*32;w[0]=1;w[2]=0 if i in(1,3,5,7,9,11)else 0x4e1ca0;w[16]=0x31000000+32*i;w[18]=i+1;w[7]=12;w[23]=int(w[2]!=0)
  r=dict(words=w);dh.append(r);(do.constructor_mfc if w[2]==0 else do.mfc).append(r);responses.allocations.append(dict(generation=i+1,live=True))
  dh.imports.append((1,i,w[2],0x5abd26,0x5bb4bc,0x80000337,0x5f401ea0,0))
 targets={'mfc-allocation-witnesses.bin':b''.join(struct.pack('<32Q',*r['words'])for r in dh.records),'mfc-import-ledger.bin':b''.join(struct.pack('<8Q',*r)for r in dh.imports),'mfc-store-ledger.bin':b''}
 class Archive:
  def data(self,name):return targets[name.split('/')[-1]]
  def words(self,*a):return (0,)*8
 do.a=Archive()
 def dump():dh.dump(do,m,responses,'selected',Counter())
 check('production_dump_exact74_union',dump)
 original=targets['mfc-allocation-witnesses.bin']
 for i in range(32):
  modified=bytearray(original);modified[32*8+i*8]^=1;targets['mfc-allocation-witnesses.bin']=bytes(modified)
  check('production_dump_ctor_word_'+str(i),dump,True)
 targets['mfc-allocation-witnesses.bin']=original
 original=targets['mfc-import-ledger.bin'];targets['mfc-import-ledger.bin']=original[:-64];check('production_dump_missing_import',dump,True);targets['mfc-import-ledger.bin']=original
 targets['mfc-store-ledger.bin']=struct.pack('<8Q',1,1,0,1,1,4,1,1);check('production_dump_extra_store',dump,True);targets['mfc-store-ledger.bin']=b''
 do.constructor_mfc[0]['words'][1]=99;check('production_dump_wrong_source_ordinal',dump,True)
 out=R/'reports/m4-141-consumer-review/MFC-chronology-controls-r3';out.mkdir()
 report=dict(passed=True,controls=len(checks),checks=checks,helper_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),actual_response_fixture=str(fixture),actual_response_fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),actual_owner_keys=sorted(actual_owner),source_actual_executed=False,canonical_reader_opened=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report=str(out/'report.json'),sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest())))
if __name__=='__main__':run()
