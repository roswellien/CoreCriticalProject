"""UNEXECUTED pure inverse/binding controls; no composer/adapter main/import."""
from pathlib import Path
import ast,copy,hashlib,json,sqlite3,sys
R=Path(__file__).resolve().parents[2]
def need(v,s):
 if not v:raise ValueError(s)
def run(name):
 folder=R/'tools/m4-controls-terminal-composite';receipt=R/'reports/m4-controls-terminal-composite/complete7-preparation-r1';checks=[];files={}
 for leaf in('build_v3.py','build_v4.py','build_v5.py','legacy_complete7_v1.py'):
  path=folder/leaf;raw=path.read_bytes();files[str(path)]=hashlib.sha256(raw).hexdigest();ast.parse(raw)
 for delta,parent,child in(('builder-exact-delta.json','build_v3.py','build_v4.py'),('builder-case-membership-delta.json','build_v4.py','build_v5.py')):
  change=json.loads((receipt/delta).read_text(encoding='utf-8-sig'));before=(folder/parent).read_bytes().decode();after=(folder/child).read_bytes().decode();assert after.count(change['new'])==1;assert after.replace(change['new'],change['old'])==before;checks.append(child+' whole exact one-hunk parent inverse')
 text=(folder/'build_v5.py').read_text();start=text.index("  need(roles['legacy_prelaunch_complete_review']['sha256']==A['legacy_complete7_sha256']");end=text.index("  limits=reports['current8_scope_review']",start);code='\n'.join(line[2:]for line in text[start:end].splitlines());compiled=compile(ast.parse(code),'<exact complete7 production source binding>','exec');path=str(R/'synthetic-ROOT-complete7.json');h='1'*64;counts=dict(whole_intended_protected_IAT_mutation_repairs=2,whole_diagnostic_only_delta=1,whole_authored_public_faults=12,whole_true_source_entry_observer=1,actual_compiler_TLS_cells=56,whole_linked_control_functions=7,entry_observer_inlined_in_whole_MFC_entry=1);base=dict(physical_domain_derivation_schema='legacy12-complete7-source-derived-v1',legacy_four_source_sha256='7979b6e0423debf0cb7972cf28f315207dcb56f54e7e0fb09b4e12dad382d73c',legacy_prefix_ROOT_review_sha256='c86c8082f396b517b805e182c4ea4a9b4396a9e19b290bf8fc098d172e9478bb',legacy_whole7_ledger_sha256='8d94a0409f3ee13480fc5cf1f28b11b11ce2b471ac94da3d845fd6c996c4095d',legacy24_terminal_sha256='2'*64,current8_used_as_legacy_proof=False,terminal_content_revalidation_by_composer_still_required=True,counts=counts)
 def accepted(pre,gate=None):
  scope=dict(roles={'legacy_prelaunch_complete_review':dict(path=path,sha256=h),'legacy24_aggregate':dict(sha256='2'*64)},A=gate or dict(legacy_complete7_sha256=h,legacy_complete7_report=path),pre=pre,Path=Path,need=need,typed=lambda a,b:type(a)is type(b)and a==b,cases=[dict(mode=i)for i in range(1,13)])
  try:exec(compiled,scope);return True
  except (ValueError,KeyError):return False
 assert accepted(base);checks.append('Exact complete7 ROOT-bound schema positive')
 for field,value in(('physical_domain_derivation_schema','arbitrary occurrence strings'),('legacy_four_source_sha256','0'*64),('legacy_prefix_ROOT_review_sha256','0'*64),('legacy_whole7_ledger_sha256','0'*64),('legacy24_terminal_sha256','0'*64),('current8_used_as_legacy_proof',True),('terminal_content_revalidation_by_composer_still_required',False)):
  bad=copy.deepcopy(base);bad[field]=value;assert not accepted(bad);checks.append('Reject altered '+field)
 bad=copy.deepcopy(base);bad['counts']['whole_true_source_entry_observer']=True;assert not accepted(bad);checks.append('Reject Boolean integer physical facet')
 bad=copy.deepcopy(base);bad['counts']['actual_compiler_TLS_cells']=64;assert not accepted(bad);checks.append('Reject current8 TLS64 replacing legacy56')
 bad=copy.deepcopy(base);bad['counts']['whole_linked_control_functions']=15;assert not accepted(bad);checks.append('Reject typed CALL15 replacing whole7')
 assert not accepted(base,dict(legacy_complete7_sha256='0'*64,legacy_complete7_report=path));checks.append('Reject unadmitted complete7 SHA')
 assert not accepted(base,dict(legacy_complete7_sha256=h,legacy_complete7_report=str(R/'other.json')));checks.append('Reject alternate complete7 path')
 # Run only the literal production membership statement over in-memory SQLite.
 tree=ast.parse(text);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');member=next(n for n in ast.walk(main)if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and any(isinstance(a,ast.Constant)and a.value=='Every strict case is physically declared by exact actual terminal aggregate, not an alternate same-count receipt'for a in n.value.args));membercode=compile(ast.Module(body=[member],type_ignores=[]),'<exact source case membership>','exec');db=sqlite3.connect(':memory:');db.execute('CREATE TABLE edges(scope,path,sha)');casepath=str(R/'synthetic-case.json');db.execute('INSERT INTO edges VALUES(?,?,?)',('legacy24_aggregate-declared',casepath,h))
 for label,row,expected in(('Exact actual case',dict(path=casepath,sha256=h),True),('Same-count alternate case',dict(path=str(R/'alternate-case.json'),sha256=h),False),('Changed case SHA',dict(path=casepath,sha256='0'*64),False)):
  try:exec(membercode,dict(db=db,Path=Path,row=row,need=need));actual=True
  except ValueError:actual=False
  assert actual is expected;checks.append(label+(' accepted'if actual else' rejected'))
 db.close();out=R/'reports/m4-controls-terminal-composite'/name;assert not out.exists();out.mkdir();(out/'report.json').write_text(json.dumps(dict(pure_controls_completed=True,control_count=len(checks),controls=checks,adapter_main_executed=False,composer_main_executed=False,ROOT_admission_created=False,canonical_reader_opened=False,accepted_function_credit=0,files=files),indent=2)+'\n')
if __name__=='__main__':run(sys.argv[1])
