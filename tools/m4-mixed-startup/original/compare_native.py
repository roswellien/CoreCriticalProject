"""Connected selected26 hardware/native comparison. Failures remain separate.

Original opaque State/events are unobserved. Native State and checked events
need their own source-bound consistency/protection checks in addition to
architectural hardware equality.
"""
from pathlib import Path
import collections,hashlib,json,mmap,re,struct,sys
sys.dont_write_bytecode=True
from observe import fields as common_fields,host_equal,PAGES,CW,INITIAL
ROOT=Path(__file__).resolve().parents[3]
ORIGINAL_SIZE=92388;NATIVE_SIZE=103468
STATE0=92388;STATE1=95892;COUNTS=99396;EVENTS=99436;ROUTES=103276
FP_ROOTS={0x4133c0,0x4adb50,0x4b5af0,0x4b7020,0x4c78f0,0x4c79d0,0x4ce5a0,0x4ce5c0,0x4ce5e0,0x4ce600}
GPR=(2216,2248,2264,2232,2312,2328,2280,2296,2472)
AF=((2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11))
SW=((2755,0),(2753,1),(2751,2),(2749,3),(2747,4),(2745,5),(2757,6),(2737,8),(2739,9),(2741,10),(2743,14))
TAILS=dict.fromkeys((0x43aec0,0x43aee0,0x43af00,0x43af20,0x43af40,0x43af60,0x43af80,0x43afa0))
def configure(extraction):
    lookup={r['pc']:r for r in extraction['instructions']};graphs={g['entry']:g for g in extraction['graphs']}
    for entry in TAILS:
        rows=[lookup[pc] for pc in graphs[entry]['instruction_pcs']]
        matches=[re.fullmatch(r'ecx, (0x[0-9a-f]+)',r['operands']) for r in rows if r['mnemonic']=='mov']
        immediates=[int(m[1],16) for m in matches if m];assert len(immediates)==1
        TAILS[entry]=immediates[0];assert TAILS[entry]&~4095==0x605000
FP_SCHEDULE={
 0x4133c0:[(0x5e1f58,4,0),(0x5e1f58,4,0),(0x604e40,4,1)],
 0x4adb50:[(0x5c8a88,8,0),(0x5c8a90,8,0),(0x5c8a98,8,0),(0x60b150,4,1),(0x60b154,4,1),(0x60b158,4,1)],
 0x4b5af0:[(0x5c936c,4,0),(0x5c936c,4,0),(0x60b2b4,4,1)],
 0x4c79d0:[(0x60b44c,4,0),(0x60b46c,4,1)],
 0x4b7020:[(0x5c9398,8,0),(0x5c93a0,8,0),(0x60b2b0,4,1),(0x5c9398,8,0),(0x5c93a0,8,0),(0x60b2ec,4,1)],
 0x4c78f0:[(0x5e8b90,4,0),(0x5cb0b0,8,0),(0x5cb0bc,4,0),(0x60b480,4,1),(0x60b478,4,1),(0x60b47c,4,1),(0x60b484,4,1)],
 0x4ce5a0:[(0x5cc530,8,0),(0x60b4a0,4,1)],0x4ce5c0:[(0x5cc538,8,0),(0x60b4a4,4,1)],
 0x4ce5e0:[(0x5cc540,8,0),(0x60b49c,4,1)],0x4ce600:[(0x5cc548,8,0),(0x60b494,4,1)]}
FP_COUNTS={0x4133c0:(2,0),0x4adb50:(6,1),0x4b5af0:(2,0),0x4c79d0:(1,0),0x4b7020:(5,2),0x4c78f0:(6,2),0x4ce5a0:(2,1),0x4ce5c0:(2,1),0x4ce5e0:(2,1),0x4ce600:(2,1)}
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def half(b,o):return struct.unpack_from('<H',b,o)[0]
def word(b,o):return struct.unpack_from('<I',b,o)[0]
def native_fields(b):
    r=common_fields(b[:ORIGINAL_SIZE]);r['state0']=b[STATE0:STATE1];r['state1']=b[STATE1:COUNTS]
    r['counts']=struct.unpack_from('<10I',b,COUNTS)
    r['events']=[struct.unpack_from('<IQII',b,EVENTS+i*20) for i in range(192)]
    r['routes']=[b[ROUTES+i*96:ROUTES+(i+1)*96] for i in range(2)]
    return r
