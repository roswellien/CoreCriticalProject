"""Compose existing independent full links with exact current source inversion."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-138-controls-review'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or v==h,str(p);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 sp=importlib.util.spec_from_file_location('link_join_header',pin(R/'tools/m4-138-controls-review/readiness.py'));header=importlib.util.module_from_spec(sp);sp.loader.exec_module(header)
 ep=pin(R/'reports/m4-joint-startup138-root/execution-r3/report.json');e=header.header(ep)
 ce=pin(R/'reports/m4-joint-startup138/context-controls-execution-r1/report.json','43d8a2a8e56e6d6a0286236685b16fc6e36b806ebcc8fc6199d49c95e69e0863');c=header.header(ce)
 assert e['passed']and c['passed']and c['all_workers_terminal']and c['actual_workers_launched']==16
 a=read(e['admission_review'],'cede59b7c9b77ab98b78da72374938775b3c78ec3e9a737f618bd688873e3325');b=read(c['admission_review'],'55990e0cff619c9ee69f2e5e81e27d9e6e92bd4da8d0b5557e4eb28879a10b3a')
 assert a['passed']and b['passed']and a['build_sha256']==e['build_sha256']and b['build_sha256']==c['build_sha256']
 assert a['counts']['whole_linked_current_functions']==1510 and b['counts']['whole_linked_current_functions']==1547 and b['counts']['whole_positive_Context_inversion']==1
 positive=read(e['build_path'],e['build_sha256']);controls=read(c['build_path'],c['build_sha256']);assert positive['passed']and controls['passed']
 for build,review in((positive,a),(controls,b)):
  assert build['preparation_sha256']==review['preparation_sha256']
  for worker in build['workers'].values():pin(worker['path'],worker['sha256']);assert review['files'][worker['path']]==worker['sha256']
 pa=Path(e['admission_review']).parent/'physical-links.json';pb=Path(c['admission_review']).parent/'physical-links.json'
 ra=read(pa,a['files'][str(pa.resolve())]);rb=read(pb,b['files'][str(pb.resolve())]);assert len(ra)==1510 and len(rb)==1547
 ka={(x['level'],x['symbol']):x for x in ra};kb={(x['level'],x['symbol']):x for x in rb};assert len(ka)==len(ra)and len(kb)==len(rb)
 shared=[];different=[]
 for k in sorted(ka.keys()&kb.keys()):
  x,y=ka[k],kb[k];row=dict(level=k[0],symbol=k[1],positive=x,controls=y)
  if(x['whole_bytes'],x['source_sha256'])==(y['whole_bytes'],y['source_sha256']):shared.append(row)
  else:
   assert Path(x['object']).name=='native_main.cpp.obj'and Path(y['object']).name=='controls_main.cpp.obj';different.append(row)
 assert len(shared)==1490 and len(different)==11
 for rows,review in((ra,a),(rb,b)):
  for p in sorted({x['object']for x in rows}):pin(p,review['files'][p])
 # Physically repeat the independent review's precise source inverse, without
 # loading any capture, executing callbacks, or granting a new launch.
 pp=R/'reports/m4-joint-startup138/preparation-r4';cp=R/'reports/m4-joint-startup138/controls-preparation-r4'
 original=pin(pp/'native_main.cpp',a['files'][str((pp/'native_main.cpp').resolve())]).read_text();current=pin(cp/'native_main.cpp',b['files'][str((cp/'native_main.cpp').resolve())]).read_text()
 route='if(c->control_route_override)W::Component::entry_40e250(r);else b.callback(r);';assert current.count(route)==1
 reduced=current.replace(route,'b.callback(r);');additions=[line for line in reduced.splitlines(True)if line.startswith((' unsigned control_route_override{};',' void control_snapshot('))];assert len(additions)==2
 snapshot=next(line for line in additions if line.startswith(' void control_snapshot('));assert all(s not in snapshot for s in ['store<','protect(','seed(','r_.cpu()='])
 for token in ['widget_component_&&registry_->live_handle()','widget_component_->checkpoint(stem);widget_whole_checkpoint(r_,stem);','const auto f=first_;','r_.poisoned()','for(const auto&c:r_.calls())']:assert token in snapshot
 for line in additions:assert reduced.count(line)==1;reduced=reduced.replace(line,'',1)
 assert reduced==original
 protocol=pin(pp/'joint_protocol.hpp',a['files'][str((pp/'joint_protocol.hpp').resolve())]);control_protocol=pin(cp/'joint_protocol.hpp',b['files'][str((cp/'joint_protocol.hpp').resolve())]);assert protocol.read_bytes()==control_protocol.read_bytes()
 for p in ['tools/m4-tree-review/review_joint138_controls_prelaunch.py','tools/m4-tree-review/review_joint138_controls_prelaunch_v4.py','tools/m4-tree-review/review_joint138_prelaunch_v10.py']:pin(R/p)
 pin(__file__);pin(sys.executable)
 d=dict(passed=True,scope='Exact current structural execution3/build5/admitted positive link to completed controls execution1/build2/admitted negative link; full independent link reviews reused, source inversion repeated',
  positive_execution_sha256=pins[str(ep)],controls_execution_sha256=pins[str(ce)],positive_prelaunch_sha256=e['admission_review_sha256'],controls_prelaunch_sha256=c['admission_review_sha256'],
  counts=dict(admitted_positive_whole_functions=1510,admitted_controls_whole_functions=1547,shared_whole_function_source_identities=1490,enumerated_changed_harness_functions=11,positive_only_admitted_functions=len(ka.keys()-kb.keys()),controls_only_admitted_functions=len(kb.keys()-ka.keys()),physically_bound_code_objects=len({x['object']for x in ra+rb})),
  changed_harness_functions=different,positive_only_functions=[ka[k]for k in sorted(ka.keys()-kb.keys())],controls_only_functions=[kb[k]for k in sorted(kb.keys()-ka.keys())],
  shared_source_protocol_whole_bytes_identical=True,whole_Context_inverse_restores_positive=True,current_native3_admitted_full_link_join=True,independent_link_function_audit_rerun=False,whole_positive_control_worker_byte_equality_claimed=False,
  native_execution_performed=False,capture_archives_opened=0,initializer_credit=0,remaining_controls_gate='Full independent raw/inventory and private/provider retry proof remains deferred; source/provider/original/pair acceptance separate',files=pins)
 out.mkdir(parents=True);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),counts=d['counts'])))
if __name__=='__main__':main(sys.argv[1])
