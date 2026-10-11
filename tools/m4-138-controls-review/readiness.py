"""Bounded reuse audit; does not open capture readers or rerun semantic workers."""
from pathlib import Path
import hashlib
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / 'reports/m4-joint-startup138/context-controls-verification-r1/report.json'
EXPECTED = '88e0a18bc8b32fb70c3fd460c828c44127613662fd4467cf3385ae78b56861cb'
SUBSET = [
    'reports/m4-joint-startup138/context-controls-execution-r1/report.json',
    'reports/m4-joint-startup138/controls-preparation-r4/report.json',
    'reports/m4-joint-startup138/controls-build-r2/build.json',
    'reports/m4-tree-review/joint138-controls-prelaunch-r4/report.json',
    'tools/m4-joint-startup138/check_context_controls_v4.py',
    'tools/m4-joint-startup138/check_context_controls_v3.py',
    'tools/m4-joint-startup138/controls_main.cpp',
    'tools/m4-runtime/runtime.cpp',
    'runtime/memory/guest_memory.cpp',
    'tools/m4-widget-growth-review/gdi_identity.py',
    'reports/m4-joint-startup138/context-controls-verification-r1/actual-Context-causes.json',
]
CONTEXT = [
    'docs/m4-development-workflow.md',
    'docs/m4-execution-plan-r13.md',
    'docs/m4-progress-startup131.md',
    'reports/m4-joint-startup131-root/acceptance-r1/report.json',
    'reports/m4-joint-startup138-root/execution-r3/report.json',
    'reports/m4-startup138-original/original-execution-r1/report.json',
    'reports/m4-startup138-original/validation-preparation-r1/report.json',
    'reports/m4-joint-startup138-source/preflight-r1/report.json',
    'tools/m4-joint-startup138/prepare_source.py',
    'tools/m4-joint-startup138/preflight_source.py',
    'tools/m4-startup138-original/validate.py',
]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def header(path):
    """Parse top-level metadata preceding files; never materialize its huge map."""
    lines = []
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            if line == '  "files": {\n':
                return json.loads(''.join(lines) + '  "files": {}\n}\n')
            lines.append(line)
            assert sum(map(len, lines)) < 1_000_000, 'Bounded metadata header'
    raise AssertionError('Expected top-level physical files map')


