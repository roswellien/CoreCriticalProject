"""UNEXECUTED ROOT-pre-admitted whole composite and typed45 source review."""
from pathlib import Path
import hashlib,importlib.util,json,re,sqlite3,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
HELPER_SHA='e73f992e185bd3f24a5a3d5fa1afb536f0250816e5a54130ca6e37bfc90de26a'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(admission,admission_sha,manifest,manifest_sha,controls_path,controls_sha,name):
 ap=Path(admission).resolve();assert sha(ap)==admission_sha;A=json.loads(ap.read_text());assert A['passed']is True and A['independent_review']is True and A['scope_identity']=='completed_controls_composite_independent_review'and A['controls_sha256']==controls_sha
 admitted={str(Path(p).resolve()):h for p,h in A['files'].items()};assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-controls-terminal-composite'/name;assert not out.exists();out.mkdir();db=sqlite3.connect(out/'reviewed-whole-scoped-union.sqlite');db.execute('PRAGMA cache_size=-4096');db.execute('PRAGMA temp_store=FILE')
 def source_only(event,args):
  if event=='open'and args and isinstance(args[0],(str,bytes))and Path(args[0]).suffix.lower()=='.pyc':raise FileNotFoundError('ROOT-sealed source imports; no cached bytecode')
 sys.addaudithook(source_only)
 db.execute('CREATE TABLE physical(path TEXT PRIMARY KEY,sha TEXT NOT NULL) WITHOUT ROWID');db.execute('CREATE TABLE edges(scope TEXT,path TEXT,sha TEXT,PRIMARY KEY(scope,path)) WITHOUT ROWID');db.execute('CREATE TABLE expected(scope TEXT,path TEXT,sha TEXT,PRIMARY KEY(scope,path)) WITHOUT ROWID');pins={str(ap):admission_sha};passed=False;closed=False;blocked=[];evidence=[];expanded=None;facets=None
 def direct(p,h=None):
  p=Path(p).resolve();v=sha(p);assert admitted.get(str(p))==v and(h is None or h==v);pins[str(p)]=v;return p
 def register(path,h):
  path=str(Path(path).resolve());old=db.execute('SELECT sha FROM physical WHERE path=?',(path,)).fetchone();assert old is None or old==(h,);db.execute('INSERT OR IGNORE INTO physical VALUES(?,?)',(path,h))
 def edge(scope,path,h):
  old=db.execute('SELECT sha FROM edges WHERE scope=?AND path=?',(scope,path)).fetchone();assert old is None or old==(h,);db.execute('INSERT OR IGNORE INTO edges VALUES(?,?,?)',(scope,path,h))
 def load(p,n,h=None):
  p=direct(p,h);s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  direct(__file__);E=load(R/'tools/m4-controls-terminal-composite/expand_composite_inventory_v3.py','sealed_composite_expander',HELPER_SHA);F=load(R/'tools/m4-controls-terminal-composite/review_composite_facets_v1.py','distinct_named_source_facets');J=load(R/'tools/m4-138-controls-review/full_raw_review_v2.py','streamed_report_metadata')
  def metadata(row,scope=None):
   p=Path(row['path']).resolve();h=row['sha256']
   if scope is None:p=direct(p,h)
   else:assert db.execute('SELECT sha FROM edges WHERE scope=?AND path=?',(scope,str(p))).fetchone()==(h,);E.measured(p,h)
   value={};keys=set()
   with p.open(encoding='utf-8')as stream:
    s=J.StreamJSON(stream);s.expect('{');first=True
    while True:
     s.trim()
     if s.buf.startswith('}'):s.buf=s.buf[1:];break
     if not first:s.expect(',')
     k=s.value();assert type(k)is str and k not in keys;keys.add(k);s.expect(':');first=False
     if k=='files':
      for q,v in s.pairs():
       q=str(Path(q).resolve())
       if scope is not None:db.execute('INSERT INTO expected VALUES(?,?,?)',(scope+'-declared',q,v))
      value[k]={}
     else:value[k]=s.value()
    s.finish()
   return value
  M=metadata(dict(path=manifest,sha256=manifest_sha));assert M['schema']=='mw34-terminal-controls-composite-input-v1'and M['actual_terminals_complete']is True
  for key,row in M['roles'].items():assert A['reviewed_role_bindings'][key]==row,'Exact ROOT pre-reviewed semantic/source-role identities, no guessed passed roles'
  controls_path=direct(controls_path,controls_sha);expanded=E.expand(controls_path,controls_sha,register,register_edge=edge);db.commit()
  gates={k:metadata(dict(path=str(controls_path.parent/leaf),sha256=A['composite_gate_hashes'][k]))for k,leaf in [('controls_preparation','controls-preparation.json'),('controls_prelaunch','controls-prelaunch.json'),('controls','controls.json')]}
  assert A['composite_gate_hashes']['controls']==controls_sha
  roles={k:metadata(v,k)for k,v in M['roles'].items()if k!='legacy24_union'}
  cases=[metadata(row,'legacy-'+row['level']+'-'+str(row['mode']))for row in M['legacy24_cases']]
  assert db.execute('SELECT COUNT(*)FROM expected e WHERE NOT EXISTS(SELECT 1 FROM edges a WHERE a.scope=e.scope AND a.path=e.path AND a.sha=e.sha)').fetchone()[0]==0,'Every consumed receipt declaration is its own physically measured scoped edge'
  assert roles['current16_semantic_review']['current16_fullraw_sha256']==M['roles']['current16_fullraw']['sha256']and roles['current16_semantic_review']['execution_sha256']==roles['current8_scope_review']['execution_sha256']==M['roles']['current8_execution']['sha256']
  assert roles['legacy_prelaunch_complete_review']['legacy24_terminal_sha256']==M['roles']['legacy24_aggregate']['sha256']
  assert gates['controls_preparation']['underlying_current8_preparation']==M['roles']['current8_preparation']and gates['controls_preparation']['underlying_legacy12_preparation']==M['roles']['legacy12_preparation']and gates['controls_prelaunch']['scoped_legacy_build']==M['roles']['legacy12_build']and gates['controls']['execution_sha256']==M['roles']['current8_execution']['sha256']
  facets=F.derive(gates,roles,cases,expanded,controls_sha)
  mapping=direct(A['mapping45']['path'],'79d6141deea3f2a7cc7faa58d2a1ada78a3122f3147d5fa90dbddb8b5ddce756');disposition=direct(A['field_disposition']['path'],'fbc42704a584377455d0d85593127c547ccfaf47e04f73c4714cbf1b972137c7');proposal=direct(A['proposal6']['path'],'626c590fdde8e2077b4fa1fa2decdd76ef07f762466c0aad92a8fd81fe447505')
  P=json.loads(proposal.read_text());assert P['criteria']==841 and P['status_counts']==dict(identity_candidate=613,finite_delta_candidate=183,unresolved=45)
  mapping=json.loads(mapping.read_text());disp=json.loads(disposition.read_text());assert len(mapping)==len(disp)==45
  reviews={('controls_review'):facets['review_fields'],**gates};targets=set()
  for m,d in zip(mapping,disp):
   assert(m['gate'],m['baseline_field'])==(d['gate'],d['field'])and F.typed(m['baseline_expected'],d['baseline_expected']);value=F.at(reviews[m['gate']],m['composite_field']);assert type(value).__name__==m['baseline_type']
   if type(value)is bool:assert value is m['baseline_expected'],'No Boolean scope flip'
   target=m['gate'],m['composite_field'];assert target not in targets;targets.add(target)
   leaf=m['baseline_field'].split('.')[-1]
   if m['gate']=='controls_prelaunch':origins=['legacy_prelaunch_complete_review'];derivation='Exact seven named physical counters from independently executed legacy complete7 source/compiled body review, compared each field'
   elif leaf in('whole_borrowed_guestCS24_prefixes','source_TLS_refusal_frame64'):origins=['named_CS24_TLS64_supplement'];derivation='Exact separately proved legacy guestCS24/zero-index sourceTLS64; no native CS40 substitution'
   elif leaf=='whole_export_targets_authenticated':origins=['current16_fullraw','legacy24_aggregate'];derivation='Actual distinct scoped raw membership count after full eachbyte composite DB expansion, not legacy semantic counter'
   elif m['gate']=='controls_preparation':origins=['current8_scope_review','current8_preparation','legacy12_preparation','legacy24_aggregate'];derivation='Distinct actual24 levels/modes derive legacy12; every case and actual current8 explicit private/permission limits remain false'
   elif leaf in('passed','all_bounded_readers_closed','raw_export_readers_closed','raw_exports_all_logical_entries','controls_verification_sha256','initializer_credit','capture_archives_opened'):origins=['current16_fullraw','legacy24_aggregate','current16_semantic_review','current8_scope_review'];derivation='Actual closed successful reviewer/fullphysical/scoped expansion; new controls hash binds exact composite, integrity does not replace source semantics'
   elif leaf=='execution_sha256':origins=['current8_execution'];derivation='Exact independently admitted current8 execution/build lineage'
   else:origins=['legacy24_aggregate'];derivation='Every exact actual24 case count summed and entire aggregate reproduced; finite legacy source counts retained separately from current16 observations'
   evidence.append(dict(gate=m['gate'],baseline_field=m['baseline_field'],baseline_expected=m['baseline_expected'],composite_field=m['composite_field'],actual_value=value,source_evidence_roles=origins,source_evidence_receipts=[M['roles'][k]for k in origins],derivation=derivation,legacy_semantic_counts_not_current16_observations=m['baseline_field'].startswith('counts.')and leaf!='whole_export_targets_authenticated',scope_exclusion=d['scope_exclusion'],physical_domain=m['physical_domain'],allowance=False))
  db.commit();passed=True
 except BaseException:blocked.append(traceback.format_exc());(out/'failure.txt').write_text(blocked[-1]);raise
 finally:
  db.commit();db.close();closed=True;proof=out/'reviewed-whole-scoped-union.sqlite';pins[str(proof)]=sha(proof)
  q=out/'report.json';result=dict(passed=passed,controls_sha256=controls_sha,controls_verification_sha256=controls_sha,all_named_composite_domains_independently_reviewed=passed,all_scoped_physical_edges_verified=passed,whole_composite_union_expanded=passed and expanded is not None,all_bounded_readers_closed=closed and(expanded is None or expanded['database_reader_closed']),capture_archives_opened=0,initializer_credit=0,accepted_function_credit=0,whole_registry_private_retry_claim=False,whole_permissions_retry_claim=False,source_counter_values_from_legacy24_only=True,expansion=expanded,counts={}if facets is None else facets['legacy_source_counts'],per_field_evidence=evidence,blockers=blocked,baseline_841_and_existing_39_gates_not_modified=True,proof_inventory=dict(path=str(proof),sha256=pins[str(proof)],sqlite_closed_before_hash=True,scope_edges_retained=True),ROOT_admission_path=str(ap),ROOT_admission_sha256=admission_sha,files=pins);q.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=passed)))
if __name__=='__main__':main(*sys.argv[1:])
