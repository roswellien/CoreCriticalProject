"""Freeze all current131 acceptance identities and complete measured facets.

This only prepares a reviewable configuration. A separate agent reviews its
actual evidence graph, then acceptance freshly rehashes the complete physical
union, including every accepted130 dependency and current capture part.
"""
from pathlib import Path
import hashlib, json, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
GATES = {
 'parent': ('reports/m4-joint-startup130-root/acceptance-r1/report.json', '12215395619ea72ee1a587763112bc3a2ed9aad15c9c99a5697f69c9658429aa'),
 'native_preparation': ('reports/m4-joint-startup131/preparation-r1/report.json', '2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25'),
 'native_build': ('reports/m4-joint-startup131/build-r1/build.json', '6381e7288fcea6ece0c2b8b4420d6daf4e5aaa616484b40498589b4f869fcca5'),
 'native_prelaunch': ('reports/m4-tree-review/joint131-prelaunch-r2/report.json', '20245da873b39e5a7a029f7fc5e20ffe0995ff88962b21917387678523491568'),
 'native_execution': ('reports/m4-joint-startup131-root/execution-r1/report.json', 'e250499a23537e21a206989f1dc9f1db2e40faae57840daa3b7cd4bb8d3a7a57'),
 'original_preparation': ('reports/m4-startup131-original/preparation-r4/report.json', '1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb'),
 'original_build': ('reports/m4-startup131-original/build-r3/build.json', 'f7a2b920c80f1d38f3d0880400ca651585086e3e263864f28efb49965e900f9d'),
 'original_prelaunch': ('reports/m4-tree-review/original131-prelaunch-r4/report.json', 'e5a09a7c7771c0c7f99cc907000ca999903e21b87d1342160684f237452608ed'),
 'original_execution': ('reports/m4-startup131-original/execution-r1/report.json', '189e6c9e1cd3bfe910698984b8b97cdf68c2e61b3704f444ba69a187f888aac4'),
 'original_validation': ('reports/m4-startup131-original/validation-r2/report.json', '9f3dc23c2b4f4eb5375882bb143d09f7caeb233a1d08d7b57373c606361ba07f'),
 'original_source': ('reports/m4-startup131-original/source-r2/report.json', '203d63def625e83cab7b2bebb274747825e888f0a2bc3b5f1331a4560055e910'),
 'original_source_review': ('reports/m4-tree-review/original131-mfc-source-r1/report.json', '83cfbaa509f99ca210dee80e139f015ed4dae27fe225c866d78a126205a264ab'),
 'original_old_source': ('reports/m4-startup131-original/inherited-source-r1/report.json', '5e97e47bfc1f05e709b30a4564403bcd84b2f5db18ebe86aea2346c4ddd46983'),
 'original_old_source_review': ('reports/m4-tree-review/original131-combined-review-r1/report.json', '367121f63da9304f4269f7225d6a9dfef83406efb2e4fea77cf2239e99df9089'),
 'source_preparation': ('reports/m4-joint-startup131-source/preparation-r6/report.json', 'fb90b0dc1d47b9fc89878049100a957d10ad6638bc718e8eff32b04ad861b6f8'),
 'source_preflight': ('reports/m4-tree-review/joint131-source-preflight-r4/report.json', 'efba70d0a02bb89fd95f87eb4707f138e48444b4cb8cc076389c80bec32ad2f2'),
 'source_legacy_flags': ('reports/m4-joint-startup131-source/legacy-flags-r4/report.json', '7cc979cff71ae061dc81a425339960a14557e66a7b150d6ad7dcde00f1031c9a'),
 'source_provider': ('reports/m4-joint-startup131-source/combined-source-provider-r2/report.json', 'e520d40b74a9e32dbe8102ebf892f3fd76139ae16d7622c2fdd6713eb520b86d'),
 'source_provider_review': ('reports/m4-tree-review/provider131-review-r1/report.json', 'ecdffbd9c4f9966f7c532275d798cb0872bc28285efc0a0fcdaba8ddb315a6cc'),
 'source_new_mfc_review': ('reports/m4-tree-review/joint131-mfc-source-r1/report.json', 'b17035122d54459cce5ba7aa7612cc73413933ee0cdb1519cdbe167b2a5b0660'),
 'source_closure': ('reports/m4-tree-review/source131-closure-r1/report.json', '95b3c1963236d6ea7eeb3a516b7f1c86f5016110ad1fea12c931fa18511a844b'),
 'pair_preparation': ('reports/m4-startup131-paired/comparer-preparation-r2/report.json', '20f5156a55099292b90ff03c3ea0c13a5e604bf604eed4c515eaa961506d2cdd'),
 'pair_policy_review': ('reports/m4-tree-review/paired131-preparation-review-r2/report.json', '3c863aed6f6bed096b6ec9f7fa705f09f6fb7ce63b0f3b8de4fe48377c740f54'),
 'loaded_input_relation': ('reports/m4-tree-review/loaded-input131-r1/report.json', '53797b98b49fb29fd1a5bb3ee28b467ae1212ca0d1adca997ce497dc511269c3'),
 'paired': ('reports/m4-startup131-paired/paired-r1/report.json', '00b2a9a0c5bb5e61c6943dfcd65bbe1d8e044dda3a83ebc608d2e6292efa78d4'),
 'paired_review': ('reports/m4-tree-review/paired131-review-r2/report.json', 'ccbbb146bca849238458afc7587dd4695e9bd4247f41ade7b81b1a28d3efb655'),
 'controls_preparation': ('reports/m4-mfc1168-native/connected-controls-preparation-r6/report.json', '0a45415c36b76ae10669f9ecbb8289fac4878b9e564f33212128a5c22ac12136'),
 'controls_build': ('reports/m4-mfc1168-native/connected-controls-build-r5/build.json', '7e7ea6be02ed299ff6fc3171e9fa119da6fd7e8aa866d7626c912bf8aefaac1d'),
 'controls_prelaunch': ('reports/m4-tree-review/mfc1168-controls-prelaunch-r9/report.json', '5d00fed2edf454249336fe29dd61592d3e7ab8cbce82003347dae0cbdf8a0527'),
 'controls_execution': ('reports/m4-mfc1168-native/connected-controls-execution-r3/report.json', 'fefde7d6702410cda8d2b5092935e67507474a4605a149056a819f1064ac38bd'),
 'controls': ('reports/m4-mfc1168-native/connected-controls-verification-r5/report.json', '23d10d824ce9d6b3ebfa6b57a2f8efcf71a00e385b66254063318b7b04a75a5b'),
 'controls_review': ('reports/m4-tree-review/mfc131-controls-review-r2/report.json', '136c015cf1d3d332e84752232dba7b83b56b82b657892465575a713ef9e39748'),
 'controls_equivalence': ('reports/m4-tree-review/mfc131-controls-equivalence-r3/report.json', '1cde64c3cde59267cb1643c20245edb61a54465ec44230854fb8e147d692e3e2'),
}

