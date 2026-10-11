"""Current125 immutable preparation lineage and local iteration boundaries.

Metadata review excludes historical archive reads. Final acceptance still must
physically rehash the complete dependency union, including every retained archive.
"""
from pathlib import Path
import ast
import hashlib
import json
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
PINS = {}
REPORTS = {
    'parent_native': ('reports/m4-lockit-native/preparation-r5/report.json', '965ea738333677c308749108b7f0b211772e89d4dd5e2ed14ea561cb63d0bdc1'),
    'parent_joint': ('reports/m4-joint-startup124/preparation-r5/report.json', '7a2e383ab47bdb668e56181cdc3eec1c75ebf03437e5f9b9ac675861370a85c7'),
    'native': ('reports/m4-tree-native/preparation-r5/report.json', '9b6c7ab64a42dd67d26e73a7b4357063729085a808173b2818e704430386fef2'),
    'joint': ('reports/m4-joint-startup125/preparation-r4/report.json', '243b6f4c86dc2b966789e23faed4a10fe2efa62ba51f43e854fa843acde392e7'),
    'build': ('reports/m4-joint-startup125/build-r1/build.json', 'cdb5b9ca08e4e66dae276fa783bc59b5944e8435113fe9bb65a73cc53f218165'),
    'execution': ('reports/m4-joint-startup125-root/execution-r1/report.json', 'e384b6271c43f2e2e8d5a88f1a09e0940c85f111f2455744ad45de30ba73d8a8'),
}


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    path = Path(path)
    need(path.suffix.lower() != '.mwb', 'No archive reader in metadata review')
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def pin(path, expected=None):
    path = Path(path).resolve()
    value = sha(path)
    need(expected is None or value == expected, 'Exact physical input ' + str(path))
    need(str(path) not in PINS or PINS[str(path)] == value, 'Unchanged input identity')
    PINS[str(path)] = value
    return path


