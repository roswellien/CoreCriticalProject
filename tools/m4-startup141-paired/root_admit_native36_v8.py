"""ROOT review of exact whole-journal container normalization; no operand relaxation."""
from pathlib import Path
import ast,contextlib,hashlib,io,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 base=R/'reports/m4-startup141-paired';p=base/'ROOT-native36-admission-r6/report.json'
 assert sha(p)=='c4b35bc8a0ec2ae8358a5d11591a1f82e2bb5d350b879a13b1dc1f4d0631998f'
 A=json.loads(p.read_bytes());pins=dict(A['files']);pins[str(p)]=sha(p)
 prep=base/'native-journal-sequence-preparation-r1/report.json'
 assert sha(prep)=='de549669fa55f95ad4f60711264f1fdbc17c13151c6ebbc85970cffae179e3ff'
 F=json.loads(prep.read_bytes());assert F['prepared'] and not F['source_executed'] and not F['reader_opened']
 pins[str(prep)]=sha(prep)
 for path,h in F['files'].items():assert pins.setdefault(path,h)==h
 for path,h in pins.items():assert Path(path).suffix.lower()not in('.mwb','.mwi','.mwc','.zip','.pyc') and sha(path)==h
 inverse=json.loads((prep.parent/'exact-inverse.json').read_bytes());current=Path(inverse['current']).read_text()
 for d in reversed(inverse['replacements']):
  assert current.count(d['new'])==d['new_count'];current=current.replace(d['new'],d['old'])
 assert current==Path(inverse['parent']).read_text();ast.parse(Path(inverse['current']).read_text())
 td=R/'tools/m4-startup141-paired';cp=td/'native_journal_sequence_controls_v1.py'
 ns={'__file__':str(cp),'__name__':'ROOT_pure_journal_sequence'};exec(compile(cp.read_text(),str(cp),'exec'),ns)
 capture=io.StringIO()
 with contextlib.redirect_stdout(capture):ns['main']()
 result=ast.literal_eval(capture.getvalue().strip());assert result['passed'] and result['adverse_controls']==27 and len(set(result['names']))==27 and not result['reader_opened'] and not result['CPU_model_executed']
 out=base/'root-journal-sequence-controls-r1';assert not out.exists();out.mkdir();cq=out/'report.json'
 cq.write_text(json.dumps(dict(**result,independent_ROOT_review=True,accepted_function_credit=0,files={str(td/f):sha(td/f)for f in('native_journal_sequence_v1.py','native_journal_sequence_controls_v1.py')}),indent=2)+'\n')
 pins[str(cq)]=sha(cq);pins[str(Path(__file__).resolve())]=sha(__file__)
 for path,h in pins.items():assert sha(path)==h
 out=base/'ROOT-native36-admission-r7';assert not out.exists();out.mkdir()
 A.update(whole_ordered_journal_container_normalization_reviewed=True,journal_scalar_schema_and_order_unchanged=True,pure_journal_adverse_controls=27,files=pins)
 q=out/'report.json';q.write_text(json.dumps(A,indent=2)+'\n');print(sha(q))
if __name__=='__main__':main()
