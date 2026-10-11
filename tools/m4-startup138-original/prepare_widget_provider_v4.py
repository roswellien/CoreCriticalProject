"""Bind source API PC separately from original ledger's unpopulated PC field."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2];base=Path(__file__).with_name('compare_widget_source_v3.py');text=base.read_text();changes=[]
def one(old,new):
 global text
 assert text.count(old)==1;pos=text.index(old);changes.append(dict(position=pos,old=old,new=new));text=text[:pos]+new+text[pos+len(old):]
one("CPU(model,list(w[:10]),'Whole actual source-defined provider API BEFORE CPU')", "need(w[9]==0,'Original producer API entry PC field explicitly unpopulated');eq(F.project(list(model.projected_cpu()),undefined)[:9],F.project(list(w[:10]),undefined)[:9],'All nine actually populated provider API BEFORE CPU words')")
one("CPU(model,list(w[10:20]),'Whole current original provider API first return CPU')", "need(w[19]==0 and model.cursor==w[25],'Unpopulated ledger AFTER PC with own exact source return-word binding');eq(F.project(list(model.projected_cpu()),undefined)[:9],F.project(list(w[10:20]),undefined)[:9],'All nine actual provider first-return CPU words')")
one("memory_output_seed=False));provider_index", "memory_output_seed=False,actual_API_PC_observed=False,source_target_bound_by_CALL_IAT_kind=True));provider_index")
reverse=text
for d in reversed(changes):
 p=d['position'];assert reverse[p:p+len(d['new'])]==d['new'];reverse=reverse[:p]+d['old']+reverse[p+len(d['new']):]
assert reverse==base.read_text();ast.parse(text);target=base.with_name('compare_widget_source_v4.py');assert not target.exists();target.write_text(text)
out=R/'reports/m4-startup138-original/widget-provider-preparation-r3';assert not out.exists();out.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
q=out/'report.json';q.write_text(json.dumps(dict(passed=True,exact_reverse_delta=True,source_execution=False,changes=changes,actual_API_PC_observed=False,complete_widget_gate=False,files={str(p.resolve()):sha(p)for p in(base,target,Path(__file__))}),indent=2)+'\n');print(q,sha(q))
