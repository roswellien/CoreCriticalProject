"""Report saved-capture diversity; not a proof of renderer equivalence."""
import argparse
import hashlib
import json
from pathlib import Path
from verify_capture import verify


def describe(run):
    receipt = verify(run / 'frame')
    rows = [json.loads(line) for line in (run / 'frame/capture.jsonl').read_text().splitlines()]
    draws = [r for r in rows if r['event'] == 'draw']
    geometry = [(d['primitive'], d['fvf'], d['vertices'], d['indices']) for d in draws]
    textures = {s['texture']['file'] for d in draws for s in d['stages'] if s['texture']}
    final = next(r['surface']['file'] for r in rows if r['event'] == 'final_target')
    receipt.update({'run': str(run), 'geometry_fingerprint': hashlib.sha256(json.dumps(geometry).encode()).hexdigest(),
                    'final_target_payload': final, 'unique_texture_payloads': len(textures)})
    return receipt, textures


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('candidate', type=Path)
    args = parser.parse_args()
    baseline, bt = describe(args.baseline)
    candidate, ct = describe(args.candidate)
    print(json.dumps({'scope': 'Captured geometry/resource diversity; gameplay timing and frame equivalence unproven',
                      'baseline': baseline, 'candidate': candidate,
                      'geometry_differs': baseline['geometry_fingerprint'] != candidate['geometry_fingerprint'],
                      'final_pixels_differ': baseline['final_target_payload'] != candidate['final_target_payload'],
                      'shared_texture_payloads': len(bt & ct), 'new_texture_payloads': len(ct - bt)}, indent=2))
