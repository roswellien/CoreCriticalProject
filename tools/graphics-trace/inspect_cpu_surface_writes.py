"""Inspect lock-return/pre-unlock RGB565 snapshots, not recovered game CPU code."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def inspect(directory, authored=False):
    manifest = directory / 'writes.jsonl'
    rows = [json.loads(line) for line in manifest.read_text().splitlines() if line]
    if len(rows) < 3 or rows[0]['event'] != 'begin' or rows[-1]['event'] != 'end':
        raise ValueError('Incomplete CPU write interval')
    if rows[0]['live'] is not (not authored) or rows[0]['diagnostic_only'] is not True or rows[0]['command_coverage_complete'] is not False:
        raise ValueError('CPU write scope mismatch')
    if rows[-1]['open_lock'] is not False or rows[-1]['boundary_matches'] is not True:
        raise ValueError('Unclosed CPU lock or flip boundary')
    writes = rows[1:-1]
    if not (1 <= len(writes) <= 16) or rows[-1]['writes'] != len(writes):
        raise ValueError('CPU write count mismatch')
    decoded = []
    files = {}
    for ordinal, row in enumerate(writes, 1):
        if row['event'] != 'cpu_write' or row['ordinal'] != ordinal or row['format'] != 'RGB565' or row['unlock_hresult'] < 0:
            raise ValueError('CPU write identity/result mismatch')
        width, height = row['width'], row['height']
        if not (0 < width <= 4096 and 0 < height <= 4096) or row['source_pitch'] < width * 2:
            raise ValueError('CPU write layout mismatch')
        snapshots = []
        for role in ('before', 'after'):
            name = row[role]
            if not re.fullmatch(r'[0-9a-f]{64}\.bin', name):
                raise ValueError('CPU write payload name')
            data = (directory / name).read_bytes()
            if len(data) != width*height*2 or hashlib.sha256(data).hexdigest() != name[:-4]:
                raise ValueError('CPU write payload identity/size')
            files[name] = len(data)
            snapshots.append(data)
        before, after = snapshots
        changed = [index for index in range(width*height) if before[index*2:index*2+2] != after[index*2:index*2+2]]
        bounds = None
        if changed:
            xs, ys = [index % width for index in changed], [index // width for index in changed]
            bounds = [min(xs), min(ys), max(xs)+1, max(ys)+1]
        decoded.append({'ordinal': ordinal, 'surface': row['surface'], 'changed_pixels': len(changed),
                        'changed_bounds': bounds, 'completed_scenes': row['completed_scenes'],
                        'successful_draws': row['successful_draws'], 'before': row['before'], 'after': row['after']})
    if set(files) != {path.name for path in directory.glob('*.bin')}:
        raise ValueError('Unreferenced CPU pixel snapshots')
    return {'scope': 'RGB565 memory changes between game Lock return and Unlock call; game instructions and native HUD production unproven',
            'live': not authored, 'diagnostic_only': True, 'command_coverage_complete': False,
            'pid': rows[0]['pid'], 'writes': len(writes), 'decoded': decoded,
            'manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(), 'payload_files': files}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--authored', action='store_true')
    args = parser.parse_args()
    print(json.dumps(inspect(args.directory, args.authored), indent=2))
