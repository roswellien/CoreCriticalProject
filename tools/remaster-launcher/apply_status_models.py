"""Use installed replacement geometry in original player/target damage previews.

Run against a fresh compatible private host source, then compile model_scene.vert
and rebuild that host. Original simulation and render producers still execute.
"""
import argparse
from pathlib import Path
import shutil


def apply(host):
    pending = {}

    def edit(name, old, new):
        path = host / name
        source = pending.get(path, path.read_text(encoding='utf-8'))
        if source.count(new) == 1:
            return
        if source.count(old) != 1:
            raise ValueError(f'{name}: expected one status-model integration anchor: {old[:70]}')
        pending[path] = source.replace(old, new, 1)

    edit('mesh_override_stage.inc', 'bool attached_cockpit{};};',
         'bool attached_cockpit{};bool preview{};OverrideMatrix preview_camera{};};')
    edit('mesh_override_stage.inc', 'std::set<std::pair<unsigned,std::string>>emitted;',
         'bool preview_active{},preview_has_bounds{},preview_fit_applied{};unsigned preview_role{};size_t preview_begin{};'
         'std::array<RECT,4>preview_boxes{};std::array<double,4>preview_bounds{};'
         'std::set<unsigned>preview_emitted;std::set<std::pair<unsigned,std::string>>emitted;')
    edit('mesh_override_stage.inc',
         '// Keep its original geometry/material state; replacements still draw in-world.',
         '// Retain its original diagnostic material state when replacing the geometry.')
    edit('mesh_override_stage.inc', 'if(!override_enabled()||override_status_preview())return previous;',
         'if(!override_enabled())return previous;')
    edit('mesh_override_stage.inc', 'o.scope.skin=o.source_skins.at(root);return previous;',
         'o.scope.skin=o.source_skins.at(root);o.scope.preview=override_status_preview();return previous;')
    edit('mesh_override_stage.inc', 'void override_restore(const OverrideScope&scope)',
         'void override_preview_start(){auto&o=override_state();o.preview_emitted.clear();o.donor_poses.clear();'
         'o.preview_has_bounds=false;o.preview_fit_applied=false;o.preview_role=override_preview_role();o.preview_begin=0;'
         'for(auto&d:host.devices)if(d.in_scene)o.preview_begin=d.commands.size();}\n'
         'void override_restore(const OverrideScope&scope)')
    edit('mesh_override_stage.inc', 'OverrideScope override_begin(unsigned node)',
         '#include "status_model_fit_stage.inc"\nOverrideScope override_begin(unsigned node)')
    edit('mesh_override_stage.inc',
         'if(!override_enabled()||!override_state().scope.node)return false;if(!override_state().emitted.count',
         'if(!override_enabled()||!override_state().scope.node)return false;'
         'if(override_state().scope.preview)return override_state().preview_emitted.count(override_state().scope.node)!=0;'
         'if(!override_state().emitted.count')
    edit('mesh_override_stage.inc', 'void override_emit(){if(!override_enabled())return;auto&o=override_state();if(o.scope.attached_cockpit)return;if(!o.scope.node||o.emitted.count({o.scope.root,o.scope.owner}))return;',
         'void override_emit(const D3DCmd*original=nullptr){if(!override_enabled())return;auto&o=override_state();if(o.scope.attached_cockpit)return;'
         'if(!o.scope.node)return;const bool preview=o.scope.preview;'
         'if(preview&&!original){const unsigned pointer=load(0x5eda90);if(!readable(pointer,4))throw std::runtime_error("Status models: missing model-view stack");o.scope.preview_camera=override_matrix(load(pointer));return;}'
         'if(preview?o.preview_emitted.count(o.scope.node)!=0:o.emitted.count({o.scope.root,o.scope.owner})!=0)return;'
         'unsigned preview_specular=0xff000000U;'
         'if(preview){if(original->vertices.empty())return;unsigned alpha_sum=0,alpha_count=0;'
         'for(size_t i=0;i+32<=original->vertices.size();i+=32){unsigned spec;std::memcpy(&spec,original->vertices.data()+i+20,4);'
         'alpha_sum+=spec>>24;++alpha_count;}'
         'if(!alpha_count)return;preview_specular=((alpha_sum+alpha_count/2)/alpha_count)<<24;}')
    edit('mesh_override_stage.inc', 'auto node_to_camera=override_matrix(load(pointer));',
         'auto node_to_camera=preview?o.scope.preview_camera:override_matrix(load(pointer));')
    edit('mesh_override_stage.inc', 'auto state_=snapshot(*device);',
         'auto state_=preview?*original->state_snapshot:snapshot(*device);')
    edit('mesh_override_stage.inc', 'for(const auto&batch:o.batches)if(batch.model==o.scope.model&&batch.owner==o.scope.owner){',
         'for(const auto&batch:o.batches)if(batch.model==o.scope.model&&batch.owner==o.scope.owner){\n'
         '  if(preview){const auto name=pose_name(o.scope.node,36);'
         'if(!batch.visibility_node.empty()?batch.visibility_node!=name:name!=batch.owner)continue;}')
    edit('mesh_override_stage.inc', 'draw.hud_role=wide_hud_role();zoom_capture_command(draw);',
         'draw.hud_role=wide_hud_role();draw.condition_schematic=preview;zoom_capture_command(draw);')
    edit('mesh_override_stage.inc', 'instance->color=batch.color;',
         'instance->color=batch.color;instance->diagnostic_fog_factor=float(preview_specular>>24)/255.f;')
    edit('mesh_override_stage.inc', 'device->commands.push_back(std::move(draw));triangles+=',
         'if(preview)for(unsigned corner=0;corner<8;++corner){double p[3];for(unsigned a=0;a<3;++a)p[a]=(corner&(1U<<a))?batch.hi[a]:batch.lo[a];'
         'double camera[3];for(unsigned row=0;row<3;++row){camera[row]=batch_to_camera[row*4+3];for(unsigned a=0;a<3;++a)camera[row]+=batch_to_camera[row*4+a]*p[a];}'
         'const double rhw=near_scale/camera[2];override_preview_point(camera[0]*scale_x*rhw+center_x,camera[1]*scale_y*rhw+center_y);}'
         'device->commands.push_back(std::move(draw));triangles+=')
    edit('mesh_override_stage.inc', 'color,0xff000000U,float(v.u),float(v.v)',
         'color,preview_specular,float(v.u),float(v.v)')
    edit('mesh_override_stage.inc', 'o.emitted.insert({o.scope.root,o.scope.owner});',
         'if(preview)o.preview_emitted.insert(o.scope.node);else o.emitted.insert({o.scope.root,o.scope.owner});')
    edit('mesh_override_stage.inc', '<<",\\\"gpu_batches\\\":"<<gpu_batches',
         '<<",\\\"preview\\\":"<<(preview?"true":"false")<<",\\\"role\\\":"<<wide_hud_role()<<",\\\"fog_factor\\\":"<<(preview_specular>>24)<<",\\\"gpu_batches\\\":"<<gpu_batches')
    edit('mfc_stage.hpp', '  if(target==0x4f3a70)distance_restore',
         '  if(target==0x4f73f0&&override_enabled()&&override_status_preview()&&!override_state().preview_active){'
         'override_state().preview_active=true;override_preview_start();'
         'try{result=remaster_body_inner(s,target,p,body);override_preview_finish();override_state().preview_active=false;return result;}'
         'catch(...){override_state().preview_active=false;throw;}}\n'
         '  if(target==0x4f3a70)distance_restore')
    edit('status_preview_clear_stage.inc', 'const unsigned role = status_preview_clear_role();',
         'const unsigned role = status_preview_clear_role();\n    override_preview_record_rect(role, rect);')
    edit('d3d_provider.inc', 'effect_observe(c);if(!override_suppress_draw()',
         'effect_observe(c);if(c.condition_schematic)override_emit(&c);if(!override_suppress_draw()')
    # Original 4F73F0 ends its D3D scene before returning. Fit while commands
    # still exist; EndScene has already cleared the device's in_scene flag.
    edit('d3d_provider.inc', 'void render_scene(D3DDev&d){auto*rt=',
         'void render_scene(D3DDev&d){if(override_state().preview_active)override_preview_finish(&d);auto*rt=')
    edit('vk_scene.hpp', 'std::uint32_t color{};\n    bool world{};',
         'std::uint32_t color{};\n    float diagnostic_fog_factor{1.f};\n    bool world{};')
    edit('vk_scene.hpp', 'mp.base.factor[3] = 1.f;',
         'mp.base.factor[3] = i.diagnostic_fog_factor;')
    edit('vk_scene.hpp', '#include "model_scene_vert.h"',
         '#include "status_model_fit.hpp"\n#include "model_scene_vert.h"')
    for path, source in pending.items():
        path.write_text(source, encoding='utf-8', newline='\n')
    for name in ('status_model_fit.hpp', 'status_model_fit_stage.inc'):
        shutil.copyfile(Path(__file__).parent / 'native-overrides' / name, host / name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host.resolve(strict=True))
