"""Exact three-root formatting frontier; static evidence only, no credit.

Reuse immutable instruction inventory, authenticate every selected byte against
the source PE, and recover bounded provider entry graphs from its decoder ledger.
No inherited capture, guest execution, host formatter or guessed allocation.
"""
from pathlib import Path
import hashlib, importlib.util, json, re, struct, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
ROOTS=(0x4df610,0x4e0710,0x4e0810)
PARAMS={0x4df610:(0x5e01c8,0x4df620,0x4df640,0x60b5e0,0x5e959c,0x5cd428,0x4df680,40),0x4e0710:(0x5e01cc,0x4e0720,0x4e0740,0x60b630,0x5e9738,0x5cd440,0x4e07b0,36),0x4e0810:(0x5e01d0,0x4e0820,0x4e0740,0x60b608,0x5e9740,0x5cd440,0x4e0850,36)}
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
    if not v:raise ValueError(s)
def main(name):
    out=R/'reports/m4-formatting-frontier'/name;need(not out.exists(),'Fresh static formatting recovery');out.mkdir(parents=True);pins={}
    def pin(p,h=None):
        p=Path(p).resolve();need(p.suffix.lower()!='.mwb','No capture payload reader');a=sha(p);need(h is None or a==h,'Exact formatting source identity '+str(p));need(str(p)not in pins or pins[str(p)]==a,'Consistent frozen source');pins[str(p)]=a;return p
    def read(p,h=None):return json.loads(pin(R/p,h).read_bytes())
    def emit(n,obj):
        p=out/n;p.write_text(json.dumps(obj,indent=2)+'\n');pin(p);return p
    def module(p,n):
        s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
    accepted=read('reports/m4-joint-startup124-root/acceptance-r1/report.json','6bd35e55bca15e1a0537044bf59a1c3ced5e9ef8b30a8a169b71c78824811462');need(accepted['passed'],'Accepted124 baseline')
    frontier=read('reports/m4-joint-startup124-root/next-frontier-r1/remaining-roots.json');selected=[x for x in frontier if x['entry']in ROOTS];need(tuple(x['entry']for x in selected)==ROOTS,'Existing144 frontier contains coherent rooted formatting group')
    allgraphs=read('reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json','da2482873e1678a0a2493ed7f60421440447c43e63826b53f2d5b09cf573ba5a')
    entries=sorted({e for r in selected for e in r['local_entries']});graphs={e:allgraphs[str(e)]for e in entries};need(len(graphs)==13 and not any(g['unresolved_controls']or g['FS_sites']or g['FP_sites']for g in graphs.values()),'Thirteen complete integer game entry graphs, no FS or FP')
    old=read('reports/m4-lockit-source/recovery-r1/instruction-contracts.json','c102e277742f2cd6e2a352f9e40f44f7d7d2ea1107d8bde242d103b586e75f25');oldrows={x['pc']for x in old['instructions']};retained={0x5ac110,0x5ac140,0x5ac580};new={e:g for e,g in graphs.items()if e not in retained};need(len(new)==10,'Ten additive game bodies and three already accepted registration bodies')
    A=module(R/'tools/m4-service-initializers/recover.py','format_physical_graphs');D=module(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py','format_instruction_contracts');game=A.Module(pin(R/'MW3/Mech3.exe',A.IDENTITIES['MW3/Mech3.exe']));crt=A.Module(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',A.IDENTITIES['local/mw3-staged/Shared_DLLs/MSVCRT.DLL']))
    def raw(pe,a,n):return pe.read(pe.rva_range(a-pe.image_base,n)[0],n)
    rows={x['pc']:x for g in graphs.values()for x in g['instructions']}
    def contract(pe,row):
        code=bytes.fromhex(row['bytes']);need(raw(pe,row['pc'],len(code))==code,'Every selected physical instruction '+hex(row['pc']))
        op=row['mnemonic'];args=row['operands'].split(' <')[0];repeat=None
        if op in('rep','repe','repz','repne','repnz'):repeat=op;op,args=args.split(None,1)
        normalized=dict(pc=row['pc'],width=row['size'],bytes_hex=row['bytes'],mnemonic=op,operands=args)
        if repeat:normalized['repeat']=repeat
        return D.instruction_contract(normalized)
    decoded=[contract(game.image,r)for r in sorted(rows.values(),key=lambda r:r['pc'])];need(len(rows)==199 and sum(r['size']for r in rows.values())==611,'Complete199 unique game rows/611 source bytes')
    # Parse the immutable existing provider decoder ledger, validating only
    # selected graphs below. A lookup row is never accepted as source bytes.
    lookup=pin(R/'reports/m4-service-initializers/static-r1/MSVCRT.DLL.linear-lookup.txt')
    for line in lookup.read_text().splitlines():
        match=A.ROW.match(line)
        if not match:continue
        asm=re.sub(r'\s+',' ',match[3].strip());op,_,args=asm.partition(' ');pc=int(match[1],16);code=bytes.fromhex(match[2]);need(pc not in crt.rows,'Unique static provider decode boundary');crt.rows[pc]=dict(pc=pc,size=len(code),bytes=code.hex(),mnemonic=op,operands=args)
    providers={};exports=[]
    for name in('strrchr','sprintf'):
        hits=[x for x in crt.exports if name in x['names']];need(len(hits)==1,'Unique exact named provider export '+name);x=hits[0];entry=crt.base+x['rva'];need(not x.get('forwarder'),'Direct exact provider export');g=A.walk(crt,entry);providers[entry]=g;exports.append(dict(name=name,entry=entry,ordinal=x['ordinal'],rva=x['rva'],source_bytes=sum(r['size']for r in g['instructions']),instructions=g['instruction_count'],local_decode_closed=g['local_decode_closed'],physical_export_observed=True,runtime_loaded_target_observed=False))
    need(providers[0x780264a9]['instruction_count']==23 and providers[0x780264a9]['local_decode_closed'],'Entire literal strrchr CFG closes in23 instructions')
    providerrows={x['pc']:x for g in providers.values()for x in g['instructions']};providerdecoded=[contract(crt.image,r)for r in sorted(providerrows.values(),key=lambda r:r['pc'])]
    # Record the exact computed output dispatch as a pending runtime contract.
    # Every apparent failure/other-format branch remains explicitly unreached.
    table=raw(crt.image,0x780103fa,32);targets=struct.unpack('<8I',table);dispatchgraphs={e:A.walk(crt,e)for e in(0x7800fc9b,*targets)}
    outputrows={x['pc']:x for g in dispatchgraphs.values()for x in g['instructions']}
    for r in outputrows.values():need(raw(crt.image,r['pc'],r['size'])==bytes.fromhex(r['bytes']),'Exact bounded output frontier row')
    need(bytes.fromhex(crt.rows[0x7800fcef]['bytes'])==bytes.fromhex('ff2485fa030178')and bytes.fromhex(crt.rows[0x7800fce7]['bytes'])==bytes.fromhex('83f807'),'Physical8-way EAX bound and indirect dispatch table')
    unresolved={json.dumps(x,sort_keys=True)for g in dispatchgraphs.values()for x in g['unresolved_controls']};dispatch=dict(entry=0x7800fc9b,table=0x780103fa,table_hex=table.hex(),table_entries=list(targets),index_max=7,index_bound_PC=0x7800fce7,index_branch_PC=0x7800fced,JMP_PC=0x7800fcef,all_branch_frontier_instructions=len(outputrows),unresolved_controls=[json.loads(s)for s in sorted(unresolved)],full_formatter_closed=False,reached_indices_observed=False,normal_literal_format='%s%s',numeric_wide_locale_paths_admitted=False)
    def string(a):
        b=bytearray()
        for k in range(128):
            c=raw(game.image,a+k,1);b+=c
            if c==b'\0':return dict(address=a,bytes_hex=b.hex(),text=b[:-1].decode('ascii'),bytes=len(b))
        raise ValueError('Bounded physical string lacksNUL')
    strings=[string(a)for a in(0x5e959c,0x5e9738,0x5e9740,0x5e9580,0x5e37f0,0x5e9558,0x5e9524,0x5e953c)];text={s['address']:s['text']for s in strings};need(text[0x5e9580]=='.zrd'and text[0x5e37f0]=='%s%s','Literal suffix and exact two-pointer variadic format')
    rootrows=[]
    for entry in ROOTS:
        slot,wrapper,ctor,obj,filename,vtable,callback,extent=PARAMS[entry];need(struct.unpack('<I',raw(game.image,slot,4))[0]==entry,'Physical rooted table slot')
        r=graphs[entry];push=next(x for x in r['instructions']if x['mnemonic']=='push');need(push['operands']==hex(callback),'Exact physical registered callback PUSH')
        calls=r['direct_calls'];need(any(x['target']==0x5ac140 for x in calls)and any(x['target']==wrapper for x in calls),'Actual wrapper and accepted registration CALL')
        w=graphs[wrapper];need(any(x['operands']==hex(filename)for x in w['instructions']if x['mnemonic']=='push')and any(x['operands']==f'ecx, 0x{obj:x}'for x in w['instructions']if x['mnemonic']=='mov')and any(x['target']==ctor for x in w['direct_calls']),'Physical filename/object/constructor argument definitions')
        name=text[filename];result=name+text[0x5e9580];request=len(name.encode())+1+4;need(request==len(result.encode())+1 and '.'not in name,'Static default scan/request and output size derivation')
        rootrows.append(dict(entry=entry,slot=slot,wrapper=wrapper,constructor=ctor,base_constructor=0x4de9c0,object=obj,object_extent=extent,owned_pointer_field=obj+4,filename=filename,filename_text=name,vtable=vtable,registration=dict(callback=callback,CALL_pc=next(x['site']for x in calls if x['target']==0x5ac140),target=0x5ac140),constructor_arguments=[filename,128,100],base_constructor_arguments=[filename,128,100,0,1],source_malloc_request_formula='(NOT ECX after source REPNE SCASB including filename NUL)+4',statically_derived_default_request=request,statically_derived_default_output=result,actual_request_observed=False,actual_capacity_observed=False,actual_allocation_count_observed=False,callback_executed=False))
    imports=[]
    for site,iat,name,args in((0x4dea15,0x5bb5a8,'strrchr',2),(0x4deab1,0x5bb664,'malloc',1),(0x4dead1,0x5bb658,'sprintf',4)):
        need(bytes.fromhex(rows[site]['bytes'])==b'\xff\x15'+struct.pack('<I',iat)and game.imports[iat]['name']==name,'Exact source imported CALL and owning name');symbol=game.imports[iat];value=struct.unpack('<I',raw(game.image,iat,4))[0];imports.append(dict(CALL_pc=site,return_pc=site+6,IAT=iat,raw_IAT=value,symbol=symbol,cdecl=True,argument_DWORDs=args,caller_cleanup_bytes=args*4,variadic=name=='sprintf',provider_entry=0x780264a9 if name=='strrchr' else 0x78022b9a if name=='sprintf' else 0x780012b3,actual_loaded_IAT_observed=False))
    fields=[dict(offset=o,width=4,value=v,source_PC=pc)for o,v,pc in((0,0x5cd418,0x4de9f7),(4,'actual returned malloc pointer',0x4deabc),(8,0,0x4de9e8),(12,0,0x4de9eb),(16,0,0x4de9ee),(20,128,0x4de9d6),(24,100,0x4de9f1),(28,0,0x4de9f4),(32,1,0x4de9dd))]
    stack=dict(base_entry='F',source_suffix=dict(address='F-8',bytes=5,source_PC_DWORD=0x4dea0d,source_PC_NUL=0x4dea11),strrchr_entry_ESP='F-36',strrchr_argument_frame=['return4DEA1B','filename','0x2E'],malloc_entry_ESP='F-32',malloc_argument_frame=['return4DEAB7','source computed request'],sprintf_entry_ESP='F-44',sprintf_argument_frame=['return4DEAD7','actual owned destination','format5E37F0','source filename','stack suffixF-8'],saved_dot_pointer=dict(address='F+8',store_PC=0x4dea20,retired_input_argument=True),temporary_dot_write_PC=0x4dea9e,restore_dot_write_PC=0x4deae2,base_RET_PC=0x4deaee,base_RET_cleanup=20,derived_RET_cleanup=12,whole_CPU_FX_ENV_frames_observed=False)
    originals=read('reports/m4-tree-original/original125-preparation-r1/report.json','6e55c14d0195d099f8a02a51dee250a4b3fb0d92832b7c0a6e08f307cbd9c5a1');observed=read('reports/m4-tree-original/original125-validation-r1/report.json','5a7911dee3f77d504a5a28cf66de2be7cc0b159a15a4e81282368a24d3a45534');need(observed['passed'],'Original125 normal extent observed; acceptance remains separate')
    data_pages={0x5cd000,0x5e3000,0x5e9000,0x60b000,0x5bb000};extra=sorted(data_pages-set(originals['observed_pages']));need(extra==[0x5cd000,0x5e3000,0x5e9000],'Three additional whole game data pages')
    for page in extra:
        q=out/f'game-{page:08x}-raw-page.bin';q.write_bytes(raw(game.image,page,4096));pin(q)
    prospective=sorted(originals['selected_order']+[dict(entry=x['entry'],slot=x['slot'])for x in rootrows],key=lambda r:r['slot']);need(len(prospective)==128,'Prospective relative-order128 source schedule')
    for i,x in enumerate(prospective):x['phase']=i
    instructions=dict(schema='mw34-formatting-frontier-v1',instructions=decoded,provider_instructions=providerdecoded,selected_order=prospective,roots=rootrows,source_data_pages=sorted(set(old['source_data_pages'])|data_pages),source_code_pages=sorted({x['pc']&~4095 for x in rows.values()}),provider_code_pages=sorted({x['pc']&~4095 for x in providerrows.values()}),FS_frame_contracts=[],new_game_entries=sorted(new),accepted_game_entries=sorted(retained),API_contracts=imports,object_fields=fields,source_stack_contract=stack,post_state_seed=False,initializer_credit=0)
    emit('game-normal-graphs.json',graphs);emit('game-new-graphs.json',new);emit('provider-entry-graphs.json',providers);emit('strrchr-graph.json',providers[0x780264a9]);emit('sprintf-output-frontier.json',dispatch);emit('output-frontier-graphs.json',dispatchgraphs);emit('roots.json',rootrows);emit('physical-strings.json',strings);emit('service-call-contracts.json',imports);emit('source-stack-contract.json',stack);emit('FS-frame-contracts.json',[]);emit('instruction-contracts.json',instructions)
    plan='''Three shared formatting roots after original125 acceptance\n\nRoots4DF610/4E0710/4E0810 use the same base constructor4DE9C0. Recover and compile its10 new game bodies once. The physical default inputs aiv, traps and targets derive source requests8,10,12 and strings aiv.zrd, traps.zrd, targets.zrd; these are predictions pending actual original capture.\n\nFirst genuine bounded prefix must use the staged authentic CRT loader/bootstrap and untouched object/stack BEFORE. Capture each actual strrchr and sprintf entry/return full CPU/FX/ENV, cdecl frames and loaded IAT names. Capture source malloc request, true API allocation/capacity/generation/initial whole backing, literal pointer publication, all output bytes and untouched capacity tail, then real source free cleanup. Do not supply predicted outputs or allocator sizes as observations.\n\nstrrchr is a closed23-instruction provider with two REPNE SCASB operations and actual STD/CLD directions. Preserve its flags and full register machine; host strrchr cannot stand in as source evidence. sprintf has a32-instruction wrapper and _output dispatch at7800FCEF. Its real8-way table is pinned. Measure and reconstruct the reached literal %s%s path through _output and its narrow-string helpers; numeric, wide and mutable-suffix alternatives remain separate. Full generic formatter closure is not claimed.\n\nNormal prefix comes before a prospective128-root/100-callback connected run. Add whole game pages5CD000/5E3000/5E9000. Preserve fixed Native offsets and typed loaded-IAT/owner/stack projections, use genuine owner occurrences for publication and whole buffer byteflow, and retain independent source/provider/paired/controls/final physical rehash gates. Current accepted count remains124 while125 final gates are open.\n'''
    (out/'next-batch.md').write_text(plan);pin(out/'next-batch.md');pin(__file__);pin(Path('C:/Users/jcbla/.agents/skills/reverse-engineer-anything/SKILL.md'))
    report=dict(passed=True,scope='Exact physical three-root formatting source and bounded provider entry frontier; static only',roots=3,root_entries=list(ROOTS),game_entries=13,new_game_bodies=10,unique_game_instructions=199,unique_game_bytes=611,strrchr_instructions=23,provider_exports=exports,sprintf_frontier_closed=False,new_game_data_pages=extra,source_stack_contract=stack,statically_derived_requests=[x['statically_derived_default_request']for x in rootrows],prospective_roots=128,prospective_callbacks=100,accepted_roots=124,original125_measured=True,original_execution_credit=False,native_execution_credit=False,initializer_credit=0,inherited_capture_reader_opened=False,files=pins)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),new_bodies=10,instructions=199,new_pages=list(map(hex,extra)))))
if __name__=='__main__':main(sys.argv[1])
