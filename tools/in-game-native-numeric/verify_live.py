"""Independent BEFORE-only source observer for the live numeric bridge receipt."""
import hashlib
import json
from pathlib import Path
import struct
import sys

REQUEST=688;RESPONSE=1352;ORIGINAL=624
ROOT=Path(__file__).resolve().parents[2]

def need(ok,reason):
    if not ok: raise ValueError(reason)

def u32(b,o): return struct.unpack_from('<I',b,o)[0]
def u16(b,o): return struct.unpack_from('<H',b,o)[0]
def words(b,o,count): return struct.unpack_from('<'+'I'*count,b,o)
def put(b,o,v,n=4): b[o:o+n]=v.to_bytes(n,'little')
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def inspect(raw,game_raw):
    need(len(raw)==REQUEST+RESPONSE+ORIGINAL,'Complete live snapshot extent')
    q=raw[:REQUEST];a=raw[REQUEST:REQUEST+RESPONSE];original=raw[REQUEST+RESPONSE:]
    need(q[:8]==b'MWNMXR01' and words(q,8,4)==(1,REQUEST,u32(q,16),2),'Actual kind-2 live request framing')
    need(a[:8]==b'MWNMXA01' and words(a,8,5)==(1,RESPONSE,u32(q,16),0,u32(a,24)),'Matched completed native response framing')
    c=list(words(q,32,10));expected=c.copy();expected[4]+=4;expected[9]=u32(q,684)
    need(words(a,28,10)==tuple(expected),'All native returned CPU registers/full flags/RET0')
    oc=words(original,0,10)
    need(oc==tuple(expected),'Original projected observed CPU versus preserved live BEFORE and return ABI')
    f=q[72:584];env=q[584:612]
    need(f[4]==0,'This observer grants only the actual empty x87 entry route')
    need(u16(f,0)==u16(env,0) and u16(f,2)==u16(env,4) and u16(env,8)==0xffff,'Literal input hardware storage/ENV coherence')
    need(u32(f,24) in (0x1f80,0x1fa0) and u16(f,0) in (0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f),'Admitted actual control state with preserved SSE precision flag')
    need((u16(f,2)>>11)&7 in (0,7) and u16(f,2)&~0x3800 in (0,2,32,34,512,514,544,546),'Admitted actual TOP/status')
    need(words(q,656,8)[0:3]==(0x23,0x2b,0x2b) and words(q,656,8)[4:7]==(0x780c0000,0x7f7fffff,0x780c10f0),'Actual provider/segments binding')
    # FLD inserts max at TOP-1, then exact FSTP returns to original TOP.
    # Logical dead slot7 contains the promoted value; slots0..6 carry intact.
    fx=bytearray(f);put(fx,2,u16(f,2)&~0x200,2)
    fx[144:154]=bytes.fromhex('0000000000ffffff7e40')
    ex=bytearray(env);put(ex,4,u16(fx,2),2);put(ex,12,0x4c1a09)
    put(ex,16,0x011d0023);put(ex,20,0x60b368);put(ex,24,0x2b,2)
    need(a[68:580]==fx and a[580:608]==ex,'Entire native published FX/ENV transport versus BEFORE-only instruction effects')
    output=struct.pack('<11I',0x7f7fffff,*([0]*10))
    need(a[608:652]==output and original[580:624]==output,'Native and actual original 44-byte global effects')
    ofx=original[40:552];oe=original[552:580]
    defined=list(range(5))+list(range(24,28))+list(range(160,288))
    for i in range(8): defined += list(range(32+16*i,42+16*i))
    need(all(ofx[i]==fx[i] for i in defined) and oe==ex,'Original architectural numerical FX and full separate ENV match native effects')
    need(words(a,1152,2)==(22,1),'Actual generated-source event closure')
    frame=0x20001800;ret=0x410a80
    # Read the raw-file IAT word from the real game PE, independently from reply.
    pe=u32(game_raw,0x3c);sections=u16(game_raw,pe+6);optional=u16(game_raw,pe+20);so=pe+24+optional
    iat_rva=0x1bb4fc;raw_iat=None
    for i in range(sections):
        sec=so+40*i;rva=u32(game_raw,sec+12);size=u32(game_raw,sec+16);off=u32(game_raw,sec+20)
        if rva<=iat_rva and iat_rva+4<=rva+size: raw_iat=u32(game_raw,off+iat_rva-rva)
    need(raw_iat is not None,'Actual raw image IAT backing')
    events=[(0x4c19f0,frame-4,c[5],4,1),(0x4c19f3,frame-8,0x4c19f8,4,1),
            (0x4c1a00,frame-12,frame-4,4,1),(0x4c1a03,0x5bb4fc,raw_iat,4,0),
            (0x4c1a03,frame-16,0x4c1a09,4,1),(0x780c10f0,0x78115004,0x7f7fffff,4,0),
            (0x780c10f6,frame-16,0x4c1a09,4,0),(0x4c1a09,0x60b368,0x7f7fffff,4,1)]
    events += [(0x4c1a0f+10*i,0x60b36c+4*i,0,4,1) for i in range(10)]
    events += [(0x4c1a73,frame-12,frame-4,4,0),(0x4c1a74,frame-8,0x4c19f8,4,0),
               (0x4c19f8,frame-4,c[5],4,0),(0x4c19f9,frame,ret,4,0)]
    need(a[652:1092]==b''.join(struct.pack('<5I',*e) for e in events),'All22 independent ordered source PC/access/value/width/op predictions')
    need(words(a,1092,15)==(ret,0x4c19f0,ret,0,1,0x4c19f3,0x4c1a00,0x4c19f8,0,1,0x4c1a03,0x5bb4fc,0x4c1a09,1,1),'All3 actual typed CALL/RET routes')
    return {'game_pid':u32(q,24),'game_tid':u32(q,28),'sequence':u32(q,16),'worker_pid':u32(a,24),
            'entry_cw':u16(f,0),'entry_sw':u16(f,2),'entry_x87_depth':0,'entry_mxcsr':u32(f,24),
            'caller':u32(q,684),'source_events':22,'completed_routes':3}

