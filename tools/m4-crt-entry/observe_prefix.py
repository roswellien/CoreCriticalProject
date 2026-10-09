"""Root source/input-derived three-CRT-service entry prefix observer.

The sole model import is the exact frozen root first-fault observer. Provider
effects follow fresh original disassembly; no author service or fixture import.
"""
import hashlib,importlib.util,json,re,struct,subprocess,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();v=sha(p);assert h is None or v==h,str(p)
    assert str(p) not in PINS or PINS[str(p)]==v;PINS[str(p)]=v;return p
def module(name,path,expected):
    spec=importlib.util.spec_from_file_location(name,pin(path,expected));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
F=module('root_frozen_first_fault',ROOT/'tools/m4-crt-entry/observe_first_fault.py','a8c5d9baabd0ec26d89618c29bde8f647458133338c601107143dbe9418a7e33')
def decode(tool,pe,path,start,stop,out,label):
    command=[str(tool),'-d','--x86-asm-syntax=intel',f'--start-address={start}',f'--stop-address={stop}',str(path)]
    cp=subprocess.run(command,capture_output=True);(out/f'{label}.txt').write_bytes(cp.stdout);(out/f'{label}.stderr').write_bytes(cp.stderr);assert cp.returncode==0
    program={}
    for line in cp.stdout.decode().splitlines():
        m=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*([a-z]+)\s*(.*?)\s*$',line)
        if m:
            pc=int(m[1],16);code=bytes.fromhex(m[2]);assert pe.read(pe.rva_range(pc-pe.image_base,len(code))[0],len(code))==code
            args=re.sub(r'\s*<[^>]*>','',m[4]).strip();program[pc]=(len(code),m[3],args.split(', ') if args else [])
    return program,command
class Model(F.Model):
    def __init__(self,program,pages,provider_program):
        super().__init__(program,pages[0x5bb000]);self.provider_program=provider_program
        for a in (0x736000,0x9a1000):self.mem[a]=bytearray(pages[a])
        self.mem[0x78038ee8]=bytearray(12)
        self.before.update({a:bytes(self.mem[a]) for a in (0x736000,0x9a1000,0x78038ee8)})
        self.routes=[dict(site=0xfffffff0,target=0x5ac3a0,return_pc=0xfffffff0,import_=False,completed=False)]
        self.runtime_cpu=None;self.provider_PCs=[]
    def raw_load(self,a):b,o=self.cell(a);return F.word(self.mem[b],o)
    def raw_store(self,a,v):b,o=self.cell(a);F.put(self.mem[b],o,v)
    def project(self,pc,flat=False):
        for o,k in zip(F.OFF,F.REGS):F.put(self.state,o,self.r[k])
        for o,bit in F.FLAGS:self.state[o]=(self.flags>>bit)&1
        F.put(self.state,2472,pc)
        if flat:F.put(self.state,2080,self.flags,8)
    def provider(self,pc):
        # Fresh decoded provider MOV/RET bodies. These original instructions
        # explain typed service effects; they are not native Remill events.
        for _ in range(3):
            size,op,args=self.provider_program[pc];self.provider_PCs.append(pc)
            if op=='mov':
                src=args[1]
                if src in self.r:v=self.r[src]
                elif src.startswith('dword ptr '):v=self.raw_load(self.address(src))
                else:v=int(src,0)&0xffffffff
                if args[0] in self.r:self.r[args[0]]=v
                else:self.raw_store(self.address(args[0]),v)
            elif op=='ret':
                return_pc=self.raw_load(self.r['esp']);self.r['esp']+=4;return return_pc
            else:raise AssertionError('Unreviewed provider opcode')
            pc+=size
        raise AssertionError('Measured provider RET not reached')
    def run(self):
        source_calls={0x5ac3cf:(0x5bb5a4,0x78004625),0x5ac3ec:(0x5bb57c,0x7800462f),0x5ac3fa:(0x5bb504,0x78004635)}
        for _ in range(26):
            size,op,args=self.program[self.pc];self.visited.append(self.pc);next_pc=self.pc+size
            if self.pc==0x5ac408:
                assert (op,args)==('mov',['eax','dword ptr [0x5bb508]'])
                self.load(0x5bb508);self.project(self.pc);return bytes(self.state),self.runtime_cpu
            if op=='push':self.push(self.read(args[0]))
            elif op=='mov':self.write(args[0],self.read(args[1]))
            elif op=='add':
                a,b=self.read(args[0]),self.read(args[1]);v=(a+b)&0xffffffff
                bits=int(a+b>0xffffffff)|(int((v&255).bit_count()%2==0)<<2)|(int(bool((a^b^v)&0x10))<<4)|(int(v==0)<<6)|(int(bool(v&0x80000000))<<7)|(int(bool((~(a^b)&(a^v))&0x80000000))<<11)
                self.flags=(self.flags&~0x8d5)|bits;self.write(args[0],v)
            elif op=='call':
                slot,entry=source_calls[self.pc];assert args==[f'dword ptr [{slot:#x}]']
                self.read(args[0]);self.push(next_pc)
                assert self.provider(entry)==next_pc
                self.project(next_pc,flat=True)
                self.runtime_cpu=struct.pack('<10I',*[self.r[k] for k in F.REGS],self.flags,next_pc)
                self.routes.append(dict(site=self.pc,target=slot,return_pc=next_pc,import_=True,completed=True))
            else:raise AssertionError('Unreviewed entry prefix opcode')
            self.pc=next_pc
        raise AssertionError('Unconnected data import not reached')
