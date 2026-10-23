"""Actual current O0/O2 Ninja library ownership and adverse rule checks."""
from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-criteria-frontier'/name;assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.stat().st_size<32*1024*1024;v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or h==v;pins[str(p)]=v;return p
 p=pin(R/'tools/m4-138-criteria-frontier/current_controls_library_rule_v1.py');spec=importlib.util.spec_from_file_location('actual_library8',p);L=importlib.util.module_from_spec(spec);spec.loader.exec_module(L)
 p=pin(R/'reports/m4-tree-review/joint138-controls-prelaunch-r4/report.json','55990e0cff619c9ee69f2e5e81e27d9e6e92bd4da8d0b5557e4eb28879a10b3a');parent=json.loads(p.read_bytes());rows=[];tests=[]
 for level in ('O0','O2'):
  folder=R/f'reports/m4-joint-startup138/controls-build-r2/build-{level}';worker=folder/'mw34_widget_context_controls.exe';library=R/f'reports/m4-fps-native/connected-component-build-r4/{level}/mw34_widget_native.lib';p=pin(folder/'build.ninja',parent['files'][str(folder/'build.ninja')]);graph=p.read_text();proof=L.prove(graph,worker,library);rows.append(dict(level=level,rule=proof))
  rule=proof['whole_rule'];prop=proof['whole_LINK_LIBRARIES'];implicit=proof['implicit_library'];wrong=str(library.with_name('unowned.lib'));replacements=[('missing_implicit',rule,rule.split(' | ')[0]),('wrong_implicit_library',rule,rule.replace(implicit,wrong)),('implicit_duplicate',rule,rule+' '+implicit),('wrong_rule_worker',rule,rule.replace(worker.name,'other-worker.exe')),('wrong_rule_kind',rule,rule.replace('CXX_EXECUTABLE_LINKER__','OTHER_LINKER__')),('wrong_property_library',prop,prop.replace(str(library),wrong)),('missing_property',prop,'  NO_LINK_LIBRARIES = 0'),('extra_property',prop,prop+'\n'+prop),('wrong_SDK',prop,prop.replace('gdi32.lib','other.lib')),('SDK_order',prop,prop.replace('bcrypt.lib  user32.lib','user32.lib  bcrypt.lib'))]
  for label,a,b in replacements:
   assert graph.count(a)==1;altered=graph.replace(a,b);rejected=False
   try:L.prove(altered,worker,library)
   except AssertionError:rejected=True
   assert rejected,(level,label);tests.append(dict(level=level,mutation=label,rejected=True))
 pin(R/'reports/m4-138-criteria-frontier/current-controls-prelaunch-preparation-r8/report.json','ee2f40e0c84147c477d9719cab074ec938a4fad3f817b4338f806e42e3d74520');pin(__file__);pin(sys.executable);r=dict(passed=True,scope='Actual whole Ninja rule and LINK_LIBRARIES ownership, ordinary graphs only; no worker/linker/fullphysical reviewer execution',actual_rule_rows=rows,adverse_controls=tests,worker_executed=False,archive_reader_opened=False,physical_reviewer_executed=False,accepted_function_credit=0,files=pins);p=out/'report.json';p.write_text(json.dumps(r,indent=2)+'\n');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
