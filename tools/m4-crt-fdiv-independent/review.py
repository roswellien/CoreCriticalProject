"""Independent static FDIV initializer source/CFG/data-import contract.

Only the frozen PE metadata parser is imported. Source bytes, full decodes,
graphs and reference dumps remain private. No original or native body runs.
"""
from pathlib import Path
from collections import deque
import hashlib, importlib.util, json, re, struct, subprocess, sys, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-fdiv'
OUT=BASE/'independent-static-scope-r1'
PINS={};CHECKS=[];COMMANDS=[]
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
RANGES=((0x78004254,0x780042e1),(0x7802c070,0x7802c0ae),(0x780042e1,0x78004410),(0x7801129b,0x78011318))
def need(ok,why):
    if not ok:raise ValueError(why)
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(path,expected=None):
    p=Path(path).resolve();s=str(p)
    if s not in PINS:PINS[s]=sha(p)
    need(expected is None or PINS[s]==expected,'Exact physical identity '+s);return p
def read(path,expected=None):return json.loads(pin(path,expected).read_text(encoding='utf-8-sig'))
def note(name,**facts):CHECKS.append(dict(name=name,passed=True,**facts))
def save(name,body):
    p=OUT/name;p.write_bytes(body if isinstance(body,bytes) else body.encode());pin(p);return p
