"""Causal controls for evidence-based legacy filtering selection."""
import argparse
import copy
import json
from pathlib import Path
from package_replay import legacy_filter
from verify_filtering import verify


def controls(run):
    positive = verify(run)
    rows = [json.loads(line) for line in (run / 'frame/capture.jsonl').read_text().splitlines()]
    original = next(row for row in rows if row['event'] == 'draw')
    rejected = []
    for name in ('missing_history', 'failed_getter', 'missing_setter', 'getter_mismatch', 'later_stage_setter', 'mixed_filters'):
        row = copy.deepcopy(original)
        if name == 'missing_history':
            del row['filter_setter_history']
        elif name == 'failed_getter':
            row['legacy_filter_getters'][0]['hresult'] = -1
        elif name == 'missing_setter':
            row['filter_setter_history']['legacy_render'][0] = None
        elif name == 'getter_mismatch':
            row['legacy_filter_getters'][0]['value'] = 1
        elif name == 'later_stage_setter':
            setter = row['filter_setter_history']['legacy_render'][0]
            row['filter_setter_history']['stage0'][0] = {'value': 1, 'serial': setter['serial'] + 1}
        elif name == 'mixed_filters':
            row['legacy_filter_getters'][1]['value'] = 1
            row['filter_setter_history']['legacy_render'][1]['value'] = 1
        try:
            legacy_filter(row)
        except ValueError:
            rejected.append(name)
        else:
            raise AssertionError(f'Control accepted: {name}')
    return {'positive': positive, 'rejected_controls': rejected}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    print(json.dumps(controls(args.run), indent=2))
