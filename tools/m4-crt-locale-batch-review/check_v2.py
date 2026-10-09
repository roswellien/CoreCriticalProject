"""Finite independent raw whole-locale/argv, native ownership and rich ABI review."""
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import time
import traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import normalized, verify_manifest
from paths import publish_bytes, workspace_path
from stages import verify_stage
from transport import DirectSet, read, need

PHASES = {'writer-before', 'writer-after', 'entry-before-invoke', 'entry-after-stop',
          'locale-batch-before', 'locale-static-locks-returned', 'locale-default-returned',
          'locale-mainargs-before', 'locale-parser-sizing-returned', 'locale-parser-output-before',
          'locale-parser-output-returned', 'locale-builder-returned', 'locale-batch-cleaned', 'final', 'retry-after'}
FORWARDS = {'HeapAlloc': 'RtlAllocateHeap', 'InitializeCriticalSection': 'RtlInitializeCriticalSection',
            'EnterCriticalSection': 'RtlEnterCriticalSection', 'LeaveCriticalSection': 'RtlLeaveCriticalSection',
            'DeleteCriticalSection': 'RtlDeleteCriticalSection'}
EXPORT_CACHE = {}

def records(raw, fmt):
    need(len(raw) % struct.calcsize(fmt) == 0, 'Exact complete raw ledger record extent')
    return list(struct.iter_unpack(fmt, raw))

def hardware(b, prefix, boundary, metrics):
    a = b.data(prefix + boundary + '-host-before.bin'); z = b.data(prefix + boundary + '-host-after.bin')
    need(len(a) == len(z) == 544, 'Full direct host FX+ENV extent')
    need(a[512:540] == z[512:540], 'Unchanged strict complete legacy ENV28')
    need(any(a[524:540]) and struct.unpack_from('<H', a, 520)[0] != 0xffff,
         'Actual nonzero legacy pointer/opcode and active x87 stack witness')
    need(a[:5] == z[:5] and a[24:28] == z[24:28], 'Unchanged strict CW/SW/FTW/MXCSR')
    need(struct.unpack_from('<H', a, 0)[0] == 0xa7f and struct.unpack_from('<I', a, 24)[0] == 0x5fa5 and a[4] != 0,
         'Actively loaded rich host control fixture')
    for i in range(8):
        need(a[32+16*i:42+16*i] == z[32+16*i:42+16*i], 'Unchanged strict each physical raw80')
    for i in range(6, 16):
        need(a[160+16*i:176+16*i] == z[160+16*i:176+16*i], 'Unchanged strict nonvolatile XMM6..15')
    e0, e1, f0, f1 = b.words(prefix+boundary+'-host-abi.bin', 4, 'Q')
    need(e0 == e1 and (f0 ^ f1) & 0x400 == 0, 'Caller LastError and ABI direction flag preserved')
    metrics['hardware_pairs'] += 1; metrics['strict_hardware_domain_gates'] += 24

def identity(b, name, pin, metadata_after_bin=False):
    v = b.words(name+'.bin', 11, 'Q')
    address, named, owner, owner_named, base, size, allocation, state, kind, protect, allocation_protect = v
    need(address == named == owner_named and owner == allocation and base <= address < base+size
         and state == 0x1000 and kind == 0x1000000 and not protect & 0x101 and protect & 0xf0,
         'Actual full-width named target executable image and owner identity')
    metadata_name = name+'.bin' if metadata_after_bin else name
    path = b.data(metadata_name+'-module-path.bin').decode('utf-16-le').split('\0', 1)[0]
    digest = b.data(metadata_name+'-module-sha.bin').decode('ascii'); need(len(digest) == 64, 'Actual native owner digest extent')
    pin(path, digest)
    return address, owner, path, digest

