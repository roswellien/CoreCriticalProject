"""Prepare additive current130 comparator without opening either capture."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 old=R/'tools/m4-tree-paired/paired_v4.py';new=R/'tools/m4-startup130-paired/paired.py';assert not new.exists();s=old.read_text();hunks=[]
 def one(a,b):
  nonlocal s
  assert s.count(a)==1,a[:180];s=s.replace(a,b);hunks.append(dict(old=a,new=b))
 def replace(a,b):
  nonlocal s
  n=s.count(a);assert n,a[:180];s=s.replace(a,b);hunks.append(dict(old=a,new=b,occurrences=n))
 replace('paired original/native125','paired original/native130')
 one('IATS={','FIXED_PAGES=PAGES;PAGES=FIXED_PAGES+(0x5cd000,0x5e3000,0x5e9000)\nIATS={')
 one('def main(native_report,name,native_source_report,native_source_sha,original_source_report,original_source_sha,original_review_report,original_review_sha):',"""def close_reader(reader):
 if reader is not None:reader.close();reader.entries.clear();reader.bundles.clear()
def main(configuration,name):
 config_path=pin(configuration);config=json.loads(config_path.read_bytes());need(config['scope']=='current130-paired-frozen-gates','Exact configuration scope')
 def gate(name):
  row=config[name];path=pin(row['path'],row['sha256']);value=json.loads(path.read_bytes());need(value['passed'],'Passed exact configured gate '+name);return path,value,row['sha256']
 native_report,execution,native_execution_sha=gate('native_execution');native_source_report,source_gate,native_source_sha=gate('native_source');original_source_report,original_source_gate,original_source_sha=gate('original_old4_source');original_review_report,full_original_gate,original_review_sha=gate('original_compiled_review');combined_path,combined_gate,combined_sha=gate('original_combined_source');loaded_input_gate_path,loaded_input_gate,loaded_input_sha=gate('loaded_inputs');policy_path,policy_gate,policy_sha=gate('paired_policy')
 need(native_execution_sha=='57914d2bde4290be5328409844cdfd221a97420b314f18fec7fdc6b565e29ec1'and combined_sha=='2a12a3a3356c0009da916ddeaa2696431ec5131423fda9b4c9b880abaee90624'and original_source_sha=='2019203ff6a2e1082ff60d37e69c66df45f3d96a5e35ef20d155139f4e2e32d7','Exact current execution2/original3/old4 source identities')
 policy=json.loads(pin(policy_gate['policy'],policy_gate['policy_sha256']).read_bytes());need(policy['paired_phases']==1560 and policy['total_source_pages']==46,'Current frozen whole130 policy')
 for row in policy['exact_format_IAT_domains']:IATS[row['cell']]=(row['actual_original_compiled_observer_target'],row['native_physical_raw_pointer32'])
 ori=None;native=None;format_pairs=[]