def main(run):
    need(not (run/'independent-live-verification.json').exists(),'Fresh verification receipt required')
    events=[json.loads(line) for line in (run/'game.jsonl').read_text().splitlines()]
    calls=[e for e in events if e.get('event')=='game_call' and e.get('native_applied')]
    need(len(calls)==1,'Exactly one actually applied initializer call')
    event=calls[0]
    captures=run/'game-captures'
    snapshots=[captures/f"call-{event['sequence']}.{kind}.bin" for kind in ('before','native','original')]
    q,a,o=(p.read_bytes() for p in snapshots)
    need(len(o)==676 and u32(o,672)==0,'Complete original capture without hardware fault')
    literal=words(o,0,10);projected=words(o,40,10)
    need(literal[4]==u32(o,664)+4 and literal[9]==u32(o,668),'Observed isolated original RET0 and capture broker')
    need(literal[:4]==projected[:4] and literal[5:9]==projected[5:9],'Original projection changes only stack and return address')
    raw=q+a+o[40:664];row=inspect(raw,(ROOT/'MW3/Mech3.exe').read_bytes())
    installed=next(e for e in events if e.get('event')=='installed')
    need(row['game_pid']==installed['pid'],'Callback process matches installed game')
    owners=next(e for e in events if e.get('event')=='loaded_owners')
    caller=row['caller'];need(owners['initterm_export']+2<=caller<owners['initterm_export']+512,'Caller near actual loaded _initterm export')
    need(owners['crt_sha256']=='23a918921c545140d189ce6dc68590bacdeb0ab2f3e3a9a2d722c5aff45ce64f' and
         owners['initterm_export']-owners['crt_base']==0x683b0 and caller-owners['initterm_export']==31,
         'Exact observed current CRT export and indirect-call return')
    # This current Windows CRT is the 32-bit SysWOW64 image. Its actual indirect
    # CALL operand is verified from independent file backing and captured GPR.
    crt=Path('C:/Windows/SysWOW64/msvcrt.dll');cb=crt.read_bytes()
    need(sha(crt)==owners['crt_sha256'],'Actual current CRT file identity matches loaded owner')
    pe=u32(cb,0x3c);so=pe+24+u16(cb,pe+20);caller_rva=caller-owners['crt_base'];opcode=None
    for i in range(u16(cb,pe+6)):
        sec=so+40*i;rva=u32(cb,sec+12);size=u32(cb,sec+16);off=u32(cb,sec+20)
        if rva<=caller_rva-2 and caller_rva<=rva+size: opcode=cb[off+caller_rva-rva-2:off+caller_rva-rva]
    qcpu=words(q,32,10)
    need(opcode==b'\xff\xd7' and qcpu[7]==installed['hook_pointer'] and qcpu[6]==0x5e016c,
         'Actual CRT CALL EDI names the installed hook and owning initializer table slot')
    row['caller_register']='EDI'
    launch=json.loads((run/'launch.json').read_text())
    need(row['game_pid']==launch['game_pid'] and row['worker_pid']==launch['worker_pid'],'Both actual process identities match launch receipt')
    controls=0
    for offset in (16,20,32,72,584,656,672,688+28,688+68,688+580,688+608,688+652,688+1092,688+1152,688+RESPONSE+40,688+RESPONSE+552,688+RESPONSE+580):
        damaged=bytearray(raw);damaged[offset]^=1
        try: inspect(damaged,(ROOT/'MW3/Mech3.exe').read_bytes())
        except (ValueError,struct.error): controls+=1
        else: raise ValueError(f'Observer missed corruption at {offset}')
    report={'passed':True,'scope':'One actual startup initializer through unchanged translated x64 wrapper/body/provider; original compared; native output consumed by x86 game',
            'observations':row,'observer_corruptions_rejected':controls,'snapshot_sha256':{p.name:sha(p) for p in snapshots},
            'hook_trace_sha256':sha(run/'game.jsonl'),'observer_sha256':sha(__file__),
            'hidden_State_seed':'authored zero; only observed x86 CPU/FP imported',
            'projections':['owned virtual stack/return broker','owned FS base','raw-file virtual IAT versus resolved live IAT'],
            'original_shadow_stack_observation':'CPU exit ESP and broker plus hook-owned full page check; live below-ESP scratch bytes are outside returned ABI claim',
            'whole_game_is_x64':False,'full_M4_complete':False}
    (run/'independent-live-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main(Path(sys.argv[1]).resolve())