def export(path, name):
    key = str(path), name
    if key in EXPORT_CACHE: return EXPORT_CACHE[key]
    raw = path.read_bytes()
    u16 = lambda p: struct.unpack_from('<H', raw, p)[0]
    u32 = lambda p: struct.unpack_from('<I', raw, p)[0]
    need(u16(0) == 0x5a4d, 'Physical native module DOS identity'); pe = u32(60); opt = pe+24
    need(u32(pe) == 0x4550 and u16(pe+4) == 0x8664 and u16(opt) == 0x20b, 'Physical native module AMD64 PE identity')
    directory, length = u32(opt+112), u32(opt+116)
    sections = [opt+u16(pe+20)+40*i for i in range(u16(pe+6))]
    def at(rva, n=1):
        hits = [u32(s+20)+rva-u32(s+12) for s in sections if u32(s+12) <= rva and rva+n <= u32(s+12)+u32(s+16)]
        need(len(hits) == 1 and hits[0]+n <= len(raw), 'Unique bounded physical export RVA'); return hits[0]
    def text(rva):
        start = at(rva); end = raw.find(b'\0', start, min(len(raw), start+4096))
        need(end >= start, 'Terminated physical export string'); return raw[start:end].decode('ascii')
    e = at(directory, 40); functions, names, ordinals = u32(e+28), u32(e+32), u32(e+36); matches = []
    for i in range(u32(e+24)):
        if text(u32(at(names+4*i, 4))) == name:
            ordinal = u16(at(ordinals+2*i, 2)); need(ordinal < u32(e+20), 'Physical named export ordinal')
            rva = u32(at(functions+4*ordinal, 4)); matches.append((rva, text(rva) if directory <= rva < directory+length else ''))
    need(len(matches) == 1, 'Unique physical named export'); EXPORT_CACHE[key] = matches[0]; return matches[0]

def export_proof(raw, ident, requested, pin):
    need(len(raw) == 4624, 'Separate finite full-width PE forwarding witness extent')
    version, named_module, target, named, owner, owner_named = struct.unpack_from('<6Q', raw)
    text = lambda offset, size: raw[offset:offset+size].split(b'\0', 1)[0].decode('ascii')
    wanted, forward, alias = text(48, 32), text(80, 256), text(336, 64)
    named_sha, owner_sha = raw[400:464].decode('ascii'), raw[464:528].decode('ascii')
    named_path = raw[528:2576].decode('utf-16-le').split('\0', 1)[0]
    owner_path = raw[2576:4624].decode('utf-16-le').split('\0', 1)[0]
    need(version == 1 and wanted == requested and target == named == owner_named == ident[0]
         and owner == ident[1] and owner_path == ident[2] and owner_sha == ident[3], 'Immutable named/owner/API association')
    named_file = pin(named_path, named_sha); owner_file = pin(owner_path, owner_sha)
    rva, physical_forward = export(named_file, requested)
    need(physical_forward == forward, 'Actual physical forwarder text')
    if forward:
        need(requested in FORWARDS and forward == 'NTDLL.'+FORWARDS[requested] and alias == FORWARDS[requested],
             'Only five exact admitted allocator/CS forwarding chains')
    else:
        need(alias == requested and named_module == owner and named_module+rva == target, 'Exact direct named native export RVA')
    owner_rva, owner_forward = export(owner_file, alias)
    need(not owner_forward and owner+owner_rva == target, 'Actual direct owner alias RVA resolves full target')

def cstring(raw, start, end):
    need(0 <= start < end <= len(raw), 'Requested bounded argv character pointer')
    stop = raw.find(b'\0', start, end); need(stop >= start, 'Argv string terminates within exact requested character extent')
    return raw[start:stop]

def parse_original_commandline(raw):
    """Independent finite original CRT quote/backslash rules, including special argv[0]."""
    need(raw.endswith(b'\0') and b'\0' not in raw[:-1], 'Actual single NUL-inclusive process command line')
    text = raw[:-1]; pos = 0; first = bytearray(); quoted = False
    while pos < len(text):
        c = text[pos]
        if c == 34: quoted = not quoted; pos += 1; continue
        if not quoted and c in (9, 32): break
        first.append(c); pos += 1
    args = [bytes(first)]
    while True:
        while pos < len(text) and text[pos] in (9, 32): pos += 1
        if pos == len(text): return args
        arg = bytearray(); quoted = False
        while pos < len(text):
            slash = 0
            while pos < len(text) and text[pos] == 92: slash += 1; pos += 1
            copy = True
            if pos < len(text) and text[pos] == 34:
                if slash % 2 == 0:
                    if quoted and pos+1 < len(text) and text[pos+1] == 34: pos += 1
                    else: copy = False; quoted = not quoted
                slash //= 2
            arg.extend(b'\\'*slash)
            if pos == len(text) or (not quoted and text[pos] in (9, 32)): break
            if copy: arg.append(text[pos])
            pos += 1
        args.append(bytes(arg))

