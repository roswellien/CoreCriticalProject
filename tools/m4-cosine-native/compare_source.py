"""Complete native State3504 and pages from literal source and finite FP seam."""
from pathlib import Path
import collections
import hashlib
import importlib.util
import json
import struct
import sys
import traceback

sys.dont_write_bytecode = True
from source_model import derive
ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'reports/m4-cosine-native'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(name):
    out = AREA / name
    assert not out.exists()
    out.mkdir(parents=True)
    pins, counts, rows = {}, collections.Counter(), []
    passed = False
    bundle = None

    def pin(path, expected=None):
        path = Path(path).resolve()
        value = sha(path)
        assert expected is None or value == expected, path
        pins[str(path)] = value
        return path

    def eq(a, b, label):
        if a != b:
            raise ValueError((label, [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y][:20]))

    try:
        build_path = pin(AREA / 'fixture-build-r1/report.json',
            '91c873f5e740c7ac87ae501f234b87b2815093e88e9a752262ae372dcdfeb6a1')
        build = json.loads(build_path.read_bytes())
        assert build['passed'] and build['native_executed']
        prep = json.loads(pin(build['preparation'], build['preparation_sha256']).read_bytes())
        pages = prep['observed_pages']
        original = json.loads(pin(ROOT / 'reports/m4-cosine-original/prefix-validation-r2/report.json',
            'cee385275cfd924366a867fc4442cf0fe78bae47af136d3b9569e0ace9952b4e').read_bytes())
        execution = json.loads(pin(original['execution_path'], original['execution_sha256']).read_bytes())
        contract_path = pin(ROOT / 'reports/m4-cosine-original/prefix-preparation-r2/instruction-contracts.json')
        contracts = json.loads(contract_path.read_bytes())
        source_prep = json.loads(pin(ROOT / 'reports/m4-cosine-original/prefix-preparation-r2/report.json',
            'aac031ac5949fa6fb1698c63130aa2652f352e521e140c02034fcb5df9f492df').read_bytes())
        assert source_prep['files'][str(contract_path)] == sha(contract_path)
        spec = importlib.util.spec_from_file_location('compound_source_direct',
            pin(ROOT / 'tools/m4-crt-allocation-root/run_v2.py'))
        direct = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(direct)
        bundle = direct.DirectSet(Path(execution['original_capture']), pin)
        for level in ('O0', 'O2'):
            output = build['outputs'][level]
            raw = pin(output['path'], output['sha256']).read_bytes()
            assert len(raw) == 32 + 6 * 361836
            for sequence in range(6):
                n = raw[32 + sequence * 361836:32 + (sequence + 1) * 361836]
                o = bundle.data(f'phase/{sequence}/0.bin')
                before = n[100:3604]
                cpu = struct.unpack_from('<10I', n, 20)
                memory = n[9268:185396]
                eq(n[20:60], o[36:76], 'genuine whole CPU BEFORE')
                eq(memory, o[2276:178404], 'genuine whole43-page BEFORE')
                result = derive(before, cpu, memory, o, contracts, pages)
                eq(result['state'], n[3604:7108], 'complete literal State3504 AFTER with explicit finite FP seam')
                eq(struct.pack('<10I', *result['CPU']), n[60:100], 'whole source CPU40 including literal AF representative')
                eq(result['pages'], n[185396:361524], 'complete literal whole43-page AFTER')
                events = [struct.unpack_from('<IQII', n, 361556 + i * 20) for i in range(14)]
                eq([(row['address'], row['value'], row['width'], int(row['writing'])) for row in result['events']], events,
                   'each complete literal memory operand value/order')
                counts.update(whole_State3504_AFTER=1, whole_CPU40_AFTER=1, whole43_page_AFTER=43,
                              literal_source_instructions=19, exact_source_access_values=14,
                              exact_immutable_F64_inputs=3, explicit_F32_numerical_oracles=3,
                              explicit_original_SW_raw80_seams=1, source_root_phases=1)
                rows.append(dict(level=level, sequence=sequence,
                                 State_BEFORE_sha256=hashlib.sha256(before).hexdigest(),
                                 source_State_AFTER_sha256=hashlib.sha256(result['state']).hexdigest(),
                                 source_pages_AFTER_sha256=hashlib.sha256(result['pages']).hexdigest(),
                                 accesses=result['events'], numerical_oracle=result['numerical_oracle']))
        assert counts['source_root_phases'] == 12
        passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        if bundle is not None:
            bundle.close()
        pin(__file__)
        pin(Path(__file__).with_name('source_model.py'))
        artifact = out / 'derivations.json'
        artifact.write_text(json.dumps(rows, indent=2) + '\n')
        pin(artifact)
        report = dict(passed=passed, scope='Literal19 source effects and complete native State/pages with explicit finite original numerical seam',
                      counts=dict(counts), source_BEFORE_machine_used=True,
                      candidate_AFTER_machine_seed=False, original_AFTER_machine_seed=False,
                      numerical_oracle_scope='Exact physical F64 default inputs/CW/TOP; three current original F32 outputs and original SW/raw80 only',
                      independent_trigonometric_prediction=False, full_State_source_comparison=True,
                      initializer_credit=0, reader_closed=True, files=pins)
        path = out / 'report.json'
        path.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(passed=passed, sha256=sha(path), counts=dict(counts))))


if __name__ == '__main__':
    main(sys.argv[1])
