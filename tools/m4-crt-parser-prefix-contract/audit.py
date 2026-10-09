"""Independent current source/IR/ABI/build/COFF audit; no native execution."""
import ctypes as C
import difflib
import hashlib
import json
import ntpath
import re
import struct
import subprocess
import sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
BASE = ROOT / 'reports/m4-crt-parser-prefix'
PREP = BASE / 'preparation-r3'
BUILD = BASE / 'build-r2'
OLD = ROOT / 'reports/m4-crt-commandline-carry/preparation-r5'
RECOVERY = ROOT / 'reports/m4-crt-mainargs/recovery-r3'
BUILD_SHA = '215cdc4fc04cbc2163250a1746f1a5d20411bc3f0a57f3680212682c1596654a'
PREP_SHA = 'fc0db6fbd06076f2bf3b4186e74c31e7216e87ed48f31d813a2673366d95ef01'
PREP_PINS_SHA = '5502f44033b0215da34b3542da40c00d0d52b56361a0f1c82d30b7307e9dcd41'
SOURCE_SHA = 'b372b4c114b8ecb170208ad508f2541c73262c3b44cfa2e7626e06a5be61fd8b'
sys.path.insert(0, str(ROOT / 'tools/analysis'))
from pe import PEImage


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def read(path):
    def unique(pairs):
        value = {}
        for k, v in pairs:
            need(k not in value, 'Unique JSON source association')
            value[k] = v
        return value
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique)


def key(path):
    return ntpath.normcase(ntpath.normpath(str(Path(path).absolute())))


def one(text, after, before):
    need(text.count(after) == 1, 'Exactly one independent inverse seam: ' + after[:80])
    return text.replace(after, before)


def inverse_composition(text):
    for a, b in (
        ('#include "carry.hpp"\n#include "parser.hpp"', '#include "carry.hpp"'),
        ('namespace cm=mw34::m4_crt_commandline_carry;\nnamespace pp=mw34::m4_crt_parser_prefix;',
         'namespace cm=mw34::m4_crt_commandline_carry;'),
        ('#include "carry_binding.inc"\n#include "parser_binding.inc"', '#include "carry_binding.inc"')):
        text = one(text, a, b)
    routes = ['return pp::current(p,a)->read32(a);', 'return pp::current(p,a)->read8(a);',
              'pp::current(p,a)->write32(a,v);return p;']
    for route in routes:
        text = one(text, 'if(pp::owner){' + route + '}', '')
    guard = 'if(pp::owner){pp::current(pp::owner,0)->unsupported(0,"Other bridge cannot use active parser owner");}'
    need(text.count(guard) == 19, 'All nineteen other ancestor bridges exclude active parser')
    text = text.replace(guard, '')
    added = 'extern "C" unsigned char mw34_mainargs_normal_parser_undefined_8()noexcept(false){return pp::current(pp::owner,0)->undefined();}\nextern "C" void*__remill_write_memory_8(void*p,unsigned a,unsigned char)noexcept(false){if(pp::owner)pp::current(p,a)->unsupported(a,"Parser output byte store outside measured prefix");throw std::runtime_error("Unreached parser byte store");}\n'
    return one(text, added, '')


def inverse_driver(text):
    text = one(text, 'namespace mw34::m4_crt_parser_prefix {void checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}}\n', '')
    evidence = [line for line in text.splitlines(True) if line.startswith('  std::array<unsigned,20>parser_job')]
    need(len(evidence) == 1, 'One additive complete parser POD/output line')
    for name in ('parser-job.bin', 'parser-accesses.bin', 'parser-events.bin', 'parser-undefined.bin', 'parser-reason.txt'):
        need(name in evidence[0], 'Exact declared parser diagnostic output ' + name)
    text = one(text, evidence[0], '')
    changes = [
        ('MW34_CRT_PARSER_PREFIX_NO_MAIN', 'MW34_CRT_COMMANDLINE_CARRY_NO_MAIN'),
        ('scenario+61', 'scenario+49'),
        ('pp::Binding parser(mainargs.context,commandline,provider,mode);', ''),
        ('pp::binding=&parser;pp::admitted_binding=&parser;', ''),
        ('entry_job.fault_pc==pp::stop&&entry_job.fault_target==pp::table+0x44',
         'entry_job.fault_pc==cm::parser_site&&entry_job.fault_target==cm::parser'),
        ('entry_job.fault_reason!=static_cast<unsigned>(FaultReason::unresolved_translation)||entry_job.fault_pc!=pp::stop||entry_job.fault_target!=pp::table+0x44',
         'entry_job.fault_pc!=cm::parser_site||entry_job.fault_target!=cm::parser'),
        ('"Literal builder consumes actual owned command line and enters real parser prefix"',
         '"Literal builder consumes actual owned command line then stops before parser body"'),
        ('   require(parser.failed&&parser.locale_reached&&parser.access_count==16&&parser.event_count==3&&parser.undefined_count==2&&parser.fault_pc==pp::stop&&parser.fault_address==pp::table+0x44,"Actual parser prefix stops before first uninitialized locale read");\n', ''),
        ('pp::binding=nullptr;pp::admitted_binding=nullptr;', '')]
    for a, b in changes:
        text = one(text, a, b)
    return text


