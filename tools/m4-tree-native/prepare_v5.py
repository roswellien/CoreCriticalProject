"""Add literal tree dispatch and generation-bound admission; no acceptance credit."""
from pathlib import Path
import hashlib
import json
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASE = ROOT / 'reports/m4-lockit-native/preparation-r5'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def one(text, before, after):
    assert text.count(before) == 1, (before, text.count(before))
    return text.replace(before, after)


def main(lift_report, expected, name):
    lp = Path(lift_report).resolve()
    assert sha(lp) == expected
    lift = json.loads(lp.read_bytes())
    assert lift['passed']
    rp = ROOT / 'reports/m4-tree-source/recovery-r1/report.json'
    assert sha(rp) == '81efa236420aab06fb6ab63453c32fb3e1364dfdf8c268cd6e1cd815d81c20a4'
    recovery = json.loads(rp.read_bytes())
    assert recovery['passed']
    source = json.loads(Path(recovery['instructions_path']).read_bytes())
    assert sha(recovery['instructions_path']) == recovery['instructions_sha256']
    assert len(source['instructions']) == 613
    parent = json.loads((BASE / 'report.json').read_bytes())
    assert sha(BASE / 'report.json') == '965ea738333677c308749108b7f0b211772e89d4dd5e2ed14ea561cb63d0bdc1'
    out = ROOT / 'reports/m4-tree-native' / name
    assert not out.exists()
    out.mkdir(parents=True)
    pins = dict(parent['files'])
    pins[str(BASE / 'report.json')] = sha(BASE / 'report.json')
    for receipt in (recovery, lift):
        for filename, digest in receipt['files'].items():
            assert filename not in pins or pins[filename] == digest
            assert sha(filename) == digest
            pins[filename] = digest
    pins[str(rp)] = sha(rp)
    pins[str(lp)] = expected
    for path in BASE.iterdir():
        if path.suffix in ('.cpp', '.hpp', '.inc'):
            assert sha(path) == parent['files'][str(path.resolve())]
            (out / path.name).write_bytes(path.read_bytes())
    (out / 'tree_operations.inc').write_bytes((HERE / 'tree_operations_v5.inc').read_bytes())
    wrappers = ('instruction', 'source_spans', 'source_pages', 'generated_undefined_sites',
                'has_body', 'dispatch_body', 'registration_callback', 'fs_root',
                'fs_frame_read', 'fs_frame_install', 'fs_frame_restore', 'fs_frame_entry',
                'mfc_root_input')
    path = out / 'lockit_contract.inc'
    text = path.read_text()
    for fn in wrappers:
        text = re.sub(r'\b' + fn + r'\(', 'accepted124_' + fn + '(', text)
    path.write_text(text)
    registers = {r: i for i, r in enumerate(('', 'eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi',
                 'al', 'cl', 'dl', 'bl', 'ah', 'ch', 'dh', 'bh', 'ax', 'cx', 'dx', 'bx', 'sp', 'bp', 'si', 'di'))}

    def operand(row, index, op):
        bits = op.get('bits', 0) or next((o['bits'] for o in row['decoded_operands'] if o.get('bits')), 32)
        if op['kind'] == 'register':
            values = [1, bits // 8, registers[op['register']], 0, 0, 0, 1, 0, 0, 1]
        elif op['kind'] == 'immediate':
            values = [2, bits // 8, 0, 0, 0, 0, 1, 0, str(op['value'] & 0xffffffffffffffff) + 'ULL', 1]
        else:
            assert op['kind'] == 'memory'
            base = idx = 0
            scale = 1
            for term in op['terms']:
                if not base and term['scale'] == 1:
                    base = registers[term['register']]
                else:
                    idx, scale = registers[term['register']], term['scale']
            displacement = op['displacement']
            if displacement >= 2 ** 31:
                displacement -= 2 ** 32
            access = int(index in row['explicit_memory_reads']) + 2 * int(index in row['explicit_memory_writes'])
            values = [3, bits // 8, 0, int(op['segment'] == 'fs'), base, idx, scale, displacement, 0, access]
        return '{' + ','.join(map(str, values)) + '}'

    dynamic_report = ROOT / 'reports/m4-tree-source/dynamic-contracts-r1/report.json'
    assert sha(dynamic_report) == '9a44bbb1c6be884f166837457e7db2619a1045efb2fb27ac398665e578df49d3'
    dynamic = json.loads(dynamic_report.read_bytes())
    assert dynamic['passed']
    for filename, digest in dynamic['files'].items():
        assert sha(filename) == digest
        assert filename not in pins or pins[filename] == digest
        pins[filename] = digest
    pins[str(dynamic_report)] = sha(dynamic_report)
    normal = json.loads((dynamic_report.parent / 'normal-contracts.json').read_bytes())
    assert len(normal['owned_causal_order']) == 172 and len(normal['publications']) == 7
    assert len(normal['Lockit_call_order']) == 26
    lines = ['} // inherited anonymous namespace', 'namespace mw34::m4_crt_locale_batch {', 'namespace {',
             'constexpr unsigned tree_owner_sites[]{' + ','.join(str(r['CALL_pc']) for r in normal['owners']) + '};',
             'struct TreeAccess{unsigned pc,role,offset,width,value_role;bool writing;};constexpr TreeAccess tree_access_order[]{']
    for row in normal['owned_causal_order']:
        lines.append('{' + ','.join(str(row[k]) for k in ('pc', 'owner_role_index', 'offset', 'bytes')) + ',' +
                     ('UINT32_MAX' if row['value_owner_role_index'] is None else str(row['value_owner_role_index'])) + ',' + str(row['write']).lower() + '},')
    lines += ['};', 'struct TreePublication{unsigned pc,role,parent,offset,global;};constexpr TreePublication tree_publication_order[]{']
    for row in normal['publications']:
        lines.append('{' + ','.join(str(row[k]) if row[k] is not None else 'UINT32_MAX' for k in
                     ('pc', 'owner_role_index', 'parent_owner_role_index', 'parent_offset', 'static_publication')) + '},')
    lines += ['};', 'constexpr unsigned tree_lockit_order[]{' + ','.join(str(r['CALL_pc']) for r in normal['Lockit_call_order']) + '};',
             'constexpr unsigned tree_root=0x4b7f70;', 'constexpr SourceInstruction tree_instructions[]{']
    rows = sorted(source['instructions'], key=lambda r: r['pc'])
    for row in rows:
        ops = row['decoded_operands']
        assert len(ops) <= 3
        operands = [operand(row, i, o) for i, o in enumerate(ops)] + ['{}'] * (3 - len(ops))
        lines.append('{' + f'{row["pc"]},{row["width"]},{json.dumps(row["mnemonic"])},{{{{' +
                     ','.join(operands) + '}},' + f'{len(ops)},0' + '},')
    lines += ['};', 'const SourceInstruction*tree_instruction(unsigned pc)noexcept{auto i=std::lower_bound(std::begin(tree_instructions),std::end(tree_instructions),pc,[](const auto&r,unsigned p){return r.pc<p;});return i!=std::end(tree_instructions)&&i->pc==pc?i:nullptr;}',
              'struct TreeImport{unsigned pc,slot,raw,target,reg;};constexpr TreeImport tree_imports[]{']
    imports = json.loads((rp.parent / 'register-import-contracts.json').read_bytes())
    for row in imports:
        lines.append('{' + ','.join(map(str, (row['pc'], row['slot'], row['raw'], row['target'],
                     registers[row['definition_register']] if row['definition_register'] else 0))) + '},')
    lines += ['};', 'const TreeImport*tree_import(unsigned pc)noexcept{for(const auto&i:tree_imports)if(i.pc==pc)return &i;return nullptr;}',
              'struct TreeScratch{unsigned site,target,offset,lea;bool normal;};constexpr TreeScratch tree_scratches[]{']
    for row in source['Lockit_scratch_contracts']:
        offset = 24 if row['CALL_pc'] == 0x4badd0 else row['ECX_minus_target_entry_ESP'][0]
        ctor = 'ctor' in row['role']
        lea = row['source_LEA_pc'] or 0x4badcc
        lines.append('{' + ','.join(map(str, (row['CALL_pc'], 0x7810a290 if ctor else 0x7810a350,
                       offset, lea))) + ',' + str(row['expected_in_fixed_normal_root']).lower() + '},')
    lines += ['};', 'const TreeScratch*tree_scratch(unsigned pc)noexcept{for(const auto&i:tree_scratches)if(i.site==pc)return &i;return nullptr;}',
              'constexpr FsFrameSpec tree_frames[]{']
    for row in source['FS_frame_contracts']:
        lines.append('{' + ','.join(str(row[k]) for k in
                     ('entry', 'handler', 'read', 'install', 'saved_previous', 'restore', 'RET_pc')) + '},')
    lines += ['};', 'constexpr MfcRootInput tree_mfc_inputs[]{']
    for call in (0x4ba306, 0x4ba33c, 0x4bab32):
        lines.append('{' + f'{0x4b7f70},{call},24,0x60b2f8,0' + '},')
    lines += ['};', 'constexpr SourceSpan tree_spans[]{']
    spans = []
    for row in rows:
        raw = bytes.fromhex(row['bytes_hex'])
        if spans and spans[-1][0] + len(spans[-1][1]) == row['pc']:
            spans[-1][1].extend(raw)
        else:
            spans.append([row['pc'], bytearray(raw)])
    for address, data in spans:
        lines.append('{' + f'{address},{len(data)},5,"{hashlib.sha256(data).hexdigest()}"' + '},')
    lines += ['};', '}']
    for field in ('read', 'install', 'restore', 'entry'):
        lines.append(f'const FsFrameSpec*fs_frame_{field}(unsigned pc)noexcept{{for(const auto&i:tree_frames)if(i.{field}==pc)return &i;return accepted124_fs_frame_{field}(pc);}}')
    lines += ['const MfcRootInput*mfc_root_input(unsigned root,unsigned site)noexcept{if(root==tree_root)for(const auto&i:tree_mfc_inputs)if(i.call==site)return &i;return accepted124_mfc_root_input(root,site);}',
              'const SourceInstruction*instruction(unsigned pc)noexcept{auto i=tree_instruction(pc);return i?i:accepted124_instruction(pc);}',
              'std::span<const SourceSpan>source_spans()noexcept{static const auto all=[](){auto old=accepted124_source_spans();std::vector<SourceSpan>v(old.begin(),old.end());v.insert(v.end(),std::begin(tree_spans),std::end(tree_spans));return v;}();return all;}',
              'std::span<const SourcePage>source_pages()noexcept{return accepted124_source_pages();}',
              'bool fs_root(unsigned root)noexcept{return root==tree_root||accepted124_fs_root(root);}',
              'unsigned registration_callback(unsigned root)noexcept{return root==tree_root?0x4b7fa0:accepted124_registration_callback(root);}']
    # The source lane supplies exact symbols and literal objects; no guessed symbols.
    bodies = lift['source_bodies']
    dispatch = [(body['entry'], body['symbol'] + '_body') for body in bodies.values()]
    assert len(dispatch) == 8
    lines += ['extern "C" void*' + symbol + '(State*,unsigned,void*);' for _, symbol in dispatch]
    lines += ['bool has_body(unsigned pc)noexcept{switch(pc){'] + [f'case {pc}:return true;' for pc, _ in dispatch] + ['default:return accepted124_has_body(pc);}}']
    lines += ['void*dispatch_body(unsigned pc,State*s,void*p){switch(pc){'] + [f'case {pc}:return {symbol}(s,pc,p);' for pc, symbol in dispatch] + ['default:return accepted124_dispatch_body(pc,s,p);}}']
    callbacks_report = ROOT / 'reports/m4-tree-source/game-callbacks-r1/report.json'
    assert sha(callbacks_report) == 'ce3e5b579fe8ed9146e2383b3349c5932eaf20907ea7ada0ef8800612e793088'
    callback_receipt = json.loads(callbacks_report.read_bytes())
    assert callback_receipt['passed']
    for filename, digest in callback_receipt['files'].items():
        assert filename not in pins or pins[filename] == digest
        assert sha(filename) == digest
        pins[filename] = digest
    pins[str(callbacks_report)] = sha(callbacks_report)
    callbacks_path = callbacks_report.parent / 'callbacks.json'
    assert sha(callbacks_path) == 'c87fa650c12261710f58ee477cea39a570ed50cce1bcd34c49fb9239827fcee4'
    callbacks = json.loads(callbacks_path.read_bytes())['State_offsets_by_original_PC']
    added = [int(pc) for pc, offsets in callbacks.items() for _ in offsets]
    lines += ['std::span<const unsigned>generated_undefined_sites()noexcept{static const auto all=[](){auto b=accepted124_generated_undefined_sites();std::map<unsigned,unsigned>counts,added;std::vector<unsigned>v;constexpr unsigned n[]{' + ','.join(map(str, added)) + '};for(auto pc:b)++counts[pc];for(auto pc:n)++added[pc];for(auto[pc,num]:added)counts[pc]=std::max(counts[pc],num);for(auto[pc,num]:counts)for(unsigned k=0;k<num;++k)v.push_back(pc);return v;}();return all;}','}', 'namespace {']
    (out / 'tree_contract.inc').write_text('\n'.join(lines) + '\n')
    path = out / 'locale_batch.hpp'
    text = one(path.read_text(), 'bool research_standalone_{};unsigned registry_root_{};',
               'bool tree_started_{},tree_completed_{};unsigned tree_owner_cursor_{},tree_publication_cursor_{};std::vector<std::array<std::uint64_t,8>>tree_lockit_held_;std::vector<std::array<std::uint64_t,16>>tree_lockit_contexts_;void tree_enter();unsigned tree_role(unsigned);void tree_returned(unsigned);void tree_owner_before(unsigned,std::uint64_t,unsigned,bool);void tree_owner_after(unsigned,std::uint64_t,unsigned,bool);std::uint64_t tree_lockit_read(unsigned,std::uint64_t,unsigned);void tree_lockit_called(unsigned,unsigned,unsigned);void tree_lockit_returned(unsigned,unsigned);\n bool research_standalone_{};unsigned registry_root_{};')
    path.write_text(text)
    path = out / 'fs_operations.inc'
    text = one(path.read_text(), 'void Binding::fs_owner_before(unsigned address,std::uint64_t value,unsigned bytes,bool writing){',
               'void Binding::fs_owner_before(unsigned address,std::uint64_t value,unsigned bytes,bool writing){if(registry_root_==tree_root){tree_owner_before(address,value,bytes,writing);return;}')
    text = one(text, 'void Binding::fs_owner_after(unsigned address,std::uint64_t value,unsigned bytes,bool writing){',
               'void Binding::fs_owner_after(unsigned address,std::uint64_t value,unsigned bytes,bool writing){if(registry_root_==tree_root){tree_owner_after(address,value,bytes,writing);return;}')
    path.write_text(text)
    path = out / 'lockit_operations.inc'
    text = one(path.read_text(), 'std::uint64_t Binding::lockit_read(unsigned address,std::uint64_t value,unsigned width){',
               'std::uint64_t Binding::lockit_read(unsigned address,std::uint64_t value,unsigned width){if(registry_root_==tree_root)return tree_lockit_read(address,value,width);')
    text = one(text, 'void Binding::lockit_called(unsigned target,unsigned site,unsigned frame){',
               'void Binding::lockit_called(unsigned target,unsigned site,unsigned frame){if(registry_root_==tree_root&&(target==0x7810a290||target==0x7810a350)){lockit_guard();tree_lockit_called(target,site,frame);return;}')
    text = one(text, 'w[15]=native_apis_.size();', 'w[15]=native_apis_.size();tree_lockit_returned(entry,frame);')
    text = one(text, ' sink("lockit-imports.bin",', ' sink("tree-lockit-contexts.bin",std::as_bytes(std::span(tree_lockit_contexts_)),context);sink("tree-lockit-held.bin",std::as_bytes(std::span(tree_lockit_held_)),context);const std::array<std::uint64_t,8>tree_status{1,unsigned(tree_started_),unsigned(tree_completed_),tree_lockit_held_.size(),tree_lockit_contexts_.size(),85,tree_owner_cursor_,tree_publication_cursor_};sink("tree-status.bin",std::as_bytes(std::span(tree_status)),context);\n sink("lockit-imports.bin",')
    path.write_text(text)
    path = out / 'locale_batch_operations.inc'
    text = one(path.read_text(), 'live_allocations()>80', 'live_allocations()>85')
    text = one(text, 'calls_.pop_back();event(50,r.pc,target,r.address);', 'calls_.pop_back();tree_returned(f.entry);event(50,r.pc,target,r.address);')
    path.write_text(text + '\n#include "tree_operations.inc"\n')
    path = out / 'locale_batch_binding.inc'
    text = one(path.read_text(), 'void Binding::stable_hook(unsigned point,bool terminal,bool cleaning){', 'void Binding::stable_hook(unsigned point,bool terminal,bool cleaning){const auto tree_held=tree_lockit_held_;const auto tree_contexts=tree_lockit_contexts_;const auto tree_started=tree_started_;const auto tree_completed=tree_completed_;const auto tree_owner_cursor=tree_owner_cursor_;const auto tree_publication_cursor=tree_publication_cursor_;')
    text = one(text, 'hook(point);admit_current();', 'hook(point);admit_current();if(tree_held!=tree_lockit_held_||tree_contexts!=tree_lockit_contexts_||tree_started!=tree_started_||tree_completed!=tree_completed_||tree_owner_cursor!=tree_owner_cursor_||tree_publication_cursor!=tree_publication_cursor_)deny("Tree observer changed private scratch or invocation witnesses",state.gpr.rip.dword);')
    path.write_text(text)
    path = out / 'session_impl.inc'
    text = one(path.read_text(), 'binding->guard();binding->source_identity();binding->calls_.push_back({root,',
               'binding->tree_enter();binding->guard();binding->source_identity();binding->calls_.push_back({root,')
    text = one(text, 'try{capture("registry-replay-"+std::to_string(roots)+"-before");binding->external_source_call(root,marker);',
               'try{capture("registry-replay-"+std::to_string(roots)+"-before");binding->tree_enter();binding->external_source_call(root,marker);')
    path.write_text(text)
    path = out / 'registry_library.cpp'
    text = one(path.read_text(), '#include "lockit_contract.inc"', '#include "lockit_contract.inc"\n#include "tree_contract.inc"')
    existing = set(re.findall(r'extern "C" .+?(\w+)\(', text))
    bridges = {bridge for body in bodies.values() for bridge in body['bridges']}
    for symbol in sorted(bridges - existing):
        if symbol.endswith('_undefined_8'):
            text += '\nextern "C" unsigned char ' + symbol + '(){return mw34::m4_onexit::undefined();}\n'
        elif symbol.startswith('sub_') or '_direct_' in symbol:
            text += '\nextern "C" void*' + symbol + '(State*s,unsigned a,void*p){return mw34::m4_onexit::called(p,s,a);}\n'
        else:
            raise ValueError('Unexpected bridge ' + symbol)
    path.write_text(text)
    objects = dict(parent['entry_objects'])
    objects.update(lift['entry_objects'])
    pins[str(Path(__file__).resolve())] = sha(__file__)
    pins[str(HERE / 'tree_operations_v5.inc')] = sha(HERE / 'tree_operations_v5.inc')
    original_report = ROOT / 'reports/m4-tree-original/prefix-validation-r2/report.json'
    assert sha(original_report) == '58e023bb24afc474b164c454bc3591bf2cd476c70b3ce90607251ea67583a920'
    original = json.loads(original_report.read_bytes())
    assert original['passed'] and original['counts']['actual_allocations'] == 7
    for filename, digest in original['files'].items():
        assert sha(filename) == digest
        pins[filename] = digest
    pins[str(original_report)] = sha(original_report)
    for filename, digest in objects.items():
        assert sha(filename) == digest
        pins[filename] = digest
    for path in out.iterdir():
        if path.is_file():
            pins[str(path.resolve())] = sha(path)
    (out / 'pins.json').write_text(json.dumps({'files': pins}, indent=2) + '\n')
    result = parent | dict(scope='Unexecuted tree native preparation; fixed normal scratch and generation-bound owned accesses; original and independent admission pending',
        native_library=str(out / 'registry_library.cpp'), native_include=str(out), entry_objects=objects,
        source_lifts=str(lp), source_lifts_sha256=expected, new_roots=[0x4b7f70],
        live_owner_bound=85, owner_bound_expanded=True, owner_bound_evidence=str(original_report),
        owner_bound_derivation='Accepted124 peak78 plus seven genuine measured tree owners',
        current_import_FS_lifetime_bound=True, exact_live_scratch_LIFO=True,
        exact_owned_causal_accesses=172, exact_owned_role_tuples=135, exact_primary_publications=7,
        foreign_or_expired_required_owner_operand_denied=True,
        original_source_dynamic_contracts=str(dynamic_report),
        normal_branch_only=True, source_or_native_executed=False,
        initializer_credit=False, files=pins | {str(out / 'pins.json'): sha(out / 'pins.json')})
    (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': True, 'report': str(out / 'report.json'), 'sha256': sha(out / 'report.json')}))


if __name__ == '__main__':
    main(*sys.argv[1:])
