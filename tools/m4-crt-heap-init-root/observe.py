"""Whole-state original-BEFORE/source comparison of native heap-prefix rows."""
import json
from pathlib import Path
import struct
import sys
import time
import traceback
sys.dont_write_bytecode = True
from consumer import F, M, OLD
from before import expected, stage
from prefix import predict, source_material, FRAGMENT, SOURCE_CALL, SOURCE_RETURN, ENTRY, API_CALL, API_SLOT, API_RETURN, RAW_API
ROOT = F.ROOT
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import unique_object, verify_manifest
from paths import publish_bytes, workspace_path
from stages import verify_stage

BASELINE_SHA = '211a866900b2274aad08c5ac710e0b69c93c34e279a7bfe3745b837541edf65e'
REASON = 'Required KERNEL32.dll HeapCreate remains unresolved'


def read(path):
    return json.loads(path.read_bytes(),object_pairs_hook=unique_object)


def ancillary_units(reader, identity, inventory):
    units = F.LogicalPath(reader,'units',inventory)
    F.require(inventory['units'] == {'api-before.bin','api-after.bin','module-before.bin','module-after.bin',
        'caller-error.bin','units-host-before.bin','units-host-after.bin'} |
        {f'capacity-{n}.bin' for n in (0,1,8,260)}, 'Exact ancillary native API-unit inventory')
    module = F.identities(units,F.pin(identity['worker']),prefix='')
    M.D.host((units/'units-host-before.bin').read_bytes(),(units/'units-host-after.bin').read_bytes())
    error = F.words((units/'caller-error.bin').read_bytes(),2)
    F.require(error[0] == error[1], 'Ancillary unit caller LastError restored')
    for size in (0,1,8,260):
        data = (units/f'capacity-{size}.bin').read_bytes()
        F.require(len(data) == 536, 'Complete ancillary real API witness')
        request,incoming,length,error = F.words(data[:16],4)
        before,after = data[16:276],data[276:]
        F.require(before == bytes((n*31+17)&255 for n in range(260)), 'Declared ancillary scratch seed')
        F.require((request,incoming) == (size,0xface0123) and after[size:] == before[size:], 'Ancillary capacity/tail')
        if size < 260:
            F.require((length,error) == (size,122), 'Actual ancillary truncation/zero-capacity result')
            if size:
                F.require(after[size-1] == 0, 'Actual ancillary truncation NUL')
        else:
            F.require(0 < length < size and after[length] == 0 and after[length+1:] == before[length+1:] and
                      after[:length].decode('mbcs') == str(module), 'Actual ancillary filename/NUL/tail')


