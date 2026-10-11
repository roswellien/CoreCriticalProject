"""Additive independent bounded130 reviewer from the retained125 review."""
from pathlib import Path
import ast, hashlib, json
R=Path(__file__).resolve().parents[2]
old=R/'tools/m4-tree-review/review_paired125_v2.py'
new=R/'tools/m4-tree-review/review_paired130.py'
source=old.read_text();hunks=[]
def change(a,b):
 global source
 assert source.count(a)==1,(a[:160],source.count(a))
 source=source.replace(a,b);hunks.append(dict(old=a,new=b))
changes={
"reports/m4-joint-startup125-root/execution-r1/report.json':'e384b6271c43f2e2e8d5a88f1a09e0940c85f111f2455744ad45de30ba73d8a8":None,
}
for a,b in (
("m4-joint-startup125-root/execution-r1/report.json','e384b6271c43f2e2e8d5a88f1a09e0940c85f111f2455744ad45de30ba73d8a8", "m4-joint-startup130-root/execution-r2/report.json','57914d2bde4290be5328409844cdfd221a97420b314f18fec7fdc6b565e29ec1"),
("actual['build_sha256']=='cdb5b9ca08e4e66dae276fa783bc59b5944e8435113fe9bb65a73cc53f218165'", "actual['build_sha256']=='1a51ee4bbba62c9505eb1ffae7dee2538cc68297708119a1fa3485769a1cde53'"),
("reports/m4-tree-native/preparation-r5/report.json','9b6c7ab64a42dd67d26e73a7b4357063729085a808173b2818e704430386fef2", "reports/m4-formatting-native/preparation-r19/report.json','1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3"),
("reports/m4-tree-original/old-Lockit-source-r3/report.json','2ebc48e5f6dd213e77b33bea8dda79ef2cd4a46b9e48997f6f346cd4e01d6c2c", "reports/m4-startup130-original/old-Lockit-source-r1/report.json','2019203ff6a2e1082ff60d37e69c66df45f3d96a5e35ef20d155139f4e2e32d7"),
("reports/m4-tree-original/full-original-review-r3/report.json','a56d25c7b35ece5315f51f8690c713321495d237522b343430d7acdc40a84260", "reports/m4-tree-review/original130-prelaunch-r7/report.json','bca1a34d40016dc27aaa4003d73d8c6723cccfbbb194cc8d69c5e89101880127"),
("sha(ROOT/'reports/m4-tree-original/full-original-review-r3/report.json')", "sha(ROOT/'reports/m4-tree-review/original130-prelaunch-r7/report.json')"),
("ROOT/'tools/m4-tree-paired/paired_v4.py'", "ROOT/'tools/m4-startup130-paired/paired_v2.py'"),
("ROOT/'reports/m4-tree-original/old-Lockit-source-r3/provider-observer-spans.json'", "ROOT/'reports/m4-startup130-original/old-Lockit-source-r1/provider-observer-spans.json'"),
("ROOT/'reports/m4-tree-review/loaded-input-page-r2/report.json'", "ROOT/'reports/m4-tree-review/loaded-input130-r1/report.json'"),
("'1da680a0f5d1751af3c35e81d3008abbe769331676800c00176d2f4fe3ace4e5'", "'66f3b663b5c66da5d40e217fb40b2686c2b2c402dd3f2640f977db9a6d1f7ba4'"),
("len(pages)==9000", "len(pages)==9360"),
("range(125)for side", "range(130)for side"),
("'paired_phases':1500,'paired125_sequences':12", "'paired_phases':1560,'paired130_sequences':12"),
("'whole_nonstack_page_relations':123000,'separate_whole_loader_page_input_relations':3000,\n                          'whole42_nonstack_page_endpoint_relations':126000,'whole_exact_loaded_input_endpoint_relations':3000", "'whole_nonstack_page_relations':137280,'separate_whole_loader_page_input_relations':3120,\n                          'whole45_nonstack_page_endpoint_relations':140400,'whole_exact_loaded_input_endpoint_relations':3120"),
("helper_path=ROOT/'tools/m4-tree-paired/tree_relations_v2.py'", "helper_path=ROOT/'tools/m4-startup130-paired/tree_relations.py'"),
("ROOT/'reports/m4-joint-startup125/preparation-r4/report.json',\n                         '243b6f4c86dc2b966789e23faed4a10fe2efa62ba51f43e854fa843acde392e7'", "ROOT/'reports/m4-joint-startup130/preparation-r2/report.json',\n                         '060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c'"),
("treephase==77 and prior_calls==2", "treephase==78 and prior_calls==2"),
("len(raw)==34", "len(raw)==36"),
("counts['complete_paired_phases']=1500", "counts['complete_paired_phases']=1560"),
):change(a,b)
start=source.index("        original_tree_gate=read(ROOT/'reports/m4-tree-source/original125-source-r1/report.json',")
end=source.index("        native_path=source_report.parent/'Tree-source-derivations.json'",start)
change(source[start:end],'''        original_tree_gate=read(ROOT/'reports/m4-startup130-original/combined-source-r3/report.json',
                               '2a12a3a3356c0009da916ddeaa2696431ec5131423fda9b4c9b880abaee90624')
        original_tree_path=ROOT/'reports/m4-startup130-original/combined-source-r3/original-Tree-source-derivations.json'
        original_tree_rows=read(original_tree_path,original_tree_gate['files'][str(original_tree_path.resolve())])
        tree_original={r['sequence']:r['source']for r in original_tree_rows}
        need(len(tree_original)==6 and all(r['phase']==78 for r in original_tree_rows),'Exact six current original tree occurrences')
''')
marker="        artifact=out/'tree-seam-observations.json';artifact.write_text(json.dumps(relations,indent=2)+'\\n');pin(artifact)"
extra='''        preflight_path=ROOT/'reports/m4-tree-review/paired130-preflight-r3/report.json'
        preflight=read(preflight_path,'89b5afc0463f2d33bdb2d84d543ee7de1b94d6e08701f91bb76a0a88eb981499')
        need(preflight['passed']and preflight['paired_executed']is False,'Exact separate unexecuted helper preflight')
        configuration=read(report['configuration_path'],report['configuration_sha256'])
        for row in configuration.values():
            if isinstance(row,dict)and 'path'in row:
                gate=read(row['path'],row['sha256']);need(gate['passed'],'All current paired frozen prerequisite gates')
        # Replay the exact formatter/mixed helper over sealed source exports.
        # This synthesized mapping supplies only literal results for bounded
        # derivation review; actual backing equality remains source/paired-reader evidence.
        fmt_path=ROOT/'tools/m4-startup130-paired/format_relations_v2.py';pin(fmt_path,report['files'][str(fmt_path.resolve())])
        spec=importlib.util.spec_from_file_location('bounded130_format_helper',fmt_path)
        FMT=importlib.util.module_from_spec(spec);spec.loader.exec_module(FMT)
        ofpath=original_tree_path.parent/'original-Formatting-source-derivations.json'
        originals=read(ofpath,original_tree_gate['files'][str(ofpath.resolve())])
        nfpath=source_report.parent/'Formatting-source-derivations.json'
        natives_fmt=read(nfpath,source['files'][str(nfpath.resolve())])
        pairs=output('Formatting-paired-source-relations.json')
        need(len(originals)==24 and len(natives_fmt)==len(pairs)==48,'All four actual roots in each current O0/O2 case')
        class DerivedFormatMapping:
            def __init__(self,row):
                self.rows={o['generation']:o for o in [row['owner']]+row['mixed_owners']}
            def data(self,key):
                import re
                match=re.search(r'locale-allocation-(\\d+)-(initial|expected|owned-page)\\.bin$',key)
                need(match is not None,'Bounded derived mapping admits only exact owner backing names')
                o=self.rows[int(match[1])]
                return bytes.fromhex(o['initial'])if match[2]=='initial'else bytes.fromhex(o['source_final_hex'])+bytes(4096-o['extent'])
        format_totals=Counter()
        for row in natives_fmt:
            old=next(o for o in originals if(o['sequence'],o['root'])==(row['sequence'],row['root']))
            actual_pair=next(p for p in pairs if(p['level'],p['sequence'],p['root'])==(row['level'],row['sequence'],row['root']))
            fields,derived,pair=FMT.compare(old,row,DerivedFormatMapping(row),f"sequence-{row['sequence']}/selected/",set(int(a)for a in source['files']if False),None) if False else FMT.compare(old,row,DerivedFormatMapping(row),f"sequence-{row['sequence']}/selected/",set(preparation['observed_pages']),None)
            need(pair==actual_pair,'Independent bounded formatter/mixed own-capacity/cdecl/FS/API/static derivation equals exact actual paired export')
            format_totals.update(derived)
        expected_format=dict(paired_new_format_owners=48,paired_new_format_cdecl_lifetimes=144,paired_new_format_cdecl_boundary_relations=288,paired_new_format_publications=48,paired_new_mixed_MFC_owners=36,paired_new_mixed_source_owned_writes=120,paired_new_mixed_publications=36,paired_new_mixed_bounded_API_relations=24,paired_new_mixed_FS_install_restore12B_relations=48,paired_new_mixed_saved_byte_source_derivations=96)
        for key,value in format_totals.items():need(report['counts'][key]==value,'All current paired formatter/mixed counts independently rederived '+key)
        for key,value in expected_format.items():need(format_totals[key]==value,'Complete finite formatter/mixed coverage '+key)
        counts.update(format_totals)
        counts['paired_comparer_exact_preflight_bound']=1
        counts['paired_configuration_prerequisites']=sum(isinstance(v,dict)and'path'in v for v in configuration.values())
'''
# Use the exact final preparation whole page inventory, including the three added pages.
extra=extra.replace('set(int(a)for a in source[\'files\']if False),None) if False else FMT.compare(old,row,DerivedFormatMapping(row),f"sequence-{row[\'sequence\']}/selected/",set(preparation[\'observed_pages\']),None)', "set(preparation['observed_pages']),None)")
change(marker,extra+marker)
change("native_capture_archive_opened=False,original_capture_archive_opened=False,original_postRET_observed=False, bounded_mapping_adapter_is_capture=False,", "paired_report_sha256=sha(paired_report),native_source_sha256=sha(source_report),paired_preflight_sha256=sha(preflight_path),native_capture_archive_opened=False,original_capture_archive_opened=False,original_postRET_observed=False, bounded_mapping_adapter_is_capture=False,")
change("        pin(__file__);paired_report=", "        pin(__file__);pin(ROOT/'tools/m4-tree-review/review_paired125_v2.py');pin(ROOT/'tools/m4-tree-review/prepare_paired130_review.py');paired_report=")
ast.parse(source)
assert not new.exists();new.write_text(source)
out=R/'reports/m4-tree-review/paired130-review-preparation-r1';assert not out.exists();out.mkdir(parents=True)
(out/'hunks.json').write_text(json.dumps(hunks,indent=2)+'\n')
pins={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest()for p in(old,new,Path(__file__),out/'hunks.json')}
(out/'report.json').write_text(json.dumps(dict(passed=True,scope='Additive independent bounded paired130 review preparation only',exact_hunks=len(hunks),capture_reader_opened=False,files=pins),indent=2)+'\n')
print(json.dumps(dict(passed=True,tool=str(new),hunks=len(hunks))))
