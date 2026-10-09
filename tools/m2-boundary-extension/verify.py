"""Independent saved-record check; never imports the differential oracle."""
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/m2-boundary-extension'
U32=(1<<32)-1
HEADER=struct.Struct('<8s4I')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def signed(value):return value-(1<<32) if value>=(1<<31) else value

def observation(words, timer_return=None, iat_target=0x10000300):
    eax,ecx,edx,ebx,esp,ebp,esi,edi,oldflags,eip,argument,global_value,ticks,choice,seed=words
    if choice not in (0,1) or eip!=0x10000000:raise ValueError('Unadmitted saved input')
    request_ticks=ticks
    if timer_return is not None:ticks=timer_return
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
    for offset,value in ((0,global_value),(8,iat_target),(12,0x10000500 if choice else 0x10000400),(16,request_ticks),(0x60,0),(0x64,0)):
        put(4096+offset,value)
    eax=argument;push(eax);eax=0xa5a5f00d;push(0x1000000f);capture(0x40)
    eax=int.from_bytes(memory[sp+4:sp+8],'little')  # Actual callee stack load.
    eax=(eax+ecx)&U32
    if pop()!=0x1000000f:raise ValueError('Direct return simulation failed')
    sp+=4  # ECX member callee RET4.
    eax=(eax+global_value)&U32;put(4096+4,eax)
    push(0x10000020);capture(0x48);put(4096+0x60,1);put(4096+0x64,1);eax=ticks
    if pop()!=0x10000020:raise ValueError('Import return simulation failed')
    edx=eax;eax=argument;push(eax);push(0x1000002d);capture(0x50);put(4096+0x58,choice)
    math_result=argument-ticks if choice else argument+ticks
    eax=math_result&U32
    if pop()!=0x1000002d:raise ValueError('Indirect return simulation failed')
    sp+=4  # Cdecl caller cleans its argument, preserving arithmetic flags.
    put(4096+0x5c,7)
    if pop()!=0x10000100:raise ValueError('Outer return simulation failed')
    carry=int(argument<ticks) if choice else int(math_result>U32)
    auxiliary=int((argument&15)<(ticks&15)) if choice else int((argument&15)+(ticks&15)>15)
    signed_result=signed(argument)-signed(ticks) if choice else signed(argument)+signed(ticks)
    overflow=int(not (-(1<<31)<=signed_result<(1<<31)))
    parity=int(bin(eax&255).count('1')%2==0)
    flags=carry+4*parity+16*auxiliary+64*int(eax==0)+128*int(eax>=1<<31)+2048*overflow+(oldflags&1024)
    return struct.pack('<16I',eax,ecx,edx,ebx,0x20001000+sp,ebp,esi,edi,flags,0x10000100,0,3,4,1,1,ticks)+memory

def verify():
    comparison=json.loads((OUT/'comparison.json').read_text())
    build=json.loads((OUT/'build.json').read_text())
    if sha(OUT/'build.json')!=comparison['build_sha256']:raise ValueError('Build record changed')
    for name,value in build['source_hashes'].items():
        if sha(ROOT/name)!=value:raise ValueError('Source changed: '+name)
    for name,value in build['artifacts'].items():
        if sha(OUT/name)!=value:raise ValueError('Artifact changed: '+name)
    for kind,worker in build['workers'].items():
        if sha(Path(worker['path']))!=worker['sha256']:raise ValueError('Actual worker changed')
    raw=(OUT/'requests.bin').read_bytes()
    if sha(OUT/'requests.bin')!=comparison['input_sha256']:raise ValueError('Saved inputs changed')
    header=HEADER.unpack_from(raw);count=header[2]
    if header!=(b'MW34BEXQ',1,count,60,32) or len(raw)!=24+count*60:raise ValueError('Input extent/header')
    data={}
    for kind,bits in (('reference',32),('O0',64),('O2',64)):
        path=OUT/f'results-{kind}.bin';binary=path.read_bytes()
        if sha(path)!=comparison['result_sha256'][kind] or HEADER.unpack_from(binary)!=(b'MW34BEXR',1,count,8256,bits) or len(binary)!=24+count*8256:raise ValueError('Saved result identity/extent')
        data[kind]=binary
    for index in range(count):
        words=struct.unpack_from('<15I',raw,24+index*60)
        expected=observation(words)
        for kind,binary in data.items():
            observed=binary[24+index*8256:24+(index+1)*8256]
            if observed!=expected:raise ValueError(f'{kind} case{index} independent instruction/frame/oracle mismatch')
    live=json.loads((OUT/'live-comparison.json').read_text());live_raw=(OUT/'live-requests.bin').read_bytes()
    if live['build_sha256']!=sha(OUT/'build.json') or sha(OUT/'live-requests.bin')!=live['requests_sha256'] or HEADER.unpack_from(live_raw)!=(b'MW34BEXQ',1,8,60,32) or len(live_raw)!=504:raise ValueError('Live input/build changed')
    for kind,bits in (('reference',32),('O0',64),('O2',64)):
        binding=live['workers'][kind];path=OUT/f'live-results-{kind}.bin';binary=path.read_bytes();meta_path=OUT/f'live-worker-{kind}.json';metadata=json.loads(meta_path.read_text())
        if sha(path)!=binding['results_sha256'] or sha(meta_path)!=binding['metadata_sha256'] or binding['worker_sha256']!=build['workers'][kind]['sha256']:raise ValueError('Live worker/result binding changed')
        if sha(Path(binding['provider_module']['path']))!=binding['provider_module']['sha256']:raise ValueError('Live provider image changed')
        if HEADER.unpack_from(binary)!=(b'MW34BEXR',1,8,8256,bits) or len(binary)!=24+8*8256:raise ValueError('Live result extent/header')
        if metadata['provider']!='WINMM.timeGetTime' or metadata['provider_calls']!=8 or metadata['bridge_calls']!=8:raise ValueError('Live provider counters')
        if bits==32 and (metadata['shim_rva']!=build['original_shim_rva'] or metadata['guest_iat_target']!=metadata['executable_base']+metadata['shim_rva']):raise ValueError('Original selected shim identity')
        ticks=[]
        for index in range(8):
            words=struct.unpack_from('<15I',live_raw,24+index*60);actual=binary[24+index*8256:24+(index+1)*8256]
            if words[8]&1024 or words[12]!=0:raise ValueError('Live DF/provider input admission')
            tick=int.from_bytes(actual[60:64],'little');wanted=observation(words,tick,metadata['guest_iat_target'])
            if actual!=wanted:raise ValueError(f'Live {kind} case{index} independent frame/CPU/provider/page mismatch')
            ticks.append(tick)
        if any(not (0<(b-a)&U32<=10000) for a,b in zip(ticks,ticks[1:])):raise ValueError('Independent live DWORD progress')
    report={'schema_version':1,'status':'passed','original_cases':count,'native_comparisons':count*2,
            'comparison_sha256':sha(OUT/'comparison.json'),'verifier_sha256':sha(Path(__file__)),
            'live_original_cases':8,'live_native_cases':16,'live_comparison_sha256':sha(OUT/'live-comparison.json'),
            'build_sha256':sha(OUT/'build.json'),'source_identity':build['source_identity'],
            'method':'separate unsigned/signed flag oracle and ordered stack/CALL/RET memory simulation; no comparator import',
            'zero_mismatches':True}
    (OUT/'independent-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return report

if __name__=='__main__':verify()
