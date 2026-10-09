"""Preserve literal sources and immutable evidence before the next local derivative."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fp-numeric-max-carry'
out=Path(sys.argv[1]).resolve();assert out.parent==BASE and not out.exists();out.mkdir()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
bindings={};copies=[]
for p in (ROOT/'tools/m4-fp-numeric-max-carry').rglob('*'):
 if p.is_file():
  q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());h=sha(p);assert sha(q)==h;copies.append({'original_path':str(p),'preserved':str(q),'build_sha256':h})
for directory in (BASE,*ROOT.glob('build/m4-nmx-carry-*')):
 for p in directory.rglob('*'):
  if p.is_file() and not p.is_relative_to(out) and 'compiler-temp' not in p.parts:bindings[str(p.resolve())]=sha(p)
prereqs=[]
for rel in ('reports/m4-fp-numeric-max-host-boundary/author-review-r1','reports/m4-fp-numeric-max-host-boundary/independent-compiled-r1','reports/m4-fp-numeric-max-host-boundary/independent-boundary-finding-r1'):
 p=ROOT/rel;d=json.loads((p/'pins.json').read_text());bindings[str(p/'report.json')]=sha(p/'report.json');bindings[str(p/'pins.json')]=sha(p/'pins.json')
 for name,h in d['files'].items():assert sha(name)==h,(name,h);bindings[name]=h
 prereqs.append({'report':str(p/'report.json'),'sha256':sha(p/'report.json'),'pins':str(p/'pins.json'),'pins_sha256':sha(p/'pins.json')})
builds=[{'path':str(BASE/name/'build.json'),'sha256':sha(BASE/name/'build.json')} for name in ('native-baseline-r1','native-repair-r2')]
manifest={'source_copies':copies,'existing_immutable_bindings':bindings,'build':builds,'preservation_script':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},'prerequisites':prereqs,'reason':'Before NEW canonical all11 FP shadow-byte admission guard; frozen hostr3/baseline/C1-only repair and actual malformed-IE alias failure remain literal','original_executed':False}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'manifest_sha256':sha(out/'manifest.json'),'sources':len(copies),'immutable_bindings':len(bindings)}))