def overlay(s,cpu,flat=True):
    s=bytearray(s)
    for off,value in zip(GPR,cpu[:8]+cpu[9:]):struct.pack_into('<I',s,off,value)
    for off,bit in AF:s[off]=(cpu[8]>>bit)&1
    if flat:struct.pack_into('<Q',s,2080,cpu[8])
    return s
def initial_state(n):
    sequence,repeat,phase,slot,entry,cw,top,*_=n['tag'];pattern=repeat*3571+cw
    s=bytearray((i*29+pattern+(i>>8)*7)&255 for i in range(3504));s[2112:2208]=bytes(96);s[2768:3280]=bytes(512)
    struct.pack_into('<I',s,2168,0x7ffde000)
    for off,value in ((2090,0x2b),(2106,0x2b),(2110,0x23)):struct.pack_into('<H',s,off,value)
    struct.pack_into('<H',s,2768,cw);struct.pack_into('<H',s,2770,top<<11);struct.pack_into('<I',s,2792,0x1f80)
    for off,bit in SW:s[off]=0
    for i in range(8):s[2486+i*16:2496+i*16]=bytes(10);s[16+i*64:32+i*64]=bytes(16)
    return bytes(overlay(s,n['before']))
def project(s):
    fx=bytearray(s[2768:3280]);status=half(s,2770)&0xb880
    for off,bit in SW:
        if s[off] not in (0,1):raise ValueError('Nonboolean native State status')
        status|=s[off]<<bit
    struct.pack_into('<H',fx,2,status)
    for i in range(8):fx[32+i*16:42+i*16]=s[2486+i*16:2496+i*16];fx[160+i*16:176+i*16]=s[16+i*64:32+i*64]
    env=struct.pack('<7I',0xffff0000|half(s,2768),0xffff0000|status,0xffffffff,word(s,2776),half(s,2780)|(half(s,2774)<<16),word(s,2784),0xffff0000|half(s,2788))
    return bytes(fx),env
def expected_state_after(o,n):
    entry=n['tag'][4];s=overlay(n['state0'],n['after'],flat=False)
    if entry in FP_ROOTS:
        # Actual hardware supplies the concrete FP results and metadata. Empty
        # raw payload equality is observation only; every other opaque byte must
        # persist. Backing SW only has its TOP updated by lifted instructions.
        sw=half(o['fx1'],2);struct.pack_into('<H',s,2770,(half(n['state0'],2770)&~0x3800)|(sw&0x3800))
        for off,bit in SW:s[off]=(sw>>bit)&1
        env=o['env1'];struct.pack_into('<H',s,2774,half(env,18)&0x7ff);struct.pack_into('<I',s,2776,word(env,12))
        struct.pack_into('<H',s,2780,half(env,16));struct.pack_into('<I',s,2784,word(env,20));struct.pack_into('<H',s,2788,half(env,24))
        for i in range(8):s[2486+i*16:2496+i*16]=o['fx1'][32+i*16:42+i*16]
    return bytes(s)
def boundary_state(previous,n):
    s=overlay(previous['state1'],n['before']);entry=n['tag'][4]
    if entry not in FP_ROOTS:
        # Exact reviewed integer adapter imports the runtime FX projection but
        # preserves the separate eighteen legacy metadata bytes. Its aggregate
        # SW synchronization is a defined adapter write between guest bodies.
        fx,_=project(previous['state1']);s[2768:3280]=fx
    return bytes(s)
def read_mem(memory,address,width):
    page=address&~4095
    if page not in PAGES or (address+width-1)&~4095!=page:raise ValueError('Event outside observed owned pages')
    offset=PAGES.index(page)*4096+(address&4095)
    return int.from_bytes(memory[offset:offset+width],'little')
