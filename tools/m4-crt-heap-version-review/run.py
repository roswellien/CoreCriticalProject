"""Execute independently authored native fixtures, then seal strict captures."""
import json
import sys
import time
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import normalized, unique_object, verify_manifest
from stages import run_stage, verify_stage
from paths import publish_bytes


def main(compiled, name):
    build_path = Path(compiled).absolute()
    base = ROOT / 'reports/m4-crt-heap-version-review'
    out = base / name
    if out.parent != base or not name.startswith('native-') or out.exists():
        raise ValueError('Fresh independent native output')
    out.mkdir()
    build = json.loads(build_path.read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)
    if build['passed'] is not True or build['compiled_only'] is not True:
        raise ValueError('Successful independent compile-only fixture required')
    files = {}
    def pin(path, expected=None):
        actual = sha_file(path)
        if expected is not None and actual != expected:
            raise ValueError('Current native dependency changed: ' + str(path))
        key = normalized(str(Path(path).absolute()))
        if key in files and files[key] != actual:
            raise ValueError('Conflicting physical source association')
        files[key] = actual
        return str(Path(path).absolute())
    pin(build_path)
    for category in ('sources', 'tools', 'libraries', 'entry_objects', 'matherr_objects', 'control_objects',
                     'initterm_objects', 'mainargs_objects', 'normal_argv_objects', 'producer_objects',
                     'parser_objects', 'locale_objects', 'heap_objects', 'heap_mode_objects', 'heap_version_objects', 'compiler_read_headers', 'artifacts'):
        for path, digest in build[category].items():
            pin(path, digest)
    for path in (Path(__file__), Path(sys.executable), ROOT / 'tools/m4-pipeline/stages.py',
                 ROOT / 'tools/m4-pipeline/capture_bundle.py', ROOT / 'tools/m4-pipeline/paths.py',
                 ROOT / 'tools/m4-pipeline/manifests.py'):
        pin(path)
    verify_manifest(files)
    levels = {}
    for level in ('O0', 'O2'):
        worker = build_path.parent / level / 'controls.exe'
        obj = ROOT / ('reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-' + level + '.obj')
        inputs = [ROOT / 'MW3/Mech3.exe', obj, ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',
                  ROOT / 'reports/m4-crt-fdiv/native-derived-r1/pack.bin',
                  ROOT / 'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin']
        tree = out / ('actual-' + level)
        stage = out / ('run-' + level)
        argv = [str(worker), *map(str, inputs), str(tree)]
        record = run_stage(argv, stage, timeout_seconds=180, required_outputs=[tree / 'COMPLETE', tree / 'controls.json'], inputs=list(files))
        digest = pin(stage / 'stage.json')
        verify_stage(stage, sha_file(stage / 'stage.json'))
        for filename in ('stdout.bin', 'stderr.bin'):
            pin(stage / filename)
        if record['passed'] is not True or (tree / 'COMPLETE').read_bytes() != b'COMPLETE':
            raise ValueError('Independent native fixture failed: ' + level)
        result = json.loads((tree / 'controls.json').read_bytes(), object_pairs_hook=unique_object)
        if result['passed'] is not True or result['scenarios'] != 98 or result['malformed_token_denials'] != 20 or result['direct_host_failure_queries'] != 2:
            raise ValueError('Exact independent completed native corpus')
        levels[level] = {'worker': str(worker), 'worker_sha256': sha_file(worker), 'argv': argv,
                         'native_stage': str(stage), 'native_stage_sha256': sha_file(stage / 'stage.json'),
                         'native_seconds': record['elapsed_seconds'], 'result': result, 'tree': str(tree)}
    for level in ('O0', 'O2'):
        info = levels[level]
        tree = Path(info['tree'])
        bundle = out / (level + '.mwb')
        stage = out / ('pack-' + level)
        record = run_stage([sys.executable, str(ROOT / 'tools/m4-pipeline/capture_bundle.py'), 'pack', str(tree), str(bundle)],
            stage, timeout_seconds=600, required_outputs=[bundle], inputs=list(files))
        verify_stage(stage, sha_file(stage / 'stage.json'))
        for filename in ('stage.json', 'stdout.bin', 'stderr.bin'):
            pin(stage / filename)
        if record['passed'] is not True:
            raise ValueError('Independent strict capture publication failed')
        digest = sha_file(bundle)
        pin(bundle, digest)
        with CaptureBundle(bundle, digest) as reader:
            inventory = {name: {'bytes': len(reader.read_bytes(name)), 'sha256': __import__('hashlib').sha256(reader.read_bytes(name)).hexdigest()} for name in reader.names()}
        inventory_path = out / (level + '-inventory.json')
        publish_bytes(inventory_path, (json.dumps({'files': inventory}, indent=2) + '\n').encode())
        pin(inventory_path)
        info.update(bundle=str(bundle), bundle_sha256=digest, logical_files=len(inventory),
                    inventory_path=str(inventory_path), inventory_sha256=sha_file(inventory_path),
                    pack_stage=str(stage), pack_stage_sha256=sha_file(stage / 'stage.json'), pack_seconds=record['elapsed_seconds'])
        del info['tree']
    closure = verify_manifest(files)
    report = {'passed': True, 'scope': 'Independent native fixture corpus on production composition with explicit State-PC-only attach fragment/heap prefix seam',
              'compiled_path': str(build_path), 'compiled_sha256': sha_file(build_path), 'levels': levels,
              'native_scenarios': 196, 'native_checks': sum(info['result']['checks'] for info in levels.values()),
              'malformed_token_denials': sum(info['result']['malformed_token_denials'] for info in levels.values()),
              'original_executed': False, 'ordinary_game_launched': False, 'HeapCreate_executed': True, 'genuine_source_token_published': True, 'full_heap_initialization_complete': False,
              'GetVersionExA_executed': True, 'counterfactual_direct_host_failure_queries': 4, 'synthetic_API_results': False, 'declared_lower_stack_inputs': 6, 'probe_return_proved': True, 'full_causal_source_model_oracle': False, 'table_initialization_proved': False, 'whole_M4_complete': False, 'closure': closure, 'files': files}
    publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps({'passed': True, 'report_sha256': sha_file(out / 'report.json'), 'native_scenarios': 196, 'native_checks': report['native_checks']}))


if __name__ == '__main__':
    main(*sys.argv[1:])
