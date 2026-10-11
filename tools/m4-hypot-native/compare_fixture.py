"""Compare actual native outputs with sealed genuine source observations.

Expected numeric bytes enter only this post-execution verifier. The runtime
receives genuine BEFORE inputs; this verifier is not a numeric prediction model.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import struct
import sys
import traceback

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'reports/m4-hypot-native'
SOURCE = ROOT / 'reports/m4-hypot-original'
ROOT_FRAME, STACK_PAGE = 0x20001800, 0x20001000
SOURCE_RETURN, NATIVE_RETURN = 0x410a80, 0xfffffff0
STATE_BYTES, API_BYTES = 3504, 15360


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def u(b, at=0, n=1):
    return struct.unpack_from('<' + 'I' * n, b, at)


def caller_projection(b, base):
    b = bytearray(b)
    at = ROOT_FRAME - base
    if 0 <= at and at + 4 <= len(b):
        assert u(b, at)[0] == SOURCE_RETURN
        struct.pack_into('<I', b, at, NATIVE_RETURN)
    return bytes(b)


def initial_state(cpu, fx):
    s = bytearray(STATE_BYTES)
    for at, value in zip((2216,2248,2264,2232,2312,2328,2280,2296,2472),
                          list(cpu[:8]) + [cpu[9]]):
        struct.pack_into('<I', s, at, value)
    struct.pack_into('<Q', s, 2080, cpu[8])
    for at, bit in zip((2065,2067,2069,2071,2073,2075,2077), (0,2,4,6,7,10,11)):
        s[at] = (cpu[8] >> bit) & 1
    s[2768:3280] = fx
    for at, value in ((2090,0x2b),(2106,0x2b),(2110,0x23)):
        struct.pack_into('<H', s, at, value)
    return bytes(s)


def main(execution_path, execution_sha, name):
    assert re.fullmatch('fixture-comparison-r[1-9][0-9]*', name)
    out = AREA / name
    assert not out.exists()
    out.mkdir()
    pins, counts, witnesses = {}, Counter(), []
    passed = False

    def pin(p, h=None):
        p = Path(p).resolve()
        assert p.suffix.lower() not in ('.mwb', '.zip')
        actual = sha(p)
        assert h is None or actual == h, p
        assert str(p) not in pins or pins[str(p)] == actual
        pins[str(p)] = actual
        return p

    def blob(p):
        return pin(p).read_bytes()

    def load(p, h=None):
        return json.loads(pin(p, h).read_bytes())

    def receipt(p, h):
        j = load(p, h)
        assert j['passed']
        for q, digest in j['files'].items():
            if Path(q).suffix.lower() not in ('.mwb', '.zip'):
                pin(q, digest)
        return j

    try:
        execution = receipt(execution_path, execution_sha)
        assert execution['all_processes_closed'] and not execution['source_after_seed']
        assert not execution['numerical_expected_seed'] and execution['native_executed']
        build = receipt(execution['build'], execution['build_sha256'])
        preparation = receipt(build['preparation'], build['preparation_sha256'])
        inputs = receipt(preparation['inputs'], preparation['inputs_sha256'])
        assert inputs['scope'] == 'Whole genuine trace BEFORE stack input coupling only'
        assert not inputs['source_AFTER_seed'] and not inputs['numerical_results_seeded']
        trace_path = SOURCE / 'trace-validation-r2/report.json'
        trace = receipt(trace_path,
            'be137c4a05a5f9d33805f5cbb9db60157bf707fb2e1298db9b90ec943686780f')
        assert trace['reader_closed'] and not trace['source_after_seed']
        source = load(trace_path.parent / 'actual-source-traces.json')
        accesses = load(trace_path.parent / 'actual-source-accesses.json')
        assert len(source) == 6 and len(accesses) == 3696
        seed = blob(Path(preparation['inputs']).parent / 'input-state.bin')
        assert len(seed) == 3480
        lifts = load(AREA / 'lifts-r4/report.json',
            'fff190c4797cc82c018982c5c247b652cc6e307c2e184953dc620275f133b9f3')
        layouts = lifts['bodies']['f_4b5910']['layouts']
        # These source-derived layouts are also independently checked against
        # every whole linked literal object by the admitted prelaunch review.
        assert layouts['struct.State']['size'] == STATE_BYTES
        assert layouts['struct.X86State']['offsets'] == [0,16,2064,2080,2088,2112,2208,2480,2608,2736,2760,2768,3280,3376]
        assert layouts['struct.anon.3']['offsets'] == [0,6]
        assert layouts['struct.float80_t']['size'] == 10
        assert layouts['struct.Segments']['offsets'] == list(range(0,24,2))
        for q in ('lifts-r4/f_4b5910-host.ll',):
            pin(AREA / q, lifts['bodies']['f_4b5910']['host_sha256'])
        pin(ROOT / 'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/X86/Runtime/State.h')
        pin(ROOT / 'tools/m4-runtime/runtime.hpp')
        assert {(r['level'],r['sequence']) for r in execution['runs']} == {
            (level,seq) for level in ('O0','O2') for seq in range(6)}
        assert len(execution['runs']) == 12
        level_states = {}
        for run in execution['runs']:
            assert run['exit_code'] == 0 and run['complete'] and run['process_closed']
            level, seq = run['level'], run['sequence']
            native = Path(run['output'])
            t = source[seq]
            assert t['sequence'] == seq and t['event_count'] == 1007 and t['API_count'] == 2
            rows = [a for a in accesses if a['sequence'] == seq]
            assert len(rows) == 616
            assert u(blob(native / 'schema.bin'), 0, 10) == (44,15360,616,2,3504,40,190,2,80,80)
            assert blob(native / 'COMPLETE.txt') == b'complete'
            before_cpu = blob(native / 'before/CPU.bin')
            after_cpu = blob(native / 'after/CPU.bin')
            assert before_cpu == seed[seq*580:seq*580+40] == struct.pack('<10I', *t['own_BEFORE_CPU'])
            expected_cpu = list(t['own_AFTER_CPU'])
            assert expected_cpu[9] == SOURCE_RETURN
            expected_cpu[9] = NATIVE_RETURN
            assert after_cpu == struct.pack('<10I', *expected_cpu)
            before_state = blob(native / 'before/State.bin')
            after_state = blob(native / 'after/State.bin')
            assert len(after_state) == STATE_BYTES
            assert before_state == initial_state(u(before_cpu,0,10), seed[seq*580+40:seq*580+552])
            assert seed[seq*580+40:seq*580+552].hex() == t['own_BEFORE_FX512_hex']
            assert seed[seq*580+552:(seq+1)*580].hex() == t['own_BEFORE_ENV28_hex']
            counts['whole_initial_State3504_relations'] += 1
            counts['whole_root_CPU40_relations'] += 2
            level_states[(level,seq)] = (before_state,after_state)
            input_case = inputs['cases'][seq]
            assert input_case['sequence'] == seq
            pack = pin(input_case['pack'],input_case['pack_sha256']).read_bytes()
            assert len(pack) == 12+190*4104 and pack[:8] == b'MW4J124P' and u(pack,8)[0] == 190
            memory, before_pages = {}, {}
            for i in range(190):
                address, rights = u(pack,12+i*4104,2)
                assert address not in memory and rights in (0,1,2)
                expected = caller_projection(pack[20+i*4104:20+i*4104+4096], address)
                actual = blob(native / f'before/pages/{address}.bin')
                assert len(actual) == 4096 and actual == expected
                memory[address] = bytearray(actual)
                before_pages[address] = actual
                counts['whole_BEFORE_page4096_relations'] += 1
            def memory_read(address, width):
                return bytes(memory[address&~4095][address&4095:(address&4095)+width])
            def memory_write(address, value):
                page, offset = address&~4095, address&4095
                assert page in memory and offset+len(value) <= 4096
                memory[page][offset:offset+len(value)] = value
            native_accesses = blob(native / 'accesses.bin')
            assert len(native_accesses) == 616*44
            for i,a in enumerate(rows):
                pc,address,width,writing = u(native_accesses,i*44,4)
                assert (pc,address,width,writing) == (a['PC'],a['address'],a['width'],a['write'])
                assert 0 < width <= 28 and bool(a['read']) != bool(a['write'])
                observed = bytes.fromhex(a['after_hex'] if writing else a['before_hex'])
                expected = observed
                if (pc,address,width,writing) == (0x4b593e,ROOT_FRAME,4,0):
                    assert i == 615 and observed == struct.pack('<I',SOURCE_RETURN)
                    expected = struct.pack('<I',NATIVE_RETURN)
                    counts['precise_caller_RET4_projections'] += 1
                actual = native_accesses[i*44+16:i*44+16+width]
                assert actual == expected
                assert native_accesses[i*44+16+width:(i+1)*44] == bytes(28-width)
                if writing:
                    memory_write(address,observed)
                else:
                    assert memory_read(address,width) == expected
                counts['whole_observed_operand_payload_relations'] += 1
            page_relations = []
            for address, expected in sorted(memory.items()):
                p = native / f'after/pages/{address}.bin'
                actual = blob(p)
                assert len(actual) == 4096 and actual == expected
                page_relations.append(dict(address=address,BEFORE_sha256=hashlib.sha256(before_pages[address]).hexdigest(),
                    own_BEFORE_plus_source_write_observations_sha256=hashlib.sha256(expected).hexdigest(),
                    native_AFTER_sha256=sha(p)))
                counts['whole_AFTER_page4096_byteflow_relations'] += 1
            publications = [a for a in rows if a['write'] and a['width']==4 and 0x60b2c8<=a['address']<=0x60b2e8]
            assert len(publications)==9 and [a['address'] for a in publications]==list(range(0x60b2c8,0x60b2ec,4))
            counts['actual_game_F32_publications'] += 9
            api_bytes = blob(native / 'APIs.bin')
            assert len(api_bytes)==2*API_BYTES
            intervals = []
            for j,a in enumerate(t['APIs']):
                at = j*API_BYTES
                assert a['index']==j and a['import_name']=='_hypot' and a['owning_IAT']==0x5bb5b0
                assert a['target']==0x7802a122 and a['argc']==4 and a['returned']==1
                header = u(api_bytes,at,3)
                assert header==(j,a['ENTRY_CPU'][4],a['return_PC'])
                frame = header[1]
                assert a['AFTER_CPU'][4]==frame+4
                for label,cpu_at,stack_at,frame_at in (
                    ('entry',7024,7168,7104),('returned',7064,11264,7136)):
                    source_cpu=a['ENTRY_CPU' if label=='entry' else 'AFTER_CPU']
                    actual_cpu=api_bytes[at+cpu_at:at+cpu_at+40]
                    assert actual_cpu==struct.pack('<10I',*source_cpu)
                    stack=api_bytes[at+stack_at:at+stack_at+4096]
                    source_stack=bytes.fromhex(a[label+'_whole_stack_hex'])
                    assert len(source_stack)==4096
                    assert stack==caller_projection(source_stack,STACK_PAGE)
                    start=source_cpu[4]-STACK_PAGE
                    source_frame=bytes.fromhex(a[label+'_frame64_hex'])
                    assert stack[start:start+64]==caller_projection(source_frame,source_cpu[4])
                    # The native32 observer always starts at the CALL frame;
                    # the actual returned source64 observer starts at ESP+4.
                    native_frame=api_bytes[at+frame_at:at+frame_at+32]
                    assert native_frame==stack[frame-STACK_PAGE:frame-STACK_PAGE+32]
                    counts['whole_API_CPU40_relations']+=1
                    counts['whole_API_stack4096_relations']+=1
                    counts['whole_API_frame64_relations']+=1
                    counts['native_API_frame32_stack_joins']+=1
                before_raw=api_bytes[at+16:at+16+STATE_BYTES]
                after_raw=api_bytes[at+3520:at+3520+STATE_BYTES]
                raw80=after_raw[2486:2496]
                assert raw80.hex()==a['actual_return_raw80_hex']
                assert api_bytes[at+7108:at+7124].hex()==a['actual_F64_arguments_hex']
                intervals.append(dict(index=j,frame=frame,return_PC=a['return_PC'],
                    whole_native_BEFORE_State_sha256=hashlib.sha256(before_raw).hexdigest(),
                    whole_native_AFTER_State_sha256=hashlib.sha256(after_raw).hexdigest(),
                    actual_source_return_raw80_hex=a['actual_return_raw80_hex'],native_return_raw80_hex=raw80.hex()))
                counts['actual_raw80_return_relations']+=1
                counts['actual_literal_cdecl_intervals']+=1
            for kind,size in (('FX',512),('ENV',28)):
                before=blob(native/f'host-before-{kind}.bin')
                after=blob(native/f'host-after-{kind}.bin')
                assert len(before)==size and before==after
                counts[f'whole_caller_{kind}{size}_restorations']+=1
            witnesses.append(dict(level=level,sequence=seq,whole_pages=page_relations,
                actual_cdecl_intervals=intervals,whole_initial_State_sha256=hashlib.sha256(before_state).hexdigest(),
                whole_final_State_sha256=hashlib.sha256(after_state).hexdigest(),
                actual_game_F32_bytes=''.join(a['after_hex'] for a in publications)))
        for seq in range(6):
            assert level_states[('O0',seq)]==level_states[('O2',seq)]
            counts['whole_State3504_cross_level_pairs']+=2
        assert counts['whole_observed_operand_payload_relations']==7392
        assert counts['actual_raw80_return_relations']==24
        assert counts['actual_game_F32_publications']==108
        assert counts['whole_API_stack4096_relations']==48
        assert counts['whole_AFTER_page4096_byteflow_relations']==2280
        (out/'whole-native-source-relations.json').write_text(json.dumps(witnesses,indent=2)+'\n')
        pin(__file__)
        pin(sys.executable)
        pin(out/'whole-native-source-relations.json')
        for p,h in pins.items():
            assert sha(p)==h,p
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc())
        raise
    finally:
        report=dict(passed=passed,scope='Finite actual numeric source observation and own-BEFORE byteflow comparison',
            execution=str(Path(execution_path).resolve()),execution_sha256=execution_sha,
            counts=dict(counts),files=pins,archive_reader_opened=False,all_target_processes_closed=True,
            source_AFTER_seed=False,numerical_expected_seed=False,independent_numeric_prediction=False,
            source_native_whole_State_equivalence=False,cold_source_domain_admitted=False,
            caller_projection=dict(address=ROOT_FRAME,source_RETURN=SOURCE_RETURN,native_RETURN=NATIVE_RETURN,
                bytes=4,source_root_RET_PC=0x4b593e),
            initializer_credit=0,requires=['Independent current comparison review',
                'Independent source-derived whole State/x87/control mapping',
                'Meaningful actual native refusal and same-context retry evidence',
                'Genuine carried-prefix integration and final current acceptance'])
        p=out/'report.json'
        p.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(passed=passed,sha256=sha(p),counts=dict(counts))))


if __name__=='__main__':
    main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
