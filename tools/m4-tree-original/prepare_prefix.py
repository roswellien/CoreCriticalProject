"""Additive one-root original prefix from authentic accepted loader/bootstrap.

All counts are measured by bounded observer arrays, never seeded predictions.
"""
from pathlib import Path
import hashlib, importlib.util, json, re, struct, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / 'reports/m4-lockit-original/original-preparation-r4'
SRC = ROOT / 'reports/m4-tree-source/recovery-r1'
BASE = ROOT / 'reports/m4-tree-original'
sys.path.insert(0, str(ROOT / 'tools/analysis'))
from pe import PEImage

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def need(value, message):
    if not value:
        raise ValueError(message)

def one(text, old, new):
    need(text.count(old) == 1, 'One bounded source replacement: ' + old[:70])
    return text.replace(old, new, 1)

def main(name):
    out = BASE / name
    need(not out.exists(), 'Fresh additive preparation')
    pins = {}
    def pin(path, expected=None):
        path = Path(path).resolve()
        need(path.suffix != '.mwb', 'No inherited capture reader')
        actual = sha(path)
        need(expected is None or actual == expected, 'Exact original source input ' + str(path))
        need(str(path) not in pins or pins[str(path)] == actual, 'Physical identity stable')
        pins[str(path)] = actual
        return path
    def text(path):
        return pin(path).read_text(encoding='utf-8-sig')
    old = json.loads(pin(OLD / 'report.json', '6a25b9b16ccdbfefe30488ea6b87afd5c266489fd63f2b5710c05c04a14fd68b').read_bytes())
    source = json.loads(pin(SRC / 'report.json', '81efa236420aab06fb6ab63453c32fb3e1364dfdf8c268cd6e1cd815d81c20a4').read_bytes())
    for parent in (old, source):
        for path, digest in parent['files'].items():
            pin(path, digest)
    contract = json.loads(pin(SRC / 'instruction-contracts.json').read_bytes())
    need(len(contract['instructions']) == 613, 'Exact physical tree source union')
    game = PEImage(pin(ROOT / 'MW3/Mech3.exe').read_bytes())
    raw = pin(OLD / 'pages.bin', old['pack_sha256']).read_bytes()
    records = {struct.unpack_from('<I', raw, 12 + i * 4104)[0]: (struct.unpack_from('<I', raw, 16 + i * 4104)[0], bytearray(raw[20 + i * 4104:4116 + i * 4104])) for i in range(struct.unpack_from('<I', raw, 8)[0])}
    spans = list(old['source_spans'])
    known = {row['pc']: row for row in spans}
    for row in contract['instructions']:
        pc = row['pc']; code = bytes.fromhex(row['bytes_hex'])
        offset, _ = game.rva_range(pc - game.image_base, len(code))
        need(game.data[offset:offset + len(code)] == code, 'Physical exact source instruction')
        if pc in known:
            need(known[pc]['size'] == len(code) and known[pc]['image_offset'] == offset, 'Existing source agreement')
            continue
        page = pc & ~4095
        need(pc + len(code) <= page + 4096, 'Source instruction does not cross page')
        if page not in records:
            records[page] = (1, bytearray(b'\xcc' * 4096))
        records[page][1][pc & 4095:(pc & 4095) + len(code)] = code
        spans.append(dict(pc=pc, size=len(code), image_offset=offset, origin=0))
        known[pc] = spans[-1]
    out.mkdir(parents=True)
    pack = b'MW4J124P' + struct.pack('<I', len(records)) + b''.join(struct.pack('<2I', page, permission) + data for page, (permission, data) in records.items())
    (out / 'pages.bin').write_bytes(pack)
    spec = text(OLD / 'spec.hpp')
    spec = re.sub(r'pack_sha\[\]="[0-9a-f]+"', 'pack_sha[]="' + sha(out / 'pages.bin') + '"', spec)
    spec = re.sub(r'pack_size=\d+', 'pack_size=' + str(len(pack)), spec)
    for field, values in [('entries', [0x4b7f70]), ('table_slots', [0x5e0168]), ('page_bases', list(records)), ('page_permissions', [permission for permission, data in records.values()])]:
        spec = re.sub(r'inline constexpr std::array<std::uint32_t,\d+> ' + field + r'\{[^;]+;', f'inline constexpr std::array<std::uint32_t,{len(values)}> ' + field + '{' + ','.join(hex(v) for v in values) + '};', spec)
    spec = re.sub(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;', f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings{{{{' + ','.join('{' + ','.join(hex(row[k]) for k in ('pc', 'size', 'image_offset', 'origin')) + '}' for row in spans) + '}};', spec)
    spec = re.sub(r'inline constexpr std::array<FsAllocationBinding,8> lockit_allocation_bindings\{\{[^;]+;', 'inline constexpr std::array<FsAllocationBinding,3> lockit_allocation_bindings{{' + ','.join('{' + ','.join(hex(v) for v in (0x4b7f70, row['CALL_pc'], row['source_request'])) + '}' for row in contract['allocations']) + '}};', spec)
    spec = re.sub(r'inline constexpr std::array<LockitRoot,4>lockit_roots\{\{[^;]+;', 'inline constexpr std::array<LockitRoot,1>lockit_roots{{{0x4b7f70,0x60b2f8,0x60b314,0x60b318,24}}};', spec)
    (out / 'spec.hpp').write_text(spec)
    protocol = text(OLD / 'protocol.hpp').replace('sequences=6, roots=124', 'sequences=1, roots=1')
    (out / 'protocol.hpp').write_text(protocol)
    broker = text(OLD / 'original_broker.hpp')
    broker_bases = list(dict.fromkeys([int(value, 16) for value in re.search(r'bases\{([^;]+)\};', broker)[1].split(',')] + [page & ~65535 for page in records]))
    broker = re.sub(r'std::array<std::uint32_t,\d+> bases\{[^;]+;', f'std::array<std::uint32_t,{len(broker_bases)}> bases' + '{' + ','.join(hex(value) for value in broker_bases) + '};', broker)
    (out / 'original_broker.hpp').write_text(broker)
    original_hooks = json.loads(pin(OLD / 'fs-hook-bindings.json').read_bytes())
    hooks = [(row['PC'], row['kind'], row['raw_bytes']) for row in original_hooks]
    frames = json.loads(pin(SRC / 'FS-frame-contracts.json').read_bytes())
    for frame in frames:
        for kind, field in enumerate(('read', 'install', 'restore')):
            pc = frame[field]
            hooks.append((pc, kind, next(row['bytes_hex'] for row in contract['instructions'] if row['pc'] == pc)))
    need(len(hooks) == 57 and len({pc for pc, kind, code in hooks}) == 57, 'Every exact static new FS observation site')
    module_spec = importlib.util.spec_from_file_location('tree_prefix_fs', pin(ROOT / 'tools/m4-fs-source/fs_hooks_v2.py'))
    fs = importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(fs); fs.HOOKS = hooks
    (out / 'fs_observer_x86.asm').write_text(fs.asm())
    ref = text(OLD / 'reference.cpp')
    start = ref.index('extern "C" extern "C" extern "C" void fs_hook_')
    end = ref.index('struct FsAllocation {', start)
    ref = ref[:start] + fs.declarations() + fs.hook_table().replace('std::array<FsHook,9>', 'std::array<FsHook,57>') + ref[end:]
    ref = ref.replace('FsEvent fs_events[64]', 'FsEvent fs_events[256]').replace('fs_event_count>=64', 'fs_event_count>=256')
    ref = ref.replace('lockit_snapshots[6]', 'lockit_snapshots[128]').replace('lockit_count>=6', 'lockit_count>=128')
    ref = ref.replace('lockit_allocations[8]', 'lockit_allocations[64]').replace('lockit_allocation_count>=8', 'lockit_allocation_count>=64')
    ref = ref.replace('RegistryAPIEntry registry_API_ledger[32]', 'RegistryAPIEntry registry_API_ledger[256]').replace('registry_initial_sizes[32]', 'registry_initial_sizes[256]').replace('registry_initial_bytes[32][1024]', 'registry_initial_bytes[256][1024]').replace('i>=32', 'i>=256').replace('registry_API_count<=32', 'registry_API_count<=256')
    ref = re.sub(r'std::array<void\*,118> pages', f'std::array<void*,{len(records)}> pages', ref)
    ref = one(ref, 'const std::array<std::array<unsigned,3>,6> cases{{{0x0,0x7f,0x0},{0x0,0x37f,0x7},{0x0,0xf7f,0x0},{0x1,0x47f,0x7},{0x1,0xa7f,0x0},{0x1,0xe7f,0x7}}};', 'const std::array<std::array<unsigned,3>,1> cases{{{0,0x7f,0}}};')
    ref = one(ref, 'r->tag.status=execute();', 'require(*reinterpret_cast<unsigned*>(0x60b314)==0&&*reinterpret_cast<unsigned*>(0x60b318)==0,"Actual untouched shared tree header/counter BEFORE");r->tag.status=execute();')
    start = ref.index('            const auto mfcbase=')
    end = ref.index('            const auto lockbase=', start)
    ref = ref[:start] + ref[end:]
    start = ref.index('            const auto stringbase=')
    end = ref.index('            out.append("phase/"', start)
    ref = ref[:start] + ref[end:]
    ref = one(ref, 'require(*crtnext-*crtbegin==96*4,"Exact96callback vectorextent");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),96*4);', 'require(*crtnext-*crtbegin==4&&*reinterpret_cast<unsigned*>(*crtbegin)==0x4b7fa0,"Actual single tree callback registration");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),4);')
    ref = one(ref, 'require(lockit_allocation_count==8,"Eight genuine four-root Lockit owners");', 'require(lockit_allocation_count>0&&lockit_allocation_count<64,"Bounded actual positive tree owners");out.append("actual-tree-owner-count.bin",&lockit_allocation_count,4);')
    start = ref.index('        require(container_allocation_count==5,')
    end = ref.index('original_free(reinterpret_cast<void*>(*crtbegin));', start)
    ref = ref[:start] + '        ' + ref[end:]
    ref = ref.replace('6 connected sequences /744 actual original initializer phases captured; full ledger and native equivalence remain open', 'One genuine tree prefix captured; counts are observations and full source/native gates remain open')
    (out / 'reference.cpp').write_text(ref)
    for filename in ('reference_x86.asm', 'preserve_x86.asm', 'nullfree_observer_x86.asm', 'vtable_observer_x86.asm', 'lockit_observer_x86.asm', 'CMakeLists.txt'):
        (out / filename).write_text(text(OLD / filename))
    hooks_json = [dict(PC=pc, kind=kind, raw_bytes=raw) for pc, kind, raw in hooks]
    (out / 'fs-hook-bindings.json').write_text(json.dumps(hooks_json, indent=2) + '\n')
    pin(__file__)
    for path in out.iterdir():
        pin(path)
    report = dict(passed=True, scope='Bounded first original tree prefix with accepted genuine DLL loader/bootstrap and one untouched root BEFORE; dynamic observation counts, no predicted owner/path effects', source_recovery_sha256=sha(SRC / 'report.json'), parent_preparation_sha256=sha(OLD / 'report.json'), source_spans=spans, pack_sha256=sha(out / 'pages.bin'), observed_pages=old['observed_pages'], source_instruction_rows=613, source_instruction_bytes=sum(row['width'] for row in contract['instructions']), original_sequences=1, original_phases=1, record_bytes=356992, FS_hooks=57, FS_observer_bound=256, Lockit_observer_bound=128, owner_observer_bound=64, predicted_counts_supplied_to_execution=False, native_executed=False, initializer_credit=False, inherited_capture_reader_opened=False, files=pins)
    path = out / 'report.json'; path.write_text(json.dumps(report, indent=2) + '\n')
    pin(path)
    (out / 'pins.json').write_text(json.dumps(dict(files=pins), indent=2) + '\n')
    print(json.dumps(dict(passed=True, sha256=sha(path), pages=len(records), source_rows=613)))

if __name__ == '__main__':
    main(sys.argv[1])
