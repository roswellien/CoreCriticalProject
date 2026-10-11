"""Record actual named API image owners and borrowed lock endpoint bytes."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-mfc1168-probe'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 parent=B/'preparation-r9';out=B/name;assert not out.exists();r=json.loads((parent/'report.json').read_bytes());assert sha(parent/'report.json')=='4a5cbb36f47e18b2fd412335951f36df05b4b1d4a1a25f527027bcefbaf143eb';out.mkdir();pins={}
 for p,h in r['files'].items():assert sha(p)==h;pins[p]=h
 for p in parent.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(p.read_bytes())
 p=out/'worker.cpp';s=p.read_text();a='dump("named-API/"+std::to_string(i)+"-entry64.bin",reinterpret_cast<void*>(named_targets[i]),64);';assert s.count(a)==1
 new=a+'MEMORY_BASIC_INFORMATION am{};require(VirtualQuery(expected,&am,sizeof(am))==sizeof(am),"Actual named API target page identity");const std::array<unsigned,8>identity{reinterpret_cast<unsigned>(owner),named_targets[i],reinterpret_cast<unsigned>(am.BaseAddress),static_cast<unsigned>(am.RegionSize),am.State,am.Protect,am.Type,reinterpret_cast<unsigned>(am.AllocationBase)};dump("named-API/"+std::to_string(i)+"-owner-metadata.bin",identity.data(),sizeof(identity));'
 s=s.replace(a,new)
 a='domain("AFTER/domain");dump("stack-after.bin"';assert s.count(a)==1;s=s.replace(a,'domain("AFTER/domain");dump("AFTER/CRT-codepage-lock/bytes.bin",reinterpret_cast<void*>(lock_pointer),24);dump("stack-after.bin"');p.write_text(s)
 for p in out.iterdir():pins[str(p.resolve())]=sha(p)
 pins[str(Path(__file__).resolve())]=sha(__file__);pins[str(parent/'report.json')]=sha(parent/'report.json');r.update(parent_preparation_sha256=sha(parent/'report.json'),correction='Actual named API owner handle/allocation/page identity is emitted, and complete borrowed lock25 AFTER endpoint is retained. Source and coherent root inputs unchanged.',files=pins)
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main(sys.argv[1])
