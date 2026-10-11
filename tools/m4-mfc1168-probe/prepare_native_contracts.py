"""Freeze the proved normal closure and borrowed-input roles for native work.

Static contracts are derived from pinned literal operands and genuine BEFORE
identities. Actual trace/result fields corroborate them; none grants new credit.
"""
from pathlib import Path
import hashlib,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-mfc1168-probe';PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);assert h is None or h==v;PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=B/name;assert not out.exists();out.mkdir();v=read(B/'validation-r6/report.json','81006b3089f41d0df95aae70428d400108d44c5026cc428682faab2407bd99f2');assert v['passed']
 for p,h in v['files'].items():pin(p,h)
 source=read(B/'validation-r6/source-derivations.json');normal=read(B/'validation-r6/reached-instruction-contracts.json');rows={r['pc']:r for r in normal['instructions']};domains=read(B/'validation-r6/actual-domain-observations.json');domain=domains[1]['domain'];backings=source['backings']
 entries=(0x5ae3e4,0x5ae3d1,0x5ae3a8,0x5abed0,0x5f401083,0x5f401000,0x5f4010ab,0x5f40107d,0x78001496,0x78003ddb,0x78001055,0x78003e84,0x7800129e);graphs={};assigned=set()
 for entry in entries:
  todo=[entry];seen=set();frontiers=[]
  while todo:
   pc=todo.pop()
   if pc in seen:continue
   if pc not in rows:frontiers.append(dict(target=pc,unproved=True));continue
   if pc in entries and pc!=entry:frontiers.append(dict(target=pc,literal_tail=True));continue
   seen.add(pc);r=rows[pc];op=r['mnemonic'];args=r['decoded_operands'];fall=pc+r['width']
   if op=='ret':continue
   if op=='call':todo.append(fall);continue
   if op=='jmp':
    if args[0]['kind']=='immediate':todo.append(args[0]['value'])
    else:frontiers.append(dict(source_PC=pc,source_indirect=True))
   elif op.startswith('j'):todo.extend((fall,args[0]['value']))
   else:todo.append(fall)
  assert seen;assigned|=seen;graphs[str(entry)]=dict(entry=entry,instructions=[dict(pc=p,size=rows[p]['width'],bytes=rows[p]['bytes_hex'],mnemonic=rows[p]['mnemonic'],operands=rows[p]['operands'])for p in sorted(seen)],FS_sites=[dict(pc=p,operands=rows[p]['operands'])for p in sorted(seen)if 'fs:'in rows[p]['operands']],FP_sites=[],unresolved_controls=[],unproved_or_tail_frontiers=frontiers,finite_normal_only=True)
 assert assigned==set(rows),(set(rows)-assigned,assigned-set(rows))
 owner_accesses=[];owned={o['role']:o for o in backings};teb=domain[0];scope=[]
 for index,(pc,address,value,width,write)in enumerate(source['accesses']):
  roles=[(o['role'],address-o['pointer'])for o in backings if o['pointer']<=address and address+width<=o['pointer']+o['extent']]
  if roles:assert len(roles)==1;role,offset=roles[0];owner_accesses.append(dict(source_access_index=index,PC=pc,role=role,offset=offset,width=width,writing=bool(write),value=value,borrowed=True))
  if not(0x20000000<=address and address+width<=0x20010000):scope.append(dict(source_access_index=index,PC=pc,address=address,width=width,writing=bool(write),value=value))
 fs=[dict(source_access_index=i,PC=a[0],offset=a[1]-teb,width=a[3],writing=bool(a[4]),value=a[2])for i,a in enumerate(source['accesses'])if teb<=a[1]<teb+8192]
 contracts=dict(root=0x5ae3e4,selected_slot=0x5e0040,instructions=[rows[p]for p in sorted(rows)],physical_entries=list(entries),borrowed_backings=[dict(role=o['role'],guest=o['pointer'],extent=o['extent'],initial_sha256=hashlib.sha256(bytes.fromhex(o['initial_hex'])).hexdigest(),ownership='Borrowed authentic post-DllMain backing; source retains identity; native must not free or replace it')for o in backings],borrowed_accesses=owner_accesses,source_nonstack_accesses=scope,FS_accesses=fs,normal_APIs=[dict(source_PC=a['source_PC'],API=a['API'],argc=a['argc'],source_target=a['target'],return_PC=a['return_PC'])for a in source['API_relations']],thread_contract=dict(source_manager=0x5f4cb008,manager_pointer_cell=0x5f4cb000,slot_cell=0x5f4cb03c,slot=1,source_TLS_index=3,current_thread_record_role='thread',current_thread_array_role='thread-array',cached_thread_object_role='thread-object',cached_thread_object_plus4=0,global_cache_cell=0x5f4cb040,global_result_role='global-object',current_process_thread=domain[1],source_TEB=teb,source_TLS_slot_address=domain[6],host_TLS_association_required=True,host_TLS_index_must_not_overwrite_source_index=True),field_writes=[x for x in owner_accesses if x['writing']],EH_contract=dict(trampoline=0x5f40107d,body=0x78001496,ret_PC=0x780014b4,source_return_PC=0x5f4010b5,FS_install_PC=0x780014a4,FS_restore_PC=0x5f4010cf,outer_caller_retained=True,special_return_must_not_pop_outer_caller=True),codepage_contract=dict(source_argument=0xfffffffd,GetACP=1252,current_codepage=1252,lock_index=25,lock_pointer_cell=0x7803708c,source_guest_CS24='Own exact authentic BEFORE opaque baseline; project only semantic fields from real native CS40',native_resource_rule='Initialize one owned native critical section and bind its current-thread/depth to source guest CS24. Never copy opaque source24 into host40; release/delete native association at fixture cleanup.'),unproved=['Lazy MFC callbacks5F4053FE/5F40B293','Empty manager/current-thread/TLS slot','Thread object+4 nonNULL branch','Global cache NULL/allocation/cleanup paths','Changed ACP/codepage/NLS conversion paths','Complete native source/provider fixture and connected131 acceptance'],initializer_credit=0)
 note='''# MFC1168 cached-root native handoff

Root 5AE3E4 has an authentic one-root normal/trace source gate. The closed normal execution is 142 physical instructions partitioned into thirteen entry bodies, four Windows API calls, one imported exception-frame registration, and two stores into the actual cached 4,240-byte provider object. The game object 7365A4 is a separate unchanged input and the root return value.

Native execution must retain the five genuine borrowed backing roles and source manager/slot/index/pointer cells. A real host TLS association needs its own host index, current-thread ownership, actual TlsGetValue call and typed source guest-pointer result; it cannot reuse source index3 as a host slot or replace the source thread data. The actual thread object+4 is NULL; the fallback global object already exists. No allocation or callback was observed.

The imported _EH_prolog installs FS:[0] at source780014A4, extends the source frame, and RETs at780014B4 to5F4010B5 without ending the outer5F4010AB call. The normal source later restores the actual preceding FS head at5F4010CF. Derive this exact geometry from source pushes/pops and caller frame; deny a generic special-return exception.

The physical _setmbcp(-3) body resolves GetACP1252 and returns through the unchanged-codepage path. CRT lock25 is a genuine initialized, borrowed source CS24. Native execution must create and own a distinct real native CS40 and transport only the declared source semantic depth/thread fields over the unchanged authentic opaque baseline; opaque bytes are not host structure input. Balanced Enter/Leave and cleanup must be measured independently.

Use game-normal-graphs.json for literal O0/O2 lifts; unknown targets remain explicit missing-block denials. Use contracts.json for every source operand role/offset, complete borrowed backing/tail equality and exact four import/cdecl contexts. The producing source proof reads genuine BEFORE pages/backings only. Full loaded MFC/CRT page endpoints and all 142 instruction spans already compare exactly. Native fixture should compare its own complete State/CPU/FX and memory against this same literal model with its own finite actual API responses; it must not seed original AFTER registers.

Lazy callbacks, altered TLS/count/slot/manager domains, global NULL, changed codepages, and allocation failure/cleanup are still open. No native or selected-initializer credit is granted by this contract preparation.
'''
 for name0,value in(('contracts.json',contracts),('game-normal-graphs.json',graphs)):
  q=out/name0;q.write_text(json.dumps(value,indent=2)+'\n');pin(q)
 q=out/'next-native.md';q.write_text(note);pin(q);pin(__file__);report=dict(passed=True,scope='Source-derived finite normal native contracts and thirteen literal graph preparation; no execution credit',source_validation=str(B/'validation-r6/report.json'),source_validation_sha256=sha(B/'validation-r6/report.json'),contracts=str(out/'contracts.json'),contracts_sha256=sha(out/'contracts.json'),graphs=str(out/'game-normal-graphs.json'),graphs_sha256=sha(out/'game-normal-graphs.json'),entries=13,instructions=142,borrowed_backings=5,borrowed_operands=len(owner_accesses),field_writes=len(contracts['field_writes']),new_allocations=0,initializer_credit=0,native_executed=False,files=PINS);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main(sys.argv[1])
