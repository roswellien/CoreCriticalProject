"""Expose precise broker reservation facts; preserve failed preparation2."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-mfc1168-probe'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 parent=B/'preparation-r2';out=B/name;assert not out.exists();r=json.loads((parent/'report.json').read_bytes());assert sha(parent/'report.json')=='c55a4f865d3e332d4dd7430e16ce401784504235ef6dfc4e6cb3ed090127bafb';out.mkdir();pins={}
 for p,h in r['files'].items():assert sha(p)==h;pins[p]=h
 for p in parent.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(p.read_bytes())
 p=out/'original_broker.hpp';s=p.read_text();a='"Internal child lacks exact broker NOACCESS reservation base="+std::to_string(base)';b=a+'+" allocation="+std::to_string(reinterpret_cast<std::uintptr_t>(info.AllocationBase))+" region="+std::to_string(reinterpret_cast<std::uintptr_t>(info.BaseAddress))+" bytes="+std::to_string(info.RegionSize)+" state="+std::to_string(info.State)+" type="+std::to_string(info.Type)+" protect="+std::to_string(info.AllocationProtect)';assert s.count(a)==1;p.write_text(s.replace(a,b))
 for p in out.iterdir():pins[str(p.resolve())]=sha(p)
 pins[str(Path(__file__).resolve())]=sha(__file__);pins[str(parent/'report.json')]=sha(parent/'report.json');r.update(parent_preparation_sha256=sha(parent/'report.json'),correction='Diagnostic only exact physical broker reserved-region facts',files=pins)
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main(sys.argv[1])
