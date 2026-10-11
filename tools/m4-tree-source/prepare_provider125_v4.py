"""Select genuine live backing observations before source cleanup."""
from pathlib import Path
import ast,hashlib,json
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 src=HERE/'compare_provider125_v3.py';dst=HERE/'compare_provider125_v4.py';out=ROOT/'reports/m4-tree-source/provider125-preparation-r4'
 if dst.exists()or out.exists():raise ValueError('Fresh live-observation revision')
 s=src.read_text();old="p=stem+'locale-allocation-'+str(owner['generation']);raw=bytes.fromhex(owner['source_final_hex']);"
 if old not in s:raise ValueError('Exact live backing anchor')
 s=s.replace(old,"p=f'sequence-{seq}/selected/locale-allocation-'+str(owner['generation']);raw=bytes.fromhex(owner['source_final_hex']);")
 s=s.replace("pin(ROOT/'tools/m4-tree-source/prepare_connected125_v3.py');","pin(ROOT/'tools/m4-tree-source/prepare_connected125_v3.py');pin(ROOT/'tools/m4-tree-source/prepare_provider125_v4.py');")
 ast.parse(s);dst.write_text(s);out.mkdir(parents=True)
 (out/'report.json').write_text(json.dumps(dict(passed=True,scope='Same strict provider model; private live tree pages observed in selected stage before actual cleanup, complete cleanup checked separately',execution_credit=False,files={str(p):sha(p)for p in(src,dst,Path(__file__).resolve())}),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main()