def observe(data,program,pages,providers,calls,result):
    m=Model(program,pages,providers);before,_=F.seeded();state,cpu=m.run()
    beforecpu=[F.word(before,o) for o in F.OFF]+[0x202,0xfffffff0];beforecpu[4]+=4
    assert data['before-state.bin']==before and data['before-cpu.bin']==struct.pack('<10I',*beforecpu),'Entire source input State/caller tuple'
    assert data['after-state.bin']==state and data['after-cpu.bin']==cpu,'Entire persistent source State and last-return RuntimeCPU'
    assert data['before-fx.bin']==data['after-fx.bin']==before[2768:3280],'Integer-only software FX512'
    for tag,mem in (('before',m.before),('after',m.mem)):
        for a in (0x20001000,0x5bb000,0x736000,0x9a1000):assert data[f'{tag}-page-{a}.bin']==mem[a],'Complete prefix memory page'
        assert data[f'{tag}-crt-globals.bin']==mem[0x78038ee8],'Complete provider DWORD region'
        assert data[f'{tag}-tib-0.bin']==mem[0x7ffde000],'Exception-head NT_TIB'
        assert data[f'{tag}-tib-4.bin']==struct.pack('<2I',0x20002000,0x20001000),'Stack NT_TIB region'
        assert data[f'{tag}-tib-24.bin']==struct.pack('<I',0x7ffde000),'Self NT_TIB region'
    assert data['events.bin']==b''.join(struct.pack('<5I',*e) for e in m.events),'Every native game event'
    expected=[{('import' if k=='import_' else k):v for k,v in row.items()} for row in m.routes]
    assert calls==expected and len(calls)==4,'Actual owner/call frames completed/incomplete ledger'
    assert len(m.visited)==26 and len(m.events)==26 and len(m.provider_PCs)==7
    assert result['passed'] and result['source_events']==26 and result['first_call_pc']==0x5ac408 and result['missing_IAT']==0x5bb508 and result['poisoned_retry_denied'] and not result['SEH_dispatch_implemented'] and result['SEH_frame']==F.FRAME-20
    assert F.word(m.mem[0x5bb000],0x508)==0x1ded32,'Raw game lookup RVA distinct from provider initialized data'
    return m
