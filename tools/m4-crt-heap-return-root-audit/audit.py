"""Independent full startup BEFORE and affine heap-publication/RET model audit."""
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
BASE = ROOT/'reports/m4-crt-heap-return-root-audit'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle
from manifests import normalized, unique_object, verify_manifest
from paths import publish_bytes, workspace_path

SOURCE_SHA = 'c285ece7e08e2c152735629c48aae461d9f28d006895cf87e9f5157b23053684'
SOURCE_PINS_SHA = 'b2aac3bca2ba716faa2549235fda92c2ee5efadb8a50da1221217065c347fc0f'
ACCEPT_SHA = 'cedd67126afce1ec3392e8e0f8fec71f54823e58bc353055aee723203eef18d1'
DRAFT_SHA = '83227a68a6b5ae148552f09b5b39cffd5bd2a8a2f2f01c999e68be1049ba33e7'
BEFORE_SHA = '819ec625f266e99c1ce6c7bd2209e030a00a29dd283b060c3c61b5d8aea97ea6'
PREFIX_SHA = '9f1eafac2333c97cc5192b0681e57d3968269617a13a1b25c7e649eb5dee716e'
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

    source_path = add(ROOT/'reports/m4-crt-heap-return-recovery/recovery-r1/report.json',SOURCE_SHA)
    source_pins = add(source_path.with_name('pins.json'),SOURCE_PINS_SHA)
    return_source = read(source_path)
    need(return_source['passed'] and return_source['schema'] == 'mw34-m4-heap-return-static-recovery-v1','Exact sealed source contract')
    source = read(add(ROOT/'reports/m4-crt-heap-version-recovery/recovery-r1/report.json',
        '90565b98f9880fa49358c40d021967af700cc598c4f35da148469bad92372b5f'))
    for path,digest in read(source_pins)['files'].items():
        add(path,digest)
    accept_path = add(ROOT/'reports/m4-crt-heap-version-root/root-acceptance-r1/report.json',ACCEPT_SHA)
    accepted = read(accept_path)
    need(accepted['passed'],'Previous accepted native HeapCreate frontier')
    identity = accepted['receipts']['author_execution']
    previous_execution = read(add(identity['path'],identity['sha256']))
    draft_path = add(ROOT/'reports/m4-crt-heap-return-root/draft-r1/report.json',DRAFT_SHA)
    draft = read(draft_path)
    need(draft['passed'] and draft['ordinary_BEFORE_models']==48 and not draft['native_executed'],
         'Fresh source-only root draft')
    for path,digest in draft['files'].items():
        add(path,digest)
    core = ROOT/'tools/m4-crt-heap-return-root'
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
    for instruction in return_source['spans']['heap-after-selector']['instructions']:
        size,op,args = heap_program[instruction['pc']]
        need(size == instruction['width'] and op == instruction['mnemonic'] and
             ' '.join(', '.join(args).split()) == ' '.join(instruction['operands'].split()),
             'Every already-lifted provider continuation instruction agrees with fresh exact decode')

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

    def eq(actual,expected,why):
        nonlocal checks
        checks += 1
        need(actual == expected,why)

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
            # Independent explicit original continuation; no opcode interpreter
            # or root expected State reused. Both CMPs overwrite six defined flags.
            suffix.extend(return_source['qualifying_added_source_PCs'])
            setpc(0x780039e8)
            cmpflags(1,3)
            eq(tuple(current[o] for o,b in FLAGS if b != 10),(1,0,1,0,1,0),
               'Original first caller CMP1-3 defined arithmetic flags')
            setpc(0x780039eb)
            phases['heap-return-mode-store-before'] = stage(current,fx,cpu,memory)
            store(0x780039eb,PAGE+4,1)
            phases['heap-return-mode-store-after'] = stage(current,fx,cpu,memory)
            # JE39F0 is not taken. CMP1-2 makes JNE39F9 branch to3A08.
            setpc(0x780039f6)
            cmpflags(1,2)
            eq(tuple(current[o] for o,b in FLAGS if b != 10),(1,1,1,0,1,0),
               'Original final caller CMP1-2 defined arithmetic flags')
            setpc(0x78003a08)
            store(0x78003a08,P-12,1)
            setreg('esp',P-12)
            setpc(0x78003a0a)
            # Authenticated existing Remill IR publishes ESP before its POP read.
            setreg('esp',P-8)
            setreg('eax',fetch(0x78003a0a,P-12,1))
            setpc(0x78003a0b)
            phases['heap-return-initializer-return-before'] = stage(current,fx,cpu,memory)
            target = fetch(0x78003a0b,P-8,0x78001843)
            setpc(target)
            setreg('esp',P-4)
            phases['heap-return-initializer-return-after'] = stage(current,fx,cpu,memory)
            eq(struct.unpack_from('<I',memory[0x20001000],0x85c)[0],1,
               'Original cdecl argument stays on stack; fragment caller not run')
            terminal_EIP,terminal_ESP = target,P-4
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
            selector_returned=good,environment_reached=not good,terminal_EIP=terminal_EIP,terminal_ESP=terminal_ESP,
            initializer_RET=good,initializer_result=1 if good else None,heap_mode_value=1 if good else 0)
        need(len(phases) == (22 if good else 18) and len(transport) == 37,'Independent source phases and37DWORD transport closure')
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
        eq(set(actual['phases']),set(expected['phases']),'Complete independent qualifying22 or alternate18 phase schema')
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
        struct.pack_into('<I',raw_changed,4,expected['heap_mode_value'])
        eq(actual['memory'][PAGE],raw_changed,'Only authentic source handle and conditional mode DWORD effects')
        eq((actual['selector_returned'],actual['environment_reached'],actual['terminal_EIP'],actual['terminal_ESP']),
           (expected['selector_returned'],expected['environment_reached'],expected['terminal_EIP'],expected['terminal_ESP']),
           'Genuine initializer RET or next unresolved environment CALL')
        eq((actual['initializer_RET'],actual['initializer_result'],actual['heap_mode_value']),
           (expected['initializer_RET'],expected['initializer_result'],expected['heap_mode_value']),
           'Source-computed conditional initializer success and mode publication')
        need(actual['stack_probe_returned'] and not actual['query_executed'] and actual['query_response_applied'] and
             actual['heap_mode_published'] == expected['selector_returned'] and
             actual['initializer_RET'] == expected['selector_returned'] and not actual['heap_initialized'],
             'Hypothetical finite response and conditional source return only; no complete allocator claim')
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
                    (entry.mem,seam[2],'Full startup all21pages/aliases')):
                    eq(actual,wanted,why)
                need(entry.init_complete and not entry.init_failed and not entry.args_failed and not entry.args_used and
                     entry.args_accesses == [],'Healthy original seam before mainargs provider')
                eq(len(earlier),20,'Twenty preserved prior source phases')
                for tag,value in earlier.items():
                    eq(value,full_phases[tag],'Full original model prior phase '+tag)
                derived = compare(entry,seam,hypothetical_response(seam))
                rows.append(dict(level=level,index=index,source_PCs=59,source_accesses=35,source_CALLs=5,
                    genuine_source_RETs=3,separate_API_return_reads=2,separate_API_transport_DWORDs=37,
                    State=3504,FX=512,RuntimeCPU=40,mappings=21,
                    prior_phases=20,new_phases=22,anticipated_native_phases=44,
                    declared_A=derived['declared_A'],declared_B=derived['declared_B'],current_native_compared=False))
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
    report = dict(schema='mw34-m4-heap-return-root-model-audit-v1',passed=True,
        scope='Independent full-original-BEFORE/affine heap publication and initializer RET audit; hypothetical typed API responses only',
        source_report_sha256=SOURCE_SHA,source_pins_sha256=SOURCE_PINS_SHA,root_draft_sha256=DRAFT_SHA,
        root_before_sha256=BEFORE_SHA,root_prefix_sha256=PREFIX_SHA,ordinary_rows=48,rows=rows,
        model_comparisons=checks,static_declared_stack_formula_controls=controls,
        static_hypothetical_API_response_formula_controls=response_controls,
        full_frozen_mainargs_before_crosscheck=True,stopping_subclass_used_as_expected_seed=False,
        AFTER_machine_state_used_as_seed=False,permitted_original_API_witness='Original FDIV input/API-query only',
        author_expected_model_imported=False,independent_affine_source_ledger=True,
        whole_State_bytes=3504,whole_FX_bytes=512,whole_Runtime_CPU_bytes=40,captured_mappings=21,
        prior_mappings_preserved=20,new_raw_RX_cold_page=COLD_PAGE,
        new_raw_RX_cold_page_sha256=hashlib.sha256(raw_cold).hexdigest(),
        lower_stack_bytes_original_observed=False,original_stack_guard_growth_proved=False,
        TIB_and_Policy_stack_limit_changed=False,ordinary_lower_stack_initial_DWORD=0,
        semantic_aliases_preserved=True,semantic_aliases_counted_as_extra_mappings=False,
        qualifying_source_PCs=59,qualifying_source_accesses=35,qualifying_source_CALLs=5,
        genuine_source_probe_RET=1,genuine_source_selector_RET=1,genuine_source_initializer_RET=1,
        separate_API_return_reads=2,separate_declared_API_transport_DWORDs=37,
        new_compiled_guarded_bytes=0,new_guest_objects=0,preserved_guest_objects=38,
        reused_compiled_heap_bytes=84,reused_selector_probe_bytes=86,reused_version_branch_bytes=60,
        source_identity_executed_bytes=192,total_source_identity_bytes=2086,anticipated_native_checkpoints_per_row=44,
        host_scheduler_changes_only=['State.EIP'],host_guest_execution_stores=0,
        declared_old_API_return_changes_only=['State.EAX.low32','State.ESP.low32','State.EIP.low32'],
        old_API_execution_is_draft_hypothesis=True,original_x86_API_internals_equivalence=False,
        original_volatile_register_or_flag_equivalence=False,generic_Runtime_CPU_and_call_records_preserved=True,
        query_struct_bytes=148,query_pointer=0x200017b8,only_size_DWORD_initialized_by_source=True,
        query_input_copied_from_independent_BEFORE_source_prefix=True,
        hypothetical_API_response_is_native_witness=False,query_output_transport_is_declared_API_effect=True,
        qualifying_terminal_EIP=0x78001843,qualifying_terminal_ESP=0x2000185c,
        qualifying_computed_selector_result=1,qualifying_computed_initializer_result=1,
        heap_mode_global_publication=True,source_reads_before_TEST=True,
        source_CALL_store_precedes_ESP_publication=True,source_IAT_read_precedes_query_return_store=True,
        real_probe_relocated_PUSH_RET_verified=True,probe_RET_not_synthesized=True,
        declared_AF_representatives=[dict(pc=pc,value=0) for pc in (0x780039bf,0x780039d6,0x780058db,0x780058c5,0x78003a31)],
        prior_selector_flags_derived_from_CMP_measured_or_declared_major_minus5=True,
        final_qualifying_flags_derived_from_source_CMP_selector1_minus2=True,
        final_qualifying_six_arithmetic_flags=[1,1,1,0,1,0],
        source_mode_global_progress_is_actual_checked_store_only=True,
        source_success_PUSH_store_precedes_ESP_publication=True,
        source_success_POP_ESP_publication_precedes_checked_read=True,
        source_initializer_RET_checked_read_precedes_EIP_and_ESP_publication=True,
        cdecl_argument_present_at_terminal_ESP=True,post_initializer_fragment_caller_executed=False,
        source_initializer_return_modelled=True,
        alternate_flags_derived_from_exact_source_path=True,undefined_AF_universal_original_equivalence=False,
        new_phase_names=list(derived['phases']),current_native_proof_bound=False,current_native_compared=False,
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
        rows=48,static_stack_controls=12,static_response_controls=12,comparisons=checks,current_native_proof_bound=False)))


if __name__ == '__main__':
    main(sys.argv[1])
