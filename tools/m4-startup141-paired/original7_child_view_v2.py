"""Pure typed view of immutable original7 children, not a paired comparator.

The caller must authenticate each entire report/artifact before decoding rows.
This module performs no IO and does not compute or widen source claims.
"""
from pathlib import PureWindowsPath
import re

WORKSPACE = 'D:/Projects/MW34Recomp'
VALIDATION_SHA = 'e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c'
AGGREGATE_SHA = '44a46bd0fda7776578232af60e2d9f0188275660350a239eb8c8def4790d9334'
FAMILIES = {
 'constructor18': ('reports/m4-original141-source/source-r4-constructors', '8f910be42c5be26bf6e41260361b61b3ec258aefedf2cbdaabe35e3992498899', ((0x4103f0,13),(0x410440,14),(0x459b40,39)), ()),
 'formatter4': ('reports/m4-original141-source/source-r4-formatters', 'e00c61062f51b554d0cfa740b0d7cec53a2f50698c4fcf074c72574b7400478f', ((0x4df610,110),(0x4e0710,111),(0x4e0810,112),(0x4e1ca0,113)), ('source-derivations.json','finite-API-inputs.json')),
 'old4': ('reports/m4-original141-source/source-r4-old4', '205bd6b71b79719d9c6aaa410107ae16df9d74142c83a387e53273869fca2b17', ((0x411010,24),(0x4dc140,109),(0x500660,117),(0x5968f0,135)), ('original-prefixes.json','original-Lockit-boundaries.json','original-owned-source-relations.json','provider-observer-spans.json','original-source-access-ledgers.json','original-source-owned-contract-corroborations.json','original-source-publication-contract-corroborations.json')),
 'new_MFC': ('reports/m4-original141-source/source-r5-MFC', '820a0832b24cd0666b4011552d1c9127623429cc0b01cfcc33319e8b40211dd4', ((0x5ae3e4,15),), ('source-derivations.json',)),
 'widget': ('reports/m4-original141-source/source-r7-widgets', 'bfc217783dd1e5869f2b9b247fe509343a0c3edec26f53ff42cb0c605e1a1d5a', ((0x40e250,17),(0x40ef50,18),(0x40f000,19),(0x479590,50),(0x5a3c30,137),(0x5a3ff0,138),(0x5a66f0,139)), ('source-derivations.json','source-font-generations.json','source-font-cleanup-joins.json','literal-FPS-joins.json','typed-GDI-inputs.json','source-memory-boundary-joins.json')),
 'tree': ('reports/m4-original141-tree-source/source-r1', '8b1d45318dbb5c29d6381e293487019728560915ad351833abb39e54ecbf3d43', ((0x4b7f70,86),), ('original-Tree-source-derivations.json',)),
}

CLAIMS = {
 'constructor18': dict(CPU='Whole original GPR/EIP and source-defined EFLAGS; undefinedness retained per case', State='Explicitly not claimed', FX='Whole own FX512', ENV='Whole own ENV28', journal='Literal own constructor/provider operands and ordered source-computed observer stores; no direct observation of all PCs', memory='Whole own pages/backings, full own stack with ordered shadow/live-read checks; no whole TIB claim'),
 'formatter4': dict(CPU='Full literal prefix and typed cdecl/CP boundary CPU; full registration provider CPU explicitly outside scope', State='Not claimed', FX='Whole typed cdecl/CP boundary FX', ENV='Finite CP boundary ENV; no new whole root/paired ENV assertion', journal='Ordered literal source_PCs/source_accesses and finite typed API inputs', memory='Whole literal owned byteflows/nonstack/CRT pages plus separate derived registry suffix; no opaque provider stack equality'),
 'old4': dict(CPU='Literal prefix and six bounded Lockit CPU joins; no generic postRET or API volatile equality', State='Not claimed', FX='Own source boundary observations and family source proof; no new whole root assertion', ENV='Own typed boundary observations; no new whole root/paired assertion', journal='Original source access ledgers and affine owner/publication corroborations', memory='Whole own source-owned capacity byteflow and suffix carry; provider scratch stack equality explicitly false'),
 'new_MFC': dict(CPU='Whole source-derived root CPU40 and seven normal/four API joins', State='Source model State bytes retained; original State equality not claimed', FX='Whole source-derived root FX512', ENV='Whole raw root ENV28 conservation', journal='142-PC derived path/ordered source operands, not a new observed per-instruction trace', memory='Whole borrowed backings/nonstack source pages; whole stack/TIB/internal OS CS writes excluded'),
 'widget': dict(CPU='Typed source/GDI CPU/frame joins and complete registrar endpoint policy; no directly observed every virtual CALL PC', State='Not claimed', FX='894 whole own API FX512 conservation pairs', ENV='893 conservation pairs plus one original-only 14-byte metadata clear; native and paired projection explicitly unproven', journal='Literal source_PCs/source_accesses, FS/virtual/array/provider joins; unobserved PCs remain source-derived', memory='Whole nonstack/CRT/object/capacity endpoint joins; whole root stack false, dead API stack bytes proven unread before overwrite; manual font cleanup is not shutdown callback execution'),
 'tree': dict(CPU='Finite original API and CPU/FX/ENV/frame/CS boundary joins', State='Whole original State explicitly false', FX='Whole typed boundary FX', ENV='Whole typed boundary ENV; no new whole root/paired assertion', journal='Literal source accesses/FS/source-written frame bytes, with opaque bytes proved unused before overwrite', memory='Whole nonstack pages/owner backings; whole opaque provider stack explicitly false'),
}

