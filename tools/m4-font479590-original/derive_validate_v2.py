"""Add current font domain and complete input exports to the one-reader validator."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];D=Path(__file__).resolve().parent
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def one(s,a,b):
 if s.count(a)!=1:raise ValueError('Exact additive validator hunk '+a[:90])
 return s.replace(a,b,1)
def main():
 p=D/'validate.py';code=p.read_text();out=D/'validate_v2.py'
 if out.exists():raise ValueError('Fresh validator source required')
 code=one(code,'page_relations=[]','page_relations=[];input_index=[];font_domains=[];source_inputs=[]')
 code=one(code,"pin(__file__);pin(R/'tools/m4-font479590-original/derive_controllers.py');", "pin(__file__);pin(R/'tools/m4-font479590-original/derive_validate_v2.py');pin(R/'tools/m4-font479590-original/validate.py','"+sha(p)+"');pin(R/'tools/m4-font479590-original/derive_controllers.py');")
 a="   prior_pages=phase_pages['after']"
 b="""   prior_pages=phase_pages['after']
   actual_input_dir=out/'actual-inputs'/f'phase-{phase}';page_exports=[]
   for side in('before','after'):
    for page,value in phase_pages[side].items():
     q=actual_input_dir/side.upper()/f'{page}.bin';q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(value);pin(q);page_exports.append(dict(side=side.upper(),page=page,path=str(q),sha256=sha(q)))
   if root['root']==0x479590:
    need(phase==5 and words(phase_pages['before'][0x638000],0x4e8)==(0,),'Actual carried479590 BEFORE zero font registry; no seeded domain')
    object_before=phase_pages['before'][0x608000][0x628:0xad8];object_after=phase_pages['after'][0x608000][0x628:0xad8];need(len(object_before)==len(object_after)==0x4b0,'Complete current newroot object source extent')
    font_domains.append(dict(phase=phase,root=root['root'],object=0x608628,extent=0x4b0,font_registry_BEFORE=0,font_registry_AFTER=words(phase_pages['after'][0x638000],0x4e8)[0],object_BEFORE_hex=object_before.hex(),object_AFTER_observed_hex=object_after.hex(),source_after_seed=False,source_model_equivalence=False))
   source_inputs.append(dict(phase=phase,root=root['root'],CPU_BEFORE_hex=raw[36:76].hex(),FX_BEFORE_hex=raw[116:628].hex(),ENV_BEFORE_hex=raw[2164:2192].hex(),whole_source_BEFORE_pages=64,whole_source_AFTER_comparison_pages=64,page_exports=page_exports))"""
 code=one(code,a,b)
 a="counts['root_callback_endpoint_observations']+=1"
 b="""counts['root_callback_endpoint_observations']+=1
   observed_callbacks=words(raw,356480,(next_-begin)//4);source_callbacks=tuple(v['callback']for v in contract['roots'][:phase+1]);need(observed_callbacks==source_callbacks,'Exact source-derived one callback publication per carried initializer, original order')
   source_inputs[-1].update(registry_BEFORE_metadata=list(registry_before),registry_BEFORE_backing_hex=initial_registry.hex(),actual_registered_callbacks=list(observed_callbacks))
   if root['root']==0x479590:font_domains[-1].update(actual_registered_callback=observed_callbacks[-1],actual_initializer_CPU_BEFORE=list(before),actual_initializer_CPU_AFTER=list(after),actual_GDI_boundary_count=count,actual_FS_event_count=fcount)"""
 code=one(code,a,b)
 a="  need(counts['actual_root_phases']==6,'Complete actual six-root extent');passed=True"
 b="""  need(counts['actual_root_phases']==6 and len(font_domains)==1,'Complete actual six-root plus new current-instance domain extent')
  # Export immutable actual transport inputs in this same bounded reader. Whole
  # GDI snapshots already have exact independent raw exports above.
  for logical_name in sorted(capture.entries):
   if logical_name.endswith('widget-snapshots.bin'):continue
   relative=Path(logical_name);need(not relative.is_absolute()and'..'not in relative.parts,'Strict actual logical input name')
   q=out/'actual-capture'/relative;q.parent.mkdir(parents=True,exist_ok=True);value=capture.data(logical_name);q.write_bytes(value);pin(q);input_index.append(dict(logical_capture_name=logical_name,bytes=len(value),export_path=str(q.resolve()),sha256=sha(q)))
  counts['whole_current_source_BEFORE_export_pages']=64*len(source_inputs);counts['whole_current_source_AFTER_comparison_export_pages']=64*len(source_inputs);counts['complete_current_logical_capture_exports']=len(input_index)
  passed=True"""
 code=one(code,a,b)
 code=one(code,"('actual-whole-page-endpoints.json',page_relations)","('actual-whole-page-endpoints.json',page_relations),('actual-font479590-domain.json',font_domains),('whole-original-inputs.json',source_inputs),('logical-capture-export-index.json',input_index)")
 code=one(code,'reader_closed=True,files=PINS','reader_closed=True,all_reader_aliases_closed=True,current_font_domain_observed=True,whole_current_source_BEFORE_exported=True,whole_current_CRT_BEFORE_exported=True,files=PINS')
 out.write_text(code);print(json.dumps(dict(path=str(out),sha256=sha(out),parent_sha256=sha(p))))
if __name__=='__main__':main()