def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()

def facets(row):
    result = {}
    for key, value in row.items():
        if type(value) in (bool, int) and not any(s in key.lower() for s in ('elapsed', 'time', 'duration')): result[key] = value
        elif key.endswith('_sha256') and isinstance(value, str): result[key] = value
    for group in ('counts', 'provider_counts'):
        for key, value in row.get(group, {}).items():
            if type(value) in (bool, int): result[group + '.' + key] = value
    if len(result) < 2: result['scope'] = row['scope']
    assert len(result) >= 2 and result['passed'] is True
    return result

def main(name):
    out = ROOT / 'reports/m4-joint-startup131-root' / name
    assert not out.exists(); out.mkdir(parents=True)
    gates = {}
    for label, (relative, identity) in GATES.items():
        path = ROOT / relative; assert sha(path) == identity, label + ' exact current receipt'
        row = json.loads(path.read_bytes()); assert row['passed'] is True
        gates[label] = dict(path=relative, sha256=identity, equal=facets(row))
    spec = out / 'review-specification.json'
    spec.write_text(json.dumps(dict(scope='Current131 full startup inventory acceptance', mandatory_gates=33, accepted_parent_roots=130, inserted_root='0x005AE3E4', physical_slot='0x005E0040', inserted_phase=13, registration_callbacks=101, raw_only_independent_reviews=True, no_metadata_hash_cache=True, fresh_all_current_and_historical_parts=True, all_current_semantic_guards_retained=True, no_whole_game_or_menu_credit=True, checklist=['Exact typed evidence facets', 'Independent current evidence edges', 'Complete original and O0/O2 source/provider/pair extents', 'All24 strict controls and physical raw retry/resource joins', 'Current raw export provenance and bounded reader closure', 'All accepted130 dependencies retained', 'Fresh full physical manifest verification']), indent=2) + '\n')
    config = out / 'configuration.json'
    config.write_text(json.dumps(dict(gates=gates, configuration_source=str(Path(__file__).resolve()), configuration_source_sha256=sha(__file__), review_specification=str(spec), review_specification_sha256=sha(spec)), indent=2) + '\n')
    print(json.dumps(dict(path=str(config), sha256=sha(config), gates=len(gates), predicates=sum(len(g['equal']) for g in gates.values()))))

if __name__ == '__main__': main(sys.argv[1])
