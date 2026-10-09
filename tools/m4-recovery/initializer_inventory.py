"""Exact-image static inventory of every CRT initializer and its direct graph.

The linear decoder is a lookup source, not a closure claim. Each followed
instruction is byte-bound; direct relative targets are checked independently.
Indirect branches, exception/callback literals and decoding limits stay open.
This tool never executes or admits guest code.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import struct
import subprocess
import sys
from collections import Counter

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/analysis'))
from pe import PEImage, read_binary

IMAGE_SHA = '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
DECODER_SHA = 'a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a'
ROW = re.compile(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}[ ]*)+)\t(.+)$')
TARGET = re.compile(r'^0x([0-9a-f]+)(?:\s|$)')
IAT = re.compile(r'^dword ptr \[0x([0-9a-f]+)\]$')


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def bind(path):
    path = Path(path).resolve()
    return {'path':str(path), 'size_bytes':path.stat().st_size, 'sha256':sha(path)}


def relative(row):
    code = bytes.fromhex(row['bytes'])
    if len(code) == 5 and code[0] in (0xe8,0xe9):
        displacement = struct.unpack_from('<i',code,1)[0]
    elif len(code) == 2 and (code[0] == 0xeb or 0x70 <= code[0] <= 0x7f or 0xe0 <= code[0] <= 0xe3):
        displacement = struct.unpack_from('<b',code,1)[0]
    elif len(code) == 6 and code[0] == 0x0f and 0x80 <= code[1] <= 0x8f:
        displacement = struct.unpack_from('<i',code,2)[0]
    else:
        raise ValueError('Unsupported direct control encoding')
    target = TARGET.match(row['operands'])
    require(target is not None, 'Missing decoder direct destination')
    actual = (row['pc']+row['size']+displacement)&0xffffffff
    require(actual == int(target[1],16), 'Encoded destination disagrees with decoder')
    return actual


def walk(entry, rows, imports, executable, limit=8000):
    pending = [entry]
    visited, calls, services, unresolved, returns, literals = set(), [], [], [], [], []
    while pending:
        pc = pending.pop()
        if pc in visited:
            continue
        if len(visited) >= limit:
            unresolved.append({'pc':pc,'reason':'Instruction traversal limit'})
            break
        if pc not in rows or not executable(pc):
            unresolved.append({'pc':pc,'reason':'No validated instruction boundary in file-backed executable storage'})
            continue
        visited.add(pc)
        row = rows[pc]
        following = pc+row['size']
        mnemonic = row['mnemonic']
        if mnemonic in ('ret','retf'):
            returns.append({'pc':pc,'mnemonic':mnemonic,'operands':row['operands']})
            continue
        if mnemonic in ('int','int3','sysenter','syscall','iret','iretd','ud2','<unknown>','data16') or mnemonic.startswith('.'):
            unresolved.append({'pc':pc,'reason':'Instruction requires separate system/decoder contract','mnemonic':mnemonic})
            continue
        for literal in re.findall(r'0x([0-9a-f]+)',row['operands']):
            address = int(literal,16)
            if executable(address) and mnemonic not in ('call','jmp') and not mnemonic.startswith('j'):
                literals.append({'pc':pc,'value':address,'role':'Unclassified executable literal; possible callback, not resolved or admitted'})
        control = mnemonic in ('call','jmp') or mnemonic.startswith('j') or mnemonic.startswith('loop')
        if control:
            direct = TARGET.match(row['operands'])
            if direct:
                try:
                    target = relative(row)
                except ValueError as error:
                    unresolved.append({'pc':pc,'reason':str(error)})
                    continue
                if mnemonic == 'call':
                    calls.append({'site':pc,'target':target,'return_pc':following})
                    pending.append(following)
                elif mnemonic == 'jmp':
                    pending.append(target)
                else:
                    pending.extend((target,following))
                continue
            slot = IAT.fullmatch(row['operands'])
            if slot and int(slot[1],16) in imports:
                services.append({'site':pc,'kind':mnemonic,'iat':int(slot[1],16),'symbol':imports[int(slot[1],16)]})
                # Calls conservatively retain fallthrough; no imported
                # nonreturn or callback/service contract is implemented here.
                if mnemonic == 'call':
                    pending.append(following)
                elif mnemonic != 'jmp':
                    unresolved.append({'pc':pc,'reason':'Unsupported imported branch kind'})
                continue
            unresolved.append({'pc':pc,'reason':'Unresolved indirect control','mnemonic':mnemonic,'operands':row['operands']})
            if mnemonic == 'call':
                pending.append(following)
            continue
        pending.append(following)
    selected = [rows[pc] for pc in sorted(visited)]
    operations = Counter(row['mnemonic'] for row in selected)
    fp = [row['pc'] for row in selected if row['mnemonic'].startswith('f')]
    simd = [row['pc'] for row in selected if re.search(r'\b(?:xmm|mm)[0-9]+\b',row['operands']) or
            row['mnemonic'] in ('ldmxcsr','stmxcsr','emms')]
    fs = [row['pc'] for row in selected if 'fs:' in row['operands']]
    return {'entry':entry,'instruction_count':len(visited),'instruction_pcs':sorted(visited),
        'instruction_bytes_sha256':hashlib.sha256(b''.join(bytes.fromhex(row['bytes']) for row in selected)).hexdigest(),
        'direct_calls':calls,'import_sites':services,'unresolved_controls':unresolved,'returns':returns,
        'unclassified_executable_literals':literals,'mnemonics':dict(sorted(operations.items())),
        'FP_sites':fp,'MMX_SSE_sites':simd,'FS_sites':fs,
        'static_local_branch_decode_closed':not unresolved,
        'execution_or_translation_admitted':False}


def controls():
    # Authored encoded branches, independent hard-coded targets and graph
    # counts distinguish real relative decoding from decoder-text trust.
    loop = {
        0x1000:{'pc':0x1000,'size':2,'bytes':'75fe','mnemonic':'jne','operands':'0x1000'},
        0x1002:{'pc':0x1002,'size':1,'bytes':'c3','mnemonic':'ret','operands':''},
    }
    require(relative(loop[0x1000]) == 0x1000, 'Authored backward branch control')
    result = walk(0x1000,loop,{},lambda p:0x1000<=p<0x1010)
    require(result['instruction_count']==2 and result['static_local_branch_decode_closed'] and
            len(result['returns'])==1,'Authored loop/exit graph control')
    for bad in ({**loop[0x1000],'operands':'0x1002'}, {**loop[0x1000],'bytes':'6675fe','size':3}):
        try:
            relative(bad)
        except ValueError:
            pass
        else:
            raise ValueError('Malformed relative control accepted')
    bad = dict(loop)
    bad[0x1000] = {**loop[0x1000],'bytes':'7501','operands':'0x1003'}
    require(not walk(0x1000,bad,{},lambda p:True)['static_local_branch_decode_closed'],
            'Missing instruction boundary became complete')
    indirect={0x1000:{'pc':0x1000,'size':2,'bytes':'ffe0','mnemonic':'jmp','operands':'eax'}}
    require(not walk(0x1000,indirect,{},lambda p:True)['static_local_branch_decode_closed'],
            'Unknown indirect branch became complete')
    return 6


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--max-functions',type=int,default=1600)
    args=parser.parse_args()
    out=args.out.resolve()
    require(out.is_relative_to(ROOT/'reports') and not out.exists(),'Fresh ignored output required')
    require(144<=args.max_functions<=4000,'Invalid traversal bound')
    authored_checks=controls()
    source=ROOT/'MW3/Mech3.exe'
    require(sha(source)==IMAGE_SHA,'Unsupported original image')
    image=PEImage(read_binary(source))
    decoder=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
    require(sha(decoder)==DECODER_SHA,'Unreviewed instruction decoder')
    sections=[s for s in image.sections if s['executable']]
    def executable(pc):
        rva=pc-image.image_base
        return any(s['virtual_address']<=rva<s['virtual_address']+s['raw_size'] for s in sections)
    out.mkdir(parents=True)
    start=min(image.image_base+s['virtual_address'] for s in sections)
    end=max(image.image_base+s['virtual_address']+s['raw_size'] for s in sections)
    command=[str(decoder),'--disassemble','--x86-asm-syntax=intel',f'--start-address={start}',f'--stop-address={end}',str(source)]
    output=subprocess.run(command,capture_output=True,check=True,timeout=120)
    require(len(output.stdout)<=64*1024*1024,'Decoder output exceeded inventory limit')
    disassembly=out/'linear-lookup-only.txt'
    disassembly.write_bytes(output.stdout)
    rows={}
    for line in output.stdout.decode('utf-8').splitlines():
        match=ROW.match(line)
        if not match:
            continue
        pc=int(match[1],16);code=bytes.fromhex(match[2]);asm=re.sub(r'\s+',' ',match[3].strip())
        mnemonic,_,operands=asm.partition(' ')
        require(pc not in rows and 0<len(code)<=15,'Duplicate/invalid instruction decode')
        offset,_=image.rva_range(pc-image.image_base,len(code))
        require(image.read(offset,len(code))==code,'Instruction bytes differ from admitted file')
        rows[pc]={'pc':pc,'size':len(code),'bytes':code.hex(),'mnemonic':mnemonic,'operands':operands}
    imports={image.image_base+s['iat_rva']:{'library':library['library'],**s}
             for library in image.imports() for s in library['symbols']}
    roots=[{'slot':slot,'entry':image.rva_u32(slot-image.image_base)} for slot in range(0x5e0000,0x5e0244,4)]
    require(len(roots)==145 and sum(bool(r['entry']) for r in roots)==144,'Actual initializer table differs')
    pending=[r['entry'] for r in roots if r['entry']]
    functions={};deferred=[]
    while pending:
        entry=pending.pop(0)
        if entry in functions:
            continue
        if len(functions)>=args.max_functions:
            deferred.append(entry);continue
        if not executable(entry):
            deferred.append(entry);continue
        node=walk(entry,rows,imports,executable)
        functions[entry]=node
        pending.extend(call['target'] for call in node['direct_calls'] if call['target'] not in functions)
    summaries=[]
    for root in roots:
        if not root['entry']:
            summaries.append({**root,'kind':'null_slot_originally_skipped'});continue
        todo=[root['entry']];seen=set();missing=[]
        while todo:
            pc=todo.pop()
            if pc in seen:continue
            seen.add(pc)
            if pc not in functions:missing.append(pc);continue
            todo.extend(call['target'] for call in functions[pc]['direct_calls'])
        nodes=[functions[pc] for pc in seen if pc in functions]
        unresolved=sum(len(n['unresolved_controls']) for n in nodes)
        service_count=sum(len(n['import_sites']) for n in nodes)
        summaries.append({**root,'kind':'initializer','conditional_local_entries':len(nodes),
            'unique_reachable_instruction_count':len({pc for n in nodes for pc in n['instruction_pcs']}),
            'unresolved_control_count':unresolved,'deferred_entries':missing,'import_site_count':service_count,
            'unclassified_executable_literals':sum(len(n['unclassified_executable_literals']) for n in nodes),
            'FP_instruction_count':len({pc for n in nodes for pc in n['FP_sites']}),
            'FS_instruction_count':len({pc for n in nodes for pc in n['FS_sites']}),
            'direct_branch_graph_import_free':not missing and not unresolved and not service_count,
            'full_dependency_closure_claimed':False,'game_execution_admitted':False})
    (out/'instruction-lookup.json').write_text(json.dumps(rows,separators=(',',':'))+'\n',encoding='utf-8')
    (out/'function-graphs.json').write_text(json.dumps(functions,indent=2)+'\n',encoding='utf-8')
    report={'schema_version':1,'scope':'Static all-initializer workload inventory; no native execution or full closure acceptance',
        'passed':True,'image':bind(source),'decoder':bind(decoder),'source':bind(Path(__file__)),
        'PE_parser':bind(ROOT/'tools/analysis/pe.py'),'command':command,'decoder_output':bind(disassembly),
        'authored_controls':authored_checks,'table_slots':145,'nonzero_roots':144,
        'direct_graph_nodes':len(functions),'deferred_local_entries':sorted(set(deferred)),
        'instruction_lookup_count':len(rows),'roots':summaries,
        'import_free_direct_graph_roots':sum(r.get('direct_branch_graph_import_free',False) for r in summaries),
        'FP_roots':sum(bool(r.get('FP_instruction_count')) for r in summaries),
        'FS_roots':sum(bool(r.get('FS_instruction_count')) for r in summaries),
        'limits':['Linear instruction lookup may fail a legitimate overlapping/misaligned code entry; any such edge stays unresolved.',
            'Normal branch/call fallthrough is conservative; imported nonreturn behavior and SEH filter/handler roots are not implemented.',
            'Executable literals may be callbacks; their dispatch and virtual object/vtable targets remain unclassified.',
            'Import-free direct graphs alone do not prove complete callback/SEH/service dependencies or translation readiness.',
            'No original game or provider instruction was executed; M4 completion is not claimed.']}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    artifacts=[bind(p) for p in sorted(out.iterdir()) if p.is_file()]
    (out/'pins.json').write_text(json.dumps({'schema_version':1,'bindings':artifacts+
        [report[k] for k in ('image','decoder','source','PE_parser')]},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('passed','nonzero_roots','direct_graph_nodes','import_free_direct_graph_roots','FP_roots','FS_roots')}))


if __name__=='__main__':
    main()
