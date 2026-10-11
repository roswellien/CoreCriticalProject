"""Rebind the unchanged strict structural runner to actual growth-guard build5."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-joint-startup138'/name;assert not out.exists();out.mkdir();pp=R/'reports/m4-joint-startup138/preparation-r4/report.json';bp=R/'reports/m4-joint-startup138/build-r5/build.json';old=R/'reports/m4-joint-startup138/controller-preparation-r2/report.json';script=R/'tools/m4-joint-startup138/run_v2.py';assert sha(pp)=='a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a'and sha(bp)=='7ca7a8a0a1f16513c5579890a2d71aab7a882016459b072669e9ab4f9922db47';d=json.loads(old.read_bytes());assert sha(script)==d['controller_sha256'];assert json.loads(bp.read_bytes())['preparation_sha256']==sha(pp)
 pins={str(p.resolve()):sha(p)for p in(pp,bp,old,script,Path(__file__),Path(sys.executable),R/'tools/m4-pipeline/stages.py',R/'tools/m4-crt-allocation-root/run_v2.py')};d.update(build_path=str(bp.resolve()),build_sha256=sha(bp),preparation_path=str(pp.resolve()),preparation_sha256=sha(pp),prior_controller_preparation=str(old.resolve()),prior_controller_preparation_sha256=sha(old),controller_byte_identical=True,scope='Unexecuted exact138 structural runner, unchanged executed run_v2 code rebound to actual same-Context source-owned growth guard build5',files=pins,writer_executed=False,capture_archive_reader_opened=False,initializer_credit=0);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
