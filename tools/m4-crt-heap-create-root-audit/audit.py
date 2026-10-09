"""Independent original-BEFORE affine audit; no native/API execution."""
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
BASE = ROOT/'reports/m4-crt-heap-create-root-audit'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path

SOURCE_SHA = '16e6d7f70c7b23747de90182e34f73471112108524d161b243db5603626a9f7c'
ACCEPT_SHA = 'a9a549d0acf1e8cd3a0015b4b7cdd2d61876ded33e0c69610c37bf9bc60b001d'
DRAFT_SHA = '885dc58b02688bfd9d34acf8bd5800937b191a926ecefbf7666986f99ef44dd4'
BEFORE_SHA = '58377061d16a0ac4d6085b3f41156b3af8042af4723b6e5c16488f0e112a33b1'
PREFIX_SHA = 'd571c81396b6e54aa2b37ffd56b41aa394d2aec77bb5277afd05b3d57f4b2fff'
ORIGINAL_SHA = 'cbcb423813a712851f63a4921b72544499e74488d24184a4f084a74ae14009b2'
TOKEN = 0x48450001
PAGE = 0x78035000
STATE_FLAGS = ((2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11))
ARITH_FLAGS = tuple(pair for pair in STATE_FLAGS if pair[1] != 10)


def need(value,why):
    if not value:
        raise ValueError(why)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes(),object_pairs_hook=unique_object)


