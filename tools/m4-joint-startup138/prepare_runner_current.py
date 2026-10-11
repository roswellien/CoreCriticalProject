"""Fresh run_v3 file, byte-identical to frozen run_v2, current build5 binds."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-joint-startup138'/name;assert not out.exists();out.mkdir();old=R/'reports/m4-joint-startup138/controller-preparation-r3/report.json';d=json.loads(old.read_bytes());source=Path(d['controller']);target=R/'tools/m4-joint-startup138/run_v3.py';assert not target.exists();target.write_bytes(source.read_bytes());assert sha(source)==sha(target)==d['controller_sha256'];pins=dict(d['files']);pins[str(old.resolve())]=sha(old);pins[str(target.resolve())]=sha(target);pins[str(Path(__file__).resolve())]=sha(__file__);pins[str(Path(sys.executable).resolve())]=sha(sys.executable);d.update(controller=str(target.resolve()),controller_sha256=sha(target),parent_controller=str(source.resolve()),parent_controller_sha256=sha(source),prior_controller_preparation=str(old.resolve()),prior_controller_preparation_sha256=sha(old),controller_byte_identical=True,files=pins);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
