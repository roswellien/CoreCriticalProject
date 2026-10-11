"""Seal explicit authentic input-page association before source execution."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 prior=ROOT/'reports/m4-lockit-source/connected-preparation-r1/report.json';assert sha(prior)=='089130e740fbc6323aee13255ee917c69c13fdb4326b8a87b42d47de7c9ce29a';d=json.loads(prior.read_bytes())
 for p,h in d['files'].items():assert sha(p)==h
 old=Path(d['comparer']);s=old.read_text();needle="      if page not in before['memory']:before['memory'][page]=initial_page(page)";assert s.count(needle)==1;s=s.replace(needle,needle+"\n      if page in (0x7810a000,0x78145000,0x78146000):equal(before['memory'][page],initial_page(page),'Explicit complete original provider input page association'+hex(page))")
 target=ROOT/'tools/m4-lockit-source/compare_connected_v2.py';assert not target.exists();target.write_text(s);out=ROOT/'reports/m4-lockit-source'/name;assert not out.exists();out.mkdir(parents=True);files=dict(d['files']);files.update({str(prior):sha(prior),str(target):sha(target),str(Path(__file__).resolve()):sha(__file__)})
 report=dict(passed=True,scope='Explicit true bootstrap BEFORE provider pages must match authentic declared whole source inputs before execution',comparer=str(target),native_compared=False,initializer_credit=False,files=files);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),comparer=str(target))))
if __name__=='__main__':main(sys.argv[1])
