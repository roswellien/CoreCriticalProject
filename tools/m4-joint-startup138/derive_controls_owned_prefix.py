"""Replace the unexecuted stock-only fault prefix with actual owned fonts.

The seven current literal contracts establish the sole CreateFontA root at
phase134. Before root5A3FF0/phase135, fifteen real creations have occurred.
No writer/build/reader is opened by this additive source preparation.
"""
from pathlib import Path
import hashlib,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 pp=R/'reports/m4-joint-startup138/controls-preparation-r3/report.json';out=pp.parent.parent/name;need(not out.exists(),'Fresh actual-owned-prefix controls');out.mkdir();pins={};copies=[];changes=[];passed=False;d={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'Ordinary source-only preparation');v=sha(p);need(h is None or h==v,'Exact ordinary source '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable source identity');pins[str(p)]=v;return p
 try:
  pin(pp,'0ef6894a8f17607d6c3d9908d618b3ce9516a1eae3c300390d67c2c11987da69');d=json.loads(pp.read_bytes());need(d['passed']and not d['worker_executed'],'Unexecuted prior controls preserved');phase=json.loads(pin(pp.parent/'widget-phase-map.json').read_bytes());contract_path=pin(R/'reports/m4-fps-native/connected-component-preparation-r4/contracts.json');contracts=json.loads(contract_path.read_bytes());need(phase[4]['phase']==134 and phase[4]['root']==0x5a3c30 and phase[5]['phase']==135 and phase[5]['root']==0x5a3ff0,'Physical table-derived exact owned-font prefix');creates=[(x['root'],sum(c['service']=='CreateFontA'for c in x['GDI_calls']))for x in contracts['roots']];need(creates==[(0x40e250,0),(0x40ef50,0),(0x40f000,0),(0x479590,0),(0x5a3c30,15),(0x5a3ff0,0),(0x5a66f0,0)],'Sole source-owned fifteen-font creation root, no stock handles reclassified');need(contracts['roots'][5]['object']==0x736130,'Current fault root actual source object');
  for p,h in d['files'].items():pin(p,h)
  for p in pp.parent.rglob('*'):
   if p.is_file()and p.name!='report.json':
    q=out/p.relative_to(pp.parent);q.parent.mkdir(parents=True,exist_ok=True);b=p.read_bytes();v=b.replace(pp.parent.as_posix().encode(),out.as_posix().encode());q.write_bytes(v);copies.append(dict(source=str(p.resolve()),target=str(q.resolve()),source_sha256=sha(p),path_rebase=b!=v))
  fixture=out/'controls_main.cpp';text=fixture.read_text();replacements=[('phase!=16','phase!=135'),('c.completed==16','c.completed==135'),('second-widget control after complete owned-font prefix','post-creation widget control after complete fifteen-owned-font prefix'),('0x40ef50','0x5a3ff0'),('0x5bb070','0x5bb52c'),('0x5fc838','0x736130'),('records.reserve(17)','records.reserve(136)'),('context.completed==16','context.completed==135'),('records.size()==16','records.size()==135'),('sixteen-root prefix','135-root prefix')]
  for a,b in replacements:
   count=text.count(a);need(count,'Exact prior source control hunk '+a);text=text.replace(a,b);changes.append(dict(old=a,new=b,occurrences=count))
  # The explicit source cause phase remains distinct from the loop predicate.
  need(text.count('cause{1,mode,phase,0x5a3ff0')==1,'Actual cause carries new selected source root');fixture.write_text(text)
  for row in copies:
   row.update(current_sha256=sha(row['target']),byte_identical=sha(row['target'])==row['source_sha256']);need(row['byte_identical']or row['path_rebase']or Path(row['target']).name=='controls_main.cpp','Only declared control injection/prefix changed')
  for x in('native_main.cpp','widget_services.hpp','onexit_session.hpp','connected_hardware_boundary.s','controls_hardware_boundary.s','joint_protocol.hpp'):
   need((out/x).read_bytes()==(pp.parent/x).read_bytes(),'Whole actual Context/provider/machine source unchanged '+x)
  generated={}
  for p in out.rglob('*'):
   if p.is_file():pin(p);generated[str(p.resolve())]=sha(p)
  pin(__file__);pin(sys.executable);d.update(control_target=0x5a3ff0,control_phase=135,completed_prefix_roots=135,owned_font_prefix_root=0x5a3c30,owned_font_prefix_phase=134,source_owned_font_create_calls=15,source_GDI_calls_before_fault=149,prior_stock_only_prefix_owned_fonts=0,generated_sources=generated);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  d.update(passed=passed,scope='Unexecuted eight actual carried Context faults after 135 sorted roots and fifteen source-created native fonts; current firstfault/retry and actual owned-font cleanup remain runtime obligations',prior_controls_preparation=str(pp.resolve()),prior_controls_preparation_sha256=sha(pp),prior_copy_relations=copies,exact_control_source_substitutions=changes,files=pins,archive_reader_opened=False,worker_executed=False,execution_admitted=False,initializer_credit=0);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