def llvm_layouts(llvm):
    sys.path.insert(0, str(ROOT / 'tools/lifting'))
    from host_adapter import LLVM, HOST_LAYOUT
    api = LLVM(llvm / 'LLVM-C.dll')
    result = []
    for name, expected_symbol in (('normal_parser-guest.ll', 'sub_7800bc48'),
                                  ('normal_parser-host.ll', 'mw34_mainargs_normal_parser_body')):
        path = RECOVERY / name
        ctx = api.ContextCreate()
        module, buffer, error = C.c_void_p(), C.c_void_p(), C.c_void_p()
        data = None
        try:
            api.check(api.CreateMemoryBufferWithContentsOfFile(str(path).encode(), C.byref(buffer), C.byref(error)), error)
            api.check(api.ParseIRInContext(ctx, buffer, C.byref(module), C.byref(error)), error)
            api.check(api.VerifyModule(module, 2, C.byref(error)), error)
            data = api.CreateTargetData(api.GetDataLayoutStr(module))
            table = {}
            for typename in re.findall(r'^%([^ =]+) = type', path.read_text(), re.M):
                ty = api.GetTypeByName2(ctx, typename.encode())
                need(ty and not api.IsOpaqueStruct(ty), 'Actual complete named State ABI type')
                table[typename] = {'size': api.ABISizeOfType(data, ty), 'alignment': api.ABIAlignmentOfType(data, ty),
                    'offsets': [api.OffsetOfElement(data, ty, i) for i in range(api.CountStructElementTypes(ty))]}
            need(api.signature(api.GetNamedFunction(module, expected_symbol.encode())) == ('ptr', ['ptr', 'i32', 'ptr']),
                 'Actual State/GuestPC/opaque-token parser ABI')
            result.append({'pointer_bytes': api.PointerSize(data), 'types': table})
        finally:
            if data:
                api.DisposeTargetData(data)
            if module.value:
                api.DisposeModule(module)
            api.ContextDispose(ctx)
    need(result[0]['pointer_bytes'] == 4 and result[1]['pointer_bytes'] == 8 and
         result[0]['types'] == result[1]['types'] and result[1]['types']['struct.State']['size'] == 3504,
         'Every actual guest32/host64 State type layout agrees')
    need(f'target datalayout = "{HOST_LAYOUT}"' in (RECOVERY / 'normal_parser-host.ll').read_text(), 'Actual AMD64 host ABI data layout')
    return result


