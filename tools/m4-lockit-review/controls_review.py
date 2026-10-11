"""Bounded review of sealed causal execution, validator and canonical lineage.

This receipt reviews the actual control proof and its current code identity.
It never claims to repeat the archived raw machine comparison, and requires
a separate agent's light tool/receipt audit before becoming an acceptance gate.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-lockit-review'


def need(value, message):
    if not value: raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(other_agent_review, name):
    out = BASE / name; need(not out.exists(), 'Fresh causal receipt review'); out.mkdir(parents=True)
    pins = {}; passed = False; counts = Counter(); causes = []
    def pin(path, digest=None):
        path = Path(path).resolve(); actual = sha(path)
        need(digest is None or actual == digest, 'Exact bounded causal input ' + str(path))
        need(str(path) not in pins or pins[str(path)] == actual, 'Immutable current causal input')
        pins[str(path)] = actual; return path
    def read(path, digest=None): return json.loads(pin(path, digest).read_bytes())
    try:
        pin(__file__)
        validation = read(BASE / 'controls-validation-r4/report.json',
            '1f37a6d0d2fd9fd9dfd812920c710c4717edf6e6cfb4e2f559b4d59fdf6ca129')
        execution = read(BASE / 'controls-execution-r4/report.json',
            'a877a33d14107c854256b7964de180015033c140c178f8832d9ee28d7eef18a2')
        build = read(BASE / 'controls-build-r5/build.json',
            'a78ad98f6d724c7b020a807b09eb60e3f94a685a02ec896a5635622b68b2ab7f')
        sources = read(BASE / 'controls-source-r2/report.json',
            'd51b930bf3bc395b3d813942bf40807f3099786ab2b485f417765680112a62ba')
        canonical_execution = read(ROOT / 'reports/m4-joint-startup124-root/execution-r2/report.json',
            'e0ca3ce031afbcde80ff84c0968d30850972625d2f6d8e2a8c8934386a2e7732')
        canonical_build = read(ROOT / 'reports/m4-joint-startup124/build-r4/build.json',
            '05a198d319f2e3ee2259b998a8989db23df0b20afd40416fb185e7a0b1d17c30')
        joint = read(ROOT / 'reports/m4-joint-startup124/preparation-r5/report.json',
            '7a2e383ab47bdb668e56181cdc3eec1c75ebf03437e5f9b9ac675861370a85c7')
        native = read(ROOT / 'reports/m4-lockit-native/preparation-r5/report.json',
            '965ea738333677c308749108b7f0b211772e89d4dd5e2ed14ea561cb63d0bdc1')
        integration = read(BASE / 'native-integration-r5/report.json',
            'b05f1e1f5c820d6d209ef1eb1176b29c098860eb06acef9d03de26a1d1f71c37')
        need(all(report['passed'] for report in (validation,execution,build,sources,
             canonical_execution,canonical_build,joint,native,integration)), 'All exact current causal prerequisites')
        need(execution['build_sha256'] == sha(BASE / 'controls-build-r5/build.json') and
             build['parent_build_sha256'] == canonical_execution['build_sha256'] ==
             sha(ROOT / 'reports/m4-joint-startup124/build-r4/build.json') and
             Path(build['preparation']).resolve() == (ROOT / 'reports/m4-joint-startup124/preparation-r5/report.json').resolve(),
             'Actual causal and canonical workers share same exact current native candidate')
        need(not build['source_bodies_modified'] and not build['API_response_injection'] and
             execution['native_executed'] and not execution['source_bodies_modified'] and
             not execution['API_response_injection'] and not execution['initializer_credit'] and
             not validation['initializer_credit'], 'Actual controls test unchanged native bodies and genuine APIs')
        other = read(other_agent_review)
        need(other['passed'], 'Separate agent causal tool/receipt review passed')
        # Audit only bounded executed sources and receipts, never inherited capture files.
        for path, digest in validation['files'].items():
            physical = Path(path)
            if physical.suffix in ('.py','.hpp','.inc') and (
                 'm4-lockit-review' in path or 'm4-container-controls' in path):
                pin(path, digest); counts['bound_causal_tool_sources'] += 1
        for report in (sources,):
            for path, digest in report['files'].items(): pin(path, digest)
        source_hooks = pin(BASE / 'controls-source-r2/hooks.hpp',
            'eabd3442a25c71ce8c6ec18415a44e381ae86f51160e58c55140cfee3d7f9c63')
        source_fixture = pin(BASE / 'controls-source-r2/fixture.inc',
            '9a857d5a19ffae1fb2c8af4c3b6dbf5c2684f68b5b4b14142967f139d04b43a9')
        need(source_hooks.read_bytes() == pin(BASE / 'controls-build-r5/hooks.hpp').read_bytes(),
             'Compiled fixture includes exact reviewed actual mutation hooks')
        hooks = source_hooks.read_text(encoding='utf-8'); fixture = source_fixture.read_text(encoding='utf-8')
        need('api[2]!=0x7810a30b' in hooks and 'api[3]!=0x78146198' in hooks and
             'api[4]!=pc' in hooks and 'trigger_api=api' in hooks,
             'Mutation triggers actual target CPU and separately retained genuine source API site')
        restore = fixture.index('(void)invoke(t);mw34_lockit_controls::restore_actual();')
        cleanup = fixture.index('c.registry().finish();')
        need(restore < cleanup and 'restore_resource->RecursionCount^=1' in hooks and
             'std::memcpy(restore_resource,resource_before.data(),40)' in hooks,
             'Real held native40 mutation restored physically after guard refusal before any real cleanup API')
        need('Context c(' in fixture and 'attempt(c,w,0,0)' in fixture and
             'c.registry().test_hook=nullptr;attempt(c,w,1,0)' in fixture,
             'Same actual Session reused for closed/poisoned refusal with mutation disabled')
        need('sample.state_before==sample.state_after&&sample.fx_before==sample.fx_after&&sample.cpu_before==sample.cpu_after' in fixture,
             'Whole actual State/FX/CPU retry conservation required by worker itself')
        causes_path = BASE / 'controls-validation-r4/causes.json'
        causes = read(causes_path, validation['files'][str(causes_path.resolve())])
        need(len(causes) == 30 and {(row['level'],row['case']) for row in causes} ==
             {(level,case) for level in ('O0','O2') for case in range(1,16)},
             'Each of15 actual interventions refused under both optimization levels')
        for row in causes:
            case = row['case']; effect = row['actual_intervention']; reason = row['reason']
            need(len(effect) == 8 and reason and row['point'] == (41 if case in (11,12) else 40),
                 'Actual indexed mutation point/refusal reason')
            if case <= 3:
                need(effect[0:4] == [1,0x78145658,2,(0,1,3)[case-1]] and
                     'generation and recursive depth' in reason, 'Genuine state2 domain causal refusal')
            elif case in (4,5,6,7):
                addresses = {4:0x78145640,5:0x5bb4f8,6:0x78146198,7:0x7810a290}
                need(effect[0] == 1 and effect[1] == addresses[case] and effect[2] != effect[3],
                     'Actual source CS/game import/provider import/physical prefix mutation')
                if case == 5:
                    need('named Lockit import projection' in reason and row['source_prefix_rows'] > 130,
                         'Changed already-read game import refuses at next actual source read after completed first-root pair')
            elif case in (8,9,10,11):
                need('private resource/source witnesses' in reason, 'Private actual witness mutation causes observer guard refusal')
            elif case == 12:
                need(effect[0] == 6 and effect[1] > 0xffffffff and effect[2:5] == [1,0,40] and
                     'actual native resource bytes' in reason, 'Physical actual native40 mutation refuses complete observer guard')
            elif case == 13:
                need(effect[0] == 4 and effect[4] == 512, 'Actual whole guestFX mutation')
            elif case == 14:
                need(effect[0] == 2 and effect[1] == 0x78145000 and effect[5] == 1,
                     'Actual current source CS page write permission refusal')
            elif case == 15:
                need(effect[0] == 3 and effect[2] == 0x78145640 and effect[3] == 0x78145644,
                     'Actual genuine stdcall stack argument causes refusal')
            counts['reviewed_actual_refusal_causes'] += 1
        expected = {'actual_attempts':64,'rich_caller_hardware_pairs':64,'real_cleanup_hardware_pairs':64,
            'same_session_refusals':32,'whole_retry_records':241328,'whole_current_pages':2080,
            'positive_four_root_runs':2,'positive_actual_Lockit_CALL_RET':16,'positive_actual_new_owners':16,
            'real_resources_deleted':160,'causal_targeted_refusals':30}
        for key, value in expected.items(): need(validation['counts'][key] == value, 'Exact complete raw causal proof count '+key)
        for level in execution['levels']:
            need(level['passed'] and level['level'] in ('O0','O2'), 'Both actual control workers completed')
            pin(level['stage'],level['stage_sha256']); pin(level['capture'],level['capture_sha256'])
            counts['actual_completed_control_workers'] += 1
        passed = True
    except Exception:
        (out / 'failure.txt').write_text(traceback.format_exc(), encoding='utf-8'); raise
    finally:
        receipt = dict(passed=passed,
            scope='Bounded current causal execution/build/native lineage and exact15 refusal causes under O0/O2; separately authored agent tool review required; original full raw causal validator remains authoritative for whole-record comparisons',
            native_capture_archive_opened=False, repeated_raw_capture_validation=False,
            validator_and_fixture_same_agent=True, separate_agent_review=str(Path(other_agent_review).resolve()),
            current_canonical_execution=str(ROOT / 'reports/m4-joint-startup124-root/execution-r2/report.json'),
            causal_proof=str(BASE / 'controls-validation-r4/report.json'),
            initializer_credit=False, original_API_volatile_EAX_equivalence_claimed=False,
            counts=dict(counts), files=pins)
        path = out / 'report.json'; path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(passed=passed,report_sha256=sha(path),counts=dict(counts))))


if __name__ == '__main__': main(Path(sys.argv[1]).resolve(),sys.argv[2])
