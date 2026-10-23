"""Code-only immutable chronology correction, no imports or input readers."""
from pathlib import Path
import hashlib,json,difflib
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-original141-source/controller-preparation-r3';assert not out.exists();out.mkdir()
 files={};rows=[]
 specs=[('widget_source141_v2.py','widget_source141_v3.py',[
  ('if phase==136:','if phase==139:'),
  ('Exact complete closed original138 observations','Exact complete closed original141 observations'),
  ("scope='Current138 six-sequence", "scope='Current141 six-sequence")]),
  ('replay_original141_v2.py','replay_original141_v3.py',[("'widget_source141_v2.py'","'widget_source141_v3.py'")])]
 for old,new,replacements in specs:
  p=R/'tools/m4-original141-source'/old;q=p.with_name(new);assert not q.exists();before=p.read_text();after=before
  for a,b in replacements:assert after.count(a)==1;after=after.replace(a,b)
  q.write_text(after);assert q.read_text()==after
  for a,b in reversed(replacements):assert after.count(b)==1;after=after.replace(b,a)
  assert after==before
  a=before.splitlines(True);b=q.read_text().splitlines(True);d=[]
  for tag,i,j,k,l in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
   if tag!='equal':d.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(a[i:j]),child=''.join(b[k:l])))
  rows.append(dict(parent=str(p),child=str(q),exact_whole_inverse=True,deltas=d))
  files[str(p)]=sha(p);files[str(q)]=sha(q)
 files[str(Path(__file__).resolve())]=sha(Path(__file__))
 (out/'inverse.json').write_text(json.dumps(rows,indent=2)+'\n');files[str(out/'inverse.json')]=sha(out/'inverse.json')
 report=dict(prepared_only=True,source_execution=False,imports_executed=False,canonical_reader_opened=False,ordinary_export_opened=False,initializer_credit=0,whole_inverse_files=rows,semantic_delta='Cleanup after current terminal widget phase139 instead of inherited136; exact current selected order already enforced. Two evidence captions identify141. Aggregate invokes only fresh corrected helper.',files=files)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q))))
if __name__=='__main__':main()
