"""Immutable NameError correction and exact giant-map scoped lineage support."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=Path(__file__).with_name('acceptance138.py');s=p.read_text();changes=[]
def change(before,after):
 global s
 assert s.count(before)==1,before;s=s.replace(before,after);changes.append(dict(before=before,after=after))
change('import acceptance138_storage as storage','import acceptance138_storage_v2 as storage')
change('PINS=None;DIRECT={}','PINS=None;SCOPES=None;DIRECT={}')
change('if stream:return storage.read_report(path,register)','if stream:return storage.read_report(path,register,SCOPES)')
change("target=normalized(str(Path(path).resolve()));return any(normalized(str(Path(p).resolve()))==target and identity==h for field in FIELDS for p,identity in report.get(field,{}).items())","target=normalized(str(Path(path).resolve()))\n for field in FIELDS:\n  values=report.get(field,{})\n  if isinstance(values,storage.ScopedFiles):\n   if values.get(target)==h:return True\n  elif any(normalized(str(Path(p).resolve()))==target and identity==h for p,identity in values.items()):return True\n return False")
change('global PINS\n','global PINS,SCOPES\n')
change("PINS=storage.Union(out/'physical-union.sqlite');passed=False","PINS=storage.Union(out/'physical-union.sqlite');SCOPES=storage.ScopeIndex(out/'receipt-scopes.sqlite');passed=False")
change("'has','Path','re')","'has','Path','re','normalized')")
change("Path(storage.__file__),PARENT_CHECKER","Path(storage.__file__),Path(storage.base.__file__),ROOT/'tools/m4-138-controls-review/expand_accepted138_union.py',PARENT_CHECKER")
change("closure=PINS.verify(lambda n:","SCOPES.close();register(SCOPES.path,sha(SCOPES.path));DIRECT[str(SCOPES.path)]=sha(SCOPES.path)\n  closure=PINS.verify(lambda n:")
change('  PINS.close()\n','  SCOPES.close();PINS.close()\n')
q=Path(__file__).with_name('acceptance138_v2.py');assert not q.exists();q.write_text(s)
c=Path(__file__).with_name('configure_acceptance138.py');t=c.read_text();assert t.count('import acceptance138 as A')==1;t=t.replace('import acceptance138 as A','import acceptance138_v2 as A');qc=c.with_name('configure_acceptance138_v2.py');assert not qc.exists();qc.write_text(t)
import ast,hashlib,json
ast.parse(s);ast.parse(t)
out=R/'reports/m4-138-controls-review/acceptance138-checker-preparation-r2';assert not out.exists();out.mkdir();delta=out/'source-delta.json';delta.write_text(json.dumps(dict(changes=changes,baseline_predicates_unchanged=True,normalized_namespace_dependency_explicit=True,exact_scoped_provenance=True),indent=2)+'\n')
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
restored=s
for row in reversed(changes):assert restored.count(row['after'])==1;restored=restored.replace(row['after'],row['before'])
assert restored==p.read_text()
report=out/'report.json';report.write_text(json.dumps(dict(passed=True,scope='Source-only immutable checker correction/scoped provenance preparation; no acceptance',inverse_restores_parent_checker=True,initializer_credit=0,files={str(x.resolve()):sha(x)for x in[p,q,c,qc,delta,Path(__file__),q.with_name('acceptance138_storage_v2.py'),q.with_name('expand_accepted138_union.py')]}),indent=2)+'\n');print(sha(report))