def main(directory):
    out = BASE / directory
    need(out.parent == BASE and directory.startswith('source-contract-') and not out.exists(), 'Fresh owned source audit output')
    pins = {}
    def bind(path, expected=None):
        path = Path(path).absolute()
        actual = sha(path)
        need(expected is None or actual == expected, 'Exact source/compiled association: ' + str(path))
        k = key(path)
        need(k not in pins or pins[k] == actual, 'Conflict-free current physical dependency')
        pins[k] = actual
        return actual
    bind(BUILD / 'build.json', BUILD_SHA)
    bind(PREP / 'pins.json', PREP_PINS_SHA)
    bind(PREP / 'report.json', PREP_SHA)
    manifest = read(BUILD / 'build.json')
    previous_path = ROOT / 'reports/m4-crt-commandline-carry/build-r6/build.json'
    bind(previous_path, '10969868ff59f5bd1c37b60065b2329d0649785ab3a5d48763696fe846759ce9')
    previous = read(previous_path)
    bind(ROOT / 'reports/m4-crt-commandline-carry/root-acceptance-r1/report.json',
         '156bb2f9b6faa0194c3801926963c700e99b278059afa8fb9717eb2bc0fb70f7')
    need(manifest['passed'] and key(manifest['preparation_path']) == key(PREP / 'report.json') and
         manifest['preparation_sha256'] == PREP_SHA, 'Exact passed source/build preparation association')
    for category in ('sources', 'tools', 'libraries', 'entry_objects', 'compiler_read_headers', 'artifacts'):
        for p, h in manifest[category].items():
            bind(p, h)
    for p, h in read(PREP / 'pins.json')['files'].items():
        bind(p, h)
    for p, h in manifest['sources'].items():
        bind(BUILD / 'sources' / Path(p).relative_to(ROOT), h)
    need(manifest['libraries'] == previous['libraries'] and len(manifest['libraries']) == 2, 'Two unchanged FDIV libraries')
    need(len(previous['entry_objects']) == 14 and all(manifest['entry_objects'].get(p) == h
         for p, h in previous['entry_objects'].items()), 'Fourteen unchanged prior guest COFF objects')
    new = {p: h for p, h in manifest['entry_objects'].items() if p not in previous['entry_objects']}
    need(set(map(key, new)) == {key(RECOVERY / ('normal_parser-' + level + '.obj')) for level in ('O0', 'O2')},
         'Exactly two pre-existing full literal parser COFF objects added')
    recovery = read(RECOVERY / 'report.json')
    bind(RECOVERY / 'report.json', 'ea623fb2d4bbad3e7636e8155eaafbc6ce6915e293fdd851e4f9eadbc2e0c038')
    parser = recovery['native']['normal_parser']
    need(parser['objects'] == read(PREP / 'report.json')['reused_parser_objects'], 'Exact original parser recovery objects')
    for row in parser['objects'].values():
        need(manifest['entry_objects'][row['path']] == row['sha256'], 'Original per-level parser object association')
    names = sorted(p.name for p in OLD.iterdir() if p.suffix in ('.cpp', '.hpp', '.inc'))
    need(len(names) == 18, 'Exact accepted carry source component inventory')
    changed = {'composition.cpp', 'carry_binding.inc', 'mainargs_binding.inc', 'observations.hpp', 'main_v2.inc'}
    unchanged, diffs = [], {}
    for name in names:
        bind(OLD / name)
        bind(PREP / (name + '.ancestor'))
        need((OLD / name).read_bytes() == (PREP / (name + '.ancestor')).read_bytes(), 'Exact frozen carry ancestor copy')
        if name not in changed:
            need((OLD / name).read_bytes() == (PREP / name).read_bytes(), 'Unchanged ancestor source: ' + name)
            unchanged.append(name)
        else:
            diffs[name] = ''.join(difflib.unified_diff((OLD / name).read_text().splitlines(True),
                (PREP / name).read_text().splitlines(True), name + '.ancestor', name))
    need(inverse_composition((PREP / 'composition.cpp').read_text()) == (OLD / 'composition.cpp').read_text(), 'Exact composition bridge/inclusion inverse')
    need(inverse_driver((PREP / 'main_v2.inc').read_text()) == (OLD / 'main_v2.inc').read_text(), 'Exact driver inverse; old seed/maps/source/runtime logic unchanged')
    delegate = 'if(!pp::binding||pp::binding!=pp::admitted_binding)context.deny("Exact admitted parser binding at real CALL required",parser,parser_site);if(&pp::binding->context!=&context)context.deny("Parser real CALL cannot use stale Context",parser,parser_site);pp::binding->enter(s,a,p);'
    previous_stop = 'first("Required actual command-line parser remains unresolved",parser,parser_site);context.first(reason,parser,parser_site);throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_translation,{parser_site},{parser},reason);'
    need(one((PREP / 'carry_binding.inc').read_text(), delegate, previous_stop) == (OLD / 'carry_binding.inc').read_text(),
         'One actual parser CALL delegate seam in otherwise unchanged command-line carry')
    need(one((PREP / 'mainargs_binding.inc').read_text(), '&&!pp::owner&&!mg::owner&&!nt::owner&&!ci::owner&&!mn::owner,"Exact exclusive mainargs service owner"',
        '&&!mg::owner&&!nt::owner&&!ci::owner&&!mn::owner,"Exact exclusive mainargs service owner"') == (OLD / 'mainargs_binding.inc').read_text(), 'One mainargs parser exclusion seam')
    observation = '{std::array<std::byte,436>b{};r.memory().read({pp::entry},b);fresh_output(phase/"parser-source.bin",b);}\n '
    need(one((PREP / 'observations.hpp').read_text(), observation, '') == (OLD / 'observations.hpp').read_text(), 'Exactly one full436B source observation')
    for name in ('parser.hpp', 'parser_binding.inc'):
        bind(ROOT / 'tools/m4-crt-parser-prefix' / name)
        need((PREP / name).read_bytes() == (ROOT / 'tools/m4-crt-parser-prefix' / name).read_bytes(), 'Exact authored/parser header preparation copy')
    bind(PREP / 'parser_binding.inc', '5e53a0d2ab4bd748359fc9da7009e961020c8069a2a4e6c60bfe72ed2f708b9a')
    provider = ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    bind(provider, '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    bind(ROOT / 'MW3/Mech3.exe', '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
    image = PEImage(provider.read_bytes())
    offset, _ = image.rva_range(0x7800bc48 - image.image_base, 436)
    source = image.data[offset:offset+436]
    need(source == (PREP / 'parser-original.bin').read_bytes() == (RECOVERY / 'normal_parser-source.bin').read_bytes()
         and hashlib.sha256(source).hexdigest() == SOURCE_SHA, 'Literal full436B source identity from exact staged provider')
    locale_path = ROOT / 'reports/m4-crt-locale-workahead/recovery-r2/report.json'
    bind(locale_path, 'cbccc6391f72121e2c9bda05b745beb6494a5e52cf9738507aa4b23f832b6188')
    decoded = read(locale_path)['spans']['parser']['instructions']
    need(not any(i['mnemonic'].startswith('call') for i in decoded), 'Full actual parser source has no CALL')
    for insn in decoded:
        pc, raw = insn['pc'], bytes.fromhex(insn['bytes_hex'])
        need(source[pc-0x7800bc48:pc-0x7800bc48+len(raw)] == raw, 'Full original decoded-source byte association')
    prefix = read(PREP / 'report.json')['prefix_source_instructions']
    need(len(prefix) == 23 and prefix[-1]['pc'] == 0x7800bce6 and prefix[-1]['bytes_hex'] == 'f683e179037804',
         'Exact23-PC nonquoted D-leading prefix including first required table read')
    for insn in prefix:
        need(insn in decoded, 'Prefix belongs to admitted original decoded source')
    guest = bind(RECOVERY / 'normal_parser-guest.ll')
    host = bind(RECOVERY / 'normal_parser-host.ll', parser['host_sha256'])
    ir = (RECOVERY / 'normal_parser-host.ll').read_text()
    need('@__remill_function_call' not in ir and not re.search(r'\b(?:nounwind|inttoptr|ptrtoint|poison|undef)\b', ir),
         'No authored source CALL/host guest-address cast/undefined poison or nonthrowing bridge attribute')
    need(ir.index('%12 = call noundef ptr @__remill_write_memory_32') < ir.index('store i32 %8, ptr %6') and
         ir.index('%70 = call noundef i32 @__remill_read_memory_32') < ir.index('%71 = call noundef ptr @__remill_write_memory_32') < ir.index('store i8 0, ptr %72'),
         'Actual first PUSH checked store before ESP; AND checked read/store before flags')
    body = (PREP / 'parser_binding.inc').read_text()
    current = body[body.index('Binding*current'):body.index('void Binding::first')]
    need(current.index('p!=owner||binding!=owner||admitted_binding!=owner') < current.index('&owner->context'),
         'Current serialized parser/token/side aliases checked before owner dereference')
    admission = body[body.index('void Binding::admit_current'):body.index('void Binding::guard')]
    need(admission.index('binding!=this') < admission.index('&binding->context') and
         admission.index('cm::binding!=&commandline||cm::admitted_binding!=&commandline') < admission.index('cm::current(c)'),
         'Known direct object and command-line references checked before side lookup')
    enter = body[body.index('[[noreturn]]void Binding::enter'):]
    need(enter.index('call_closure(s,a,p)') < enter.index('frame=context.frame-52') < enter.index('owner=this') < enter.index('mw34_mainargs_normal_parser_body'),
         'Real caller closure then private frame publication before actual compiled parser')
    need('~Cleanup()noexcept{b.active=false;b.depth=0;owner=nullptr;}' in enter and
         enter.count('active=false;depth=0;owner=nullptr;checkpoint') == 2,
         'Terminal current owner/activity/depth clear before callback checkpoints, plus cleanup RAII')
    need(body.index('checkpoint(context.runtime,"parser-locale-before")') < body.index('stable_hook(3)') <
         body.index('locale_reached=true') < body.index('throw m4_runtime::Fault'),
         'Required locale operand stops publicly before table memory load')
    need(body.count('memory().map(') == body.count('memory().unmap(') == 0 and
         'std::memcmp(&state,&context.state,sizeof(State))' in body and
         'std::memcmp(&cpu,&context.runtime.cpu(),sizeof(cpu))' in body,
         'Borrowed16page lifecycle and full State/FX/runtime/ledger stable observer closures')
    need('return 0;' in body[body.index('unsigned char Binding::undefined'):body.index('[[noreturn]]void Binding::unsupported')],
         'Only exact two undefined AF sites choose zero; no guest-defined flags fabricated')
    llvm = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
    bind(ROOT / 'tools/lifting/host_adapter.py', '97b101725526866a2a2fa4788be3a850f11da49fbf7cb563cefa1eed44c5b5ed')
    bind(llvm / 'LLVM-C.dll')
    layouts = llvm_layouts(llvm)
    need(layouts[1]['types'] == parser['layouts'], 'Recovery layout facts equal independently queried LLVM layout')
    header = ROOT / 'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/X86/Runtime/State.h'
    need(str(header) in manifest['compiler_read_headers'], 'Actual compiler read exact Remill State header')
    need(str(PREP / 'parser.hpp') in manifest['compiler_read_headers'] and str(PREP / 'parser_binding.inc') in manifest['compiler_read_headers'],
         'Actual compiler read exact prepared new ABI/binding headers')
    inspector = llvm / 'llvm-readobj.exe'
    bind(inspector)
    out.mkdir()
    commands = []
    for level in ('O0', 'O2'):
        compile_path = BUILD / level / 'compile_commands.json'
        bind(compile_path)
        rows = read(compile_path)
        compiled = [r for r in rows if Path(r['file']).name == 'composition.cpp']
        need(len(compiled) == 1 and key(compiled[0]['file']) == key(PREP / 'composition.cpp'), 'Actual compile current exact composition')
        recipe = compiled[0]['command']
        need('/EHs' in recipe and '/EHsc' not in recipe and ('/Od' if level == 'O0' else '/O2') in recipe and
             'ADDRESS_SIZE_BITS=32' in recipe, 'Actual C++ throwing bridge, level and guest32 recipe')
        obj = Path(compiled[0]['output'])
        need(str(obj) in manifest['artifacts'], 'Actual compiled composition object in final build')
        for label, target in (('composition', obj), ('parser', RECOVERY / ('normal_parser-' + level + '.obj'))):
            args = [str(inspector), '--file-headers', '--symbols', '--relocations', '--unwind', str(target)]
            result = subprocess.run(args, capture_output=True, timeout=30)
            need(result.returncode == 0, 'Read-only actual COFF metadata inspection')
            content = result.stdout.decode()
            need('IMAGE_FILE_MACHINE_AMD64' in content and 'RuntimeFunction {' in content, 'Actual AMD64 COFF/unwind metadata')
            if label == 'composition':
                need('__CxxFrameHandler3' in content and 'Binding@m4_crt_parser_prefix' in content and
                     'mw34_mainargs_normal_parser_undefined_8' in content, 'Actual typed parser/throwing C++ closure and undefined bridge')
            else:
                for symbol in ('mw34_mainargs_normal_parser_body', '__remill_read_memory_32', '__remill_write_memory_32',
                    '__remill_read_memory_8', '__remill_write_memory_8', '__remill_function_return', 'mw34_mainargs_normal_parser_undefined_8'):
                    need(symbol in content, 'Actual full parser bridge relocation/symbol: ' + symbol)
                need('__remill_function_call' not in content, 'Actual full parser COFF has no guest call bridge')
            output = out / (label + '-' + level + '-coff.txt')
            output.write_bytes(result.stdout)
            err = out / (label + '-' + level + '-coff.stderr')
            err.write_bytes(result.stderr)
            commands.append({'argv': args, 'exit_code': result.returncode, 'output_sha256': bind(output), 'stderr_sha256': bind(err)})
        worker = Path(manifest['workers'][level])
        data = worker.read_bytes()
        pe_offset = struct.unpack_from('<I', data, 0x3c)[0]
        need(data[pe_offset:pe_offset+4] == b'PE\0\0' and struct.unpack_from('<H', data, pe_offset+4)[0] == 0x8664,
             'Actual linked AMD64 worker; never executed by this audit')
        ninja = BUILD / level / 'build.ninja'
        link = ninja.read_text()
        need(str(RECOVERY / ('normal_parser-' + level + '.obj')).replace('\\', '/') in link.replace('$:', ':').replace('\\', '/'),
             'Actual final linker associates same frozen parser COFF')
    for name, diff in diffs.items():
        p = out / (name + '.diff')
        p.write_text(diff)
        bind(p)
    for p in (Path(__file__), ROOT / 'tools/analysis/pe.py', RECOVERY / 'normal_parser-source.bin', OLD / 'pins.json',
              BASE / 'source-contract-r1/report.json', BASE / 'source-contract-r1/audit-source-snapshot.py'):
        bind(p)
    for p, h in list(pins.items()):
        need(sha(p) == h, 'Stable final source/ABI/artifact binding')
    report = {'passed': True, 'scope': 'Independent actual-source/derivative/IR/ABI/build/COFF association only',
        'build_sha256': BUILD_SHA, 'preparation_sha256': PREP_SHA, 'preparation_pins_sha256': PREP_PINS_SHA,
        'unchanged_guest_COFF_objects': 14, 'unchanged_FDIV_libraries': 2, 'reused_complete_parser_COFF_objects': 2,
        'unchanged_ancestor_components': unchanged, 'exact_additive_inverse_components': sorted(changed),
        'actual_named_State_types_checked': len(layouts[1]['types']), 'State_bytes': 3504, 'FX_bytes': 512,
        'compiled_State_header_sha256': manifest['compiler_read_headers'][str(header)],
        'parser_source_bytes': 436, 'parser_source_sha256': SOURCE_SHA, 'full_parser_source_has_CALL': False,
        'bounded_nonquoted_actual_input_first_byte': 0x44, 'prefix_PC_count_including_unperformed_table_read': 23,
        'completed_generated_memory_accesses': 16, 'required_unperformed_read_ordinal': 17,
        'real_CALL_site': 0x7800bbf7, 'real_parser_entry': 0x7800bc48, 'real_return_word': 0x7800bbfc,
        'parser_entry_ESP': 0x2000182c, 'source_stop_PC': 0x7800bce6, 'source_required_byte_address': 0x78037a25,
        'raw_locale_table_base': 0x780379e1, 'source_test_mask': 4,
        'typed_internal_provider_context_not_generic_Runtime_frame': True, 'borrowed_pages': 16,
        'new_page_mapping': False, 'State_or_FX_reseed': False,
        'partial_order': 'Checked PUSH store before ESP; checked AND read/store before flags; undefined AF chosen only at two admitted TEST sites; locale read denied before load',
        'terminal_owner_activity_depth_cleared_before_checkpoints': True, 'cleanup_RAII_retained': True,
        'parent_only_BridgeAbort_diagnostic_preserved_without_synthetic_parser_first': True,
        'static_metadata_commands': commands, 'original_executed': False, 'native_worker_executed': False,
        'game_launched': False, 'locale_table_initialization_proved': False, 'parser_RET_claimed': False,
        'parser_sizing_complete': False, 'argument_outputs_claimed': False, 'whole_CRT_complete': False,
        'whole_M4_complete': False,
        'preserved_audit_attempt': {'path': str(BASE / 'source-contract-r1/report.json'),
            'sha256': pins[key(BASE / 'source-contract-r1/report.json')],
            'cause': 'First auditor compared an unescaped Windows path with Ninja D$: syntax; only the audit predicate changed'},
        'limitations': ['Source association is separate from actual native hostile fixtures and original-BEFORE scalar comparison.',
            'The bounded actual nonquoted D-leading input path performs real local count stores but has no parser return or completed sizing/argv outputs.',
            'Current token/side-pointer order is checked for the admitted serialized owner; this is not universal arbitrary-pointer lifetime validation.',
            'Native callback fault controls remain actual artifact fixtures; no general guest State alias mutation equivalence is claimed.']}
    (out / 'pins.json').write_text(json.dumps({'files': dict(sorted(pins.items()))}, indent=2) + '\n')
    report['pins_sha256'] = sha(out / 'pins.json')
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': True, 'report_sha256': sha(out / 'report.json'), 'pins_sha256': report['pins_sha256'],
        'current_physical_bindings': len(pins)}))


if __name__ == '__main__':
    main(sys.argv[1])
