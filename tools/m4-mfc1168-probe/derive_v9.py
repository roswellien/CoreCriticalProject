"""Declare MASM's FS access for the coherent actual root TEB snapshot."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-mfc1168-probe'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 parent=B/'preparation-r8';out=B/name;assert not out.exists();r=json.loads((parent/'report.json').read_bytes());assert sha(parent/'report.json')=='150eb230de1f2cde738b72d485cb79358ac310a89024988c6d46c88ba673c135';out.mkdir();pins={}
 for p,h in r['files'].items():assert sha(p)==h;pins[p]=h
 for p in parent.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(p.read_bytes())
 p=out/'reference_x86.asm';s=p.read_text();assert s.count('.code\n')==1;p.write_text(s.replace('.code\n','.code\nASSUME fs:NOTHING\n'))
 for p in out.iterdir():pins[str(p.resolve())]=sha(p)
 pins[str(Path(__file__).resolve())]=sha(__file__);pins[str(parent/'report.json')]=sha(parent/'report.json');r.update(parent_preparation_sha256=sha(parent/'report.json'),correction='MASM FS:NOTHING declaration permits the actual FS:[18h] TEB boundary copy. Source, inputs and probe observations otherwise identical.',files=pins)
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main(sys.argv[1])
