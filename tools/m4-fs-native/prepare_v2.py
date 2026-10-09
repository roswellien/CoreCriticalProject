"""Additive owned normal-FS and shared-list derivative of accepted103."""
from pathlib import Path
import hashlib, json, re, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
HOME = Path(__file__).parent
BASE = ROOT / 'reports/m4-mfc-native/preparation-r1'
SOURCE = ROOT / 'reports/m4-fs-source'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def js(p):
    return json.loads(Path(p).read_bytes())

def need(condition, message):
    if not condition:
        raise ValueError(message)

def main(name):
    out = ROOT / 'reports/m4-fs-native' / name
    need(re.fullmatch('preparation-r[1-9][0-9]*', name) and not out.exists(), 'Fresh FS derivative')
    pins = {}
    def pin(p, expected=None):
        p = Path(p).resolve()
        value = sha(p)
        need(expected is None or value == expected, 'Exact frozen physical input: ' + str(p))
        pins[str(p)] = value
        return p
    def receipt(p, expected):
        value = js(pin(p, expected))
        need(value['passed'], 'Successful immutable predecessor receipt')
        for q, digest in value['files'].items():
            pin(q, digest)
        return value
    acceptance = pin(ROOT / 'reports/m4-joint-startup103-root/acceptance-r1/report.json', '13cc2567f30f2dae2d12991a3a76aa6c953c70a49148dc4ed13df34837b14c7c')
    need(js(acceptance)['passed'], 'Accepted103 parent')
    base = receipt(BASE / 'report.json', '3a2a6a2b43c4cc38c305e8f6965e4a56254f9677415c67cbb40091919072817e')
    rec = receipt(SOURCE / 'recovery-r3/report.json', '17c7840c58bcdce2a82989d141f202cbb25540b6c29b4f314c06c0d1c2bf3a6b')
    game = receipt(SOURCE / 'lifts-r1/report.json', 'f5af3ee18fd942c5f58226b0ae98fca29d7bdc93877d7cfdd624a43cc0aa1ab8')
    attr = receipt(SOURCE / 'symbol-attribution-r1/report.json', '5399065e2f4b6b96da6513ae86d77f06257bbb1f2ff81afd42494652946f8769')
    callbacks = receipt(SOURCE / 'game-callbacks-r1/report.json', '7ab319107620d377406401ce555ebff6428101403b457213b48f1f998a5e88d4')
    allocation = receipt(SOURCE / 'allocation-interface-r1/report.json', 'f7440d694771cc39c662a9842f7673c0c97d63274505b41894e325bcfde48a9b')
    geometry = receipt(SOURCE / 'geometry-r1/report.json', 'ec2a0a1fa4e7b98cdb1c27a81e465da01a27ab8e380f4a72e6af3b714a88ae24')
    gi = js(pin(SOURCE / 'recovery-r3/instruction-contracts.json'))
    inputs = js(pin(SOURCE / 'allocation-interface-r1/allocation-inputs.json'))
    accesses = js(pin(SOURCE / 'allocation-interface-r1/shared-owner-accesses.json'))
    dispatch = js(pin(SOURCE / 'symbol-attribution-r1/physical-dispatch.json'))
    cb = js(pin(SOURCE / 'game-callbacks-r1/callbacks.json'))['State_offsets_by_original_PC']
    need(len(gi['roots']) == 6 and len(inputs) == 10 and len(dispatch) == 17, 'Exact six roots, ten allocations, seventeen new bodies')
    need(len({(r['root'], r['CALL_pc']) for r in inputs}) == 10, 'Distinct reached allocation tuples')
    out.mkdir(parents=True)
    for p in BASE.iterdir():
        if p.suffix in ('.cpp', '.hpp', '.inc'):
            (out / p.name).write_bytes(p.read_bytes())
    pin(__file__)
    pin(HOME / 'fs_operations.inc')
    (out / 'fs_operations.inc').write_bytes((HOME / 'fs_operations.inc').read_bytes())
    old = (out / 'mfc_contract.inc').read_text()
    wrappers = ('instruction', 'source_spans', 'source_pages', 'generated_undefined_sites', 'source_api_contracts', 'has_body', 'dispatch_body', 'registration_callback', 'mfc_root_input', 'mfc_callsite')
    for fn in wrappers:
        old = re.sub(r'\b' + fn + r'\(', 'accepted103_' + fn + '(', old)
    (out / 'mfc_contract.inc').write_text(old)
    rows = {r['pc']: r for r in gi['instructions']}
    regs = {r: i for i, r in enumerate(['', 'eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi', 'al', 'cl', 'dl', 'bl', 'ah', 'ch', 'dh', 'bh', 'ax', 'cx', 'dx', 'bx', 'sp', 'bp', 'si', 'di'])}
    def operand(r, i, x):
        kind = x['kind']
        bits = x.get('bits', 0) or next((v.get('bits', 0) for v in r['decoded_operands'] if v.get('bits', 0)), 32)
        if kind == 'register':
            return '{' + f'1,{bits//8},{regs[x["register"]]},0,0,0,1,0,0,1' + '}'
        if kind == 'immediate':
            return '{' + f'2,{bits//8},0,0,0,0,1,0,{x["value"]&0xffffffffffffffff}ULL,1' + '}'
        need(kind == 'memory', 'Exact integer/FS decoded operand')
        base_reg = index = 0
        scale = 1
        for term in x['terms']:
            if not base_reg and term['scale'] == 1:
                base_reg = regs[term['register']]
            else:
                index = regs[term['register']]
                scale = term['scale']
        displacement = x['displacement']
        if displacement >= 2**31:
            displacement -= 2**32
        access = int(i in r['explicit_memory_reads']) + 2 * int(i in r['explicit_memory_writes'])
        return '{' + f'3,{bits//8},0,{int(x["segment"]=="fs")},{base_reg},{index},{scale},{displacement},0,{access}' + '}'
    frame_specs = [
        (0x4e78d0, 0x5b986b, 0x4e78d7, 0x4e78de, 0x4e7997, 0x4e799f, 0x4e79aa),
        (0x48f290, 0x5b5233, 0x48f297, 0x48f29e, 0x48f353, 0x48f360, 0x48f36b),
        (0x4d48f0, 0x5b8538, 0x4d48f7, 0x4d48fe, 0x4d492a, 0x4d4948, 0x4d4953),
    ]
    lines = ['} // anonymous composition namespace', 'namespace mw34::m4_crt_locale_batch {', 'namespace {',
             'struct FsFrameSpec{unsigned entry,handler,read,install,saved,restore,ret;};', 'constexpr FsFrameSpec fs_frames[]{']
    lines += ['{' + ','.join(map(str, r)) + '},' for r in frame_specs]
    lines += ['};']
    for field in ('read', 'install', 'restore', 'entry'):
        lines.append(f'const FsFrameSpec*fs_frame_{field}(unsigned pc)noexcept{{for(const auto&i:fs_frames)if(i.{field}==pc)return &i;return nullptr;}}')
    lines += ['bool fs_root(unsigned root)noexcept{switch(root){' + ''.join('case ' + str(r['entry']) + ':return true;' for r in gi['roots']) + 'default:return false;}}',
              'struct FsInput{unsigned root,call,request,object,publication,publication_pc,owner_root,owner_call,offset;};', 'constexpr FsInput fs_inputs[]{']
    for r in inputs:
        owner = r['publication_owner'] or {}
        values = [r[k] for k in ('root', 'CALL_pc', 'requested_size', 'object', 'publication', 'publication_PC')] + [owner.get('root', 0), owner.get('CALL_pc', 0), owner.get('offset', 0)]
        lines.append('{' + ','.join(map(str, values)) + '},')
    lines += ['};', 'const FsInput*fs_input(unsigned root,unsigned site)noexcept{for(const auto&i:fs_inputs)if(i.root==root&&i.call==site)return &i;return nullptr;}',
              'constexpr MfcRootInput fs_mfc_inputs[]{']
    for r in inputs:
        lines.append('{' + ','.join(str(r[k]) for k in ('root', 'CALL_pc', 'requested_size', 'object')) + ',0},')
    lines += ['};', 'struct FsOwnedAccess{unsigned root,pc,write,bytes,owner_root,owner_call,offset;};', 'constexpr FsOwnedAccess fs_owned_accesses[]{']
    for r in accesses:
        lines.append('{' + ','.join(str(int(r[k])) for k in ('root', 'pc', 'write', 'bytes', 'owner_root', 'owner_CALL_pc', 'owner_offset')) + '},')
    lines += ['};', 'constexpr SourceInstruction fs_instructions[]{']
    for pc, r in sorted(rows.items()):
        ops = r['decoded_operands']
        need(len(ops) <= 3, 'Finite original operands')
        rep = {None: 0, 'rep': 1, 'repe': 2, 'repz': 2, 'repne': 3, 'repnz': 3}.get(r.get('repeat'), 0)
        lines.append('{' + f'{pc},{r["width"]},{json.dumps(r["mnemonic"])},{{{{' + ','.join([operand(r, i, x) for i, x in enumerate(ops)] + ['{}'] * (3-len(ops))) + '}},' + f'{len(ops)},{rep}' + '},')
    spans = []
    raw = bytearray()
    start = end = None
    for pc, r in sorted(rows.items()):
        if start is not None and pc != end:
            spans.append((start, end, bytes(raw)))
            start = None
            raw = bytearray()
        if start is None:
            start = pc
        raw.extend(bytes.fromhex(r['bytes_hex']))
        end = pc + r['width']
    if start is not None:
        spans.append((start, end, bytes(raw)))
    lines += ['};', 'constexpr SourceSpan fs_spans[]{'] + ['{' + f'{a},{b-a},5,"{hashlib.sha256(raw).hexdigest()}"' + '},' for a, b, raw in spans] + ['};', '}']
    pages = {int(p): v for p, v in base['source_pages'].items()}
    lines += [
        'const MfcRootInput*mfc_root_input(unsigned root,unsigned site)noexcept{for(const auto&i:fs_mfc_inputs)if(i.root==root&&i.call==site)return &i;return accepted103_mfc_root_input(root,site);}',
        'bool mfc_callsite(unsigned pc)noexcept{return accepted103_mfc_callsite(pc);}',
        'const SourceInstruction*instruction(unsigned pc)noexcept{auto it=std::lower_bound(std::begin(fs_instructions),std::end(fs_instructions),pc,[](const auto&i,unsigned p){return i.pc<p;});return it!=std::end(fs_instructions)&&it->pc==pc?it:accepted103_instruction(pc);}',
        'std::span<const SourceSpan>source_spans()noexcept{static const auto all=[](){auto b=accepted103_source_spans();std::vector<SourceSpan>v(b.begin(),b.end());v.insert(v.end(),std::begin(fs_spans),std::end(fs_spans));return v;}();return all;}',
        'std::span<const SourcePage>source_pages()noexcept{return accepted103_source_pages();}',
        'std::span<const SourceApi>source_api_contracts()noexcept{return accepted103_source_api_contracts();}',
    ]
    counts = {int(pc): len(offsets) for pc, offsets in cb.items()}
    newlist = [pc for pc, count in sorted(counts.items()) for _ in range(count)]
    lines += ['std::span<const unsigned>generated_undefined_sites()noexcept{static const auto all=[](){auto b=accepted103_generated_undefined_sites();std::map<unsigned,unsigned>counts,added;std::vector<unsigned>v;constexpr unsigned n[]{' + ','.join(map(str, newlist)) + '};for(auto pc:b)++counts[pc];for(auto pc:n)++added[pc];for(auto[pc,num]:added)counts[pc]=std::max(counts[pc],num);for(auto[pc,num]:counts)for(unsigned k=0;k<num;++k)v.push_back(pc);return v;}();return all;}']
    lines += ['unsigned registration_callback(unsigned root)noexcept{switch(root){'] + ['case ' + str(r['entry']) + ':return ' + str(r['registration']['callback']) + ';' for r in gi['roots']] + ['default:return accepted103_registration_callback(root);}}']
    bodies = {}
    for d in dispatch:
        path = pin(d['host_LL'], d['host_sha256'])
        symbol = d['source_function_symbol']
        need(re.search(r'^define ptr @' + re.escape(symbol) + r'\(ptr(?: noalias)? %\w+, i32 %\w+, ptr(?: noalias)? %\w+\)', path.read_text(), re.M), 'Actual physical body ABI')
        for level, obj in d['objects'].items():
            need(obj['machine'] == 0x8664 and obj['symbol'] == symbol and sha(obj['path']) == obj['sha256'], 'Physical AMD64 symbol/object attribution')
        bodies[d['entry']] = symbol
    lines += ['extern "C" void*' + s + '(State*,unsigned,void*);' for s in sorted(set(bodies.values()))]
    lines += ['bool has_body(unsigned pc)noexcept{switch(pc){'] + ['case ' + str(pc) + ':return true;' for pc in sorted(bodies)] + ['default:return accepted103_has_body(pc);}}',
              'void*dispatch_body(unsigned pc,State*s,void*p){switch(pc){'] + ['case ' + str(pc) + ':return ' + s + '(s,pc,p);' for pc, s in sorted(bodies.items())] + ['default:return accepted103_dispatch_body(pc,s,p);}}', '}', 'namespace {']
    (out / 'fs_contract.inc').write_text('\n'.join(lines) + '\n')
    h = (out / 'locale_batch.hpp').read_text()
    needle = 'bool research_standalone_{};unsigned registry_root_{};'
    addon = '''struct FsRecord{std::array<std::uint64_t,32>words{};bool operator==(const FsRecord&)const=default;};
 std::vector<FsRecord>fs_records_;std::vector<unsigned>fs_active_;std::vector<std::array<std::uint64_t,16>>fs_events_,fs_owner_accesses_,fs_publications_,fs_graphs_,fs_record_bytes_;
 std::array<std::uint64_t,16>fs_native_input_{},fs_probe_{},fs_owner_probe_{};bool fs_admitted_{};
 void fs_admit();void fs_guard();void fs_hook(unsigned);void fs_event(unsigned,unsigned,unsigned,unsigned);void fs_read_before(unsigned,unsigned);void fs_read_after(unsigned,std::uint64_t,unsigned);void fs_write_before(unsigned,std::uint64_t,unsigned);void fs_write_after(unsigned,std::uint64_t,unsigned);void fs_returned(unsigned,unsigned,unsigned);void dump_fs(CaptureSink,void*)const;
 MfcRecord*fs_mfc_owner(unsigned,unsigned);void fs_owner_before(unsigned,std::uint64_t,unsigned,bool);void fs_owner_after(unsigned,std::uint64_t,unsigned,bool);bool fs_allowed_cross(unsigned,unsigned)const noexcept;void fs_graph_complete();
 '''
    need(h.count(needle) == 1, 'Exact additive private FS state insertion')
    (out / 'locale_batch.hpp').write_text(h.replace(needle, addon + needle))
    o = (out / 'locale_batch_operations.inc').read_text()
    o = o.replace('void Binding::batch_guard(){', 'void Binding::batch_guard(){\n fs_guard();', 1)
    needle = 'check_source_access(a,0,n,false);'
    need(o.count(needle) == 1, 'Actual read admission hook')
    o = o.replace(needle, needle + 'fs_read_before(a,n);fs_owner_before(a,0,n,false);')
    o = o.replace('source_access(a,v,n,false);', 'source_access(a,v,n,false);fs_read_after(a,v,n);fs_owner_after(a,v,n,false);', 1)
    o = o.replace('check_source_access(a,v,n,true);', 'check_source_access(a,v,n,true);fs_write_before(a,v,n);fs_owner_before(a,v,n,true);', 1)
    commit = 'expected_store(a,&v,n);source_access(a,v,n,true);'
    need(o.count(commit) == 1, 'Exact committed source write plus mirrored backing and access ledger')
    o = o.replace(commit, commit + 'fs_write_after(a,v,n);fs_owner_after(a,v,n,true);', 1)
    write_body = o[o.index('void Binding::write('):o.index('unsigned char Binding::batch_undefined(')]
    ordered = ['check_source_access(a,v,n,true);', 'fs_write_before(a,v,n);', 'runtime.memory().write(', commit, 'fs_write_after(a,v,n);']
    positions = [write_body.index(anchor) for anchor in ordered]
    need(positions == sorted(positions) and len(set(positions)) == len(positions), 'Literal checked store occurs before committed FS/owner after hooks')
    o = o.replace('mfc_returned(f.entry,state.gpr.rax.dword,f.frame);', 'mfc_returned(f.entry,state.gpr.rax.dword,f.frame);fs_returned(f.entry,f.frame,target);', 1)
    o += '\n#include "fs_operations.inc"\n'
    (out / 'locale_batch_operations.inc').write_text(o)
    m = (out / 'mfc_operations.inc').read_text()
    needle = 'record->words[2]!=registry_root_'
    need(m.count(needle) == 1, 'Exact old same-root ownership guard')
    m = m.replace(needle, '(record->words[2]!=registry_root_&&!fs_allowed_cross(address,bytes))')
    (out / 'mfc_operations.inc').write_text(m)
    contract = (out / 'registry_contract.inc').read_text()
    match = re.search(r'constexpr unsigned registry_game_pages\[\]\{([^}]*)\}', contract)
    need(match, 'Exact inherited observed game pages')
    gamepages = sorted(set(map(int, match[1].split(','))) | set(gi['source_data_pages']))
    contract = contract[:match.start(1)] + ','.join(map(str, gamepages)) + contract[match.end(1):]
    (out / 'registry_contract.inc').write_text(contract)
    c = (out / 'registry_library.cpp').read_text().replace('#include "mfc_contract.inc"', '#include "mfc_contract.inc"\n#include "fs_contract.inc"', 1)
    bridges = {b for record in game['source_bodies'].values() for b in record['bridges']}
    existing = set(re.findall(r'extern "C" .+?(\w+)\(', c))
    for symbol in sorted(bridges-existing):
        if symbol.endswith('_undefined_8'):
            c += '\nextern "C" unsigned char ' + symbol + '(){return mw34::m4_onexit::undefined();}\n'
        elif symbol.startswith('sub_') or '_direct_' in symbol:
            c += '\nextern "C" void*' + symbol + '(State*s,unsigned a,void*p){return mw34::m4_onexit::called(p,s,a);}\n'
        elif symbol.startswith('__remill_'):
            need(symbol in {'__remill_read_memory_32','__remill_write_memory_32','__remill_write_memory_8','__remill_write_memory_16','__remill_function_call','__remill_function_return','__remill_missing_block'}, 'Existing known bridge')
        else:
            raise ValueError('Unclassified FS bridge ' + symbol)
    (out / 'registry_library.cpp').write_text(c)
    s = (out / 'session_impl.inc').read_text()
    s = s.replace('binding->research_standalone_=true;', 'binding->fs_admit();binding->research_standalone_=true;', 1)
    s = s.replace('binding->dump_mfc(sink,user);', 'binding->dump_mfc(sink,user);binding->dump_fs(sink,user);', 1)
    s = s.replace('if(bootstrapped&&!failed){::project', 'if(bootstrapped&&!failed){require(binding->fs_active_.empty(),"Normal FS records restored before genuine source cleanup");::project', 1)
    s += '''
namespace mw34::m4_onexit {
std::vector<std::array<std::uint64_t,32>>Session::fs_witnesses()const{std::vector<std::array<std::uint64_t,32>>v;for(const auto&r:impl_->binding->fs_records_)v.push_back(r.words);return v;}
std::array<std::uint64_t,16>Session::fs_chain_probe()const noexcept{return impl_->binding->fs_probe_;}
std::array<std::uint64_t,16>Session::fs_owner_probe()const noexcept{return impl_->binding->fs_owner_probe_;}
}
'''
    (out / 'session_impl.inc').write_text(s)
    h = (out / 'session.hpp').read_text()
    needle = 'std::vector<std::array<std::uint64_t,32>>mfc_witnesses()const;'
    need(h.count(needle) == 1, 'Stable accepted Session API plus additive FS observation getters')
    h = h.replace(needle, 'std::vector<std::array<std::uint64_t,32>>fs_witnesses()const;std::array<std::uint64_t,16>fs_chain_probe()const noexcept;std::array<std::uint64_t,16>fs_owner_probe()const noexcept;\n ' + needle)
    (out / 'session.hpp').write_text(h)
    objects = dict(base['entry_objects'])
    objects.update(game['entry_objects'])
    for p, digest in objects.items():
        pin(p, digest)
    for p, digest in base['libraries'].items():
        pin(p, digest)
    interface = dict(schema='mw34-fs-native-interface-v1', frames=frame_specs, native_TIB_base=0x7ffde000, native_sentinel=0xffffffff,
        sentinel_provenance='Runtime-created owned virtual TIB, independent of original Windows host FS0', TIB_observation='Only exact five mapped ownership fields; no whole TIB-page admission',
        frame_words=['v','index','root','canonicalEntry','actualCallerSite','entryESP','returnPC','readPC','previousFS0','recordAddress','handler','initialScope','priorDepth','parentIndexPlus1','installPC','installed','savedReadPC','savedValue','restorePC','restored','finalRETpc','returned','headAfterRestore','actualCallEntry','FSbase','sentinel','actualScopeAtRestore','actualInstallPrevious','actualInstallHandler','actualInstallScope','actualRestorePrevious','actualRestoreHandler'],
        owner_words=['v','index','root','pc','address','width','actualValue','write','ownerCreationRoot','ownerCALL','ownedGuest','generation','fullNative','offset','MFCrecordIndex','sourceAccessCount'],
        hooks={80:'before genuine FS0 read',81:'before literal complete-record installation',82:'after actual FS0 install',83:'before exact saved-predecessor restore',84:'after committed FS0 restoration',85:'genuine RET after normal record restoration',86:'before precise owned-node write',87:'after committed precise owned-node write'},
        normal_new_allocations=10,normal_total_live_owners=62,normal_game_records=7,normal_graph_appends=5,cleanup='All45MFC objects genuinely source-freed through MFC825/CRTfree before16strings and registry, then actual HeapDestroy; exception handler/TLS paths remain refused')
    (out / 'fs-interface.json').write_text(json.dumps(interface, indent=2) + '\n')
    (out / 'fs-physical-dispatch.json').write_text(json.dumps(dispatch, indent=2) + '\n')
    files = dict(pins)
    for p in out.iterdir():
        if p.is_file():
            files[str(p.resolve())] = sha(p)
    report = dict(passed=True,schema='mw34-fs-native-preparation-v1',scope='Additive normal FS/shared-owner library and physical COFF closure only; native109 execution/review pending',
        parent_acceptance_sha256=sha(acceptance),parent_native_preparation_sha256=sha(BASE/'report.json'),entry_objects=objects,libraries=base['libraries'],source_pages=pages,game_pages=gamepages,
        native_library=str((out/'registry_library.cpp').resolve()),native_include=str(out.resolve()),new_roots=[r['entry'] for r in gi['roots']],all_selected_roots=[r['entry'] if isinstance(r,dict) else r for r in gi['selected_order']],
        new_game_bodies=17,provider_bodies_added=0,normal_new_allocations=10,normal_total_live_owners=62,native_executed=False,roots_admitted=0,accepted103_files_modified=False,
        resource_bounds=dict(liveAllocations=64,events=8192,typedAPIs=4096,sourceAccesses=200000,FsRecords=128,FsEvents=4096,FsOwnedAccesses=8192),files=files)
    (out/'pins.json').write_text(json.dumps(pins, sort_keys=True, indent=2)+'\n')
    report['files'][str((out/'pins.json').resolve())] = sha(out/'pins.json')
    (out/'report.json').write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print(json.dumps(dict(passed=True, report_sha256=sha(out/'report.json'), physical_objects=len(objects), new_game_bodies=17, new_allocations=10)))

if __name__ == '__main__':
    main(*sys.argv[1:])
