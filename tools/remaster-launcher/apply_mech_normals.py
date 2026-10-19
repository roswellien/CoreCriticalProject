"""Normal maps for every replacement mech, and separate mech/ground normal strength.

* The Mad Cat-only normals loader becomes generic: each replacement model reads
  the BWNRM1 sidecar named by its texture variable with _TEXTURES replaced by
  _NORMALS (MW34_MADCAT_NORMALS, MW34_BUSHWACKER_NORMALS, MW34_ORION_LOD1_NORMALS, ...).
* MW34_SUN_NORMAL_STRENGTH applies to replacement mechs; terrain and world
  meshes use MW34_SUN_GROUND_NORMAL_STRENGTH (default 1.0, the previous ground look).
Apply after the sun/shadow/atmosphere/ground-normal host edits.
"""
from pathlib import Path
import argparse

def edit(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError(f'Expected one mech-normal anchor in {path.name}: {old[:80]}')
    path.write_text(text.replace(old,new))

def apply(host):
    edit(host/'mesh_override_stage.inc',''' if(std::string(model.id)!="madcat")return;
 const char*path=std::getenv("MW34_MADCAT_NORMALS");if(!path)return;''',''' std::string env=model.texture_env;const auto suffix=env.rfind("_TEXTURES");if(suffix==std::string::npos)return;env.replace(suffix,9,"_NORMALS");
 const char*path=std::getenv(env.c_str());if(!path||!*path)return;''')
    vk=host/'vk_scene.hpp'
    edit(vk,'mw34::sun::settings().normal_strength,mw34::sun::settings().shadow_debug?1.f:0.f,1};',
            'mw34::sun::settings().ground_normal_strength,mw34::sun::settings().shadow_debug?1.f:0.f,1};')
    edit(vk,'u=mw34::sun::uniform(instance.sun_normal,mw34::sun::settings());u.world=instance.sun_world;',
            'u=mw34::sun::uniform(instance.sun_normal,mw34::sun::settings());u.world=instance.sun_world;if(instance.world)u.extra[1]=mw34::sun::settings().ground_normal_strength;')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('host_source',type=Path);apply(p.parse_args().host_source)
