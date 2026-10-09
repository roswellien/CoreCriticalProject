"""Final independent actual native/typed query-response and ownership audit."""
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
BASE = ROOT/'reports/m4-crt-heap-version-root-audit'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path
from stages import verify_stage

SOURCE_SHA = '90565b98f9880fa49358c40d021967af700cc598c4f35da148469bad92372b5f'
SOURCE_PINS_SHA = '5064c6bbb8f42d6003bf5449fb7db34efde7d8214a235ed344d44cd769592d67'
ACCEPT_SHA = 'fccb8400f1c4a5b8ee3824684d763d1a6391d9322ad28c0a5b173ef8bf483154'
DRAFT_SHA = '6f9f630ad17c34d85605fa74fa24cad75ff36d21f74e58ace0d3386538aabc21'
BEFORE_SHA = 'eb99d9298b3fd81d405d193b311b2379abc47ea55d0c73c011d26a5e5ee7f8d2'
PREFIX_SHA = '894c0b674fbc1b2c625e5ff10dd74931d349b70a51b07d754a889cefe96de066'
ORIGINAL_SHA = 'cbcb423813a712851f63a4921b72544499e74488d24184a4f084a74ae14009b2'
TOKEN,PAGE,PROBE_PAGE,STACK_PAGE = 0x48450001,0x78035000,0x78005000,0x20000000
COLD_PAGE = 0x7800c000
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


