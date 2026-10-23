"""Complete bounded77 positive-source domain and exact third ASM inverse."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-criteria-frontier'/name;assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.stat().st_size<32*1024*1024;v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or h==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def blob(p,h=None):return pin(p,h).read_bytes()
 folder=R/'reports/m4-joint-startup138/controls-preparation-r4';prep=read(folder/'report.json','f413ea66cb259ecebf8bf76024113a0410fe5883304fa10af9a442b291c1b07e');pf=R/'reports/m4-mfc1168-native/connected-fixture-preparation-r5'
 generated=R/'reports/m4-138-criteria-frontier/current-controls-prelaunch-preparation-r10';pr=read(generated/'report.json','89d0db8f4c1c202c86896667c7280995cabc5ce1876a5f0ed6421617cdbf8a51');code=pin(generated/'review.py',pr['files'][str(generated/'review.py')]).read_text()
 tree=ast.parse(code);nodes=[n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name=='prove_positive_file'];assert len(nodes)==1
 original_widget=read(R/'reports/m4-fps-original/preparation-r1/report.json','7c2aea9d60270b768b1c9ecdd63ed7f2898decfa72f5536c43151e7b7e1278a1');wc=read(prep['widget_component_preparation'],prep['widget_component_preparation_sha256']);wp=Path(prep['widget_component_preparation']).parent;contracts=read(wp/'contracts.json',wc['files'][str(wp/'contracts.json')]);newroots=[x['root']for x in contracts['roots']]
 import re
 fixed=[int(v,16)for v in re.search(rb' pages\{([^}]+)',blob(pf/'joint_protocol.hpp'))[1].split(b',')]
 ns=dict(folder=folder,prep=prep,blob=blob,read=read,re=re,original_widget=original_widget,newroots=newroots,fixed=fixed,contracts=contracts)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'exact preparation10 positive-source predicate','exec'),ns);prove=ns['prove_positive_file'];rows=[];changed=[]
 for p in pf.rglob('*'):
  if not p.is_file()or p.name=='report.json':continue
  rel=p.relative_to(pf)
  if rel.as_posix()in('native_main.cpp','joint_protocol.hpp','CMakeLists.txt'):continue
  before=blob(p).replace(pf.as_posix().encode(),folder.as_posix().encode());after=blob(folder/rel)
  if before==after:relation='whole_bytes_equal'
  else:relation=prove(rel,before,after);changed.append(rel.as_posix())
  rows.append(dict(file=rel.as_posix(),parent_sha256=pins[str(p)],current_sha256=pins[str(folder/rel)],relation=relation))
 assert len(rows)==77 and sorted(changed)==['connected_hardware_boundary.s','onexit_session.hpp','registration_contract.hpp']and len(rows)-len(changed)==74
 before=blob(pf/'connected_hardware_boundary.s');after=blob(folder/'connected_hardware_boundary.s');tests=[]
 for label,value in [('changed_first_body',after.replace(b'pushq %rbx',b'pushq %rax',1)),('wrong_second_target',after.replace(b'callq context_controls_guarded',b'callq mfc_connected_invoke_guarded')),('missing_separator',after[:len(before)]+after[len(before)+1:]),('extra_bytes',after+b'\n'),('changed_second_label',after.replace(b'context_controls_hardware_call',b'other_controls_hardware_call'))]:
  rejected=False
  try:prove(Path('connected_hardware_boundary.s'),before,value)
  except AssertionError:rejected=True
  assert rejected;tests.append(dict(name=label,rejected=True))
 p=out/'whole77-positive-domain.json';p.write_text(json.dumps(rows,indent=2)+'\n');pin(p);pin(__file__);pin(sys.executable);report=dict(passed=True,scope='Complete actual77 source files with74 whole byte equality+3 exact finite inverse relations; existing exclusion set exactly retained; no compiled reviewer execution',complete_positive_files=77,whole_equal=74,finite_inverses=3,exact_changed=changed,adverse_ASM_controls=tests,baseline_declared_previous_partition=dict(equal=75,inverse=2),physical_reviewer_executed=False,worker_executed=False,archive_reader_opened=False,accepted_function_credit=0,files=pins);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
