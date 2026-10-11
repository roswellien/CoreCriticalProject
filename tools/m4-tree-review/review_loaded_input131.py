"""Fresh current131 whole-page relation, full source operands and typed APIs.

Derived from the frozen current130 bounded proof with actual current receipts;
the original current inherited aggregate is an explicit invocation input.
"""
from pathlib import Path
import ast
R=Path(__file__).resolve().parents[2]
prior=R/'tools/m4-tree-review/review_loaded_input130.py';s=prior.read_text()
changes=[('loaded-input130-preparation-r1','loaded-input131-preparation-r2'),('678e719aa7a9b9c51504fd1cfee8f76b0ae146f9c8b755d892ff70a25d12f4e7','88aa9f5cede4176128903e0d98e871ce2cc4ede03304e0cde30fd72712561f1f'),('m4-joint-startup130-root/execution-r2','m4-joint-startup131-root/execution-r1'),('57914d2bde4290be5328409844cdfd221a97420b314f18fec7fdc6b565e29ec1','e250499a23537e21a206989f1dc9f1db2e40faae57840daa3b7cd4bb8d3a7a57'),('m4-joint-startup130/preparation-r2','m4-joint-startup131/preparation-r1'),('m4-joint-startup130/build-r2','m4-joint-startup131/build-r1'),('current130','current131'),('original130/native19','original131/native19')]
for a,b in changes:s=s.replace(a,b)
s=s.replace('def main(name,source_path,source_sha):','def main(name,source_path,source_sha,combined_path,combined_sha):')
old="and jp['native_preparation_sha256']==sha(R/'reports/m4-formatting-native/preparation-r19/report.json')"
new="and Path(jp['native_library']).resolve()==(R/'reports/m4-formatting-native/preparation-r19/registry_library.cpp').resolve() and build['files'][str(Path(jp['native_library']).resolve())]==np['files'][str(Path(jp['native_library']).resolve())]"
assert s.count(old)==1;s=s.replace(old,new)
begin=s.index("  combined_path=R/'reports/m4-startup130-original/combined-source-r3/report.json'")
end=s.index('  original_ledgers=[]',begin)
s=s[:begin]+"""  combined_path=Path(combined_path).resolve();combined=read(combined_path,combined_sha);need(combined['passed']and combined['reader_closed']and not combined['candidate_AFTER_machine_seed']and combined['original_validation_sha256']==prep['original_validation_sha256'],'Current original131 whole own-BEFORE inherited literal proof')
  old_case=next(c for c in combined['cases']if c['kind']=='old4');old_path=Path(old_case['receipt']).resolve();old=read(old_path,old_case['sha256']);need(old['passed']and old['original_validation_sha256']==prep['original_validation_sha256'],'Exact fresh old4 child of current131 aggregate')
  mfc_case=next(c for c in combined['cases']if c['kind']=='new_MFC');mfc_path=Path(mfc_case['receipt']).resolve();mfc=read(mfc_path,mfc_case['sha256']);mfc_rows=output(mfc,mfc_path,'source-derivations.json');need(mfc['passed']and len(mfc_rows)==6,'All genuine current cached-MFC source inputs')
  for row in mfc_rows:
   need(len(row['source_accesses'])==113 and not row['source_AFTER_seed']and row['actual_prefix_carried_BEFORE'],'Exact new-MFC source operand scope from own carried BEFORE')
   need(not any(overlap(v[1],v[3],0x78145000,0x78147000)for v in row['source_accesses']),'No cached-MFC source operand consumes any loaded MSVCP RW/IAT byte')
   counts['original_cached_MFC_operand_disjointness_cases']+=1;counts['original_cached_MFC_operands_checked']+=len(row['source_accesses'])
  native_MFC=output(source,source_path,'MFC-source-derivations.json');need(len(native_MFC)==12,'All current native cached-MFC literal case ledgers retained')
  for row in native_MFC:
   operands=row['source_accesses'];need(len(operands)==113,'Whole current native cached-MFC operand sequence')
   need(not any(overlap(v[1],v[3],0x78145000,0x78147000)for v in operands),'No current native cached-MFC source operand touches loaded MSVCP RW/IAT')
   counts['native_cached_MFC_operand_disjointness_cases']+=1;counts['native_cached_MFC_operands_checked']+=len(operands)
"""+s[end:]
s=s.replace('pin(artifact);pin(__file__);passed=True','pin(artifact);pin(prior);pin(__file__);passed=True')
s=s.replace("original_validation_sha256=prep['original_validation_sha256']if'prep'in locals()else None,", "original_validation_sha256=prep['original_validation_sha256']if'prep'in locals()else None,original_combined_source_sha256=combined_sha,whole_original_MFC_source_operands_checked=counts['original_cached_MFC_operands_checked'],whole_native_MFC_source_operands_checked=counts['native_cached_MFC_operands_checked'],")
s=s.replace('main(sys.argv[1],sys.argv[2],sys.argv[3])','main(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])')
ast.parse(s)
exec(compile(s,str(prior),'exec'),globals())
