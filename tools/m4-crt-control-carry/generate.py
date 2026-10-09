"""Additive original pack and reversible shared adapters for control-to-FP carry."""
import hashlib, json, pathlib, re, struct, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-control-carry'
MIXED = ROOT / 'reports/m4-mixed-startup'
CONNECTED = ROOT / 'reports/m4-crt-control-integration'
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools/m4-crt'))
from recover_provider import PE


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'))


def need(value, why):
    if not value:
        raise ValueError(why)


def once(text, old, new):
    need(text.count(old) == 1, 'Unique derivative anchor: ' + old)
    return text.replace(old, new)


def generate(out):
    need(not out.exists() and out.is_relative_to(BASE), 'Fresh private carry preparation required')
    expected = {
        MIXED / 'independent-review-r1/report.json': '3c4f6b2903efeca37f08b2119b1dc87d374a39cc2284079ccc26abfd30db9f96',
        MIXED / 'native-derived-r2/generation.json': 'eef6604787b10e87b4d9535f390b2c104168daeb9c8bc55306f72e614357414a',
        MIXED / 'original-extract-original-build-r2/extraction.json': '62983322b91c6b446ddee5562248614ad3a22512dc1c256f1c0bfea56fcf6b97',
        CONNECTED / 'author-review-r1/report.json': '5224a32cc92ba202aed8d8465f736533aff3f206116b67b7711a705b21ce65ed',
        CONNECTED / 'research-r1/host.ll': '45de8ae06bda09bfbd7a734f4be67eeca6fc5a9f68161e614a89b2871a7b569a',
    }
    original = {}

    def source(path):
        path = pathlib.Path(path)
        original[str(path.resolve())] = sha(path)
        return path.read_text(encoding='utf-8-sig')

    for path, digest in expected.items():
        need(sha(path) == digest, 'Exact bounded prior association ' + str(path))
        original[str(path)] = digest
    old_generation = read(MIXED / 'native-derived-r2/generation.json')
    for key in ('original_sources', 'generated_sources'):
        for path, digest in old_generation[key].items():
            need(sha(path) == digest, 'Frozen shared26 source ' + path)
            original[path] = digest
    extraction = read(MIXED / 'original-extract-original-build-r2/extraction.json')
    mixed_pack_path = pathlib.Path(extraction['pack']['path'])
    need(sha(mixed_pack_path) == extraction['pack']['sha256'], 'Exact mixed original pack')
    original[str(mixed_pack_path)] = sha(mixed_pack_path)
    mixed_pack = mixed_pack_path.read_bytes()
    control_pack_path = CONNECTED / 'research-r1/pack.bin'
    control_pack = control_pack_path.read_bytes()
    need(sha(control_pack_path) == '135d7d7f8c41ba9a232f2cdc76fb673f9eb52e1939cf70111b3b59cbd6fd91d9', 'Exact connected pack')
    original[str(control_pack_path)] = sha(control_pack_path)
    need(mixed_pack[:8] == b'MW4MXP01' and len(mixed_pack) == 12 + 22 * 4104 and control_pack[:8] == b'MW4CIPK1', 'Declared pack layouts')
    extra = bytearray(control_pack[12:])
    # Instrumentation changes only the authored outer-continuation jump.
    need(extra[8 + 0x436] == 0xE9, 'Previous authored capture jump')
    struct.pack_into('<I', extra, 8 + 0x437, (0x410A80 - 0x5AC43B) & 0xFFFFFFFF)
    pack = b'MW4CCP01' + struct.pack('<I', 26) + mixed_pack[12:] + extra
    pages = [struct.unpack_from('<II', pack, 12 + i * 4104) for i in range(26)]
    # Original connected role2 is readonly; mixed role2 is writable.
    pack = bytearray(pack)
    struct.pack_into('<I', pack, 12 + 23 * 4104 + 4, 0)
    pages[23] = (pages[23][0], 0)
    need(len(set(a for a, _ in pages)) == 26 and pages[22:] == [(0x5AC000, 1), (0x5BB000, 0), (0x78004000, 1), (0x78011000, 1)], 'Disjoint source pages and roles')
    out.mkdir(parents=True)
    generated = {}

    def write(relative, text):
        path = out / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        generated[str(path)] = sha(path)
        return path

    pack_path = out / 'pack.bin'
    pack_path.write_bytes(pack)
    generated[str(pack_path)] = sha(pack_path)
    spec = source(MIXED / 'original-extract-original-build-r2/spec.hpp')
    spec = spec.replace('mw34::m4_mixed_original', 'mw34::m4_crt_control_carry_original')
    spec = spec.replace(extraction['pack']['sha256'], sha(pack_path)).replace('pack_size=90300', 'pack_size=106716')
    for name, first in [('entries', '0x5ac5a0'), ('table_slots', '0')]:
        spec = once(spec, 'std::uint32_t,26> ' + name + '{', 'std::uint32_t,27> ' + name + '{' + first + ',')
    for name, values in [('page_bases', [a for a, _ in pages]), ('page_permissions', [p for _, p in pages])]:
        pattern = r'inline constexpr std::array<std::uint32_t,22> ' + name + r'\{[^}]*\};'
        need(len(re.findall(pattern, spec)) == 1, 'Exact old page declaration')
        spec = re.sub(pattern, 'inline constexpr std::array<std::uint32_t,26> ' + name + '{' + ','.join(hex(v) for v in values) + '};', spec)
    prep = read(CONNECTED / 'preparation-r1/report.json')
    rows = prep['complete_source_ranges']
    additions = ','.join('{0x%x,%d,%d,%d}' % (r['address'], r['size_bytes'], r['file_offset'], 12 + 22 * 4104 + 8 + r['address'] - 0x5AC000) for r in rows)
    spec = once(spec, 'std::array<CodeBinding,194> code_bindings{{', 'std::array<CodeBinding,196> code_bindings{{' + additions + ',')
    provider_path = ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    pe = PE(provider_path, prep['provider_sha256'])
    original[str(provider_path)] = sha(provider_path)
    provider_bindings = []
    for address, size, page_index in [(0x780042E1, 303, 24), (0x7801129B, 125, 25)]:
        offset = pe.offset(address - 0x78000000, size)
        po = 12 + page_index * 4104 + 8 + (address & 4095)
        need(pe.bytes[offset:offset + size] == pack[po:po + size], 'Literal frozen provider slice')
        provider_bindings.append((address, size, offset, po))
    spec += '\nnamespace mw34::m4_crt_control_carry_original {\ninline constexpr char provider_sha[]="' + sha(provider_path) + '";\ninline constexpr std::array<CodeBinding,2> provider_bindings{{' + ','.join('{%d,%d,%d,%d}' % row for row in provider_bindings) + '}};\n}\n'
    write('original/spec.hpp', spec)
    protocol = source(ROOT / 'tools/m4-mixed-startup/original/protocol.hpp')
    protocol = protocol.replace('mw34::m4_mixed_original', 'mw34::m4_crt_control_carry_original')
    protocol = once(protocol, 'sequences=48, roots=26', 'sequences=24, roots=27')
    write('original/protocol.hpp', protocol)
    ref = source(ROOT / 'tools/m4-mixed-startup/original/reference.cpp')
    ref = ref.replace('mw34::m4_mixed_original', 'mw34::m4_crt_control_carry_original')
    ref = once(ref, 'dispatch(argc,argv,4)', 'dispatch(argc,argv,5)')
    ref = once(ref, 'require(argc==4,"Connected original: exact-pack exact-image fresh-output");', 'require(argc==5,"Carry original: exact-pack exact-image exact-provider fresh-output");\n    require(reinterpret_cast<std::uintptr_t>(GetModuleHandleW(nullptr))==0x60000000,"Disjoint actual original probe placement required");')
    ref = once(ref, 'std::array<void*,22> pages{};', 'const auto provider=read(argv[3],266293);require(provider.size()==266293&&sha256(provider)==provider_sha,"Exact carry provider identity required");\n    for(const auto &span:provider_bindings)require(std::uint64_t{span.image_offset}+span.size<=provider.size()&&std::memcmp(provider.data()+span.image_offset,pack.data()+span.pack_offset,span.size)==0,"Literal provider/pack slice identity required");\n    std::array<void*,26> pages{};')
    ref = once(ref, '"MW4MXP01"', '"MW4CCP01"')
    ref = once(ref, 'Output out(argv[3]);', 'Output out(argv[4]);')
    ref = once(ref, '"MW4MXO01"', '"MW4CCO01"')
    ref = once(ref, 'for(unsigned top:{0u,7u})', 'for(unsigned top:{0u})')
    ref = once(ref, 'std::memcpy(reinterpret_cast<void*>(frame),&capture_pc,4);', 'const std::uint32_t return_word=phase?capture_pc:0x5ac436;std::memcpy(reinterpret_cast<void*>(frame),&return_word,4);')
    ref = once(ref, '48 connected sequences / 1248 actual original initializer phases captured', '24 carry sequences / 648 actual original control and selected initializer phases captured')
    write('original/reference.cpp', ref)
    asm = source(ROOT / 'tools/m4-mixed-startup/original/reference_x86.asm')
    write('original/reference_x86.asm', asm)
    broker = source(ROOT / 'tools/m4-mixed-startup/original/original_broker.hpp')
    broker = once(broker, 'std::array<std::uint32_t,11> bases{0x400000,0x410000,0x430000,0x460000,0x4a0000,0x4b0000,0x4c0000,0x5c0000,0x5e0000,0x600000,0x20000000}', 'std::array<std::uint32_t,15> bases{0x400000,0x410000,0x430000,0x460000,0x4a0000,0x4b0000,0x4c0000,0x5a0000,0x5b0000,0x5c0000,0x5e0000,0x600000,0x20000000,0x78000000,0x78010000}')
    write('original/original_broker.hpp', broker)

    # Fresh external symbol namespace; reverse equality is recorded for all IR.
    configuration = []
    for path, digest in old_generation['generated_sources'].items():
        path = pathlib.Path(path)
        relative = path.relative_to(MIXED / 'native-derived-r2')
        text = path.read_text(encoding='utf-8-sig')
        renamed = text.replace('m4_mixed::', 'm4_crt_control_carry::').replace('mw34::m4_mixed', 'mw34::m4_crt_control_carry').replace('mw34_mixed_', 'mw34_carry_')
        renamed = renamed.replace((ROOT / 'tools/m4-mixed-startup/native_protocol.hpp').as_posix(), (ROOT / 'tools/m4-crt-control-carry/native_protocol.hpp').as_posix())
        need(renamed.replace('m4_crt_control_carry::', 'm4_mixed::').replace('mw34::m4_crt_control_carry', 'mw34::m4_mixed').replace('mw34_carry_', 'mw34_mixed_').replace((ROOT / 'tools/m4-crt-control-carry/native_protocol.hpp').as_posix(), (ROOT / 'tools/m4-mixed-startup/native_protocol.hpp').as_posix()) == text, 'Reversible shared derivative namespace ' + str(path))
        if relative.as_posix() in ('chain/runtime_adapter.cpp', 'integer/runtime_adapter.cpp'):
            # Only a local offline-validator Request representation changes.
            # The resident FX view and complete State retain the actual hardware
            # capability field, which is not the architectural MXCSR register.
            renamed = once(renamed, '    std::memcpy(domain.fx.data(),fx.data(),512);',
                '    std::memcpy(domain.fx.data(),fx.data(),512);\n'
                '    require(word<std::uint32_t>(domain.fx.data()+28)==0x2ffff&&word<std::uint32_t>(reinterpret_cast<const std::uint8_t *>(&s.x87)+28)==0x2ffff,"Observed carry FX capability mask changed");\n'
                '    std::fill_n(domain.fx.data()+28,4,0); // temporary Request only; resident State/FX unchanged')
        write('native/' + relative.as_posix(), renamed)
    for component in old_generation['components']:
        current = dict(component)
        for name in ('cpp',):
            current[name] = str(out / 'native' / pathlib.Path(component[name]).relative_to(MIXED / 'native-derived-r2'))
        for name in ('bridges', 'modules'):
            current[name] = [str(out / 'native' / pathlib.Path(p).relative_to(MIXED / 'native-derived-r2')) for p in component[name]]
        current['mapping'] = {a: b.replace('mw34_mixed_', 'mw34_carry_') for a, b in component['mapping'].items()}
        configuration.append(current)
    control_text = source(CONNECTED / 'research-r1/host.ll')
    symbols = ['__remill_function_return', '__remill_jump', '__remill_read_memory_32', '__remill_write_memory_32', 'mw34_cf_enter', 'mw34_cf_load_cw', 'mw34_cf_store_cw', 'mw34_cf_wait', 'mw34_ci_enter']
    mappings = {s: 'mw34_carry_control_' + s for s in symbols}

    def control_namespace(text):
        for old, new in mappings.items():
            text = re.sub(r'\b' + re.escape(old) + r'\b', new, text)
        return text

    renamed = control_namespace(control_text)
    reverse = renamed
    for old, new in mappings.items():
        reverse = re.sub(r'\b' + re.escape(new) + r'\b', old, reverse)
    need(reverse == control_text, 'Complete reversible control IR external namespace')
    write('native/control.ll', renamed)
    context_path = ROOT / 'tools/m4-crt-control-integration/native_context.hpp'
    context = source(context_path)
    for name in ('common.hpp', 'runtime.hpp', 'guest_cw.hpp', 'admission.hpp'):
        paths = {'common.hpp': context_path.parent / name, 'runtime.hpp': ROOT / 'tools/m4-runtime' / name, 'guest_cw.hpp': ROOT / 'tools/m4-guest-cw' / name, 'admission.hpp': ROOT / 'tools/m4-startup' / name}
        context = once(context, '#include "' + name + '"', '#include "' + paths[name].as_posix() + '"')
    write('native/control_context.hpp', control_namespace(context))
    capture = source(ROOT / 'tools/m4-crt-control-integration/state_capture.hpp')
    capture = once(capture, '#include "native_context.hpp"', '#include "control_context.hpp"')
    write('native/control_capture.hpp', capture)
    generation = {'passed': True, 'scope': 'Additive preparation only: actual control wrapper followed by26selected roots; no execution/equivalence credit', 'original_sources': original, 'generated_sources': generated, 'components': configuration, 'control_external_mapping': mappings, 'temporary_Request_representation': {'adapters': ['chain', 'integer'], 'offset': 28, 'bytes': 4, 'required_actual_resident_FX_value': 0x2ffff, 'temporary_offline_validator_value': 0, 'resident_State_or_Runtime_FX_mutated': False, 'architectural_CW_MXCSR_or_status_mutated': False}, 'original_pages': [{'address': a, 'role': p} for a, p in pages], 'original_capture_projection': 'Prior5AC436→10000100 authored instrumentation is now5AC436→410A80. Original numerical returns already use410A80; native control return remains5AC436.', 'sequences': 24, 'phases_per_sequence': 27, 'original_phases': 648, 'incoming_TOP': 0, 'full_CRT_executed': False, 'whole_M4_complete': False}
    write('generation.json', json.dumps(generation, indent=2) + '\n')
    print('Prepared carry:', len(generated), 'private files;', sha(out / 'generation.json'))


if __name__ == '__main__':
    generate(pathlib.Path(sys.argv[1]).resolve())
