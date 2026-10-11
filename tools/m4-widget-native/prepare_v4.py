"""Add one physically recovered lower-tail literal entry; old51 bodies fixed."""
from pathlib import Path
import hashlib, json, re, shutil, sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-widget-native'/name;need(not out.exists(),'Fresh component52 preparation');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Actual unchanged component input '+str(p));pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 prior_path=R/'reports/m4-widget-native/preparation-r3/report.json';prior=read(prior_path,'69a29eddf46f6c189edc462e5f5734a96e3d98c2c1f37778a54d36c0fd62eae5');need(prior['passed']and prior['literal_bodies']==51,'Frozen complete prior component')
 for p,h in prior['files'].items():pin(p,h)
 tail_path=R/'reports/m4-widget-native/lifts-r1/report.json';tail=read(tail_path,'6a8add20208591957a439c6f4b804ed446c8581875b60726e7ea6fcebc95fe57');need(tail['passed']and set(tail['source_bodies'])=={'f_5a4590'},'One exact fresh lower-tail compiled body')
 for p,h in tail['files'].items():pin(p,h)
 outputs=[]
 for p in prior_path.parent.iterdir():
  if p.is_file()and p.name!='report.json':q=out/p.name;shutil.copyfile(p,q);outputs.append(dict(name=p.name,prior_path=str(p),prior_sha256=sha(p),current_path=str(q),current_sha256=sha(q)));need(sha(q)==sha(p),'Whole prior generated source and51 IRs copied exact')
 b=tail['source_bodies']['f_5a4590'];source=pin(tail_path.parent/'f_5a4590-host.ll',b['host_sha256']);raw=source.read_text();transformed=raw.replace('mw34_onexit_game_','mw34_widget_game_');need(transformed.replace('mw34_widget_game_','mw34_onexit_game_')==raw,'Namespace-only new lower-tail IR');q=out/'f_5a4590-host.ll';q.write_text(transformed);new_ir=q
 hp=out/'literals.hpp';h=hp.read_text();a='inline Body body(unsigned pc){switch(pc){';need(h.count(a)==1,'One actual typed body dispatcher');h=h.replace(a,'extern "C" void *mw34_widget_game_f_5a4590_body(State*,unsigned,void*);\n'+a+'\ncase 5916048:return mw34_widget_game_f_5a4590_body;');hp.write_text(h)
 bridges=out/'bridges.inc';text=bridges.read_text();added=[]
 for name in sorted(set(re.findall(r'@((?:mw34_widget_game_)[A-Za-z0-9_]+)',transformed))):
  if '_direct_'in name and not re.search(r'\b'+re.escape(name)+r'\(',text):added.append('extern "C" void *%s(State*s,unsigned a,void*p){return mw34_widget_game_call(s,a,p);}'%name)
  elif name.endswith('_undefined_8')and not re.search(r'\b'+re.escape(name)+r'\(',text):added.append('extern "C" std::uint8_t %s(){return 0;}'%name)
 if added:bridges.write_text(text+'\n'.join(added)+'\n')
 need((out/'component.cpp').read_bytes()==(prior_path.parent/'component.cpp').read_bytes()and(out/'contracts.json').read_bytes()==(prior_path.parent/'contracts.json').read_bytes(),'All source/owner/FS/causal/cleanup guards and literal operand tables unchanged')
 for p in out.iterdir():pin(p)
 pin(__file__);pin(R/'tools/m4-widget-native/build_v3.py');pin(R/'tools/m4-widget-native/build_v3.ps1')
 report=dict(prior);report.update(literal_bodies=52,IRs=[str(out/Path(p).name)for p in prior['IRs']]+[str(new_ir)],namespace_relations=[dict(v,component_IR=str(out/Path(v['component_IR']).name))for v in prior['namespace_relations']]+[dict(entry=0x5a4590,original_IR=str(source),original_sha256=sha(source),component_IR=str(new_ir),component_sha256=sha(new_ir),change='Exact symbol-prefix substitution only')],scope='Reusable six-root widget component with52 literal entries; exact normal backward constructor tail added, no execution/equality credit',prior_component_sha256=sha(prior_path),lower_tail_lift_sha256=sha(tail_path),lower_tail_entry=0x5a4590,whole_prior_IRs_unchanged=51,changed_generated_files=['literals.hpp','bridges.inc'],new_bridge_symbols=added,component_cpp_unchanged=True,contracts_json_unchanged=True,physical_prior_rows_unchanged=1093,files=pins)
 report['namespace_relations'][-1]['instructions']=b['instructions'];report['prior_copy_relations']=outputs
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(p),sha256=sha(p),literal_bodies=52)))
if __name__=='__main__':main(sys.argv[1])
