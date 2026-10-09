"""Whole-state original-BEFORE/source comparison of native heap-create continuation rows."""
import json
from pathlib import Path
import struct
import sys
import time
import traceback
sys.dont_write_bytecode = True
from consumer import F, M, OLD
from before import expected, stage
from prefix import predict, source_material, FRAGMENT, SOURCE_CALL, SOURCE_RETURN, ENTRY, API_CALL, API_SLOT, API_RETURN, RAW_API, MODE_CALL, MODE_ENTRY, MODE_RETURN
from positive import positive
ROOT = F.ROOT
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import unique_object, verify_manifest
from paths import publish_bytes, workspace_path
from stages import verify_stage

BASELINE_SHA = 'a9a549d0acf1e8cd3a0015b4b7cdd2d61876ded33e0c69610c37bf9bc60b001d'
REASON = 'Required genuine CRT heap mode selector remains unresolved'


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




def main(execution_directory, execution_sha, output_directory):
    started = time.perf_counter_ns()
    out = workspace_path(output_directory,reports=True)
    if out.exists() or out.parent != ROOT/'reports/m4-crt-heap-create-root':
        raise ValueError('Fresh root observer output')
    out.mkdir()
    passed,rows,stages = False,[],[]
    try:
        for path in Path(__file__).parent.glob('*.py'):
            F.pin(path)
        F.pin(sys.executable)
        for name,digest in F.PIPELINE_SHAS.items():
            F.pin(ROOT/'tools/m4-pipeline'/name,digest)
        F.pin(ROOT/'reports/m4-crt-heap-init-root/root-acceptance-r1/report.json',BASELINE_SHA)
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
        source.update(raw)
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
                    F.require(value['passed'] and value['scenario'] == index and value['control'] == (0 if index < 24 else index+97), 'Complete declared native request inventory')
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
            native_executor='Delegated heap-creation author; root verifies actual stages and independently models ordinary rows',
            independently_executed_by_root=False,execution_sha256=execution_sha,native_stages=stages,
            scope='Original BEFORE/source composition plus declared real HeapCreate ownership witness and finite guest API ABI model',
            whole_State_bytes=3504,whole_FX_bytes=512,whole_Runtime_CPU_bytes=40,whole_pages=18,
            source_identity_bytes=1940,new_compiled_source_bytes=84,new_guarded_source_bytes=84,executed_source_bytes=48,new_guest_objects=0,prior_guest_objects_preserved=26,
            source_PCs=13,source_accesses=10,actual_source_CALLs=3,distinct_API_return_reads=1,host_guest_stack_stores=0,
            State_projection='EIP only',generic_Runtime_CPU_preserved=True,
            undefined_AF_architectural_equivalence_claimed=False,defined_final_arithmetic_flags='TEST opaque48450001: all6zero; AF generated representative0',
            borrowed_heap_global_page=True,HeapCreate_executed=True,host_heap_cleanup=True,heap_initialized=False,
            source_RET_executed=False,locale_executed=False,locale_initialized=False,parser_executed=False,
            argument_initialization_complete=False,original_attach_proved=False,
            source_commands=commands+heap_commands,main_initializer_count=27,whole_M4_complete=False,
            ordinary_game_launched=False,original_executed=False,author_expected_model_imported=False,
            AFTER_machine_state_used_as_seed=False,original_x86_API_internals_equivalence=False,files=F.PHYSICAL,physical_closure=closure if passed else None,
            seconds=(time.perf_counter_ns()-started)/1e9)
        publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
        if passed:
            F.pin(out/'report.json')
            publish_bytes(out/'pins.json',(json.dumps(dict(files=F.PHYSICAL),indent=2)+'\n').encode())
        print(json.dumps({k:v for k,v in report.items() if k not in ('files','rows','source_commands','native_stages')}))


if __name__ == '__main__':
    main(*sys.argv[1:])
