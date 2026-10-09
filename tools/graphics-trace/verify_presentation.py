"""Verify bounded live presentation candidates; not displayed-frame equivalence."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from verify import verify, records


def inspect(run, monitor=None):
    trace = verify(run, 'draws', monitor)
    game = records(run / 'game.jsonl')
    fixtures = [r for r in game if r['event'] == 'presentation_fixture']
    if len(fixtures) != 1 or fixtures[0]['live'] or not all(fixtures[0].get(k) is True for k in ('passed','failed_results_preserved','last_error_preserved')):
        raise ValueError('Presentation forwarding fixtures missing or failed')
    if any(r['event'] == 'presentation_observer_failed' for r in game):
        raise ValueError('Presentation observer failed')
    path = run / 'presentation.jsonl'
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    if not rows or len(rows) > 2048 or any(r['seq'] != i+1 or r['pid'] != trace['pid'] for i,r in enumerate(rows)):
        raise ValueError('Presentation sequence/process mismatch')
    for previous, current in zip(rows, rows[1:]):
        if current['completed_scenes'] < previous['completed_scenes'] or current['successful_draws'] < previous['successful_draws']:
            raise ValueError('Presentation counters moved backwards')
    flips = [r for r in rows if r['method'] == 'Flip' and r['hresult'] >= 0 and r['surface_info_hresult'] >= 0 and r['caps'] & 512]
    gameplay = [r for r in flips if r['completed_scenes'] > 0]
    if len(gameplay) < 2 or any(r['scene_open'] for r in gameplay):
        raise ValueError('No repeated closed-scene primary flips')
    if len({r['tid'] for r in rows}) != 1 or len({r['destination'] for r in gameplay}) != 1:
        raise ValueError('Timeline needs further thread/surface disambiguation')
    scene_counts, draw_counts = [], []
    for previous,current in zip(gameplay, gameplay[1:]):
        scene_counts.append(current['completed_scenes']-previous['completed_scenes'])
        draw_counts.append(current['successful_draws']-previous['successful_draws'])
    return {'scope':'Successful primary-surface Flip candidates observed after scenes; presentation pixels, all commands and physically displayed-frame equivalence unproven',
            'pid':trace['pid'],'events':len(rows),'event_budget_reached':len(rows)==2048,
            'methods':dict(Counter(r['method'] for r in rows)), 'gameplay_primary_flips':len(gameplay),
            'scene_intervals_between_flips':dict(Counter(scene_counts)),
            'draws_between_flips_min':min(draw_counts),'draws_between_flips_max':max(draw_counts),
            'primary_surface':gameplay[0]['destination'],'dimensions':[gameplay[0]['width'],gameplay[0]['height']],
            'presentation_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'monitor':trace.get('monitor')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    parser.add_argument('--monitor',type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.run,args.monitor),indent=2))
