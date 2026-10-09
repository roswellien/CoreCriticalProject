"""Seal the bounded actual CRT-entry/control composition and independent proof."""
import hashlib,json,sys,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main(out):
    assert out.parent==ROOT/'reports/m4-crt-entry-control' and not out.exists()
    out.mkdir();pins={}
    def pin(p,h=None):
        p=Path(p).resolve();name=str(p)
        if name in pins:
            assert h is None or h==pins[name],name
            return p
        v=sha(p);assert h is None or v==h,name;pins[name]=v;return p
    def receipt(path,name='report.json',h=None):
        r=json.loads(pin(path/name,h).read_text(encoding='utf-8-sig'));assert r['passed']
        manifest=path/'pins.json'
        if manifest.exists():
            files=json.loads(pin(manifest).read_text())['files']
        else:files=r['files']
        for p,v in files.items():pin(p,v)
        return r
    try:
        parent=out.parent;build=parent/'build-r6'
        b=json.loads(pin(build/'build.json','c91bf5dd0101595fd93f283712f8c7e629af606f513ae23879f95a3a25aa052a').read_text(encoding='utf-8-sig'));assert b['passed']
        for group in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
            for p,h in b[group].items():pin(p,h)
        # The inherited tool map omits llc, while its literal commands are saved.
        # Bind its current physical identity explicitly; no process file-open
        # attestation is inferred from this post-build association.
        commands=[v for v in b['commands'] if Path(v['program']).name=='llc.exe']
        assert len(commands)==2
        llc=pin(commands[0]['program'],'8576d294a52d9aef29be54d8ac7dd293ab612652bc7d12f2a3d8b8cadd28e168');assert commands[1]['program']==str(llc)
        for level,command in zip(('O0','O2'),commands):
            assert command['exit_code']==0
            assert command['arguments']==['-filetype=obj','-'+level,str(ROOT/'reports/m4-crt-entry-control/preparation-r5/control.ll'),'-o',str(build/f'control-{level}.obj')]
            pin(command['log_path'],command['log_sha256'])
        execution=receipt(parent/'root-execution-r1','execution.json','f479bb8d9e3927ae60d012da439f845b04e9fd5810d62bbade8eac78f0a878c6')
        model=receipt(parent/'root-model-r3',h='91d4f8129c39317498c3a56f963121854f9c434bb8d3b4725857c59a9da945ed')
        source=receipt(parent/'independent-source-r2',h='7b80b529739ed078777715ca104d96ad4c7e28a7333746e99d47a0446fbbc6e3')
        compiled=receipt(parent/'independent-compiled-review-r1',h='20ecd100514e697c06d3e7859a13cd7c93b29ba28ff405078a3a2e7a17148278')
        hardware=receipt(parent/'independent-compiled-observer-controls-r1',h='c618e518ceda1d2eaab7745d9cb8af6c8c22d378881222eb28f99df05594a6ff')
        audit=receipt(parent/'independent-root-model-audit-r1',h='e95cb0dbba7454a62e93dfe5893e42d8976f121e1fea7131645209af5a308965')
        previous=receipt(ROOT/'reports/m4-crt-entry-matherr/root-acceptance-r1',h='0a316ceb9372055d62bdc42d357a05a79ab30e9a36733048adf769a08037111e')
        joint=receipt(ROOT/'reports/m4-joint-startup27/root-acceptance-r1',h='ad1b2decb9d32d354120ae4ae53f4ebfd5db65bbec287cc9a8eb55f981b590a9')
        assert execution['native_executed_by_root'] and execution['positive_cases']==48 and execution['causal_controls']==72
        assert model['positive_records']==48 and model['causal_records']==72
        assert (model['whole_State_bytes'],model['whole_FX_bytes'],model['whole_pages'],model['source_identity_bytes'])==(3504,512,14,900)
        assert (model['positive_writer_events'],model['positive_game_events'],model['positive_matherr_events'],model['control_phase_events'],model['control_source_accesses'])==(4656,1824,240,624,2496)
        assert model['direct_host_boundary_pairs']==234 and len(model['observer_corruption_denials'])==51574
        assert not model['author_model_imported'] and not model['AF_undefined_representative_generalized']
        assert all(v['control_phase_events']==13 and v['control_accesses']==52 for v in model['positives'])
        assert source['findings']==[] and source['selected_initializer_count_unchanged']==27
        assert (compiled['checks'],compiled['scenarios'],compiled['direct_host_records'],compiled['nonzero_complete_legacy_metadata_records'],compiled['malformed_token_denials'])==(1676,72,144,144,144)
        assert (hardware['actual_hardware_raw80_before_fixtures'],hardware['actual_complete_legacy_tag_before_fixtures'],hardware['meaningful_corruption_denials'])==(144,144,548)
        observer=pin(ROOT/'tools/m4-crt-entry-control-root/observe.py')
        source_model=pin(ROOT/'tools/m4-crt-entry-control-root/model.py')
        assert audit['no_additional_blocker_for_current_bounded_corpus'] and not audit['findings']
        assert audit['root_model_sha256']==sha(source_model) and audit['root_observer_sha256']==sha(observer)
        assert audit['root_proof_sha256']==sha(parent/'root-model-r3/report.json')
        assert previous['actual_CRT_matherr_registration_composition_accepted']
        assert joint['selected_joint_gate_accepted'] and joint['connected_roots']==27 and joint['remaining_nonzero_roots']==117
        assert not any(v['whole_M4_complete'] for v in (execution,model,source,compiled,hardware,previous,joint))
        # Preserve the observer revisions, including both model failures.
        for folder in ('root-model-r1','root-model-r2'):
            pin(parent/folder/'failure.txt')
        for p,h in list(pins.items()):assert sha(p)==h,p
        pin(__file__);pin(sys.executable)
        (out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py')
        result=dict(passed=True,date='2026-10-08',actual_CRT_entry_control_composition_accepted=True,
            build_path=str(build/'build.json'),root_execution_path=str(parent/'root-execution-r1/execution.json'),root_source_model_path=str(parent/'root-model-r3/report.json'),
            independent_source_path=str(parent/'independent-source-r2/report.json'),independent_compiled_path=str(parent/'independent-compiled-review-r1/report.json'),independent_hardware_observer_path=str(parent/'independent-compiled-observer-controls-r1/report.json'),independent_root_model_audit_path=str(parent/'independent-root-model-audit-r1/report.json'),
            next_required_direct_call=dict(source_PC=0x5ac440,target=0x5ac598,return_PC=0x5ac445,role='actual _initterm thunk; first null-only interval [0x5E0248,0x5E024C)'),
            positive_compositions=48,causal_cases=72,whole_State_bytes=3504,separate_FX_bytes=512,owned_pages=14,source_identity_bytes=900,
            writer_positive_events=4656,game_positive_events=1824,matherr_positive_events=240,control_phase_events=624,control_source_accesses=2496,
            root_observer_corruption_denials=51574,root_direct_host_pairs=234,independent_compiled_assertions=1676,independent_compiled_compositions=72,independent_rich_host_pairs=144,independent_token_denials=144,independent_hardware_capture_denials=548,
            source_model_read_only_audit=dict(passed=True,model_sha256=sha(source_model),observer_sha256=sha(observer),BEFORE_only_seed=True,PUSH_failed_store_before_ESP_publication=True,post_RET_failed_closure_before_Runtime_CPU_publication=True),
            complete_control_provider_translated=True,provider_pages_reused_without_reset=True,control_IR_derivative='Exactly nine reversible symbol identifier changes; provider instruction bodies and bridge declarations unchanged; new O0/O2 COFFs compiled. Earlier accepted objects retained.',
            control_context_cleanup='BridgeAbort with typed current-owner checks; C++ catch paths clear active ownership and nesting; encompassing host FX/legacy ENV guard retained.',
            llc_post_build_physical_identity=dict(path=str(llc),sha256=sha(llc),recorded_commands=commands,process_file_open_attested=False),
            connected_initializer_roots=27,total_nonzero_roots=144,remaining_nonzero_roots=117,entry_and_selected_table_composed_together=False,
            limits=['Guest corpus is twelve masked CWs, empty TOP0 stack, two repetitions; full incoming FP domain unproved','Root hot/cold mutations 28/29 deny at the earlier FDIV integrity guard; separate compiled controls test late provider mutations','Rich hardware caller evidence covers populated metadata, distinct raw80 values, depths0/1/3/7, TOP3/7 and masked sticky status; broader host domain unproved','Failed provider POP-read ordering is outside this root fault corpus; no such partial-prefix equivalence is claimed','Undefined AF representative is not generalized; volatile XMM0-5 equality unclaimed','No new complete-original-CRT capture; source-model composition proof is distinct from prior isolated original/native component observations','Guest math-error callback execution, full DLL attach/SEH/CRT termination, full initializer tables, application startup and native menus remain open'],
            failed_observer_revisions_retained=True,prior_frozen_objects_mutated=False,ordinary_game_launched=False,original_executed=False,M4_status='active',whole_M4_complete=False,physical_dependency_bindings=len(pins))
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');pin(out/'report.json')
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(pins.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,bindings=len(pins),report_sha256=sha(out/'report.json'),next_target=hex(0x5ac598),connected_roots=27)))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(*[Path(p).resolve() for p in sys.argv[1:]])
