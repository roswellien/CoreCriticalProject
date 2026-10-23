"""Pure finite-contract controls only; no capture reader/source execution."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys
R=Path(__file__).resolve().parents[2];P=R/'reports/m4-original141-fp-review/source-preparation-r1';sys.dont_write_bytecode=True
def main(out):
 assert not out.exists();out.mkdir(parents=True)
 s=importlib.util.spec_from_file_location('finite_env_control',P/'finite_env_contract_v1.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);e=m.EXPECTED
 b={**e['identity'],'header':e['before_header'],'CPU':e['before_CPU'],'arguments':e['arguments'],'ENV28_hex':e['before_ENV28_hex'],'FX512_hex':e['FX512_hex'],'side':'entry'}
 own=bytes.fromhex(b['ENV28_hex']);a={**b,'index':37,'header':e['after_header'],'CPU':e['after_CPU'],'side':'first-source-return','ENV28_hex':(own[:12]+bytes(14)+own[26:]).hex()}
 assert m.predict(b,a,own,m.VALIDATION_SHA,m.WRAPPER_SHA,0)==(own[:12]+bytes(14)+own[26:],1,True)
 controls=[]
 def bad(label,mutate,env=own,v=m.VALIDATION_SHA,w=m.WRAPPER_SHA,seen=0):
  x,y=copy.deepcopy(b),copy.deepcopy(a);mutate(x,y)
  try:m.predict(x,y,env,v,w,seen)
  except ValueError:controls.append(label);return
  raise AssertionError('Refused adverse '+label)
 def flip(h,pos):
  v=bytearray.fromhex(h);v[pos]^=1;return v.hex()
 for i in range(28):bad('output-byte-'+str(i),lambda x,y,i=i:y.update(ENV28_hex=flip(y['ENV28_hex'],i)))
 bad('whole-FX',lambda x,y:y.update(FX512_hex=flip(y['FX512_hex'],400)))
 bad('arguments',lambda x,y:x['arguments'].__setitem__(0,0))
 bad('CPU-frame',lambda x,y:x['CPU'].__setitem__(4,0))
 bad('API-target',lambda x,y:x['header'].__setitem__(7,0))
 bad('unlisted-sequence',lambda x,y:x.update(sequence=1))
 bad('unlisted-index',lambda x,y:x.update(index=38))
 bad('repeat',lambda x,y:None,seen=1)
 bad('validation-pin',lambda x,y:None,v='0'*64)
 bad('wrapper-pin',lambda x,y:None,w='0'*64)
 bad('source-own-before',lambda x,y:None,env=bytes(28))
 x,y=copy.deepcopy(b),copy.deepcopy(b);x['index']=y['index']=0
 assert m.predict(x,y,own,m.VALIDATION_SHA,m.WRAPPER_SHA,0)==(own,0,False)
 files={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in (P/'report.json',P/'finite_env_contract_v1.py',Path(__file__).resolve())}
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,pure_positive_controls=2,adverse_controls=controls,source_evaluated=False,archive_reader_opened=False,acceptance_credit=0,files=files),indent=2)+'\n');print(str(q))
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
