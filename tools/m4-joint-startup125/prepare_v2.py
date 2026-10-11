"""Add the measured tree to the unchanged accepted124 Runtime schedule."""
from pathlib import Path
import hashlib
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
PARENT = ROOT / 'reports/m4-joint-startup124/preparation-r5'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def one(text, before, after):
    assert text.count(before) == 1, (before, text.count(before))
    return text.replace(before, after)


def main(native_report, expected, name):
    native_report = Path(native_report).resolve()
    out = ROOT / 'reports/m4-joint-startup125' / name
    assert not out.exists()
    out.mkdir(parents=True)
    pins, inherited, generated = {}, {}, {}

    def pin(path, digest=None, reuse_archive=False):
        path = Path(path).resolve()
        if reuse_archive and path.suffix == '.mwb':
            assert path.is_file() and len(digest) == 64
            assert all(c in '0123456789abcdef' for c in digest)
            value = digest
            inherited[str(path)] = value
        else:
            value = sha(path)
            assert digest is None or value == digest, (path, digest, value)
        assert str(path) not in pins or pins[str(path)] == value
        pins[str(path)] = value
        return path

    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        generated[str(path.resolve())] = sha(path)

    pin(PARENT / 'report.json', '7a2e383ab47bdb668e56181cdc3eec1c75ebf03437e5f9b9ac675861370a85c7')
    parent = json.loads((PARENT / 'report.json').read_bytes())
    assert parent['passed'] and len(parent['selected_order']) == 124
    accepted = pin(ROOT / 'reports/m4-joint-startup124-root/acceptance-r1/report.json',
                   '6bd35e55bca15e1a0537044bf59a1c3ced5e9ef8b30a8a169b71c78824811462')
    assert json.loads(accepted.read_bytes())['passed']
    parent_pins = pin(PARENT / 'pins.json')
    for path, digest in json.loads(parent_pins.read_bytes())['files'].items():
        pin(path, digest, reuse_archive=True)
    pin(native_report, expected)
    native = json.loads(native_report.read_bytes())
    assert native['passed'] and native['new_roots'] == [0x4b7f70]
    assert native['exact_owned_causal_accesses'] == 172
    assert native['exact_primary_publications'] == 7 and native['live_owner_bound'] == 85
    for path, digest in native['files'].items():
        pin(path, digest, reuse_archive=True)
    lifts_path = pin(native['source_lifts'], native['source_lifts_sha256'])
    lifts = json.loads(lifts_path.read_bytes())
    assert lifts['passed'] and len(lifts['source_bodies']) == 8
    root = lifts['source_bodies']['f_4b7f70']
    assert root['entry'] == 0x4b7f70 and root['source_bytes'] == 46
    game = pin(ROOT / 'MW3/Mech3.exe',
               '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
    sys.path.insert(0, str(ROOT / 'tools/analysis'))
    from pe import PEImage
    pe = PEImage(game.read_bytes())
    def read_va(address, size):
        offset, _ = pe.rva_range(address - pe.image_base, size)
        return pe.data[offset:offset + size]
    assert int.from_bytes(read_va(0x5e0168, 4), 'little') == 0x4b7f70
    selected = sorted(parent['selected_order'] + [dict(entry=0x4b7f70, slot=0x5e0168)], key=lambda r: r['slot'])
    assert len(selected) == 125 and len({r['entry'] for r in selected}) == 125
    assert [r for r in selected if r['entry'] != 0x4b7f70] == parent['selected_order']
    for row in selected:
        assert int.from_bytes(read_va(row['slot'], 4), 'little') == row['entry']
    for path in PARENT.rglob('*'):
        if path.is_file() and path.suffix in ('.cpp', '.hpp', '.inc'):
            write(out / path.relative_to(PARENT), path.read_text().replace(PARENT.as_posix(), out.as_posix()))
    protocol = (out / 'joint_protocol.hpp').read_text()
    begin = protocol.index('constexpr std::array<std::uint32_t,124> entries')
    end = protocol.index(';', begin)
    write(out / 'joint_protocol.hpp', protocol[:begin] +
          'constexpr std::array<std::uint32_t,125> entries{' + ','.join(hex(r['entry']) for r in selected) + '}' + protocol[end:])
    roots = parent['registration_roots'] + [0x4b7f70]
    assert len(set(roots)) == len(roots) == 97
    pages = parent['extra_pages']
    assert len(pages) == 26
    write(out / 'registration_contract.hpp', '#pragma once\nnamespace mw34::m4_mixed {\n' +
          'constexpr std::array<unsigned,26> registration_pages{' + ','.join(hex(p) for p in pages) + '};\n' +
          'constexpr std::array<unsigned,97> registration_roots{' + ','.join(hex(r) for r in roots) + '};\n}\n')
    write(out / 'onexit_session.hpp', (Path(native['native_include']) / 'session.hpp').read_text())
    text = (out / 'native_main.cpp').read_text()
    text = one(text, 'phase==124&&r_.calls().size()==127&&r_.translation_count()==125',
               'phase==125&&r_.calls().size()==128&&r_.translation_count()==126')
    for before, after in [('selected124', 'selected125'), ('Connected124', 'Connected125'),
                          ('connected124', 'connected125'), ('persistent124', 'persistent125'),
                          ('Joint124', 'Joint125'), ('records.reserve(124)', 'records.reserve(125)'),
                          ('records.size()==124', 'records.size()==125'), ('total==744', 'total==750'),
                          ('744native', '750native'), ('1,6,124,744,17,sizeof(Native)', '1,6,125,750,17,sizeof(Native)'),
                          ('124-root', '125-root')]:
        text = text.replace(before, after)
    write(out / 'native_main.cpp', text)
    objects = {}
    root_raw = read_va(0x4b7f70, 46)
    root_sha = hashlib.sha256(root_raw).hexdigest()
    assert root_sha == root['source_sha256']
    for level in ('O0', 'O2'):
        objects[level] = list(parent['objects'][level])
        assert len(objects[level]) == 363
        for body in lifts['source_bodies'].values():
            obj = pin(body['objects'][level]['path'], body['objects'][level]['sha256'])
            assert str(obj).casefold() not in {str(Path(p).resolve()).casefold() for p in objects[level]}
            objects[level].append(str(obj))
        assert len(objects[level]) == 371
        for path in objects[level]:
            pin(path)
        binding = 'r_.register_translation({{0x4b7f70},{m4_runtime::Abi::Cdecl,0,true},&registration_entry,"Selected literal movement-name tree initializer",{m4_runtime::Domain::admitted_game,m4::admitted_image_hash,46,"' + root_sha + '","' + root['objects'][level]['sha256'] + '","' + sha(lifts_path) + '"}});\n'
        path = out / level / 'registration_bindings.inc'
        write(path, path.read_text() + '\n' + binding)
    write(out / 'CMakeLists.txt', (PARENT / 'CMakeLists.txt').read_text().replace('Startup124', 'Startup125').replace('startup124', 'startup125'))
    pin(__file__)
    report = dict(passed=True, scope='Connected125 preparation only; execution and full semantic acceptance pending',
                  native_library=native['native_library'], native_include=native['native_include'],
                  native_preparation=str(native_report), native_preparation_sha256=expected,
                  parent_acceptance=str(accepted), parent_acceptance_sha256=sha(accepted),
                  parent_preparation=str(PARENT / 'report.json'), parent_preparation_sha256=sha(PARENT / 'report.json'),
                  source_lifts=str(lifts_path), source_lifts_sha256=sha(lifts_path),
                  selected_order=selected, registration_roots=roots, extra_pages=pages, objects=objects,
                  linked_literal_COFFs_per_level=371, added_literal_COFFs_per_level=8,
                  retained_unlinked_archives=parent['retained_unlinked_archives'],
                  packed_Native_bytes=159716, State_bytes=3504, FX_bytes=512, CPU_bytes=40,
                  generated_sources=generated, physical_dependencies=pins,
                  inherited_capture_payload_hashes_reused=inherited,
                  full_dependency_acceptance_rehash_required=True,
                  source_bodies_modified=False, per_phase_reseed=False, AFTER_machine_seed=False,
                  native_executed=False, initializer_credit=False, whole_M4_complete=False)
    write(out / 'report.json', json.dumps(report, indent=2) + '\n')
    write(out / 'pins.json', json.dumps(dict(files=pins | generated), indent=2) + '\n')
    print(json.dumps(dict(passed=True, report=str(out / 'report.json'), sha256=sha(out / 'report.json'), selected_roots=125)))


if __name__ == '__main__':
    main(*sys.argv[1:])
