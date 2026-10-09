"""Additive immutable source/artifact identities before a local repair."""
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def bind(p):
 p=Path(p).resolve();return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha(p)}
out=Path(sys.argv[1]).resolve();assert out.is_relative_to(ROOT/'reports/m4-fp-numeric-max') and not out.exists();out.mkdir(parents=True)
sources=[]
for p in (ROOT/'tools/m4-fp-numeric-max').glob('*'):
 if p.is_file():
  target=out/'sources'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);sources.append({'original':bind(p),'preserved':bind(target)})
existing=[]
for directory in sys.argv[2:]:
 p=Path(directory).resolve();assert p.is_relative_to(ROOT/'reports/m4-fp-numeric-max') and p!=out
 existing.extend(bind(x) for x in p.rglob('*') if x.is_file())
report={'source_copies':sources,'existing_immutable_bindings':existing,'preservation_script':bind(__file__)}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'sources':len(sources),'existing_files':len(existing),'output':str(out)}))