def main(kind, name):
    started = time.perf_counter()
    out = ROOT / 'reports/m4-tree-build-review' / name
    need(not out.exists(), 'Fresh additive boundary review')
    out.mkdir(parents=True)
    passed = False
    result = {}
    try:
        rows = {}
        for label, (path, expected) in REPORTS.items():
            rows[label] = json.loads(pin(ROOT / path, expected).read_bytes())
            need(rows[label]['passed'] is True, 'Passed preparation/build/run ' + label)
        pin(__file__)
        native, joint, build, execution = (rows[k] for k in ('native', 'joint', 'build', 'execution'))
        if kind == 'lineage':
            parent = rows['parent_joint']
            need(joint['native_preparation_sha256'] == REPORTS['native'][1], 'Joint derives from exact tree native5')
            native_report = str((ROOT / REPORTS['native'][0]).resolve())
            need(joint['physical_dependencies'][native_report] == REPORTS['native'][1], 'Authoritative joint physical dependency')
            need(build['preparation_sha256'] == REPORTS['joint'][1] and execution['build_sha256'] == REPORTS['build'][1], 'Exact executed native preparation/build lineage')
            need(Path(joint['native_library']).resolve() == Path(native['native_library']).resolve(), 'Current compiled native library path')
            current = joint['selected_order']
            need(len(current) == 125 and len(parent['selected_order']) == 124, 'One complete root added')
            need([r for r in current if r['entry'] != 0x4b7f70] == parent['selected_order'], 'Every124 frozen row retains original relative order')
            need(current[77]['entry'] == 0x4b7f70 and current[77]['table_slot'] == 0x5e0168, 'Genuine original tree table position')
            need(len(joint['registration_roots']) == 97 and len(set(joint['registration_roots'])) == 97, 'Exact97 registration schedule')
            need(native['live_owner_bound'] == 85 and native['exact_owned_causal_accesses'] == 172 and native['exact_primary_publications'] == 7, 'Owner bound and exact finite measured tree contracts')
            sources = {}
            directory = Path(native['native_include']).resolve()
            for path in directory.iterdir():
                if path.suffix in ('.cpp', '.hpp', '.h', '.inc'):
                    exact = str(path.resolve())
                    need(exact in native['files'] and exact in build['sources'], 'Current physical source appears in native and compiled closures')
                    need(native['files'][exact] == build['sources'][exact], 'Immutable native-to-build source identity')
                    pin(path, native['files'][exact])
                    sources[exact] = PINS[exact]
            for level in ('O0', 'O2'):
                need(build['workers'][level]['objects'] == joint['objects'][level], 'Every actual literal object follows preparation')
                old = set(parent['objects'][level])
                new = set(joint['objects'][level])
                need(old < new and len(new) == 371 and len(new - old) == 8, 'Accepted363 bodies plus eight literal tree bodies')
                for path in new - old:
                    pin(path, build['sources'][str(Path(path).resolve())])
            result = dict(authenticated_preparation_edges=3, selected_roots=125, registrations=97,
                          generated_native_sources_checked=len(sources), literal_objects_per_level=371,
                          literal_objects_added_per_level=8, live_owner_bound=85,
                          original_relative_order_preserved=True, executed_receipts_modified=False)
        elif kind == 'iteration':
            base = ROOT / 'tools/m4-joint-startup125'
            build_source = pin(base / 'build.py').read_text()
            run_source = pin(base / 'run.py').read_text()
            pin(base / 'build_v2.ps1')
            for text in (build_source, run_source):
                ast.parse(text)
            for required in ("inherited_archives={pp:h for pp,h in pins.items() if Path(pp).suffix=='.mwb'}",
                             "if pp not in inherited_archives:assert sha(pp)==h,(pp,h)",
                             "if pp not in inherited_archives:assert sha(pp)==h,('Source changed',pp)",
                             "'full_dependency_acceptance_rehash_required':True"):
                need(required in build_source, 'Actual local build boundary ' + required)
            for required in ("if Path(p).suffix=='.mwb':", 'Path(p).is_file()',
                             'inputs=[p for p in pins if p not in inherited_archives]',
                             "records=ds.DirectSet(capture/'transport.json',pin)",
                             "if p not in inherited_archives:assert sha(p)==h,('Unchanged input',p)",
                             'full_dependency_acceptance_rehash_required=True,initializer_credit=False'):
                need(required in run_source, 'Actual local run boundary ' + required)
            need(build['full_dependency_acceptance_rehash_required'] is True and execution['full_dependency_acceptance_rehash_required'] is True, 'Final complete physical rehash obligation retained')
            archives = build['inherited_capture_payload_hashes_reused']
            need(archives == execution['inherited_capture_payload_hashes_reused'] and len(archives) == 165, 'Every historical archive identity is carried unchanged')
            for path, digest in archives.items():
                need(Path(path).is_file() and Path(path).suffix == '.mwb' and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest), 'Present inherited exact archive identity')
                need(build['sources'][path] == execution['files'][path] == digest, 'No inherited archive disappears from acceptance union')
            direct = pin(ROOT / 'tools/m4-crt-allocation-root/run_v2.py').read_text()
            need("path = pin(self.path.parent / name, part['sha256'])" in direct and "reader = CaptureBundle(path, part['sha256'])" in direct and 'reader.read_bytes(logical)' in direct, 'Current output canonical identity and per-logical verification')
            verifier = pin(ROOT / 'tools/m4-pipeline/manifests.py').read_text()
            need("for path, expected in normalized_files.items():\n        with Path(path).open('rb') as stream:" in verifier and "actual = hashlib.file_digest(stream, 'sha256').hexdigest()" in verifier and '.mwb' not in verifier, 'Full final physical verifier has no archive exemption')
            result = dict(historical_archive_identities=len(archives), historical_archive_bytes=sum(Path(p).stat().st_size for p in archives),
                          historical_payloads_opened=False, native_output_canonical_verification=True,
                          historical_identities_retained_in_dependency_union=True,
                          full_final_dependency_rehash_required=True, selected_roots=125,
                          native_levels=2, initializer_credit=False)
        else:
            raise ValueError(kind)
        passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        report = dict(passed=passed, scope='Current125 ' + kind + ' metadata/source review; no semantic or acceptance credit',
                      **result, files=PINS, elapsed_seconds=time.perf_counter() - started)
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(passed=passed, report=str(out / 'report.json'), sha256=sha(out / 'report.json'))))


if __name__ == '__main__':
    main(*sys.argv[1:])
