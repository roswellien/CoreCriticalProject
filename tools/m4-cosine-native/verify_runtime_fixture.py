"""Independently compare Runtime source, full retry witnesses and cleanup.

Numerical results use the reviewed finite original SW/raw80/F32 seam. This
does not independently predict trigonometry or accept the connected schedule.
"""
from pathlib import Path
import collections
import hashlib
import importlib.util
import json
import re
import struct
import sys
import traceback

sys.dont_write_bytecode = True
from source_model import derive
ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'reports/m4-cosine-native'
CASES = [(0x7f,0),(0x37f,7),(0xf7f,0),(0x47f,7),(0xa7f,0),(0xe7f,7)]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(execution_path, digest, name):
    out = AREA / name
    assert not out.exists()
    out.mkdir(parents=True)
    pins, counts, derivations = {}, collections.Counter(), []
    original_bundle = native_bundle = None
    passed = False

    def pin(path, expected=None):
        path = Path(path).resolve()
        value = sha(path)
        assert expected is None or value == expected, path
        assert str(path) not in pins or pins[str(path)] == value
        pins[str(path)] = value
        return path

    def read(path, expected=None):
        return json.loads(pin(path, expected).read_bytes())

    def equal(a, b, label):
        if a != b:
            raise ValueError((label, len(a), len(b), [(i,x,y) for i,(x,y) in enumerate(zip(a,b)) if x != y][:24]))

    def hardware_equal(before, after, label, volatile=False):
        assert len(before) == len(after) == 544
        equal(before[:5], after[:5], label + ' control/status/tag')
        equal(before[24:28], after[24:28], label + ' MXCSR')
        equal(before[512:540], after[512:540], label + ' whole ENV28')
        for i in range(8):
            equal(before[32+i*16:42+i*16], after[32+i*16:42+i*16], label + ' raw80')
        start = 160 if volatile else 256
        equal(before[start:416], after[start:416], label + ' caller XMM domain')
        counts['architectural_host_and_whole_ENV_pairs'] += 1

    def pages(bundle, prefix, addresses):
        assert tuple(struct.unpack('<43I', bundle.data(prefix + 'current-page-addresses.bin'))) == tuple(addresses)
        values = [bundle.data(prefix + f'current-page-{address}.bin') for address in addresses]
        assert all(len(value) == 4096 for value in values)
        return b''.join(values)

    try:
        execution = read(execution_path, digest)
        assert execution['passed'] and len(execution['observations']) == 32
        build = read(execution['build_path'], execution['build_sha256'])
        prep = read(build['preparation'], build['preparation_sha256'])
        assert prep['cases'] == list(map(list, CASES))
        addresses = prep['current_pages']
        contract_path = pin(ROOT / 'reports/m4-cosine-original/prefix-preparation-r2/instruction-contracts.json')
        original_prep = read(ROOT / 'reports/m4-cosine-original/prefix-preparation-r2/report.json',
            'aac031ac5949fa6fb1698c63130aa2652f352e521e140c02034fcb5df9f492df')
        assert original_prep['files'][str(contract_path)] == sha(contract_path)
        contracts = json.loads(contract_path.read_bytes())
        validation = read(ROOT / 'reports/m4-cosine-original/prefix-validation-r2/report.json',
            'cee385275cfd924366a867fc4442cf0fe78bae47af136d3b9569e0ace9952b4e')
        original_execution = read(validation['execution_path'], validation['execution_sha256'])
        module_path = pin(ROOT / 'tools/m4-crt-allocation-root/run_v2.py')
        spec = importlib.util.spec_from_file_location('runtime_cosine_direct', module_path)
        direct = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(direct)
        original_bundle = direct.DirectSet(Path(original_execution['original_capture']), pin)
        for observation in execution['observations']:
            assert observation['exit_code'] == 0
            native_bundle = direct.DirectSet(pin(observation['transport'], observation['transport_sha256']), pin)
            control, sequence = observation['control'], observation['sequence']
            sample = native_bundle.data('sample.bin')
            assert len(sample) == 9968
            tags = struct.unpack_from('<32Q', sample)
            assert tags[0:2] == (1, 0x4b64f0)
            assert tags[4] == 1 and tags[5] == 0x4d573354 and not (tags[6] ^ tags[7]) & 0x400
            assert tags[8] == 1 and tags[9:11] == (0, 0)
            assert tags[2:4] == ((0,0) if control else (1,1))
            if control:
                assert tags[11] == 1
            owner_after = struct.unpack_from('<32Q', sample, 512)
            assert owner_after[10] == owner_after[11] == owner_after[15] == 0
            hardware_equal(sample[8880:9424], sample[9424:9968], 'actual outside public return')
            for name in ('invocation', 'cleanup'):
                hardware_equal(native_bundle.data(f'actual-{name}-hardware-before.bin'),
                               native_bundle.data(f'actual-{name}-hardware-after.bin'), 'actual ' + name)
            before_keys = {key.removeprefix('actual-retry-before/') for key in native_bundle.entries if key.startswith('actual-retry-before/')}
            after_keys = {key.removeprefix('actual-retry-after/') for key in native_bundle.entries if key.startswith('actual-retry-after/')}
            assert before_keys == after_keys and {'State.bin','CPU.bin','FX.bin','routes.bin'} <= before_keys
            for key in sorted(before_keys):
                equal(native_bundle.data('actual-retry-before/' + key), native_bundle.data('actual-retry-after/' + key), 'complete unchanged retry ' + key)
            retry = struct.unpack('<4I', native_bundle.data('actual-retry.bin'))
            assert retry == (1,0,1,int(bool(control)))
            counts.update(complete_retry_State3504=1, complete_retry_CPU40=1, complete_retry_FX512=1,
                          complete_retry_route_ledgers=1, complete_retry_private_and_page_records=len(before_keys),
                          completed_cleanup=1, outside_LastError_DF_pairs=1)
            root_before = pages(native_bundle, 'actual-before-root/', addresses)
            live = pages(native_bundle, 'actual-live/', addresses)
            records = native_bundle.data('actual-root-records.bin')
            if not control:
                assert len(records) == 159716
                n = records
                cw, top = CASES[sequence]
                assert (observation['CW'], observation['TOP']) == (cw, top)
                original = original_bundle.data(f'phase/{sequence}/0.bin')
                before = bytearray(root_before)
                stack = addresses.index(0x20001000) * 4096 + 0x800
                before[stack:stack+4] = (0x410a80).to_bytes(4, 'little')
                equal(bytes(before[:17*4096]), n[2276:71908], 'complete fixed17 Runtime BEFORE pages after literal CALL')
                cpu = struct.unpack_from('<10I', n, 36)
                result = derive(n[141540:145044], cpu, bytes(before), original, contracts, addresses)
                equal(result['state'], n[145044:148548], 'complete isolated Runtime source State3504')
                equal(struct.pack('<10I', *result['CPU']), n[76:116], 'complete literal Runtime CPU40')
                equal(result['pages'], pages(native_bundle, 'actual-after-root/', addresses), 'whole43 Runtime source AFTER pages')
                equal(result['pages'][:17*4096], n[71908:141540], 'complete fixed17 Runtime AFTER pages')
                events = [struct.unpack_from('<IQII', n, 148588 + i*20) for i in range(14)]
                equal([(row['address'],row['value'],row['width'],int(row['writing'])) for row in result['events']], events,
                      'all fourteen literal Runtime operands')
                assert struct.unpack_from('<10I', n, 148548) == (14,4,10,6,6,1,3,0,1,0)
                equal(n[145044:148548], native_bundle.data('actual-causal-State.bin'), 'State survives dispatcher return')
                equal(n[76:116], native_bundle.data('actual-causal-CPU.bin'), 'CPU survives dispatcher return')
                counts.update(whole_Runtime_State3504_source=1, whole_Runtime_CPU40_source=1,
                              whole43_Runtime_source_pages=43, literal_Runtime_source_accesses=14,
                              finite_original_F32_joins=3, positive_dispatcher_routes=1)
                derivations.append(dict(level=observation['level'], sequence=sequence, CW=cw, TOP=top,
                                        State_after_sha256=hashlib.sha256(result['state']).hexdigest(),
                                        pages_after_sha256=hashlib.sha256(result['pages']).hexdigest(),
                                        numerical_oracle=result['numerical_oracle'], events=result['events']))
            else:
                assert records == b''
                reason = native_bundle.data('actual-context-failure.bin').decode()
                assert reason and '0x004b64f0' in reason
                expected = bytearray(root_before)
                stack = addresses.index(0x20001000) * 4096 + 0x800
                expected[stack:stack+4] = (0x410a80).to_bytes(4, 'little')
                if control in (3,4):
                    original = original_bundle.data('phase/1/0.bin')
                    for row in contracts['instructions']:
                        if row['mnemonic'] != 'mov':
                            continue
                        address = int(re.search(r'\[(0x[0-9a-f]+)\]', row['operands'])[1], 16)
                        operand = row['operands'].split(',')[-1].strip()
                        value = 0 if operand == 'eax' else int(operand, 0)
                        at = addresses.index(address & ~4095)*4096+(address&4095)
                        expected[at:at+4] = value.to_bytes(4,'little')
                    for address in ((0x5e8880,) if control == 3 else (0x5e8880,0x5e8884)):
                        at = addresses.index(address&~4095)*4096+(address&4095)
                        expected[at:at+4] = original[178404+at:178408+at]
                equal(bytes(expected), live, 'all43 pages for actual first-fault partial source extent')
                counts.update(rejected_actual_controls=1, source_first_fault_whole43_page_extent=43,
                              no_completed_root_credit_on_fault=1)
                derivations.append(dict(level=observation['level'], sequence=sequence, control=control,
                                        name=observation['control_name'], actual_first_failure=reason,
                                        pages_after_sha256=hashlib.sha256(live).hexdigest()))
            native_bundle.close()
            native_bundle = None
        assert counts['whole_Runtime_State3504_source'] == 12 and counts['rejected_actual_controls'] == 20
        passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        for bundle in (native_bundle, original_bundle):
            if bundle is not None:
                bundle.close()
        pin(__file__)
        pin(Path(__file__).with_name('source_model.py'))
        artifact = out / 'derivations.json'
        artifact.write_text(json.dumps(derivations, indent=2) + '\n')
        pin(artifact)
        report = dict(passed=passed, scope='Isolated actual Runtime source/ten causal controls/complete retry/owned cleanup; connected130 acceptance remains separate',
                      execution_path=str(execution_path), execution_sha256=digest,
                      counts=dict(counts), original_finite_numerical_oracle=True,
                      independent_trigonometric_prediction=False, source_BEFORE_machine_used=True,
                      original_AFTER_machine_seed=False, candidate_AFTER_machine_seed=False,
                      complete_persistent_bootstrap_source=False, initializer_credit=0, reader_closed=True, files=pins)
        path = out / 'report.json'
        path.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(passed=passed, sha256=sha(path), counts=dict(counts))))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3])
