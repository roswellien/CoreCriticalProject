"""Preserve failed build1 and fix only inline assembler statement boundaries."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-mfc1168-probe'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 parent=B/'preparation-r1';out=B/name;assert not out.exists();r=json.loads((parent/'report.json').read_bytes());assert sha(parent/'report.json')=='b274526caf9e808174ad8bb98b7824d3f1928c9e54580d1b38f5e5c2e979e4b8'
 out.mkdir();pins={}
 for p,h in r['files'].items():assert sha(p)==h;pins[p]=h
 for p in parent.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(p.read_bytes())
 p=out/'worker.cpp';s=p.read_text();a='__asm{fninit fldcw cw fxsave mixed_guest_fx}';assert s.count(a)==1;s=s.replace(a,'__asm {\n fninit\n fldcw cw\n fxsave mixed_guest_fx\n }');p.write_text(s)
 for p in out.iterdir():pins[str(p.resolve())]=sha(p)
 pins[str(Path(__file__).resolve())]=sha(__file__);pins[str(parent/'report.json')]=sha(parent/'report.json')
 r.update(parent_preparation_sha256=sha(parent/'report.json'),correction='Only inline assembler source statement separation; all physical instructions/pack/contracts unchanged',files=pins)
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main(sys.argv[1])
