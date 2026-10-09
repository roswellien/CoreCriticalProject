"""Independent full-startup BEFORE and affine selector/probe root-model audit."""
import contextlib
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import sys
import time
import types
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
BASE = ROOT/'reports/m4-crt-heap-mode-root-audit'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path

SOURCE_SHA = '135ad3a9d2b24635d3f2547aa6904fef968daab02ae230302d1e3812914cd74c'
SOURCE_PINS_SHA = '02ea38025b52d4502a7e082744ee1c044ad4267d7d745c22fd5e55283a4fe312'
ACCEPT_SHA = 'e40df22e7b6263f75d9215cdaeadeb6a30030a4b07008c58442d8512d10c4326'
DRAFT_SHA = 'c950916e1ced732e0035bd5a9adc40dc9c2a4142059d9f15ba20f094b159c642'
BEFORE_SHA = 'f42551f20b4365f663fd22b3d85cb1ae88771b52ac71391ebdacdd55edc221fa'
PREFIX_SHA = '95dd875e421a98c2a286e2cc528c279f97829a045ccb8afc53c0dce59e29d9f1'
ORIGINAL_SHA = 'cbcb423813a712851f63a4921b72544499e74488d24184a4f084a74ae14009b2'
TOKEN,PAGE,PROBE_PAGE,STACK_PAGE = 0x48450001,0x78035000,0x78005000,0x20000000
FLAGS = ((2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11))


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


