"""Derive bounded existing compiler/writer drivers with namespace only edits."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 paths=[Path(__file__)];hunks=[]
 for fn in('build.ps1','run.py'):
  p=R/'tools/m4-cosine-original'/fn;q=R/'tools/m4-hypot-original'/fn;assert not q.exists();s=p.read_text(encoding='utf-8-sig')
  for a,b in [('m4-cosine-original','m4-hypot-original'),('original-cosine1','original-hypot1')]:
   n=s.count(a);s=s.replace(a,b);hunks.append(dict(file=fn,old=a,new=b,occurrences=n))
  if fn.endswith('.py'):ast.parse(s)
  q.write_text(s);paths+=[p,q]
 out=R/'reports/m4-hypot-original/driver-preparation-r1';assert not out.exists();out.mkdir(parents=True);hp=out/'hunks.json';hp.write_text(json.dumps(hunks,indent=2)+'\n');paths.append(hp);p=out/'report.json';p.write_text(json.dumps(dict(passed=True,scope='Existing x86 compiler and bounded writer drivers with namespace-only edits',archive_reader_opened=False,files={str(p.resolve()):sha(p)for p in paths}),indent=2)+'\n');print(sha(p))
if __name__=='__main__':main()
