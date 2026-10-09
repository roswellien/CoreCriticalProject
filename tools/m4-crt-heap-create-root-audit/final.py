"""Final independent machine/OS-witness audit; no native/API execution here."""
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
from stages import verify_stage

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
EXECUTION_SHA = 'bbff62b849ca9c92368e83c781918cab434df2ef17a8ee6534d1fdcf53662a02'
OBSERVER_SHA = 'b0f9d688733d6c42a172dd7e9a8bce58d88033eca33c08e5724618511ee4b6c5'
STAGE_SHA = '336b917fba26fca4ef13f132755faaa20f4113610595ceafabbee5ad3fd3ca74'


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
    execution_path = add(ROOT/'reports/m4-crt-heap-create/execution-r1/report.json',EXECUTION_SHA)
    observer_path = add(ROOT/'reports/m4-crt-heap-create-root/observe-r3/report.json',OBSERVER_SHA)
    stage_path = add(ROOT/'reports/m4-crt-heap-create-root/observe-stage-r3/stage.json',STAGE_SHA)
    execution,observer = read(execution_path),read(observer_path)
    need(execution['passed'] and execution['native_stages_completed'] == 2 and execution['native_executed_by_author'],
         'Both actual delegated native executions')
    need(observer['passed'] and observer['execution_sha256'] == EXECUTION_SHA
         and observer['original_BEFORE_ordinary_sequences'] == 48 and observer['root_full_causal_model_sequences'] == 0
         and observer['independently_executed_by_root'] is False and observer['AFTER_machine_state_used_as_seed'] is False
         and observer['author_expected_model_imported'] is False and observer['original_x86_API_internals_equivalence'] is False,
         'Exact current root ordinary observation and bounded credit')
    for receipt in (execution,observer):
        for category in ('files','sources','source_files','tools','libraries','entry_objects','compiler_read_headers','artifacts','input_files'):
            for path,digest in receipt.get(category,{}).items():
                add(path,digest)
    for receipt_path in (execution_path,observer_path):
        pins_path = receipt_path.parent/'pins.json'
        if pins_path.exists():
            add(pins_path)
            for path,digest in read(pins_path)['files'].items():
                add(path,digest)
    add(core/'before.py',BEFORE_SHA)
    add(core/'prefix.py',PREFIX_SHA)
    for path in (Path(__file__),Path(__file__).with_name('README.md'),Path(sys.executable),
                 core/'consumer.py',core/'draft.py',ROOT/'tools/m4-pipeline/manifests.py',
                 ROOT/'tools/m4-pipeline/paths.py',ROOT/'tools/m4-pipeline/capture_bundle.py'):
        add(path)
    add(Path(__file__).with_name('README-final.md'))
    add(Path(__file__).with_name('audit.py'))
    draft_audit_path = add(BASE/'draft-r1/report.json','5e598ea90886137db18d10de7942df68ccac9715e79463d49b33d7ab08f4b04e')
    draft_audit_pins = add(BASE/'draft-r1/pins.json','8e1db2564c65ce82c612e25fa29afba2561cd19b24cf320691ffe2339f089005')
    for path,digest in read(draft_audit_pins)['files'].items():
        add(path,digest)
    native_stages = []
    for level in ('O0','O2'):
        for name in ('native_stage','pack_stage'):
            path = add(Path(execution['levels'][level][name])/'stage.json')
            verified = verify_stage(path.parent,sha(path))
            need(verified['recorded_stage_passed'],'Current successful native/pack stage')
            native_stages.append(verified)
    observer_stage = verify_stage(stage_path.parent,STAGE_SHA)
    need(observer_stage['recorded_stage_passed'],'Current successful frozen root observer stage')
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
    native_rows,unused_records,phase_metadata_pairs = 0,0,0
    export_cache,API_identity_evidence = {},[]

    def eq(actual,expected,why):
        nonlocal checks
        checks += 1
        need(actual == expected,why)

    def named_export(path,digest,name):
        key = (normalized(str(path)),digest)
        if key not in export_cache:
            data = Path(path).read_bytes()
            need(hashlib.sha256(data).hexdigest() == digest,'Exact current native API owner file bytes')
            u16 = lambda offset:struct.unpack_from('<H',data,offset)[0]
            u32 = lambda offset:struct.unpack_from('<I',data,offset)[0]
            pe = u32(0x3c)
            need(data[:2] == b'MZ' and data[pe:pe+4] == b'PE\0\0' and u16(pe+4) == 0x8664,
                 'Actual API owner is x64 PE')
            opt = pe+24
            need(u16(opt) == 0x20b,'Actual API owner PE32+ header')
            sections = []
            for index in range(u16(pe+6)):
                offset = opt+u16(pe+20)+index*40
                virtual,rva,raw,file_offset = struct.unpack_from('<4I',data,offset+8)
                need(file_offset+raw <= len(data),'API owner section raw bounds')
                sections.append((rva,raw,file_offset))
            def at(rva,count=1):
                for start,length,offset in sections:
                    if start <= rva and rva+count <= start+length:
                        return offset+rva-start
                raise ValueError('Exact native API export raw RVA bounds')
            directory,length = struct.unpack_from('<2I',data,opt+112)
            offset = at(directory,40)
            count,names,functions,name_table,ordinals = struct.unpack_from('<5I',data,offset+20)
            exports = {}
            for index in range(names):
                name_rva = u32(at(name_table+index*4,4))
                name_offset = at(name_rva)
                end = data.index(0,name_offset,min(name_offset+4096,len(data)))
                text = data[name_offset:end].decode('ascii')
                ordinal = u16(at(ordinals+index*2,2))
                need(ordinal < count,'API owner export ordinal index')
                function_rva = u32(at(functions+ordinal*4,4))
                exports[text] = (function_rva,directory <= function_rva < directory+length)
            export_cache[key] = (exports,u32(opt+56))
        exports,image_size = export_cache[key]
        need(name in exports and not exports[name][1],'Actual function owner direct named export')
        return exports[name][0],image_size

    def API_identity(row,stem,name):
        before_data = (row/(stem+'-api-before.bin')).read_bytes()
        eq((row/(stem+'-api-after.bin')).read_bytes(),before_data,'Actual named API identity remains equal before/after')
        need(len(before_data) == 2184,'Complete typed native API identity')
        target,named,owner,owner_named = struct.unpack_from('<4Q',before_data)
        base,size,allocation,allocation_state,image_type,protection,reserved = struct.unpack_from('<3Q4I',before_data,32)
        need(target != 0 and owner != 0 and target == named == owner_named and owner == allocation
             and allocation <= base <= target < base+size <= 2**64,
             'Nonzero real named API and nonwrapping committed owner range')
        need(allocation_state == 0x1000 and image_type == 0x1000000 and protection&0xf0 and not protection&0x101,
             'Actual committed executable native API image')
        digest = before_data[72:136].decode('ascii')
        text = before_data[136:].decode('utf-16-le')
        filename,separator,tail = text.partition('\0')
        need(separator and filename and all(char == '\0' for char in tail),'Complete terminated/padded native owner path')
        path = add(Path(filename),digest)
        function_rva,image_size = named_export(path,digest,name)
        eq(target,owner+function_rva,'Independent on-disk native owner named export/RVA association '+name)
        need(owner <= target < owner+image_size <= 2**64,'Named actual API address within owner image size')
        evidence = dict(name=name,target=target,owner=owner,path=str(path),sha256=digest,named_export_RVA=function_rva)
        if evidence not in API_identity_evidence:
            API_identity_evidence.append(evidence)
        return evidence

    def OS_witness(row):
        job_data = (row/'heap-create-job.bin').read_bytes()
        need(len(job_data) == 128,'Complete immutable ordinary heap-create job')
        job = struct.unpack('<32I',job_data)
        eq(job[:22],(0,0x20001858,0x20001860,10,1,6,2,10,0,0x780039e3,0x78003a0c,
                        1,0,1,1,1,1,1,1,1,0,1),'Actual source/API/cleanup bounded job lifecycle')
        eq(job[22],job[23],'Outer native caller LastError restored')
        eq(job[24:],(0x7800183c,0x780039bf,0x7800183e,0x78001843,0x78003a0c,0x780039e3,18,84),
           'Actual immutable source identity/frame job metadata')
        w_data,r_data = (row/'heap-create-witness.bin').read_bytes(),(row/'heap-create-registry.bin').read_bytes()
        need(len(w_data) == 128 and len(r_data) == 144,'Complete typed full-width host witness/registry')
        w,r = struct.unpack('<16Q',w_data),struct.unpack('<18Q',r_data)
        eq(w[:6],(1,0,1,0,4096,0),'Actual noninjected named HeapCreate request')
        need(w[6] != 0 and w[6] != TOKEN and w[7] == TOKEN and w[11] == w[6],
             'Real full-width handle distinct from opaque guest token; registration preserves exact handle')
        eq((w[8],w[10]),(job[22],job[22]),'Inner actual API caller LastError restored')
        eq(w[12:],(0x20001848,0x780039d6,0x20001858,0x780039d6),'Declared genuine checked stdcall frame/return')
        need(r[0] == 1 and r[1] != 0,'Real binding owner/generation schema')
        eq(r[2:11],(1,TOKEN,w[6],1,1,0,1,1,1),'Exactly one private acquisition, registration and real successful destruction')
        eq(r[12:],(1,0,0,1,w[6],0),'One actual cleanup, exact full destruction input, no skip/rollback/duplicate/denial')
        need(w[9] <= 0xffffffff and r[11] <= 0xffffffff,'Actual unconstrained DWORD API/cleanup error words')
        create = API_identity(row,'heap-create','HeapCreate')
        destroy = API_identity(row,'heap-destroy','HeapDestroy')
        return dict(token=TOKEN,handle=w[6],owner=r[1],witness=w,registry=r,create=create,destroy=destroy)

    def ownership_phase(tag,actual):
        w,r = actual['witness'],actual['registry']
        if not tag.startswith('heap-create-') and tag not in ('entry-after-fault','retry-after'):
            return {'heap-create-witness.bin':bytes(128),'heap-create-registry.bin':bytes(144)}
        if tag in ('heap-create-before','heap-create-projected','heap-create-provider-before','heap-create-api-before'):
            return {'heap-create-witness.bin':bytes(128),
                'heap-create-registry.bin':struct.pack('<18Q',1,actual['owner'],1,*([0]*15))}
        if tag in ('heap-create-api-return-before','heap-create-api-returned','heap-create-published','heap-create-mode-before'):
            live = (1,actual['owner'],1,TOKEN,actual['handle'],1,1,1,1,*([0]*9))
            return {'heap-create-witness.bin':struct.pack('<16Q',*w),'heap-create-registry.bin':struct.pack('<18Q',*live)}
        need(tag in ('heap-create-after','entry-after-fault','retry-after'),'Exact terminal closed ownership phase')
        return {'heap-create-witness.bin':struct.pack('<16Q',*w),'heap-create-registry.bin':struct.pack('<18Q',*r)}

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
            identity = execution['levels'][level]
            add(identity['bundle'],identity['bundle_sha256'])
            reader = stack.enter_context(CaptureBundle(identity['bundle'],identity['bundle_sha256']))
            need(len(reader.names()) == identity['logical_files'] and reader.read_bytes('COMPLETE') == b'COMPLETE',
                 'Complete hash-bound current native archive; only BEFORE input/query bytes seed machine expectations')
            need({name.split('/')[0] for name in reader.names()} == {'COMPLETE','units'}|{'row-'+str(index) for index in range(36)},
                 'Exact complete current archive top-level inventory')
            for index in range(36):
                request = json.loads(reader.read_bytes('row-'+str(index)+'/result.json'),object_pairs_hook=unique_object)
                need(request['passed'] and request['scenario'] == index and request['control'] == (0 if index < 24 else index+97),
                     'Exact all36 declared current requests; causal model credit remains zero')
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
                actual = OS_witness(row)
                derived = compare(entry,seam,actual['token'])
                all_phases = dict(earlier,**derived['phases'])
                terminal = derived['phases']['heap-create-after']
                all_phases['entry-after-fault'] = terminal
                all_phases['retry-after'] = terminal
                tags = {name.split('/')[1] for name in row.inventory if name.startswith(row.name+'/') and name.count('/') == 1}
                eq(tags,set(all_phases),'Exact all31 current checkpoint inventory')
                eq(len(all_phases),31,'Exactly31 independent machine and ownership phases')
                for tag,values in all_phases.items():
                    expected_files = dict(values,**ownership_phase(tag,actual))
                    eq(row.inventory[row.name+'/'+tag],set(expected_files),'Exact complete current checkpoint file inventory '+tag)
                    eq({name:(row/tag/name).read_bytes() for name in expected_files},expected_files,
                       'Every current State/FX/CPU18page/source/W/R byte '+tag)
                    phase_metadata_pairs += 1
                access_bytes = b''.join(struct.pack('<5I',*item) for item in derived['ledger'])
                eq((row/'heap-create-accesses.bin').read_bytes(),access_bytes+bytes(640-len(access_bytes)),
                   'Actual complete independent ten-source-access ledger and zero tail')
                return_bytes = struct.pack('<5I',*derived['API_return_access'])
                eq((row/'heap-create-api-accesses.bin').read_bytes(),return_bytes+bytes(160-len(return_bytes)),
                   'Actual distinct finite-API-return read ledger and zero tail')
                events = ((1,0x7800183c,0x20001860,0),(2,0x7800183e,0x780039bf,0x78001843),
                          (3,0x780039d0,0x7802e0a8,0x3461e),(4,0x780039d0,0x20001848,0x780039d6),
                          (5,0x780039d8,PAGE,TOKEN),(6,0x780039e3,0x78003a0c,0x780039e8))
                event_bytes = b''.join(struct.pack('<4I',*item) for item in events)
                eq((row/'heap-create-events.bin').read_bytes(),event_bytes+bytes(128-len(event_bytes)),
                   'Actual source CALL/API-return/publication event ledger')
                eq((row/'heap-create-scheduler.bin').read_bytes(),struct.pack('<8I',*derived['scheduler']),
                   'Actual EIP-only scheduling metadata; zero host guest stores')
                eq((row/'heap-create-undefined.bin').read_bytes(),struct.pack('<8I',0x780039bf,0x780039d6,*([0]*6)),
                   'Actual two exact source-site compiled AF representatives')
                evidence = OLD.evidence(entry)
                evidence['mainargs-job.bin'] = struct.pack('<20I',M.SLOT,M.RAW,*([0]*13),1,0,0,0x780039e3,0x78003a0c)
                evidence['mainargs-events.bin'],evidence['mainargs-accesses.bin'] = bytes(256),bytes(1280)
                for name,value in evidence.items():
                    captured = (row/name).read_bytes()
                    eq(json.loads(captured,object_pairs_hook=unique_object) if name.endswith('.json') else captured,value,
                       'Complete carried prior-source and first-fault ledger '+name)
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
                }
                for name,value in unused.items():
                    eq((row/name).read_bytes(),value,'Exact constructed but unused older/later-service record '+name)
                    unused_records += 1
                for name in ('filename','commandline','parser','locale','heap'):
                    eq((row/(name+'-reason.txt')).read_text().strip(),'','No fabricated reason on inactive service '+name)
                for name in ('mainargs','heap-create'):
                    eq((row/(name+'-reason.txt')).read_text().strip(),'Required genuine CRT heap mode selector remains unresolved',
                       'Exact unresolved source-selector diagnostic')
                for name,reason in (('initterm',entry.init_reason),('control',entry.control_reason),('matherr','')):
                    eq((row/(name+'-reason.txt')).read_text().strip(),reason,'Carried prior source diagnostic')
                for actor in ('writer','entry'):
                    M.D.host((row/(actor+'-host-before.bin')).read_bytes(),(row/(actor+'-host-after.bin')).read_bytes())
                entry_job = (row/'entry-job.bin').read_bytes()
                need(len(entry_job) == 40 and entry_job[32:] == bytes(8),'Complete entry job without fixture callback')
                eq(struct.unpack_from('<3I',entry_job,20),(0,0x780039e3,0x78003a0c),'Actual unresolved translation fault metadata')
                current = json.loads((row/'result.json').read_bytes(),object_pairs_hook=unique_object)
                need(current['writer_complete'] and current['entry_executed'] and current['poisoned_retry']
                     and not current['State_reseed_after_writer'] and not current['full_CRT'] and not current['whole_M4_complete'],
                     'Actual bounded ordinary row execution and poisoned retry')
                eq((current['fault_reason'],current['fault_site'],current['fault_target']),(0,0x780039e3,0x78003a0c),
                   'Actual source-mode frontier typed fault')
                eq((current['source_events'],current['writer_events'],current['data_routes']),(len(entry.events),97,1),
                   'All carried ordinary event counts')
                root_files = set(evidence)|set(unused)|{'input.bin','writer-record.bin','writer-host-before.bin','writer-host-after.bin',
                    'entry-host-before.bin','entry-host-after.bin','entry-job.bin','result.json','matherr-reason.txt','control-reason.txt',
                    'initterm-reason.txt','mainargs-reason.txt','filename-reason.txt','commandline-reason.txt','parser-reason.txt',
                    'locale-reason.txt','heap-reason.txt','heap-create-reason.txt','heap-create-job.bin','heap-create-events.bin',
                    'heap-create-accesses.bin','heap-create-api-accesses.bin','heap-create-scheduler.bin','heap-create-undefined.bin',
                    'heap-create-witness.bin','heap-create-registry.bin','heap-create-api-before.bin','heap-create-api-after.bin',
                    'heap-destroy-api-before.bin','heap-destroy-api-after.bin'}
                eq(row.inventory[row.name],root_files,'Exact complete current ordinary root evidence inventory')
                native_rows += 1
                ordinary_rows.append(dict(level=level,index=index,token=TOKEN,source_PCs=13,source_accesses=10,
                    source_CALLs=3,separate_API_return_reads=1,State=3504,FX=512,RuntimeCPU=40,mappings=18,
                    prior_phases=20,new_phases=9,anticipated_native_phases=31,mode_frame=0x20001854,
                    host_guest_execution_stores=0,current_native_compared=True,
                    actual_full_host_handle=actual['handle'],actual_registry_owner=actual['owner'],
                    actual_host_private_heap_created_and_destroyed=True,ownership_metadata_phases=31))
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
    need(native_rows == 48 and phase_metadata_pairs == 1488 and unused_records == 912,'Complete ordinary native/metadata/inactive-record coverage')
    report = dict(schema='mw34-m4-heap-create-root-final-audit-v1',passed=True,
        scope='Independent full-original-BEFORE affine source and actual named OS ownership witness audit of all ordinary native HeapCreate continuation rows',
        source_report_sha256=SOURCE_SHA,root_draft_sha256=DRAFT_SHA,root_before_sha256=BEFORE_SHA,root_prefix_sha256=PREFIX_SHA,
        unimported_historical_root_draft_context=excluded_draft_context,
        root_draft_all_dependency_closure_claimed=False,root_model_dependency_closure_verified=True,
        ordinary_rows=48,rows=ordinary_rows,model_comparisons=checks,static_token_formula_controls=token_controls,
        preserved_draft_static_token_formula_controls=10,
        current_ordinary_native_rows_compared=native_rows,current_native_checkpoints_per_row=31,
        current_phase_machine_and_W_R_metadata_pairs_compared=phase_metadata_pairs,
        exact_unused_older_later_native_records_compared=unused_records,
        named_native_API_identity_and_direct_export_evidence=API_identity_evidence,
        full_frozen_mainargs_before_crosscheck=True,stopping_subclass_used_as_expected_seed=False,
        AFTER_machine_state_used_as_seed=False,permitted_API_witness='Original FDIV input/API query plus separately validated typed native heap API/ownership witness; no machine AFTER seeds',
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
        root_predicted_API_executed_flag_is_draft_hypothesis=False,
        actual_native_API_result_bound_to_full_width_registry=True,
        handle_publication_phase_PC=0x780039d8,publication_snapshot_at_source_write_before_PC_advance=True,
        raw_heap_page_only_source_handle_DWORD_changed=True,source_CALL_store_precedes_ESP_publication=True,
        source_IAT_read_precedes_API_CALL_return_store=True,source_return_bridge_read_precedes_State_publication=True,
        declared_AF_representatives=[dict(pc=0x780039bf,value=0),dict(pc=0x780039d6,value=0)],
        undefined_AF_universal_original_equivalence=False,
        new_phase_names=list(derived['phases']),anticipated_native_checkpoints_per_row=31,
        current_native_proof_bound=True,current_native_compared=True,
        final_root_proof=dict(execution_sha256=EXECUTION_SHA,observer_sha256=OBSERVER_SHA,stage_sha256=STAGE_SHA,
            native_stages=native_stages,observer_stage=observer_stage,native_executor=observer['native_executor'],
            independent_root_native_execution_credit=False),
        native_or_original_or_game_executed_by_this_audit=False,HeapCreate_executed=False,
        actual_named_host_HeapCreate_results_witnessed=48,actual_owned_host_HeapDestroy_successes_witnessed=48,
        host_handle_created_by_this_audit=False,heap_initialized=False,mode_selected=False,source_initializer_RET_executed=False,
        original_attach_proved=False,root_full_causal_model_audited=False,whole_M4_complete=False,
        source_commands=commands+heap_commands,initial_dependency_check=initial_check,
        final_dependency_check=verify_manifest(files),elapsed_seconds=(time.perf_counter_ns()-started)/1e9,
        files=dict(sorted(files.items())))
    report_path = out/'report.json'
    publish_bytes(report_path,(json.dumps(report,indent=2)+'\n').encode())
    add(report_path)
    publish_bytes(out/'pins.json',(json.dumps(dict(files=dict(sorted(files.items()))),indent=2)+'\n').encode())
    print(json.dumps(dict(passed=True,report_sha256=sha(report_path),pins_sha256=sha(out/'pins.json'),
        rows=48,comparisons=checks,current_native_proof_bound=True)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output',type=Path)
    main(parser.parse_args())
