"""Root gate audit: rehash independent actual source/carry/failure receipts."""
import hashlib,json,sys,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-joint-startup27'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(out):
    assert out.parent==BASE and not out.exists();out.mkdir();pins={}
    def pin(p,h=None):
        p=Path(p).resolve();v=sha(p);assert h is None or h==v,str(p)
        assert str(p) not in pins or pins[str(p)]==v,str(p)
        pins[str(p)]=v;return p
    def read(directory, name='report.json', passed=True):
        p=BASE/directory;d=json.loads(pin(p/name).read_text(encoding='utf-8-sig'))
        assert d['passed'] is passed,(directory,name)
        q=p/'pins.json'
        for source,digest in json.loads(pin(q).read_text())['files'].items():pin(source,digest)
        return d
    try:
        paired=read('independent-repaired-paired-r1');controls=read('independent-controls-r3');checkpoint=read('independent-checkpoint-r1')
        assert paired['counts']==dict(native_phases=2592,source_events=35712,runtime_root_routes=2784,native_State_carry_boundaries=2496,original_phases=1296,hardware_carry_boundaries=1248,complete_sequences=48)
        assert paired['connected_roots']==27 and paired['source_fault_controls_accepted'] and not paired['full_CRT'] and not paired['ordinary_game_launched']
        assert paired['corruption_rejections']==1944 and paired['original_software_State_unobserved']
        assert controls['actual_records']==204 and controls['scenarios']==102 and controls['corruption_rejections']==3468 and controls['old_O2_ENV_loss_preserved']
        assert controls['complete_State_bytes']==3504 and controls['complete_owned_pages']==14
        assert checkpoint['actual_checkpoints']==48 and checkpoint['O0_O2_bridges']==96 and checkpoint['observer_corruption_rejections']==1632 and checkpoint['connected_roots']==27
        assert checkpoint['numeric_actual_table_slot']==0x5e016c and not checkpoint['debugger_legacyENV_metadata_observed'] and not checkpoint['original_software_State_observed']
        old=json.loads(pin(BASE/'controls-capture-r1/report.json').read_text());assert not old['passed'] and old['failure']
        pin(BASE/'boundary-derivation-r1/derivation.json')
        for p,h in list(pins.items()):assert sha(p)==h,p
        pin(__file__);pin(sys.executable)
        (out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py')
        result=dict(passed=True,selected_joint_gate_accepted=True,connected_roots=27,total_nonzero_initializer_roots=144,remaining_nonzero_roots=117,
            original_direct_sequences=48,original_phases=1296,native_O0_O2_sequences=96,native_phases=2592,whole_native_State_bytes=3504,whole_guest_pages=14,
            independent_source_events=35712,independent_root_nested_routes=2784,native_whole_State_carry_boundaries=2496,hardware_carry_boundaries=1248,
            actual_provider_return_checkpoints=48,actual_failure_control_records=204,failure_control_scenarios=102,independent_observer_corruption_denials=1944+3468+1632,
            old_O2_ENV_failure_preserved=True,old_failure_cause_proven=False,
            failure_acceptance='Exact first faults/source-prefix pages/routes, coherent raw failed View, owner cleanup and immutable corrected retries; no subsequent guest work. Full entered partial-State semantic equivalence and raw per-access fault event values are not claimed.',
            FP_scope='Twelve masked CW, TOP0/7 empty inputs, actual preceding selected roots and canonical numeric admitted carry. Full legacy ENV in direct original/native and direct host boundary; reserved/dead rawFX and undefined flags are scoped observations.',
            exclusions=['117 remaining nonzero initializer roots','Full CRT entry and actual complete _initterm table invocation','DLL attach and guest SEH dispatch','Full entered failed-State semantic equivalence','Native application, menus and gameplay','Volatile SIMD or reserved rawFX blanket equivalence'],
            ordinary_game_launched=False,full_CRT=False,whole_M4_complete=False,dependency_bindings=len(pins),receipts={n:str(BASE/n/'report.json') for n in ('independent-repaired-paired-r1','independent-controls-r3','independent-checkpoint-r1')})
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');pin(out/'report.json')
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(pins.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,connected_roots=27,remaining_nonzero_roots=117,bindings=len(pins),report_sha256=sha(out/'report.json'))))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
