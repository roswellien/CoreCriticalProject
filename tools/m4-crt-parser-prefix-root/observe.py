"""Independent original BEFORE/source comparison of ordinary carried x64 rows.

The two measured native APIs are explicit external inputs. Candidate AFTER
State, pages and CPU are never expected-machine seeds. Rich causal admission
checks are supplied separately by the compiled reviewer.
"""
import copy
import hashlib
import json
import struct
import subprocess
import sys
import time
import traceback
from pathlib import Path
sys.dont_write_bytecode = True
from consumer import F, M, OLD, predict as consumer_predict
from model import expected
from parser import predict as parser_predict, source_material as parser_source, SOURCE_SHA
ROOT = F.ROOT
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import CaptureBundle, sha_file
from manifests import verify_manifest
from paths import publish_bytes, workspace_path

def enrich(values, owned=None):
    result = dict(values)
    page = values[f'page-{0x78001000}.bin']
    result['commandline-source.bin'] = page[0x88c:0x897]
    F.require(result['commandline-source.bin'] == bytes.fromhex('ff1534e00278a374710378'),
              'Literal eleven-byte producer remains unpatched')
    result['parser-source.bin'] = values[f'page-{0x7800b000}.bin'][0xc48:0xdfc]
    F.require(hashlib.sha256(result['parser-source.bin']).hexdigest() == SOURCE_SHA,
              'Exact full 436-byte original parser remains unpatched')
    if owned is not None:
        result['commandline-owned.bin'] = owned
    return result

def commandline_identity(row, host_bytes):
    before = (row / 'commandline-api-before.bin').read_bytes()
    after = (row / 'commandline-api-after.bin').read_bytes()
    F.require(before == after and len(before) == 2184, 'Full actual command-line API identity before and after')
    address, named, owner, owner_named = struct.unpack_from('<4Q', before)
    base, size, allocation, state, kind, protection, allocation_protection = struct.unpack_from('<3Q4I', before, 32)
    F.require(address == named == owner_named and owner == allocation and base <= address < base + size,
              'Named and forwarded actual executable command-line API target')
    F.require(state == 0x1000 and kind == 0x1000000 and protection & 0xf0 and not protection & 0x101,
              'Committed executable loaded native API image')
    digest = before[72:136].decode('ascii')
    path = Path(before[136:].decode('utf-16-le').split('\0')[0])
    F.pin(path, digest)
    borrowed = (row / 'commandline-host-pointer.bin').read_bytes()
    F.require(len(borrowed) == 8, 'Host borrowed pointer has its full uint64 extent')
    pointer = struct.unpack('<Q', borrowed)[0]
    F.require(pointer != 0 and pointer + len(host_bytes) <= 1 << 64, 'Actual host input extent does not wrap')
    regions = (row / 'commandline-host-regions.bin').read_bytes()
    F.require(regions and len(regions) % 40 == 0, 'Complete bounded host input memory regions')
    covered = pointer
    for offset in range(0, len(regions), 40):
        rb, rs, ra, st, ty, pr, ap = struct.unpack_from('<3Q4I', regions, offset)
        F.require(rs != 0 and rb + rs <= 1 << 64 and rb <= covered < rb + rs and
                  st == 0x1000 and not pr & 0x101 and pr & 0xee,
                  'Contiguous committed readable host command-line region')
        covered = rb + rs
    F.require(covered >= pointer + len(host_bytes), 'All measured NUL-inclusive host bytes covered')
    metadata = json.loads((row / 'commandline-api-identity.json').read_bytes())
    F.require(metadata == dict(before=digest, after=digest, target=address, named_target=named,
                               owner=owner, owner_named_target=owner_named), 'Legacy identity agrees with complete packed witness')