""")
 one("out=ROOT/'reports/m4-tree-paired'/name", "out=ROOT/'reports/m4-startup130-paired'/name")
 one("ROOT/'reports/m4-tree-original/original125-validation-r1/report.json','5a7911dee3f77d504a5a28cf66de2be7cc0b159a15a4e81282368a24d3a45534'", "ROOT/'reports/m4-startup130-original/validation-r2/report.json','91a3ca940214636b0d4c1a08c7ccf503a5c06127a3af4b26fdad50c876f1ffca'")
 replace("cdb5b9ca08e4e66dae276fa783bc59b5944e8435113fe9bb65a73cc53f218165", "1a51ee4bbba62c9505eb1ffae7dee2538cc68297708119a1fa3485769a1cde53")
 one("roots={r['entry']:r['registration']['callback']for r in rootrows};stringrows", "roots={r['entry']:r['registration']['callback']for r in rootrows};roots.update({0x4df610:0x4df680,0x4e0710:0x4e07b0,0x4e0810:0x4e0850,0x4e1ca0:0x4e1ce0});stringrows")
 one("ROOT/'reports/m4-tree-original/original125-preparation-r1/report.json','6e55c14d0195d099f8a02a51dee250a4b3fb0d92832b7c0a6e08f307cbd9c5a1'", "ROOT/'reports/m4-startup130-original/preparation-r2/report.json','8664d889eee0b3d65453205dd969d4bd377ae6bf6ff1dd0ca7185b002ccbd814'")
 one('G.PAGES=PAGES;', 'G.PAGES=FIXED_PAGES;')
 one("ROOT/'reports/m4-tree-original/original125-build-r1/build.json','e25a97c26e9a23d54f8340c7c0908a891915865b9ccda044ae3793e244d5a585'", "ROOT/'reports/m4-startup130-original/build-r2/build.json','3326ce7b2d9e1724ba254a12c451ad0a6b30aca3b89ecc416324624c16158103'")
 one("ROOT/'reports/m4-tree-original/original125-execution-r1/report.json','1e327ed23d5276964fc67e70308ce80a60a7e34051960b02e9c30da67b9998ae'", "ROOT/'reports/m4-startup130-original/execution-r2/report.json','a22a14bc771d3ed237cee5a6b1cb65e8b0f32777787d93c7782a8abce5934c86'")
 one("need(full_original_gate['passed']and full_original_gate['original_validation_sha256']=='5a7911dee3f77d504a5a28cf66de2be7cc0b159a15a4e81282368a24d3a45534'", "need(full_original_gate['passed']and full_original_gate['preparation_sha256']=='8664d889eee0b3d65453205dd969d4bd377ae6bf6ff1dd0ca7185b002ccbd814'and full_original_gate['build_sha256']=='3326ce7b2d9e1724ba254a12c451ad0a6b30aca3b89ecc416324624c16158103'")
 a="""  loaded_input_gate_path=ROOT/'reports/m4-tree-review/loaded-input-page-r2/report.json'
  loaded_input_gate=json.loads(pin(loaded_input_gate_path,'1da680a0f5d1751af3c35e81d3008abbe769331676800c00176d2f4fe3ace4e5').read_bytes())
  need(loaded_input_gate['passed'] and loaded_input_gate['counts']==dict(whole_bootstrap_input_pages=2,explicit_loaded_input_difference_bytes=71,explicit_loaded_input_difference_DWORDs=25,native_literal_state2_operand_joins=408,original_literal_state2_operand_joins=204,native_API_disjoint_CS24_joins=408),'Exact independently reviewed finite loaded-input and disjoint source/API domain')
"""
 b="""  need(loaded_input_gate['passed']and loaded_input_gate['original_validation_sha256']==sha(ROOT/'reports/m4-startup130-original/validation-r2/report.json'),'Exact fresh current130 original input domain')
  need(loaded_input_gate['native_execution_sha256']==native_execution_sha and loaded_input_gate['native_source_sha256']==native_source_sha,'Current actual native/source input-domain proof')
  need(loaded_input_gate['counts']['whole_bootstrap_input_pages']==2,'Both complete current provider inputs')
"""
 one(a,b)
 one("domain_path=loaded_input_gate_path.parent/'input-domain.json';loaded_input_domain=json.loads(pin(domain_path,loaded_input_gate['files'][str(domain_path.resolve())]).read_bytes())", "domain_path=Path(loaded_input_gate['input_domain_path']);loaded_input_domain=json.loads(pin(domain_path,loaded_input_gate['input_domain_sha256']).read_bytes())")
 replace('Complete actual71-byte input difference list','Complete current actual input difference list')
 one("T=load('current125_tree_pair_relations',ROOT/'tools/m4-tree-paired/tree_relations_v2.py')", "T=load('current130_tree_pair_relations',ROOT/'tools/m4-startup130-paired/tree_relations.py');FMT=load('current130_format_pair_relations',ROOT/'tools/m4-startup130-paired/format_relations.py')")
 a="""  original_tree_gate_path=ROOT/'reports/m4-tree-source/original125-source-r1/report.json'
  original_tree_gate=json.loads(pin(original_tree_gate_path,'884abbe43d69570265b2b8539d04455bdb622664d136b0055b8ab073a8735c5f').read_bytes());need(original_tree_gate['passed'],'All six genuine original tree source cases')
  original_trees={}
  for row in original_tree_gate['cases']:
   receipt=Path(row['receipt']);case=json.loads(pin(receipt,row['sha256']).read_bytes());need(case['passed'],'Passed own original tree case');original_trees[row['sequence']]=source_artifact(receipt.parent,case,'source-derivations.json')
