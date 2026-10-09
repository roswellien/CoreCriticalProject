"""Measure original offline operation recordings against compiled native runs.

Original per-access events are explicitly unobserved. Native bridge events are
actual recordings and are checked against a separate mutable-memory oracle.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys

from corpus import (cases, coverage, pack_sequences, unpack_sequences, expected_steps,
                    SETTER, CONSUMER, SENTINEL, IMAGE_SHA, SETTER_SHA, CONSUMER_SHA,
                    HEADER, RESULT_SIZE, STATE_SIZE, ENTRY_FLAGS, EVENT, MAX_EVENTS,
                    MAX_STEPS, REQUEST_SIZE, STACK, GLOBAL, BUFFER, PAGE)

ROOT = Path(__file__).resolve().parents[2]
CPU = struct.Struct('<10I')
META = struct.Struct('<6I')
CONSUMER_IR_SHA = '1e5827d9dcc1bb42795ec6f4c690e0649f995e744a2d60f3a97e36f966d6623e'
MEMORY_BEFORE, MEMORY_AFTER = 104, 16488
FX_BEFORE, FX_AFTER = 32872, 33384
ENV_BEFORE, ENV_AFTER = 33896, 33924
STATE_BEFORE, STATE_AFTER, EVENTS = 33952, 37456, 40960


def first_observer():
    """Reuse the frozen first-gate byte observers without broadening that gate."""
    path = ROOT/'tools/m3-slice'
    prior = sys.modules.get('corpus')
    try:
        spec = importlib.util.spec_from_file_location('_m3_first_corpus', path/'corpus.py')
        source = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = source
        spec.loader.exec_module(source)
        sys.modules['corpus'] = source
        spec = importlib.util.spec_from_file_location('_m3_first_observer', path/'compare_slice.py')
        observer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(observer)
    finally:
        if prior is None:
            sys.modules.pop('corpus', None)
        else:
            sys.modules['corpus'] = prior
    return observer


OBS = first_observer()
require, sha = OBS.require, OBS.sha


def put_json(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def validate_record(row, sequence, sequence_index, step_index, goal, mode, layouts,
                    *, original=None, previous=None):
    require(len(row) == RESULT_SIZE, 'result.record_size')
    seq, step, status, provenance, restored, event_count = META.unpack_from(row, 80)
    require((seq, step) == (sequence_index, step_index), 'result.actual_step_identity')
    require(status == 0, 'result.execution_status')
    require(provenance == mode, 'result.observation_provenance')
    require(restored == 1, 'result.host_environment_restoration')
    OBS.check_cpu(CPU.unpack_from(row), goal.cpu_before, ENTRY_FLAGS, 'entry_cpu')
    OBS.check_cpu(CPU.unpack_from(row, 40), goal.cpu_after, goal.flag_mask, 'exit_cpu')
    require(row[MEMORY_BEFORE:MEMORY_AFTER] == goal.memory_before, 'memory.actual_before_four_pages')
    require(row[MEMORY_AFTER:FX_BEFORE] == goal.memory_after, 'memory.actual_after_four_pages')
    fb, fa = row[FX_BEFORE:FX_AFTER], row[FX_AFTER:ENV_BEFORE]
    OBS.check_fx(fb, sequence.fx, 'entry_persistent_fp', metadata=bool(mode))
    if mode==0:
        actual=(OBS.u16(fb,6),OBS.u32(fb,8),OBS.u32(fb,16))
        seeded=(OBS.u16(sequence.fx,6),OBS.u32(sequence.fx,8),OBS.u32(sequence.fx,16))
        require(actual in ((0,0,0),seeded),'original.supported_FXSAVE_metadata_view')
    OBS.check_fx(fa, fb, 'preserved_fp')
    require(all(fb[32+i*16:42+i*16] == fa[32+i*16:42+i*16] for i in range(8)),
            'preserved_fp.all_actual_raw_storage')
    OBS.check_env(row[ENV_BEFORE:ENV_AFTER], fb, 'entry_env', metadata=sequence.fx)
    OBS.check_env(row[ENV_AFTER:STATE_BEFORE], fa, 'exit_env', metadata=sequence.fx)
    if previous is not None:
        OBS.check_fx(fb, previous[FX_AFTER:ENV_BEFORE], 'cross_step_persistent_fp')
    sb, sa = row[STATE_BEFORE:STATE_AFTER], row[STATE_AFTER:EVENTS]
    layout = layouts['setter' if goal.cpu_before[9] == SETTER else 'consumer']
    if mode == 0:
        require(event_count == 0 and row[EVENTS:] == bytes(MAX_EVENTS*EVENT.size),
                'original.per_access_trace_explicitly_unobserved')
        require(sb == bytes(STATE_SIZE) and sa == bytes(STATE_SIZE), 'original.opaque_state_explicitly_unobserved')
    else:
        require(event_count == len(goal.events) and event_count <= MAX_EVENTS, 'native.actual_event_count')
        for i, event in enumerate(goal.events):
            require(EVENT.unpack_from(row, EVENTS+i*EVENT.size) == event, f'native.ordered_event_{i}')
        require(row[EVENTS+event_count*EVENT.size:] == bytes((MAX_EVENTS-event_count)*EVENT.size),
                'native.unused_event_slots')
        OBS.check_cpu(OBS.state_cpu(sb, layout), CPU.unpack_from(row), ENTRY_FLAGS, 'actual_state.before_cpu_projection')
        OBS.check_cpu(OBS.state_cpu(sa, layout), CPU.unpack_from(row, 40), ENTRY_FLAGS, 'actual_state.after_cpu_projection')
        OBS.check_fx(OBS.state_fx(sb, layout), fb, 'actual_state.before_fp_projection')
        OBS.check_fx(OBS.state_fx(sa, layout), fa, 'actual_state.after_fp_projection')
        for start, end in OBS.protected_ranges(layout):
            require(sb[start:end] == sa[start:end], f'actual_state.protected_bytes_{start}_{end}')
        if previous is not None:
            ps = previous[STATE_AFTER:EVENTS]
            # Only the explicit caller CPU overlay may differ between steps.
            x = layout['struct_layouts']['struct.X86State']['offsets']
            g = layout['struct_layouts']['struct.GPR']['offsets']
            a = layout['struct_layouts']['struct.ArithFlags']['offsets']
            overlay = [(x[6]+g[i], x[6]+g[i]+4) for i in (1,3,5,7,9,11,13,15,33)]
            overlay += [(x[2]+a[i], x[2]+a[i]+1) for i in (1,3,5,7,9,11,13)]
            overlay += [(x[3], x[3]+8)]
            last = 0
            for start, end in sorted(overlay):
                require(ps[last:start] == sb[last:start], f'cross_step_state.persistent_bytes_{last}_{start}')
                last = end
            require(ps[last:] == sb[last:], 'cross_step_state.persistent_tail')
        if original is not None:
            OBS.check_fx(fb, original[FX_BEFORE:FX_AFTER], 'original_native.before_fp',metadata=False)
            OBS.check_fx(fa, original[FX_AFTER:ENV_BEFORE], 'original_native.after_fp',metadata=False)


def compare_saved(paths, sequences, layouts):
    streams = {name: path.open('rb') for name, path in paths.items()}
    count = sum(len(s.steps) for s in sequences)
    differences, examples, samples = Counter(), [], []
    try:
        for name, stream in streams.items():
            require(HEADER.unpack(stream.read(24)) == (b'MW34S3RS', 1, count, RESULT_SIZE,
                                                       32 if name == 'original' else 64), 'result.header:'+name)
        for seq_index, sequence in enumerate(sequences):
            previous = {name: None for name in streams}
            for step_index, goal in enumerate(expected_steps(sequence)):
                rows = {name: stream.read(RESULT_SIZE) for name, stream in streams.items()}
                for name, row in rows.items():
                    try:
                        validate_record(row, sequence, seq_index, step_index, goal, int(name != 'original'), layouts,
                                        original=rows['original'] if name != 'original' else None,
                                        previous=previous[name])
                    except ValueError as error:
                        differences[name] += 1
                        if len(examples) < 30:
                            examples.append({'worker': name, 'sequence': seq_index, 'step': step_index,
                                             'category': sequence.category, 'field': str(error)})
                previous = rows
                if seq_index < 10 or sequence.category in ('maximum_steps_and_work_budget', 'seeded_reconfiguration_connected_sequence') and seq_index % 32 == 0:
                    samples.append((seq_index, step_index, sequence, goal, rows))
        require(all(stream.read(1) == b'' for stream in streams.values()), 'result.trailing_bytes')
    finally:
        for stream in streams.values():
            stream.close()
    controls = observer_controls(samples, layouts) if not differences else []
    return {'passed': not differences, 'mismatched_records': dict(differences), 'examples': examples,
            'observer_controls': controls, 'observer_controls_count': len(controls)}


def observer_controls(samples, layouts):
    controls = []
    for kind in (SETTER, CONSUMER):
        seq_index, step_index, sequence, goal, rows = next(v for v in samples if v[3].cpu_before[9] == kind)
        good = rows['native-O2']
        mutations = [(f'{kind:x}_entry_gpr{i}', 4*i, 1) for i in range(8)]
        mutations += [(f'{kind:x}_exit_gpr{i}', 40+4*i, 1) for i in range(8)]
        mutations += [(f'{kind:x}_exit_flag{bit}', 72+bit//8, 1 << (bit%8))
                      for bit in range(12) if goal.flag_mask & (1 << bit)]
        mutations += [(f'{kind:x}_metadata_{offset}', offset, 1) for offset in (80,84,88,92,96,100)]
        mutations += [(f'{kind:x}_memory_{side}_{i}', side+i, 1)
                      for side in (MEMORY_BEFORE, MEMORY_AFTER)
                      for i in (0,4095,4096,8191,8192,16383,PAGE+0x1e4,PAGE+0x1f7)]
        mutations += [(f'{kind:x}_actual_state_{side}_{i}', side+i, 1)
                      for side in (STATE_BEFORE,STATE_AFTER) for i in (16,1024,2216,2486,2608,2737,2768,3503)]
        mutations += [(f'{kind:x}_FP_{side}_{i}', side+i, 1)
                      for side in (FX_BEFORE,FX_AFTER) for i in (0,2,4,6,8,16,24,160,287)]
        mutations += [(f'{kind:x}_env_{side}_{i}', side+i, 1)
                      for side in (ENV_BEFORE,ENV_AFTER) for i in (0,4,8,12,18,20)]
        mutations += [(f'{kind:x}_event_{i}_{field}', EVENTS+i*16+field, 1)
                      for i in (0,len(goal.events)-1) for field in (0,4,8,12)]
        mutations.append((f'{kind:x}_unused_event', EVENTS+len(goal.events)*16, 1))
        for name, offset, xor in mutations:
            bad = bytearray(good); bad[offset] ^= xor
            try:
                validate_record(bytes(bad), sequence, seq_index, step_index, goal, 1, layouts)
            except ValueError as error:
                controls.append({'name': name, 'outcome': 'rejected', 'reason': str(error)})
            else:
                raise ValueError('Observer ignored corruption: '+name)
        if kind == SETTER:
            altered = bytearray(good); altered[72] ^= 16; altered[STATE_AFTER+2069] ^= 1
            validate_record(bytes(altered),sequence,seq_index,step_index,goal,1,layouts)
            controls.append({'name':'setter_final_AF','outcome':'accepted_explicit_exclusion'})
        for offset in (28,47):
            altered = bytearray(good); altered[FX_BEFORE+offset] ^= 1; altered[FX_AFTER+offset] ^= 1
            validate_record(bytes(altered),sequence,seq_index,step_index,goal,1,layouts)
            controls.append({'name':f'{kind:x}_FX_report_only_exclusion_{offset}','outcome':'accepted_explicit_exclusion'})
        # Reversing actual bridge events must be visible even when disjoint
        # writes happen to yield the same final memory image.
        altered = bytearray(good)
        altered[EVENTS:EVENTS+16], altered[EVENTS+16:EVENTS+32] = altered[EVENTS+16:EVENTS+32], altered[EVENTS:EVENTS+16]
        try:
            validate_record(bytes(altered),sequence,seq_index,step_index,goal,1,layouts)
        except ValueError as error:
            controls.append({'name':f'{kind:x}_reordered_actual_events','outcome':'rejected','reason':str(error)})
        else:
            raise ValueError('Reordered event observer control admitted')
    return controls


def validate_layouts(layouts):
    setter,consumer=layouts['setter'],layouts['consumer']
    for kind,layout,pc,end,length,code,ir in (
        ('setter',setter,SETTER,0x5582bb,43,SETTER_SHA,OBS.GUEST_IR_SHA),
        ('consumer',consumer,CONSUMER,0x55a5d7,119,CONSUMER_SHA,CONSUMER_IR_SHA)):
        require(layout['profile']=='m3-connected-buffer-'+kind and
                layout['entry_va']==pc and layout['end_va']==end and layout['source_length']==length and
                layout['image_sha256']==IMAGE_SHA and layout['code_sha256']==code and layout['guest_ir_sha256']==ir,
                kind+'.exact_actual_function_layout')
        require(layout['state_bytes']==STATE_SIZE and layout['guest_pointer_bits']==32 and
                layout['host_pointer_bits']==64 and layout['all_struct_layouts_equal'] is True,
                kind+'.state_pointer_layout')
        require(layout['dll_sha256']==OBS.LLVM_SHA and layout['llvm_version']==[21,1,8] and
                layout['indirect_host_calls']==0 and layout['pointer_integer_conversions']==0,
                kind+'.tool_and_static_native_targets')
        OBS.protected_ranges(layout)
    require(consumer['struct_layouts']==setter['struct_layouts'],'consumer.same_complete_state_layout')
    require(setter['struct_layouts']['struct.X86State']['offsets']==
            [0,16,2064,2080,2088,2112,2208,2480,2608,2736,2760,2768,3280,3376],
            'component.reviewed_complete_state_offsets')
    flags=[(2065,1),(2067,1),(2069,1),(2071,1),(2073,1),(2077,1)]
    expected_setter=flags+[(2216,4),(2264,4),(2312,4),(2472,4)]
    expected_consumer=flags+[(2216,4),(2232,4),(2248,4),(2264,2),(2280,4),(2296,4),(2312,4),(2328,4),(2472,4)]
    for kind,expected in (('setter',expected_setter),('consumer',expected_consumer)):
        require(sorted((v['offset'],v['bytes']) for v in layouts[kind]['state_write_ranges'])==sorted(expected),
                kind+'.exact_integer_state_write_union')
    require(setter['call_counts']=={'__remill_read_memory_32':3,'__remill_write_memory_32':5,
                                  '__remill_function_return':1,'llvm.ctpop.i8':2,
                                  '__remill_flag_computation_carry':1,'__remill_flag_computation_zero':1,
                                  '__remill_flag_computation_sign':1,'__remill_flag_computation_overflow':1,
                                  '__remill_undefined_8':1},'setter.exact_static_call_counts')
    require(consumer['call_counts']=={'__remill_flag_computation_carry':4,'llvm.ctpop.i8':11,
                                    '__remill_flag_computation_zero':9,'__remill_flag_computation_sign':9,
                                    '__remill_flag_computation_overflow':6,'__remill_write_memory_32':8,
                                    '__remill_read_memory_32':12,'__remill_undefined_8':5,
                                    '__remill_compare_neq':3,'__remill_compare_sle':2,
                                    '__remill_read_memory_16':1,'__remill_write_memory_16':1,
                                    '__remill_function_return':1},'consumer.exact_static_call_counts')
    p=setter['undefined_flag_policy']
    require(p['policy']=='single-final-SAR-AF-arbitrary-zero' and p['value_has_only_AF_store_use'] is True and
            p['subsequent_AF_reads']==0 and p['defined_exit_flags_mask']==0xcc5,
            'setter.final_undefined_AF_policy')
    p=consumer['undefined_flag_policy']
    require(p['policy']=='consumer-intermediate-AF-overwritten-before-every-return' and
            p['state_offset']==2069 and p['width']==1 and p['undefined_calls']==5 and
            p['defined_exit_flags_mask']==0xcd5 and p['subsequent_AF_reads']==0 and
            p['value_has_only_AF_store_use'] is True and p['final_AF_defined'] is True and
            p['final_overwrite_dominates_every_return'] is True and
            p['final_overwrite']['block']=='634' and p['returns']==['671'] and len(p['llvm_cfg'])==47,
            'consumer.complete_CFG_final_defined_AF_policy')


def load_build(path):
    build = json.loads(path.read_bytes())
    require(build['schema_version'] == 1, 'build.schema')
    prior = build.get('previous_gate_pins', {})
    labels = ('first_build', 'first_comparison_report', 'first_initial_failure_report',
              'first_initial_failure_manifest', 'm2_final_pins', 'm2_independent_pins',
              'first_independent_review')
    for label in labels:
        binding = prior.get(label, {})
        p = Path(binding.get('path', ''))
        require(p.is_absolute() and sha(p) == binding.get('sha256'), 'build.previous_gate:'+label)
    require(prior['m2_final_pins']['sha256'] ==
            'eac862903896cc35721049d44818a7c50175302a1377b0707a0de20a2bc41a9e' and
            prior['m2_independent_pins']['sha256'] ==
            '41555de79e619c9fa41ccbbd7ea225514273fa9e3d13838691cb13df73fe067b',
            'build.frozen_M2_final_pins')
    require(prior['first_initial_failure_report']['sha256'] ==
            'c0b91148155e0fa6936137cb17f230e665489765916a39cabcc1e0ce49d56224' and
            prior['first_initial_failure_manifest']['sha256'] ==
            'ef335b729a757e36b88564db77322306e6cee7ca9166301b935e8e0d00614206',
            'build.frozen_first_failure')
    first = json.loads(Path(prior['first_comparison_report']['path']).read_bytes())
    require(first.get('passed') is True and first.get('original_cases') == 15780 and
            first.get('native_comparisons') == 31560 and
            first.get('build_sha256') == prior['first_build']['sha256'],
            'build.accepted_actual_first_comparison')
    require(json.loads(Path(prior['first_independent_review']['path']).read_bytes()).get('passed') is True,
            'build.accepted_first_independent_review')
    from source_identity import identity
    current = identity(ROOT)
    files = {str((ROOT/name).resolve()): value for name,value in current['source_files'].items()}
    require(build['source_files'] == files and build['source_digest'] == current['source_digest'], 'build.complete_current_source_snapshot')
    for group in ('source_files', 'tool_files'):
        require(build.get(group), 'build.missing_'+group)
        for name, digest in build[group].items():
            require(Path(name).is_absolute() and sha(Path(name)) == digest, 'build.identity:'+name)
    artifacts = {}
    for name, digest in build['artifacts'].items():
        p = Path(name) if Path(name).is_absolute() else path.parent/name
        require(sha(p) == digest, 'build.artifact:'+name)
        artifacts[p.resolve()] = digest
    workers = {name:Path(build['workers'][name]) for name in ('original','native-O0','native-O2')}
    for name,p in workers.items():
        require(p.is_absolute() and p.resolve() in artifacts, 'build.unpinned_worker:'+name)
    layouts = {name:json.loads(Path(build['layouts'][name]).read_bytes()) for name in ('setter','consumer')}
    validate_layouts(layouts)
    for kind in ('setter','consumer'):
        require(Path(build['layouts'][kind]).resolve() in artifacts,'build.unpinned_layout:'+kind)
        require(sha(path.parent/(kind+'-guest.ll'))==layouts[kind]['guest_ir_sha256'] and
                sha(path.parent/(kind+'-host.ll'))==layouts[kind]['host_ir_sha256'],'build.actual_IR_layout_binding:'+kind)
    image, codes = Path(build['image_path']), {name:Path(build['codes'][name]) for name in ('setter','consumer')}
    require(sha(image) == IMAGE_SHA and sha(codes['setter']) == SETTER_SHA and sha(codes['consumer']) == CONSUMER_SHA,
            'build.actual_private_code_image')
    return build,layouts,workers,image,codes


def run_worker(worker,request,output,image,codes,log):
    require(not output.exists(),'Refusing to overwrite previous evidence')
    cmd = [str(worker),str(request),str(output),str(codes['setter']),str(codes['consumer']),str(image)]
    run = subprocess.run(cmd,capture_output=True,timeout=180)
    log.write_bytes(run.stdout+b'\n'+run.stderr)
    return {'command':cmd,'exit_code':run.returncode,'log_path':str(log),'log_sha256':sha(log),
            'output_exists':output.exists(),'output_bytes':output.stat().st_size if output.exists() else 0}


def rejection_controls(workers,codes,image,out,sequences):
    """Late invalid operations must reject the whole input before execution."""
    out.mkdir()
    sequence=next(s for s in sequences if len(s.steps)>=3 and s.steps[0].cpu[9]==SETTER and
                  any(e[2]==2 for row in expected_steps(s) for e in row.events))
    good=pack_sequences([sequence])
    record=sequence.pack()
    entries=[('short_header',good[:7]),('short_record',good[:-1]),('trailing_byte',good+b'X')]
    prefix=24
    setter=528
    consumer=528+48
    mutations=[('step_count_zero',0,0),('step_count_high',0,MAX_STEPS+1),
               ('sequence_reserved',12,1),('full_tags_high',8,0x10000),
               ('setter_PC',setter+36,SETTER+1),('setter_frame_low',setter+16,STACK-1),
               ('setter_frame_high',setter+16,STACK+PAGE-11),
               ('consumer_PC',consumer+36,CONSUMER+1),
               ('consumer_frame_low',consumer+16,STACK+23),
               ('consumer_frame_high',consumer+16,STACK+PAGE-3),
               ('consumer_frame_wrap',consumer+16,0xffffffff),
               ('consumer_TF',consumer+32,0x302),('consumer_IF',consumer+32,2),
               ('consumer_unused_arg',consumer+40,1),
               ('source_span_cross_buffer_end',setter+4,BUFFER+8191),
               ('source_global_alias',setter+4,GLOBAL+0x1e4),
               ('source_stack_alias',setter+4,STACK+1024),
               ('source_code_alias',setter+4,SETTER),
               ('destination_span_cross_buffer_end',consumer+4,BUFFER+8191),
               ('destination_global_alias',consumer+4,GLOBAL+0x1e4),
               ('destination_stack_alias',consumer+4,STACK+1024),
               ('destination_code_alias',consumer+4,CONSUMER),
               ('outer_work_budget',setter+40,34),('inner_work_budget',setter+8,66),
               ('unsupported_MXCSR',16+24,0),('reserved_selector',16+12,1),
               ('nonzero_guest_FIP',16+8,1),('nonzero_guest_FDP',16+16,1)]
    for name,offset,value in mutations:
        bad=bytearray(record);struct.pack_into('<I',bad,offset,value)
        entries.append((name,HEADER.pack(b'MW34S3RQ',1,1,REQUEST_SIZE,32)+bad))
        entries.append(('late_sequence_'+name,HEADER.pack(b'MW34S3RQ',1,2,REQUEST_SIZE,32)+record+bad))
    for name,offset,value in [('unmasked_CW',16,0x37e),('reserved_PC',16,0x17f),
                             ('unsupported_SW',18,0x8000),('nonzero_guest_FOP',22,1)]:
        bad=bytearray(record);struct.pack_into('<H',bad,offset,value)
        entries.append((name,HEADER.pack(b'MW34S3RQ',1,1,REQUEST_SIZE,32)+bad))
        entries.append(('late_sequence_'+name,HEADER.pack(b'MW34S3RQ',1,2,REQUEST_SIZE,32)+record+bad))
    bad=bytearray(record);bad[528+len(sequence.steps)*48]=1
    entries.append(('unused_step_slot',HEADER.pack(b'MW34S3RQ',1,1,REQUEST_SIZE,32)+bad))
    bad=bytearray(record);struct.pack_into('<I',bad,528+(len(sequence.steps)-1)*48+36,CONSUMER+1)
    entries.append(('late_step_unknown_entry',HEADER.pack(b'MW34S3RQ',1,1,REQUEST_SIZE,32)+bad))
    altered={}
    for name,code in codes.items():
        altered[name]=out/f'{name}-changed-private-code.bin'
        body=bytearray(code.read_bytes());body[0]^=1;altered[name].write_bytes(body)
    results=[]
    for worker_name,worker in workers.items():
        for name,data in entries+[('changed_setter_code',good),('changed_consumer_code',good),('missing_private_image',good)]:
            inp=out/f'{worker_name}-{name}.request.bin';inp.write_bytes(data)
            output=out/f'{worker_name}-{name}.result.bin'
            selected=dict(codes)
            if name=='changed_setter_code':selected['setter']=altered['setter']
            if name=='changed_consumer_code':selected['consumer']=altered['consumer']
            run=run_worker(worker,inp,output,out/'missing-image.exe' if name=='missing_private_image' else image,
                           selected,out/f'{worker_name}-{name}.log')
            require(run['exit_code']!=0 and run['output_bytes']==0,
                    'Missing zero-output rejection:'+worker_name+'/'+name)
            results.append({'worker':worker_name,'name':name,'request_sha256':sha(inp),
                            'outcome':'rejected_before_execution_output',**run})
    return results


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--replay',type=Path)
    args=parser.parse_args()
    out=args.out.resolve()
    require(out.is_relative_to((ROOT/'reports/m3-subsystem').resolve()),'Private results must stay under reports/m3-subsystem')
    require(not out.exists(),'Refusing to replace previous evidence')
    build,layouts,workers,image,codes=load_build(args.build.resolve())
    out.mkdir(parents=True)
    sequences=cases()
    request=out/'requests.bin';request.write_bytes(pack_sequences(sequences))
    require(pack_sequences(unpack_sequences(request.read_bytes())) == request.read_bytes(),'request.exact_roundtrip')
    paths,executions={},{}
    if args.replay:
        require(sha(args.replay/'requests.bin') == sha(request),'replay.actual_input_identity')
        paths={name:args.replay/f'{name}.results.bin' for name in workers}
    else:
        for name,worker in workers.items():
            paths[name]=out/f'{name}.results.bin'
            executions[name]=run_worker(worker,request,paths[name],image,codes,out/f'{name}.log')
            if executions[name]['exit_code'] or not paths[name].exists():
                put_json(out/'report.json',{'schema_version':1,'passed':False,'failure':'worker_execution','executions':executions})
                return 1
    comparison=compare_saved(paths,sequences,layouts)
    controls=rejection_controls(workers,codes,image,out/'rejection-controls',sequences) if comparison['passed'] and not args.replay else []
    report={'schema_version':1,'experiment':'actual_connected_MW3_buffer_component',
            'coverage':coverage(sequences),'passed':comparison['passed'],'comparison':comparison,
            'build_path':str(args.build.resolve()),'build_sha256':sha(args.build),
            'request_path':str(request),'request_sha256':sha(request),'executions':executions,
            'results':{name:{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for name,p in paths.items()},
            'recording_provenance':'actual original isolated x86 per-step CPU/pages/FX/env; offline operation recordings',
            'original_per_access_trace':'unobserved; zero fields',
            'native_per_access_trace':'actual checked bridge events compared against independent mutable-memory oracle',
            'guest_metadata_domain':'zero FOP/FIP/FDP only; nonzero requests reject before execution',
            'rejection_controls':controls,'rejection_controls_count':len(controls),
            'observed_in_game_consumer_use':False,'replayed_saved_records':bool(args.replay)}
    put_json(out/'report.json',report)
    print(json.dumps({'passed':report['passed'],**report['coverage']}))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    try:
        sys.exit(main())
    except (ValueError,KeyError,OSError,subprocess.SubprocessError) as error:
        print('M3 subsystem comparison rejected: '+str(error),file=sys.stderr)
        sys.exit(1)
