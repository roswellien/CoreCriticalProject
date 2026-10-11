"""Definition/inverse/synthetic preflight only; no writer or capture reader."""
from pathlib import Path
import ast,collections,hashlib,json,struct,textwrap
R=Path(__file__).resolve().parents[2];P={}
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip');v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or h==v;P[str(p)]=v;return p
prep=R/'reports/m4-startup138-original/realloc-controller-validation-preparation-r1/report.json';data=json.loads(pin(prep,'811c1bcf6736e02663cd41ec847c8d5ff12e92659f88e6c2e4ba0cc71827f4b0').read_bytes())
for field in('controller_path','validator_path'):ast.parse(pin(data[field],data[field.replace('_path','_sha256')]).read_text())
for target,changes in data['changes'].items():
 text=pin(R/'tools/m4-startup138-original'/target).read_text()
 for d in reversed(changes):
  p=d['position'];assert text[p:p+len(d['new'])]==d['new'];text=text[:p]+d['old']+text[p+len(d['new']):]
 parent='run_v2.py'if target.startswith('run_')else'validate_v3.py';assert text==pin(R/'tools/m4-startup138-original'/parent).read_text()
delta=next(x for x in data['changes']['validate_realloc_v1.py']if 'Actual complete provider API ledger'in x['old']);addition=delta['new'][len(delta['old']):];body=textwrap.dedent(addition);compile(body,'bounded-realloc-gate','exec')
def evaluate(case):
 before=bytes(range(128));words=[0]*26;words[4]=0x20001000;words[14]=words[4]+20;words[10]=0x310000;words[22]=0x300000;words[23]=144;words[24]=3;words[25]=0x78011c2d
 values={'phase/0/47/registry-before-meta.bin':struct.pack('<4I',0x300000,0x300080,128,1),'phase/0/47/registry-before-backing.bin':before,'phase/0/47/api-initial/0/size.bin':struct.pack('<I',144),'phase/0/47/api-initial/0/bytes.bin':before+b'\xcc'*16}
 if case=='wrong-return':words[25]+=1
 if case=='nonzero-PC':words[9]=1
 if case=='small-size':values['phase/0/47/api-initial/0/size.bin']=struct.pack('<I',128);values['phase/0/47/api-initial/0/bytes.bin']=before
 if case=='changed-prefix':values['phase/0/47/api-initial/0/bytes.bin']=b'\xee'+values['phase/0/47/api-initial/0/bytes.bin'][1:]
 if case=='missing-backing':del values['phase/0/47/api-initial/0/bytes.bin']
 class Records:
  def data(self,k):return values[k]
 def need(v,m):
  if not v:raise ValueError(m)
 env=dict(struct=struct,records=Records(),seq=0,phase=47,apicount=1,ledger=struct.pack('<26I',*words),counts=collections.Counter(),need=need)
 try:exec(body,env);return True
 except (ValueError,KeyError):return False
controls={case:evaluate(case)for case in('valid','wrong-return','nonzero-PC','small-size','changed-prefix','missing-backing')};assert controls==dict(valid=True,**{x:False for x in controls if x!='valid'})
pin(__file__);out=R/'reports/m4-startup138-original/realloc-controls-preflight-r1';assert not out.exists();out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,controls=controls,exact_reverse_restores_both_parents=True,writer_launched=False,reader_opened=False,source_machine_executed=False,initializer_credit=0,files=P),indent=2)+'\n');print(q,hashlib.sha256(q.read_bytes()).hexdigest())