def dump(name,obj):return save(name,json.dumps(obj,indent=2)+'\n')
def command(args,name):
    args=list(map(str,args));pin(args[0]);r=subprocess.run(args,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
    path=save(name,r.stdout);err=save(name+'.stderr',r.stderr)
    COMMANDS.append(dict(argv=args,exit_code=r.returncode,stdout=str(path),stdout_sha256=sha(path),stderr=str(err),stderr_sha256=sha(err)))
    need(r.returncode==0 and not r.stderr,'Fresh static tooling '+name);return r.stdout.decode()
def metadata():
    p=pin(ROOT/'tools/analysis/pe.py','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
    spec=importlib.util.spec_from_file_location('own_fdiv_metadata_only',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    gamepath=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
    dllpath=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    return [(gamepath,m.PEImage(gamepath.read_bytes()),gamepath.read_bytes()),(dllpath,m.PEImage(dllpath.read_bytes()),dllpath.read_bytes())]
def raw(item,address,count):
    _,pe,b=item;o,_=pe.rva_range(address-pe.image_base,count);return b[o:o+count]
def section(item,address,count,permissions,file_backed=False):
    pe=item[1];rva=address-pe.image_base
    hits=[s for s in pe.sections if s['virtual_address']<=rva and rva+count<=s['virtual_address']+(s['raw_size'] if file_backed else max(s['virtual_size'],s['raw_size']))]
    need(len(hits)==1 and hits[0]['characteristics']&0xe0000000==permissions,'Exact owning section '+hex(address))
    s=hits[0];return dict(name=s['name'],characteristics=s['characteristics'],file_backed=rva+count<=s['virtual_address']+s['raw_size'],virtual_RVA=s['virtual_address'],raw_bytes=s['raw_size'],virtual_bytes=s['virtual_size'])
def decode(item,name):
    out=command([LLVM/'llvm-objdump.exe','--disassemble','--x86-asm-syntax=intel',item[0]],name)
    rows={}
    for line in out.splitlines():
        m=re.match(r'^\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)$',line)
        if not m:continue
        pc=int(m[1],16);body=bytes.fromhex(m[2]);need(raw(item,pc,len(body))==body and pc not in rows,'Unique fresh instruction bytes match input')
        section(item,pc,len(body),0x60000000,True)
        rows[pc]=dict(address=pc,size=len(body),mnemonic=m[3],operands=m[4].strip(),bytes_hex=body.hex())
    return rows
def encoded_flow(row):
    pc=row['address'];n=row['size'];b=bytes.fromhex(row['bytes_hex']);op=b[0];next_pc=pc+n
    if op==0xe8:kind='direct_call';target=next_pc+struct.unpack_from('<i',b,1)[0]
    elif op in (0xe9,0xeb):kind='jump';target=next_pc+(struct.unpack_from('<i',b,1)[0] if op==0xe9 else struct.unpack_from('<b',b,1)[0])
    elif 0x70<=op<=0x7f:kind='condition';target=next_pc+struct.unpack_from('<b',b,1)[0]
    elif op==0x0f and 0x80<=b[1]<=0x8f:kind='condition';target=next_pc+struct.unpack_from('<i',b,2)[0]
    elif op in (0xc2,0xc3):kind='return';target=None
    elif op==0xff and (b[1]>>3)&7==2:kind='indirect_call';target=None
    else:
        need(row['mnemonic']!='call' and not row['mnemonic'].startswith('j') and row['mnemonic']!='ret','No unmodeled control encoding')
        kind='next';target=None
    if target is not None:
        need(int(re.match(r'^0x([0-9a-f]+)',row['operands'])[1],16)==target,'Independent encoded branch target matches decode')
    return kind,target,next_pc
def graph(rows,entry,bounds):
    todo=deque((entry,));pcs=set();edges=[];calls=[];returns=[]
    while todo:
        pc=todo.popleft()
        if pc in pcs:continue
        need(pc in rows,'Every branch-reachable instruction decoded '+hex(pc));r=rows[pc]
        need(any(a<=pc and pc+r['size']<=b for a,b in bounds),'Every branch-reachable instruction lies in explicit closure bounds '+hex(pc))
        pcs.add(pc);kind,target,nxt=encoded_flow(r)
        if kind=='return':returns.append(dict(site=pc,callee_pop_bytes=(struct.unpack_from('<H',bytes.fromhex(r['bytes_hex']),1)[0] if r['size']==3 else 0)));continue
        if kind.endswith('call'):calls.append(dict(site=pc,target=target,return_pc=nxt,kind=kind,operands=r['operands']))
        if kind in ('jump','condition'):edges.append([pc,target]);todo.append(target)
        if kind!='jump':edges.append([pc,nxt]);todo.append(nxt)
    return dict(entry=entry,instructions=[rows[p] for p in sorted(pcs)],edges=sorted(edges),calls=sorted(calls,key=lambda x:x['site']),returns=sorted(returns,key=lambda x:x['site']))
def closure(rows):
    todo=deque((0x78004254,));graphs={}
    while todo:
        entry=todo.popleft()
        if entry in graphs:continue
        g=graph(rows,entry,RANGES);graphs[entry]=g
        todo.extend(c['target'] for c in g['calls'] if c['target'] is not None)
    return graphs
def named_import(item,slot,name,library):
    pe=item[1];hits=[(d['library'],s) for d in pe.imports() for s in d['symbols'] if pe.image_base+s['iat_rva']==slot]
    need(len(hits)==1 and hits[0][0].casefold()==library.casefold() and hits[0][1].get('name')==name,'Unique exact named IAT owner '+name)
    return dict(slot=slot,library=hits[0][0],symbol=hits[0][1],raw_DWORD=struct.unpack('<I',raw(item,slot,4))[0],section=section(item,slot,4,0x40000000,True))
def exact(row,op,args):need(row['mnemonic']==op and row['operands']==args,'Exact instruction operands '+hex(row['address']))
def pointer_model(rows):
    # Independent symbolic execution of the complete bounded eight instructions.
    g=graph(rows,0x7800426b,RANGES);eax=None;stores=[]
    for r in g['instructions']:
        if r['mnemonic']=='ret':continue
        need(r['mnemonic']=='mov','Pointer table helper has only MOV/RET')
        lhs,rhs=r['operands'].split(', ')
        value=eax if rhs=='eax' else int(rhs,16)
        if lhs=='eax':eax=value
        else:
            m=re.fullmatch(r'dword ptr \[0x([0-9a-f]+)\]',lhs);need(m is not None and value is not None,'Exact DWORD source pointer store');stores.append(dict(site=r['address'],address=int(m[1],16),value=value))
    need(len(stores)==6 and eax==0x780286e2,'Complete six-store helper and EAX result')
    need([(s['address'],s['value']) for s in stores]==[(0x78037c34,0x7802838c),(0x78037c30,0x780286e2),(0x78037c38,0x780283f2),(0x78037c3c,0x78028332),(0x78037c40,0x780283da),(0x78037c44,0x780286e2)],'All original related guest function pointer values')
    return stores
def scalar_control_model(cw):
    # Derive the complete finite bit remapping from the reached integer helpers.
    decoded=0
    for bit,flag in ((0,0x10),(2,8),(3,4),(4,2),(5,1),(1,0x80000)):
        if cw&(1<<bit):decoded|=flag
    decoded|=(cw&0xc00)>>2
    if cw&0x300==0:decoded|=0x20000
    elif cw&0x300==0x200:decoded|=0x10000
    if cw&0x1000:decoded|=0x40000
    modified=(decoded&~0x30000)|0x10000
    encoded=0
    for flag,bit in ((0x10,0),(8,2),(4,3),(2,4),(1,5),(0x80000,1)):
        if modified&flag:encoded|=1<<bit
    encoded|=(modified&0x300)<<2
    if modified&0x30000==0:encoded|=0x300
    elif modified&0x30000==0x10000:encoded|=0x200
    if modified&0x40000:encoded|=0x1000
    return decoded,modified,encoded
def inspect(game,dll,game_rows,rows,author):
    need(game[1].image_base==0x400000 and dll[1].image_base==0x78000000,'Actual preferred module bases')
    data_export=[x for x in dll[1].exports() if '_adjust_fdiv' in x['names']]
    need(len(data_export)==1 and data_export[0]['ordinal']==158 and data_export[0]['rva']==0x37c2c and 'forwarder' not in data_export[0],'Actual nonforwarded named data export')
    data_owner=section(dll,0x78037c28,32,0xc0000000,True)
    initial=struct.unpack('<8I',raw(dll,0x78037c28,32));need(initial[0]==0x78004254 and initial[1]==0,'Source callback DWORD nonzero; source data-export DWORD zero')
    imported=named_import(game,0x5bb508,'_adjust_fdiv','MSVCRT.dll')
    local=closure(rows);unique={r['address'] for g in local.values() for r in g['instructions']}
    need(set(local)=={0x78004254,0x7800426b,0x780042a3,0x780042cf,0x780042e1,0x780042f7,0x7800432c,0x7800439f} and len(unique)==204,'Own recursive call closure exactly204 distinct instruction PCs')
    roots={g['entry']:g for g in author['complete_graphs']}
    for entry,g in local.items():
        a=roots[entry];need(g['instructions']==a['instructions'] and g['edges']==sorted(a['edges']) and [(c['site'],c['target'],c['return_pc'],c['operands']) for c in g['calls']]==[(c['site'],c['target'],c['return_pc'],c['operands']) for c in a['calls']],'Full independent exact CFG/source/call match '+hex(entry))
    fallback=graph(rows,0x7802c070,RANGES);need(fallback['instructions']==roots[0x7802c070]['instructions'] and fallback['edges']==sorted(roots[0x7802c070]['edges']),'Complete separate fallback branch graph agrees')
    control=read(ROOT/'reports/m4-crt-control/independent-review-r4/report.json','b75abde48029efcdb8cb123c163c6bfb27a9b76dc62da014e620fca7c95bac56')
    accepted=set(control['source_model']['exact_model_source_PC_coverage'])|{int(x,16) for x in control['source_model']['unexecuted_static_PCs']}
    own_control={r['address'] for e,g in local.items() if e in (0x780042e1,0x780042f7,0x7800432c,0x7800439f) for r in g['instructions']}
    need(own_control==accepted and len(accepted)==148,'Own complete accepted148 hot/cold control identity including two unmeasured PCs')
    stores=pointer_model(rows)
    for s in stores:section(dll,s['address'],4,0xc0000000,True);section(dll,s['value'],1,0x60000000,True)
    imports=[named_import(dll,0x7802e098,'GetModuleHandleA','KERNEL32.dll'),named_import(dll,0x7802e0d0,'GetProcAddress','KERNEL32.dll')]
    names=[dll[1].rva_string(a-dll[1].image_base) for a in (0x7802e404,0x7802e3e8)]
    need(names==['KERNEL32','IsProcessorFeaturePresent'],'Exact private API lookup strings')
    exact(rows[0x780042a3],'push','0x7802e404');exact(rows[0x780042a8],'call','dword ptr [0x7802e098]')
    exact(rows[0x780042b6],'push','0x7802e3e8');exact(rows[0x780042bb],'push','eax');exact(rows[0x780042bc],'call','dword ptr [0x7802e0d0]')
    exact(rows[0x780042ca],'push','0x0');exact(rows[0x780042cc],'call','eax');exact(rows[0x780042ce],'ret','')
    constants=[]
    for a,wanted in ((0x78030018,3145727.0),(0x78030010,4195835.0),(0x7802ffc8,1.0)):
        b=raw(dll,a,8);need(struct.unpack('<d',b)[0]==wanted,'Exact binary64 fallback operand');section(dll,a,8,0x40000000,True)
        constants.append(dict(address=a,value=wanted,source_sha256=hashlib.sha256(b).hexdigest()))
    need([rows[a]['mnemonic'] for a in (0x7802c076,0x7802c07c,0x7802c07f,0x7802c085,0x7802c088,0x7802c08b,0x7802c08e,0x7802c091,0x7802c094,0x7802c097,0x7802c09a,0x7802c0a0,0x7802c0a2,0x7802c0a3)]==['fld','fstp','fld','fstp','fld','fdiv','fmul','fsubr','fstp','fld','fcomp','fnstsw','sahf','jbe'],'Exact complete fallback arithmetic/status/cpu branch sequence')
    exact(rows[0x7800425e],'mov','dword ptr [0x78037c2c], eax');exact(rows[0x78004268],'fnclex','')
    exact(rows[0x780042cf],'push','0x30000');exact(rows[0x780042d4],'push','0x10000')
    exact(rows[0x780042de],'pop','ecx');exact(rows[0x780042df],'pop','ecx')
    parent=graph(rows,0x78004227,((0x78004227,0x78004254),));need(parent['instructions']==author['callback_orchestrator']['instructions'],'Complete original callback orchestrator separate from writer scope')
    attach=rows[0x780018ab];need(encoded_flow(attach)[0:2]==('direct_call',0x78004227),'Actual static process attach call into separate orchestrator')
    refs=[r for r in rows.values() if re.search(r'(?<![0-9a-f])0x78037c2c(?![0-9a-f])',r['operands'])]
    need([r['address'] for r in refs]==[0x7800425e,0x78028d53,0x7802c6d4],'Whole-provider decoded direct data references')
    game_iat=[r for r in game_rows.values() if re.search(r'(?<![0-9a-f])0x5bb508(?![0-9a-f])',r['operands'])]
    sinkrefs=[r for r in game_rows.values() if re.search(r'(?<![0-9a-f])0x9a17e4(?![0-9a-f])',r['operands'])]
    need([r['address'] for r in game_iat]==[0x5ac408],'Only decoded direct game IAT reference')
    exact(game_rows[0x5ac408],'mov','eax, dword ptr [0x5bb508]');exact(game_rows[0x5ac40d],'mov','ecx, dword ptr [eax]');exact(game_rows[0x5ac40f],'mov','dword ptr [0x9a17e4], ecx')
    sinksection=section(game,0x9a17e4,4,0xc0000000)
    nextcall=game_rows[0x5ac415];need(encoded_flow(nextcall)[0:2]==('direct_call',0x5ac5c0),'Exact following direct call')
    empty=graph(game_rows,0x5ac5c0,((0x5ac5c0,0x5ac5c1),));need(len(empty['instructions'])==1 and empty['instructions'][0]['mnemonic']=='ret','Following reached local5AC5C0 is exact empty RET')
    consumer=graph(game_rows,0x5ac408,((0x5ac408,0x5ac415),)) if False else [game_rows[x] for x in (0x5ac408,0x5ac40d,0x5ac40f)]
    spans=[]
    for a,b in RANGES+((0x78004227,0x78004254),(0x780018ab,0x780018b0)):
        body=raw(dll,a,b-a);p=save(f'provider-source-{a:x}.bin',body);spans.append(dict(image='provider',address=a,size_bytes=b-a,file_offset=dll[1].rva_range(a-dll[1].image_base,b-a)[0],sha256=sha(p),path=str(p)))
    for a,b in ((0x5ac408,0x5ac415),(0x5ac415,0x5ac41a),(0x5ac5c0,0x5ac5c1),(0x5ac431,0x5ac448)):
        body=raw(game,a,b-a);p=save(f'game-source-{a:x}.bin',body);spans.append(dict(image='game',address=a,size_bytes=b-a,file_offset=game[1].rva_range(a-game[1].image_base,b-a)[0],sha256=sha(p),path=str(p)))
    for a in author['source_spans']:
        own=next(x for x in spans if x['image']=='provider' and x['address']==a['address']);need(own['sha256']==a['sha256'] and own['size_bytes']==a['size_bytes'] and own['file_offset']==a['file_offset'],'Exact full source-span hash/length/file offset')
    sdk=pin('C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/um/winnt.h');sdktext=sdk.read_text(encoding='utf-8-sig');need(re.search(r'#define\s+PF_FLOATING_POINT_PRECISION_ERRATA\s+0\s',sdktext),'Exact SDK feature constant0')
    declaration=pin('C:/Program Files (x86)/Windows Kits/10/Include/10.0.26100.0/um/processthreadsapi.h');dtext=declaration.read_text(encoding='utf-8-sig');need(re.search(r'BOOL\s+WINAPI\s+IsProcessorFeaturePresent\(\s*_In_ DWORD ProcessorFeature\s*\)',dtext),'Actual typed Win32 BOOL/stdcall DWORD declaration')
    primitive_model=[]
    for cw in (0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f):
        decoded,modified,encoded=scalar_control_model(cw);need(encoded==(cw&0x1c3f)|0x200,'Independent finite scalar precision-setting map')
        primitive_model.append(dict(before_CW=cw,decoded_abstract_CW=decoded,writer_final_EAX=modified,raw_FLDCW_word=encoded,hardware_CW_measured=False,reserved_bit6_not_in_raw_mapping=True))
    note('Independent fresh exact metadata/decode/recursive writer and accepted control CFG',unique_writer_instruction_PCs=204,unique_control_hot_cold_PCs=148,unique_noncontrol_PCs=56,local_call_entries=list(local),source_callbacks_initial=initial[0],source_adjust_initial=initial[1],initialized_adjust_measured=False,full_source_spans=spans)
    note('Own exact side effects, dynamic API boundaries and game data consumer',pointer_stores=stores,provider_imports=imports,dynamic_query_argument=0,dynamic_query_success_not_assumed=True,game_consumer_entry=0x5ac408,game_consumer_end=0x5ac415,game_sink=0x9a17e4,game_sink_owner=sinksection,following_empty_RET_entry=0x5ac5c0,fullprocess_attach=False)
    return dict(graphs=list(local.values()),separate_fallback_graph=fallback,callback_orchestrator=parent,attach_call=attach,provider_direct_adjust_references=refs,game_direct_adjust_IAT_references=game_iat,game_direct_adjust_copy_references=sinkrefs,game_consumer_instructions=consumer,pointer_stores=stores,provider_imports=imports,data_export=data_export[0],game_import=imported,data_owner=data_owner,source_DWORDs=list(initial),lookup_names=names,constants=constants,scalar_precision_model=primitive_model,source_spans=spans)
def causal_static(rows,graphs):
    controls=[]
    # Causal corruption changes actual encoded branches, body coverage or exact
    # side-effect operands; only the private copy is mutated.
    for name,pc,mode in (('wrong encoded writer call',0x78004254,'call'),('missing fallback terminal',0x7802c0ad,'missing'),('wrong pointer destination',0x78004270,'store'),('wrong pointer value',0x7800426b,'value'),('wrong dynamic target',0x780042cc,'dynamic')):
        altered={p:dict(v) for p,v in rows.items()}
        if mode=='missing':del altered[pc]
        elif mode=='call':b=bytearray.fromhex(altered[pc]['bytes_hex']);b[1]^=1;altered[pc]['bytes_hex']=b.hex()
        elif mode=='store':altered[pc]['operands']=altered[pc]['operands'].replace('0x78037c34','0x78037c30')
        elif mode=='value':altered[pc]['operands']='eax, 0x780286e3'
        else:altered[pc]['operands']='ecx'
        try:
            if mode in ('call','missing'):closure(altered)
            elif mode in ('store','value'):pointer_model(altered)
            else:exact(altered[pc],'call','eax')
        except ValueError as e:controls.append(dict(name=name,rejected=True,reason=str(e)))
        else:raise ValueError('Own static cause was not rejected '+name)
    note('Own causal static source/CFG controls',controls=controls,native_or_original_executed=False)
    return controls
def main():
    need(not OUT.exists(),'Fresh independent static dossier');OUT.mkdir(parents=True);save('review-source.py',Path(__file__).read_bytes());pin(Path(__file__));pin(sys.executable)
    try:
        author=read(BASE/'source-recovery-r1/report.json','c124fbfbf5bf64125b9e93c52b9b0e0500f2dd93df6d6ee440b89f5d90f895fd')
        pins=read(BASE/'source-recovery-r1/pins.json','6b0327531d1932e19ee2376ff7bb2a41b1b6b8b20f27288e5f73dd24cbd7fa07')
        for p,h in pins['files'].items():pin(p,h if isinstance(h,str) else h['sha256'])
        note('Frozen root static recovery physical identities rehashed',bindings=len(pins['files']),root_recover_imported=False,whole_M4_credit=False)
        game,dll=metadata();rows=decode(dll,'provider-fresh-llvm.txt');grows=decode(game,'game-fresh-llvm.txt')
        model=inspect(game,dll,grows,rows,author);controls=causal_static(rows,model['graphs']);dump('exact-source-CFG-model.json',model)
        scope=dict(writer='No-argument cdecl leaf/root0x78004254; real RET0 after nested calls. Six pointer stores + returned probe EAX store + reached controlfp wrapper + FNCLEX; complete204 local direct dependency PCs, exactly148 accepted control PCs reused as source identities only.',dynamic='GetModuleHandleA(KERNEL32) stdcall4; GetProcAddress(handle,IsProcessorFeaturePresent) stdcall8; dynamically resolved BOOL WINAPI query(feature0) stdcall4. Null module or null export selects exact arithmetic fallback. Unspecified API volatile registers/arithmetic flags must remain separate observations; no guest caller volatile equality invented.',data='Provider data export0x78037C2C, file DWORD0, must have actual writer result. Callback pointer0x78037C28 has source value0x78004254. Game0x5AC408 loads owned data address from IAT0x5BB508;0x5AC40D reads DWORD;0x5AC40F copies it into0x9A17E4. Three MOVs leave arithmetic flags and other GPRs/ESP/FP unchanged, end0x5AC415. Following5AC5C0 is exact empty RET; later5AC436 is unrelated _initterm setup.',fallback='Branch-reachable24 instructions; probe-entry SP=P; pushEBP/frame/sub24, localsP-12/P-20/P-28. Stores binary64 constants4195835 and3145727, divides/multiplies then subtracts from numerator, binary64 store, FCOMP1, FNSTSW AX/SAHF/JBE. Below/equal/unordered returns0 via XOR; above returns1 via PUSH/POP. EBP restored with LEAVE; no callee argument cleanup. Host arithmetic/CW/exception/occupied-stack outcomes unmeasured.',FP='After query result store, pushes mask0x30000/new0x10000 and actual calls _controlfp. Raw mapping sets precision53 and maps supported exception/round/infinity fields; reserved CW bits omitted, hardware canonicalization needs separate transport proof. Final returned EAX is mapped abstract modified CW, not `_adjust_fdiv`; final ECX is caller pop mask0x30000. FNCLEX defined clear mask0x80FF; C0/C1/C2/C3 undefined. CW/TOP/tags/raw80/legacy fields remain untouched by FNCLEX; MXCSR unaffected. Entire writer can change CW and query/fallback can change FP metadata.',ownership='Opaque native API targets/handles must be typed host-owned services; 32-bit guest data/pointer values are never host pointers. Raw provider/game IAT words remain original metadata and named dispatch must separately bind measured loaded Windows target/module/export identity. All data/stack accesses require checked guest permissions and exact bounded lifetime.')
        report=dict(passed=True,scope='Independent static FDIV writer/dependency/actual game consumption only',checks=CHECKS,commands=COMMANDS,model_path=str(OUT/'exact-source-CFG-model.json'),model_sha256=sha(OUT/'exact-source-CFG-model.json'),decoded_provider_instructions=len(rows),decoded_game_instructions=len(grows),unique_writer_dependency_instructions=204,accepted_control_hot_cold_instructions=148,complete_local_function_entries=8,separate_fallback_instructions=24,game_consumer_entry=0x5ac408,game_consumer_end=0x5ac415,game_consumer_source_size=13,causal_static_controls=controls,source_ABI_contract=scope,architecture_reference=dict(url='https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2a-manual.pdf',order='253666-060US',dated='September2016',pdf_zero_based_page=422,manual_page='3-321',verified_via_browser=True,FNCLEX_SW_defined_clear_mask=0x80ff,undefined_condition_mask=0x4700,original_API_or_body_execution=False),root_changes_required=[],clarifications=['Actual direct game consumer lies before matherr at5AC408, not after5AC436','The source global zero is not initialized writer output; callback source pointer is nonzero','Six function-pointer destinations/values are guest data; their target bodies are not called by this writer closure','Complete148 control CFG includes146 previously observed plus two exact retained unexecuted static PCs','FNCLEX condition bits undefined; native retention is an explicit representative and any raw equality is observed only','Raw scalar mapping omits reserved CW bit6; actual hardware canonicalization must be measured, not assumed by scalar model'],primary_recover_or_native_imported=False,original_or_provider_executed=False,native_execution_credit=False,full_process_attach=False,full_CRT=False,full_startup=False,frontend=False,whole_M4_complete=False,limitations=['Decoded whole-text reference inventory does not establish absence of indirect aliases or dynamically discovered targets.','The orchestrator source calls this writer through its nonzero data pointer before two _initterm table ranges; these other root closures/process attach remain outside204 writer PCs.','Scalar CW mapping and fallback algorithm/branch classification are static models only; no arithmetic/result or host API observation/equivalence credit.','Direct-import and dynamic Win32 stdcall contracts come from exact instructions plus local SDK declaration; real loaded target pointer/module association and actual cleanup require provider reference measurements.','Public review code contains metadata/operand facts and private hash identities, no complete original instruction byte literals. Full bytes/decodes/graphs stay ignored private.','No original process, provider load, Windows query, IAT replacement, native writer, shared Runtime modification, callback invocation or menu launch.'])
        rp=dump('report.json',report)
        for p,h in PINS.items():need(sha(p)==h,'Final unchanged physical association '+p)
        (OUT/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,bindings=len(PINS),unique_writer_instructions=204,control_instructions=148,game_consumer_entry=hex(0x5ac408),report_sha256=sha(rp),pins_sha256=sha(OUT/'pins.json'))))
    except Exception:
        save('failure.txt',traceback.format_exc());dump('partial.json',dict(checks=CHECKS,commands=COMMANDS,bindings=len(PINS)));raise
if __name__=='__main__':main()
