"""Correct API function type and retain actual complete borrowed stack input."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-mfc1168-probe'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 parent=B/'preparation-r5';out=B/name;assert not out.exists();r=json.loads((parent/'report.json').read_bytes());assert sha(parent/'report.json')=='415a2922441f0e95e299a139586ac1b6c67052ce94f4971aa3b6676ad2e49928';out.mkdir();pins={}
 for p,h in r['files'].items():assert sha(p)==h;pins[p]=h
 for p in parent.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(p.read_bytes())
 p=out/'worker.cpp';s=p.read_text();a='const void(*hooks[])()';assert s.count(a)==1;s=s.replace(a,'void(*const hooks[])()')
 a='if(tracing)trace_begin();const auto status=execute();';assert s.count(a)==1
 b='''dump("stack-before.bin",reinterpret_cast<void*>(0x20000000),65536);for(unsigned i=0;i<4;++i){const auto base=word<unsigned>(pack.data()+12+i*4104);dump("BEFORE/game-physical/"+std::to_string(base)+".bin",reinterpret_cast<void*>(base),4096);}const unsigned lock_cell=0x78037028+25*8;const unsigned lock_pointer=dword(lock_cell);const std::array<unsigned,4>lock_meta{lock_cell,lock_pointer,24,lock_pointer?1U:0U};dump("BEFORE/CRT-codepage-lock/meta.bin",lock_meta.data(),sizeof(lock_meta));if(lock_pointer)dump("BEFORE/CRT-codepage-lock/bytes.bin",reinterpret_cast<void*>(lock_pointer),24);
 if(tracing)trace_begin();const auto status=execute();'''
 s=s.replace(a,b);p.write_text(s)
 for p in out.iterdir():pins[str(p.resolve())]=sha(p)
 pins[str(Path(__file__).resolve())]=sha(__file__);pins[str(parent/'report.json')]=sha(parent/'report.json');r.update(parent_preparation_sha256=sha(parent/'report.json'),correction='API pointer return type corrected to void; actual full64KiB borrowed source stack/game pages and declared lock25 source-pointer/24B input retained before root',files=pins)
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main(sys.argv[1])
