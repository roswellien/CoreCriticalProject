"""Fresh Runtime-selected compound cosine fixture and actual admission controls.

The accepted125 bootstrap is retained. Only one selected root is executed;
no original AFTER payload is provided to this worker.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import shutil
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
        assert digest is None or value == digest, path
        pins[str(path)] = value
        return path

    def read(path, digest=None):
        return json.loads(pin(path, digest).read_bytes())

    def one(text, before, after):
        assert text.count(before) == 1, (before, text.count(before))
        return text.replace(before, after)

    runtime_path = AREA / 'runtime-preparation-r1/report.json'
    runtime_digest = 'd6c804c83b1f9a00fb026a27d0df1d6982d93d63f133d214956354d8bcf7c506'
    callback = read(runtime_path, runtime_digest)
    assert callback['passed'] and not callback['Runtime_executed']
    for path, digest in callback['files'].items():
        pin(path, digest)
    parent = ROOT / 'reports/m4-joint-startup125/preparation-r4'
    prior = read(parent / 'report.json', '243b6f4c86dc2b966789e23faed4a10fe2efa62ba51f43e854fa843acde392e7')
    native_path = pin(prior['native_preparation'], prior['native_preparation_sha256'])
    for path, digest in prior['generated_sources'].items():
        pin(path, digest)
    connected = out / 'connected'
    connected.mkdir()
    for folder in ('derived', 'ancestors', 'O0', 'O2'):
        shutil.copytree(parent / folder, connected / folder)
    for path in parent.iterdir():
        if path.suffix in ('.cpp', '.hpp', '.inc') or path.name == 'CMakeLists.txt':
            shutil.copy2(path, connected / path.name)
    for path in [callback['CPP']] + callback['bridges']:
        shutil.copy2(path, connected / 'derived' / Path(path).name)
    path = connected / 'joint_protocol.hpp'
    text, count = re.subn(r'constexpr std::array<std::uint32_t,125> entries\{[^\n]+\};',
                         'constexpr std::array<std::uint32_t,1> entries{0x4b64f0};', path.read_text())
    assert count == 1
    text = one(text, 'void cosine(m4_runtime::Runtime &);',
               'void cosine(m4_runtime::Runtime &);void compound_cosine(m4_runtime::Runtime &);')
    path.write_text(text)
    path = connected / 'native_main.cpp'
    path.write_text(one(path.read_text(), 'phase==125&&r_.calls().size()==128&&r_.translation_count()==126',
                        'phase==1&&r_.calls().size()==1&&r_.translation_count()==127'))
    module = pin(ROOT / 'tools/analysis/pe.py')
    spec = importlib.util.spec_from_file_location('compound_fixture_pe', module)
    pe_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pe_module)
    game = pe_module.PEImage(pin(ROOT / 'MW3/Mech3.exe',
        '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
    offset, _ = game.rva_range(0x4b64f0 - game.image_base, 121)
    physical_code_sha = hashlib.sha256(game.data[offset:offset + 121]).hexdigest()
    objects = {}
    for level in ('O0', 'O2'):
        objects[level] = prior['objects'][level] + [callback['objects'][level]['path']]
        assert len(set(objects[level])) == len(objects[level])
        for obj in objects[level]:
            pin(obj)
        path = connected / level / 'mixed_bindings.hpp'
        text = one(path.read_text(), 'std::array<FpBinding,10>fp_bindings',
                   'std::array<FpBinding,11>fp_bindings')
        marker = '&atan}}};'
        text = one(text, marker, '&atan},{0x4b64f0,121,"' + physical_code_sha + '","' +
                   callback['objects'][level]['sha256'] + '","' + runtime_digest + '",&compound_cosine}}};')
        path.write_text(text)
    pages = read(AREA / 'fixture-preparation-r1/report.json',
        '6e10d1bc883ab6fcd8597962f75e4c8660d028c637578ca39553bff034672643')['observed_pages']
    assert len(pages) == 43
    (out / 'current_pages.hpp').write_text('#pragma once\nnamespace mw34_tree_fixture {inline constexpr std::array<unsigned,43>current_pages{' +
        ','.join(hex(page) for page in pages) + '};}\n')
    text = pin(ROOT / 'tools/m4-tree-review/fixture_v2.inc').read_text()
    text = one(text, 'constexpr unsigned tree_root=0x4b7f70;', 'constexpr unsigned tree_root=0x4b64f0;')
    text = one(text, 'thread_local Task*active_tree_task{};', 'thread_local Task*active_tree_task{};\n' + r'''
unsigned fixture_top{},fixture_control{};
mw34::m4::ImageRegion region_for(Context&c,unsigned address){
 for(auto region:c.runtime().image_metadata().mapped_regions)
  if(address>=region.start.value&&std::uint64_t{address}<std::uint64_t{region.start.value}+region.size)return region;
 throw std::runtime_error("Control mapped source region absent");
}
void flip(Context&c,unsigned address){
 auto region=region_for(c,address);auto&memory=c.runtime().memory();
 memory.protect(region.start,Permissions::read|Permissions::write);
 memory.store<unsigned char>({address},memory.load<unsigned char>({address})^1U);
 memory.protect(region.start,region.permissions);
}
void mutate(Context&c){
 switch(fixture_control){
 case 0:break;
 case 1:flip(c,0x4b64f0);break;
 case 2:flip(c,0x5c93d0);break;
 case 3:flip(c,0x5c93d8);break;
 case 4:flip(c,0x5c93e0);break;
 case 5:c.state().addr.ds_base.dword=1;break;
 case 6:c.state().addr.fs_base.dword^=0x1000;break;
 case 7:c.state().x87.fxsave.cwd.flat=0x17f;break;
 case 8:c.state().x87.fxsave.mxcsr.flat^=0x2000;break;
 case 9:c.state().x87.fxsave.ftw.flat=1;break;
 case 10:{auto region=region_for(c,0x5e8880);c.runtime().memory().protect(region.start,Permissions::read);break;}
 default:throw std::runtime_error("Unknown compound causal control");
 }
}
''')
    text = one(text, 't.c->invoke_selected_table(0,0,0,t.records)',
               't.c->invoke_selected_table(0,0,fixture_top,t.records)')
    text = one(text, 'dump(c,*active_tree_task->w,"actual-before-root/",active_tree_task->aliases);',
               'dump(c,*active_tree_task->w,"actual-before-control/",active_tree_task->aliases);mutate(c);dump(c,*active_tree_task->w,"actual-before-root/",active_tree_task->aliases);')
    text = one(text, '  dump(c,*t.w,"actual-live/",t.aliases);', r'''
  dump(c,*t.w,"actual-live/",t.aliases);
  std::array<std::byte,3504>retry_state{};std::memcpy(retry_state.data(),&c.state(),3504);
  const auto retry_cpu=c.runtime().cpu(),retry_fx=c.runtime().fx();
  const auto calls=c.runtime().calls().size();
  dump(c,*t.w,"actual-retry-before/",t.aliases);
  std::vector<Native>retry_records;const auto retry=c.invoke_selected_table(0,0,fixture_top,retry_records);
  dump(c,*t.w,"actual-retry-after/",t.aliases);
  need(!retry&&retry_records.empty()&&c.runtime().calls().size()==calls&&!std::memcmp(retry_state.data(),&c.state(),3504)&&!std::memcmp(&retry_cpu,&c.runtime().cpu(),40)&&retry_fx==c.runtime().fx(),"Actual unchanged retry must reject all State/CPU/FX/routes");
  const unsigned retry_receipt[]{1,0,unsigned(calls),unsigned(c.runtime().poisoned())};t.w->append("actual-retry.bin",retry_receipt,sizeof(retry_receipt));
''')
    text = one(text, 'need(argc==6,"Exact game/numeric/CRT/MFC/fresh output arguments");',
               'need(argc==9,"Exact game/numeric/CRT/MFC/fresh output/CW/TOP/control arguments");const auto fixture_cw=unsigned(std::stoul(argv[6],nullptr,0));fixture_top=unsigned(std::stoul(argv[7],nullptr,0));fixture_control=unsigned(std::stoul(argv[8],nullptr,0));need(fixture_control<=10,"Bounded actual causal control");')
    text = one(text, 'std::as_bytes(std::span{mfc}),0,0x37f,0);',
               'std::as_bytes(std::span{mfc}),0,fixture_cw,fixture_top);')
    text = one(text, 'need(result&&t.completed==1&&sample.tags[9]==7&&sample.tags[10]==7&&!c.registry().string_witnesses().size(),"Actual isolated one-root seven-owner/seven-FS positive extent");',
               'need(!sample.tags[9]&&!sample.tags[10]&&!c.registry().string_witnesses().size(),"Compound root has no allocation/FS providers");need(fixture_control?(!result&&!t.completed&&c.runtime().poisoned()):bool(result&&t.completed==1),"Actual compound positive/causal completion extent");')
    text = text.replace('Isolated literal tree positive passed; connected125 acceptance is separate',
                        'Isolated Runtime compound positive/control passed; connected acceptance is separate')
    (out / 'fixture.cpp').write_text('#define main frozen_connected125_worker_main\n#include "' +
        (connected / 'native_main.cpp').as_posix() + '"\n#undef main\n' + text)
    asm = pin(ROOT / 'tools/m4-crt-allocation/capture.s').read_text()
    asm = one(asm, '  movdqu 256(%r9), %xmm6',
              '  fxrstor64 (%r9)\n  fldenv 512(%r9)\n  movdqu 256(%r9), %xmm6')
    (out / 'capture.s').write_text(asm)
    cmake = one((connected / 'CMakeLists.txt').read_text(), '"${MW34_PREP}/native_main.cpp"',
                '"' + (out / 'fixture.cpp').as_posix() + '"')
    cmake = one(cmake, '${MW34_OBJECTS} "${MW34_WRITER}"',
                '${MW34_OBJECTS} "' + (out / 'capture.obj').as_posix() + '" "${MW34_WRITER}"')
    (out / 'CMakeLists.txt').write_text(cmake)
    pin(__file__)
    files = {str(path.resolve()):sha(path) for path in out.rglob('*') if path.is_file()}
    report = dict(passed=True, scope='Actual Runtime compound cosine selected fixture and 10 bounded causal controls preparation',
                  native_preparation=str(native_path), native_preparation_sha256=prior['native_preparation_sha256'],
                  compound_runtime_preparation=str(runtime_path), compound_runtime_preparation_sha256=runtime_digest,
                  native_library=prior['native_library'], native_include=prior['native_include'],
                  connected_include=str(connected), objects=objects, current_pages=pages,
                  selected_roots=[0x4b64f0], source_bytes=121, physical_code_sha256=physical_code_sha,
                  State_bytes=3504, CPU_bytes=40, FX_bytes=512, Native_bytes=159716,
                  cases=[(0x7f,0),(0x37f,7),(0xf7f,0),(0x47f,7),(0xa7f,0),(0xe7f,7)],
                  controls=['code','input-1','input-2','input-3','DS','FS','CW','MXCSR','FTW','output-RW'],
                  native_executed=False, source_after_seed=False, initializer_credit=0, sources=pins, files=files)
    path = out / 'report.json'
    path.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=True, sha256=sha(path), literal_objects_per_level=len(objects['O0']))))


if __name__ == '__main__':
    main(sys.argv[1])
