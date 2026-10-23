"""ROOT finite source-predicted FS input and physical constructor lineage review."""
from pathlib import Path
import ast,contextlib,hashlib,io,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 base=R/'reports/m4-startup141-paired';td=R/'tools/m4-startup141-paired'
 parent=base/'ROOT-native36-admission-r8/report.json'
 assert sha(parent)=='012f13fae39029a24255eb64509ba93d40ccb9bc1ae73fa3915ccf367aabbe99'
 A=json.loads(parent.read_bytes());pins=dict(A['files']);pins[str(parent)]=sha(parent)
 prep=base/'native-input-provenance-derivative-preparation-r2/report.json'
 assert sha(prep)=='c2bf65fba0d085bbb449b028ba990aae4fc60a9e76accf4132b0160b36979971'
 P=json.loads(prep.read_bytes());assert P['prepared']and not P['source_executed']and not P['controls_executed']and P['exact_source14_adapter7_inverses']
 pins[str(prep)]=sha(prep)
 for p,h in P['files'].items():assert pins.setdefault(p,h)==h
 for p,h in pins.items():assert Path(p).suffix.lower()not in('.mwb','.mwi','.mwc','.zip','.pyc')and sha(p)==h
 for group in json.loads((base/'native-input-provenance-derivative-preparation-r1/exact-inverse.json').read_bytes()):
  text=(td/group['current']).read_text()
  for change in reversed(group['replacements']):
   assert text.count(change['new'])==change['new_count'];text=text.replace(change['new'],change['old'])
  assert text==(td/group['parent']).read_text();ast.parse((td/group['current']).read_text())
 runtime=(R/'tools/m4-runtime/runtime.cpp').read_text();header=(R/'tools/m4-runtime/runtime.hpp').read_text()
 scope=(R/'reports/m4-startup141-runway/service-preparation-r2/session_impl.inc').read_text()
 component=(R/'reports/m4-constructor-native/preparation-r7/component.cpp').read_text()
 assert 'static constexpr std::uint32_t seh_end = 0xffffffff;'in header
 assert 'image_.memory.store<std::uint32_t>(policy_.teb, seh_end);'in runtime
 assert 'binding->fs_expected_==m4_runtime::Runtime::seh_end&&r.memory().load<unsigned>(r.fs_base())==m4_runtime::Runtime::seh_end'in scope
 assert component.index('session.constructor_scope(s,root,true)')<component.index('checkpoint("before")')<component.index('literal::body(entry)')
 linkage=td/'prove_constructor_entry_linkage_v3.py';assert sha(linkage)=='6895de529b303062070ecae9c4beeb7c19af92fed77ecb71448efa3d39d86585'
 text=linkage.read_text();old="out=R/'reports/m4-startup141-paired/constructor-entry-linkage-r2'";assert text.count(old)==1
 text=text.replace(old,"out=R/'reports/m4-startup141-paired/root-constructor-entry-linkage-r1'")
 ns={'__file__':str(linkage),'__name__':'ROOT_exact_physical_linkage'};exec(compile(text,str(linkage),'exec'),ns);ns['main']()
 lp=base/'root-constructor-entry-linkage-r1/report.json';L=json.loads(lp.read_bytes());assert L['passed']and len(L['cases'])==2
 pins[str(lp)]=sha(lp)
 for p,h in L['files'].items():assert pins.setdefault(p,h)==h
 native=json.loads((R/'reports/m4-startup141-source/combined-source-provider-r6/report.json').read_bytes())
 assert native['executed_lineage']['build_sha256']=='ba1f699354fc2a14eb5dcc3bbfa4497e9ceb4ce01786e75cd95430f6c58de1bc'
 cp=td/'native_input_provenance_controls_v1.py';ns={'__file__':str(cp),'__name__':'ROOT_pure_FS_inputs'};exec(compile(cp.read_text(),str(cp),'exec'),ns)
 captured=io.StringIO()
 with contextlib.redirect_stdout(captured):ns['main']()
 result=ast.literal_eval(captured.getvalue().strip());assert result['passed']and result['adverse_controls']==23 and len(set(result['names']))==23 and not result['reader_opened']and not result['source_execution']
 out=base/'root-native-input-provenance-controls-r1';assert not out.exists();out.mkdir();cq=out/'report.json'
 cq.write_text(json.dumps(dict(**result,independent_ROOT_review=True,source_prediction_guard_before_checkpoint_physically_linked=True,accepted_function_credit=0,files={str(td/f):sha(td/f)for f in('native_input_provenance_v1.py','native_input_provenance_controls_v1.py')}),indent=2)+'\n')
 pins[str(cq)]=sha(cq);pins[str(Path(__file__).resolve())]=sha(__file__)
 for p,h in pins.items():assert sha(p)==h
 out=base/'ROOT-native36-admission-r9';assert not out.exists();out.mkdir()
 A.update(files=pins,sourcepredicted_FS4_guard_and_restoration_reviewed=True,actual_prior_checkpoint_has_zero_surviving_nonphase_domains=True,whole_TIB_claim=False,second_CPU_owner_carry_claim=False,physical_constructor_entry_linkage_ROOT_receipt=str(lp),pure_FS_input_adverse_controls=23)
 q=out/'report.json';q.write_text(json.dumps(A,indent=2)+'\n');print(sha(q))
if __name__=='__main__':main()
