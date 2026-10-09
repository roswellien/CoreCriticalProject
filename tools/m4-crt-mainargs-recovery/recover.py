"""Static literal staged __getmainargs recovery and native object preparation.

No provider/game code is executed. Outgoing calls remain typed bridge stops.
"""
import ctypes as c
import hashlib
import json
import pathlib
import re
import struct
import subprocess
import sys
import traceback

sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-mainargs'
sys.path.insert(0, str(ROOT / 'tools/m4-crt'))
from recover_provider import PE, IMAGE_SHA, PROVIDER_SHA
sys.path.insert(0, str(ROOT / 'tools/lifting'))
from host_adapter import LLVM, HOST_LAYOUT, FUNCTION_INDEX, checked_state_offsets

ROOTS = {
    'mainargs': 0x7800BA5E,
    'normal_argv': 0x7800BBBC,
    'wildcard_argv': 0x7800B3B4,
    'normal_parser': 0x7800BC48,
    'wildcard_parser': 0x7800B451,
}
BRIDGES = {
    '__remill_read_memory_8', '__remill_read_memory_32',
    '__remill_write_memory_8', '__remill_write_memory_32',
    '__remill_function_call', '__remill_function_return',
}

def need(value, why):
    if not value:
        raise ValueError(why)

def sha(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def decode(data, pe):
    result = {}
    for line in data.decode().splitlines():
        m = re.match(r'^\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)$', line)
        if not m:
            continue
        address = int(m[1], 16)
        body = bytes.fromhex(m[2])
        need(address not in result, 'Unique instruction starts')
        need(pe.read(address-pe.base, len(body)) == body, 'Exact decoder source bytes')
        need(any(va <= address-pe.base and address-pe.base+len(body) <= va+min(vs, rs)
                 and flags & 0xE0000000 == 0x60000000
                 for va, vs, rs, rp, flags in pe.sections), 'File-backed RX instruction')
        result[address] = dict(address=address, size=len(body), bytes=body.hex(),
                               mnemonic=m[3], operands=m[4].strip())
    return result

def branch(i):
    raw = bytes.fromhex(i['bytes'])
    end = i['address']+len(raw)
    if raw[0] in (0xE8, 0xE9):
        need(len(raw) == 5, 'rel32 width')
        return end+struct.unpack_from('<i', raw, 1)[0]
    if raw[0] == 0xEB or 0x70 <= raw[0] <= 0x7F:
        need(len(raw) == 2, 'rel8 width')
        return end+struct.unpack_from('<b', raw, 1)[0]
    if raw[0] == 0x0F and 0x80 <= raw[1] <= 0x8F:
        need(len(raw) == 6, 'conditional rel32 width')
        return end+struct.unpack_from('<i', raw, 2)[0]
    return None

def graph(instructions, entry, imports):
    """Close every local branch while retaining calls as explicit dependencies."""
    pending, seen, edges, calls, returns = [entry], set(), [], [], []
    while pending:
        address = pending.pop()
        if address in seen:
            continue
        need(address in instructions, 'Missing source CFG instruction '+hex(address))
        need(len(seen) < 4096, 'Bounded local CFG')
        seen.add(address)
        i = instructions[address]
        m, end, raw = i['mnemonic'], address+i['size'], bytes.fromhex(i['bytes'])
        if m in ('ret', 'retl'):
            returns.append(address)
            continue
        if m == 'call':
            target = branch(i)
            if target is not None:
                calls.append(dict(site=address, target=target, return_PC=end, kind='direct'))
            else:
                need(raw[:2] == b'\xff\x15' and len(raw) == 6, 'Named IAT call only '+hex(address))
                slot = struct.unpack_from('<I', raw, 2)[0]
                need(slot in imports, 'Exact provider IAT owner')
                calls.append(dict(site=address, iat=slot, return_PC=end, kind='import', owner=imports[slot]))
            edges.append(dict(source=address, target=end, kind='call-continuation'))
            pending.append(end)
        elif m == 'jmp' or m.startswith('j'):
            target = branch(i)
            need(target is not None, 'No unreviewed indirect branch '+hex(address))
            edges.append(dict(source=address, target=target, kind='branch'))
            pending.append(target)
            if m != 'jmp':
                edges.append(dict(source=address, target=end, kind='fallthrough'))
                pending.append(end)
        else:
            edges.append(dict(source=address, target=end, kind='fallthrough'))
            pending.append(end)
    need(returns, 'Local closure has a source RET')
    begin, end = min(seen), max(a+instructions[a]['size'] for a in seen)
    need(begin == entry, 'Function local CFG stays after entry')
    owned = set()
    for address in seen:
        for byte in range(address, address+instructions[address]['size']):
            need(byte not in owned, 'No overlapping instruction paths')
            owned.add(byte)
    need(len(owned) == end-begin, 'Complete contiguous function instruction coverage')
    return dict(entry=entry, end_exclusive=end, source_bytes=end-begin,
                instructions=[instructions[a] for a in sorted(seen)],
                instruction_count=len(seen), edges=edges, outgoing_calls=sorted(calls, key=lambda v:v['site']),
                returns=sorted(returns), complete_local_CFG=True,
                complete_dependency_closure=False)

def main(name):
    out = BASE / name
    need(name.startswith('recovery-') and out.parent == BASE and not out.exists(), 'Fresh private recovery directory')
    out.mkdir(parents=True)
    commands, files = [], {}
    def pin(path):
        p = pathlib.Path(path).resolve()
        files[str(p)] = sha(p)
        return p
    def run(program, args, stem):
        p = pin(program)
        r = subprocess.run([str(p), *args], capture_output=True)
        (out/(stem+'.stdout')).write_bytes(r.stdout)
        (out/(stem+'.stderr')).write_bytes(r.stderr)
        commands.append(dict(program=str(p), arguments=args, exit_code=r.returncode))
        need(r.returncode == 0, stem+' succeeded')
        return r.stdout
    try:
        provider = PE(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'), PROVIDER_SHA)
        game = PE(pin(ROOT/'MW3/Mech3.exe'), IMAGE_SHA)
        exports = provider.exports()
        need(exports['__getmainargs']['address'] == ROOTS['mainargs'], 'Exact export address')
        slot = [v for v in game.imports() if v.get('name') == '__getmainargs' and v['library'].casefold() == 'msvcrt.dll']
        need(len(slot) == 1 and slot[0]['iat'] == 0x5BB514, 'Unique actual game IAT owner')
        raw_iat = struct.unpack('<I', game.read(0x5BB514-game.base, 4))[0]
        need(raw_iat == 0x1DED02, 'Literal raw game IAT')
        llvm = ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
        decoded = run(llvm/'llvm-objdump.exe', ['-d', '--x86-asm-syntax=intel', str(provider.path)], 'provider-decode')
        instructions = decode(decoded, provider)
        imports = {v['iat']:v for v in provider.imports()}
        graphs = {n:graph(instructions, e, imports) for n,e in ROOTS.items()}
        need(graphs['mainargs']['end_exclusive'] == 0x7800BAA0 and graphs['mainargs']['instruction_count'] == 21, 'Complete export66 bytes')
        need(graphs['normal_argv']['end_exclusive'] == 0x7800BC48, 'Normal builder140 bytes')
        need(graphs['wildcard_argv']['end_exclusive'] == 0x7800B451, 'Wildcard builder157 bytes')
        need(graphs['normal_parser']['end_exclusive'] == 0x7800BDFC, 'Normal parser436 bytes')
        call = graphs['normal_argv']['outgoing_calls'][0]
        need(call['site'] == 0x7800BBD0 and call['iat'] == 0x7802E018 and call['owner']['name'] == 'GetModuleFileNameA', 'First normal required OS dependency')
        frame_rows = []
        for level in ('O0','O2'):
            for row in range(24):
                phase = ROOT/f'reports/m4-crt-entry-initterm/execution-r2/{level}/row-{row}/entry-after-fault'
                stack = pin(phase/f'page-{0x20001000}.bin').read_bytes()
                state_cpu = pin(phase/'state-cpu.bin').read_bytes()
                runtime_cpu = pin(phase/'runtime-cpu.bin').read_bytes()
                s, r = struct.unpack('<10I', state_cpu), struct.unpack('<10I', runtime_cpu)
                words = struct.unpack_from('<6I', stack, 0x860)
                need(s[4] == 0x20001860 and s[9] == 0x1DED02 and r[4] == 0x20001864 and r[9] == 0x5AC468, 'Accepted stopped frame')
                need(words == (0x5AC46E,0x2000189C,0x2000188C,0x20001898,0,0x20001890), 'Actual five game arguments')
                need(struct.unpack_from('<I', stack, 0x890)[0] == 0, 'Actual startupinfo DWORD zero')
                frame_rows.append(dict(level=level, row=row, StateESP=s[4], StatePC=s[9], RuntimeESP=r[4], RuntimePC=r[9], words=list(words), startupinfo_value=0))
        globals = []
        for address, role in ((0x78037150,'startup new-mode'), (0x78037174,'command-line pointer'), (0x78038EF4,'argc'), (0x7803B3D8,'argv'), (0x78037C04,'environment pointer'), (0x7803B3E0,'program-name pointer')):
            value = struct.unpack('<I', provider.read(address-provider.base,4))[0]
            refs = [i for i in instructions.values() if re.search(r'(?<![0-9a-f])0x'+format(address,'x')+r'(?![0-9a-f])', i['operands'])]
            globals.append(dict(address=address, role=role, raw_value=value, raw_offset=provider.offset(address-provider.base,4), direct_source_references=refs, initialized_value_admitted=False, exhaustive_alias_proof=False))
        for n,g in graphs.items():
            body = provider.read(g['entry']-provider.base,g['source_bytes'])
            (out/(n+'-source.bin')).write_bytes(body)
            g['source_sha256'] = sha(out/(n+'-source.bin'))
            g['raw_offset'] = provider.offset(g['entry']-provider.base,g['source_bytes'])
        controls = []
        for label, address in (('missing-export-zero-branch',0x7800BA99), ('missing-normal-import',0x7800BBD0), ('missing-normal-parser-tail',0x7800BDFB)):
            corrupted = dict(instructions)
            corrupted.pop(address)
            entry = ROOTS['mainargs'] if address == 0x7800BA99 else ROOTS['normal_argv'] if address == 0x7800BBD0 else ROOTS['normal_parser']
            try:
                graph(corrupted,entry,imports)
            except ValueError as e:
                controls.append(dict(name=label,rejected=True,reason=str(e)))
            else:
                raise ValueError('Static corruption accepted '+label)
        (out/'source-CFG.json').write_text(json.dumps(dict(graphs=graphs,controls=controls),indent=2)+'\n')
        (out/'accepted-frame-evidence.json').write_text(json.dumps(dict(scope='Previously accepted native stop snapshots; not original x86 BEFORE this export',rows=frame_rows),indent=2)+'\n')
        (out/'global-prerequisites.json').write_text(json.dumps(dict(globals=globals),indent=2)+'\n')
        lift = pin(ROOT/'local/tools/remill-x87-control-repair/remill-lift-control-21.exe')
        sem = pin(ROOT/'local/tools/remill-x87-control-repair/semantics/x86.bc')
        need(sha(sem) == '618707dcbc2db87233c821551abb6921f2a72fd8375aa41c20fedd97bf4e45ca', 'Pinned semantics')
        dll = pin(llvm/'LLVM-C.dll')
        need(sha(dll) == '34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb', 'Pinned LLVM API')
        upstream = pin(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp').read_text()
        native = {}
        for n,g in graphs.items():
            body = (out/(n+'-source.bin')).read_bytes()
            run(lift, ['--arch=x86','--os=windows','--address='+str(g['entry']), '--entry_address='+str(g['entry']), '--bytes='+body.hex(),'--semantics_dir='+str(sem.parent),'--ir_out='+str(out/(n+'-guest.ll'))], n+'-lift')
            native[n] = lower(out,n,g,dll,upstream,run,llvm)
        header = '#pragma once\n#include <cstdint>\n#include <remill/Arch/X86/Runtime/State.h>\n// Static recovered objects only; dependency dispatch and execution are not admitted.\nextern "C" {\n'
        for n,g in graphs.items():
            header += f'void* mw34_mainargs_{n}_body(State*, std::uint32_t, void*);\n'
        header += '}\nstatic_assert(sizeof(State)==3504 && alignof(State)==8);\n'
        (out/'recovered-provider.hpp').write_text(header)
        report = dict(passed=True,scope='Complete literal export and direct parser/builder source recovery plus static x64 COFF preparation only',export=exports['__getmainargs'],game_import=slot[0],raw_game_IAT=raw_iat,graphs={n:{k:v for k,v in g.items() if k not in ('instructions','edges')} for n,g in graphs.items()},native=native,decoded_source_instructions=len(instructions),observed_prior_native_frames=48,original_x86_getmainargs_BEFORE_observed=False,proposed_boundary=dict(source_call=0x5AC468,provider_entry=ROOTS['mainargs'],zero_wildcard_CALL=0x7800BA99,zero_wildcard_target=ROOTS['normal_argv'],first_required_import=call,normal_arg_buffer=0x7803B3F0,normal_arg_buffer_capacity=260,successful_outputs_admitted=False),prerequisites=['Literal bounded helper prefix can reach GetModuleFileNameA without reading command-line state','Successful normal parser requires an owned initialized command-line buffer or admitted program-name fallback','Allocator and guest argv ownership must be measured and implemented','Environment producer must initialize78037C04 before successful export copyout','Provider raw globals alone do not authorize initialized data'],commands=commands,ordinary_game_launched=False,original_executed=False,native_body_executed=False,startup_integrated=False,whole_M4_complete=False)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        for p in [pathlib.Path(__file__),ROOT/'tools/m4-crt/recover_provider.py',ROOT/'tools/lifting/host_adapter.py',pathlib.Path(sys.executable),*out.iterdir()]:
            if p.is_file():
                pin(p)
        (out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
        print(json.dumps(dict(passed=True,source_functions=len(graphs),native_objects=2*len(native),bindings=len(files),report_sha256=sha(out/'report.json'))))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc())
        raise

def lower(out,name,source_graph,dll,upstream,run,llvm):
    entry=source_graph['entry']
    direct_targets={v['target'] for v in source_graph['outgoing_calls'] if v['kind']=='direct'}
    guest = out/(name+'-guest.ll')
    text = guest.read_text()
    need(re.findall(r'^define ptr @([^ (]+)',text,re.M) == [f'sub_{entry:x}'] and '__remill_missing_block' not in text, 'Exactly one complete lifted local function')
    api = LLVM(dll)
    ctx = api.ContextCreate()
    module,buffer,error = c.c_void_p(),c.c_void_p(),c.c_void_p()
    api.check(api.CreateMemoryBufferWithContentsOfFile(str(guest).encode(),c.byref(buffer),c.byref(error)),error)
    api.check(api.ParseIRInContext(ctx,buffer,c.byref(module),c.byref(error)),error)
    gd,hd = api.CreateTargetData(api.GetDataLayoutStr(module)),api.CreateTargetData(HOST_LAYOUT.encode())
    layouts = {}
    for n in re.findall(r'^%([^ =]+) = type',text,re.M):
        ty = api.GetTypeByName2(ctx,n.encode())
        def layout(d):
            return dict(size=api.ABISizeOfType(d,ty),alignment=api.ABIAlignmentOfType(d,ty),offsets=[api.OffsetOfElement(d,ty,i) for i in range(api.CountStructElementTypes(ty))])
        a,b = layout(gd),layout(hd)
        need(a==b,'All guest/host structure layouts equal '+n)
        layouts[n]=a
    need(len(layouts)==34 and layouts['struct.State']['size']==3504 and layouts['struct.State']['alignment']==8,'Full34 layouts and State3504')
    offsets = checked_state_offsets(api,api.GetNamedFunction(module,f'sub_{entry:x}'.encode()),gd)
    builder = api.CreateBuilderInContext(ctx)
    api.dll.LLVMSetLinkage.restype=None
    api.dll.LLVMSetLinkage.argtypes=[c.c_void_p,c.c_uint]
    api.dll.LLVMSetValueName2.restype=None
    api.dll.LLVMSetValueName2.argtypes=[c.c_void_p,c.c_char_p,c.c_size_t]
    helpers,bridges = {},set()
    for fn in list(api.iterate(api.GetFirstFunction(module),api.GetNextFunction)):
        n = api.name(fn)
        if n.startswith('__remill_flag_computation_') or n.startswith('__remill_compare_'):
            need(not api.CountBasicBlocks(fn) and api.signature(fn)==('i1',['i1']),'Pure annotation signature')
            need(re.search(r'bool '+re.escape(n)+r'\(bool result(?:, \.\.\.)?\)\s*\{\s*return result;\s*}',upstream),'Exact upstream identity '+n)
            block=api.AppendBasicBlockInContext(ctx,fn,b'identity')
            api.PositionBuilderAtEnd(builder,block)
            api.BuildRet(builder,api.GetParam(fn,0))
            api.dll.LLVMSetLinkage(fn,8)
            helpers[n]='upstream bool identity, internal linkage'
        elif n.startswith('__remill_undefined_'):
            need(n=='__remill_undefined_8','Undefined scalar8 only')
            renamed=('mw34_mainargs_'+name+'_undefined_8').encode()
            api.dll.LLVMSetValueName2(fn,renamed,len(renamed))
            bridges.add(renamed.decode())
        elif n.startswith('llvm.'):
            need(n in ('llvm.ctpop.i8','llvm.ctpop.i32','llvm.fshl.i32','llvm.fshr.i32'),'Reviewed LLVM integer intrinsic '+n)
        elif n == f'sub_{entry:x}':
            renamed=('mw34_mainargs_'+name+'_body').encode()
            api.dll.LLVMSetValueName2(fn,renamed,len(renamed))
        else:
            direct=re.fullmatch(r'sub_([0-9a-f]+)',n)
            need(n in BRIDGES or (direct and int(direct[1],16) in direct_targets and api.signature(fn)==('ptr',['ptr','i32','ptr']) and not api.CountBasicBlocks(fn)),'Bounded memory/control or exact direct source bridge '+n)
            bridges.add(n)
        api.SetFunctionCallConv(fn,0)
        for attr in (b'nounwind',b'willreturn'):
            api.RemoveEnumAttributeAtIndex(fn,FUNCTION_INDEX,api.GetEnumAttributeKindForName(attr,len(attr)))
        for attr in (b'target-cpu',b'target-features'):
            api.RemoveStringAttributeAtIndex(fn,FUNCTION_INDEX,attr,len(attr))
        for block in api.iterate(api.GetFirstBasicBlock(fn),api.GetNextBasicBlock):
            for inst in api.iterate(api.GetFirstInstruction(block),api.GetNextInstruction):
                need(not api.IsAIntToPtrInst(inst) and not api.IsAPtrToIntInst(inst),'No raw guest/host address casts')
                if api.IsACallInst(inst):
                    need(api.IsAFunction(api.GetCalledValue(inst)),'Only named LLVM calls')
                    api.SetInstructionCallConv(inst,0)
                    for attr in (b'nounwind',b'willreturn'):
                        api.RemoveCallSiteEnumAttribute(inst,FUNCTION_INDEX,api.GetEnumAttributeKindForName(attr,len(attr)))
    api.SetTarget(module,b'x86_64-pc-windows-msvc')
    api.SetDataLayout(module,HOST_LAYOUT.encode())
    api.check(api.VerifyModule(module,2,c.byref(error)),error)
    host=out/(name+'-host.ll')
    api.check(api.PrintModuleToFile(module,str(host).encode(),c.byref(error)),error)
    api.DisposeBuilder(builder);api.DisposeTargetData(gd);api.DisposeTargetData(hd);api.DisposeModule(module);api.ContextDispose(ctx)
    objects={}
    for level in ('O0','O2'):
        obj=out/(name+'-'+level+'.obj')
        run(llvm/'clang.exe',['--target=x86_64-pc-windows-msvc','-'+level,'-c',str(host),'-o',str(obj)],name+'-compile-'+level)
        objects[level]=dict(path=str(obj.resolve()),sha256=sha(obj))
        run(llvm/'llvm-nm.exe',['--undefined-only',str(obj)],name+'-undefined-'+level)
    return dict(host_sha256=sha(host),layouts=layouts,State_offsets=offsets,helpers=helpers,bridges=sorted(bridges),objects=objects,execution_admitted=False)

if __name__ == '__main__':
    main(sys.argv[1])
