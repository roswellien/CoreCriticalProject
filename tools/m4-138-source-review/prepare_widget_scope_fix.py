"""Immutable active-widget scope guard; retains legacy provider observer paths."""
from pathlib import Path
import ast, hashlib, json, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PARENT='8308fe8ceaaae3fbb07b2f7204bd167c495dbffd5f281fed95d83c2b4a90f7f8'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 pp=R/'reports/m4-joint-startup138-source/preparation-r3/report.json';assert sha(pp)==PARENT
 p=json.loads(pp.read_bytes());base=R/'tools/m4-joint-startup138/persistent_widgets.py';source=base.read_text();changes=[]
 def replace(old,new,count=1):
  nonlocal source
  assert source.count(old)==count;source=source.replace(old,new);changes.append(dict(old=old,new=new,count=count))
 replace('    def before_control(self, event, data):\n','    def before_control(self, event, data):\n        if not self.root:\n            return\n')
 replace('    def after_control(self, event, data):\n','    def after_control(self, event, data):\n        if not self.root:\n            return\n')
 replace("association and association.mode == 'component'", "association and association.root and association.mode == 'component'",4)
 replace('            if association:\n','            if association and association.root:\n',2)
 reverse=source
 for change in reversed(changes):
  assert reverse.count(change['new'])==change['count'];reverse=reverse.replace(change['new'],change['old'])
 assert reverse==base.read_text();ast.parse(source)
 helper=base.with_name('persistent_widgets_v2.py');assert not helper.exists();helper.write_text(source)
 entry=Path(p['entrypoint']);old=entry.read_text();before='import persistent_widgets as PW'
 after="_widget_spec=importlib.util.spec_from_file_location('current138_persistent_widgets',ROOT/'tools/m4-joint-startup138/persistent_widgets_v2.py')\nPW=importlib.util.module_from_spec(_widget_spec);_widget_spec.loader.exec_module(PW)"
 assert old.count(before)==1;text=old.replace(before,after);assert text.replace(after,before)==old
 out=pp.parent.parent/'preparation-r4';assert not out.exists();out.mkdir()
 files=dict(p['files']);files[str(pp)]=PARENT
 for name in('continuity138.py','final_observer138.py','final_observer138_v2.py','paired_exports.py','original-admission-delta.json'):
  target=out/name;target.write_bytes((entry.parent/name).read_bytes());files[str(target)]=sha(target)
 target=out/entry.name;target.write_text(text);files[str(target)]=sha(target)
 delta=out/'widget-scope-delta.json';delta.write_text(json.dumps(dict(before=before,after=after,helper_changes=changes,exact_inverse_restores_parent=True),indent=2)+'\n');files[str(delta)]=sha(delta)
 for path in(base,helper,Path(__file__).resolve()):files[str(path)]=sha(path)
 report=dict(p);report.update(parent_preparation=str(pp),parent_preparation_sha256=PARENT,entrypoint=str(target),scope='Unexecuted138 source preparation with widget association active only inside exact entered widget root; legacy provider events retain their observer paths',widget_active_scope_guard=True,files=files)
 receipt=out/'report.json';receipt.write_text(json.dumps(report,indent=2)+'\n')
 preflight=(R/'tools/m4-138-source-review/preflight_original_admission.py').read_text()
 assert preflight.count("PREP='"+PARENT+"'")==1
 preflight=preflight.replace("PREP='"+PARENT+"'","PREP='"+sha(receipt)+"'").replace('preparation-r3/report.json','preparation-r4/report.json')
 anchor="  current=entry.read_text();need(current.count(delta['new'])==1"
 insertion="  scope_delta=json.loads(pin(entry.parent/'widget-scope-delta.json').read_bytes());current_text=entry.read_text();need(current_text.count(scope_delta['after'])==1,'One exact explicit widget helper binding');restored=current_text.replace(scope_delta['after'],scope_delta['before']);need(restored==(ROOT/'reports/m4-joint-startup138-source/preparation-r3/compare_provider138.py').read_text(),'Widget binding inverse retains every prep3 predicate');need(Path(module.PW.__file__).resolve()==ROOT/'tools/m4-joint-startup138/persistent_widgets_v2.py','Exact additive active-widget helper')\n  current=restored;need(current.count(delta['new'])==1"
 assert preflight.count(anchor)==1;preflight=preflight.replace(anchor,insertion)
 check=R/'tools/m4-138-source-review/preflight_widget_scope.py';assert not check.exists();check.write_text(preflight);ast.parse(preflight)
 print(json.dumps(dict(preparation=str(receipt),sha256=sha(receipt),helper=str(helper),preflight=str(check))))
if __name__=='__main__':main()
