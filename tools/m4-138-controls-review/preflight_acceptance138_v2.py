"""Synthetic scoped lineage/parent expansion and complete retained semantics test."""
from pathlib import Path
import copy,json,re,sqlite3,sys
sys.dont_write_bytecode=True
import acceptance138_v2 as A
import expand_accepted138_union as E
R=A.ROOT
def main():
 out=R/'reports/m4-138-controls-review/acceptance138-machinery-preflight-r2';assert not out.exists();out.mkdir();controls=[];pins={}
 def pin(p):p=Path(p).resolve();pins[str(p)]=A.sha(p)
 def okay(label,fn):fn();controls.append(dict(name=label,passed=True))
 def refused(label,fn):
  try:fn()
  except (ValueError,AssertionError,KeyError):controls.append(dict(name=label,refused=True));return
  raise AssertionError(label+' unexpectedly allowed')
 payload=out/'synthetic.bin';payload.write_bytes(b'physical exact scoped dependency');h=A.sha(payload)
 scope=A.storage.ScopeIndex(out/'scopes.sqlite');a=out/'a.json';b=out/'b.json';a.write_text(json.dumps(dict(files={str(payload):h},passed=True)));b.write_text(json.dumps(dict(files={},passed=True)))
 union=A.storage.Union(out/'union.sqlite');A.PINS=union;A.SCOPES=scope
 ra=A.read(a,stream=True);rb=A.read(b,stream=True)
 okay('scope-positive-exact-own-edge',lambda:A.need(A.has(ra,payload,h),'Exact owner receipt edge'))
 refused('global-union-is-not-another-receipt-edge',lambda:A.need(A.has(rb,payload,h),'Must not infer scoped owner'))
 refused('wrong-scoped-content-identity',lambda:A.need(A.has(ra,payload,'0'*64),'Exact scoped hash'))
 scope.close();union.close()
 # Actual retained semantic function executes on synthetic lineage rows plus
 # ordinary current source/preparation metadata. No worker/archive execution.
 parent=json.loads((R/'reports/m4-joint-startup131-root/acceptance-r1/report.json').read_bytes());prep=json.loads((R/'reports/m4-joint-startup138/preparation-r4/report.json').read_bytes());source=json.loads((R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json').read_bytes())
 gates={k:dict(path='synthetic/'+k+'.json',sha256='1'*64)for k in A.REQUIRED}
 gates['parent']['sha256']=A.PARENT_SHA;gates['native_preparation']['path']='reports/m4-joint-startup138/preparation-r4/report.json';gates['native_preparation']['sha256']=source['executed_lineage']['joint_preparation_sha256'];gates['native_build']['sha256']=source['executed_lineage']['build_sha256'];gates['native_execution']['sha256']=source['executed_lineage']['execution_sha256'];gates['source_provider']['path']='reports/m4-joint-startup138-source/combined-source-provider-r6/report.json';gates['source_provider']['sha256']='40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052'
 rows={k:{}for k in A.REQUIRED};rows.update(parent=parent,native_preparation=prep,original_preparation=dict(selected_order=prep['selected_order']),source_provider=source)
 rows['native_build']=dict(preparation_sha256=gates['native_preparation']['sha256']);rows['native_execution']=dict(build_sha256=gates['native_build']['sha256'],admission_review_sha256=gates['native_prelaunch']['sha256'],all_bounded_readers_closed=True,all_workers_terminal=True,levels=[dict(level='O0'),dict(level='O2')]);rows['native_prelaunch']=dict(build_sha256=gates['native_build']['sha256'])
 rows['original_build']=dict(preparation_sha256=gates['original_preparation']['sha256']);rows['original_execution']=dict(build_sha256=gates['original_build']['sha256']);rows['original_validation']=dict(build_sha256=gates['original_build']['sha256'],counts=dict(phases=828,MFC_original_phases=6,MFC_full_normal_boundaries=42,MFC_full_named_API_pairs=24,MFC_true_root_TIB8192_endpoints=12,MFC_whole_borrowed_backing_endpoints=60,MFC_codepage_CS24_endpoints=12));rows['original_source']=dict(original_validation_sha256=gates['original_validation']['sha256']);rows['original_source_review']=dict(current_source_sha256=gates['original_source']['sha256'])
 rows['source_legacy_flags']=dict(conditional_PCs=2,source_consumers_per_sequence=171,capture_reader_opened=False,worker_executed=False,initializer_credit=0);rows['paired']=dict(reader_closed=True,paired_initialization_data_contract=True,blanket_page_mask=False,original_and_native_bytes_modified=False,whole_game_liveness_proven=False,loaded_input_native_DllMain_credit=False)
 for label,target in [('source_provider_review','source_provider'),('source_new_mfc_review','source_provider'),('source_closure','source_provider'),('original_old_source_review','original_old_source'),('paired_review','paired'),('controls_review','controls')]:rows[label]['files']={str((R/gates[target]['path']).resolve()):gates[target]['sha256']}
 rows['controls_execution']=dict(build_sha256=gates['controls_build']['sha256']);rows['controls_build']=dict(preparation_sha256=gates['controls_preparation']['sha256']);rows['controls_prelaunch']=dict(build_sha256=gates['controls_build']['sha256'])
 u=A.storage.Union(out/'semantic-parent-union.sqlite');A.PINS=u
 for p,h0 in parent['files'].items():A.register(p,h0)
 module=A.storage.load('synthetic_retained138_semantics',R/'tools/m4-138-controls-review/acceptance138_semantics_v3.py')
 # Extract the exact injection tuple from current checker AST/source. A missing
 # required global such as normalized therefore fails this whole function test.
 import ast
 tree=ast.parse(Path(A.__file__).read_text());tuples=[n.iter for n in ast.walk(tree)if isinstance(n,ast.For)and isinstance(n.target,ast.Name)and n.target.id=='key'and isinstance(n.iter,ast.Tuple)];assert len(tuples)==1;keys=ast.literal_eval(tuples[0]);assert 'normalized'in keys
 for key in keys:setattr(module,key,getattr(A,key))
 okay('complete-retained-semantic-function-including-21083-parent-pins',lambda:module.semantic_checks(rows,gates))
 wrong=copy.deepcopy(rows);wrong['parent']['files'][next(iter(parent['files']))]='0'*64;refused('physical-parent-union-end-predicate-refuses-mutation',lambda:module.semantic_checks(wrong,gates));u.close()
 p=out/'parent-payload.bin';p.write_bytes(b'whole accepted union fixture');u=A.storage.Union(out/'parent-proof.sqlite');u[str(p)]=A.sha(p);closure=u.verify();proof=u.seal()
 parent_fixture=dict(passed=True,scope='SYNTHETIC accepted138-shaped integrity fixture, zero acceptance credit',connected_roots=138,acceptance_requires_inventory_expansion=True,physical_closure=closure,proof_inventory=proof,files={proof['path']:proof['sha256']})
 def expand(label,d,fail=False):
  q=out/(label+'.json');q.write_text(json.dumps(d)+'\n');captured={}
  def run():
   result=E.expand(q,A.sha(q),lambda p,h:captured.__setitem__(p,h));A.need(result['whole_dependency_rows_measured']==1 and result['database_reader_closed']and captured[A.normalized(str(p))]==A.sha(p),'Complete synthetic expansion')
  (refused if fail else okay)(label,run)
 expand('accepted-parent-entire-closed-union-expansion',parent_fixture)
 d=copy.deepcopy(parent_fixture);d['proof_inventory']['sqlite_closed_before_hash']=False;expand('unclosed-parent-union-refused',d,True)
 d=copy.deepcopy(parent_fixture);d['files']={};expand('missing-parent-db-pin-refused',d,True)
 d=copy.deepcopy(parent_fixture);d['proof_inventory']['physical_rows']=2;d['physical_closure']['whole_dependency_rows_measured']=2;d['physical_closure']['unique_physical_dependencies']=2;expand('wrong-parent-entire-count-refused',d,True)
 old=p.read_bytes();p.write_bytes(b'x'*len(old));expand('same-size-parent-row-mutation-refused',parent_fixture,True);p.write_bytes(old)
 db=sqlite3.connect(proof['path']);db.execute('UPDATE dependencies SET measured=0');db.commit();db.close();d=copy.deepcopy(parent_fixture);d['proof_inventory']['sha256']=A.sha(proof['path']);d['files'][proof['path']]=d['proof_inventory']['sha256'];expand('unmeasured-parent-row-refused',d,True)
 for path in [Path(__file__),Path(A.__file__),Path(A.storage.__file__),Path(A.storage.base.__file__),Path(E.__file__),R/'tools/m4-138-controls-review/acceptance138_semantics_v3.py',R/'tools/m4-138-controls-review/configure_acceptance138_v2.py',R/'tools/m4-138-controls-review/prepare_acceptance138_checker_v2.py',Path(sys.executable),R/'reports/m4-joint-startup131-root/acceptance-r1/report.json',R/'reports/m4-joint-startup138/preparation-r4/report.json',R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json']:pin(path)
 for path in out.iterdir():
  if path.is_file():pin(path)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Bounded synthetic scoped proof/parent expansion and full retained semantic-function execution with actual parent21083 declarations/current ordinary metadata; no native/source machine or real union bytehash',controls=controls,actual_parent_declarations=len(parent['files']),complete_semantic_function_executed_on_synthetic_lineage=True,real_acceptance_executed=False,real_inventory_expanded=False,capture_reader_opened=False,worker_executed=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=A.sha(q),controls=len(controls))))
if __name__=='__main__':main()
