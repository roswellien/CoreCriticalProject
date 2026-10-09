"""Independent exact register/flag/page/call-frame oracle and saved-record replay."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
from build import OUT, ROOT, FIXTURE_HASH, GAME_HASH, LLVM, REMILL, sha, BLOCKS
from adapt import REVIEWED_IR

MASK=0xffffffff
STACK=0x20001000
DATA=0x21001000
CODE=0x10000000
REQ=struct.Struct('<15I')
RES_SIZE=8256
HEADER=struct.Struct('<8s4I')

def flags(a,b,sub):
    r=(a-b if sub else a+b)&MASK
    cf=int(a<b) if sub else int(a+b>MASK)
    af=int(bool((a^b^r)&0x10))
    of=int(bool(((a^b)&(a^r) if sub else (~(a^b)&(a^r)))&0x80000000))
    return cf|(int((r&255).bit_count()%2==0)<<2)|(af<<4)|(int(r==0)<<6)|((r>>31)<<7)|(of<<11)

def expected(q, actual_timer=None, iat_target=CODE+0x300):
    regs=list(q[:8]);inflags=q[8];arg,g,timer,choice,seed=q[10:]
    if choice not in (0,1):raise ValueError('Oracle rejects unknown selector')
    esp=regs[4]
    if actual_timer is not None: timer=actual_timer
    mem=bytearray((i*37+seed)&255 for i in range(8192))
    def store(off,v):struct.pack_into('<I',mem,off,v&MASK)
    frame=esp-STACK
    store(frame,CODE+0x100);store(frame+4,arg)
    store(4096,g);store(4096+8,iat_target);store(4096+12,CODE+(0x500 if choice else 0x400));store(4096+16,q[12])
    # Actual CALL/PUSH/RET instructions leave these words in the original page.
    store(frame-4,arg);store(frame-8,CODE+0x2d);store(frame-12,arg)
    store(4096+4,arg+regs[1]+g)
    for off,v in ((0x40,CODE+0xf),(0x44,esp-8),(0x48,CODE+0x20),(0x4c,esp-4),(0x50,CODE+0x2d),(0x54,esp-8),(0x58,choice),(0x5c,7),(0x60,1),(0x64,1)):
        store(4096+off,v)
    regs[0]=(arg-timer if choice else arg+timer)&MASK;regs[2]=timer;regs[4]=esp+4
    flagword=flags(arg,timer,bool(choice))|(inflags&0x400)
    return struct.pack('<16I',*regs,flagword,CODE+0x100,0,3,4,1,1,timer)+mem

def validate_build():
    record=json.loads((OUT/'build.json').read_text())
    if record['fixture_sha256']!=FIXTURE_HASH or sha(OUT/'calls.bin')!=FIXTURE_HASH:
        raise ValueError('Fixture identity changed')
    for name,expected_hash in record['source_hashes'].items():
        if sha(ROOT/name)!=expected_hash:raise ValueError('Source changed: '+name)
    if hashlib.sha256(json.dumps(record['source_hashes'],sort_keys=True,separators=(',',':')).encode()).hexdigest()!=record['source_identity']:raise ValueError('Source map identity changed')
    for name,expected_hash in record['artifacts'].items():
        if sha(OUT/name)!=expected_hash:raise ValueError('Generated artifact changed: '+name)
    for value in record['workers'].values():
        if sha(value['path'])!=value['sha256']:raise ValueError('Worker changed')
    for name,identity in record['worker_evidence'].items():
        if sha(OUT/name)!=identity:raise ValueError('Worker PE evidence changed')
    if sha(record['original_link_map']['path'])!=record['original_link_map']['sha256']:raise ValueError('Original shim link map changed')
    provider=record['provider_contract']
    if provider['identities']!=['deterministic-uint32','WINMM.timeGetTime'] or provider['provider_calls_per_case']!=1 or provider['bridge_calls_per_case']!=1 or provider['guest_host_pointer_casts']!=0 or provider['live_requests']!=8 or provider['live_df']!=0 or provider['live_unused_timer']!=0:raise ValueError('Provider contract changed')
    for name,expected_hash in record['tools'].items():
        if sha(LLVM/name)!=expected_hash:raise ValueError('Tool changed: '+name)
    if record['remill_commit']!='0e324aee8c67a63ec759ef379dcfafa0b3cb1448' or subprocess.check_output(['git','-C',str(REMILL),'rev-parse','HEAD'],text=True).strip()!=record['remill_commit']:
        raise ValueError('Pinned Remill commit changed')
    for path,expected_hash in ((REMILL/'build/lib/Arch/X86/Runtime/x86.bc',record['semantics_sha256']),
                               (REMILL/'build/bin/lift/remill-lift-21.exe',record['remill_lifter_sha256']),
                               (REMILL/'include/remill/Arch/X86/Runtime/State.h',record['remill_state_header_sha256'])):
        if sha(path)!=expected_hash:raise ValueError('Remill build/header changed')
    observed=OUT/'observed-import.json'
    if sha(observed)!=record['observed_import_sha256']:raise ValueError('Observed import record changed')
    evidence=json.loads(observed.read_text())
    if sha(ROOT/'MW3/Mech3.exe')!=GAME_HASH or evidence['image_sha256']!=GAME_HASH or evidence['provider']!='WINMM.dll' or evidence['symbol']!='timeGetTime' or evidence['iat_guest_va']!=0x5bb75c or evidence['iat_rva']!=0x1bb75c or sha(ROOT/'games/mw3/docs/imports-mw3-us-1-2-retail.csv')!=evidence['import_csv_sha256']:
        raise ValueError('Game/import evidence identity changed')
    for name,(address,length) in BLOCKS.items():
        layout=json.loads((OUT/f'{name}-layout.json').read_text())
        if (layout['profile'],layout['block'],layout['guest_entry'],layout['source_length'],layout['state_bytes'],layout['guest_pointer_bits'],layout['host_pointer_bits'],layout['all_struct_layouts_equal'],layout['indirect_host_calls'],layout['pointer_integer_conversions'])!=('m2-boundary-extension',name,address,length,3504,32,64,True,0,0):
            raise ValueError('Adapter boundary changed')
        if not layout['guest_ir_identity_reviewed'] or layout['guest_ir_sha256']!=REVIEWED_IR[name] or sha(OUT/f'{name}-host.ll')!=layout['host_ir_sha256']:
            raise ValueError('Reviewed block IR identity changed')
    return record

def cases():
    rng=random.Random(0x34ca11)
    edge=[0,1,2,0x7f,0x80,0xff,0x100,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]
    values=[(a,b) for a in edge for b in edge]+[(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(1024)]+[(0xa5a5f00c,1),(0xa5a5f00d,2),(0xa5a5f00e,3)]
    qs=[]
    for i,(arg,timer) in enumerate(values):
        for choice in (0,1):
            for df in (0,1):
                regs=[rng.getrandbits(32) for _ in range(8)];regs[4]=STACK+64+(i%128)*24
                inflags=0x202|(df<<10)|((i%64&1)<<0)|((i%64>>1&1)<<2)|((i%64>>2&1)<<4)|((i%64>>3&1)<<6)|((i%64>>4&1)<<7)|((i%64>>5&1)<<11)
                qs.append(tuple(regs+[inflags,CODE,arg,rng.getrandbits(32),timer,choice,rng.getrandbits(32)]))
    return qs

def read_results(path,count,pointer_bits):
    raw=path.read_bytes()
    if len(raw)!=24+count*RES_SIZE or HEADER.unpack_from(raw)!=(b'MW34BEXR',1,count,RES_SIZE,pointer_bits):
        raise ValueError('Invalid result header/extent')
    return [raw[24+i*RES_SIZE:24+(i+1)*RES_SIZE] for i in range(count)]

def verify(qs,path,bits):
    for i,(q,actual) in enumerate(zip(qs,read_results(path,len(qs),bits),strict=True)):
        want=expected(q)
        if actual!=want:
            offset=next(j for j,(a,b) in enumerate(zip(actual,want)) if a!=b)
            raise ValueError(f'{path.name} case{i} mismatch byte{offset} actual={actual[offset]} expected={want[offset]}')

def run(replay=False):
    record=validate_build();qs=cases();request=OUT/'requests.bin'
    encoded=HEADER.pack(b'MW34BEXQ',1,len(qs),REQ.size,32)+b''.join(REQ.pack(*q) for q in qs)
    if replay:
        if request.read_bytes()!=encoded:raise ValueError('Saved inputs changed')
    else:
        request.write_bytes(encoded)
    results={}
    for kind,worker in record['workers'].items():
        output=OUT/f'results-{kind}.bin'
        if not replay:
            done=subprocess.run([worker['path'],str(request),str(output),str(OUT/'calls.bin')],capture_output=True,text=True,check=True)
            print(done.stdout.strip())
        verify(qs,output,32 if kind=='reference' else 64);results[kind]=sha(output)
    report={'schema_version':1,'status':'passed','original_cases':len(qs),'native_comparisons':len(qs)*2,
            'zero_mismatches':True,'stack_and_global_bytes_per_case':8192,'defined_flags_mask':0xcd5,
            'call_trace':'3 original instruction-recorded return PCs and callee ESPs; native 3 calls/4 returns',
            'build_sha256':sha(OUT/'build.json'),'input_sha256':sha(request),'result_sha256':results,
            'oracle_sha256':sha(Path(__file__)),'scope':'authored offline integration; no game execution or game timing proof'}
    (OUT/('replay.json' if replay else 'comparison.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--replay',action='store_true');args=parser.parse_args();run(args.replay)