def positive(row, entry, phases, program, parser_program, index, worker, host_bytes, argv, attack):
    result = json.loads((row / 'result.json').read_bytes())
    F.require(result['passed'] and result['scenario'] == index and result['control'] == 0,
              'Ordinary row request identity')
    F.require(result['writer_complete'] and result['entry_executed'] and result['poisoned_retry'] and
              not result['State_reseed_after_writer'] and not result['full_CRT'] and not result['whole_M4_complete'],
              'Declared bounded startup without reseed/full-CRT credit')
    F.require(result['source_events'] == len(entry.events) and result['writer_events'] == 97 and result['data_routes'] == 1,
              'Complete earlier source ledgers remain intact')
    F.require(host_bytes == subprocess.list2cmdline(argv).encode('mbcs') + b'\0',
              'Actual measured native command line binds the root-owned launch request')
    F.require(host_bytes[0] == 0x44, 'Exact measured D-leading native parser domain')
    commandline_identity(row, host_bytes)
    base = phases['mainargs-builder-after']
    state, memory, fx, cpu = bytearray(entry.state), copy.deepcopy(entry.mem), bytes(entry.fx), bytes(entry.runtime_cpu)
    witness = (row / 'filename-witness.bin').read_bytes()
    F.require(len(witness) == 536, 'Whole native filename witness')
    capacity, incoming, length, error = struct.unpack('<4I', witness[:16])
    before, after = witness[16:276], witness[276:]
    F.require((capacity, incoming) == (260, 0xa11c0000 + index) and 0 < length < 260 and after[length] == 0,
              'Exact filename request and measured return')
    F.require(before == bytes(memory[0x7803b000][0x3f0:0x4f4]) and after[length + 1:] == before[length + 1:],
              'Independently predicted API scratch and untouched tail')
    module_path = F.identities(row, worker)
    F.require(after[:length].decode('mbcs') == str(module_path), 'Actual filename denotes this native worker')
    filename_job = F.words((row / 'filename-job.bin').read_bytes(), 22)
    F.require(filename_job[:5] == (0, incoming, 0x20001834, length, error) and
              filename_job[5] == filename_job[6] and filename_job[18] == filename_job[19],
              'Exact normal filename request/result and inner/outer LastError closure')
    F.require(filename_job[7:18] == (5, 5, 0, 0, 1, 0, 1, 1, 1, 1, 0) and
              filename_job[20:] == (0x78037174, 0x7800bbd6),
              'Exact filename five-hook completed service/consumer lifecycle')
    F.require((row / 'filename-reason.txt').read_text().strip() == '',
              'Successful filename service retains no fabricated fault')
    phases['filename-before'] = base
    phases['filename-api-after'] = base
    memory[0x7803b000][0x3f0:0x4f4] = after
    phases['filename-buffer-after'] = OLD.stage(state, fx, cpu, memory)
    struct.pack_into('<I', state, 2216, length)
    struct.pack_into('<I', state, 2312, 0x20001844)
    struct.pack_into('<I', state, 2472, 0x7800bbd6)
    phases['filename-return-after'] = OLD.stage(state, fx, cpu, memory)
    phases['filename-commandline-before'] = phases['filename-return-after']
    phases['commandline-consumer-before'] = phases['filename-return-after']
    holder = type('ExpectedConsumerMachine', (), dict(state=state, mem=memory, fx=fx, runtime_cpu=cpu))()
    consumed = consumer_predict(holder, program, host_bytes)
    parser_before = OLD.stage(consumed['state'], consumed['fx'], consumed['cpu'], consumed['memory'])
    phases['commandline-parser-before'] = parser_before
    parser_holder = type('ExpectedParserMachine', (), dict(state=consumed['state'],
        mem=consumed['memory'], fx=consumed['fx'], runtime_cpu=consumed['cpu']))()
    parsed = parser_predict(parser_holder, parser_program, host_bytes)
    phases.update(parsed['phases'])
    final = OLD.stage(parsed['state'], parsed['fx'], parsed['cpu'], parsed['memory'])
    for name in ('mainargs-builder-after', 'mainargs-after', 'entry-after-fault', 'retry-after'):
        phases[name] = final

    before_owned = {'mainargs-before', 'commandline-producer-before', 'commandline-producer-projected',
                    'commandline-api-before', 'commandline-api-after'}
    for tag, values in list(phases.items()):
        has_owned = (tag.startswith(('mainargs-', 'filename-', 'commandline-', 'parser-')) and tag not in before_owned) or tag in ('entry-after-fault', 'retry-after')
        phases[tag] = enrich(values, host_bytes if has_owned else None)
    tags = {name.split('/')[1] for name in row.inventory
            if name.startswith(row.name + '/') and name.count('/') == 1}
    F.require(tags == set(phases), 'Exact independently derived checkpoint inventory')
    for tag, values in phases.items():
        F.full_stage(row, tag, values, attack and tag.startswith(('commandline-', 'filename-', 'parser-')))

    evidence = OLD.evidence(entry)
    routes = list(entry.args_events)
    routes.append((5, 0x7800bbd6, 0x20001844, length))
    routes.append((6, 0x7800bbf7, 0x7800bc48, 0x7800bbfc))
    evidence['mainargs-events.bin'] = b''.join(struct.pack('<4I', *v) for v in routes) + bytes(256 - len(routes) * 16)
    job = list(entry.args_job)
    job[11], job[18], job[19] = len(routes), parsed['stop_PC'], parsed['stop_address']
    evidence['mainargs-job.bin'] = struct.pack('<20I', *job)
    for name, value in evidence.items():
        actual = (row / name).read_bytes()
        F.require((json.loads(actual) if name.endswith('.json') else actual) == value,
                  'Complete earlier independent evidence: ' + name)
    F.require((result['fault_reason'], result['fault_site'], result['fault_target']) == (0, parsed['stop_PC'], parsed['stop_address']),
              'Typed refusal before actual uninitialized locale-table read')
    F.require((row / 'mainargs-reason.txt').read_text().strip() == 'Required initialized CRT lead-byte table remains unresolved',
              'Required locale dependency reason retained')
    F.require((row / 'commandline-reason.txt').read_text().strip() == '',
              'Completed command-line producer and consumer retain no fabricated fault')
    for name in ('writer', 'entry'):
        M.D.host((row / f'{name}-host-before.bin').read_bytes(), (row / f'{name}-host-after.bin').read_bytes())
    actual_job = (row / 'entry-job.bin').read_bytes()
    F.require(len(actual_job) == 40 and actual_job[32:] == bytes(8) and
              struct.unpack_from('<3I', actual_job, 20) == (0, parsed['stop_PC'], parsed['stop_address']),
              'Actual ordinary boundary job and no fixture callback')
    # New source accesses are independently known, not inferred from a count.
    accesses = b''.join(struct.pack('<5I', *v) for v in consumed['accesses'])
    F.require((row / 'commandline-consumer-accesses.bin').read_bytes() == accesses + bytes(320 - len(accesses)),
              'Whole nine-entry consumer access ledger including CMP8 and CALL')
    producer = b''.join(struct.pack('<5I', *v) for v in entry.cmd_accesses)
    F.require((row / 'commandline-accesses.bin').read_bytes() == producer + bytes(320 - len(producer)),
              'Whole actual producer IAT/CALL/MOV source access ledger')
    job = F.words((row / 'commandline-job.bin').read_bytes(), 28)
    before = entry.cmd_phases['commandline-producer-before']
    saved_pc = struct.unpack_from('<I', before[0], 2472)[0]
    saved_eax = struct.unpack_from('<I', before[1])[0]
    F.require(job[:9] == (0, 0x20001860, saved_pc, saved_eax, 0x3442e,
                         len(host_bytes), 3, 7, 9), 'Exact producer admission and access counts')
    F.require(job[9:23] == (8, 0, 0, 0,
                           1, 0, 1, 1, 1, 1, 1, 1, 1, 0),
              'Exact terminal producer/consumer/parser boundary lifecycle')
    F.require(job[23] == job[24] and job[25:] == (0x33000000, 0x78037174, 0x78001897),
              'Host LastError preserved and typed guest pointer separated')
    events = [(1, 0x7800188c, 0x20001860, saved_pc),
              (2, 0x7800188c, 0x7802e034, 0x3442e),
              (3, 0x78001892, 0x33000000, len(host_bytes)),
              (4, 0x78001897, 0x78037174, 0x33000000),
              (5, saved_pc, 0x78037174, 0x33000000),
              (6, 0x7800bbd6, 0x78037174, 0x33000000),
              (7, 0x7800bbf7, 0x7800bc48, 0x7800bbfc)]
    event_bytes = b''.join(struct.pack('<4I', *v) for v in events)
    F.require((row / 'commandline-events.bin').read_bytes() == event_bytes + bytes(256 - len(event_bytes)),
              'Complete producer and consumer source-qualified route ledger')
    F.require(len(parsed['accesses']) == 16 and len(parsed['PCs']) == 23 and
              not parsed['locale_read_completed'], 'Complete source prefix before denied table access')
    parser_accesses = b''.join(struct.pack('<5I', *v) for v in parsed['accesses'])
    F.require((row / 'parser-accesses.bin').read_bytes() == parser_accesses + bytes(640 - len(parser_accesses)),
              'Entire parser PUSH, argument, count and immutable-input access ledger')
    F.require(F.words((row / 'parser-undefined.bin').read_bytes(), 8) ==
              (0x7800bc66, 0x7800bcd7, 0, 0, 0, 0, 0, 0),
              'Exact two TEST undefined-AF representative sites')
    parser_events = [(1, 0x7800bbf7, 0x7800bc48, 0x7800bbfc),
                     (2, 0x7800bc48, 0x2000182c, 0x7800bbfc),
                     (3, parsed['stop_PC'], parsed['stop_address'], 0x44)]
    parser_events_bytes = b''.join(struct.pack('<4I', *v) for v in parser_events)
    F.require((row / 'parser-events.bin').read_bytes() == parser_events_bytes + bytes(128 - len(parser_events_bytes)),
              'Entire source-qualified parser route and uninitialized locale refusal ledger')
    F.require(F.words((row / 'parser-job.bin').read_bytes(), 20) ==
              (0, 0x2000182c, 0x20001860, 16, 3, 2, 4, 0, parsed['stop_PC'],
               parsed['stop_address'], 1, 0, 1, 1, 0x7800bc48, 0x7800bbf7,
               0x7800bbfc, 0x7800bce6, 0x780379e1, 436),
              'Exact normal parser immutable frame, lifecycle, source and first-fault metadata')
    F.require((row / 'parser-reason.txt').read_text().strip() ==
              'Required initialized CRT lead-byte table remains unresolved', 'Typed parser first dependency reason')
    return dict(index=index, control=0, producer_source_bytes=11,
                consumer_source_instructions=len(consumed['PCs']), consumer_memory_accesses=9,
                borrowed_pages=16, owned_bytes=len(host_bytes), parser_CALL_executed=True,
                parser_body_executed=True, parser_source_instructions=len(parsed['PCs']),
                parser_memory_accesses=16, locale_read_completed=False, parser_RET_executed=False,
                State3504_FX512=True, checkpoints=len(phases))

