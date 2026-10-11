"""Independently check actual connected refusal bytes using sealed raw exports.

The semantic producer remains responsible for literal source derivation. This
review joins that derivation to every actual accepted operand, complete borrowed
backing, retry vector, caller boundary and physical native resource invocation.
No canonical capture archive is opened here.
"""
from pathlib import Path
import collections, hashlib, importlib.util, json, struct, sys, traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PINS = {}

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def need(value, label):
    if not value: raise ValueError(label)

def eq(actual, expected, label):
    need(actual == expected, label)

def pin(path, identity=None):
    path = Path(path).resolve(); actual = sha(path)
    need(identity is None or actual == identity, 'Exact physical input ' + str(path))
    need(str(path) not in PINS or PINS[str(path)] == actual, 'Stable physical input')
    PINS[str(path)] = actual
    return path

def read(path, identity=None):
    return json.loads(pin(path, identity).read_bytes())

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, pin(path))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def main(source_path, source_sha, name):
    out = ROOT / 'reports/m4-tree-review' / name
    need(not out.exists(), 'Fresh independent controls review'); out.mkdir()
    passed = False; closed = True; counts = collections.Counter(); joins = []; proofs = {}
    try:
        source = read(source_path, source_sha)
        need(source['passed'] and source['all_bounded_readers_closed'] and source['raw_export_readers_closed'] and source['raw_exports_all_logical_entries'], 'Complete semantic and raw export closure')
        execution = read(source['execution'], source['execution_sha256'])
        need(execution['passed'] and execution['all_workers_terminal'] and execution['all_bounded_readers_closed'], 'Actual current workers completed')
        build = read(execution['build'], execution['build_sha256'])
        preparation = read(build['preparation'], build['preparation_sha256'])
        cases = read(Path(source_path).parent / 'causal-controls.json')
        eq({(c['level'], c['mode']) for c in cases}, {(l, m) for l in ('O0', 'O2') for m in range(1, 13)}, 'Exactly all24 actual refusal cases')
        eq(len(cases), 24, 'No duplicate refusal case')
        X = load(ROOT / 'tools/m4-joint-startup131/paired_exports.py', 'root_mfc_controls_exports')
        V = load(ROOT / 'tools/m4-mfc1168-native/verify_resource_fixture.py', 'root_mfc_controls_physical'); V.PINS = PINS
        reasons = {1:'source segment/entry identity', 2:'literal physical source span', 3:'physical raw import preimage', 4:'TIB TLS mirror', 5:'borrowed BEFORE', 6:'borrowed BEFORE', 7:'Guest access permission denied', 8:'Guest access permission denied', 9:'physical raw import preimage', 10:'cached CRT additions', 11:'Typed guest TLS index3/borrowed CS24 argument', 12:'source segment/entry identity'}
        eq([r['branch'] for r in source['raw_exports']], ['O0', 'O2'], 'Both compiler levels with ordered actual raw exports')
        for row in source['raw_exports']:
            level = row['branch']; eq((row['logical_files'], row['payload_bytes']), (4345, 36743981), 'Whole measured raw export extent')
            a = X.Facade(row, pin); closed = False
            try:
                for key in a.entries: a.data(key); counts['whole_export_targets_authenticated'] += 1
                for mode in range(1, 13):
                    case = next(c for c in cases if c['level'] == level and c['mode'] == mode)
                    stem = f'control-{mode}/'; terminal = a.words(stem + 'terminal-facts.bin', 13)
                    eq(terminal[:7], (1, mode, 0, 1, 1, 13, 13), 'Actual failure poison and thirteen preceding roots'); eq(list(terminal), case['terminal'], 'Whole actual terminal observation')
                    has = bool(terminal[7]); eq(a.words(stem + 'facts.bin', 8), (1, mode, 13, 1, 1, 1, 1, int(has)), 'Actual refusal retry and cleanup facts')
                    reason = a.data(stem + 'refusal.txt').decode(); eq(reason, case['reason'], 'Whole actual precise refusal reason'); need(reasons[mode].lower() in reason.lower(), 'Expected precise refusal domain')
                    need(case['complete_private_retry_compared'] and case['attempted_mutation_source_authored'] and not case['rejected_local_read_payload_observed'], 'Honest admitted-source and observed retry scope')
                    counts['actual_precise_denials'] += 1
                    for prefix in (stem + 'retry-before/', stem + 'MFC/retry-before/'):
                        keys = {k for k in a.entries if k.startswith(prefix)}
                        after_prefix = prefix.replace('/retry-before/', '/retry-after/')
                        eq({k[len(prefix):] for k in keys}, {k[len(after_prefix):] for k in a.entries if k.startswith(after_prefix)}, 'Entire retry vector set')
                        if '/MFC/' not in prefix:
                            need(keys, 'Actual complete refused runtime retry')
                            eq(len(a.data(prefix + 'State.bin')), 3504, 'Whole retry State3504'); eq(len(a.data(prefix + 'CPU.bin')), 40, 'Whole retry CPU40'); eq(len(a.data(prefix + 'FX.bin')), 512, 'Whole retry FX512')
                        for key in keys:
                            eq(a.data(key), a.data(key.replace('/retry-before/', '/retry-after/')), 'Entire poisoned retry unchanged ' + key); counts['whole_retry_vectors'] += 1
                    for suffix in ('caller-hardware.bin', 'retry-hardware.bin'):
                        hw = a.data(stem + suffix); eq(len(hw), 1632, 'Complete three-sided actual hardware observation'); eq(hw[:512], hw[1088:1600], 'Whole caller FX512 restored'); eq(hw[512:540], hw[1600:1628], 'Whole caller ENV28 restored'); counts['whole_caller_FX512_ENV28'] += 1
                    if has:
                        prefix = stem + 'MFC/'; accesses = list(struct.iter_unpack('<IIQII', a.data(prefix + 'refused/accesses.bin')))
                        eq([list(v) for v in accesses], case['source_access_prefix'], 'Every actual accepted source operand with semantic derivation')
                        eq(len(a.data(prefix + 'refused/APIs.bin')), case['source_API_records'] * 352, 'Entire typed source API vector')
                        memory = {}
                        for address, size in struct.iter_unpack('<2I', a.data(prefix + 'entry/memory-index.bin')):
                            need(address not in memory, 'Unique complete own-entry extent'); memory[address] = a.data(prefix + f'entry/memory-{address}-{size}.bin'); eq(len(memory[address]), size, 'Whole own entry BEFORE bytes')
                        eq(len(case['borrowed_byteflows']), 5, 'Every borrowed owner represented')
                        committed = accesses[:-1] if mode == 7 else accesses
                        for index, owner in enumerate(preparation['inputs']['role_owners']):
                            before = memory[owner['new']]; eq(len(before), owner['extent'], 'Whole actual borrowed owner capacity')
                            expected = bytearray(before)
                            for pc, address, value, width, writing in committed:
                                if writing and owner['new'] <= address and address + width <= owner['new'] + owner['extent']:
                                    expected[address - owner['new']:address - owner['new'] + width] = value.to_bytes(width, 'little')
                            flow = case['borrowed_byteflows'][index]; eq(flow['role'], owner['role'], 'Exact source role'); eq(bytes.fromhex(flow['initial_hex']), before, 'Source own-entry role input'); eq(bytes.fromhex(flow['source_refused_hex']), bytes(expected), 'Committed source-only role flow'); eq(a.data(prefix + f'refused/borrowed/{index}.bin'), bytes(expected), 'Whole actual borrowed bytes versus causal flow'); counts['whole_borrowed_capacity_prefixes'] += 1
                        eq(memory[preparation['inputs']['guest_CS']], a.data(prefix + 'refused/guestCS24.bin'), 'Complete borrowed guest CS24 unchanged before refused API transport'); counts['whole_borrowed_guestCS24_prefixes'] += 1
                        if mode == 7:
                            eq(accesses[-1][1:], (0x33005014, 0, 1, 1), 'Source attempted RO byte14 write retained'); eq(case['recorded_failed_write_payload'], list(accesses[-1]), 'Exact rejected write record'); counts['recorded_rejected_source_write_payloads'] += 1
                        if mode == 11:
                            provenance = case['source_refusal_API_provenance']; eq(len(accesses), 17, 'Exact source TLS refusal prefix')
                            eq(accesses[-4], (0x5f401010, 0x5f4cb008, 0, 4, 0), 'Actual zero TLS-index source read'); eq(accesses[-3][0], 0x5f401010, 'Actual source push PC'); eq(accesses[-3][2:], (0, 4, 1), 'Actual committed zero TLS argument')
                            eq(provenance['source_argument'], 0, 'Observed source zero TLS argument'); eq(provenance['admitted_argument'], 3, 'Exact service admitted index'); eq(provenance['actual_source_API_records'], 0, 'No refused source API record'); eq(provenance['source_API_entered'], False, 'Typed argument denial precedes source API')
                            frame = provenance['frame']; lower = a.data(stem + 'retry-before/memory-536875008-4096.bin'); need(0x20001000 <= frame and frame + 64 <= 0x20002000, 'Whole source refused call frame range')
                            eq(bytes.fromhex(provenance['source_frame64_hex']), lower[frame - 0x20001000:frame - 0x20001000 + 64], 'Whole actual refused source frame64'); eq(struct.unpack_from('<2I', lower, frame - 0x20001000), (0x5f401018, 0), 'Actual refused source return and zero argument'); counts['source_TLS_refusal_frame64'] += 1
                        context = a.words(prefix + 'cleaned/resource-context.bin', 12, 'Q'); eq(context[2:7], (0, 0, 0, 0, 0), 'Actual cleaned resource ownership')
                        virtual = (out / f'logical-{level}-{mode}').resolve(); oldraw = V.raw
                        def virtual_raw(path):
                            path = Path(path).resolve()
                            return a.data(prefix + path.relative_to(virtual).as_posix()) if path.is_relative_to(virtual) else oldraw(path)
                        V.raw = virtual_raw; tls = None; assoc = 0; section = None; depth = 0; freed = False; deleted = False; thread = None
                        try:
                            for serial in range(context[11]):
                                base = virtual / 'resources' / str(serial); w = struct.unpack('<8Q', virtual_raw(base / 'call.bin')); eq(w[:2], (1, serial), 'Actual contiguous live service'); kind, arg0, arg1, result, tid, error = w[2:]; need(kind < 8, 'Finite refused-prefix service'); thread = tid if thread is None else thread; eq(tid, thread, 'Same actual owning thread')
                                identity = V.native_identity(base, kind, proofs); before = virtual_raw(base / 'CS-before40.bin'); after = virtual_raw(base / 'CS-after40.bin'); eq((len(before), len(after)), (40, 40), 'Both whole native CS40 observations')
                                if kind == 0: need(tls is None and result != 0xffffffff, 'One successful actual TLS allocation'); tls = result
                                elif kind == 1: eq(arg0, tls, 'Owned TLS association slot'); need(not freed and result == 1, 'Live successful TLS set'); assoc = arg1
                                elif kind == 2: eq(arg0, tls, 'Owned TLS lookup slot'); need(not freed and result == assoc, 'Actual owned current-thread lookup')
                                elif kind == 3: eq(arg0, tls, 'Owned TLS release slot'); need(not freed and not assoc and result == 1, 'Clear before actual TLS release'); freed = True
                                elif kind == 4: need(section is None, 'One actual native CS initialization'); section = arg0; eq(V.cs(after), (0, 0), 'Actual native CS initialized unheld')
                                elif kind in (5, 6):
                                    eq(arg0, section, 'Exact owned native CS'); need(not deleted, 'Live native CS'); eq(V.cs(before), (depth, thread if depth else 0), 'Actual incoming CS depth and owner'); depth += 1 if kind == 5 else -1; need(depth in (0, 1), 'Finite balanced actual depth'); eq(V.cs(after), (depth, thread if depth else 0), 'Actual outgoing CS depth and owner')
                                elif kind == 7: eq(arg0, section, 'Owned CS destruction'); need(not deleted and not depth, 'Unheld actual CS release'); deleted = True
                                joins.append(dict(level=level, mode=mode, serial=serial, kind=kind, call_words=list(w), proof_identity=[kind, identity['actual_owner'], identity['RVA'], identity['entry64']])); counts['actual_API_identity_CS40_sides'] += 2
                            need(tls is not None and freed and section is not None and deleted and not depth, 'Actual owned TLS and CS released'); counts['actual_owned_lifecycles'] += 1
                        finally: V.raw = oldraw
                    else:
                        need(not any(k.startswith(stem + 'MFC/resources/') for k in a.entries), 'Early refusal has no owned native resource'); counts['pre_resource_refusals'] += 1
                    counts['actual_unchanged_poisoned_retries'] += 1
            finally: a.close(); a.entries.clear(); closed = True
        eq(joins, read(Path(source_path).parent / 'actual-provider-identity-joins.json'), 'Every actual physical provider invocation independently reproduced')
        eq(list(proofs.values()), read(Path(source_path).parent / 'unique-physical-API-proofs.json'), 'Complete unique physical API export proofs independently reproduced')
        for field, expected in source['counts'].items(): eq(counts[field], expected, 'All measured semantic extents independently joined ' + field)
        pin(__file__); pin(sys.executable)
        for path, identity in PINS.items(): eq(sha(path), identity, 'Every actual raw and physical input stable after closure')
        passed = True
    except BaseException:
        (out / 'failure.txt').write_text(traceback.format_exc()); raise
    finally:
        result = dict(passed=passed, scope='Independent complete sealed raw refusal, retry, caller, borrowed source byteflow, TLS argument and actual physical API/CS40/lifetime joins', controls_verification_sha256=source_sha, counts=dict(counts), all_bounded_readers_closed=closed, capture_archives_opened=0, initializer_credit=0, files=PINS)
        (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(dict(passed=passed, sha256=sha(out / 'report.json'), counts=dict(counts))), flush=True)

if __name__ == '__main__': main(Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3])