def positive(row, entry, phases, program, index, level):
    result = read(row/'result.json')
    F.require(result['passed'] and result['scenario'] == index and result['control'] == 0, 'Ordinary native row identity')
    F.require(result['writer_complete'] and result['entry_executed'] and result['poisoned_retry'] and
              not result['State_reseed_after_writer'] and not result['full_CRT'] and
              not result['whole_M4_complete'], 'Bounded carried startup and terminal retry')
    F.require(result['source_events'] == len(entry.events) and result['writer_events'] == 97 and
              result['data_routes'] == 1, 'Complete prior source execution ledgers')
    heap = predict(entry,program)
    phases.update(heap['phases'])
    final = stage(heap['state'],heap['fx'],heap['cpu'],heap['memory'])
    phases['entry-after-fault'] = final
    phases['retry-after'] = final
    tags = {name.split('/')[1] for name in row.inventory if name.startswith(row.name+'/') and name.count('/') == 1}
    F.require(tags == set(phases), 'Exact independently derived checkpoint inventory')
    for tag,files in phases.items():
        F.full_stage(row,tag,files,index == 0 and tag.startswith('heap-'))
    evidence = OLD.evidence(entry)
    evidence['mainargs-job.bin'] = struct.pack('<20I',M.SLOT,M.RAW,*([0]*13),1,0,0,API_CALL,API_SLOT)
    evidence['mainargs-events.bin'] = bytes(256)
    evidence['mainargs-accesses.bin'] = bytes(1280)
    for name,value in evidence.items():
        actual = (row/name).read_bytes()
        F.require((json.loads(actual) if name.endswith('.json') else actual) == value, 'Complete prior evidence '+name)
    F.require((result['fault_reason'],result['fault_site'],result['fault_target']) == (1,API_CALL,API_SLOT),
              'Typed unresolved named import at actual HeapCreate CALL')
    for name in ('mainargs-reason.txt','heap-reason.txt'):
        F.require((row/name).read_text().strip() == REASON, 'First genuine import diagnostic '+name)
    for name,reason in (('initterm',entry.init_reason),('control',entry.control_reason),('matherr','')):
        F.require((row/(name+'-reason.txt')).read_text().strip() == reason, 'Prior reason '+name)
    for actor in ('writer','entry'):
        M.D.host((row/(actor+'-host-before.bin')).read_bytes(),(row/(actor+'-host-after.bin')).read_bytes())
    job = (row/'entry-job.bin').read_bytes()
    F.require(len(job) == 40 and job[32:] == bytes(8) and struct.unpack_from('<3I',job,20) == (1,API_CALL,API_SLOT),
              'Ordinary entry boundary job without fixture callback')
    access = b''.join(struct.pack('<5I',*v) for v in heap['accesses'])
    F.require((row/'heap-accesses.bin').read_bytes() == access+bytes(640-len(access)), 'Full eight-entry source access ledger')
    events = [(1,FRAGMENT,heap['parent_frame'],0),(2,SOURCE_CALL,ENTRY,SOURCE_RETURN),
              (3,API_CALL,API_SLOT,RAW_API)]
    event_bytes = b''.join(struct.pack('<4I',*v) for v in events)
    F.require((row/'heap-events.bin').read_bytes() == event_bytes+bytes(128-len(event_bytes)), 'Host projection and actual source CALL events')
    F.require(F.words((row/'heap-scheduler.bin').read_bytes(),8) == heap['scheduler'], 'EIP-only host scheduling; no host guest-memory store')
    F.require(F.words((row/'heap-undefined.bin').read_bytes(),8) == (ENTRY,0,0,0,0,0,0,0), 'Sole exact source XOR undefined-AF bridge site')
    job = F.words((row/'heap-job.bin').read_bytes(),26)
    F.require(job[:14] == (0,heap['initializer_frame'],heap['parent_frame'],8,3,1,4,0,API_CALL,API_SLOT,1,0,1,1)
              and job[14] == job[15] and job[16:] == (FRAGMENT,ENTRY,SOURCE_CALL,SOURCE_RETURN,
              API_CALL,API_SLOT,API_RETURN,RAW_API,17,84), 'Exact heap-prefix immutable job, lifecycle and LastError closure')
    unused = {
        'filename-job.bin':struct.pack('<22I',0,0xa11c0000+index,*([0]*18),0x78037174,0x7800bbd6),
        'filename-witness.bin':bytes(536),
        'commandline-job.bin':struct.pack('<28I',*([0]*4),0x3442e,*([0]*20),0x33000000,0x78037174,0x78001897),
        'commandline-accesses.bin':bytes(320),'commandline-consumer-accesses.bin':bytes(320),'commandline-events.bin':bytes(256),
        'parser-job.bin':struct.pack('<20I',*([0]*14),0x7800bc48,0x7800bbf7,0x7800bbfc,0x7800bce6,0x780379e1,436),
        'parser-accesses.bin':bytes(640),'parser-events.bin':bytes(128),'parser-undefined.bin':bytes(32),
        'locale-job.bin':struct.pack('<24I',*([0]*15),0x78003dd2,0x78003ddb,0x78001055,0x7800107b,0x780012b3,0x78001080,0x7803708c,17,269),
        'locale-accesses.bin':bytes(640),'locale-events.bin':bytes(128),'locale-scheduler.bin':bytes(40),
    }
    for name,value in unused.items():
        F.require((row/name).read_bytes() == value, 'Constructed but unexecuted service '+name)
    for name in ('filename','commandline','parser','locale'):
        F.require((row/(name+'-reason.txt')).read_text().strip() == '', 'Unused service has no fabricated fault '+name)
    root_files = set(evidence)|set(unused)|{'input.bin','writer-record.bin','writer-host-before.bin','writer-host-after.bin',
        'entry-host-before.bin','entry-host-after.bin','entry-job.bin','result.json','matherr-reason.txt','control-reason.txt',
        'initterm-reason.txt','mainargs-reason.txt','filename-reason.txt','commandline-reason.txt','parser-reason.txt',
        'locale-reason.txt','heap-reason.txt','heap-job.bin','heap-events.bin','heap-accesses.bin','heap-scheduler.bin','heap-undefined.bin'}
    F.require(row.inventory[row.name] == root_files, 'Exact complete ordinary evidence inventory')
    F.require(len(heap['PCs']) == 9 and len(heap['accesses']) == 8 and len(heap['routes']) == 2 and
              heap['API_frame'] == 0x20001848 and not heap['API_executed'] and not heap['heap_initialized'], 'Complete source frontier without API/heap result')
    F.require(0x78035000 not in heap['memory'], 'No raw heap-global map or initialized-state credit')
    return dict(index=index,level=level,source_PCs=9,source_accesses=8,actual_source_CALLs=2,
        host_guest_stack_stores=0,checkpoints=len(phases),whole_State=3504,whole_FX=512,whole_Runtime_CPU=40,
        whole_pages=17,undefined_XOR_AF='Declared compiled representative0; final CMP defines arithmetic flags',
        HeapCreate_executed=False,heap_initialized=False,original_attach_proved=False)


