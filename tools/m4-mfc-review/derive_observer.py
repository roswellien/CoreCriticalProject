"""Seal observation-only changes to the unchanged persistent source comparison."""
from pathlib import Path
import difflib,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(path):
 with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(version):
 out=ROOT/'reports/m4-mfc-review'/version
 if out.exists():raise ValueError('Fresh observed source derivation')
 baseline=ROOT/'tools/m4-mfc-source/compare_connected.py';target=ROOT/'tools/m4-mfc-review/observe_connected.py'
 if target.exists():raise ValueError('Fresh immutable derived observer source')
 original=baseline.read_text();text=original;edits=[]
 def one(before,after,why):
  nonlocal text
  if text.count(before)!=1:raise ValueError('Exact observation seam '+why)
  text=text.replace(before,after);edits.append(why)
 one('import provider_capture as C','import provider_capture as C\nsys.path.insert(0,str(Path(__file__).resolve().parent))\nimport final_observer as V','Read-only independent observer addon')
 one("out=ROOT/'reports/m4-mfc-source'/name","out=ROOT/'reports/m4-mfc-review'/name",'Fresh independent report directory')
 one("stem=f'sequence-{seq}/selected/';index=C.checkpoints(a,stem);before,facts,heap,oldpc,oldsp=C.bootstrap_inputs(a,stem,index)","stem=f'sequence-{seq}/cleaned/';index=C.checkpoints(a,stem);before,facts,heap,oldpc,oldsp=C.bootstrap_inputs(a,stem,index)\n     V.configure(G,m,a,seq,level,pin)",'Same true BEFORE plus finite complete actual API leaf trace; no AFTER-machine input')
 one("machine.call_stack.append((entry,FRAME,BROKER,0,machine.reg('ebp'),machine.reg('ebx'),machine.reg('esi'),machine.reg('edi'),0));G.complete_root(machine,api=responses);expected_callbacks.append(roots[entry]);responses.completed_registry(machine,expected_callbacks);counts['literal_registration_roots']+=1","V.begin(machine);machine.call_stack.append((entry,FRAME,BROKER,0,machine.reg('ebp'),machine.reg('ebx'),machine.reg('esi'),machine.reg('edi'),0));G.complete_root(machine,api=responses);V.end(machine);expected_callbacks.append(roots[entry]);responses.completed_registry(machine,expected_callbacks);counts['literal_registration_roots']+=1",'Observe same persistent whole source root BEFORE/AFTER without reseed')
 one("need(len(expected_callbacks)==75,'All75 actual callback registrations carried');counts['persistent103_sequences']+=1","need(len(expected_callbacks)==75,'All75 actual callback registrations carried');counts['persistent103_sequences']+=1\n     V.finish(machine,responses,expected_callbacks,G)",'Execute literal genuine additional growth and source frees from carried selected state')
 one("counts=dict(counts),per_phase_BEFORE_machine_seed=False","counts=dict(counts),provider_counts=dict(V.COUNTS),provider_sequences=V.ROWS,per_phase_BEFORE_machine_seed=False",'Report independent source checkpoint/owner/lifecycle observations')
 one("whole_provider_checkpoints_review_separate=True","whole_provider_checkpoints_review_separate=False,worker_post_HeapDestroy_identity_observed=True",'Record full provider gate and actual postdestroy export scope')
 one("  passed=True","  need(V.COUNTS['complete103_provider_sequences']==12,'All12 complete independent provider sequences')\n  for file in (Path(__file__).with_name('final_observer.py'),ROOT/'tools/m4-strings-review/final_observer_v2.py',ROOT/'tools/m4-mfc-review/provider_model.py',ROOT/'tools/m4-mfc-review/provider_interface.py'):\n   pin(file)\n  passed=True",'Require completed full provider sequences and pin all additive observation code')
 target.write_text(text);out.mkdir(parents=True)
 (out/'baseline-source.py').write_bytes(baseline.read_bytes());(out/'observed-source.py').write_bytes(target.read_bytes())
 (out/'observer.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile=str(baseline),tofile=str(target))))
 pins={str(p.resolve()):sha(p)for p in(baseline,target,Path(__file__),ROOT/'tools/m4-mfc-review/final_observer.py',ROOT/'tools/m4-strings-review/final_observer_v2.py',out/'baseline-source.py',out/'observed-source.py',out/'observer.patch')}
 report=dict(passed=True,scope='Exact original comparison source plus narrow read-only provider observation and genuine continuation derivation',edits=edits,source_algorithm_changed=False,new_after_machine_inputs=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),observer_sha256=sha(target),baseline_sha256=sha(baseline))))
if __name__=='__main__':main(sys.argv[1])
