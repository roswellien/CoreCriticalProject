"""Consolidate frozen static records into a bounded application work inventory.

No decoder, compiler, original executable or native game is run. Each projected
body/call retains its original receipt and JSON pointer. This is work planning,
not a new source equivalence or application execution proof.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from check import graph_cycles, topological_order

FILES = {
    'app': 'reports/m4-startup/services/application-chain-report.json',
    'mfc': 'reports/m4-startup/services/mfc-callback-recovery.json',
    'menu': 'reports/m4-startup/services/menu-resource-links.json',
    'handoff': 'reports/m4-application-closure/handoff.json',
    'static_review': 'reports/m4-application-closure/verification.json',
    'bounded': 'reports/m4-application-closure/bounded-graph.json',
    'focused': 'reports/m4-application-closure/frontend-focused-graph.json',
    'services': 'reports/m4-application-closure/service-callback-graph-v2.json',
    'assets': 'reports/m4-assets/recovery-r2/report.json',
    'asset_cfg': 'reports/m4-assets/recovery-r2/exact-reader-widget-cfg.json',
    'asset_host_review': 'reports/m4-assets/independent-root-r1/review.json',
    'initializers': 'reports/m4-initializer-inventory/r1/report.json',
    'crt_cut': 'reports/m4-crt-mainargs/root-acceptance-r1/report.json',
    'startup': 'reports/m4-startup/recovery/report.json',
}


def identity(path):
    data = path.read_bytes()
    return {'path': str(path), 'size_bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def ref(receipt, pointer, value):
    return {'receipt': receipt, 'pointer': pointer,
            'value_sha256': hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}


def batch(key, title, roots, depends, unknowns, deliverable, gate, readiness='contract_preparation_now'):
    return {'id': key, 'title': title, 'roots': roots, 'depends_on': depends,
            'preparation_readiness': readiness, 'implementation_status': 'not_admitted_by_this_workahead',
            'unknowns': unknowns, 'next_deliverable': deliverable, 'integration_gate': gate}


def build():
    docs = {key: json.loads((ROOT / path).read_text()) for key, path in FILES.items()}
    h, a, f, assets = docs['handoff'], docs['app'], docs['focused'], docs['assets']
    # These orders describe implementation prerequisites, not the chronological
    # order of calls. Actual conditional call order remains in source_path below.
    batches = [
        batch('crt-environment', 'CRT arguments, environment, SEH and callback dispatch', [], [],
              ['GetModuleFileNameA producer is the current separate CRT task', 'command-line, locale, allocator/argv/environment and x86 SEH/TLS closure'],
              'Complete the bounded CRT producer/consumer chain without reseeding carried State or pages.',
              'Actual CRT caller reaches the main initializer table with owned services and callback dispatch.', 'external_current_crt_work'),
        batch('provider-state', 'Exact staged MFC module/thread state and object ABI',
              [0x5f401083, 0x5f4021df, 0x5f40aefa, 0x5f40ae1b, 0x5f40afb7, 0x5f40b35d], [],
              ['Actual loaded MFC provider is unobserved; staged and SysWOW64 targets differ',
               'Module/TLS state, FS/SEH helpers, callbacks and allocation/destruction ownership',
               'Application receiver in module-state+4 must be the constructor-owned object'],
              'Recover narrowly missing state/TLS/SEH helper contracts and an exact typed receiver/lifetime ledger.',
              'No ordinal callback executes until exact provider and receiver lifetime contracts pass.'),
        batch('localization-config', 'Localization, registry and working-directory services',
              h['service_implementation_targets'][0]['entries'] + h['service_implementation_targets'][2]['entries'] + [0x575e30], [],
              ['ZLocGetID selected module/output buffers and locale identity',
               'RunDir registry value type/size/access/errors and current-directory/file semantics',
               'Version/online/WSA prerequisite branch values cannot be fabricated'],
              'Group the concrete API contracts and guest buffer/handle ownership from these existing roots.',
              'Success and failure branches match original service observations and exact source order.'),
        batch('application-initializers', 'Application and Intro/Menu state construction',
              [0x47f760, 0x47f770, 0x47f7a0, 0x58fcd0, 0x47f470, 0x482a60, 0x47f4b0, 0x486920, 0x482970],
              ['crt-environment', 'provider-state', 'localization-config'],
              ['Three exact slots are not import-free/native-admitted by the static inventory',
               '_strdup/atexit/localization/MFC effects and object/table mutation order',
               'Factory index12 reads app+1DC dynamically; default index2 remains conditional'],
              'Implement the three main-table slots as one coherent object/state lifetime batch, after prerequisite contracts.',
              'Real initializer dispatcher calls slots5E00E4,5E00E8,5E010C in original table order; constructors preserve ownership and State.'),
        batch('other-initializers', 'Other required main-table initializer closure', [], ['crt-environment'],
              ['117 roots remain outside the selected27 gate; this includes the application/state slots until admitted',
               'Remaining roots need required dependencies, table ordering, SEH/provider effects and native route ownership'],
              'Use the existing144-root inventory to batch independent low-risk roots while preserving actual caller order.',
              'All other required initializer roots complete through actual table dispatch.', 'external_initializer_work'),
        batch('main-table-complete', 'Complete actual main initializer table', [],
              ['application-initializers', 'other-initializers'],
              ['Selected initializer composition and actual full CRT main-table composition are different gates'],
              'Compose full initializer ledger into CRT entry without fake null slots or skipped required constructors.',
              'All144 nonzero roots execute in required order with complete failure/termination closure.', 'integration_blocked'),
        batch('window-frame', 'Native frame and MFC callback/message routing',
              [0x5ae390, 0x5ae3f4, 0x5abe82, 0x480000, 0x47ff90, 0x482d10, 0x590920, 0x590a10, 0x47fa10],
              ['main-table-complete', 'provider-state', 'localization-config', 'archive-reader'],
              ['App+BC frame receiver, app+20/frame+C0 back-reference, HWND lifetime and callback reentrancy',
               'Class registration, module/resource handles and MFC ordinal bridges',
               '24-byte message table signatures/handler ABI and shutdown/exception paths'],
              'First native-window cut: execute the real initialization prefix through frame/window creation and creation callbacks; refuse the next unsupported service without fabricating Init return.',
              'Owned native HWND/frame creation and required creation callbacks/failure cleanup pass; later message-pump/focus/normal quit require service and retail integration.'),
        batch('archive-reader', 'Archive registry, cursor and reader object service ABI',
              sorted(set(assets['archive_registration'] + [0x40c420, 0x556740, 0x5572c0, 0x576ae0, 0x576b40,
                         0x557180, 0x576460, 0x556930, 0x5569e0, 0x5569f0, 0x556a60, 0x556ae0])), [],
              ['Archive registry order, selected entry/cursor/short reads and returned guest allocations',
               'detail.zrd direct open and reader.zbd fallback occur before frame construction',
               'Textual external-file branch; host parser agreement does not implement original guest reader ABI'],
              'Reuse the accepted host directory/tree parser and implement the real guest registry/cursor/read/allocation bridge with typed failure results.',
              'Actual detail.zrd/archive loading and typed reader/tree objects satisfy the pre-frame prefix without fabricated defaults.'),
        batch('widget-properties', 'Inherited typed-property and named widget ABI',
              sorted(set(assets['menu_section_binding'] + assets['named_widget_binding'] +
                         [0x59f010, 0x59f050, 0x59f080, 0x59cdc0, 0x59f810, 0x59f8b0, 0x59f8d0, 0x59fa10])), ['archive-reader'],
              ['Inherited widget loader status/default behavior and text/locale branches',
               'Root+128/12C ownership and widget+84/+88 receiver/font/bitmap/primitive lifetimes',
               'Actual float accessor/x87 conversion and dynamic callbacks remain unresolved'],
              'Prepare exact inherited property branches and guest section/widget ownership in parallel with CRT/backend work.',
              'dialog.zrd MAINMENU and seven named bindings are consumed by actual translated guest widget paths.'),
        batch('video', 'Menu graphics and presentation service contracts',
              h['service_implementation_targets'][4]['entries'], [],
              ['DirectDrawCreate/QueryInterface provider, COM slots and object809358 ownership',
               'Stored callback table809324/809344/72F364 lifetime',
               'Surface format/lock/pitch/palette/cooperative mode/GDI and conditional HSE status branches'],
              'Prepare exact callback/COM/interface contracts and the narrow renderer needed for the menu.',
              'Actual required graphics path draws/presents menu assets with truthful HRESULT/failure and destruction semantics.'),
        batch('input-audio', 'Menu input and audio/CD service contracts',
              h['service_implementation_targets'][5]['entries'] + h['service_implementation_targets'][6]['entries'], [],
              ['DirectInput object638578/device638594 format/cooperative/buffer/acquire/read/focus semantics',
               'Conditional COM DirectSound route versus DSOUND ordinal1; buffer/interface lifetimes',
               'MCI/CD/audio-quality branches and assets; required path cannot be replaced by unconditional success'],
              'Prepare keyboard/mouse and menu sound contracts in parallel; retain optional branch conditions and failures.',
              'Actual input/focus and required audio route work and clean up with observed statuses.'),
        batch('service-callback', 'Application services and startup state queue',
              [0x58fc70, 0x480570, 0x58fd70, 0x590230, 0x590250, 0x482070, 0x482170],
              ['window-frame', 'archive-reader', 'video', 'input-audio'],
              ['App+AC must return success after required services; resource147 is explicitly removed',
               'Queue records/type3 dispatch, receiver lifetime and original timer/x87/_ftol semantics',
               'Intro/splash or actual -nofmv path; command-line selection and app+1DC mutation unobserved'],
              'Compose app services and the startup state transitions using exact typed queue/callback routes.',
              'Real state608F58 dispatch reaches default/current app+1DC608F00 without inventing completion or command-line flags.', 'integration_blocked'),
        batch('retail-menu', 'Retail MAINMENU construction, update and seven actions',
              [0x486990, 0x486260, 0x486d40, 0x48ed30, 0x5a2bb0, 0x59fa60] + [x['target_va'] for x in h['retail_menu_actions']],
              ['service-callback', 'widget-properties', 'video', 'input-audio'],
              ['MAINMENU parse false still permits constructor return; allocation alone is not readiness',
               'Child list/vtable hit-test/update/render receivers and callbacks need typed ownership',
               'Directed original/native menu input trace, visible presentation, focus and clean shutdown'],
              'Compose the real menu state/widget path and verify directed menu navigation and quit.',
              'Native retail menu renders and accepts required input with all source/service/failure checks; gameplay is a later milestone.', 'integration_blocked'),
    ]
    # Prefer narrowly recovered exact asset CFGs, then dedicated provider/application
    # records, then focused/service/bounded discovery. No transitive reinventory.
    body_sources = [('asset_cfg', '/bodies'), ('app', '/game_cfgs'), ('app', '/provider_constructor_cfgs'),
                    ('mfc', '/provider_cfgs'), ('menu', '/frame_constructor_cfg'),
                    ('menu', '/provider_table_search_cfg'), ('menu', '/provider_table_dispatch_cfg'),
                    ('focused', '/bodies'), ('services', '/bodies'), ('bounded', '/bodies')]
    lookup = {}
    for receipt, pointer in body_sources:
        value = docs[receipt][pointer[1:]]
        records = value if isinstance(value, list) else [value]
        for i, body in enumerate(records):
            p = pointer + '/' + str(i) if isinstance(value, list) else pointer
            lookup.setdefault(body['entry_va'], (receipt, p, body))
    for i, state in enumerate(f['state_links']):
        lookup.setdefault(state['constructor_va'], ('focused', f'/state_links/{i}/constructor_cfg', state['constructor_cfg']))
    for i, action in enumerate(h['retail_menu_actions']):
        lookup.setdefault(action['target_va'], ('handoff', f'/retail_menu_actions/{i}/callback_cfg', action['callback_cfg']))
    # The exact initializer wrappers are also recovered within the original main
    # table graph. Keep their source linkage even when no body projection is present.
    requested = sorted({r for b in batches for r in b['roots']})
    bodies, edges, gaps = [], [], []
    for address in requested:
        if address not in lookup:
            gaps.append({'entry_va': address, 'reason': 'No selected exact body record; explicit discovery prerequisite, not a fabricated body.'})
            continue
        receipt, pointer, body = lookup[address]
        cfg = {int(k): v for k, v in body.get('edges', {}).items()}
        image = 'mfc42_staged' if address >= 0x5f400000 else 'game'
        bodies.append({'entry_va': address, 'image': image, 'source': ref(receipt, pointer, body),
                       'instruction_count': body['instruction_count'], 'call_count': len(body.get('calls', [])),
                       'closure_limit': body.get('closure_limit', 'Bounded original source record; called-body and dynamic effects remain separate.'),
                       'cfg_cycles': graph_cycles(cfg)})
        for i, call in enumerate(body.get('calls', [])):
            imported = call.get('import') or call.get('iat_thunk') or call.get('direct_iat')
            kind = 'import' if imported else ('direct' if call.get('target_va') is not None else 'unresolved_indirect')
            edges.append({'caller_entry': address, 'image': image, 'source': ref(receipt, pointer + '/calls/' + str(i), call),
                          'record': call, 'kind': kind, 'target_in_selected_inventory': call.get('target_va') in requested,
                          'native_route_admitted': False})
    call_graph = {x['entry_va']: [] for x in bodies}
    for e in edges:
        if e['kind'] == 'direct' and e['record']['target_va'] in call_graph:
            call_graph[e['caller_entry']].append(e['record']['target_va'])
    words = [{'image': 'game', 'va': a['initializer_root']['slot_va'], 'value': a['initializer_root']['target_va'],
              'source': ref('app', '/initializer_root', a['initializer_root'])}]
    for slot in a['application_vtable']['slots']:
        if slot['offset'] in [0x58, 0x5c, 0x70, 0x8c]:
            i = a['application_vtable']['slots'].index(slot)
            words.append({'image': 'game', 'va': a['application_vtable']['va'] + slot['offset'], 'value': slot['target_va'],
                          'source': ref('app', '/application_vtable/slots/' + str(i), slot)})
    for state_index in [1, 2]:
        state = f['state_links'][state_index]
        for va in state['static_constructor_slot_vas']:
            words.append({'image': 'game', 'va': va, 'value': state['wrapper_va'],
                          'source': ref('focused', f'/state_links/{state_index}', state)})
        table = state['vtable_stores'][-1]
        for slot in table['slots'][:5]:
            if slot['offset'] in [0xc, 0x10]:
                words.append({'image': 'game', 'va': table['table_va'] + slot['offset'], 'value': slot['target_va'],
                              'source': ref('focused', f'/state_links/{state_index}/vtable_stores/{len(state["vtable_stores"])-1}', table)})
    for i, action in enumerate(h['retail_menu_actions']):
        words.append({'image': 'game', 'va': action['final_vtable_va'] + action['slot'], 'value': action['target_va'],
                      'source': ref('handoff', '/retail_menu_actions/' + str(i), action)})
    priorities = {'crt-environment': 0, 'provider-state': 1, 'archive-reader': 1,
                  'localization-config': 2, 'widget-properties': 2, 'video': 2, 'input-audio': 2,
                  'application-initializers': 3, 'other-initializers': 3, 'main-table-complete': 4,
                  'window-frame': 5, 'service-callback': 6, 'retail-menu': 7}
    for b in batches:
        b['preparation_priority'] = priorities[b['id']]
    frontiers = []
    for b in batches:
        selected = [i for i, e in enumerate(edges) if e['caller_entry'] in b['roots']]
        frontiers.append({'batch': b['id'], 'source_edge_indices': selected,
                          'missing_body_entries': [g['entry_va'] for g in gaps if g['entry_va'] in b['roots']],
                          'unresolved_indirect_edge_indices': [i for i in selected if edges[i]['kind'] == 'unresolved_indirect'],
                          'import_edge_indices': [i for i in selected if edges[i]['kind'] == 'import'],
                          'outside_direct_edge_indices': [i for i in selected if edges[i]['kind'] == 'direct' and not edges[i]['target_in_selected_inventory']]})
    return {
        'schema_version': 1,
        'scope': 'Bounded static application/menu dependency preparation; no new decoder, native/original execution or implementation credit.',
        'images': {'game': a['image'], 'mfc42_staged': a['provider'], 'msvcrt_staged': identity(ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'),
                   'localization': h['localization_provider']['identity']},
        'receipts': {key: identity(ROOT / path) for key, path in FILES.items()},
        'source_path': [{'source': ref('handoff', '/conditional_default_retail_path/' + str(i), value), 'record': value}
                        for i, value in enumerate(h['conditional_default_retail_path'])],
        'critical_links': [{'image': 'mfc42_staged' if value['pc'] >= 0x5f400000 else 'game',
                            'source': ref(receipt, '/' + key + '/' + str(i), value), 'record': value}
                           for receipt, key in [('handoff', 'critical_link_instructions'), ('app', 'provider_state_link_instructions'), ('menu', 'exact_link_instructions')]
                           for i, value in enumerate(docs[receipt][key])],
        'table_words': words,
        'bodies': bodies, 'source_edges': edges, 'missing_bodies': gaps,
        'selected_direct_call_cycles': graph_cycles(call_graph),
        'linear_startup_regions': [{'source': ref('startup', '/regions/' + key, docs['startup']['regions'][key]),
                                    'record': docs['startup']['regions'][key],
                                    'limit': 'Exact bounded linear bytes; this projection grants no called-provider or application execution credit.'}
                                   for key in ['winmain_argument_forwarder', 'mfc_winmain_import_thunk']],
        'batches': batches, 'integration_topological_order': topological_order(batches),
        'batch_frontiers': frontiers,
        'priority_order': sorted([b['id'] for b in batches], key=lambda key: (priorities[key], key)),
        'parallel_preparation_batches': [b['id'] for b in batches if b['preparation_readiness'] == 'contract_preparation_now'],
        'earliest_native_window_cut': ['crt-environment', 'provider-state', 'localization-config', 'archive-reader', 'application-initializers',
                                      'other-initializers', 'main-table-complete', 'window-frame'],
        'retail_menu_additional_batches': ['widget-properties', 'video', 'input-audio', 'service-callback', 'retail-menu'],
        'native_credit': {'new_original_execution': False, 'new_native_execution': False, 'application_window_implemented': False,
                          'retail_menu_implemented': False, 'complete_application_closure': False,
                          'host_asset_parser_only': True, 'resource147_is_retail_menu': False},
        'reusable_accepted_prerequisites': {
            'crt': {'source': ref('crt_cut', '', docs['crt_cut']), 'selected_initializer_roots': docs['crt_cut']['connected_initializer_roots'],
                    'full_CRT': docs['crt_cut']['full_CRT'], 'actual_main_table_composed': docs['crt_cut']['entry_and_selected_main_table_composed_together'],
                    'next_required_import': docs['crt_cut']['next_required_import']},
            'host_assets': {'source': ref('asset_host_review', '', docs['asset_host_review']), 'directory_records': docs['asset_host_review']['directory_records'],
                            'tokens': docs['asset_host_review']['tokens'], 'scope': docs['asset_host_review']['scope']}},
        'failure_branches': [{'source': ref('handoff', '/startup_failure_branches/' + str(i), x), 'record': x}
                             for i, x in enumerate(h['startup_failure_branches'])],
        'dynamic_ownership_limits': [
            'Staged MFC42 is an exact static contract candidate; actual Windows provider selection and runtime callback receiver are unobserved.',
            'An import/name/ordinal or vtable word establishes a static target; it does not authorize a native service or a valid current receiver.',
            'Body CFG loops and selected direct-call SCCs are marked; batch ordering is prerequisite planning, not a proof of acyclic runtime execution.',
            'Call frontiers are complete only for the selected body records; bounded discovery and inherited provider helpers remain incomplete.',
            'No command-line -nofmv injection, fake initializer return or fabricated successful API/parser/interface result is admitted.',
            'Topological order is conditional on completing each batch gate and is not a calendar ETA or claimed minimal complete call closure.',
        ],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    path = ROOT / args.out
    if path.exists():
        raise SystemExit('Refuse overwrite of workahead inventory')
    path.parent.mkdir(parents=True, exist_ok=True)
    result = build()
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'inventory': identity(path), 'batches': len(result['batches']), 'bodies': len(result['bodies']), 'source_edges': len(result['source_edges'])}))
