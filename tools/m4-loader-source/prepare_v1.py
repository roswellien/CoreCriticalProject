"""Prepare the remaining loader root and physically close its readonly switch.
Static source and compilation obligations only; no API results or live owners."""
from pathlib import Path
from collections import deque
import copy,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-loader-source'/name;assert not out.exists();out.mkdir(parents=True)
 pins={};commands=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.zip','.mwb');v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def write(n,d):q=out/n;q.write_text(json.dumps(d,indent=2)+'\n');pin(q)
 try:
  static=R/'reports/m4-remaining-service-source/preparation-r2'
  prior=read(static/'report.json','e137cf7e923009c39de1ba3b6135e0e8ca5b43826f0ec993396f77bd82acc2c4');assert prior['passed']
  graphs=read(static/'all-seven-graphs.json',prior['files'][str((static/'all-seven-graphs.json').resolve())])
  regs=read(R/'reports/m4-remaining-service-source/preparation-r1/registration-roots.json')
  root=next(x for x in regs if x['entry']==0x47f760);assert root['callback']==0x47f790
  rp=pin(R/'tools/m4-onexit-batch-recovery/recover.py');sp=importlib.util.spec_from_file_location('loader_focused_recovery',rp);recovery=importlib.util.module_from_spec(sp);sp.loader.exec_module(recovery)
  game=recovery.Module(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'))
  for g in graphs.values():recovery.ingest(game,g['instructions'])
  def physical(a,n):off,_=game.image.rva_range(a-game.base,n);return game.image.data[off:off+n],off
  assert physical(root['slot'],4)[0]==struct.pack('<I',root['entry'])
  evidence=read(R/'reports/m4-loader-source/ghidra-registry-r1/dossier.json')['structuredContent']
  dossier=evidence['result'];assert dossier['procedure']['address']=='0x482970'
  switch=dossier['native_api']['jump_tables'];assert len(switch)==1
  switch=switch[0];assert switch['dispatch_address']=='0x482979'and switch['data_sources'][0]['entry_size_bytes']==4 and switch['data_sources'][0]['entry_count']==13
  table,offset=physical(0x4829e8,52);targets=struct.unpack('<13I',table)
  mappings={x['case_value']:int(x['target_address'],16)for x in switch['mappings']}
  assert set(mappings)==set(range(13))-{11} and switch['default_targets'][0]['target_address']=='0x4829e1'
  for i in range(13):assert targets[i]==mappings.get(i,0x4829e1)
  sections=[x for x in game.image.sections if x['virtual_address']<=0x4829e8-game.base and 0x482a1c-game.base<=x['virtual_address']+x['raw_size']]
  assert len(sections)==1 and sections[0]['readable']and not sections[0]['writable']
  assert physical(0x482970,16)[0]==bytes.fromhex('8b44240483f80c7768ff2485e8294800b8')
  # Focused decoder supplies the case instructions omitted by the first
  # disassembler's targetless indirect edge, without erasing that edge.
  recovery.decode(game,0x482980,0x4829e6,out,commands)
  cases,deferred=recovery.closure(game,sorted(set(targets)),out,commands,maximum=20);assert not deferred
  assert len(cases)==13 and all(not g['unresolved_controls']and not g['direct_calls']for g in cases.values())
  accepted={0x5abd26,0x5abdb0,0x5ac0b0,0x5ac110,0x5ac140,0x5ac580}
  queue=deque([0x47f760]);seen=set()
  while queue:
   e=queue.popleft()
   if e in seen:continue
   seen.add(e);assert str(e)in graphs
   if e in accepted:continue
   queue.extend(x['target']for x in graphs[str(e)]['direct_calls'])
  selected={e:copy.deepcopy(graphs[str(e)])for e in sorted(seen-accepted)}
  selected.update(cases)
  case_rows={x['pc']:x for g in cases.values()for x in g['instructions']}
  dispatcher=selected[0x482970]
  dispatcher['instructions']=sorted({**{x['pc']:x for x in dispatcher['instructions']},**case_rows}.values(),key=lambda x:x['pc'])
  dispatcher['instruction_count']=len(dispatcher['instructions'])
  dispatcher['instruction_bytes_sha256']=hashlib.sha256(b''.join(bytes.fromhex(x['bytes'])for x in dispatcher['instructions'])).hexdigest()
  dispatcher['indirect_physical_table_candidates']=list(targets)
  dispatcher['execution_or_admission']='Complete source candidates; actual EAX bound/table readonly/current operand and dispatch path still required'
  rows={}
  for e,g in selected.items():
   for x in g['instructions']:
    assert physical(x['pc'],x['size'])[0].hex()==x['bytes']
    assert x['pc']not in rows or rows[x['pc']]==x;rows[x['pc']]=x
  imports=[dict(entry=e,**x)for e,g in selected.items()for x in g['import_sites']]
  unresolved=[dict(entry=e,**x)for e,g in selected.items()for x in g['unresolved_controls']]
  plan=dict(scope='Loader root actual source side effects and owning API requirements, no fixed success substitution',
   root=root,object=0x608c88,
   registry=dict(procedure=0x4828d0,version_getter=0x4af280,path_format=0x5e5fa0,RunDir=0x5e5f98,
    APIs=['RegOpenKeyExA','RegQueryValueExA','SetCurrentDirectoryA','RegCloseKey'],
    require_actual_registry_status_type_size_buffer_handle_and_CWD=True),
   message_library=dict(procedure=0x575f30,library='Mech3Msg.dll',export='ZLocGetID',
    require_actual_search_path_module_generation_export_and_retained_release=True),
   directx=dict(procedure=0x57a3d0,require_actual_OSVERSIONINFO148=True,
    dynamic_exports=['DirectDrawCreate','DirectInputCreateA'],require_owned_COM_identity_and_each_live_vtable_slot=True,
    require_actual_QueryInterface_hresult_output_release_refcount_and_whole_guest_structs=True,
    legacy_minimum=0x600,fixed_DirectX_success_forbidden=True),
   error_paths=dict(retained_ExitProcess=True,actual_FormatMessage_LocalFree_MessageBeep_GetFocus_MessageBox_required_on_observed_path=True),
   MFC=dict(accepted_named_imports_as_boundary_requirements=True,CString_constructor=0x5abdb0,allocation=0x5abd26,request_on_success=0xc0),
   switch=dict(dispatch=0x482979,table=0x4829e8,whole_table_hex=table.hex(),file_offset=offset,targets=list(targets),
    own_readonly_actual_input_and_bound_EAX_required=True),
   original_capture_required=True,native_current_side_effect_identity_required=True,
   source_AFTER_input=False,original_executed=False,native_executed=False,initializer_credit=0)
  write('game-new-graphs.json',selected);write('fs-roots.json',[root]);write('source-rows.json',list(rows.values()));write('import-boundaries.json',imports);write('execution-plan.json',plan)
  for q in (R/'tools/m4-service-initializers/recover.py',R/'tools/analysis/pe.py',recovery.DECODER,Path(__file__),Path(sys.executable)):pin(q)
  for q in out.iterdir():
   if q.is_file():pin(q)
  report=dict(passed=True,scope='Remaining loader initializer: exact complete source rows and physically closed readonly switch candidates, typed API/COM/live-owner obligations retained',roots=[root],root_count=1,literal_bodies=len(selected),instructions=len(rows),source_bytes=sum(x['size']for x in rows.values()),new_entries=sorted(selected),accepted_service_entries=sorted(accepted),priority_new_unresolved_controls=unresolved,readonly_switch_candidates=len(targets),Ghidra_evidence_is_source_guide_only=True,commands=commands,original_executed=False,native_executed=False,initializer_credit=0,files=pins)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');passed=True;print(json.dumps(dict(passed=True,sha256=sha(q),bodies=len(selected),instructions=len(rows),remaining_indirect_obligations=len(unresolved))))
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(sys.argv[1])

