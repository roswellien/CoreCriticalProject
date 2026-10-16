"""Add opt-in host geometry measurements to a fresh local host snapshot."""
from pathlib import Path
import argparse
import shutil


def replace(path, old, new):
    value = path.read_text()
    if value.count(old) != 1:
        raise RuntimeError(f"{path.name}: expected one source contract: {old[:65]}")
    path.write_text(value.replace(old, new))


def apply(host):
    shutil.copyfile(Path(__file__).parent / "native-overrides/geometry_profile.hpp",
                    host / "geometry_profile.hpp")
    replace(host / "vk_scene.hpp", '#include "model_scene_vert.h"',
            '#include "geometry_profile.hpp"\n#include "model_scene_vert.h"')
    replace(host / "mfc_stage.hpp", ' #include "mesh_override_stage.inc"',
            ' mw34::GeometryProfile geometry_profile;\n #include "mesh_override_stage.inc"')
    replace(host / "mfc_stage.hpp", '}else result=body(s,target,p);if(target==0x51fb30)override_emit();return result;}',
            '}else if(target==0x51fb30){mw34::GeometryProfile::Scope measure(geometry_profile,true);result=body(s,target,p);}\n'
            '  else result=body(s,target,p);if(target==0x51fb30)override_emit();return result;}')
    mesh = host / "mesh_override_stage.inc"
    replace(mesh, 'void override_emit(){',
            'void override_emit(){mw34::GeometryProfile::Scope measure(geometry_profile,false);')
    replace(mesh, '++gpu_batches;continue;}++cpu_near_batches;',
            '++gpu_batches;if(geometry_profile.file){++geometry_profile.gpu_batches;geometry_profile.gpu_vertices+=batch.vertices.size();}continue;}'
            '++cpu_near_batches;if(geometry_profile.file)++geometry_profile.near_batches;')
    replace(mesh, '}draw.vertices.reserve(batch.vertices.size()*sizeof(TlVertex));',
            '}if(geometry_profile.file)geometry_profile.cpu_vertices+=batch.vertices.size();draw.vertices.reserve(batch.vertices.size()*sizeof(TlVertex));')
    replace(mesh, 'if(!draw.vertices.empty())device->commands.push_back(std::move(draw));',
            'if(geometry_profile.file)geometry_profile.tl_bytes+=draw.vertices.size();\n'
            '  if(!draw.vertices.empty())device->commands.push_back(std::move(draw));')
    replace(host / "vdd.inc", ' if(host.frame_dump&&(host.frames==1||host.frames%host.frame_dump==0))',
            ' geometry_profile.present(host.frames);\n if(host.frame_dump&&(host.frames==1||host.frames%host.frame_dump==0))')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host_source", type=Path)
    apply(parser.parse_args().host_source.resolve(strict=True))
