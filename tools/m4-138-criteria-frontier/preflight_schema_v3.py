"""Bounded inverse/adverse owning-symbol controls, no physical executable review."""
from pathlib import Path
import hashlib,json,collections,struct,sys,runpy,ast
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prep=R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r3'
pr=json.loads((prep/'report.json').read_bytes());out=R/'reports/m4-138-criteria-frontier/schema-synthetic-preflight-r2';assert not out.exists()
pins={str(prep/'report.json'):sha(prep/'report.json'),str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
for p,h in pr['files'].items():assert sha(Path(p))==h;pins[p]=h
delta=pr['linked_delta'];s=(prep/'native-linked.py').read_text()
assert s.count(delta['after'])==1 and s.count(delta['new_case'])==1
inverse=s.replace(delta['after'],delta['before']).replace(delta['new_case'],delta['old_case'])
assert inverse==(R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r2/native-linked.py').read_text()
ns=runpy.run_path(str(R/'tools/m4-138-criteria-frontier/check_schema138_v3.py'),run_name='definition_only');assert callable(ns['main'])
prefix=s[:s.index('def current_body_matches')]
tests=[]
def trial(label,mutation=None,bad=False):
 owner='?owner@m4_mfc1168_connected@mw34@@YA@PEAX@Z';tls='?current@Impl@Component@m4_mfc1168_connected@mw34@@2PEAU1234@EA'
 targets={'mw34_mfc1168_read32':0x2000,'mw34_mfc1168_write8':0x2100,'mw34_mfc1168_write32':0x2200,'mw34_mfc1168_call':0x2300,'mw34_mfc1168_jump':0x2400,'mw34_mfc1168_return':0x2500,owner:0x3000}
 level='O0'
 if mutation=='O2 ambiguity':level='O2'
 class C:
  @staticmethod
  def parse(raw):return {},{}
  @staticmethod
  def function(sy,se,name):
   rel=[dict(offset=0,type=4,symbol=dict(name=owner))]
   if name==owner:rel=[dict(offset=0,type=11,symbol=dict(name='wrong_tls' if mutation=='wrong TLS identity' else tls))]
   if mutation=='missing call owner' and name=='mw34_mfc1168_call':rel=[]
   return name.encode(),rel
 def matches(image,raw,rel):
  name=raw.decode();a=targets[name];t=0x3001 if mutation=='wrong call owner target' and name=='mw34_mfc1168_call' else 0x3000
  rows=[(a,struct.pack('<i',t-a-4))]
  if name in ('mw34_mfc1168_read32','mw34_mfc1168_write8','mw34_mfc1168_write32'):
   other=a+0x10000;rows.append((other,struct.pack('<i',(0x3000 if mutation=='duplicate live-owner bridge' else 0x4000)-other-4)))
  if name==owner and mutation=='duplicate owner':rows.append((a+1,bytes(4)))
  return rows
 env=dict(pin=lambda p:p,bf=Path('.'),C=C,linked_candidates=matches,TLS_relations=lambda *a:None,image=None,level=level,struct=struct,links=[],counts=collections.Counter())
 try:
  exec(compile(prefix,'synthetic owning-function prefix','exec'),env)
  assert env['bridge_targets']=={k:v for k,v in targets.items()if k!=owner}
  assert env['counts']['whole_current_typed_bridge_functions']==6
  assert env['counts']['otherwise_identical_bridge_owner_attributions']==3
 except (AssertionError,KeyError):
  if not bad:raise
 else:assert not bad,'Adverse incorrectly admitted: '+label
 tests.append(dict(label=label,passed=True,adverse=bad))
trial('exact whole owner and three physically scoped bridges')
for m in ('missing call owner','wrong call owner target','wrong TLS identity','duplicate live-owner bridge','duplicate owner','O2 ambiguity'):trial(m,m,True)
for n in ('native-inputs.py','native-TLS.py','native-boundary.py','native-graph.py'):
 assert (prep/n).read_bytes()==(R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r2'/n).read_bytes();ast.parse((prep/n).read_text())
out.mkdir();p=out/'report.json';p.write_text(json.dumps(dict(passed=True,scope='Synthetic/inverse code controls only; no actual current executable check, worker, or reader',exact_linked_inverse=True,all_other_blocks_whole_equal=True,tests=tests,files=pins),indent=2)+'\n');print(sha(p))
