"""UNEXECUTED ROOT substantive 45-field review; run only after an actual PASS of
review_completed_composite_v3. Emits the ROOT_field_review consumed by
prepare_postterminal_templates_v1 final45. Creates no allowance/configuration.

For each mapped field it reads the actual composite gate value, classifies it
as identity (same field, same typed value) or changed, and requires mechanical
evidence for every changed value:
- actual_compiler_TLS_cells: equals the independently ROOT-run legacy complete7
  physical review count (different, actually compiled legacy12 build);
- whole_retry_vectors: equals the streamed legacy24 aggregate counter, and the
  per-case verifier loop that increments it is textually identical to the
  baseline connected-controls loop (same predicate, larger retained inventory);
- execution_sha256: equals the manifest's current8 execution role;
- controls_verification_sha256: equals the new composite controls gate SHA;
- whole_export_targets_authenticated: equals the reviewer's whole expanded raw
  rows (current16 10,691,866 plus legacy24 raw outputs).
Any other changed value refuses.
"""
from pathlib import Path
import hashlib,importlib.util,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
MANIFEST=('reports/m4-controls-terminal-composite/completed-input-preparation-r4/completed-input-manifest.json','e8e3c1ecd45784a51355e7f89fc30b7eb7977ed85598d0f85746823d77cf0251')
MAPPING=('reports/m4-138-criteria-frontier/terminal45-typed-recipe-r1/pending45-terminal-field-mapping.json','79d6141deea3f2a7cc7faa58d2a1ada78a3122f3147d5fa90dbddb8b5ddce756')
DISPOSITION=('reports/m4-controls-terminal-composite/field-disposition-r1/per-field-disposition.json','fbc42704a584377455d0d85593127c547ccfaf47e04f73c4714cbf1b972137c7')
BASE_LOOP=('tools/m4-mfc1168-native/verify_connected_controls.py',)
CASE_LOOP=('reports/m4-138-preresource-strict-review/preparation-r5/verify_case_v5.py',)
LOOP="      for key in keys:eq(a.data(key),a.data(key.replace('/retry-before/','/retry-after/')),'Entire unchanged poisoned retry '+key);counts['whole_retry_vectors']+=1"
PREFIX="     for prefix in(stem+'retry-before/',stem+'MFC/retry-before/'):"
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def at(d,k):
 for part in k.split('.'):d=d[part]
 return d
def typed(a,b):return type(a)is type(b)and a==b
def retry_predicate_identical(pin):
 """Pure source check usable before the reviewer runs."""
 base=pin(R/BASE_LOOP[0]).read_text().splitlines();case=pin(R/CASE_LOOP[0]).read_text().splitlines()
 for lines in(base,case):
  assert lines.count(LOOP)==1 and lines.count(PREFIX)==1 and lines.index(PREFIX)+2==lines.index(LOOP),'Same two retry prefixes and whole-key comparison loop'
 return True
def stream_counts(path,pin,h):
 sp=importlib.util.spec_from_file_location('stream_json',pin(R/'tools/m4-138-controls-review/full_raw_review_v2.py'));J=importlib.util.module_from_spec(sp);sp.loader.exec_module(J)
 out={}
 with pin(path,h).open(encoding='utf-8')as f:
  s=J.StreamJSON(f);s.expect('{');first=True
  while True:
   s.trim()
   if s.buf.startswith('}'):break
   if not first:s.expect(',')
   k=s.value();s.expect(':');first=False
   if k=='files':
    for _ in s.pairs():pass
   else:out[k]=s.value()
 return out
