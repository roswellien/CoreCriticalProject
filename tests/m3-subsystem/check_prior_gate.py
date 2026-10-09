"""Asset-free controls: malformed preceding evidence must stop before tools."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('_m3_prior_admission', ROOT/'tools/m3-subsystem/check_prior_gate.py')
admission = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admission)


def controls(out):
    out = out.resolve()
    assert out.is_relative_to((ROOT/'reports/m3-subsystem').resolve()) and not out.exists()
    out.mkdir(parents=True)
    authored_build = out/'authored-build.json'
    authored_build.write_text('{}\n')
    report = {'passed': False, 'original_cases': 15780, 'native_comparisons': 31560,
              'comparison': {'passed': False, 'mismatched_records': {'original': 1}},
              'build_path': str(authored_build), 'build_sha256': admission.sha(authored_build)}
    authored_report = out/'authored-failed-report.json'
    authored_report.write_text(json.dumps(report))
    pins = {name: {'path': str(authored_build), 'sha256': admission.sha(authored_build)}
            for name in admission.LABELS}
    pins['first_comparison_report'] = {'path': str(authored_report), 'sha256': admission.sha(authored_report)}
    rows = []

    def reject(name, candidate, diagnostic):
        path = out/(name+'.json')
        path.write_text(json.dumps(candidate))
        try:
            admission.check(path)
        except (OSError, ValueError, KeyError, TypeError) as error:
            assert diagnostic in str(error), (name, error)
            rows.append({'name': name, 'outcome': 'rejected_before_workers', 'diagnostic': str(error)})
        else:
            raise AssertionError('Unsafe authored preceding gate admitted: '+name)

    reject('missing_labels', {}, 'Missing exact')
    changed = copy.deepcopy(pins);del changed['first_independent_review']
    reject('missing_independent_review', changed, 'Missing exact')
    changed = copy.deepcopy(pins);changed['m2_final_pins']['sha256'] = '0'*64
    reject('changed_frozen_binding', changed, 'hash differs')
    changed = copy.deepcopy(pins);changed['first_build']['path'] = 'relative.json'
    reject('relative_prior_artifact', changed, 'Malformed absolute')
    changed = copy.deepcopy(pins);changed['first_build']['unreviewed'] = True
    reject('unexpected_binding_fields', changed, 'Malformed absolute')
    reject('failed_actual_comparison', pins, 'not accepted')
    for name, field, value in [('missing_full_original_corpus', 'original_cases', 1),
                              ('missing_native_O0_O2_corpus', 'native_comparisons', 15780),
                              ('accepted_label_with_differences', 'comparison', {'passed': True, 'mismatched_records': {'original': 1}}),
                              ('comparison_build_hash_mismatch', 'build_sha256', '0'*64),
                              ('comparison_build_path_mismatch', 'build_path', str(out/'other-build.json'))]:
        altered = copy.deepcopy(report);altered['passed'] = True
        altered['comparison'] = {'passed': True, 'mismatched_records': {}}
        altered[field] = value
        path = out/(name+'-report.json');path.write_text(json.dumps(altered))
        selected = copy.deepcopy(pins);selected['first_comparison_report'] = {'path': str(path), 'sha256': admission.sha(path)}
        reject(name, selected, 'identity differs' if field.startswith('build_') else 'not accepted')
    result = {'passed': True, 'asset_free_rejections': len(rows), 'worker_executions': 0, 'controls': rows,
              'checker_sha256': admission.sha(ROOT/'tools/m3-subsystem/check_prior_gate.py')}
    (out/'report.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({name: result[name] for name in ('passed', 'asset_free_rejections', 'worker_executions')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    controls(parser.parse_args().out)
