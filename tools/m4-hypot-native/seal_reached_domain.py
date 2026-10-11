"""Join genuine reached source PCs to current literal x64 object preparation.

This is source coverage, not a linked runtime, numeric oracle, or acceptance.
"""
from pathlib import Path
import hashlib
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'reports/m4-hypot-native'


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main(name):
    assert re.fullmatch('reached-domain-r[1-9][0-9]*', name)
    out = AREA / name
    assert not out.exists()
    out.mkdir(parents=True)
    pins = {}

    def pin(path, expected=None):
        path = Path(path).resolve()
        assert path.suffix.lower() not in ('.mwb', '.zip')
        digest = sha(path)
        assert expected is None or digest == expected, path
        assert str(path) not in pins or pins[str(path)] == digest
        pins[str(path)] = digest
        return path

    def read(path, expected=None):
        return json.loads(pin(path, expected).read_bytes())

    def receipt(path, expected):
        j = read(path, expected)
        assert j['passed'] is True
        for p, h in j['files'].items():
            if Path(p).suffix.lower() not in ('.mwb', '.zip'):
                pin(p, h)
        return j

    old = receipt(AREA / 'lifts-r4/report.json',
        'fff190c4797cc82c018982c5c247b652cc6e307c2e184953dc620275f133b9f3')
    new = receipt(AREA / 'lifts-r5/report.json',
        'fd5186d1619078be2d03c3e05bf7ec1b251190e3af58d12f15d25b331b1ea01f')
    trace_path = ROOT / 'reports/m4-hypot-original/trace-validation-r2/report.json'
    trace = receipt(trace_path,
        'be137c4a05a5f9d33805f5cbb9db60157bf707fb2e1298db9b90ec943686780f')
    independent = receipt(ROOT / 'reports/m4-tree-review/hypot-trace-actual-r1/report.json',
        '92c18c03c0b24c9f4c8aeccea8c4efbdcfea8c864e744415c09b70605a3e2421')
    observed = read(trace_path.parent / 'actual-source-traces.json')
    assert len(observed) == 6 and trace['reader_closed']
    assert not trace['source_after_seed'] and not trace['canonical_debugger_FIP_FDP_claimed']
    bodies = {}
    physical = {}
    owners = {}
    previous = set()
    for label, j in [('existing', old), ('additional', new)]:
        for symbol, b in j['bodies'].items():
            assert symbol not in bodies and not b['execution_admitted']
            assert b['initializer_credit'] == 0 and b['layouts']['struct.State']['size'] == 3504
            assert set(b['objects']) == {'O0', 'O2'}
            for obj in b['objects'].values():
                pin(obj['path'], obj['sha256'])
            host = Path(next(iter(b['objects'].values()))['path']).parent / (symbol + '-host.ll')
            host_text = pin(host, b['host_sha256']).read_text()
            name = 'mw34_hypot_' + symbol + '_body'
            assert host_text.count('define ptr @' + name + '(') == 1
            bodies[symbol] = dict(entry=b['entry'], symbol=name,
                source_receipt=label, machine_fragment=b['machine_fragment'],
                objects=b['objects'], host_IR_sha256=b['host_sha256'],
                omitted_unreached_instructions=len(b.get('omitted_unreached_rows', [])),
                CW_transfers=b.get('CW_transfers', []),
                execution_admitted=False)
            for row in b['physical_instructions']:
                pc = row['pc']
                identity = (row['bytes'], row['size'], row['mnemonic'])
                assert pc not in physical or physical[pc] == identity
                physical[pc] = identity
                owners.setdefault(pc, []).append(symbol)
                if label == 'existing':
                    previous.add(pc)
    reached = set(map(int, observed[0]['actual_reached_PC_counts']))
    assert len(reached) == 439 and reached <= set(physical)
    assert all(set(map(int, t['actual_reached_PC_counts'])) == reached for t in observed)
    assert sum(t['event_count'] for t in observed) == 6042
    joins = []
    for t in observed:
        assert len(t['instructions']) == t['event_count'] == 1007
        for row in t['instructions']:
            assert row['PC'] in reached and row['BEFORE_CPU'][9] == row['PC']
            assert row['AFTER_CPU'][9] == row['next_PC']
            joins.append(dict(sequence=t['sequence'], index=row['index'], PC=row['PC'],
                source_bytes=physical[row['PC']][0], native_body_candidates=owners[row['PC']]))
    (out / 'source-PC-joins.json').write_text(json.dumps(joins, indent=2) + '\n')
    (out / 'literal-bodies.json').write_text(json.dumps(bodies, indent=2) + '\n')
    declarations = ['#pragma once', '#include <cstdint>', 'struct State;']
    for b in bodies.values():
        declarations.append('extern "C" void *' + b['symbol'] + '(State *, std::uint32_t, void *);')
    declarations += ['namespace mw34_hypot_literal {',
        'using Function = void *(*)(State *, std::uint32_t, void *);',
        'struct Body { std::uint32_t entry; Function call; bool fragment; };',
        'inline const Body bodies[] = {']
    for b in bodies.values():
        declarations.append(' {' + hex(b['entry']) + ', &' + b['symbol'] + ', ' +
                            ('true' if b['machine_fragment'] else 'false') + '},')
    declarations += ['};', '}']
    (out / 'literal_dispatch.hpp').write_text('\n'.join(declarations) + '\n')
    pin(__file__)
    for p in out.iterdir():
        if p.is_file():
            pin(p)
    report = dict(passed=True,
        scope='Complete genuine reached source-PC coverage by compiled literal object preparation only',
        counts=dict(genuine_cases=6, genuine_instruction_occurrences=len(joins),
            unique_reached_PCs=len(reached), previously_compiled_reached_PCs=len(reached & previous),
            additional_compiled_reached_PCs=len(reached - previous), missing_reached_PCs=0,
            literal_bodies=len(bodies), literal_objects=2*len(bodies)),
        source_trace_sha256=sha(trace_path),
        independent_source_trace_sha256=sha(ROOT / 'reports/m4-tree-review/hypot-trace-actual-r1/report.json'),
        cold_source_domain_admitted=False, object_preparation_only=True,
        source_after_seed=False, numerical_expected_seed=False, native_linked=False,
        native_executed=False, source_native_equivalence=False, initializer_credit=0,
        requires=['Actual registered native fixture and linked body/bridge membership',
                  'Native own BEFORE State/memory/control/operand execution',
                  'Independent raw80/F32 source observations and whole State/memory comparison',
                  'Whole caller hardware restoration and actual refusal/lifecycle evidence',
                  'Connected admitted-image integration and final current acceptance'], files=pins)
    p = out / 'report.json'
    p.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=True, sha256=sha(p), counts=report['counts'])))


if __name__ == '__main__':
    main(sys.argv[1])