def main(execution_directory, output_directory):
    started = time.perf_counter_ns()
    out = workspace_path(output_directory, reports=True)
    if out.exists() or out.parent != ROOT / 'reports/m4-crt-parser-prefix':
        raise ValueError('Fresh root observer output required')
    out.mkdir()
    passed, rows = False, []
    try:
        for path in Path(__file__).parent.glob('*.py'):
            F.pin(path)
        for name, digest in F.PIPELINE_SHAS.items():
            F.pin(ROOT / 'tools/m4-pipeline' / name, digest)
        execution_path = F.pin(Path(execution_directory) / 'report.json')
        execution = json.loads(execution_path.read_text(encoding='utf-8'))
        F.require(execution['passed'] and execution['native_executed_by_root'], 'Fresh root native execution')
        for p, h in execution['files'].items():
            F.pin(p, h)
        program, providers, maths, ctrl, init, args, argv, source, commands = M.source_material(out)
        parser_program, parser_command = parser_source(out)
        wp, pp, gp = M.R.source_material()
        original_path = F.pin(ROOT / 'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin', F.ORIGINAL_SHA)
        originals = M.R.originals(original_path.read_bytes())
        payloads = [M.R.project(v) for v in originals[:24]]
        for level in ('O0', 'O2'):
            identity = execution['levels'][level]
            bundle = F.pin(identity['bundle'], identity['bundle_sha256'])
            worker = F.pin(identity['worker'])
            with CaptureBundle(bundle, identity['bundle_sha256']) as reader:
                F.require(reader.read_bytes('COMPLETE') == b'COMPLETE', 'Strict bundled completion')
                root = F.LogicalPath(reader, 'root')
                for index in range(24):
                    row = F.LogicalPath(reader, f'row-{index}', root.inventory)
                    host_bytes = (row / 'commandline-api-bytes.bin').read_bytes()
                    entry, phases = expected(row, payloads[index], wp, pp, gp, program,
                        providers, maths, ctrl, init, args, argv, source, host_bytes, level)
                    rows.append(dict(level=level, **positive(row, entry, phases, argv, parser_program, index,
                        worker, host_bytes, identity['argv'], index == 0)))
        for module in (M, M.M, M.M.M, M.M.M.M, M.D, M.R, M.N, M.D.E, M.F, M.C):
            for p, h in module.PINS.items():
                F.pin(p, h)
        F.pin(ROOT / 'tools/m4-crt-filename-root/observe.py', F.FILENAME_SHA if hasattr(F, 'FILENAME_SHA') else '405797301b25103cdc27dd0635e93e169a4ef86f415afb7c8a431da23703733e')
        F.pin(subprocess.__file__)
        for p in out.iterdir():
            if p.is_file():
                F.pin(p)
        closure = verify_manifest(F.PHYSICAL)
        passed = True
    except Exception:
        publish_bytes(out / 'failure.txt', traceback.format_exc().encode('utf-8'))
        raise
    finally:
        report = dict(passed=passed, rows=rows, checks=F.CHECKS,
            scope='Independent original BEFORE/source derivation and two declared native OS witnesses',
            independently_modeled_ordinary_sequences=48 if passed else 0,
            standard_causal_sequences_independently_modeled_by_root=0,
            selected_semantic_byte_corruption_denials=F.SEMANTIC_DENIALS,
            State_bytes=3504, FX_bytes=512, borrowed_pages=16, new_owned_buffer=0x33000000,
            source_writer_and_consumer_executed=passed, parser_body_executed=passed,
            parser_source_bytes=436, source_identity_bytes=1587, locale_read_completed=False,
            parser_RET_executed=False, parser_sizing_complete=False,
            DllMain_or_original_scheduling_recovered=False, State_reseed=False,
            argument_initialization_complete=False, main_initializer_count=27,
            whole_M4_complete=False, game_launched=False, original_executed=False,
            author_expected_model_imported=False, files=F.PHYSICAL,
            physical_closure=closure if passed else None,
            seconds=(time.perf_counter_ns() - started) / 1e9)
        publish_bytes(out / 'report.json', (json.dumps(report, indent=2) + '\n').encode('utf-8'))
        print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'rows')}))

if __name__ == '__main__':
    main(*sys.argv[1:])
