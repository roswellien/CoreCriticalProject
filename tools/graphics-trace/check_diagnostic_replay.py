"""Check diagnostic ordering rejection without weakening accepted-scene gates."""
import argparse
import copy
import json
from pathlib import Path
import tempfile

from verify_capture import verify_presentation_diagnostic


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    accepted = verify_presentation_diagnostic(args.capture)
    rows = [json.loads(line) for line in (args.capture / 'capture.jsonl').read_text().splitlines()]
    controls = {}
    changed = copy.deepcopy(rows); changed[0]['command_coverage_complete'] = True
    controls['overstated_coverage'] = changed
    changed = copy.deepcopy(rows); changed.insert(4, {'event': 'scene_begin'})
    controls['nested_scene'] = changed
    changed = copy.deepcopy(rows); changed.pop(next(i for i, r in enumerate(changed) if r['event'] == 'scene_begin'))
    controls['draw_outside_scene'] = changed
    changed = copy.deepcopy(rows); next(r for r in changed if r['event'] == 'scene_end')['draws_so_far'] += 1
    controls['scene_accounting'] = changed
    changed = copy.deepcopy(rows); changed.insert(-1, {'event': 'unsupported_clear'})
    controls['unreplayed_command'] = changed
    changed = copy.deepcopy(rows); changed[-1]['command_coverage_complete'] = True
    controls['overstated_footer'] = changed
    rejected = []
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        for name, candidate in controls.items():
            (directory / 'capture.jsonl').write_text('\n'.join(json.dumps(r) for r in candidate))
            try:
                verify_presentation_diagnostic(directory)
            except ValueError as error:
                if 'payload' in str(error).lower(): raise ValueError('Control rejected too late') from error
                rejected.append({'control': name, 'reason': str(error)})
            else:
                raise ValueError(f'{name} incorrectly admitted')
    report = {'scope': 'Diagnostic payload/order gate only; no full-frame equivalence',
              'accepted_diagnostic_draws': accepted['draws'], 'rejected_controls': rejected}
    args.output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
