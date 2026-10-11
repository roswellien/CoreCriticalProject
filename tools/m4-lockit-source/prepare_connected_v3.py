"""Add explicit scheduling audit to the same complete native reader."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 prior=ROOT/'reports/m4-lockit-source/connected-preparation-r2/report.json';assert sha(prior)=='a5b2eb40992e461e091be29536de976a5008420270e77e6026220cd47db0c975';d=json.loads(prior.read_bytes())
 for p,h in d['files'].items():assert sha(p)==h
 s=Path(d['comparer']).read_text();s=s.replace('import responses as R','import responses as R\nimport continuity as A');assert s.count('lockit_rows=[]')==1;s=s.replace('lockit_rows=[]','lockit_rows=[];continuity_rows=[]');needle="   a=D.DirectSet(Path(native_report).parent/level/'transport.json',pin)";assert s.count(needle)==1;s=s.replace(needle,needle+"\n   continuity_rows.append(dict(level=level,**A.audit(a,m,J)));pin(ROOT/'tools/m4-lockit-source/continuity.py')");needle="('Lockit-source-derivations.json',lockit_rows)";assert s.count(needle)==1;s=s.replace(needle,needle+",('native-continuity.json',continuity_rows)");needle='native_DllMain_credit=False,files=PINS';assert s.count(needle)==1;s=s.replace(needle,'native_DllMain_credit=False,native_continuity=continuity_rows,files=PINS');target=ROOT/'tools/m4-lockit-source/compare_connected_v3.py';assert not target.exists();target.write_text(s);out=ROOT/'reports/m4-lockit-source'/name;assert not out.exists();out.mkdir(parents=True);files=dict(d['files']);files.update({str(prior):sha(prior),str(target):sha(target),str(Path(__file__).resolve()):sha(__file__),str(ROOT/'tools/m4-lockit-source/continuity.py'):sha(ROOT/'tools/m4-lockit-source/continuity.py')});report=dict(passed=True,scope='Same native reader verifies all scheduler/host continuity and literal persistent source124 semantics; no duplicate >11GB reader',comparer=str(target),native_compared=False,initializer_credit=False,files=files);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),comparer=str(target))))
if __name__=='__main__':main(sys.argv[1])
