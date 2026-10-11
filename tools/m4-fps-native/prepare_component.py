"""Prepare seven Runtime routes from current52 plus exact six formatter lifts."""
from pathlib import Path
import hashlib,importlib.util,json,re,shutil,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-fps-native'/name;need(not out.exists(),'Fresh FPS component');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact input '+str(p));pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 prior_path=R/'reports/m4-widget-native/preparation-r6/report.json';prior=read(prior_path,'714a5f0093a62e68911f78c93a07d34e4bd9f4b39e79e0931a4812bee6877ed9');need(prior['passed']and prior['literal_bodies']==52,'Exact successful52 component')
 execution=read(R/'reports/m4-widget-native/fixture-execution-r4/report.json','1b7f14c5b68f43df3389b9d6cddbbf9dd594c794b4420e002349188313a7a12c');need(execution['passed']and execution['all_workers_terminal'],'Closed positive both-level current component')
 old=read(prior_path.parent/'contracts.json',prior['files'][str((prior_path.parent/'contracts.json').resolve())]);extension_path=R/'reports/m4-fps-native/extension-preparation-r1/report.json';extension=read(extension_path,'0ec2a3114a83e4db8169b88b1ce217bdb0acd6627945e853b12ceafca47c99de');ext=read(extension_path.parent/'contracts.json',extension['files'][str((extension_path.parent/'contracts.json').resolve())]);reuse=read(extension_path.parent/'reused-literal-bodies.json');lift_path=R/'reports/m4-fps-native/lifts-r1/report.json';lift=read(lift_path,'e8cc860f4696f86c40fe52c43ce4fec93e407522ad5efd429da4c51f020786f9')
 actual_path=R/'reports/m4-fps-original/source-r3/report.json';actual=read(actual_path,'12a24d02ef22120d7798ae9c273866d76a2abd1089353127b22f9f8e6d57e154');observed=read(actual_path.parent/'source-derivations.json',actual['files'][str((actual_path.parent/'source-derivations.json').resolve())])[-1];need(observed['root']==ext['root']['entry']==0x40f000,'Exact actual seventh source route')
 model_path=pin(R/'reports/m4-fps-original/source-preparation-r4/game_model.py');spec=importlib.util.spec_from_file_location('FPS_current_program',model_path);model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model);program,callbacks=model.source_program()
 p=pin(R/'tools/analysis/pe.py');spec=importlib.util.spec_from_file_location('FPS_component_PE',p);pe=importlib.util.module_from_spec(spec);spec.loader.exec_module(pe)
 game_path=pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');crt_path=pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');game=pe.PEImage(game_path.read_bytes());crt=pe.PEImage(crt_path.read_bytes())
 rows={x['pc']:x for x in old['instructions']}
 for row in ext['instructions']+[program[p]for p in ext['literal_registration_tail_PCs']]:
  if row['pc']in rows:need(row==rows[row['pc']],'Whole shared source row unchanged')
  rows[row['pc']]=row
 physical=[]
 for pc,row in sorted(rows.items()):
  image=crt if pc>=0x78000000 else game;b=bytes.fromhex(row['bytes_hex']);offset,_=image.rva_range(pc-image.image_base,len(b));need(image.data[offset:offset+len(b)]==b,'Complete physical instruction source');physical.append(dict(PC=pc,file_offset=offset,bytes_hex=b.hex(),image=str(crt_path if pc>=0x78000000 else game_path)))
 root_frame=0x20001800;r=ext['root'];extra=dict(root=r['entry'],slot=r['slot'],object=r['object'],registration=r['registration'],GDI_calls=[],virtual_calls=ext['virtual_calls'],array_invocations=[],FS_operations=[dict(order=i,**x)for i,x in enumerate(ext['FS_operations'])],reached_PCs=ext['reached_PCs']+ext['literal_registration_tail_PCs'])
 for i,row in enumerate(observed['API_inputs']):
  need(row['API']in('GetStockObject','DeleteObject'),'Finite exact FPS GDI services');args=[dict(kind='literal_constant',value=10)]if row['API']=='GetStockObject'else[dict(kind='source_instance_live_handle',instance_root_offset=0,field_offset=600)]
  extra['GDI_calls'].append(dict(order=i,CALL_pc=row['source_CALL_pc'],service=row['API'],per_site_ordinal=0,instance_root_offset=0,frame_minus_root_frame=row['source_frame']-root_frame,argument_contract=args,return_pc=row['source_CALL_pc']+6))
 need(len(extra['GDI_calls'])==2 and len(extra['virtual_calls'])==6 and len(extra['FS_operations'])==9,'Finite current seventh source chronology')
 corrected=dict(ext);corrected['format_CALL']=dict(ext['format_CALL'],destination_role='Same current source instance + 0x34',destination_offset=0x34,frame_minus_root_frame=-140,va_minus_root_frame=-108,post_return_pointer_field_offset=0x238);need(program[0x5a2f63]['operands']=='edx, [esi + 0x34]'and program[0x5a2f6e]['operands']=='eax, dword ptr [esi + 0x238]','Physical destination versus later scalar source roles')
 roots=old['roots']+[extra];reached=sorted(set(old['reached_PCs'])|set(extra['reached_PCs']));contract=dict(old);contract.update(schema='mw34-widget-FPS-seven-source-contracts-v1',roots=roots,instructions=list(rows.values()),reached_PCs=reached,format_contract=corrected['format_CALL'],format_dispatches=ext['output_dispatches'],external_imports=old['external_imports']+[[0x5a2f68,0x5bb53c]],host_vsprintf_substitution=False)
 tail=dict(root=0x40f000,provider_return_PC=0x5ac124,source_PCs=ext['literal_registration_tail_PCs'],source_read_PC_and_frame_offsets=[[0x5ac127,-16,4,False],[0x5ac154,-8,4,False],[r['registration']['CALL_pc']+8,0,4,False]],value_oracle=False,observed_prefix_tail_extended_by_literal_physical_source=True);contract['registration_epilogues']=old['registration_epilogues']+[tail]
 operands=[]
 for phase in read(R/'reports/m4-font479590-original/source-r1/source-derivations.json'):
  operands.append([dict(pc=pc,role=1 if 0x20001000<=a<0x20002000 else 2 if a==0x7ffde000 else 0,offset=a-root_frame if 0x20001000<=a<0x20002000 else 0 if a==0x7ffde000 else a,width=width,writing=bool(writing))for pc,a,_value,width,writing in phase['source_accesses']]+[dict(pc=pc,role=1,offset=off,width=4,writing=False)for pc,off,_width,_wr in next(t for t in old['registration_epilogues']if t['root']==phase['root'])['source_read_PC_and_frame_offsets']])
 operands.append([dict(pc=x['PC'],role=x['address_role'],offset=x['offset'],width=x['width'],writing=x['writing'])for x in ext['causal_operands']]);need([len(x)for x in operands][-1]==360 and sum(map(len,operands))==25003,'Exact ordered source operand count without values')
 irs=[];origins=[];bridge_names=set();entries=[]
 for row in prior['namespace_relations']:
  p=pin(row['component_IR'],row['component_sha256']);q=out/p.name;shutil.copyfile(p,q);irs.append(str(q));origins.append(dict(row,component_IR=str(q)));entries.append(row['entry']);bridge_names|=set(re.findall(r'@(mw34_widget_game_[A-Za-z0-9_]+)',q.read_text()))
 for row in reuse+[dict(entry=int(k[2:],16),IR=str(lift_path.parent/(k+'-host.ll')),IR_sha256=v['host_sha256'])for k,v in lift['source_bodies'].items()]:
  p=pin(row['IR'],row['IR_sha256']);raw=p.read_text();text=raw.replace('mw34_onexit_game_','mw34_widget_game_');need(text.replace('mw34_widget_game_','mw34_onexit_game_')==raw,'Exact namespace-only fresh literal relation');q=out/f"f_{row['entry']:x}-host.ll";q.write_text(text);irs.append(str(q));entries.append(row['entry']);origins.append(dict(entry=row['entry'],original_IR=str(p),original_sha256=sha(p),component_IR=str(q),component_sha256=sha(q),change='Exact symbol-prefix substitution only'));bridge_names|=set(re.findall(r'@(mw34_widget_game_[A-Za-z0-9_]+)',text))
 need(len(entries)==len(set(entries))==58,'Successful52 plus four reused and two new exact bodies')
 h=['#pragma once','#include "component.hpp"','#include <array>','namespace mw34::m4_widget_native::literal {','struct Instruction {unsigned pc,size;bool call,ret;std::array<unsigned char,16>bytes;};','inline constexpr Instruction instructions[]{']
 for pc,row in sorted(rows.items()):
  b=bytes.fromhex(row['bytes_hex']);h.append('{%d,%d,%s,%s,{%s}},'%(pc,len(b),str(row['mnemonic']=='call').lower(),str(row['mnemonic'].startswith('ret')).lower(),','.join(map(str,b))))
 h+=['};','inline const Instruction*instruction(unsigned pc){for(auto&v:instructions)if(v.pc==pc)return &v;return nullptr;}','inline constexpr unsigned reached[]{'+','.join(map(str,reached))+'};','inline bool admitted(unsigned pc){for(auto v:reached)if(v==pc)return true;return false;}','inline constexpr unsigned char fps_format[]{'+','.join(str(v)for v in bytes.fromhex(corrected['format_CALL']['format_physical_16B']))+'};','struct Root {unsigned root,slot,object,callback,registration,GDI_begin,GDI_count,virtual_begin,virtual_count,FS_begin,FS_count,operand_begin,operand_count;};','struct Virtual {unsigned pc,instance_offset,store,vptr,slot,target;int frame_offset;};','struct GDI {unsigned pc,service,instance_offset,argc;int frame_offset;std::array<unsigned,14>values,kinds;};','struct FS {unsigned pc;bool writing;};','struct Array {unsigned root,site,base_offset,stride,count,ctor,dtor;};','inline constexpr Root roots[]{'];gi=vi=fi=oi=0
 for i,row in enumerate(roots):
  reg=row['registration'];h.append('{%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d},'%(row['root'],row['slot'],row['object'],reg['callback'],reg.get('CALL_pc',reg.get('registration_CALL_pc')),gi,len(row['GDI_calls']),vi,len(row['virtual_calls']),fi,len(row['FS_operations']),oi,len(operands[i])));gi+=len(row['GDI_calls']);vi+=len(row['virtual_calls']);fi+=len(row['FS_operations']);oi+=len(operands[i])
 h+=['};','inline constexpr Virtual virtuals[]{']
 for root in roots:
  for v in root['virtual_calls']:h.append('{%d,%d,%d,%d,%d,%d,%d},'%(v['CALL_pc'],v['instance_root_offset'],v['source_store_PC'],v['source_vptr'],v['readonly_slot'],v['target'],v['frame_minus_root_frame']))
 h+=['};','inline constexpr GDI GDIs[]{']
 for root in roots:
  for v in root['GDI_calls']:
   values=[];kinds=[]
   for a in v['argument_contract']:kinds.append({'literal_constant':0,'source_instance_live_handle':1,'source_guest_string':2}[a['kind']]);values.append(a.get('value',a.get('field_offset',a.get('address',0))))
   h.append('{%d,%d,%d,%d,%d,{%s},{%s}},'%(v['CALL_pc'],{'GetStockObject':0,'DeleteObject':1,'CreateFontA':2}[v['service']],v['instance_root_offset'],len(values),v['frame_minus_root_frame'],','.join(map(str,values)),','.join(map(str,kinds))))
 h+=['};','inline constexpr FS FSs[]{']
 for root in roots:
  for v in root['FS_operations']:h.append('{%d,%s},'%(v['PC'],str(bool(v['writing'])).lower()))
 h+=['};','inline constexpr Array arrays[]{']
 for v in old['source_array_contracts']:
  for root in v['roots']:h.append('{%d,%d,%d,%d,%d,%d,%d},'%(root,v['CALL_pc'],v['base_root_offset'],v['stride'],v['count'],v['constructor'],v['destructor']))
 h+=['};','struct Operand {unsigned pc,role;long long offset;unsigned width;bool writing;};','inline constexpr Operand operands[]{']
 for phase in operands:
  for x in phase:h.append('{%d,%d,%d,%d,%s},'%(x['pc'],x['role'],x['offset'],x['width'],str(x['writing']).lower()))
 h+=['};','using Body=void*(*)(State*,unsigned,void*);']+['extern "C" void*mw34_widget_game_f_%x_body(State*,unsigned,void*);'%e for e in entries]+['inline Body body(unsigned pc){switch(pc){']+['case %d:return mw34_widget_game_f_%x_body;'%(e,e)for e in entries]+['default:return nullptr;}}','}']
 (out/'literals.hpp').write_text('\n'.join(h)+'\n');bridges=[]
 for n in sorted(bridge_names):
  if '_direct_'in n:bridges.append('extern "C" void*%s(State*s,unsigned a,void*p){return mw34_widget_game_call(s,a,p);}'%n)
  elif n.endswith('_undefined_8'):bridges.append('extern "C" std::uint8_t %s(){return 0;}'%n)
 (out/'bridges.inc').write_text('\n'.join(bridges)+'\n')
 for dst,src in [('component.cpp',R/'tools/m4-fps-native/component_v1.cpp'),('component.hpp',R/'tools/m4-fps-native/component_v1.hpp'),('native_api.s',prior_path.parent/'native_api.s')]:shutil.copyfile(pin(src),out/dst)
 for dst,obj in [('contracts.json',contract),('corrected-FPS-contract.json',corrected),('physical-instruction-relations.json',physical),('causal-operands.json',operands)]:q=out/dst;q.write_text(json.dumps(obj,indent=2)+'\n')
 for q in out.iterdir():pin(q)
 for q in [__file__,R/'tools/m4-fps-native/derive_component.py',R/'tools/m4-fps-native/component-source-relations.json',R/'tools/m4-fps-native/build_component.py',R/'tools/m4-fps-native/build_component.ps1']:pin(q)
 report=dict(passed=True,scope='Seven-route reusable widget/FPS literal component and finite source contracts; compilation preparation only',root_count=7,roots=[x['root']for x in roots],literal_bodies=58,instructions=len(rows),reached_PCs=len(reached),GDI_calls=gi,virtual_calls=vi,FS_operations=fi,array_iterations=75,causal_operands=oi,IRs=irs,namespace_relations=origins,successful_prior_component_sha256=sha(prior_path),successful_prior_execution_sha256='1b7f14c5b68f43df3389b9d6cddbbf9dd594c794b4420e002349188313a7a12c',whole_prior_IRs_unchanged=52,added_body_entries=[x['entry']for x in origins[52:]],physical_destination_offset=0x34,physical_post_return_pointer_offset=0x238,formatter_frame_offset=-140,formatter_va_offset=-108,host_vsprintf_substitution=False,AFTER_State_or_memory_seed=False,original_handle_or_output_seed=False,native_executed=False,source_native_equivalence=False,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=True,counts=[7,58,len(rows),gi,vi,fi,oi])))
if __name__=='__main__':main(sys.argv[1])
