"""Verify all G1 fixture records and their actual source/input/output identities."""
import json
from pathlib import Path
import sys

from compare_fixture import digest, source_digest


def verify(root):
    current_source = source_digest(root)
    records = []
    for kind in ('add', 'branch', 'memory', 'shift'):
        folder = root / f'reports/fixture-{kind}-differential'
        lifted = root / f'reports/fixture-{kind}-lift'
        report = json.loads((folder / 'report.json').read_text())
        if report['fixture'] != f'fixture_{kind}' or report['outcome'] not in ('arithmetic_lift_passed', 'fixture_lift_passed'):
            raise ValueError(f'{kind}: fixture did not pass')
        if report['total_cases'] < 10144 or report['random_cases'] < 10000 or len(report['lifted_runs']) != 2:
            raise ValueError(f'{kind}: missing required cases/builds')
        if report['source_digest'] != current_source:
            raise ValueError(f'{kind}: authored sources changed after the run')
        if digest((folder / 'corpus.bin').read_bytes()) != report['corpus_sha256']:
            raise ValueError(f'{kind}: corpus identity mismatch')
        for worker in [report['reference_run'], *report['lifted_runs']]:
            if worker['exit_code'] != 0:
                raise ValueError(f'{kind}: worker did not exit successfully')
            for index, key in ((0, 'worker_sha256'), (2, 'output_sha256')):
                if digest(Path(worker['command'][index]).read_bytes()) != worker[key]:
                    raise ValueError(f'{kind}: {key} differs from recorded artifact')
        if any(run['differential_result'] != 'zero mismatches' for run in report['lifted_runs']):
            raise ValueError(f'{kind}: differential mismatch')
        build = report['build_provenance']
        for name, checksum in build['artifacts'].items():
            if digest((lifted / name).read_bytes()) != checksum:
                raise ValueError(f'{kind}: generated artifact identity mismatch: {name}')
        controls = json.loads((lifted / 'controls.json').read_text())['controls']
        expected_checks = {'add': 30, 'branch': 31, 'memory': 44, 'shift': 30}[kind]
        if len(controls) != expected_checks or any(entry['outcome'] not in ('rejected', 'passed') for entry in controls):
            raise ValueError(f'{kind}: missing rejection/bridge checks')
        if kind == 'branch':
            coverage = report['branch_coverage']
            if coverage['signed_less'] == 0 or coverage['signed_greater_equal'] == 0:
                raise ValueError('Missing branch path coverage')
            if not any(entry['name'] == 'unresolved_control_flow_target' and '__remill_missing_block' in entry['reason']
                       for entry in controls):
                raise ValueError('Missing unresolved-target rejection')
        if kind == 'memory':
            coverage = report['memory_coverage']
            if coverage['unaligned_buffer_cases'] == 0 or not {0, 4084}.issubset(coverage['buffer_offsets']):
                raise ValueError('Missing unaligned/page-boundary coverage')
            if sum(entry.get('failure_probes', 0) for entry in controls) != 14:
                raise ValueError('Missing bridge failure probes')
        records.append({'fixture': kind, 'cases': report['total_cases'],
                        'report_sha256': digest((folder / 'report.json').read_bytes()),
                        'controls_sha256': digest((lifted / 'controls.json').read_bytes()),
                        'checks': len(controls), 'native_builds': ['O0', 'O2']})
    summary = {'version': 1, 'gate': 'G1', 'outcome': 'passed',
               'scope': 'reviewed authored integer leaves; no MW3 function proof',
               'source_digest': current_source, 'fixtures': records,
               'total_valid_cases': sum(record['cases'] for record in records),
               'total_native_case_comparisons': sum(record['cases'] * 2 for record in records),
               'total_rejection_bridge_checks': sum(record['checks'] for record in records)}
    output = root / 'reports/fixture-suite'
    output.mkdir(parents=True, exist_ok=True)
    (output / 'report.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(f"G1 passed: {summary['total_valid_cases']} valid cases, O0/O2, {summary['total_rejection_bridge_checks']} rejection/bridge checks")


if __name__ == '__main__':
    try:
        verify(Path(__file__).resolve().parents[2])
    except (KeyError, ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
