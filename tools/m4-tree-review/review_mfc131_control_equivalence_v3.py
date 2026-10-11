"""Join the previously proven common component to current strict control results."""
from pathlib import Path
import hashlib, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
parent = R / 'tools/m4-tree-review/review_mfc131_control_equivalence_v2.py'
assert hashlib.sha256(parent.read_bytes()).hexdigest() == '4a609ae2d5f2fc7c9b2d2e934bcc4f4b98a7708393bbb54edb846bb1ca8dbfad'
text = parent.read_text()
old = "    assert positive['inputs']==controls['inputs'],'Exact same source/role/pointer/CRT/TIB contract'"
new = """    semantic = receipt(R/'reports/m4-mfc1168-native/connected-controls-verification-r5/report.json','23d10d824ce9d6b3ebfa6b57a2f8efcf71a00e385b66254063318b7b04a75a5b')
    execution = receipt(semantic['execution'], semantic['execution_sha256'])
    assert semantic['execution_sha256'] == 'fefde7d6702410cda8d2b5092935e67507474a4605a149056a819f1064ac38bd'
    assert execution['admission_review_sha256'] == '5d00fed2edf454249336fe29dd61592d3e7ab8cbce82003347dae0cbdf8a0527'
    checker = pin(R/'tools/m4-mfc1168-native/verify_connected_controls_v5.py','5b304d861fe11bbae7f14669b6b3742ee8b461fd1b82e9d9d5f3212ec484ce26')
    assert semantic['files'][str(checker)] == files[str(checker)]
    checker_prep = receipt(R/'reports/m4-mfc1168-native/connected-controls-checker-preparation-r5/report.json','98daffb1a170fc7d54d7ad136d85b2a3b31806622c49e1f9a211360e2f998279')
    assert checker_prep['files'][str(checker)] == files[str(checker)]
    assert semantic['counts']['actual_precise_denials'] == semantic['counts']['actual_unchanged_poisoned_retries'] == 24
    assert semantic['raw_exports_all_logical_entries'] and semantic['raw_export_readers_closed'] and semantic['all_bounded_readers_closed']
    cases_path = R/'reports/m4-mfc1168-native/connected-controls-verification-r5/causal-controls.json'
    cases = json.loads(pin(cases_path,semantic['files'][str(cases_path)]).read_bytes())
    assert len(cases) == 24
    for case in cases:
        assert case['complete_private_retry_compared'] and case['attempted_mutation_source_authored'] and not case['rejected_local_read_payload_observed']
        if case['mode'] == 11:
            provenance = case['source_refusal_API_provenance']
            assert provenance['source_argument'] == 0 and provenance['admitted_argument'] == 3
            assert provenance['actual_source_API_records'] == 0 and provenance['source_API_entered'] is False
            assert len(case['source_access_prefix']) == 17
            assert 'Typed guest TLS index3/borrowed CS24 argument' in case['reason']
    pin(parent)
""" + old
assert text.count(old) == 1
text = text.replace(old, new)
exec(compile(text, str(parent), 'exec'), globals())
