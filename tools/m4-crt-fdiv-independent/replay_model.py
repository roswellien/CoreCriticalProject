"""Root-owned BEFORE-only replay model and explicit original observations.

Only frozen root scalar/model and PE code are imported. Original AFTER bytes
are comparison evidence, never model seeds. Full native State/pages are checked;
real x86 Windows service footprints and volatile SIMD remain raw differences.
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
ROOT=Path(__file__).resolve().parents[2]
PINS={}

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def pin(path,expected=None):
    path=Path(path).resolve();digest=sha(path)
    assert expected is None or digest==expected,str(path)
    assert str(path) not in PINS or PINS[str(path)]==digest
    PINS[str(path)]=digest;return path

spec=importlib.util.spec_from_file_location('root_fdiv_replay_scalar',pin(ROOT/'tools/m4-crt-fdiv-independent/native_model.py','8eada91041660b2e3d149cc8df89c01c3a13c5e0d925b21f0bca0af69d2bed6b'))
N=importlib.util.module_from_spec(spec);spec.loader.exec_module(N)
PINS.update(N.PINS)
put=N.put

def originals(raw):
    assert raw[:8]==b'MW4FDOR1' and struct.unpack_from('<6I',raw,8)==(1,48,91348,716,80,1048576)
    result=[];at=32
    for index in range(48):
        size=N.u32(raw,at);row=raw[at+4:at+4+size];tags=struct.unpack_from('<27I',row)
        assert tags[0]==index and tags[2]==int(index>=24) and tags[4]==0
        assert tags[17]==716 and tags[24:27]==(1,1,1)
        stack_at=91348+40*(tags[18]+tags[19]);assert len(row)==stack_at+2*tags[8]
        assert tags[7]<=tags[9]<tags[7]+tags[8] and tags[10:14]==(tags[7],tags[7]+tags[8],tags[7],tags[7]+tags[8])
        result.append((tags,row,row[stack_at:stack_at+tags[8]],row[stack_at+tags[8]:]))
        at+=4+size
    assert raw[at:]==b'COMPLETE'
    return result

def project(original):
    tags,row,stack,_=original;assert not tags[2]
    cpu=list(struct.unpack_from('<10I',row,108));assert cpu[4]==tags[9] and cpu[9]==0x78004254
    cpu[4]=0x20001800
    page=bytearray([0xa5]*4096);mask=bytearray(4096)
    for offset in range(4096):
        source=tags[9]-0x800+offset
        if tags[7]<=source<tags[7]+tags[8]:page[offset]=stack[source-tags[7]];mask[offset]=1
    assert N.u32(page,0x800)==0x10000100;put(page,0x800,0x78004232)
    return struct.pack('<6I',tags[0],tags[1],tags[3],tags[9],tags[7],tags[7]+tags[8])+struct.pack('<10I',*cpu)+row[188:700]+row[2236:2264]+page+mask

def seed(payload):
    index,repeat,cw,*_=struct.unpack_from('<6I',payload)
    cpu=struct.unpack_from('<10I',payload,24);fx=payload[64:576];env=payload[576:604]
    assert len(payload)==8796 and len(fx)==512 and len(env)==28
    assert struct.unpack_from('<HHB',fx)==(cw,0,0) and N.u32(fx,24)==0x1f80
    assert struct.unpack_from('<H',env)[0]==cw and struct.unpack_from('<H',env,4)[0]==0 and struct.unpack_from('<H',env,8)[0]==0xffff
    state=bytearray((i*31+index*17+3)&255 for i in range(3504));state[2112:2208]=bytes(96);put(state,2168,0x7ffde000)
    for offset,value in zip(N.OFFSETS,cpu[:8]):put(state,offset,value)
    put(state,2472,cpu[9]);put(state,2080,cpu[8],8)
    for offset,bit in N.FLAGS:state[offset]=(cpu[8]>>bit)&1
    state[2768:3280]=fx
    for target,source,width in ((2776,12,4),(2780,16,2),(2774,18,2),(2784,20,4),(2788,24,2)):state[target:target+width]=env[source:source+width]
    for offset in (2755,2753,2751,2749,2747,2745,2757,2737,2739,2741,2743):state[offset]=0
    for i in range(8):
        state[16+64*i:32+64*i]=fx[160+16*i:176+16*i]
        state[2616+16*i:2624+16*i]=fx[32+16*i:40+16*i]
    return state,bytearray(fx),cpu,cw,repeat

class ReplayModel(N.Model):
    def __init__(self,program,pages,cpu,cw,feature):
        self.program=program;self.r=dict(zip(N.REGS,cpu[:8]));self.pc=cpu[9];self.flags=cpu[8];self.cw=cw
        self.memory=bytearray(pages);self.feature=feature;self.events=[];self.frames=[];self.visited=set();self.routes=[];self.enter()

def observe(row,payload,program,provider_pages,game_page):
    before,fx,cpu,cw,repeat=seed(payload);index=N.u32(payload)
    assert len(row)==N.STRIDE and struct.unpack_from('<7I',row)==(index,repeat,cw,1,97,3,3)
    assert row[28:3532]==before and row[7036:7548]==fx,'Complete declared BEFORE architecture and opaque storage'
    pages=b''.join(provider_pages)+payload[604:4700]+game_page;assert row[9140:46004]==pages
    feature=N.u32(row,88072+2*6556+12)
    for phase in range(3):
        at=88072+phase*6556;kind,token,arg,result,error=struct.unpack_from('<5I',row,at);host=struct.unpack_from('<Q',row,at+20)[0]
        assert kind==phase+1 and token==(0x11001000,0x11000300,0x11000300)[phase] and arg==0
        assert (result==0 and host) if phase<2 else result==host==feature
        api_before=row[at+28:at+2212];api_after=row[at+2212:at+4396]
        assert api_before==api_after,'Actual API identity stable around query'
        address,named,owner,owner_named=struct.unpack_from('<4Q',api_before)
        assert address==named==owner_named and address and owner
        module=row[at+4396:at+6556];assert struct.unpack_from('<Q',module)[0]
    model=ReplayModel(program,pages,cpu,cw,feature).run();after=bytearray(before)
    for offset,name in zip(N.OFFSETS,N.REGS):put(after,offset,model.r[name])
    put(after,2472,model.pc)
    for offset,bit in N.FLAGS:after[offset]=(model.flags>>bit)&1
    put(after,2768,model.cw,2);put(fx,0,model.cw,2)
    assert row[3532:7036]==after,'Whole3504 State from BEFORE-only source model'
    assert row[7548:8060]==fx and row[46004:82868]==model.memory,'Whole separate FX512 and nine guest pages'
    events=b''.join(struct.pack('<5I',*event) for event in model.events)
    assert row[82868:87988]==events+bytes(5120-len(events))
    assert row[87988:88072]==b''.join(struct.pack('<7I',*route) for route in model.routes)
    assert row[8060:8572]==row[8572:9084] and row[9084:9112]==row[9112:9140],'Internal checkpoint scope only'
    return model

def original_compare(original,row,model):
    tags,source,stack_before,stack_after=original;w=tags[9]
    actual_cpu=struct.unpack_from('<10I',source,148)
    expected_cpu=[model.r[name] for name in N.REGS]+[model.flags,model.pc]
    expected_cpu[4]=w+4;expected_cpu[9]=0x10000100
    assert tuple(expected_cpu)==actual_cpu,'Observed final GPR/flags with declared ESP/outer-return transport'
    # These observed fields match for this empty-register corpus. FNCLEX
    # condition codes and metadata are not generalized beyond these inputs.
    fx_before=source[188:700];fx_after=source[700:1212];native_fx=row[7548:8060]
    ranges=((0,5),(24,28))+tuple((32+16*i,42+16*i) for i in range(8))
    for lo,hi in ranges:assert native_fx[lo:hi]==fx_after[lo:hi]
    legacy=bytearray(source[2236:2264]);put(legacy,0,model.cw,2)
    assert source[2264:2292]==legacy,'Separate direct legacy ENV28 with source CW change'
    source_before=source[2348:31020];source_after=source[31020:59692]
    predicted=bytearray(model.memory[:7*4096])
    for slot,value in ((0x7802e098,tags[20]),(0x7802e0d0,tags[21])):put(predicted,N.PAGES.index(slot&~4095)*4096+(slot&4095),value)
    assert source_after==predicted,'All seven original provider pages with explicit real32bit IAT transport'
    original_window=stack_after[w-0x800-tags[7]:min(w+0x800,tags[7]+tags[8])-tags[7]]
    native_window=model.memory[7*4096:8*4096]
    differences=[i for i,value in enumerate(original_window) if value!=native_window[i]]
    cw_writes=[]
    for kind,pc,address,value,width in model.events:
        if kind==1 and width==2:
            actual=w+address-0x20001800;assert stack_after[actual-tags[7]:actual-tags[7]+2]==value.to_bytes(2,'little')
            cw_writes.append({'source_pc':pc,'guest_address':address,'original_address':actual,'bytes':2,'value':value})
    return {'id':tags[0],'CW_before':tags[3],'CW_after':model.cw,'source_written_BOOL':N.u32(source_after,6*4096+0xc2c),
            'observed_FP_ranges_equal':list(ranges),'original_vs_native_full_FX_differing_offsets':[i for i in range(512) if fx_after[i]!=native_fx[i]],
            'direct_original_before_vs_after_FX_offsets':[i for i in range(512) if fx_before[i]!=fx_after[i]],
            'observed_legacy_ENV28_equal_after_CW_change':True,'source_control_halfword_writes':cw_writes,
            'translated_actual_stack_bytes_compared':len(original_window),'translated_actual_stack_differing_offsets':differences,
            'native_source_stack_sha256':hashlib.sha256(native_window).hexdigest(),'original_actual_stack_sha256':hashlib.sha256(stack_after).hexdigest(),
            'whole_original_stack_equivalence_claimed':False,'volatile_XMM_equivalence_claimed':False,
            'difference_scope':'Raw real x86 API/caller footprint, actual pointers and ABI-volatile residual storage retained; no blanket normalization or expected whole-stack equality.'}

def source_material():
    recovery=json.loads(pin(ROOT/'reports/m4-crt-fdiv/source-recovery-r1/report.json','c124fbfbf5bf64125b9e93c52b9b0e0500f2dd93df6d6ee440b89f5d90f895fd').read_text())
    provider=N.PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
    game=N.PE.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
    def source(pe,address,size):offset,_=pe.rva_range(address-pe.image_base,size);return pe.data[offset:offset+size]
    pages={page:bytearray([0xcc]*4096) for page in N.PAGES[:7]};program={}
    for span in recovery['source_spans']:
        raw=source(provider,span['address'],span['size_bytes']);assert hashlib.sha256(raw).hexdigest()==span['sha256'];offset=span['address']&4095;pages[span['address']&~4095][offset:offset+len(raw)]=raw
    for row in recovery['callback_orchestrator']['instructions']:
        raw=source(provider,row['address'],row['size']);assert raw.hex()==row['bytes_hex'];offset=row['address']&4095;pages[row['address']&~4095][offset:offset+len(raw)]=raw
    for item in recovery['fallback_constants']:
        address=item['address'];raw=source(provider,address,8);assert hashlib.sha256(raw).hexdigest()==item['sha256'];pages[address&~4095][address&4095:(address&4095)+8]=raw
    for page in (0x7802e000,0x78037000):pages[page]=bytearray(source(provider,page,4096))
    for graph in recovery['complete_graphs']:
        for row in graph['instructions']:
            assert source(provider,row['address'],row['size']).hex()==row['bytes_hex']
            text=re.sub(r' <[^>]+>','',row['operands']);value=(row['size'],row['mnemonic'],[x.strip() for x in text.split(',')] if text else [])
            assert row['address'] not in program or program[row['address']]==value;program[row['address']]=value
    assert len(program)==204
    return program,[pages[p] for p in N.PAGES[:7]],source(game,0x5bb000,4096)

def main(out):
    assert out.parent==ROOT/'reports/m4-crt-fdiv-replay' and not out.exists();out.mkdir();(out/'review-source.py').write_bytes(Path(__file__).read_bytes())
    try:
        for path,digest in (
            ('reports/m4-crt-fdiv-reference/run-normal-r1/report.json','4d5b66e3b48a808b722b0b38e921d11a8e716b1fe06f79516364283c5f0261e6'),
            ('reports/m4-crt-fdiv-reference/run-normal-r1/pins.json','ace672f9f4689ea53980e4e9e8ecbb3b39fed3d17d534d7d36d9675e7e51fed5'),
            ('reports/m4-crt-fdiv-replay/preparation-r1/report.json','b4e36d5fd4966b4c4e9ab1a5b0564f699e5c6f851cc2e6bbeb643e99dd85ec3f'),
            ('reports/m4-crt-fdiv-replay/run-normal-r1/report.json','9965638d34f8b04762b037c39ce8f6b64b6604a82e324d60777ced89fec39b07'),
            ('reports/m4-crt-fdiv-replay/run-normal-r1/pins.json','58eb07e634ed2904e6610166b534f7b6f68a2f33f271d5661a042c39f90bdb74')):pin(ROOT/path,digest)
        for path in ('reports/m4-crt-fdiv-reference/run-normal-r1/pins.json','reports/m4-crt-fdiv-replay/run-normal-r1/pins.json'):
            for name,digest in json.loads((ROOT/path).read_text())['files'].items():pin(name,digest)
        prior=ROOT/'reports/m4-crt-fdiv-replay/root-model-r1'
        if out.name!='root-model-r1':
            for path in prior.iterdir():
                if path.is_file():pin(path)
        original=originals(pin(ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin','cbcb423813a712851f63a4921b72544499e74488d24184a4f084a74ae14009b2').read_bytes())
        inputs=pin(ROOT/'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin','4294b8d926966c04d305b6e22a9166f08a328f4cc1c62984b72677fe83dd638a').read_bytes()
        derived=b'MW4FRIN1'+struct.pack('<4I',1,24,8796,4096)+b''.join(project(x) for x in original[:24]);assert inputs==derived,'Every execution input derived independently from literal original BEFORE'
        program,provider_pages,game_page=source_material();coverage=set();comparisons=[];controls=0
        for level in ('O0','O2'):
            raw=pin(ROOT/f'reports/m4-crt-fdiv-replay/run-normal-r1/native-{level}.bin').read_bytes()
            assert raw[:8]==b'MW4FDRN1' and struct.unpack_from('<4I',raw,8)==(1,24,N.STRIDE,9) and len(raw)==24+24*N.STRIDE+8 and raw[-8:]==b'COMPLETE'
            for index in range(24):
                payload=inputs[24+8796*index:24+8796*(index+1)];row=raw[24+N.STRIDE*index:24+N.STRIDE*(index+1)]
                model=observe(row,payload,program,provider_pages,game_page);coverage|=model.visited
                comparisons.append({'level':level,**original_compare(original[index],row,model)})
            payload=inputs[24:24+8796];row=raw[24:24+N.STRIDE]
            for offset in (0,4,8,12,16,20,24,28,40,3532,3548,7036,7548,7550,8060,9084,9140,46004,82868,87988,88072,88100):
                corrupt=bytearray(row);corrupt[offset]^=1;rejected=False
                try:observe(corrupt,payload,program,provider_pages,game_page)
                except AssertionError:rejected=True
                assert rejected,'Own raw observer causal rejection '+str(offset);controls+=1
        assert len(coverage)==174
        (out/'original-observed-differences.json').write_text(json.dumps({'rows':comparisons},indent=2)+'\n')
        result={'passed':True,'scope':'Independent BEFORE-only native replay model and explicitly bounded original observation comparison',
                'independent_before_inputs':24,'native_records':48,'whole_native_State_bytes':3504,'whole_native_FX_bytes':512,'whole_native_pages':9,
                'actual_native_events':48*97,'actual_native_routes':48*3,'source_static_PCs':204,'source_executed_PCs':174,'observer_corruption_rejects':controls,
                'original_observed_final_CPU_with_ESP_outer_PC_transport':True,'original_seven_source_pages_with_two_real_IAT_cells_transport':True,
                'original_observed_CW_SW_FTW_MXCSR_raw80_and_direct_legacy_ENV':True,
                'original_full_FX_or_stack_equivalence':False,'API_volatile_representative_difference_retained':True,
                'author_comparator_fixture_or_projector_imported':False,'original_AFTER_used_as_input':False,
                'native_or_original_executed_by_this_reviewer':False,'full_CRT_or_joint_integration_accepted':False,'whole_M4_complete':False}
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');pin(Path(__file__))
        for path in out.iterdir():
            if path.is_file():pin(path)
        (out/'pins.json').write_text(json.dumps({'files':dict(sorted(PINS.items()))},indent=2)+'\n')
        print(json.dumps({'passed':True,'records':48,'controls':controls,'bindings':len(PINS),'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json')}))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);main(parser.parse_args().output.resolve())
