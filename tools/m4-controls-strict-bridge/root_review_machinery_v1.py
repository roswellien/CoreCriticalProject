"""ROOT source-only bridge review receipt; no configuration or acceptance admission."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 folder=R/'reports/m4-controls-strict-bridge';pure=folder/'root-pure-preflight-r1/report.json'
 P=json.loads(pure.read_bytes());assert P['pure_controls_completed'] and P['control_count']==27 and not P['checker_or_configurator_imported'] and not P['actual_composer_or_DB_opened']
 pins=dict(P['files']);pins[str(pure)]=sha(pure)
 exp=R/'reports/m4-controls-terminal-composite/composite-expander-preparation-r3/report.json'
 assert sha(exp)=='8f2c36fa99dfb6b253d4cd428723d4a3a9d48675d42e246ffa4db0ffdedc997b'
 E=json.loads(exp.read_bytes());pins[str(exp)]=sha(exp)
 for p,h in E['files'].items():assert pins.setdefault(p,h)==h
 current=R/'tools/m4-controls-terminal-composite/expand_composite_inventory_v3.py';text=current.read_text()
 for d in reversed(E['changes']):
  assert text.count(d['after'])==1;text=text.replace(d['after'],d['before'])
 assert text==current.with_name('expand_composite_inventory_v2.py').read_text()
 controls=R/'reports/m4-controls-terminal-composite/root-composite-inventory-controls-r1/report.json'
 assert sha(controls)=='389bf53132d6f59cc5249eaa8816cc05c766284b41cf6a29017636c73b5275fd'
 pins[str(controls)]=sha(controls);pins[str(Path(__file__).resolve())]=sha(__file__)
 for p,h in pins.items():
  assert sha(p)==h
  if Path(p).suffix=='.py':ast.parse(Path(p).read_text())
 out=folder/'root-machinery-review-r1';assert not out.exists();out.mkdir()
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Finite strict producer bridge and distinct composite inventory source review only',controls_composite_source_bridge_reviewed=True,controls_composite_inventory_expander_reviewed=True,required_gates=39,required_baseline_predicates=841,pure_graph_controls=27,pure_inventory_controls=20,actual_composite_or_inventory_opened=False,configuration_or_checker_executed=False,criteria_delta_allowances_reviewed=False,acceptance_admitted=False,accepted_function_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main()
