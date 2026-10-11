"""Authenticate frozen candidate files-map lineage and retain a stale path label."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
FILES={}

def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def read(relative,expected):
 path=(ROOT/relative).resolve();assert sha(path)==expected,relative
 FILES[str(path)]=expected
 data=json.loads(path.read_bytes());assert data['passed'] is True,relative
 return path,data

def main(name):
 out=ROOT/'reports/m4-joint-startup124-root'/name;assert not out.exists();out.mkdir(parents=True)
 p3,r3=read('reports/m4-lockit-native/preparation-r3/report.json','4c28406fb33cc34976b754ceedd0203540be80535c557a79b322407aae342b7d')
 p4,r4=read('reports/m4-lockit-native/preparation-r4/report.json','f090bad6da0e6e28090218f04e9f98ebe358e31ac6901a266d8e29ffc45ff608')
 p5,r5=read('reports/m4-lockit-native/preparation-r5/report.json','965ea738333677c308749108b7f0b211772e89d4dd5e2ed14ea561cb63d0bdc1')
 pj,rj=read('reports/m4-joint-startup124/preparation-r5/report.json','7a2e383ab47bdb668e56181cdc3eec1c75ebf03437e5f9b9ac675861370a85c7')
 pb,rb=read('reports/m4-joint-startup124/build-r4/build.json','05a198d319f2e3ee2259b998a8989db23df0b20afd40416fb185e7a0b1d17c30')
 assert r4['previous_native_preparation']==str(p3) and r4['previous_native_preparation_sha256']==FILES[str(p3)]
 assert r4['files'][str(p3)]==r5['files'][str(p3)]==FILES[str(p3)]
 assert r5['files'][str(p4)]==FILES[str(p4)]
 # The executed additive writer carried the old path label but set the new hash.
 assert r5['previous_native_preparation']==str(p3) and r5['previous_native_preparation_sha256']==FILES[str(p4)]
 assert rj['native_preparation_sha256']==FILES[str(p5)] and rj['files'][str(p5)]==FILES[str(p5)]
 assert rb['preparation_sha256']==FILES[str(pj)] and Path(rj['native_library']).parent==p5.parent
 native_sources={path:value for path,value in r5['files'].items() if Path(path).parent==p5.parent and Path(path).suffix in ('.cpp','.hpp','.inc')}
 assert set(native_sources)=={str(p.resolve()) for p in p5.parent.iterdir() if p.suffix in ('.cpp','.hpp','.inc')}
 for path,value in native_sources.items():
  assert sha(path)==value,path
  FILES[path]=value
 for relative in ('tools/m4-lockit-native/prepare_owned_v5.py','tools/m4-lockit-native/prepare_fs_v4.py','tools/m4-joint-startup124/derive_refresh_v4.py'):
  path=(ROOT/relative).resolve();FILES[str(path)]=sha(path)
 FILES[str(Path(__file__).resolve())]=sha(__file__)
 result=dict(passed=True,scope='Exact immutable candidate5 files-map lineage through native4/native3 and final joint5/build4; no source or worker changes',authenticated_preparation_edges=4,authenticated_native_generations=3,stale_metadata_path_discrepancies=1,stale_metadata_field='nativeprep5.previous_native_preparation',stale_metadata_path=str(p3),stale_metadata_SHA_belongs_to=str(p4),authoritative_native_previous_preparation=str(p4),authoritative_native_previous_preparation_sha256=FILES[str(p4)],authoritative_files_map_consistent=True,generated_native_sources_checked=len(native_sources),executed_receipts_modified=False,generated_code_modified=False,native_worker_modified=False,initializer_credit=False,files=FILES)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=True,report=str(out/'report.json'),sha256=sha(out/'report.json'))))

if __name__=='__main__':main(sys.argv[1])
