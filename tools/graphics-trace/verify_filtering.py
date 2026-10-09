"""Correlate captured filtering diagnostics with successful live setter records."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from package_replay import legacy_filter
from verify import verify as verify_trace, records
from verify_capture import verify as verify_capture


def verify(run):
    trace = verify_trace(run, 'draws')
    capture = verify_capture(run / 'frame')
    if trace['pid'] != capture['pid']:
        raise ValueError('Capture/trace process mismatch')
    events = records(run / 'game.jsonl')
    devices = {r['output'] for r in events if r['live'] and r['event'] == 'create_device' and r['hresult'] >= 0}
    if len(devices) != 1:
        raise ValueError('Filtering verifier requires one live device')
    device = next(iter(devices))
    setters = {r['serial']: r for r in events if r['live'] and r['event'] == 'filter_setter' and r['object'] == device}
    rows = [json.loads(line) for line in (run / 'frame/capture.jsonl').read_text().splitlines()]
    counts = Counter()
    disagreements = 0
    for draw in (r for r in rows if r['event'] == 'draw'):
        filtering = legacy_filter(draw)
        counts['linear' if filtering else 'nearest'] += 1
        for group, api in (('legacy_render', 'legacy_render'), ('stage0', 'stage0')):
            for index, request in enumerate(draw['filter_setter_history'][group]):
                if request is None:
                    continue
                event = setters.get(request['serial'])
                if not event or event['hresult'] < 0 or event['api'] != api or event['index'] != index or event['value'] != request['value']:
                    raise ValueError('Filtering history lacks matching successful live setter')
        expected = 2 if filtering else 1
        ss = draw['stages'][0]['states']
        disagreements += int(ss['16'] != expected or ss['17'] != expected)
    config = json.loads((run / 'wrapper-config.json').read_text(encoding='utf-8-sig'))
    if hashlib.sha256((run / 'dgVoodoo.conf').read_bytes()).hexdigest() != config['sha256']:
        raise ValueError('Wrapper config snapshot hash mismatch')
    return {'pid': capture['pid'], 'draws': capture['draws'], 'legacy_filters': dict(counts),
            'draws_with_stage_getter_disagreement': disagreements,
            'scope': 'Legacy filtering supported by matching successful setter/getter evidence; general API precedence and frame equivalence unproven',
            'config_sha256': config['sha256'], 'manifest_sha256': capture['manifest_sha256']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.run), indent=2))
