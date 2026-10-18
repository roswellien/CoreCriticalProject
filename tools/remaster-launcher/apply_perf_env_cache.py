"""Performance: no environment lookups in per-draw / per-node paths.

Profiling a ~10-mech Big Lake battle showed ~30% of the main thread inside
ucrtbase getenv (a linear scan of ~150 variables):
* override_begin (every guest mesh-node draw, 0x53F2E0) called getenv for all
  13 model slots, then string-compared the node name against every roster;
* override_validate_root did the same 13 lookups per root per scene;
* Renderer::render read MW34_SKY_DEBUG once per draw and MW34_SUN_SHADOW_AUDIT
  per shadow scene.
The environment is fixed before the host starts, so each value is read once.
Node-name candidacy uses a set built once from the enabled rosters.
The performance overlay reuses its strip buffer instead of allocating and
zeroing a width x 24 buffer every frame (it clears its own box). Behaviour is unchanged. Apply after apply_mech_normals.py.

After replacing or expanding the model adapter, --models-only restores its caches
without reapplying renderer/HUD edits. This mode accepts an already cached adapter
and validates every model anchor before writing the file.
"""
from pathlib import Path
import argparse

def edit(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError(f'Expected one perf-env anchor in {path.name}: {old[:80]}')
    path.write_text(text.replace(old,new))

HELPERS='''// Model slot paths and roster names are fixed for the process; read them once.
static const char*override_mesh_env(const OverrideModel&m){
 static const auto paths=[]{std::array<const char*,override_models.size()>p{};for(size_t i=0;i<p.size();++i)p[i]=std::getenv(override_models[i].mesh_env);return p;}();
 return paths[size_t(&m-override_models.data())];}
static bool override_candidate_name(const std::string&name){
 static const auto names=[]{std::set<std::string>s;for(const auto&m:override_models)if(override_mesh_env(m))for(size_t at=0;at<m.count;++at)s.insert(m.roster[at].name);return s;}();
 return names.count(name)!=0;}
#include "override_arm_damage_plans.inc"'''

def model_cache_text(text):
    changes=[
        ('#include "override_arm_damage_plans.inc"',HELPERS),
        ('bool candidate=false;for(const auto&m:override_models)if(std::getenv(m.mesh_env))for(size_t at=0;at<m.count;++at)if(name==m.roster[at].name)candidate=true;if(!candidate)return previous;',
         'if(!override_candidate_name(name))return previous;'),
        ('const auto&m=override_models[id];if(!std::getenv(m.mesh_env))continue;bool match=',
         'const auto&m=override_models[id];if(!override_mesh_env(m))continue;bool match='),
    ]
    for old,new in changes:
        if text.count(new)==1:
            # HELPERS deliberately retains the include used as its old anchor.
            expected_old=1 if old in new else 0
            if text.count(old)!=expected_old:
                raise RuntimeError('Conflicting model-cache anchors: '+old[:80])
            continue
        if text.count(new)!=0 or text.count(old)!=1:
            raise RuntimeError('Expected one model-cache anchor: '+old[:80])
        text=text.replace(old,new)
    return text


def apply_model_cache(host):
    m=host/'mesh_override_stage.inc'
    text=m.read_text()
    updated=model_cache_text(text)
    if updated!=text:
        m.write_text(updated)


def apply(host):
    apply_model_cache(host)
    vk=host/'vk_scene.hpp'
    edit(vk,'if(const char* dbg=std::getenv("MW34_SKY_DEBUG"))',
            'if(const char* dbg=[]{static const char*const v=std::getenv("MW34_SKY_DEBUG");return v;}())')
    edit(vk,'if(const char* audit=std::getenv("MW34_SUN_SHADOW_AUDIT");',
            'if(const char* audit=[]{static const char*const v=std::getenv("MW34_SUN_SHADOW_AUDIT");return v;}();')
    edit(host/'gpu_hud.inc','std::vector<std::uint16_t>buf(size_t(w)*24,0);ov.draw(buf.data(),w,24);',
            'static std::vector<std::uint16_t>buf;buf.resize(size_t(w)*24);ov.draw(buf.data(),w,24);')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('host_source',type=Path)
    p.add_argument('--models-only',action='store_true')
    a=p.parse_args()
    (apply_model_cache if a.models_only else apply)(a.host_source)
