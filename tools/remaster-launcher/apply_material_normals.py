"""Install the shared, validated material-normal reader in a lit native host.

Apply to a private copy. Validates and computes the complete edit before writing;
preserves the renderer, lighting, geometry, donor solver and model-path caches.
"""
from pathlib import Path
import argparse
import shutil

READER = '''void override_load_normals(const OverrideModel&model,size_t first,size_t end){
 if(!mw34::sun::settings().enabled||!mw34::materials::normal_maps_enabled())return;
 const std::string env=std::string(model.texture_env).substr(0,std::strlen(model.texture_env)-9)+"_NORMALS";
 const char*path=std::getenv(env.c_str());if(!path||!*path)return;
 std::ifstream file(path,std::ios::binary);if(!file)throw std::runtime_error("Configured replacement normal sidecar is missing: "+env);
 auto&o=override_state();std::vector<std::string>materials;
 for(size_t at=first;at<end;++at){const int index=o.batches[at].texture;
  if(index<0||size_t(index)>=o.textures.size())throw std::runtime_error("Normal map requires its albedo material binding");
  materials.push_back(o.textures[index].name);}
 auto pack=mw34::materials::read_normals(file,materials);
 const size_t offset=o.normal_textures.size();
 if(offset+pack.images.size()>size_t(std::numeric_limits<int>::max()))throw std::runtime_error("Normal image index overflow");
 std::vector<int>indices;
 for(auto&image:pack.images){auto found=std::find_if(o.normal_textures.begin(),o.normal_textures.end(),[&](const OverrideTexture&existing){return existing.width==image.width&&existing.height==image.height&&existing.hash==image.hash&&existing.pixels32==image.pixels;});
  if(found!=o.normal_textures.end()){indices.push_back(int(found-o.normal_textures.begin()));continue;}
  indices.push_back(int(o.normal_textures.size()));OverrideTexture t{};t.name=std::move(image.name);t.width=image.width;t.height=image.height;t.hash=image.hash;t.pixels32=std::move(image.pixels);o.normal_textures.push_back(std::move(t));}
 for(size_t at=first;at<end;++at){const auto index=pack.bindings[at-first];o.batches[at].normal_texture=index==mw34::materials::no_normal?-1:indices[index];}
 o.log<<"{\\"event\\":\\"normals_loaded\\",\\"model\\":\\""<<model.id<<"\\",\\"lod\\":"<<model.lod<<",\\"materials\\":"<<pack.images.size()<<",\\"format\\":\\"RGBA8888\\",\\"binding\\":\\"material-name\\"}\\n";
}
'''