def path(p):
 p=PureWindowsPath(p)
 assert p.is_absolute() and '..' not in p.parts
 return str(p).casefold()

def location(relative):
 return str(PureWindowsPath(WORKSPACE)/relative)

def sha(h):
 assert type(h)is str and re.fullmatch('[0-9a-f]{64}',h)
 return h

def build_view(aggregate_path, aggregate_sha, aggregate, packets, selected_order):
 """Packets contain already-authenticated report, artifact refs and decoded rows.

 For a large widget list the caller may stream rows while retaining immutable
 physical row indices; it must hash the entire source artifact, not its header.
 No returned case or claim is acceptance eligibility.
 """
 assert path(aggregate_path)==path(location('reports/m4-original141-source/source-r7/report.json')) and aggregate_sha==AGGREGATE_SHA
 assert aggregate['passed']is True and aggregate['reader_closed']is True
 assert aggregate['original_validation_sha256']==VALIDATION_SHA and aggregate['raw_export_report_sha256']==VALIDATION_SHA
 assert aggregate['candidate_AFTER_machine_seed']is False and aggregate['source_AFTER_seed']is False
 assert aggregate['whole_original_State_claim']is False and aggregate['full_original846_CPU_execution_claim']is False
 assert len(selected_order)==141 and len({r['entry']for r in selected_order})==141
 children=aggregate['children'];assert len(children)==6 and {c['domain']for c in children}==set(FAMILIES)
 assert set(packets)==set(FAMILIES)
 result=[];used_paths=set();used_hashes=set();artifact_domains={};artifact_hash_domains={};all_keys=set()
 for family,(folder,h,roots,leaves)in FAMILIES.items():
  child=next(c for c in children if c['domain']==family);p=packets[family];report=p['report']
  expected=location(folder+'/report.json');assert path(child['path'])==path(child['receipt'])==path(p['report_path'])==path(expected)
  assert child['sha256']==p['report_sha256']==h and aggregate['files'].get(str(PureWindowsPath(expected)))==h
  assert path(expected)not in used_paths and h not in used_hashes;used_paths.add(path(expected));used_hashes.add(h)
  assert report['passed']is True and report['source_AFTER_seed']is False and report['canonical_reader_opened']is False
  if family!='constructor18':assert report['original_validation_sha256']==VALIDATION_SHA and report['source_case_extent']==6*len(roots)
  else:assert report['whole_original_State_claim']is False and report['ordinary_reader_closed']is True
  if family=='widget':
   assert report['native_ENV_projection_proven']is False and report['paired_ENV_projection_proven']is False and report['source_shutdown_executed']is False and report['whole_source_root_stack_compared']is False
  if family=='tree':assert report['whole_original_State_claim']is False and report['whole_provider_stack_compared']is False
  for root,phase in roots:assert selected_order[phase]['entry']==root
  refs=p['artifacts'];assert set(refs)==set(leaves)
  for leaf,ref in refs.items():
   q=location(folder+'/'+leaf);assert path(ref['path'])==path(q) and report['files'].get(str(PureWindowsPath(q)))==sha(ref['sha256'])
   assert path(q)not in artifact_domains;artifact_domains[path(q)]=family
   assert ref['sha256']not in artifact_hash_domains or artifact_hash_domains[ref['sha256']]==family
   artifact_hash_domains[ref['sha256']]=family
  rows=p['rows'];assert type(rows)is list and len(rows)==6*len(roots)
  keys=set()
  for index,row in enumerate(rows):
   core=row['source']if family=='tree'else row
   sequence=row['sequence'];assert type(sequence)is int and 0<=sequence<6
   root=0x4b7f70 if family=='tree'else row['root'];phase=dict(roots)[root]
   assert type(root)is int and (family=='constructor18' or core['phase']==phase)
   assert core.get('branch','original')=='original' and row.get('branch','original')=='original'
   if family=='tree':
    q=location(folder+'-case-'+str(sequence)+'/report.json')
    assert core['sequence']==sequence and path(row['path'])==path(q) and report['files'].get(q)==sha(row['sha256'])
   key=(family,sequence,root);assert key not in all_keys and (sequence,root)not in keys;all_keys.add(key);keys.add((sequence,root))
   case_refs=[]
   if family=='constructor18':
    assert row['source_complete']is True and all(row[k]is True for k in('whole_GPR_EIP','defined_EFLAGS','whole_FX512','whole_ENV28')) and row['source_AFTER_seed']is False and row['original_State_equality_claim']is False
    assert row==report['cases'][index]
    for leaf in('input.json','source-derivation.json'):
     q=location(folder+'/original-'+str(sequence)+'-'+str(root)+'/'+leaf);assert q in report['files'];case_refs.append(dict(path=q,sha256=sha(report['files'][q])))
   result.append(dict(family=family,sequence=sequence,root=root,phase=phase,source_row_index=index,report_path=expected,report_sha256=h,artifact_references=refs,case_artifact_references=case_refs,available_claims=dict(CLAIMS[family]),source_case_binding_only=True,whole_original_State_claim=False,paired_claim=False,complete_acceptance_gate=False))
  assert keys=={(s,r)for s in range(6)for r,_ in roots}
 assert len(result)==120
 return dict(schema='mw34-original141-source7-typed-child-view-v1',cases=result,source_case_extent=120,unique_family_sequence_root_bindings=True,source_models_executed=False,source_outputs_modified=False,original_full846_CPU_claim=False,complete_paired141_gate=False,accepted_function_credit=0)


