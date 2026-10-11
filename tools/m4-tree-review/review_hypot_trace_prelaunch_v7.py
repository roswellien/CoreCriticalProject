"""Independent, bounded physical hypot-tracer prelaunch review; never run guest code."""
from pathlib import Path
from collections import Counter
import hashlib, json, re, struct, sys

sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'tools/analysis'))
from pe import PEImage

PREP = R / 'reports/m4-hypot-original/trace-preparation-r8'
BUILD = R / 'reports/m4-hypot-original/trace-build-r7'
PH = '94a53e0fffb364f0265e86d54c43e215b3f454aa24e97b5da21573e091bc6b86'
BH = '8d1ad8ac1f1ad72c58484930a95add94440e62c7da9ece0ac1d7adb60032d29e'
PINS = {}

def need(v, m):
    if not v: raise ValueError(m)

def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def pin(p, h=None):
    p = Path(p).resolve()
    need(p.suffix.lower() not in ('.mwb', '.zip'), 'No capture/archive reader')
    v = sha(p)
    need(h is None or v == h, 'Exact physical input ' + str(p))
    need(str(p) not in PINS or PINS[str(p)] == v, 'Consistent physical pin')
    PINS[str(p)] = v
    return p

def load(p, h=None): return json.loads(pin(p, h).read_bytes())

def coff(data):
    machine, count, _, table, total, optional, _ = struct.unpack_from('<HHIIIHH', data)
    need(machine == 0x14c and optional == 0, 'Standard actual x86 COFF')
    strings = table + total * 18
    end = strings + struct.unpack_from('<I', data, strings)[0]
    need(end <= len(data), 'Whole COFF string table')
    symbols, i = {}, 0
    while i < total:
        name, value, section, typ, storage, aux = struct.unpack_from('<8sIhHBB', data, table + i * 18)
        if name[:4] == bytes(4):
            start = strings + struct.unpack_from('<I', name, 4)[0]
            need(strings + 4 <= start < end, 'Bounded COFF long symbol')
            name = data[start:data.index(b'\0', start, end)]
        else: name = name.rstrip(b'\0')
        symbols[i] = dict(name=name.decode('ascii'), value=value, section=section, type=typ, storage=storage)
        i += 1 + aux
    sections = {}
    for i in range(count):
        start = 20 + i * 40
        size, raw, reloc, _, number = struct.unpack_from('<IIIIH', data, start + 16)
        flags = struct.unpack_from('<I', data, start + 36)[0]
        need((raw+size<=len(data) or (raw==0 and flags&0x80 and not flags&0x20000000)) and reloc+number*10<=len(data), 'Whole initialized COFF bytes or actual nonexecutable uninitialized BSS, and all relocations')
        rows = []
        for j in range(number):
            offset, target, typ = struct.unpack_from('<IIH', data, reloc + j * 10)
            need(target in symbols, 'Every relocation names actual symbol')
            rows.append(dict(offset=offset, symbol=symbols[target], type=typ))
        sections[i + 1] = dict(bytes=data[raw:raw+size] if raw else b'', logical_size=size, uninitialized=bool(flags&0x80), flags=flags, relocations=rows)
    return symbols, sections

