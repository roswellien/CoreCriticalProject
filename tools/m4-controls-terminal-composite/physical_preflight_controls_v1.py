"""Pure syntax/finite inverse controls; never runs the physical prover/main."""
from pathlib import Path
import ast, hashlib, json, sys
R=Path(__file__).resolve().parents[2]
def need(value,why):
 if not value:raise ValueError(why)
def run(name):
 files={};trees={}
 for leaf in('build_v3.py','finalize45_v3.py','legacy_four_physical_v1.py','legacy_four_physical_v2.py'):
  p=R/'tools/m4-controls-terminal-composite'/leaf;raw=p.read_bytes();files[str(p)]=hashlib.sha256(raw).hexdigest();trees[leaf]=ast.parse(raw)
 scope={'need':need};nodes=[n for n in trees['legacy_four_physical_v2.py'].body if isinstance(n,ast.FunctionDef)and n.name in('inverse','literal_assignments')];assert len(nodes)==2;scope['ast']=ast;exec(compile(ast.Module(body=nodes,type_ignores=[]),'<only finite inverse/literal helpers>','exec'),scope)
 controls=[];old='BEGIN original source END';new='BEGIN readonly repair END';deltas=[('original source','readonly repair')]
 assert scope['inverse'](new,deltas)==old;controls.append('Exact one-site whole inverse positive')
 for label,text in [('Absent replacement',old),('Duplicated replacement',new+' readonly repair')]:
  try:scope['inverse'](text,deltas)
  except ValueError:controls.append(label+' rejected')
  else:raise AssertionError(label)
 assert scope['inverse'](new+' arbitrary unrelated byte',deltas)!=old;controls.append('Whole inverse rejects arbitrary intervening source delta by parent equality')
 literal='old="before"\nnew="after"\n';assert scope['literal_assignments'](literal,('old','new'))=={'old':'before','new':'after'};controls.append('Literal-only schema positive')
 for label,value in [('Executable RHS','old=unknown_call()\nnew="after"\n'),('Missing literal','old="before"\n')]:
  try:scope['literal_assignments'](value,('old','new'))
  except (ValueError,TypeError):controls.append(label+' rejected without call execution')
  else:raise AssertionError(label)
 # Exactly the preserved v1->v2 four finite substitutions, whole text inverse.
 source1=(R/'tools/m4-controls-terminal-composite/legacy_four_physical_v1.py').read_text();source2=(R/'tools/m4-controls-terminal-composite/legacy_four_physical_v2.py').read_text();changes=[("p.drive.casefold()==R.drive.casefold()and p.is_relative_to(R)","p.drive.casefold()in(R.drive.casefold(),'c:')"),(" folder=R/'reports/m4-138-preresource-controls/preparation-r3';"," pin(__file__);folder=R/'reports/m4-138-preresource-controls/preparation-r3';"),("controls=text(folder/'controls_main.cpp');start=","need(len(prep['legacy_controls_changes'])==12 and len(prep['parent_main_changes'])==5,'Exact retained twelve/five finite source inverse geometry');controls=text(folder/'controls_main.cpp');start="),("report=dict(passed=True,scope=","files[str(out/'whole-hook-bodies.json')]=sha(out/'whole-hook-bodies.json');report=dict(passed=True,scope=")];assert scope['inverse'](source2,changes)==source1;controls.append('Whole physical-prover4-hunk exact parent inverse')
 parent=(R/'tools/m4-controls-terminal-composite/finalize45_v2.py').read_text();child=(R/'tools/m4-controls-terminal-composite/finalize45_v3.py').read_text();a=" rows=read(M['proposal841']);mapping=read(M['mapping45']);";b=" assert M['proposal841']['sha256']=='c9051a3c047efe3e029fc30a1d3706746eb0d4c6065a360cf3fe867d07274fb4' and parent['files'][str(Path(M['proposal841']['path']).resolve())]==M['proposal841']['sha256'],'Exact parent841 physically declared row table';rows=read(M['proposal841']);mapping=read(M['mapping45']);";assert scope['inverse'](child,[(a,b)])==parent;controls.append('Whole finalizer1-hunk exact parent inverse')
 # Execute only new finite parent-table assert, with synthetic declared edges.
 tree=trees['finalize45_v3.py'];main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');guard=next(n for n in ast.walk(main)if isinstance(n,ast.Assert)and isinstance(n.msg,ast.Constant)and n.msg.value=='Exact parent841 physically declared row table');code=compile(ast.Module(body=[guard],type_ignores=[]),'<exact source extracted parent table assertion>','exec');h='c9051a3c047efe3e029fc30a1d3706746eb0d4c6065a360cf3fe867d07274fb4';p=str(R/'synthetic-proposal841.json')
 for label,declared,current,accepted in [('Correct exact parent table',h,h,True),('Wrong whole table bytes','0'*64,'0'*64,False),('Valid declared path wrong parent SHA','0'*64,h,False)]:
  env=dict(M={'proposal841':dict(path=p,sha256=current)},parent={'files':{p:declared}},Path=Path)
  try:exec(code,env);result=True
  except AssertionError:result=False
  assert result is accepted;controls.append(label+(' accepted'if result else' rejected'))
 out=R/'reports/m4-controls-terminal-composite'/name;assert not out.exists();out.mkdir();report=dict(pure_finite_controls_completed=True,controls=controls,control_count=len(controls),four_source_prover_unexecuted=True,composer_unexecuted=True,whole_physical_hook_proof_not_claimed=True,canonical_reader_opened=False,accepted_function_credit=0,files=files);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':run(sys.argv[1])
