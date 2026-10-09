"""Root independent control instruction model and actual original carry checks.

Only the separately frozen root-owned control model is imported. Numerical
outputs are hardware observations here; this stage grants no native carry gate.
"""
import hashlib,importlib.util,json,struct,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-control-carry'
PINS={}
ENT=(0x5ac5a0,0x410910,0x410940,0x4133c0,0x43aec0,0x43aee0,0x43af00,
     0x43af20,0x43af40,0x43af60,0x43af80,0x43afa0,0x467490,0x4674b0,
     0x4674d0,0x4adb50,0x4b5af0,0x4b5b20,0x4b7020,0x4c78f0,0x4c7940,
     0x4c79d0,0x4ce5a0,0x4ce5c0,0x4ce5e0,0x4ce600,0x4cfef0)
CWS=(0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f)
CPU=struct.Struct('<10I');STRIDE=92388;FRAME=0x20001800;CAP=0x410a80

def need(ok,why):
    if not ok:raise ValueError(why)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,want=None):
    p=Path(p).resolve();actual=sha(p);need(want is None or actual==want,'Exact immutable identity '+str(p))
    need(str(p) not in PINS or PINS[str(p)]==actual,'Conflicting physical identity')
    PINS[str(p)]=actual;return p
def read(p):return json.loads(pin(p).read_text(encoding='utf-8-sig'))
def u16(b,o):return struct.unpack_from('<H',b,o)[0]

def tags(row,sequence,phase):
    actual=struct.unpack_from('<9I',row)
    need(actual[:3]==(sequence,sequence//12,phase) and actual[4:]==(ENT[phase],CWS[sequence%12],0,0,1),'Exact original phase tags')
    need(actual[3]==0 if phase==0 else actual[3]>=0x5e0000 and actual[3]<0x5e0244,'Declared real table slot / separate outer control boundary')

def control(row,sequence,model,program):
    tags(row,sequence,0)
    before=CPU.unpack_from(row,36)
    need(before[4]==FRAME and before[9]==ENT[0] and before[8]&0x202==0x202,'Real original incoming control frame/PC/CPL3 flags')
    stack=row[2276+10*4096:2276+11*4096]
    f0,f1=row[116:628],row[628:1140];e0,e1=row[2164:2192],row[2192:2220]
    cw=CWS[sequence%12]
    need(u16(f0,0)==cw and u16(f0,2)==0 and f0[4]==0 and struct.unpack_from('<I',f0,24)[0]==0x1f80,'Actual masked empty TOP0 control entry')
    after,memory,changed,events,visited=model.source_model(program,before,stack,cw)
    expected=list(after);expected[9]=CAP
    need(CPU.unpack_from(row,76)==tuple(expected),'Complete original control CPU including ADD-defined AF')
    pages=bytearray(row[2276:47332]);pages[10*4096:11*4096]=memory
    need(row[47332:92388]==pages,'Full original eleven-page control mutation model')
    fx=bytearray(f0);struct.pack_into('<H',fx,0,changed)
    env=bytearray(e0);struct.pack_into('<H',env,0,changed)
    need(f1==fx and e1==env,'Control changes only source-derived normalized CW')
    need(changed==(cw&~0x300)|0x200,'Actual wrapper sets double precision while retaining rounding/masks')
    return changed,len(events),visited

def host(row):
    need(row[1140:1652]==row[1652:2164] and row[2220:2248]==row[2248:2276],'Entire actual original host FX/ENV restoration')

def carry(previous,row,sequence,phase):
    tags(row,sequence,phase)
    c=list(CPU.unpack_from(previous,76));c[4]=FRAME;c[9]=ENT[phase]
    need(CPU.unpack_from(row,36)==tuple(c),'Actual whole CPU carry except declared entry PC/frame reset')
    memory=bytearray(previous[47332:92388]);struct.pack_into('<I',memory,10*4096+0x800,CAP)
    need(row[2276:47332]==memory,'Actual all-eleven-page carry except declared caller return-word setup')
    need(row[116:628]==previous[628:1140] and row[2164:2192]==previous[2192:2220],'Actual complete hardware FX/legacy ENV carry')

def main(out):
    need(out.is_relative_to(BASE) and not out.exists(),'Fresh independent original carry check')
    out.mkdir(parents=True);(out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py')
    try:
        source=ROOT/'tools/m4-crt-control-integration-independent/original_model.py'
        prior=read(ROOT/'reports/m4-crt-control-integration/independent-original-model-r1/pins.json')
        pin(source,prior['files'][str(source)])
        spec=importlib.util.spec_from_file_location('frozen_root_control_source_model',source)
        model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
        program,commands=model.CRT.decode(out)
        p=pin(BASE/'original-run-r1/original.bin','30661de67975c894b4f8d3216a688a46621c63f6734d11b08249562253d5b549')
        changed=set();visited=set();events=0;raw=p.read_bytes()
        need(raw[:8]==b'MW4CCO01' and struct.unpack_from('<6I',raw,8)==(1,24,27,648,11,STRIDE)
             and len(raw)==32+648*STRIDE,'Exact whole original carry framing')
        for seq in range(24):
            previous=None
            for phase in range(27):
                start=32+(seq*27+phase)*STRIDE;row=raw[start:start+STRIDE];host(row)
                if phase==0:
                    cw,n,pc=control(row,seq,model,program);changed.add(cw);events+=n;visited|=pc
                else:carry(previous,row,seq,phase)
                previous=row
        denials=[];first=raw[32:32+STRIDE];nextrow=raw[32+STRIDE:32+2*STRIDE]
        for offset in (0,4,8,16,20,24,28,32,76,108,112,628,630,632,660,2192,
                       47332,47332+10*4096+0x7f4,47332+10*4096+0x800):
            b=bytearray(first);b[offset]^=1
            try:control(b,0,model,program);host(b)
            except (ValueError,struct.error) as e:denials.append({'control_offset':offset,'rejected':True,'reason':str(e)})
            else:raise ValueError('Original control observer accepted corruption '+str(offset))
        for offset in (36,68,72,116,118,120,148,276,2164,2182,2276,2276+10*4096+0x804):
            b=bytearray(nextrow);b[offset]^=1
            try:carry(first,b,0,1);host(b)
            except (ValueError,struct.error) as e:denials.append({'carry_offset':offset,'rejected':True,'reason':str(e)})
            else:raise ValueError('Original carry observer accepted corruption '+str(offset))
        PINS.update(model.PINS);PINS.update(model.CRT.PINS)
        report={'passed':True,'scope':'Independent source model of actual24 control phases and observed624 whole original carry boundaries only',
                'original_phases':648,'original_control_source_models':24,'whole_CPU_FX_ENV_page_carry_boundaries':624,
                'source_modeled_provider_events':events,'provider_instructions_visited':len(visited-{0x5ac5af}),
                'resulting_CW_words':sorted(changed),'causal_corruptions':denials,'commands':commands,
                'capture_projection':'Actual outer RET5AC436 is followed by authored captureJMP410A80; source model only projects final observation PC',
                'numerical_output_scope':'Following numerical outputs remain original hardware observations, no independent numerical oracle claim in this stage',
                'native_carry_accepted':False,'whole_M4_complete':False}
        p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');pin(p);pin(Path(__file__))
        (out/'pins.json').write_text(json.dumps({'files':dict(sorted(PINS.items()))},indent=2)+'\n')
        print(json.dumps({'passed':True,'original_phases':648,'controls':len(denials),'report_sha256':sha(p),'pins_sha256':sha(out/'pins.json')}))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
