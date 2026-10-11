"""Exact physical version initializer preparation; no worker or API execution."""
from pathlib import Path
from collections import deque
import hashlib, json, struct, sys, traceback

R=Path(__file__).resolve().parents[2]
BASE=R/'reports/m4-version-source'
STATIC=R/'reports/m4-remaining-service-source/preparation-r1'
STATIC_SHA='2cf6b50240076b4fd2ecced04ce1389b3b94c8b03ea331799c48ec90b4b34933'
GAME_SHA='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
ROOT=0x4af240
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh additive version preparation');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No capture access');v=sha(p);need(h is None or h==v,'Exact physical input '+str(p));pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def write(n,d):
  p=out/n;p.write_text(json.dumps(d,indent=2)+'\n');pin(p);return p
 try:
  prior=read(STATIC/'report.json',STATIC_SHA);need(prior['passed'],'Frozen remaining-service preparation')
  graphs=read(STATIC/'all-seven-graphs.json',prior['files'][str((STATIC/'all-seven-graphs.json').resolve())])
  prereq=read(STATIC/'normal-prerequisites.json',prior['files'][str((STATIC/'normal-prerequisites.json').resolve())]);need(prereq['heavy_frontiers']['version']['root']==ROOT,'Physical version identity')
  registrations=read(STATIC/'registration-roots.json',prior['files'][str((STATIC/'registration-roots.json').resolve())]);root=next(v for v in registrations if v['entry']==ROOT)
  sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
  game_path=pin(R/'MW3/Mech3.exe',GAME_SHA);pe=PEImage(game_path.read_bytes());pin(R/'tools/analysis/pe.py')
  def physical(a,n):
   off,_=pe.rva_range(a-pe.image_base,n);return pe.data[off:off+n],off
  queue=deque([ROOT]);reached=set()
  while queue:
   e=queue.popleft()
   if e in reached:continue
   reached.add(e);need(str(e)in graphs,'Finite physically decoded version graph')
   if e==0x5ac140:continue # Accepted literal onexit supplied by existing service.
   queue.extend(x['target']for x in graphs[str(e)]['direct_calls'])
  accepted={0x5abd1a,0x5abd26,0x5ac140};new={e:graphs[str(e)]for e in sorted(reached-accepted)}
  need(set(new)=={0x4af240,0x4af250,0x4af0a0,0x4af0f0,0x4af1a0,0x4eac90,0x4eac96,0x4eac9c},'Eight exact literal bodies')
  rows={}
  for g in new.values():
   need(not g['unresolved_controls']and not g['FP_sites']and not g['FS_sites'],'Finite flat no-FP version bodies')
   for x in g['instructions']:
    b,off=physical(x['pc'],x['size']);need(b.hex()==x['bytes'],'Every complete physical instruction')
    need(x['pc']not in rows or rows[x['pc']]==x,'One physical source row');rows[x['pc']]=x
  filename,fo=physical(0x5e867c,10);subblock,so=physical(0x5e8664,2)
  need(filename==b'mech3.exe\0'and subblock==b'\\\0','Actual physical source filename and root subblock')
  object_before=physical(0x60b198,60)[0];need(len(object_before)==60,'Whole physical 60-byte object')
  api=[]
  for pc,thunk,slot,name,argc,ret in [(0x4af10e,0x4eac9c,0x5bb748,'GetFileVersionInfoSizeA',2,0x4af113),(0x4af12c,0x4eac96,0x5bb74c,'GetFileVersionInfoA',4,0x4af131),(0x4af167,0x4eac90,0x5bb750,'VerQueryValueA',4,0x4af16c)]:
   g=graphs[str(thunk)];site=g['import_sites'][0];need(site['iat']==slot and site['symbol']['name']==name and site['symbol']['library']=='VERSION.dll','Exact complete version named import')
   api.append(dict(CALL_pc=pc,return_PC=ret,thunk=thunk,IAT=slot,name=name,argc=argc,physical_CALL_hex=rows[pc]['bytes'],physical_thunk_hex=g['instructions'][0]['bytes'],physical_IAT_hex=physical(slot,4)[0].hex(),calling_convention='stdcall',actual_native_identity_and_hardware_required=True))
  contract=dict(schema='mw34-version-initializer-physical-v1',root=root,object=dict(address=0x60b198,extent=60,physical_BEFORE_hex=object_before.hex(),source_constructor_zeroes=60),filename=dict(address=0x5e867c,bytes=10,hex=filename.hex(),file_offset=fo),query_subblock=dict(address=0x5e8664,bytes=2,hex=subblock.hex(),file_offset=so),APIs=api,MFC_calls=[dict(CALL_pc=0x4af11a,thunk=0x5abd26,ordinal=823,return_PC=0x4af11f,request='Same current object DWORD size from actual GetFileVersionInfoSizeA return',pointer_publication_PC=0x4af124,pointer_field=0x60b19c),dict(CALL_pc=0x4af1a8,thunk=0x5abd1a,ordinal=825,return_PC=0x4af1ad,argument='Current object pointer, including actual initial NULL',retain_NULL_free_route=True)],copy=dict(length_compare_PC=0x4af174,maximum=52,source='Actual VerQueryValueA pointer translated inside same genuine whole MFC owner',destination=0x60b1a0,full_buffer_before_after_required=True),working_directory=dict(path=str((R/'MW3').resolve()),actual_file=str(game_path),actual_file_sha256=GAME_SHA,relative_filename=True,current_directory_proof_required=True),registration=dict(CALL_pc=0x4af265,callback=0x4af270,service='Accepted source onexit; exact own committed guest CALL',callback_executed=False),normal_failure_routes_retained=[0x4af197,0x4af135],fixed_success_substitution=False,AFTER_seed=False)
  plan=dict(scope='One version root: physical static preparation only',original=dict(worker='New bounded selected-chronology capture, independent root admission before execution',observations=['All three actual VERSION.dll named export identities and entry bytes before/after','Whole guest API CPU40 FX512 ENV28 frame64, actual filename/subblock','Actual GetFileVersionInfoSizeA handle DWORD and return, branch taken','Each genuine MFC823 requested size/full capacity/native identity/whole initial bytes and MFC825 NULL or owned free','Whole resource buffer before/after both APIs and VerQueryValueA pointer/length inside same owner','Entire 60-byte object and carried prefix stack/State before/after','Source onexit registry API/owner/lifecycle and literal callback publication'],canonical_slot_required=True),native=dict(literal_bodies=8,provider='Actual native VERSION.dll functions; full pointer projection and hardware witnesses',owned_buffer='Existing genuine MFC823 allocation. New narrowly bounded borrowed-provider interface required; never std::vector malloc substitution',service_extension=['Borrow exact existing committed source MFC CALL frame through accepted literal allocator/free bodies','Retain actual NULL free behavior at first 4AF1A0 invocation','Authenticate actual same generation native allocation extent before version API','Commit whole native API output back to guest and checked private expected mirror, preserving unchanged capacity tail','Translate VerQueryValueA pointer only within that same actual owner','Borrow actual onexit only for physical callback 4AF270'],worker_execution_requires_independent_admission=True),source=dict(evaluator='Replay all eight exact physical bodies with typed actual native version call outputs as boundary observations',AFTER_as_input=False,same_buffer_alias_and_query_length_required=True),integration=dict(actual_carried_accepted_prefix_required=True,selected_chronology_excludes_unaccepted_roots=True,full144_credit_after_union_source_native_original_controls=False),native_executed=False,original_executed=False,initializer_credit=0)
  write('game-new-graphs.json',new);write('source-rows.json',list(rows.values()));write('fs-roots.json',[root]);write('contracts.json',contract);write('execution-plan.json',plan)
  pin(__file__);pin(R/'tools/m4-remaining-service-source/lift.py','998290ca327e5dce18a22da3d45a723f2f0f55f35f4cce137820ffa3aeea6b44')
  report=dict(passed=True,scope='One version initializer, eight complete finite physical literal bodies and genuine API/owner execution obligations',roots=[root],root_count=1,literal_bodies=len(new),instructions=len(rows),source_bytes=sum(x['size']for x in rows.values()),priority_new_unresolved_controls=[],new_entries=sorted(new),accepted_service_entries=sorted(accepted),native_executed=False,original_executed=False,initializer_credit=0,files=pins)
  p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(p),sha256=sha(p),bodies=len(new),instructions=len(rows))))
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(sys.argv[1])
