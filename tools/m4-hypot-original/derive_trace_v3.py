"""Additive /WX repair of a trace-local identifier shadowing the worker owner."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-hypot-original'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 parent=B/'trace-preparation-r2';out=B/name;assert not out.exists();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 old=json.loads(pin(parent/'report.json','e0d6e8c9c71428b87e33c316dbf6298c75d1a0a7733aa256e3eabdba64391990').read_bytes())
 for p,h in old['files'].items():pin(p,h)
 failed=pin(B/'trace-build-r1/build.json');assert not json.loads(failed.read_text(encoding='utf-8-sig'))['passed'];pin(B/'trace-build-r1/compile.log');out.mkdir()
 for p in parent.iterdir():
  if p.name not in('report.json','pins.json'):(out/p.name).write_bytes(pin(p).read_bytes())
 p=out/'hypot_trace.hpp';text=p.read_text();assert len(re.findall(r'\bowner\b',text))==7;p.write_text(re.sub(r'\bowner\b','source_owner',text))
 pin(__file__);pin(sys.executable)
 for p in out.iterdir():pin(p)
 report={**old,'scope':old['scope']+'; trace-local source_owner avoids inherited global owner shadowing under /WX','previous_trace_preparation_sha256':sha(parent/'report.json'),'identifier_only_rename_count':7,'files':pins};q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');pin(q);(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
