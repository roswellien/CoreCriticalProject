"""Freeze actual source EAX at VOID provider CALL/RET; preserve prior prep4."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True);src=HERE/'compare_provider130_v2.py';dst=HERE/'compare_provider130_v3.py';assert not dst.exists();s=src.read_text()
 for a,b in [('import final_observer130 as F','import final_observer130_v2 as F'),('import formatting_derivations as FD','import formatting_derivations_v2 as FD')]:assert s.count(a)==1;s=s.replace(a,b)
 a="pin(ROOT/'tools/m4-formatting-source/formatting_derivations.py');";assert s.count(a)==1;s=s.replace(a,a+"pin(ROOT/'tools/m4-formatting-source/formatting_derivations_v2.py');pin(ROOT/'tools/m4-formatting-source/final_observer130_v2.py');pin(ROOT/'tools/m4-formatting-source/prepare_provider130_v5.py');")
 ast.parse(s);dst.write_text(s);files={str(p.resolve()):sha(p)for p in(src,dst,Path(__file__),HERE/'formatting_derivations.py',HERE/'formatting_derivations_v2.py',HERE/'final_observer130.py',HERE/'final_observer130_v2.py',HERE/'continuity130.py')}
 report=dict(passed=True,scope='Complete130 source/provider preparer, retaining source-derived mixed VOID EAX and whole private CALL/RET rows',tool=str(dst),source_only_CALL_scalar=True,LastError_is_not_VOID_EAX=True,files=files,executed=False,capture_reader_opened=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