def schedule(o,static_events):
    entry=o['tag'][4];ret=(0x20001800,4,0,None)
    if entry==0x410910:return [(0x604130+i*20,1,1,0) for i in range(167)]+[ret]
    if entry==0x410940:
        events=[]
        for event in static_events:
            a=event['address'];address=a.get('guest_va',0x20001800+a.get('entry_esp_offset',0));value=event['value']
            if isinstance(value,dict):value=o['before'][3] if 'incoming_register' in value else 0x410a80
            events.append((address,event['width_bytes'],int(event['operation']=='write'),value))
        return events
    if entry in TAILS:return [(TAILS[entry]+i*4,4,1,0) for i in range(7)]+[ret]
    if entry in (0x467490,0x4674b0,0x4674d0):return [ret]
    if entry==0x4b5b20:return [(0x60b2b8,4,1,0x60b2f4),(0x60b2bc,4,1,0),(0x60b2c0,1,1,0),(0x60b2c1,1,1,0),ret]
    if entry==0x4c7940:return [(0x60b44c,4,1,0xfffff),ret]
    if entry==0x4cfef0:return [(0x60b4a8,4,1,0),(0x60b4ac,4,1,0),ret]
    return [(a,w,op,read_mem(o['memory1'],a,w) if op else None) for a,w,op in FP_SCHEDULE[entry]]+[ret]
def check_events(o,n,static_events):
    expected=schedule(o,static_events);actual=n['events'];errors=[];memory=bytearray(o['memory0']);expected_values=[]
    for address,width,operation,constant in expected:
        value=constant if operation else read_mem(memory,address,width)
        expected_values.append((address,value,width,operation))
        if operation:
            offset=PAGES.index(address&~4095)*4096+(address&4095);memory[offset:offset+width]=value.to_bytes(width,'little')
    if actual[:len(expected)]!=expected_values:errors.append('exact_ordered_events')
    if any(any(x) for x in actual[len(expected):]):errors.append('inactive_event_storage')
    if bytes(memory)!=o['memory1']:errors.append('event_replay_whole_pages')
    entry=o['tag'][4];reads=sum(not e[2] for e in expected);writes=len(expected)-reads;tests,primitives=FP_COUNTS.get(entry,(0,0));routes=2 if entry==0x410940 else 1 if entry in TAILS else 0;returns=3 if entry==0x410940 else 1
    if n['counts']!=(len(expected),reads,writes,tests,tests,returns,primitives,routes,1,0):errors.append('typed_bridge_counts')
    return errors
def check_routes(o,n):
    entry=o['tag'][4];routes=[];incoming=o['before']
    if entry in TAILS:
        c=list(incoming);c[1]=TAILS[entry];c[9]=0x43ae30
        routes=[(0x43ae30,0x410a80,0,1,tuple(c),n['after'])]
    elif entry==0x410940:
        before=list(incoming);before[:5]=[0x604118,0x6040f0,0x3f800000,0,0x20001800-20];before[8]=(incoming[8]&~0xcd5)|0x44;before[9]=0x40daf0
        after=before.copy();after[0]=0;after[4]=0x20001800-4;after[9]=0x4109d7
        before2=after.copy();before2[1]=0x6040d0;before2[4]=0x20001800-28;before2[9]=0x40db30
        after2=before2.copy();after2[0]=0x604100;after2[2]=0;after2[4]=0x20001800-4;after2[8]=(incoming[8]&~0xcd5)|4;after2[9]=0x4109fc
        routes=[(0x40daf0,0x4109d7,12,1,tuple(before),tuple(after)),(0x40db30,0x4109fc,20,1,tuple(before2),tuple(after2))]
    expected=[struct.pack('<4I',*r[:4])+struct.pack('<10I',*r[4])+struct.pack('<10I',*r[5]) for r in routes]+[bytes(96)]*(2-len(routes))
    return [] if n['routes']==expected else ['exact_compiled_call_RET_routes']
