"""ROOT exact generated-view receipt closure; input and semantic scope unchanged."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 base=R/'reports/m4-startup141-paired';td=R/'tools/m4-startup141-paired'
 parent=base/'ROOT-original7-layout-admission-r1/report.json';assert sha(parent)=='2d25418cd60aa4ae4cdd0ce7d91eb40c1b016b3225832991fe164ec3d10c127e'
 A=json.loads(parent.read_bytes());pins=dict(A['files']);pins[str(parent)]=sha(parent)
 prep=base/'original7-layout-consumer-preparation-r2/preparation-only.json';assert sha(prep)=='9629bc6c1cfc635b96051e065ef513f68daf3d7f1183f47fe0031d73c011db2a'
 P=json.loads(prep.read_bytes());assert P['prepared_only']and P['exact_whole_inverse']and P['input_final_conservation_unchanged'];pins[str(prep)]=sha(prep)
 for p,h in P['files'].items():assert pins.setdefault(p,h)==h
 I=json.loads((prep.parent/'inverse.json').read_bytes());text=(td/'consume_original7_child_view_v2.py').read_text()
 for c in reversed(I['replacements']):assert text.count(c['new'])==1;text=text.replace(c['new'],c['old'])
 assert text==(td/'consume_original7_child_view_v1.py').read_text();ast.parse((td/'consume_original7_child_view_v2.py').read_text())
 pins[str(Path(__file__).resolve())]=sha(__file__)
 for p,h in pins.items():assert sha(p)==h
 out=base/'ROOT-original7-layout-admission-r2';assert not out.exists();out.mkdir();A.update(files=pins,generated_view_output_sha_receipt_closure_reviewed=True)
 q=out/'report.json';q.write_text(json.dumps(A,indent=2)+'\n');print(sha(q))
if __name__=='__main__':main()
