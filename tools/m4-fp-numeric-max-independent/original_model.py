"""Independent input-derived numerical/tag oracle for frozen original captures.

No author comparator, executor, repair helper or expected result is imported.
This original-only record grants no native/shared-runtime admission.
"""
import hashlib
import itertools
import json
import mmap
from pathlib import Path
import struct
import sys
import traceback

ROOT=Path(__file__).resolve().parents[2]
GATE=ROOT/'reports/m4-fp-numeric-max'
WORDS=(0x7F7FFFFF,0,0x80000000,1,0x80000001,0x7FFFFF,0x800000,0x3F800000,0xBF800000,0x3EAAAAAB,0xFF7FFFFF,0x7F800000,0xFF800000,0x7FC12345,0x7F812345,0xFF812345)
CWS=(0x7F,0x47F,0x87F,0xC7F,0x27F,0x67F,0xA7F,0xE7F,0x37F,0x77F,0xB7F,0xF7F)
STRIDE=35764

def need(value,reason):
    if not value:raise ValueError(reason)

def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def ints(b,offset,count):return struct.unpack_from('<'+'I'*count,b,offset)
def word(b,offset=0):return struct.unpack_from('<H',b,offset)[0]
def put(b,offset,value,n=4):b[offset:offset+n]=value.to_bytes(n,'little')

def widen(value):
    """Exact integer binary32→binary80 promotion, with masked sNaN quieting."""
    sign=value>>31;exponent=(value>>23)&255;fraction=value&0x7FFFFF
    exception=0
    if exponent==255:
        exp80=0x7FFF;mantissa=1<<63
        if fraction:
            mantissa|=(fraction<<40)|(1<<62)
            if not fraction&(1<<22):exception=1
        tag=2
    elif exponent:
        exp80=exponent-127+16383;mantissa=((1<<23)|fraction)<<40;tag=0
    elif fraction:
        high=fraction.bit_length()-1;exp80=16383-149+high;mantissa=fraction<<(63-high);tag=0;exception=2
    else:
        exp80=mantissa=0;tag=1
    raw=struct.pack('<QH',mantissa,exp80|(sign<<15))
    output=value|(0x400000 if exponent==255 and fraction else 0)
    return raw,exception,tag,output,exponent!=255

def tags(top,depth):
    occupied=0;full=0xFFFF
    for i in range(depth):
        physical=(top+i)&7;occupied|=1<<physical;full&=~(3<<(2*physical))
    return occupied,full

def expected_tag(case):
    repeat,input_index,depth,sticky,cw,top,entry=case
    return (repeat,input_index,entry,cw,top,depth,sticky,0,1,int(entry==0x4C19F0))

def observe(row,case):
    tag=expected_tag(case);need(len(row)==STRIDE and ints(row,0,10)==tag,'Exact original directed tag/domain/order')
    _,input_index,entry,cw,top,depth,sticky,*_=tag
    before=ints(row,40,10);after=ints(row,80,10)
    need(before==(0x13579BDF,0x2468ACE0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xAABBCCDD,0x202,entry),'Actual original entry CPU')
    need(after==before[:4]+(0x20001804,)+before[5:9]+(0x10000100,),'Actual complete CPU/FLAGS preservation and RET4')
    f0,f1=row[120:632],row[632:1144];e0,e1=row[2168:2196],row[2196:2224]
    memory0,memory1=row[2280:18664],row[18664:35048]
    operand=ints(memory0,4096+4,1)[0]
    need(operand==WORDS[input_index],'Exact declared f32 provider input')
    raw,exception,classification,output,finite=widen(operand)
    old_sticky=(0,2,34)[sticky];occupied,full=tags(top,depth)
    need(word(f0)==cw and word(f0,2)==(top<<11)|old_sticky and f0[4]==occupied and ints(f0,24,1)==(0x1F80,),'Independent incoming CW/SW/TOP/physical occupancy model')
    need(word(e0)==cw and word(e0,4)==(top<<11)|old_sticky and word(e0,8)==full,'Separate incoming full legacy tags')
    for i in range(8):
        expected=struct.pack('<QH',(1<<63)+(i<<56),0x4000|(0x8000 if i&1 else 0))
        need(f0[32+i*16:42+i*16]==expected,'Exact distinct incoming live/dead register fixture')
    leaf=entry==0x780C10F0;newtop=(top-1)&7
    sw=old_sticky|exception|((newtop if leaf else top)<<11)
    expected_fx=bytearray(f0);put(expected_fx,2,sw,2)
    expected_fx[4]=occupied|(1<<newtop) if leaf else occupied
    if leaf:
        bank=[raw]+[f0[32+i*16:42+i*16] for i in range(7)]
    else:
        bank=[f0[32+i*16:42+i*16] for i in range(7)]+[raw]
    for i,value in enumerate(bank):expected_fx[32+i*16:42+i*16]=value
    need(f1==expected_fx,'Independent exact binary80 bank/physical tag/TOP/sticky status model; dead storage observed')
    expected_env=bytearray(e0);put(expected_env,4,sw,2)
    put(expected_env,8,(full&~(3<<(newtop*2)))|(classification<<(newtop*2)) if leaf else full,2)
    put(expected_env,12,0x780C10F0 if leaf else 0x4C1A09)
    put(expected_env,18,0x105 if leaf else 0x11D,2)
    put(expected_env,20,0x78115004 if leaf else 0x60B368)
    need(e1==expected_env,'Independent actual last-FLD/FSTP legacy PC/opcode/data-address model')
    expected_memory=bytearray(memory0)
    if not leaf:
        put(expected_memory,8192+0x368,output)
        expected_memory[8192+0x36C:8192+0x394]=bytes(40)
        for offset,value in ((0x7FC,0x92837465),(0x7F8,0x4C19F8),(0x7F4,0x200017FC),(0x7F0,0x4C1A09)):
            put(expected_memory,12288+offset,value)
    need(memory1==expected_memory,'Independent all four pages and actual wrapper stack/store/ten-zero-dword model')
    need(row[1144:1656]==row[1656:2168] and row[2224:2252]==row[2252:2280],'Full original actual host FX512/ENV28 restoration')
    context=row[35048:]
    if leaf:
        need(context==bytes(716),'No fabricated direct-leaf connected checkpoint')
    else:
        need(ints(context,156,12)==(before[7],before[6],before[3],before[2],before[1],before[0],0x200017F4,0x4C1A0A,0x23,before[8],0x200017F4,0x2B),'Actual stopped x86 CONTEXT CPU at the original INT3 PC')
        need(word(context,28)==cw and word(context,32)==old_sticky|exception|(newtop<<11),'Connected original debugger CW/SW/TOP observation')
        expected_full=(full&~(3<<(newtop*2)))|(classification<<(newtop*2))
        need(word(context,36)==expected_full,'Connected original debugger full physical tags')
        for i,value in enumerate([raw]+[f0[32+j*16:42+j*16] for j in range(7)]):
            need(context[56+i*10:66+i*10]==value and context[204+32+i*16:204+42+i*16]==value,'Connected actual live/dead logical raw80 at provider return')
        need(context[40:56]==bytes(16) and context[210:228]==bytes(18),'Debugger metadata zeros remain distinct/unobserved, not inferred direct FNSTENV')
    return finite,not leaf

