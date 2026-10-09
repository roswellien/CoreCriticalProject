"""Deterministic, fail-closed static inventory/source association checker.

This checker reads existing records and original PE bytes. It does not execute
original/provider/native code and does not claim whole transitive closure.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/analysis'))
from pe import PEImage

ADMITTED = {
    'game': '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf',
    'mfc42_staged': '5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8',
    'msvcrt_staged': '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7',
    'localization': '8899fabb7e57383a9a483cb048636bcc027334b48941aa49835cdcc1c4715b8c',
}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def value_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def identity(path):
    data = path.read_bytes()
    return {'path': str(path), 'size_bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def pointer(document, path):
    value = document
    if path:
        need(path.startswith('/'), 'Invalid source JSON pointer')
        for component in path[1:].split('/'):
            component = component.replace('~1', '/').replace('~0', '~')
            value = value[int(component)] if isinstance(value, list) else value[component]
    return value


def graph_cycles(graph):
    """Sorted Tarjan SCCs, retaining only actual cycles (including self edges)."""
    vertices = sorted(set(graph) | {x for values in graph.values() for x in values})
    index, low, stack, active, answer = {}, {}, [], set(), []
    def visit(vertex):
        index[vertex] = low[vertex] = len(index)
        stack.append(vertex); active.add(vertex)
        for target in sorted(set(graph.get(vertex, []))):
            if target not in index:
                visit(target); low[vertex] = min(low[vertex], low[target])
            elif target in active:
                low[vertex] = min(low[vertex], index[target])
        if low[vertex] == index[vertex]:
            group = []
            while True:
                item = stack.pop(); active.remove(item); group.append(item)
                if item == vertex: break
            group.sort()
            if len(group) > 1 or vertex in graph.get(vertex, []): answer.append(group)
    for vertex in vertices:
        if vertex not in index: visit(vertex)
    return sorted(answer)


def topological_order(batches):
    ids = [b['id'] for b in batches]
    need(len(ids) == len(set(ids)), 'Duplicate batch identity')
    dependencies = {b['id']: set(b['depends_on']) for b in batches}
    need(all(d <= set(ids) for d in dependencies.values()), 'Unknown batch dependency')
    result = []
    while len(result) < len(ids):
        ready = sorted(key for key in dependencies if key not in result and dependencies[key] <= set(result))
        need(bool(ready), 'Integration dependency cycle')
        result.extend(ready)
    return result


def load_sources(inventory):
    receipts, actual = {}, {}
    for key, pin in inventory['receipts'].items():
        path = Path(pin['path'])
        actual[key] = identity(path)
        need(actual[key] == pin, 'Changed source receipt ' + key)
        receipts[key] = json.loads(path.read_text())
    images, image_actual = {}, {}
    for key, pin in inventory['images'].items():
        need(key in ADMITTED and pin['sha256'] == ADMITTED[key], 'Unadmitted image ' + key)
        path = Path(pin['path']); image_actual[key] = identity(path)
        need(image_actual[key] == pin, 'Changed image ' + key)
        images[key] = PEImage(path.read_bytes())
    need(set(images) == set(ADMITTED), 'Missing admitted image')
    return receipts, actual, images, image_actual


def validate(inventory, sources):
    receipts, actual, images, image_actual = sources
    need(inventory['schema_version'] == 1, 'Unsupported schema')
    need(inventory['receipts'] == actual, 'Receipt identity substitution')
    need(inventory['images'] == image_actual, 'Image identity substitution')
    need(all(pin['sha256'] == ADMITTED[key] for key, pin in inventory['images'].items()), 'Unadmitted image hash')
    for key, document in receipts.items():
        for image_field in ['image', 'game']:
            if image_field in document:
                need(document[image_field] == inventory['images']['game'], 'Receipt game identity mismatch: ' + key)
    need(receipts['app']['provider'] == receipts['menu']['provider'] == inventory['images']['mfc42_staged'], 'Exact staged MFC identity mismatch')
    mfc_snapshot = receipts['mfc']['provider_snapshots'][0]
    need(all(mfc_snapshot[k] == inventory['images']['mfc42_staged'][k] for k in ['path', 'size_bytes', 'sha256']), 'MFC snapshot identity mismatch')
    need(receipts['handoff']['localization_provider']['identity'] == inventory['images']['localization'], 'Localization provider identity mismatch')
    counts = {'source_refs': 0, 'original_instruction_rows': 0, 'original_instruction_bytes': 0, 'table_words': 0}
    def referenced(ref):
        need(ref['receipt'] in receipts, 'Unknown source receipt')
        value = pointer(receipts[ref['receipt']], ref['pointer'])
        need(value_hash(value) == ref['value_sha256'], 'Source reference value mismatch')
        counts['source_refs'] += 1
        return value
    def instruction(image_key, row):
        image = images[image_key]
        raw = bytes.fromhex(row['bytes'])
        need(len(raw) == row['size'], 'Instruction size mismatch')
        offset = image.rva_range(row['pc'] - image.image_base, row['size'])[0]
        need(image.data[offset:offset + row['size']] == raw, 'Original instruction byte mismatch')
        if 'file_offset' in row: need(row['file_offset'] == offset, 'Original source file offset mismatch')
        if 'sha256' in row: need(hashlib.sha256(raw).hexdigest() == row['sha256'], 'Original row SHA mismatch')
        counts['original_instruction_rows'] += 1; counts['original_instruction_bytes'] += len(raw)
    body_by_entry, call_refs, expected_edges = {}, {}, []
    need(len(inventory['bodies']) == len({b['entry_va'] for b in inventory['bodies']}), 'Duplicate selected body')
    for body in inventory['bodies']:
        original = referenced(body['source'])
        need(body['entry_va'] == original['entry_va'], 'Body entry substitution')
        need(body['instruction_count'] == original['instruction_count'] == len(original['instructions']), 'Body instruction count mismatch')
        need(body['call_count'] == len(original.get('calls', [])), 'Body call count mismatch')
        need(body['closure_limit'] == original.get('closure_limit', 'Bounded original source record; called-body and dynamic effects remain separate.'), 'Body closure limitation changed')
        need(body['image'] == ('mfc42_staged' if body['entry_va'] >= 0x5f400000 else 'game'), 'Body image domain mismatch')
        need(body['cfg_cycles'] == graph_cycles({int(k): v for k, v in original.get('edges', {}).items()}), 'Unmarked or incorrect CFG cycle')
        body_by_entry[body['entry_va']] = original
        for row in original['instructions']: instruction(body['image'], row)
        for i, call in enumerate(original.get('calls', [])):
            call_refs[(body['source']['receipt'], body['source']['pointer'] + '/calls/' + str(i))] = (body, call)
    requested = sorted({r for b in inventory['batches'] for r in b['roots']})
    need(set(body_by_entry) | {g['entry_va'] for g in inventory['missing_bodies']} == set(requested), 'Dropped selected root or missing-body marker')
    need(not(set(body_by_entry) & {g['entry_va'] for g in inventory['missing_bodies']}), 'Body marked both present and missing')
    seen = set(); call_graph = {key: [] for key in body_by_entry}
    for edge in inventory['source_edges']:
        key = (edge['source']['receipt'], edge['source']['pointer'])
        need(key in call_refs and key not in seen, 'Unknown or duplicate source call edge')
        seen.add(key); body, call = call_refs[key]
        need(referenced(edge['source']) == edge['record'] == call, 'Source call projection mismatch')
        need(edge['caller_entry'] == body['entry_va'] and edge['image'] == body['image'], 'Call owner/domain substitution')
        imported = call.get('import') or call.get('iat_thunk') or call.get('direct_iat')
        kind = 'import' if imported else ('direct' if call.get('target_va') is not None else 'unresolved_indirect')
        need(edge['kind'] == kind, 'Call classification mismatch')
        need(edge['target_in_selected_inventory'] == (call.get('target_va') in requested), 'Call frontier classification mismatch')
        need(edge['native_route_admitted'] is False, 'Static call has invented native credit')
        row = next((r for r in body_by_entry[edge['caller_entry']]['instructions'] if r['pc'] == call['pc']), None)
        need(row is not None and row['mnemonic'] == 'call' and row['operands'] == call['operands'], 'Call does not match exact instruction')
        raw = bytes.fromhex(row['bytes'])
        if raw[0] == 0xe8:
            target = (row['pc'] + 5 + struct.unpack('<i', raw[1:5])[0]) & 0xffffffff
            need(target == call.get('target_va'), 'Decoded direct CALL target mismatch')
        if kind == 'direct' and call['target_va'] in call_graph: call_graph[edge['caller_entry']].append(call['target_va'])
    need(seen == set(call_refs), 'Dropped call frontier')
    need(inventory['selected_direct_call_cycles'] == graph_cycles(call_graph), 'Unmarked selected call graph cycle')
    for link in inventory['critical_links']:
        need(referenced(link['source']) == link['record'], 'Critical source link mismatch')
        instruction(link['image'], link['record'])
    for word in inventory['table_words']:
        record = referenced(word['source'])
        allowed = []
        if word['source']['receipt'] == 'app' and word['source']['pointer'] == '/initializer_root':
            allowed = [(record['slot_va'], record['target_va'])]
        elif word['source']['receipt'] == 'app' and word['source']['pointer'].startswith('/application_vtable/slots/'):
            allowed = [(receipts['app']['application_vtable']['va'] + record['offset'], record['target_va'])]
        elif word['source']['receipt'] == 'focused' and '/vtable_stores/' in word['source']['pointer']:
            allowed = [(record['table_va'] + x['offset'], x['target_va']) for x in record['slots']]
        elif word['source']['receipt'] == 'focused' and word['source']['pointer'].startswith('/state_links/'):
            allowed = [(x, record['wrapper_va']) for x in record['static_constructor_slot_vas']]
        elif word['source']['receipt'] == 'handoff' and word['source']['pointer'].startswith('/retail_menu_actions/'):
            allowed = [(record['final_vtable_va'] + record['slot'], record['target_va'])]
        need(word['image'] == 'game' and (word['va'], word['value']) in allowed, 'Table word is not linked to its source record')
        image = images[word['image']]; offset = image.rva_range(word['va'] - image.image_base, 4)[0]
        need(struct.unpack_from('<I', image.data, offset)[0] == word['value'], 'Original slot/vtable word mismatch')
        counts['table_words'] += 1
    for section in ['source_path', 'failure_branches']:
        need(len(inventory[section]) == len(receipts['handoff']['conditional_default_retail_path' if section == 'source_path' else 'startup_failure_branches']), 'Dropped conditional path/failure branch')
        for i, row in enumerate(inventory[section]):
            field = 'conditional_default_retail_path' if section == 'source_path' else 'startup_failure_branches'
            need(row['source']['receipt'] == 'handoff' and row['source']['pointer'] == '/' + field + '/' + str(i), 'Conditional source order/substitution mismatch')
            need(referenced(row['source']) == row['record'], 'Conditional source record mismatch')
    need(len(inventory['linear_startup_regions']) == 2, 'Dropped linear startup source region')
    for key, region in zip(['winmain_argument_forwarder', 'mfc_winmain_import_thunk'], inventory['linear_startup_regions']):
        need(region['source']['receipt'] == 'startup' and region['source']['pointer'] == '/regions/' + key, 'Startup region substitution')
        need(referenced(region['source']) == region['record'], 'Linear startup source mismatch')
        for row in region['record']['instructions']:
            instruction('game', dict(row, pc=row['va']))
    order = topological_order(inventory['batches'])
    need(inventory['integration_topological_order'] == order, 'Incorrect deterministic integration order')
    for b in inventory['batches']:
        need(bool(b['unknowns']) and bool(b['next_deliverable']) and bool(b['integration_gate']), 'Batch missing actionable blocker/gate')
        need(b['implementation_status'] == 'not_admitted_by_this_workahead', 'Invented batch implementation credit')
        need(type(b['preparation_priority']) is int and 0 <= b['preparation_priority'] <= 7, 'Invalid batch priority')
    priorities = {b['id']: b['preparation_priority'] for b in inventory['batches']}
    need(inventory['priority_order'] == sorted(priorities, key=lambda key: (priorities[key], key)), 'Incorrect priority order')
    need(len(inventory['batch_frontiers']) == len(inventory['batches']), 'Dropped batch frontier')
    for b, frontier in zip(inventory['batches'], inventory['batch_frontiers']):
        need(frontier['batch'] == b['id'], 'Batch frontier association changed')
        selected = [i for i, e in enumerate(inventory['source_edges']) if e['caller_entry'] in b['roots']]
        need(frontier['source_edge_indices'] == selected, 'Dropped or substituted batch source edge')
        need(frontier['missing_body_entries'] == [g['entry_va'] for g in inventory['missing_bodies'] if g['entry_va'] in b['roots']], 'Dropped batch source gap')
        for field, predicate in [('unresolved_indirect_edge_indices', lambda e: e['kind'] == 'unresolved_indirect'),
                                 ('import_edge_indices', lambda e: e['kind'] == 'import'),
                                 ('outside_direct_edge_indices', lambda e: e['kind'] == 'direct' and not e['target_in_selected_inventory'])]:
            need(frontier[field] == [i for i in selected if predicate(inventory['source_edges'][i])], 'Batch unresolved frontier mismatch')
    need(inventory['parallel_preparation_batches'] == [b['id'] for b in inventory['batches'] if b['preparation_readiness'] == 'contract_preparation_now'], 'Parallel readiness mismatch')
    credit = inventory['native_credit']
    need(credit == {'new_original_execution': False, 'new_native_execution': False, 'application_window_implemented': False,
                    'retail_menu_implemented': False, 'complete_application_closure': False, 'host_asset_parser_only': True, 'resource147_is_retail_menu': False}, 'Unsupported application/menu execution claim')
    crt = inventory['reusable_accepted_prerequisites']['crt']; old = referenced(crt['source'])
    need(old['passed'] is True and crt['selected_initializer_roots'] == old['connected_initializer_roots'] == 27, 'CRT selected gate mismatch')
    need(crt['full_CRT'] is old['full_CRT'] is False and crt['actual_main_table_composed'] is old['entry_and_selected_main_table_composed_together'] is False, 'Full CRT/main table credit invented')
    need(crt['next_required_import'] == old['next_required_import'], 'CRT boundary changed')
    host = inventory['reusable_accepted_prerequisites']['host_assets']; previous = referenced(host['source'])
    need(previous['passed'] is True and host['directory_records'] == previous['directory_records'] == 178 and host['tokens'] == previous['tokens'] == 14925, 'Accepted host asset scope mismatch')
    counts.update({'batches': len(inventory['batches']), 'selected_bodies': len(inventory['bodies']),
                   'missing_bodies': len(inventory['missing_bodies']), 'source_edges': len(inventory['source_edges']),
                   'unresolved_indirect_edges': sum(e['kind'] == 'unresolved_indirect' for e in inventory['source_edges']),
                   'import_edges': sum(e['kind'] == 'import' for e in inventory['source_edges']),
                   'direct_edges_outside_selected_roots': sum(e['kind'] == 'direct' and not e['target_in_selected_inventory'] for e in inventory['source_edges']),
                   'body_CFG_cycle_groups': sum(len(b['cfg_cycles']) for b in inventory['bodies']),
                   'selected_call_cycle_groups': len(inventory['selected_direct_call_cycles'])})
    return counts


def controls(inventory, sources):
    cases = [
        ('wrong-admitted-game', lambda x: x['images']['game'].__setitem__('sha256', '0' * 64)),
        ('call-target-substitution', lambda x: x['source_edges'][0]['record'].__setitem__('target_va', 0x480001)),
        ('dropped-call-frontier', lambda x: x['source_edges'].pop()),
        ('middle-instruction-body', lambda x: x['bodies'][0].__setitem__('entry_va', x['bodies'][0]['entry_va'] + 1)),
        ('wrong-source-json-pointer', lambda x: x['critical_links'][0]['source'].__setitem__('pointer', '/critical_link_instructions/1')),
        ('vtable-target-substitution', lambda x: x['table_words'][0].__setitem__('value', 0x480001)),
        ('integration-cycle', lambda x: x['batches'][0]['depends_on'].append('retail-menu')),
        ('wrong-topological-order', lambda x: x['integration_topological_order'].reverse()),
        ('static-native-success', lambda x: x['source_edges'][0].__setitem__('native_route_admitted', True)),
        ('resource147-retail-credit', lambda x: x['native_credit'].__setitem__('resource147_is_retail_menu', True)),
        ('dropped-failure-branch', lambda x: x['failure_branches'].pop()),
        ('dropped-batch-frontier', lambda x: x['batch_frontiers'].pop()),
        ('wrong-priority-order', lambda x: x['priority_order'].reverse()),
    ]
    cycling = next(i for i, b in enumerate(inventory['bodies']) if b['cfg_cycles'])
    cases.append(('unmarked-body-CFG-cycle', lambda x: x['bodies'][cycling].__setitem__('cfg_cycles', [])))
    result = []
    for name, change in cases:
        mutated = copy.deepcopy(inventory); change(mutated)
        try: validate(mutated, sources)
        except (ValueError, KeyError, IndexError) as error: result.append({'case': name, 'denied': True, 'reason': str(error)})
        else: raise ValueError('Corruption accepted: ' + name)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--inventory', required=True)
    parser.add_argument('--out')
    parser.add_argument('--controls', action='store_true')
    args = parser.parse_args()
    path = ROOT / args.inventory; inventory = json.loads(path.read_text())
    sources = load_sources(inventory); counts = validate(inventory, sources)
    negative = controls(inventory, sources) if args.controls else []
    result = {'passed': True, 'scope': 'Static source identity, projection, original-byte and work-order consistency only; no new code execution or full application closure.',
              'inventory': identity(path), 'checker': identity(Path(__file__)), 'counts': counts,
              'corruption_denials': negative, 'integration_order': inventory['integration_topological_order']}
    if args.out:
        out = ROOT / args.out
        need(not out.exists(), 'Refuse overwrite checker report directory')
        out.mkdir(parents=True)
        (out / 'report.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
        paths = [path, Path(__file__), Path(__file__).with_name('prepare.py'), ROOT / 'tools/analysis/pe.py', ROOT / 'docs/m4-application-workahead.md']
        paths += [Path(p['path']) for p in inventory['receipts'].values()] + [Path(p['path']) for p in inventory['images'].values()]
        (out / 'pins.json').write_text(json.dumps({'scope': result['scope'], 'bindings': [identity(p) for p in sorted(set(paths))]}, indent=2, sort_keys=True) + '\n')
        print(json.dumps({'report': identity(out / 'report.json'), 'pins': identity(out / 'pins.json'), 'counts': counts, 'corruption_denials': len(negative)}))
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
