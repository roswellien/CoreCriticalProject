"""Install the bounded, observed terrain perspective-loop experiment.

Apply to a fresh current Big Lake host copy. Reuses the existing scratch observer
and exact compiled loop transformation; requires the previously built complete
watched object list. Does not change the playable launcher. Modes 1 (reference)
and 2 (omit admitted prefixes) use MW34_TERRAIN_PROJECTION, independently of the
unpromoted general MW34_GPU_PROJECTION experiment.

Audit and scratch observation default on. The explicit *_AUDIT=0 and *_WATCH=0
settings are for separate timing runs only; they do not establish safety for
unobserved production use. Keep the complete watched object list for proof runs.
"""
from pathlib import Path
import argparse
import shutil

from apply_world_direct import replace
from apply_projection_bypass import apply as projection_adapters
from harden_projection_watch import apply as harden_observation


def finish(host):
    source = Path(__file__).parent / 'native-overrides'
    shutil.copyfile(source / 'terrain_work_profile.hpp', host / 'terrain_work_profile.hpp')
    replace(host / 'vk_scene.hpp', '#include "geometry_profile.hpp"',
            '#include "geometry_profile.hpp"\n#include "terrain_work_profile.hpp"')
    stage = host / 'mfc_stage.hpp'
    replace(stage, '#include "terrain_stage.inc"',
            '#include "terrain_stage.inc"\n'
            'mw34::TerrainWorkProfile terrain_work;')
    replace(stage, 'world_scope=world_begin(state.gpr.rcx.dword,state.gpr.rsp.dword-4);try{',
            'world_scope=world_begin(state.gpr.rcx.dword,state.gpr.rsp.dword-4);'
            'std::string terrain_name;if(terrain_work.file&&host.frames>=terrain_work.from){'
            'SunCaptureFp preserve;terrain_name=pose_name(state.gpr.rcx.dword,36);}'
            'const unsigned terrain_group=terrain_name=="ter"?1U:terrain_name.rfind("bwg",0)==0?2U:0U;'
            'mw34::TerrainWorkProfile::Scope terrain_measure(terrain_work,0,host.frames,terrain_group,terrain_name);try{')
    replace(stage, 'if(target==0x545720)return terrain_545720_probe(s,target,p,body);',
            'if(target==0x545720){mw34::TerrainWorkProfile::Scope terrain_measure(terrain_work,1,host.frames);'
            'return terrain_545720_probe(s,target,p,body);}')
    replace(stage, 'if(target==0x555a70&&distance_log())distance_fog_consumed();',
            'if(target==0x555a70&&distance_log())distance_fog_consumed();\n'
            'if(target==0x555a70){mw34::TerrainWorkProfile::Scope terrain_measure(terrain_work,2,host.frames);'
            'return body(s,target,p);}')

    gate = host / 'projection_stage.inc'
    replace(gate, 'std::getenv("MW34_GPU_PROJECTION")', 'std::getenv("MW34_TERRAIN_PROJECTION")')
    replace(gate, 'MW34_GPU_PROJECTION must be 0, 1 (reference), or 2 (prefix bypass)',
            'MW34_TERRAIN_PROJECTION must be 0, 1 (reference), or 2 (prefix bypass)')
    replace(gate, 'void projection_access(unsigned address,',
            'static bool projection_observed(){static const bool on=[]{'
            'const char*p=std::getenv("MW34_TERRAIN_PROJECTION_WATCH");'
            'if(!p||!std::strcmp(p,"1"))return true;'
            'if(std::strcmp(p,"0"))throw std::runtime_error("MW34_TERRAIN_PROJECTION_WATCH must be 0 or 1");'
            'std::fputs("Terrain perspective timing only: scratch observation disabled; no safety credit\\n",stderr);'
            'return false;}();return on;}\nvoid projection_access(unsigned address,')
    replace(gate, 'if(!mw34::projection::overlaps(address,size))return;',
            'if(!projection_observed()||!mw34::projection::overlaps(address,size))return;')
    replace(gate, 'if(projection_dirty.any(address,count*32)){',
            'if(projection_observed()&&projection_dirty.any(address,count*32)){')
    replace(gate, 'unsigned projection_begin(){', 'unsigned projection_begin(State&state){')
    replace(gate, 'if(std::getenv("MW34_DIVERGENCE_TRACE"))',
            'if([]{static const bool on=std::getenv("MW34_DIVERGENCE_TRACE")!=nullptr;return on;}())')
    replace(gate, 'const auto&scope=*world_scope;const unsigned frame=',
            'const auto&scope=*world_scope;'
            'if(scope.name!="ter"&&scope.name.rfind("bwg",0)!=0)return projection_reject(15);'
            'const unsigned frame=')
    replace(gate, 'if(instance->projection[5]<=0)return 0;',
            'if(instance->projection[5]<=0)return 0;sun_capture_world(*instance,scope.node);')
    # Full per-command hashing is a correctness diagnostic, not part of the
    # retained-geometry render contract. Keep it on by default; timing runs may
    # turn it off equally for reference and bypass, without disabling admission.
    replace(gate, 'projection_fold(&raw,4);projection_fold(&draw.flags,4);',
            'static const bool audit=[]{const char*p=std::getenv("MW34_TERRAIN_PROJECTION_AUDIT");'
            'if(!p||!std::strcmp(p,"1"))return true;if(!std::strcmp(p,"0"))return false;'
            'throw std::runtime_error("MW34_TERRAIN_PROJECTION_AUDIT must be 0 or 1");}();'
            'if(audit){projection_fold(&raw,4);projection_fold(&draw.flags,4);')
    replace(gate, '++projection_commands;', '}++projection_commands;')
    composition = host / 'composition.cpp'
    replace(composition, 'result=mf::owner->projection_begin();',
            'result=mf::owner->projection_begin(*s);')
    # Restore host/guest FP and Win32 error state on both normal and exceptional
    # exits. Declare restored XMM registers to the compiler, as the sun adapter does.
    text = composition.read_text()
    save = '__asm__ volatile("fxsave64 %0":"=m"(saved)::"memory");'
    restore = '__asm__ volatile("fxrstor64 %0"::"m"(saved):"memory");'
    if text.count(save) != 3 or text.count(restore) != 6:
        raise ValueError('Projection FP wrapper anchors changed')
    text = text.replace(save, save + 'const DWORD saved_error=::GetLastError();')
    registers = ','.join('"xmm' + str(i) + '"' for i in range(16))
    text = text.replace(restore, '::SetLastError(saved_error);'
                        '__asm__ volatile("fxrstor64 %0"::"m"(saved):"memory",' + registers + ');')
    composition.write_text(text)


def apply(host):
    projection_adapters(host)
    harden_observation(host)
    finish(host)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source', type=Path)
    args = parser.parse_args()
    apply(args.host_source.resolve(strict=True))
