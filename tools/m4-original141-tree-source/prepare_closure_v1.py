"""Current tree source static closure and physical chronology preflight only."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-original141-tree-source/closure-preparation-r1';out.mkdir();files={};excluded=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or h==v,(str(p),h,v);assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 parent=pin(R/'reports/m4-startup138-original/inherited-source-r5/report.json','7024af25138f109143adfd72db01b58f3bd58e9a22d8c772fda0e983d18d3eb4');old=json.loads(parent.read_bytes());assert old['passed'];tree=[c for c in old['cases']if c['kind']=='tree'];assert [c['sequence']for c in tree]==list(range(6))
 for c in tree:
  p=pin(c['receipt'],c['sha256']);j=json.loads(p.read_bytes());assert j['passed']
  for f,h in j['files'].items():
   q=Path(f)
   if q.is_relative_to(R)and q.suffix.lower()in('.py','.json')and q.name!='transport.json':pin(q,h)
   else:excluded.append(dict(path=f,sha256=h,reason='Historical capture/cache/binary provenance not current source code or contract; not reused as current tree input'))
 for f in ('report.json','instruction-contracts.json'):pin(R/'reports/m4-tree-source/recovery-r1'/f)
 pin(R/'reports/m4-tree-source/game-callbacks-r1/callbacks.json');pin(R/'reports/m4-tree-source/dynamic-contracts-r1/normal-contracts.json','fbdd6e79dc26328ae2bd6a2e02d264971eaa190251d589f085904ffd9486829c')
 p=pin(R/'reports/m4-original141-tree-source/preparation-r2/report.json','4cb5546572cfde539fcf20bc66eabf0d982155a77349bef8d0ac8e936c6bb41d');j=json.loads(p.read_bytes())
 for f,h in j['files'].items():pin(f,h)
 order=json.loads(pin(R/'reports/m4-original141/source-preparation-r6/selected-order.json').read_bytes());assert len(order)==141 and order[86]['entry']==0x4b7f70
 prior=json.loads(pin(R/'reports/m4-startup138-original/preparation-r8/report.json','9bd1ef9049eccaeb9f87e81f38e001d0d1c805f077c75a8563fc08ec0e67b161').read_bytes())['selected_order'];assert [r for r in order if r['entry']not in(0x4103f0,0x410440,0x459b40)]==prior and prior[83]['entry']==0x4b7f70
 for f in ('tree_source_v2.py','run_ordinary_v1.py'):ast.parse(pin(R/'tools/m4-original141-tree-source'/f).read_text(encoding='utf-8'))
 pin(R/'tools/m4-startup131-original/export_reader.py');pin(__file__)
 p=out/'historical-input-exclusions.json';p.write_text(json.dumps(excluded,indent=2)+'\n',encoding='utf-8');pin(p)
 report=dict(passed=True,prepared_only=True,exact_current_order_without_three_constructors_recovers_entire138=True,tree_phase=86,source_case_extent_required=6,strict_current_export_pending=True,physical_source_and_contract_closure_rehashed=True,ordinary_reader_opened=False,canonical_reader_opened=False,worker_launched=False,accepted_function_credit=0,files=files)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main()
