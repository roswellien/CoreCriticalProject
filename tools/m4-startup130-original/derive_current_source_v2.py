"""Freeze finite registry response scope in the one-reader aggregate."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 old=R/'tools/m4-startup130-original/current_source.py';new=old.with_name('current_source_v2.py');assert not new.exists();body=old.read_text();hunks=[]
 def one(a,b):
  nonlocal body
  assert body.count(a)==1,a;body=body.replace(a,b);hunks.append(dict(old=a,new=b))
 one("R/'reports/m4-startup130-original/format-source-preparation-r1/report.json'","R/'reports/m4-startup130-original/format-source-preparation-r2/report.json'")
 one("'tools/m4-startup130-original/format_source.py'","'tools/m4-startup130-original/format_source_v2.py'")
 one("original_current_CRT_registration_relation='Separate physical no-growth callback-store/cursor-store relation from complete genuine preceding carried BEFORE; no AFTER input'","original_current_CRT_registration_relation='Separate physical callback/pointer/cursor-store relation from complete genuine preceding carried BEFORE and finite true HeapReAlloc scalar if growth occurs; no AFTER input or new unused growth-tail model claim'")
 new.write_text(body);out=R/'reports/m4-startup130-original/combined-source-preparation-r1';assert not out.exists();out.mkdir(parents=True);p=out/'hunks.json';p.write_text(json.dumps(hunks,indent=2)+'\n');pins={str(q.resolve()):sha(q)for q in [old,new,Path(__file__),p,R/'tools/m4-startup130-original/format_source_v2.py',R/'tools/m4-startup130-original/tree_source.py']};report=dict(passed=True,scope='One current original130 shared archive session prepared, not opened',planned_output='reports/m4-startup130-original/combined-source-r1',files=pins,archive_sessions=1,capture_reader_opened=False,executed=False);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(sha(p))
if __name__=='__main__':main()
