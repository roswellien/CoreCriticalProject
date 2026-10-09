"""Execute a finite independent native corpus directly into strict archives."""
import json
from pathlib import Path
import sys
import time
import traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import normalized,verify_manifest
from paths import publish_bytes,workspace_path
from stages import run_stage,verify_stage
from transport import DirectSet,read,need

def main(build_path,build_sha,directory):
    start=time.perf_counter();out=workspace_path(directory,reports=True)
    need(out.parent==ROOT/'reports/m4-crt-allocation-review' and not out.exists(),'Fresh independent native report')
    out.mkdir(parents=True);files={};levels={};launched=completed=0;passed=False;closure=None
    def pin(p,expected=None):
        p=Path(p).absolute();actual=sha_file(p);need(expected is None or actual==expected,'Literal current native input: '+str(p))
        key=normalized(str(p));need(key not in files or files[key]==actual,'Conflict-free physical association');files[key]=actual;return p
    try:
        build=read(pin(build_path,build_sha));need(build['passed'] and not build['native_executed'],'Successful independent compilation only')
        for category in ('sources','tools','entry_objects','libraries','compiler_read_headers','artifacts'):
            for p,digest in build[category].items():pin(p,digest)
        pin(build['fixture_report'],build['fixture_report_sha256']);pin(build['author_build'],build['author_build_sha256']);pin(build['writer_build'],build['writer_build_sha256'])
        game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
        provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
        pack=pin(ROOT/'reports/m4-crt-fdiv/native-derived-r1/pack.bin','fd9a41958ac2edf5e1c3f118ec24a59e2df295d94ac1d1b1346deb3cbc46aa80')
        before=pin(ROOT/'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin','4294b8d926966c04d305b6e22a9166f08a328f4cc1c62984b72677fe83dd638a')
        for p in (Path(__file__),Path(__file__).parent/'transport.py',Path(sys.executable)):pin(p)
        for name in ('capture_bundle.py','paths.py','stages.py','manifests.py'):pin(ROOT/'tools/m4-pipeline'/name)
        for level in ('O0','O2'):
            worker=pin(build['workers'][level]);obj=pin(ROOT/f'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-{level}.obj')
            captures=out/('native-'+level);stage=out/('run-'+level);argv=list(map(str,(worker,game,obj,provider,pack,before,captures)));launched+=1
            result=run_stage(argv,stage,timeout_seconds=180,required_outputs=[captures/'transport.json'],inputs=list(files))
            stage_sha=sha_file(pin(stage/'stage.json'));verify_stage(stage,stage_sha)
            for name in ('stdout.bin','stderr.bin'):pin(stage/name)
            need(result['passed'] is True,'Actual independent native worker completed: '+level);completed+=1
            verify_start=time.perf_counter();bundle=DirectSet(captures/'transport.json',pin)
            try:
                need(bundle.data('COMPLETE')==b'COMPLETE' and 'INCOMPLETE' not in bundle.entries,'Complete semantic corpus, no partial success')
                summary=json.loads(bundle.data('review-controls.json'))
                need(summary['passed'] and summary['rows']==24 and summary['ordinary_rows']==12 and summary['independent_control_rows']==12 and not summary['game_executed'] and not summary['original_executed'],'Fixed independent authored row scope')
                inventory=out/('inventory-'+level+'.json');publish_bytes(inventory,(json.dumps({'files':dict(sorted(bundle.records.items()))},indent=2)+'\n').encode());pin(inventory)
                levels[level]={'worker':str(worker),'argv':argv,'native_stage':str(stage),'native_stage_sha256':stage_sha,'transport_manifest':str(bundle.path),'transport_sha256':sha_file(bundle.path),'inventory_path':str(inventory),'inventory_sha256':sha_file(inventory),'logical_files':len(bundle.entries),'payload_bytes':bundle.value['payload_bytes'],'archive_parts':len(bundle.bundles),'native_and_emission_seconds':result['elapsed_seconds'],'emit_seconds':bundle.value['emit_seconds'],'finalize_parts_seconds':bundle.value['finalize_parts_seconds'],'strict_verification_seconds':time.perf_counter()-verify_start,'compiled_checks':summary['checks'],'token_units':summary['token_units'],'wrong_thread_units':summary['wrong_thread_units']}
            finally:bundle.close()
        closure=verify_manifest(files);passed=True
    except BaseException:
        publish_bytes(out/'failure.txt',traceback.format_exc().encode());raise
    finally:
        report={'passed':passed,'scope':'Independent native allocation fixtures; source semantics/hardware admitted separately by raw checker','build_path':str(Path(build_path).absolute()),'build_sha256':build_sha,'native_executed':launched>0,'native_stages_completed':completed,'native_rerun':False,'native_scenarios':48 if passed else 0,'levels':levels,'files':files,'current_physical_closure':closure,'game_launched':False,'original_executed':False,'full_CRT_complete':False,'whole_M4_complete':False,'per_record_physical_files':0,'later_copy_or_pack_passes':0,'elapsed_seconds':time.perf_counter()-start}
        publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode());print(json.dumps({k:v for k,v in report.items() if k not in ('files','levels')}))

if __name__=='__main__':main(*sys.argv[1:])
