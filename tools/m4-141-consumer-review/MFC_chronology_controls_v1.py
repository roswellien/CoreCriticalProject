"""Narrow synthetic source-event controls; no archive or source worker."""
from pathlib import Path
import importlib.util,json,struct,hashlib,types,copy
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-native141-source/mfc_chronology141_v1.py'
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
  owner=dict(guest=0x31010000+index*16,acquired=0xdead000000+index,generation=index+1,extent=16,kind=4,requested=request,live=True);m.responses.allocations.append(owner);m.r['eax']=owner['guest']
  h.constructor(o,m,'returned',dict(caller=(0x780012b3,),frame=0x200018e8));h.constructor(o,m,'returned',dict(caller=(0x5f401ea0,),frame=0x20001900))
  r=c['source_record'];o.constructor_mfc.append(r);w=r['words']
  expected=[1,index,0,0x5f401ea0,site,0x20001900,site+5,request,0x78001498,0x780012b3,0x5f401ea1,0x5f401eb5,0x200018e8,request,0x5f401ead,0xffffffff,owner['guest'],owner['acquired'],owner['generation'],16,owner['guest'],1,0x12345678,0,0,0,0,0,0,0,0,0]
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
 out=R/'reports/m4-141-consumer-review/MFC-chronology-controls-r1';out.mkdir()
 report=dict(passed=True,controls=len(checks),checks=checks,helper_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source_actual_executed=False,canonical_reader_opened=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report=str(out/'report.json'),sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest())))
if __name__=='__main__':run()
