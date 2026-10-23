"""Exact producer namespace correction; all semantic projection gates retained."""
from pathlib import Path
import ast,hashlib,json,shutil,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 parent=ROOT/'reports/m4-joint-startup138-source/preparation-r9';out=parent.parent/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip');v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 report=json.loads(pin(parent/'report.json').read_bytes());assert report['passed'] and report['initializer_credit']==0
 for p,h in report['files'].items():pin(p,h)
 build=json.loads(pin(ROOT/'reports/m4-joint-startup138/build-r5/build.json','7ca7a8a0a1f16513c5579890a2d71aab7a882016459b072669e9ab4f9922db47').read_bytes())
 producer=ROOT/'reports/m4-fps-native/service-preparation-r3';texts={}
 for name0 in ('session_impl.inc','locale_batch_operations.inc'):
  p=producer/name0;texts[name0]=pin(p,build['files'][str(p)]).read_text()
 assert 'binding->research_projections_.push_back({9,root,0x5ac11e,0x5bb52c,0x1decb0,0x78004a36,frame,ret});'in texts['session_impl.inc']
 assert 'sink("registry-research-projections.bin",std::as_bytes(std::span(projections)),user);'in texts['session_impl.inc']
 assert 'binding->dump(sink,user)'in texts['session_impl.inc']
 assert 'sink("locale-research-projections.bin",std::as_bytes(std::span(research_projections_)),context);'in texts['locale_batch_operations.inc']
 entry=parent/'compare_provider138.py';old=entry.read_text();before="association.prove_projection_rows(a.data(stem+'registry-research-projections.bin'))";after=before.replace('registry-','locale-');assert old.count(before)==1
 current=old.replace(before,after,1);assert current.replace(after,before,1)==old;ast.parse(current)
 out.mkdir()
 for p in parent.iterdir():
  if p.is_file()and p.name!='report.json':shutil.copyfile(p,out/p.name);pin(out/p.name)
 (out/'compare_provider138.py').write_text(current);pin(out/'compare_provider138.py');pin(__file__);pin(sys.executable)
 delta=dict(old=before,new=after,position=old.index(before));(out/'projection-namespace-delta.json').write_text(json.dumps(delta,indent=2)+'\n');pin(out/'projection-namespace-delta.json')
 result=dict(passed=True,scope='Exact physical producer namespace key correction only; entire tag9 literal source list equality retained',entrypoint=str(out/'compare_provider138.py'),parent_preparation_sha256=sha(parent/'report.json'),exact_inverse_restores_parent=True,all_prior_gates_retained=True,writer_executed=False,capture_archive_reader_opened=False,source_execution_performed=False,initializer_credit=0,delta=delta,files=pins)
 q=out/'report.json';q.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
