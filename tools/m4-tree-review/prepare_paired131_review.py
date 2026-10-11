"""Carry every inherited bounded paired-review predicate into current131."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(name):
    out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True)
    p=R/'tools/m4-tree-review/review_paired130_v2.py';t=p.read_text();changes=[]
    def change(a,b,n=1):
        nonlocal t
        assert t.count(a)==n,(a,t.count(a));t=t.replace(a,b);changes.append(dict(before=a,after=b,count=n))
    change("report=read(paired_report);source=read(source_report)","report=read(paired_report);source=read(source_report);configuration=read(report['configuration_path'],report['configuration_sha256'])")
    change('reports/m4-joint-startup130-root/execution-r2/report.json','reports/m4-joint-startup131-root/execution-r1/report.json')
    change('57914d2bde4290be5328409844cdfd221a97420b314f18fec7fdc6b565e29ec1','e250499a23537e21a206989f1dc9f1db2e40faae57840daa3b7cd4bb8d3a7a57')
    change('1a51ee4bbba62c9505eb1ffae7dee2538cc68297708119a1fa3485769a1cde53','6381e7288fcea6ece0c2b8b4420d6daf4e5aaa616484b40498589b4f869fcca5')
    change("original=read(ROOT/'reports/m4-startup130-original/old-Lockit-source-r1/report.json','2019203ff6a2e1082ff60d37e69c66df45f3d96a5e35ef20d155139f4e2e32d7')","original=read(configuration['original_old4_source']['path'],configuration['original_old4_source']['sha256'])")
    change('reports/m4-tree-review/original130-prelaunch-r7/report.json','reports/m4-tree-review/original131-prelaunch-r4/report.json',2)
    change('bca1a34d40016dc27aaa4003d73d8c6723cccfbbb194cc8d69c5e89101880127','e5a09a7c7771c0c7f99cc907000ca999903e21b87d1342160684f237452608ed')
    change('tools/m4-startup130-paired/paired_v2.py','tools/m4-startup131-paired/paired_v2.py')
    change("patch_path=(ROOT/'reports/m4-startup130-original/old-Lockit-source-r1/provider-observer-spans.json').resolve()","patch_path=(Path(configuration['original_old4_source']['path']).parent/'provider-observer-spans.json').resolve()")
    change("input_gate_path=ROOT/'reports/m4-tree-review/loaded-input130-r1/report.json'","input_gate_path=Path(configuration['loaded_inputs']['path']).resolve()")
    change("read(input_gate_path,'66f3b663b5c66da5d40e217fb40b2686c2b2c402dd3f2640f977db9a6d1f7ba4')","read(input_gate_path,configuration['loaded_inputs']['sha256'])")
    change('len(pages)==9360','len(pages)==9432')
    change('range(130)','range(131)')
    change("'paired_phases':1560,'paired130_sequences':12","'paired_phases':1572,'paired131_sequences':12")
    change("'whole_nonstack_page_relations':137280,'separate_whole_loader_page_input_relations':3120,\n                          'whole45_nonstack_page_endpoint_relations':140400,'whole_exact_loaded_input_endpoint_relations':3120","'whole_nonstack_page_relations':138336,'separate_whole_loader_page_input_relations':3144,\n                          'whole45_nonstack_page_endpoint_relations':141480,'whole_exact_loaded_input_endpoint_relations':3144")
    change('tools/m4-startup130-paired/tree_relations.py','tools/m4-startup131-paired/tree_relations.py')
    change("original_tree_gate=read(ROOT/'reports/m4-startup130-original/combined-source-r3/report.json',\n                               '2a12a3a3356c0009da916ddeaa2696431ec5131423fda9b4c9b880abaee90624')","original_tree_gate=read(configuration['original_combined_source']['path'],configuration['original_combined_source']['sha256'])")
    change("original_tree_path=ROOT/'reports/m4-startup130-original/combined-source-r3/original-Tree-source-derivations.json'","original_tree_path=Path(configuration['original_combined_source']['path']).parent/'original-Tree-source-derivations.json'")
    change("r['phase']==78","r['phase']==79")
    change("preparation=read(ROOT/'reports/m4-joint-startup130/preparation-r2/report.json',\n                         '060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c')","preparation=read(ROOT/'reports/m4-joint-startup131/preparation-r1/report.json',\n                         '2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25')")
    change('treephase==78','treephase==79')
    change('reports/m4-tree-review/paired130-preflight-r3/report.json','reports/m4-tree-review/paired131-preparation-review-r2/report.json',2)
    change('89b5afc0463f2d33bdb2d84d543ee7de1b94d6e08701f91bb76a0a88eb981499','3c863aed6f6bed096b6ec9f7fa705f09f6fb7ce63b0f3b8de4fe48377c740f54')
    change('tools/m4-startup130-paired/format_relations_v2.py','tools/m4-startup131-paired/format_relations.py')
    change("original_prep=read(ROOT/'reports/m4-startup130-original/preparation-r2/report.json','8664d889eee0b3d65453205dd969d4bd377ae6bf6ff1dd0ca7185b002ccbd814')","original_prep=read(ROOT/'reports/m4-startup131-original/preparation-r4/report.json','1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb')")
    change("counts['complete_paired_phases']=1560","counts['complete_paired_phases']=1572")
    # Current MFC output was evaluated over the authenticated raw targets by
    # the independently preflighted finite helper. Preserve all whole outputs
    # and bind complete coverage alongside the inherited actual relations.
    marker="        counts['paired_comparer_exact_preflight_bound']=1"
    addition="""        mfc=output('MFC-paired-source-relations.json')
        need(len(mfc)==12 and {(row['level'],row['sequence'])for row in mfc}==cases,'Every current MFC branch pair retained')
        for row in mfc:
            need(row['root']==0x5ae3e4 and row['phase']==13 and len(row['operand_relations'])==113 and len(row['borrowed_roles'])==5 and len(row['normal_boundaries'])==7 and len(row['API_lifetimes'])==4 and len(row['native_whole_regions'])==12 and len(row['whole_module_input_relations'])==2,'All finite MFC full relation outputs')
            need(not row['original_postRET_observed']and not row['candidate_AFTER_machine_seed']and not row['original_API_held_CS24_observed'],'Exact MFC capture/source scope')
        for key,value in dict(paired_MFC_source_PC_occurrences=1704,paired_MFC_ordered_operand_relations=1356,paired_MFC_normal_boundary_relations=84,paired_MFC_named_API_lifetimes=48,paired_MFC_whole_borrowed_role_byteflows=60,paired_MFC_whole_borrowed_endpoint_pairs=120,paired_MFC_source_FS_install_restore_relations=24,paired_MFC_whole_region_endpoint_relations=288,paired_MFC_whole_module_input_relations=24).items():
            need(report['counts'][key]==value,'Every actual new MFC paired relation '+key);counts[key]=value
        for path,digest in preflight['files'].items():pin(path,digest)
"""
    change(marker,addition+marker)
    ast.parse(t);q=R/'tools/m4-tree-review/review_paired131.py';assert not q.exists();q.write_text(t)
    files={str(x.resolve()):hashlib.sha256(x.read_bytes()).hexdigest()for x in(p,q,Path(__file__))}
    r=dict(passed=True,scope='Unexecuted exact current131 bounded paired reviewer preserving all old actual API/FS/owner/page and tree/formatter source replay predicates; explicit current MFC coverage added under independent finite-helper preflight',changes=changes,files=files,capture_reader_opened=False,worker_executed=False,initializer_credit=0)
    f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256(f.read_bytes()).hexdigest())))
if __name__=='__main__':main(sys.argv[1])
