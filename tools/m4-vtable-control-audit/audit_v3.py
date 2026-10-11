"""Independent read-only audit of frozen finite-vtable executable controls.

Only the canonical archive reader and physical PE export decoder are reused.
All hardware, retry, source-prefix, private-span, dispatch and FS predicates
below are authored independently of the controls producer/checker.
"""
from pathlib import Path
import collections, hashlib, importlib.util, json, re, struct, sys, traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'reports/m4-vtable-control-audit'
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from manifests import verify_manifest
from stages import verify_stage
sys.path.insert(0, str(ROOT/'tools/m4-crt-locale-batch-review'))

EXEC_SHA = '7f94c71955cdb44e1547570005acd5fb471089efe2cee83214bddf24de6e48fb'
BUILD_SHA = 'ffb1d2ba01313fafe3628c9ef071d67117488fe0975f2a8ded0d5d2ef5acda36'
CHECK_SHA = '0ab89ceb89d871ba9e56bbbc55227b6adc8f1f27d13d24b7772203ddc9db31de'
NATIVE_SHA = 'b52c62a1ec6e1306a9629f53fbe80621be96404907d322efbbeef136ec10ee93'
ROOTS = (0x40f0e0,0x4795f0,0x47f5f0,0x4b5220)
TIB = 0x7ffde000

def need(value, why):
    if not value: raise ValueError(why)