def load_authenticated_view(read_json, iter_authenticated_rows, selected_order):
 """Inject ROOT-admitted ordinary-only whole-hash readers, never raw exports.

 read_json(path, sha) must verify complete physical bytes before decoding.
 iter_authenticated_rows(path, sha) must verify the whole artifact, then stream
 the complete top-level array without model evaluation. The callbacks own
 admission and reader closure. This wrapper retains only typed selectors for
 large arrays, leaving source bytes unmodified at their immutable references.
 No callback is provided by default, and this function has no standalone main.
 """
 aggregate_path=location('reports/m4-original141-source/source-r7/report.json')
 aggregate=read_json(aggregate_path,AGGREGATE_SHA);packets={}
 for family,(folder,h,roots,leaves)in FAMILIES.items():
  report_path=location(folder+'/report.json');report=read_json(report_path,h)
  refs={leaf:dict(path=location(folder+'/'+leaf),sha256=sha(report['files'][location(folder+'/'+leaf)]))for leaf in leaves}
  if family=='constructor18':rows=report['cases']
  else:
   leaf={'old4':'original-prefixes.json','tree':'original-Tree-source-derivations.json'}.get(family,'source-derivations.json')
   ref=refs[leaf];rows=[]
   for row in iter_authenticated_rows(ref['path'],ref['sha256']):
    if family=='tree':
     source=row['source'];rows.append(dict(sequence=row['sequence'],path=row['path'],sha256=row['sha256'],source=dict(sequence=source['sequence'],phase=source['phase'],**({'branch':source['branch']}if'branch'in source else{}))))
    else:rows.append({k:row[k]for k in('sequence','root','phase')}|({'branch':row['branch']}if'branch'in row else{}))
   assert len(rows)==6*len(roots)
  packets[family]=dict(report_path=report_path,report_sha256=h,report=report,artifacts=refs,rows=rows)
 return build_view(aggregate_path,AGGREGATE_SHA,aggregate,packets,selected_order)