"""
 b="""  need(combined_gate['original_validation_sha256']==sha(ROOT/'reports/m4-startup130-original/validation-r2/report.json')and combined_gate['reader_closed'],'Closed current original formatter4/tree source gate')
  original_trees={r['sequence']:r['source']for r in source_artifact(combined_path.parent,combined_gate,'original-Tree-source-derivations.json')};need(len(original_trees)==6,'Six current phase78 tree cases')
  original_formats=source_artifact(combined_path.parent,combined_gate,'original-Formatting-source-derivations.json');native_formats=source_artifact(Path(native_source_report).parent,source_gate,'Formatting-source-derivations.json');need(len(original_formats)==24 and len(native_formats)==48,'All current formatting4 source derivations')
  mixed_contract=json.loads(pin(ROOT/'reports/m4-mixed-format-original/native-interface-r1/contracts.json').read_bytes())
"""
 one(a,b)
 replace("len(mfc_records)==65,'65 exact", "len(mfc_records)==68,'68 exact")
 replace("len(native_Lockit)==34,'All34", "len(native_Lockit)==36,'All36")
 one("need(len(a)==356992 and len(b)==159716,'Fixed original/native record geometry')", "need(len(a)==356992 and len(b)==159716,'Fixed original/native record geometry')")if "need(len(a)==356992 and len(b)==159716,'Fixed original/native record geometry')"in s else None
 # Family field activation derives once from current independently proved
 # source data; endpoint carries stay exact for each whole page.
 one("header_predictions={};live_lockit_fields={}", "header_predictions={};live_family_fields={};live_lockit_fields={}")
 needle="     observation=dict(level=level,sequence=seq,phase=phase,entry=entry,"
 insertion="""     if entry in FMT.ROOTS:
      source_original=next(r for r in original_formats if r['sequence']==seq and r['root']==entry);source_native=next(r for r in native_formats if r['sequence']==seq and r['level']==level and r['root']==entry)
      newfields,newcounts,newrow=FMT.compare(source_original,source_native,native,stem,PAGES,mixed_contract);counts.update(newcounts);format_pairs.append(newrow)
      for address,(av,bv,pc)in newfields.items():live_family_fields[address]=(phase,av,bv,pc)