def main(reviewer_path,reviewer_sha,name):
 pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(str(p),v,h);assert pins.setdefault(str(p),v)==v;return p
 pin(__file__);rv=json.loads(pin(reviewer_path,reviewer_sha).read_bytes())
 assert rv['passed']is True and rv['all_named_composite_domains_independently_reviewed']is True and rv['all_scoped_physical_edges_verified']is True and rv['whole_composite_union_expanded']is True and rv['final_input_conservation']['metadata_only_cache_used']is False,'Actual closed independent composite reviewer PASS only'
 A=json.loads(pin(rv['ROOT_admission_path'],rv['ROOT_admission_sha256']).read_bytes());gates_hash=A['composite_gate_hashes'];assert gates_hash['controls']==rv['controls_sha256']
 controls_dir=(R/'reports/m4-controls-terminal-composite/terminal-composite-r1').resolve()
 assert A['files'][str(controls_dir/'controls.json')]==gates_hash['controls'],'Admission pinned the actual terminal composer controls gate'
 gates={k:dict(path=str((controls_dir/leaf).resolve()),sha256=gates_hash[k])for k,leaf in(('controls_preparation','controls-preparation.json'),('controls_prelaunch','controls-prelaunch.json'),('controls','controls.json'))}
 gates['controls_review']=dict(path=str(Path(reviewer_path).resolve()),sha256=reviewer_sha)
 actual={k:json.loads(pin(v['path'],v['sha256']).read_bytes())for k,v in gates.items()}
 M=json.loads(pin(R/MANIFEST[0],MANIFEST[1]).read_bytes());mapping=json.loads(pin(R/MAPPING[0],MAPPING[1]).read_bytes());disp=json.loads(pin(R/DISPOSITION[0],DISPOSITION[1]).read_bytes());assert len(mapping)==len(disp)==45
 agg=stream_counts(M['roles']['legacy24_aggregate']['path'],pin,M['roles']['legacy24_aggregate']['sha256']);pre=json.loads(pin(M['roles']['legacy_prelaunch_complete_review']['path'],M['roles']['legacy_prelaunch_complete_review']['sha256']).read_bytes())
 assert retry_predicate_identical(pin)
 reviews={};changed=[]
 for m,d in zip(mapping,disp):
  assert(m['gate'],m['baseline_field'])==(d['gate'],d['field']);v=at(actual[m['gate']],m['composite_field']);assert type(v).__name__==m['baseline_type']and(type(v)is not bool or v is m['baseline_expected'])
  leaf=m['baseline_field'].split('.')[-1];identity=m['composite_field']==m['baseline_field']and typed(v,m['baseline_expected'])
  if identity:reason='Same field and same typed value '+repr(v)+' re-measured in the actual composite gate; no translation required'
  elif leaf=='actual_compiler_TLS_cells':assert typed(v,pre['counts']['actual_compiler_TLS_cells'])and pre['physical_domain_derivation_schema']=='legacy12-complete7-source-derived-v1';reason='Physical TLS cell count of the actually compiled legacy12 build from the independent complete7 source/compiled review; baseline counted an earlier build'
  elif leaf=='whole_retry_vectors':assert typed(v,agg['counts']['whole_retry_vectors']);reason='Identical per-key whole retry comparison loop and prefixes as the baseline verifier; legacy24 workers retain a larger retry inventory, every key compared byte-for-byte'
  elif leaf=='execution_sha256':assert v==M['roles']['current8_execution']['sha256'];reason='Exact independently admitted current8 execution receipt replaces the historical execution identity'
  elif leaf=='controls_verification_sha256':assert v==gates_hash['controls'];reason='Identity of the new reviewed composite controls gate replaces the historical controls receipt'
  elif leaf=='whole_export_targets_authenticated':assert v==rv['expansion']['raw_rows']and rv['expansion']['current16_raw_rows']==10691866;reason='Distinct scoped raw membership after full composite expansion (current16 plus legacy24 outputs), every byte rehashed'
  else:raise AssertionError('Unreviewed changed value '+m['gate']+':'+m['baseline_field'])
  if not identity:changed.append(m['gate']+':'+m['baseline_field'])
  reviews[m['gate']+':'+m['baseline_field']]=dict(actual_report_sha256=gates[m['gate']]['sha256'],actual_field=m['composite_field'],actual_value=v,identity=identity,substantive_ROOT_reviewed=True,physical_domain=m['physical_domain']if len(m['physical_domain'].strip())>=12 else d['scope_exclusion'],reason=reason,scope_exclusion=d['scope_exclusion'])
 assert len(changed)==6,changed
 for p_,h in list(pins.items()):assert sha(p_)==h
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-controls-terminal-composite'/name;assert not out.exists();out.mkdir()
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,independent_review=True,fields_reviewed=45,identity_fields=39,changed_fields=changed,per_field_reviews=reviews,actual_composite_gates=gates,allowance_created=False,configuration_created=False,accepted_function_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),changed=changed)))
if __name__=='__main__':main(*sys.argv[1:])
