"""Root-owned input/source oracle for the exact connected original wrapper.

Imports only the separately frozen root CRT instruction interpreter. The
author connected comparator, fixtures and executable helpers are not imported.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import traceback

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];GATE=ROOT/'reports/m4-crt-control-integration';PINS={}
CWS=(0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f)
SP=(0x100,0x1fc,0x200,0x7f0,0x7fc,0x800,0x808,0xff0)
FLAGS=(0x202,0x203,0x212,0x246,0x282,0xa02,0x242,0x802)

def need(ok,why):
    if not ok:raise ValueError(why)

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def bind(p,h=None):
    p=Path(p).resolve();got=sha(p);need(h is None or got==h,'Exact root-model identity '+str(p))
    need(str(p) not in PINS or PINS[str(p)]==got,'Conflicting root identity');PINS[str(p)]=got;return p

def u32(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def u16(b,o=0):return struct.unpack_from('<H',b,o)[0]
def put(b,o,v,n=4):b[o:o+n]=v.to_bytes(n,'little')

path=bind(ROOT/'tools/m4-crt-control-independent/review.py','49eea1a0c6615d685acad629c4ef10bab32c6f14aa960a0c1e1d01c6750f6e61')
spec=importlib.util.spec_from_file_location('own_root_crt_instruction_model',path);CRT=importlib.util.module_from_spec(spec);spec.loader.exec_module(CRT)

def before_cpu(scenario):
    q=0x1020304*scenario
    return (0x13579bdf^q,0x2468ace0^q,0x81726354^q,0x10293847^q,0x20001000+SP[scenario],0x92837465^q,0x56473829^q,0xaabbccdd^q,FLAGS[scenario]|0x200,0x5ac5a0)

def add_flags(flags,a,b):
    total=a+b;value=total&0xffffffff
    bits=(int(total>0xffffffff)|(int((value&255).bit_count()%2==0)<<2)|(int(bool((a^b^value)&16))<<4)
          |(int(value==0)<<6)|(int(bool(value&0x80000000))<<7)|(int(bool((~(a^b)&(a^value))&0x80000000))<<11))
    return (flags&~0x8d5)|bits

def source_model(program,before,stack,cw):
    """Execute provider instructions between input-derived actual game frames.

    The two literal PUSH arguments and CALL frame come from the recovered game
    bytes. A reviewer-only zero-length jump at provider continuation ends the
    provider interpreter; ADD ESP,8 and RET are modeled separately below.
    This jump is not claimed as an executed original instruction.
    """
    memory=bytearray(stack);sp=before[4]
    for delta,value in ((4,0x30000),(8,0x10000),(12,0x5ac5af)):put(memory,sp-0x20001000-delta,value)
    cpu=list(before);cpu[4]=sp-12;cpu[9]=0x780042e1
    instructions=dict(program);instructions[0x5ac5af]=(0,'jmp',['0x10000100'])
    after,memory,changed,events,visited=CRT.X86(instructions,tuple(cpu),memory,cw).run()
    after=list(after);need(after[4]==sp-8,'Actual cdecl provider RET closes one word')
    after[8]=add_flags(after[8],after[4],8);after[4]+=8
    need(u32(memory,sp-0x20001000)[0]==0x5ac436,'Actual outer game continuation word')
    after[4]+=4;after[9]=0x10000100
    return tuple(after),memory,changed,events,visited

def observe(row,index,program):
    scenario=index%8;cw=CWS[(index%96)//8]
    need(len(row)==10444 and u32(row,0,3)==(index//96,cw,scenario),'Exact192 original row/tag ordering')
    before=before_cpu(scenario);need(u32(row,12,10)==before,'CPL3 IF-preserving input CPU/FLAGS model')
    stack=bytearray([0xa5]*4096);put(stack,SP[scenario],0x5ac436)
    need(row[2252:6348]==stack,'Complete original input stack fixture')
    f0,f1=row[92:604],row[604:1116];e0,e1=row[2140:2168],row[2168:2196]
    need(u16(f0)==cw and u16(f0,2)==0 and f0[4]==0 and u32(f0,24)[0]==0x1f80,'Masked empty TOP0 incoming FP domain')
    for i in range(8):need(f0[32+16*i:42+16*i]==bytes((17+i*13+j*7)&255 for j in range(10)),'All eight original seeded raw80 slots')
    need(f0[160:288]==bytes((i*19+3)&255 for i in range(128)),'All eight original seeded XMM lanes')
    env=struct.pack('<7I',0xffff0000|cw,0xffff0000,0xffffffff,0x11223344,0x11d0023,0x55667788,0xffff002b)
    need(e0==env,'Complete original incoming legacy environment')
    after,memory,changed,events,visited=source_model(program,before,stack,cw)
    actual=u32(row,52,10)
    need(actual==after,'Input-derived entire original exit CPU including ADD-defined AF')
    need(row[6348:10444]==memory,'Input-derived full original post stack/frame/argument residue')
    fx=bytearray(f0);put(fx,0,changed,2);env=bytearray(e0);put(env,0,changed,2)
    need(f1==fx and e1==env,'Only source-derived normalized CW changes; complete original FX/ENV retained')
    need(row[1116:1628]==row[1628:2140] and row[2196:2224]==row[2224:2252],'Complete actual original host FX/ENV restoration')
    return after,memory,changed,events,visited

def main(out):
    need(not out.exists() and out.is_relative_to(GATE),'Fresh private original-only connected model')
    out.mkdir(parents=True);(out/'model-source.py').write_bytes(Path(__file__).read_bytes());bind(out/'model-source.py')
    try:
        program,commands=CRT.decode(out)
        path=bind(GATE/'original-normal-windows-r2/original.bin','4dfcd09eac41e6323150701e2cf85693719eb397aecfb81b0a4962fe31adfabf');raw=path.read_bytes()
        need(raw[:8]==b'MW4CIC01' and u32(raw,8,4)==(1,192,10444,4096) and len(raw)==2005272,'Exact whole original framing')
        changed=set();visited=set();events=0;controls=[]
        for i in range(192):
            result=observe(raw[24+i*10444:24+(i+1)*10444],i,program);changed.add(result[2]);visited|=result[4];events+=len(result[3])
        row=raw[24:24+10444]
        for offset in (0,12,44,48,52,56,60,68,84,88,92,94,96,124,252,604,606,608,636,764,2140,2168,2168+12,2168+18,1628,2224,2252,2252+SP[0],6348+SP[0]-4,6348+SP[0]-8,6348+SP[0]-12,6348+SP[0]):
            b=bytearray(row);b[offset]^=1
            try:observe(b,0,program)
            except (ValueError,struct.error) as e:controls.append({'offset':offset,'rejected':True,'diagnostic':str(e)})
            else:raise ValueError('Root original observer accepted corruption '+str(offset))
        PINS.update(CRT.PINS)
        report={'passed':True,'scope':'Independent actual original connected game control wrapper/source model only; no native/shared-runtime acceptance yet',
            'records':192,'source_provider_instructions_visited':len(visited-{0x5ac5af}),'provider_frame_events':events,'resulting_CW_words':sorted(changed),'observer_controls':controls,
            'requested_flags':list(FLAGS),'actual_input_flags':[x|0x200 for x in FLAGS],'defined_final_ADD_flags_mask':0xcd5,
            'instrumentation':'Original outer5AC436 capture jump maps to10000100; a reviewer-only zero-length provider-continuation jump stops the scalar provider model, never original execution credit.',
            'native_accepted':False,'whole_M4_complete':False}
        p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');bind(p);bind(Path(__file__))
        (out/'pins.json').write_text(json.dumps({'files':dict(sorted(PINS.items()))},indent=2)+'\n')
        print(json.dumps({'passed':True,'records':192,'controls':len(controls),'report_sha256':sha(p),'pins_sha256':sha(out/'pins.json')}))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
