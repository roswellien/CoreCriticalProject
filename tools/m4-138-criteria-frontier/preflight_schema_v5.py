"""Inverse/negative current guarded CALL ownership controls only."""
from pathlib import Path
import json,hashlib,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prep=R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r4';pr=json.loads((prep/'report.json').read_bytes());out=prep.parent/'schema-synthetic-preflight-r3';assert not out.exists()
pins={str(prep/'report.json'):sha(prep/'report.json'),str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
for p,h in pr['files'].items():assert sha(Path(p))==h;pins[p]=h
s=(prep/'native-linked.py').read_text();inverse=s
for c in reversed(pr['changes']):assert inverse.count(c['after'])==1;inverse=inverse.replace(c['after'],c['before'])
assert inverse==(prep.parent/'schema-checker-preparation-r3/native-linked.py').read_text()
code=pr['changes'][0]['after'];tests=[]
def trial(label,rows,good):
 env=dict(image=None,br=None,brels=None,linked_candidates=lambda *a:rows,wm=[(0x5000,b'')],struct=struct)
 try:exec(compile(code,'synthetic exact guarded CALL','exec'),env)
 except AssertionError:assert not good
 else:assert good and env['address']==0x1000
 tests.append(dict(label=label,passed=True,adverse=not good))
def body(a,t):return bytes(25)+struct.pack('<i',t-a-29)+bytes(56)
trial('one current and one unrelated whole ASM body',[(0x1000,body(0x1000,0x5000)),(0x2000,body(0x2000,0x6000))],True)
trial('duplicate current guarded targets',[(0x1000,body(0x1000,0x5000)),(0x2000,body(0x2000,0x5000))],False)
trial('no current guarded target',[(0x2000,body(0x2000,0x6000))],False)
trial('off-by-one guarded target',[(0x1000,body(0x1000,0x5001))],False)
for n in ('native-inputs.py','native-TLS.py','native-boundary.py','native-graph.py'):assert (prep/n).read_bytes()==(prep.parent/'schema-checker-preparation-r3'/n).read_bytes()
out.mkdir();p=out/'report.json';p.write_text(json.dumps(dict(passed=True,scope='Bounded exact inverse and guarded target adverse controls only; no current checker/worker/reader run',tests=tests,files=pins),indent=2)+'\n');print(sha(p))
