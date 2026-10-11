"""Validate reservations once before commit, not again inside a shared region."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-mfc1168-probe'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 parent=B/'preparation-r3';out=B/name;assert not out.exists();r=json.loads((parent/'report.json').read_bytes());assert sha(parent/'report.json')=='f4bbf5051bf95f648736d020357bca4f7e853f10819282a436ea842e4edd7a73';out.mkdir();pins={}
 for p,h in r['files'].items():assert sha(p)==h;pins[p]=h
 for p in parent.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(p.read_bytes())
 p=out/'worker.cpp';s=p.read_text()
 for a in('mw34::original_broker::reserve_or_adopt(base);','mw34::original_broker::reserve_or_adopt(0x20000000);','mw34::original_broker::reserve_or_adopt(0x410000);'):assert s.count(a)==1;s=s.replace(a,'')
 p.write_text(s)
 for p in out.iterdir():pins[str(p.resolve())]=sha(p)
 pins[str(Path(__file__).resolve())]=sha(__file__);pins[str(parent/'report.json')]=sha(parent/'report.json');r.update(parent_preparation_sha256=sha(parent/'report.json'),correction='Exact all-region pre-CRT reservation validation remains in broker dispatch; remove duplicate validate_reserved after first page already commits shared5A region',files=pins)
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main(sys.argv[1])
