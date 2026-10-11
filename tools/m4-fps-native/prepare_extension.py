"""Prepare the seventh widget/FPS literal extension without a target worker.

The actual source proof selects reached addresses and call identities only.
Observed memory values, CPU outputs and GDI handles never enter the executable
contracts or compilation graphs.
"""
from pathlib import Path
import ast, collections, hashlib, importlib.util, json, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={};READS=set();OPTIONAL=set()
def need(v,m):
 if not v:raise ValueError(m)
def audit(event,args):
 if event!='open' or not args or not isinstance(args[0],(str,bytes)):return
 p=Path(args[0]).resolve();mode=args[1]if len(args)>1 else None;flags=args[2]if len(args)>2 else 0
 if p.is_relative_to(R)and(isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and not(flags&3)):
  need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader in extension preparation');(READS if p.is_file()else OPTIONAL).add(str(p))
sys.addaudithook(audit)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Whole physical fixed input '+str(p));PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def load(p,n):
 s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(name):
 out=R/'reports/m4-fps-native'/name;need(not out.exists(),'Fresh archive-free FPS preparation');out.mkdir(parents=True)
 current=read(R/'reports/m4-widget-native/preparation-r3/report.json','69a29eddf46f6c189edc462e5f5734a96e3d98c2c1f37778a54d36c0fd62eae5');contracts=read(R/'reports/m4-widget-native/preparation-r3/contracts.json',current['files'][str((R/'reports/m4-widget-native/preparation-r3/contracts.json').resolve())])
 actual_path=R/'reports/m4-fps-original/source-r3/report.json';actual=read(actual_path,'12a24d02ef22120d7798ae9c273866d76a2abd1089353127b22f9f8e6d57e154');need(actual['passed']and not actual['AFTER_machine_or_memory_seed']and not actual['source_registration_provider_executed'],'Literal genuine prefix with precise finite scope')
 source=read(actual_path.parent/'source-derivations.json',actual['files'][str((actual_path.parent/'source-derivations.json').resolve())]);need(len(source)==7 and source[-1]['root']==0x40f000,'Six widgets then actual FPS initializer');row=source[-1]
 G=load(R/'reports/m4-fps-original/source-preparation-r4/game_model.py','FPS_extension_literal');program,callbacks=G.source_program();raw_contracts=read(R/'reports/m4-fps-original/source-preparation-r4/source-contracts.json');root=raw_contracts['selected_roots'][-1];need(root['entry']==0x40f000 and root['object']==0x5fc378,'Exact seventh Runtime route and source instance')
 PE=load(R/'tools/analysis/pe.py','FPS_extension_PE');game_path=pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');crt_path=pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');game=PE.PEImage(game_path.read_bytes());crt=PE.PEImage(crt_path.read_bytes())
 reached=sorted(set(row['source_PCs']));physical=[]
 for pc in reached:
  v=program[pc];b=bytes.fromhex(v['bytes_hex']);pe=crt if pc>=0x78000000 else game;offset,_=pe.rva_range(pc-pe.image_base,len(b));need(pe.data[offset:offset+len(b)]==b,'Every reached whole physical source instruction');physical.append(dict(PC=pc,width=len(b),bytes_hex=b.hex(),file_offset=offset,image=str(crt_path if pc>=0x78000000 else game_path),mnemonic=v['mnemonic'],operands=v['operands']))
 calls=[]
 for i,pc in enumerate(row['source_PCs'][:-1]):
  v=program[pc]
  if v['mnemonic']=='call':calls.append(dict(PC=pc,next_source_PC=row['source_PCs'][i+1],operand=v['operands']))
 game_reuse=read(R/'reports/m4-remaining-service-source/lifts-r2/report.json','b408ef417766435e082a436a2af6fbbcd3827fd1e30e6503d7d16fc7b1fb3c8e');provider_reuse=read(R/'reports/m4-formatting-source/lifts-r1/report.json','bc7683eca1610ee80595a0582789fbed76c72cc69e2c5ab78fabd14e2f670da0');reuse=[]
 for entry,gate,folder in [(0x40f000,game_reuse,'m4-remaining-service-source'),(0x40f010,game_reuse,'m4-remaining-service-source'),(0x7800fc9b,provider_reuse,'m4-formatting-source'),(0x7801041a,provider_reuse,'m4-formatting-source')]:
  key=f'f_{entry:x}';b=gate['source_bodies'][key];ir=pin(R/f'reports/{folder}/lifts-r2/{key}-host.ll'if folder=='m4-remaining-service-source'else R/f'reports/{folder}/lifts-r1/{key}-host.ll',b['host_sha256']);objects=[]
  for v in b['objects'].values():objects.append(dict(path=str(pin(v['path'],v['sha256'])),sha256=v['sha256']))
  reuse.append(dict(entry=entry,IR=str(ir),IR_sha256=sha(ir),objects=objects,instructions=b['instructions'],namespace_change_prepared='mw34_onexit_game_ to mw34_widget_game_ only'))
 new_vs=read(R/'reports/m4-fps-original/source-preparation-r4/vsprintf-physical-graph.json');normal=read(R/'reports/m4-formatting-source/provider-recovery-r2/instruction-contracts.json');new_graphs={}
 for entry,rows in [(0x780230dd,[program[v['pc']]for v in new_vs['instructions']]),(0x7800fe25,[v for v in normal['instructions']if 0x7800fc9b<=v['pc']<0x7801041a])]:
  ins=[dict(pc=v['pc'],size=v['width'],bytes=v['bytes_hex'],mnemonic=v['mnemonic'],operands=v['operands'])for v in rows]
  for v in ins:
   offset,_=crt.rva_range(v['pc']-crt.image_base,v['size']);need(crt.data[offset:offset+v['size']]==bytes.fromhex(v['bytes']),'Complete fresh literal graph physical CRT bytes')
  new_graphs[str(entry)]=dict(entry=entry,instructions=ins,unresolved_controls=[],FS_sites=[],FP_sites=[],research_terminal=False)
 need(len(new_graphs[str(0x780230dd)]['instructions'])==31 and len(new_graphs[str(0x7800fe25)]['instructions'])==595,'Only exact vsprintf body and full lower-span output continuation')
 known={v['pc']for v in contracts['instructions']};covered=set(known)
 for v in reuse:covered.update(r['pc']for r in v['instructions'])
 for v in new_graphs.values():covered.update(r['pc']for r in v['instructions'])
 need(set(reached)<=covered,'All actually derived seventh-root PCs covered by existing51 plus four reuse and two fresh entries')
 frame=0x20001800;operands=[]
 for pc,address,_value,width,writing in row['source_accesses']:
  role=1 if 0x20001000<=address<0x20002000 else 2 if address==0x7ffde000 else 0;offset=address-frame if role==1 else 0 if role==2 else address;operands.append(dict(PC=pc,address_role=role,offset=offset,width=width,writing=bool(writing)))
 need(len(operands)==357,'Exact real seventh prefix operands, no value oracle');registration=root['registration'];site=registration['CALL_pc'];tail=[0x5ac124,0x5ac127,0x5ac14a,0x5ac14d,0x5ac14f,0x5ac151,0x5ac153,0x5ac154,site+5,site+8]
 for pc in tail:need(pc in program,'Literal final epilogue physical contract exists')
 for pc,offset in [(0x5ac127,-16),(0x5ac154,-8),(site+8,0)]:operands.append(dict(PC=pc,address_role=1,offset=offset,width=4,writing=False))
 virtuals=[dict(CALL_pc=v['PC'],instance_root_offset=v['instance']-root['object'],source_store_PC=v['source_store']['PC'],source_vptr=v['source_store']['value'],readonly_slot=v['slot'],target=v['target'],frame_minus_root_frame=v['ESP']-frame)for v in row['virtual_calls']]
 dispatches=[dict(PC=v['PC'],index=v['index'],readonly_table_address=v['table_read'],target=v['target'])for v in row['provider_dispatches']];need(len(dispatches)==3 and all(v['PC']==0x7800fcef and v['index']==0 and v['target']==0x7800fe25 for v in dispatches),'Only exact actual literal-character output dispatch')
 static_tables=[]
 for v in dispatches:
  offset,_=crt.rva_range(v['readonly_table_address']-crt.image_base,4);value=int.from_bytes(crt.data[offset:offset+4],'little');need(value==v['target'],'Whole raw CRT static dispatch cell');static_tables.append(dict(address=v['readonly_table_address'],bytes_hex=crt.data[offset:offset+4].hex(),target=value))
 fmt_offset,_=game.rva_range(0x5e1590-game.image_base,16);fmt=game.data[fmt_offset:fmt_offset+16];need(fmt[:4]==b'fps\0','Exact physical finite narrow format')
 new_contract=dict(schema='mw34-FPS-widget-extension-v1',root=root,selected_after=contracts['roots'][-1]['root'],causal_operands=operands,reached_PCs=reached,instructions=[program[p]for p in reached],virtual_calls=virtuals,FS_operations=[dict(PC=v['PC'],writing=v['writing'])for v in row['FS_joins']],literal_registration_tail_PCs=tail,format_CALL=dict(PC=0x5a2f68,IAT=0x5bb53c,named_source_target=0x780230dd,return_PC=0x5a2f6e,argument_count=3,frame_role='Committed current literal CALL frame',destination_role='Same current instance + 0x238',destination_extent=512,format_address=0x5e1590,format_physical_16B=fmt.hex(),va_role='Exact third cdecl argument derives source current frame',host_vsprintf_substitution=False),output_dispatches=dispatches,whole_physical_dispatch_cells=static_tables,original_output_values_seeded=False,original_handles_seeded=False,AFTER_State_or_memory_seed=False,cold_formatter_paths_admitted=False,source_shutdown_callbacks_admitted=False)
 payloads={'contracts.json':new_contract,'new-literal-graphs.json':new_graphs,'reused-literal-bodies.json':reuse,'physical-reached-instructions.json':physical,'actual-source-control-identities.json':calls,'roots.json':[dict(entry=0x40f000,object=root['object'],slot=root['slot'],registration=registration)]}
 for n,v in payloads.items():p=out/n;p.write_text(json.dumps(v,indent=2)+'\n');pin(p)
 template_path=pin(R/'tools/m4-formatting-source/lift_provider.py');template=template_path.read_text();need(template.count("  pin(REC/'report.json',REC_SHA);rows=")==1,'Exact inherited literal compiler graph-load boundary')
 a=template.index("  pin(REC/'report.json',REC_SHA);rows=");b=template.index('  roots=[];inputs={}',a);template=template[:a]+"  pin(REC/'report.json',REC_SHA);graphs=json.loads(pin(REC/'new-literal-graphs.json').read_bytes())\n"+template[b:]
 template=template.replace("ROOT/'reports/m4-formatting-source/provider-recovery-r2'","ROOT/'reports/m4-fps-native/extension-preparation-r1'").replace("2aa9a712983ab98a08c3f59adf8e29b24c17f1f8c0d41ebb786a55c7241a13b9",'FRESH_PREPARATION_SHA').replace("ROOT/'reports/m4-formatting-source'/name","ROOT/'reports/m4-fps-native'/name").replace("undefined_calls=len(re.findall(r'call i8 @__remill_undefined_8\\(',baseline.read_text()))","undefined_calls=len(re.findall(r'call (?:zeroext )?i8 @__remill_undefined_8\\(',baseline.read_text()))").replace("scope='Literal narrow formatter seven helpers plus two exact indirect continuations; dormant physical branches unadmitted'","scope='Fresh literal vsprintf and exact FE25 continuation, compilation only; every cold branch remains unadmitted'")
 ast.parse(template);p=out/'lift-template.py';p.write_text(template);pin(p)
 for p in list(READS):pin(p)
 pin(__file__);pin(sys.executable);need(READS<=set(PINS),'All actual successful source preparation reads pinned')
 report=dict(passed=True,scope='Archive-free exact seventh widget/FPS source contracts and minimal literal compilation plan; no component execution/admission/equality credit',counts=dict(existing_widget_bodies=51,reused_added_bodies=4,new_bodies=2,prospective_component_bodies=57,prospective_component_literal_objects=114,reached_instruction_occurrences=len(row['source_PCs']),reached_unique_PCs=len(reached),provider_instruction_occurrences=sum(p>=0x78000000 for p in row['source_PCs']),provider_unique_PCs=sum(p>=0x78000000 for p in reached),prefix_operands=357,root_operands=360,virtual_calls=len(virtuals),FS_operations=len(row['FS_joins']),GDI_calls=len(row['API_inputs']),literal_character_dispatches=len(dispatches)),new_entries=[0x780230dd,0x7800fe25],reused_entries=[v['entry']for v in reuse],current_six_component_sha256=sha(R/'reports/m4-widget-native/preparation-r3/report.json'),genuine_FPS_source_sha256=sha(actual_path),output_or_AFTER_seed=False,native_executed=False,source_native_equality=False,initializer_credit=0,archive_reader_opened=False,all_actual_read_dependencies_pinned=True,optional_reads=sorted(OPTIONAL),files=PINS)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');h=sha(p);target=R/'tools/m4-fps-native/lift_extension.py';need(not target.exists(),'Fresh minimal literal compiler');target.write_text(template.replace('FRESH_PREPARATION_SHA',h));print(json.dumps(dict(passed=True,path=str(p),sha256=h,counts=report['counts'],lift_tool_sha256=sha(target))))
if __name__=='__main__':main(sys.argv[1])