def main(execution_directory, execution_sha, output_directory):
    started = time.perf_counter_ns()
    out = workspace_path(output_directory,reports=True)
    if out.exists() or out.parent != ROOT/'reports/m4-crt-heap-init-root':
        raise ValueError('Fresh root observer output')
    out.mkdir()
    passed,rows,stages = False,[],[]
    try:
        for path in Path(__file__).parent.glob('*.py'):
            F.pin(path)
        F.pin(sys.executable)
        for name,digest in F.PIPELINE_SHAS.items():
            F.pin(ROOT/'tools/m4-pipeline'/name,digest)
        F.pin(ROOT/'reports/m4-crt-locale-default-root/root-acceptance-r2/report.json',BASELINE_SHA)
        execution = read(F.pin(Path(execution_directory)/'report.json',execution_sha))
        F.require(execution['passed'] and execution['native_stages_completed'] == 2, 'Both actual delegated native workers complete')
        for path,digest in execution['files'].items():
            F.pin(path,digest)
        for level in ('O0','O2'):
            for key in ('native_stage','pack_stage'):
                path = F.pin(Path(execution['levels'][level][key])/'stage.json')
                checked = verify_stage(path.parent,sha_file(path))
                F.require(checked['recorded_stage_passed'], 'Current zero-exit native/pack stage')
                stages.append(checked)
        program,providers,maths,ctrl,init,args,argv,source,commands = M.source_material(out)
        heap_program,raw,heap_commands = source_material(out)
        source[0x78003000] = raw
        wp,pp,gp = M.R.source_material()
        original = F.pin(ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin',F.ORIGINAL_SHA)
        payloads = [M.R.project(v) for v in M.R.originals(original.read_bytes())[:24]]
        for level in ('O0','O2'):
            identity = execution['levels'][level]
            with CaptureBundle(F.pin(identity['bundle'],identity['bundle_sha256']),identity['bundle_sha256']) as reader:
                F.require(reader.read_bytes('COMPLETE') == b'COMPLETE', 'Strict complete capture')
                F.require(len(reader.names()) == identity['logical_files'], 'Complete externally bound capture inventory')
                F.require({n.split('/')[0] for n in reader.names()} == {'COMPLETE','units'}|{f'row-{n}' for n in range(36)}, 'Exact complete top-level capture inventory')
                root = F.LogicalPath(reader,'root')
                ancillary_units(reader,identity,root.inventory)
                for index in range(36):
                    value = read(F.LogicalPath(reader,f'row-{index}/result.json',root.inventory))
                    F.require(value['passed'] and value['scenario'] == index and value['control'] == (0 if index < 24 else index+85), 'Complete declared native request inventory')
                for index in range(24):
                    row = F.LogicalPath(reader,f'row-{index}',root.inventory)
                    entry,phases = expected(row,payloads[index],wp,pp,gp,program,providers,maths,ctrl,init,args,argv,source,level)
                    rows.append(positive(row,entry,phases,heap_program,index,level))
        for module in (M,M.M,M.M.M,M.M.M.M,M.D,M.R,M.N,M.D.E,M.F,M.C):
            for path,digest in module.PINS.items():
                F.pin(path,digest)
        for path in out.iterdir():
            if path.is_file():
                F.pin(path)
        closure = verify_manifest(F.PHYSICAL)
        passed = True
    except Exception:
        publish_bytes(out/'failure.txt',traceback.format_exc().encode())
        raise
    finally:
        report = dict(passed=passed,rows=rows,checks=F.CHECKS,
            original_BEFORE_ordinary_sequences=48 if passed else 0,root_full_causal_model_sequences=0,
            selected_semantic_byte_corruption_denials=F.SEMANTIC_DENIALS,
            native_executor='Delegated heap initializer author; root verifies actual stages and independently models ordinary rows',
            independently_executed_by_root=False,execution_sha256=execution_sha,native_stages=stages,
            scope='Independent original BEFORE/source composition; frozen FDIV native OS query witness only',
            whole_State_bytes=3504,whole_FX_bytes=512,whole_Runtime_CPU_bytes=40,whole_pages=17,
            source_identity_bytes=1940,new_compiled_source_bytes=84,new_guarded_source_bytes=84,
            source_PCs=9,source_accesses=8,actual_source_CALLs=2,host_guest_stack_stores=0,
            State_projection='EIP only',generic_Runtime_CPU_preserved=True,
            undefined_AF_architectural_equivalence_claimed=False,defined_final_arithmetic_flags='CMP1-0: all6zero',
            borrowed_heap_global_page=False,HeapCreate_executed=False,heap_initialized=False,
            source_RET_executed=False,locale_executed=False,locale_initialized=False,parser_executed=False,
            argument_initialization_complete=False,original_attach_proved=False,
            source_commands=commands+heap_commands,main_initializer_count=27,whole_M4_complete=False,
            ordinary_game_launched=False,original_executed=False,author_expected_model_imported=False,
            AFTER_machine_state_used_as_seed=False,files=F.PHYSICAL,physical_closure=closure if passed else None,
            seconds=(time.perf_counter_ns()-started)/1e9)
        publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
        if passed:
            F.pin(out/'report.json')
            publish_bytes(out/'pins.json',(json.dumps(dict(files=F.PHYSICAL),indent=2)+'\n').encode())
        print(json.dumps({k:v for k,v in report.items() if k not in ('files','rows','source_commands','native_stages')}))


if __name__ == '__main__':
    main(*sys.argv[1:])
