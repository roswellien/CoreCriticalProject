"""Root input/source-derived observer for the native first-service entry probe.

Imports only the frozen root PE reader. No author fixture/executor/model import,
no original execution, and no service implementation or full startup credit.
"""
import hashlib,importlib.util,json,re,struct,subprocess,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
REGS=('eax','ecx','edx','ebx','esp','ebp','esi','edi')
OFF=(2216,2248,2264,2232,2312,2328,2280,2296)
FLAGS=((2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11))
FRAME=0x20001900
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();value=sha(p);assert h is None or value==h,str(p)
    assert str(p) not in PINS or PINS[str(p)]==value;PINS[str(p)]=value;return p
def put(data,o,v,n=4):data[o:o+n]=(v&((1<<(8*n))-1)).to_bytes(n,'little')
def word(data,o=0,n=4):return int.from_bytes(data[o:o+n],'little')
def seeded():
    state=bytearray((i*31+3)&255 for i in range(3504));state[2112:2208]=bytes(96);put(state,2168,0x7ffde000)
    for o,v in ((2090,0x2b),(2106,0x2b),(2110,0x23)):put(state,o,v,2)
    regs=(0x13579bdf,0x2468ace0,0x81726354,0x10293847,FRAME,0x92837465,0x56473829,0xaabbccdd)
    for o,v in zip(OFF,regs):put(state,o,v)
    put(state,2472,0x5ac3a0);put(state,2080,0x202,8)
    for o,_ in FLAGS:state[o]=0
    state[2768:3280]=bytes(512);put(state,2768,0x37f,2);put(state,2792,0x1f80);put(state,2796,0x2ffff)
    for o in (2755,2753,2751,2749,2747,2745,2757,2737,2739,2741,2743):state[o]=0
    return state,dict(zip(REGS,regs))
class Model:
    def __init__(self,program,iat):
        self.program=program;self.state,self.r=seeded();self.pc=0x5ac3a0;self.flags=0x202;self.events=[];self.visited=[]
        self.mem={0x20001000:bytearray(4096),0x5bb000:bytearray(iat),0x7ffde000:bytearray(struct.pack('<I',0xffffffff))}
        self.before={k:bytes(v) for k,v in self.mem.items()}
        # External Runtime invocation installs its own declared caller return.
        # It is outside original instruction/event coverage.
        self.store(FRAME,0xfffffff0,event=False)
    def cell(self,a):
        matches=[(b,a-b) for b,v in self.mem.items() if b<=a and a+4<=b+len(v)]
        assert len(matches)==1,'Owned bounded model address';return matches[0]
    def load(self,a):
        base,o=self.cell(a);v=word(self.mem[base],o);self.events.append((self.pc,a,v,4,0));return v
    def store(self,a,v,event=True):
        base,o=self.cell(a);put(self.mem[base],o,v)
        if event:self.events.append((self.pc,a,v&0xffffffff,4,1))
    def address(self,s):
        if s=='dword ptr fs:[0x0]':return 0x7ffde000
        match=re.fullmatch(r'dword ptr \[(0x[0-9a-f]+|[a-z]+)(?: ([+-]) (0x[0-9a-f]+))?\]',s);assert match,s
        base=int(match[1],16) if match[1].startswith('0x') else self.r[match[1]]
        return (base+(1 if match[2]=='+' else -1)*int(match[3],16) if match[3] else base)&0xffffffff
    def read(self,s):
        if s in self.r:return self.r[s]
        if s.startswith('dword ptr '):return self.load(self.address(s))
        return int(s,0)&0xffffffff
    def write(self,s,v):
        if s in self.r:self.r[s]=v&0xffffffff
        else:self.store(self.address(s),v)
    def push(self,v):self.r['esp']=(self.r['esp']-4)&0xffffffff;self.store(self.r['esp'],v)
    def run(self):
        for _ in range(16):
            size,op,args=self.program[self.pc];self.visited.append(self.pc);next_pc=self.pc+size
            if op=='push':self.push(self.read(args[0]))
            elif op=='mov':self.write(args[0],self.read(args[1]))
            elif op=='add':
                a,b=self.read(args[0]),self.read(args[1]);v=(a+b)&0xffffffff
                bits=int(a+b>0xffffffff)|(int((v&255).bit_count()%2==0)<<2)|(int(bool((a^b^v)&0x10))<<4)|(int(v==0)<<6)|(int(bool(v&0x80000000))<<7)|(int(bool((~(a^b)&(a^v))&0x80000000))<<11)
                self.flags=(self.flags&~0x8d5)|bits;self.write(args[0],v)
            elif op=='call':
                assert self.pc==0x5ac3cf and args==['dword ptr [0x5bb5a4]']
                target=self.read(args[0]);self.push(next_pc)
                for o,name in zip(OFF,REGS):put(self.state,o,self.r[name])
                for o,bit in FLAGS:self.state[o]=(self.flags>>bit)&1
                put(self.state,2472,target)
                runtime_cpu=[self.r[name] for name in REGS]+[self.flags,self.pc];runtime_cpu[4]+=4
                return bytes(self.state),struct.pack('<10I',*runtime_cpu)
            else:raise AssertionError('Unreviewed first-entry opcode '+op)
            self.pc=next_pc
        raise AssertionError('Source first CALL not reached')
