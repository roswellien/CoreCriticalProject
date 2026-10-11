"""Match the existing whole-page array type, without changing caller semantics."""
from pathlib import Path
import hashlib,json,shutil,sys
R=Path(__file__).resolve().parents[2];OLD=R/'reports/m4-version-source/original-preparation-r7'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-version-source'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 d=json.loads(pin(OLD/'report.json','287da1775f4fed6aefa8f0b07433e0c4921f8245f36d31fc57ecdcc83cfab7af').read_bytes());assert d['passed']
 for p,h in d['files'].items():pin(p,h)
 pin(R/'reports/m4-version-source/original-build-r7/build.json','7873362d06ac84d6b4c5bfacf018e2c9bb3c2d56ae0acefcbda9e4c0de1768b6');out.mkdir(parents=True);parents={}
 for p in OLD.iterdir():
  if p.is_file()and p.name not in('report.json','pins.json','failure.txt'):
   q=out/p.name;shutil.copyfile(p,q);parents[q.name]=p
 q=out/'reference.cpp';s=q.read_text();a='std::vector<unsigned char>common_bootstrap_pages(memory_size);copy_pages(common_bootstrap_pages);out.append("common-caller/bootstrap-pages.bin",common_bootstrap_pages.data(),common_bootstrap_pages.size());';b='auto common_bootstrap_pages=std::make_unique<std::array<std::uint8_t,memory_size>>();copy_pages(*common_bootstrap_pages);out.append("common-caller/bootstrap-pages.bin",common_bootstrap_pages->data(),common_bootstrap_pages->size());';assert s.count(a)==1;s=s.replace(a,b,1);q.write_text(s);pin(__file__);relations=[]
 for q in out.iterdir():
  if q.is_file():
   pin(q);p=parents[q.name];relations.append(dict(parent=str(p),child=str(q),parent_sha256=sha(p),sha256=sha(q),unchanged=p.read_bytes()==q.read_bytes()))
 report={k:v for k,v in d.items()if k not in('files','source_relations','parent_preparation_sha256','scope')};report.update(passed=True,scope='Original8 retains the exact one common external caller and all original6 guards; complete bootstrap page witness uses the existing whole fixed-array type; prepare/build only',parent_preparation_sha256=sha(OLD/'report.json'),source_relations=relations,compiler_fix_changes_caller_or_source_semantics=False,original_executed=False,native_executed=False,archive_reader_opened=False,files=pins);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=True,executed=False)))
if __name__=='__main__':main(sys.argv[1])
