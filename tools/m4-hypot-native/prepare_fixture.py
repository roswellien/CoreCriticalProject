"""Freeze registered numeric fixture code with genuine BEFORE-only inputs."""
from pathlib import Path
import hashlib
import json
import re
import sys
import traceback

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT / 'reports/m4-hypot-native'


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main(name):
    assert re.fullmatch('fixture-preparation-r[1-9][0-9]*',name)
    out = AREA / name
    assert not out.exists()
    out.mkdir(parents=True)
    pins = {}
    passed = False
    objects = {}

    def pin(p, expected=None):
        p=Path(p).resolve()
        assert p.suffix.lower() not in ('.mwb','.zip')
        h=sha(p); assert expected is None or h==expected,p
        assert str(p) not in pins or pins[str(p)]==h
        pins[str(p)]=h
        return p

    def receipt(p,expected):
        j=json.loads(pin(p,expected).read_bytes()); assert j['passed']
        for q,h in j['files'].items():
            if Path(q).suffix.lower() not in ('.mwb','.zip'):
                pin(q,h)
        return j

    try:
        domain=receipt(AREA/'reached-domain-r1/report.json',
            '3c47c52775937a8831ca4ef3642e4d48d28ab4c4f4f6302fce58888e7edadcc2')
        inputs=receipt(AREA/'inputs-r3/report.json',
            '46e04c33ef7ca4f8ddcf8e59a4ecb1e6189f1f0410ad635fd471538c5458125d')
        assert domain['counts']['missing_reached_PCs']==0 and domain['counts']['literal_bodies']==21
        assert inputs['memory_pages_per_case']==190 and not inputs['numerical_results_seeded']
        bodies=json.loads(pin(AREA/'reached-domain-r1/literal-bodies.json').read_bytes())
        trace=ROOT/'reports/m4-hypot-original/trace-validation-r2'
        actual=json.loads(pin(trace/'actual-source-accesses.json').read_bytes())
        accesses=[(a['PC'],a['address'],a['width'],a['write']) for a in actual if a['sequence']==0]
        assert len(accesses)==616
        for seq in range(6):
            assert [(a['PC'],a['address'],a['width'],a['write']) for a in actual if a['sequence']==seq]==accesses
        # Values and AFTER bytes are excluded from the compiled operand guard.
        graphs={}
        recovery=ROOT/'reports/m4-hypot-original/recovery-r1'
        for f in ('game-graphs.json','CRT-provider-graphs.json'):
            graphs.update(json.loads(pin(recovery/f).read_bytes()))
        calls=sorted({r['pc'] for g in graphs.values() for r in g['instructions'] if r['mnemonic']=='call'})
        bridges=set()
        for parent in ('lifts-r4','lifts-r5'):
            j=json.loads(pin(AREA/parent/'report.json').read_bytes())
            for b in j['bodies'].values():
                bridges.update(b['bridges'])
        generated=[]
        for bridge in sorted(bridges):
            if '_direct_' in bridge:
                generated.append('extern "C" void *'+bridge+'(State*s,unsigned pc,void*p){auto&c=owner(p);need(&c.s==s,"Exact direct State");bool call=!c.frames.empty()&&c.frames.back().target==0&&c.frames.back().address==s->gpr.rsp.dword;return c.dispatch(pc,call);}')
            elif bridge.endswith('_undefined_8'):
                generated.append('extern "C" unsigned char '+bridge+'(){need(active,"Active explicit undefined arithmetic flag representative");active->authority();return 0;}')
        (out/'generated_bridges.inc').write_text('\n'.join(generated)+'\n')
        (out/'fixture.cpp').write_bytes(pin(ROOT/'tools/m4-hypot-native/fixture.cpp').read_bytes())
        (out/'control_runtime.cpp').write_bytes(pin(ROOT/'tools/m4-hypot-native/control_runtime.cpp',
            sha(ROOT/'tools/m4-hypot-native/control_runtime.cpp')).read_bytes())
        (out/'literal_dispatch.hpp').write_bytes(pin(AREA/'reached-domain-r1/literal_dispatch.hpp').read_bytes())
        root_source=pin(AREA/'lifts-r4/f_4b5910-source.bin').read_bytes()
        assert root_source[:5]==bytes.fromhex('e90b000000')
        prefix=['#pragma once','#include <array>',
            'namespace mw34_hypot_fixture {','inline constexpr unsigned initial_flags=0x202U,root_bytes=5U;',
            'struct AccessSpec {unsigned pc,address,width,writing;};',
            'inline constexpr std::array<AccessSpec,616> accesses{{'+','.join('{'+','.join(str(v)+'U' for v in a)+'}' for a in accesses)+'}};',
            'inline bool is_call(unsigned pc){switch(pc){'+''.join('case '+str(p)+'U:' for p in calls)+'return true;default:return false;}}',
            'inline constexpr const char *root_sha="'+hashlib.sha256(root_source[:5]).hexdigest()+'";',
            'inline constexpr const char *lift_report_sha="'+sha(AREA/'reached-domain-r1/report.json')+'";']
        for level in ('O0','O2'):
            objects[level]=[b['objects'][level]['path'] for b in bodies.values()]
            for b in bodies.values():pin(b['objects'][level]['path'],b['objects'][level]['sha256'])
            (out/('fixture_spec_'+level+'.hpp')).write_text('\n'.join(prefix+[
                'inline constexpr const char *native_object_sha="'+bodies['f_4b5910']['objects'][level]['sha256']+'";','}'])+'\n')
        cmake='''cmake_minimum_required(VERSION 3.24)
project(HypotNative LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
configure_file("${CMAKE_CURRENT_SOURCE_DIR}/fixture_spec_${MW34_LEVEL}.hpp" "${CMAKE_CURRENT_BINARY_DIR}/fixture_spec.hpp" COPYONLY)
add_executable(hypot-native fixture.cpp control_runtime.cpp "${MW34_ROOT}/tools/m4-runtime/runtime.cpp" "${MW34_ROOT}/tools/m4-startup/image_loader.cpp" "${MW34_ROOT}/runtime/memory/guest_memory.cpp" ${MW34_OBJECTS})
target_include_directories(hypot-native PRIVATE "${CMAKE_CURRENT_BINARY_DIR}" "${MW34_ROOT}/tools/m4-runtime" "${MW34_ROOT}/tools/m4-startup" "${MW34_ROOT}/runtime")
target_include_directories(hypot-native SYSTEM PRIVATE "${MW34_REMILL}")
target_link_libraries(hypot-native PRIVATE bcrypt)
'''
        (out/'CMakeLists.txt').write_text(cmake)
        remill=ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/include'
        for q in remill.rglob('*.h'):pin(q)
        for q in ['tools/m4-runtime/runtime.cpp','tools/m4-runtime/runtime.hpp','tools/m4-startup/image_loader.cpp',
                  'tools/m4-startup/image_loader.hpp','tools/m4-startup/admission.hpp','runtime/memory/guest_memory.cpp',
                  'runtime/memory/guest_memory.hpp','runtime/core/guest_address.hpp','tools/m4-runtime/service_provider.hpp']:
            pin(ROOT/q)
        pin(__file__);pin(sys.executable)
        for q in out.iterdir():
            if q.is_file():pin(q)
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        report=dict(passed=passed,scope='Registered admitted-image literal numeric fixture preparation; writer unlaunched',
            objects=objects,remill_include=str(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/include'),
            inputs=str(AREA/'inputs-r3/report.json'),inputs_sha256=sha(AREA/'inputs-r3/report.json'),
            source_domain=str(AREA/'reached-domain-r1/report.json'),source_domain_sha256=sha(AREA/'reached-domain-r1/report.json'),
            counts=dict(literal_bodies=21,literal_objects=42,genuine_cases=6,causal_operands_per_case=616,source_pages_per_case=190),
            original_AFTER_seed=False,source_API_response_seed=False,numerical_oracle=False,
            guest_CW_is_authority=True,raw80_pointer_ABI=True,native_executed=False,initializer_credit=0,
            unknown_cold_domain_denied=True,undefined_flags='Explicit zero representative; source undefined-flag equality unclaimed',files=pins)
        p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(passed=passed,sha256=sha(p))))


if __name__=='__main__':
    main(sys.argv[1])
