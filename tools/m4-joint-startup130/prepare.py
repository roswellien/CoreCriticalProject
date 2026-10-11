"""Compose reviewed formatting4 and compound cosine over accepted125.

Preparation binds historical capture hashes; final acceptance must physically
rehash the complete dependency union. No initializer credit is granted here.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PARENT = ROOT / 'reports/m4-joint-startup125/preparation-r4'
ADDED = {0x4df610:0x5e01c8, 0x4e0710:0x5e01cc,
         0x4e0810:0x5e01d0, 0x4e1ca0:0x5e01d4, 0x4b64f0:0x5e0160}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def one(text, before, after):
    assert text.count(before) == 1, (before, text.count(before))
    return text.replace(before, after)


def main(native_path, digest, name):
    native_path = Path(native_path).resolve()
    out = ROOT / 'reports/m4-joint-startup130' / name
    assert not out.exists()
    out.mkdir(parents=True)
    pins, reused, generated = {}, {}, {}

    def pin(path, expected=None, reuse_archive=False):
        path = Path(path).resolve()
        if reuse_archive and path.suffix == '.mwb':
            assert path.is_file() and len(expected) == 64
            assert all(c in '0123456789abcdef' for c in expected)
            value = expected
            reused[str(path)] = value
        else:
            value = sha(path)
            assert expected is None or expected == value, (path, expected, value)
        assert str(path) not in pins or pins[str(path)] == value
        pins[str(path)] = value
        return path

    def read(path, expected=None):
        return json.loads(pin(path, expected).read_bytes())

    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        generated[str(path.resolve())] = sha(path)

    accepted = pin(ROOT / 'reports/m4-joint-startup125-root/acceptance-r2/report.json',
        '856ba8bd458e178f4a9afd91ff24299becc4debef76ee17c359da0f741165d51')
    acceptance = json.loads(accepted.read_bytes())
    assert acceptance['passed']
    prior = read(PARENT / 'report.json', '243b6f4c86dc2b966789e23faed4a10fe2efa62ba51f43e854fa843acde392e7')
    assert prior['passed'] and len(prior['selected_order']) == 125
    for path, expected in read(PARENT / 'pins.json')['files'].items():
        pin(path, expected, reuse_archive=True)
    native = read(native_path, digest)
    assert native['passed'] and set(native['new_roots']) == set(ADDED) - {0x4b64f0}
    assert native['live_owner_bound'] == 92
    for path, expected in native['files'].items():
        pin(path, expected, reuse_archive=True)
    cosine_path = ROOT / 'reports/m4-cosine-native/runtime-preparation-r2/report.json'
    cosine_digest = '6b9ad4a06fc8426b8c7215cd31a118883e8de7c4bc9c7087647ebe0c017fd61e'
    cosine = read(cosine_path, cosine_digest)
    assert cosine['passed']
    for path, expected in cosine['files'].items():
        pin(path, expected, reuse_archive=True)
    required = [
        (ROOT / 'reports/m4-cosine-native/runtime-fixture-verification-r1/report.json',
         'cc037925bc3f47f8d31c5ef96f0865632939688e65455e3c2b68c97b1ff3e12d'),
        (ROOT / 'reports/m4-tree-review/cosine-runtime-r6/report.json',
         '8b9a817d83b439a980452621e6f7fe5564b37944be7e6ca63b73495882457671'),
        (ROOT / 'reports/m4-formatting-source/native-source-r9/report.json',
         '0f2e817ff2bf938e32be26d7018d3921be5142461bf54ddfe70e0a676daa2306'),
        (ROOT / 'reports/m4-formatting-source/native-witnesses-r4/report.json',
         '284091a7d9efd64e695d399e89de94496a8c8c9181e4f0a3ecf589ef3d864510'),
        (ROOT / 'reports/m4-tree-review/formatting-controls-validation-r2/report.json',
         'a6f755471aec327792ffc9e379cc0ba8001b7e02f0416cc47e99acbda073933c'),
        (ROOT / 'reports/m4-tree-review/formatting-native-r1/report.json',
         'd1e07fa9728d0e019971bdcca5b16d058a9f3af47a837631a181125341452d04'),
        (ROOT / 'reports/m4-mixed-format-original/original-source-r7/report.json',
         '3a30f008243812bc5205487cbb08265e4ab9fd1e0e8377cb7ccd176230929823')]
    for path, expected in required:
        gate = read(path, expected)
        assert gate['passed']
        for dependency, dependency_sha in gate.get('files', {}).items():
            pin(dependency, dependency_sha, reuse_archive=True)
    game_path = pin(ROOT / 'MW3/Mech3.exe',
        '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
    pe_path = pin(ROOT / 'tools/analysis/pe.py')
    spec = importlib.util.spec_from_file_location('joint130_physical_pe', pe_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    game = module.PEImage(game_path.read_bytes())

    def physical(address, size):
        offset, _ = game.rva_range(address - game.image_base, size)
        result = game.data[offset:offset + size]
        assert len(result) == size
        return result

    selected = sorted(prior['selected_order'] + [dict(entry=root, slot=slot) for root, slot in ADDED.items()],
                      key=lambda row:row['slot'])
    assert len(selected) == len({row['entry'] for row in selected}) == 130
    assert [row for row in selected if row['entry'] not in ADDED] == prior['selected_order']
    for row in selected:
        assert int.from_bytes(physical(row['slot'], 4), 'little') == row['entry']
    for path in PARENT.rglob('*'):
        if path.is_file() and path.suffix in ('.cpp', '.hpp', '.inc'):
            write(out / path.relative_to(PARENT), path.read_text().replace(PARENT.as_posix(), out.as_posix()))
    protocol = (out / 'joint_protocol.hpp').read_text()
    protocol, count = re.subn(r'constexpr std::array<std::uint32_t,125> entries\{[^\n]+\};',
        'constexpr std::array<std::uint32_t,130> entries{' + ','.join(hex(row['entry']) for row in selected) + '};', protocol)
    assert count == 1
    protocol = one(protocol, 'void cosine(m4_runtime::Runtime &);',
                   'void cosine(m4_runtime::Runtime &);void compound_cosine(m4_runtime::Runtime &);')
    write(out / 'joint_protocol.hpp', protocol)
    roots = prior['registration_roots'] + [0x4df610,0x4e0710,0x4e0810,0x4e1ca0]
    assert len(set(roots)) == len(roots) == 101
    pages = prior['extra_pages'] + [0x5cd000,0x5e3000,0x5e9000]
    assert len(set(pages)) == len(pages) == 29
    write(out / 'registration_contract.hpp', '#pragma once\nnamespace mw34::m4_mixed {\n' +
          'constexpr std::array<unsigned,29> registration_pages{' + ','.join(hex(page) for page in pages) + '};\n' +
          'constexpr std::array<unsigned,101> registration_roots{' + ','.join(hex(root) for root in roots) + '};\n}\n')
    write(out / 'onexit_session.hpp', pin(Path(native['native_include']) / 'session.hpp').read_text())
    for source in [cosine['CPP']] + cosine['bridges']:
        write(out / 'derived' / Path(source).name, pin(source).read_text())
    text = (out / 'native_main.cpp').read_text()
    text = one(text, 'phase==125&&r_.calls().size()==128&&r_.translation_count()==126',
               'phase==130&&r_.calls().size()==133&&r_.translation_count()==131')
    for before, after in [('selected125','selected130'),('Connected125','Connected130'),
                          ('connected125','connected130'),('persistent125','persistent130'),
                          ('Joint125','Joint130'),('records.reserve(125)','records.reserve(130)'),
                          ('records.size()==125','records.size()==130'),('total==750','total==780'),
                          ('750native','780native'),('1,6,125,750,17,sizeof(Native)','1,6,130,780,17,sizeof(Native)'),
                          ('125-root','130-root')]:
        text = text.replace(before, after)
    write(out / 'native_main.cpp', text)
    bodies = native['formatting_bodies']
    assert len(bodies) == 25
    assert all(str(root) in bodies for root in set(ADDED) - {0x4b64f0})
    objects, bindings = {}, {}
    for level in ('O0','O2'):
        objects[level] = list(prior['objects'][level])
        assert len(objects[level]) == 371
        for body in bodies.values():
            obj = pin(body['objects'][level]['path'], body['objects'][level]['sha256'])
            assert str(obj).casefold() not in {str(Path(existing).resolve()).casefold() for existing in objects[level]}
            objects[level].append(str(obj))
        objects[level].append(str(pin(cosine['objects'][level]['path'], cosine['objects'][level]['sha256'])))
        assert len(objects[level]) == len(set(objects[level])) == 397
        for obj in objects[level]:
            pin(obj)
        path = out / level / 'registration_bindings.inc'
        text = path.read_text()
        bindings[level] = []
        for root in (0x4df610,0x4e0710,0x4e0810,0x4e1ca0):
            body = bodies[str(root)]
            width = body['source_bytes']
            code_sha = hashlib.sha256(physical(root,width)).hexdigest()
            object_sha = body['objects'][level]['sha256']
            text += '\nr_.register_translation({{' + hex(root) + '},{m4_runtime::Abi::Cdecl,0,true},&registration_entry,"Selected literal formatting/mixed initializer",{m4_runtime::Domain::admitted_game,m4::admitted_image_hash,' + str(width) + ',"' + code_sha + '","' + object_sha + '","' + digest + '"}});\n'
            bindings[level].append(dict(entry=root, physical_code_bytes=width, physical_code_sha256=code_sha, object_sha256=object_sha))
        write(path, text)
        path = out / level / 'mixed_bindings.hpp'
        text = one(path.read_text(), 'std::array<FpBinding,10>fp_bindings', 'std::array<FpBinding,11>fp_bindings')
        code_sha = hashlib.sha256(physical(0x4b64f0,121)).hexdigest()
        text = one(text, '&atan}}};', '&atan},{0x4b64f0,121,"' + code_sha + '","' +
                   cosine['objects'][level]['sha256'] + '","' + cosine_digest + '",&compound_cosine}}};')
        write(path, text)
    write(out / 'CMakeLists.txt', (PARENT / 'CMakeLists.txt').read_text().replace('Startup125','Startup130').replace('startup125','startup130'))
    pin(__file__)
    report = dict(passed=True, scope='Connected130 frozen preparation only; genuine full execution, source/provider/control/review/physical acceptance pending',
                  native_library=native['native_library'], native_include=native['native_include'],
                  native_preparation=str(native_path), native_preparation_sha256=digest,
                  compound_runtime_preparation=str(cosine_path), compound_runtime_preparation_sha256=cosine_digest,
                  parent_acceptance=str(accepted), parent_acceptance_sha256=sha(accepted),
                  parent_preparation=str(PARENT/'report.json'), parent_preparation_sha256=sha(PARENT/'report.json'),
                  selected_order=selected, registration_roots=roots, extra_pages=pages,
                  new_roots=list(ADDED), exact_new_root_bindings=bindings, objects=objects,
                  linked_literal_COFFs_per_level=397, added_literal_COFFs_per_level=26,
                  retained_unlinked_archives=prior['retained_unlinked_archives'],
                  packed_Native_bytes=159716, State_bytes=3504, FX_bytes=512, CPU_bytes=40,
                  whole_source_pages=46, registration_callbacks=101, normal_owner_bound=92,
                  generated_sources=generated, physical_dependencies=pins,
                  inherited_capture_payload_hashes_reused=reused, full_dependency_acceptance_rehash_required=True,
                  source_bodies_modified=False, per_phase_reseed=False, AFTER_machine_seed=False,
                  native_executed=False, initializer_credit=0, whole_M4_complete=False)
    write(out/'report.json', json.dumps(report,indent=2)+'\n')
    write(out/'pins.json', json.dumps(dict(files=pins|generated),indent=2)+'\n')
    print(json.dumps(dict(passed=True, sha256=sha(out/'report.json'), selected_roots=130, linked_objects=397)))


if __name__ == '__main__':
    main(*sys.argv[1:])
