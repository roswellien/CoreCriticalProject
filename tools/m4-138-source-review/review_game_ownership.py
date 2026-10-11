"""Independent ordinary-input inverse and native PE ownership review."""
from pathlib import Path
import ast, hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main(name):
    out = ROOT / 'reports/m4-joint-startup138-source' / name
    assert not out.exists()
    pins = {}
    def pin(path, expected=None):
        path = Path(path).resolve()
        assert path.suffix.lower() not in ('.mwb', '.mwi', '.zip')
        assert path.name not in ('transport.json', 'index.json', 'payload.bin')
        digest = sha(path)
        assert expected is None or digest == expected, str(path)
        assert str(path) not in pins or pins[str(path)] == digest
        pins[str(path)] = digest
        return path
    prep = ROOT / 'reports/m4-joint-startup138-source/preparation-r7'
    report = json.loads(pin(prep / 'report.json').read_bytes())
    assert report['passed'] and not report['source_execution_performed']
    for path, digest in report['files'].items():
        pin(path, digest)
    parent = ROOT / 'reports/m4-joint-startup138-source/preparation-r4'
    pin(parent / 'report.json', report['parent_preparation_sha256'])
    text = (prep / 'compare_provider138.py').read_text()
    ast.parse(text)
    for delta in reversed(report['comparator_deltas']):
        assert text.count(delta['after']) == 1
        text = text.replace(delta['after'], delta['before'], 1)
    assert text == (parent / 'compare_provider138.py').read_text()
    helper = pin(report['helper'], report['helper_sha256'])
    text = helper.read_text()
    addition = """
import importlib.util
_game_spec=importlib.util.spec_from_file_location('current138_game_owned_memory',ROOT/'tools/m4-138-constructor-readiness/mapped_game_memory_v2.py')
GAME_OWNERSHIP=importlib.util.module_from_spec(_game_spec);_game_spec.loader.exec_module(GAME_OWNERSHIP)
admit_game_regions=GAME_OWNERSHIP.admit
"""
    assert text.count(addition) == 1
    text = text.replace(addition, '', 1)
    addition = """    need(hasattr(machine,'_source_game_ownership'),'Source-owned PE allocations admitted before bootstrap')
    actual_inventory=[(int(name[len(prefix+'game-region-'):-4]),len(archive.data(name)))for name in names]
    equal(sorted(actual_inventory),machine._source_game_ownership['regions'],'Every and only independently PE-owned Game region')
"""
    assert text.count(addition) == 1
    text = text.replace(addition, '', 1)
    assert text == pin(ROOT / 'tools/m4-joint-startup138/persistent_widgets_v2.py').read_text()
    def load(name, path):
        spec = importlib.util.spec_from_file_location(name, pin(path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    pe_module = load('independent_game_pe', ROOT / 'tools/analysis/pe.py')
    pe = pe_module.PEImage(pin(ROOT / 'MW3/Mech3.exe').read_bytes())
    model = load('independent_game_ownership', ROOT / 'tools/m4-138-constructor-readiness/mapped_game_memory_v2.py')
    regions = [(pe.image_base, (pe.size_of_headers + 4095) & ~4095, 0, pe.size_of_headers)]
    regions += [(pe.image_base + s['virtual_address'], (max(s['raw_size'], s['virtual_size']) + 4095) & ~4095, s['raw_offset'], s['raw_size']) for s in pe.sections]
    assert sorted(regions) == model.mapped_regions(pe)
    loader = pin(ROOT / 'tools/m4-startup/image_loader.cpp').read_text()
    for predicate in ('round_up(header_size, page_size)', 'std::max(section.virtual_size, section.raw_size)', 'round_up(extent, page_size)'):
        assert predicate in loader, predicate
    assert regions[-1][0:2] == (0x9a2000, 0x53000)
    assert regions[-1][3] == 0x52600
    pin(__file__)
    pin(sys.executable)
    for path, digest in pins.items():
        assert sha(path) == digest
    out.mkdir()
    result = dict(passed=True, scope='Exact additive inverse and physical native loader inventory only', comparator_inverse_restores_parent=True, helper_inverse_restores_parent=True, prior_all_semantic_gates_retained=True, PE_regions=regions, independent_resource_raw_bytes=0x52600, independent_resource_zero_tail_bytes=0xa00, archive_reader_opened=False, source_execution_performed=False, initializer_credit=0, files=pins)
    target = out / 'report.json'
    target.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(passed=True, sha256=sha(target), physical_inputs=len(pins))))

if __name__ == '__main__':
    main(sys.argv[1])
