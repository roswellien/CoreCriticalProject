"""Bounded synthetic journal/FS/index/projection controls, no source execution."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,types
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'tools/m4-native141-source'),str(R/'tools/m4-lockit-source'),str(R/'tools/m4-container-review')]
s=importlib.util.spec_from_file_location('observer141_final_preflight',R/'tools/m4-native141-source/final_observer141_v5.py');F=importlib.util.module_from_spec(s);s.loader.exec_module(F)
from constructor_journal141_v2 import Association
from constructor_fs_union141_v1 import partition
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-141-consumer-review/observer-controls-r1';assert not out.exists();out.mkdir(parents=True);checks=[]
 def reject(label,fn):
  try:fn()
  except (ValueError,AssertionError):checks.append(label);return
  raise AssertionError('Expected refusal '+label)
 class Fake:
  def __init__(self,files):self.entries=files
  def data(self,key):return self.entries[key]
 order=json.loads(F.ORDER_PATH.read_bytes());borrowed=[v['entry']for v in order if v['entry']in F.ROOTS+F.WIDGETS];names=['registry-bootstrap-before']
 for root in borrowed:
  if root in F.ROOTS:
   for _ in range(3 if root in F.ROOTS[:2]else 2):names+=['constructor-mfc-before','constructor-mfc-after']
  names+=['widget-onexit-before','widget-onexit-after']
 files={f'sequence-0/cleaned/registry-checkpoint-{n}-name.bin':v.encode()for n,v in enumerate(names)};idx=F.checkpoint_index(Fake(files),'sequence-0/cleaned/');assert len(idx)==37;checks.append('complete37 unique current aliases')
 reject('duplicate ordinary checkpoint',lambda:F.checkpoint_index(Fake({**files,'sequence-0/cleaned/registry-checkpoint-37-name.bin':b'registry-bootstrap-before'}),'sequence-0/cleaned/'))
 projections=[(9,r,0x5ac11e,0x5bb52c,0x1decb0,0x78004a36,0x200017e8,0x5ac124)for r in borrowed]
 calls=[(11,r,pc,thunk,0x5bb4bc if thunk==0x5abd26 else 0x5bb4c8,0x80000337 if thunk==0x5abd26 else 0x80000339,0x20001790,pc+5)for (r,pc),(thunk,size)in F.SITES.items()]
 F.S.CURRENT=types.SimpleNamespace(constructor_projections=[r for r in projections if r[1]in F.ROOTS],constructor_call_rows=calls)
 encode=lambda rows:b''.join(struct.pack('<8I',*r)for r in rows)
 assert F.prove_constructor_projections(None,encode(projections+calls))==encode([r for r in projections if r[1]not in F.ROOTS]+calls);checks.append('exact three projection extraction with eight fullMFC joins')
 reject('temporal borrowed permutation',lambda:F.prove_constructor_projections(None,encode([projections[1],projections[0]]+projections[2:]+calls)))
 reject('extra MFC projection',lambda:F.prove_constructor_projections(None,encode(projections+calls+[calls[0]])))
 class M:
  def __init__(self):self.accesses=[(1,2,3,4,0)];self.responses=types.SimpleNamespace(allocations=[]);self.esp=0x200017f0;self.mem={self.esp:struct.pack('<I',0x58af17)};self.hook=None
  def reg(self,k):assert k=='esp';return self.esp
  def word(self,k):assert k==2168;return 0x7ffde000
  def bytes(self,a,n):return self.mem[a][:n]
 m=M();o=types.SimpleNamespace(constructor_game_FS_serial=0);full=m.accesses;hookviews=[]
 def hook(machine,event,d):assert machine.accesses is not full;hookviews.append(list(machine.accesses))
 m.hook=hook;association=Association(m,o,F.ROOTS[0])
 def operand(row):
  full.append(row);association.observer_hook(m,'write-after'if row[4]else'read-after',dict(domain='source',pc=row[0],address=row[1],value=row[2],bytes=row[3]));assert m.accesses is full and full[-1]==row
 operand((0x58af12,m.esp,0x58af17,4,1));association.observer_hook(m,'control',dict(op='call',site=0x58af12,target=0x5abd26))
 operand((0x5abd26,0x5bb4bc,0x80000337,4,0));operand((0x5f401edd,m.esp,0x58af17,4,0));frame=m.esp;m.esp+=4;association.observer_hook(m,'returned',dict(caller=(0x5f401ea0,),frame=frame))
 operand((0x41040b,m.esp,0x410a80,4,0));proof=association.finish();assert len(proof['whole_literal_source_accesses'])==4 and len(proof['component_source_accesses'])==2 and len(proof['provider_source_accesses'])==3 and len(proof['shared_source_accesses'])==1;assert m.accesses==[(1,2,3,4,0)]+[tuple(r)for r in proof['provider_source_accesses']];checks.append('full source chronology retained through every guard; exact shared union4=2+3-1')
 bad=M();badassoc=Association(bad,o,F.ROOTS[0]);badassoc.component=[(0x58af12,bad.esp,0,4,1)];reject('wrong shared literal CALL row',lambda:badassoc.observer_hook(bad,'control',dict(op='call',site=0x58af12,target=0x5abd26)))
 frames=[];records=[];observations=[];specs=json.loads((R/'reports/m4-startup141-runway/service-preparation-r2/constructor-FS-contracts.json').read_bytes())['frames']
 for i in range(35):
  isnew=i in(2,5,9,14,21,27,33);f=[0]*32;f[0]=1;f[2]=F.ROOTS[len(observations)//9%3]if isnew else 0x4e78d0
  if isnew:
   spec=specs[len(observations)//3%len(specs)];addr=0x20001080+16*i;f[3]=spec['entry'];f[5]=addr+12;f[7]=spec['read'];f[8]=0xffffffff;f[10]=spec['handler'];f[11]=0xffffffff;raw=struct.pack('<3I',0xffffffff,spec['handler'],0xffffffff).hex()
   observations+=[dict(root=f[2],PC=spec['read'],kind=0,group_entry=spec['entry'],entry_ESP=f[5],before_head=0xffffffff,handler=spec['handler']),dict(root=f[2],PC=spec['install'],kind=1,record_address=addr,record_hex=raw),dict(root=f[2],PC=spec['restore'],kind=2,record_address=addr,record_hex=raw)]
  frames.append(tuple(f))
  for point in(81,84):
   r=[0]*16;r[0]=1;r[2]=i;r[3]=f[2];r[4]=point
   if isnew:r[5]=spec['install']if point==81 else spec['restore'];r[6]=addr;r[7]=12;r[8:11]=[0xffffffff,spec['handler'],0xffffffff]
   records.append(tuple(r))
 def fsarchive(f,r):return Fake({'fs-frame-witnesses.bin':b''.join(struct.pack('<32Q',*v)for v in f),'fs-record-bytes.bin':b''.join(struct.pack('<16Q',*v)for v in r)})
 observer=types.SimpleNamespace(constructor_FS_observations=observations);old,raw=partition(fsarchive(frames,records),'',observer,F.ROOTS);assert len(old)==28 and len(raw)==56 and len(observer.constructor_FS_partition['constructor_source_joins'])==14;checks.append('all35 frames/all70raw observations partitioned with exact14 source12B joins')
 mutated=list(records);j=next(i for i,r in enumerate(mutated)if r[3]in F.ROOTS);r=list(mutated[j]);r[9]^=1;mutated[j]=tuple(r);reject('mutated constructor frame byte',lambda:partition(fsarchive(frames,mutated),'',observer,F.ROOTS))
 reject('missing raw12 observation',lambda:partition(fsarchive(frames,records[:-1]),'',observer,F.ROOTS))
 mutated=list(records);r=list(mutated[j]);r[2]=0;mutated[j]=tuple(r);reject('wrong physical frame owner',lambda:partition(fsarchive(frames,mutated),'',observer,F.ROOTS))
 mutated=list(frames);r=list(mutated[0]);r[13]=3;mutated[0]=tuple(r);reject('legacy parent references removed ctor',lambda:partition(fsarchive(mutated,records),'',observer,F.ROOTS))
 pins={str(p.resolve()):sha(p)for p in(Path(__file__),Path(F.__file__),F.PREP/'report.json',F.PREP/'final_observer141_parent.py',F.PREP/'final_observer141_parent_v2.py',R/'tools/m4-native141-source/constructor_journal141_v2.py',R/'tools/m4-native141-source/constructor_fs_union141_v1.py',R/'tools/m4-native141-source/constructor_native_outputs141_v2.py',F.ORDER_PATH)}
 (out/'report.json').write_text(json.dumps(dict(passed=True,checks=checks,source_machine_executed=False,native_executed=False,canonical_reader_opened=False,actual_semantics_or_ownership_claim=False,files=pins),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main()
