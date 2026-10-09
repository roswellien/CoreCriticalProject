"""Per-root BEFORE unit probe with independently carried provider ownership."""
from pathlib import Path
import copy,hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-onexit-review'))
import provider_bridge as P
import provider_capture as C
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(capture,name):
 out=ROOT/'reports/m4-onexit-review'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or v==h;pins[str(p)]=v;return p
 G=load('registration_probe_game',pin(ROOT/'tools/m4-onexit-source/game_model.py'));D=load('registration_probe_capture',pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'));a=D.DirectSet(capture,pin)
 try:
  stem='sequence-0/selected/';index=C.checkpoints(a,stem);before,facts,heap,oldpc,oldsp=C.bootstrap_inputs(a,stem,index);static=out/'static';static.mkdir();material=P.material(static,pin);program,callbacks=G.source_program()
  m,responses=P.bootstrap(before,facts,heap,material,G.Machine,program,callbacks,oldpc,oldsp)
  expected_callbacks=[];roots={r['entry']:r['registration']['callback']for r in json.loads((ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json').read_bytes())};done=0;state_failures=0
  while 'registry-root-'+str(done)+'-after'in index:
   label='registry-root-'+str(done);b=C.checkpoint(a,index,label+'-before');z=C.checkpoint(a,index,label+'-after')
   provider_before=copy.deepcopy(m.memory);owned_addresses=[allocation['guest']for allocation in responses.allocations if allocation['live']]
   for address,raw in b['memory'].items():
    if address>=0x78000000 or address in owned_addresses:assert m.bytes(address,len(raw))==raw,('Independent carried owner/provider BEFORE',done,hex(address))
   # Caller State/FX/stack/game pages are true unit BEFORE inputs. All provider
   # pages and privately owned allocation bytes retain independent prior effects.
   m.state=bytearray(b['state']);m.fx=b['fx'];m.cpu=b['runtime_cpu'];m.cursor=m.word(2472);m.phases={}
   for address,raw in b['memory'].items():
    if address<0x78000000 and address not in owned_addresses:m.memory[address]=bytearray(raw)
   entry=m.word(2472);frame=m.reg('esp');ret=int.from_bytes(m.bytes(frame,4),'little');assert entry in roots and frame==0x20001800 and ret==0x410a80
   m.call_stack.append((entry,frame,ret,0,m.reg('ebp'),m.reg('ebx'),m.reg('esi'),m.reg('edi'),0));m.run(stop=lambda x:x.cursor==ret,api=responses);assert not m.call_stack
   expected_callbacks.append(roots[entry]);responses.completed_registry(m,expected_callbacks)
   m.cpu=P.cpu(m.state)
   fields=[('State',bytes(m.state),z['state']),('FX',m.fx,z['fx']),('CPU',m.cpu,z['cpu'])]
   fields += [('page-'+hex(address),m.bytes(address,len(raw)),raw)for address,raw in z['memory'].items()]
   for tag,expected,observed in fields:
    diff=[(i,x,y)for i,(x,y)in enumerate(zip(expected,observed))if x!=y]
    assert len(expected)==len(observed)
    if tag=='State'and diff:
     print('State mismatch retained',done,hex(entry),len(diff),diff[:15],flush=True);state_failures+=1
    else:assert not diff,(done,hex(entry),tag,len(diff),diff[:15])
   print('Root',done,hex(entry),'APIcount',responses.index,'ownership/pages inspected',flush=True);done+=1
  print('Complete per-root units',done,'provider source instructions',len(m.PCs),'full State mismatches retained',state_failures)
 finally:a.close()
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2])