def main(name,execution_directory,execution_sha,observer_directory,observer_sha,stage_file,stage_sha):
    started = time.perf_counter_ns()
    need(re.fullmatch(r'final-r[1-9][0-9]*',name),'Fresh final audit name')
    need(all(re.fullmatch(r'[0-9a-f]{64}',v) for v in (execution_sha,observer_sha,stage_sha)),
         'Explicit full current proof hashes')
    out = workspace_path(BASE/name,reports=True)
    need(out.parent == BASE and not out.exists(),'Fresh private output')
    files = {}

    def add(path,digest=None):
        path = Path(path).absolute()
        key,value = normalized(str(path)),sha(path) if digest is None else digest
        need(sha(path) == value and (key not in files or files[key] == value),'Exact unique physical dependency')
        files[key] = value
        return path

    source_path = add(ROOT/'reports/m4-crt-heap-version-recovery/recovery-r1/report.json',SOURCE_SHA)
    source_pins = add(source_path.with_name('pins.json'),SOURCE_PINS_SHA)
    source = read(source_path)
    need(source['passed'] and source['schema'] == 'mw34-m4-heap-version-static-recovery-v1','Exact sealed source contract')
    for path,digest in read(source_pins)['files'].items():
        add(path,digest)
    accept_path = add(ROOT/'reports/m4-crt-heap-mode-root/root-acceptance-r1/report.json',ACCEPT_SHA)
    accepted = read(accept_path)
    need(accepted['passed'],'Previous accepted native HeapCreate frontier')
    identity = accepted['receipts']['author_execution']
    previous_execution = read(add(identity['path'],identity['sha256']))
    draft_path = add(ROOT/'reports/m4-crt-heap-version-root/draft-r2/report.json',DRAFT_SHA)
    draft = read(draft_path)
    need(draft['passed'] and draft['ordinary_BEFORE_models']==48 and not draft['native_executed'],
         'Fresh source-only root draft')
    for path,digest in draft['files'].items():
        add(path,digest)
    core = ROOT/'tools/m4-crt-heap-version-root'
    add(core/'before.py',BEFORE_SHA)
    add(core/'prefix.py',PREFIX_SHA)
    for path in (Path(__file__),Path(__file__).with_name('README.md'),Path(sys.executable),
                 core/'consumer.py',core/'draft.py',ROOT/'tools/m4-pipeline/manifests.py',
                 ROOT/'tools/m4-pipeline/paths.py',ROOT/'tools/m4-pipeline/capture_bundle.py'):
        add(path)
    add(Path(__file__).with_name('README-final.md'))
    add(Path(__file__).with_name('audit.py'))
    audit_receipt = add(BASE/'draft-r1/report.json','c749a38bcf0f5f9912c36829c1801553bd47c84dbaa42d042526c0ca527ef676')
    audit_pins = add(BASE/'draft-r1/pins.json','467d6ae1a1c570bd68cd14baf23e778aa15e5d1435a3088a1679fb255bd55a45')
    for path,digest in read(audit_pins)['files'].items():
        add(path,digest)
    execution_path = add(Path(execution_directory)/'report.json',execution_sha)
    observer_path = add(Path(observer_directory)/'report.json',observer_sha)
    stage_path = add(Path(stage_file),stage_sha)
    need(execution_path.parent.parent == ROOT/'reports/m4-crt-heap-version' and
         observer_path.parent.parent == ROOT/'reports/m4-crt-heap-version-root' and
         stage_path.parent.parent == ROOT/'reports/m4-crt-heap-version-root','Current proof namespaces')
    execution,observer = read(execution_path),read(observer_path)
    need(execution['passed'] and execution['native_stages_completed'] == 2 and execution['native_executed_by_author'],
         'Both actual delegated native workers completed')
    need(observer['passed'] and observer['execution_sha256'] == execution_sha and
         observer['original_BEFORE_ordinary_sequences'] == 48 and observer['root_full_causal_model_sequences'] == 0 and
         observer['independently_executed_by_root'] is False and observer['AFTER_machine_state_used_as_seed'] is False and
         observer['author_expected_model_imported'] is False and observer['original_API_internals_equivalence'] is False and
         observer['manifest_dependent_output_universal_equivalence'] is False and observer['GetVersionExA_executed'] is True and
         observer['ordinary_selector_RET_sequences'] == 48 and observer['ordinary_environment_frontier_sequences'] == 0 and
         observer['environment_API_called'] is False and observer['heap_mode_global_published'] is False and
         observer['heap_initializer_RET'] is False and observer['lower_stack_original_observed'] is False and
         observer['original_guard_stack_growth_proved'] is False and observer['TIB_and_Policy_changed'] is False,
         'Current ordinary native observation and strictly bounded version/selector credit')
    for receipt in (execution,observer):
        for category in ('files','sources','source_files','tools','libraries','entry_objects','compiler_read_headers','artifacts','input_files'):
            for path,digest in receipt.get(category,{}).items():
                add(path,digest)
    for receipt_path in (execution_path,observer_path):
        pins_path = receipt_path.with_name('pins.json')
        if pins_path.exists():
            add(pins_path)
            for path,digest in read(pins_path)['files'].items():
                add(path,digest)
    native_stages = []
    for level in ('O0','O2'):
        for key in ('native_stage','pack_stage'):
            path = add(Path(execution['levels'][level][key])/'stage.json')
            checked = verify_stage(path.parent,sha(path))
            need(checked['recorded_stage_passed'],'Actual successful native/packing stage')
            native_stages.append(checked)
    observer_stage = verify_stage(stage_path.parent,stage_sha)
    need(observer_stage['recorded_stage_passed'],'Successful current root observer stage')
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
    raw_code,raw_heap,raw_probe,raw_cold = (M.D.mapped(provider,address) for address in (0x78003000,PAGE,PROBE_PAGE,COLD_PAGE))
    need(source_pages == {0x78003000:raw_code,PAGE:raw_heap,PROBE_PAGE:raw_probe,COLD_PAGE:raw_cold},'Four exact raw source pages')
    need(hashlib.sha256(raw_cold).hexdigest() == source['data']['selector-cold-page']['sha256'],'Fresh RX cold code page identity')
    pages.update(source_pages)
    for label in ('heap-fragment','heap-provider','selector-prefix','stack-probe',*source['new_guarded_source_span_names']):
        for instruction in source['spans'][label]['instructions']:
            size,op,args = heap_program[instruction['pc']]
            need(size == instruction['width'] and op == instruction['mnemonic'] and
                 ' '.join(', '.join(args).split()) == ' '.join(instruction['operands'].split()),
                 'Every actual full source instruction/width matches independent receipt')

    def stage(state,fx,cpu,memory):
        result = OLD.stage(state,fx,cpu,memory)
        for address in (0x78003000,PAGE,PROBE_PAGE,STACK_PAGE,COLD_PAGE):
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
            ('heap-stack-probe.bin',PROBE_PAGE,0x8b5,0x8e6),
            ('heap-version-branch.bin',0x78003000,0xa31,0xa4b),
            ('heap-version-environment.bin',0x78003000,0xa4b,0xa62),
            ('heap-version-mode1.bin',COLD_PAGE,0xcc5,0xccd),
            ('heap-version-epilogue.bin',0x78003000,0xa7d,0xa80)):
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

    checks,rows,controls,response_controls = 0,[],[],[]
    native_rows,metadata_pairs,unused_records,distinct_ctor_owners = 0,0,0,0
    export_cache,API_identity_evidence,actual_version_outcomes = {},[],[]

    def eq(actual,expected,why):
        nonlocal checks
        checks += 1
        need(actual == expected,why)

    def named_export(path,digest,name):
        key = (normalized(str(path)),digest)
        if key not in export_cache:
            data = Path(path).read_bytes()
            need(hashlib.sha256(data).hexdigest() == digest,'Exact actual native API owner file bytes')
            u16 = lambda off:struct.unpack_from('<H',data,off)[0]
            u32 = lambda off:struct.unpack_from('<I',data,off)[0]
            pe = u32(0x3c)
            need(data[:2] == b'MZ' and data[pe:pe+4] == b'PE\0\0' and u16(pe+4) == 0x8664,
                 'Actual API owner is x64 PE')
            opt = pe+24
            need(u16(opt) == 0x20b,'Actual API owner PE32+ header')
            sections = []
            for index in range(u16(pe+6)):
                off = opt+u16(pe+20)+index*40
                virtual,rva,raw,file_off = struct.unpack_from('<4I',data,off+8)
                need(file_off+raw <= len(data),'API owner raw section bounds')
                sections.append((rva,raw,file_off))
            def at(rva,count=1):
                for start,length,off in sections:
                    if start <= rva and rva+count <= start+length:
                        return off+rva-start
                raise ValueError('API owner export raw RVA bounds')
            directory,length = struct.unpack_from('<2I',data,opt+112)
            off = at(directory,40)
            count,names,functions,name_table,ordinals = struct.unpack_from('<5I',data,off+20)
            exports = {}
            for index in range(names):
                name_rva = u32(at(name_table+index*4,4))
                name_off = at(name_rva)
                end = data.index(0,name_off,min(name_off+4096,len(data)))
                text = data[name_off:end].decode('ascii')
                ordinal = u16(at(ordinals+index*2,2))
                need(ordinal < count,'API owner export ordinal index')
                function_rva = u32(at(functions+ordinal*4,4))
                exports[text] = (function_rva,directory <= function_rva < directory+length)
            export_cache[key] = (exports,u32(opt+56))
        exports,image_size = export_cache[key]
        need(name in exports and not exports[name][1],'Actual native owner direct named export')
        return exports[name][0],image_size

    def API_identity(row,stem,name):
        data = (row/(stem+'-api-before.bin')).read_bytes()
        eq((row/(stem+'-api-after.bin')).read_bytes(),data,'Actual API owner identity before/after')
        need(len(data) == 2184,'Complete typed actual API owner identity')
        target,named,owner,owner_named = struct.unpack_from('<4Q',data)
        base,size,allocation,allocation_state,image_type,protection,reserved = struct.unpack_from('<3Q4I',data,32)
        need(target != 0 and owner != 0 and target == named == owner_named and owner == allocation and
             allocation <= base <= target < base+size <= 2**64,'Nonzero API/owner and nonwrapping range')
        need(allocation_state == 0x1000 and image_type == 0x1000000 and protection&0xf0 and not protection&0x101,
             'Actual executable committed native API image')
        digest = data[72:136].decode('ascii')
        text = data[136:].decode('utf-16-le')
        filename,separator,tail = text.partition('\0')
        need(separator and filename and all(char == '\0' for char in tail),'Terminated/padded actual owner path')
        path = add(Path(filename),digest)
        function_rva,image_size = named_export(path,digest,name)
        eq(target,owner+function_rva,'Independent named owner export/RVA association '+name)
        need(owner <= target < owner+image_size <= 2**64,'Named API inside actual owner image')
        evidence = dict(name=name,target=target,owner=owner,path=str(path),sha256=digest,named_export_RVA=function_rva)
        if evidence not in API_identity_evidence:
            API_identity_evidence.append(evidence)
        return evidence

    def OS_witness(row):
        data = (row/'heap-version-job.bin').read_bytes()
        need(len(data) == 256,'Complete64DWORD immutable version job')
        job = struct.unpack('<64I',data)
        w_data,r_data,q_data = ((row/name).read_bytes() for name in
            ('heap-version-witness.bin','heap-version-registry.bin','heap-version-query-witness.bin'))
        need(len(w_data) == 128 and len(r_data) == 144 and len(q_data) == 160,'Typed W16Q/R18Q/Q20Q complete witnesses')
        w,r,q = struct.unpack('<16Q',w_data),struct.unpack('<18Q',r_data),struct.unpack('<20Q',q_data)
        eq(w[:6],(1,0,1,0,4096,0),'Actual noninjected named HeapCreate request')
        need(w[6] != 0 and w[6] != TOKEN and w[7] == TOKEN and w[11] == w[6],
             'Exact full native heap handle distinct from opaque guest token')
        eq((w[8],w[10],job[23]),(job[22],job[22],job[22]),'Actual inner/outer caller error restored')
        eq(w[12:],(0x20001848,0x780039d6,0x20001858,0x780039d6),'Finite authentic HeapCreate ABI return')
        need(r[0] == 1 and r[1] != 0,'Typed actual resource-owner/generation')
        eq(r[2:11],(1,TOKEN,w[6],1,1,0,1,1,1),'One actual private acquisition and successful matching release')
        eq(r[12:],(1,0,0,1,w[6],0),'One same-full-handle cleanup without skip/rollback/duplicate/denial')
        need(w[9] <= 0xffffffff and r[11] <= 0xffffffff,'Actual unconstrained DWORD heap API errors')
        before,after = (row/'query-input.bin').read_bytes(),(row/'query-output.bin').read_bytes()
        need(len(before) == len(after) == 148 and struct.unpack_from('<I',before)[0] == 148,
             'Exact source148B input and full measured scratch output')
        eq(q[:3],(1,1,1),'One admitted actual named version query')
        need(q[3] <= 0xffffffff and q[9] <= 0xffffffff,'Raw actual full BOOL and DWORD query error')
        eq(q[4:8],(148,0x200017b8,0x20000618,0x78003a31),'Authentic query size/pointer/frame/return')
        eq((q[8],q[10]),(job[22],job[22]),'Measured actual query caller error restored')
        eq(q[11:16],(37,1,1,1,1),'Complete output37DWORD/preflight/transport/checked return lifecycle')
        header,major,minor,build,platform = struct.unpack_from('<5I',after)
        good = q[3] != 0 and platform == 2 and major >= 5
        eq(q[16:],(int(good),int(not good),major,platform),'Measured output fields determine source branch')
        need(good,'Current48 ordinary query witnesses actually qualify; no assumed version')
        eq(job[:22],(0,0x20001858,0x20001860,31,2,11,5,10,0,0x78003a7f,0x780039e8,
                    1,0,1,1,1,1,1,1,1,0,1),'Actual source/query/selector-return/closed-heap job lifecycle')
        eq(job[24:],(0x7800183c,0x780039bf,0x7800183e,0x78001843,0x78003a0c,0x780039e3,21,84,
            0x2000184c,0x780058b5,0x78003a14,0x78003a19,0x78003a2b,0x7802e0a0,0x34600,0x78003a31,1,1,86,2086,
            0x20000618,0x200017b8,1,q[3],37,1,1,1,1,0,26,23,8,3,0x78003a5c,0x7802e09c,0x345e6,0x7800ccc5,148,2086),
            'Immutable current source/transport/decision job metadata')
        outcome = dict(raw_BOOL=q[3],size=header,major=major,minor=minor,build=build,platform=platform,
            full_output_sha256=hashlib.sha256(after).hexdigest(),manifest_universal_equivalence=False)
        if outcome not in actual_version_outcomes:
            actual_version_outcomes.append(outcome)
        return dict(token=TOKEN,handle=w[6],owner=r[1],witness=w,registry=r,query=q,
            input=before,output=after,response=dict(input=before,output=after,result=q[3]),
            create=API_identity(row,'heap-version-create','HeapCreate'),
            destroy=API_identity(row,'heap-version-destroy','HeapDestroy'),
            query_identity=API_identity(row,'heap-version-query','GetVersionExA'))

    def ownership_phase(tag,actual):
        active = tag.startswith(('heap-create-','heap-mode-','heap-version-')) or tag in ('entry-after-fault','retry-after')
        if not active:
            w,r = bytes(128),bytes(144)
        elif tag in ('heap-create-before','heap-create-projected','heap-create-provider-before','heap-create-api-before'):
            w,r = bytes(128),struct.pack('<18Q',1,actual['owner'],1,*([0]*15))
        else:
            closed = tag in ('heap-create-after','entry-after-fault','retry-after')
            registry = actual['registry'] if closed else (1,actual['owner'],1,TOKEN,actual['handle'],1,1,1,1,*([0]*9))
            w,r = struct.pack('<16Q',*actual['witness']),struct.pack('<18Q',*registry)
        return {'heap-create-witness.bin':w,'heap-create-registry.bin':r}

    def query_phase(tag,actual,model):
        q = [0]*20
        before,after,writes = bytes(148),bytes(148),bytes(1280)
        active = tag == 'heap-mode-query-before' or tag.startswith('heap-version-') or tag in ('heap-create-after','entry-after-fault','retry-after')
        if active:
            source_q = actual['query']
            q = [1,1,0,0,148,0x200017b8,0x20000618,0x78003a31,source_q[8],0,0,0,0,0,0,0,0,0,0,0]
            before = actual['input']
            if tag != 'heap-mode-query-before':
                q[12] = 1
            if tag not in ('heap-mode-query-before','heap-version-query-native-before'):
                q[2:4],q[9:11],q[18:] = source_q[2:4],source_q[9:11],source_q[18:]
                after = actual['output']
            if tag not in ('heap-mode-query-before','heap-version-query-native-before','heap-version-query-native-after'):
                q[11],q[13] = 37,1
                raw = b''.join(struct.pack('<5I',*word) for word in model['query_output_accesses'])
                writes = raw+bytes(1280-len(raw))
            if tag in ('heap-version-query-returned','heap-version-selector-return-after','heap-version-environment-before',
                       'heap-create-after','entry-after-fault','retry-after'):
                q[14:16] = [1,1]
            if tag in ('heap-version-selector-return-after','heap-version-environment-before','heap-create-after','entry-after-fault','retry-after'):
                q[16:18] = source_q[16:18]
        return {'heap-version-query-witness.bin':struct.pack('<20Q',*q),'query-input.bin':before,
            'query-output.bin':after,'heap-version-output-accesses.bin':writes}

    def native_observation(row,index,entry,earlier,derived,actual):
        nonlocal native_rows,metadata_pairs,unused_records,distinct_ctor_owners
        eq((row/'heap-version-lower-input.bin').read_bytes(),bytes(4096),'Ordinary declared lower-page input')
        phases = dict(earlier,**derived['phases'])
        phases['entry-after-fault'] = derived['phases']['heap-create-after']
        phases['retry-after'] = derived['phases']['heap-create-after']
        tags = {name.split('/')[1] for name in row.inventory if name.startswith(row.name+'/') and name.count('/') == 1}
        eq(tags,set(phases),'Current exact40-checkpoint inventory')
        eq(len(phases),40,'Forty complete independently calculated phases')
        for tag,values in phases.items():
            expected_files = dict(values,**ownership_phase(tag,actual),**query_phase(tag,actual,derived))
            eq(row.inventory[row.name+'/'+tag],set(expected_files),'Complete actual phase inventory '+tag)
            eq({name:(row/tag/name).read_bytes() for name in expected_files},expected_files,
               'Every State/FX/CPU21pages/source/W/R/Q/input/output/transport byte '+tag)
            metadata_pairs += 1
        def ledger(name,values,capacity):
            raw = b''.join(struct.pack('<5I',*word) for word in values)
            eq((row/name).read_bytes(),raw+bytes(capacity-len(raw)),'Actual complete typed ledger '+name)
        ledger('heap-version-accesses.bin',derived['ledger'],1280)
        ledger('heap-version-api-accesses.bin',[derived['API_return_access'],derived['query_return_access']],160)
        ledger('heap-version-output-accesses.bin',derived['query_output_accesses'],1280)
        events = ((1,0x7800183c,0x20001860,0),(2,0x7800183e,0x780039bf,0x78001843),
            (3,0x780039d0,0x7802e0a8,0x3461e),(4,0x780039d0,0x20001848,0x780039d6),
            (5,0x780039d8,PAGE,TOKEN),(6,0x780039e3,0x78003a0c,0x780039e8),
            (7,0x78003a14,0x780058b5,0x78003a19),(8,0x780058cf,0x78003a19,0x20000620),
            (9,0x78003a2b,0x7802e0a0,0x34600),(10,0x78003a2b,0x20000618,0x78003a31),
            (11,0x78003a7f,0x780039e8,0x20001854))
        raw = b''.join(struct.pack('<4I',*word) for word in events)
        eq((row/'heap-version-events.bin').read_bytes(),raw+bytes(256-len(raw)),'Real source CALL/RET and separate ABI-return events')
        eq((row/'heap-version-scheduler.bin').read_bytes(),struct.pack('<8I',*derived['scheduler']),'Actual EIP-only scheduler')
        eq((row/'heap-version-undefined.bin').read_bytes(),struct.pack('<8I',0x780039bf,0x780039d6,0x780058db,0x780058c5,0x78003a31,0,0,0),
           'Five exact source-qualified AF representatives')
        evidence = OLD.evidence(entry)
        evidence['mainargs-job.bin'] = struct.pack('<20I',M.SLOT,M.RAW,*([0]*13),1,0,0,0x78003a7f,0x780039e8)
        evidence['mainargs-events.bin'],evidence['mainargs-accesses.bin'] = bytes(256),bytes(1280)
        for name,value in evidence.items():
            captured = (row/name).read_bytes()
            eq(json.loads(captured,object_pairs_hook=unique_object) if name.endswith('.json') else captured,value,
               'Complete carried earlier evidence '+name)
        unused = {
            'filename-job.bin':struct.pack('<22I',0,0xa11c0000+index,*([0]*18),0x78037174,0x7800bbd6),
            'filename-witness.bin':bytes(536),
            'commandline-job.bin':struct.pack('<28I',*([0]*4),0x3442e,*([0]*20),0x33000000,0x78037174,0x78001897),
            'commandline-accesses.bin':bytes(320),'commandline-consumer-accesses.bin':bytes(320),'commandline-events.bin':bytes(256),
            'parser-job.bin':struct.pack('<20I',*([0]*14),0x7800bc48,0x7800bbf7,0x7800bbfc,0x7800bce6,0x780379e1,436),
            'parser-accesses.bin':bytes(640),'parser-events.bin':bytes(128),'parser-undefined.bin':bytes(32),
            'locale-job.bin':struct.pack('<24I',*([0]*15),0x78003dd2,0x78003ddb,0x78001055,0x7800107b,0x780012b3,0x78001080,0x7803708c,17,269),
            'locale-accesses.bin':bytes(640),'locale-events.bin':bytes(128),'locale-scheduler.bin':bytes(40),
            'heap-job.bin':struct.pack('<26I',*([0]*16),0x7800183c,0x780039bf,0x7800183e,0x78001843,0x780039d0,0x7802e0a8,0x780039d6,0x3461e,17,84),
            'heap-accesses.bin':bytes(640),'heap-events.bin':bytes(128),'heap-undefined.bin':bytes(32),'heap-scheduler.bin':bytes(32),
            'heap-create-job.bin':struct.pack('<32I',*([0]*24),0x7800183c,0x780039bf,0x7800183e,0x78001843,0x78003a0c,0x780039e3,18,84),
            'heap-create-accesses.bin':bytes(640),'heap-create-api-accesses.bin':bytes(160),'heap-create-events.bin':bytes(128),
            'heap-create-undefined.bin':bytes(32),'heap-create-scheduler.bin':bytes(32),'heap-create-witness.bin':bytes(128),
            'heap-mode-job.bin':struct.pack('<44I',*([0]*24),0x7800183c,0x780039bf,0x7800183e,0x78001843,0x78003a0c,0x780039e3,20,84,
                0,0x780058b5,0x78003a14,0x78003a19,0x78003a2b,0x7802e0a0,0x34600,0x78003a31,0,0,86,2026),
            'heap-mode-accesses.bin':bytes(1280),'heap-mode-api-accesses.bin':bytes(160),'heap-mode-events.bin':bytes(256),
            'heap-mode-undefined.bin':bytes(32),'heap-mode-scheduler.bin':bytes(32),'heap-mode-witness.bin':bytes(128),
            'heap-mode-lower-input.bin':bytes(4096)}
        for name,value in unused.items():
            eq((row/name).read_bytes(),value,'Exact unused older/later-service record '+name)
            unused_records += 1
        owners = [actual['owner']]
        for name in ('heap-create-registry.bin','heap-mode-registry.bin'):
            raw = (row/name).read_bytes()
            need(len(raw) == 144,'Complete typed constructor-only registry '+name)
            ctor = struct.unpack('<18Q',raw)
            need(ctor[0] == 1 and ctor[1] != 0 and ctor[1] not in owners,'Distinct unused private constructor owner '+name)
            eq(ctor[2:],(1,*([0]*15)),'Unused private constructor registry has no acquired resource '+name)
            owners.append(ctor[1]);distinct_ctor_owners += 1
        for name in ('filename','commandline','parser','locale','heap','heap-create','heap-mode'):
            eq((row/(name+'-reason.txt')).read_text().strip(),'','No fabricated inactive-service fault '+name)
        for name in ('mainargs','heap-version'):
            eq((row/(name+'-reason.txt')).read_text().strip(),'Genuine selector returned; heap mode publication remains unadmitted',
               'Truthful actual selector-return boundary reason')
        for name,value in (('initterm',entry.init_reason),('control',entry.control_reason),('matherr','')):
            eq((row/(name+'-reason.txt')).read_text().strip(),value,'Unchanged earlier source diagnostic')
        for actor in ('writer','entry'):
            M.D.host((row/(actor+'-host-before.bin')).read_bytes(),(row/(actor+'-host-after.bin')).read_bytes())
        entry_job = (row/'entry-job.bin').read_bytes()
        need(len(entry_job) == 40 and entry_job[32:] == bytes(8),'Complete entry job without fixture callback')
        eq(struct.unpack_from('<3I',entry_job,20),(0,0x78003a7f,0x780039e8),'Actual typed selector-return frontier fault')
        current = json.loads((row/'result.json').read_bytes(),object_pairs_hook=unique_object)
        need(current['passed'] and current['scenario'] == index and current['control'] == 0 and
             current['writer_complete'] and current['entry_executed'] and current['poisoned_retry'] and
             not current['State_reseed_after_writer'] and not current['full_CRT'] and not current['whole_M4_complete'],
             'Actual ordinary execution and preserved poisoned retry')
        eq((current['fault_reason'],current['fault_site'],current['fault_target']),(0,0x78003a7f,0x780039e8),
           'Actual selector-return fault metadata')
        eq((current['source_events'],current['writer_events'],current['data_routes']),(len(entry.events),97,1),
           'All carried ordinary event counts')
        root_files = set(evidence)|set(unused)|{'heap-create-registry.bin','heap-mode-registry.bin','input.bin','writer-record.bin',
            'writer-host-before.bin','writer-host-after.bin','entry-host-before.bin','entry-host-after.bin','entry-job.bin','result.json',
            'matherr-reason.txt','control-reason.txt','initterm-reason.txt','mainargs-reason.txt','filename-reason.txt','commandline-reason.txt',
            'parser-reason.txt','locale-reason.txt','heap-reason.txt','heap-create-reason.txt','heap-mode-reason.txt','heap-version-reason.txt',
            'heap-version-job.bin','heap-version-accesses.bin','heap-version-api-accesses.bin','heap-version-output-accesses.bin',
            'heap-version-events.bin','heap-version-undefined.bin','heap-version-scheduler.bin','heap-version-witness.bin','heap-version-registry.bin',
            'heap-version-lower-input.bin','heap-version-query-witness.bin','query-input.bin','query-output.bin',
            'heap-version-create-api-before.bin','heap-version-create-api-after.bin','heap-version-destroy-api-before.bin',
            'heap-version-destroy-api-after.bin','heap-version-query-api-before.bin','heap-version-query-api-after.bin'}
        eq(row.inventory[row.name],root_files,'Exact full ordinary root-file inventory')
        native_rows += 1

    def affine(seam,response=None):
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
        value = dict(state=bytes(current),memory=memory,phases=phases,ledger=ledger,
            API_return_access=API_return_access,probe_return_access=(0x780058cf,0x20000620,0x78003a19,4,0),
            scheduler=(1,struct.unpack_from('<I',initial,2472)[0],P,0x7800183c,P,0,M.SLOT,P),
            routes=[(0x7800183e,0x780039bf,0x78001843),(0x780039d0,0x3461e,0x780039d6),
                    (0x780039e3,0x78003a0c,0x780039e8),(0x78003a14,0x780058b5,0x78003a19),
                    (0x78003a2b,0x34600,0x78003a31)],declared_A=A,declared_B=B)
        query_input = bytes(memory[0x20001000][0x7b8:0x7b8+148])
        value['query_input'] = query_input
        if response is None:
            return value
        need(set(response) == {'input','output','result'} and response['input'] == query_input and
             isinstance(response['output'],bytes) and len(response['output']) == 148 and
             isinstance(response['result'],int) and not isinstance(response['result'],bool) and
             0 <= response['result'] <= 0xffffffff,'Independent finite complete explicitly typed API response')
        phases.pop('heap-create-after')
        phases['heap-version-query-native-before'] = stage(current,fx,cpu,memory)
        phases['heap-version-query-native-after'] = stage(current,fx,cpu,memory)
        transport = []
        for index in range(37):
            address = 0x200017b8+index*4
            word = struct.unpack_from('<I',response['output'],index*4)[0]
            struct.pack_into('<I',memory[0x20001000],address&4095,word)
            transport.append((0x78003a2b,address,word,4,1))
        phases['heap-version-query-output-after'] = stage(current,fx,cpu,memory)
        phases['heap-version-query-return-before'] = stage(current,fx,cpu,memory)
        returned = struct.unpack_from('<I',memory[STACK_PAGE],0x618)[0]
        eq(returned,0x78003a31,'Separate authentic version-query stdcall return word')
        query_return_access = (0x78003a2b,0x20000618,returned,4,0)
        setreg('eax',response['result'])
        setreg('esp',0x20000620)
        setpc(returned)
        phases['heap-version-query-returned'] = stage(current,fx,cpu,memory)
        raw_BOOL = response['result']
        flags(CF=0,PF=int((raw_BOOL&255).bit_count()%2 == 0),AF=0,ZF=int(raw_BOOL == 0),SF=raw_BOOL>>31,OF=0)
        suffix = [0x78003a31,0x78003a33]

        def cmpflags(a,b):
            result = (a-b)&0xffffffff
            signed = lambda number:number if number < 0x80000000 else number-0x100000000
            difference = signed(a)-signed(b)
            flags(CF=int(a<b),PF=int((result&255).bit_count()%2 == 0),AF=int((a&15)<(b&15)),
                ZF=int(result == 0),SF=result>>31,OF=int(not -0x80000000 <= difference <= 0x7fffffff))

        good = raw_BOOL != 0
        if good:
            platform = fetch(0x78003a35,0x200017c8)
            suffix.extend((0x78003a35,0x78003a3c))
            cmpflags(platform,2)
            good = platform == 2
            if good:
                major = fetch(0x78003a3e,0x200017bc)
                suffix.extend((0x78003a3e,0x78003a45))
                cmpflags(major,5)
                good = major >= 5
        if good:
            suffix.extend((0x7800ccc5,0x7800ccc7,0x7800ccc8,0x78003a7d,0x78003a7e,0x78003a7f))
            store(0x7800ccc5,0x2000061c,1)
            setreg('esp',0x2000061c)
            setreg('eax',fetch(0x7800ccc7,0x2000061c,1))
            setreg('esp',0x20000620)
            setreg('ebx',fetch(0x78003a7d,0x20000620,EBX0))
            setreg('esp',0x20000624)
            # LEAVE genuinely repositions ESP before its checked saved-EBP read.
            setreg('esp',0x20001850)
            setreg('ebp',fetch(0x78003a7e,0x20001850,EBP0))
            setreg('esp',0x20001854)
            target = fetch(0x78003a7f,0x20001854,0x780039e8)
            setreg('esp',0x20001858)
            setpc(target)
            phases['heap-version-selector-return-after'] = stage(current,fx,cpu,memory)
            terminal_EIP,terminal_ESP = target,0x20001858
        else:
            suffix.extend((0x78003a4b,0x78003a51,0x78003a56,0x78003a57,0x78003a5c))
            setreg('eax',0x20000624)
            store(0x78003a51,0x2000061c,0x1090)
            setreg('esp',0x2000061c)
            store(0x78003a56,0x20000618,0x20000624)
            setreg('esp',0x20000618)
            store(0x78003a57,0x20000614,0x7802e3b8)
            setreg('esp',0x20000614)
            target = fetch(0x78003a5c,0x7802e09c,0x345e6)
            store(0x78003a5c,0x20000610,0x78003a62)
            setreg('esp',0x20000610)
            setpc(target)
            value['routes'].append((0x78003a5c,target,0x78003a62))
            phases['heap-version-environment-before'] = stage(current,fx,cpu,memory)
            terminal_EIP,terminal_ESP = target,0x20000610
        phases['heap-create-after'] = stage(current,fx,cpu,memory)
        value.update(state=bytes(current),memory=memory,phases=phases,ledger=ledger,
            PCs=source['carried_source_PCs']+suffix,query_output=response['output'],query_result=raw_BOOL,
            query_output_accesses=transport,query_return_access=query_return_access,
            undefined=[(pc,0) for pc in (0x780039bf,0x780039d6,0x780058db,0x780058c5,0x78003a31)],
            selector_returned=good,environment_reached=not good,terminal_EIP=terminal_EIP,terminal_ESP=terminal_ESP)
        need(len(phases) == 18 and len(transport) == 37,'Independent18phase/37DWORD API transport closure')
        return value

    def hypothetical_response(seam,BOOL=1,platform=2,major=6):
        before = affine(seam)['query_input']
        after = bytearray(before)
        struct.pack_into('<I',after,4,major)
        struct.pack_into('<I',after,16,platform)
        return dict(input=before,output=bytes(after),result=BOOL)

    def compare(entry,seam,response):
        actual = prefix.predict(entry,heap_program,TOKEN,response)
        expected = affine(seam,response)
        eq(set(actual['phases']),set(expected['phases']),'Complete independent eighteen-phase schema')
        for tag,value in expected['phases'].items():
            eq(actual['phases'][tag],value,'Whole State/FX/CPU21page/source phase '+tag)
            eq(len([name for name in value if name.startswith('page-')]),21,'Exactly21 mappings, excluding aliases')
        eq(bytes(actual['state']),expected['state'],'Full3504State terminal source effects')
        eq(actual['memory'],expected['memory'],'All21pages and semantic aliases')
        eq(actual['fx'],seam[3],'Whole512FX carried')
        eq(actual['cpu'],seam[1],'Whole40RuntimeCPU carried')
        eq(actual['accesses'],expected['ledger'],'All ordered genuine source accesses, excluding API transport')
        eq(actual['API_return_access'],expected['API_return_access'],'Separate old API return read')
        eq(actual['probe_return_access'],expected['probe_return_access'],'Genuine relocated source RET access')
        eq(actual['query_return_access'],expected['query_return_access'],'Separate query return read')
        eq(actual['query_output_accesses'],expected['query_output_accesses'],'Separate37DWORD API transport ledger')
        eq(actual['query_input'],expected['query_input'],'Exact carried pre-query148B scratch input')
        eq(actual['query_output'],expected['query_output'],'Exact declared148B scratch output')
        eq(actual['query_result'],expected['query_result'],'Exact declared rawBOOL bits')
        eq(actual['PCs'],expected['PCs'],'All source PCs and actual finite-response branch path')
        eq(actual['routes'],expected['routes'],'All genuine source CALL routes')
        eq(actual['scheduler'],expected['scheduler'],'EIP-only old scheduler, zero guest execution stores')
        eq(actual['undefined'],expected['undefined'],'Only five exact-PC AF representatives')
        eq(actual['memory'][PROBE_PAGE],raw_probe,'Original RX probe page unmodified')
        eq(actual['memory'][COLD_PAGE],raw_cold,'Original RX cold page unmodified')
        eq({k:v for k,v in actual['memory'].items() if k not in (0x20001000,STACK_PAGE,PAGE)},
           {k:v for k,v in seam[2].items() if k not in (0x20001000,STACK_PAGE,PAGE)},
           'All unrelated pages and TIB/StackLimit semantic bytes preserved')
        raw_changed = bytearray(raw_heap)
        struct.pack_into('<I',raw_changed,0,TOKEN)
        eq(actual['memory'][PAGE],raw_changed,'Only source handle DWORD changes; mode remains unproduced')
        eq((actual['selector_returned'],actual['environment_reached'],actual['terminal_EIP'],actual['terminal_ESP']),
           (expected['selector_returned'],expected['environment_reached'],expected['terminal_EIP'],expected['terminal_ESP']),
           'Genuine selector RET or next unresolved environment CALL')
        need(actual['stack_probe_returned'] and not actual['query_executed'] and actual['query_response_applied'] and
             not actual['heap_mode_published'] and not actual['initializer_RET'] and not actual['heap_initialized'],
             'Hypothetical finite API response only; no heap publication/initializer completion')
        return expected

    payloads = [M.R.project(value) for value in M.R.originals(original_path.read_bytes())[:24]]
    with contextlib.ExitStack() as stack:
        readers = {}
        for level in ('O0','O2'):
            identity = execution['levels'][level]
            add(identity['bundle'],identity['bundle_sha256'])
            reader = stack.enter_context(CaptureBundle(identity['bundle'],identity['bundle_sha256']))
            need(len(reader.names()) == identity['logical_files'] and reader.read_bytes('COMPLETE') == b'COMPLETE',
                 'Strict complete current bundle; original BEFORE and typed API witnesses only')
            need({name.split('/')[0] for name in reader.names()} == {'COMPLETE','units'}|{'row-'+str(i) for i in range(36)},
                 'Exact current whole archive inventory')
            for index in range(36):
                request = json.loads(reader.read_bytes('row-'+str(index)+'/result.json'),object_pairs_hook=unique_object)
                need(request['passed'] and request['scenario'] == index and request['control'] == (0 if index < 24 else index+121),
                     'Exact all36 declared current requests; no full causal-model credit')
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
                    (entry.mem,seam[2],'Full startup all21pages/aliases')):
                    eq(actual,wanted,why)
                need(entry.init_complete and not entry.init_failed and not entry.args_failed and not entry.args_used and
                     entry.args_accesses == [],'Healthy original seam before mainargs provider')
                eq(len(earlier),20,'Twenty preserved prior source phases')
                for tag,value in earlier.items():
                    eq(value,full_phases[tag],'Full original model prior phase '+tag)
                actual_OS = OS_witness(row)
                derived = compare(entry,seam,actual_OS['response'])
                native_observation(row,index,entry,earlier,derived,actual_OS)
                rows.append(dict(level=level,index=index,source_PCs=51,source_accesses=31,source_CALLs=5,
                    genuine_source_RETs=2,separate_API_return_reads=2,separate_API_transport_DWORDs=37,
                    State=3504,FX=512,RuntimeCPU=40,mappings=21,
                    prior_phases=20,new_phases=18,anticipated_native_phases=40,
                    declared_A=derived['declared_A'],declared_B=derived['declared_B'],current_native_compared=True,
                    native_BOOL=actual_OS['query'][3],measured_major=actual_OS['query'][18],measured_platform=actual_OS['query'][19],
                    full_host_handle=actual_OS['handle'],resource_registry_owner=actual_OS['owner'],
                    actual_HeapCreate=True,actual_owned_HeapDestroy=True,actual_GetVersionExA=True,
                    selector_returned=True,heap_mode_global_published=False,heap_initializer_RET=False,
                    machine_ownership_query_metadata_phases=40))
                if index == 0:
                    for BOOL,platform,major in ((0,2,6),(1,1,6),(1,2,4),(1,2,5),(1,2,6),(0xffffffff,2,0xffffffff)):
                        response = hypothetical_response(seam,BOOL,platform,major)
                        hypothetical = compare(entry,seam,response)
                        response_controls.append(dict(level=level,hypothetical_BOOL=BOOL,hypothetical_platform=platform,
                            hypothetical_major=major,selector_returned=hypothetical['selector_returned'],
                            source_PCs=len(hypothetical['PCs']),source_accesses=len(hypothetical['ledger']),
                            native_or_API_executed=False))
                    for value in (0,0xffffffff,8,0x40,0x1848,0x80000000):
                        stack_input = struct.pack('<I',value)*1024
                        alternate,_ = before.expected(row,payload,wp,pp,gp,program,providers,maths,ctrl,
                            init,mainargs,argv,pages,level,stack_input)
                        complete,_ = full_model(stack_input)(row,payload,wp,pp,gp,program,providers,maths,ctrl,
                            init,mainargs,argv,pages,0,level)
                        other_seam = complete.args_phases['mainargs-before']
                        eq(bytes(alternate.state),other_seam[0],'Directed full-startup BEFORE State')
                        eq(alternate.mem,other_seam[2],'Directed explicit owned input full memory')
                        control = compare(alternate,other_seam,hypothetical_response(other_seam))
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
    need(native_rows == 48 and metadata_pairs == 1920 and unused_records == 1632 and distinct_ctor_owners == 96,
         'Complete48row40phase/unused-record/private-owner coverage')
    report = dict(schema='mw34-m4-heap-version-root-final-audit-v1',passed=True,
        scope='Independent full-original-BEFORE/affine source, actual named API output and heap ownership audit of every ordinary current native row',
        source_report_sha256=SOURCE_SHA,source_pins_sha256=SOURCE_PINS_SHA,root_draft_sha256=DRAFT_SHA,
        root_before_sha256=BEFORE_SHA,root_prefix_sha256=PREFIX_SHA,ordinary_rows=48,rows=rows,
        model_comparisons=checks,static_declared_stack_formula_controls=controls,
        static_hypothetical_API_response_formula_controls=response_controls,
        full_frozen_mainargs_before_crosscheck=True,stopping_subclass_used_as_expected_seed=False,
        AFTER_machine_state_used_as_seed=False,permitted_original_API_witness='Original FDIV input/query and separately validated typed actual heap/query API witnesses; no AFTER-machine seeds',
        author_expected_model_imported=False,independent_affine_source_ledger=True,
        whole_State_bytes=3504,whole_FX_bytes=512,whole_Runtime_CPU_bytes=40,captured_mappings=21,
        prior_mappings_preserved=20,new_raw_RX_cold_page=COLD_PAGE,
        new_raw_RX_cold_page_sha256=hashlib.sha256(raw_cold).hexdigest(),
        lower_stack_bytes_original_observed=False,original_stack_guard_growth_proved=False,
        TIB_and_Policy_stack_limit_changed=False,ordinary_lower_stack_initial_DWORD=0,
        semantic_aliases_preserved=True,semantic_aliases_counted_as_extra_mappings=False,
        qualifying_source_PCs=51,qualifying_source_accesses=31,qualifying_source_CALLs=5,
        genuine_source_probe_RET=1,genuine_source_selector_RET=1,
        separate_API_return_reads=2,separate_declared_API_transport_DWORDs=37,
        new_compiled_guarded_bytes=60,reused_compiled_heap_bytes=84,reused_selector_probe_bytes=86,
        source_identity_executed_bytes=169,total_source_identity_bytes=2086,anticipated_native_checkpoints_per_row=40,
        host_scheduler_changes_only=['State.EIP'],host_guest_execution_stores=0,
        declared_old_API_return_changes_only=['State.EAX.low32','State.ESP.low32','State.EIP.low32'],
        old_API_execution_is_draft_hypothesis=False,original_x86_API_internals_equivalence=False,
        original_volatile_register_or_flag_equivalence=False,generic_Runtime_CPU_and_call_records_preserved=True,
        query_struct_bytes=148,query_pointer=0x200017b8,only_size_DWORD_initialized_by_source=True,
        query_input_copied_from_independent_BEFORE_source_prefix=True,
        hypothetical_API_response_is_native_witness=False,query_output_transport_is_declared_API_effect=True,
        actual_native_BOOL_and_complete148_output_witness_drives_source=True,
        actual_ordinary_version_outcomes=actual_version_outcomes,actual_version_assumed=False,
        measured_manifest_sensitive_API_universal_original_equivalence=False,
        qualifying_terminal_EIP=0x780039e8,qualifying_terminal_ESP=0x20001858,
        qualifying_computed_selector_result=1,heap_mode_global_publication=False,source_reads_before_TEST=True,
        source_CALL_store_precedes_ESP_publication=True,source_IAT_read_precedes_query_return_store=True,
        real_probe_relocated_PUSH_RET_verified=True,probe_RET_not_synthesized=True,
        declared_AF_representatives=[dict(pc=pc,value=0) for pc in (0x780039bf,0x780039d6,0x780058db,0x780058c5,0x78003a31)],
        final_qualifying_flags_derived_from_CMP_measured_or_declared_major_minus5=True,
        alternate_flags_derived_from_exact_source_path=True,undefined_AF_universal_original_equivalence=False,
        new_phase_names=list(derived['phases']),current_native_proof_bound=True,current_native_compared=True,
        current_ordinary_native_rows_compared=native_rows,current_native_checkpoints_per_row=40,
        current_phase_machine_W_R_Q_input_output_transport_sets_compared=metadata_pairs,
        exact_unused_older_later_native_records_compared=unused_records,
        distinct_typed_ctor_private_owner_checks=distinct_ctor_owners,
        unused_heap_create_and_heap_mode_ctor_registries_have_no_resource=True,
        named_native_API_identity_and_direct_export_evidence=API_identity_evidence,
        actual_named_host_HeapCreate_results_witnessed=48,actual_owned_host_HeapDestroy_successes_witnessed=48,
        actual_named_GetVersionExA_results_and_full148_outputs_witnessed=48,
        actual_ordinary_selector_RET_sequences=48,actual_ordinary_environment_frontier_sequences=0,
        environment_API_executed=False,query_output_DWORD_ledger_checked_in_every_phase=True,
        complete_query20Q_and_heap16Q18Q_metadata_checked_in_every_phase=True,
        current_fault_site=0x78003a7f,current_fault_target=0x780039e8,current_fault_reason=0,
        final_root_proof=dict(execution_sha256=execution_sha,observer_sha256=observer_sha,stage_sha256=stage_sha,
            native_stages=native_stages,observer_stage=observer_stage,native_executor=observer['native_executor'],
            independent_root_native_execution_credit=False),
        native_or_original_or_game_executed_by_this_audit=False,HeapCreate_executed=False,GetVersionExA_executed=False,
        host_handle_created=False,heap_initialized=False,selector_return_modelled=True,selector_RET_executed_by_this_audit=False,
        source_initializer_RET_executed=False,original_attach_proved=False,root_full_causal_model_audited=False,
        whole_M4_complete=False,source_commands=commands+heap_commands,initial_dependency_check=initial,
        final_dependency_check=verify_manifest(files),elapsed_seconds=(time.perf_counter_ns()-started)/1e9,
        files=dict(sorted(files.items())))
    path = out/'report.json'
    publish_bytes(path,(json.dumps(report,indent=2)+'\n').encode())
    add(path)
    publish_bytes(out/'pins.json',(json.dumps(dict(files=dict(sorted(files.items()))),indent=2)+'\n').encode())
    print(json.dumps(dict(passed=True,schema=report['schema'],report_sha256=sha(path),pins_sha256=sha(out/'pins.json'),
        rows=48,phases=40,metadata_sets=metadata_pairs,unused_records=unused_records,
        static_stack_controls=12,static_response_controls=12,comparisons=checks,current_native_proof_bound=True)))


if __name__ == '__main__':
    main(*sys.argv[1:])
