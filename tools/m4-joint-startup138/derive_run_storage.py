"""One new capture root/cwd; all current138 worker and structural gates retained."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name,review,review_sha):
 review=Path(review).resolve();assert sha(review)==review_sha;d=json.loads(review.read_bytes());assert d['passed']and d['hash_index_payload_limits_and_stable_close_unchanged']
 out=R/'reports/m4-joint-startup138'/name;assert not out.exists();out.mkdir();src=Path(__file__).with_name('run_v3.py');dst=src.with_name('run_v4.py');assert not dst.exists();t=src.read_text()
 changes=[
 ('from stages import run_stage,verify_stage','from stages_capture_storage import run_stage,verify_stage\nfrom paths_capture_storage import STORAGE_ROOT'),
 ("capture=out/level;stage=out/(level+'-stage')","capture=STORAGE_ROOT/'reports/m4-joint-startup138'/name/level;stage=out/(level+'-stage')"),
 ("required_outputs=[capture/'transport.json'],inputs=list(pins)","required_outputs=[capture/'transport.json'],inputs=list(pins),cwd=STORAGE_ROOT"),
 ("R/'tools/m4-crt-allocation-root/run_v2.py'","R/'tools/m4-crt-allocation-root/run_storage.py'")]
 for before,after in changes:assert t.count(before)==1;t=t.replace(before,after)
 anchor='  a=json.loads(pin(review,review_sha).read_bytes());'
 assert t.count(anchor)==1
 extra="  storage_review=json.loads(pin(Path("+repr(str(review))+"),"+repr(review_sha)+").read_bytes());need(storage_review['passed']and storage_review['hash_index_payload_limits_and_stable_close_unchanged'],'Actual strict storage-root admission')\n  for q,h in storage_review['files'].items():pin(q,h)\n"
 t=t.replace(anchor,extra+anchor);compile(t,str(dst),'exec');dst.write_text(t)
 pins={str(p.resolve()):sha(p)for p in(src,dst,review,Path(__file__),Path(sys.executable))};pins.update(d['files'])
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,parent_controller=str(src),current_controller=str(dst),whole_controller_relation='Only current storage module imports, exact capture path and worker cwd changed; added strict storage receipt pin closure',exact_changes=changes,storage_admission_sha256=review_sha,worker_build_sha256='7ca7a8a0a1f16513c5579890a2d71aab7a882016459b072669e9ab4f9922db47',worker_preparation_sha256='a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a',worker_code_changed=False,workers_launched=0,archives_opened=False,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),controller_sha256=sha(dst))))
if __name__=='__main__':main(sys.argv[1],sys.argv[2],sys.argv[3])