def load(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(args):
    started = time.perf_counter_ns()
    out = workspace_path(args.output,reports=True)
    need(out.parent == BASE and not out.exists(),'Fresh immediate private audit output')
    files = {}

    def add(path,digest=None):
        path = Path(path).absolute()
        key,value = normalized(str(path)),sha(path) if digest is None else digest
        need(sha(path) == value and (key not in files or files[key] == value),'Exact unique physical dependency '+str(path))
        files[key] = value
        return path

    source_path = add(ROOT/'reports/m4-crt-heap-create-recovery/recovery-r1/report.json',SOURCE_SHA)
    source = read(source_path)
    need(source['passed'] and source['API_executed'] is False,'Fresh frozen static source identity only')
    source_pins = add(source_path.parent/'pins.json')
    for path,digest in read(source_pins)['files'].items():
        add(path,digest)
    draft_path = add(ROOT/'reports/m4-crt-heap-create-root/draft-r4/report.json',DRAFT_SHA)
    draft = read(draft_path)
    need(draft['passed'] and draft['ordinary_BEFORE_models'] == 48 and not draft['current_native_compared']
         and not draft['HeapCreate_executed'],'Explicit draft scope, no current native/API credit')
    core = ROOT/'tools/m4-crt-heap-create-root'
    excluded_draft_context = []
    for path,digest in draft['files'].items():
        physical = Path(path)
        if physical.parent == core and physical.name in ('observe.py','ownership.py','positive.py'):
            excluded_draft_context.append(dict(path=path,recorded_historical_sha256=digest,
                imported_as_model=False,current_identity_claimed=False))
        else:
            add(path,digest)
    accepted_path = add(ROOT/'reports/m4-crt-heap-init-root/root-acceptance-r1/report.json',ACCEPT_SHA)
    accepted = read(accepted_path)
    need(accepted['passed'],'Exact accepted prior frontier')
    previous_identity = accepted['receipts']['author_execution']
    previous_execution = read(add(previous_identity['path'],previous_identity['sha256']))
    add(core/'before.py',BEFORE_SHA)
    add(core/'prefix.py',PREFIX_SHA)
    for path in (Path(__file__),Path(__file__).with_name('README.md'),Path(sys.executable),
                 core/'consumer.py',core/'draft.py',ROOT/'tools/m4-pipeline/manifests.py',
                 ROOT/'tools/m4-pipeline/paths.py',ROOT/'tools/m4-pipeline/capture_bundle.py'):
        add(path)
    original_path = add(ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin',ORIGINAL_SHA)
    refusal = BASE/'refusal-r1'
    for path,digest in read(refusal/'pins.json')['files'].items():
        add(path,digest)
    add(refusal/'pins.json')
    initial_check = verify_manifest(files)
    out.mkdir(parents=True)
    previous = {name:sys.modules.get(name) for name in ('consumer','before')}
    consumer = load('heap_create_independent_consumer',core/'consumer.py')
    sys.modules['consumer'] = consumer
    try:
        before = load('heap_create_independent_before',core/'before.py')
        sys.modules['before'] = before
        prefix = load('heap_create_independent_prefix',core/'prefix.py')
    finally:
        for name,value in previous.items():
            if value is None:
                sys.modules.pop(name,None)
            else:
                sys.modules[name] = value
    F,M,OLD = consumer.F,consumer.M,consumer.OLD
    need(tuple(M.F.FLAGS) == STATE_FLAGS,'Exact inherited State flag offsets')
    program,providers,maths,ctrl,init,mainargs,argv,pages,commands = M.source_material(out)
    wp,pp,gp = M.R.source_material()
    heap_program,root_pages,heap_commands = prefix.source_material(out)
    provider = M.N.PE.PEImage((ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes())
    raw_code,raw_heap = M.D.mapped(provider,0x78003000),M.D.mapped(provider,PAGE)
    need(root_pages == {0x78003000:raw_code,PAGE:raw_heap},'Fresh exact complete source and RW page mapping')
    need(hashlib.sha256(raw_heap).hexdigest() == source['data']['heap-page-file-identity']['sha256'],
         'Independent source raw page hash')
    pages.update({0x78003000:raw_code,PAGE:raw_heap})
    for label in ('attach-fragment','heap-initializer'):
        for instruction in source['spans'][label]['instructions']:
            size,op,operands = heap_program[instruction['pc']]
            need(size == len(bytes.fromhex(instruction['bytes_hex'])) and op == instruction['mnemonic']
                 and ' '.join(', '.join(operands).split()) == ' '.join(instruction['operands'].split()),
                 'Fresh complete actual source instruction decode')

    def stage(state,fx,cpu,memory):
        value = OLD.stage(state,fx,cpu,memory)
        for name,address,start,end in (
            ('page-2013278208.bin',0x78003000,0,4096),
            ('page-'+str(PAGE)+'.bin',PAGE,0,4096),
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
        result[0x78003000] = bytearray(raw_code)
        result[PAGE] = bytearray(raw_heap)
        return result

    frozen_writer = types.FunctionType(F.writer.__code__,dict(F.writer.__globals__,base_memory=memory,stage=stage))
    frozen_full = types.FunctionType(OLD.expected.__code__,dict(OLD.expected.__globals__,writer_result=frozen_writer,stage=stage))
    payloads = [M.R.project(row) for row in M.R.originals(original_path.read_bytes())[:24]]
    checks,ordinary_rows,token_controls = 0,[],[]

    def eq(actual,expected,why):
        nonlocal checks
        checks += 1
        need(actual == expected,why)

    def affine(initial,fx,cpu,initial_memory,token):
        mem = copy.deepcopy(initial_memory)
        P = struct.unpack_from('<I',initial,consumer.STATE_REG['esp'])[0]
        need(P == 0x20001860 and struct.unpack_from('<I',cpu,16)[0] == P
             and struct.unpack_from('<I',cpu,36)[0] == M.SLOT,'Authentic inherited mainargs parent frame/site')
        need(struct.unpack_from('<I',initial,2120)[0] == 0 and struct.unpack_from('<I',initial,2184)[0] == 0,
             'Independent flat source SS/DS bases')
        current = bytearray(initial)
        stages = {'heap-create-before':stage(current,fx,cpu,mem)}
        struct.pack_into('<I',current,2472,0x7800183c)
        stages['heap-create-projected'] = stage(current,fx,cpu,mem)
        ledger = []
        for access in source['carried_prefix_source_accesses']:
            expr = access['address_expression']
            address = P-int(expr[2:]) if expr.startswith('P-') else int(expr,0)
            value = access['value']
            if access['write']:
                need(0x20001000 <= address <= 0x20001ffc,'Exact owned source stack store')
                struct.pack_into('<I',mem[0x20001000],address&4095,value)
            else:
                eq(struct.unpack_from('<I',mem[address&~4095],address&4095)[0],value,'Ordered original source operand read')
            ledger.append((access['pc'],address,value,4,int(access['write'])))
            if len(ledger) == 2:
                struct.pack_into('<I',current,consumer.STATE_REG['esp'],P-8)
                struct.pack_into('<I',current,2472,0x780039bf)
                stages['heap-create-provider-before'] = stage(current,fx,cpu,mem)
        struct.pack_into('<I',current,consumer.STATE_REG['eax'],0)
        struct.pack_into('<I',current,consumer.STATE_REG['esp'],P-24)
        struct.pack_into('<I',current,2472,0x3461e)
        for offset,bit in ARITH_FLAGS:
            current[offset] = 0
        stages['heap-create-api-before'] = stage(current,fx,cpu,mem)
        stages['heap-create-api-return-before'] = stage(current,fx,cpu,mem)
        # Checked API return has one read and no guest-memory store. Its finite
        # declared effect is low EAX/ESP/EIP only; original API internals unrun.
        return_word = struct.unpack_from('<I',mem[0x20001000],(P-24)&4095)[0]
        eq(return_word,0x780039d6,'Independent checked original stdcall return word')
        return_access = (0x780039d0,P-24,return_word,4,0)
        struct.pack_into('<I',current,consumer.STATE_REG['eax'],token)
        struct.pack_into('<I',current,consumer.STATE_REG['esp'],P-8)
        struct.pack_into('<I',current,2472,return_word)
        stages['heap-create-api-returned'] = stage(current,fx,cpu,mem)
        values = {0:0,2:int((token&255).bit_count()%2 == 0),4:0,6:0,7:(token>>31)&1,11:0}
        for offset,bit in ARITH_FLAGS:
            current[offset] = values[bit]
        struct.pack_into('<I',current,2472,0x780039d8)
        struct.pack_into('<I',mem[PAGE],0,token)
        ledger.append((0x780039d8,PAGE,token,4,1))
        stages['heap-create-published'] = stage(current,fx,cpu,mem)
        # Genuine CALL stores return first and only then publishes ESP/EIP.
        struct.pack_into('<I',mem[0x20001000],(P-12)&4095,0x780039e8)
        ledger.append((0x780039e3,P-12,0x780039e8,4,1))
        struct.pack_into('<I',current,consumer.STATE_REG['esp'],P-12)
        struct.pack_into('<I',current,2472,0x78003a0c)
        stages['heap-create-mode-before'] = stage(current,fx,cpu,mem)
        stages['heap-create-after'] = stage(current,fx,cpu,mem)
        return dict(state=bytes(current),memory=mem,phases=stages,ledger=ledger,API_return_access=return_access,
            scheduler=(1,struct.unpack_from('<I',initial,2472)[0],P,0x7800183c,P,0,M.SLOT,P),
            routes=[(0x7800183e,0x780039bf,0x78001843),(0x780039d0,0x3461e,0x780039d6),
                    (0x780039e3,0x78003a0c,0x780039e8)])

    def compare(entry,seam,token):
        result = prefix.predict(entry,heap_program,token)
        expected = affine(seam[0],seam[3],seam[1],seam[2],token)
        eq(set(result['phases']),set(expected['phases']),'Exact independently derived nine-phase schema')
        for tag,values in expected['phases'].items():
            eq(result['phases'][tag],values,'Whole State/FX/CPU18page/source identity phase '+tag)
            eq(len([name for name in values if name.startswith('page-')]),18,'Exactly18 captured mappings, semantic aliases retained')
        eq(bytes(result['state']),expected['state'],'Whole source-terminal3504State')
        eq(result['memory'],expected['memory'],'All carried pages and semantic aliases')
        eq(result['fx'],seam[3],'Whole512FX carried')
        eq(result['cpu'],seam[1],'Whole40 generic RuntimeCPU carried')
        eq(result['accesses'],expected['ledger'],'Exact ordered ten original-source accesses')
        eq(result['API_return_access'],expected['API_return_access'],'Separate checked API-return read')
        eq(result['PCs'],source['success_contract']['all_original_source_PCs'],'All thirteen original source PCs')
        eq(result['routes'],expected['routes'],'All three genuine source CALL routes')
        eq(result['scheduler'],expected['scheduler'],'EIP-only schedule; zero host guest execution stores')
        eq(result['undefined'],[(0x780039bf,0),(0x780039d6,0)],'Only two declared source-qualified AF representatives')
        raw_changed = bytearray(raw_heap)
        struct.pack_into('<I',raw_changed,0,token)
        eq(result['memory'][PAGE],raw_changed,'Only genuine source handle DWORD changes in raw RW page')
        need(not result['heap_initialized'] and result['mode_frame'] == 0x20001854
             and result['fault_PC'] == 0x780039e3 and result['fault_address'] == 0x78003a0c,
             'Unrun selector boundary, no mode or initializer completion')
        return expected

    with contextlib.ExitStack() as stack:
        readers = {}
        for level in ('O0','O2'):
            identity = previous_execution['levels'][level]
            add(identity['bundle'],identity['bundle_sha256'])
            reader = stack.enter_context(CaptureBundle(identity['bundle'],identity['bundle_sha256']))
            need(len(reader.names()) == identity['logical_files'] and reader.read_bytes('COMPLETE') == b'COMPLETE',
                 'Complete hash-bound prior native archive; only BEFORE input/query bytes seed this audit')
            readers[level] = reader
        for level in ('O0','O2'):
            reader = readers[level]
            for index,payload in enumerate(payloads):
                row = F.LogicalPath(reader,'row-'+str(index))
                entry,earlier = before.expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,mainargs,argv,pages,level)
                full,full_phases = frozen_full(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,mainargs,argv,pages,0,level)
                seam = full.args_phases['mainargs-before']
                eq(bytes(entry.state),seam[0],'Whole full-source healthy before-State3504')
                eq(bytes(entry.fx),seam[3],'Whole full-source healthy before-FX512')
                eq(bytes(entry.runtime_cpu),seam[1],'Whole full-source healthy before-CPU40')
                eq(entry.mem,seam[2],'All full-source healthy before-memory bytes including aliases')
                need(entry.init_complete and not entry.init_failed and not entry.args_failed and not entry.args_used
                     and entry.args_accesses == [],'Healthy seam before argument-provider admission')
                eq(len(earlier),20,'Exactly20 carried prior phases')
                for tag,value in earlier.items():
                    eq(value,full_phases[tag],'Every complete prior source-model phase '+tag)
                derived = compare(entry,seam,TOKEN)
                ordinary_rows.append(dict(level=level,index=index,token=TOKEN,source_PCs=13,source_accesses=10,
                    source_CALLs=3,separate_API_return_reads=1,State=3504,FX=512,RuntimeCPU=40,mappings=18,
                    prior_phases=20,new_phases=9,anticipated_native_phases=31,mode_frame=0x20001854,
                    host_guest_execution_stores=0,current_native_compared=False))
                if index == 0:
                    for token in (1,2,0x80,0x80000000,0xffffffff):
                        compare(entry,seam,token)
                        token_controls.append(dict(level=level,token=token,SF=(token>>31)&1,
                            PF=int((token&255).bit_count()%2 == 0),scope='Static hypothetical token formula; no API result'))
    for path,digest in F.PHYSICAL.items():
        add(path,digest)
    for module in (M,M.M,M.M.M,M.M.M.M,M.D,M.R,M.N,M.D.E,M.F,M.C):
        add(module.__file__)
        for path,digest in getattr(module,'PINS',{}).items():
            add(path,digest)
    add(F.__file__)
    for path in out.iterdir():
        if path.is_file():
            add(path)
    report = dict(schema='mw34-m4-heap-create-root-model-audit-v1',passed=True,
        scope='Independent full-original-BEFORE and affine-source audit of draft HeapCreate continuation model; no current native/API proof',
        source_report_sha256=SOURCE_SHA,root_draft_sha256=DRAFT_SHA,root_before_sha256=BEFORE_SHA,root_prefix_sha256=PREFIX_SHA,
        unimported_historical_root_draft_context=excluded_draft_context,
        root_draft_all_dependency_closure_claimed=False,root_model_dependency_closure_verified=True,
        ordinary_rows=48,rows=ordinary_rows,model_comparisons=checks,static_token_formula_controls=token_controls,
        full_frozen_mainargs_before_crosscheck=True,stopping_subclass_used_as_expected_seed=False,
        AFTER_machine_state_used_as_seed=False,permitted_API_witness='Declared original FDIV input/API-query record only',
        author_expected_model_imported=False,independent_affine_source_ledger=True,
        whole_State_bytes=3504,whole_FX_bytes=512,whole_Runtime_CPU_bytes=40,captured_mappings=18,
        prior_mappings_preserved=17,new_raw_RW_page=PAGE,new_raw_RW_page_sha256=hashlib.sha256(raw_heap).hexdigest(),
        semantic_memory_aliases_preserved=True,semantic_aliases_counted_as_extra_mappings=False,
        actual_source_PCs=13,actual_source_accesses=10,actual_source_CALLs=3,separate_API_return_reads=1,
        separate_API_return_log_context_PC=0x780039d0,separate_API_return_incoming_State_EIP=0x3461e,
        source_identity_compiled_guarded_bytes=84,source_identity_executed_bytes=48,
        host_scheduler_changes_only=['State.EIP'],host_guest_execution_stores=0,
        declared_API_return_changes_only=['State.EAX.low32','State.ESP.low32','State.EIP.low32'],
        generic_Runtime_CPU_and_call_records_preserved=True,original_x86_API_internals_equivalence=False,
        original_volatile_register_or_flag_equivalence=False,declared_token=TOKEN,
        root_predicted_API_executed_flag_is_draft_hypothesis=True,
        handle_publication_phase_PC=0x780039d8,publication_snapshot_at_source_write_before_PC_advance=True,
        raw_heap_page_only_source_handle_DWORD_changed=True,source_CALL_store_precedes_ESP_publication=True,
        source_IAT_read_precedes_API_CALL_return_store=True,source_return_bridge_read_precedes_State_publication=True,
        declared_AF_representatives=[dict(pc=0x780039bf,value=0),dict(pc=0x780039d6,value=0)],
        undefined_AF_universal_original_equivalence=False,
        new_phase_names=list(derived['phases']),anticipated_native_checkpoints_per_row=31,
        current_native_proof_bound=False,current_native_compared=False,
        native_or_original_or_game_executed_by_this_audit=False,HeapCreate_executed=False,
        host_handle_created=False,heap_initialized=False,mode_selected=False,source_initializer_RET_executed=False,
        original_attach_proved=False,root_full_causal_model_audited=False,whole_M4_complete=False,
        source_commands=commands+heap_commands,initial_dependency_check=initial_check,
        final_dependency_check=verify_manifest(files),elapsed_seconds=(time.perf_counter_ns()-started)/1e9,
        files=dict(sorted(files.items())))
    report_path = out/'report.json'
    publish_bytes(report_path,(json.dumps(report,indent=2)+'\n').encode())
    add(report_path)
    publish_bytes(out/'pins.json',(json.dumps(dict(files=dict(sorted(files.items()))),indent=2)+'\n').encode())
    print(json.dumps(dict(passed=True,report_sha256=sha(report_path),pins_sha256=sha(out/'pins.json'),
        rows=48,comparisons=checks,current_native_proof_bound=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output',type=Path)
    main(parser.parse_args())
