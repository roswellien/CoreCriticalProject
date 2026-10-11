"""Namespace-only constructor lifts and concrete same-session service contracts."""
from pathlib import Path
import hashlib,json,re,shutil,struct,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name,service,service_sha):
 out=R/'reports/m4-constructor-native'/name;need(not out.exists(),'Fresh constructor Component preparation');out.mkdir(parents=True);pins={};origins=[];irs=[];bridge_names=set()
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No capture reader');v=sha(p);need(h is None or h==v,'Exact physical constructor input '+str(p));pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 source=read(R/'reports/m4-constructor-source/preparation-r1/report.json','0d5adb32fbd8b8d3d8d3da308cd48a7050071f2f2c61795840d63955385c26cf');bodies=read(R/'reports/m4-constructor-source/preparation-r1/literal-bodies.json',source['files'][str((R/'reports/m4-constructor-source/preparation-r1/literal-bodies.json').resolve())]);contracts=read(R/'reports/m4-constructor-source/preparation-r1/contracts.json',source['files'][str((R/'reports/m4-constructor-source/preparation-r1/contracts.json').resolve())]);rows=read(R/'reports/m4-constructor-source/preparation-r1/source-instructions.json',source['files'][str((R/'reports/m4-constructor-source/preparation-r1/source-instructions.json').resolve())]);need(len(rows)==1401,'Complete frozen constructor source union')
 observed=read(R/'reports/m4-constructor-original/chronological-validation-r3/report.json','00f22911cff2ebde706df7eac235d1621127cb6bd670fd9d680c8478f19b0b95');need(observed['passed']and observed['reader_closed'],'Whole current positive original observation')
 for key in('constructor-observations.json','constructor-normal-boundaries.json','actual-initial-allocation-inputs.json','actual-list-graphs.json','actual-new-NULL-free-boundaries.json','actual-new-owner-cleanup.json'):p=R/'reports/m4-constructor-original/chronological-validation-r3'/key;pin(p,observed['files'][str(p.resolve())])
 rounding=read(R/'reports/m4-constructor-original/request-rounding-r1/report.json','c1817707871eda399c126602e2bc6240081f076d914776cb091ff3babc375ee7');need(rounding['passed'],'Physical finite request-rounding domain')
 service=pin(service,service_sha);sv=json.loads(service.read_bytes());need(sv['passed']and sv['whole_native_and_guest_extent_mirror']and sv['does_not_infer_HeapSize_capacity'],'Current unexecuted concrete borrowed service fork');pin(service.parent/'session.hpp',sv['files'][str((service.parent/'session.hpp').resolve())]);shutil.copyfile(service.parent/'session.hpp',out/'session.hpp')
 lifts=read(R/'reports/m4-remaining-service-source/lifts-r2/report.json','b408ef417766435e082a436a2af6fbbcd3827fd1e30e6503d7d16fc7b1fb3c8e');parent=read(R/'reports/m4-formatting-native/preparation-r19/report.json','1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3')
 entries=[]
 for row in bodies['compiled']:
  entry=row['entry'];entries.append(entry)
  for item in row['objects'].values():pin(item['path'],item['sha256'])
  p=R/f'reports/m4-remaining-service-source/lifts-r2/f_{entry:x}-host.ll';pin(p,lifts['source_bodies'][f'f_{entry:x}']['host_sha256'])
  raw=p.read_text();transformed=raw.replace('mw34_onexit_game_','mw34_constructor_game_');need(transformed.replace('mw34_constructor_game_','mw34_onexit_game_')==raw,'Namespace-only IR substitution');q=out/p.name;q.write_text(transformed);irs.append(str(q));origins.append(dict(entry=entry,original_IR=str(p.resolve()),original_sha256=sha(p),component_IR=str(q),component_sha256=sha(q),change='Exact symbol-prefix substitution only'));bridge_names|=set(re.findall(r'@(mw34_constructor_game_[A-Za-z0-9_]+)',transformed))
 for row in bodies['reused']:
  entry=row['entry'];entries.append(entry);matches=[Path(p)for p in parent['entry_objects']if Path(p).name==f'f_{entry:x}-O0.obj'];need(len(matches)==1,'Unique physical accepted helper object');obj=pin(matches[0],parent['entry_objects'][str(matches[0])]);p=pin(obj.with_name(f'f_{entry:x}-host.ll'));raw=p.read_text();transformed=raw.replace('mw34_onexit_game_','mw34_constructor_game_');need(transformed.replace('mw34_constructor_game_','mw34_onexit_game_')==raw,'Exact helper namespace-only IR');q=out/p.name;q.write_text(transformed);irs.append(str(q));origins.append(dict(entry=entry,original_IR=str(p),original_sha256=sha(p),component_IR=str(q),component_sha256=sha(q),change='Exact symbol-prefix substitution only'));bridge_names|=set(re.findall(r'@(mw34_constructor_game_[A-Za-z0-9_]+)',transformed))
 need(len(entries)==len(set(entries))==31 and bodies['uncompiled'][0]['entry']==0x56fea0,'25 compiled bodies plus6 authentic helpers; cold recursion stays explicit')
 sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
 pin(R/'tools/analysis/pe.py');gamepath=pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');game=PEImage(gamepath.read_bytes())
 def physical(address,n):return game.data[game.rva_to_offset(address-game.image_base):game.rva_to_offset(address-game.image_base)+n]
 raw=struct.unpack('<I',physical(0x5bb52c,4))[0]
 h=['#pragma once','#include "component.hpp"','#include <array>','namespace mw34::m4_constructor_native::literal {','struct Instruction {unsigned pc,size,pop;bool call,ret;std::array<unsigned char,16>bytes;};','inline constexpr Instruction instructions[]{']
 for row in rows:
  data=bytes.fromhex(row['bytes']);need(len(data)==row['size']<=16 and physical(row['pc'],len(data))==data,'Whole physically exact current constructor source rows');pop=int(row['operands'].split()[0],0)if row['mnemonic'].startswith('ret')and row['operands'].strip()else 0
  h.append('{%d,%d,%d,%s,%s,{%s}},'%(row['pc'],row['size'],pop,str(row['mnemonic']=='call').lower(),str(row['mnemonic'].startswith('ret')).lower(),','.join(str(x)for x in data)))
 h+=['};','inline const Instruction*instruction(unsigned pc){for(auto&v:instructions)if(v.pc==pc)return&v;return nullptr;}',f'inline constexpr unsigned onexit_raw={raw};','inline bool readonly_getter_slot(unsigned address){return address==0x5bcc80||address==0x5cab78||address==0x5ca6f0;}','using Body=void*(*)(State*,unsigned,void*);']
 for entry in entries:h.append('extern "C" void*mw34_constructor_game_f_%x_body(State*,unsigned,void*);'%entry)
 h+=['inline Body body(unsigned pc){switch(pc){']+['case %d:return mw34_constructor_game_f_%x_body;'%(e,e)for e in entries]+['default:return nullptr;}}','}']
 (out/'literals.hpp').write_text('\n'.join(h)+'\n');bridges=[]
 for bridge in sorted(bridge_names):
  if '_direct_'in bridge:bridges.append('extern "C" void*%s(State*s,unsigned a,void*p){return mw34_constructor_game_call(s,a,p);}'%bridge)
  elif bridge.endswith('_undefined_8'):bridges.append('extern "C" std::uint8_t %s(){return 0;}'%bridge)
 (out/'bridges.inc').write_text('\n'.join(bridges)+'\n')
 for filename in('component.hpp','component.cpp'):shutil.copyfile(pin(R/'tools/m4-constructor-native'/filename),out/filename)
 asm=pin(R/'tools/m4-widget-native/native_api.s','692b17f008c0cdc69c9cc4ea57959df76f520d4913e40a49ee281e212f9e1e7a').read_text();asm='.text\n'+asm[asm.index('.globl mw34_widget_hardware_call'):];(out/'native_api.s').write_text(asm.replace('mw34_widget_','mw34_constructor_'))
 service_delta=dict(parent_widget_service_sha256=sv['parent_service_sha256'],current_service_sha256=service_sha,public_methods=['borrow_constructor_mfc(State&,root,site,frame,return_PC)','constructor_owner(guest,bytes)','constructor_owner_read(State&,root,PC,address,width,value)','constructor_source_write(State&,root,PC,address,width,value)'],MFC_allocations=[dict(root=r,site=s,requested=n)for r,s,n in[(0x4103f0,0x58af12,12),(0x4103f0,0x58af6a,4),(0x410440,0x58af12,12),(0x410440,0x58af6a,4),(0x459b40,0x58f2a2,12),(0x459b40,0x45b80e,12)]],MFC_free=[dict(root=r,site=0x58af9a,argument=0)for r in(0x4103f0,0x410440)],callbacks=[dict(root=r['entry'],callback=r['callback'])for r in contracts['roots']],original_targets='Physically authenticated MFC8235F401EA0/MFC8255F401782; native literal provider keeps own projected routes',rounding='Actual current CRT mode1 literal (request+15)&FFFFFFF0; sourceHeapAllocextent distinct from measured HeapSizecapacity',source_mirror='Full native extent and mapped guest tails checked before/after every literal owned scalar; updates expected_store and genuine source TIB effects',getter='Whole current carried circular native-owner list; excludes sentinel payload; current readonly source slot/held EDX and published PE receiver',constructor_after_seed=False)
 (out/'service-delta.json').write_text(json.dumps(service_delta,indent=2)+'\n')
 for p in out.iterdir():pin(p)
 for p in(__file__,R/'tools/m4-constructor-native/build.py',R/'tools/m4-constructor-native/build.ps1'):pin(p)
 report=dict(passed=True,scope='Compile-only constructor3 namespaced literal Component and finite real service preparation; no genuine literal comparison/native execution/admission/initializer credit',root_count=3,roots=[0x4103f0,0x410440,0x459b40],literal_bodies=31,new_bodies_from_existing_compiled_IR=25,reused_helper_IRs=6,physical_rows=len(rows),namespace_relations=origins,IRs=irs,service_path=str(service),service_sha256=service_sha,original_validation_sha256=sha(R/'reports/m4-constructor-original/chronological-validation-r3/report.json'),cold_recursive_entry=0x56fea0,whole_literal_original_source_proof_pending=True,flag_consumer_audit_pending=True,before_current_native_graph_admission_pending=True,native_executed=False,initializer_credit=0,source_AFTER_seed=False,files=pins)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p),literal_bodies=len(entries))))
if __name__=='__main__':main(sys.argv[1],Path(sys.argv[2]).resolve(),sys.argv[3])
