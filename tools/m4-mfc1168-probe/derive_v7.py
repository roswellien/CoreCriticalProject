"""Bind lock25 pointer lookup to physical4*index arithmetic."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-mfc1168-probe'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 parent=B/'preparation-r6';out=B/name;assert not out.exists();r=json.loads((parent/'report.json').read_bytes());assert sha(parent/'report.json')=='48486b0de07743eca8a8f9f9f60cbdcc199c45c521d1f9f361d17259272b25da';out.mkdir();pins={}
 for p,h in r['files'].items():assert sha(p)==h;pins[p]=h
 for p in parent.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(p.read_bytes())
 p=out/'worker.cpp';s=p.read_text();a='const unsigned lock_cell=0x78037028+25*8;';assert s.count(a)==1;p.write_text(s.replace(a,'const unsigned lock_cell=0x78037028+25*4;'))
 rows=json.loads((out/'instruction-contracts.json').read_bytes())['instructions'];proof=[x for x in rows if x['pc']in(0x7800105c,0x78001064,0x780012a4)];assert len(proof)==3;(out/'lock25-address-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
 for p in out.iterdir():pins[str(p.resolve())]=sha(p)
 pins[str(Path(__file__).resolve())]=sha(__file__);pins[str(parent/'report.json')]=sha(parent/'report.json');r.update(parent_preparation_sha256=sha(parent/'report.json'),correction='Exact physical CRT25 lock table has DWORD stride4, retained three physical operand proofs. No source code or source input is altered.',files=pins)
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main(sys.argv[1])
