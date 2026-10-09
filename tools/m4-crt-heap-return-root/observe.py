"""Original-BEFORE/source observer of the actual native source heap-mode publication and initializer return gate."""
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback
sys.dont_write_bytecode=True
from consumer import F,M
from before import expected
from prefix import source_material
from positive import positive
ROOT=F.ROOT
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle,sha_file
from manifests import unique_object,verify_manifest
from paths import publish_bytes,workspace_path
from stages import verify_stage

path=F.pin(ROOT/'tools/m4-crt-heap-mode-root/observe.py',
    'c0ed3705d9417d7b706ec6fbb9c759f2bf0c3bcb1a4784a67b883c03633cdf31')
spec=importlib.util.spec_from_file_location('heap_return_fixed_ancillary',path)
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)


def read(path): return json.loads(path.read_bytes(),object_pairs_hook=unique_object)


def main(execution_directory,execution_sha,output_directory):
    started=time.perf_counter_ns();out=workspace_path(output_directory,reports=True)
    if out.exists() or out.parent!=ROOT/'reports/m4-crt-heap-return-root':
        raise ValueError('Fresh observer output')
    out.mkdir();passed=False;rows=[];stages=[];closure=None
    try:
        for name in ('consumer.py','before.py','prefix.py','draft.py','ownership.py','positive.py','observe.py'):
            F.pin(Path(__file__).with_name(name))
        F.pin(sys.executable)
        for name,h in F.PIPELINE_SHAS.items(): F.pin(ROOT/'tools/m4-pipeline'/name,h)
        for path,h in (
            ('reports/m4-crt-heap-version-root/root-acceptance-r1/report.json','cedd67126afce1ec3392e8e0f8fec71f54823e58bc353055aee723203eef18d1'),
            ('reports/m4-crt-heap-return-recovery/recovery-r1/report.json','c285ece7e08e2c152735629c48aae461d9f28d006895cf87e9f5157b23053684'),
            ('reports/m4-crt-heap-return-review/source-r3/report.json','814f2fb571baf2c60f88905204bf28ae1552a4e1a1b0d4fe3a2584f8525a8904')):
            F.pin(ROOT/path,h)
        execution=read(F.pin(Path(execution_directory)/'report.json',execution_sha))
        F.require(execution['passed'] and execution['native_stages_completed']==2,'Both actual delegated native workers complete')
        for path,h in execution['files'].items(): F.pin(path,h)
        for level in ('O0','O2'):
            for key in ('native_stage','pack_stage'):
                path=F.pin(Path(execution['levels'][level][key])/'stage.json')
                checked=verify_stage(path.parent,sha_file(path))
                F.require(checked['recorded_stage_passed'],'Current stable successful native/pack stage');stages.append(checked)
        program,providers,maths,ctrl,init,args,argv,source,commands=M.source_material(out)
        heap_program,pages,heap_commands=source_material(out);source.update(pages)
        wp,pp,gp=M.R.source_material()
        original=F.pin(ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin',F.ORIGINAL_SHA)
        payloads=[M.R.project(v) for v in M.R.originals(original.read_bytes())[:24]]
        for level in ('O0','O2'):
            identity=execution['levels'][level]
            with CaptureBundle(F.pin(identity['bundle'],identity['bundle_sha256']),identity['bundle_sha256']) as reader:
                F.require(reader.read_bytes('COMPLETE')==b'COMPLETE' and len(reader.names())==identity['logical_files'],
                          'Strict whole-digest, per-entry and complete inventory binding')
                F.require({n.split('/')[0] for n in reader.names()}=={'COMPLETE','units'}|{f'row-{i}' for i in range(36)},
                          'Exact complete native top-level inventory')
                root=F.LogicalPath(reader,'root');prior.ancillary_units(reader,identity,root.inventory)
                for i in range(36):
                    value=read(F.LogicalPath(reader,f'row-{i}/result.json',root.inventory))
                    F.require(value['passed'] and value['scenario']==i and value['control']==(0 if i<24 else i+133),
                              'Complete declared ordinary/fault request inventory')
                for i in range(24):
                    row=F.LogicalPath(reader,f'row-{i}',root.inventory)
                    entry,phases=expected(row,payloads[i],wp,pp,gp,program,providers,maths,ctrl,init,args,argv,source,level)
                    rows.append(positive(row,entry,phases,heap_program,i,level))
        for module in (M,M.M,M.M.M,M.M.M.M,M.D,M.R,M.N,M.D.E,M.F,M.C):
            for path,h in module.PINS.items(): F.pin(path,h)
        for path in out.iterdir():
            if path.is_file(): F.pin(path)
        closure=verify_manifest(F.PHYSICAL);passed=True
    except Exception:
        publish_bytes(out/'failure.txt',traceback.format_exc().encode());raise
    finally:
        ordinary_returned=sum(row['selector_returned'] for row in rows)
        report=dict(passed=passed,rows=rows,checks=F.CHECKS,original_BEFORE_ordinary_sequences=48 if passed else 0,
            root_full_causal_model_sequences=0,selected_semantic_byte_corruption_denials=F.SEMANTIC_DENIALS,
            native_executor='Delegated heap-return author; root compares full source and finite actual API witnesses',
            independently_executed_by_root=False,execution_sha256=execution_sha,native_stages=stages,
            whole_State_bytes=3504,whole_FX_bytes=512,whole_Runtime_CPU_bytes=40,whole_pages=21,checkpoints_per_qualifying_row=44,
            source_identity_bytes=2086,new_compiled_source_bytes=0,reused_heap_source_bytes=84,reused_selector_probe_source_bytes=86,
            qualifying_executed_source_bytes=192,new_guest_objects=0,prior_guest_objects_preserved=38,
            qualifying_source_PCs=59,qualifying_source_accesses=35,qualifying_source_CALLs=5,qualifying_genuine_source_RETs=3,
            separate_API_return_reads=2,API_output_DWORDs_per_row=37,API_output_bytes_per_row=148,
            original_API_internals_equivalence=False,manifest_dependent_output_universal_equivalence=False,
            native_version_fields_and_BOOL_witness_drives_source=True,synthetic_API_response_used=False,
            host_source_execution_stores=0,State_projection='EIP only',generic_Runtime_CPU_preserved=True,
            undefined_AF_universal_original_equivalence=False,GetVersionExA_executed=passed,HeapCreate_executed=passed,
            host_heap_cleanup=passed,ordinary_selector_RET_sequences=ordinary_returned,
            ordinary_environment_frontier_sequences=len(rows)-ordinary_returned,environment_API_called=False,
            heap_mode_global_published=ordinary_returned>0,heap_initializer_RET=ordinary_returned>0,
            ordinary_initializer_RET_sequences=sum(row['heap_initializer_RET'] for row in rows),
            fragment_caller_executed=False,full_heap_allocator_initialized=False,heap_initialized=False,locale_initialized=False,
            argument_initialization_complete=False,original_attach_proved=False,main_initializer_count=27,
            lower_stack_original_observed=False,original_guard_stack_growth_proved=False,TIB_and_Policy_changed=False,
            ordinary_game_launched=False,original_executed=False,author_expected_model_imported=False,
            AFTER_machine_state_used_as_seed=False,whole_M4_complete=False,source_commands=commands+heap_commands,
            files=F.PHYSICAL,physical_closure=closure,seconds=(time.perf_counter_ns()-started)/1e9)
        publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
        if passed:
            F.pin(out/'report.json');publish_bytes(out/'pins.json',(json.dumps(dict(files=F.PHYSICAL),indent=2)+'\n').encode())
        print(json.dumps({k:v for k,v in report.items() if k not in ('files','rows','source_commands','native_stages')}))


if __name__=='__main__': main(*sys.argv[1:])
