"""Independent BEFORE-only observer of original/native helper publication."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[2]
REQUEST=624
RESPONSE=4940
ORIGINAL=632
GAME_SHA='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
LEAF_SHA='560c17c210dd7fedd7de601f42570c2a0473fa71962c13cfa85a005509a77c65'
PREFIX_SHA='c1ac93565fd8ecd512260561f2cc54310e6e3a430394651e42913f4f043a6c43'
CALL_SHA='113fd2486dfadd238e546035e16e8857a923b98ffcaf340faacc7eb4d7f38aad'

def need(condition,message):
    if not condition: raise ValueError(message)

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def words(raw,offset,count): return struct.unpack_from('<'+'I'*count,raw,offset)
def u32(raw,offset): return words(raw,offset,1)[0]

def expected(before):
    # This formula observes source instruction effects. Execution is performed
    # exclusively by the frozen translated object, independently from this model.
    cpu=list(words(before,32,10));n=u32(before,612)
    t=(48*n)&0xffffffff;r=(t-n)&0xffffffff
    flags=(int(t<n)|int((r&255).bit_count()%2==0)<<2|
           int(bool((t^n^r)&16))<<4|int(r==0)<<6|
           int(bool(r&0x80000000))<<7|
           int(bool((t^n)&(t^r)&0x80000000))<<11)
    cpu[0]=(cpu[1]+188*n+312)&0xffffffff;cpu[2]=r
    cpu[4]+=8;cpu[8]=(cpu[8]&~0x8d5)|flags;cpu[9]=u32(before,616)
    memory=bytearray((u32(before,620)+37*i)&255 for i in range(4096))
    struct.pack_into('<II',memory,2048,0x10000100,n)
    events=struct.pack('<8I',0x20001804,n,4,0,0x20001800,0x10000100,4,0)
    return tuple(cpu),bytes(memory),events

def inspect(q,a,o,mb,ma,kind):
    need((len(q),len(a),len(o),len(mb),len(ma))==(REQUEST,RESPONSE,ORIGINAL,4096,4096),'Complete binary snapshots')
    need(q[:8]==b'MWHLPR01' and words(q,8,4)==(1,REQUEST,u32(q,16),kind),'Request framing/kind')
    need(a[:8]==b'MWHLPA01' and words(a,8,4)==(1,RESPONSE,u32(q,16),0),'Completed matched response')
    need(u32(a,24)!=0 and u32(q,24)!=0 and u32(q,28)!=0,'Observed process/thread identities')
    cpu=words(q,32,10)
    need(cpu[9]==0x409ed0 and 8<=cpu[4]<=0xfffffff7,'Admitted literal helper entry and stack range')
    need(cpu[8]&0x202==0x202 and cpu[8]&~(0x202|0xcd5)==0,'Measured restorable flags domain for hardware comparison')
    if kind==2: need(u32(q,616)==0x405173,'Only reviewed actual CALL route')
    ecpu,memory,events=expected(q)
    need(words(a,28,10)==ecpu,'Native all-register/full-flag/RET4 effects from BEFORE')
    need(a[68:608]==q[72:612],'Native opaque FP/ENV unchanged')
    need(a[608:4704]==memory,'Entire native owned page versus BEFORE-only seed/stack projection')
    need(a[4704:4736]==events and words(a,4736,3)==(2,1,1),'Two generated reads, no writes, one completed RET4')
    need(u32(o,628)==0,'Original hardware completed without fault')
    literal=words(o,0,10);projected=words(o,40,10)
    need(literal[4]==u32(o,620)+8 and literal[9]==u32(o,624),'Literal original RET4 and actual capture broker')
    need(projected==ecpu,'Original projected state versus BEFORE-only source model')
    need(literal[:4]==projected[:4] and literal[5:9]==projected[5:9],'Original only ESP/EIP projection')
    need(o[80:620]==q[72:612],'Original full seeded FX512 and ENV28 preserved')
    need(mb==ma,'Actual full original owned page unchanged')
    # Shadow entry lies at the same offset as the generated virtual stack.
    need(words(mb,2048,2)==(u32(o,624),u32(q,612)),'Original actually consumed shadow return/argument at entry')
    mm=bytearray(memory);struct.pack_into('<I',mm,2048,u32(o,624))
    need(mb==mm,'Original page differs from generated projection only by its owned hardware return broker')
    return {'game_pid':u32(q,24),'game_tid':u32(q,28),'worker_pid':u32(a,24),'sequence':u32(q,16),
            'n':u32(q,612),'base':cpu[1],'eax':ecpu[0],'edx':ecpu[2],
            'flags':ecpu[8],'caller':u32(q,616),'generated_reads':2,'completed_returns':1}

def game_bytes():
    game=ROOT/'MW3/Mech3.exe';raw=game.read_bytes()
    need(hashlib.sha256(raw).hexdigest()==GAME_SHA,'Exact admitted game')
    need(hashlib.sha256(raw[0x92d0:0x92d0+22]).hexdigest()==LEAF_SHA,'Entire integer-only source leaf')
    pe=u32(raw,0x3c);so=pe+24+struct.unpack_from('<H',raw,pe+20)[0]
    def read(va,size):
        rva=va-0x400000
        for i in range(struct.unpack_from('<H',raw,pe+6)[0]):
            sec=so+40*i;v=u32(raw,sec+12);n=u32(raw,sec+16);p=u32(raw,sec+20)
            if v<=rva and rva+size<=v+n:return raw[p+rva-v:p+rva-v+size]
        raise ValueError('Source VA lacks independent file backing')
    prefix=read(0x405160,19);call=read(0x40516e,5)
    need(hashlib.sha256(prefix).hexdigest()==PREFIX_SHA and hashlib.sha256(call).hexdigest()==CALL_SHA,'Actual disk caller route pins')
    need(call[0]==0xe8 and (0x405173+struct.unpack_from('<i',call,1)[0])&0xffffffff==0x409ed0,'Original direct CALL actually resolves helper')
    return raw

def verify(run,selftest=False):
    receipt=run/('independent-selftest-verification.json' if selftest else 'independent-live-verification.json')
    need(not receipt.exists(),'Fresh observer receipt required')
    game_bytes()
    log=run/('selftest.jsonl' if selftest else 'game.jsonl')
    events=[json.loads(line) for line in log.read_text().splitlines()]
    kind=1 if selftest else 2
    label='hook_selftest_call' if selftest else 'game_call'
    calls=[e for e in events if e.get('event')==label]
    need(bool(calls),'Actual native publication records required')
    need(not any(e.get('event')=='fatal' for e in events),'No fatal hook failure')
    snapshots={};rows=[];controls=0
    captures=run/('selftest-captures' if selftest else 'game-captures')
    need(sha(captures/'admitted-helper-source.bin')==LEAF_SHA and
         sha(captures/'admitted-caller-prefix.bin')==PREFIX_SHA,'Private source/caller bytes agree with independently admitted disk route')
    for event in calls:
        need(event.get('native_applied') is (not selftest) and event.get('original_compare') is True,'Compiled publication/original comparison with separate synthetic versus live credit')
        need(event.get('actual_ss_queried') is True and event.get('actual_ss_base')==0,'Observed flat hardware SS base for the stack projection')
        seq=event['sequence']
        paths=[captures/f'call-{seq}.{suffix}' for suffix in ('before.bin','native.bin','original.bin','original-memory-before.bin','original-memory-after.bin')]
        q,a,o,mb,ma=(p.read_bytes() for p in paths)
        for field,path in zip(('before_sha256','native_sha256','original_sha256','original_memory_before_sha256','original_memory_after_sha256'),paths):
            need(sha(path)==event[field],'Private snapshot identity versus actual hook trace')
        row=inspect(q,a,o,mb,ma,kind);rows.append(row)
        need(row['game_pid']==event['pid'] and row['game_tid']==event['tid'],'Literal captured process/thread versus hook trace')
        need(row['worker_pid']==event['worker_pid'],'Actual worker identity versus trace')
        snapshots.update({str(p.relative_to(run)):sha(p) for p in paths})
        for member,offset in ((0,16),(0,20),(0,36),(0,72),(0,584),(0,612),(0,616),(0,620),
                              (1,20),(1,28),(1,60),(1,68),(1,580),(1,608),(1,4704),(1,4736),
                              (2,0),(2,40),(2,80),(2,592),(2,620),(2,624),(2,628),(3,0),(4,0)):
            parts=[q,a,o,mb,ma];changed=bytearray(parts[member]);changed[offset]^=1;parts[member]=bytes(changed)
            try:inspect(*parts,kind)
            except (ValueError,struct.error):controls+=1
            else:raise ValueError(f'Observer missed corruption member{member} offset{offset}')
    if not selftest:
        launch=json.loads((run/'launch.json').read_text())
        installed=next(e for e in events if e.get('event')=='installed')
        need(all(r['game_pid']==launch['game_pid']==installed['pid'] and r['worker_pid']==launch['worker_pid'] for r in rows),'Both actually owned process identities versus launch')
        need(installed['callsite_va']==0x40516e and installed['entry_va']==0x409ed0 and installed['patched_call_bytes']==5,'Only reviewed original caller redirected')
        prefix=bytearray((captures/'admitted-caller-prefix.bin').read_bytes())
        struct.pack_into('<I',prefix,15,(installed['hook_pointer']-0x405173)&0xffffffff)
        need(hashlib.sha256(prefix).hexdigest()==installed['patched_caller_prefix_sha256'],'Declared loaded CALL route resolves only the installed thunk')
        need(installed['patched_source_bytes']==0 and installed['source_sha256']==LEAF_SHA and installed['original_call_sha256']==CALL_SHA,'Unmodified whole source and original caller identity')
    record={'passed':True,'scope':('Synthetic authored thunk' if selftest else 'Actual reviewed original-game caller')+' publishes frozen translated x64 helper result after hardware original comparison',
            'observations':rows,'observer_corruptions_rejected':controls,'snapshot_sha256':snapshots,
            'trace_sha256':sha(log),'observer_sha256':sha(__file__),
            'FP_scope':'Opaque full seeded FX512 and separate ENV28 carry; integer-only source does not inspect FP',
            'hidden_State_seed':'authored zero; observed CPU/flags imported; FP preserved as opaque transport',
            'memory_scope':'Owned 4096-byte stack projection; actual original page before/after independently unchanged',
            'whole_game_is_x64':False,'full_M4_complete':False}
    receipt.write_text(json.dumps(record,indent=2)+'\n')
    print(f'{receipt}: passed, {len(rows)} calls, {controls} corrupted records rejected')
    return record

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('run',type=Path);parser.add_argument('--selftest',action='store_true')
    args=parser.parse_args();verify(args.run.resolve(),args.selftest)
