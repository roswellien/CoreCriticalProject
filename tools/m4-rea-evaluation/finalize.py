"""Freeze measured tool-evaluation receipts without granting execution credit."""
from pathlib import Path
import hashlib
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
EVAL = ROOT / 'reports/m4-rea-evaluation'
EXPECTED = {
    'reports/m4-rea-evaluation/benchmark-r1.json': '52fc308ea683e3d839dd2e9f8f3e4f1e8b9edb9b0de1a317f3796e4dd53555e5',
    'reports/m4-rea-evaluation/initializer-inventory-r1.json': '5ad06d70b0e15c3fdfccff249f99cd4e08ab8220df8de9e3007db9b4802e4226',
    'reports/m4-rea-evaluation/rea-game-evidence-r1.json': '566f780dc55a32eb4e654278acd7201f162de609120e0873d2752f2b95d844ff',
    'reports/m4-rea-evaluation/provider-headless-r1/report.json': 'd5911ebac5319cf205241b85a8a750a5b63042fc713d79c10dd921a263ae3bd6',
    'reports/m4-rea-evaluation/game-headless-r1/report.json': '3fe2990c597a172b0dba4a9080d445ad33bcf35fb31153d8747c9c52e077333b',
    'reports/m4-rea-evaluation/process-review-r1/report.json': 'd76167b297350e04a0776aad38952b4cc14bd286d5017dd2b3763e3586a3d443',
    'reports/m4-joint-startup28-root/acceptance-r2/report.json': '3f3f1486b94b28e15eb09572965bdd4e861b0a286375db8fbcaf9b0a4902140a',
    'reports/m4-onexit-source/original-run-r4/report.json': 'da0fd8d0bd3c1c0b4e57bc7a8b33875d33020aa8ab240cfd5d011b247620fe0e',
    'reports/m4-onexit-native/preparation-r3/report.json': 'c614cf928234d60d59a6aa58ee020fe4f31e58cd309ab8205c33cebbddda8882',
    'reports/m4-onexit-source/symbol-attribution-r2/report.json': '190dca3427791734853f033623a37604daccefbf8d6979adc19f0e09272a33d9',
}

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    output = EVAL / 'evaluation-r1.json'
    if output.exists():
        raise ValueError('Evaluation output already exists; preserve it')
    files = {}
    for relative, expected in EXPECTED.items():
        path = ROOT / relative
        actual = digest(path)
        if actual != expected:
            raise ValueError(f'Frozen input mismatch: {relative}')
        files[str(path)] = actual
    benchmark = json.loads((EVAL / 'benchmark-r1.json').read_text())
    pilots = {}
    for mode, directory in [('game', 'game-headless-r1'), ('provider', 'provider-headless-r1')]:
        report = json.loads((EVAL / directory / 'report.json').read_text())
        if not report['passed'] or report['native_executed'] or report['initializer_credit']:
            raise ValueError('Pilot scope/pass mismatch')
        for run in report['runs']:
            exported = EVAL / directory / f"{run['name']}-export.json"
            if digest(exported) != run['export_sha256']:
                raise ValueError('Export changed after pilot')
            data = json.loads(exported.read_text())
            if data['target_sha256'] != report['target_sha256']:
                raise ValueError('Export target differs')
            if not all(f['present'] and f['decompile_completed'] for f in data['exports']):
                raise ValueError('Representative export incomplete')
            files[str(exported)] = digest(exported)
        pilots[mode] = dict(target_sha256=report['target_sha256'], runs=report['runs'])
    cold, warm = pilots['game']['runs']
    if cold['table'] != dict(existing_exact=3, created=141, conflicts=0, seed_seconds=cold['table']['seed_seconds']):
        raise ValueError('Cold seed coverage differs')
    if warm['table']['existing_exact'] != 144 or warm['table']['created'] or warm['table']['conflicts']:
        raise ValueError('Persisted seed coverage differs')
    game = ROOT / 'MW3/Mech3.exe'
    if digest(game) != benchmark['versions']['game_SHA']:
        raise ValueError('Original game changed')
    for relative in ['reports/m4-rea-evaluation/rea-game-analysis-r1.json',
                     'docs/m4-tooling-evaluation.md', 'docs/m4-execution-plan-r4.md',
                     'tools/m4-rea-evaluation/README.md', 'tools/m4-rea-evaluation/finalize.py']:
        path = ROOT / relative
        files[str(path)] = digest(path)
    data = dict(passed=True, scope='Measured static-tool evaluation and adoption decision',
                versions=benchmark['versions'], warm_REA_four_function_ms=41,
                default_exact_initializer_entries=3, seeded_exact_initializer_entries=144,
                representative_game_functions=7, representative_provider_functions=2,
                pilot_measurements=pilots, files=files,
                adoption='Persistent seeded Ghidra static lane; REA focused EXE evidence; existing Remill/LLVM and original/native acceptance retained',
                expected_benefit='Less manual field, ABI and dependency investigation; fewer cold imports and repeated analyses',
                quantified_end_to_end_speedup_established=False,
                accepted_initializers_unchanged=28, initializer_total=144,
                registration54_original_and_preparation_preserved=True,
                original_game_executed=False, native_functions_accepted=False, initializer_credit=False)
    output.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(passed=True, report=str(output), sha256=digest(output),
                         seeded_entries=144, accepted_initializers_unchanged=28)))

if __name__ == '__main__':
    main()
