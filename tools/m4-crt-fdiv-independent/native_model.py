"""Independent source-input model for the bounded native FDIV writer.

Uses only frozen root-owned scalar instruction semantics and PE metadata.
Actual Windows return observations are explicit external inputs. No original
instructions, author comparator or author fixture generator are executed.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import sys
import traceback

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
PAGES=(0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000,0x20001000,0x5bb000)
CWS=(0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f)
REGS=('eax','ecx','edx','ebx','esp','ebp','esi','edi')
OFFSETS=(2216,2248,2264,2232,2312,2328,2280,2296)
FLAGS=((2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11))
STRIDE=107740


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def pin(path,expected=None):
    path=Path(path).resolve();digest=sha(path)
    assert expected is None or digest==expected,str(path)
    assert str(path) not in PINS or PINS[str(path)]==digest
    PINS[str(path)]=digest;return path


def module(path,name,expected):
    spec=importlib.util.spec_from_file_location(name,pin(path,expected));result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


CONTROL=module(ROOT/'tools/m4-crt-control-independent/review.py','root_fdiv_scalar','49eea1a0c6615d685acad629c4ef10bab32c6f14aa960a0c1e1d01c6750f6e61')
PE=module(ROOT/'tools/analysis/pe.py','root_fdiv_PE','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')


def u32(data,offset=0):return struct.unpack_from('<I',data,offset)[0]
def put(data,offset,value,width=4):struct.pack_into({1:'<B',2:'<H',4:'<I',8:'<Q'}[width],data,offset,value&((1<<(8*width))-1))


def seeded(cw,repeat):
    state=bytearray((i*31+repeat*17+3)&255 for i in range(3504));state[2112:2208]=bytes(96)
    put(state,2168,0x7ffde000)
    for offset,value in zip(OFFSETS,(0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xaabbccdd)):put(state,offset,value)
    put(state,2472,0x78004254);put(state,2080,0x202,8)
    for offset,_ in FLAGS:state[offset]=0
    put(state,2768,cw,2);put(state,2770,0,2);state[2772]=0
    for offset in (2755,2753,2751,2749,2747,2745,2757,2737,2739,2741,2743):state[offset]=0
    for offset,value in ((2792,0x1f80),(2796,0x2ffff),(2776,0x11223344),(2784,0x55667788)):put(state,offset,value)
    for offset,value in ((2780,0x23),(2774,0x11d),(2788,0x2b)):put(state,offset,value,2)
    fx=bytearray(state[2768:3280]);fx[6:24]=bytes(18)
    return state,fx


class Model(CONTROL.X86):
    def __init__(self,program,pages,cw,feature):
        self.program=program;self.r=dict(zip(REGS,(0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xaabbccdd)))
        self.pc=0x78004254;self.flags=0x202;self.cw=cw;self.memory=bytearray(pages);self.feature=feature;self.events=[];self.frames=[];self.visited=set();self.routes=[];self.enter()

    def position(self,address,size):
        matching=[i*4096+address-page for i,page in enumerate(PAGES) if page<=address and address+size<=page+4096]
        assert len(matching)==1,'Exact owned model page';return matching[0]

    def load(self,address,size,event=True):
        offset=self.position(address,size);value=int.from_bytes(self.memory[offset:offset+size],'little')
        if event:self.events.append((0,self.pc,address,value,size))
        return value

    def store(self,address,value,size):
        value&=(1<<(size*8))-1;put(self.memory,self.position(address,size),value,size);self.events.append((1,self.pc,address,value,size))

    def address(self,operand):
        expression=re.fullmatch(r'(?:byte|word|dword) ptr \[([a-z]+|0x[0-9a-f]+)(?: ([+-]) (0x[0-9a-f]+))?\]',operand)
        assert expression,operand
        base=self.r[expression[1]] if expression[1] in self.r else int(expression[1],0)
        return (base+(0 if expression[3] is None else (1 if expression[2]=='+' else -1)*int(expression[3],0)))&0xffffffff

    def read(self,operand):
        if operand.startswith(('byte ptr','word ptr','dword ptr')):
            address=self.address(operand);value=self.load(address,self.width(operand))
            if address in (0x7802e098,0x7802e0d0):
                slot,target=(0x7802e098,0x11000100) if address==0x7802e098 else (0x7802e0d0,0x11000200)
                assert value==(0x345d2 if slot==0x7802e098 else 0x346ac)
                self.events.append((6,self.pc,address,target,4));return target
            return value
        return super().read(operand)

    def write(self,operand,value):
        if operand.startswith(('byte ptr','word ptr','dword ptr')):self.store(self.address(operand),value,self.width(operand))
        else:super().write(operand,value)

    def push(self,value):
        self.r['esp']-=4;self.store(self.r['esp'],value,4)

    def pop(self):
        result=self.load(self.r['esp'],4);self.r['esp']+=4;return result

    def enter(self):
        ret=self.load(self.r['esp'],4,False);self.frames.append((self.pc,self.r['esp'],ret,self.nonvol()));self.events.append((2,self.pc,self.r['esp'],ret,4))

    def run(self):
        for _ in range(512):
            if self.pc==0x78004232:
                assert not self.frames and len(self.events)==97 and len(self.routes)==3
                return self
            assert self.pc in self.program,hex(self.pc)
            self.visited.add(self.pc);size,op,args=self.program[self.pc];next_pc=self.pc+size
            if op in ('mov','movzx'):self.write(args[0],self.read(args[1]))
            elif op in ('xor','and','or','test','cmp'):
                result=self.arithmetic(op,self.read(args[0]),self.read(args[1]),self.width(args[0]))
                if op not in ('test','cmp'):self.write(args[0],result)
            elif op=='not':self.write(args[0],~self.read(args[0]))
            elif op=='push':self.push(self.read(args[0]))
            elif op=='pop':self.write(args[0],self.pop())
            elif op=='call':
                target=self.read(args[0]);self.push(next_pc)
                if target in (0x11000100,0x11000200,0x11000300):
                    index=len(self.routes);assert target==(0x11000100,0x11000200,0x11000300)[index]
                    count=(4,8,4)[index];value=(0x11001000,0x11000300,self.feature)[index];esp=self.r['esp']
                    argument=self.load(esp+4,4,False);assert argument==(0x7802e404,0x11001000,0)[index]
                    if index==1:assert self.load(esp+8,4,False)==0x7802e3e8
                    self.r['eax']=value;self.r['esp']+=4+count;self.events.append((4,self.pc,target,value,count));self.routes.append((self.pc,target,next_pc,esp,self.r['esp'],count,1))
                else:self.pc=target;self.enter();next_pc=target
            elif op=='ret':
                frame=self.frames.pop();next_pc=self.pop();assert (self.r['esp'],next_pc,self.nonvol())==(frame[1]+4,frame[2],frame[3]);self.events.append((3,next_pc,self.r['esp'],next_pc,4))
            elif op=='leave':self.r['esp']=self.r['ebp'];self.r['ebp']=self.pop()
            elif op=='fnstcw':self.write(args[0],self.cw)
            elif op=='fldcw':self.cw=(self.read(args[0])&0x1f3f)|0x40
            elif op=='wait':pass
            elif op=='fnclex':self.events.append((5,self.pc,0,0,2))
            elif op in ('je','jne'):
                if bool(self.flags&0x40)==(op=='je'):next_pc=self.read(args[0])
            elif op=='jmp':next_pc=self.read(args[0])
            else:raise AssertionError('Unsupported source '+op)
            self.pc=next_pc
        raise AssertionError('Bounded source model exhausted')


def observe(row,index,program,provider_pages,game_page):
    assert len(row)==STRIDE
    cw,repeat=CWS[index//2],index%2
    assert struct.unpack_from('<7I',row)==(index,repeat,cw,1,97,3,3)
    before,fx=seeded(cw,repeat);assert row[28:3532]==before and row[7036:7548]==fx
    stack=bytearray((i*7+repeat*19+0xa5)&255 for i in range(4096));put(stack,0x800,0x78004232)
    pages=b''.join(provider_pages)+stack+game_page;assert row[9140:46004]==pages
    feature=u32(row,88072+2*6556+12)
    for phase in range(3):
        at=88072+phase*6556;kind,token,arg,result,error=struct.unpack_from('<5I',row,at);host=struct.unpack_from('<Q',row,at+20)[0]
        assert kind==phase+1 and token==(0x11001000,0x11000300,0x11000300)[phase] and arg==0
        if phase<2:assert result==0 and host
        else:assert result==host==feature
    model=Model(program,pages,cw,feature).run()
    after=bytearray(before)
    for offset,name in zip(OFFSETS,REGS):put(after,offset,model.r[name])
    put(after,2472,model.pc)
    for offset,bit in FLAGS:after[offset]=(model.flags>>bit)&1
    put(after,2768,model.cw,2);put(fx,0,model.cw,2)
    assert row[3532:7036]==after,'Whole3504 source State'
    assert row[7548:8060]==fx and row[46004:82868]==model.memory,'Whole separate FX and nine pages'
    events=b''.join(struct.pack('<5I',*event) for event in model.events)
    assert row[82868:87988]==events+bytes(5120-len(events)),'Exact97 source accesses/frames/routes/FNCLEX'
    assert row[87988:88072]==b''.join(struct.pack('<7I',*route) for route in model.routes),'Actual stdcall frames'
    assert row[8060:8572]==row[8572:9084] and row[9084:9112]==row[9112:9140],'Internal restored host checkpoints only'
    return model.visited


def main(out):
    assert out.parent==ROOT/'reports/m4-crt-fdiv' and not out.exists()
    out.mkdir();(out/'review-source.py').write_bytes(Path(__file__).read_bytes())
    try:
        recovery=json.loads(pin(ROOT/'reports/m4-crt-fdiv/source-recovery-r1/report.json','c124fbfbf5bf64125b9e93c52b9b0e0500f2dd93df6d6ee440b89f5d90f895fd').read_text())
        provider=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
        game=PE.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
        def source(pe,address,size):offset,_=pe.rva_range(address-pe.image_base,size);return pe.data[offset:offset+size]
        page_map={page:bytearray([0xcc]*4096) for page in PAGES[:7]}
        for span in recovery['source_spans']:
            raw=source(provider,span['address'],span['size_bytes']);assert hashlib.sha256(raw).hexdigest()==span['sha256'];at=span['address']&4095;page_map[span['address']&~4095][at:at+len(raw)]=raw
        # The source callback orchestrator owns the real outer return address.
        # Its retained bytes are identity data; this writer gate does not run it.
        for row in recovery['callback_orchestrator']['instructions']:
            raw=source(provider,row['address'],row['size']);assert raw.hex()==row['bytes_hex'];at=row['address']&4095;page_map[row['address']&~4095][at:at+len(raw)]=raw
        for constant in recovery['fallback_constants']:
            address=constant['address'];raw=source(provider,address,8);assert hashlib.sha256(raw).hexdigest()==constant['sha256'];page_map[address&~4095][address&4095:(address&4095)+8]=raw
        for page in (0x7802e000,0x78037000):page_map[page]=bytearray(source(provider,page,4096))
        game_page=source(game,0x5bb000,4096);program={}
        for graph in recovery['complete_graphs']:
            for row in graph['instructions']:
                assert source(provider,row['address'],row['size']).hex()==row['bytes_hex']
                args=re.sub(r' <[^>]+>','',row['operands']);value=(row['size'],row['mnemonic'],[a.strip() for a in args.split(',')] if args else [])
                assert row['address'] not in program or program[row['address']]==value;program[row['address']]=value
        assert len(program)==204
        coverage=set();mutations=0;raw_count=0
        for level in ('O0','O2'):
            raw=pin(ROOT/f'reports/m4-crt-fdiv/native-build-r3/native-{level}.bin').read_bytes();assert raw[:8]==b'MW4FDIN2' and struct.unpack_from('<4I',raw,8)==(2,24,STRIDE,9) and len(raw)==24+24*STRIDE
            for index in range(24):coverage|=observe(raw[24+index*STRIDE:24+(index+1)*STRIDE],index,program,[page_map[p] for p in PAGES[:7]],game_page);raw_count+=1
            row=raw[24:24+STRIDE]
            for offset in (0,8,12,28,3532,7548,46004,82868,87988,8060,9084):
                corrupt=bytearray(row);corrupt[offset]^=1;rejected=False
                try:observe(corrupt,0,program,[page_map[p] for p in PAGES[:7]],game_page)
                except AssertionError:rejected=True
                assert rejected,'Causal own observer control';mutations+=1
        assert len(coverage)==174
        result=dict(passed=True,scope='Independent source-input native-only writer comparison; original and complete CRT/startup remain unaccepted',native_records=raw_count,source_PCs=len(program),executed_source_PCs=len(coverage),whole_State_bytes=3504,pages=9,actual_events=48*97,actual_stdcall_routes=48*3,observer_corruption_rejects=mutations,author_comparator_or_fixture_imported=False,actual_API_result_inputs='Frozen real Windows result observations; no constant expected BOOL',host_restoration_scope='Internal Registry checkpoints; final caller boundary and volatile SIMD separate',original_executed=False,native_executed_by_reviewer=False,full_CRT=False,whole_M4_complete=False)
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');pin(Path(__file__))
        for path in out.iterdir():
            if path.is_file():pin(path)
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,records=raw_count,source_PCs=len(coverage),mutations=mutations,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'))))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);main(parser.parse_args().output.resolve())
