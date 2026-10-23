"""ROOT adds the physical standard-library facade to the unchanged pair closure."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 base=R/'reports/m4-startup141-paired';p=base/'ROOT-structural54-admission-r1/report.json';assert sha(p)=='d2e050c0b3b2f86910089e7034d43585b055992311c7c791bb7c489e37fb9e36'
 A=json.loads(p.read_bytes());pins=dict(A['files']);pins[str(p)]=sha(p)
 for p in(Path(sys.base_prefix)/'Lib/struct.py',R/'tools/m4-startup141-paired/structural54_source_bootstrap_v1.py',Path(__file__).resolve()):pins[str(p)]=sha(p)
 for path,h in pins.items():assert sha(path)==h
 out=base/'ROOT-structural54-admission-r2';assert not out.exists();out.mkdir();q=out/'report.json';A.update(physical_struct_facade_preload_reviewed=True,cached_struct_bytecode_used=False,files=pins)
 q.write_text(json.dumps(A,indent=2)+'\n');print(sha(q))
if __name__=='__main__':main()