def native_checks(o,n,previous,extraction,static_events):
    errors=[];phase=n['tag'][2]
    expected=boundary_state(previous,n) if phase else initial_state(n)
    if n['state0']!=expected:errors.append('full_State_entry_carry_or_seed')
    if n['state1']!=expected_state_after(o,n):errors.append('full_State_actual_defined_writes_and_protection')
    for ph in ('0','1'):
        fx,env=project(n['state'+ph])
        if (fx,env)!=(n['fx'+ph],n['env'+ph]):errors.append('State_FX_ENV_projection'+ph)
        s=n['state'+ph];cpu=tuple(word(s,off) for off in GPR[:8]);flags=0x202
        for off,bit in AF:
            if s[off] not in (0,1):errors.append('State_nonboolean_arithmetic_flags')
            flags|=s[off]<<bit
        if cpu+(flags,word(s,GPR[8]))!=n['before' if ph=='0' else 'after']:errors.append('State_CPU_projection'+ph)
    if phase:
        wanted=list(previous['after']);wanted[4]=0x20001800;wanted[9]=n['tag'][4]
        if n['before']!=tuple(wanted):errors.append('native_CPU_carry')
        if n['memory0']!=previous['memory1']:errors.append('native_whole_page_carry')
        if n['fx0']!=previous['fx1']:errors.append('native_software_FP_carry')
        if n['env0']!=previous['env1']:errors.append('native_legacy_ENV_carry')
    else:
        if n['before']!=INITIAL+(n['tag'][4],):errors.append('native_initial_CPU')
    if n['tag'][4]==0x4c79d0:
        # This is the real connected integer→FP dependency, not a standalone
        # FILD fixture. The previous actual writer must feed its exact DWORD.
        if previous['tag'][4]!=0x4c7940 or read_mem(previous['memory1'],0x60b44c,4)!=0xfffff or n['events'][0]!=(0x60b44c,0xfffff,4,0):errors.append('integer_to_FILD_dependency')
    errors+=check_events(o,n,static_events)+check_routes(o,n)
    return errors
def architectural_pair(o,n,phase):
    errors=[]
    def eq(field,a,b):
        if a!=b:errors.append(field)
    eq('tag',o['tag'],n['tag'])
    # AF becomes undefined at the first XOR tail and stays unconsumed. Raw flags
    # remain captured; the original defined-before and defined-after mask differ
    # precisely at that first XOR boundary.
    before_mask=0xcd5 if phase<=3 else 0xcc5;after_mask=0xcd5 if phase<3 else 0xcc5
    for label,mask in [('before',before_mask),('after',after_mask)]:
        eq('CPU_'+label,o[label][:8]+o[label][9:],n[label][:8]+n[label][9:])
        eq('defined_CPU_flags_'+label,o[label][8]&mask,n[label][8]&mask)
    for label in ('memory0','memory1'):eq(label,o[label],n[label])
    for ph in ('0','1'):
        a,b=o['fx'+ph],n['fx'+ph]
        eq('CW'+ph,a[:2],b[:2]);eq('FSW_core'+ph,half(a,2)&0xb8ff,half(b,2)&0xb8ff)
        # C1 and all empty physical payload bytes remain measured explicitly;
        # this default-sequence gate does not globally drop their differences.
        eq('observed_C1'+ph,half(a,2)&0x200,half(b,2)&0x200)
        eq('observed_C0_C2_C3'+ph,half(a,2)&0x4500,half(b,2)&0x4500)
        eq('FTW'+ph,a[4],b[4]);eq('MXCSR'+ph,a[24:28],b[24:28]);eq('XMM0_7'+ph,a[160:288],b[160:288])
        for i in range(8):eq('observed_dead_raw80_'+ph+'_'+str(i),a[32+i*16:42+i*16],b[32+i*16:42+i*16])
        eq('hardware_FX_zero_metadata'+ph,a[6:24],bytes(18))
        eq('legacy_ENV'+ph,o['env'+ph],n['env'+ph])
    eq('original_host_restore',host_equal(o['host0'],o['host1'],o['hostenv0'],o['hostenv1']),True)
    eq('native_host_restore',host_equal(n['host0'],n['host1'],n['hostenv0'],n['hostenv1']) and n['host0'][160:416]==n['host1'][160:416],True)
    return errors
