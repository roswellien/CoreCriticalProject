"""UNEXECUTED terminal controls composer. Requires future ROOT admission.

Build three producer gates, then ROOT independently reviews their exact bytes.
No allowance/configuration/acceptance is produced by this tool.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,sqlite3,sys
R=Path(__file__).resolve().parents[2]
CURRENT_PREP='f413ea66cb259ecebf8bf76024113a0410fe5883304fa10af9a442b291c1b07e'
CURRENT_BUILD='e064098f58982c7c6115e43f0ebf14a39eb1ae68f4162225c48c10c70b2f1bf6'
LEGACY_PREP='8a322602c066931f5dd3ced2b9319f6907b0b01413828e2d72dd482c5ce09b2c'
LEGACY_BUILD='9a65633f858e7c06c5ca09a8191a41051321cf2848c1a25b4318bd4c61c08a9f'
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def at(obj,key):
 for part in key.split('.'):obj=obj[part]
 return obj
def typed(a,b):return type(a)is type(b)and a==b
def main(admission_path,admission_sha,manifest_path,manifest_sha,name):
 admission_path=Path(admission_path).resolve();need(sha(admission_path)==admission_sha,'Exact future ROOT composer admission');A=json.loads(admission_path.read_bytes());need(A['passed']is True and A['terminal_controls_composer_admitted']is True,'Independent ROOT code/physical/domain review required')
 need(A['files'][str(Path(__file__).resolve())]==sha(__file__),'Actual composer code admitted');need(A['files'][str(Path(manifest_path).resolve())]==manifest_sha,'Exact future completed input manifest admitted')
 need(re.fullmatch('[A-Za-z0-9_-]{1,90}',name),'Simple fresh namespace');out=R/'reports/m4-controls-terminal-composite'/name;need(not out.exists(),'Fresh output');out.mkdir(parents=True)
 db=sqlite3.connect(out/'whole-ordinary-union.sqlite');db.execute('PRAGMA cache_size=-4096');db.execute('PRAGMA temp_store=FILE');db.execute('CREATE TABLE physical(path TEXT PRIMARY KEY,folded TEXT UNIQUE,sha TEXT NOT NULL,size INTEGER NOT NULL,seen INTEGER NOT NULL) WITHOUT ROWID');db.execute('CREATE TABLE edges(scope TEXT NOT NULL,path TEXT NOT NULL,sha TEXT NOT NULL,PRIMARY KEY(scope,path)) WITHOUT ROWID');db.execute('CREATE TABLE raw(scope TEXT NOT NULL,caseid TEXT NOT NULL,path TEXT UNIQUE NOT NULL,PRIMARY KEY(scope,caseid,path)) WITHOUT ROWID');parser=None;closed=False
 def measure(p,h,n=None,scope='metadata'):
  p=Path(p).resolve();need(p.is_absolute()and p.is_file()and p.name!='transport.json'and p.suffix.lower()not in('.mwb','.mwi','.mwc','.zip','.7z'),'Only ordinary source/raw input');need(type(h)is str and re.fullmatch('[0-9a-f]{64}',h),'Exact whole SHA');s=p.stat();need(sha(p)==h and (n is None or s.st_size==n),'Every physical row whole bytes/length');t=p.stat();need((s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_size,t.st_mtime_ns,t.st_ctime_ns),'Stable physical input');old=db.execute('SELECT path,sha,size FROM physical WHERE folded=?',(str(p).casefold(),)).fetchone();need(old is None or old==(str(p),h,s.st_size),'No path spelling/hash/size collision');db.execute('INSERT OR IGNORE INTO physical VALUES(?,?,?,?,1)',(str(p),str(p).casefold(),h,s.st_size));db.execute('INSERT OR IGNORE INTO edges VALUES(?,?,?)',(scope,str(p),h));return p
 def read(row,scope):
  p=measure(row['path'],row['sha256'],scope=scope);metadata={};keys=set()
  with p.open(encoding='utf-8')as f:
   s=parser.StreamJSON(f);s.expect('{');first=True
   while True:
    s.trim()
    if s.buf.startswith('}'):s.buf=s.buf[1:];break
    if not first:s.expect(',')
    key=s.value();need(type(key)is str and key not in keys,'Unique report top-level keys');keys.add(key);s.expect(':');first=False
    if key=='files':
     for path,h in s.pairs():
      need(db.execute('SELECT 1 FROM edges WHERE scope=?AND path=?',(scope+'-declared',str(Path(path).resolve()))).fetchone()is None,'No duplicate declared map key');measure(path,h,scope=scope+'-declared')
     metadata[key]={}
    else:metadata[key]=s.value()
   s.finish()
  measure(p,row['sha256'],scope=scope);return metadata
 try:
  # Parser import happens only AFTER explicit ROOT code admission. Its ordinary
  # I/O/JSON primitives are reused, never its checker main or successful flag.
  helper=R/'tools/m4-138-controls-review/full_raw_review_v2.py';need(str(helper)in A['files'],'Exact parser code included');measure(helper,A['files'][str(helper)]);sp=importlib.util.spec_from_file_location('controls_composite_stream',helper);parser=importlib.util.module_from_spec(sp);sp.loader.exec_module(parser)
  # Bounded terminal frontier FIRST, before any large report/filemap/hash.
  mp=Path(manifest_path).resolve();need(mp.stat().st_size<2*1024*1024 and sha(mp)==manifest_sha,'Small independently ROOT-admitted future manifest');probe=json.loads(mp.read_bytes());need(probe['actual_terminals_complete']is True,'Actual terminals required');rawrow=probe['roles']['current16_fullraw'];rp=Path(rawrow['path']).resolve();need(rp.is_file()and rp.stat().st_size<32*1024*1024 and sha(rp)==rawrow['sha256'],'Actual bounded current16 terminal receipt');rv=json.loads(rp.read_bytes());need(rv['passed']is True and rv['raw_export_readers_closed']is True and rv['all_bounded_readers_closed']is True and rv['proof_inventory']['sqlite_closed_before_hash']is True and rv['counts']['whole_export_targets_authenticated']==10691866,'No partial current16 before large input I/O');need(probe['roles']['legacy24_aggregate']['sha256']=='d3f4c2352cbf957088d885f2a8f5d21268cf86efc002556994b6a71c4d42e8c9','Actual ROOT-confirmed terminal legacy24 aggregate, not union admission alone')
  M=read(dict(path=manifest_path,sha256=manifest_sha),'manifest');need(M['schema']=='mw34-terminal-controls-composite-input-v1','Exact future input schema');need(M['actual_terminals_complete']is True,'No running/partial receipt');roles=M['roles']
  required={'legacy24_aggregate','legacy24_admission','legacy24_union','current16_fullraw','current16_semantic_review','current8_preparation','current8_build','current8_execution','current8_scope_review','current8_physical_review','legacy12_preparation','legacy12_build','legacy_prelaunch_complete_review','named_CS24_TLS64_supplement'};need(set(roles)==required,'All-and-only named completed domains')
  # Future semantic/scope decisions must be exact independently ROOT-run
  # receipts. Manifest admission alone must not substitute free passed flags.
  for key in('current16_fullraw','current16_semantic_review','current8_scope_review'):
   binding=A['reviewed_role_bindings'][key];need(roles[key]['sha256']==binding['sha256']and str(Path(roles[key]['path']).resolve())==str(Path(binding['path']).resolve()),'Exact ROOT-reviewed completed role '+key)
  reports={}
  for role,row in roles.items():
   if role=='legacy24_union':continue
   reports[role]=read(row,role);need(reports[role]['passed']is True,'Actual terminal/independently reviewed role '+role)
  fixed_roles={'legacy24_admission':'4e1f23cf8be6ff2db1362a71f5141c51cf2bd51bf702fe8d911e61cc7f036f4c','current8_physical_review':'4c961184ef9442788eef3eba69bd37dc85427f123d4494ed30d6fa7e0123f83f','named_CS24_TLS64_supplement':'88bb674315463694c75fcd21c62a0f3bf5151a2ba5a55149994e1489074f5265'};need(all(roles[k]['sha256']==h for k,h in fixed_roles.items()),'Actual retained ROOT physical domains, not author substitutes')
  need(roles['current8_preparation']['sha256']==CURRENT_PREP and roles['current8_build']['sha256']==CURRENT_BUILD and roles['legacy12_preparation']['sha256']==LEGACY_PREP and roles['legacy12_build']['sha256']==LEGACY_BUILD,'Separate immutable two actual build/preparation domains')
  need(reports['current8_build']['preparation_sha256']==CURRENT_PREP and reports['current8_execution']['build_sha256']==CURRENT_BUILD,'Exact current16 physical lineage');need(reports['legacy12_build']['preparation_sha256']==LEGACY_PREP,'Exact legacy24 physical lineage')
  legacy=reports['legacy24_aggregate'];need(legacy['case_count']==24,'Actual terminal24 aggregation');need(reports['legacy24_admission']['case_count']==24 and reports['legacy24_admission']['whole_dependency_count']==1167180,'Actual closed legacy union domain')
  cases=M['legacy24_cases'];need(len(cases)==24 and {(r['level'],r['mode'])for r in cases}=={(l,m)for l in('O0','O2')for m in range(1,13)},'24 distinct actual legacy cases');sums=collections.Counter();rawroots=[]
  for row in cases:
   need(db.execute('SELECT 1 FROM edges WHERE scope=?AND path=?AND sha=?',('legacy24_aggregate-declared',str(Path(row['path']).resolve()),row['sha256'])).fetchone()is not None,'Every strict case is physically declared by exact actual terminal aggregate, not an alternate same-count receipt')
   case=read(row,'legacy-'+row['level']+'-'+str(row['mode']));need(case['passed']is True and case['all_bounded_readers_closed']is True and (case['level'],case['mode'])==(row['level'],row['mode']),'Closed same exact case');c=case['counts'];need(all(type(v)is int and v>=0 for v in c.values()),'Actual typed counters');need(c['actual_precise_denials']==c['actual_unchanged_poisoned_retries']==c['entryframe64_checked']==1 and c['whole_caller_FX512_ENV28']==2,'Each actual denial/retry/frame/caller semantic facet')
   for flag in('whole_Runtime_hidden_private_retry_claim','whole_old_registry_private_retry_claim','whole_permissions_retry_claim'):need(case[flag]is False,'Explicit observation limit')
   sums.update(c)
   execution_scope='legacy-execution-'+row['level']+'-'+str(row['mode']);ep=Path(case['execution']).resolve();eh=case['execution_sha256'];need(db.execute('SELECT 1 FROM edges WHERE scope=?AND path=?AND sha=?',('legacy24_aggregate-declared',str(ep),eh)).fetchone()is not None,'Exact sealed raw execution belongs to actual terminal aggregate')
   actual_execution=read(dict(path=str(ep),sha256=eh),execution_scope);need(actual_execution['passed']is True and actual_execution['worker_closed']is True and actual_execution['worker_executed']is True and(actual_execution['level'],actual_execution['mode'])==(row['level'],row['mode'])and actual_execution['facts']['exit_code']==0,'Actual closed same legacy12 raw case, not another namespace')
   args=actual_execution['facts']['arguments'];worker=reports['legacy12_build']['workers'][row['level']];need(len(args)==8 and str(Path(args[0]).resolve())==str(Path(worker['path']).resolve())and args[7]==str(row['mode']),'Actual legacy12 physical worker and authored mode')
   for role in('legacy12_build','legacy12_preparation'):
    declared=roles[role];need(db.execute('SELECT 1 FROM edges WHERE scope=?AND path=?AND sha=?',(execution_scope+'-declared',str(Path(declared['path']).resolve()),declared['sha256'])).fetchone()is not None,'Actual raw worker owns same legacy12 producing source/build')
   root=Path(args[5]).resolve();actual_raw_count=sum(Path(path).is_relative_to(root)for path, in db.execute('SELECT path FROM edges WHERE scope=?',(execution_scope+'-declared',)));need(type(actual_raw_count)is int and actual_raw_count>0,'Derive full payload count from exact producer-declared output inventory')
   if 'ordinary_raw_root'in row:need(Path(row['ordinary_raw_root']).resolve()==root,'Optional manifest root must equal actual producer argument')
   if 'actual_raw_files'in row:need(typed(row['actual_raw_files'],actual_raw_count),'Optional manifest count must equal actual producer full inventory')
   rawroots.append((root,row['level']+'-'+str(row['mode']),actual_raw_count))
  need(dict(sums)==legacy['counts'],'Reproduce all terminal legacy counters from all24 cases, not success-only copy')
  need(all(not a[0].is_relative_to(b[0])and not b[0].is_relative_to(a[0])for i,a in enumerate(rawroots)for b in rawroots[i+1:]),'Disjoint exact raw namespaces')
  union=read(roles['legacy24_union'],'legacy24-union');need(union['passed']is True,'Closed whole ordinary legacy union');legacy_raw=collections.Counter()
  for path, in db.execute("SELECT path FROM edges WHERE scope='legacy24-union-declared'"):
   owners=[r for r in rawroots if Path(path).is_relative_to(r[0])];need(len(owners)<=1,'Unique actual raw case owner')
   if owners:db.execute('INSERT INTO raw VALUES(?,?,?)',('legacy24',owners[0][1],path));legacy_raw[owners[0][1]]+=1
  need(all(legacy_raw[caseid]==count for root,caseid,count in rawroots),'All actual legacy outputs, not all dependency count mistaken for raw count')
  # Future completed durable current16 DB expanded with exact retained schema,
  # SHA/size,16case rows/seen checks and content hashes before/after readonly use.
  expander=R/'tools/m4-138-controls-review/expand_proof_inventory.py';need(str(expander)in A['files'],'Actual expansion code admitted');measure(expander,A['files'][str(expander)]);sp=importlib.util.spec_from_file_location('controls_composite_expand',expander);expand=importlib.util.module_from_spec(sp);sp.loader.exec_module(expand)
  raw=reports['current16_fullraw'];need(raw['raw_export_readers_closed']is True and raw['all_bounded_readers_closed']is True and raw['raw_exports_all_logical_entries']is True,'Actual terminal raw closure');need(raw['counts']['whole_export_targets_authenticated']==10691866 and raw['counts']['whole_exported_retry_files_equal']==3547696,'Distinct current raw/retry domains');need(raw['controls_verification_sha256']==M['current16_verification_sha256'],'Actual independently verified semantic producer')
  expansion=expand.expand(roles['current16_fullraw']['path'],roles['current16_fullraw']['sha256'],lambda p,h:measure(p,h,scope='current16-whole-inventory'))
  proof=raw['proof_inventory'];connection=sqlite3.connect(Path(proof['path']).as_uri()+'?mode=ro',uri=True)
  try:
   connection.execute('PRAGMA query_only=ON')
   for path,caseid in connection.execute('SELECT path,rawcase FROM physical WHERE rawcase IS NOT NULL ORDER BY k'):db.execute('INSERT INTO raw VALUES(?,?,?)',('current16',str(caseid),path))
  finally:connection.close()
  measure(proof['path'],proof['sha256'],proof['bytes'],'current16-whole-inventory');need(db.execute("SELECT count(*) FROM raw WHERE scope='current16'").fetchone()[0]==10691866,'Every actual current16 raw path unique')
  semantic=reports['current16_semantic_review'];need(semantic['current16_fullraw_sha256']==roles['current16_fullraw']['sha256']and semantic['execution_sha256']==roles['current8_execution']['sha256']and semantic['all16_distinct_modes_reviewed']is True and semantic['finite_GDI_owner_manual_cleanup_lifetime_predicates_reviewed']is True and semantic['committed_source_write_values_independently_instruction_evaluated']is False and semantic['committed_write_values_from_actual_source_witness']is True and semantic['whole_fault_memory_fully_source_predicted']is False,'Future independent complete semantic/resource scope; raw integrity is not semantics')
  pre=reports['legacy_prelaunch_complete_review'];need(pre['legacy_preparation_sha256']==LEGACY_PREP and pre['legacy_build_sha256']==LEGACY_BUILD and pre['all_seven_named_fields_physically_reviewed']is True,'Future actual whole legacy7 physical facets, not inferred baseline values')
  need(roles['legacy_prelaunch_complete_review']['sha256']==A['legacy_complete7_sha256']and str(Path(roles['legacy_prelaunch_complete_review']['path']).resolve())==str(Path(A['legacy_complete7_report']).resolve()),'Actual independently ROOT-run complete7 receipt, never arbitrary descriptions')
  need(pre['physical_domain_derivation_schema']=='legacy12-complete7-source-derived-v1'and pre['legacy_four_source_sha256']=='7979b6e0423debf0cb7972cf28f315207dcb56f54e7e0fb09b4e12dad382d73c'and pre['legacy_prefix_ROOT_review_sha256']=='c86c8082f396b517b805e182c4ea4a9b4396a9e19b290bf8fc098d172e9478bb'and pre['legacy_whole7_ledger_sha256']=='8d94a0409f3ee13480fc5cf1f28b11b11ce2b471ac94da3d845fd6c996c4095d'and pre['legacy24_terminal_sha256']==roles['legacy24_aggregate']['sha256'],'All exact whole source/compiled/TLS/body/actualterminal proof domains')
  need(pre['current8_used_as_legacy_proof']is False and pre['terminal_content_revalidation_by_composer_still_required']is True,'No borrowed current8 domain or inherited terminal-only byte assertion')
  expected_physical={'whole_intended_protected_IAT_mutation_repairs':2,'whole_diagnostic_only_delta':1,'whole_authored_public_faults':len({r['mode']for r in cases}),'whole_true_source_entry_observer':1,'actual_compiler_TLS_cells':56,'whole_linked_control_functions':7,'entry_observer_inlined_in_whole_MFC_entry':1}
  need(set(pre['counts'])==set(expected_physical)and all(typed(pre['counts'][k],v)for k,v in expected_physical.items()),'Exact seven counts after source-derived physical proof; not baseline-only or annotations')
  limits=reports['current8_scope_review']['observation_limits'];need(all(limits[k]is False for k in('old_registry_private_vectors_retry_claim','full_memory_permission_snapshot_claim','whole_hidden_Runtime_frames_or_permissions_claim')),'Current source/serializer limitations explicit')
  named=reports['named_CS24_TLS64_supplement'];need(named['counts']['whole_borrowed_guestCS24_prefixes']==12 and named['counts']['source_TLS_refusal_frame64']==2,'Distinct actual CS24 and TLS64 runtime proofs');legacy_counts=dict(sums);legacy_counts['whole_borrowed_guestCS24_prefixes']=named['counts']['whole_borrowed_guestCS24_prefixes'];legacy_counts['source_TLS_refusal_frame64']=named['counts']['source_TLS_refusal_frame64'];legacy_counts['whole_export_targets_authenticated']=db.execute('SELECT COUNT(*) FROM raw').fetchone()[0]
  # This final independent byte pass is mandatory; SQLite seen/stat values do
  # not replace current content hashes. No giant in-memory physical file map.
  for path,h,size in db.execute('SELECT path,sha,size FROM physical ORDER BY path'):need(sha(path)==h and Path(path).stat().st_size==size,'Final whole measured union row')
  total=db.execute('SELECT COUNT(*)FROM physical').fetchone()[0];db.commit();db.close();closed=True;database=out/'whole-ordinary-union.sqlite';inventory=dict(path=str(database),sha256=sha(database),bytes=database.stat().st_size,physical_rows=total,sqlite_closed_before_hash=True,every_row_whole_byte_rehashed=True,expansion_query='SELECT path,sha,size,seen FROM physical ORDER BY path',scope_edges_query='SELECT scope,path,sha FROM edges ORDER BY scope,path')
  edges={row['path']:row['sha256']for row in roles.values()};edges[str(database)]=inventory['sha256'];edges[str(Path(__file__).resolve())]=sha(__file__)
  prep=dict(passed=True,scope_identity='current138_controls_preparation_composite_v1',control_cases=len({r['mode']for r in cases}),underlying_current8_preparation=roles['current8_preparation'],underlying_legacy12_preparation=roles['legacy12_preparation'],old_registry_private_vectors_retry_claim=False,full_memory_permission_snapshot_claim=False,observation_limits=limits,files=edges)
  prelaunch=dict(passed=True,build_sha256=CURRENT_BUILD,counts=pre['counts'],measurements=reports['current8_physical_review']['measurements'],scoped_legacy_build=roles['legacy12_build'],files=edges)
  controls=dict(passed=True,scope_identity='current138_terminal_legacy24_current16_controls_composite_v1',counts=legacy_counts,current16_counts=raw['counts'],execution_sha256=roles['current8_execution']['sha256'],raw_exports_all_logical_entries=expansion['raw_rows']==10691866,raw_export_readers_closed=raw['raw_export_readers_closed'],all_bounded_readers_closed=closed and raw['all_bounded_readers_closed'],whole_old_registry_private_retry_claim=False,whole_permissions_retry_claim=False,initializer_credit=0,proof_inventory=inventory,acceptance_requires_inventory_expansion=True,files=edges)
  for leaf,value in(('controls-preparation.json',prep),('controls-prelaunch.json',prelaunch),('controls.json',controls)):(out/leaf).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
  (out/'independent-review-required.json').write_text(json.dumps(dict(prepared=True,controls_path=str(out/'controls.json'),controls_sha256=sha(out/'controls.json'),all45_final_mapping_pending_independent_review=True,allowance_created=False,configuration_created=False,acceptance_executed=False,accepted_function_credit=0),indent=2)+'\n',encoding='utf-8')
 finally:
  if not closed:db.close()
if __name__=='__main__':main(*sys.argv[1:])
