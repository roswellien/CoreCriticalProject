"""Inventory every operand overlapping the finite provider page domain."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True)
 src=HERE/'compare_provider130_v5.py';dst=HERE/'compare_provider130_v6.py';assert not dst.exists();s=src.read_text()
 a='if 0x78145000<=r[1]and r[1]+r[3]<=0x78147000';assert s.count(a)==2;s=s.replace(a,'if r[1]<0x78147000 and r[1]+r[3]>0x78145000')
 a="pin(ROOT/'tools/m4-formatting-source/prepare_provider130_v7.py');";assert s.count(a)==1;s=s.replace(a,a+"pin(ROOT/'tools/m4-formatting-source/prepare_provider130_v8.py');")
 ast.parse(s);dst.write_text(s)
 files={str(p.resolve()):sha(p)for p in(src,dst,Path(__file__),HERE/'formatting_derivations.py',HERE/'formatting_derivations_v2.py',HERE/'formatting_derivations_v3.py',HERE/'final_observer130.py',HERE/'final_observer130_v2.py',HERE/'continuity130.py')}
 report=dict(passed=True,scope='Complete130 provider source-domain overlap export includes boundary-crossing operands',tool=str(dst),domain=[0x78145000,0x78147000],predicate='address<domain_end and address+width>domain_begin',source_and_API_transport_inventory=True,files=files,executed=False,capture_reader_opened=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
