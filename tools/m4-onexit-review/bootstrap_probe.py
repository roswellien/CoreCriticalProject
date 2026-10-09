"""Development probe of the independent bridge on saved finite bootstrap facts."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-onexit-review'))
import provider_bridge as P
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(capture,name):
 out=ROOT/'reports/m4-onexit-review'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or v==h,(str(p),h,v);pins[str(p)]=v;return p
 G=load('onexit_probe_game',pin(ROOT/'tools/m4-onexit-source/game_model.py'));D=load('onexit_probe_direct',pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'))
 a=D.DirectSet(capture,pin);stem='sequence-0/selected/';checkpoints={}
 try:
  for logical in a.entries:
   if logical.startswith(stem+'registry-checkpoint-')and logical.endswith('-name.bin'):
    checkpoints[a.data(logical).decode()]=logical[:-9]
  def checkpoint(name):
   prefix=checkpoints[name];memory={int(logical[len(prefix)+6:-4]):a.data(logical)for logical in a.entries if logical.startswith(prefix+'-page-')}
   return dict(state=a.data(prefix+'-state.bin'),fx=a.data(prefix+'-fx.bin'),cpu=a.data(prefix+'-cpu.bin'),runtime_cpu=a.data(prefix+'-runtime-cpu.bin'),memory=memory)
  before=checkpoint('registry-bootstrap-before');facts=[]
  contracts=dict(P.R.B.contracts(),**{})
  contracts.update(P.R.NEW_CONTRACTS)
  for index in range(a.words(stem+'locale-summary.bin',32)[18]):
   p=stem+'locale-api-'+str(index);w=a.words(p+'-witness.bin',32,'Q');inputs=[];outputs=[]
   for suffix,target in (('input',inputs),('output',outputs)):
    k=0
    while p+'-'+suffix+'-'+str(k)+'.bin'in a.entries:target.append(a.data(p+'-'+suffix+'-'+str(k)+'.bin'));k+=1
   if w[31]:name_='HeapFree'if w[3]==0x7802e090 else'LeaveCriticalSection'if w[3]==0x7802e048 else'DeleteCriticalSection'
   else:name_=contracts[w[2]]['name']
   fact=dict(words=w,inputs=inputs,outputs=outputs,name=name_,buffers=list(struct.iter_unpack('<4I',a.data(p+'-buffers.bin'))))
   facts.append(fact)
  heap=dict(create=a.words(stem+'heap-create-witness.bin',16,'Q'),registry=a.words(stem+'heap-create-registry.bin',18,'Q'),query=a.words(stem+'heap-query-witness.bin',20,'Q'),input=a.data(stem+'heap-query-input.bin'),output=a.data(stem+'heap-query-output.bin'))
  projections=list(struct.iter_unpack('<8I',a.data(stem+'registry-research-projections.bin')));assert projections[0][0]==1
  static=out/'static';static.mkdir();material=P.material(static,pin);program,callbacks=G.source_program()
  machine,responses=P.bootstrap(before,facts,heap,material,G.Machine,program,callbacks,projections[0][1],projections[0][2])
  actual=checkpoint('registry-bootstrap-returned');fields=[('state',bytes(machine.state),actual['state']),('FX',machine.fx,actual['fx']),('CPU',machine.cpu,actual['cpu'])]
  fields += [('page-'+hex(p),machine.bytes(p,len(raw)),raw)for p,raw in actual['memory'].items()]
  for name_,expected,observed in fields:
   diffs=[(i,x,y)for i,(x,y)in enumerate(zip(expected,observed))if x!=y]
   assert len(expected)==len(observed)
   print(name_,len(expected),'diffs',len(diffs),diffs[:20])
  print('API',responses.index,'phases',len(machine.phases))
 finally:a.close()
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2])