def apply(host):
    stage = host / 'mesh_override_stage.inc'
    text = stage.read_text()
    begin = text.index('void override_load_normals(')
    end = text.index('void override_load_ground_normals(', begin)
    updated = text[:begin] + READER + text[end:]
    vk = host / 'vk_scene.hpp'
    renderer = vk.read_text()
    include = '#include "material_normals.hpp"'
    if include not in renderer:
        if renderer.count('#include "sun_lighting.hpp"') != 1:
            raise ValueError('Material normals require a lit host')
        renderer = renderer.replace('#include "sun_lighting.hpp"', '#include "sun_lighting.hpp"\n' + include)
    if 'mw34::materials::normal_maps_enabled()' not in renderer:
        anchor='                std::memcpy(static_cast<unsigned char*>(sunBuffer.mapped)+at*sunStride,&u,sizeof(u));sunScene=true;'
        if renderer.count(anchor)!=1:raise ValueError('Missing per-draw lighting uniform anchor')
        renderer=renderer.replace(anchor,
            '                if(!mw34::materials::normal_maps_enabled()||draw.normal_texture<0)u.extra[1]=0;\n'+anchor)
    if 'const bool normal_active=' not in renderer:
        anchor='                Tex *t = (d.normal_texture >= 0 && size_t(d.normal_texture) < bound.size()) ? bound[size_t(d.normal_texture)] : &flatNormal;'
        if renderer.count(anchor)!=1:raise ValueError('Missing normal descriptor binding anchor')
        renderer=renderer.replace(anchor,
            '                const auto&normal_settings=mw34::sun::settings();\n'
            '                const float normal_strength=d.model&&!d.model->world?normal_settings.normal_strength:normal_settings.ground_normal_strength;\n'
            '                const bool normal_active=mw34::materials::normal_maps_enabled()&&normal_strength>0;\n'
            '                Tex *t = (normal_active && d.normal_texture >= 0 && size_t(d.normal_texture) < bound.size()) ? bound[size_t(d.normal_texture)] : &flatNormal;')
    mfc=host/'mfc_stage.hpp';stage_text=mfc.read_text()
    surface_include='#include "surface_normals_stage.inc"'
    if surface_include not in stage_text:
        anchor='#include "sun_tl_capture_stage.inc"'
        if stage_text.count(anchor)!=1:raise ValueError('Missing sun TL capture adapter')
        stage_text=stage_text.replace(anchor,surface_include+'\n'+anchor)
    capture=host/'sun_tl_capture_stage.inc';capture_text=capture.read_text()
    old='!mw34::sun::settings().enabled||!world_cell_depth||draw.model'
    if old in capture_text:
        capture_text=capture_text.replace(old,'!mw34::sun::settings().enabled||draw.model')
    # Material admission is independent of perturbation: maps-off reads only
    # the registration header. Preserve the bounded stock-material admission.
    capture_text=capture_text.replace(
        ' if(!world_cell_depth){auto*surface=draw.texture?vsurface(draw.texture):nullptr;'
        'if(!surface||surface_normal_index(*surface)<0)return;}\n','')
    anchor=' OverrideMatrix camera_world;if(!sun_camera_world(camera_world))return;'
    if 'surface_normal_registered(*surface)' not in capture_text:
        if anchor not in capture_text:raise ValueError('Missing TL material admission anchor')
        capture_text=capture_text.replace(anchor,
            ' if(!world_cell_depth){auto*surface=draw.texture?vsurface(draw.texture):nullptr;'
            'if(!surface||!surface_normal_registered(*surface))return;}\n'+anchor,1)
    # Cutout world surfaces retain their original alpha test. Admit only
    # registered world textures, preserving the blend/depth/camera exclusions.
    alpha=' if(rs[D3DRENDERSTATE_ALPHABLENDENABLE]||rs[D3DRENDERSTATE_ALPHATESTENABLE]||'
    alpha_admission=(' if(rs[D3DRENDERSTATE_ALPHATESTENABLE]){static const bool world_normals=std::getenv("MW34_WORLD_NORMALS")!=nullptr;'
                     'if(!world_normals)return;auto*surface=draw.texture?vsurface(draw.texture):nullptr;'
                     'if(!surface||!surface_world_normal_registered(*surface))return;}\n')
    if alpha in capture_text:
        capture_text=capture_text.replace(alpha,' if(rs[D3DRENDERSTATE_ALPHABLENDENABLE]||',1)
    capture_text=capture_text.replace(alpha_admission,'')
    depth_guard='    !rs[D3DRENDERSTATE_ZENABLE]||!rs[D3DRENDERSTATE_ZWRITEENABLE]||!draw.texture)return;\n'
    if capture_text.count(depth_guard)!=1:raise ValueError('Missing world cutout depth guard')
    capture_text=capture_text.replace(depth_guard,depth_guard+alpha_admission,1)
    provider=host/'d3d_provider.inc';provider_text=provider.read_text()
    anchor='  if(bind_normal_idx>=0){const auto&o=override_state();'
    if 'surface_normal_index(*surface)' not in provider_text:
        if provider_text.count(anchor)!=1:raise ValueError('Missing normal material bind anchor')
        provider_text=provider_text.replace(anchor,
            '  if(bind_normal_idx<0&&(c.sun_tl||(c.model&&c.model->world))&&tex)'
            'if(auto*surface=vsurface(tex))bind_normal_idx=surface_normal_index(*surface);\n'+anchor)
    # Surface-only materials must work with original models as well.
    updated=updated.replace('if(std::getenv("MW34_GROUND_NORMALS"))return true;',
                            'if(std::getenv("MW34_GROUND_NORMALS")||std::getenv("MW34_SURFACE_NORMALS"))return true;')
    updated=updated.replace('if(std::getenv("MW34_GROUND_NORMALS")||std::getenv("MW34_SURFACE_NORMALS"))return true;',
                            'if(std::getenv("MW34_GROUND_NORMALS")||std::getenv("MW34_SURFACE_NORMALS")||std::getenv("MW34_WORLD_NORMALS"))return true;')
    shutil.copyfile(Path(__file__).resolve().parents[2] / 'runtime/graphics/material_normals.hpp', host / 'material_normals.hpp')
    shutil.copyfile(Path(__file__).parent / 'native-overrides/surface_normals_stage.inc',host / 'surface_normals_stage.inc')
    shutil.copyfile(Path(__file__).parent / 'native-overrides/world_normals_pages.inc',host / 'world_normals_pages.inc')
    stage.write_text(updated)
    vk.write_text(renderer)
    mfc.write_text(stage_text)
    capture.write_text(capture_text)
    provider.write_text(provider_text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source', type=Path)
    apply(parser.parse_args().host_source.resolve(strict=True))
