"""Read-only physical lookahead after candidate109; no execution or coverage credit."""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=ROOT/'reports/m4-fs-next-plan'/name;need(not out.exists(),'Fresh planning receipt');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();actual=sha(p);need(h is None or actual==h,'Exact frozen planning input '+str(p));pins[str(p)]=actual;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 pin(__file__);spec=importlib.util.spec_from_file_location('next_plan_pe',pin(ROOT/'tools/analysis/pe.py'));P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
 game=P.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 mfc=P.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes())
 crt=P.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
 frontier=read(ROOT/'reports/m4-joint-startup109-root/next-frontier-r1/report.json')
 need(frontier['passed']and frontier['counts']['remaining_roots']==35,'Candidate109 leaves exact35 nonzero table roots')
 remaining=read(ROOT/'reports/m4-joint-startup109-root/next-frontier-r1/remaining-roots.json',frontier['files'][str(ROOT/'reports/m4-joint-startup109-root/next-frontier-r1/remaining-roots.json')])
 graphs=read(ROOT/'reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json','da2482873e1678a0a2493ed7f60421440447c43e63826b53f2d5b09cf573ba5a')
 mfc_graphs=read(ROOT/'reports/m4-service-initializers/static-r1/MFC42.DLL.provider.json')
 crt_graphs=read(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/provider-graphs.json')
 candidate=read(ROOT/'reports/m4-fs-source/recovery-r3/instruction-contracts.json')
 need(len(candidate['selected_order'])==109,'Pending candidate109 basis only')
 native=read(ROOT/'reports/m4-fs-native/preparation-r3/report.json','5ee2a50044e6e887c54d49b7a574806a21be032c7352fefacfbe431397abb35e')
 need(native['normal_total_live_owners']==62,'Actual candidate109 resource geometry')
 for n in('mfc_operations.inc','locale_batch_operations.inc','session_impl.inc','mfc_contract.inc'):
  pin(ROOT/'reports/m4-fs-native/preparation-r3'/n)
 loader=read(ROOT/'reports/m4-mfc-source/loader-identity-r1/report.json','7925f659144954487b1b13d781d4aee48aa0b8d20887ce9ee8aa40ce7a12b09b')
 need(loader['MFC_free_export825']==0x5f401782,'Existing actual32 loader/export825 identity')
 table={(a,game.rva_u32(a-game.image_base))for a in range(0x5e0000,0x5e0244,4)}
 checked={}
 def physical(pe,rows,label):
  for row in rows:
   pc=row['pc'];raw=bytes.fromhex(row['bytes']);off,_=pe.rva_range(pc-pe.image_base,len(raw));need(pe.data[off:off+len(raw)]==raw,'Literal '+label+' PE bytes '+hex(pc))
   key=(label,pc);need(key not in checked or checked[key]==raw,'Unambiguous literal row');checked[key]=raw
 # Verify all35 source summaries independently, rather than trusting classification.
 for r in remaining:
  need((r['slot'],r['entry'])in table,'Real original table slot')
  for e in r['local_entries']:physical(game,graphs[str(e)]['instructions'],'game')
 vector_roots=[0x4ada90,0x4b12d0,0x4d84a0,0x5a7dc0];string_roots=[0x47f5b0,0x47f6d0,0x48f210];selected=vector_roots+string_roots
 chosen=[r for r in remaining if r['entry']in selected];need(len(chosen)==7 and all(not r['unresolved_controls']and not r['FP_sites']for r in chosen),'Seven closed integer normal root closures')
 entries=sorted({e for r in chosen for e in r['local_entries']});allrows={i['pc']:i for e in entries for i in graphs[str(e)]['instructions']}
 oldpcs={i['pc']for i in candidate['instructions']}
 newrows=[i for pc,i in sorted(allrows.items())if pc not in oldpcs]
 frames=[]
 for r in chosen:
  fs=sorted({i['pc']:i for e in r['local_entries']for i in graphs[str(e)]['instructions']if 'fs:'in i['operands']}.values(),key=lambda i:i['pc'])
  need(len(fs)==3 and fs[0]['mnemonic']=='mov'and fs[1]['mnemonic']=='mov'and fs[2]['mnemonic']=='mov','One literal normalFSframe for each chosen root')
  helper=fs[0]['pc']-7;handler=game.rva_u32(helper+3-game.image_base)
  frames.append(dict(root=r['entry'],helper_entry=helper,handler=handler,read=fs[0]['pc'],install=fs[1]['pc'],restore=fs[2]['pc'],bytes=12))
 mfc540=next(r for r in mfc_graphs['requested_exports']if r['requested']==540)
 need(mfc540['local_entries']==[0x5f4020b4,0x5f4020c4]and mfc540['unique_instructions']==10 and not mfc540['nested_imports']and not mfc540['unresolved_controls'],'Small exact MFC540 integer provider')
 provider540={i['pc']:i for e in mfc540['local_entries']for i in mfc_graphs['graphs'][str(e)]['instructions']};physical(mfc,provider540.values(),'MFC540')
 need(next(e for e in mfc.exports()if e['ordinal']==540)['rva']==0x20b4,'Physical MFCordinal540 export target')
 free825=mfc_graphs['graphs'][str(0x5f401782)]['instructions'];physical(mfc,free825,'MFC825')
 null_pcs=[0x78001390,0x78001391,0x78001393,0x78001395,0x7800139a,0x7800139f,0x780013a5,0x780013a6,0x780013ad,0x780013b0,0x780013b1,0x780013b2,0x780013b3,0x780013b6,0x780013b8,0x78001416,0x78001419,0x78001420,0x78001421,0x78001422,0x78001423,0x78001424]
 freegraph={i['pc']:i for i in crt_graphs[str(0x78001390)]['instructions']};nullrows=[freegraph[p]for p in null_pcs];physical(crt,nullrows,'CRTfreeNULL')
 need(freegraph[0x780013b8]['operands'].startswith('0x78001416'),'Genuine literal NULL branch skips HeapFree and TLS/mode reads')
 def virtual(pe,address,n):
  rva=address-pe.image_base
  for s in pe.sections:
   d=rva-s['virtual_address']
   if 0<=d and d+n<=max(s['virtual_size'],s['raw_size']):
    data=b''.join(bytes([pe.data[s['raw_offset']+d+k]])if d+k<s['raw_size']else b'\0'for k in range(n))
    return dict(address=address,section=s['name'],file_backed=d+n<=s['raw_size'],raw_hex=data.hex(),raw_DWORD=struct.unpack('<I',data)[0]if n==4 else None,post_DllMain_value_known=False)
  raise ValueError('Mapped input bound')
 nil=virtual(mfc,0x5f4ccb54,4)
 game_slots=[dict(slot=a,raw=game.rva_u32(a-game.image_base),requested_ordinal=o)for a,o in((0x5bb4c8,825),(0x5bb454,540))]
 need([r['raw']for r in game_slots]==[0x80000339,0x8000021c],'Exact original game import ordinal cells remain raw and require read-time projection')
 allocs=[dict(root=0x4ada90,call=0x4ad87c,request=768,object=0x60b110,publication=0x60b114,publication_pc=0x4ad90c,capacity_pc=0x4ad8eb,free_CALL=0x4ad8d8),dict(root=0x4b12d0,call=0x4b11da,request=136,object=0x60b240,publication=0x60b248,publication_pc=0x4b1237,capacity_pc=0x4b1223,free_CALL=0x4b1210),dict(root=0x4b12d0,call=0x4b1257,request=64,object=0x60b240,publication=0x60b258,publication_pc=0x4b12ab,capacity_pc=0x4b1292,free_CALL=0x4b1287),dict(root=0x4d84a0,call=0x4d82bc,request=64,object=0x60b580,publication=0x60b584,publication_pc=0x4d8314,capacity_pc=0x4d82f7,free_CALL=0x4d82ec),dict(root=0x5a7dc0,call=0x5a879c,request=256,object=0x736558,publication=0x73655c,publication_pc=0x5a87fa,capacity_pc=0x5a87e1,free_CALL=0x5a87cf)]
 for r in allocs:
  call=allrows[r['call']];free=allrows[r['free_CALL']]
  need(call['mnemonic']==free['mnemonic']=='call'and call['operands'].startswith('0x5abd26')and free['operands'].startswith('0x5abd1a'),'Literal positive allocate and NULL-free game thunks')
  pushes=sorted((i for i in allrows.values()if i['mnemonic']=='push'and i['pc']<r['call']and r['call']-i['pc']<64),key=lambda i:i['pc'])
  need(pushes and pushes[-1]['operands']==hex(r['request']),'Exact literal request is final PUSH before allocator CALL')
  need(allrows[r['publication_pc']]['mnemonic']=='mov'and allrows[r['capacity_pc']]['mnemonic']=='mov','Exact literal pointer publication and capacity stores')
 def string_input(root):
  r=next(r for r in chosen if r['entry']==root);rs={i['pc']:i for e in r['local_entries']for i in graphs[str(e)]['instructions']};calls=[i for i in rs.values()if i['mnemonic']=='call'and i['operands'].startswith('0x48eb10')]
  need(len(calls)==1,'One original string base constructor')
  call=calls[0];pushes=[i for i in rs.values()if call['pc']-12<=i['pc']<call['pc']and i['mnemonic']=='push'and i['operands'].startswith('0x5e')]
  need(len(pushes)==1,'Exact literal nonzero string argument');address=int(pushes[0]['operands'],16);off,end=game.rva_range(address-game.image_base,1);stop=game.data.find(b'\0',off,min(end,off+256));need(stop>=off,'Bounded actual source NUL input')
  return dict(root=root,constructor_call=call['pc'],source=address,source_bytes_hex=game.data[off:stop+1].hex(),NUL_inclusive_bytes=stop+1-off,actual_duplicate_count_unexecuted=True)
 inputs=[string_input(r)for r in string_roots]
 plan=dict(recommended='Seven-root normalFS container/string batch (+7→candidate116), two parallel source families with one integration. If post-DllMain MFCnil input remains unresolved, seal four-vector subset (+4→candidate113) without waiting for new service infrastructure.',root_gain=7,root_order_by_real_table=[r['entry']for r in sorted(chosen,key=lambda r:r['slot'])],vector_roots=vector_roots,string_roots=string_roots,game_local_entry_union=entries,game_rows=len(allrows),game_PE_bytes=sum(i['size']for i in allrows.values()),new_game_rows_against_candidate109=len(newrows),new_game_PE_bytes=sum(i['size']for i in newrows),new_provider_entries=mfc540['local_entries'],new_provider_rows=len(provider540),new_provider_bytes=sum(i['size']for i in provider540.values()),normal_frames=frames,positive_allocation_static_sites=allocs,string_inputs=inputs,MFC540_nil_input=nil,owning_game_import_slots=game_slots,expected_new_positive_owners_before_execution=8,expected_total_live_owners_before_execution=70,actual_new_owner_count_claimed=False,
 gaps=[dict(priority=1,behavior='Reach game MFC825 thunk5ABD1A',first_frontier_pc=0x5abd1a,slot=0x5bb4c8,raw=0x80000339,required='Exact ordinal825 physical/actual-loader identity, read-time raw→target projection, preserve true original CALL frame through JMP, active free dispatch witness.'),dict(priority=2,behavior='Normal genuine MFC825→CRTfree(NULL)',first_guard='MFC free entry requires exact live whole private object and generation',required='Separate null source-free witness with original argument0/frame and exact source CRTbranch780013B8→78001416; no native HeapFree call, no owner generation or success invented.'),dict(priority=3,behavior='MFC540 small data-copy constructor',entry=0x5f4020b4,game_thunk=0x5abdb0,game_slot=0x5bb454,required='Lift both10-row physical functions, actual32 post-DllMain DWORD at5F4CCB54 and pointee provenance/whole observed input, map narrow correct MFCpage. Do not manufacture nil pointer; preserve raw game import.'),dict(priority=4,behavior='Finite resource bound',current_live_bound=64,current_actual_live=62,required='Derive exact fresh persistent counts/maximum (static estimate70 including3duplicates), raise only finite bound in new derivative; do not modify accepted109.'),dict(priority=5,behavior='New source object/FS admissions',required='Seven canonical normal12B frame descriptors plus exact static MFCallocation publication/capacity joins; add three string input specs/lifetimes and MFCnil borrowed-data relation. Do not enable all vector-growth/handler branches.')],
 execution_plan=['Source lane: freeze exact7-root rows/thunks/tail entries and callback attribution, derive BEFORE positive/null-free/object/publication geometry, observe loaded540nil provenance, execute original116 persistent sequence. Original counts/API/FS machine capture are sole execution evidence.','Native lane: versioned derivative accepted109, exact825game import and separate literal NULL-free path, two literal540provider bodies, seven normalFS descriptors, five positive request specs+three strdup specs, finite ownership bound. Retain all103/109 machine/owner/checkpoint ABI.','Integration: single connected116 O0/O2 build/canonical sequence, carry original144relative ordering and source-verified cleanup; independent BEFORE-only fullState/CPU/FX/ENV, whole mapped pages, allocation/FS/import/callback and raw owner relation checks. No separate large replay for each helper.','Controls: isolate this7-root family after genuine bootstrap; actualfree0 must preserve frame/FS/machine and invoke zero HeapFree APIs; changed825/540import and nil-data refuse exactcause; ROcapacity/publication field proves retained preceding stores; ROFSinstall/restore, fullnativepadding corruption, unchanged sameSession retry and strict authored caller boundaries; independently measure native HeapDestroy. Reuse existing reader/writer/control framework.'],
 delayed_families=[dict(roots=[0x411010,0x4dc140,0x500660,0x5968f0],missing='MSVCP_Lockit shared critical-section init/atexit/atomic/Sleep loop; include morecomplex4B7F70onlyafterliteral reached dependencies. This is a later counted4-root or5-root batch.'),dict(roots=[0x4df610,0x4e0710,0x4e0810],missing='sprintf variadic formatting and strrchr provider integer closure plus owned path buffers; next3-root batch after this7, rather than fullgeneric libc.'),dict(roots=[0x5ae3e4],missing='MFC1168 TLS/LocalAlloc/LocalReAlloc/critical-section closure plus CRTsetmbcp; 391staticMFCrows and23nestedimports, sixindirect controls; substantially less count per new service.')],
 scope='Physically authenticated static normal-path execution plan only. Candidate109 acceptance still pending, no constructor/allocator/free/provider/API execution performed by this report; original/null-owner/after-state facts require fresh actual captures. Exception handlers, vector relocation of nonemptyold buffers, generic callback dispatch and fullgame/menu remain excluded.')
 for fname,value in(('plan.json',plan),('physical-game-rows.json',list(allrows.values())),('physical-MFC540-rows.json',list(provider540.values())),('physical-CRTfreeNULL-rows.json',nullrows),('positive-allocation-sites.json',allocs),('string-inputs.json',inputs)):
  p=out/fname;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
 report=dict(passed=True,scope=plan['scope'],recommended_root_gain=7,fallback_root_gain=4,candidate109_pending=True,counts=dict(all_remaining_physically_checked_rows=sum(label=='game'for label,pc in checked),chosen_game_entries=len(entries),chosen_game_rows=len(allrows),chosen_game_bytes=plan['game_PE_bytes'],new_game_rows=plan['new_game_rows_against_candidate109'],new_MFC540_bodies=2,new_MFC540_rows=10,new_MFC540_bytes=plan['new_provider_bytes'],new_normal_FS_frames=7,positive_MFC_static_CALL_sites=5,normal_NULLfree_static_CALL_sites=5,new_nonzero_strdups_static_sites=3),files=pins,original_executed=False,native_executed=False,API_result_injection=False,initializer_credit=0,accepted_files_modified=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),counts=report['counts'],nil=nil,string_inputs=inputs)))
if __name__=='__main__':main(sys.argv[1])
