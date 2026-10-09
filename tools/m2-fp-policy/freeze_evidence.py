"""Bind bounded prior acceptance and new exclusion evidence without rebuilding."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/m2-fp-policy'
PINS=OUT/'final-pins.json'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok,reason):
    if not ok:raise AssertionError(reason)


def create():
    require(not PINS.exists(),'Refusing to replace an existing frozen identity bundle')
    pins={};families=[]
    def pin(path,expected=None):
        path=Path(path).resolve();key=str(path);digest=pins.get(key)
        if digest is None:digest=sha(path);pins[key]=digest
        require(expected is None or digest==expected,('identity mismatch',str(path),digest,expected))
        return path
    domain=json.loads(pin(ROOT/'tools/m2-fp-policy/profiles.json').read_text())
    for path,digest in domain['source_hashes'].items():pin(ROOT/path,digest)
    selected=[('control-store','x87-repair/store',12,'d939c3'),
              ('control-load-store','x87-repair/load-store',144,'d929d93ac3')]
    mapping={'numeric-add-sub':'x87-numeric','spill64':'x87-c1/spill64','fistp32':'x87-c1/fistp32',
             'mul64':'x87-store-c1/mul64','div64':'x87-store-c1/div64',
             'mul-special':'x87-store-c1/mul-special','div-special':'x87-store-c1/div-special',
             'mul-range':'x87-range/mul64','div-range':'x87-range/div64'}
    selected.extend((name,family,domain['profiles'][name]['cases'],domain['profiles'][name]['fixture_hex'])
                    for name,family in mapping.items())
    for name,family,count,code in selected:
        base=ROOT/'reports'/family;build_path=pin(base/'build.json');build=json.loads(build_path.read_text())
        report_path=pin(base/'comparison/report.json');report=json.loads(report_path.read_text())
        require(report['bounded_contract_passed'] is True and report['native_architectural_mismatches']==0,
                ('prior bounded profile not passed',name))
        require(report['total_cases']==count and sha(build_path)==report['metadata_sha256'],('prior profile/build binding',name))
        for path,digest in build['source_files'].items():pin(ROOT/path,digest)
        if 'tool_files' not in build:
            require(name in ('control-store','control-load-store'),'missing prior numerical tool identities')
        for path,digest in build.get('tool_files',{}).items():pin(path,digest)
        for path,digest in build['artifacts'].items():pin(base/path,digest)
        for key,path in build.items():
            if key.endswith('_path') and key[:-5]+'_sha256' in build:pin(path,build[key[:-5]+'_sha256'])
        provenance=json.loads(pin(build['repair_provenance_path'],build['repair_provenance_sha256']).read_text())
        for key,path in provenance.items():
            if key.endswith('_path') and key[:-5]+'_sha256' in provenance:pin(path,provenance[key[:-5]+'_sha256'])
        for field in ('semantics_component_hashes','link_libraries'):
            for path,digest in provenance[field].items():pin(path,digest)
        fixtures=[path for path,digest in build['artifacts'].items() if path.endswith('.bin') and digest==build['fixture_sha256']]
        require(len(fixtures)==1,('unambiguous original fixture artifact',name))
        fixture=pin(base/fixtures[0],build['fixture_sha256'])
        require(fixture.read_bytes()==bytes.fromhex(code),('fixture sequence changed',name))
        corpus=pin(report['corpus_path'],report['corpus_sha256'])
        if name in mapping:
            raw=corpus.read_bytes()
            require(struct.unpack_from('<8s4I',raw)==(b'MW34REQ1',1,count,64,32) and len(raw)==24+64*count,
                    ('full numerical corpus header/extent',name))
            observed=[struct.unpack_from('<I',raw,24+i*64+40)+(struct.unpack_from('<QQ',raw,24+i*64+48)) for i in range(count)]
            expected={(cw,a,b) for cw in domain['control_words'] for a,b in domain['profiles'][name]['vectors']}
            require(len(set(observed))==count and set(observed)==expected,('exact profile CW/vector corpus',name))
            require(int(report['observed_status_word_mask'],16)==domain['profiles'][name]['exit_status_mask'],
                    ('status observation mask changed',name))
        runs=[('reference',report['reference_run'])]+[(r['optimization'],r) for r in report['native_runs']]
        require({level for level,_ in runs}=={'reference','O0','O2'} and len(runs)==3,('worker levels',name))
        for level,run in runs:
            pin(run['command'][0],run['worker_sha256']);output=pin(run['output_path'],run['output_sha256'])
            result_raw=output.read_bytes();record_size=report['result_record_bytes'];width=32 if level=='reference' else 64
            require(struct.unpack_from('<8s4I',result_raw)==(b'MW34RES1',1,count,record_size,width) and
                    len(result_raw)==24+count*record_size,('saved whole result header/extent',name,level))
            saved_cases=run.get('cases',count);saved_count=len(saved_cases) if isinstance(saved_cases,list) else saved_cases
            require(run['exit_code']==0 and saved_count==count,('saved successful whole run',name,level))
            require(run['worker_sha256']==build['reference_sha256' if level=='reference' else 'native_'+level+'_sha256'],
                    ('worker/build binding',name,level))
        families.append({'profile':name,'prior_original_cases':count,'prior_native_O0_O2_cases':2*count,
                         'build_path':str(build_path),'build_sha256':sha(build_path),
                         'comparison_path':str(report_path),'comparison_sha256':sha(report_path),
                         'fresh_replay_in_this_supplement':name in ('fistp32','mul-special','div-special')})
    worker_path=pin(OUT/'worker-exclusions.json');worker=json.loads(worker_path.read_text())
    require(worker['positive_records_replayed']==4032 and worker['negative_run_count']==174 and
            worker['original_records_unchanged'] is True,'supplementary worker counts/preservation')
    for path,digest in worker['frozen_input_identities'].items():pin(path,digest)
    for run in worker['negative_runs']:
        require(run['exit_code']==1 and run['output_bytes']==0,'unsafe worker input did not reject')
        path=Path(run['output_path']);require(not path.exists() or path.stat().st_size==0,('unexpected negative result bytes',str(path)))
        pin(run['input_path'],run['input_sha256']);pin(run['fixture_path'],run['fixture_sha256'])
    for run in worker['positive_runs']:
        pin(OUT/run['kind']/(run['optimization']+'-positive.bin'),run['output_sha256'])
        require(run['exact_full_record_replay'] is True and run['output_sha256']==run['prior_output_sha256'],'positive replay disagreement')
    controls=json.loads(pin(OUT/'planning-controls.json').read_text())
    require(controls['profile_admissions']==8124 and controls['rejected_admission_calls']==186 and
            controls['separate_domain_identity_rejections']==1 and controls['failed_groups']==0 and
            controls['skipped_groups']==0 and controls['all_execution_remains_denied'] is True,'planning control outcomes')
    for path,digest in controls['source_identities'].items():pin(ROOT/path,digest)
    control_review=json.loads(pin(ROOT/'reports/x87-repair/independent-verification.json').read_text())
    require(control_review['bounded_control_word_contract_passed'] is True and control_review['mismatches']==0,
            'control independent review not passed')
    pin(ROOT/'reports/x87-repair'/control_review['fresh_toolchain_review'],control_review['fresh_toolchain_review_sha256'])
    numeric_review=json.loads(pin(ROOT/'reports/x87-numeric/independent-verification.json').read_text())
    require(numeric_review['bounded_numeric_contract_passed'] is True and numeric_review['mismatches']==0,
            'numeric independent review not passed')
    baseline=pin(ROOT/'reports/x87-state/baseline-failure/report.json',
                 '7b0c935743991ecef15174d7c3d343852a772d63e0fc6d52a2cecf3198c88f11')
    manifest=pin(ROOT/'reports/x87-state/baseline-failure/manifest.json',
                 '21d69c5a0539ba6166a8e49e3101b906dc9b66d5776371437a5b54073991c048')
    summary={'schema_version':1,'status':'bounded_policy_and_exclusions_recorded_live_state_pending',
             'prior_accepted_profiles':families,'prior_original_cases':sum(x['prior_original_cases'] for x in families),
             'prior_native_O0_O2_cases':sum(x['prior_native_O0_O2_cases'] for x in families),
             'fresh_supplement_original_O0_O2_records':4032,'fresh_supplement_negative_worker_runs':174,
             'planning_profile_admissions':8124,'planning_rejected_calls':186,'separate_domain_identity_rejections':1,
             'live_state_baseline':{'report_path':str(baseline),'report_sha256':sha(baseline),
                                    'manifest_path':str(manifest),'manifest_sha256':sha(manifest),
                                    'status':'preserved_failure_not_compatibility'},
             'live_state_final_acceptance':'pending','M2_completion_allowed':False,
             'scope':'Exact prior bounded domains plus supplementary exclusions; no wider FP compatibility claim.'}
    (OUT/'consolidated-evidence.json').write_text(json.dumps(summary,indent=2)+'\n')
    for path in [ROOT/'docs/m2-floating-point-policy.md',*sorted((ROOT/'tools/m2-fp-policy').rglob('*')),
                 *sorted((ROOT/'tests/m2-fp-policy').rglob('*')),*sorted(OUT.rglob('*'))]:
        if path.is_file() and '__pycache__' not in path.parts and path!=PINS:pin(path)
    for path,digest in pins.items():require(sha(Path(path))==digest,('identity changed during freeze',path))
    record={'schema_version':1,'status':'frozen_supplement_live_state_pending','files':pins,
            'identity_count':len(pins),'general_execution_allowed':False,'M2_completion_allowed':False}
    PINS.write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'pins_sha256':sha(PINS),'identity_count':len(pins),'accepted_profile_count':len(families),
                      'prior_original_cases':summary['prior_original_cases'],'live_state_final_acceptance':'pending'},indent=2))


def verify():
    record=json.loads(PINS.read_text());require(record['general_execution_allowed'] is False and
                                             record['M2_completion_allowed'] is False,'unexpected compatibility authorization')
    require(record['identity_count']==len(record['files']),'frozen identity count changed')
    for path,digest in record['files'].items():require(sha(Path(path))==digest,('frozen identity mismatch',path))
    worker=json.loads((OUT/'worker-exclusions.json').read_text())
    for run in worker['negative_runs']:
        path=Path(run['output_path']);require(not path.exists() or path.stat().st_size==0,('unexpected rejection result bytes',str(path)))
    print(json.dumps({'verified_identities':len(record['files']),'pins_sha256':sha(PINS),
                      'live_state_final_acceptance':'pending','general_execution_allowed':False},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--create',action='store_true');group.add_argument('--verify',action='store_true')
    args=parser.parse_args();create() if args.create else verify()
