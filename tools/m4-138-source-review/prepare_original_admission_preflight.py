"""Independently bind/reverse-check prep3 and create bounded definition preflight."""
from pathlib import Path
import ast, hashlib, json, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PREP='8308fe8ceaaae3fbb07b2f7204bd167c495dbffd5f281fed95d83c2b4a90f7f8'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 pp=R/'reports/m4-joint-startup138-source/preparation-r3/report.json';assert sha(pp)==PREP
 p=json.loads(pp.read_bytes());oldpp=R/'reports/m4-joint-startup138-source/preparation-r2/report.json'
 assert sha(oldpp)==p['parent_preparation_sha256']=='0f4ddf4df9576aa132388e22c26dff01f1abbed59e4975dd8818a42800bec26d'
 old=json.loads(oldpp.read_bytes());entry=Path(p['entrypoint']);delta_path=entry.parent/'original-admission-delta.json'
 assert sha(delta_path)==p['files'][str(delta_path)]
 delta=json.loads(delta_path.read_bytes());text=entry.read_text();prior=Path(old['entrypoint']).read_text()
 assert text.count(delta['new'])==1 and text.replace(delta['new'],delta['old'])==prior
 for name in ('continuity138.py','final_observer138.py','final_observer138_v2.py','paired_exports.py'):
  assert (entry.parent/name).read_bytes()==(Path(old['entrypoint']).parent/name).read_bytes()
 validator=R/'tools/m4-startup138-original/validate_v3.py';vtext=validator.read_text();vtree=ast.parse(vtext);tree=ast.parse(text)
 expected=None;metadata=None
 for node in ast.walk(tree):
  if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='required_original'for t in node.targets):
   assert isinstance(node.value,ast.Call)and node.value.func.id=='dict'
   expected={k.arg:ast.literal_eval(k.value)for k in node.value.keywords}
 for node in ast.walk(vtree):
  if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='report'for t in node.targets):
   assert isinstance(node.value,ast.Call)and node.value.func.id=='dict';metadata={k.arg:k.value for k in node.value.keywords}
 assert expected and metadata
 for field,value in expected.items():
  if field in('passed','build_sha256','preparation_sha256'):continue
  assert ast.literal_eval(metadata[field])==value,(field,value)
 assert expected['build_sha256']in vtext and expected['preparation_sha256']in vtext
 for marker in("counts['phases']==828","counts['widget_actual_root_phases']==42","counts['widget_whole_source_page_endpoints']==114264", "counts['widget_whole_CRT_phase_page_endpoints']==105984", "counts['widget_whole_nonstack_carried_page_relations']==55896", "counts['widget_exact_MFC_CRT_transition_page_relations']==768", "counts['widget_actual_stdcall_RETURN_relations']*2==counts['widget_complete_GDI_boundary_sides']"):
  assert marker in vtext,marker
 assert text.index('required_original=dict(')<text.index('ori=D.DirectSet(')
 assert text.index("original_counts['widget_exact_MFC_CRT_transition_page_relations']==768")<text.index('ori=D.DirectSet(')
 base=R/'tools/m4-138-source-review/preflight_helper_fix.py';preflight=base.read_text()
 assert preflight.count("PREP='"+old['files'].get(str(oldpp),'0f4ddf4df9576aa132388e22c26dff01f1abbed59e4975dd8818a42800bec26d')+"'")==1
 preflight=preflight.replace("PREP='0f4ddf4df9576aa132388e22c26dff01f1abbed59e4975dd8818a42800bec26d'","PREP='"+PREP+"'").replace('preparation-r2/report.json','preparation-r3/report.json')
 marker="  need(module.EX.selected('sequence-0/Widget/root-4252240/carried-before/State.bin'),'Complete current Widget equality targets exported')"
 extra="""  delta_path=pin(entry.parent/'original-admission-delta.json')
  delta=json.loads(delta_path.read_bytes());parent=pin(ROOT/'reports/m4-joint-startup138-source/preparation-r2/compare_provider138.py')
  current=entry.read_text();need(current.count(delta['new'])==1 and current.replace(delta['new'],delta['old'])==parent.read_text(),'Independent exact inverse retains every parent source gate')
  need(current.index('required_original=dict(')<current.index('ori=D.DirectSet(') and current.index("original_counts['widget_exact_MFC_CRT_transition_page_relations']==768")<current.index('ori=D.DirectSet('),'Complete original identity/count guards before canonical reader')
  pin(ROOT/'tools/m4-startup138-original/validate_v3.py','@VALIDATOR@')
  pin(ROOT/'tools/m4-138-source-review/prepare_original_admission_preflight.py','@SELF@')""".replace('@VALIDATOR@',sha(validator)).replace('@SELF@',sha(__file__))
 assert preflight.count(marker)==1;preflight=preflight.replace(marker,marker+'\n'+extra)
 target=R/'tools/m4-138-source-review/preflight_original_admission.py';assert not target.exists();target.write_text(preflight);ast.parse(preflight)
 print(json.dumps(dict(passed=True,exact_inverse_restores_parent=True,validator_metadata_matches=True,all_helpers_byte_identical=True,entry=str(entry),preflight=str(target),preflight_sha256=sha(target),archive_reader_opened=False,worker_launched=False,initializer_credit=0)))
if __name__=='__main__':main()
