"""Bounded ordinary candidate recommendations, never acceptance or execution."""
from pathlib import Path
import collections, hashlib, importlib.util, json, struct, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
CURRENT = '4c961184ef9442788eef3eba69bd37dc85427f123d4494ed30d6fa7e0123f83f'
PREFIX = 'c86c8082f396b517b805e182c4ea4a9b4396a9e19b290bf8fc098d172e9478bb'
BUILD = '9a65633f858e7c06c5ca09a8191a41051321cf2848c1a25b4318bd4c61c08a9f'
LINKS = 'd89d74c0808f07c535ceb61914d085ae74e00d0058cddfa60421722dd12ceebe'
LEGACY = {
 'counts.whole_intended_protected_IAT_mutation_repairs',
 'counts.whole_diagnostic_only_delta', 'counts.whole_authored_public_faults',
 'counts.whole_true_source_entry_observer',
 'counts.entry_observer_inlined_in_whole_MFC_entry',
 'counts.whole_linked_control_functions', 'counts.actual_compiler_TLS_cells'}
PREFIXES = ('main', '?mfc_mutate@@', '?mfc_retry_snapshot@@', '?mfc_control_entry@@')

def at(value, field):
 for part in field.split('.'): value = value[part]
 return value

def candidate(row, measured, report, digest):
 old = row['baseline_expected']; assert type(measured) is type(old)
 if isinstance(old, bool): assert measured is old, 'No Boolean flip'
 return dict(gate='controls_prelaunch', baseline_field=row['baseline_field'],
  baseline_expected=old, baseline_type=row['baseline_type'], current_expected=measured,
  current_field='measurements.current8_shared_MFC_prelaunch.' + row['baseline_field'],
  current_report_path=str(report), current_report_sha256=digest,
  status='identity_candidate' if old == measured else 'finite_delta_candidate',
  physical_domain=row['named_domain'], reason=row['required_proof'],
  authoritative_allowance=False, authoritative_composite_gate_still_required=True)

def select_seven(rows):
 result=[]; seen=set()
 for row in rows:
  name=row.get('symbol','')
  if row.get('scope')!='actual prefix control/caller/cleanup':continue
  if not any(name==p if p=='main' else name.startswith(p) for p in PREFIXES):continue
  key=(row['level'], name, row['address'])
  assert key not in seen, 'Duplicate whole-body attribution'; seen.add(key);result.append(row)
 assert len(result)==7 and collections.Counter(x['level']for x in result)==dict(O0=4,O2=3)
 for level in ('O0','O2'):
  for p in PREFIXES:
   count=sum(x['level']==level and (x['symbol']==p if p=='main' else x['symbol'].startswith(p))for x in result)
   assert count==(0 if level=='O2'and p=='?mfc_control_entry@@'else 1), (level,p,count)
 return result

