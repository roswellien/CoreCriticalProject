"""Independent affine-source audit of the heap initializer BEFORE model."""
import argparse
import contextlib
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import time
import types
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
BASE = ROOT / 'reports/m4-crt-heap-init-root-audit'
sys.path.insert(0, str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path
from stages import verify_stage
SOURCE = ROOT/'reports/m4-crt-heap-init-recovery/recovery-r1/report.json'
SOURCE_SHA = '4706dd8c297247de56da28566f4c3e2b4891c68cc8db8deb28dc604608b5498b'
CONSUMER_SHA = '01c0c248f00785acb73b5c1ce96f2ddda1b675db6c60a0602bf04c175b1b48a8'
ORIGINAL_SHA = 'cbcb423813a712851f63a4921b72544499e74488d24184a4f084a74ae14009b2'
PRIOR = ROOT/'reports/m4-crt-commandline-carry/root-execution-r1'
STATE_FLAGS = ((2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11))
ARITH_FLAGS = tuple(pair for pair in STATE_FLAGS if pair[1] != 10)


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main(args):
    started = time.perf_counter_ns()
    out = workspace_path(args.output, reports=True)
    need(out.parent == BASE and not out.exists(), 'Fresh immediate audit output')
    files = {}

    def add(path, digest=None):
        path = Path(path).absolute()
        key, value = normalized(str(path)), sha(path) if digest is None else digest
        need(key not in files or files[key] == value, 'Stable unique current dependency')
        need(sha(path) == value, 'Physical byte identity '+str(path))
        files[key] = value
        return path

    source = read(add(SOURCE, SOURCE_SHA))
    add(SOURCE.parent/'pins.json')
    for path, digest in read(SOURCE.parent/'pins.json')['files'].items():
        add(path, digest)
    for path in (Path(__file__), Path(__file__).with_name('README.md'), Path(sys.executable),
                 ROOT/'tools/m4-pipeline/capture_bundle.py', ROOT/'tools/m4-pipeline/manifests.py',
                 ROOT/'tools/m4-pipeline/paths.py', ROOT/'tools/m4-pipeline/stages.py'):
        add(path)
    core = ROOT/'tools/m4-crt-heap-init-root'
    for name in ('before.py', 'prefix.py'):
        add(core/name)
    add(core/'consumer.py', CONSUMER_SHA)
    original_path = add(ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin', ORIGINAL_SHA)
    history = BASE/'tool-history-r1'
    for name, digest in (('audit.py','1429d52619bc57cb55732f7c6bb227c0ab541e82c185913f8b1f2fb709338d0b'),
                         ('README.md','bf1cc2c4137b4d2c1c33220021bcc1fcd0fa212560d1f9da0906afc490527ea3')):
        add(history/name,digest)
    add(history/'pins.json')
    supplied = (args.execution, args.execution_sha, args.observer, args.observer_sha, args.stage, args.stage_sha)
    need(all(supplied) or not any(supplied), 'All final receipts and explicit hashes, or draft only')
    if args.observer:
        add(core/'observe.py')
    initial_check = verify_manifest(files)
    out.mkdir(parents=True)
    previous = {name:sys.modules.get(name) for name in ('consumer','before')}
    consumer = load('heap_independent_audit_consumer', core/'consumer.py')
    sys.modules['consumer'] = consumer
    try:
        before = load('heap_independent_audit_before', core/'before.py')
        sys.modules['before'] = before
        prefix = load('heap_independent_audit_prefix', core/'prefix.py')
    finally:
        for name, value in previous.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value
    F, M, OLD = consumer.F, consumer.M, consumer.OLD
    need(tuple(M.F.FLAGS) == STATE_FLAGS, 'Fixed inherited State flag offsets')
    need(list(prefix.PCS) == source['executed_source_prefix_PCs'], 'Exact independent nine-PC source order')
    program, providers, maths, ctrl, init, mainargs, argv, pages, commands = M.source_material(out)
    wp, pp, gp = M.R.source_material()
    heap_program, page, heap_commands = prefix.source_material(out)
    provider = M.N.PE.PEImage((ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes())
    raw_page = M.D.mapped(provider, 0x78003000)
    need(page == raw_page and len(page) == 4096, 'Existing literal RX source page identity')
    pages[0x78003000] = raw_page
    for label in ('attach-fragment','heap-initializer'):
        for instruction in source['spans'][label]['instructions']:
            size, op, operands = heap_program[instruction['pc']]
            need(size == len(bytes.fromhex(instruction['bytes_hex'])) and op == instruction['mnemonic']
                 and ' '.join(', '.join(operands).split()) == ' '.join(instruction['operands'].split()),
                 'Fresh exact complete source decode')
    original = M.R.originals(original_path.read_bytes())
    payloads = [M.R.project(row) for row in original[:24]]
    checks, rows, native_count, unused_count = 0, [], 0, 0

    def eq(actual, expected, why):
        nonlocal checks
        checks += 1
        need(actual == expected, why)

    def stage(state, fx, cpu, memory):
        value = OLD.stage(state, fx, cpu, memory)
        for name, address, start, end in (
                ('page-2013278208.bin',0x78003000,0,4096),
                ('commandline-source.bin',0x78001000,0x88c,0x897),
                ('parser-source.bin',0x7800b000,0xc48,0xdfc),
                ('locale-stub.bin',0x78003000,0xdd2,0xddb),
                ('locale-setmbcp.bin',0x78003000,0xddb,0xe84),
                ('locale-lock.bin',0x78001000,0x55,0xb0),
                ('heap-fragment.bin',0x78001000,0x83c,0x843),
                ('heap-provider.bin',0x78003000,0x9bf,0xa0c)):
            value[name] = bytes(memory[address][start:end])
        return value

    def memory(*values):
        result = OLD.base_memory(*values)
        result[0x78003000] = bytearray(raw_page)
        return result

    frozen_writer = types.FunctionType(F.writer.__code__, dict(F.writer.__globals__, base_memory=memory, stage=stage))
    frozen_full = types.FunctionType(OLD.expected.__code__, dict(OLD.expected.__globals__, writer_result=frozen_writer, stage=stage))
    readers, final = {}, None
    stack = contextlib.ExitStack()
    if all(supplied):
        execution = read(add(args.execution, args.execution_sha))
        observer = read(add(args.observer, args.observer_sha))
        need(execution['passed'] and observer['passed'], 'Successful explicitly bound final receipts')
        need(observer['AFTER_machine_state_used_as_seed'] is False and observer['author_expected_model_imported'] is False,
             'Native observer no AFTER machine or author model seed')
        need(observer['root_full_causal_model_sequences'] == 0,
             'No full independent causal-model claim')
        need(observer['original_BEFORE_ordinary_sequences'] == 48
             and observer['independently_executed_by_root'] is False
             and observer['execution_sha256'] == args.execution_sha,
             'Exact delegated native receipt and bounded original-BEFORE scope')
        add(args.stage,args.stage_sha)
        for level in ('O0','O2'):
            identity = execution['levels'][level]
            add(identity['bundle'], identity['bundle_sha256'])
            readers[level] = stack.enter_context(CaptureBundle(identity['bundle'], identity['bundle_sha256']))
            need(len(readers[level].names()) == identity['logical_files']
                 and readers[level].read_bytes('COMPLETE') == b'COMPLETE', 'Complete strict current archive')
    for level in ('O0','O2'):
        for index, payload in enumerate(payloads):
            if readers:
                row = F.LogicalPath(readers[level], 'row-'+str(index))
            else:
                row = PRIOR/('native-'+level)/('row-'+str(index))
                for name in ('input.bin','writer-record.bin'):
                    add(row/name)
            base, phases = before.expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,mainargs,argv,pages,level)
            full, full_phases = frozen_full(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,mainargs,argv,pages,0,level)
            seam = full.args_phases['mainargs-before']
            eq(bytes(base.state),seam[0],'Whole3504 source-derived seam State')
            eq(bytes(base.fx),seam[3],'Whole512 source-derived seam FX')
            eq(bytes(base.runtime_cpu),seam[1],'Whole40 actual mainargs RuntimeCPU')
            eq(base.mem,seam[2],'All17 source-derived seam page bytes')
            need(base.init_complete and not base.init_failed and not base.args_failed and not base.args_used
                 and base.args_accesses == [], 'Healthy seam before argument-provider admission')
            for tag, value in phases.items():
                eq(value,full_phases[tag],'All independently recomputed prior phase bytes '+tag)
            result = prefix.predict(base,heap_program)
            initial = bytes(base.state)
            final_state = bytearray(initial)
            current_memory = copy.deepcopy(base.mem)
            P = struct.unpack_from('<I',initial,consumer.STATE_REG['esp'])[0]
            need(P == 0x20001860 and struct.unpack_from('<I',base.runtime_cpu,16)[0] == P
                 and struct.unpack_from('<I',base.runtime_cpu,36)[0] == M.SLOT,
                 'Actual inherited mainargs parent frame/site')
            eq(result['phases']['heap-before'],stage(initial,base.fx,base.runtime_cpu,current_memory),'No new BEFORE seed')
            projected = bytearray(initial)
            struct.pack_into('<I',projected,2472,0x7800183c)
            eq(result['phases']['heap-projected'],stage(projected,base.fx,base.runtime_cpu,current_memory),
               'Host changes only StateEIP, with zero stack stores/ESP changes')
            ledger = []
            for access in source['source_access_ledger']:
                expr = access['address_expression']
                address = P-int(expr[2:]) if expr.startswith('P-') else int(expr,0)
                value = access['value']
                if access['write']:
                    need(0x20001000 <= address <= 0x20001ffc,'Exact owned source stack write domain')
                    struct.pack_into('<I',current_memory[0x20001000],address&4095,value)
                else:
                    eq(struct.unpack_from('<I',current_memory[address&~4095],address&4095)[0],value,'Ordered source operand read')
                ledger.append((access['pc'],address,value,4,int(access['write'])))
                if len(ledger) == 2:
                    call_state = bytearray(initial)
                    struct.pack_into('<I',call_state,consumer.STATE_REG['esp'],P-8)
                    struct.pack_into('<I',call_state,2472,0x780039bf)
                    eq(result['phases']['heap-provider-before'],stage(call_state,base.fx,base.runtime_cpu,current_memory),
                       'Whole actual source CALL frame before any XOR or API argument effect')
            struct.pack_into('<I',final_state,consumer.STATE_REG['eax'],0)
            struct.pack_into('<I',final_state,consumer.STATE_REG['esp'],P-24)
            struct.pack_into('<I',final_state,2472,0x3461e)
            for offset, bit in ARITH_FLAGS:
                final_state[offset] = 0
            eq(bytes(result['state']),bytes(final_state),'Whole terminal State from independent source affine ledger')
            eq(result['memory'],current_memory,'All17 pages; only six actual source stack stores change bytes')
            eq(result['fx'],bytes(base.fx),'Whole512 FX carried')
            eq(result['cpu'],bytes(base.runtime_cpu),'Generic RuntimeCPU remains at genuine mainargs boundary')
            eq(result['accesses'],ledger,'All ordered eight source accesses')
            eq(result['PCs'],source['executed_source_prefix_PCs'],'All nine source instruction addresses')
            eq(result['routes'],[(0x7800183e,0x780039bf,0x78001843),(0x780039d0,0x3461e,0x780039d6)],'Two actual source CALLs')
            eq(result['undefined'],[(0x780039bf,0)],'Sole declared source-qualified compiled AF representative; no universal original AF claim')
            eq(result['scheduler'],(1,struct.unpack_from('<I',initial,2472)[0],P,0x7800183c,P,0,M.SLOT,P),
               'Explicit EIP-only scheduler metadata and source-store count zero')
            terminal = stage(final_state,base.fx,base.runtime_cpu,current_memory)
            for tag in ('heap-api-before','heap-after'):
                eq(result['phases'][tag],terminal,'Exact whole unexecuted HeapCreate boundary '+tag)
            need(struct.unpack_from('<I',final_state,2120)[0] == 0 and not result['API_executed']
                 and not result['heap_initialized'],'Flat source SS, no API or initialized heap credit')
            if readers:
                expected = dict(phases,**result['phases'])
                expected['entry-after-fault'] = terminal
                expected['retry-after'] = terminal
                eq(len(expected),27,'Exactly27 independently recomputed native phase snapshots')
                tags = {name.split('/')[1] for name in row.inventory if name.startswith(row.name+'/') and name.count('/') == 1}
                eq(tags,set(expected),'Exact complete current native checkpoint inventory')
                for tag, values in expected.items():
                    eq(row.inventory[row.name+'/'+tag],set(values),'Exact complete native checkpoint files '+tag)
                    eq({name:(row/tag/name).read_bytes() for name in values},values,'Whole current native checkpoint '+tag)
                unused = {
                    'filename-job.bin':struct.pack('<22I',0,0xa11c0000+index,*([0]*18),0x78037174,0x7800bbd6),
                    'filename-witness.bin':bytes(536),
                    'commandline-job.bin':struct.pack('<28I',*([0]*4),0x3442e,*([0]*20),0x33000000,0x78037174,0x78001897),
                    'commandline-accesses.bin':bytes(320),'commandline-consumer-accesses.bin':bytes(320),'commandline-events.bin':bytes(256),
                    'parser-job.bin':struct.pack('<20I',*([0]*14),0x7800bc48,0x7800bbf7,0x7800bbfc,0x7800bce6,0x780379e1,436),
                    'parser-accesses.bin':bytes(640),'parser-events.bin':bytes(128),'parser-undefined.bin':bytes(32),
                    'locale-job.bin':struct.pack('<24I',*([0]*15),0x78003dd2,0x78003ddb,0x78001055,0x7800107b,0x780012b3,0x78001080,0x7803708c,17,269),
                    'locale-accesses.bin':bytes(640),'locale-events.bin':bytes(128),'locale-scheduler.bin':bytes(40),
                }
                for name, value in unused.items():
                    eq((row/name).read_bytes(),value,'Exact native inactive later-service record '+name)
                    unused_count += 1
                for name in ('filename','commandline','parser','locale'):
                    eq((row/(name+'-reason.txt')).read_text().strip(),'','No reason on native inactive later service')
                eq((row/'heap-accesses.bin').read_bytes(),b''.join(struct.pack('<5I',*item) for item in ledger)+bytes(480),
                   'Actual native source8access ledger and zero unused tail')
                events = ((1,0x7800183c,P,0),(2,0x7800183e,0x780039bf,0x78001843),
                          (3,0x780039d0,0x7802e0a8,0x3461e))
                eq((row/'heap-events.bin').read_bytes(),b''.join(struct.pack('<4I',*item) for item in events)+bytes(80),
                   'Actual native projection and both genuine source CALL events')
                scheduler = (1,struct.unpack_from('<I',initial,2472)[0],P,0x7800183c,P,0,M.SLOT,P)
                eq((row/'heap-scheduler.bin').read_bytes(),struct.pack('<8I',*scheduler),
                   'Actual native EIP-only scheduler record, zero host guest stores')
                eq((row/'heap-undefined.bin').read_bytes(),struct.pack('<8I',0x780039bf,*([0]*7)),
                   'Actual native sole source-qualified compiled AF representative')
                job_data = (row/'heap-job.bin').read_bytes()
                need(len(job_data) == 104,'Complete native immutable heap job')
                job = struct.unpack('<26I',job_data)
                eq(job[:14],(0,P-8,P,8,3,1,4,0,0x780039d0,0x7802e0a8,1,0,1,1),
                   'Actual native initializer frame and typed bounded lifecycle')
                eq(job[14],job[15],'Actual native caller LastError restored')
                eq(job[16:],(0x7800183c,0x780039bf,0x7800183e,0x78001843,0x780039d0,
                              0x7802e0a8,0x780039d6,0x3461e,17,84),
                   'Actual native immutable source and page identity metadata')
                prior_evidence = OLD.evidence(base)
                prior_evidence['mainargs-job.bin'] = struct.pack('<20I',M.SLOT,M.RAW,*([0]*13),1,0,0,0x780039d0,0x7802e0a8)
                prior_evidence['mainargs-events.bin'] = bytes(256)
                prior_evidence['mainargs-accesses.bin'] = bytes(1280)
                for name,value in prior_evidence.items():
                    actual = (row/name).read_bytes()
                    eq(json.loads(actual,object_pairs_hook=unique_object) if name.endswith('.json') else actual,value,
                       'All carried prior-source and first-fault ledger bytes '+name)
                for name in ('mainargs','heap'):
                    eq((row/(name+'-reason.txt')).read_text().strip(),'Required KERNEL32.dll HeapCreate remains unresolved',
                       'Actual named first frontier diagnostic')
                current = json.loads((row/'result.json').read_bytes(),object_pairs_hook=unique_object)
                need(current['passed'] and current['scenario'] == index and current['control'] == 0
                     and current['poisoned_retry'] and not current['State_reseed_after_writer']
                     and (current['fault_reason'],current['fault_site'],current['fault_target']) == (1,0x780039d0,0x7802e0a8),
                     'Actual ordinary native request/refusal/retry scope')
                native_count += 1
            rows.append(dict(level=level,id=index,source_accesses=8,source_PCs=9,source_CALLs=2,
                             host_guest_stores=0,parent_frame=P,heap_frame=P-8,API_frame=P-24,
                             State=3504,FX=512,RuntimeCPU=40,pages=17,checkpoints=27 if readers else None))
    for module in (M,M.M,M.M.M,M.M.M.M,M.D,M.R,M.N,M.D.E,M.F,M.C):
        add(module.__file__)
        for path,digest in getattr(module,'PINS',{}).items():
            add(path,digest)
    add(F.__file__)
    add(ROOT/'tools/m4-crt-locale-default-root/before.py','9776d1271e1076990f7f50d264eae54f88d332cb6b817197c444fb7db7ceb830')
    for path in out.iterdir():
        if path.is_file():
            add(path)
    if readers:
        for receipt in (execution,observer):
            for category in ('files','sources','source_files','tools','libraries','entry_objects','compiler_read_headers','artifacts','input_files'):
                for path,digest in receipt.get(category,{}).items():
                    add(path,digest)
        for receipt in (args.execution,args.observer):
            pins = Path(receipt).parent/'pins.json'
            if pins.exists():
                add(pins)
                for path,digest in read(pins)['files'].items():
                    add(path,digest)
        stage_path = add(args.stage,args.stage_sha)
        verified = verify_stage(stage_path.parent,args.stage_sha)
        need(verified['recorded_stage_passed'],'Final successful current native observer stage')
        final = dict(execution_sha256=args.execution_sha,observer_sha256=args.observer_sha,
                     stage_sha256=sha(stage_path),stage_verification=verified,
                     ordinary_current_native_rows_compared=native_count,
                     exact_unused_later_native_records_compared=unused_count,
                     native_executor=observer.get('native_executor'),independent_root_execution_credit=False)
    stack.close()
    report = dict(schema='mw34-m4-heap-init-root-audit-v1',passed=True,scope='Independent original-BEFORE source/affine audit of heap prefix model',
        source_report_sha256=SOURCE_SHA,rows=rows,model_comparisons=checks,ordinary_rows=48,
        full_frozen_mainargs_before_crosscheck=True,stopping_subclass_used_as_expected_seed=False,
        independent_affine_source_ledger=True,whole_State_bytes=3504,whole_FX_bytes=512,whole_Runtime_CPU_bytes=40,
        prior_mappings=17,additional_mappings=0,State_EIP_only_scheduler=True,host_guest_memory_stores=0,
        actual_source_PCs=9,actual_source_accesses=8,actual_source_CALLs=2,new_source_identity_bytes=84,
        current_native_checkpoints_per_row=27 if final else 0,
        source_checked_store_precedes_ESP_publication=True,source_IAT_read_precedes_CALL_return_store=True,
        declared_undefined_AF_representative=dict(pc=0x780039bf,value=0,universal_original_AF_equivalence=False),
        final_defined_arithmetic_flags=dict(pc=0x780039c3,CF=0,PF=0,AF=0,ZF=0,SF=0,OF=0),
        AFTER_machine_state_used_as_seed=False,permitted_API_witness='Declared FDIV input/API query record only',
        author_expected_model_imported=False,root_full_causal_model_audited=False,
        current_native_proof_bound=final is not None,final_root_proof=final,
        native_or_original_or_game_executed_by_this_audit=False,HeapCreate_executed=False,heap_initialized=False,
        original_GetVersion_or_attach_proved=False,locale_initialized=False,whole_M4_complete=False,
        source_commands=commands+heap_commands,initial_dependency_check=initial_check,
        final_dependency_check=verify_manifest(files),elapsed_seconds=(time.perf_counter_ns()-started)/1e9,
        files=dict(sorted(files.items())))
    report_path = out/'report.json'
    publish_bytes(report_path,(json.dumps(report,indent=2)+'\n').encode())
    add(report_path)
    publish_bytes(out/'pins.json',(json.dumps(dict(files=dict(sorted(files.items()))),indent=2)+'\n').encode())
    print(json.dumps(dict(passed=True,report_sha256=sha(report_path),pins_sha256=sha(out/'pins.json'),
                         rows=48,comparisons=checks,current_native_proof_bound=final is not None)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output',type=Path)
    parser.add_argument('--execution',type=Path)
    parser.add_argument('--execution-sha')
    parser.add_argument('--observer',type=Path)
    parser.add_argument('--observer-sha')
    parser.add_argument('--stage',type=Path)
    parser.add_argument('--stage-sha')
    main(parser.parse_args())
