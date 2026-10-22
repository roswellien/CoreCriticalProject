"""Exercise authored surface observations and reject malformed/overstated logs."""
import argparse
import copy
import json
from pathlib import Path
import tempfile
from inspect_surface_operations import inspect
from inspect_cpu_surface_writes import inspect as inspect_pixels
from verify_capture import depth_fill_command, cpu_write_regions


def check(path):
    positive = inspect(path, authored=True)
    if positive['operations'] != 10 or positive['successful_depth_fills'] != 1 or positive['depth_destination_operations'] != 8:
        raise ValueError('Missing authored forwarding/diagnostic cases')
    if positive['decoded'][7]['fill_depth'] != 65535:
        raise ValueError('Depth fill union offset is incorrect')
    original = [json.loads(line) for line in path.read_text().splitlines()]
    controls = ('missing_footer', 'mixed_pid', 'mixed_thread', 'wrong_sequence', 'wrong_count',
                'wrong_ordinal', 'wrong_boundary', 'failed_flip', 'overstated_coverage', 'live_scope',
                'unknown_method', 'short_descriptor', 'wrong_descriptor_size', 'short_rectangle',
                'missing_depth_effects', 'wrong_effects_size', 'short_lock_output', 'failed_output', 'missing_surface')
    rejected = []
    with tempfile.TemporaryDirectory(prefix='surface-controls-', dir=path.parent) as temporary:
        candidate = Path(temporary) / 'operations.jsonl'
        for name in controls:
            rows = copy.deepcopy(original)
            if name == 'missing_footer': rows.pop()
            elif name == 'mixed_pid': rows[1]['pid'] += 1
            elif name == 'mixed_thread': rows[1]['tid'] += 1
            elif name == 'wrong_sequence': rows[1]['seq'] += 1
            elif name == 'wrong_count': rows[-1]['operations'] += 1
            elif name == 'wrong_ordinal': rows[1]['ordinal'] += 1
            elif name == 'wrong_boundary': rows[-1]['primary'] += 1
            elif name == 'failed_flip': rows[-1]['hresult'] = -1
            elif name == 'overstated_coverage': rows[0]['command_coverage_complete'] = True
            elif name == 'live_scope': rows[0]['live'] = True
            elif name == 'unknown_method': rows[1]['method'] = 'Invented'
            elif name == 'short_descriptor': rows[1]['destination_info']['raw'] = '00'
            elif name == 'wrong_descriptor_size':
                value = rows[1]['destination_info']['raw']
                rows[1]['destination_info']['raw'] = '00000000' + value[8:]
            elif name == 'short_rectangle': rows[1]['destination_rectangle'] = '00'
            elif name == 'missing_depth_effects': rows[8]['effects'] = None
            elif name == 'wrong_effects_size':
                value = rows[8]['effects']
                rows[8]['effects'] = '00000000' + value[8:]
            elif name == 'short_lock_output': rows[1]['output'] = '00'
            elif name == 'failed_output': rows[5]['output'] = rows[1]['output']
            elif name == 'missing_surface': rows[1]['destination'] = 0
            candidate.write_text(''.join(json.dumps(row) + '\n' for row in rows))
            try:
                inspect(candidate, authored=True)
            except ValueError:
                rejected.append(name)
            else:
                raise AssertionError(f'Invalid observation admitted: {name}')
    pixel_directory = path.parent / 'cpu-command/surface-pixels'
    pixels = inspect_pixels(pixel_directory, authored=True)
    if pixels['writes'] != 1 or pixels['decoded'][0]['changed_pixels'] != 1 or pixels['decoded'][0]['changed_bounds'] != [1, 0, 2, 1]:
        raise ValueError('Authored CPU write delta mismatch')
    cpu_directory = path.parent / 'cpu-command'
    cpu_rows = [json.loads(line) for line in (cpu_directory / 'cpu-command-fixture.jsonl').read_text().splitlines()]
    if len(cpu_rows) != 1:
        raise ValueError('CPU fixture command count')
    cpu = cpu_rows[0]
    before, after = [(cpu_directory / cpu[key]).read_bytes() for key in ('before', 'after')]
    if cpu_write_regions(cpu, 2, 2, before, after) != [(1, 0, 1, 1)] or before != bytes(8) or after != bytes.fromhex('0000e00700000000'):
        raise ValueError('CPU command changed unchanged pixels')
    cpu_rejected = []
    for key, value in (('format', 'RGBA8'), ('unlock_hresult', -1), ('width', 3), ('source_pitch', 1)):
        try:
            cpu_write_regions(dict(cpu, **{key: value}), 2, 2, before, after)
        except ValueError:
            cpu_rejected.append(key)
        else:
            raise AssertionError('Unsupported CPU write admitted')
    command_directory = path.parent / 'depth-command'
    commands = [json.loads(line) for line in (command_directory / 'depth-command-fixture.jsonl').read_text().splitlines()]
    if len(commands) != 1:
        raise ValueError('Depth fixture command count')
    command = commands[0]
    effects = (command_directory / command['effects']).read_bytes()
    if depth_fill_command(command, 2, 2, effects) != (2, 2, 0, 0, 2, 2, 0, 0, 0, 0):
        raise ValueError('Depth command translation mismatch')
    depth_rejected = []
    for key, value in (('flags', 0), ('fill_depth', 1), ('bits', 32), ('depth_bits', 1065353216), ('hresult', -1), ('rectangle', [-1, 0, 2, 2])):
        candidate = dict(command, **{key: value})
        try:
            depth_fill_command(candidate, 2, 2, effects)
        except ValueError:
            depth_rejected.append(key)
        else:
            raise AssertionError('Unsupported depth command admitted')
    return {'scope': 'Authored API forwarding/diagnostic format only; no live renderer equivalence',
            'positive_sha256': positive['sha256'], 'positive_operations': positive['operations'],
            'depth_fill': positive['decoded'][7]['fill_depth'], 'rejected_controls': rejected,
            'cpu_write': pixels, 'cpu_command_rejected_controls': cpu_rejected, 'depth_command_rejected_controls': depth_rejected}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.path), indent=2))
