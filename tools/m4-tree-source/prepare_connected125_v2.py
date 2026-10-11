"""Add explicit executed lineage and exact publication-key adapter."""
from pathlib import Path
import ast,hashlib,json
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;PINS={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def edit(src,dst,replacements):
 p=HERE/src;PINS[str(p)]=sha(p);s=p.read_text()
 for old,new in replacements:
  if old not in s:raise ValueError('Exact revision anchor '+old[:150])
  s=s.replace(old,new)
 ast.parse(s);target=HERE/dst
 if target.exists():raise ValueError('Fresh revision')
 target.write_text(s);PINS[str(target)]=sha(target)
def main():
 out=ROOT/'reports/m4-tree-source/connected125-preparation-r2'
 if out.exists():raise ValueError('Fresh receipt')
 out.mkdir(parents=True)
 edit('final_observer125.py','final_observer125_v2.py',[("proof['owner_CALL_pc']","proof['allocation_CALL_pc']")])
 edit('compare_connected125.py','compare_connected125_v2.py',[
  ('import header_derivations as H','import header_derivations as H\nimport identity_records as Q'),
  ('continuity_rows=[];tree_rows=[]','continuity_rows=[];tree_rows=[];executed_lineage={}'),
  ("need(nr['passed'],'All current actual native125 sequences complete')","need(nr['passed'],'All current actual native125 sequences complete');executed_lineage=Q.lineage(native_report,nr,pin)"),
  ('report=dict(passed=passed,scope=','report=dict(passed=passed,executed_lineage=executed_lineage,scope='),
  ("'final_observer125.py'","'final_observer125_v2.py'")])
 edit('compare_provider125.py','compare_provider125_v2.py',[
  ('import final_observer125 as F','import final_observer125_v2 as F'),
  ("'final_observer125.py'","'final_observer125_v2.py'")])
 PINS[str(Path(__file__).resolve())]=sha(__file__)
 (out/'report.json').write_text(json.dumps(dict(passed=True,execution_credit=False,files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main()