def main():
    original,build_path,out=map(lambda p:Path(p).resolve(),sys.argv[1:4])
    assert out.parent==ROOT/'reports/m4-mixed-startup' and out.name.startswith('original-') and not out.exists();out.mkdir()
    build=json.loads(build_path.read_text(encoding='utf-8-sig'));assert build['passed']
    extraction_path=original.parent.parent/'original-extract-original-build-r2/extraction.json'
    extraction=json.loads(extraction_path.read_text());configure(extraction)
    static_path=ROOT/'reports/m4-startup/next-initializer-410940-events/report.json'
    assert sha(static_path)=='cabc667bc4bad34e57a47093fc82aeba981d354dad6390eeb1a082c4a153c82b'
    static_events=json.loads(static_path.read_text())['memory_events']
    for p,h in build['artifacts'].items():assert sha(p)==h,'Native physical artifact changed: '+p
    results={}
    with original.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
        assert raw[:8]==b'MW4MXO01' and struct.unpack_from('<6I',raw,8)==(1,48,26,1248,11,ORIGINAL_SIZE) and len(raw)==32+1248*ORIGINAL_SIZE
        for level in ('O0','O2'):
            path=build_path.parent/('native-'+level+'.bin');totals=collections.Counter();samples=[];bad=0;roots={};previous=None;event_total=route_total=0
            with path.open('rb') as nf,mmap.mmap(nf.fileno(),0,access=mmap.ACCESS_READ) as nr:
                assert nr[:8]==b'MW4MXN01' and struct.unpack_from('<6I',nr,8)==(1,48,26,1248,11,NATIVE_SIZE) and len(nr)==32+1248*NATIVE_SIZE
                for i in range(1248):
                    o=common_fields(raw[32+i*ORIGINAL_SIZE:32+(i+1)*ORIGINAL_SIZE]);n=native_fields(nr[32+i*NATIVE_SIZE:32+(i+1)*NATIVE_SIZE]);phase=i%26
                    errors=architectural_pair(o,n,phase)
                    try:errors+=native_checks(o,n,previous,extraction,static_events)
                    except Exception as e:errors.append('native_observer_exception: '+str(e))
                    previous=n;event_total+=n['counts'][0];route_total+=n['counts'][7]
                    pc=hex(o['tag'][4]);roots.setdefault(pc,{'records':0,'mismatch_records':0});roots[pc]['records']+=1
                    if errors:
                        bad+=1;roots[pc]['mismatch_records']+=1;totals.update(errors)
                        if len(samples)<40:samples.append({'index':i,'tag_original':o['tag'],'tag_native':n['tag'],'fields':errors,'original_sw':[half(o['fx0'],2),half(o['fx1'],2)],'native_sw':[half(n['fx0'],2),half(n['fx1'],2)]})
            results[level]={'records':1248,'mismatch_records':bad,'field_totals':dict(totals),'roots':roots,'samples':samples,'actual_checked_events':event_total,'actual_compiled_routes':route_total,
                            'whole_State_pairs':1248,'persistent_CPU_State_FP_ENV_page_boundaries':1200,'integer_to_FILD_dependencies':48}
    result={'passed':all(v['mismatch_records']==0 for v in results.values()),'scope':'Connected exact selected26 default-input native/hardware gate; full table/CRT/startup/menu remain open','comparisons':results,
            'architecture_flags':'CD5 before first XOR and CC5 thereafter; AF undefined and never consumed after XOR',
            'FP_status':'Core exceptions/SF/ES/TOP/B checked architecturally; all C1/C0/C2/C3 and dead raw80 payload differences checked separately as concrete observations, no general undefined-bit admission',
            'original_State_events':'Unobserved; native whole State protection/projection/carry and ordered checked access/call routes independently validated',
            'bindings':{str(p):sha(p) for p in (original,build_path,Path(__file__),Path(__file__).with_name('observe.py'),extraction_path,static_path,build_path.parent/'native-O0.bin',build_path.parent/'native-O2.bin')}}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'comparisons':{k:{'mismatch_records':v['mismatch_records'],'fields':v['field_totals']} for k,v in results.items()}}))
if __name__=='__main__':main()
