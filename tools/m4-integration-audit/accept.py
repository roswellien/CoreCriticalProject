"""Seal root acceptance of two separate bounded M4 integration advances."""
import hashlib,json,sys,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(out):
    assert out.parent==ROOT/'reports/m4-integration-audit' and not out.exists();out.mkdir(parents=True);pins={}
    def pin(p,h=None):
        p=Path(p).resolve();v=sha(p);assert h is None or v==h,str(p)
        assert str(p) not in pins or pins[str(p)]==v,str(p);pins[str(p)]=v;return p
    def receipt(relative,name='report.json'):
        d=ROOT/relative;r=json.loads(pin(d/name).read_text(encoding='utf-8-sig'));assert r['passed']
        for p,h in json.loads(pin(d/'pins.json').read_text())['files'].items():pin(p,h)
        return r
    try:
        entry_execution=receipt('reports/m4-crt-entry-data/root-execution-r1','execution.json')
        entry_model=receipt('reports/m4-crt-entry-data/root-model-r1')
        entry_source=receipt('reports/m4-crt-entry-data/independent-source-r1')
        joint_root=receipt('reports/m4-joint-startup27/root-acceptance-r1')
        joint_final=receipt('reports/m4-joint-startup27/independent-final-r1')
        assert entry_execution['native_executed_by_root'] and entry_execution['positive_cases']==48 and entry_execution['causal_controls']==24
        assert entry_model['records']==48 and len(entry_model['actual_compiled_causal_cases'])==24 and len(entry_model['observer_corruption_denials'])==56
        assert entry_model['writer_events']==4656 and entry_model['consumer_events']==1632 and entry_model['host_direct_boundary_records']==138
        assert entry_source['no_blocker_to_bounded_gate'] and entry_source['independently_checked_direct_host_records']==138 and entry_source['nonzero_before_legacy_metadata_records']==138
        assert joint_root['selected_joint_gate_accepted'] and joint_root['connected_roots']==27 and joint_root['remaining_nonzero_roots']==117
        assert joint_final['connected_count']==27 and joint_final['observer_corruption_denials']==7044 and joint_final['actual_original_phases']==1296 and joint_final['actual_native_phases']==2592
        assert len(joint_final['binary_audits'])==4 and all(v['private_probe_after_wrapper_capture'] for v in joint_final['binary_audits'])
        assert not any(r['whole_M4_complete'] for r in (entry_execution,entry_model,entry_source,joint_root,joint_final))
        for p,h in list(pins.items()):assert sha(p)==h,p
        pin(__file__);pin(sys.executable);(out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py')
        report=dict(passed=True,date='2026-10-08',initialized_FDIV_to_entry_gate_accepted=True,selected_initializer_gate_accepted=True,connected_initializer_roots=27,total_nonzero_roots=144,remaining_nonzero_roots=117,
            entry_next_required_import=dict(name='MSVCRT.dll!__setusermatherr',source_PC=0x5ac428,owning_game_IAT=0x5bb50c),
            entry_positive_cases=48,entry_causal_cases=24,joint_original_phases=1296,joint_native_phases=2592,joint_fault_scenarios=102,joint_actual_provider_checkpoints=48,
            entry_and_selected_table_composed_together=False,
            scope='Two separately accepted bounded integrations; full CRT/entry/table/application/menu path remains open.',
            limits=['Full entered partial-State semantics after joint fault not claimed','Old optimized ENV failure cause remains inferred','Undefined flags, volatile SIMD and reserved/dead FX retain admitted observation limits','Original full entry, DLL attach, SEH dispatch, 117 remaining nonzero roots and native menus unproved'],
            shared_frozen_runtime_or_component_objects_mutated=False,ordinary_game_launched=False,M4_status='active',whole_M4_complete=False,physical_dependency_bindings=len(pins))
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json')
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(pins.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,connected_roots=27,remaining=117,bindings=len(pins),report_sha256=sha(out/'report.json'))))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