def mutation_controls(row,case):
    controls=[]
    for offset in (0,40,80,120,122,124,632,634,636,2168,2196,2204,2208,2214,2216,18664+8192+0x368,18664+8192+0x36C,18664+12288+0x7F0,1656,2252,35048+184,35048+196,35048+32,35048+36,35048+56,35048+204+32):
        changed=bytearray(row);changed[offset]^=1
        try:observe(changed,case)
        except ValueError as e:controls.append({'offset':offset,'rejected':True,'diagnostic':str(e)})
        else:raise ValueError('Input-derived observer accepted corruption '+str(offset))
    return controls

def main(output):
    need(output.is_relative_to(GATE) and not output.exists(),'Fresh private original-only model')
    output.mkdir(parents=True);(output/'model-source.py').write_bytes(Path(__file__).read_bytes())
    try:
        records=finite=checkpoints=0;controls=[];files={};streams=[]
        for mode,inputs in (('default',range(1)),('directed',range(16))):
            path=GATE/'original-r5-normal-windows'/(mode+'.bin');files[str(path)]=sha(path)
            cases=list(itertools.product(range(2),inputs,(0,1,7),range(3),CWS,(0,7),(0x780C10F0,0x4C19F0)))
            with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
                need(raw[:8]==b'MW4NMO01' and ints(raw,8,4)==(1,len(cases),STRIDE,4) and len(raw)==24+len(cases)*STRIDE,'Actual complete original header/extent')
                for i,case in enumerate(cases):
                    row=raw[24+i*STRIDE:24+(i+1)*STRIDE]
                    numerical,connected=observe(row,case);finite+=numerical;checkpoints+=connected;records+=1
                controls+=mutation_controls(raw[24+STRIDE:24+2*STRIDE],cases[1])
            streams.append({'mode':mode,'records':len(cases),'path':str(path),'sha256':files[str(path)]})
        report={'passed':True,'scope':'Independent original-only input-derived binary32/raw80/tag/sticky/stack/CPU/checkpoint model; no native admission','records':records,'finite_exact_value_and_C1_records':finite,'special_records_observed_C1_only':records-finite,'actual_connected_debugger_checkpoints':checkpoints,'streams':streams,'observer_controls':controls,'native_compared':False,'whole_M4_complete':False,'limitations':['Only declared 16 binary32 words, 12 masked CWs, TOP0/7, live depths0/1/7 and sticky0/DE/DE+PE.','Finite promotion and same-value store are exact under all declared PC/RC modes, making their C1 zero; special C1 remains an observation.','C0/C2/C3 and unoccupied raw80 are actual observations with explicit physical write/rotation models, not an expanded architectural preservation claim.','Connected checkpoint is raw Windows x86 CONTEXT at INT3 EIP4C1A0A; zero FP metadata is unobserved and is never substituted for direct FNSTENV.']}
        (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        for path in (Path(__file__),*output.iterdir()):
            if path.is_file():files[str(path)]=sha(path)
        (output/'pins.json').write_text(json.dumps({'files':files},indent=2)+'\n')
        print(json.dumps({'passed':True,'records':records,'finite_C1':finite,'checkpoints':checkpoints,'controls':len(controls),'report_sha256':sha(output/'report.json')}))
    except Exception:
        (output/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
