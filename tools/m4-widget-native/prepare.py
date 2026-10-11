"""Pure source/contract preparation. No original/native worker execution."""
from pathlib import Path
import hashlib,json,re,shutil,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def main():
 out=(R/sys.argv[1]).resolve();need(not out.exists(),'Fresh widget preparation');out.mkdir(parents=True)
 files={};origins=[]
 def bind(p,h=None):
  p=(R/p).resolve() if not Path(p).is_absolute() else Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact frozen input '+str(p));files[str(p)]=v;return p
 def load(p,h=None):return json.loads(bind(p,h).read_text())
 normal=load('reports/m4-widget-source/normal-contracts-r1/normal-contracts.json','475564050065c5216a64a71b93849a2d5a5187fdbcf9ba262df70fed85283481')
 prep=load('reports/m4-widget-source/lift-preparation-r1/report.json','b1778f7359075bae0c6c2afa0f5745b864b481f2e762dce64b385bb16c9a01dd')
 lifts=load('reports/m4-widget-source/lifts-r1/report.json')
 parent=load('reports/m4-formatting-native/preparation-r19/report.json','1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3')
 source=load('reports/m4-font479590-original/source-r1/report.json','7a5b070228618400a1a4524b4df4214226f12c2570bcff9775fc6416265c4e9b')
 font=load('reports/m4-font479590-original/source-r1/source-derivations.json',source['files'][str((R/'reports/m4-font479590-original/source-r1/source-derivations.json').resolve())])
 contracts=load('reports/m4-font479590-original/source-preparation-r1/source-contracts.json','97792d1f89cf5b66debbcf456bc5d4467cf0e685829de449ef421d18e37b0d2d')
 remaining=load('reports/m4-remaining-service-source/lifts-r2/report.json','b408ef417766435e082a436a2af6fbbcd3827fd1e30e6503d7d16fc7b1fb3c8e')
 roots=normal['roots'];six=contracts['selected_roots'][-1];last=font[-1];need(six['entry']==last['root']==0x479590,'Exact sixth font root')
 root_frame=0x20001800
 extra={'root':last['root'],'slot':six['slot'],'object':six['object'],'registration':six['registration'],'GDI_calls':[],'virtual_calls':[],'array_invocations':[],'FS_operations':[],'reached_PCs':sorted(set(last['source_PCs']))}
 for k,row in enumerate(last['API_inputs']):
  need(row['API'] in ('GetStockObject','DeleteObject'),'Only finite font GetStock/Delete')
  args=[{'kind':'literal_constant','value':10}]if row['API']=='GetStockObject' else[{'kind':'source_instance_live_handle','instance_root_offset':0,'field_offset':600}]
  extra['GDI_calls'].append({'order':k,'CALL_pc':row['source_CALL_pc'],'service':row['API'],'per_site_ordinal':0,'instance_root_offset':0,'frame_minus_root_frame':row['source_frame']-root_frame,'argument_contract':args,'return_pc':row['source_CALL_pc']+6})
 for k,row in enumerate(last['virtual_calls']):extra['virtual_calls'].append({'order':k,'CALL_pc':row['PC'],'instance_root_offset':row['instance']-six['object'],'source_store_PC':row['source_store']['PC'],'source_vptr':row['source_store']['value'],'readonly_slot':row['slot'],'target':row['target'],'frame_minus_root_frame':row['ESP']-root_frame})
 extra['FS_operations']=[{'order':k,'PC':v['PC'],'writing':v['writing']}for k,v in enumerate(last['FS_joins'])]
 roots=roots+[extra]
 instructions=contracts['instructions'];byPC={row['pc']:row for row in instructions};need(len(byPC)==1093,'1093 exact six-root physical rows')
 reached=sorted(set(pc for row in font for pc in row['source_PCs'])&set(byPC));need(len(reached)>677,'Six-root reached physical source domain')
 entries=sorted(set(prep['new_entries']+prep['reused_entries']+[0x479590,0x4795a0]));need(len(entries)==51,'51 literal bodies')
 irs=[];bridge_names=set()
 for entry in entries:
  key=f'f_{entry:x}'
  if key in lifts['source_bodies']:
   p=bind(f'reports/m4-widget-source/lifts-r1/{key}-host.ll',lifts['source_bodies'][key]['host_sha256'])
  elif entry in (0x479590,0x4795a0):
   p=bind(f'reports/m4-remaining-service-source/lifts-r2/{key}-host.ll',remaining['source_bodies'][key]['host_sha256'])
  else:
   candidates=[Path(k)for k in parent['entry_objects']if Path(k).name==key+'-O0.obj'];need(len(candidates)==1,'Unique accepted reused body '+key)
   obj=bind(candidates[0],parent['entry_objects'][str(candidates[0])]);p=bind(obj.with_name(key+'-host.ll'))
  raw=p.read_text();need('mw34_onexit_game_'+key+'_body' in raw,'Actual literal body symbol')
  transformed=raw.replace('mw34_onexit_game_','mw34_widget_game_');q=out/(key+'-host.ll');q.write_text(transformed)
  need(transformed.replace('mw34_widget_game_','mw34_onexit_game_')==raw,'Namespace-only literal IR relation')
  origins.append({'entry':entry,'original_IR':str(p),'original_sha256':sha(p),'component_IR':str(q),'component_sha256':sha(q),'change':'Exact symbol-prefix substitution only'})
  irs.append(str(q));bridge_names|=set(re.findall(r'@((?:mw34_widget_game_)[A-Za-z0-9_]+)',transformed));files[str(q)]=sha(q)
 # No observed API values, handles, State/FX or AFTER bytes enter these tables.
 derived={'schema':'mw34-widget-native-source-contracts-v1','roots':roots,'instructions':instructions,'reached_PCs':reached,'source_indirect_contracts':contracts['source_indirect_contracts'],'source_array_contracts':contracts['source_array_contracts'],'cold_PCs':[0x5ac24b,0x5a075b],'external_imports':[[0x517287,0x5bb064],[0x5ac11e,0x5bb52c],[0x5ac580,0x5bb530]],'GDI_imports':[[0x5a013c,0x5bb070],[0x5a063f,0x5bb074],[0x5a074b,0x5bb068]],'original_GDI_handle_seed':False,'AFTER_State_or_memory_seed':False,'source_callback_execution':False}
 (out/'contracts.json').write_text(json.dumps(derived,indent=2)+'\n')
 h=['#pragma once','#include "component.hpp"','#include <array>','namespace mw34::m4_widget_native::literal {','struct Instruction { unsigned pc,size; bool call,ret; std::array<unsigned char,16> bytes; };','inline constexpr Instruction instructions[]{']
 for row in instructions:
  b=bytes.fromhex(row['bytes_hex']);need(len(b)==row['width']<=16,'Whole physical instruction');h.append('{%d,%d,%s,%s,{%s}},'%(row['pc'],len(b),str(row['mnemonic']=='call').lower(),str(row['mnemonic'].startswith('ret')).lower(),','.join(str(x)for x in b)))
 h+=['};','inline const Instruction *instruction(unsigned pc){ for(auto &v:instructions)if(v.pc==pc)return &v;return nullptr; }','inline constexpr unsigned reached[]{'+','.join(str(x)for x in reached)+'};','inline bool admitted(unsigned pc){for(auto v:reached)if(v==pc)return true;return false;}']
 h+=['struct Root {unsigned root,slot,object,callback,registration;unsigned GDI_begin,GDI_count,virtual_begin,virtual_count,FS_begin,FS_count;};','struct Virtual {unsigned pc,instance_offset,store,vptr,slot,target;int frame_offset;};','struct GDI {unsigned pc,service,instance_offset,argc;int frame_offset;std::array<unsigned,14> values;std::array<unsigned,14> kinds;};','struct FS {unsigned pc;bool writing;};','struct Array {unsigned root,site,base_offset,stride,count,ctor,dtor;};','inline constexpr Root roots[]{']
 gi=vi=fi=0
 for row in roots:
  reg=row['registration'];h.append('{%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d},'%(row['root'],row['slot'],row['object'],reg['callback'],reg.get('CALL_pc',reg.get('registration_CALL_pc')),gi,len(row['GDI_calls']),vi,len(row['virtual_calls']),fi,len(row['FS_operations'])));gi+=len(row['GDI_calls']);vi+=len(row['virtual_calls']);fi+=len(row['FS_operations'])
 h+=['};','inline constexpr Virtual virtuals[]{']
 for root in roots:
  for v in root['virtual_calls']:h.append('{%d,%d,%d,%d,%d,%d,%d},'%(v['CALL_pc'],v['instance_root_offset'],v['source_store_PC'],v['source_vptr'],v['readonly_slot'],v['target'],v['frame_minus_root_frame']))
 h+=['};','inline constexpr GDI GDIs[]{']
 for root in roots:
  for v in root['GDI_calls']:
   values=[];kinds=[]
   for a in v['argument_contract']:
    kind=a['kind'];need(kind in ('literal_constant','source_instance_live_handle','source_guest_string'),'Typed source GDI argument kind '+kind)
    kinds.append({'literal_constant':0,'source_instance_live_handle':1,'source_guest_string':2}[kind]);values.append(a.get('value',a.get('field_offset',a.get('address',0))))
   h.append('{%d,%d,%d,%d,%d,{%s},{%s}},'%(v['CALL_pc'],{'GetStockObject':0,'DeleteObject':1,'CreateFontA':2}[v['service']],v['instance_root_offset'],len(values),v['frame_minus_root_frame'],','.join(str(x)for x in values),','.join(str(x)for x in kinds)))
 h+=['};','inline constexpr FS FSs[]{']
 for root in roots:
  for v in root['FS_operations']:h.append('{%d,%s},'%(v['PC'],str(bool(v['writing'])).lower()))
 h+=['};','inline constexpr Array arrays[]{']
 for v in contracts['source_array_contracts']:
  for root in v['roots']:h.append('{%d,%d,%d,%d,%d,%d,%d},'%(root,v['CALL_pc'],v['base_root_offset'],v['stride'],v['count'],v['constructor'],v['destructor']))
 h+=['};','using Body=void*(*)(State*,unsigned,void*);']
 for entry in entries:h.append('extern "C" void *mw34_widget_game_f_%x_body(State*,unsigned,void*);'%entry)
 h+=['inline Body body(unsigned pc){switch(pc){']+['case %d:return mw34_widget_game_f_%x_body;'%(e,e)for e in entries]+['default:return nullptr;}}','} // namespace literal']
 (out/'literals.hpp').write_text('\n'.join(h)+'\n')
 bridges=[]
 for name in sorted(bridge_names):
  if '_direct_'in name:bridges.append('extern "C" void *%s(State*s,unsigned a,void*p){return mw34_widget_game_call(s,a,p);}'%name)
  elif name.endswith('_undefined_8'):bridges.append('extern "C" std::uint8_t %s(){return 0;}'%name)
 (out/'bridges.inc').write_text('\n'.join(bridges)+'\n')
 for name in ('component.hpp','component.cpp','native_api.s'):
  p=bind('tools/m4-widget-native/'+name);shutil.copyfile(p,out/name)
 for p in out.iterdir():files[str(p)]=sha(p)
 for p in [Path(__file__).resolve(),R/'tools/m4-widget-native/build.py',R/'tools/m4-widget-native/build.ps1']:bind(p)
 report={'passed':True,'scope':'Reusable six-root widget native component preparation; no execution, service implementation admission, source/native equivalence or initializer credit','roots':[r['root']for r in roots],'root_count':6,'literal_bodies':51,'instructions':1093,'reached_PCs':len(reached),'GDI_calls':gi,'virtual_calls':vi,'FS_operations':fi,'array_iterations':75,'IRs':irs,'namespace_relations':origins,'files':files,'actual_GDI_provider_calls_prepared':True,'borrowed_stock_and_owned_fonts_distinct':True,'CRT_registry_services':'Explicit caller-context actual Services interface; no return/allocation output seeds','native_executed':False,'source_native_equivalence':False,'initializer_credit':0,'cold_path_admission':False,'permission_query_available':False,'whole_caller_FP_execution_proof':False}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'report':str(out/'report.json'),'sha256':sha(out/'report.json'),'counts':[6,51,1093,gi,vi,fi]}))
if __name__=='__main__':main()
