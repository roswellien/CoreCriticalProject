"""Independent saved-record check; never imports the differential oracle."""
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/m2-integration'
U32=(1<<32)-1
HEADER=struct.Struct('<8s4I')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def signed(value):return value-(1<<32) if value>=(1<<31) else value

def observation(words):
    eax,ecx,edx,ebx,esp,ebp,esi,edi,oldflags,eip,argument,global_value,ticks,choice,seed=words
    if choice not in (0,1) or eip!=0x10000000:raise ValueError('Unadmitted saved input')
    memory=bytearray((37*index+seed)%256 for index in range(8192))
    sp=esp-0x20001000
    def put(where,value):memory[where:where+4]=(value&U32).to_bytes(4,'little')
    def push(value):
        nonlocal sp
        sp-=4;put(sp,value)
    def pop():
        nonlocal sp
        value=int.from_bytes(memory[sp:sp+4],'little');sp+=4;return value
    def capture(offset):
        # Independently account for the actual authored PUSH/POP instrumentation.
        push(eax);put(4096+offset,int.from_bytes(memory[sp+4:sp+8],'little'));put(4096+offset+4,0x20001000+sp+4);pop()
    put(sp,0x10000100);put(sp+4,argument)
    for offset,value in ((0,global_value),(8,0x10000300),(12,0x10000500 if choice else 0x10000400),(16,ticks)):
        put(4096+offset,value)
    eax=argument;push(eax);push(0x1000000a);capture(0x40);eax=(eax+ecx)&U32
    if pop()!=0x1000000a:raise ValueError('Direct return simulation failed')
    sp+=4  # ECX member callee RET4.
    eax=(eax+global_value)&U32;put(4096+4,eax)
    push(0x1000001b);capture(0x48);eax=ticks
    if pop()!=0x1000001b:raise ValueError('Import return simulation failed')
    edx=eax;eax=argument;push(eax);push(0x10000028);capture(0x50);put(4096+0x58,choice)
    math_result=argument-ticks if choice else argument+ticks
    eax=math_result&U32
    if pop()!=0x10000028:raise ValueError('Indirect return simulation failed')
    sp+=4  # Cdecl caller cleans its argument, preserving arithmetic flags.
    put(4096+0x5c,7)
    if pop()!=0x10000100:raise ValueError('Outer return simulation failed')
    carry=int(argument<ticks) if choice else int(math_result>U32)
    auxiliary=int((argument&15)<(ticks&15)) if choice else int((argument&15)+(ticks&15)>15)
    signed_result=signed(argument)-signed(ticks) if choice else signed(argument)+signed(ticks)
    overflow=int(not (-(1<<31)<=signed_result<(1<<31)))
    parity=int(bin(eax&255).count('1')%2==0)
    flags=carry+4*parity+16*auxiliary+64*int(eax==0)+128*int(eax>=1<<31)+2048*overflow+(oldflags&1024)
    return struct.pack('<13I',eax,ecx,edx,ebx,0x20001000+sp,ebp,esi,edi,flags,0x10000100,0,3,4)+memory

def verify():
    comparison=json.loads((OUT/'comparison.json').read_text())
    build=json.loads((OUT/'build.json').read_text())
    if sha(OUT/'build.json')!=comparison['build_sha256']:raise ValueError('Build record changed')
    for name,value in build['source_hashes'].items():
        if sha(ROOT/name)!=value:raise ValueError('Source changed: '+name)
    raw=(OUT/'requests.bin').read_bytes()
    if sha(OUT/'requests.bin')!=comparison['input_sha256']:raise ValueError('Saved inputs changed')
    header=HEADER.unpack_from(raw);count=header[2]
    if header!=(b'MW34M2Q1',1,count,60,32) or len(raw)!=24+count*60:raise ValueError('Input extent/header')
    data={}
    for kind,bits in (('reference',32),('O0',64),('O2',64)):
        path=OUT/f'results-{kind}.bin';binary=path.read_bytes()
        if sha(path)!=comparison['result_sha256'][kind] or HEADER.unpack_from(binary)!=(b'MW34M2R1',1,count,8244,bits) or len(binary)!=24+count*8244:raise ValueError('Saved result identity/extent')
        data[kind]=binary
    for index in range(count):
        words=struct.unpack_from('<15I',raw,24+index*60)
        expected=observation(words)
        for kind,binary in data.items():
            observed=binary[24+index*8244:24+(index+1)*8244]
            if observed!=expected:raise ValueError(f'{kind} case{index} independent instruction/frame/oracle mismatch')
    report={'schema_version':1,'status':'passed','original_cases':count,'native_comparisons':count*2,
            'comparison_sha256':sha(OUT/'comparison.json'),'verifier_sha256':sha(Path(__file__)),
            'method':'separate unsigned/signed flag oracle and ordered stack/CALL/RET memory simulation; no comparator import',
            'zero_mismatches':True}
    (OUT/'independent-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return report

if __name__=='__main__':verify()