def main(build,out):
    assert not out.exists() and out.is_relative_to(ROOT/'reports/m4-crt-entry');out.mkdir(parents=True);(out/'review-source.py').write_bytes(Path(__file__).read_bytes())
    try:
        PE=module('root_prefix_PE',ROOT/'tools/analysis/pe.py','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
        image_path=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');image=PE.PEImage(image_path.read_bytes())
        provider_path=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');provider=PE.PEImage(provider_path.read_bytes())
        tool=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe','a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
        program,entry_command=decode(tool,image,image_path,0x5ac3a0,0x5ac40d,out,'entry-source');providers,provider_command=decode(tool,provider,provider_path,0x78004625,0x7800463b,out,'provider-source')
        assert len(program)==26 and len(providers)==7
        def mapped_page(a):
            rva=a-image.image_base;matches=[s for s in image.sections if s['virtual_address']<=rva and rva+4096<=s['virtual_address']+((max(s['virtual_size'],s['raw_size'])+4095)&~4095)]
            assert len(matches)==1;section=matches[0];delta=rva-section['virtual_address'];n=max(0,min(4096,section['raw_size']-delta))
            return image.read(section['raw_offset']+delta,n)+bytes(4096-n) if n else bytes(4096)
        pages={a:mapped_page(a) for a in (0x5bb000,0x736000,0x9a1000)}
        assert provider.read(provider.rva_range(0x78038ee8-provider.image_base,12)[0],12)==bytes(12)
        receipt=json.loads(pin(build/'build.json').read_text(encoding='utf-8-sig'));assert receipt['passed'] and receipt['native_entry_executed'] and not receipt['original_executed']
        for key in ('source_files','primary_pre_call_tools','artifacts'):
            for p,h in receipt[key].items():pin(p,h)
        pin(ROOT/'reports/m4-crt/provider-comparison-r1/report.json','09a6018bb2cd3a6daf79786ee0bd2485b25f6b8c78740a352989019a2511e42a')
        rows=[];controls=[]
        for level in ('O0','O2'):
            directory=build/f'native-{level}';data={p.name:pin(p).read_bytes() for p in directory.glob('*.bin')};calls=json.loads(pin(directory/'calls.json').read_text());result=json.loads(pin(directory/'result.json').read_text())
            m=observe(data,program,pages,providers,calls,result)
            for name,offset in (('before-state.bin',2168),('before-cpu.bin',16),('after-state.bin',2065),('after-state.bin',2080),('after-state.bin',2312),('after-state.bin',2328),('after-state.bin',2472),('after-state.bin',3400),('after-cpu.bin',16),('after-cpu.bin',36),('after-fx.bin',0),('after-page-536875008.bin',0x884),('after-page-536875008.bin',0x870),('after-page-6008832.bin',0x508),('after-page-7561216.bin',0x59c),('after-page-10096640.bin',0x7ec),('after-crt-globals.bin',0),('after-crt-globals.bin',4),('after-crt-globals.bin',8),('after-tib-0.bin',0),('after-tib-4.bin',0),('after-tib-24.bin',0),('events.bin',0),('events.bin',500)):
                altered=dict(data);b=bytearray(data[name]);b[offset]^=1;altered[name]=bytes(b)
                try:observe(altered,program,pages,providers,calls,result)
                except AssertionError:controls.append(dict(level=level,file=name,offset=offset,rejected=True))
                else:raise AssertionError('Prefix raw corruption accepted')
            for index,key in ((0,'completed'),(1,'site'),(2,'target'),(3,'return_pc')):
                altered=[dict(row) for row in calls];altered[index][key]=not altered[index][key] if isinstance(altered[index][key],bool) else altered[index][key]^1
                try:observe(data,program,pages,providers,altered,result)
                except AssertionError:controls.append(dict(level=level,ledger=index,key=key,rejected=True))
                else:raise AssertionError('Prefix route corruption accepted')
            rows.append(dict(level=level,State_bytes=3504,complete_pages=4,provider_DWORDs=3,NT_TIB_regions=[4,8,4],game_source_PCs=m.visited,modeled_provider_PCs=m.provider_PCs,actual_game_events=26,completed_imports=3,root_incomplete=True,denial_before_MOV_completion=True))
        for name in ('prefix-preparation-r1','prefix-preparation-r2','prefix-preparation-r3','prefix-build-r1','prefix-build-r2'):
            for path in (ROOT/'reports/m4-crt-entry'/name).rglob('*'):
                if path.is_file() and 'compiler-temp' not in path.parts:pin(path)
        for path in (ROOT/'reports/m4-crt-entry/prefix-observation-r1').iterdir():
            if path.is_file():pin(path)
        pin(__file__);pin(sys.executable)
        for p in out.iterdir():
            if p.is_file():pin(p)
        report=dict(passed=True,scope='Root source/input-derived native three-CRT-service entry prefix research; compiled causal composition review and original game entry comparison pending',rows=rows,own_corruption_rejects=controls,physical_bindings=len(PINS),source_commands=[entry_command,provider_command],author_fixture_or_service_model_imported=False,original_executed=False,full_source_object_PCs_not_execution_credit=148,raw_game_IAT_508=0x1ded32,provider_adjust_fdiv_file_DWORD=0,unconnected_initialized_FDIV_dependency=True,limitations=['Author-defined initial integer State/stack policy; not observed original process startup','Provider original disassembly models typed service effects; provider instructions are not captured native Remill source events','Only implemented NT_TIB fields captured; no guest exception dispatch','Software FP image is unchanged; no numerical/coherence/caller-host boundary claim','Current build/source associations are not execution-time dependency attestation','No initialized FDIV, remaining CRT, initializer coverage, application or menu acceptance'],full_CRT=False,full_startup=False,whole_M4_complete=False)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,records=2,game_PCs=26,game_events=52,completed_imports=6,corruption_rejects=len(controls),report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'))))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
