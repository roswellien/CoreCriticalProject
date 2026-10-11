"""Finite six-root literal-source adapter from current genuine exports; no execution."""
from pathlib import Path
import copy,hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-font479590-original';T=Path(__file__).resolve().parent
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
def one(s,a,b):need(s.count(a)==1,'Exact adapter derivation '+a[:90]);return s.replace(a,b,1)
def main(name):
 out=B/name;need(not out.exists(),'Fresh source preparation');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact source input '+str(p));need(p.suffix!='.mwb','No capture archive');pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
 validation=read(B/'validation-r1/report.json','3b5e6b93cd4f6600c765666d9489bf28e821aa5269ec7c522e849a75a0e972a9');need(validation['passed']and validation['all_reader_aliases_closed'],'Current genuine six-root inputs')
 read(B/'preparation-r1/report.json','56dab048c049f8cf634c494ed894a8444bba8c50da0d4dc99c7a22cfeab50ab9')
 prior=read(R/'reports/m4-widget-source/original-source-r5/report.json','6af93443636136ce46aa021a4e056ce7eb767bd144c98429fdb1ddd4e8c0561c');need(prior['passed'],'Exact prior bounded widget source proof')
 c=copy.deepcopy(read(R/'reports/m4-widget-source/lift-preparation-r1/instruction-contracts.json','7e1095cb13aef3450991ef577b23de0b6daed874e85e02d2b375543b607e21e7'))
 worker=read(B/'preparation-r1/normal-contracts.json');known={v['pc']:v for v in c['instructions']};newrows=[]
 for row in worker['instructions']:
  if row['pc']not in known:newrows.append(row);known[row['pc']]=row
 need(len(newrows)==12 and sum(v['width']for v in newrows)==41,'Only exact physical newroot source')
 c['instructions']+=newrows
 registration=copy.deepcopy(worker['new_font_root']);registration.update(push_PC=0x4795c0,CALL_pc=0x4795c5,return_PC=0x4795ca)
 c['selected_roots'].append(dict(entry=0x479590,slot=0x5e00cc,object=0x608628,registration=registration,measured=False))
 binding=next(v for v in c['source_indirect_contracts']if v['CALL_pc']==0x5a0669)
 binding['object_role']+=' or current root479590 whole instance608628; no vector membership inferred'
 c.update(schema='mw34-font479590-literal-source-v1',source_prefix_only=True,source_registration_provider_executed=False,source_shutdown_executed=False,raw_game_initialization_or_AFTER_seed=False,real_fps_formatter40F000_admitted=False)
 out.mkdir(parents=True);cp=out/'source-contracts.json';cp.write_text(json.dumps(c,indent=2)+'\n');pin(cp)
 parent_model=pin(R/'tools/m4-widget-source/game_model.py','6e23a38d644028ada87dd81e75b65f09404cac4e28845d6d5b56abc36897e181')
 model=parent_model.read_text();model=one(model,"def contracts():return frozen('reports/m4-widget-source/lift-preparation-r1/instruction-contracts.json','7e1095cb13aef3450991ef577b23de0b6daed874e85e02d2b375543b607e21e7')", "def contracts():return frozen('"+cp.relative_to(R).as_posix()+"','"+sha(cp)+"')")
 # A model under reports/<namespace>/<preparation> resolves R at parents[3].
 model=one(model,'R=Path(__file__).resolve().parents[2]','R=Path(__file__).resolve().parents[3]');mp=out/'game_model.py';mp.write_text(model);pin(mp)
 parent_compare=pin(R/'tools/m4-widget-source/compare_original_v6.py')
 comp=parent_compare.read_text();comp=one(comp,"out=R/'reports/m4-widget-source'/name","out=R/'reports/m4-font479590-original'/name")
 comp=one(comp,"exports=R/'reports/m4-widget-source/original-inputs-r1';export=read(exports/'report.json','e45e403b85ced5cc0a9d7b5737c661a9c91b1d1bfa58aa65bda43592b8cb1af8')", "exports=R/'reports/m4-font479590-original/validation-r1';export=read(exports/'report.json','3b5e6b93cd4f6600c765666d9489bf28e821aa5269ec7c522e849a75a0e972a9')")
 comp=one(comp,"validation_path=R/'reports/m4-widget-original/validation-r1/report.json';validation=read(validation_path,'2cf3792eeecce837f141dd7d1347c634ddd6e14e275189e5f56e1ed737ec996c')", "validation_path=R/'reports/m4-font479590-original/validation-r1/report.json';validation=read(validation_path,'3b5e6b93cd4f6600c765666d9489bf28e821aa5269ec7c522e849a75a0e972a9')")
 comp=one(comp,"G=load(R/'tools/m4-widget-source/game_model.py','literal_widget_machine');", "source_prep=read(R/'"+(out/'report.json').relative_to(R).as_posix()+"');need(source_prep['passed'],'Finite newroot source adapter');G=load(R/'"+mp.relative_to(R).as_posix()+"','literal_widget_machine');")
 comp=one(comp,"counts['literal_widget_registration_prefixes']==5 and counts['finite_typed_actual_GDI_responses']==145 and counts['actual_literal_FS_PC_CPU_FX_ENV_frame_joins']==570", "counts['literal_widget_registration_prefixes']==6 and counts['finite_typed_actual_GDI_responses']==validation['counts']['actual_stdcall_RET_joins'] and counts['actual_literal_FS_PC_CPU_FX_ENV_frame_joins']==validation['counts']['actual_FS_instruction_observations']")
 comp=one(comp,"pin(__file__);pin(R/'tools/m4-widget-source/compare_original_v5.py');", "pin(__file__);pin(R/'tools/m4-font479590-original/prepare_source.py');pin(R/'tools/m4-widget-source/compare_original_v6.py','"+sha(parent_compare)+"');pin(R/'tools/m4-widget-source/compare_original_v5.py');")
 comp=comp.replace('Literal five-widget normal registration prefixes','Literal carried five-widget plus479590 normal registration prefixes')
 # Generated comparator is a tool in the two-level tools namespace.
 qp=T/'compare_source.py';need(not qp.exists(),'Fresh comparator source');qp.write_text(comp);pin(qp)
 pin(__file__);pin(R/'tools/m4-formatting-source/flag_domain.py');
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Exact additive six-root pure source and current genuine-input adapter only; no source execution yet',counts=dict(new_literal_rows=12,new_literal_bytes=41,roots=6),validation_sha256=sha(B/'validation-r1/report.json'),contracts_sha256=sha(cp),model_sha256=sha(mp),comparer_sha256=sha(qp),AFTER_machine_or_memory_seed=False,source_registration_provider_executed=False,real_fps_formatter40F000_admitted=False,initializer_credit=0,archive_reader_opened=False,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),comparer_sha256=sha(qp))))
if __name__=='__main__':main(sys.argv[1])