def linked_function(image, symbols, sections, name):
    definitions = [s for s in symbols.values() if s['name'] == name and s['section'] > 0 and s['type'] == 0x20]
    need(len(definitions) == 1, 'One actual compiled function ' + name)
    s = definitions[0]; section = sections[s['section']]
    need(section['flags'] & 0x20000000, 'Executable COFF function')
    ends = [v['value'] for v in symbols.values() if v['section'] == s['section'] and v['type'] == 0x20 and v['value'] > s['value']]
    end = min(ends, default=len(section['bytes']))
    raw = section['bytes'][s['value']:end]
    relocs = [dict(r, offset=r['offset']-s['value']) for r in section['relocations'] if s['value'] <= r['offset'] < end]
    need(raw and all(r['type'] in (6,0x14) or (r['type']==11 and r['symbol']['name']=='__Init_thread_epoch' and r['symbol']['section']==0) for r in relocs), 'x86 DIR32/REL32 executable relocations')
    ignored = {i for r in relocs for i in range(r['offset'], r['offset'] + 4)}
    runs, begin = [], None
    for i in range(len(raw) + 1):
        if i < len(raw) and i not in ignored:
            if begin is None: begin = i
        elif begin is not None:
            runs.append((begin, raw[begin:i])); begin = None
    anchor, needle = max(runs, key=lambda x: len(x[1])); candidates = []
    for sec in image.sections:
        if not sec['executable']: continue
        data = image.data[sec['raw_offset']:sec['raw_offset']+sec['raw_size']]; pos = 0
        while True:
            pos = data.find(needle, pos)
            if pos < 0: break
            start = pos - anchor
            actual = data[start:start+len(raw)] if start >= 0 else b''
            if len(actual) == len(raw) and all(a == b for i,(a,b) in enumerate(zip(actual,raw)) if i not in ignored):
                candidates.append((image.image_base+sec['virtual_address']+start,actual))
            pos += 1
    need(len(candidates) == 1, 'Unique whole linked nonrelocated function bytes ' + name)
    address, actual = candidates[0]; resolved = []
    for r in relocs:
        i=r['offset']; original=struct.unpack_from('<I',raw,i)[0]; final=struct.unpack_from('<I',actual,i)[0]
        value=(final-original+(address+i+4 if r['type']==0x14 else 0)) & 0xffffffff
        resolved.append(dict(offset=i,type=r['type'],symbol=r['symbol']['name'],symbol_section=r['symbol']['section'],symbol_value=r['symbol']['value'],resolution_kind='compiler TLS section-relative offset' if r['type']==11 else 'virtual address',**({'section_relative_offset':value} if r['type']==11 else {'actual_symbol_address':value})))
    return dict(symbol=name,address=address,bytes=len(raw),object_raw_hex=raw.hex(),linked_hex=actual.hex(),relocations=resolved)