def observe(data,program,iat):
    m=Model(program,iat);before,_=seeded();state,cpu=m.run()
    beforecpu=[word(before,o) for o in OFF]+[0x202,0xfffffff0];beforecpu[4]+=4
    assert data['before-state.bin']==before and data['before-cpu.bin']==struct.pack('<10I',*beforecpu),'Entire source-input State/Runtime caller tuple'
    assert data['after-state.bin']==state and data['after-cpu.bin']==cpu,'Entire source-derived State and distinct dispatcher CPU at missing-service boundary'
    assert data['before-fx.bin']==before[2768:3280] and data['after-fx.bin']==before[2768:3280],'Integer-only software FX512 unchanged'
    for tag,memory in (('before',m.before),('after',m.mem)):
        assert data[f'{tag}-page-536875008.bin']==memory[0x20001000],'Complete owned stack page'
        assert data[f'{tag}-page-6008832.bin']==memory[0x5bb000],'Complete raw IAT page'
        assert data[f'{tag}-tib-0.bin']==memory[0x7ffde000],'Complete implemented FS exception-head region'
        assert data[f'{tag}-tib-4.bin']==struct.pack('<2I',0x20002000,0x20001000),'Actual owned stack NT_TIB fields'
        assert data[f'{tag}-tib-24.bin']==struct.pack('<I',0x7ffde000),'Actual owned NT_TIB self field'
    assert data['events.bin']==b''.join(struct.pack('<5I',*e) for e in m.events),'Every actual source PC/address/value/width/direction event'
    assert len(m.visited)==16 and len(m.events)==15
    return m
def main(build,out):
    assert not out.exists() and out.is_relative_to(ROOT/'reports/m4-crt-entry');out.mkdir(parents=True)
    (out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py')
    try:
        path=pin(ROOT/'tools/analysis/pe.py','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
        spec=importlib.util.spec_from_file_location('root_entry_PE',path);PE=importlib.util.module_from_spec(spec);spec.loader.exec_module(PE)
        image_path=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');image=PE.PEImage(image_path.read_bytes())
        objdump=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe','a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
        command=[str(objdump),'-d','--x86-asm-syntax=intel','--start-address=5948320','--stop-address=5948373',str(image_path)]
        cp=subprocess.run(command,capture_output=True);(out/'source.txt').write_bytes(cp.stdout);(out/'source.stderr').write_bytes(cp.stderr);assert cp.returncode==0
        program={}
        for line in cp.stdout.decode().splitlines():
            m=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*([a-z]+)\s*(.*?)\s*$',line)
            if m:
                pc=int(m[1],16);code=bytes.fromhex(m[2]);assert image.read(image.rva_range(pc-image.image_base,len(code))[0],len(code))==code
                args=re.sub(r'\s*<[^>]*>','',m[4]).strip();program[pc]=(len(code),m[3],args.split(', ') if args else [])
        assert len(program)==16
        iat=image.read(image.rva_range(0x5bb000-image.image_base,4096)[0],4096)
        receipt=json.loads(pin(build/'build.json').read_text(encoding='utf-8-sig'));assert receipt['passed'] and receipt['native_entry_executed'] and not receipt['original_executed']
        for key in ('source_files','primary_pre_call_tools','artifacts'):
            for p,h in receipt[key].items():pin(p,h)
        controls=[];rows=[]
        for level in ('O0','O2'):
            directory=build/f'native-{level}';data={p.name:pin(p).read_bytes() for p in directory.glob('*.bin')};m=observe(data,program,iat)
            for name,offset in (('before-state.bin',2168),('before-cpu.bin',16),('after-state.bin',2065),('after-state.bin',2312),('after-state.bin',2328),('after-state.bin',2472),('after-state.bin',3400),('after-cpu.bin',16),('after-cpu.bin',36),('after-fx.bin',0),('after-page-536875008.bin',0x884),('after-page-536875008.bin',0x870),('after-page-6008832.bin',0x5a4),('after-tib-0.bin',0),('after-tib-4.bin',0),('after-tib-24.bin',0),('events.bin',0),('events.bin',280)):
                changed=dict(data);b=bytearray(data[name]);b[offset]^=1;changed[name]=bytes(b)
                try:observe(changed,program,iat)
                except AssertionError:controls.append(dict(level=level,file=name,offset=offset,rejected=True))
                else:raise AssertionError('Raw first-entry corruption accepted')
            rows.append(dict(level=level,State_bytes=3504,stack_and_IAT_pages=2,NT_TIB_regions=[4,8,4],source_PCs=m.visited,events=15,missing_service='MSVCRT.dll!__set_app_type',guest_SEH_frame=FRAME-20))
        for attempt in ('first-fault-build-r1','first-fault-build-r2','first-fault-build-r3'):
            base=ROOT/'reports/m4-crt-entry'/attempt
            for path in base.rglob('*'):
                if path.is_file() and 'compiler-temp' not in path.parts:pin(path)
        for name in ('review-source.py','failure.txt'):pin(ROOT/'reports/m4-crt-entry/first-fault-observation-r1'/name)
        pin(Path(__file__));pin(sys.executable)
        for p in out.iterdir():
            if p.is_file():pin(p)
        report=dict(passed=True,scope='Root source/input-derived first-service research observer; independent compiled/ABI review and original comparison pending',rows=rows,own_corruption_rejects=controls,physical_bindings=len(PINS),source_decode_command=command,original_executed=False,guest_source_PCs_observed_natively=16,full_source_object_PCs_not_execution_credit=148,raw_hint_target_and_dispatch_slot_explicit=True,limitations=['Author-defined initial State/stack policy, not original process startup observation','Only implemented NT_TIB regions captured; unmapped TEB holes remain absent','Native missing-service dispatch leaves source State at raw IAT target and Runtime CPU at call site with unpushed return; both independently modeled','No numerical/live-stack FX coherence or actual caller host-state preservation claim in this integer entry probe','Full exception dispatch, service returns, initialized CRT and menus unimplemented','Post-build source/tool associations are not execution-time dependency attestation'],full_CRT=False,full_startup=False,whole_M4_complete=False)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,records=2,source_PCs=16,events=30,corruption_rejects=len(controls),report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'))))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
