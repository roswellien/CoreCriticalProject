from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
def main():
 p=H/'static.py';t=p.read_text();needle="'source_access(a,v,n,true)'";assert t.count(needle)==1;t=t.replace(needle,"';source_access(a,v,n,true)'")
 target=H/'static_v2.py';assert not target.exists();target.write_text(t,encoding='utf-8',newline='\n')
 out=R/'reports/m4-fs-control-audit/static-r1';(out/'report.json').write_text(json.dumps({'passed':False,'native_executed':False,'error':'Reviewer matcher selected check_source_access substring rather than the committed source_access call. It did not establish an implementation failure.','script_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'replacement':'static_v2.py'},indent=2)+'\n')
if __name__=='__main__':main()
