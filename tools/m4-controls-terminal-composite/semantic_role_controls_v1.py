"""UNEXECUTED source-extracted finite-policy controls; no main/import/I/O."""
from pathlib import Path
import ast,collections,copy,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def need(v,s):
 if not v:raise ValueError(s)
def run(name):
 p=R/'tools/m4-controls-terminal-composite/current16_semantic_v2.py';raw=p.read_bytes();tree=ast.parse(raw);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');keyed=next(n for n in main.body if isinstance(n,ast.FunctionDef)and n.name=='keyed');loop=next(n for n in main.body if isinstance(n,ast.For)and isinstance(n.target,ast.Tuple)and[n.id for n in n.target.elts]==['key','case']);keycode=compile(ast.Module(body=[keyed],type_ignores=[]),'<exact16-mode source guard>','exec');loopcode=compile(ast.Module(body=[loop],type_ignores=[]),'<exact current16 finite manual/owner source block>','exec');expected={(level,mode)for level in('O0','O2')for mode in range(1,9)};scope={'need':need,'expected':expected};exec(keycode,scope);rows=[dict(level=level,mode=mode)for level,mode in sorted(expected)];assert set(scope['keyed'](rows))==expected;checks=['All16 mode source guard positive']
 for label,bad in(('Missing mode',rows[:-1]),('Duplicate replacing mode',rows[:-1]+[rows[0]]),('Additional mode',rows+[dict(level='O0',mode=9)])):
  try:scope['keyed'](bad)
  except ValueError:checks.append(label+' rejected')
  else:raise AssertionError(label)
 C={};W={};G={}
 for level,mode in sorted(expected):
  proof=dict(passed=True,actual_source_calls=149,actual_manual_calls=15,whole_identity_sides=328,whole_named_entry64_sides=328,calls=[dict(serial=i,call_words=[1,i,0,int(i>=149)])for i in range(164)],source_output_equivalence_claimed=False,font_lifetime_closure_claimed=False,origin_forwarder_chain_verified=False);source_rows={3:461,5:16,7:6}.get(mode,0);C[level,mode]=dict(actual_GDI_identity=proof,actual_fault_context_words=[1,1,1,135,0,0,0,135,0,0,0,0,1],actual_cause_words=[1,mode,135,0x5a3ff0],actual_suffix_operands=[[]for i in range(source_rows)]);W[level,mode]=dict(source_rows=source_rows,resource_rows=15,full_current_Context_direct_retry=True);G[level,mode]=dict(proof=copy.deepcopy(proof))
 def accepted(c,w,g):
  env=dict(C=c,W=w,G=g,sums=collections.Counter(),need=need)
  try:exec(loopcode,env);return env['sums']
  except ValueError:return None
 sums=accepted(C,W,G);assert sums==dict(cases=16,source_operand_rows=966,source_GDI_calls=2384,manual_owned_cleanup_calls=240,whole_identity_sides=5248,whole_entry64_sides=5248);checks.append('Reproduce all scoped16/966/2384/240/5248 counters from every source-extracted case')
 for label,mutate in(('Changed whole owner proof',lambda c,w,g:g['O0',1]['proof'].update(actual_manual_calls=14)),('Success-only manual count',lambda c,w,g:(c['O0',1]['actual_GDI_identity'].update(actual_manual_calls=14),g['O0',1]['proof'].update(actual_manual_calls=14))),('Source/manual chronological swap',lambda c,w,g:(c['O0',1]['actual_GDI_identity']['calls'][149]['call_words'].__setitem__(3,0),g['O0',1]['proof']['calls'][149]['call_words'].__setitem__(3,0))),('Invented owner source equivalence',lambda c,w,g:(c['O0',1]['actual_GDI_identity'].update(source_output_equivalence_claimed=True),g['O0',1]['proof'].update(source_output_equivalence_claimed=True))),('Partial font lifetime witness',lambda c,w,g:w['O0',1].update(resource_rows=14)),('Missing causal write-prefix rows',lambda c,w,g:w['O0',3].update(source_rows=460)),('Wrong firstfault phase',lambda c,w,g:c['O0',1]['actual_fault_context_words'].__setitem__(7,134))):
  c,w,g=copy.deepcopy(C),copy.deepcopy(W),copy.deepcopy(G);mutate(c,w,g);assert accepted(c,w,g)is None;checks.append(label+' rejected')
 # These limits are SOURCE POLICY output claims, not evidence of literal full
 # source write evaluation. Assert exact literal values in output construction.
 outputs=[node for node in ast.walk(main)if isinstance(node,ast.Call)and isinstance(node.func,ast.Name)and node.func.id=='dict'];fields={k.arg:k.value for node in outputs for k in node.keywords if k.arg};required={'committed_source_write_values_independently_instruction_evaluated':False,'committed_write_values_from_actual_source_witness':True,'whole_fault_memory_fully_source_predicted':False,'source_callbacks_executed':False};assert all(isinstance(fields[k],ast.Constant)and fields[k].value is v for k,v in required.items());checks.append('Exact finite observed-write/manual scope output values preserved')
 out=R/'reports/m4-controls-terminal-composite'/name;assert not out.exists();out.mkdir();(out/'report.json').write_text(json.dumps(dict(pure_production_controls_completed=True,controls=checks,control_count=len(checks),actual_metadata_case_proof_claimed=False,semantic_adapter_main_executed=False,canonical_reader_opened=False,raw_or_SQLite_opened=False,accepted_function_credit=0,files={str(p):hashlib.sha256(raw).hexdigest()}),indent=2)+'\n')
if __name__=='__main__':run(sys.argv[1])
