"""Physical remaining seven-root preparation; no new runtime admission."""
from pathlib import Path
import copy,hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-remaining-service-source';PINS={}
ROOTS=(0x4103f0,0x410440,0x459b40,0x40f000,0x479590,0x4af240,0x47f760)
PRIORITY=ROOTS[:5]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(x,m):
 if not x:raise ValueError(m)
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No captures');v=sha(p);need(h is None or h==v,'Exact physical '+str(p));PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def load(p,name):
 s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(name):
 out=B/name;need(not out.exists(),'Fresh remaining source preparation');out.mkdir(parents=True);passed=False;commands=[]
 try:
  acceptance=read(R/'reports/m4-joint-startup130-root/acceptance-r1/report.json','12215395619ea72ee1a587763112bc3a2ed9aad15c9c99a5697f69c9658429aa');need(acceptance['passed'],'Exact accepted130 parent')
  frontier=read(R/'reports/m4-joint-startup116-root/next-frontier-r1/remaining-roots.json','d2faf2654877f203cef768634038254a7072bcdcdc4948bda3e9e93988ea3152')
  graphs=read(R/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json','da2482873e1678a0a2493ed7f60421440447c43e63826b53f2d5b09cf573ba5a')
  widget=read(R/'reports/m4-widget-source/dispatch-r1/report.json','ee96052d75b9f459bcb1a96953e7130bbb98125c1d57c76fa7ed8ada9c415375');need(widget['passed'],'Frozen widget dispatch49')
  wg=read(R/'reports/m4-widget-source/dispatch-r1/game-bound-graphs.json');wl=read(R/'reports/m4-widget-source/lifts-r1/report.json');need(wl['passed'],'Existing widget literal objects')
  existing=read(R/'reports/m4-formatting-native/preparation-r19/report.json','1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3')
  recovery=load(R/'tools/m4-onexit-batch-recovery/recover.py','remaining_exact_graph');game=recovery.Module(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'))
  for g in graphs.values():recovery.ingest(game,g['instructions'])
  for g in wg.values():recovery.ingest(game,g['instructions'])
  selected=[next(x for x in frontier if x['entry']==root)for root in ROOTS];entries={e for x in selected for e in x['local_entries']};all_graphs={e:copy.deepcopy(wg.get(str(e),graphs[str(e)]))for e in entries}
  # Exact readonly slots give source candidates; current owner/vptr/store/RET
  # joins remain a genuine-observation obligation, not a dispatch admission.
  dynamic=[]
  for table,store,root in((0x5bcc68,0x4c0350,0x4103f0),(0x5cab60,0x4c05b0,0x410440),(0x5ca6d8,0x4bf945,None)):
   fact=game.data(table+0x18,4);target=int.from_bytes(bytes.fromhex(fact['initial_hex']),'little');need(target==0x40a850,'Physical shared identifier getter');dynamic.append(dict(CALL_pc=0x58b183,source_table=table,slot=table+0x18,slot_offset=0x18,slot_physical=fact,target=target,dominating_store_PC=store,root=root,current_owner_list_required=True,current_instance_store_required=True,measured=False))
  target_nodes,deferred=recovery.closure(game,[0x40a850,0x5733d0],out,commands,maximum=40);need(not deferred,'Two focused source targets closed physically');all_graphs.update(target_nodes)
  dynamic.append(dict(CALL_pcs=[0x5560ec,0x556100],literal_register='EDI',source_definition_PC=0x5733c0,definition='MOV EDX,5733D0 before CALL5733C5; callee MOV EDI,EDX5560D6',target=0x5733d0,caller=0x5733b0,source_shared_owner_global=0x72c508,nonnull_list_path_unmeasured=True,measured=False))
  raw_rows={}
  for e,g in all_graphs.items():
   for row in g['instructions']:
    pc=row['pc'];physical=game.data(pc,row['size']);need(physical['initial_hex']==row['bytes'],'Each retained whole physical instruction');need(pc not in raw_rows or raw_rows[pc]['bytes']==row['bytes'],'One physical byte identity');raw_rows[pc]=row
  # Root-specific source role bindings are additive. Body reuse does not reuse
  # the old widget runtime instance/array domain for these two font objects.
  font_indirect=[]
  for root,obj,store in((0x40f000,0x5fc378,0x40f187),(0x479590,0x608628,0x40e880)):
   fact=game.data(0x5bc598+0x8c,4);need(int.from_bytes(bytes.fromhex(fact['initial_hex']),'little')==0x5a0680,'Exact newroot font slot');font_indirect.append(dict(root=root,object=obj,CALL_pc=0x5a0669,source_vptr=0x5bc598,source_vptr_store_PC=store,slot_offset=0x8c,slot_physical=fact,target=0x5a0680,current_zero6384E8_required=True,current_instance_observation_required=True,measured=False))
  parser=load(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py','remaining_operands');contracts=[]
  for pc,row in sorted(raw_rows.items()):
   x=dict(pc=pc,width=row['size'],bytes_hex=row['bytes'],mnemonic=row['mnemonic'],operands=row['operands'].split(' <')[0])
   if x['mnemonic']in('rep','repe','repz','repne','repnz'):x['repeat']=x['mnemonic'];x['mnemonic'],x['operands']=x['operands'].split(None,1)
   c=parser.instruction_contract(x)
   if x['mnemonic'].startswith('stos'):c['explicit_memory_reads']=[];c['explicit_memory_writes']=[0]
   contracts.append(c)
  old={}
  for p,h in existing['entry_objects'].items():
   m=re.search(r'(?:^|[/\\])(?:f_|game_)([0-9a-f]+)-O([02])\.obj$',p)
   if m:old.setdefault(int(m[1],16),{})[m[2]]=dict(path=p,sha256=h,provider='accepted130')
  for body in wl['source_bodies'].values():
   old[body['entry']]={level[-1]:dict(path=o['path'],sha256=o['sha256'],provider='widget49 pending0credit')for level,o in body['objects'].items()}
  priorities={e for x in selected if x['entry']in PRIORITY for e in x['local_entries']}|set(target_nodes);new={e:g for e,g in all_graphs.items()if e in priorities and e not in old};reused={e:old[e]for e in sorted(set(all_graphs)&set(old))}
  for e,objects in reused.items():
   need(set(objects)=={'0','2'},'Both optimization source object identities')
   for obj in objects.values():pin(obj['path'],obj['sha256'])
  roots=[]
  for x in selected:
   root=x['entry'];graph=all_graphs[root];calls=[r for r in graph['direct_calls']if r['target']==0x5ac140];need(len(calls)==1,'One literal registry CALL perroot');call=calls[0];push=next(r for r in graph['instructions']if r['pc']+r['size']==call['site']);callback=int(push['operands'].split(' <')[0],0);need(push['mnemonic']=='push','Source literal callback');slot=game.data(x['slot'],4);need(int.from_bytes(bytes.fromhex(slot['initial_hex']),'little')==root,'Physical original table entry')
   roots.append(dict(entry=root,slot=x['slot'],slot_physical=slot,callback=callback,registration_CALL_pc=call['site'],registration_return_PC=call['return_pc'],callback_executed=False,priority=root in PRIORITY,root_family='MFC shared-node constructor'if root in ROOTS[:3]else'widget/font'if root in ROOTS[3:5]else'version'if root==0x4af240 else'registry/library loader'))
  allocation_sites=[]
  for row in raw_rows.values():
   if row['mnemonic']=='call'and row['operands'].startswith('0x5abd26'):
    allocation_sites.append(dict(CALL_pc=row['pc'],return_PC=row['pc']+row['size'],row=row,physical_MFC_import=game.data(0x5bb4bc,4),source_request='Actual current stack argument derived from literal preceding instructions; size/capacity/providerreturn/newoccurrence unmeasured',source_current_owner_publication_required=True,measured=False))
  fs_rows=[r for r in contracts if'fs:'in r['operands']];frontiers=[dict(entry=e,**u)for e,g in all_graphs.items()for u in g['unresolved_controls']]
  plan=dict(priority_roots=list(PRIORITY),constructor_batch=dict(roots=list(ROOTS[:3]),current13prefix_required_for_first2=True,shared_header_pointer_cell=0x603fdc,global_request_base=game.data(0x5f2a48,4),current_shared_header_entire_capacity_and_links_required=True,each_repeated_MFC823_occurrence_identity_capacity_initial_bytes_required=True,source_MFC825_NULL_and_owned_free_lifetimes_required=True,virtual_bindings=dynamic,known_providers=['Accepted genuine MFC823/825 and whole registry lifecycle'],whole_before_object_pages_required=[0x603000,0x604000,0x605000,0x5f2000],static_prediction_supplies_observation=False),font_batch=dict(roots=list(ROOTS[3:5]),root_objects=[dict(root=0x40f000,base=0x5fc378,extent=0x4bc),dict(root=0x479590,base=0x608628,extent=0x4b0)],shared_widget49_literal_bodies_reused=True,instance_bindings=font_indirect,zero_font_registry_required=game.data(0x6384e8,4),normal_stock10_and_DeleteObject_attempt_reuse=True,owned_CreateFont_normal_path_unmeasured=False,root40F000_vsprintf_frontier=dict(CALL_pc=0x5a2f68,IAT=0x5bb53c,name='vsprintf',format=game.data(0x5e1590,4),format_text='fps',calling_convention='cdecl:destinstance+34,format5E1590,va_listpointerderivedbyLEA5A2F5E',full_actual_API_CPU_FX_ENV_frame_buffer_required=True,provider_literal_no_directives_path_required=True,old_widget_null_format_domain_reused=False),root479590_null_argument_route_reuses_widget=True),heavy_frontiers=dict(version=dict(root=0x4af240,object=0x60b198,input_filename=game.data(0x5e867c,10),names=['GetFileVersionInfoSizeA','GetFileVersionInfoA','VerQueryValueA'],actual_game_working_directory_and_file_identity_required=True,actual_success_or_failure_branch_required=True),registry_loader=dict(root=0x47f760,object=0x608c88,actual_registry_values_library_search_current_directory_module_handle_exports_required=True,error_ExitProcess_branch_retained=True,source_API_fixed_success_substitution=False)),original_executed=False,native_executed=False,initializer_credit=0)
  payloads={'all-seven-graphs.json':all_graphs,'game-new-graphs.json':new,'game-reused-objects.json':reused,'fs-roots.json':roots[:5],'registration-roots.json':roots,'instruction-contracts.json':dict(instructions=contracts,selected_roots=roots),'normal-prerequisites.json':plan,'open-frontiers.json':dict(unresolved_controls=frontiers,allocation_sites=allocation_sites,imports=[dict(entry=e,**site)for e,g in all_graphs.items()for site in g['import_sites']],FS_rows=fs_rows,all_dynamic_targets_unadmitted=True)}
  for label,data in payloads.items():p=out/label;p.write_text(json.dumps(data,indent=2)+'\n');pin(p)
  pin(__file__);pin(R/'tools/m4-service-initializers/recover.py');pin(R/'tools/analysis/pe.py');pin(recovery.DECODER)
  report=dict(passed=True,scope='Exact remaining seven static source roots; priority3constructor+2font literal preparation and existing widget49/accepted130 object reuse, with current ownership/provider/frame/frontier obligations retained',counts=dict(roots=7,priority_roots=5,source_graph_entries=len(all_graphs),unique_instructions=len(raw_rows),source_bytes=sum(r['size']for r in raw_rows.values()),priority_new_literal_bodies=len(new),reused_literal_entries=len(reused),MFC823_static_call_sites=len(allocation_sites),FS_static_sites=len(fs_rows),retained_unresolved_controls=len(frontiers),focused_new_target_graphs=len(target_nodes)),new_entries=sorted(new),reused_entries=sorted(reused),priority_new_unresolved_controls=[dict(entry=e,**u)for e,g in new.items()for u in g['unresolved_controls']],commands=commands,original_executed=False,native_executed=False,initializer_credit=0,files=PINS);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p),counts=report['counts'])))
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(sys.argv[1])
