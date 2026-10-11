"""Authenticate the first genuine original tree prefix without seeded effects."""
from pathlib import Path
import collections, hashlib, importlib.util, json, struct, sys, traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-tree-original'
PINS = {}

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def need(value, message):
    if not value:
        raise ValueError(message)

def pin(path, expected=None):
    path = Path(path).resolve(); actual = sha(path)
    need(expected is None or actual == expected, 'Exact physical input ' + str(path))
    need(str(path) not in PINS or PINS[str(path)] == actual, 'Stable source identity')
    PINS[str(path)] = actual
    return path

def read(path, expected=None):
    return json.loads(pin(path, expected).read_text(encoding='utf-8-sig'))

def words(data, offset=0, count=1):
    return struct.unpack_from('<' + 'I' * count, data, offset)

def main(execution_path, execution_digest, name):
    out = BASE / name; need(not out.exists(), 'Fresh additive observations'); out.mkdir(parents=True)
    passed = False; owners = []; locks = []; frames = []; counts = collections.Counter(); tree = {}
    try:
        execution = read(execution_path, execution_digest); need(execution['passed'], 'Actual bounded original execution')
        build = read(execution['build_path'], execution['build_sha256']); need(build['passed'] and build['sequences'] == build['phases'] == 1, 'Exact one-root worker')
        pin(build['worker'], build['worker_sha256'])
        preparation = read(Path(build['preparation']) / 'report.json', build['preparation_sha256'])
        need(preparation['predicted_counts_supplied_to_execution'] is False, 'Counts not seeded')
        spec = importlib.util.spec_from_file_location('tree_original_direct', pin(ROOT / 'tools/m4-crt-allocation-root/run_v2.py'))
        direct = importlib.util.module_from_spec(spec); spec.loader.exec_module(direct)
        bundle = direct.DirectSet(Path(execution['original_capture']), pin)
        data = bundle.data('phase/0/0.bin'); need(len(data) == 356992, 'Unchanged full original record')
        need(words(data, 0, 9) == (0, 0, 0, 0x5e0168, 0x4b7f70, 0x7f, 0, 0, 1), 'Actual successful tree root and hardware host restoration')
        pages = preparation['observed_pages']; need(len(pages) == 43, 'Complete accepted ordinary page scope')
        def image(side, address, size):
            offset = (2276 if side == 'before' else 178404) + pages.index(address & ~4095) * 4096 + (address & 4095)
            need((address & 4095) + size <= 4096, 'Single whole-page field')
            return data[offset:offset + size]
        need(words(image('before', 0x60b314, 8), 0, 2) == (0, 0), 'Genuine untouched shared header/counter')
        owner_count = words(bundle.data('actual-tree-owner-count.bin'))[0]
        ledger = list(struct.iter_unpack('<26I', bundle.data('phase/0/0/api-ledger.bin')))
        need(words(bundle.data('phase/0/0/api-count.bin'))[0] == len(ledger), 'Complete actual CRT API records')
        site_ordinals = collections.Counter(); pointers = {}
        for index in range(owner_count):
            stem = f'phase/0/0/lockit-allocation/{index}'
            meta = words(bundle.data(stem + '/meta.bin'), 0, 9)
            need(meta[0:3] == (1, index, 0x4b7f70) and meta[3] in (0x4ba306, 0x4ba33c, 0x4bab32), 'Actual dynamic owner site and occurrence')
            need(meta[4] == 24 and meta[7] and meta[8] >= meta[4] and meta[7] not in pointers, 'Positive unique measured owner/capacity')
            api = ledger[meta[6]]
            need(api[24] == 0 and api[10] == meta[7] and api[4] + 104 == meta[5] and api[22] == 24, 'Actual named allocator API result/frame/request')
            initial = bundle.data(f'phase/0/0/api-initial/{meta[6]}/bytes.bin')
            final = bundle.data(stem + '/bytes.bin')
            need(len(initial) == len(final) == meta[8] == words(bundle.data(f'phase/0/0/api-initial/{meta[6]}/size.bin'))[0], 'Complete genuine initial/final owner backing')
            need(initial[24:] == final[24:], 'Untouched complete capacity tail')
            ordinal = site_ordinals[meta[3]]; site_ordinals[meta[3]] += 1
            owner = dict(index=index, generation=index + 1, root=meta[2], CALL_pc=meta[3], site_invocation=ordinal, request=meta[4], source_frame=meta[5], actual_API_index=meta[6], pointer=meta[7], capacity=meta[8], meta=list(meta), initial_hex=initial.hex(), final_hex=final.hex(), object_DWORDs=list(words(final, 0, 6)), actual_source_changed_offsets=[i for i, (a, b) in enumerate(zip(initial, final)) if a != b])
            owners.append(owner); pointers[meta[7]] = index
        counts['actual_allocations'] = owner_count
        for pc, count in site_ordinals.items():
            counts[f'actual_CALL_{pc:x}_invocations'] = count
        snapshots = bundle.data('phase/0/0/lockit-snapshots.bin'); lock_count = words(bundle.data('phase/0/0/lockit-count.bin'))[0]
        need(len(snapshots) == lock_count * 12988, 'Complete raw Lockit snapshots')
        thread = words(bundle.data('lockit/thread.bin'))[0]; depth = 0; maximum_depth = 0; call_occurrence = 0
        for index in range(lock_count):
            snapshot = snapshots[index * 12988:(index + 1) * 12988]
            header = words(snapshot, 0, 16); cpu = words(snapshot, 64, 10); cs = words(snapshot, 676, 6); kind = header[3]
            need(header[0] == 1 and header[1] == index and header[2] == 0x4b7f70 and header[6] == thread and header[7] == 2, 'Actual authentic loaded domain/current thread')
            need(kind in range(6), 'Declared actual Lockit snapshot kind')
            if kind in (0, 3):
                call_occurrence += 1
            if kind == 2:
                depth += 1
            elif kind == 5:
                depth -= 1
            need(depth >= 0 and cs[2] == depth and cs[3] == (thread if depth else 0), 'Measured balanced semantic recursion/current thread')
            maximum_depth = max(maximum_depth, depth)
            locks.append(dict(index=index, call_occurrence=call_occurrence - 1, kind=kind, source_PC=header[4], actual_API_target=header[9], cpu=list(cpu), frame32_hex=snapshot[644:676].hex(), CS24_hex=snapshot[676:700].hex(), observed_depth=cs[2], FX512_sha256=hashlib.sha256(snapshot[104:616]).hexdigest(), ENV28_hex=snapshot[616:644].hex(), actual_original_postRET_observed=False))
        need(depth == 0, 'Actual final Lockit balance')
        counts['actual_Lockit_snapshots'] = lock_count; counts['actual_Lockit_calls'] = call_occurrence; counts['actual_maximum_recursion'] = maximum_depth
        fs_static = read(ROOT / 'reports/m4-tree-source/recovery-r1/FS-frame-contracts.json')
        fs_by_pc = {row[field]: (row, kind) for row in fs_static for kind, field in enumerate(('read', 'install', 'restore'))}
        raw_fs = bundle.data('phase/0/0/fs-events.bin'); need(len(raw_fs) % 1216 == 0, 'Full actual FS records')
        counts['all_actual_FS_observations'] = len(raw_fs) // 1216
        active = {}; occurrences = collections.Counter()
        for index in range(len(raw_fs) // 1216):
            event = raw_fs[index * 1216:(index + 1) * 1216]; header = words(event, 0, 8)
            if header[2] not in fs_by_pc:
                continue
            contract, kind = fs_by_pc[header[2]]; before = words(event, 32, 10); after = words(event, 72, 10)
            need(header[1] == 0x4b7f70 and header[3] == kind, 'Actual static tree FS source site')
            if kind == 0:
                identifier = sum(occurrences.values()); occurrences[contract['entry']] += 1
                active[contract['entry']] = dict(invocation_id=identifier, entry=contract['entry'], invocation_at_entry=occurrences[contract['entry']] - 1, entry_ESP=before[4] + 8, read_event=index, actual_saved_previous=header[4], root=0x4b7f70)
            else:
                current = active[contract['entry']]
                need(header[7] and header[6] == current['entry_ESP'] - 12, 'Complete source-affine actual12B record')
                record = words(event, 112, 3)
                need(record[0] == current['actual_saved_previous'] and record[1] == contract['handler'], 'Actual source previous/handler fields')
                current['install_event' if kind == 1 else 'restore_event'] = index
                current['installed_record_hex' if kind == 1 else 'restored_record_hex'] = event[112:124].hex()
                if kind == 2:
                    need(header[5] == current['actual_saved_previous'], 'Actual source previous head restored')
                    frames.append(current); del active[contract['entry']]
            counts['actual_tree_FS_observations'] += 1
        need(not active, 'Every measured tree frame restored')
        counts['actual_tree_FS_invocations'] = len(frames)
        for entry, count in occurrences.items():
            counts[f'actual_FS_{entry:x}_invocations'] = count
        globals_after = words(image('after', 0x60b2f8, 36), 0, 9)
        tree = dict(map_object=0x60b2f8, actual_globals_DWORDs=list(globals_after), header_pointer=words(image('after', 0x60b314, 4))[0], counter=words(image('after', 0x60b318, 4))[0], owner_pointer_to_generation={str(pointer): index + 1 for pointer, index in pointers.items()}, actual_nodes=[])
        for owner in owners:
            fields = owner['object_DWORDs']
            tree['actual_nodes'].append(dict(generation=owner['generation'], CALL_pc=owner['CALL_pc'], site_invocation=owner['site_invocation'], pointer=owner['pointer'], left=fields[0], parent=fields[1], right=fields[2], key=fields[3], value=fields[4], color=fields[5], left_generation=pointers.get(fields[0], -1) + 1, parent_generation=pointers.get(fields[1], -1) + 1, right_generation=pointers.get(fields[2], -1) + 1))
        registration = bundle.data('cleanup/0/registry.bin'); need(registration == struct.pack('<I', 0x4b7fa0), 'Actual one ordered tree callback')
        for index in range(owner_count):
            stem = f'cleanup/0/lockit-allocation-{index}'
            need(bundle.data(stem + '-owned.bin') == bytes.fromhex(owners[index]['final_hex']) and words(bundle.data(stem + '-returned.bin'))[0] == 1, 'Actual complete owner carry and positive source825 cleanup')
        counts['actual_positive_owner_cleanups'] = owner_count
        for label, item in [('actual-owners.json', owners), ('actual-Lockit-boundaries.json', locks), ('actual-FS-frames.json', frames), ('actual-tree-image.json', tree)]:
            path = out / label; path.write_text(json.dumps(item, indent=2) + '\n'); pin(path)
        bundle.close(); pin(__file__); passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc()); raise
    finally:
        report = dict(passed=passed, scope='Measured one-root original first tree prefix from authentic accepted loader and untouched BEFORE; full-capacity owners, actual repeated allocation/FS/Lockit records and callback; instruction access trace/source/native equivalence still separate', counts=dict(counts), root=0x4b7f70, original_record_bytes=356992, genuine_BEFORE_header_counter_zero=True, source_or_AFTER_values_used_as_observations=False, predicted_counts_used=False, actual_original_postRET_observed=False, instruction_level_tree_access_ledger_pending=True, initializer_credit=False, execution_path=str(execution_path), execution_sha256=execution_digest, files=PINS)
        path = out / 'report.json'; path.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(passed=passed, sha256=sha(path), counts=dict(counts))))

if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3])
