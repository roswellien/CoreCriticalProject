"""Read-only admission of an already accepted, fully pinned first M3 gate."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
LABELS = ('first_build', 'first_comparison_report', 'first_initial_failure_report',
          'first_initial_failure_manifest', 'm2_final_pins', 'm2_independent_pins',
          'first_independent_review')


def require(ok, diagnostic):
    if not ok:
        raise ValueError(diagnostic)


def sha(path):
    with Path(path).open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return digest


def check(record):
    document = json.loads(record.read_bytes())
    pins = document.get('previous_gate_pins', document)
    require(set(LABELS).issubset(pins), 'Missing exact preceding gate labels')
    for name in LABELS:
        binding = pins[name]
        require(set(binding) == {'path', 'sha256'} and Path(binding['path']).is_absolute(),
                'Malformed absolute preceding gate binding:' + name)
        require(sha(binding['path']) == binding['sha256'], 'Preceding gate hash differs:' + name)
    report = json.loads(Path(pins['first_comparison_report']['path']).read_bytes())
    require(report.get('passed') is True and report.get('original_cases') == 15780 and
            report.get('native_comparisons') == 31560 and report['comparison']['passed'] is True and
            not report['comparison']['mismatched_records'], 'Preceding first M3 comparison is not accepted')
    require(report['build_sha256'] == pins['first_build']['sha256'] and
            Path(report['build_path']).resolve() == Path(pins['first_build']['path']).resolve(),
            'Accepted comparison/build identity differs')
    # Invoke the first gate's unchanged artifact/layout/source admission using
    # its own modules. This neither executes workers nor broadens its domain.
    names = ('source_identity', 'corpus')
    old = {name: sys.modules.get(name) for name in names}
    try:
        for name in names:
            spec = importlib.util.spec_from_file_location(name, ROOT/'tools/m3-slice'/(name+'.py'))
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
        spec = importlib.util.spec_from_file_location('_accepted_first_gate', ROOT/'tools/m3-slice/compare_slice.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.load_build(Path(pins['first_build']['path']).resolve())
    finally:
        for name, previous in old.items():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous
    require(sha(report['request_path']) == report['request_sha256'], 'Accepted first request binding differs')
    require(set(report['results']) == {'original', 'native-O0', 'native-O2'}, 'Accepted first worker set differs')
    for name, result in report['results'].items():
        require(sha(result['path']) == result['sha256'] and
                Path(result['path']).stat().st_size == result['bytes'] == 24 + 15780*24564,
                'Accepted first actual results differ:' + name)
        require(report['executions'][name]['exit_code'] == 0, 'Accepted first worker exit differs:' + name)
    return {'passed': True, 'gate_pins_sha256': sha(record), 'required_bindings': len(LABELS),
            'first_build_sha256': pins['first_build']['sha256'], 'worker_execution': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pins', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.pins)))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print('Preceding M3 gate rejected: ' + str(error), file=sys.stderr)
        sys.exit(1)
