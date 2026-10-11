"""Freeze exact additional paired domains without opening either capture."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-startup130-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()!='.mwb';v=sha(p);assert h is None or h==v;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 original_path=R/'reports/m4-startup130-original/validation-r2/report.json';original=read(original_path,'91a3ca940214636b0d4c1a08c7ccf503a5c06127a3af4b26fdad50c876f1ffca');assert original['passed']and original['reader_closed']
 prep=read(Path(original['preparation_path'])/'report.json',original['preparation_sha256']);assert len(prep['selected_order'])==130 and len(prep['observed_pages'])==43 and prep['extra_whole_source_pages']==[0x5cd000,0x5e3000,0x5e9000]
 old4_path=R/'reports/m4-startup130-original/old-Lockit-source-r1/report.json';old4=read(old4_path,'2019203ff6a2e1082ff60d37e69c66df45f3d96a5e35ef20d155139f4e2e32d7');assert old4['passed']and old4['original_validation_sha256']==sha(original_path)
 mixed_path=R/'reports/m4-mixed-format-original/native-interface-r1/report.json';mixed_gate=read(mixed_path,'1513911ec682032f5ec844aae2010d39c435e545ed60f8b2946cfaae1df0e4ee');mixed=read(mixed_path.parent/'contracts.json',mixed_gate['files'][str((mixed_path.parent/'contracts.json').resolve())])
 normal_path=R/'reports/m4-formatting-source/normal-contracts-r1/report.json';normal_gate=read(normal_path,'ce23d46d409b1e5895788c677e0b97f33cce439634c78eef47af77a571e6e773');normal=read(normal_gate['contracts'],normal_gate['contracts_sha256'])
 iat_path=original_path.parent/'format-IAT-relations.json';iats=read(iat_path,original['files'][str(iat_path.resolve())]);targets={}
 for x in iats:
  assert x['actual_before']==x['actual_after']==x['declared_entry_target'];a=x['cell'];targets.setdefault(a,x['declared_entry_target']);assert targets[a]==x['declared_entry_target']
 assert len(iats)==2340 and set(targets)=={0x5bb5a8,0x5bb664,0x5bb658}
 finite_iat=[]
 for x in mixed['owning_IAT_rows']:
  if x['cell']not in targets:continue
  finite_iat.append(dict(cell=x['cell'],source_read_pc=x['source_pc'],actual_original_compiled_observer_target=targets[x['cell']],native_physical_raw_pointer32=x['raw_file_pointer32'],named_source_target32=x['named_loaded_pointer32'],named_import=x['name'],original_compile_and_every_phase_identity_proven=True,whole_DWORD_identity_required=True))
 assert len(finite_iat)==3
 format_fields=[dict(root=x['entry'],publication_pc=0x4deabc,address=x['owned_pointer_field'],request=x['statically_derived_default_request'],source_filename=x['filename'],finite_suffix_hex='2e7a726400',source_root_contract=x)for x in normal['roots']]
 format_fields.append(dict(root=0x4e1ca0,publication_pc=0x4deabc,address=mixed['entry_to_object']['format_owned_pointer_field'],request=mixed['source_format_domain']['normal_request'],source_filename=mixed['entry_to_object']['filename'],finite_suffix_hex='2e7a726400',source_root_contract=mixed['source_format_domain']))
 assert len(format_fields)==4 and [x['request']for x in format_fields]==[8,10,12,11]
 tree_phase=next(i for i,x in enumerate(prep['selected_order'])if x['entry']==0x4b7f70);cosine_phase=next(i for i,x in enumerate(prep['selected_order'])if x['entry']==0x4b64f0);assert cosine_phase<tree_phase
 pins_to_retain=['tools/m4-tree-paired/paired_v4.py','tools/m4-tree-paired/tree_relations_v2.py','tools/m4-startup130-original/family_phase_v2.py','tools/m4-startup130-original/old4_source.py']
 for p in pins_to_retain:pin(R/p)
 policy=dict(schema='mw34-paired130-current-source-domains-v1',paired_phases=1560,paired_sequences=12,original_phases=780,selected_roots=130,callback_roots=101,fixed_record_pages=43,additional_whole_page_addresses=prep['extra_whole_source_pages'],total_source_pages=46,
  ordinary_nonstack_pages=44,ordinary_nonstack_page_endpoints=137280,separate_whole_loader_page_input_relations=3120,whole45_nonstack_page_endpoints=140400,whole46_source_page_endpoints=143520,
  record_ABI=dict(original=356992,native=159716,CPU=40,FX=512,ENV=28,State=3504),tree_activation_phase=tree_phase,tree_activation_source='Actual current physical selected_order; no inherited constant77',cosine_phase=cosine_phase,
  exact_format_IAT_domains=finite_iat,format_fields=format_fields,mixed_allocations=mixed['MFC_allocation_contracts'],mixed_owned_accesses=mixed['owned_access_contracts'],mixed_publications=mixed['publication_contracts'],mixed_FS_frames=mixed['FS_frame_contracts'],mixed_Lockit_scratch=mixed['Lockit_scratch_contracts'],
  paired_new_format_owners=48,paired_new_format_cdecl_lifetimes=144,paired_new_format_cdecl_boundary_relations=288,paired_new_mixed_MFC_owners=36,paired_new_mixed_source_owned_writes=120,paired_new_mixed_publications=36,paired_new_mixed_bounded_API_relations=24,paired_new_mixed_normal_FS_records=48,
  named_cdecl_scope='Actual original provider entry and captured entry+instruction-size return-patch boundary; full original cdecl frame/CPU/FX/ENV retained. Source RET cleanup is separately literal-derived; native source-defined cdecl CPU/cells and actual owner facts are derived without any original AFTER seed.',
  loaded_provider_scope='Current original and native complete independently admitted bootstrap pages. Preserve every measured difference byte/value, observer opcode span and exact2API/3format IAT DWORD identities. Fresh current input-domain receipt required; inherited71 difference bytes must not be assumed.',
  source_stack_scope='Complete persistent each-branch source stack is independently proven. Raw original/private API spill bytes are retained; no blanket cross-branch stack or volatile API equality.',
  owner_scope='Each branch starts with its own genuine complete allocator backing. Derive all ordered literal writes, typed same-role pointers/publications and untouched capacity tails; compare whole native mapped4096 expected/actual carry and original physical capacity backing.',
  cosine_scope='Three physical defaultF64 inputs and literal3FCOS/FSTP source semantics through six current CW/TOP sequences. Whole rawFP is related by the accepted strict primitive contract; no host cos or candidateAFTER expected seed.',
  required_fresh_gates=['actual_native130_execution','strict_persistent_native130_source','full_native130_provider_lifecycle','actual_original130_validation','current_original130_old4_source','current_original130_tree_source','current_original130_format4_source','current_loader_input_domain','current_final_linked_original_observers','independent_paired130_review'],
  archive_reader_opened=False,opaque_page_mask=False,arbitrary_AF_mask=False,candidate_AFTER_seed=False,initializer_credit=0)
 path=out/'policy.json';path.write_text(json.dumps(policy,indent=2)+'\n');pin(path);pin(__file__)
 report=dict(passed=True,scope='Prepared current130 exact domains and inventory only; no paired reader executed or initializer credit',policy=str(path),policy_sha256=sha(path),original_validation_sha256=sha(original_path),original_old4_source_sha256=sha(old4_path),files=pins,archive_reader_opened=False,paired_executed=False,initializer_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),tree_phase=tree_phase,cosine_phase=cosine_phase)))
if __name__=='__main__':main(sys.argv[1])
