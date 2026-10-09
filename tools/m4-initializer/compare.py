"""Measure the actual whole MW3 function; never implements a worker body.

Large result streams are read one record at a time. Proprietary inputs and
generated translations remain in the ignored private report directory.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

from corpus import (Case, ENTRY, SENTINEL, STACK, GLOBAL, PAGE, CWS, IMAGE_SHA,
                    CODE_SHA, HEADER, PREFIX, REQUEST_SIZE, RESULT_SIZE,
                    STATE_SIZE, ENTRY_FLAGS, EXIT_FLAGS, cases, expected,
                    initial_memory, full_tags,request_bytes)
from adapt_slice import CALL_COUNTS

ROOT = Path(__file__).resolve().parents[2]
CPU = struct.Struct('<10I')
OFFSETS = {'cpu_before': 0, 'cpu_after': 40, 'status': 80,
           'observation_mode': 84, 'host_restored': 88,
           'memory_before': 92, 'memory_after': 8284,
           'fx_before': 16476, 'fx_after': 16988,
           'env_before': 17500, 'env_after': 17528,
           'state_before': 17556, 'state_after': 21060}
GUEST_IR_SHA = '8dc7dc98da449480bd1ed4c472a2e65f79b27a2a5bb4d4fcd0e4f7f189d1b3fb'
LLVM_SHA = '34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb'
FLAG_FIELDS = ((0, 1), (2, 3), (4, 5), (6, 7), (7, 9), (10, 11), (11, 13))
SW_FIELDS = ((8, 1), (9, 3), (10, 5), (14, 7), (5, 9), (4, 11),
             (3, 13), (2, 15), (1, 17), (0, 19), (6, 21))


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


def protected_ranges(layout: dict) -> list[tuple[int, int]]:
    ranges = sorted((v['offset'], v['offset'] + v['bytes']) for v in layout['state_write_ranges'])
    out, last = [], 0
    for start, end in ranges:
        require(last <= start < end <= STATE_SIZE, 'layout.state_write_range_overlap')
        if last < start:
            out.append((last, start))
        last = end
    if last < STATE_SIZE:
        out.append((last, STATE_SIZE))
    return out


def validate_layout(layout):
    require(layout['profile']=='m4-startup-initializer-410910','layout.profile')
    require(layout['guest_ir_sha256']==GUEST_IR_SHA and layout['dll_sha256']==LLVM_SHA and layout['llvm_version']==[21,1,8],'layout.tool_ir_identity')
    require(layout['state_bytes']==3504 and layout['guest_pointer_bits']==32 and layout['host_pointer_bits']==64 and layout['all_struct_layouts_equal'] is True,'layout.abi')
    require(layout['struct_layouts']['struct.X86State']['offsets']==[0,16,2064,2080,2088,2112,2208,2480,2608,2736,2760,2768,3280,3376],'layout.actual_state_offsets')
    require(sorted((x['offset'],x['bytes']) for x in layout['state_write_ranges'])==[(2065,1),(2067,1),(2069,1),(2071,1),(2073,1),(2077,1),(2216,4),(2248,4),(2312,4),(2472,4)],'layout.exact_store_union')
    require(layout['call_counts']==CALL_COUNTS,'layout.exact_calls')
    require(layout['entry_va']==ENTRY and layout['end_va']==0x410934 and layout['source_length']==36 and layout['image_sha256']==IMAGE_SHA and layout['code_sha256']==CODE_SHA,'layout.actual_route')
    require(layout['undefined_flag_policy']=={'policy':'all arithmetic exit flags defined','defined_exit_flags_mask':0xcd5,'excluded_exit_flags':[]},'layout.all_flags_defined')
    require(layout['indirect_host_calls']==0 and layout['pointer_integer_conversions']==0 and layout['semantic_repairs']==[],'layout.unsupported_execution')
    protected_ranges(layout)


def validate_record(row,q,mode,layout,reference=None):
    require(len(row)==RESULT_SIZE,'result.size')
    require(struct.unpack_from('<3I',row,80)==(0,mode,1),'result.status_provenance_host')
    before,after=CPU.unpack_from(row),CPU.unpack_from(row,40)
    goal,memory,events=expected(q)
    check_cpu(before,q.cpu,ENTRY_FLAGS,'cpu.before')
    check_cpu(after,goal,EXIT_FLAGS,'cpu.after')
    require(row[92:8284]==initial_memory(q),'memory.before_all_bytes')
    require(row[8284:16476]==memory,'memory.after_all_bytes')
    fb,fa=row[16476:16988],row[16988:17500]
    check_fx(fb,q.fx,'fp.before')
    check_fx(fa,q.fx,'fp.after')
    for i in range(8):
        require(fb[32+i*16:42+i*16]==fa[32+i*16:42+i*16],'fp.preserved_all_raw80_slots')
    check_env(row[17500:17528],q.fx,'env.before')
    check_env(row[17528:17556],q.fx,'env.after')
    require(row[17500:17528]==row[17528:17556],'env.full_actual_preservation')
    sb,sa=row[17556:21060],row[21060:24564]
    count=u32(row,24564)
    actual_events=tuple(struct.unpack_from('<4I',row,24568+i*16) for i in range(168))
    if mode==0:
        require(sb==bytes(3504) and sa==bytes(3504),'original.State_unobserved_zero')
        require(count==0 and actual_events==((0,0,0,0),)*168,'original.events_unobserved_zero')
    else:
        require(count==168 and actual_events==events,'native.actual_ordered_events')
        check_cpu(state_cpu(sb,layout),before,ENTRY_FLAGS,'State.before_cpu_projection')
        check_cpu(state_cpu(sa,layout),after,EXIT_FLAGS,'State.after_cpu_projection')
        check_fx(state_fx(sb,layout),fb,'State.before_fp_projection')
        check_fx(state_fx(sa,layout),fa,'State.after_fp_projection')
        for lo,hi in protected_ranges(layout):require(sb[lo:hi]==sa[lo:hi],f'State.protected_{lo}_{hi}')
        if reference is not None:
            check_cpu(after,CPU.unpack_from(reference,40),EXIT_FLAGS,'original_native_cpu')
            require(row[92:16476]==reference[92:16476],'original_native_all_memory')
            for off in (16476,16988):check_fx(row[off:off+512],reference[off:off+512],'original_native_actual_FP')
            require(row[17500:17556]==reference[17500:17556],'original_native_actual_ENV')


def compare_files(paths,rows,layout):
    from contextlib import ExitStack
    with ExitStack() as stack:
        streams={name:stack.enter_context(path.open('rb')) for name,path in paths.items()}
        for name,stream in streams.items():
            require(HEADER.unpack(stream.read(24))==(b'MW34I4RS',1,len(rows),RESULT_SIZE,32 if name=='original' else 64),'result.header')
        sample=None
        for i,q in enumerate(rows):
            actual={name:stream.read(RESULT_SIZE) for name,stream in streams.items()}
            for name,record in actual.items():
                try:validate_record(record,q,0 if name=='original' else 1,layout,actual['original'] if name!='original' else None)
                except ValueError as e:raise ValueError(f'{name} row{i} {q.category}: {e}') from e
            if i==0:sample=actual
        require(all(not s.read(1) for s in streams.values()),'result.trailing')
    return sample


def observer_controls(sample,q,layout):
    controls=[]
    def reject(name,offset,mode,delta=1):
        changed=bytearray(sample['native-O0' if mode else 'original']);changed[offset]^=delta
        try:validate_record(bytes(changed),q,mode,layout,sample['original'] if mode else None)
        except ValueError as e:controls.append({'name':name,'rejected':True,'reason':str(e)});return
        raise ValueError('Observer accepted corruption '+name)
    for mode in (0,1):
        for i in range(8):reject(f'mode{mode}.entry_gpr{i}',i*4,mode);reject(f'mode{mode}.exit_gpr{i}',40+i*4,mode)
        for bit in (0,2,4,6,7,10,11):reject(f'mode{mode}.defined_exit_flag{bit}',72+bit//8,mode,1<<(bit%8))
        for name,off in [('entryPC',36),('exitPC',76),('status',80),('provenance',84),('host',88),
                         ('stack_before',92),('stack_after',8284),('data_before',4188),('data_after',12380),
                         ('CWbefore',16476),('CWafter',16988),('FOPbefore',16482),('FIPbefore',16484),('FDPafter',17004),
                         ('FTWafter',16992),('MXCSRafter',17012),('ENVtagsafter',17536),('ENVFIPafter',17540),('ENVFDPafter',17548)]:
            reject(f'mode{mode}.{name}',off,mode)
        for i in range(8):reject(f'mode{mode}.raw80slot{i}',16988+32+i*16,mode);reject(f'mode{mode}.XMM{i}',16988+160+i*16,mode)
    for name,off in [('state_before_cpu',17556+2216),('state_after_AF',21060+2069),('protected_state',21060+3000),
                     ('event_count',24564),('first_event_address',24568),('first_event_value',24572),('first_event_width',24576),
                     ('first_event_operation',24580),('last_event_address',24568+167*16),('last_event_value',24572+167*16)]:reject(name,off,1)
    return controls


def worker(worker,request,out,code,image):
    run=subprocess.run([str(worker),str(request),str(out),str(code),str(image)],capture_output=True,timeout=180)
    return run


def admission_controls(workers,code,image,out,good):
    base=request_bytes(good[:2]);controls=[];folder=out/'admission';folder.mkdir()
    mutations={}
    def changed(name,offset,value,width=1):
        b=bytearray(base);b[offset:offset+width]=value.to_bytes(width,'little');mutations[name]=bytes(b)
    changed('header-magic',0,0);changed('header-width',20,64,4);changed('header-version',8,2,4)
    changed('entry-PC',24+36,ENTRY+1,4);changed('late-entry-PC',24+568+36,ENTRY+1,4)
    changed('stack-below',24+16,STACK-1,4);changed('stack-last-plus1',24+16,STACK+4093,4)
    changed('unmasked-CW',24+56,0x7e,2);changed('invalid-SW',24+58,0x8000,2)
    changed('FOP',24+62,1,2);changed('FIP',24+64,1,4);changed('FDP',24+72,1,4)
    changed('late-FOP',24+568+62,1,2);changed('reserved-FX',24+61,1)
    changed('unused-arg',24+40,1,4);changed('late-unused-arg',24+568+44,1,4)
    changed('unsafe-entry-flags',24+32,0x3202,4);changed('bad-MXCSR',24+80,0,4)
    mutations['truncated']=base[:-1];mutations['trailing']=base+b'x'
    paths={}
    for name,data in mutations.items():
        path=folder/(name+'.rq');path.write_bytes(data);paths[name]=(path,code,image)
    bad_code=folder/'changed-code.bin';b=bytearray(code.read_bytes());b[-1]^=1;bad_code.write_bytes(b)
    bad_image=folder/'changed-image.bin';b=bytearray(image.read_bytes());b[0]^=1;bad_image.write_bytes(b)
    valid=folder/'valid.rq';valid.write_bytes(base)
    paths['changed-code']=(valid,bad_code,image);paths['changed-image']=(valid,code,bad_image)
    for label,exe in workers.items():
        for name,(request,candidate,owner_image) in paths.items():
            output=folder/(label+'-'+name+'.rs')
            run=worker(exe,request,output,candidate,owner_image)
            log=folder/(label+'-'+name+'.log');log.write_bytes(run.stdout+run.stderr)
            detail=run.stderr.decode(errors='replace')
            require(run.returncode!=0 and not output.exists(),'admission accepted invalid '+label+'/'+name)
            require('reservation failed' not in detail.lower(),'admission rejected before intended diagnostic '+label+'/'+name)
            controls.append({'worker':label,'name':name,'exit_code':run.returncode,'output_created':False,
                             'request_sha256':sha(request),'code_sha256':sha(candidate),'image_sha256':sha(owner_image),
                             'log_path':str(log),'log_sha256':sha(log),'diagnostic':detail})
    return controls


def load_build(path):
    build=json.loads(path.read_text(encoding='utf-8-sig'))
    require(build['profile']=='m4-startup-initializer-410910','build.profile')
    for field in ('source_files','tool_files','previous_gate_pins'):
        for name,digest in build[field].items():require(sha(Path(name))==digest,'build.changed '+field+' '+name)
    for name,digest in build['artifacts'].items():require(sha(Path(name) if Path(name).is_absolute() else path.parent/name)==digest,'build.changed artifact '+name)
    code,image=Path(build['code_path']),Path(build['image_path'])
    require(sha(code)==CODE_SHA and sha(image)==IMAGE_SHA,'build.actual_input')
    require(build['guest_ir_sha256']==GUEST_IR_SHA and build['fast_math'] is False and build['static_native_translation'] is True and build['semantic_repairs']==[],'build.translation')
    layout=json.loads(Path(build['layout_path']).read_text());validate_layout(layout)
    return build,layout,{name:Path(p) for name,p in build['workers'].items()},code,image


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();out=a.out.resolve();require(out.is_relative_to((ROOT/'reports/m4-initializer').resolve()) and not out.exists(),'Fresh private output required')
    out.mkdir(parents=True)
    report={'schema_version':1,'passed':False,'scope':'Complete actual startup initializer wrapper/body offline; not native startup or menus'}
    try:
        build,layout,workers,code,image=load_build(a.build)
        rows=cases();request=out/'requests.bin';request.write_bytes(request_bytes(rows))
        paths={}
        for label,exe in workers.items():
            path=out/(label+'.bin');run=worker(exe,request,path,code,image)
            (out/(label+'.log')).write_bytes(run.stdout+run.stderr)
            require(run.returncode==0,'Worker failed '+label+' '+run.stderr.decode(errors='replace'))
            paths[label]=path
        samples=compare_files(paths,rows,layout)
        observations=observer_controls(samples,rows[0],layout)
        negatives=admission_controls(workers,code,image,out,rows)
        report.update(passed=True,original_cases=len(rows),native_comparisons=len(rows)*2,defined_differences=0,
                      categories=dict(Counter(q.category for q in rows)),loop_taken_per_case=166,loop_exit_per_case=1,
                      byte_writes_per_case=167,ordered_native_events_per_case=168,
                      observer_controls=observations,admission_controls=negatives,
                      build_path=str(a.build.resolve()),build_sha256=sha(a.build),request_sha256=sha(request),
                      outputs={label:{'path':str(path),'size_bytes':path.stat().st_size,'sha256':sha(path)} for label,path in paths.items()},
                      image_sha256=IMAGE_SHA,code_sha256=CODE_SHA,defined_exit_flags_mask=EXIT_FLAGS,excluded_flags=[],
                      guest_metadata_domain='zero-only FOP/FIP/FDP; exact mandatory actual FX and ENV equality',
                      original_event_provenance='unobserved zero; no per-access hardware tracing',native_event_provenance='actual checked bridge calls',
                      original_State_provenance='unobserved zero',native_State_provenance='actual full3504-byte snapshots',
                      fp='all requested architectural fields; every captured raw80 slot preserved within each worker; exact full ENV and all protected State storage')
    except (ValueError,OSError,subprocess.TimeoutExpired) as e:
        report['error']=str(e);put_json(out/'report.json',report);print(json.dumps(report));return 1
    put_json(out/'report.json',report)
    print(json.dumps({key:report[key] for key in ('passed','original_cases','native_comparisons','defined_differences')}));return 0

if __name__=='__main__':raise SystemExit(main())


