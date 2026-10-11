"""Fresh derivative of the accepted131 independent MFC causal-byteflow review."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
parent=R/'tools/m4-tree-review/review_original131_mfc_source.py'
text=parent.read_text();changes=[]
def change(a,z):
 global text
 assert text.count(a)==1,a
 changes.append(dict(before=a,after=z,occurrences=1));text=text.replace(a,z)
change("SOURCE=ROOT/'reports/m4-startup131-original/source-r2/report.json'","SOURCE=ROOT/'reports/m4-startup138-original/mfc-source-r1/report.json'")
change("SOURCE_SHA='203d63def625e83cab7b2bebb274747825e888f0a2bc3b5f1331a4560055e910'","SOURCE_SHA='e320179826dc0d0ab6033e98502eb5706186afa235222dd906d67c7d9605180f'")
change("VALIDATION_SHA='9f3dc23c2b4f4eb5375882bb143d09f7caeb233a1d08d7b57373c606361ba07f'","VALIDATION_SHA='74d444a5c9cfef4af293a0340af5bdfe6e6891d848b4ac16f9d1f8e562fa6181'")
change("ADMISSION_SHA='e5a09a7c7771c0c7f99cc907000ca999903e21b87d1342160684f237452608ed'","ADMISSION_SHA='efaa5d25802440f8cd47092d16a0368084cf5ea744d8c2cda5c826522f96122a'")
change("path=Path(path).resolve();need(path.suffix.lower()!='.mwb','Closed archive-reader audit')","path=Path(path).resolve();need(path.suffix.lower()not in('.mwb','.zip','.mwi')and path.name not in('index.json','payload.bin','transport.json','manifest.json','bundle.json')and path.stat().st_size<=32*1024*1024,'Only bounded ordinary sealed inputs; archive readers remain closed')")
change("out=ROOT/'reports/m4-tree-review'/name;","out=ROOT/'reports/m4-138-validation-review'/name;")
change("admission=read(ROOT/'reports/m4-tree-review/original131-prelaunch-r4/report.json',ADMISSION_SHA)","admission=read(ROOT/'reports/m4-tree-review/original138-prelaunch-r5/report.json',ADMISSION_SHA)\n        adapter=read(ROOT/'reports/m4-startup138-original/mfc-source-preparation-r1/report.json','bfe55dfebb2cbeb462b5180809da012a0062b6fddb685028398b84982c26e892');need(adapter['passed']and adapter['exact_inverse_restores_parent']and adapter['original_validation_sha256']==VALIDATION_SHA,'Current additive MFC source adapter lineage')\n        for path,identity in adapter['files'].items():pin(path,identity)\n        need(validation['counts']['phases']==828 and validation['combined_pages']==69 and validation['callbacks']==108 and validation['initializer_credit']==0 and not validation['native_executed'],'Current138 observation domain without credit')\n        need(len(preparation['observed_pages'])==43 and len(preparation['extra_whole_source_pages'])==26,'Complete global69 preparation geometry')\n        mfc_extras=(0x5cd000,0x5e3000,0x5e9000);need(set(mfc_extras)<=set(preparation['extra_whole_source_pages']),'All inherited MFC46 own-domain extras retained')")
change("for address in preparation['extra_whole_source_pages']:","for address in mfc_extras:")
change("        pin(__file__);pin(sys.executable)","        equal(counts['independent_whole_nonstack_page_byteflows'],2064,'Exact retained MFC46 plus full actual module endpoint byteflows')\n        equal(counts['whole_actual_root_CPU_FX_ENV_joins'],6,'All actual normal root endpoints')\n        equal(counts['actual_TIB_head_source_joins'],12,'All source-entry and source-return FS head joins')\n        pin(ROOT/'tools/m4-tree-review/review_original131_mfc_source.py');pin(ROOT/'tools/m4-138-validation-review/derive_mfc_source_review.py');pin(ROOT/'reports/m4-138-validation-review/mfc-source-review-preparation-r1/report.json');pin(__file__);pin(sys.executable)")
change("initializer_credit=0,source_derived_intermediate_control=True","initializer_credit=0,native_credit=0,semantic_page_domain=46,global_original138_page_domain=69,widget_global69_semantics_reviewed=False,source_derived_intermediate_control=True")
target=R/'tools/m4-138-validation-review/review_original138_mfc_source.py';assert not target.exists();target.write_text(text)
out=R/'reports/m4-138-validation-review/mfc-source-review-preparation-r1';assert not out.exists();out.mkdir(parents=True)
files={}
for p in(parent,target,Path(__file__).resolve()):files[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
delta=out/'deltas.json';delta.write_text(json.dumps(changes,indent=2)+'\n');files[str(delta)]=hashlib.sha256(delta.read_bytes()).hexdigest()
inverse=text
for row in reversed(changes):assert inverse.count(row['after'])==1;inverse=inverse.replace(row['after'],row['before'])
assert inverse==parent.read_text()
p=out/'report.json';p.write_text(json.dumps(dict(passed=True,scope='Fresh additive independent review adapter only, no source or archive execution',exact_inverse_restores_parent=True,adaptations=len(changes),retained_causal_byteflow_and_flag_and_root_FS_checks=True,semantic_domain=46,global_domain=69,initializer_credit=0,files=files),indent=2)+'\n')
print(json.dumps(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())))
