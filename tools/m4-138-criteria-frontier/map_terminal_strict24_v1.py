"""Bounded24 receipt metadata facets; no raw inventory/aggregate rerun."""
from pathlib import Path
import collections,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main(name):
 out=R/'reports/m4-138-criteria-frontier'/name;assert not out.exists();out.mkdir();pins={}
 def read(p,h=None,head_only=False):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.stat().st_size<32*1024*1024
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or h==v;assert pins.setdefault(str(p),v)==v
  if not head_only:return json.loads(p.read_bytes())
  with p.open('rb')as f:head=f.read(65536)
  marker=b'  "files":';assert head.count(marker)==1,'Bounded known producer files-last schema'
  metadata=json.loads(head[:head.index(marker)]+b'  "files":{}}')
  # Authenticate whole receipt bytes, parse only bounded leading fields.
  with p.open('rb')as f:f.seek(-8,2);tail=f.read()
  assert tail.rstrip().endswith(b'}\n}')or tail.rstrip().endswith(b'}\r\n}'),'Known complete top-level terminal files map'
  return metadata
 batch_path=R/'reports/m4-138-preresource-strict-review/root-strict-remaining23-r1/report.json';batch=read(batch_path,'2cf7c24beaa1bf64ce79861c1b08c2ade3e3498acbde8c697f819119341ec654')
 assert batch['passed']is True and batch['all_children_terminal']is True and batch['strict_case_count']==24 and batch['capture_reader_opened']is False
 seen=set();totals=collections.Counter();cases=[]
 for row in batch['strict_cases']:
  v=read(row['report'],row['sha256'],True);key=v['level'],v['mode'];assert key not in seen;seen.add(key)
  assert key==(row['level'],row['mode'])and v['passed']is True and v['all_bounded_readers_closed']is True and type(v['initializer_credit'])is int and v['initializer_credit']==0
  assert v['execution_sha256']==row['raw_execution_sha256']and Path(v['execution']).resolve()==Path(row['raw_execution']).resolve()
  for field in('whole_Runtime_hidden_private_retry_claim','whole_old_registry_private_retry_claim','whole_permissions_retry_claim'):assert v[field]is False
  assert all(type(n)is int and n>=0 for n in v['counts'].values())
  assert v['counts']['actual_precise_denials']==v['counts']['actual_unchanged_poisoned_retries']==v['counts']['entryframe64_checked']==1 and v['counts']['whole_caller_FX512_ENV28']==2
  totals.update(v['counts']);cases.append(dict(level=key[0],mode=key[1],report=row['report'],sha256=row['sha256'],execution=v['execution'],execution_sha256=v['execution_sha256'],counts=v['counts'],closed=True,observation_claims={k:v[k]for k in('whole_Runtime_hidden_private_retry_claim','whole_old_registry_private_retry_claim','whole_permissions_retry_claim')}))
 assert seen=={(l,m)for l in('O0','O2')for m in range(1,13)}
 schema_path=R/'reports/m4-138-criteria-frontier/root-pending-controls-schema-r1/pending-45-composite-schema.json'
 if not schema_path.exists():schema_path=R/'reports/m4-138-criteria-frontier/current-controls-composite-schema-r1/pending-45-composite-schema.json'
 schema=read(schema_path);rows=schema['field_mapping'];assert len(rows)==45
 fields=[]
 for r in rows:
  gate=r['gate'];field=r['baseline_field'];value=None;source=None;obligation=r['substantive_requirement'];kind='pending_named_physical_measurement'
  if gate=='controls_preparation':
   value=12 if field=='control_cases'else False
   source='strict_cases exact level/mode set'if field=='control_cases'else'all24 explicit scoped '+('whole_old_registry_private_retry_claim'if field=='old_registry_private_vectors_retry_claim'else'whole_permissions_retry_claim')
   kind='bounded_actual_metadata_support; complete producer source/inventory union still mandatory'
  elif gate in('controls','controls_review')and field.startswith('counts.')and field!='counts.whole_export_targets_authenticated':
   count=field.split('.',1)[1];assert count in totals,(gate,count);value=totals[count];source='exact strict24 named counts.'+count
   kind='actual_strict24_named_facet; terminal complete physical aggregate and independent provenance required'
  elif gate=='controls'and field in('whole_old_registry_private_retry_claim','whole_permissions_retry_claim'):
   value=False;source='all24 explicit '+field;kind='bounded_scope_identity; not complete hidden-vector or permission observation'
  elif gate in('controls','controls_review')and field=='initializer_credit':
   value=0;source='each24 initializer_credit integer0';kind='bounded_actual_metadata_support'
  if value is not None:
   assert type(value)is type(r['baseline_expected'])
   if isinstance(value,bool):assert value is r['baseline_expected'],'No Boolean flip'
  fields.append(dict(gate=gate,baseline_field=field,baseline_expected=r['baseline_expected'],baseline_type=r['baseline_type'],named_domain=r['named_domain'],measured_strict24_support=value,source_facet=source,typed_relation=None if value is None else('identity'if value==r['baseline_expected']else'finite_named_scope_delta'),support_kind=kind,still_required=obligation,authoritative_binding_created=False))
 assert len(fields)==45
 for leaf,data in [('strict24-bounded-case-facets.json',cases),('pending45-named-facet-mapping.json',fields)]:
  p=out/leaf;p.write_text(json.dumps(data,indent=2)+'\n');read(p)
 for p in(Path(__file__).resolve(),Path(sys.executable).resolve()):
  with p.open('rb')as f:pins[str(p)]=hashlib.file_digest(f,'sha256').hexdigest()
 report=dict(passed=True,scope='Authenticated bounded24 terminal receipt metadata only; no raw/declared files expansion or actual aggregation',strict_case_metadata=24,named_legacy_prefix_modes=12,named_MFC_counter_totals=dict(totals),whole_current_entry_frame64_checks=totals['entryframe64_checked'],fields=45,measured_metadata_support_fields=sum(x['measured_strict24_support']is not None for x in fields),all_current8_or_fullraw_union_fields_still_pending=True,complete_raw_inventory_authentication_claim=False,independent_raw_review_claim=False,full_aggregate_executed=False,worker_executed=False,archive_reader_opened=False,configuration_created=False,allowance_created=False,initializer_credit=0,accepted_function_credit=0,files=pins)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(hashlib.sha256(p.read_bytes()).hexdigest());print(json.dumps(dict(totals)))
if __name__=='__main__':main(sys.argv[1])
