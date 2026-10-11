"""Current shared Context refusal recipe after a real owned-font prefix.

Derive from the unexecuted measured138 candidate. Eight actual source/context
faults use six carried CW/TOP cases, and the same failed Context is retried.
No worker or reader is opened here.
"""
from pathlib import Path
import hashlib,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def one(t,a,b):need(t.count(a)==1,'Exact control-only hunk '+a[:90]);return t.replace(a,b)
def main(name):
 pp=R/'reports/m4-joint-startup138/preparation-r3/report.json';out=pp.parent.parent/name;need(not out.exists(),'Fresh Context controls recipe');out.mkdir();pins={};copies=[];passed=False;d={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'Ordinary source only');v=sha(p);need(h is None or h==v,'Exact control input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable input');pins[str(p)]=v;return p
 try:
  pin(pp,'ea6c0f3713796e85042039c8af7cf36f0b9faee7035cdf511be1af000023d7ca');d=json.loads(pp.read_bytes());need(d['passed']and d['source_roots']==138,'Current measured138 preparation');phase=json.loads(pin(pp.parent/'widget-phase-map.json').read_bytes());need(phase[0]['phase']==15 and phase[1]['phase']==16 and phase[0]['root']==0x40e250 and phase[1]['root']==0x40ef50,'Exact first owned-font and second fault root table slots')
  for p,h in d['files'].items():pin(p,h)
  for p in pp.parent.rglob('*'):
   if p.is_file()and p.name!='report.json':
    q=out/p.relative_to(pp.parent);q.parent.mkdir(parents=True,exist_ok=True);raw=p.read_bytes();b=raw.replace(pp.parent.as_posix().encode(),out.as_posix().encode());q.write_bytes(b);copies.append(dict(source=str(p.resolve()),target=str(q.resolve()),source_sha256=sha(p),path_rebase=raw!=b))
  p=out/'native_main.cpp';s=p.read_text();s=one(s,' bool routed{};for(const auto&b:widget_bindings)if(b.root==r.cpu().eip){b.callback(r);routed=true;break;}',' bool routed{};for(const auto&b:widget_bindings)if(b.root==r.cpu().eip){if(c->control_route_override)W::Component::entry_40e250(r);else b.callback(r);routed=true;break;}') if ' bool routed{};'in s else one(s,'bool routed{};for(const auto&b:widget_bindings)if(b.root==r.cpu().eip){b.callback(r);routed=true;break;}','bool routed{};for(const auto&b:widget_bindings)if(b.root==r.cpu().eip){if(c->control_route_override)W::Component::entry_40e250(r);else b.callback(r);routed=true;break;}')
  anchor=' unsigned completed{};';methods=''' unsigned control_route_override{};
 void control_snapshot(std::string_view stem){require(widget_component_&&registry_->live_handle(),"Actual live Context diagnostic owner");widget_component_->checkpoint(stem);widget_whole_checkpoint(r_,stem);const auto f=first_;const std::array<std::uint64_t,13>w{1,unsigned(attempted_),unsigned(failed_),completed,unsigned(widget_cleaned_),admitted_cw_,control_route_override,f.phase,f.pc,f.address,f.step,f.kind,unsigned(r_.poisoned())};widget_dump(std::string(stem)+"/Context.bin",w.data(),sizeof(w));std::vector<std::array<unsigned,5>>routes;for(const auto&c:r_.calls())routes.push_back({c.site.value,c.target.value,c.return_pc.value,unsigned(c.import),unsigned(c.completed)});widget_dump(std::string(stem)+"/routes.bin",routes.data(),routes.size()*sizeof(routes[0]));}
''';s=one(s,anchor,methods+anchor);p.write_text(s)
  fixture=pin(R/'tools/m4-joint-startup138/controls_main.cpp');(out/fixture.name).write_bytes(fixture.read_bytes());asm=pin(pp.parent/'connected_hardware_boundary.s').read_text();asm=asm.replace('mfc_connected_hardware_call','context_controls_hardware_call').replace('mfc_connected_invoke_guarded','context_controls_guarded');(out/'controls_hardware_boundary.s').write_text(asm)
  cm=out/'CMakeLists.txt';t=cm.read_text();t=one(t,'"${MW34_PREP}/native_main.cpp"','"${MW34_PREP}/controls_main.cpp"');t=t.replace('mw34_joint_startup138','mw34_widget_context_controls');cm.write_text(t)
  for row in copies:row.update(current_sha256=sha(row['target']),byte_identical=sha(row['target'])==row['source_sha256']);need(row['byte_identical']or row['path_rebase']or Path(row['target']).name in('native_main.cpp','CMakeLists.txt'),'Only declared ordinary control fixture changes')
  generated={}
  for p in out.rglob('*'):
   if p.is_file():pin(p);generated[str(p.resolve())]=sha(p)
  pin(__file__);pin(sys.executable);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  d.update(passed=passed,scope='Unexecuted eight current shared Context faults after sixteen true selected roots including actual owned fonts, same failed Context retry and genuine manual font/registry failure cleanup',parent_preparation=str(pp.resolve()),parent_preparation_sha256=sha(pp),prior_copy_relations=copies,generated_sources=generated,files=pins,control_modes=8,control_target=0x40ef50,control_phase=16,completed_prefix_roots=16,control_CW_TOP_cases=[[0,127,0],[0,895,7],[0,3967,0],[1,1151,7],[1,2687,0],[1,3711,7]],no_per_root_reseed=True,ordinary_outputs_only=True,worker_executed=False,execution_admitted=False,initializer_credit=0);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