def main(name):
    started = time.perf_counter_ns()
    need(re.fullmatch(r'draft-r[1-9][0-9]*',name),'Fresh draft audit name')
    out = workspace_path(BASE/name,reports=True)
    need(out.parent == BASE and not out.exists(),'Fresh private output')
    files = {}

    def add(path,digest=None):
        path = Path(path).absolute()
        key,value = normalized(str(path)),sha(path) if digest is None else digest
        need(sha(path) == value and (key not in files or files[key] == value),'Exact unique physical dependency')
        files[key] = value
        return path

    source_path = add(ROOT/'reports/m4-crt-heap-mode-recovery/recovery-r1/report.json',SOURCE_SHA)
    source_pins = add(source_path.with_name('pins.json'),SOURCE_PINS_SHA)
    source = read(source_path)
    need(source['passed'] and source['schema'] == 'mw34-m4-heap-mode-static-recovery-v1','Exact sealed source contract')
    for path,digest in read(source_pins)['files'].items():
        add(path,digest)
    accept_path = add(ROOT/'reports/m4-crt-heap-create-root/root-acceptance-r1/report.json',ACCEPT_SHA)
    accepted = read(accept_path)
    need(accepted['passed'],'Previous accepted native HeapCreate frontier')
    identity = accepted['receipts']['author_execution']
    previous_execution = read(add(identity['path'],identity['sha256']))
    draft_path = add(ROOT/'reports/m4-crt-heap-mode-root/draft-r1/report.json',DRAFT_SHA)
    draft = read(draft_path)
    need(draft['passed'] and draft['ordinary_BEFORE_models']==48 and not draft['native_executed'],
         'Fresh source-only root draft')
    for path,digest in draft['files'].items():
        add(path,digest)
    core = ROOT/'tools/m4-crt-heap-mode-root'
    add(core/'before.py',BEFORE_SHA)
    add(core/'prefix.py',PREFIX_SHA)
    for path in (Path(__file__),Path(__file__).with_name('README.md'),Path(sys.executable),
                 core/'consumer.py',core/'draft.py',ROOT/'tools/m4-pipeline/manifests.py',
                 ROOT/'tools/m4-pipeline/paths.py',ROOT/'tools/m4-pipeline/capture_bundle.py'):
        add(path)
    original_path = add(ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin',ORIGINAL_SHA)
    initial = verify_manifest(files)
    out.mkdir(parents=True)
    previous_modules = {name:sys.modules.get(name) for name in ('consumer','before')}
    consumer = load('heap_mode_audit_consumer',core/'consumer.py')
    sys.modules['consumer'] = consumer
    try:
        before = load('heap_mode_audit_before',core/'before.py')
        sys.modules['before'] = before
        prefix = load('heap_mode_audit_prefix',core/'prefix.py')
    finally:
        for name,value in previous_modules.items():
            if value is None:
                sys.modules.pop(name,None)
            else:
                sys.modules[name] = value
    F,M,OLD,REG = consumer.F,consumer.M,consumer.OLD,consumer.STATE_REG
    need(tuple(M.F.FLAGS) == FLAGS,'Exact State flag offsets')
    program,providers,maths,ctrl,init,mainargs,argv,pages,commands = M.source_material(out)
    wp,pp,gp = M.R.source_material()
    heap_program,source_pages,heap_commands = prefix.source_material(out)
    provider = M.N.PE.PEImage((ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes())
    raw_code,raw_heap,raw_probe = (M.D.mapped(provider,address) for address in (0x78003000,PAGE,PROBE_PAGE))
    need(source_pages == {0x78003000:raw_code,PAGE:raw_heap,PROBE_PAGE:raw_probe},'Three exact raw source pages')
    need(hashlib.sha256(raw_probe).hexdigest() == source['data']['stack-probe-page']['sha256'],'Fresh RX probe page identity')
    pages.update(source_pages)
    for label in ('heap-fragment','heap-provider','selector-prefix','stack-probe'):
        for instruction in source['spans'][label]['instructions']:
            size,op,args = heap_program[instruction['pc']]
            need(size == instruction['width'] and op == instruction['mnemonic'] and
                 ' '.join(', '.join(args).split()) == ' '.join(instruction['operands'].split()),
                 'Every actual full source instruction/width matches independent receipt')

    def stage(state,fx,cpu,memory):
        result = OLD.stage(state,fx,cpu,memory)
        for address in (0x78003000,PAGE,PROBE_PAGE,STACK_PAGE):
            result['page-'+str(address)+'.bin'] = bytes(memory[address])
        for label,address,lo,hi in (
            ('commandline-source.bin',0x78001000,0x88c,0x897),
            ('parser-source.bin',0x7800b000,0xc48,0xdfc),
            ('locale-stub.bin',0x78003000,0xdd2,0xddb),
            ('locale-setmbcp.bin',0x78003000,0xddb,0xe84),
            ('locale-lock.bin',0x78001000,0x55,0xb0),
            ('heap-fragment.bin',0x78001000,0x83c,0x843),
            ('heap-provider.bin',0x78003000,0x9bf,0xa0c),
            ('heap-mode-selector.bin',0x78003000,0xa0c,0xa31),
            ('heap-stack-probe.bin',PROBE_PAGE,0x8b5,0x8e6)):
            result[label] = bytes(memory[address][lo:hi])
        return result

    def full_model(stack_input):
        def memory(*values):
            result = OLD.base_memory(*values)
            for address,raw in source_pages.items():
                result[address] = bytearray(raw)
            result[STACK_PAGE] = bytearray(stack_input)
            return result
        writer = types.FunctionType(F.writer.__code__,dict(F.writer.__globals__,base_memory=memory,stage=stage))
        return types.FunctionType(OLD.expected.__code__,dict(OLD.expected.__globals__,writer_result=writer,stage=stage))

    checks,rows,controls = 0,[],[]

    def eq(actual,expected,why):
        nonlocal checks
        checks += 1
        need(actual == expected,why)

    def affine(seam):
        initial,cpu,initial_memory,fx = seam
        memory = copy.deepcopy(initial_memory)
        current = bytearray(initial)
        P = struct.unpack_from('<I',initial,REG['esp'])[0]
        need(P == 0x20001860 and struct.unpack_from('<I',cpu,16)[0] == P and
             struct.unpack_from('<I',cpu,36)[0] == M.SLOT,'Original mainargs parent frame and call site')
        need(struct.unpack_from('<I',initial,2120)[0] == 0 and struct.unpack_from('<I',initial,2184)[0] == 0,
             'Carried flat SS/DS bases')
        phases = {'heap-create-before':stage(current,fx,cpu,memory)}
        struct.pack_into('<I',current,2472,0x7800183c)
        phases['heap-create-projected'] = stage(current,fx,cpu,memory)
        ledger = []

        def store(pc,address,value):
            struct.pack_into('<I',memory[address&~4095],address&4095,value)
            ledger.append((pc,address,value,4,1))

        def fetch(pc,address,wanted=None):
            value = struct.unpack_from('<I',memory[address&~4095],address&4095)[0]
            if wanted is not None:
                eq(value,wanted,'Independent source-ordered operand read')
            ledger.append((pc,address,value,4,0))
            return value

        def setreg(name,value):
            struct.pack_into('<I',current,REG[name],value&0xffffffff)

        def setpc(value):
            struct.pack_into('<I',current,2472,value)

        def flags(**values):
            for offset,bit in FLAGS:
                name = {0:'CF',2:'PF',4:'AF',6:'ZF',7:'SF',10:'DF',11:'OF'}[bit]
                if name in values:
                    current[offset] = values[name]

        for access in source['carried_source_access_ledger'][:8]:
            expr = access['address_expression']
            address = P-int(expr[2:]) if expr.startswith('P-') else int(expr,0)
            if access['write']:
                store(access['pc'],address,access['value'])
            else:
                fetch(access['pc'],address,access['value'])
            if len(ledger) == 2:
                setreg('esp',P-8)
                setpc(0x780039bf)
                phases['heap-create-provider-before'] = stage(current,fx,cpu,memory)
        setreg('eax',0)
        setreg('esp',P-24)
        setpc(0x3461e)
        flags(CF=0,PF=0,AF=0,ZF=0,SF=0,OF=0)
        phases['heap-create-api-before'] = stage(current,fx,cpu,memory)
        phases['heap-create-api-return-before'] = stage(current,fx,cpu,memory)
        returned = struct.unpack_from('<I',memory[0x20001000],(P-24)&4095)[0]
        eq(returned,0x780039d6,'Distinct checked API ABI return word')
        API_return_access = (0x780039d0,P-24,returned,4,0)
        setreg('eax',TOKEN)
        setreg('esp',P-8)
        setpc(returned)
        phases['heap-create-api-returned'] = stage(current,fx,cpu,memory)
        flags(CF=0,PF=0,AF=0,ZF=0,SF=0,OF=0)
        setpc(0x780039d8)
        store(0x780039d8,PAGE,TOKEN)
        phases['heap-create-published'] = stage(current,fx,cpu,memory)
        store(0x780039e3,P-12,0x780039e8)
        setreg('esp',P-12)
        setpc(0x78003a0c)
        phases['heap-create-mode-before'] = stage(current,fx,cpu,memory)
        EBP0,ECX0,EBX0 = (struct.unpack_from('<I',initial,REG[name])[0] for name in ('ebp','ecx','ebx'))
        # Explicit affine source effects; no root opcode interpreter reused.
        store(0x78003a0c,P-16,EBP0)
        setreg('esp',P-16)
        setreg('ebp',P-16)
        setreg('eax',0x122c)
        store(0x78003a14,P-20,0x78003a19)
        setreg('esp',P-20)
        setpc(0x780058b5)
        phases['heap-mode-probe-before'] = stage(current,fx,cpu,memory)
        store(0x780058b5,P-24,ECX0)
        setreg('esp',P-24)
        setreg('ecx',P-16)
        setreg('ecx',P-16-0x1000)
        setreg('eax',0x22c)
        A = fetch(0x780058db,P-16-0x1000)
        eq(P-16-0x1000,0x20000850,'First probe affine address')
        # CMP22C,1000 and SUBECX,22C precede final TEST. Intermediate
        # arithmetic constants are authenticated by the sealed source receipt.
        setreg('ecx',P-16-0x122c)
        setreg('eax',P-24)
        B = fetch(0x780058c5,P-16-0x122c)
        tested = B&(P-24)
        flags(CF=0,PF=int((tested&255).bit_count()%2 == 0),AF=0,ZF=int(tested == 0),SF=tested>>31,OF=0)
        setreg('esp',P-16-0x122c)
        setreg('ecx',fetch(0x780058c9,P-24,ECX0))
        setreg('eax',fetch(0x780058cb,P-20,0x78003a19))
        store(0x780058ce,P-20-0x122c,0x78003a19)
        setreg('esp',P-20-0x122c)
        target = fetch(0x780058cf,P-20-0x122c,0x78003a19)
        setreg('esp',P-16-0x122c)
        setpc(target)
        phases['heap-mode-probe-after'] = stage(current,fx,cpu,memory)
        setreg('eax',P-16-0x98)
        store(0x78003a1f,P-20-0x122c,EBX0)
        setreg('esp',P-20-0x122c)
        store(0x78003a20,P-24-0x122c,P-16-0x98)
        setreg('esp',P-24-0x122c)
        store(0x78003a21,P-16-0x98,148)
        fetch(0x78003a2b,0x7802e0a0,0x34600)
        store(0x78003a2b,P-28-0x122c,0x78003a31)
        setreg('esp',P-28-0x122c)
        setpc(0x34600)
        phases['heap-mode-query-before'] = stage(current,fx,cpu,memory)
        phases['heap-create-after'] = stage(current,fx,cpu,memory)
        need(len(ledger) == 24 and len(phases) == 12,'Independent24access12phase affine closure')
        return dict(state=bytes(current),memory=memory,phases=phases,ledger=ledger,
            API_return_access=API_return_access,probe_return_access=(0x780058cf,0x20000620,0x78003a19,4,0),
            scheduler=(1,struct.unpack_from('<I',initial,2472)[0],P,0x7800183c,P,0,M.SLOT,P),
            routes=[(0x7800183e,0x780039bf,0x78001843),(0x780039d0,0x3461e,0x780039d6),
                    (0x780039e3,0x78003a0c,0x780039e8),(0x78003a14,0x780058b5,0x78003a19),
                    (0x78003a2b,0x34600,0x78003a31)],declared_A=A,declared_B=B)

    def compare(entry,seam):
        actual = prefix.predict(entry,heap_program,TOKEN)
        expected = affine(seam)
        eq(set(actual['phases']),set(expected['phases']),'Complete independent twelve-phase schema')
        for tag,value in expected['phases'].items():
            eq(actual['phases'][tag],value,'Whole State/FX/CPU20page/source phase '+tag)
            eq(len([name for name in value if name.startswith('page-')]),20,'Exactly20 mappings, excluding aliases')
        eq(bytes(actual['state']),expected['state'],'Full3504State terminal source effects')
        eq(actual['memory'],expected['memory'],'All20pages and semantic aliases')
        eq(actual['fx'],seam[3],'Whole512FX carried')
        eq(actual['cpu'],seam[1],'Whole40RuntimeCPU carried')
        eq(actual['accesses'],expected['ledger'],'All24 ordered genuine source accesses')
        eq(actual['API_return_access'],expected['API_return_access'],'Separate old API return read')
        eq(actual['probe_return_access'],expected['probe_return_access'],'Genuine relocated source RET access')
        eq(actual['PCs'],source['all_source_PCs'],'Exact39 source PCs and dynamic probe branch path')
        eq(actual['routes'],expected['routes'],'Five actual source CALL routes')
        eq(actual['scheduler'],expected['scheduler'],'EIP-only old scheduler, zero guest execution stores')
        eq(actual['undefined'],[(0x780039bf,0),(0x780039d6,0),(0x780058db,0),(0x780058c5,0)],
           'Only four exact-PC AF representatives')
        eq(actual['memory'][PROBE_PAGE],raw_probe,'Original RX probe page unmodified')
        eq({k:v for k,v in actual['memory'].items() if k not in (0x20001000,STACK_PAGE,PAGE)},
           {k:v for k,v in seam[2].items() if k not in (0x20001000,STACK_PAGE,PAGE)},
           'All unrelated pages and TIB/StackLimit semantic bytes preserved')
        raw_changed = bytearray(raw_heap)
        struct.pack_into('<I',raw_changed,0,TOKEN)
        eq(actual['memory'][PAGE],raw_changed,'Only source handle DWORD changes; mode remains unproduced')
        need(actual['terminal_EIP'] == 0x34600 and actual['terminal_ESP'] == 0x20000618 and
             actual['stack_probe_returned'] and not actual['query_executed'] and not actual['mode_selected'] and
             not actual['initializer_RET'] and not actual['heap_initialized'],'Exact unrun API terminal frontier')
        return expected

    payloads = [M.R.project(value) for value in M.R.originals(original_path.read_bytes())[:24]]
    with contextlib.ExitStack() as stack:
        readers = {}
        for level in ('O0','O2'):
            identity = previous_execution['levels'][level]
            add(identity['bundle'],identity['bundle_sha256'])
            reader = stack.enter_context(CaptureBundle(identity['bundle'],identity['bundle_sha256']))
            need(len(reader.names()) == identity['logical_files'] and reader.read_bytes('COMPLETE') == b'COMPLETE',
                 'Strict complete prior bundle; original BEFORE inputs only')
            readers[level] = reader
        for level in ('O0','O2'):
            for index,payload in enumerate(payloads):
                row = F.LogicalPath(readers[level],'row-'+str(index))
                entry,earlier = before.expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,init,mainargs,argv,pages,level)
                full,full_phases = full_model(bytes(4096))(row,payload,wp,pp,gp,program,providers,maths,ctrl,
                    init,mainargs,argv,pages,0,level)
                seam = full.args_phases['mainargs-before']
                for actual,wanted,why in ((bytes(entry.state),seam[0],'Full startup healthy3504State'),
                    (bytes(entry.fx),seam[3],'Full startup healthy512FX'),
                    (bytes(entry.runtime_cpu),seam[1],'Full startup healthy40RuntimeCPU'),
                    (entry.mem,seam[2],'Full startup all20pages/aliases')):
                    eq(actual,wanted,why)
                need(entry.init_complete and not entry.init_failed and not entry.args_failed and not entry.args_used and
                     entry.args_accesses == [],'Healthy original seam before mainargs provider')
                eq(len(earlier),20,'Twenty preserved prior source phases')
                for tag,value in earlier.items():
                    eq(value,full_phases[tag],'Full original model prior phase '+tag)
                derived = compare(entry,seam)
                rows.append(dict(level=level,index=index,source_PCs=39,source_accesses=24,source_CALLs=5,
                    genuine_probe_RET=1,separate_API_return_reads=1,State=3504,FX=512,RuntimeCPU=40,mappings=20,
                    prior_phases=20,new_phases=12,anticipated_native_phases=34,
                    declared_A=derived['declared_A'],declared_B=derived['declared_B'],current_native_compared=False))
                if index == 0:
                    for value in (0,0xffffffff,8,0x40,0x1848,0x80000000):
                        stack_input = struct.pack('<I',value)*1024
                        alternate,_ = before.expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,
                            init,mainargs,argv,pages,level,stack_input)
                        complete,_ = full_model(stack_input)(row,payload,wp,pp,gp,program,providers,maths,ctrl,
                            init,mainargs,argv,pages,0,level)
                        other_seam = complete.args_phases['mainargs-before']
                        eq(bytes(alternate.state),other_seam[0],'Directed full-startup BEFORE State')
                        eq(alternate.mem,other_seam[2],'Directed explicit owned input full memory')
                        control = compare(alternate,other_seam)
                        controls.append(dict(level=level,initial_lower_page_DWORD=value,A=control['declared_A'],
                            B=control['declared_B'],native_executed=False,original_lower_stack_captured=False))
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
    report = dict(schema='mw34-m4-heap-mode-root-model-audit-v1',passed=True,
        scope='Independent full-original-BEFORE/affine selector and probe audit of source-only root draft',
        source_report_sha256=SOURCE_SHA,source_pins_sha256=SOURCE_PINS_SHA,root_draft_sha256=DRAFT_SHA,
        root_before_sha256=BEFORE_SHA,root_prefix_sha256=PREFIX_SHA,ordinary_rows=48,rows=rows,
        model_comparisons=checks,static_declared_stack_formula_controls=controls,
        full_frozen_mainargs_before_crosscheck=True,stopping_subclass_used_as_expected_seed=False,
        AFTER_machine_state_used_as_seed=False,permitted_original_API_witness='Original FDIV input/API-query only',
        author_expected_model_imported=False,independent_affine_source_ledger=True,
        whole_State_bytes=3504,whole_FX_bytes=512,whole_Runtime_CPU_bytes=40,captured_mappings=20,
        prior_mappings_preserved=18,new_owned_lower_stack_page=STACK_PAGE,new_raw_RX_probe_page=PROBE_PAGE,
        new_raw_RX_probe_page_sha256=hashlib.sha256(raw_probe).hexdigest(),
        lower_stack_bytes_original_observed=False,original_stack_guard_growth_proved=False,
        TIB_and_Policy_stack_limit_changed=False,ordinary_lower_stack_initial_DWORD=0,
        semantic_aliases_preserved=True,semantic_aliases_counted_as_extra_mappings=False,
        actual_source_PCs=39,actual_source_accesses=24,actual_source_CALLs=5,genuine_source_probe_RET=1,
        separate_API_return_reads=1,new_compiled_guarded_bytes=86,reused_compiled_heap_bytes=84,
        source_identity_executed_bytes=132,anticipated_native_checkpoints_per_row=34,
        host_scheduler_changes_only=['State.EIP'],host_guest_execution_stores=0,
        declared_old_API_return_changes_only=['State.EAX.low32','State.ESP.low32','State.EIP.low32'],
        old_API_execution_is_draft_hypothesis=True,original_x86_API_internals_equivalence=False,
        original_volatile_register_or_flag_equivalence=False,generic_Runtime_CPU_and_call_records_preserved=True,
        query_struct_bytes=148,query_pointer=0x200017b8,only_size_DWORD_initialized_by_source=True,
        terminal_EIP=0x34600,terminal_ESP=0x20000618,source_reads_before_TEST=True,
        source_CALL_store_precedes_ESP_publication=True,source_IAT_read_precedes_query_return_store=True,
        real_probe_relocated_PUSH_RET_verified=True,probe_RET_not_synthesized=True,
        declared_AF_representatives=[dict(pc=pc,value=0) for pc in (0x780039bf,0x780039d6,0x780058db,0x780058c5)],
        final_TEST_flags_derived_from_declared_lower_page=True,undefined_AF_universal_original_equivalence=False,
        new_phase_names=list(derived['phases']),current_native_proof_bound=False,current_native_compared=False,
        native_or_original_or_game_executed_by_this_audit=False,HeapCreate_executed=False,GetVersionExA_executed=False,
        host_handle_created=False,heap_initialized=False,mode_selected=False,selector_RET_executed=False,
        source_initializer_RET_executed=False,original_attach_proved=False,root_full_causal_model_audited=False,
        whole_M4_complete=False,source_commands=commands+heap_commands,initial_dependency_check=initial,
        final_dependency_check=verify_manifest(files),elapsed_seconds=(time.perf_counter_ns()-started)/1e9,
        files=dict(sorted(files.items())))
    path = out/'report.json'
    publish_bytes(path,(json.dumps(report,indent=2)+'\n').encode())
    add(path)
    publish_bytes(out/'pins.json',(json.dumps(dict(files=dict(sorted(files.items()))),indent=2)+'\n').encode())
    print(json.dumps(dict(passed=True,schema=report['schema'],report_sha256=sha(path),pins_sha256=sha(out/'pins.json'),
        rows=48,static_controls=12,comparisons=checks,current_native_proof_bound=False)))


if __name__ == '__main__':
    main(sys.argv[1])
