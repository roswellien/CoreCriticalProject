"""Independent raw observations; never used by any original/native worker."""
import argparse,hashlib,json,struct,subprocess,sys
from collections import Counter
from pathlib import Path
from corpus import *
from bindings import FUNCTIONS,LINKED_IR_SHA
ROOT=Path(__file__).resolve().parents[2]
CPU=struct.Struct("<10I")
FLAG_FIELDS=((0,1),(2,3),(4,5),(6,7),(7,9),(10,11),(11,13))
SW_FIELDS=((8,1),(9,3),(10,5),(14,7),(5,9),(4,11),(3,13),(2,15),(1,17),(0,19),(6,21))
def require(ok: bool, field: str) -> None:
    if not ok:
        raise ValueError(field)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def put_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from('<H', data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from('<I', data, offset)[0]


def check_cpu(actual: tuple[int, ...], goal: tuple[int, ...], mask: int, phase: str) -> None:
    for i, name in enumerate(('eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi')):
        require(actual[i] == goal[i], phase + '.' + name)
    require((actual[8] ^ goal[8]) & mask == 0, phase + '.defined_flags')
    require(actual[9] == goal[9], phase + '.eip')


def fp_fields(fx: bytes) -> tuple:
    """Architecturally defined legacy fields; occupied values use TOP/FTW.

    The omitted bytes are capability, selectors/reserved bytes and padding.
    Empty raw80 storage is separately preserved within each worker.
    """
    cw, sw, ftw, fop = u16(fx, 0), u16(fx, 2), fx[4], u16(fx, 6)
    top = sw >> 11 & 7
    slots = tuple(fx[32 + i * 16:42 + i * 16] if ftw & (1 << ((top + i) & 7)) else None
                  for i in range(8))
    return (cw, sw, ftw, fop, u32(fx, 8), u32(fx, 16), u32(fx, 24),
            slots, fx[160:288])


def check_fx(actual: bytes, goal: bytes, phase: str, *, metadata: bool = True) -> None:
    names = ('cw', 'sw', 'physical_ftw', 'fop', 'fip', 'fdp', 'mxcsr', 'occupied_raw80', 'xmm0_7')
    for name, a, b in zip(names, fp_fields(actual), fp_fields(goal)):
        if not metadata and name in ('fop', 'fip', 'fdp'):
            continue
        require(a == b, phase + '.' + name)


def check_env(env: bytes, fx: bytes, phase: str, *, metadata: bytes | None = None) -> None:
    require(u16(env, 0) == u16(fx, 0), phase + '.cw')
    require(u16(env, 4) == u16(fx, 2), phase + '.sw')
    require(u16(env, 8) == full_tags(fx), phase + '.full_physical_tags')
    metadata = fx if metadata is None else metadata
    require(u32(env, 12) == u32(metadata, 8), phase + '.fip')
    require(u16(env, 18) & 0x7ff == u16(metadata, 6), phase + '.fop')
    require(u32(env, 20) == u32(metadata, 16), phase + '.fdp')


def state_cpu(state: bytes, layout: dict) -> tuple[int, ...]:
    structures = layout['struct_layouts']
    x = structures['struct.X86State']['offsets']
    g = structures['struct.GPR']['offsets']
    a = structures['struct.ArithFlags']['offsets']
    registers = tuple(u32(state, x[6] + g[i]) for i in (1, 5, 7, 3, 13, 15, 9, 11))
    flags = 0
    for bit, index in FLAG_FIELDS:
        value = state[x[2] + a[index]]
        require(value in (0, 1), 'state.arithmetic_flag_encoding')
        flags |= value << bit
    return (*registers, flags, u32(state, x[6] + g[33]))


def state_fx(state: bytes, layout: dict) -> bytes:
    """An independent projection from the recorded State, not the request."""
    structures = layout['struct_layouts']
    x = structures['struct.X86State']['offsets']
    s = structures['struct.FPUStatusFlags']['offsets']
    raw = structures['struct.anon.3']['offsets'][1]
    slot_size = structures['struct.anon.3']['size']
    vector_size = structures['union.VectorReg']['size']
    fx = bytearray(state[x[11]:x[11] + 512])
    sw = u16(fx, 2) & 0x3880
    for bit, index in SW_FIELDS:
        value = state[x[9] + s[index]]
        require(value in (0, 1), 'state.status_flag_encoding')
        sw |= value << bit
    struct.pack_into('<H', fx, 2, sw)
    for i in range(8):
        start = x[7] + i * slot_size + raw
        fx[32 + i * 16:42 + i * 16] = state[start:start + 10]
        start = x[1] + i * vector_size
        fx[160 + i * 16:176 + i * 16] = state[start:start + 16]
    return bytes(fx)

def protected_ranges(layout,root):
    writes=list(layout['functions']['sub_'+format(ENTRIES[root],'x')]['writes'])
    if root<8:writes+=layout['functions']['sub_43ae30']['writes']
    allowed={i for w in writes for i in range(w['offset'],w['offset']+w['width'])}
    ranges=[];start=None
    for i in range(3505):
        protected=i<3504 and i not in allowed
        if protected and start is None:start=i
        if not protected and start is not None:ranges.append((start,i));start=None
    return ranges

def validate(row,q,goal,mode,layout,reference=None,previous=None):
    require(len(row)==RESULT_SIZE,'record.size');before=CPU.unpack_from(row,0);after=CPU.unpack_from(row,40)
    before_mask=0xcc5 if q.arg_b and q.arg_a else 0xcd5
    check_cpu(before,goal['before'],before_mask,'cpu.before');check_cpu(after,goal['after'],goal['mask'],'cpu.after')
    require(struct.unpack_from('<3I',row,80)==(0,mode,1),'status/provenance/host')
    require(row[92:12380]==goal['memory_before'] and row[12380:24668]==goal['memory_after'],'actual.entire_three_pages')
    fb,fa=row[24668:25180],row[25180:25692];check_fx(fb,q.fx,'FX.before');check_fx(fa,fb,'FX.preservation')
    for i in range(8):require(fb[32+i*16:42+i*16]==fa[32+i*16:42+i*16],'FX.actual_all_raw80_storage')
    eb,ea=row[25692:25720],row[25720:25748];check_env(eb,fb,'ENV.before');check_env(ea,fa,'ENV.after');require(eb==ea,'actual.ENV_preservation')
    sb,sa=row[25748:29252],row[29252:32756];count=u32(row,32756);events=tuple(struct.unpack_from('<4I',row,32760+i*16) for i in range(8));route_count=u32(row,32888)
    if mode:
        require(count==len(goal['events']) and events[:count]==goal['events'] and events[count:]==((0,0,0,0),)*(8-count),'actual.ordered_events')
        check_cpu(state_cpu(sb,layout),before,before_mask,'State.before_cpu');check_cpu(state_cpu(sa,layout),after,goal['mask'],'State.after_cpu')
        check_fx(state_fx(sb,layout),fb,'State.before_FP');check_fx(state_fx(sa,layout),fa,'State.after_FP')
        for lo,hi in protected_ranges(layout,q.arg_a):require(sb[lo:hi]==sa[lo:hi],f'protected.State_{lo}_{hi}')
        require(route_count==len(goal['routes']),'actual.tail_count')
        for incoming,outgoing,entry,ret,pop,complete in goal['routes']:
            check_cpu(CPU.unpack_from(row,32892),incoming,before_mask,'tail.before');check_cpu(CPU.unpack_from(row,32932),outgoing,goal['mask'],'tail.after')
            require(struct.unpack_from('<4I',row,32972)==(entry,ret,pop,complete),'actual.tail_route')
        if not route_count:require(row[32892:]==bytes(96),'unused.tail_zero')
        if reference:
            check_cpu(after,CPU.unpack_from(reference,40),goal['mask'],'original_native_cpu')
            require(row[92:24668]==reference[92:24668],'original_native_all_pages')
            check_fx(fb,reference[24668:25180],'original_native_FPbefore');check_fx(fa,reference[25180:25692],'original_native_FPafter')
            require(row[25692:25748]==reference[25692:25748],'original_native_ENV')
    else:require(sb==bytes(3504) and sa==bytes(3504) and count==0 and row[32760:]==bytes(228),'original.State_events_tail_unobserved_zero')
    if previous is not None:
        require(previous[12380:24668]==row[92:12380],'persistent.all_pages')
        require(previous[25180:25692]==fb and previous[25720:25748]==eb,'persistent.full_FP_ENV')
        if mode:
            wanted=bytearray(previous[29252:32756]);struct.pack_into('<I',wanted,2312,q.cpu[4]);struct.pack_into('<I',wanted,2472,q.cpu[9])
            require(bytes(wanted)==sb,'persistent.full_State_only_SP_PC_rearmed')

def compare_files(paths,rows,layout):
    from contextlib import ExitStack
    with ExitStack() as stack:
        streams={name:stack.enter_context(path.open('rb')) for name,path in paths.items()}
        for name,s in streams.items():require(HEADER.unpack(s.read(24))==(b'MW34I4RS',1,len(rows),RESULT_SIZE,32 if name=='original' else 64),'stream.header')
        previous={};goal=None;sample=None
        for i,q in enumerate(rows):
            continued=q.arg_b and q.arg_a
            goal=expected(q,goal['after'] if continued else None,goal['memory_after'] if continued else None)
            actual={name:s.read(RESULT_SIZE) for name,s in streams.items()}
            for name,row in actual.items():
                try:validate(row,q,goal,0 if name=='original' else 1,layout,actual['original'] if name!='original' else None,previous.get(name) if continued else None)
                except ValueError as e:raise ValueError(f'{name} row{i} root{q.arg_a} {q.category}: {e}') from e
            if sample is None:sample=(actual,goal)
            previous=actual
        require(all(not s.read(1) for s in streams.values()),'stream.trailing')
    return sample

def observer_controls(sample,q,layout):
    actual,goal=sample;controls=[]
    for mode in (0,1):
        offsets=[i*4 for i in range(10)]+[40+i*4 for i in range(10) if i!=8]+[72,80,84,88,92,12380,24668,25180,25692,25720]
        if mode:offsets+=[25748+2216,29252+2065,29252+3000,32756,32760,32764,32768,32772,32888,32892+36,32932+36,32972+8]
        else:offsets+=[25748,29252,32756,32888]
        for offset in offsets:
            changed=bytearray(actual['native-O0' if mode else 'original']);changed[offset]^=1
            try:validate(bytes(changed),q,goal,mode,layout,actual['original'] if mode else None)
            except ValueError as e:controls.append({'mode':mode,'offset':offset,'rejected':True,'reason':str(e)});continue
            raise ValueError(f'Observer accepted corruption {mode}/{offset}')
    return controls

def worker(exe,request,out,code,image):return subprocess.run([str(exe),str(request),str(out),str(code),str(image)],capture_output=True,timeout=180)

def admission_controls(workers,code,image,out,rows):
    folder=out/'admission';folder.mkdir();base=request_bytes(rows[:2]);mutations={};paths={};controls=[]
    def change(name,offset,value,width=1):
        raw=bytearray(base);raw[offset:offset+width]=value.to_bytes(width,'little');mutations[name]=bytes(raw)
    change('magic',0,0);change('version',8,2,4);change('width',20,64,4);change('PC',24+36,ENTRY+1,4)
    change('root-index',24+40,14,4);change('sequence-mode',24+44,2,4);change('incomplete-sequence',24+44,1,4)
    change('late-root-index',24+568+40,14,4);change('stack-below',24+16,STACK-1,4);change('stack-over',24+16,STACK+4093,4)
    change('unmasked-CW',24+56,0x7e,2);change('reserved-FX',24+61,1);change('FOP',24+62,1,2);change('FIP',24+64,1,4);change('FDP',24+72,1,4)
    mutations['truncated']=base[:-1];mutations['trailing']=base+b'x'
    for name,raw in mutations.items():p=folder/(name+'.rq');p.write_bytes(raw);paths[name]=(p,code,image)
    valid=folder/'valid.rq';valid.write_bytes(base)
    for entry,known in FUNCTIONS.items():
        p=folder/f'changed-code-{entry:x}.bin';raw=bytearray(code.read_bytes());raw[known['bundle']]^=1;p.write_bytes(raw);paths[f'changed-code-{entry:x}']=(valid,p,image)
    p=folder/'changed-image.bin';raw=bytearray(image.read_bytes());raw[0]^=1;p.write_bytes(raw);paths['changed-image']=(valid,code,p)
    for name,exe in workers.items():
        for label,(request,bundle,owner) in paths.items():
            output=folder/(name+'-'+label+'.rs');run=worker(exe,request,output,bundle,owner);log=folder/(name+'-'+label+'.log');log.write_bytes(run.stdout+run.stderr)
            require(run.returncode!=0 and not output.exists() and b'reservation failed' not in run.stderr.lower(),'Causal denial missed '+name+'/'+label)
            controls.append({'worker':name,'name':label,'exit_code':run.returncode,'output_created':False,'log_path':str(log),'log_sha256':sha(log),'diagnostic':run.stderr.decode(errors='replace')})
    return controls

def load_build(path):
    build=json.loads(path.read_text(encoding='utf-8-sig'));require(build['profile']=='m4-integer-startup-fourteen-roots','build.profile')
    for field in ('source_files','tool_files','previous_gate_pins'):
        for name,d in build[field].items():require(sha(Path(name))==d,'build.changed '+name)
    for name,d in build['artifacts'].items():require(sha(Path(name) if Path(name).is_absolute() else path.parent/name)==d,'build.artifact '+name)
    layout=json.loads(Path(build['layout_path']).read_text());require(layout['guest_ir_sha256']==LINKED_IR_SHA and layout['semantic_repairs']==[] and layout['all_struct_layouts_equal'] is True,'layout.admission')
    require(set(layout['functions'])=={'sub_'+format(e,'x') for e in FUNCTIONS} and len(layout['closed_actual_tail_targets'])==8,'layout.closure')
    for e,k in FUNCTIONS.items():require(layout['functions']['sub_'+format(e,'x')]['call_counts']==k['calls'],'layout.calls')
    code,image=Path(build['code_path']),Path(build['image_path']);require(sha(code)==CODE_SHA and sha(image)==IMAGE_SHA,'build.inputs')
    return build,layout,{k:Path(v) for k,v in build['workers'].items()},code,image

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    require(not a.out.exists() and a.out.resolve().is_relative_to((ROOT/'reports/m4-integer-startup').resolve()),'Fresh private comparison required');a.out.mkdir(parents=True)
    report={'schema_version':1,'passed':False,'scope':'Remaining14 import-free integer initializer roots and complete shared tail; persistent ordered14-root batch; full M4 open'}
    try:
        b,layout,workers,code,image=load_build(a.build);rows=cases();request=a.out/'requests.bin';request.write_bytes(request_bytes(rows));paths={}
        for name,exe in workers.items():
            output=a.out/(name+'.bin');run=worker(exe,request,output,code,image);(a.out/(name+'.log')).write_bytes(run.stdout+run.stderr)
            require(run.returncode==0,'Worker failed '+name+' '+run.stderr.decode(errors='replace'));paths[name]=output
        sample=compare_files(paths,rows,layout);observers=observer_controls(sample,rows[0],layout);negatives=admission_controls(workers,code,image,a.out,rows)
        report.update(passed=True,original_records=len(rows),native_comparisons=len(rows)*2,defined_differences=0,
                      roots=14,complete_functions=15,persistent_sequences=64,persistent_sequence_records=896,
                      categories=dict(Counter(q.category for q in rows)),standalone_defined_flags={'XOR_routes':0xcc5,'MOV_RET_routes':0xcd5},persistent_defined_flags_mask=0xcc5,
                      AF_scope='Undefined final XOR AF excluded on ten standalone roots and inherited persistent route; no other flags excluded',
                      original_State_events_tail='Explicit unobserved zero',native_State_events_tail='Actual full snapshots and checked bridges/hooks',
                      observer_controls=observers,admission_controls=negatives,build_path=str(a.build.resolve()),build_sha256=sha(a.build),request_sha256=sha(request),
                      outputs={name:{'path':str(path.resolve()),'size_bytes':path.stat().st_size,'sha256':sha(path)} for name,path in paths.items()})
    except (ValueError,OSError,subprocess.TimeoutExpired) as e:report['error']=str(e);put_json(a.out/'report.json',report);print(json.dumps(report));return 1
    put_json(a.out/'report.json',report);print(json.dumps({k:report[k] for k in ('passed','original_records','native_comparisons','defined_differences')}));return 0
if __name__=='__main__':raise SystemExit(main())


