"""Select the precise measured-FS adapter in the one-reader aggregate."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 old=R/'tools/m4-startup130-original/current_source_v2.py';new=old.with_name('current_source_v3.py');assert not new.exists();body=old.read_text();hunks=[]
 for a,b in [('format-source-preparation-r2','format-source-preparation-r3'),('format_source_v2.py','format_source_v3.py')]:
  assert body.count(a)==1;body=body.replace(a,b);hunks.append(dict(old=a,new=b))
 ast.parse(body);new.write_text(body);out=R/'reports/m4-startup130-original/combined-source-preparation-r2';assert not out.exists();out.mkdir(parents=True);p=out/'hunks.json';p.write_text(json.dumps(hunks,indent=2)+'\n')
 paths=[old,new,Path(__file__),p,R/'reports/m4-startup130-original/format-source-preparation-r3/report.json',R/'reports/m4-startup130-original/current-source-preparation-r1/report.json',R/'tools/m4-startup130-original/format_source_v3.py',R/'tools/m4-startup130-original/tree_source.py'];pins={str(p.resolve()):sha(p)for p in paths}
 p=out/'report.json';p.write_text(json.dumps(dict(passed=True,scope='Unexecuted one-reader current original130 aggregate with finite genuine measured FS input adapter',files=pins,capture_reader_opened=False,executed=False,failed_prior_receipt= str((R/'reports/m4-startup130-original/combined-source-r1/report.json').resolve())),indent=2)+'\n');print(sha(p))
if __name__=='__main__':main()