def main(name):
    out = R / 'reports/m4-tree-review' / name
    need(not out.exists(), 'Additive output only')
    prep=load(PREP/'report.json',PH); build=load(BUILD/'build.json',BH)
    need(prep['passed'] is True and build['passed'] is True, 'Actual passed preparation and compilation')
    for d,key in ((prep,'files'),(build,'sources')):
        for p,h in d[key].items(): pin(p,h)
    need(Path(build['preparation']).resolve()==PREP.resolve() and build['preparation_sha256']==PH, 'Current actual build consumes final prep8')
    need(all(c['exit_code']==0 for c in build['commands']), 'Actual configure/compile success')
    need((build['roots'],build['sequences'],build['phases'],build['pages'],build['record_bytes'])==(1,6,6,43,356992), 'Finite actual original-only schedule/ABI')
    need(prep['trace_descriptors']==3538 and prep['descriptor_gaps']==[] and prep['provider_imports']==145, 'Exact descriptor/import inventory, no gaps')
    for k in ('predicted_outputs_supplied_to_execution','provider_preinvoked','source_after_seed','archive_reader_opened','original_executed','normal_return_replay_used'):
        need(prep[k] is False, 'No execution/seed/acceptance credit: '+k)
    need(type(prep['initializer_credit'])is int and prep['initializer_credit']==0,'Explicit integer zero initializer credit')
    need([prep[k] for k in ('trace_event_bytes','trace_api_bytes','trace_cell_bytes','trace_context_bytes','trace_event_bound','trace_API_bound')]==[1840,9800,60,716,32768,256], 'Complete bounded observation layouts')
    rows=load(PREP/'trace-instruction-contracts.json')['instructions']
    need(len(rows)==3538 and Counter(r['module'] for r in rows)==Counter(game=65,CRT=3473), 'Exact physical game/provider row extent')
    modules={
      'game':PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes()),
      'CRT':PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())}
    seen=set(); descriptor=bytearray(); physical=[]
    for r in rows:
        need(r['pc'] not in seen and r['descriptor_complete'] is True, 'Unique complete instruction descriptor')
        seen.add(r['pc']); raw=bytes.fromhex(r['bytes_hex']); image=modules[r['module']]
        off,_=image.rva_range(r['pc']-image.image_base,len(raw))
        need(len(raw)==r['width'] and raw[0]==r['opcode'] and image.data[off:off+len(raw)]==raw, 'Whole exact physical instruction bytes')
        need(len(r['cells'])<=4, 'Bounded cell inventory')
        descriptor.extend(struct.pack('<4I',r['pc'],r['width'],r['opcode'],len(r['cells'])))
        for c in r['cells']:
            need(0<c['width']<=16 and c['read'] in (0,1) and c['write'] in (0,1) and c['segment'] in (0,1) and len(c['coefficients'])==8, 'Exact bounded flat32/FS cell')
            descriptor.extend(struct.pack('<13I',c['displacement'],*c['coefficients'],c['width'],c['read'],c['write'],c['segment']))
        descriptor.extend(bytes((4-len(r['cells']))*52))
        physical.append(dict(pc=r['pc'],module=r['module'],file_offset=off,width=r['width'],bytes_hex=r['bytes_hex']))
    need(all(a['pc']+a['width']<=b['pc'] for a,b in zip(rows,rows[1:])), 'All physical instructions disjoint and ordered')
    by={r['pc']:r for r in rows}
    for pc,op,registers,reads,writes in ((0x78001041,'stosd',[7],[0],[1]),(0x78010752,'movsd',[6,7],[1,0],[0,1]),(0x780108b3,'movsd',[6,7],[1,0],[0,1])):
        r=by[pc]; need(r['mnemonic']==op and r['repeat']=='rep' and len(r['cells'])==len(registers), 'Precise REP string descriptor')
        for c,reg,rd,wr in zip(r['cells'],registers,reads,writes):
            need(c==dict(displacement=0,coefficients=[int(i==reg)for i in range(8)],width=4,read=rd,write=wr,segment=0),'Exact normalized source operand')
    need(not any(r['mnemonic'] in ('fnstenv','fstenv','fnsave','fsave','frstor','fxsave','fxrstor') for r in rows), 'No omitted >16B FP memory descriptor in this finite physical set')
    fs=load(PREP/'fs-hook-bindings.json')
    need(not any(r['PC']<=pc<r['PC']+len(bytes.fromhex(r['raw_bytes'])) for r in fs for pc in seen), 'No inherited FS patch overlaps a traced source instruction')
    imports=load(PREP/'api-imports.json'); expected=[]
    for label,image in modules.items():
        for d in image.imports():
            for s in d['symbols']:
                iat=image.image_base+s['iat_rva']
                if label=='game' and iat!=0x5bb5b0: continue
                expected.append((label,iat,s.get('name')or('#'+str(s['ordinal'])),d['library']))
    need([(x['module'],x['iat'],x['name'],x['library']) for x in imports]==expected, 'Every candidate IAT identity from actual whole PE import tables')
    need(imports[0]['iat']==0x5bb5b0 and imports[0]['name']=='_hypot' and imports[0]['argc']==4, 'Exact four-word cdecl hypot input')
    old3=R/'reports/m4-hypot-original/trace-preparation-r3'; old4=R/'reports/m4-hypot-original/trace-preparation-r4'
    a=pin(old3/'hypot_trace.hpp').read_text(); b=pin(old4/'hypot_trace.hpp').read_text(); trace=pin(PREP/'hypot_trace.hpp').read_text()
    need(a.replace('pending=~0U;c.EFlags&=~0x100U;require(SetThreadContext','pending=~0U;c.EFlags&=~0x100U;c.ContextFlags=CONTEXT_CONTROL;require(SetThreadContext').replace('pending=point;require(SetThreadContext','pending=point;c.ContextFlags=CONTEXT_CONTROL;require(SetThreadContext')==b, 'Exactly two CONTROL-only debugger source changes')
    need(trace.count('c.ContextFlags=CONTEXT_CONTROL;require(SetThreadContext')==2 and trace.count('c.ContextFlags=CONTEXT_FULL|CONTEXT_FLOATING_POINT|CONTEXT_EXTENDED_REGISTERS;require(GetThreadContext')==1, 'Full stopped observation, two control writes only')
    need(trace.count('SetThreadContext')==2 and not any(s in trace for s in ('c.Eax=','c.Ebx=','c.Ecx=','c.Edx=','c.Esi=','c.Edi=','c.Esp=','c.Ebp=','c.FloatSave=','c.ExtendedRegisters=')), 'No authored integer/FP data modification by tracer; observed CONTROL EBP/ESP remain unchanged')
    source=pin(PREP/'reference.cpp').read_text(); broker=pin(PREP/'original_broker.hpp').read_text()
    need('const bool debugger=false;mw34::original_broker::checkpoint_mode=true;' in source and 'if(hypot_trace_debug(child,event))return true;' in source, 'Actual parent debugger association precedes inherited checkpoint')
    need('hypot_trace_begin();r->tag.status=execute();hypot_trace_finish();' in source and 'require(hypot_count==0,' in source, 'Actual genuine execution bracket and no normal cdecl replay')
    need('for(const auto&hook:hypot_hooks)' not in source and '=reinterpret_cast<unsigned>(&hypot_entry)' not in source, 'No normal return patch or game-IAT observer installation')
    need('hypot_target==0x7802a122' in source and '*reinterpret_cast<unsigned*>(0x5bb5b0)=hypot_target;' in source, 'Actual named genuine _hypot target, not shim')
    need('DEBUG_ONLY_THIS_PROCESS' in broker and 'if(handle_debug_checkpoint(child.value,event))++checkpoints;' in broker and 'ContinueDebugEvent' in broker, 'Actual external stopped child broker route')
    need('require(pending==~0U&&c.Eip==pc+1' in trace and 'measured.exception_eip=c.Eip' in trace and 'measured.before=c' in trace and 'measured.after=c' in trace, 'Raw breakpoint/step CONTEXT retained with precise source PC')
    need('a.after.Eip=pc' in trace and 'a.entry=c' in trace and 'a.after=c' in trace, 'Raw cdecl boundaries plus explicit breakpoint PC projection')
    for s in ('hypot_trace_owner=GetCurrentThreadId()','source_owner==event.dwThreadId&&teb','GetThreadSelectorEntry','o.base==0&&o.limit==0xffffffff','teb+0x34','maybe(teb,&v,4)','maybe(0x20001000,a.stack_entry,4096)','maybe(0x20001000,a.stack_after,4096)','*b=hypot_trace_original[i]','patch(hypot_trace_points[pending].pc,0xcc)','VirtualProtectEx','FlushInstructionCache'):
        need(s in trace,'Bounded actual source/stack/FS/LastError/segment/control/restoration contract '+s)
    old5=R/'reports/m4-hypot-original/trace-preparation-r5'
    removal=load(PREP/'removed-trace-overlaps.json')
    need(removal['original_hook_count']==45 and removal['retained_hook_count']==42 and [v['PC']for v in removal['removed']]==[0x7800139f,0x780013a6,0x78001419],'Exact three physical overlapping inherited CRT hooks removed')
    oldref=pin(old5/'reference.cpp').read_text()
    for h in removal['removed']:
        fragment='{'+hex(h['PC'])+','+str(len(bytes.fromhex(h['raw_bytes'])))+','+str(h['kind'])+',&'+h['declared_observer']+',{'+','.join(hex(x)for x in bytes.fromhex(h['raw_bytes']))+'}},'
        need(oldref.count(fragment)==1,'Exact old source hook initializer')
        oldref=oldref.replace(fragment,'')
    oldref=oldref.replace('const std::array<FsHook,45> fs_hooks','const std::array<FsHook,42> fs_hooks')
    oldnull='const std::array<NullHook,2> null_hooks{{{0x78001390,&nullfree_entry_hook,{0x55,0x8b,0xec,0x6a,0xff}},{0x78001420,&nullfree_ret_hook,{0x5f,0x5e,0x5b,0xc9,0xc3}}}};'
    need(oldref.count(oldnull)==1 and oldref.replace(oldnull,'const std::array<NullHook,0> null_hooks{};')==source,'Only exact three FS and two NULL-free overlapping source-hook removals')
    oldkernel=pin(R/'reports/m4-hypot-original/trace-preparation-r6/hypot_trace.hpp').read_text()
    oldbegin='for(unsigned i=0;i<hypot_trace_points.size();++i){const auto&p=hypot_trace_points[i];auto*b=reinterpret_cast<unsigned char*>(p.pc);require(*b==p.opcode,"Exact physical source first opcode before trace");hypot_trace_original[i]=*b;DWORD old{},ignored{};'
    newbegin='for(unsigned i=0;i<hypot_trace_points.size();++i){const auto&p=hypot_trace_points[i];const auto actual=*reinterpret_cast<unsigned char*>(p.pc);require(actual==p.opcode,("Exact physical source first opcode before trace PC="+std::to_string(p.pc)+" expected="+std::to_string(p.opcode)+" actual="+std::to_string(actual)).c_str());hypot_trace_original[i]=actual;}\n for(unsigned i=0;i<hypot_trace_points.size();++i){const auto&p=hypot_trace_points[i];auto*b=reinterpret_cast<unsigned char*>(p.pc);DWORD old{},ignored{};'
    need(oldkernel.count(oldbegin)==1 and oldkernel.replace(oldbegin,newbegin)==trace,'Exact two-pass first-opcode validation plus bounded diagnostic; remaining kernel unchanged')
    need(trace.index('hypot_trace_original[i]=actual;}')<trace.index('require(VirtualProtect(b,1')<trace.index('*b=0xcc')<trace.index('hypot_trace_active=1'),'Every source opcode validated before any breakpoint installation')
    actual_hooks=[];families=[]
    for typ,label,count in [('FsHook','fs_hooks',42),('NullHook','null_hooks',0),('VtableHook','vtable_hooks',6),('LockitHook','lockit_hooks',4)]:
        match=re.search(r'const std::array<'+typ+r',([0-9]+)>\s*'+label+r'(\{.*?\});',source)
        need(match and int(match[1])==count,'Exact current active hook family '+label)
        hooks=[]
        if count:
            for pc,size,entry,raw in re.findall(r'\{(0x[0-9a-f]+),([0-9]+),(?:[0-9]+,)?&([A-Za-z_0-9]+),\{([^{}]+)\}',match[2]):
                data=bytes(int(x.strip(),0)for x in raw.split(','));need(len(data)==int(size),'Complete actual hook source span');pc=int(pc,16)
                need(not any(pc<r['pc']+r['width']and pc+len(data)>r['pc']for r in rows),'Every full active hook source span is disjoint from every full traced instruction')
                hooks.append(dict(family=typ,PC=pc,size=int(size),declared_observer=entry,raw_hex=data.hex()))
        need(len(hooks)==count,'Exact current complete hook rows');families.append(dict(family=typ,active_count=count));actual_hooks+=hooks
    hook_audit=load(PREP/'active-hook-overlap-audit.json')
    need(actual_hooks==hook_audit['complete_active_code_spans']and families==hook_audit['active_families']and hook_audit['overlaps']==[]and len(actual_hooks)==52,'Independent current whole hook table matches frozen all-family audit')
    for pc,size in [(0x410a80,5),(0x5ac3ec,5)]:need(not any(pc<r['pc']+r['width']and pc+size>r['pc']for r in rows),'Exact endpoint/sentinel brokers disjoint')
    need(pin(old5/'trace-instruction-contracts.json').read_bytes()==pin(PREP/'trace-instruction-contracts.json').read_bytes(),'No descriptor/source rows changed by hook removal')
    compile_log=pin(BUILD/'compile.log').read_text(); configure=pin(BUILD/'configure.log').read_text()
    need(str(PREP/'reference.cpp') in compile_log and '/W4 /WX' in compile_log and '/MACHINE:X86' in compile_log and '0 Warning(s)' in compile_log and '0 Error(s)' in compile_log, 'Actual current source compiler and x86 linker success')
    worker=PEImage(pin(build['worker'],build['worker_sha256']).read_bytes())
    need(worker.image_base==0x18000000 and worker.machine==0x14c, 'Actual fixed preferred-base x86 worker')
    pos=worker.data.find(descriptor); need(pos>=0 and worker.data.find(descriptor,pos+1)<0,'Unique whole3538 compiled descriptor array')
    section=next(s for s in worker.sections if s['raw_offset']<=pos and pos+len(descriptor)<=s['raw_offset']+s['raw_size'])
    need(section['readable'] and not section['writable'] and not section['executable'],'Actual compiled immutable descriptor array')
    obj=pin(BUILD/'build-x86/mw34_joint_startup124_original.dir/Release/reference.obj'); symbols,sections=coff(obj.read_bytes())
    names=[s['name'] for s in symbols.values() if s['type']==0x20 and s['section']>0 and (s['name'].startswith('?hypot_trace_') or s['name'].startswith('?handle_debug_checkpoint@') or (s['name'].startswith('??R<lambda_')and'??hypot_trace_debug@@'in s['name']))]
    omitted=[n for n in names if n=='?hypot_trace_register@@YAIABU_CONTEXT@@I@Z' or any(n.startswith('??R<lambda_'+str(i)+'>') for i in (1,2,3,6))]
    need(len(names)==12 and len(omitted)==5,'Exact compiler-only inline/unreferenced helper definitions')
    retained_sections={s['section']for s in symbols.values()if s['name']in names and s['name']not in omitted and s['section']>0}
    need(not any(q['symbol']['name']in omitted for sec in retained_sections for q in sections[sec]['relocations']),'No retained tracer references an omitted helper')
    linked=[linked_function(worker,symbols,sections,n)for n in names if n not in omitted]
    need(len(linked)==7,'Three retained tracer functions, three observation lambdas, actual broker handler')
    tls=[q for f in linked for q in f['relocations']if q['type']==11]
    need(len(tls)==1 and tls[0]['symbol']=='__Init_thread_epoch' and tls[0]['offset']==553 and tls[0]['section_relative_offset']==4,'Exactly one typed compiler TLS SECREL at actual offset4')
    tls_rva,tls_size=worker.directories[9];need(tls_size==24,'Complete real x86 TLS directory')
    tls_off,_=worker.rva_range(tls_rva,24);tls_words=struct.unpack_from('<6I',worker.data,tls_off)
    tls_start,tls_end,tls_index,tls_callbacks,tls_zero,tls_characteristics=tls_words
    need(tls_end-tls_start==8 and tls_zero==0,'Exact initialized TLS template extent')
    tls_off,_=worker.rva_range(tls_start-worker.image_base,8)
    need(worker.data[tls_off:tls_off+8]==bytes.fromhex('0000000000000080'),'Actual compiler TLS epoch initial integer at section-relative4, not a virtual address')
    pin(R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/include/llvm/BinaryFormat/COFF.h')

    assigned={x['symbol']:x['address'] for x in linked}; assigned.update({'__imp__'+s['name']+'@'+str({'SetThreadContext':8,'GetThreadContext':8,'OpenThread':12,'ReadProcessMemory':20,'WriteProcessMemory':20,'GetThreadSelectorEntry':12,'VirtualProtectEx':20,'FlushInstructionCache':12,'VirtualProtect':16,'GetCurrentThreadId':0,'GetCurrentProcess':0}.get(s['name'],-1)):worker.image_base+s['iat_rva'] for d in worker.imports() for s in d['symbols'] if 'name'in s})
    assigned['?hypot_trace_points@@3V?$array@UHypotTracePoint@@$0NNC@@std@@B']=worker.image_base+section['virtual_address']+pos-section['raw_offset']
    bases={};reloc_count=0;typed=0
    for f in linked:
        for q in f['relocations']:
            reloc_count+=1
            if q['type']==11: continue
            n=q['symbol'];v=q['actual_symbol_address']; sec=q['symbol_section'];sv=q['symbol_value']
            if n in assigned: need(v==assigned[n], 'Actual relocation matches attributed function/import/data '+n);typed+=1
            if sec>0:
                need(sec not in bases or bases[sec]==(v-sv)&0xffffffff,'All real COFF section-relative relocation identities agree')
                bases[sec]=(v-sv)&0xffffffff
    debug=next(f for f in linked if f['symbol']=='?hypot_trace_debug@@YA_NPAXABU_DEBUG_EVENT@@@Z')
    debug_bytes=bytes.fromhex(debug['linked_hex']);set_rows=[q for q in debug['relocations']if q['symbol']=='__imp__SetThreadContext@8'];get_rows=[q for q in debug['relocations']if q['symbol']=='__imp__GetThreadContext@8']
    need(len(set_rows)==2 and len(get_rows)==1,'Exactly two actual compiled SetThreadContext calls and one whole GetThreadContext call')
    for q in set_rows:
        o=q['offset'];need(debug_bytes[o-6:o-2]==struct.pack('<I',0x10001) and debug_bytes[o-2:o]==bytes.fromhex('ff15'),'Each actual compiled SetThreadContext call immediately follows CONTEXT_CONTROL store')
    # All current source files actually compiled by this build are physically bound.
    readlog=pin(BUILD/'build-x86/mw34_joint_startup124_original.dir/Release/mw34_joi.79E99ED3.tlog/CL.read.1.tlog').read_text(encoding='utf-16')
    actual_headers=[p for p in PREP.iterdir() if p.suffix=='.hpp' and str(p).upper()in readlog.upper()]
    for p in actual_headers: need(str(p.resolve())in build['sources'],'Actual consumed header was build-pinned');pin(p)
    need(PREP/'hypot_trace.hpp' in actual_headers and PREP/'trace_points.hpp' in actual_headers and PREP/'api_imports.hpp' in actual_headers,'Actual current tracer headers consumed')
    pin(__file__);pin(R/'tools/analysis/pe.py');pin(sys.executable)
    out.mkdir();(out/'physical-instructions.json').write_text(json.dumps(physical,indent=2)+'\n');(out/'compiled-observer.json').write_text(json.dumps(linked,indent=2)+'\n')
    (out/'all-active-hooks.json').write_text(json.dumps(actual_hooks,indent=2)+'\n')
    for p in out.iterdir():pin(p)
    report=dict(passed=True,preparation_sha256=PH,build_sha256=BH,worker_sha256=build['worker_sha256'],trace_descriptors=3538,game_instructions=65,CRT_instructions=3473,physical_instruction_bytes=sum(r['width']for r in rows),descriptor_gaps=0,compiled_descriptor_bytes=len(descriptor),compiled_descriptor_VA=assigned['?hypot_trace_points@@3V?$array@UHypotTracePoint@@$0NNC@@std@@B'],compiled_functions=len(linked),compiler_only_unreferenced_helpers=omitted,compiler_TLS_section_relative_relocations=tls,compiler_TLS_directory=list(tls_words),compiled_function_bytes=sum(x['bytes']for x in linked),compiled_relocations=reloc_count,explicit_function_import_descriptor_relocations=typed,consumed_current_headers=len(actual_headers),provider_IAT_identities=145,corrected_string_rows=3,CONTROL_only_SetThreadContext_calls=2,full_stopped_CONTEXT_observation=True,raw_FP_metadata_preserved_in_observations=True,actual_genuine_run_bracket=True,normal_IAT_return_instrumentation_removed=True,trace_source_overlaps_inherited_FS_hooks=0,all_active_code_hooks=52,all_active_hook_family_overlaps=0,source_first_opcode_validation_before_any_patch=True,failed_old_execution_preserved=True,sequences=6,roots=1,phases=6,pages=43,record_bytes=356992,prelaunch_justified=True,guest_code_executed=False,archive_reader_opened=False,initializer_credit=False,native_credit=False,numerical_predictions_supplied=False,scope='Independent physical/source/compiler/link prelaunch only. Raw debugger CONTEXT/FP metadata is retained; only observed CONTROL registers are written back with authored EIP/TF changes. Each REP descriptor names potential per-iteration source operands; eventual trace validation must admit actual ECX/DF/count/control and valid reads, including zero-count suppression. External WinAPI internals, dormant/exception paths, actual numerical equivalence, loaded target/export provenance, whole live code-page snapshots, and initializer acceptance remain open until genuine execution and separate validation.',files=PINS)
    p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(p),sha256=sha(p),descriptors=3538,compiled_functions=len(linked),files=len(PINS))))

if __name__=='__main__':main(sys.argv[1])
