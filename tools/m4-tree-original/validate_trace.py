"""Authenticate actual bounded instruction cells/control against physical source.

Owner replay starts at the genuine API initial backing. Candidate final bytes
are compared only after the complete measured instruction write history.
"""
from pathlib import Path
import collections, hashlib, importlib.util, json, struct, sys, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-tree-original'
PINS={}
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
    if not v:raise ValueError(m)
def pin(p,h=None):
    p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical identity '+str(p));need(str(p) not in PINS or PINS[str(p)]==v,'Stable identity');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def u32(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def cpu(context):
    return [u32(context,o)[0] for o in (176,172,168,164,196,180,160,156,192,184)]
def project_cpu(c):
    c=list(c);c[8]&=~0x10100;return c
def main(execution_path,execution_sha,prefix_path,prefix_sha,name):
    out=BASE/name;need(not out.exists(),'Fresh additive trace gate');out.mkdir(parents=True)
    passed=False;counts=collections.Counter();events=[];accesses=[];controls=[];imports=[];scratch=[];publications=[];insertions=[];owner_replays=[];bundle=None
    try:
        execution=read(execution_path,execution_sha);need(execution['passed'],'Actual trace worker exited successfully')
        prefix=read(prefix_path,prefix_sha);need(prefix['passed'] and prefix['execution_sha256']==execution_sha,'Same actual prefix raw validation')
        build=read(execution['build_path'],execution['build_sha256']);need(build['passed'],'Exact successful x86 build');pin(build['worker'],build['worker_sha256'])
        prep_path=Path(build['preparation']);prep=read(prep_path/'report.json',build['preparation_sha256'])
        need(prep['trace_descriptors']==632 and prep['trace_event_bytes']==1656 and prep['physical_after_effects_supplied'] is False,'Exact bounded trace admission')
        for p,h in prep['files'].items():pin(p,h)
        descriptors=read(prep_path/'trace_points.json');points={d['pc']:d for d in descriptors};need(len(points)==632,'Unique physical instruction points')
        sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
        game=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
        mfc=PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes())
        for d in descriptors:
            pe=mfc if d['pc']>=0x5f400000 else game;raw=bytes.fromhex(d['bytes_hex']);offset,_=pe.rva_range(d['pc']-pe.image_base,len(raw));need(pe.data[offset:offset+len(raw)]==raw,'Exact whole physical instruction bytes')
        contract=read(ROOT/'reports/m4-tree-source/recovery-r1/instruction-contracts.json')
        reg_calls={r['pc']:r for r in contract['register_import_calls']}
        scratch_contract={r['CALL_pc']:r for r in contract['Lockit_scratch_contracts']}
        fs_contract=read(ROOT/'reports/m4-tree-source/recovery-r1/FS-frame-contracts.json')
        fs_by_read={r['read']:r for r in fs_contract}
        normal_owners=read(Path(prefix_path).parent/'actual-owners.json')
        normal_locks=read(Path(prefix_path).parent/'actual-Lockit-boundaries.json')
        originals={o['index']:bytearray.fromhex(o['initial_hex']) for o in normal_owners}
        final_owner={o['index']:o for o in normal_owners};owner_pointer={o['pointer']:o for o in normal_owners}
        need(len(originals)==prefix['counts']['actual_allocations'],'Same genuine owner inventory')
        s=importlib.util.spec_from_file_location('tree_trace_direct',pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
        bundle=m.DirectSet(Path(execution['original_capture']),pin)
        count=u32(bundle.data('tree-trace/count.bin'))[0];raw=bundle.data('tree-trace/events.bin')
        need(0<count<=prep['trace_event_bound'] and len(raw)==count*1656,'Actual complete bounded trace extent')
        phase=bundle.data('phase/0/0.bin');pages=prep['observed_pages'];map_page=bytearray(phase[2276+pages.index(0x60b000)*4096:2276+(pages.index(0x60b000)+1)*4096])
        fs_raw=bundle.data('phase/0/0/fs-events.bin');fs_rows=[fs_raw[i:i+1216] for i in range(0,len(fs_raw),1216)]
        fs_cursor=0;lock_cursor=0;previous=None;previous_owners=0;frame_stack=[];next_frame=0;definitions={};last_LEA={};last_store={};active_insertion=None;allocation_calls={};call_counts=collections.Counter()
        regs=['eax','ecx','edx','ebx','esp','ebp','esi','edi'];write_counts=collections.Counter()
        for index in range(count):
            block=raw[index*1656:(index+1)*1656];header=u32(block,0,8);i,pc,nextpc,kind,ncells,owners,exception_eip,opcode=header
            need(i==index and pc in points,'Every actual event names a unique admitted source PC');d=points[pc]
            need((kind,ncells,opcode)==(d['kind'],len(d['cells']),d['opcode']) and exception_eip==pc+1,'Actual first-opcode debugger entry metadata')
            before_context=block[32:748];after_context=block[748:1464];before=cpu(before_context);after=cpu(after_context)
            need(before[9]==pc+1 and after[9]==nextpc,'Retained raw debugger EIPs')
            need(previous_owners<=owners<=previous_owners+1 and owners<=len(originals),'Monotonic actual allocation generations');previous_owners=owners
            event=dict(index=index,PC=pc,mnemonic=d['mnemonic'],operands=d['operands'],instruction_kind=kind,next_PC=nextpc,owner_count_before=owners,raw_debugger_before_cpu=before,raw_debugger_after_cpu=after,CONTEXT_before_sha256=hashlib.sha256(before_context).hexdigest(),CONTEXT_after_sha256=hashlib.sha256(after_context).hexdigest(),cells=[])
            projected_before=project_cpu(before);projected_before[9]=pc;projected_after=project_cpu(after)
            if previous is not None and previous['next_PC']==pc and previous['instruction_kind']==0:
                prior=project_cpu(previous['raw_debugger_after_cpu']);prior[9]=pc
                need(prior==projected_before,'Actual single instruction continuation into next source breakpoint')
                counts['direct_source_CPU_continuations']+=1
            cells=[]
            for ci,md in enumerate(d['cells']):
                words=u32(block,1464+ci*48,12);address,width,rd,wr,owner,generation,bval,aval,bvalid,avalid,segment,offset=words
                expected=(md['displacement']+sum(projected_before[r]*v for r,v in enumerate(md['coefficients'])))&0xffffffff
                need((address,width,rd,wr,segment)==(expected,md['width'],md['read'],md['write'],0) and bvalid==avalid==1,'Actual complete affine source cell bytes before and after')
                cell=dict(event=index,PC=pc,operand=ci,address=address,width=width,read=rd,write=wr,owner_index=None if owner==0xffffffff else owner,generation=generation,owner_offset=None if offset==0xffffffff else offset,before_value=bval,after_value=aval)
                if owner!=0xffffffff:
                    need(owner<owners and generation==owner+1 and offset+width<=final_owner[owner]['capacity'] and address==final_owner[owner]['pointer']+offset,'Exact actual complete live owner generation')
                    current=originals[owner];need(bytes(current[offset:offset+width])==bval.to_bytes(width,'little'),'Actual owner before/read agrees with carried full initial backing and prior measured stores')
                    if wr:
                        current[offset:offset+width]=aval.to_bytes(width,'little');write_counts[owner]+=1;counts['actual_owned_writes']+=1
                    if rd:counts['actual_owned_reads']+=1
                    if offset+width>final_owner[owner]['request']:counts['capacity_tail_accesses']+=1
                else:
                    for o in range(owners):need(not(final_owner[o]['pointer']<=address<final_owner[o]['pointer']+final_owner[o]['capacity']),'A live owned cell cannot evade actual generation classification')
                if 0x60b000<=address and address+width<=0x60c000:
                    local=address-0x60b000;need(bytes(map_page[local:local+width])==bval.to_bytes(width,'little'),'Whole shared tree page actual source carry')
                    if wr:map_page[local:local+width]=aval.to_bytes(width,'little')
                if rd:counts['actual_memory_reads']+=1
                if wr:
                    counts['actual_memory_writes']+=1
                    for k in range(width):last_store[address+k]=dict(event=index,PC=pc,value=(aval>>(k*8))&255,store_address=address,store_width=width,byte_offset=k)
                cells.append(cell);event['cells'].append(cell);accesses.append(cell)
                if wr and width==4 and aval in owner_pointer and owner_pointer[aval]['index']<owners:
                    publications.append({**cell,'published_owner_index':owner_pointer[aval]['index'],'published_generation':owner_pointer[aval]['generation']})
            if kind==1:
                need(fs_cursor<len(fs_rows),'Actual traced FS source event has raw semantic witness');fs=fs_rows[fs_cursor];fw=u32(fs,0,8)
                raw_before=list(u32(fs,32,10));raw_before[8]&=~0x10100
                need(fw[2]==pc and raw_before==projected_before,'Debugger source entry joins the actual complete raw FS operation')
                event['raw_FS_event']=fs_cursor;fs_cursor+=1;counts['actual_FS_observer_JMPs']+=1
            else:
                mnemonic=d['mnemonic'];fallthrough=pc+d['width'];control=None
                if mnemonic in ('call','jmp'):
                    operand=d['operands'];target=int(operand,16) if operand.startswith('0x') else projected_before[regs.index(operand)] if operand in regs else next(c['before_value'] for c in cells if c['read'])
                    need(nextpc==target,'Actual CALL/JMP target derives actual loaded operand');control=dict(event=index,PC=pc,kind=mnemonic,target=target,return_PC=fallthrough if mnemonic=='call' else None)
                    if mnemonic=='call':
                        call_counts[pc]+=1;need(after[4]==before[4]-4 and any(c['address']==before[4]-4 and c['write'] and c['after_value']==fallthrough for c in cells),'Actual CALL full return-word/frame publication')
                elif mnemonic in ('je','jne'):
                    zf=bool(before[8]&0x40);taken=zf if mnemonic=='je' else not zf;target=int(d['operands'],16)
                    need(nextpc==(target if taken else fallthrough),'Actual branch follows genuine incoming ZF');control=dict(event=index,PC=pc,kind=mnemonic,target=target,taken=taken,actual_next_PC=nextpc)
                elif mnemonic=='ret':
                    target=next(c['before_value'] for c in cells if c['read']);cleanup=int(d['operands'],16) if d['operands'] else 0
                    need(nextpc==target and after[4]==before[4]+4+cleanup,'Actual RET target and complete cleanup from genuine stack read');control=dict(event=index,PC=pc,kind='ret',target=target,cleanup=cleanup)
                else:need(nextpc==fallthrough,'Actual noncontrol source instruction advances exact width')
                if control:controls.append(control)
                if mnemonic=='lea':
                    destination=d['operands'].split(',')[0];need(destination in regs,'Declared source LEA destination');last_LEA[destination]=dict(event=index,PC=pc,value=after[regs.index(destination)],raw_before_cpu=before,raw_after_cpu=after)
                if pc==0x4bab00:
                    active_insertion=dict(invocation=len(insertions),entry_event=index,entry_ESP=before[4],owners_before=owners,events=[]);insertions.append(active_insertion)
                if active_insertion is not None:
                    if any(c['owner_index'] is not None and c['write'] for c in cells):active_insertion['events'].append(index)
                    if pc==0x4bae1f:
                        active_insertion['RET_event']=index;active_insertion['owners_after']=owners;active_insertion['final_live_objects']={str(o):bytes(originals[o]).hex() for o in range(owners)};active_insertion=None
                for rc in reg_calls.values():
                    if pc==rc['definition_PC']:
                        value=after[regs.index(rc['register'])];need(value==rc['provider'] and any(c['address']==rc['IAT'] and c['read'] and c['before_value']==value for c in cells),'Actual loaded owning register import definition');definitions[rc['register']]=dict(event=index,PC=pc,value=value,IAT=rc['IAT'])
                if pc in reg_calls:
                    rc=reg_calls[pc];definition=definitions.get(rc['register']);need(definition and definition['PC']==rc['definition_PC'] and before[regs.index(rc['register'])]==rc['provider']==nextpc,'Actual retained nonvolatile import reaches true provider')
                    imports.append(dict(event=index,PC=pc,register=rc['register'],target=nextpc,definition=definition,raw_before_cpu=before,raw_after_cpu=after))
                if pc in scratch_contract:
                    need(lock_cursor*3<len(normal_locks),'Every actual source Lockit CALL has raw provider witness');entry=normal_locks[lock_cursor*3];raw_cpu=list(entry['cpu']);raw_cpu[8]&=~0x10100
                    need(raw_cpu[:9]==projected_after[:9] and raw_cpu[9]==nextpc,'Actual CALL frame and registers join raw genuine Lockit entry')
                    lea=last_LEA.get('ecx');need(lea and lea['value']==before[1] and lea['PC'] in scratch_contract[pc]['source_LEA_pcs'],'Actual same-thread scratch comes from exact reached source LEA')
                    affine=before[1]-after[4];need(affine in scratch_contract[pc]['ECX_minus_target_entry_ESP'],'Actual reached source scratch affine')
                    scratch.append(dict(event=index,CALL_PC=pc,entry_snapshot=lock_cursor*3,target=nextpc,scratch_ECX=before[1],target_entry_ESP=after[4],affine=affine,source_LEA=lea,raw_before_cpu=before,raw_after_cpu=after));lock_cursor+=1
                if pc in (0x4ba306,0x4ba33c,0x4bab32):allocation_calls[(pc,call_counts[pc])]=dict(event=index,CALL_PC=pc,invocation=call_counts[pc],source_frame=after[4],return_PC=fallthrough)
            previous=event;events.append(event)
        need(fs_cursor==len(fs_rows) and lock_cursor*3==len(normal_locks),'Complete trace/raw FS and Lockit seam joins')
        need(not active_insertion and not frame_stack,'Every actual insertion returned normally')
        for o in normal_owners:
            need(bytes(originals[o['index']]).hex()==o['final_hex'],'Whole owned capacity derives complete actual source write history')
            allocation=allocation_calls.get((o['CALL_pc'],o['site_invocation']));need(allocation and allocation['source_frame']==o['source_frame'],'Actual repeated source CALL frame binds exact allocator generation')
            owner_replays.append(dict(index=o['index'],generation=o['generation'],pointer=o['pointer'],request=o['request'],capacity=o['capacity'],source_CALL=allocation,measured_writes=write_counts[o['index']],initial_hex=o['initial_hex'],derived_final_hex=bytes(originals[o['index']]).hex()))
        need(map_page==phase[178404+pages.index(0x60b000)*4096:178404+(pages.index(0x60b000)+1)*4096],'Whole shared tree page derives all actual source writes without AFTER seed')
        need(events[0]['PC']==0x4b7f70 and events[-1]['PC']==0x4b7f9d and events[-1]['next_PC']==0x410a80,'Actual complete bounded root path to raw capture broker')
        counts.update(actual_instructions=count,physical_source_points=len(points),actual_unique_reached_PCs=len({e['PC'] for e in events}),actual_control_events=len(controls),actual_register_import_CALLs=len(imports),actual_Lockit_scratch_CALLs=len(scratch),actual_insertions=len(insertions),actual_owner_generations=len(normal_owners),actual_pointer_publications=len(publications),whole_owner_capacity_bytes=sum(o['capacity'] for o in normal_owners),whole_shared_tree_page_bytes=4096)
        counts['actual_rotation_ctor_4bad8f']=call_counts[0x4bad8f]
        counts['actual_mirror_recolor_4bad09']=sum(e['PC']==0x4bad09 for e in events)
        counts['actual_MFC_823_entries']=sum(e['PC']==0x5f401ea0 for e in events)
        counts['actual_MFC_CALL_EBX']=call_counts[0x5f401eb5]
        need(counts['capacity_tail_accesses']==0,'No observed source access to allocator capacity tail')
        passed=True
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        if bundle is not None:bundle.close()
        for filename,value in [('actual-instructions.json',events),('actual-source-access-ledger.json',accesses),('actual-controls.json',controls),('actual-register-imports.json',imports),('actual-Lockit-scratch.json',scratch),('actual-pointer-publications.json',publications),('actual-insertions.json',insertions),('actual-owner-byteflows.json',owner_replays)]:
            (out/filename).write_text(json.dumps(value,indent=2)+'\n');pin(out/filename)
        pin(__file__)
        report=dict(passed=passed,scope='Genuine bounded debugger instruction reads/writes/control and whole original owner/shared-tree byteflows. Debugger CONTEXT/TF/RF are explicit observer metadata; frozen normal raw CPU/FX/ENV/CS/FS remains distinct. No broad125/native credit.',execution_sha256=execution_sha,prefix_validation_sha256=prefix_sha,counts=dict(counts),debugger_CONTEXT_is_raw_hardware_FX_claim=False,observer_flags_projection_mask=0x10100,actual_final_bytes_supply_derivation=False,predicted_paths_supply_observations=False,reader_closed=True,initializer_credit=False,files=PINS)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])
