"""Seal the independently reviewed, bounded actual CRT matherr composition."""
import hashlib,json,sys,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main(foundation,out):
    assert foundation.parent==out.parent==ROOT/'reports/m4-crt-entry-matherr' and not out.exists();out.mkdir();pins={}
    def pin(p,h=None):
        p=Path(p).resolve();v=sha(p);assert h is None or v==h,str(p)
        assert str(p) not in pins or pins[str(p)]==v,str(p);pins[str(p)]=v;return p
    def receipt(path,name='report.json'):
        r=json.loads(pin(path/name).read_text(encoding='utf-8-sig'));assert r['passed']
        for p,h in json.loads(pin(path/'pins.json').read_text())['files'].items():pin(p,h)
        return r
    try:
        build=ROOT/'reports/m4-crt-entry-matherr/build-r3';b=json.loads(pin(build/'build.json').read_text(encoding='utf-8-sig'));assert b['passed']
        for group in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
            for p,h in b[group].items():pin(p,h)
        execution=receipt(out.parent/'root-execution-r2','execution.json')
        model=receipt(out.parent/'root-model-r4')
        review=receipt(foundation)
        joint=receipt(ROOT/'reports/m4-joint-startup27/root-acceptance-r1')
        assert execution['native_executed_by_root'] and execution['positive_cases']==48 and execution['causal_controls']==48
        assert model['positive_records']==model['causal_records']==48 and model['whole_pages']==14
        assert model['whole_State_bytes']==3504 and model['whole_FX_bytes']==512
        assert model['positive_writer_events']==4656 and model['positive_game_events']==1680 and model['positive_matherr_events']==240
        assert model['direct_host_boundary_pairs']==186 and len(model['observer_corruption_denials'])==11248
        assert not model['author_model_imported'] and not model['AF_undefined_representative_generalized']
        assert review['no_additional_blocker_to_bounded_gate'] and review['independent_compiled_causal']['closed']
        assert review['build_path']==str(build/'build.json')
        assert review['independent_compiled_causal']['checks']==494 and review['independent_compiled_causal']['scenarios']==34
        assert review['independent_compiled_causal']['direct_host_records']==68
        assert review['nonzero_host_legacy_metadata_records']==0 and review['direct_host_records']==186
        assert review['independent_compiled_causal']['nonzero_legacy_metadata_records']==68
        assert review['independent_compiled_causal']['actual_malformed_token_denials']==30
        assert not review['FDIV_page_overlap'] and not review['Runtime_r9_changed']
        assert joint['selected_joint_gate_accepted'] and joint['connected_roots']==27 and joint['remaining_nonzero_roots']==117
        # Independent read-only semantic audit of the exact source observers.
        observer=pin(ROOT/'tools/m4-crt-entry-matherr-root/observe.py','8a55f96c298f19ff1ccbe6c24a449378064b678cea07da3fd6aa83a79a58445f')
        source_model=pin(ROOT/'tools/m4-crt-entry-matherr-root/model.py','5bd21ddfc1ffef390a88891f60821ff055c32d73610fba7740d1f94688e0da32')
        leaf_ir=pin(ROOT/'reports/m4-crt-matherr/abi-r1/host.ll','6afb5776644c82629221ad44799e2ea7c0ce821258fc0413eb04e2819ca60a4c')
        assert not any(r['whole_M4_complete'] for r in (execution,model,review,joint))
        for p,h in list(pins.items()):assert sha(p)==h,p
        pin(__file__);pin(sys.executable);(out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py')
        report=dict(passed=True,date='2026-10-08',actual_CRT_matherr_registration_composition_accepted=True,
            build_path=str(build/'build.json'),root_execution_path=str(out.parent/'root-execution-r2/execution.json'),root_source_model_path=str(out.parent/'root-model-r4/report.json'),independent_foundation_path=str(foundation/'report.json'),
            callback_guest_address=0x51e7b0,callback_executed=False,next_required_direct_call=dict(source_PC=0x5ac431,target=0x5ac5a0,role='CRT floating-point control wrapper'),
            positive_compositions=48,causal_cases=48,whole_State_bytes=3504,separate_FX_bytes=512,owned_pages=14,writer_positive_events=4656,game_positive_events=1680,matherr_positive_events=240,source_identity_bytes=447,
            root_observer_corruption_denials=11248,independent_compiled_assertions=494,independent_compiled_fixtures=34,root_direct_host_pairs=186,independent_rich_host_pairs=68,
            source_model_read_only_audit=dict(passed=True,model_sha256=sha(source_model),observer_sha256=sha(observer),leaf_IR_sha256=sha(leaf_ir),source_only_BEFORE_seed=True,AND_flags_after_store=True,RET_partial_failure_order=True,CPU_State_distinction=True),
            host_boundary_repair='Full FX and legacy ENV guard spans the actual bool-returning invocation boundary including catch handlers; internal invoke guard is additional protection.',
            prior_claim_correction='The previous entry-data review overstated nonzero legacy metadata coverage: its 138 direct caller pairs had zero FIP/FDP/CS/DS/FOP. Their equality results remain bounded. This gate adds 68 deliberately populated hardware caller pairs and preserves the newly exposed failure.',
            connected_initializer_roots=27,total_nonzero_roots=144,remaining_nonzero_roots=117,entry_and_selected_table_composed_together=False,
            limits=['FDIV guest corpus remains twelve masked control words with empty TOP0 stack and two repetitions','Rich caller host fixtures cover depths0/1/3/7 and TOP3/7 with masked sticky status; broader host domains unproved','Three additional provider pages are exact raw source-backed section pages including final raw padding; complete DLL initialized process state unproved','Callback is stored as guest data; execution is unproved','Undefined AF receives explicit representative only, volatile XMM0-5 equality unclaimed','Original complete CRT entry, DLL attach, guest SEH, control/argument setup, full initializer table and native menus remain open'],
            frozen_runtime_and_component_objects_mutated=False,ordinary_game_launched=False,original_executed=False,M4_status='active',whole_M4_complete=False,physical_dependency_bindings=len(pins))
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json')
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(pins.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,bindings=len(pins),report_sha256=sha(out/'report.json'),connected_roots=27,next_target=hex(0x5ac5a0))))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(*[Path(p).resolve() for p in sys.argv[1:]])
