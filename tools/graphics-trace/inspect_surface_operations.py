"""Inspect bounded surface API observations; never grant frame/replay coverage."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

ZBUFFER = 0x20000
DEPTHFILL = 0x2000000
METHODS = {'Blt', 'BltFast', 'Lock', 'Unlock', 'GetDC', 'ReleaseDC'}


def raw(value, size):
    if not isinstance(value, str):
        raise ValueError('Missing raw API bytes')
    try:
        result = bytes.fromhex(value)
    except ValueError as error:
        raise ValueError('Malformed API bytes') from error
    if len(result) != size:
        raise ValueError('API structure size mismatch')
    return result


def descriptor(info):
    if info is None:
        return None
    if info['hresult'] < 0:
        if info['raw'] is not None:
            raise ValueError('Failed descriptor contains assumed output')
        return {'hresult': info['hresult']}
    data = raw(info['raw'], 124)
    if struct.unpack_from('<I', data)[0] != 124:
        raise ValueError('DDSURFACEDESC2 dwSize mismatch')
    return {'hresult': info['hresult'], 'descriptor_flags': struct.unpack_from('<I', data, 4)[0],
            'width': struct.unpack_from('<I', data, 12)[0], 'height': struct.unpack_from('<I', data, 8)[0],
            'caps': struct.unpack_from('<I', data, 104)[0],
            'pixel_format_flags': struct.unpack_from('<I', data, 76)[0],
            'pixel_format_bits_union': struct.unpack_from('<I', data, 84)[0]}


def inspect(path, authored=False):
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    if len(rows) < 2 or len(rows) > 4098:
        raise ValueError('Incomplete or over-budget surface interval')
    begin, end = rows[0], rows[-1]
    if begin['event'] != 'begin' or begin['schema_version'] != 1 or end['event'] != 'end':
        raise ValueError('Missing interval boundaries')
    if begin['live'] is not (not authored):
        raise ValueError('Live/authored scope mismatch')
    if begin['diagnostic_only'] is not True or begin['command_coverage_complete'] is not False:
        raise ValueError('Overstated coverage')
    if end['boundary_matches'] is not True or end['hresult'] < 0 or begin['primary'] != end['primary']:
        raise ValueError('Closing flip does not match')
    if any(row['seq'] != i + 1 or row['pid'] != begin['pid'] or row['tid'] != begin['tid']
           for i, row in enumerate(rows)):
        raise ValueError('Mixed or reordered interval')
    operations = rows[1:-1]
    if end['operations'] != len(operations):
        raise ValueError('Operation count mismatch')
    decoded = []
    for ordinal, row in enumerate(operations, 1):
        if row['event'] != 'operation' or row['ordinal'] != ordinal or row['method'] not in METHODS:
            raise ValueError('Unknown or reordered surface operation')
        destination = descriptor(row['destination_info'])
        source = descriptor(row['source_info'])
        if not row['destination'] or destination is None or bool(row['source']) != (source is not None):
            raise ValueError('Surface identity/descriptor mismatch')
        rects = {}
        for key in ('destination_rectangle', 'source_rectangle'):
            rects[key] = list(struct.unpack('<4i', raw(row[key], 16))) if row[key] is not None else None
        effects = raw(row['effects'], 100) if row['effects'] is not None else None
        if effects is not None and struct.unpack_from('<I', effects)[0] != 100:
            raise ValueError('DDBLTFX dwSize mismatch')
        output = row['output']
        expected = 124 if row['method'] == 'Lock' else 4 if row['method'] == 'GetDC' else 0
        if row['hresult'] < 0 or not expected:
            if output is not None:
                raise ValueError('Unexpected or failed-call output')
        else:
            raw(output, expected)
        depth_fill = row['method'] == 'Blt' and bool(row['flags'] & DEPTHFILL)
        if depth_fill and effects is None:
            raise ValueError('Depth fill missing effects input')
        decoded.append({'ordinal': ordinal, 'method': row['method'], 'hresult': row['hresult'],
                        'destination': row['destination'], 'source': row['source'], 'flags': row['flags'],
                        'destination_info': destination, 'source_info': source, **rects,
                        'x': row['x'], 'y': row['y'], 'depth_fill': depth_fill,
                        'completed_scenes': row.get('completed_scenes'), 'successful_draws': row.get('successful_draws'),
                        'scene_open': row.get('scene_open'),
                        'fill_depth': struct.unpack_from('<I', effects, 80)[0] if depth_fill else None})
    return {'scope': 'Observed API inputs/results in one flip interval; unobserved aliases and pixel writes remain open',
            'diagnostic_only': True, 'command_coverage_complete': False, 'live': not authored,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'pid': begin['pid'], 'operations': len(decoded),
            'methods': dict(Counter(row['method'] for row in decoded)),
            'depth_destination_operations': sum(bool(row['destination_info'].get('caps', 0) & ZBUFFER) for row in decoded),
            'successful_depth_fills': sum(row['depth_fill'] and row['hresult'] >= 0 for row in decoded),
            'decoded': decoded}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('--authored', action='store_true')
    args = parser.parse_args()
    print(json.dumps(inspect(args.path, args.authored), indent=2))
