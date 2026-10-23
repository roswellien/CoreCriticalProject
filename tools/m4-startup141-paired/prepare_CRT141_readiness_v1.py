"""Current CRT source/schema readiness plus pure span controls, no readers."""
from pathlib import Path
import ast,copy,hashlib,json
R=Path(__file__).resolve().parents[2]

def main():
 out=R/'reports/m4-startup141-paired/CRT-readiness-r1';assert not out.exists();files={}
 def read(p):
  p=Path(p).resolve();assert p.stat().st_size<4*1024*1024;raw=p.read_bytes();files[str(p)]=hashlib.sha256(raw).hexdigest();return raw
 parents=[R/'tools/m4-startup138-paired'/n for n in('prove_CRT_import_cells_v3.py','prove_original_CRT_data_footprint_v3.py','preflight_CRT_page_policy_v4.py','crt_page_policy_v5.py')]
 for p in parents:ast.parse(read(p).decode())
 helper=R/'tools/m4-startup141-paired/CRT_footprint141_v1.py';env={};exec(compile(ast.parse(read(helper).decode()),str(helper),'exec'),env)
 page=env['PAGE'];check=env['check_supplied_spans'];controls=[]
 good=([4,5],[(0x7800105c,page+8,0,4,0)],[dict(PC=0x7800106d,address=page+0x130,bytes=24,role='guest_CS24',direction='read_write',origin='synthetic exact typed ABI buffer')],[8,9])
 assert check(*good)['complete_current141_footprint']is False;controls.append(dict(name='positive_supplied_spans_only',rejected=False))
 tests=[
  ('source_read_overlap',lambda x:x[1].append((1,page+4,0,1,0))),
  ('source_write_overlap',lambda x:x[1].append((1,page+4,0,1,1))),
  ('partial_cross_page_source_overlap',lambda x:x[1].append((1,page-1,0,6,0))),
  ('API_read_overlap',lambda x:x[2].append(dict(PC=1,address=page+4,bytes=1,role='API-input',direction='read',origin='own buffer'))),
  ('API_write_overlap',lambda x:x[2].append(dict(PC=1,address=page+4,bytes=1,role='API-output',direction='write',origin='own buffer'))),
  ('API_partial_cross_page_overlap',lambda x:x[2].append(dict(PC=1,address=page-8,bytes=14,role='API-input',direction='read',origin='own buffer'))),
  ('physical_direct_overlap',lambda x:x[3].append(4)),
  ('duplicate_opaque_offset',lambda x:x[0].append(4)),
  ('bool_opaque_offset',lambda x:x[0].append(True)),
  ('opaque_offset_overflow',lambda x:x[0].append(4096)),
  ('source_address_wrap',lambda x:x[1].append((1,2**32-2,0,4,0))),
  ('zero_width',lambda x:x[1].append((1,page,0,0,0))),
  ('invalid_direction',lambda x:x[1].append((1,page,0,1,2))),
  ('missing_API_role',lambda x:x[2][0].pop('role')),
  ('empty_API_origin',lambda x:x[2][0].update(origin='')),
 ]
 for name,mutate in tests:
  args=copy.deepcopy(good);mutate(args);refused=False
  try:check(*args)
  except(AssertionError,KeyError,ValueError):refused=True
  assert refused;controls.append(dict(name=name,rejected=True))
 source=R/'reports/m4-original141-source/source-r7/report.json';report=json.loads(read(source));assert report['passed']and report['original_validation_sha256']=='e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c'
 registry=source.parent/'registry-source-relations.json';rows=json.loads(read(registry));assert len(rows)==846 and len({(r['sequence'],r['phase'],r['root'])for r in rows})==846
 assert all(not any(k in r for k in('before_original','after_original','source_store','source_derived_begin','source_derived_next'))for r in rows)
 requirements=[
 dict(domain='current_own_inputs',required='Only genuine strict3 original141 export and same-level actual native141 source6; two complete4096-byte CRT pages7802E000/78037000 per12 domains. Current two provider bootstrap/CS24 input pages separately authenticated; no native6 original138 row.'),
 dict(domain='named144',required='Resolve all144 physical MSVCRT KERNEL32 imports from current captured loaded module identities/EAT/forwarder chain; installed eight shims match current compiled rebased source and exact phase15 restore/reinstall spec. Original shim targetbase/ranges and modulebases cannot be inherited138 constants.'),
 dict(domain='mode1_229',required='Keep actual physical229-PC malloc/free/onexit closed-successor proof and mode1 branch predicates. Derive current846 mode/lock inputs and all current API counts from actual26DWORD ledgers (zeroPC9/19 retained), not old828/2718/1422 counts. Any new constructor CRT call/PC outside closure must extend physically, never prune to229 by convenience.'),
 dict(domain='lock13_lock25',required='Exact lock25 cell and whole24B lock13 original-vs-native descriptor relation, native40B owner identity. Derive actual Enter/Leave counts per sequence from exhaustive current source/API chronology and exact instance; parent hardcoded108 pairs cannot be copied or blindly changed111.'),
 dict(domain='complete_source_API_footprint',required='Original7 six families and current native6 own source operands including18/36 constructor source-derivations, every typed input/output buffer/frame/CS24 region. Authenticate each whole source artifact; stream widget181MB. Pure supplied-span guard proves disjointness only; API/source inventory completeness must independently close.'),
 dict(domain='registry111_source_schedule',required='New current141 original registry schedule with own BEFORE, literal cursor/callback stores, successful realloc input/full initial capacities and all before/after begin/next from source derivation. Existing846 registry-source-relations rows retain hashes/lengths/growth/callback but omit metadata/source_store needed inherited CRT registry_fields. Native same-source journal schedule must include111 callbacks/ctor chronology; compare whole vector/backing and complete unused tails.'),
 dict(domain='allphase_global',required='Separate whole5F2000 current constructor-global before/after on all1692paired phases3384 endpoints. Source-owned ctor publication pointers and intervening old53 family stores must be typed; structural54 constructor-only global comparisons cannot prove this allphase carry.'),
 dict(domain='whole_page_policy',required='Only after domains above: exact whole2-page equality from own input+source registry fields+named IAT mode+typed lock cells/objects; opaque startup offsets disjoint from all complete physical/own source/API footprints. No whole-page masking/source AFTER input. Physical MFC phase15 table binding, normal28/56 FS separate ctor7/14/21, no new global merger.'),
 ]
 out.mkdir(parents=True)
 for leaf,obj in [('pure-span-controls.json',dict(pure_controls=True,controls=controls,actual_inputs_consumed=False)),('required-current-artifacts.json',requirements)]:
  p=out/leaf;p.write_text(json.dumps(obj,indent=2)+'\n');files[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 files[str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 q=out/'preparation-only.json';q.write_text(json.dumps(dict(prepared_only=True,pure_controls=len(controls),current_original_registry846_metadata_inspected=True,current_registry_pointer_schedule_missing=True,parent108_lock13_count_not_reused=True,current144_named_import_execution_pending=True,retained229_mode1_actualcurrent_proof_pending=True,complete_two_page_policy_not_admitted=True,pure_helper_scope='Provided byte spans only; no footprint completeness or physical import proof',canonical_reader_opened=False,ordinary_export_reader_opened=False,source_models_executed=False,whole_union_executed=False,worker_launched=False,accepted_function_credit=0,files=files),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest())))

if __name__=='__main__':main()
