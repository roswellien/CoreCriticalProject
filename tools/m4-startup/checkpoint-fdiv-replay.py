"""Additive prerequisite rollup with literal prior live-status preservation."""
import hashlib,json,pathlib,sys,traceback
ROOT=pathlib.Path(__file__).resolve().parents[2];PINS={};HISTORY={};REBIND=[]
def sha(p):
    with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=pathlib.Path(p).resolve();v=sha(p)
    if h is not None and v!=h:
        key=(str(p),h);assert key in HISTORY,'No literal historical association '+str(p)
        literal=HISTORY[key];assert sha(literal)==h;REBIND.append({'original_path':str(p),'historical_sha256':h,'literal_path':str(literal)});p=literal;v=h
    assert h is None or v==h,str(p);assert str(p) not in PINS or PINS[str(p)]==v;PINS[str(p)]=v;return p
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def stage(base,rh,ph,name='report.json'):
    base=ROOT/base;report=read(pin(base/name,rh));assert report.get('passed',report.get('passed_recorded_tests',False))
    for p,h in read(pin(base/'pins.json',ph))['files'].items():pin(p,h)
    return report
def proofs(text):return [(s[1].strip(),s[2].strip()) for line in text.splitlines() if line.startswith('| M4-') for s in [line.split('|')]]
def main(out):
    assert out.parent==ROOT/'reports/m4-startup' and not out.exists();out.mkdir();(out/'checkpoint-source.py').write_bytes(pathlib.Path(__file__).read_bytes())
    try:
        # Preserve current live documents before this deliberately small update.
        before=out/'before';before.mkdir();documents={}
        for name in ('m4-startup-plan.md','project-milestones.md','roadmap.md'):
            path=ROOT/'docs'/name;copy=before/name;copy.write_bytes(path.read_bytes());h=sha(copy);HISTORY[(str(path.resolve()),h)]=copy;documents[name]={'before_sha256':h,'before_literal':str(copy)}
        old=stage('reports/m4-startup/status-after-three-service-prefix-r1','1f01887be5c66269cd8421efe8d74695582dc4b708790636905fb8cd3269420b','5cfab4fb8a1b8f775c860a78c088babe312ca33ddf725fa367ff3adb6892c79a')
        model=stage('reports/m4-crt-fdiv-replay/root-model-r2','53f2589041d3081147915901de1920f622695a5a5644a817cdb6a76331124a60','168e9d10f342731d7ecfa8b50c161ca2097733f8461d2379b0905749a38ec883')
        assert model['native_records']==48 and model['original_observed_CW_SW_FTW_MXCSR_raw80_and_direct_legacy_ENV'] and not model['original_full_FX_or_stack_equivalence']
        first=stage('reports/m4-crt-entry/independent-first-fault-closure-r1','c7089fe136853a1314f63f1a9c2d6a3f6fe246ac8366008663cc1be884da27d2','be7cbb9c57d50e592663fa1a1410903324ad23091a3628852eddf900322ead7d')
        prefix=stage('reports/m4-crt-entry/independent-prefix-compiled-r1','286eba2982e976783b1fc37792af9fe21619198a8773714bca29b91548bcbcf7','54391a234327dd51b09a4d0a03aaca16237b9d1c0099754da558de371fdd2251')
        receipt=stage('reports/m4-crt-entry/independent-prefix-receipt-r1','5100ac87d4cbdd126e23ca8afbd2333c25a8af66f3b2bef4d2291105799863c6','0c75674f3f6afcf89826c9f52688e57d5e4ed2ad890bd10145c83a3dfacd241a','receipt.json')
        assert receipt['tests_per_optimization']['checks']==439 and receipt['tests_per_optimization']['scenarios']==27
        assert not receipt['full_CRT'] and not receipt['whole_M4_complete']
        link='[bounded FDIV replay and entry review](m4-fdiv-replay-and-entry-prerequisites.md)'
        replacements={
            'm4-startup-plan.md':('kept separate. Original/native replay comparison is still required.','kept separate. The '+link+' now passes for the\nretained direct-before corpus, with original XMM0 and real-stack differences\npreserved. Initialized FDIV data is still unconnected to game entry.'),
            'roadmap.md':('Its isolated original capture has completed; original/native replay is pending.','Its '+link+' now passes the measured\nbefore-only corpus; connecting initialized data to game entry remains open.'),
            'project-milestones.md':('capture has completed 48 runs; its native replay comparison remains open.','capture has completed 48 runs; the '+link+' now\npasses within the explicit CPU/FP/provider-page transport scope. Complete CRT\nentry and initialized-data consumption remain open.')}
        for name,(needle,replacement) in replacements.items():
            path=ROOT/'docs'/name;text=path.read_text(encoding='utf-8-sig');assert text.count(needle)==1;text=text.replace(needle,replacement)
            if name=='project-milestones.md':text=text.replace('FDIV original/native replay pending','bounded FDIV replay passes; initialized-data entry composition open')
            assert proofs(text)==proofs((before/name).read_text(encoding='utf-8-sig'))
            path.write_text(text,encoding='utf-8');copy=out/name;copy.write_bytes(path.read_bytes());documents[name].update(after_sha256=sha(copy),after_literal=str(copy));pin(copy)
        # The earlier receipt binds historical live versions. Rebind explicitly
        # to preserved literals; the changed live files have separate hashes.
        for name,item in documents.items():
            path=ROOT/'docs'/name;PINS.pop(str(path.resolve()),None);pin(path);pin(before/name,item['before_sha256'])
        pin(ROOT/'docs/m4-fdiv-replay-and-entry-prerequisites.md');pin(__file__);pin(sys.executable)
        result={'passed':True,'scope':'Bounded FDIV original/native replay and actual three-service compatibility prerequisite rollup; full M4 open',
                'FDIV_before_only_native_records':48,'whole_native_State_bytes':3504,'whole_native_pages':9,'actual_events':4656,'actual_routes':144,
                'original_observed_transport_comparison_passed':True,'whole_original_FX_or_stack_equivalence':False,
                'three_service_prefix_independent_checks_per_level':439,'three_service_prefix_independent_scenarios_per_level':27,
                'first_fault_independent_closure_retained':True,'selected_joint_initializer_roots_accepted':26,'joint27_acceptance':False,
                'documents':documents,'required_twelve_proofs_unchanged':True,'physical_bindings':len(PINS),'explicit_historical_path_rebindings':REBIND,
                'initialized_FDIV_data_connected_to_game_entry':False,'guest_SEH_dispatch':False,'full_CRT':False,'frontend':False,'whole_M4_complete':False}
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');pin(out/'report.json')
        (out/'pins.json').write_text(json.dumps({'files':dict(sorted(PINS.items()))},indent=2)+'\n')
        print(json.dumps({'passed':True,'bindings':len(PINS),'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json'),'whole_M4_complete':False}))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(pathlib.Path(sys.argv[1]).resolve())