def main(name):
 out=R/'reports/m4-138-criteria-frontier'/name;assert not out.exists();out.mkdir();pins={}
 def pin(path, expected=None):
  path=Path(path).resolve();assert path.suffix.lower()not in('.mwb','.mwi','.zip')and path.name!='transport.json'
  assert path.stat().st_size<64*1024*1024, 'Bounded ordinary input'
  data=path.read_bytes();h=hashlib.sha256(data).hexdigest();assert expected is None or h==expected,(str(path),h,expected)
  assert pins.setdefault(str(path),h)==h;return data
 def read(path,h=None):return json.loads(pin(path,h))
 def module(path,name):
  pin(path);s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 cp=R/'reports/m4-138-criteria-frontier/root-current8-physical-review-r5/report.json';current=read(cp,CURRENT);assert current['passed']is True
 domain=read(R/'reports/m4-138-criteria-frontier/current-controls-prelaunch-domain-map-r1/field-domain-map.json');assert len(domain)==21 and len({x['baseline_field']for x in domain})==21
 measurement=current['measurements']['current8_shared_MFC_prelaunch'];recommend=[];pending=[]
 for row in domain:
  if row['baseline_field']in LEGACY:
   pending.append(dict(**row, status='legacy_named_domain_pending_strict24_aggregate', current8_not_a_substitute=True));continue
  value=at(measurement,row['baseline_field']);recommend.append(candidate(row,value,cp,CURRENT))
 assert len(recommend)==14 and len(pending)==7 and len({x['current_field']for x in recommend})==14
 pp=R/'reports/m4-138-preresource-root-review/root-review-r1/report.json';prefix=read(pp,PREFIX)
 assert prefix['passed']is True and prefix['worker_executed']is False and prefix['canonical_reader_opened']is False
 assert prefix['current12_refusals_proven']is False and prefix['TLS64_runtime_proven']is False
 lp=pp.parent/'links.json';links=read(lp,LINKS);assert prefix['files'][str(lp)]==LINKS
 seven=select_seven(links)
 bp=R/'reports/m4-138-preresource-controls/build-r4/build.json';build=read(bp,BUILD);assert build['passed']is True and build['worker_executed']is False
 C=module(R/'tools/m4-tree-review/amd64_coff.py','seven_coff')
 M=module(R/'tools/m4-tree-review/review_mfc1168_native_prelaunch_v4.py','seven_pe')
 bodies=[]
 for level in ('O0','O2'):
  w=build['workers'][level];op=Path(w['object']);wp=Path(w['path'])
  assert prefix['files'][str(op)]==w['object_sha256']and prefix['files'][str(wp)]==w['sha256']
  sy,se=C.parse(pin(op,w['object_sha256']));image=M.AMD64Image(pin(wp,w['sha256']))
  for row in [x for x in seven if x['level']==level]:
   raw,rel=C.function(sy,se,row['symbol']);assert len(raw)==row['whole_bytes']and len(rel)==row['relocations']
   owning=[s for s in image.sections if s['executable']and image.image_base+s['virtual_address']<=row['address']and row['address']+len(raw)<=image.image_base+s['virtual_address']+s['raw_size']];assert len(owning)==1
   s=owning[0];offset=s['raw_offset']+row['address']-image.image_base-s['virtual_address'];physical=image.data[offset:offset+len(raw)]
   masks=set();relrows=[]
   for r in rel:
    assert 0<=r['offset']<=len(raw)-4
    masks.update(range(r['offset'],r['offset']+4))
    relrows.append(dict(offset=r['offset'],type=r['type'],symbol=r['symbol'],COFF_DWORD=raw[r['offset']:r['offset']+4].hex(),linked_DWORD=physical[r['offset']:r['offset']+4].hex()))
   assert all(a==b for i,(a,b)in enumerate(zip(raw,physical))if i not in masks)
   bodies.append(dict(**row,COFF_whole_sha256=hashlib.sha256(raw).hexdigest(),linked_whole_sha256=hashlib.sha256(physical).hexdigest(),object_path=str(op),object_sha256=w['object_sha256'],worker_path=str(wp),worker_sha256=w['sha256'],relocations_complete=relrows,nonrelocation_whole_bytes_equal=True,relocation_TLS_and_target_attribution_retained_ROOT_proof=str(pp)))
 assert len(bodies)==7
 # Complete source provenance belongs to the ROOT inverse review, not seven guessed function snippets.
 sp=R/'reports/m4-138-preresource-controls/preparation-r3/report.json';preparation=read(sp,build['preparation_sha256'])
 for leaf in ('native_main.cpp','controls_main.cpp'):
  path=sp.parent/leaf;expected=prefix['files'][str(path)];pin(path,expected)
 baseline=R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch.py';text=pin(baseline).decode();assert "for prefix in ('main','?mfc_mutate@@','?mfc_retry_snapshot@@','?mfc_control_entry@@')"in text
 pin(R/'tools/m4-138-preresource-root-review/review_v4.py');pin(__file__);pin(sys.executable)
 # Negative controls are pure structures; they never change the sealed evidence.
 adverse=[]
 def reject(label,fn):
  try:fn()
  except (AssertionError,KeyError):adverse.append(label);return
  raise AssertionError('Adverse accepted: '+label)
 reject('Boolean flip',lambda:candidate(next(x for x in domain if x['baseline_field']=='worker_launched'),True,cp,CURRENT))
 reject('scalar type coercion',lambda:candidate(next(x for x in domain if x['baseline_field']=='counts.whole_current_typed_bridge_functions'),True,cp,CURRENT))
 reject('duplicate whole-body row',lambda:select_seven(links+[seven[0]]))
 reject('one whole helper missing',lambda:select_seven([x for x in links if x is not seven[0]]))
 reject('15 target joins substituted for whole-body rows',lambda:select_seven([dict(x,scope='target joins only')for x in seven]))
 assert len(adverse)==5
 for leaf,value in [('current14-field-candidates.json',recommend),('legacy7-pending-domain-map.json',pending),('legacy7-whole-body-ledger.json',bodies)]:
  p=out/leaf;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
 report=dict(passed=True,scope='Bounded ordinary recommendations and exact deduplicated whole-body subset; no authoritative criteria allowance or composite gate',current8_fields=14,current8_identity_candidates=sum(x['status']=='identity_candidate'for x in recommend),current8_finite_delta_candidates=sum(x['status']=='finite_delta_candidate'for x in recommend),legacy7_pending=True,legacy7_whole_linked_control_functions=7,legacy_whole_body_level_counts=dict(O0=4,O2=3),prefix_typed_target_joins_separate=prefix['counts']['actual_current_control_typed_function_target_joins'],legacy_compiler_TLS_occurrences_separate=prefix['counts']['actual_compiler_TLS_cells'],current8_compiler_TLS_occurrences_separate=measurement['counts']['actual_compiler_TLS_cells'],source_whole_inverse_proof_retained=str(pp),no_new_link_uniqueness_or_TLS_review_claim=True,adverse_controls=adverse,strict24_aggregate_not_read_or_inferred=True,worker_executed=False,canonical_reader_opened=False,authoritative_allowance=False,accepted_function_credit=0,files=pins)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
