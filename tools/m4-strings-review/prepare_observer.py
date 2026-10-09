"""Freeze an exact source-computation derivative with observation-only hooks."""
from pathlib import Path
import hashlib,json,difflib
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'tools/m4-strings-source/compare_connected.py'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=source.read_text();new=old
changes=[
 ('import provider_capture as C','import provider_capture as C\nimport sys\nsys.path.insert(0,str(Path(__file__).resolve().parent))\nimport final_observer as V'),
 ("out=ROOT/'reports/m4-strings-source'/name","out=ROOT/'reports/m4-strings-review'/name"),
 ("material=B.material(static,pin)","material=B.material(static,pin)\n  for path,digest in material['prefix'].F.PHYSICAL.items():pin(path,digest)"),
 ("stem=f'sequence-{seq}/selected/';index=C.checkpoints(a,stem);before,facts,heap,oldpc,oldsp=C.bootstrap_inputs(a,stem,index)","stem=f'sequence-{seq}/cleaned/';index=C.checkpoints(a,stem);before,facts,heap,oldpc,oldsp=C.bootstrap_inputs(a,stem,index)\n     V.configure(G,m,a,seq,level,pin)"),
 ("machine.call_stack.append((entry,FRAME,BROKER,0,machine.reg('ebp'),machine.reg('ebx'),machine.reg('esi'),machine.reg('edi'),0));G.complete_root(machine,api=responses);expected_callbacks.append(roots[entry])","V.begin(machine);machine.call_stack.append((entry,FRAME,BROKER,0,machine.reg('ebp'),machine.reg('ebx'),machine.reg('esi'),machine.reg('edi'),0));G.complete_root(machine,api=responses);V.end(machine);expected_callbacks.append(roots[entry])"),
 ("need(len(expected_callbacks)==43,'All43 actual callback registrations carried');counts['persistent71_sequences']+=1","need(len(expected_callbacks)==43,'All43 actual callback registrations carried');counts['persistent71_sequences']+=1\n     V.finish(machine,responses,expected_callbacks,G)"),
 ("passed=True\n except Exception", "pin(ROOT/'tools/m4-strings-review/final_observer.py');pin(ROOT/'tools/m4-strings-review/source-observation-diff.patch');pin(ROOT/'tools/m4-strings-review/source-observation-receipt.json');passed=True\n except Exception"),
 ("report=dict(passed=passed,scope=", "report=dict(provider_counts=dict(V.COUNTS),provider_rows=V.ROWS,passed=passed,scope="),
 ("whole_provider_checkpoints_review_separate=True", "whole_provider_checkpoints_review_separate=False,independent_provider_observation=True,complete_resource_cleanup=True")
]
for a,b in changes:
 assert new.count(a)==1,(a,new.count(a));new=new.replace(a,b)
out=ROOT/'tools/m4-strings-review';out.mkdir(exist_ok=True)
target=out/'observe_connected.py';target.write_text(new)
(out/'source-observation-diff.patch').write_text(''.join(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile=str(source),tofile=str(target))))
(out/'source-observation-receipt.json').write_text(json.dumps(dict(original_source=str(source),original_source_sha256=sha(source),derived_source=str(target),derived_source_sha256=sha(target),purpose='Exact frozen source computation, same one bootstrap BEFORE, all finite responses; added read-only observation hooks plus genuine source replay/free continuation',semantic_game_computation_changes=False,checkpoint_machine_seed=False),indent=2)+'\n')
print(sha(target))
