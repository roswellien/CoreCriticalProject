"""Additive original138 MFC replay from ordinary sealed inputs, no archives."""
from pathlib import Path
import ast, hashlib, json, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
VALIDATION='74d444a5c9cfef4af293a0340af5bdfe6e6891d848b4ac16f9d1f8e562fa6181'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 parent=R/'tools/m4-startup131-original/compare_source_v2.py'
 receipt=R/'reports/m4-startup131-original/source-r2/report.json';accepted=json.loads(receipt.read_bytes())
 assert accepted['passed']and accepted['files'][str(parent)]==sha(parent)
 validation=R/'reports/m4-startup138-original/original-validation-r2/report.json';assert sha(validation)==VALIDATION
 v=json.loads(validation.read_bytes());assert v['passed']and v['reader_closed']and v['counts']['phases']==828
 original=parent.read_text();text=original;changes=[]
 def one(a,b,label):
  nonlocal text
  assert text.count(a)==1,label;text=text.replace(a,b,1);changes.append(dict(label=label,old=a,new=b))
 one("B=R/'reports/m4-startup131-original'","B=R/'reports/m4-startup138-original'",'Fresh138 output namespace')
 one("p=Path(p).resolve();v=sha(p);", "p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip','.mwi')and p.name not in('transport.json','manifest.json','bundle.json'),'Only ordinary sealed source inputs');v=sha(p);",'Enforce no canonical capture access')
 one("v['counts']['phases']==786","v['counts']['phases']==828 and v['record_bytes']==356992 and v['combined_pages']==69 and v['callbacks']==108 and v['original_executed'] and not v['native_executed'] and not v['state_seeded'] and not v['per_phase_reseed'] and not v['AFTER_machine_seed']",'Exact complete original138 input domain')
 one("v=read(validation,digest);", "need(digest=='"+VALIDATION+"','Exact current admitted original138 validation');v=read(validation,digest);",'Pin passed original138 validation')
 old="contracts=read(prep['contracts']);contract=dict(fixed_current_source_pages=prep['observed_pages'],external_source_pages=prep['extra_whole_source_pages']);need(len(contract['fixed_current_source_pages'])==43 and len(contract['external_source_pages'])==3,'Fixed original13146-page endpoint inventory')"
 new="contracts=read(prep['contracts']);need(len(prep['observed_pages'])==43 and len(prep['extra_whole_source_pages'])==26 and len(set(prep['observed_pages']+prep['extra_whole_source_pages']))==69,'Complete physically prepared original138 global page inventory');mfc_extra=[0x5cd000,0x5e3000,0x5e9000];need(set(mfc_extra)<=set(prep['extra_whole_source_pages']),'All inherited MFC semantic pages retained');pin(R/'tools/m4-startup131-original/mfc_phase_v3.py');contract=dict(fixed_current_source_pages=prep['observed_pages'],external_source_pages=mfc_extra);need(len(contract['fixed_current_source_pages'])==43 and len(contract['external_source_pages'])==3,'Unchanged MFC46 semantic pages plus complete actual MFC/CRT module extents; other138 pages remain separate')"
 one(old,new,'Retain exact exported MFC46 semantic domain while authenticate global69 inventory')
 one("scope='Current genuine full131 six-domain MFC phase13 literal replay", "scope='Current genuine full138 six-domain MFC phase13 literal replay",'Current report scope')
 one("pin(R/'tools/m4-startup131-original/prepare_source.py');pin(__file__);", "pin(R/'tools/m4-startup131-original/prepare_source.py');pin(R/'tools/m4-startup131-original/compare_source_v2.py');pin(R/'tools/m4-startup138-original/prepare_mfc_source.py');pin(__file__);",'Preserve additive generator/source lineage')
 reverse=text
 for d in reversed(changes):
  assert reverse.count(d['new'])==1;reverse=reverse.replace(d['new'],d['old'],1)
 assert reverse==original;ast.parse(text)
 target=Path(__file__).with_name('compare_mfc_source.py');assert not target.exists();target.write_text(text)
 out=R/'reports/m4-startup138-original/mfc-source-preparation-r1';assert not out.exists();out.mkdir()
 pins={str(p):sha(p)for p in(parent,receipt,validation,R/'tools/m4-startup131-original/mfc_phase_v3.py',Path(__file__).resolve(),target)}
 report=dict(passed=True,scope='Additive bounded ordinary-export original138 MFC source adapter preparation',parent_accepted_source_report=str(receipt),entrypoint=str(target),original_validation_sha256=VALIDATION,changes=changes,exact_inverse_restores_parent=True,
  semantic_domain='Unchanged fixed43 and three exported MFC extras plus whole actual module/backing inputs; additional widget/global69 semantics remain separate',archive_reader_opened=False,source_machine_executed=False,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),source=str(target))))
if __name__=='__main__':main()