def api_rows(b, root, summary, contracts, pin, metrics):
    source = records(b.data(root+'locale-source-accesses.bin'), '<IIQII')
    transports = records(b.data(root+'locale-api-transports.bin'), '<IIQII')
    need(len(source) == summary[16] and len(transports) == summary[17], 'Complete counted source and actual output transport ledgers')
    api_reads = records(b.data(root+'heap-api-accesses.bin'), '<5I'); active_reads = [a for a in api_reads if any(a)]
    need(active_reads[:2] == [(0x780039d0, 0x20001848, 0x780039d6, 4, 0), (0x78003a2b, 0x20000618, 0x78003a31, 4, 0)],
         'Two genuine carried prefix API-return reads')
    transport_cursor = 0; returned = []; actual = []; cleanup_started = False
    for n in range(summary[18]):
        stem = root+f'locale-api-{n}'
        a = b.words(stem+'-witness.bin', 32, 'Q')
        need(a[0:2] == (1, n) and not a[28] and a[31] in (0, 1), 'Exact indexed typed source/research API record')
        if a[31]:
            cleanup_started = True; need(a[2] == a[5] == a[6] == a[7] == 0 and a[14:16] == (1, 1) and a[8] == 1,
                 'Measured research lifecycle completion is distinct from source stdcall/void return')
            requested = {0x7802e040: 'DeleteCriticalSection', 0x7802e048: 'LeaveCriticalSection', 0x7802e090: 'HeapFree'}[a[3]]
            metrics['actual_research_cleanup_APIs'] += 1
        else:
            need(not cleanup_started and a[2] in contracts, 'Source API invocation precedes all research cleanup')
            slot, raw, argc, requested, tail = contracts[a[2]]
            need(a[3:5] == (slot, raw) and a[7] == argc and a[19] == tail and not any(a[20+argc:28]), 'Authentic original API name/IAT/raw/argc/tail association')
            if not tail:
                need((a[2], a[5], a[6], 4, 1) in source, 'Actual genuine source CALL committed its API return word')
            if a[15]: returned.append((a[2], a[5], a[6], 4, 0))
        before = identity(b, stem+'-identity-before', pin)
        export_proof(b.data(stem+'-export-before.bin'), before, requested, pin)
        if a[14]:
            after = identity(b, stem+'-identity-after', pin); need(before == after, 'Actual typed native export target remained identical')
            need(b.data(stem+'-export-before.bin') == b.data(stem+'-export-after.bin'), 'Actual complete immutable native forwarding witnesses')
            export_proof(b.data(stem+'-export-after.bin'), after, requested, pin)
            need(a[9] == a[11], 'Each actual native call restores caller LastError')
            metrics['actual_native_APIs'] += 1; actual.append((requested, a))
            if not a[31]: metrics['actual_source_APIs'] += 1
        else:
            need(not a[15] and not any(b.data(stem+'-export-after.bin')), 'Pre-API identity refusal has no fabricated native after witness')
            metrics['pre_API_refusals'] += 1
        if requested.endswith('CriticalSection') and not a[31]:
            need(a[16] > 0xffffffff and a[16] % 8 == 0 and a[17] == 40 and a[8] == 0 and a[13] == 0,
                 'Private native SDK40 object; original24 bytes are opaque input; void has no BOOL result')
            need(len(b.data(stem+'-input-0.bin')) == 24, 'Complete opaque source CS24 BEFORE input witness')
        buffers = records(b.data(stem+'-buffers.bin'), '<4I')
        need(all(direction in (1, 2) and pointer+size <= 0x100000000 and index < a[29] for pointer,size,direction,index in buffers),
             'Checked bounded typed native buffer descriptors')
        for pointer, size, direction, index in buffers:
            need(len(b.data(stem+f'-input-{index}.bin')) == size, 'Complete exact input/output-BEFORE buffer capacity')
        outputs = [(p, size) for p,size,direction,index in buffers if direction == 2]
        need(len(outputs) == a[30], 'Actual typed NLS output buffers and recorded capacities agree')
        committed = 0
        for k, (address, size) in enumerate(outputs):
            if not a[14]: continue
            data = b.data(stem+f'-output-{k}.bin'); need(len(data) == size, 'Actual native output captured for complete capacity, including BOOL0')
            count = min(size, max(0, a[13]-committed)); offset = 0
            while offset < count:
                width = min(4, count-offset, 4096-((address+offset)&4095))
                expected = (a[2], address+offset, int.from_bytes(data[offset:offset+width], 'little'), width, 1)
                need(transport_cursor < len(transports) and transports[transport_cursor] == expected,
                     'Each committed guest output is the genuine typed API witness byte sequence')
                transport_cursor += 1; offset += width
            committed += count
        if requested not in ('HeapAlloc',) and not requested.endswith('CriticalSection'):
            need(committed == a[13], 'Only actual declared NLS output commits receive transport credit')
        if requested == 'HeapAlloc' and a[14]:
            need(a[8] > 0xffffffff and 0x31000000 <= a[12] < 0x32000000 and a[20] == 0x48450001
                 and not a[21] and a[13] == a[22] and len(b.data(stem+'-output-0.bin')) == a[22], 'Real full native heap allocation and opaque disjoint guest backing')
            metrics['actual_HeapAlloc_calls'] += 1
        if requested == 'HeapFree' and a[14]:
            need(a[16] > 0xffffffff, 'Real full native pointer is used for actual free')
            metrics['actual_HeapFree_calls'] += 1
        if a[14] and requested in ('GetCPInfo','GetStringTypeW','GetStringTypeA','LCMapStringW','LCMapStringA','MultiByteToWideChar','WideCharToMultiByte','GetACP','GetOEMCP','GetModuleFileNameA'):
            metrics['actual_NLS_APIs'] += 1
            if not a[8]: metrics['actual_NLS_zero_returns'] += 1
    need(transport_cursor == len(transports), 'No extra fabricated native output commits')
    need(active_reads[2:] == returned and not any(any(x) for x in api_reads[len(active_reads):]), 'Each actual source stdcall return reads the genuine guest word exactly once; research cleanup adds none')
    metrics['actual_output_transport_records'] += len(transports); metrics['genuine_source_API_return_reads'] += len(returned)
    return source, actual

