"""Couple the complete genuine trace BEFORE stack; no target or archive reader."""
from pathlib import Path
import hashlib
import json
import re
import struct
import sys
import traceback

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'reports/m4-hypot-native'
SOURCE = ROOT / 'reports/m4-hypot-original'


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main(name):
    assert re.fullmatch('inputs-r[1-9][0-9]*', name)
    out = AREA / name
    assert not out.exists()
    out.mkdir()
    pins, cases, witnesses = {}, [], []
    passed = False

    def pin(p, h=None):
        p = Path(p).resolve()
        assert p.suffix.lower() not in ('.mwb', '.zip')
        actual = sha(p)
        assert h is None or actual == h, p
        assert str(p) not in pins or pins[str(p)] == actual
        pins[str(p)] = actual
        return p

    def load(p, h=None):
        return json.loads(pin(p, h).read_bytes())

    try:
        parent = load(AREA / 'inputs-r4/report.json',
            '2e06405a753a7cd1ec4fec34f85ea4af0cce5040c250d39b0c5ee3990bea5c8a')
        trace_path = SOURCE / 'trace-validation-r2/report.json'
        trace = load(trace_path,
            'be137c4a05a5f9d33805f5cbb9db60157bf707fb2e1298db9b90ec943686780f')
        assert parent['passed'] and trace['passed'] and trace['reader_closed']
        for receipt in (parent, trace):
            for q, h in receipt['files'].items():
                if Path(q).suffix.lower() not in ('.mwb', '.zip'):
                    pin(q, h)
        prep_path = SOURCE / 'trace-preparation-r8/report.json'
        prep = load(prep_path, trace['files'][str(prep_path.resolve())])
        assert prep['record_bytes'] == 356992 and len(prep['observed_pages']) == 43
        stack_index = prep['observed_pages'].index(0x20001000)
        before_offset = 2276 + stack_index * 4096
        states = pin(AREA / 'inputs-r4/input-state.bin').read_bytes()
        assert len(states) == 3480
        assert parent['permission_encoding'] == {'0': 'read execute', '1': 'read', '2': 'read write'}
        for c in parent['cases']:
            seq = c['sequence']
            raw_path = trace_path.parent / 'raw-observations' / f'case-{seq}-record.bin'
            raw = pin(raw_path, trace['files'][str(raw_path.resolve())]).read_bytes()
            assert len(raw) == 356992
            header = struct.unpack_from('<9I', raw)
            assert header[0] == seq and header[3:5] == (0x5e0154, 0x4b5910)
            # The actual trace CPU/FX/ENV BEFOREs already equal the ordinary
            # BEFORE inputs. Only a complete actual BEFORE stack page is coupled.
            actual_seed = raw[36:76] + raw[116:628] + raw[2164:2192]
            assert states[seq * 580:(seq + 1) * 580] == actual_seed
            pack = bytearray(pin(c['pack'], c['pack_sha256']).read_bytes())
            assert pack[:8] == b'MW4J124P' and len(pack) == 12 + 190 * 4104
            assert struct.unpack_from('<I', pack, 8)[0] == 190
            indexes = [i for i in range(190)
                if struct.unpack_from('<I', pack, 12 + i * 4104)[0] == 0x20001000]
            assert len(indexes) == 1
            at = 20 + indexes[0] * 4104
            previous = bytes(pack[at:at + 4096])
            actual_before = raw[before_offset:before_offset + 4096]
            assert len(actual_before) == 4096
            changes = [i for i in range(4096) if previous[i] != actual_before[i]]
            assert changes == [0x7ae, 0x7d0, 0x7d1]
            assert struct.unpack_from('<I', actual_before, 0x800)[0] == 0x410a80
            pack[at:at + 4096] = actual_before
            original = Path(c['pack']).read_bytes()
            assert pack[:at] == original[:at] and pack[at + 4096:] == original[at + 4096:]
            p = out / f'input-{seq}.bin'
            p.write_bytes(pack)
            pin(p)
            row = dict(c, pack=str(p.resolve()), pack_sha256=sha(p),
                input_source='Ordinary actual BEFORE providers plus entire genuine trace BEFORE stack page')
            cases.append(row)
            witnesses.append(dict(sequence=seq, raw_source=str(raw_path.resolve()),
                raw_source_sha256=sha(raw_path), raw_BEFORE_offset=before_offset,
                pack_offset=at, whole_BEFORE_stack_sha256=hashlib.sha256(actual_before).hexdigest(),
                changed_bytes=[dict(address=0x20001000+i, ordinary=previous[i], trace=actual_before[i]) for i in changes],
                other_whole_pages_unchanged=189, every_permission_tag_unchanged=True,
                CPU_FX_ENV_BEFORE_unchanged=True, caller_source_return=0x410a80))
        (out / 'input-state.bin').write_bytes(states)
        for name_copy in ('input-mapping.json', 'page-permissions.json'):
            (out / name_copy).write_bytes(pin(AREA / 'inputs-r4' / name_copy).read_bytes())
        (out / 'trace-BEFORE-coupling.json').write_text(json.dumps(witnesses, indent=2) + '\n')
        pin(__file__)
        pin(sys.executable)
        for p in out.iterdir():
            if p.is_file():
                pin(p)
        passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        report = dict(passed=passed, scope='Whole genuine trace BEFORE stack input coupling only',
            parent_inputs=str((AREA / 'inputs-r4/report.json').resolve()),
            parent_inputs_sha256='2e06405a753a7cd1ec4fec34f85ea4af0cce5040c250d39b0c5ee3990bea5c8a',
            source_trace=str((SOURCE / 'trace-validation-r2/report.json').resolve()),
            source_trace_sha256='be137c4a05a5f9d33805f5cbb9db60157bf707fb2e1298db9b90ec943686780f',
            cases=cases, memory_pages_per_case=190,
            permission_encoding={'0': 'read execute', '1': 'read', '2': 'read write'},
            numerical_results_seeded=False, source_AFTER_seed=False,
            archive_reader_opened=False, native_executed=False, initializer_credit=0, files=pins)
        p = out / 'report.json'
        p.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(passed=passed, sha256=sha(p), cases=len(cases))))


if __name__ == '__main__':
    main(sys.argv[1])
