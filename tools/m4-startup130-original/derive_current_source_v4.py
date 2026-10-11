"""Repair only scalar diagnostic formatting; measured FS predicate unchanged."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 old=R/'tools/m4-startup130-original/format_source_v3.py';new=old.with_name('format_source_v4.py');assert not new.exists();body=old.read_text();a="eq(u(self.bytes(0x7ffde000,4))[0],actual['header'][5],'Actual compiled observer FS head matches literal entry/return head')";b="need(u(self.bytes(0x7ffde000,4))[0]==actual['header'][5],'Actual compiled observer FS head matches literal entry/return head')";assert body.count(a)==1;body=body.replace(a,b);ast.parse(body);new.write_text(body)
 oldagg=old.with_name('current_source_v3.py');newagg=old.with_name('current_source_v4.py');assert not newagg.exists();body=oldagg.read_text();assert body.count('format_source_v3.py')==1;body=body.replace('format_source_v3.py','format_source_v4.py');ast.parse(body);newagg.write_text(body)
 out=R/'reports/m4-startup130-original/combined-source-preparation-r3';assert not out.exists();out.mkdir(parents=True);hp=out/'hunks.json';hp.write_text(json.dumps([dict(old=a,new=b),dict(old='format_source_v3.py',new='format_source_v4.py')],indent=2)+'\n');paths=[old,new,oldagg,newagg,Path(__file__),hp,R/'reports/m4-startup130-original/format-source-preparation-r3/report.json',R/'reports/m4-startup130-original/combined-source-preparation-r2/report.json'];p=out/'report.json';p.write_text(json.dumps(dict(passed=True,scope='Only scalar diagnostic TypeError repaired; genuine scalar input/admission/predicate/source semantics unchanged',files={str(q.resolve()):sha(q)for q in paths},capture_reader_opened=False,executed=False),indent=2)+'\n');print(sha(p))
if __name__=='__main__':main()
