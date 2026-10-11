"""Physical nine-root frontier and exact static indirect target source graphs."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-next-source'
sys.path.insert(0,str(R/'tools/m4-service-initializers'))
s=importlib.util.spec_from_file_location('next_batch_recover',R/'tools/m4-onexit-batch-recovery/recover.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M)
ROOTS=(0x40e250,0x40ef50,0x40f0e0,0x4795f0,0x47f5f0,0x4b5220,0x5a3c30,0x5a3ff0,0x5a66f0)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=B/name;need(not out.exists(),'New frontier report');out.mkdir(parents=True);pins={};commands=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical input');pins[str(p)]=v;return p
 accepted=json.loads(pin(R/'reports/m4-joint-startup116-root/acceptance-r1/report.json','de76b4e006e5ad2ce0b90f634054379f2271abd14ecb8591643c24e72cc4c0e6').read_bytes());need(accepted['passed'],'Accepted116 parent')
 old=json.loads(pin(R/'reports/m4-joint-startup116-root/next-frontier-r1/remaining-roots.json').read_bytes());roots=[r for r in old if r['entry']in ROOTS];need(len(roots)==9,'Exact nine remaining registration-only static closures')
 game=M.Module(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'));allgraphs=json.loads(pin(R/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json','da2482873e1678a0a2493ed7f60421440447c43e63826b53f2d5b09cf573ba5a').read_bytes())
 for g in allgraphs.values():M.ingest(game,g['instructions'])
 targets=[]
 for pc,slot,required in((0x59fbab,0x5cfd14,0x40e820),(0x59fdc5,0x5bc100,0x59ff00),(0x59ff6e,0x5bc0fc,0x59ff80)):
  fact=game.data(slot,4);value=int.from_bytes(bytes.fromhex(fact['initial_hex']),'little');need(value==required and game.executable(value),'Exact file-backed executable vtable slot');targets.append(dict(CALL_pc=pc,slot=slot,target=value,physical_slot=fact,control_kind='fixed vtable slot'if pc!=0x59ff6e else 'source-written base vtable plus1C'))
 normal,deferred=M.closure(game,[r['entry']for r in roots]+[r['target']for r in targets],out,commands);need(not deferred,'Bounded direct dependency recovery');tails={e['to']for g in normal.values()for e in g['edges']if e['to']<g['entry']and 'jump'in e['kind']};tailgraphs,taildeferred=M.closure(game,sorted(tails),out,commands);need(not taildeferred,'Exact lower-tail source recovery');normal.update(tailgraphs)
 for label,value in(('roots.json',roots),('game-normal-graphs.json',normal),('static-indirect-inputs.json',targets)):(out/label).write_text(json.dumps(value,indent=2)+'\n');pin(out/label)
 per=[]
 for r in roots:
  entries=set(M.descendants(normal,r['entry']));added=True
  while added:
   added=False
   for target in targets:
    if any(any(row['pc']==target['CALL_pc']for row in normal[e]['instructions'])for e in entries if e in normal):
     before=len(entries);entries.update(M.descendants(normal,target['target']));added|=len(entries)!=before
  requirements=M.requirements(normal,sorted(entries));per.append(dict(root=r['entry'],slot=r['slot'],**requirements,allocation_or_provider_normal_path='Undecided until exact target instructions/source branch evaluation; no execution credit'))
 (out/'root-frontiers.json').write_text(json.dumps(per,indent=2)+'\n');pin(out/'root-frontiers.json');pin(__file__);pin(R/'tools/m4-onexit-batch-recovery/recover.py');pin(R/'tools/m4-service-initializers/recover.py')
 report=dict(passed=True,scope='Physical static planning: exact nine remaining onexit-only roots plus three previously indirect static game vtable targets. Reached-path/source execution and root selection remain pending.',roots=per,targets=targets,commands=commands,files=pins,original_executed=False,native_executed=False,initializer_credit=0);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),targets=targets,root_rows={hex(r['root']):r['unique_instructions']for r in per})))
if __name__=='__main__':main(sys.argv[1])
