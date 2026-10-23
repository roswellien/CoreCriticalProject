"""ROOT finite literal heap publication input review; no whole provider-page claim."""
from pathlib import Path
import ast,contextlib,hashlib,io,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 base=R/'reports/m4-startup141-paired';p=base/'ROOT-native36-admission-r5/report.json'
 assert sha(p)=='a1add26d06e840cff2b0c1527982f80f35e6d39ab4fb6cc38b3c5e4eb619a8b0'
 A=json.loads(p.read_bytes());pins=dict(A['files']);pins[str(p)]=sha(p)
 prep=base/'native-heap-field-cut-preparation-r3/report.json'
 assert sha(prep)=='1954be0a92c91b77789ecedfbc52e15fa9d4720287d18aed15c81555a2ac90a1'
 F=json.loads(prep.read_bytes());assert F['prepared'] and not F['source_executed'] and not F['reader_opened']
 pins[str(prep)]=sha(prep)
 for path,h in F['files'].items():assert pins.setdefault(path,h)==h
 diag=base/'native-heap-field-diagnostic-r1/report.json'
 assert sha(diag)=='d13cadc4f572607680f17ac51f4938b7ddf46b39deba9e0cdc38272ec31d597f'
 D=json.loads(diag.read_bytes());pins[str(diag)]=sha(diag)
 for path,h in D.get('files',{}).items():assert pins.setdefault(path,h)==h
 for path,h in pins.items():assert Path(path).suffix.lower()not in('.mwb','.mwi','.mwc','.zip','.pyc') and sha(path)==h
 inverse=json.loads((prep.parent/'exact-inverse.json').read_bytes())
 for group in inverse.values():
  current=Path(group['current']).read_text();parent=Path(group['parent']).read_text()
  for d in reversed(group['replacements']):
   assert current.count(d['new'])==d['new_count'];current=current.replace(d['new'],d['old'])
  assert current==parent;ast.parse(Path(group['current']).read_text())
 td=R/'tools/m4-startup141-paired';ns={'__file__':str(td/'native_heap_field_controls_v2.py'),'__name__':'ROOT_pure_heap_fields'}
 exec(compile((td/'native_heap_field_controls_v2.py').read_text(),ns['__file__'],'exec'),ns)
 capture=io.StringIO()
 with contextlib.redirect_stdout(capture):ns['main']()
 result=ast.literal_eval(capture.getvalue().strip());assert result['passed'] and result['adverse_controls']==22 and len(set(result['names']))==22 and not result['reader_opened'] and not result['CPU_model_executed'] and not result['whole_page_claim']
 out=base/'root-heap-field-controls-r1';assert not out.exists();out.mkdir();cq=out/'report.json'
 cq.write_text(json.dumps(dict(**result,independent_ROOT_review=True,accepted_function_credit=0,files={str(td/f):sha(td/f)for f in('native_heap_field_cut_v1.py','native_heap_field_controls_v2.py')}),indent=2)+'\n')
 pins[str(cq)]=sha(cq);pins[str(Path(__file__).resolve())]=sha(__file__)
 for path,h in pins.items():assert sha(path)==h
 out=base/'ROOT-native36-admission-r6';assert not out.exists();out.mkdir()
 A.update(finite_heap_publication_scalars_reviewed=True,heap_provider_input_bytes=8,whole_heap_provider_page_claim=False,actual_bootstrap_publications_and_prior_write_exclusion_required=True,source_computed_scalar_conservation_required=True,files=pins)
 q=out/'report.json';q.write_text(json.dumps(A,indent=2)+'\n');print(sha(q))
if __name__=='__main__':main()
