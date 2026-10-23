"""Current original141 whole linked observer review; no worker or capture reader."""
from pathlib import Path
import ast,collections,hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-original141'/name;assert not out.exists();out.mkdir();files={};links=[];counts=collections.Counter();passed=False
 def pin(p,h=None):p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip');v=sha(p);assert h is None or h==v,(p,h,v);assert files.setdefault(str(p),v)==v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def text(p):return pin(p).read_text()
 def module(p,n):s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  bf=R/'reports/m4-original141/build-r1';folder=R/'reports/m4-original141/source-preparation-r2';current=R/'reports/m4-original141/source-preparation-r3'
  b=read(bf/'build.json','088e5dfbe970baee5e8187edbfbb5f06eafd217d2b1f5554e344ed55b836d79b');p=read(folder/'report.json','7c1acf0bb08043cf8a371a6b31d7fc3f4071771dae936a748abad66969c8cbd8');cp=read(current/'report.json','8f983d72c0a3aeabedd87cc009f7dd5704f6236d251bc66610671551161d365b');assert b['passed']and b['preparation_sha256']==sha(folder/'report.json')and Path(b['preparation'])==folder and not b['original_executed']and not b['native_executed']
  for r,key in((p,'files'),(cp,'files'),(b,'sources')):
   for path,h in r[key].items():pin(path,h)
  for f in folder.iterdir():
   if f.is_file()and f.name not in('report.json','pins.json'):assert pin(f).read_bytes()==pin(current/f.name).read_bytes();counts['whole_actual_source2_to_review_source3_payloads']+=1
  old=R/'reports/m4-startup138-original/preparation-r8'
  for leaf,delta,n in(('reference.cpp','CPP-deltas.json',22),('reference_x86.asm','reference-ASM-deltas.json',2),('fs_observer_x86.asm','FS-ASM-deltas.json',2)):
   body=text(folder/leaf);ds=read(folder/delta);assert len(ds)==n
   for d in reversed(ds):assert body.count(d['new'])==1;body=body.replace(d['new'],d['old'],1)
   assert body==text(old/leaf);counts['whole_source_inverse_edits']+=n
  geometry=read(R/'reports/m4-original141/geometry-controls-r2/report.json','7e1daf0ab03e597818d62099eb8c74482c17823688e36b374eadf260f295aa93');assert geometry['passed']
  for path,h in geometry['files'].items():pin(path,h)
  PE=module(R/'tools/analysis/pe.py','compiled_original141_PE')
  parent=pin(R/'reports/m4-original141/compiled-review-recipe-r1/retained138-review-materialized.py').read_text();start=parent.index("        C=module(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py'");end=parent.index('        consumed=set()',start);block='\n'.join(v[8:]for v in parent[start:end].splitlines());deltas=[]
  def change(a,z):
   nonlocal block
   assert block.count(a)==1;block=block.replace(a,z,1);deltas.append(dict(old=a,new=z,count=1))
  change("'widget_observer_x86','fps_observer_x86'):","'widget_observer_x86','fps_observer_x86','constructor_observer_x86'):")
  change("'_widget_observe','_fps_observe'}","'_widget_observe','_fps_observe','_ctor_observe','_registry_observe_allocation','_ctor_record_fs_failure','?capture_constructor_input_segments@@YAXXZ','?execute@@YAIXZ'}")
  change("'?widget_cleanup_resource@@')))","'?widget_cleanup_resource@@','?constructor_is_root@@','?constructor_whole_live_owners@@','?constructor_member_graph@@','?constructor_normal_dump@@')))")
  change('len(names)==len(set(names))==17','len(names)==len(set(names))==26')
  reverse=block
  for d in reversed(deltas):assert reverse.count(d['new'])==1;reverse=reverse.replace(d['new'],d['old'])
  assert reverse=='\n'.join(v[8:]for v in parent[start:end].splitlines());ast.parse(block)
  env=dict(R=R,pin=pin,read=read,text=text,module=module,PE=PE,b=b,bf=bf,folder=folder,re=re,struct=struct,Path=Path,counts=counts,links=links)
  exec(compile(block,'whole retained138 physical link block with exact additive141 domain','exec'),env)
  assert counts['whole_linked_ASM_sections']==12 and counts['whole_linked_CPP_functions']==24
  release=bf/'build-x86/mw34_joint_startup124_original.dir/Release';consumed=set();tlogs=list(release.rglob('CL.read.1.tlog'));assert len(tlogs)==1
  for line in pin(tlogs[0]).read_text(encoding='utf-16').splitlines():
   q=Path(line.strip().lstrip('^'))
   if q.is_absolute()and q.is_file():consumed.add(pin(q))
  assert {folder/name for name in('reference.cpp','protocol.hpp','spec.hpp','constructor_normal.hpp','connected_observer.hpp','prerequisite_observer.hpp','format_observer.hpp','original_broker.hpp','widget_observer.hpp','fps_observer.hpp')}<=consumed
  log=text(bf/'compile.log');assert '/MACHINE:X86'in log and '/W4 /WX'in log and '0 Warning(s)'in log and '0 Error(s)'in log;counts['actual_consumed_compiler_inputs']=len(consumed)
  (out/'predicate-deltas.json').write_text(json.dumps(deltas,indent=2)+'\n');pin(out/'predicate-deltas.json');(out/'whole-linked-predicate.py').write_text(block+'\n');pin(out/'whole-linked-predicate.py')
  pin(__file__)
  for path,h in tuple(files.items()):assert sha(path)==h
  passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc())
 (out/'physical-links.json').write_text(json.dumps(links,indent=2)+'\n');pin(out/'physical-links.json')
 report=dict(passed=passed,scope='Actual current original141 whole linked observer source2; current source3 byte-identical review lineage',actual_compiled_preparation=str(folder),current_review_preparation=str(current),counts=dict(counts),whole_linked_observer_source_attribution=passed,compiled_PUSHFD_causal_stack_controls_pending=True,whole_CRT_IAT_transition_validator_pending=True,worker_launch_admitted=False,worker_executed=False,canonical_reader_opened=False,original141_equivalence=False,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'),counts=dict(counts))))
 if not passed:raise SystemExit(1)
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('name');main(p.parse_args().name)
