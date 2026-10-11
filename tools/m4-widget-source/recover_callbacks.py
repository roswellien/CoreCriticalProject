"""Distinct widget destructors/array cleanup dependency inventory only."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-widget-source'
sys.path.insert(0,str(R/'tools/m4-service-initializers'))
s=importlib.util.spec_from_file_location('widget_callback_recover',R/'tools/m4-onexit-batch-recovery/recover.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,t):
 if not v:raise ValueError(t)
def main(name):
 out=B/name;need(not out.exists(),'Fresh source callback inventory');out.mkdir(parents=True);pins={};commands=[]
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.zip','.mwb'),'No archive payload');v=sha(p);need(h is None or h==v,'Exact physical source/callback dependency');pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 d=read(B/'dispatch-r1/report.json','ee96052d75b9f459bcb1a96953e7130bbb98125c1d57c76fa7ed8ada9c415375');need(d['passed'],'Exact current constructor recovery')
 game=M.Module(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'))
 for name0 in('game-bound-graphs.json',):
  for g in read(B/'dispatch-r1'/name0).values():M.ingest(game,g['instructions'])
 for g in read(B/'recovery-r2/callback-physical-graphs.json').values():M.ingest(game,g['instructions'])
 entries=(0x409ef0,0x5a05a0,0x5a01f0,0x40e420,0x40ef90,0x5a3c60,0x5a4020,0x5a6720)
 nodes,deferred=M.closure(game,entries,out,commands,maximum=140)
 rows={r['pc']:r for g in nodes.values()for r in g['instructions']}
 summaries=[dict(entry=e,**M.requirements(nodes,M.descendants(nodes,e)),runtime_executed=False)for e in entries]
 payloads={'callback-dependency-graphs.json':nodes,'callback-source-summaries.json':summaries,'callback-open-frontiers.json':dict(direct_deferred=deferred,unresolved=[dict(entry=e,**u)for e,g in nodes.items()for u in g['unresolved_controls']],imports=[dict(entry=e,**u)for e,g in nodes.items()for u in g['import_sites']],scope='All direct callback source including destructor/delete/error branches; no current lifetime or invocation admission')}
 for n,v in payloads.items():p=out/n;p.write_text(json.dumps(v,indent=2)+'\n');pin(p)
 for p in(Path(__file__),R/'tools/m4-onexit-batch-recovery/recover.py',R/'tools/m4-service-initializers/recover.py',R/'tools/analysis/pe.py',M.DECODER):pin(p)
 for p in out.iterdir():
  if p.is_file():pin(p)
 report=dict(passed=True,scope='Actual distinct callback source bodies and full direct dependency inventory; no reverse-dispatch/destructor/API execution claim',counts=dict(callback_roots=8,graph_entries=len(nodes),instructions=len(rows),bytes=sum(r['size']for r in rows.values()),fresh_decodes=len(commands)),direct_deferred=deferred,commands=commands,files=pins,original_executed=False,native_executed=False,initializer_credit=0)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p),counts=report['counts'],deferred=deferred)))
if __name__=='__main__':main(sys.argv[1])
