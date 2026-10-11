"""Unchanged measured37 fixture with fresh corrected service library lineage."""
from pathlib import Path
import hashlib,json,shutil,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(service_build,service_build_sha,name):
 out=R/'reports/m4-constructor-native'/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or h==v,str(p);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 parent=R/'reports/m4-constructor-native/fixture-preparation-r5'
 d=json.loads(pin(parent/'report.json','31b3f6b5ce2f8af0bb43dbcf7b983629c6978f2d1fcf71c25f14efc6750682a1').read_bytes())
 service=R/'reports/m4-constructor-native/service-preparation-r8/report.json'
 s=json.loads(pin(service,'7437fa44e96c0ad7ec07431b8b69c00e08e63a8be139827bf7e1e11caaa53140').read_bytes())
 build=pin(R/service_build,service_build_sha);b=json.loads(build.read_bytes())
 assert all(x['passed']for x in(d,s,b))and b['preparation_sha256']==sha(service)
 for p,h in d['files'].items():pin(p,h)
 for p,h in b['files'].items():pin(p,h)
 out.mkdir(parents=True);relations=[]
 for p in parent.rglob('*'):
  if p.is_file()and p.name!='report.json':
   dst=out/p.relative_to(parent);dst.parent.mkdir(parents=True,exist_ok=True);pin(p,d['files'][str(p.resolve())]);shutil.copyfile(p,dst);pin(dst);assert p.read_bytes()==dst.read_bytes();relations.append(dict(parent=str(p),child=str(dst),sha256=sha(dst),whole_bytes_equal=True))
 for level in('O0','O2'):
  v=b['levels'][level];d['levels'][level]['service_library']=v['library'];d['levels'][level]['service_library_sha256']=v['library_sha256'];pin(v['library'],v['library_sha256'])
 d['native_include']=str(service.parent);d['native_library']=str(service.parent/'registry_library.cpp')
 d['service_preparation_sha256']=sha(service);d['service_build_sha256']=sha(build)
 d['parent_fixture_preparation_sha256']=sha(parent/'report.json')
 d['whole_fixture_sources_unchanged']=True;d['fixture_source_relations']=relations
 d['only_service_provenance_changed']=True;d['native_executed']=False;d['initializer_credit']=0
 pin(__file__);d['files']=pins
 q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(*sys.argv[1:])
