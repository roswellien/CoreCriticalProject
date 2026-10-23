"""Prepared finite old producer/composite bridge, never a success-only alias."""
SEMANTICS='88e0a18bc8b32fb70c3fd460c828c44127613662fd4467cf3385ae78b56861cb'
RAW='2a0086d81039912923fb6f9ed294ea851098ae7e5078fc96faf5f0c246b63035'
SEM_ROLE='9f2b37cb7412c845b49846b45533e4e5b94cd65323c09435acfcfc5c046aa4a9'
SCOPE_ROLE='9c79f74002c7b8630e699b4687fc987e7edfcd12d31f3ec53f9be5deae9fa6e3'
PREP='f413ea66cb259ecebf8bf76024113a0410fe5883304fa10af9a442b291c1b07e'
BUILD='e064098f58982c7c6115e43f0ebf14a39eb1ae68f4162225c48c10c70b2f1bf6'
LEGACY_PREP='8a322602c066931f5dd3ced2b9319f6907b0b01413828e2d72dd482c5ce09b2c'
LEGACY_BUILD='9a65633f858e7c06c5ca09a8191a41051321cf2848c1a25b4318bd4c61c08a9f'
COMPLETE7='4a88d2c69f550221f553267af1a2eb5a569ccb8c1c9d7cf1ed4be859c8616212'
def current8_legacy12_preparation(rows,gates,*,ROOT,read,has,typed_equal,need):
 prep=rows['controls_preparation'];need(set(prep)=={'passed','scope_identity','control_cases','underlying_current8_preparation','underlying_legacy12_preparation','old_registry_private_vectors_retry_claim','full_memory_permission_snapshot_claim','observation_limits','files'},'Exact actual generated composite preparation source schema')
 typed_equal(prep['scope_identity'],'current138_controls_preparation_composite_v1','Actual composite preparation domain');typed_equal(prep['control_cases'],12,'Separate complete legacy12 control extent')
 for flag in('old_registry_private_vectors_retry_claim','full_memory_permission_snapshot_claim'):typed_equal(prep[flag],False,'Preserved unsupported full-state claim '+flag)
 for flag in('old_registry_private_vectors_retry_claim','full_memory_permission_snapshot_claim','whole_hidden_Runtime_frames_or_permissions_claim'):typed_equal(prep['observation_limits'][flag],False,'Explicit finite source/serializer observation limit '+flag)
 actual=prep['underlying_current8_preparation'];legacy=prep['underlying_legacy12_preparation'];typed_equal(actual['sha256'],PREP,'Actual existing current8 source preparation');typed_equal(legacy['sha256'],LEGACY_PREP,'Distinct actual existing legacy12 source preparation');need(has(prep,ROOT/actual['path'],PREP)and has(prep,ROOT/legacy['path'],LEGACY_PREP),'Both producing preparations own exact scoped physical edges')
 typed_equal(gates['controls_build']['sha256'],BUILD,'Actual current8 compile identity');typed_equal(rows['controls_build']['preparation_sha256'],PREP,'Current8 build still consumes genuine current8 preparation');current=read(ROOT/actual['path'],PREP)
 for key,value in dict(control_modes=8,control_phase=135,completed_prefix_roots=135,source_owned_font_create_calls=15).items():typed_equal(current[key],value,'Actual fixed source schema '+key)
 old_build=rows['controls_prelaunch']['scoped_legacy_build'];typed_equal(old_build['sha256'],LEGACY_BUILD,'Actual distinct legacy12 build');need(has(prep,ROOT/old_build['path'],LEGACY_BUILD)and has(rows['controls_prelaunch'],ROOT/old_build['path'],LEGACY_BUILD),'Scoped exact legacy12 build source graph');old=read(ROOT/old_build['path'],LEGACY_BUILD);typed_equal(old['preparation_sha256'],LEGACY_PREP,'Actual legacy12 build consumes genuine legacy12 source')
def old_semantic_composite(rows,gates,*,ROOT,read,has,typed_equal,need):
 controls=rows['controls'];raw=rows['controls_full_raw'];typed_equal(controls['scope_identity'],'current138_terminal_legacy24_current16_controls_composite_v1','Actual measured old24/new16 composite domain');typed_equal(controls['initializer_credit'],0,'Composite integrity grants no initializer credit');typed_equal(gates['controls_full_raw']['sha256'],RAW,'Actual existing completed current16 raw evidence');typed_equal(raw['controls_verification_sha256'],SEMANTICS,'Raw retains actual executed checker4 semantic producer')
 old=ROOT/'reports/m4-joint-startup138/context-controls-verification-r1/report.json';need(has(raw,old,SEMANTICS)and has(rows['controls_gdi_owners'],old,SEMANTICS),'Actual raw and GDI owner evidence preserve exact old executed producer; never relabeled to composite')
 for key,value in dict(capture_archives_opened=0,worker_executed=False,source_machine_executed=False,whole_hidden_Runtime_frames_or_permissions_claim=False,whole_current138_positive_semantic_equivalence_claim=False,initializer_credit=0).items():typed_equal(raw[key],value,'Existing raw full-scope limit '+key)
 rawpath=ROOT/gates['controls_full_raw']['path'];need(has(controls,rawpath,RAW),'Actual composite physically owns existing raw16 receipt')
 s=ROOT/'reports/m4-controls-terminal-composite/root-current16-finite-review-r1/current16-semantic-review.json';p=ROOT/'reports/m4-controls-terminal-composite/root-current16-finite-review-r1/current8-scope-review.json';complete=ROOT/'reports/m4-controls-terminal-composite/root-complete7-physical-r1/report.json'
 need(has(controls,s,SEM_ROLE)and has(controls,p,SCOPE_ROLE)and has(controls,complete,COMPLETE7),'Actual separately ROOT-reviewed finite semantic/scope/legacy7 role graph');sem=read(s,SEM_ROLE);scope=read(p,SCOPE_ROLE)
 for row in(sem,scope):
  for key,value in dict(passed=True,preparation_sha256=PREP,build_sha256=BUILD,executed_semantic_sha256=SEMANTICS,committed_source_write_values_independently_instruction_evaluated=False,committed_write_values_from_actual_source_witness=True,whole_fault_memory_fully_source_predicted=False,source_callbacks_executed=False).items():typed_equal(row[key],value,'Exact finite current8 reviewed role '+key)
 typed_equal(sem['current16_fullraw_sha256'],RAW,'Actual finite review consumes completed raw');typed_equal(sem['execution_sha256'],gates['controls_execution']['sha256'],'Actual finite review consumes existing current8 workers');typed_equal(sem['all16_distinct_modes_reviewed'],True,'All16 actual modes');typed_equal(sem['finite_GDI_owner_manual_cleanup_lifetime_predicates_reviewed'],True,'Only finite named owner/manual generation predicates')
 need(has(sem,rawpath,RAW)and has(scope,rawpath,RAW),'Both finite roles physically retain actual raw identity')
 for key in('source_bootstrap_or_teardown_modeled','partial_fault_register_prediction','whole_hidden_Runtime_frames_or_permissions_claim','forwarder_origin_or_transitive_wrapper_body_claim','whole_current138_positive_semantic_equivalence_claim'):typed_equal(sem[key],False,'No broadened semantic claim '+key)
 for key in('manual_native_owned_cleanup_only','final_named_owner_entry64_only'):typed_equal(scope[key],True,'Explicit finite cleanup/owner scope '+key)
 # Fresh exact independent controls_review->new composite is STILL mandatory
 # in inherited semantic_checks. No old raw/owner receipt can impersonate it.