def semantics(b, selection, contracts, pin, metrics):
    need(b.data('COMPLETE') == b'COMPLETE' and 'INCOMPLETE' not in b.entries and 'FAILURE.txt' not in b.entries, 'Complete semantic corpus publication')
    totals = json.loads(b.data('review-controls.json'))
    need(totals['passed'] and totals['rows'] == 2 and totals['ordinary_rows'] == totals['independent_control_rows'] == 1
         and totals['selection'] == selection and totals['wrong_thread_units'] == 1 and totals['actual_GetCommandLineA_input']
         and not totals['API_response_injection'] and not totals['game_executed'], 'Exact two-row finite compiled fixture')
    metrics['compiled_assertions'] += totals['checks']; metrics['wrong_thread_denials'] += totals['wrong_thread_units']
    need({n.split('/')[0] for n in b.names()} == {'COMPLETE','review-controls.json','row-0','row-1'}, 'Exact finite compiled logical namespace')
    for scenario in (0, 1):
        p = f'row-{scenario}/'; mode = 1001+selection if scenario else 0
        result = json.loads(b.data(p+'result.json'))
        need(result['passed'] and result['scenario'] == scenario and result['control'] == mode
             and not result['full_CRT'] and not result['whole_M4_complete'] and not result['State_reseed_after_writer'], 'Actual row identity and finite completion scope')
        for name in ('writer','entry','cleanup','retry'): hardware(b, p, name, metrics)
        phases = {n[len(p):].split('/')[0] for n in b.names() if n.startswith(p) and '/' in n[len(p):]}
        need(phases <= PHASES and (scenario or phases == PHASES), 'Functional milestones only; every ordinary milestone actually captured')
        for phase in phases:
            root = p+phase+'/'
            need(len(b.data(root+'state.bin')) == 3504 and len(b.data(root+'fx.bin')) == 512
                 and len(b.data(root+'runtime-cpu.bin')) == len(b.data(root+'state-cpu.bin')) == 40 and len(b.data(root+'tib.bin')) == 20,
                 'Complete carried machine State/FX/CPU and minimal TIB observation')
            pages = b.words(root+'pages-index.bin', len(b.data(root+'pages-index.bin'))//4)
            need(len(pages) == 26 and len(set(pages)) == 26 and tuple(sorted(pages)) == pages
                 and b.words(root+'page-addresses.bin', 1, 'Q')[0] == 26, 'Exact complete26 source page inventory')
            for page in pages: need(len(b.data(root+f'page-{page}.bin')) == 4096, 'Full4096 mapped source page witness')
            if phase not in ('writer-before',):
                need(b.data(root+'fx.bin') == b.data(p+'writer-after/fx.bin'), 'Whole source unit carries complete actual writer Runtime FX')
            metrics['complete_milestones'] += 1; metrics['complete_page_observations'] += 26
        need(b.data(p+'writer-after/state.bin') == b.data(p+'entry-before-invoke/state.bin'), 'Binding setup borrows the complete actual writer State without reseed')
        for name in ('state.bin','fx.bin','runtime-cpu.bin','state-cpu.bin','tib.bin','pages-index.bin'):
            need(b.data(p+'entry-after-stop/'+name) == b.data(p+'final/'+name) == b.data(p+'retry-after/'+name), 'Cleanup and poisoned retry preserve carried complete machine observations')
        for page in b.words(p+'final/pages-index.bin', 26):
            need(b.data(p+f'entry-after-stop/page-{page}.bin') == b.data(p+f'final/page-{page}.bin') == b.data(p+f'retry-after/page-{page}.bin'), 'Cleanup/retry preserve complete mapped source pages')
        s = b.words(p+'final/locale-summary.bin', 32); live = b.words(p+'entry-after-stop/locale-summary.bin', 32)
        h = b.words(p+'final/heap-create-registry.bin', 18, 'Q'); q = b.words(p+'final/heap-query-witness.bin', 20, 'Q')
        own = b.words(p+'review-ownership.bin', 12, 'Q')
        need(s[:2] == (1, mode) and s[14:16] == (0, 0) and s[23] == 1 and s[30] == 0 and s[31] == bool(scenario), 'Private ownership is closed; failures never publish successful builder completion')
        need(h[4] > 0xffffffff and h[4] == h[16] and h[7] == 0 and h[8:11] == (1, 1, 1) and h[15] == 1,
             'Actual full private HANDLE survives until one successful dependency-ordered heap release')
        need(own == (1,selection,scenario,mode,scenario,1,1,1,live[9],live[12],live[18],1), 'Independent hook and private lifecycle witnesses agree')
        output = b.data(p+'final/heap-query-output.bin')
        need(q[:3] == (1,1,1) and q[3] != 0 and q[4] == 148 and q[11:18] == (37,1,1,1,1,1,0)
             and q[18] >= 5 and q[19] == 2 and len(output) == 148, 'Actual measured qualifying version result reaches authentic heap mode1')
        metrics['actual_heaps'] += 1; metrics['actual_heap_releases'] += 1; metrics['actual_queries'] += 1
        sections = records(b.data(p+'final/locale-critical-sections.bin'), '<16Q')
        allocations = records(b.data(p+'final/locale-allocations.bin'), '<16Q')
        need(len(sections) == s[12] == s[13] and len(allocations) == s[9] == s[10]+s[11], 'Actual private object counters match complete retained ownership records')
        need(len({x[10] for x in sections}) == len(sections), 'Each SDK critical section has unique stable full native storage')
        for x in sections:
            need(x[0] == 1 and x[3] == x[4] and x[5:10] == (0,1,1,1,1) and x[10] > 0xffffffff and x[10] % 8 == 0
                 and x[11] == 40 and not any(x[12:]), 'Every native SDK40 section is unowned and deleted once before heap cleanup')
        for x in allocations:
            need(x[0] == 1 and 0x31000000 <= x[1] < 0x32000000 and x[3] == ((x[2] or 1)+15)&~15
                 and x[4] == (x[3]+4095)&~4095 and x[7] > 0xffffffff and x[8:10] == (0,0)
                 and x[10]+x[11] == 1 and x[12] == h[4] and not any(x[13:]), 'Exact source rounding, disjoint backing, retained full native pointer and parent; each freed once')
        metrics['actual_CS_initialized'] += len(sections); metrics['actual_CS_deleted'] += len(sections)
        source, actual = api_rows(b, p+'final/', s, contracts, pin, metrics)
        # Cleanup records order must match private object releases, never a source API or allocator substitute.
        cleanup = [(name,a) for name,a in actual if a[31]]
        free_indices = [i for i,(name,a) in enumerate(cleanup) if name == 'HeapFree']
        delete_indices = [i for i,(name,a) in enumerate(cleanup) if name == 'DeleteCriticalSection']
        need(not free_indices or max(delete_indices) < min(free_indices), 'All critical sections deleted before any backing heap allocation is freed')
        need({a[16] for name,a in cleanup if name == 'HeapFree'} == {x[7] for x in allocations}, 'Exactly retained full allocation pointers supplied to research cleanup')
        need({a[16] for name,a in cleanup if name == 'DeleteCriticalSection'} == {x[10] for x in sections}, 'Exactly retained SDK objects supplied to actual DeleteCriticalSection')
        if not scenario:
            need(s[3:7] == (1,1,2,1) and result['builder_returned'] and result['fault_pc'] == 0x7800ba9e
                 and result['fault_target'] == 0x7800ba76 and live[14:16] == (2,5) and live[30] == 1,
                 'Whole static/default/two-pass argv builder returns genuinely while dependencies remain live')
            before = b.words(p+'locale-batch-before/state-cpu.bin', 10)
            for phase in ('locale-static-locks-returned','locale-default-returned'):
                cpu = b.words(p+phase+'/state-cpu.bin', 10)
                need(cpu[3:8] == before[3:8], 'Genuine external helper RET preserves caller nonvolatiles and ESP')
            need((0x78003c1c,0x2000185c,0xffffffc0,4,0) in source and (0x78003dda,0x2000185c,0xffffffb0,4,0) in source,
                 'Literal static/default RET instructions read genuine research caller words')
            need((0x7800bdfb,0x2000182c,0x7800bbfc,4,0) in source and (0x7800bdfb,0x2000182c,0x7800bc32,4,0) in source
                 and source[-1] == (0x7800bc47,0x20001858,0x7800ba9e,4,0), 'Both real parser RETs and genuine original builder RET are executed')
            cpu = b.words(p+'locale-builder-returned/state-cpu.bin', 10)
            need(cpu[9] == 0x7800ba9e and cpu[4] == 0x2000185c and cpu[3] == before[3] and cpu[6:8] == before[6:8], 'Original builder genuine RET ABI before unresolved __getmainargs continuation')
            ar = next(x for x in records(b.data(p+'locale-builder-returned/locale-allocations.bin'), '<16Q') if x[6] == 2)
            data = b.data(p+f'locale-builder-returned/locale-allocation-{ar[5]}-owned-page.bin')
            need(ar[1] == s[8] and ar[2] == s[26]+4*s[27] and s[27] == s[7]+1, 'Exact requested argv allocation equals sizing characters plus pointer slots')
            vectors = struct.unpack_from('<'+str(s[27])+'I', data)
            need(vectors[-1] == 0, 'Actual source null argv sentinel')
            strings = [cstring(data, v-ar[1], ar[2]) for v in vectors[:-1]]
            need(all(v >= ar[1]+4*s[27] for v in vectors[:-1]), 'Every argv pointer remains within exact requested character subrange')
            cmd = b.data(p+'locale-builder-returned/commandline-owned.bin')
            need(cmd == b.data(p+'locale-builder-returned/commandline-host-bytes.bin') and len(cmd) == s[25], 'Measured genuine process command line equals owned immutable parser input')
            host = b.words(p+'locale-builder-returned/commandline-host-witness.bin', 3, 'Q')
            need(host[0] > 0xffffffff and host[1] == len(cmd) and host[2] > 0, 'Actual borrowed full host command-line pointer and readable-region witness')
            need(strings == parse_original_commandline(cmd) and len(strings) == s[7], 'Independent complete original quote/backslash parser outputs match real process command line')
            cp = b.words(p+'locale-builder-returned/commandline-progress.bin',24)
            need(cp[13] == cp[14] and cp[17:22] == (1,1,1,1,1) and not cp[23], 'Genuine command-line API called and carried, with caller LastError retained')
            need(identity(b,p+'locale-builder-returned/commandline-api-before',pin,True) == identity(b,p+'locale-builder-returned/commandline-api-after',pin,True), 'Actual unchanged executable GetCommandLineA target/owner identity')
            # Validate each executed parser output store against its separately bounded region.
            for pc,address,value,width,write in source:
                if write and 0x7800bc48 <= pc < 0x7800bdfc and 0x31000000 <= address < 0x32000000:
                    need((width == 4 and ar[1] <= address and address+4 <= ar[1]+4*s[27])
                         or (width == 1 and ar[1]+4*s[27] <= address and address+1 <= ar[1]+ar[2]), 'Each actual parser store respects vector/character requested subrange')
            metrics['ordinary_sequences'] += 1; metrics['actual_parser_passes'] += 2; metrics['genuine_builder_RETs'] += 1
        else:
            need(not result['builder_returned'] and not s[6] and s[31] and b.data(p+'final/locale-fault-reason.bin'), 'Selected causal failure never publishes ordinary completion')
            source_apis = [(name,a) for name,a in actual if not a[31]]
            if mode == 1001:
                need(source_apis[-1][0] == 'InitializeCriticalSection' and source_apis[-1][1][20] == 0x31000000 and not source_apis[-1][1][15], 'Fault occurs after actual lazy native initialization before source return/publication')
            if mode == 1002:
                need(source_apis[-1][0] == 'EnterCriticalSection' and source_apis[-1][1][20] == 0x31000000 and not source_apis[-1][1][15], 'Fault occurs after actual recursive-owned lazy Enter, before source return')
            if mode == 1003:
                a = next(a for name,a in source_apis if a[2] == 0x78003e29)
                need(a[14:16] == (1,0) and a[13] == 0 and not s[17], 'Read-only destination fails after actual CPINFO response with zero fabricated commits/return')
            if mode == 1004:
                a = next(b.words(p+f'final/locale-api-{i}-witness.bin',32,'Q') for i in range(s[18]) if b.words(p+f'final/locale-api-{i}-witness.bin',32,'Q')[2] == 0x78003e29)
                need(a[14:16] == (0,0) and a[13] == 0, 'Mutated IAT fails before actual GetCPInfo and before source return')
            if mode == 1005:
                need(s[5] == 1 and len(allocations) == 2 and not s[6], 'Read-only parser backing faults after real malloc and before second parser completion')
            if mode == 1006:
                need(s[5] == 2 and source[-1] == (0x7800bc47,0x20001858,0x7800ba9e,4,0) and not s[6], 'Terminal observer fault retains genuine RET effects and marks failed before completion publication')
                metrics['control_genuine_builder_RETs'] += 1
            metrics['independent_control_sequences'] += 1

def main(native_path, native_sha, directory):
    start = time.perf_counter(); out = workspace_path(directory, reports=True)
    need(out.parent == ROOT/'reports/m4-crt-locale-batch-review' and not out.exists(), 'Fresh independent raw checker namespace'); out.mkdir(parents=True)
    native = read(native_path); need(sha_file(native_path) == native_sha and native['passed'] and native['native_scenarios'] == 24 and not native['native_rerun'], 'Exact frozen24-row actual native receipt')
    files = dict(native['files']); passed = False; closure = None
    metrics = {key:0 for key in ('hardware_pairs','strict_hardware_domain_gates','compiled_assertions','wrong_thread_denials',
        'complete_milestones','complete_page_observations','actual_heaps','actual_heap_releases','actual_queries',
        'actual_CS_initialized','actual_CS_deleted','actual_HeapAlloc_calls','actual_HeapFree_calls','actual_native_APIs',
        'actual_source_APIs','actual_research_cleanup_APIs','actual_NLS_APIs','actual_NLS_zero_returns','pre_API_refusals',
        'actual_output_transport_records','genuine_source_API_return_reads','ordinary_sequences','independent_control_sequences',
        'actual_parser_passes','genuine_builder_RETs','control_genuine_builder_RETs')}
    def pin(path, expected=None):
        path = Path(path).absolute(); actual = sha_file(path); need(expected is None or actual == expected, 'Current literal independent check dependency')
        key = normalized(str(path)); need(key not in files or files[key] == actual, 'Conflict-free immutable current dependency'); files[key] = actual; return path
    try:
        for p in (native_path, __file__, Path(__file__).parent/'transport.py', sys.executable): pin(p)
        build = read(pin(native['build_path'], native['build_sha256'])); fixture = Path(build['fixture_report']).parent
        ops = pin(fixture/'locale_batch_operations.inc').read_text()
        need(ops.count('call=[&,wide]') == 2 and 'call=[&](){if(wide)' not in ops
             and 'call=[&](){return static_cast<unsigned>(wide ?' not in ops,
             'Both deferred native typed dispatch branches capture their block-local selector by value')
        contract = pin(fixture/'source_contract.inc').read_text().split('constexpr SourceApi original_apis[]{',1)[1].split('};',1)[0]
        contracts = {}
        for site,slot,raw,argc,name,tail in re.findall(r'\{(0x[0-9a-f]+|\d+),(0x[0-9a-f]+|\d+),(0x[0-9a-f]+|\d+),(\d+),"([^"]+)",(\d+)\}',contract):
            contracts[int(site,0)] = (int(slot,0),int(raw,0),int(argc),name,int(tail))
        need(len(contracts) == 29, 'Complete recovered named source API contract plus two genuine allocator imports')
        for level in ('O0','O2'):
            invocations = native['levels'][level]['invocations']; need(len(invocations) == 6, 'Six actual supplementary command-line selections per level')
            for selection,info in enumerate(invocations):
                need(info['selection'] == selection and info['argv'][0] == build['workers'][level] and info['argv'][7] == str(selection), 'Actual compiled worker and process selection association')
                verify_stage(info['native_stage'], info['native_stage_sha256']); pin(info['inventory_path'],info['inventory_sha256'])
                b = DirectSet(info['transport_manifest'], pin)
                try:
                    need(sha_file(b.path) == info['transport_sha256'] and read(info['inventory_path'])['files'] == dict(sorted(b.records.items())), 'Actual strict compact archive equals externally pinned complete logical union')
                    semantics(b, selection, contracts, pin, metrics)
                finally: b.close()
        need(metrics['hardware_pairs'] == 96 and metrics['ordinary_sequences'] == metrics['independent_control_sequences'] == 12
             and metrics['wrong_thread_denials'] == 12, 'Exact actual finite independent scenario/ABI counts')
        closure = verify_manifest(files); passed = True
    except BaseException:
        publish_bytes(out/'failure.txt',traceback.format_exc().encode()); raise
    finally:
        report = dict(passed=passed,native_path=str(Path(native_path).absolute()),native_sha256=native_sha,
            build_path=native['build_path'],build_sha256=native['build_sha256'],metrics=metrics,files=files,current_physical_closure=closure,
            native_rerun=False,game_launched=False,original_executed=False,API_response_injection=False,
            full_CRT_complete=False,whole_M4_complete=False,foreign_Binding_destruction_claimed=False,
            partial_NLS_output_transport_claimed=False,volatile_XMM0_5_equality_claimed=False,
            source_instruction_model_claimed=False,scope='Independent compiled functional milestones, typed API outputs, ownership, parser bounds and strict rich host ABI; full literal source modeling is separate',
            elapsed_seconds=time.perf_counter()-start)
        publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
        print(json.dumps({k:v for k,v in report.items() if k != 'files'}))

if __name__ == '__main__': main(*sys.argv[1:])
