"""Bounded ordinary-definition/inverse preflight; never invokes comparer/main."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 prep=pin(R/'reports/m4-startup138-paired/comparer-preparation-r5/report.json','53529d80eec7a4055aa2a21222a60a1cea6ebfc31008fb81ed46271453888685');gate=json.loads(prep.read_bytes());assert gate['passed']and gate['exact_inverse_restores_parent']and not gate['full_pair_invocation_ready'];source=pin(gate['comparer'],gate['comparer_sha256']).read_text();hunks=json.loads(pin(prep.parent/'hunks.json',gate['files'][str((prep.parent/'hunks.json').resolve())]).read_bytes());inverse=source
 for h in reversed(hunks):
  for position in h['positions']:
   assert inverse[position:position+len(h['new'])]==h['new'];inverse=inverse[:position]+h['old']+inverse[position+len(h['new']):]
 parent=pin(R/'tools/m4-startup131-paired/paired_v2.py','61c3d15dea49cfc712cee70e04c2132470a20dd094abe79ada4f7971a736cd43').read_text();assert inverse==parent
 marker='      # actual volatile outputs at SPI and its immediate caller input seam.';end='      for i,page in enumerate(PAGES):';assert parent[parent.index(marker):parent.index(end)]==source[source.index(marker):source.index("      if side=='after'and entry in WG.WIDGETS:")]
 tree=ast.parse(source);assert not any(isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='main'for s in tree.body if not isinstance(s,(ast.FunctionDef,ast.If))for n in ast.walk(s));tree.body=[s for s in tree.body if not isinstance(s,ast.If)];namespace={'__file__':gate['comparer'],'__name__':'bounded_definition_only'};exec(compile(tree,gate['comparer'],'exec'),namespace);assert namespace['ROOT']==R and callable(namespace['main'])
 policy=json.loads(pin(gate['policy_preparation'],gate['policy_preparation_sha256']).read_bytes());assert policy['selected_roots']==138 and policy['paired_phases']==1656 and policy['total_source_pages']==69 and not policy['parent_domain_arrays_are_unadmitted_current_placeholders'];assert len(policy['MFC_current_original_domains'])==6 and len(policy['exact_widget_FPS_IAT_domains'])==4 and len(policy['exact_format_IAT_domains'])==3;assert "pair_review['current138_complete_typed_domain_policy_reviewed']is True"in source and source.index("pair_review['current138_complete_typed_domain_policy_reviewed']is True")<source.index('E.ExportReader(')
 cr=json.loads(pin(policy['CRT_page_source_domains_path'],policy['CRT_page_source_domains_sha256']).read_bytes());assert len(cr)==12 and all(len(r['registry_fields'])==138 and not any(v['AFTER_page_bytes_used_as_input']for v in r['registry_fields'])for r in cr)
 cells=json.loads(pin(policy['CRT_physical_import_cells_path'],policy['CRT_physical_import_cells_sha256']).read_bytes());assert len(cells)==12 and {(r['level'],r['sequence'])for r in cells}=={(l,s)for l in('O0','O2')for s in range(6)} and policy['CRT_IAT_opaque_initial_difference_admission']is False
 ps=pin(R/'tools/m4-startup138-paired/crt_page_policy_v4.py','0d4797ccdf4d7adc5372893366a0e2d2bbd678ab65b8963769698d80c45d4cc8');pn={'__name__':'policy_definition_only'};exec(compile(ps.read_text(),str(ps),'exec'),pn);controls=[]
 for cellcase in cells:
  row=next(r for r in cr if r['level']==cellcase['level']and r['sequence']==cellcase['sequence']);ao={int(k):bytes.fromhex(v)for k,v in row['original_inputs'].items()};bo={int(k):bytes.fromhex(v)for k,v in row['native_inputs'].items()};physical=cellcase['physical_import_cells'];assert len(physical)==144 and len({v['offset']for v in physical})==144 and sum(v['observer_shim']for v in physical)==8
  for label in('missing-cell','duplicate-cell','raw-target','installed-target','shim-real-target'):
   wrong=[dict(v)for v in physical]
   if label=='missing-cell':wrong.pop()
   elif label=='duplicate-cell':wrong[-1]=dict(wrong[0])
   elif label=='raw-target':wrong[0]['native_raw_thunk']^=1
   elif label=='installed-target':wrong[0]['original_installed_target']^=1
   else:next(v for v in wrong if v['observer_shim'])['original_real_target']^=1
   try:
    instance=pn['Policy'](ao,bo,row['patches'],row['unused_input_offsets'],wrong,row['typed_CRT_loader_cells'])
    restored=bytearray(ao[0x7802e000])
    for v in physical:
     if v['observer_shim']:pn['struct'].pack_into('<I',restored,v['offset'],v['original_real_target'])
    instance.page(13,'before',0x7802e000,bytes(restored),bo[0x7802e000],[],[])
   except ValueError:controls.append(dict(level=row['level'],sequence=row['sequence'],name=label,refused=True))
   else:raise AssertionError(label)
  assert len(row['typed_CRT_loader_cells'])==1 and not set(range(0x8c,0x90))&set(row['unused_input_offsets'])
  for label in('missing-typed-loader','original-typed-loader','native-typed-loader'):
   typed=[dict(v)for v in row['typed_CRT_loader_cells']]
   if label=='missing-typed-loader':typed=[]
   elif label=='original-typed-loader':typed[0]['original_target']^=1
   else:typed[0]['native_target']^=1
   try:pn['Policy'](ao,bo,row['patches'],row['unused_input_offsets'],physical,typed)
   except ValueError:controls.append(dict(level=row['level'],sequence=row['sequence'],name=label,refused=True))
   else:raise AssertionError(label)
 assert len(controls)==96
 for path,h in gate['files'].items():pin(path,h)
 for path,h in policy['current_domain_receipts'].items():
  r=json.loads(pin(path,h).read_bytes());assert r['passed']
  # Every ordinary physical dependency is individually pinned. Archive manifest
  # identities are data inside receipts, never reopened by this preflight.
  for dependency,digest in r['files'].items():
   dp=Path(dependency)
   if dp.name=='transport.json'or dp.suffix.lower()in('.mwb','.mwi','.zip'):continue
   pin(dp,digest)
 pin(__file__);pin(sys.executable);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Self bounded definition/inverse and physical ordinary input preflight only; independent policy review remains required',comparer_preparation_sha256=sha(prep),all46_hunks_exactly_invert=True,first42_parent_hunks_retained=True,additional_four_bindings_exactly_invert=True,accepted131_CPU_FX_ENV_rules_byte_for_byte_retained=True,generated_main_not_invoked=True,definition_only_executed=True,current138_complete_typed_domain_policy_reviewed=False,independent_review=False,physical_import_negative_controls=controls,physical_import_cells=1728,archive_reader_opened=False,raw_export_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
