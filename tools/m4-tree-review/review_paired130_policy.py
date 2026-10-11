"""Independent preparatory paired130 domains/count/source inventory review."""
from pathlib import Path
import json,hashlib,struct,sys,importlib.util
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];P={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix not in('.mwb','.zip');d=sha(p);assert h is None or d==h,(p,h,d);P[str(p)]=d;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
 receipt=read(R/'reports/m4-startup130-paired/preparation-r2/report.json','536e42689082903f2ff55201d1c262c66885393628f5cd291afc5354b8ceea97');assert receipt['passed']and not receipt['paired_executed']and not receipt['archive_reader_opened']
 for p,h in receipt['files'].items():pin(p,h)
 policy=read(receipt['policy'],receipt['policy_sha256']);original=read(R/'reports/m4-startup130-original/preparation-r2/report.json','8664d889eee0b3d65453205dd969d4bd377ae6bf6ff1dd0ca7185b002ccbd814')
 assert(policy['paired_sequences'],policy['paired_phases'],policy['original_phases'],policy['selected_roots'],policy['callback_roots'])==(12,1560,780,130,101)
 assert policy['record_ABI']==dict(original=356992,native=159716,CPU=40,FX=512,ENV=28,State=3504)
 assert policy['ordinary_nonstack_page_endpoints']==12*130*2*44==137280 and policy['separate_whole_loader_page_input_relations']==12*130*2==3120 and policy['whole45_nonstack_page_endpoints']==140400 and policy['whole46_source_page_endpoints']==143520
 roots=[r['entry']for r in original['selected_order']];assert roots[policy['tree_activation_phase']]==0x4b7f70 and policy['tree_activation_phase']==78 and roots[policy['cosine_phase']]==0x4b64f0 and policy['cosine_phase']==76
 assert policy['additional_whole_page_addresses']==[0x5cd000,0x5e3000,0x5e9000]and len(original['observed_pages'])==43
 fields=policy['format_fields'];assert[(f['root'],f['request'])for f in fields]==[(0x4df610,8),(0x4e0710,10),(0x4e0810,12),(0x4e1ca0,11)]and all(f['publication_pc']==0x4deabc and f['finite_suffix_hex']=='2e7a726400'for f in fields)
 assert(policy['paired_new_format_owners'],policy['paired_new_format_cdecl_lifetimes'],policy['paired_new_format_cdecl_boundary_relations'])==(48,144,288)
 assert(policy['paired_new_mixed_MFC_owners'],policy['paired_new_mixed_source_owned_writes'],policy['paired_new_mixed_publications'],policy['paired_new_mixed_bounded_API_relations'])==(36,120,36,24)
 assert len(policy['mixed_allocations'])==3 and len(policy['mixed_owned_accesses'])==10 and len(policy['mixed_publications'])==3 and len(policy['mixed_FS_frames'])==2 and len(policy['mixed_Lockit_scratch'])==2
 assert policy['paired_new_mixed_normal_FS_records']==48 # endpoint joins:12cases*2invocations*2install/restore boundaries
 for forbidden in('archive_reader_opened','opaque_page_mask','arbitrary_AF_mask','candidate_AFTER_seed','initializer_credit'):assert not policy[forbidden]
 for required in('strict_persistent_native130_source','full_native130_provider_lifecycle','current_loader_input_domain','current_final_linked_original_observers','independent_paired130_review'):assert required in policy['required_fresh_gates']
 loader=pin(R/'tools/analysis/pe.py');spec=importlib.util.spec_from_file_location('paired130_physical',loader);pe=importlib.util.module_from_spec(spec);spec.loader.exec_module(pe);game=pe.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 for row in original['selected_order']:off,_=game.rva_range(row['slot']-game.image_base,4);assert struct.unpack_from('<I',game.data,off)[0]==row['entry']
 iats=policy['exact_format_IAT_domains'];assert len(iats)==3 and {r['named_import']for r in iats}=={'strrchr','malloc','sprintf'}
 for row in iats:off,_=game.rva_range(row['cell']-game.image_base,4);assert struct.unpack_from('<I',game.data,off)[0]==row['native_physical_raw_pointer32']and row['whole_DWORD_identity_required']and row['original_compile_and_every_phase_identity_proven']
 current=read(R/'reports/m4-startup130-original/old-Lockit-source-r1/report.json','2019203ff6a2e1082ff60d37e69c66df45f3d96a5e35ef20d155139f4e2e32d7');assert current['passed']and current['original_validation_sha256']==receipt['original_validation_sha256']and current['reader_closed']
 for p,h in current['files'].items():
  if Path(p).suffix not in('.mwb','.zip'):pin(p,h)
 pin(__file__);target=out/'report.json';target.write_text(json.dumps(dict(passed=True,scope='Independent preparatory current130 paired finite typed domains, exact schedule/physical source IAT and refreshed original old4 source receipt review; fresh native source/provider and paired execution remain required',policy_sha256=receipt['policy_sha256'],original_validation_sha256=receipt['original_validation_sha256'],original_old4_source_sha256=receipt['original_old4_source_sha256'],selected_roots=130,callback_roots=101,tree_activation_phase=78,cosine_phase=76,whole_current_source_pages=46,ordinary_nonstack_page_endpoints=137280,separate_whole_loader_input_endpoints=3120,combined45_nonstack_page_endpoints=140400,mixed_source_frame_invocations=24,mixed_full12B_install_restore_relations=48,mixed_read_install_restore_events=72,physical_table_pairs=130,physical_named_format_IAT_DWORDs=3,archive_readers_opened=0,paired_executed=False,initializer_credit=0,files=P),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(target))))
if __name__=='__main__':main(sys.argv[1])
