"""Adapt exact accepted130 comparisons to current131 raw equality exports."""
from pathlib import Path
import ast, hashlib, json
ROOT=Path(__file__).resolve().parents[2]

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    parent=ROOT/'tools/m4-startup130-paired/paired_v2.py'
    assert sha(parent)=='1f5eb70c706a3267c09af0c488977abe537c9d31ea295f529262a8f7ed026677'
    text=parent.read_text();hunks=[]
    def one(old,new):
        nonlocal text
        assert text.count(old)==1,old
        text=text.replace(old,new);hunks.append(dict(old=old,new=new))
    one('Bounded paired original/native130','Bounded paired original/native131')
    one(" p=Path(p).resolve();v=sha(p);", " p=Path(p).resolve();need(p.suffix.lower()!='.mwb','No archive opened by paired raw-export consumer');v=sha(p);")
    one("current130-paired-frozen-gates", "current131-paired-frozen-gates")
    old=" need(native_execution_sha=='57914d2bde4290be5328409844cdfd221a97420b314f18fec7fdc6b565e29ec1'and combined_sha=='2a12a3a3356c0009da916ddeaa2696431ec5131423fda9b4c9b880abaee90624'and original_source_sha=='2019203ff6a2e1082ff60d37e69c66df45f3d96a5e35ef20d155139f4e2e32d7','Exact current execution2/original3/old4 source identities')"
    new=""" need(native_execution_sha=='e250499a23537e21a206989f1dc9f1db2e40faae57840daa3b7cd4bb8d3a7a57'and combined_gate['original_validation_sha256']=='9f3dc23c2b4f4eb5375882bb143d09f7caeb233a1d08d7b57373c606361ba07f'and original_source_gate['original_validation_sha256']=='9f3dc23c2b4f4eb5375882bb143d09f7caeb233a1d08d7b57373c606361ba07f','Exact current131 execution/original/old4 source identities')
 need(combined_gate['raw_export_report_sha256']==native_source_sha,'Fresh inherited source uses exact current raw export producer')
 mfc_path,mfc_gate,mfc_sha=gate('original_new_MFC_source');need(mfc_sha=='203d63def625e83cab7b2bebb274747825e888f0a2bc3b5f1331a4560055e910','Exact current genuine six-domain MFC literal proof')
 pair_prep_path,pair_prep,pair_prep_sha=gate('comparer_preparation');pair_review_path,pair_review,pair_review_sha=gate('paired_preflight')
 need(pair_review['comparer_preparation_sha256']==pair_prep_sha,'Independent exact current comparer preflight')
 for path,digest in pair_prep['files'].items():pin(path,digest)"""
    one(old,new)
    one(" need(combined_review_sha=='8365b62801e51146ec68bfbe597971745919c8722f2e9c411325a775376af186' and combined_review_gate['original_combined_source_sha256']==combined_sha,'Current independent original combined source review')", " need(combined_review_gate['original_combined_source_sha256']==combined_sha,'Current independent original combined source review')")
    one("policy['paired_phases']==1560", "policy['paired_phases']==1572")
    one("Current frozen whole130 policy", "Current frozen whole131 policy")
    one(" for row in policy['exact_format_IAT_domains']:IATS[row['cell']]=(row['actual_original_compiled_observer_target'],row['native_physical_raw_pointer32'])", " for row in policy['exact_format_IAT_domains']:IATS[row['cell']]=(row['actual_original_compiled_observer_target'],row['native_physical_raw_pointer32'])\n for row in policy['exact_new_MFC_IAT_domains']:IATS[row['cell']]=(row['actual_original_named_target'],row['native_physical_raw_pointer32'])")
    one(" ori=None;native=None;format_pairs=[]", " ori=None;native=None;format_pairs=[];mfc_pairs=[]")
    one(" out=ROOT/'reports/m4-startup130-paired'/name", " out=ROOT/'reports/m4-startup131-paired'/name")
    one("ROOT/'reports/m4-startup130-original/validation-r2/report.json','91a3ca940214636b0d4c1a08c7ccf503a5c06127a3af4b26fdad50c876f1ffca'", "ROOT/'reports/m4-startup131-original/validation-r2/report.json','9f3dc23c2b4f4eb5375882bb143d09f7caeb233a1d08d7b57373c606361ba07f'")
    one("Strict persistent native130 source gate", "Strict persistent native131 source gate")
    one("execution['build_sha256']=='1a51ee4bbba62c9505eb1ffae7dee2538cc68297708119a1fa3485769a1cde53'", "execution['build_sha256']=='6381e7288fcea6ece0c2b8b4420d6daf4e5aaa616484b40498589b4f869fcca5'")
    one("Exact finalprep4/build1 actual native130 run", "Exact current131 prep1/build1 actual run")
    one("D=load('paired_direct',ROOT/'tools/m4-crt-allocation-root/run_v2.py')", "E=load('paired_raw_export',ROOT/'tools/m4-startup131-original/export_reader.py')")
    one("ROOT/'reports/m4-startup130-original/preparation-r2/report.json','8664d889eee0b3d65453205dd969d4bd377ae6bf6ff1dd0ca7185b002ccbd814'", "ROOT/'reports/m4-startup131-original/preparation-r4/report.json','1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb'")
    one("ori=D.DirectSet(Path(original_report['original_capture']),pin)", "ori=E.ExportReader(native_source_report,native_source_sha,'original',pin);equal(ori.path,Path(original_report['original_capture']).resolve(),'Current original raw export canonical identity')")
    one("ROOT/'reports/m4-startup130-original/build-r2/build.json','3326ce7b2d9e1724ba254a12c451ad0a6b30aca3b89ecc416324624c16158103'", "ROOT/'reports/m4-startup131-original/build-r3/build.json','f7a2b920c80f1d38f3d0880400ca651585086e3e263864f28efb49965e900f9d'")
    one("ROOT/'reports/m4-startup130-original/execution-r2/report.json','a22a14bc771d3ed237cee5a6b1cb65e8b0f32777787d93c7782a8abce5934c86'", "ROOT/'reports/m4-startup131-original/execution-r1/report.json','189e6c9e1cd3bfe910698984b8b97cdf68c2e61b3704f444ba69a187f888aac4'")
    one("full_original_gate['preparation_sha256']=='8664d889eee0b3d65453205dd969d4bd377ae6bf6ff1dd0ca7185b002ccbd814'and full_original_gate['build_sha256']=='3326ce7b2d9e1724ba254a12c451ad0a6b30aca3b89ecc416324624c16158103'", "full_original_gate['preparation_sha256']=='1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb'and full_original_gate['build_sha256']=='f7a2b920c80f1d38f3d0880400ca651585086e3e263864f28efb49965e900f9d'")
    old="sha(ROOT/'reports/m4-startup130-original/validation-r2/report.json')"
    assert text.count(old)==2
    text=text.replace(old,"sha(ROOT/'reports/m4-startup131-original/validation-r2/report.json')");hunks.append(dict(old=old,new="sha(ROOT/'reports/m4-startup131-original/validation-r2/report.json')",occurrences=2))
    one("Exact fresh current130 original input domain", "Exact fresh current131 original input domain")
    one("T=load('current130_tree_pair_relations',ROOT/'tools/m4-startup130-paired/tree_relations.py');FMT=load('current130_format_pair_relations',ROOT/'tools/m4-startup130-paired/format_relations_v2.py')", "T=load('current131_tree_pair_relations',ROOT/'tools/m4-startup131-paired/tree_relations.py');FMT=load('current131_format_pair_relations',ROOT/'tools/m4-startup131-paired/format_relations.py');MFC=load('current131_MFC_pair_relations',ROOT/'tools/m4-startup131-paired/mfc_relations.py')")
    one("Six current phase78 tree cases", "Six current phase79 tree cases")
    one("Every current full130 literal tree source case", "Every current full131 literal tree source case")
    one("  tree_pairs=[]", """  tree_pairs=[]
  original_MFC=source_artifact(mfc_path.parent,mfc_gate,'source-derivations.json');native_MFC=source_artifact(Path(native_source_report).parent,source_gate,'MFC-source-derivations.json')
  original_MFC_actual=source_artifact(Path(original_report['original_validation_path']).parent,original_report,'fresh-MFC-observations.json') if 'original_validation_path'in original_report else source_artifact(ROOT/'reports/m4-startup131-original/validation-r2',original_report,'fresh-MFC-observations.json')
  need(len(original_MFC)==len(original_MFC_actual)==6 and len(native_MFC)==12,'All current six genuine and twelve independent native MFC source cases')
  native_MFC_prep=json.loads(pin(ROOT/'reports/m4-joint-startup131/preparation-r1/report.json','2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25').read_bytes());MFC_inputs=native_MFC_prep['inputs']""")
    one("native=D.DirectSet(nr.parent/level/'transport.json',pin)", "native=E.ExportReader(native_source_report,native_source_sha,level,pin);equal(native.path,(nr.parent/level/'transport.json').resolve(),'Current native raw export canonical identity')")
    one("     if entry in FMT.ROOTS:", """     if entry==MFC.ROOT:
      source_original=next(r for r in original_MFC if r['sequence']==seq);source_native=next(r for r in native_MFC if r['sequence']==seq and r['level']==level);actual_original=next(r for r in original_MFC_actual if r['sequence']==seq)
      newcounts,newrow=MFC.compare(source_original,actual_original,source_native,MFC_inputs,ori,native,m.hardwarefx);counts.update(newcounts);mfc_pairs.append(newrow)
     if entry in FMT.ROOTS:""")
    one("progress='paired130 sequence complete'", "progress='paired131 sequence complete'")
    old="counts['paired130_sequences']"
    assert text.count(old)==2;text=text.replace(old,"counts['paired131_sequences']");hunks.append(dict(old=old,new="counts['paired131_sequences']",occurrences=2))
    one("counts['paired_phases']==1560", "counts['paired_phases']==1572")
    one("counts['whole_nonstack_page_relations']==137280", "counts['whole_nonstack_page_relations']==138336")
    one("counts['separate_whole_loader_page_input_relations']==3120", "counts['separate_whole_loader_page_input_relations']==3144")
    one("counts['whole45_nonstack_page_endpoint_relations']==140400", "counts['whole45_nonstack_page_endpoint_relations']==141480")
    one("len(provider_page_rows)==9360", "len(provider_page_rows)==9432")
    one("counts['whole_exact_loaded_input_endpoint_relations']==3120", "counts['whole_exact_loaded_input_endpoint_relations']==3144")
    one("Complete full130 paired coverage", "Complete full131 paired coverage")
    one("  pin(__file__);passed=True", """  need(len(mfc_pairs)==12 and counts['paired_MFC_source_PC_occurrences']==1704 and counts['paired_MFC_ordered_operand_relations']==1356 and counts['paired_MFC_normal_boundary_relations']==84 and counts['paired_MFC_named_API_lifetimes']==48 and counts['paired_MFC_whole_borrowed_role_byteflows']==60 and counts['paired_MFC_whole_borrowed_endpoint_pairs']==120 and counts['paired_MFC_source_FS_install_restore_relations']==24 and counts['paired_MFC_whole_region_endpoint_relations']==288 and counts['paired_MFC_whole_module_input_relations']==24,'Complete new MFC source/role/API/normal/FS/whole endpoint coverage')
  pin(__file__);passed=True""")
    one("('Formatting-paired-source-relations.json',format_pairs)", "('MFC-paired-source-relations.json',mfc_pairs),('Formatting-paired-source-relations.json',format_pairs)")
    one("Fresh whole selected130 paired initialization relation", "Fresh whole selected131 paired initialization relation")
    one("counts=dict(counts),reader_closed=True,configuration_path", "counts=dict(counts),reader_closed=True,capture_archive_opened=False,archive_sessions_opened=0,raw_export_source_report_sha256=native_source_sha,comparer_preparation_sha256=pair_prep_sha,comparer_preflight_sha256=pair_review_sha,original_new_MFC_source_sha256=mfc_sha,configuration_path")
    target=ROOT/'tools/m4-startup131-paired/paired.py';assert not target.exists();ast.parse(text);target.write_text(text)
    oldtree=ROOT/'tools/m4-startup130-paired/tree_relations.py';tree=oldtree.read_text();assert sha(oldtree)=='16ea7247d289006467188fab67c0c1ea101b1a1369785ca8bd7d9b71ccae275e'
    assert tree.count('TREE_PHASE = 78')==1;tree=tree.replace('TREE_PHASE = 78','TREE_PHASE = 79')
    newtree=target.with_name('tree_relations.py');assert not newtree.exists();ast.parse(tree);newtree.write_text(tree)
    oldfmt=ROOT/'tools/m4-startup130-paired/format_relations_v2.py';newfmt=target.with_name('format_relations.py');assert sha(oldfmt)=='709335f12eee2b44ccf996737898068a8faff6cc7ac3a25b9e97f60f25131d79' and not newfmt.exists();newfmt.write_bytes(oldfmt.read_bytes())
    helper=target.with_name('mfc_relations.py');ast.parse(helper.read_text())
    out=ROOT/'reports/m4-startup131-paired/comparer-preparation-r1';assert not out.exists();out.mkdir(parents=True)
    delta=out/'hunks.json';delta.write_text(json.dumps(dict(comparer=hunks,tree=dict(old='TREE_PHASE = 78',new='TREE_PHASE = 79'),format_helper_byte_identical=True),indent=2)+'\n')
    paths=[parent,target,oldtree,newtree,oldfmt,newfmt,helper,delta,Path(__file__),ROOT/'tools/m4-startup131-original/export_reader.py',ROOT/'reports/m4-startup131-paired/preparation-r1/report.json',ROOT/'reports/m4-startup131-original/inherited-source-preparation-r3/report.json',ROOT/'reports/m4-startup131-original/source-r2/report.json']
    report=dict(passed=True,scope='Additive current131 comparer code and finite helper preparation only; all original/native bytes remain equality targets and no archive opened',files={str(p.resolve()):sha(p)for p in paths},comparer=str(target.resolve()),comparer_sha256=sha(target),helper=str(helper.resolve()),helper_sha256=sha(helper),counts=dict(expected_paired_phases=1572,expected_sequences=12,expected_MFC_source_PCs=1704,expected_MFC_operands=1356),capture_reader_opened=False,paired_executed=False,initializer_credit=0)
    q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(q),comparer_sha256=sha(target),helper_sha256=sha(helper),hunks=len(hunks))))
if __name__=='__main__':main()
