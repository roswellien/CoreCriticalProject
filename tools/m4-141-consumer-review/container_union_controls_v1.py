"""Bounded source-event observer controls, never a source-execution receipt."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,struct,types
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main():
 out=R/'reports/m4-141-consumer-review/container-union-controls-r1';out.mkdir();files={};checks=[]
 def pin(p):
  p=Path(p).resolve();files[str(p)]=sha(p);return p
 source=pin(R/'tools/m4-native141-source/container_events141_v1.py');spec=importlib.util.spec_from_file_location('finite_container141',source);E=importlib.util.module_from_spec(spec);spec.loader.exec_module(E)
 proof=json.loads(pin(R/'reports/m4-startup141-source/combined-source-provider-r5/Constructor-carried-source-derivations.json').read_bytes())
 diagnostic=R/'reports/m4-141-consumer-review/root-container-diagnostic-r1';pin(diagnostic/'report.json');actual=json.loads(pin(diagnostic/'rows.json').read_bytes())
 class Machine:
  def __init__(self,row):
   self.constructor_active=True;self.responses=types.SimpleNamespace(generation=41,index=26,allocations=[dict(live=True)]*9);self.accesses=[None]*100;self.mem={};self.eax=0;self.sp=row['constructor_call_results'][-1][3];self.call_stack=[(0x5abd1a,self.sp,0,0x58af9a)]
  def reg(self,n):return {'esp':self.sp,'eax':self.eax,'ecx':0}[n]
  def bytes(self,a,n):return bytes(self.mem.get(a+i,0)for i in range(n))
  def put(self,a,value,n=4):
   for i,b in enumerate(value.to_bytes(n,'little')):self.mem[a+i]=b
 def run(row,mutation=None):
  root=row['root'];call=row['constructor_call_results'][-1];need(call[1:6]==[0x58af9a,0x5abd1a,call[3],0x58af9f,0],'Actual source constructor NULL frame fixture')
  o=types.SimpleNamespace(root=root,container_tail_projections=0,constructor_active_call=dict(root=root,site=call[1],thunk=call[2],frame=call[3],ret=call[4],request=0))
  m=Machine(row);events=E.ContainerEvents(o,[],[],[]);events.nulls=[]
  p=row['provider_source_accesses'];first=next(i for i,z in enumerate(p)if z[0]==0x5abd1a);rows=p[first:first+25];need(rows[-1][0]==0x5f40178d,'Complete retained source NULL provider return operand')
  # Initial values come only from retained source operands/frame. Counters deliberately synthetic.
  m.put(m.sp,call[4]);m.put(m.sp+4,0);head=next(z[2]for z in rows if z[0]==0x7800139f);m.put(0x7ffde000,head)
  for i,z in enumerate(rows):
   pc,a,v,n,write=z;d=dict(domain='source',pc=pc,address=a,value=v,bytes=n)
   if mutation==('raw',i):d['value']^=1
   if write:m.put(a,v,n)
   else:
    # A fixture read is an actual source operand; a prior committed fixture write must agree.
    if all(a+j in m.mem for j in range(n)):need(int.from_bytes(m.bytes(a,n),'little')==v,'Retained source operand agrees with its committed frame/FS writes')
    else:m.put(a,v,n)
   m.accesses.append(tuple(z));events.event(m,'write-after'if write else'read-after',d)
   if i==0:
    events.event(m,'control',dict(op='jmp',site=0x5abd1a,target=0x5f401782))
   if pc==0x5f401786 and write:
    m.sp=a;events.event(m,'control',dict(op='call',site=pc,target=0x78001390))
   if pc==0x78001424:
    m.eax=head;events.event(m,'returned',dict(caller=(0x78001390,),frame=call[3]-8,site=pc))
   if pc==0x5f40178d:
    m.sp=call[3]+4;m.eax=call[6];events.event(m,'returned',dict(caller=(0x5f401782,),frame=call[3],site=pc))
  need(events.null_active is None and events.constructor_null_roots==[root],'Whole source NULL frame closed with exact logical root')
  w=events.nulls[0];expected=[1,0,0,0x58af9a,0x5f401782,call[3],0x58af9f,0,0x80000339,0x5abd1a,41,0x78001390,call[3]-8,0x5f40178c,0x7800138a,0x5f401786,0x78001390,1,1,head,head,head,head,26,26,9,9,101,125,head,call[6],41]
  need(w==expected,'All32 source-event fields with independent counterfactual API/generation/live metadata')
  need(events.imports==[(1,0,0,0x5abd1a,0x5bb4c8,0x80000339,0x5f401782,825),(1,1,0,0x5f401786,0x5f498148,0x7800138a,0x78001390,0)],'Whole two source raw-first import rows')
  return w
 for row in proof[:2]:run(row);checks.append(dict(passed=True,name=hex(row['root'])+' full32 source-event counterfactual fixture'))
 for index in(0,3):
  try:run(proof[0],('raw',index))
  except ValueError:checks.append(dict(passed=True,name='reject raw input mutation '+str(index)))
  else:raise AssertionError('Mutation accepted')
 # Production whole-array comparison extracted unchanged. Native arrays are only comparison controls.
 tree=ast.parse(source.read_text());cl=next(x for x in tree.body if isinstance(x,ast.ClassDef));dump=next(x for x in cl.body if isinstance(x,ast.FunctionDef)and x.name=='dump');loop=next(x for x in dump.body if isinstance(x,ast.For));compare=ast.unparse(loop)
 def joins(rows):
  ns=dict(struct=struct,need=need,stem='sequence-0/selected/',stage='selected',self=types.SimpleNamespace(nulls=rows['container-nullfree-witnesses.bin'],borrowed=rows['container-borrowed-witnesses.bin'],imports=rows['container-import-ledger.bin'],stores=rows['container-vector-stores.bin']),a=types.SimpleNamespace(data=lambda k:(diagnostic/k.split('/')[-1]).read_bytes()))
  exec(compile(compare,'actual_production_whole_arrays','exec'),ns)
 names=['container-nullfree-witnesses.bin','container-borrowed-witnesses.bin','container-import-ledger.bin','container-vector-stores.bin'];rows={n:actual['sequence-0/selected/'+n]for n in names}
 for n in names:pin(diagnostic/n)
 joins(rows);checks.append(dict(passed=True,name='unchanged production complete arrays equality on actual diagnostic shapes'))
 for n in names:
  for field in range(len(rows[n][0])):
   changed=copy.deepcopy(rows);changed[n][0][field]^=1
   try:joins(changed)
   except ValueError:checks.append(dict(passed=True,name='reject '+n+' field '+str(field)))
   else:raise AssertionError('Whole-field mutation accepted')
  for operation in('missing','extra'):
   changed=copy.deepcopy(rows)
   if operation=='missing':changed[n].pop()
   else:changed[n].append(changed[n][-1])
   try:joins(changed)
   except ValueError:checks.append(dict(passed=True,name='reject '+n+' '+operation))
   else:raise AssertionError('Whole cardinality mutation accepted')
 pin(__file__);report=dict(passed=True,controls=len(checks),checks=checks,source_event_counterfactual_controls=True,actual_diagnostic_comparator_controls_only=True,source_API_generation_live_counters_synthetic=True,actual_source_equivalence_claim=False,AFTER_seed=False,canonical_reader_opened=False,worker_launched=False,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(out/'report.json'),sha256=sha(out/'report.json'),controls=len(checks))))
if __name__=='__main__':main()