def main(name):
    out = ROOT / 'reports/m4-138-controls-review' / name
    assert not out.exists(), 'Fresh immutable audit output required'
    files = {}

    def pin(relative):
        path = ROOT / relative
        assert path.suffix not in ('.mwb', '.zip'), 'No capture archive input'
        files[str(path.resolve())] = sha(path)
        return path

    receipt = pin(RECEIPT.relative_to(ROOT))
    assert files[str(receipt)] == EXPECTED, 'Exact known completed controls receipt'
    metadata = header(receipt)
    assert metadata['passed'] and metadata['initializer_credit'] == 0
    assert not metadata['archive_reader_opened']
    for field in ('partial_fault_register_prediction', 'hidden_Runtime_frames_or_permissions_bytes_observed',
                  'whole_prior131_semantic_source_equivalence_claimed', 'source_callbacks_executed',
                  'source_bootstrap_or_teardown_modeled'):
        assert metadata[field] is False, field
    expected_counts = {'whole_successful_prefix_records': 2160,
                       'same_actual_Context_retry_relations': 16,
                       'exact_current_first_refusals': 16,
                       'actual_owned_font_cleanup_calls': 240,
                       'whole_ASM_FX512_ENV28_restore_pairs': 48}
    for field, value in expected_counts.items():
        assert metadata['counts'][field] == value, field
    selected = {str((ROOT / relative).resolve()): relative for relative in SUBSET}
    embedded = {}
    physical_map_rows = 0
    inside = False
    with receipt.open(encoding='utf-8') as stream:
        for line in stream:
            if line == '  "files": {\n':
                inside = True
                continue
            if not inside:
                continue
            if line == '  }\n':
                break
            assert line.startswith('    "'), 'Ordinary one-row-per-line files map'
            pair = json.loads('{' + line.strip().removesuffix(',') + '}')
            assert len(pair) == 1
            path, digest = next(iter(pair.items()))
            physical_map_rows += 1
            if path in selected:
                assert path not in embedded, 'Unique selected physical key'
                embedded[path] = digest
    assert set(embedded) == set(selected), 'Every bounded selected dependency is pinned by receipt'
    for path, relative in selected.items():
        pin(relative)
        assert files[path] == embedded[path], 'Fresh bounded physical provenance: ' + relative
    execution = header(ROOT / SUBSET[0])
    assert execution['passed'] and execution['actual_workers_launched'] == 16
    assert execution['all_workers_terminal'] and not execution['archive_reader_opened']
    assert metadata['execution_sha256'] == files[str((ROOT / SUBSET[0]).resolve())]
    lineage = [('preparation_path', 'preparation_sha256'), ('build_path', 'build_sha256'),
               ('admission_review', 'admission_review_sha256')]
    for path_key, hash_key in lineage:
        assert execution[path_key] in files and files[execution[path_key]] == execution[hash_key]
    for relative in CONTEXT:
        pin(relative)
    accepted = header(ROOT / 'reports/m4-joint-startup131-root/acceptance-r1/report.json')
    assert accepted['passed'] and accepted['connected_roots'] == 131
    checker = (ROOT / 'tools/m4-joint-startup138/check_context_controls_v4.py').read_text()
    for fragment in ('Actual Runtime CALL-first committed-memory', 'Same actual Context whole observable retry',
                     'Actual successful current-thread DeleteObject', 'All consumed physical/ordinary files unchanged'):
        assert fragment in checker, fragment
    files[str(Path(__file__).resolve())] = sha(Path(__file__).resolve())
    files[str(Path(sys.executable).resolve())] = sha(Path(sys.executable).resolve())
    report = dict(
        passed=True,
        scope='Bounded controls receipt/provenance readiness only; historical proof is reusable, independent full raw/equivalence and acceptance remain separate',
        accepted_count_from_existing_receipt=131,
        total_inventory_roots=144,
        remaining_inventory_roots=13,
        initializer_credit=0,
        native_execution_performed=False,
        semantic_verifier_rerun=False,
        archive_reader_opened=False,
        independent_full_raw_review=False,
        independent_controls_equivalence_proved=False,
        full_capture_union_rehashed=False,
        full_acceptance_union_rehashed=False,
        controls_report_sha256=EXPECTED,
        receipt_metadata=metadata,
        execution_metadata=execution,
        files_map_rows_streamed=physical_map_rows,
        receipt_physical_dependencies_freshly_rehashed=len(SUBSET),
        reusable_obligations=['Sixteen O0/O2 Context first-fault cases after 135 carried roots',
                              'Exact authored input mutation and causal source operand prefix',
                              'Whole exported Context/private/registry retry equality',
                              'Fifteen source-owned fonts per case and 240 actual cleanup calls',
                              'Forty-eight ASM FX512/ENV28 restores'],
        limitations=['Historical reported relations reviewed from checker and metadata; capture raw files were not independently compared in this audit',
                     'Observed machine state excludes hidden Runtime frames and permission bytes',
                     'No whole prior131 semantic/source-equivalence claim or bootstrap/teardown modeling',
                     'No source shutdown callback execution or native game launch proof'],
        remaining_138_gates=['Strict original138 source/resource/semantic capture validation',
                             'Executed complete138 source/provider comparison',
                             'Independent source/output closure review',
                             'Independent controls raw review and equivalence as required by final gate configuration',
                             'Loaded input relationship and paired equality/review',
                             'Typed acceptance configuration and fresh complete physical dependency union'],
        recommendation='Reuse completed controls and positive captures; execute strict original validation next, then source/provider and paired closure. No controls rerun or recapture is justified by this audit.',
        files=files,
    )
    out.mkdir(parents=True)
    target = out / 'report.json'
    target.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=True, report=str(target), sha256=sha(target), initializer_credit=0)))


if __name__ == '__main__':
    main(sys.argv[1])