"""
 one(needle,insertion+needle)
 one("before_original=G.normalize_memory(a[2276:178404],0x1df20c);before_native=", "before_original=G.normalize_memory(a[2276:178404],0x1df20c);before_original.update({p:ori.data(f'phase/{seq}/{phase}/extra-before/{p}.bin')for p in PAGES[len(FIXED_PAGES):]});before_native=")
 one("for i,page in enumerate(PAGES):\n       original=a[mo+i*4096:mo+(i+1)*4096];actual=", "for i,page in enumerate(PAGES):\n       original=a[mo+i*4096:mo+(i+1)*4096]if i<len(FIXED_PAGES)else ori.data(f'phase/{seq}/{phase}/extra-{side}/{page}.bin');actual=")
 one("T.carry(tree_fields,phase,side,page,original,actual,declared,counts)", "T.carry(tree_fields,phase,side,page,original,actual,declared,counts);FMT.carry(live_family_fields,phase,side,page,original,actual,declared,counts)")
 replace("'<97I'", "'<101I'")
 replace('paired125_sequences','paired130_sequences');replace('paired125 sequence','paired130 sequence')
 replace('whole42_nonstack_page_endpoint_relations','whole45_nonstack_page_endpoint_relations')
 replace("counts['paired_phases']==1500", "counts['paired_phases']==1560")
 replace("counts['whole_nonstack_page_relations']==123000", "counts['whole_nonstack_page_relations']==137280")
 replace("counts['separate_whole_loader_page_input_relations']==3000", "counts['separate_whole_loader_page_input_relations']==3120")
 replace("counts['whole45_nonstack_page_endpoint_relations']==126000", "counts['whole45_nonstack_page_endpoint_relations']==140400")
 replace('len(provider_page_rows)==9000','len(provider_page_rows)==9360')
 replace("counts['whole_exact_loaded_input_endpoint_relations']==3000", "counts['whole_exact_loaded_input_endpoint_relations']==3120")
 one('  pin(__file__);passed=True',"""  need(counts['paired_new_format_owners']==48 and counts['paired_new_format_cdecl_lifetimes']==144 and counts['paired_new_format_cdecl_boundary_relations']==288 and counts['paired_new_mixed_MFC_owners']==36 and counts['paired_new_mixed_source_owned_writes']==120 and counts['paired_new_mixed_publications']==36 and counts['paired_new_mixed_bounded_API_relations']==24 and counts['paired_new_mixed_FS_install_restore12B_relations']==48,'Complete exact new family finite owner/cdecl/API/FS endpoint contracts')
  pin(__file__);passed=True""")
 one(' finally:\n  for label,value in', " finally:\n  close_reader(ori);close_reader(native)\n  for label,value in")
 one("(('Tree-paired-source-relations.json'", "(('Formatting-paired-source-relations.json',format_pairs),('Tree-paired-source-relations.json'")
 replace('Fresh whole selected125','Fresh whole selected130');replace('all43 page coverage via42','all46 page coverage via45')
 one('loaded_input_difference_bytes=71,loaded_input_difference_DWORDs=25', "loaded_input_difference_bytes=len(locals().get('loaded_input_differences',[])),loaded_input_difference_DWORDs=loaded_input_gate['counts']['explicit_loaded_input_difference_DWORDs']")
 one("counts=dict(counts),native_source_report_sha256=native_source_sha", "counts=dict(counts),reader_closed=True,configuration_path=str(config_path),configuration_sha256=sha(config_path),native_execution_sha256=native_execution_sha,original_combined_source_sha256=combined_sha,paired_policy_sha256=policy_sha,native_source_report_sha256=native_source_sha")
 one("if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],Path(sys.argv[5]).resolve(),sys.argv[6],Path(sys.argv[7]).resolve(),sys.argv[8])", "if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2])")
 replace('Every current full125','Every current full130');replace('Complete full125','Complete full130')
 replace('native125 source gate','native130 source gate');replace('actual native125 run','actual native130 run')
 ast.parse(s);new.write_text(s)
 tp=R/'tools/m4-tree-paired/tree_relations_v2.py';tn=new.with_name('tree_relations.py');assert not tn.exists();text=tp.read_text();assert text.count('TREE_PHASE = 77')==1;text=text.replace('TREE_PHASE = 77','TREE_PHASE = 78');ast.parse(text);tn.write_text(text)
 fp=new.with_name('format_relations.py');ast.parse(fp.read_text());out=R/'reports/m4-startup130-paired/comparer-preparation-r1';assert not out.exists();out.mkdir(parents=True);hp=out/'hunks.json';hp.write_text(json.dumps(hunks,indent=2)+'\n');paths=[old,new,tp,tn,fp,Path(__file__),hp,R/'reports/m4-startup130-paired/preparation-r2/report.json',R/'reports/m4-startup130-original/combined-source-r3/report.json'];report=dict(passed=True,scope='Prepared current130 whole46-page typed comparer. Runtime/static closure review pending; no archive opened and no new initializer credit.',required_configuration_rows=['native_execution','native_source','original_old4_source','original_compiled_review','original_combined_source','loaded_inputs','paired_policy'],files={str(p.resolve()):sha(p)for p in paths},capture_reader_opened=False,executed=False,initializer_credit=0);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(sha(p))
if __name__=='__main__':main()
