"""Synthetic index/projection controls only; no source machine or raw readers."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,types
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'tools/m4-lockit-source'),str(R/'tools/m4-container-review')]
s=importlib.util.spec_from_file_location('observer141_preflight',Path(__file__).with_name('final_observer141_v1.py'));F=importlib.util.module_from_spec(s);s.loader.exec_module(F)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-native141-source/observer-preflight-r1';assert not out.exists();out.mkdir(parents=True);checks=[]
 class Fake:
  def __init__(self,names):self.names=names;self.entries={f'sequence-0/cleaned/registry-checkpoint-{n}-name.bin':v.encode()for n,v in enumerate(names)}
  def data(self,key):return self.entries[key]
 names=['registry-bootstrap-before'];order=json.loads(F.ORDER_PATH.read_bytes());borrowed=[v['entry']for v in order if v['entry']in F.ROOTS+F.WIDGETS]
 for root in borrowed:
  if root in F.ROOTS:
   for _ in range(3 if root in F.ROOTS[:2]else 2):names+=['constructor-mfc-before','constructor-mfc-after']
  names+=['widget-onexit-before','widget-onexit-after']
 idx=F.checkpoint_index(Fake(names),'sequence-0/cleaned/');assert len(idx)==len(names)==37;checks.append('positive complete37 checkpoint aliases')
 def reject(label,fn):
  try:fn()
  except (ValueError,AssertionError):checks.append(label);return
  raise AssertionError('Expected refusal '+label)
 reject('missing MFC after',lambda:F.checkpoint_index(Fake(names[:-3]+names[-2:]),'sequence-0/cleaned/'))
 reject('duplicate ordinary label',lambda:F.checkpoint_index(Fake(names+['registry-bootstrap-before']),'sequence-0/cleaned/'))
 reject('reversed MFC pair',lambda:F.checkpoint_index(Fake([{'constructor-mfc-before':'constructor-mfc-after','constructor-mfc-after':'constructor-mfc-before'}.get(n,n)for n in names]),'sequence-0/cleaned/'))
 projections=[(9,r,0x5ac11e,0x5bb52c,0x1decb0,0x78004a36,0x200017e8,0x5ac124)for r in borrowed]
 calls=[(11,r,pc,thunk,0x5bb4bc if thunk==0x5abd26 else 0x5bb4c8,0x80000337 if thunk==0x5abd26 else 0x80000339,0x20001790,pc+5)for (r,pc),(thunk,size)in F.SITES.items()]
 F.S.CURRENT=types.SimpleNamespace(constructor_projections=[r for r in projections if r[1]in F.ROOTS],constructor_call_rows=calls)
 def encode(rows):return b''.join(struct.pack('<8I',*r)for r in rows)
 raw=encode(projections+calls);retained=F.prove_constructor_projections(None,raw);assert retained==encode([r for r in projections if r[1]not in F.ROOTS]+calls);checks.append('exact source-derived3 removed retaining seven+eight')
 changed=list(projections+calls);i=next(i for i,r in enumerate(changed)if r[1]in F.ROOTS);row=list(changed[i]);row[6]+=4;changed[i]=tuple(row)
 reject('constructor wrong sourceframe',lambda:F.prove_constructor_projections(None,encode(changed)))
 reject('missing exact constructor projection',lambda:F.prove_constructor_projections(None,encode((projections+calls)[:i]+(projections+calls)[i+1:])))
 reject('extra tag11 projection',lambda:F.prove_constructor_projections(None,raw+encode([calls[0]])))
 reject('temporal tag9 permutation',lambda:F.prove_constructor_projections(None,encode([projections[1],projections[0]]+projections[2:]+calls)))
 pins={str(p.resolve()):sha(p)for p in(Path(__file__),Path(F.__file__),F.ORDER_PATH,F.PREP/'report.json',F.PREP/'final_observer141_parent.py',F.PREP/'final_observer141_parent_v2.py')}
 (out/'report.json').write_text(json.dumps(dict(passed=True,checks=checks,source_machine_executed=False,native_executed=False,canonical_reader_opened=False,raw_capture_used=False,actual141_semantics_claim=False,files=pins),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main()
