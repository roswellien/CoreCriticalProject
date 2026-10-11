"""Six genuine BEFORE-input packs and a bounded compound-FCOS native worker."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'reports/m4-cosine-native'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(name):
    out = AREA / name
    assert not out.exists()
    out.mkdir(parents=True)
    pins = {}

    def pin(path, digest=None):
        path = Path(path).resolve()
        value = sha(path)
        assert digest is None or digest == value, path
        pins[str(path)] = value
        return path

    original_path = pin(ROOT / 'reports/m4-cosine-original/prefix-validation-r2/report.json',
                        'cee385275cfd924366a867fc4442cf0fe78bae47af136d3b9569e0ace9952b4e')
    original = json.loads(original_path.read_bytes())
    assert original['passed'] and original['reader_closed']
    execution = json.loads(pin(original['execution_path'], original['execution_sha256']).read_bytes())
    prep = json.loads(pin(ROOT / 'reports/m4-cosine-original/prefix-preparation-r2/report.json',
                          'aac031ac5949fa6fb1698c63130aa2652f352e521e140c02034fcb5df9f492df').read_bytes())
    pack = pin(ROOT / 'reports/m4-cosine-original/prefix-preparation-r2/pages.bin', prep['pack_sha256']).read_bytes()
    records = {}
    for i in range(struct.unpack_from('<I', pack, 8)[0]):
        offset = 12 + i * 4104
        page, permission = struct.unpack_from('<2I', pack, offset)
        records[page] = (permission, pack[offset + 8:offset + 4104])
    assert records[0x5e8000][0] == 2
    observed = prep['observed_pages']
    spec = importlib.util.spec_from_file_location('compound_original_direct',
        pin(ROOT / 'tools/m4-crt-allocation-root/run_v2.py'))
    direct = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(direct)
    bundle = direct.DirectSet(Path(execution['original_capture']), pin)
    seed = bytearray()
    case_hashes = []
    mapped_pages = None
    try:
        for sequence in range(6):
            data = bundle.data(f'phase/{sequence}/0.bin')
            assert len(data) == 356992 and struct.unpack_from('<I', data)[0] == sequence
            # Only actual BEFORE CPU, FX, ENV and complete BEFORE pages are
            # published to the native worker. No original AFTER byte is copied.
            seed += data[36:76] + data[116:628] + data[2164:2192]
            pages = dict(records)
            for i, page in enumerate(observed):
                permission = pages[page][0] if page in pages else 0
                pages[page] = (permission, data[2276 + i * 4096:2276 + (i + 1) * 4096])
            if mapped_pages is None:
                mapped_pages = [(page, permission) for page, (permission, _) in pages.items()]
            assert mapped_pages == [(page, permission) for page, (permission, _) in pages.items()]
            blob = b'MW4J124P' + struct.pack('<I', len(pages)) + b''.join(
                struct.pack('<2I', page, permission) + data for page, (permission, data) in pages.items())
            path = out / f'input-{sequence}.bin'
            path.write_bytes(blob)
            case_hashes.append(sha(path))
    finally:
        bundle.close()
    (out / 'input-state.bin').write_bytes(seed)
    assert len(seed) == 6 * 580
    old = pin(ROOT / 'tools/m4-fp-transcendental/native_cosine.cpp').read_text()

    def one(before, after):
        nonlocal old
        assert old.count(before) == 1, (before, old.count(before))
        old = old.replace(before, after)

    one('#include "probe_spec.hpp"\n#include "cosine_spec.hpp"', '#include "fixture_spec.hpp"')
    begin = old.index('extern "C" void *mw34_fp_entry_4ce5a0')
    end = old.index('constexpr char image_sha', begin)
    old = old[:begin] + '''extern "C" void *mw34_fp_entry_4b64f0(State *,std::uint32_t,void *);
namespace mw34::m4_fp_cosine_native {
struct Root {unsigned entry,input,output;};
constexpr std::uint32_t frame=0x20001800,sentinel=0x410a80;
static void *route(State *state,std::uint32_t pc,void *memory){
    require_placeholder:
    if(pc!=0x4b64f0)throw std::runtime_error("Unadmitted compound cosine route");
    return mw34_fp_entry_4b64f0(state,pc,memory);
}
''' + old[end:]
    old = old.replace('    require_placeholder:\n', '')
    one('constexpr unsigned memory_size=9*4096;', 'constexpr unsigned memory_size=43*4096;')
    one('static std::vector<std::uint8_t> admit(const char *pack_path,const char *image_path){',
        'static std::vector<std::uint8_t> admit(const char *pack_path,const char *image_path,unsigned sequence){')
    one('auto pack=read(pack_path,61572);require(pack.size()==61572&&sha256(pack)==m4_fp::pack_sha,"Exact reviewed pack required");',
        'auto pack=read(pack_path,fixture::pack_size);require(sequence<6&&pack.size()==fixture::pack_size&&sha256(pack)==fixture::pack_sha[sequence],"Exact genuine BEFORE input pack required");')
    one('std::memcmp(pack.data(),"MW4FPK01",8)==0&&word<std::uint32_t>(pack.data()+8)==15',
        'std::memcmp(pack.data(),"MW4J124P",8)==0&&word<std::uint32_t>(pack.data()+8)==fixture::page_bases.size()')
    old = old.replace('i<15', 'i<fixture::page_bases.size()')
    old = old.replace('m4_fp::page_bases', 'fixture::page_bases').replace('m4_fp::page_permissions', 'fixture::page_permissions')
    one('for(unsigned i=6;i<fixture::page_bases.size();++i)memory.read({fixture::page_bases[i]},std::as_writable_bytes(std::span{bytes.data()+(i-6)*4096,4096}));',
        'for(unsigned i=0;i<43;++i)memory.read({fixture::observed_pages[i]},std::as_writable_bytes(std::span{bytes.data()+i*4096,4096}));')
    old = old.replace('std::array<Event,3>', 'std::array<Event,14>')
    one('sizeof(Result)==83088', 'sizeof(Result)==361836')
    one('const std::array<Event,14> sequence{{{root.input,0,8,0},{root.output,0,4,1},{frame,0,4,0}}};',
        'const std::array<Event,14> sequence{{{0x5c93d0,0,8,0},{0x5e886c,0x7f7fffff,4,1},{0x5e8870,0x40400000,4,1},{0x5e8874,0x40c00000,4,1},{0x5e8878,0x3f800000,4,1},{0x5e887c,0,4,1},{0x5e888c,0x42480000,4,1},{0x5e8890,0,4,1},{0x5e8880,0,4,1},{0x5c93d8,0,8,0},{0x5e8884,0,4,1},{0x5c93e0,0,8,0},{0x5e8888,0,4,1},{frame,0,4,0}}};')
    old = old.replace('event_count!=3', 'event_count!=14').replace('reads!=2||writes!=1||clears!=2||tests!=2', 'reads!=4||writes!=10||clears!=6||tests!=6').replace('primitives!=1', 'primitives!=3')
    one('if(primitives||clears!=1||tests||event_count!=1){fault();return;}++primitives;',
        'constexpr unsigned positions[]{1,10,12};if(primitives>=3||clears!=2*primitives+1||tests!=2*primitives||event_count!=positions[primitives]){fault();return;}++primitives;')
    old = old.replace('clears>=2', 'clears>=6').replace('tests>=2', 'tests>=6')
    one('if(mask!=127||clears!=tests||clears>=6){fault();return;}++clears;',
        'constexpr unsigned positions[]{1,8,10,10,12,12};if(mask!=127||clears!=tests||clears>=6||event_count!=positions[clears]){fault();return;}++clears;')
    one('if(!access(address,4,1))return;bool ok{};',
        'if(!access(address,4,1))return;if(event_count>=1&&event_count<=7){constexpr unsigned literal[]{0x7f7fffff,0x40400000,0x40c00000,0x3f800000,0,0x42480000,0};if(value!=literal[event_count-1]){fault();return;}}bool ok{};')
    start = old.index('static void controls(')
    end = old.index('class Output {', start)
    old = old[:start] + old[end:]
    one('extern "C" void *__remill_write_memory_f32',
        'extern "C" void *__remill_write_memory_32(void *c,unsigned address,unsigned value){static_cast<mw34::m4_fp_cosine_native::Context *>(c)->write32(address,value);return c;}\nextern "C" void *__remill_write_memory_f32')
    start = old.index('int main(')
    old = old[:start] + '''int main(int argc,char **argv){using namespace mw34::m4_fp_cosine_native;try{
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    require(argc==4,"Usage: compound_cosine BEFORE_input_directory admitted_image fresh_output");
    const auto directory=std::filesystem::path(argv[1]);const auto state_path=(directory/"input-state.bin").string();
    const auto seeds=read(state_path.c_str(),3480);require(seeds.size()==3480&&sha256(seeds)==fixture::state_sha,"Exact original BEFORE CPU/FX/ENV input file");
    Output out(argv[3]);const std::uint32_t header[]{1,6,sizeof(Result),3504,43,4096};out.write("MW4COS03",8);out.write(header,sizeof(header));
    for(unsigned sequence=0;sequence<6;++sequence){
        const auto pack_path=(directory/("input-"+std::to_string(sequence)+".bin")).string();const auto pack=admit(pack_path.c_str(),argv[2],sequence);
        Harness h(pack);Root root{0x4b64f0,0x5c93d0,0x5e8880};Context c(h.memory,root);State s;
        const auto input=seeds.data()+sequence*580;const unsigned cw=word<std::uint16_t>(input+40),top=(word<std::uint16_t>(input+42)>>11)&7;
        initialize(s,cw,top,sequence*3571+cw,root.entry);
        std::memcpy(&s.x87,input+40,512);
        for(unsigned i=0;i<8;++i){std::memcpy(&s.st.elems[i].val,input+40+32+i*16,10);std::memcpy(&s.vec[i],input+40+160+i*16,16);}
        require(std::memcmp(&cpu(s),input,40)==0,"Complete BEFORE CPU seeded without output values");
        Result r{};r.repeat=sequence;r.pc=root.entry;r.cw=cw;r.top=top;
        execute(h,s,c,r);require(!r.status&&r.host_restored,"Native compound route/host isolation failed");out.write(&r,sizeof(r));
    }
    out.commit();std::cout<<"Six actual compound FCOS native records; separate comparison required\\n";return 0;
}catch(const std::exception &e){std::cerr<<e.what()<<'\\n';return 1;}}
'''
    old = old.replace('require(std::memcmp(&cpu(s),input,40)==0,', 'const auto initial_cpu=cpu(s);require(std::memcmp(&initial_cpu,input,40)==0,')
    (out / 'native.cpp').write_text(old)
    spec = '#pragma once\n#include <array>\n#include <cstdint>\nnamespace fixture {\n'
    spec += 'constexpr unsigned pack_size=' + str(12 + 4104 * len(mapped_pages)) + ';\n'
    spec += 'constexpr const char *pack_sha[]{' + ','.join(json.dumps(h) for h in case_hashes) + '};\n'
    spec += 'constexpr const char state_sha[]=' + json.dumps(sha(out / 'input-state.bin')) + ';\n'
    for field, values in [('page_bases', [p for p, _ in mapped_pages]),
                          ('page_permissions', [v for _, v in mapped_pages]),
                          ('observed_pages', observed)]:
        spec += f'constexpr std::array<unsigned,{len(values)}> {field}' + '{' + ','.join(hex(v) for v in values) + '};\n'
    spec += '}\n'
    (out / 'fixture_spec.hpp').write_text(spec)
    (out / 'raw80.cpp').write_bytes(pin(ROOT / 'tools/m4-fp-cosine-repair/raw80_status.cpp').read_bytes())
    (out / 'store_test.cpp').write_bytes(pin(ROOT / 'tools/m4-fp-store-repair/store_test.cpp').read_bytes())
    cmake = '''cmake_minimum_required(VERSION 3.24)
project(MW34CompoundCosine LANGUAGES CXX)
if(NOT WIN32 OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8 OR NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang")
 message(FATAL_ERROR "Windows x64 Clang required")
endif()
add_executable(mw34_compound_cosine native.cpp raw80.cpp store_test.cpp "${MW34_ROOT}/runtime/memory/guest_memory.cpp" "${MW34_HOST_OBJECT}")
target_compile_features(mw34_compound_cosine PRIVATE cxx_std_20)
target_include_directories(mw34_compound_cosine PRIVATE "${MW34_ROOT}/runtime")
target_include_directories(mw34_compound_cosine SYSTEM PRIVATE "${MW34_ROOT}/local/tools/remill-v6.0.1/remill-6.0.1/include")
target_compile_definitions(mw34_compound_cosine PRIVATE ADDRESS_SIZE_BITS=32 HAS_FEATURE_AVX=0 HAS_FEATURE_AVX512=0)
target_compile_options(mw34_compound_cosine PRIVATE /EHsc /clang:-frounding-math)
target_link_libraries(mw34_compound_cosine PRIVATE bcrypt)
'''
    (out / 'CMakeLists.txt').write_text(cmake)
    candidate = pin(AREA / 'host-candidate-r1/report.json',
                    '52fbe84a286e333d7c095be292088b922138eaabb661cf41d364bfab7c0ffb9e')
    pin(ROOT / 'runtime/memory/guest_memory.cpp')
    pin(ROOT / 'runtime/memory/guest_memory.hpp')
    pin(ROOT / 'runtime/core/guest_address.hpp')
    pin(__file__)
    for path in out.iterdir():
        pin(path)
    report = dict(passed=True, scope='Six original BEFORE input packs and compound native worker preparation',
                  root=0x4b64f0, host_candidate=str(candidate), host_candidate_sha256=sha(candidate),
                  original_source=str(original_path), original_source_sha256=sha(original_path),
                  sequences=6, observed_pages=observed, mapped_pages=mapped_pages,
                  native_record_bytes=361836, event_count=14, primitive_count=3,
                  native_executed=False, source_after_seed=False, initializer_credit=0,
                  reader_closed=True, files=pins)
    path = out / 'report.json'
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=True, sha256=sha(path), mapped_pages=len(mapped_pages))))


if __name__ == '__main__':
    main(sys.argv[1])