def sha(path):
    with Path(path).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def module(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def rows(raw, fmt):
    need(len(raw) % struct.calcsize(fmt) == 0, 'Complete fixed-width source observation')
    return list(struct.iter_unpack(fmt, raw))

def hardware(before, after, rich=False):
    need(len(before)==len(after)==544, 'Actual complete hardware boundary encoding')
    need(before[:5]==after[:5] and before[24:28]==after[24:28]
         and before[512:540]==after[512:540], 'Exact CW/SW/FTW, all MXCSR and legacy ENV28')
    for k in range(8):
        need(before[32+k*16:42+k*16]==after[32+k*16:42+k*16], 'Every complete physical raw80 x87 value')
    need(before[256:416]==after[256:416], 'Every byte of nonvolatile XMM6..15')
    if rich:
        need(struct.unpack_from('<H',before)[0]==0xa7f and struct.unpack_from('<I',before,24)[0]==0x5fa5
             and before[4] and any(before[524:540]), 'Actual rich x87/MXCSR and nonzero ENV instruction metadata')

def same_dump(a, old, new):
    names = {n[len(old):] for n in a.entries if n.startswith(old)}
    other = {n[len(new):] for n in a.entries if n.startswith(new)}
    need(names==other and names, 'Exact retry logical inventory, including all pages and private state')
    for n in names: need(a.data(old+n)==a.data(new+n), 'Byte-exact same-session retry record '+n)
    return len(names)

def machine(path):
    data=Path(path).read_bytes()
    if data[:2]==b'MZ':
        p=struct.unpack_from('<I',data,60)[0];need(data[p:p+4]==b'PE\0\0','Physical PE signature')
        return struct.unpack_from('<H',data,p+4)[0]
    return struct.unpack_from('<H',data,6 if data[:4]==b'\0\0\xff\xff' else 0)[0]

def expected_cause(c):
    cell='Exact physical finite indirect cell target and one active call'
    page='Only committed source/API/research effects may change owned locale pages'
    store='Checked actual source locale/parser store fault'
    private='Vtable observer changed private source-cell/frame/store witnesses'
    observer='Independent deliberate finite-vtable source boundary observer failure'
    d={1:(0x59fbab,0x5cfd14,110,cell),2:(0x59fdc5,0x5bc100,110,cell),3:(0x59ff6e,0x5bc0fc,110,cell),
       4:(0x59ff64,0x608ae0,110,'Actual live instance vptr follows its exact committed source publication'),
       5:(0x59fba5,0x5fc338,114,store),6:(0x40e824,0x5fc33c,114,store),7:(0x40f138,0x5fc338,114,store),
       8:(0x40e824,0x608eac,114,store),9:(0x59ff6e,0x20001000,111,page),
       10:(0x59ff6e,0x780039bf,110,'Heap creation observer changed State/FX or ownership/lifecycle ledgers'),
       25:(0x4824ed,TIB,83,store),26:(0x4824ae,0x20001000,81,page)}
    for case,pc,point in ((11,0x59fbab,111),(12,0x59ff64,111),(13,0x59fba5,115),
                          (14,0x59fbab,110),(15,0x59fba5,114),(16,0x40e820,112)):
        d[case]=(pc,pc,point,private)
    for case,pc,point in ((17,0x59fbab,110),(18,0x59fbab,111),(19,0x40e820,112),
                          (20,0x59fbb1,113),(21,0x59fba5,114),(22,0x59fba5,115),
                          (23,0x4824a7,80),(24,0x4824ae,82)):
        d[case]=(pc,0,point,observer)
    return d[c]

def fs_proof(a,live,source,counts):
    frames=rows(a.data(live+'fs-frame-witnesses.bin'),'<32Q')
    events=rows(a.data(live+'fs-chain-events.bin'),'<16Q')
    recordbytes=rows(a.data(live+'fs-record-bytes.bin'),'<16Q')
    active=rows(a.data(live+'fs-active-records.bin'),'<I')
    tib=a.words(live+'fs-current-tib.bin',5)
    provenance=a.words(live+'fs-native-input.bin',16,'Q')
    need(tib[0]==tib[4]==TIB and tib[2:4]==(0x20002000,0x20001000), 'Owned minimal native TIB identity')
    need(provenance[:8]==(1,TIB,TIB,0xffffffff,0x20002000,0x20001000,TIB,0xffffffff)
         and not any(provenance[8:]), 'Native sentinel has explicit independent input/provenance')
    need(len(frames)<=1, 'Isolated family has at most one literal game FS record')
    for f in frames:
        need(f[:3]==(1,0,0x47f5f0) and f[9]==f[5]-12 and f[8]==0xffffffff
             and not f[13], 'Actual source record geometry and un-nested predecessor')
        for e in events:
            need(e[3]==0, 'FS events reference this exact acquired source frame')
            if e[4] in (82,84):
                value=f[9] if e[4]==82 else f[8]
                need(e[13] and source[e[13]-1]==(e[5],TIB,value,4,1), 'FS after hook follows real committed store/ledger')
                counts['actual_postcommit_FS_events']+=1
        for r in recordbytes:
            need(r[0]==1 and r[2]==0 and r[6:8]==(f[9],12)
                 and r[8:10]==(f[8],f[10]), 'Complete actual stack record identity')
            raw=struct.pack('<3I',*r[8:11])
            for k,byte in enumerate(raw):
                address=f[9]+k
                prior=next((s for s in reversed(source[:r[11]]) if s[4] and s[1]<=address<s[1]+s[3]),None)
                need(prior is not None and (prior[2]>>(8*(address-prior[1])))&255==byte,
                     'Every record byte is independently replayed from authentic literal writes')
            counts['full12B_record_source_replays']+=1
        if f[15] and not f[19]:
            need(active==[(0,)] and tib[1]==f[9], 'Refusal after installation retains exact committed virtual chain')
            counts['partial_active_FS_chains']+=1
        else:
            need(not active and tib[1]==0xffffffff, 'Source chain is sentinel before installation or after genuine restore')
        if f[21]:
            need(f[15]==f[19]==1 and f[17]==f[22]==f[8] and (f[20],f[5],f[6],4,0) in source,
                 'Literal saved predecessor and final RET genuinely returned')
            counts['complete_game_FS_records']+=1
    need(bool(active)==bool(frames and frames[-1][15] and not frames[-1][19]), 'No invented active record')
    return frames,tib

def checkpoint_map(a,live):
    d={}
    for n in a.entries:
        if n.startswith(live+'registry-checkpoint-') and n.endswith('-name.bin'):
            key=a.data(n).decode();need(key not in d,'Distinct checkpoint name');d[key]=n[:-9]
    return d

def call_proof(a,live,source,calls,specs,counts):
    cps=checkpoint_map(a,live)
    for index,w in enumerate(calls):
        spec=specs[(w[2],w[3])]
        need(w[:2]==(1,index) and w[4:8]==(spec['slot'],spec['target'],spec['target']^(int(w[2]==0x40f0e0 and index==0 and a.words(live+'locale-fault.bin',4)[3]==111 and a.data(live+'locale-fault-reason.bin').startswith(b'Vtable observer'))),w[3]),
             'Exact independently recovered owning-cell/target source association')
        need(w[9]==spec['entry_ECX'] and source[w[8]]==(w[3],w[4],w[5],4,0), 'Raw finite cell read and correct delivered ECX')
        if spec.get('source_vtable'):
            need(w[10]==w[11]==spec['source_vtable'] and source[w[12]]==(spec['dominating_vtable_store_PC'],spec['source_object'],w[11],4,1),
                 'Existing publication is proved for both fixed and virtual calls')
            if w[3]==0x59ff6e:
                need(w[13]>w[12] and source[w[13]]==(0x59ff64,spec['source_object'],w[11],4,0), 'True instance read precedes the virtual CALL')
            else: need(not w[13], 'Fixed absolute cell does not invent a future instance read')
        else: need(not any(w[10:14]), 'Simple fixed setter has no invented publication/read fact')
        counts['actual_cell_provenance_joins']+=1
        if not w[14]: continue
        entered=cps.get(f'vtable-call-{index}-entered');need(entered is not None,'Actual complete CALL-entry checkpoint')
        e=a.words(entered+'-cpu.bin',10);need(e[1]==w[9] and e[4]==w[14] and e[9]==spec['target'], 'Full CPU checkpoint retains actual entry frame/ECX/target')
        page=a.data(entered+f'-page-{w[14]&~4095}.bin');offset=w[14]&4095
        need(struct.unpack_from('<I',page,offset)[0]==w[15]==spec['return_pc'], 'Genuine literal CALL return is stored at the authentic frame')
        need((w[3],w[14],w[15],4,1) in source[w[22]:], 'CALL-frame source write is retained')
        if spec['argument'] is not None:
            need(struct.unpack_from('<I',page,offset+4)[0]==w[16]==0 and w[17]==4, 'Authentic admitted zero argument and RET4 domain')
        else: need(w[17]==0,'Genuine no-argument plain RET domain')
        counts['complete_actual_CALL_entry_frames']+=1
        if not w[21]: continue
        returned=cps.get(f'vtable-call-{index}-returned');need(returned is not None,'Actual complete RET checkpoint')
        z=a.words(returned+'-cpu.bin',10)
        need(z[4]==w[18]==e[4]+4+w[17] and z[0]==w[19] and z[9]==w[15]
             and w[24]==w[25] and w[26]==w[27] and w[28]==w[29]
             and source[w[23]-1]==(w[20],w[14],w[15],4,0), 'Genuine literal RET/frame cleanup has no new API/owner/chain effect')
        need(a.data(entered+'-fx.bin')==a.data(returned+'-fx.bin'), 'Complete virtual FX512 carried through integer helper')
        need(all(e[k]==z[k] for k in (1,3,5,6,7)), 'Every untouched GPR across physical source helper')
        local=source[w[22]:w[23]]
        if spec['target']==0x40e820:
            need(z[0]==0 and e[2]==z[2] and e[8]==z[8] and (0x40e824,w[9]+4,0,4,1) in local,
                 'Physical setter returns actual zero EAX and commits only the real child DWORD')
        elif spec['target']==0x59ff00:
            g=[s for s in local if s[0]==0x59ff00 and s[1]==0x5f49b8 and not s[4]]
            old=[s for s in local if s[0]==0x59ff05 and s[1]==w[9]+12 and not s[4]]
            dst=[s for s in local if s[0]==0x59ff0a and s[1]==w[9]+12 and s[4]]
            need(len(g)==len(old)==len(dst)==1,'Exact actual global/read/OR-store source rows')
            value=g[0][2]|old[0][2];mask=0x8c5
            flags=(4 if (value&255).bit_count()%2==0 else 0)|(0x40 if value==0 else 0)|(0x80 if value&0x80000000 else 0)
            need(dst[0][2]==z[2]==value and z[0]==g[0][2] and z[8]&mask==flags
                 and (e[8]^z[8])&~(mask|0x10)==0, 'Literal arbitrary DWORD OR result and every defined/preserved flags bit')
            counts['whole_OR_result_flag_prefixes']+=1
        else:
            need(spec['target']==0x59ff80 and z[0]==0 and z[2]==e[2] and z[8]&0x8c5==0x44
                 and not any(0x59ff88<=s[0]<=0x59ff9e for s in local), 'Zero TEST/branch/RET retains literal flags and reaches no nonzero pointee byte')
            counts['zero_argument_no_pointee_prefixes']+=1
        counts['complete_literal_CALL_RET_proofs']+=1

def cause_proof(a,c,live,source,calls,stores,frames,tib,counts):
    p=f'case-{c}/first-trigger/';fault=a.words(live+'locale-fault.bin',4)
    reason=a.data(live+'locale-fault-reason.bin').decode();identity=a.words(p+'identity.bin',3)
    need(fault[0]==1 and tuple(fault[1:])+(reason,)==expected_cause(c), 'Exact actually reached cause/PC/address/stage for case '+str(c))
    need(identity[0] in (80,81,82,83,110,111,112,113,114,115) and identity[1], 'Actual reached trigger selector')
    if c in (5,6,7,8,25):
        need(not any(s[0]==fault[1] and s[1]==fault[2] and s[4] for s in source), 'Refused literal store has no committed source row')
    if c in range(11,17):
        before=a.data(p+'private-before.bin');after=a.data(p+'private-after.bin');name=a.data(p+'private-name.bin').decode()
        expected_names={11:'vtable-call-witnesses.bin',12:'vtable-instance-vptr.bin',13:'vtable-source-stores.bin',14:'vtable-read-probe.bin',15:'vtable-store-probe.bin',16:'vtable-active.bin'}
        need(name==expected_names[c] and identity[2]==1 and len(before)==len(after), 'One genuine private backing span intervention')
        width=4 if c==16 else 8;index={11:len(before)//8-26,12:4,13:len(before)//8-10,14:5,15:6,16:0}[c]
        want=bytearray(before);off=index*width;want[off:off+width]=(int.from_bytes(want[off:off+width],'little')^1).to_bytes(width,'little')
        need(bytes(want)==after==a.data(live+name), 'Complete actual private record changed in precisely one intended word')
        counts['actual_private_span_word_flips']+=1
    state=a.data(f'case-{c}/first-causal-State.bin');fx=a.data(f'case-{c}/first-causal-FX.bin');env=a.data(f'case-{c}/first-causal-guest-ENV.bin')
    if c not in (6,):
        wanted=bytearray(a.data(p+'State.bin'))
        if c==10:
            q=a.words(p+'actual-intervention.bin',8,'Q');need(q[0]==4 and q[2]^q[3]==4,'Actual observer changed only EDX bit2')
            need(int.from_bytes(wanted[q[1]:q[1]+4],'little')==q[2],'Trigger fullState authentic incomingEDX')
            wanted[q[1]:q[1]+4]=q[3].to_bytes(4,'little')
        need(bytes(wanted)==state and a.data(p+'FX.bin')==fx and a.data(p+'guest-ENV.bin')==env,
             'Whole trigger/causal3504State,512FX and28guestENV relation at first refusal')
        counts['complete_trigger_causal_machine_relations']+=1
    def guest(address):
        return struct.unpack_from('<I',a.data(live+f'current-page-{address&~4095}.bin'),address&4095)[0]
    if c in (1,2,3,4,9,26):
        q=a.words(p+'actual-intervention.bin',8,'Q')
        need(q[0] in (1,3) and q[2]!=q[3] and guest(q[1])==q[3]==q[6], 'Actual retained intervention bytes, not synthetic requested corruption')
        if c<=3:
            need(q[1] in (0x5cfd14,0x5bc100,0x5bc0fc) and q[2]^q[3]==4
                 and not any(s[0]==fault[1] and s[1]==q[1] for s in source), 'Exact raw-cell guard refuses after real read but before committed source read association')
        if c==9:
            need(calls[-1][14]==0 and calls[-1][21]==0 and not any(0x59ff80<=s[0]<=0x59ffa1 for s in source),
                 'Committed-stack mirror refusal occurs before CALL/helper/pointee; no direct pointer-admission claim')
    if c in (6,7,8):
        address=0x608ea8 if c==8 else 0x5fc338
        need(guest(address)==0x5cfd10, 'The complete already committed base-vptr DWORD survives later RO refusal')
        if c==6: need(len(stores)==1 and stores[0][3:7]==(0x59fba5,0x5fc338,4,0x5cfd10), 'Only first genuine object store committed')
        if c==7: need(not any(s[0]==0x40f138 and s[4] for s in source),'Final derived header is not fabricated after refusal')
        if c==8: need(frames[0][15] and not frames[0][19] and tib[1]==frames[0][9],'Child setter refused within genuine installed game record')
        counts['partial_committed_object_prefixes']+=1
    if c in (23,24,25,26):
        f=frames[0];need(f[2]==0x47f5f0,'FS cause belongs to selected real normal-path constructor')
        if c in (23,26): need(not f[15] and tib[1]==0xffffffff,'Pre-install refusal does not invent an installed chain')
        if c in (24,25): need(f[15] and not f[19] and tib[1]==f[9],'Committed installation is retained without invented handler/unwind')
        if c==25: need((0x4824da,f[9],f[8],4,0) in source,'Restore fault follows authentic saved predecessor read')
        if c==26:
            need(a.words(p+'record.bin',3)[1]^guest(f[9]+4)==4,'Only genuine saved-handler DWORD intervention at actual stack frame')
    return dict(case=c,PC=fault[1],address=fault[2],stage=fault[3],reason=reason,trigger_point=identity[0],trigger_PC=identity[1])

def main(name):
    out=BASE/name;need(not out.exists(),'Fresh independent audit receipt');out.mkdir(parents=True)
    pins={};counts=collections.Counter();levels=[];causes=[];passed=False
    def pin(p,h=None):
        p=Path(p).resolve();actual=pins.get(str(p)) or sha(p)
        need(h is None or h==actual,'Immutable physical input '+str(p));pins[str(p)]=actual;return p
    def read(p,h=None): return json.loads(pin(p,h).read_bytes())
    try:
        pin(__file__);pin(sys.executable)
        for f in ('manifests.py','stages.py','capture_bundle.py','paths.py'):pin(ROOT/'tools/m4-pipeline'/f)
        ex_path=ROOT/'reports/m4-vtable-controls/execution-r1/report.json';ex=read(ex_path,EXEC_SHA)
        build_path=Path(ex['build']);build=read(build_path,BUILD_SHA)
        check_path=ROOT/'reports/m4-vtable-controls/check-r1/report.json';check=read(check_path,CHECK_SHA)
        need(ex['passed'] and build['passed'] and check['passed'] and check['execution']==str(ex_path)
             and check['execution_sha256']==EXEC_SHA and check['build_sha256']==BUILD_SHA,'Direct final compiled execution/checker binding')
        for value in (ex,check):
            for p,h in value['files'].items():pin(p,h)
        for category in ('sources','artifacts'):
            for p,h in build[category].items():pin(p,h)
        prep=read(build['preparation']);native_path=Path(prep['native_include']);np=read(native_path/'report.json',NATIVE_SHA)
        need(native_path==ROOT/'reports/m4-vtable-native/preparation-r4','Exact final native4 derivative, unchanged source bodies')
        specs_path=pin(ROOT/'reports/m4-next-source/recovery-r1/indirect-call-inputs.json','a329e3988a4d77137e1270d9606c2c65f8b6aee95d1f04fb5928eb9a28a90d9a')
        specs={(s['root'],s['CALL_pc']):s for s in json.loads(specs_path.read_bytes())}
        need(len(specs)==6,'Six exact independent physical call contracts')
        D=module('vtable_audit_archive',pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'))
        P=module('vtable_audit_physical_exports',pin(ROOT/'tools/m4-crt-locale-batch-review/check_v2.py'))
        P.FORWARDS.update(HeapSize='RtlSizeHeap',HeapReAlloc='RtlReAllocateHeap',HeapFree='RtlFreeHeap')
        current=sorted(set(map(int,np['source_pages']))|set(np['game_pages'])|{0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x20000000})
        need(len(current)==62 and TIB not in current and 0x5f4ce000 not in current,'Exact owned whole-page and minimal-TIB scope')
        # Authenticated actual Ninja graph: retained archive is never an active input.
        for level,worker in build['workers'].items():
            exe=pin(worker['path'],worker['sha256']);graph=pin(exe.parent/'build.ninja').read_text()
            line=next(s for s in graph.splitlines() if s.startswith('build '+exe.name+': CXX_EXECUTABLE_LINKER'))
            tokens=line.split(' ',3)[3].split(' |')[0].split(' ')
            linked={str((exe.parent/Path(t.replace('$:',':').replace('$ ',' '))).resolve()) for t in tokens if t.endswith(('.obj','.lib'))}
            declared=set(worker['objects']);need(len(declared)==351 and declared<=linked and len(linked)==381
                 and not any(p.endswith('.lib') for p in linked),'351 literal plus30 actual compiled/capture COFFs, no retained archive on link graph')
            for p in linked:pin(p);need(machine(p)==0x8664,'Actual AMD64 linked COFF')
            need(machine(exe)==0x8664,'Actual AMD64 worker executable');counts['actual_linked_AMD64_COFFs']+=len(linked)
        for l in ex['levels']:
            verify_stage(Path(l['stage']).parent,l['stage_sha256']);a=D.DirectSet(pin(l['capture'],l['capture_sha256']),pin)
            try:
                need(a.words('header.bin',6)==(1,27,54,9968,4,6),'Complete isolated four-root/six-call capture scope')
                for c in range(27):
                    s=f'case-{c}/';first=a.data(s+'first.bin');retry=a.data(s+'retry.bin')
                    need(len(first)==len(retry)==9968,'Actual complete packed State/owner/hardware samples')
                    for i,b in enumerate((first,retry)):
                        tag=struct.unpack_from('<32Q',b);need(tag[:3]==(1,c,i) and tag[6]==tag[16]==1
                             and tag[7]==0x4d573354 and not (tag[8]^tag[9])&0x400,'Actual case/attempt, LastError and DF/cleanup')
                        hardware(b[8880:9424],b[9424:9968],True);counts['outside_hardware_pairs']+=1
                        stem=s+('retry' if i else 'first')
                        hardware(a.data(stem+'-cleanup-hardware-before.bin'),a.data(stem+'-cleanup-hardware-after.bin'));counts['cleanup_hardware_pairs']+=1
                        for label,size in (('State',3504),('CPU',40),('FX',512),('guest-ENV',28),('stack',4096)):
                            need(len(a.data(stem+'-causal-'+label+'.bin'))==size,'Complete causal machine '+label)
                        counts['actual_attempts']+=1
                    rt=struct.unpack_from('<32Q',retry);ft=struct.unpack_from('<32Q',first)
                    need(rt[3]==rt[4]==0 and retry[256:512]==retry[512:768]
                         and retry[768:4272]==retry[4272:7776] and retry[7776:8288]==retry[8288:8800]
                         and retry[8800:8840]==retry[8840:8880], 'Finished/poisoned retry cannot change full machine or owner counters')
                    need(first[4272:7776]==retry[768:4272] and first[8288:8800]==retry[7776:8288]
                         and first[8840:8880]==retry[8800:8840], 'Same actual cleaned Session is retained through retry')
                    for suffix in ('retry-live/','retry-cleaned/'):
                        counts['byte_exact_retry_records']+=same_dump(a,s+'first-cleaned/',s+suffix)
                    counts['same_session_retry_refusals']+=1
                    live=s+'first-live/';clean=s+'first-cleaned/'
                    source=rows(a.data(live+'locale-source-accesses.bin'),'<IIQII')
                    calls=rows(a.data(live+'vtable-call-witnesses.bin'),'<32Q');stores=rows(a.data(live+'vtable-source-stores.bin'),'<16Q')
                    need(a.words(live+'current-page-addresses.bin',62)==tuple(current),'Whole admitted page inventory is exact')
                    for page in current:need(len(a.data(live+f'current-page-{page}.bin'))==4096,'Whole current admitted page');counts['whole_current_pages']+=1
                    need(a.data(live+'current-page-536875008.bin')==a.data(s+'first-causal-stack.bin'),'Whole source stack equals retained causal stack')
                    for index,w in enumerate(stores):
                        value=w[6]^int(c==13 and index==len(stores)-1)
                        need(w[:2]==(1,index) and w[8]>w[7] and source[w[8]-1]==(w[3],w[4],value,w[5],1),
                             'Each actual object-store witness joins a genuine committed source byte write')
                        counts['committed_literal_object_store_joins']+=1
                    call_proof(a,live,source,calls,specs,counts)
                    frames,tib=fs_proof(a,live,source,counts)
                    owned=rows(a.data(live+'locale-allocations.bin'),'<16Q');freed=rows(a.data(clean+'locale-allocations.bin'),'<16Q')
                    need(len(owned)==len(freed)==1,'Actual isolated bootstrap owns one genuine registry allocation')
                    for o,f in zip(owned,freed):
                        need(o[:8]==f[:8] and o[8]==o[7] and o[8] and o[9] and f[8:10]==(0,0)
                             and f[10:12]==((0,1) if c else (1,0)), 'Exactly-once source free or honest fault native safeguard, full identity retained')
                        stem=live+f'locale-allocation-{o[5]}';initial=a.data(stem+'-initial.bin');expected=a.data(stem+'-expected.bin')
                        actual=a.data(stem+'-owned-page.bin');native=a.data(live+f'native-full-{o[5]}.bin')
                        need(len(initial)==len(native)==o[3] and len(actual)==len(expected)==o[4] and o[2]<=o[3]<=o[4],'Complete actual rounded native extent and full guest mirror')
                        want=bytearray(initial+bytes(o[4]-o[3]))
                        for pc,address,value,width,write in source:
                            if write and o[1]<=address<o[1]+o[4]:
                                need(address+width<=o[1]+o[3] and width in (1,2,4,8),'Literal owned write remains within authentic full backing')
                                want[address-o[1]:address-o[1]+width]=value.to_bytes(width,'little')
                        need(bytes(want)==expected==actual and native==expected[:o[3]],'Entire registry backing from actual initial bytes plus literal committed writes')
                        counts['whole_native_guest_owner_source_replays']+=1
                    need(a.data(live+'fs-current-tib.bin')==a.data(clean+'fs-current-tib.bin')
                         and a.data(live+'fs-active-records.bin')==a.data(clean+'fs-active-records.bin'), 'Native fault cleanup does not fabricate source unwind')
                    if c:
                        need(ft[3]==0 and ft[5]==ft[14]==1,'Exactly one genuinely reached causal refusal')
                        causes.append(dict(level=l['level'],**cause_proof(a,c,live,source,calls,stores,frames,tib,counts)));counts['exact_causal_refusals']+=1
                    else:
                        need(ft[3:7]==(1,4,0,1) and len(calls)==6 and all(w[21] for w in calls)
                             and len(frames)==1 and frames[0][21] and not a.data(live+'fs-active-records.bin')
                             and not a.data(live+'mfc-allocation-witnesses.bin') and not a.data(live+'strings-witnesses.bin'), 'Ordinary complete four roots/six returned helpers/one FS/zero new owners')
                        counts['ordinary_sequences']+=1
                    sections=rows(a.data(clean+'locale-critical-sections.bin'),'<16Q')
                    need(all(q[5]==0 and q[7]==q[8]==q[9]==1 for q in sections),'Every actual initialized owned CS was deleted exactly once')
                    summary=a.words(clean+'locale-summary.bin',32);need(summary[23]==1 and not any(summary[k] for k in (14,15,30)), 'No live native heap/owners after finish')
                    heap=a.words(clean+'heap-create-witness.bin',16,'Q');life=a.words(clean+'heap-create-registry.bin',18,'Q')
                    need(heap[6] and heap[6]!=0x48450001 and heap[11]==heap[6]
                         and life[2:11]==(1,0x48450001,heap[6],1,1,0,1,1,1)
                         and life[12:]==(1,0,0,1,heap[6],0),'Actual matching full-width heap handle created/destroyed once')
                    p=clean+'heap-destroy-api-';before=P.identity(a,p+'before',pin);after=P.identity(a,p+'after',pin)
                    raw=a.words(s+'first-cleanup-api-after.bin',11,'Q');target,named,owner,owner_named,base,size,allocation,state,kind,protect,_=raw
                    need(target==named==owner_named and owner==allocation and base<=target<base+size
                         and state==0x1000 and kind==0x1000000 and protect&0xf0 and not protect&0x101,'Independent actual postdestroy executable image identity')
                    path=a.data(s+'first-cleanup-api-path.bin').decode('utf-16-le').split('\0',1)[0];digest=a.data(s+'first-cleanup-api-sha.bin').decode();pin(path,digest)
                    need(before==after==(target,owner,path,digest),'Three independent actually measured HeapDestroy owner/target identities match')
                    rva,forward=P.export(Path(path),'HeapDestroy');need(not forward and owner+rva==target,'Exact physical named AMD64 HeapDestroy export')
                    counts['actual_HeapDestroy_identity_triplets']+=1
                    for index in range(summary[18]):
                        p=clean+f'locale-api-{index}';w=a.words(p+'-witness.bin',32,'Q')
                        if w[14]:
                            before=P.identity(a,p+'-identity-before',pin);after=P.identity(a,p+'-identity-after',pin);raw=a.data(p+'-export-before.bin')
                            need(before==after and raw==a.data(p+'-export-after.bin'),'Actual typed API full-width source ownership identity unchanged')
                            P.export_proof(raw,before,raw[48:80].split(b'\0',1)[0].decode(),pin);counts['physical_typed_API_export_chains']+=1
                need(a.words('counts.bin',3)[1:]==(27,54) and a.data('COMPLETE.txt')==b'Bounded four-root finite-vtable research controls passed; canonical120 is separate\n','Actual complete authored finite suite')
                levels.append(dict(level=l['level'],logical_records=len(a.entries),capture=l['capture'],capture_sha256=l['capture_sha256']));print(json.dumps(levels[-1]),flush=True)
            finally: a.close()
        need(counts['actual_attempts']==108 and counts['exact_causal_refusals']==52 and counts['same_session_retry_refusals']==54
             and counts['actual_HeapDestroy_identity_triplets']==54 and counts['actual_private_span_word_flips']==12,'Complete both-mode independent finite extent')
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        result=dict(passed=passed,execution=str(ROOT/'reports/m4-vtable-controls/execution-r1/report.json'),execution_sha256=EXEC_SHA,
                    build=str(ROOT/'reports/m4-vtable-controls/build-r1/build.json'),build_sha256=BUILD_SHA,
                    checker=str(ROOT/'reports/m4-vtable-controls/check-r1/report.json'),checker_sha256=CHECK_SHA,
                    native_preparation=str(ROOT/'reports/m4-vtable-native/preparation-r4/report.json'),native_preparation_sha256=NATIVE_SHA,
                    levels=levels,counts=dict(counts),causes=causes,files=pins,physical_closure=verify_manifest(pins),
                    scope='Independent actual O0/O2 isolated four-root compiled control audit. Authored caller NumericHostBoundary/ErrorBoundary encloses invocation and C++ catch. Normal zero-argument finite helpers only; source commits/FS chain at refusal are retained. Same finished/poisoned Session retries have every raw dump byte unchanged. Case9 is committed-stack mirror refusal; case10 generic State integrity refusal. Native fallback cleanup does not fabricate source frees or unwind. No naked throwing Session hardware guarantee, nonzero pointee/handler path, new API failures, or full M4/menu/Training admission.',
                    initializer_credit=False,candidate_or_capture_modified=False)
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
        (out/'pins.json').write_text(json.dumps(dict(files=pins|{str(out/'report.json'):sha(out/'report.json')}),indent=2)+'\n')
        print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'),counts=dict(counts))))

if __name__=='__main__': main(sys.argv[1])
