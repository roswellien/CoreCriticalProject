"""Extend the completed renderer with catalogue-defined chassis model bindings.

Apply after apply_additional_chassis.py to a private completed-source copy.
The stock model table stays intact; new resource identities select independent
payloads using a declared compatible original controller/mesh roster.
"""
from pathlib import Path
import argparse
import re


def apply(source):
    source = Path(source)
    names = ('mesh_override_stage.inc', 'additional_skins_stage.inc', 'donor_runtime.inc',
             'mfc_stage.hpp', 'd3d_provider.inc', 'composition.cpp', 'mechlab_skins_stage.inc', 'model_arm_damage.inc')
    prepared = {name: (source / name).read_text(encoding='utf-8') for name in names}
    mesh = prepared['mesh_override_stage.inc']

    def change(old, new):
        nonlocal mesh
        if mesh.count(old) != 1 or new in mesh:
            raise ValueError('Chassis visual patch does not match source: ' + old[:100])
        mesh = mesh.replace(old, new)

    change('size_t count;unsigned lod;};',
           'size_t count;unsigned lod;const char*resource;const char*direct_mesh;const char*direct_texture;const char*source_chassis;};')
    change('inline static constexpr std::array<OverrideModel,36> override_models{{',
           'inline static constexpr std::array<OverrideModel,36> stock_override_models{{')
    prepared['mesh_override_stage.inc'] = mesh
    old = 'if(index>=19)return {}; // Original empty/unassigned selection has no skin additions.'
    text = prepared['mechlab_skins_stage.inc']
    if text.count(old) != 1:
        raise ValueError('Expected original Mech Lab skin identity guard')
    prepared['mechlab_skins_stage.inc'] = text.replace(old, '''if(index>=mw34::chassis::first_runtime_id) {
        const auto& registrations=mw34::chassis::configured_catalog();
        const auto offset=index-mw34::chassis::first_runtime_id;
        if(offset<registrations.size())return registrations[offset].id;
    }
    if(index>=19)return {}; // Preserve the original unassigned sentinel.''')
    old = 'if(model.id!=std::string(plan.model)||model.lod!=plan.lod)continue;'
    text = prepared['model_arm_damage.inc']
    if text.count(old) != 1:
        raise ValueError('Expected recovered arm-damage controller check')
    prepared['model_arm_damage.inc'] = text.replace(old,
        'if(std::string(model.source_chassis?model.source_chassis:model.id)!=plan.model||model.lod!=plan.lod)continue;')
    for name in names:
        prepared[name] = re.sub(r'\boverride_models\b', 'override_models()', prepared[name])
    mesh = prepared['mesh_override_stage.inc']
    pos = mesh.index('}};', mesh.index('stock_override_models{{')) + 3
    begin = mesh.index('stock_override_models{{')
    block, count = re.subn(r'(,\d+)(\},?)$', r'\1,nullptr,nullptr,nullptr,nullptr\2',
                          mesh[begin:pos], flags=re.MULTILINE)
    if count != 36:
        raise ValueError('Expected exactly 36 preserved stock model records')
    mesh = mesh[:begin] + block + mesh[pos:]
    pos = begin + len(block)
    mesh = mesh[:pos] + '''
static const std::vector<OverrideModel>& override_models() {
 static const auto models=[] {
  std::vector<OverrideModel> result(stock_override_models.begin(),stock_override_models.end());
  for(const auto& record:mw34::chassis::configured_catalog()) {
   if(record.visual_template.empty())continue;
   for(unsigned lod=0;lod<2;++lod) {
    const OverrideModel* original=nullptr;
    for(const auto& candidate:stock_override_models)
     if(record.visual_template==candidate.id&&candidate.lod==lod)original=&candidate;
    if(!original)throw std::runtime_error("Additional chassis: unsupported visual controller");
    result.push_back({record.id.c_str(),"","",original->roster,original->count,lod,
      record.resource.c_str(),record.meshes[lod].c_str(),record.textures[lod].c_str(),record.visual_template.c_str()});
   }
  }
  return result;
 }();return models;
}
''' + mesh[pos:]
    change('static const char*override_mesh_env(const OverrideModel&m){',
           'static const char*override_mesh_env(const OverrideModel&m){\n if(m.direct_mesh)return m.direct_mesh;')
    change('std::array<const char*,override_models().size()>p{};',
           'std::vector<const char*>p(override_models().size());')
    change('if(std::getenv(m.mesh_env))return true;', 'if(override_mesh_env(m))return true;')
    change('direct_path?direct_path:std::getenv(alternate_env?alternate_env:model.texture_env)',
           'direct_path?direct_path:model.direct_texture?model.direct_texture:std::getenv(alternate_env?alternate_env:model.texture_env)')
    change('const std::string env=std::string(model.texture_env).substr',
           'if(model.resource)return; // Optional donor normals need an explicit pack binding.\n const std::string env=std::string(model.texture_env).substr')
    change('for(unsigned id=0;id<override_models().size();++id){const auto&m=override_models()[id];if(!override_mesh_env(m))continue;',
           '''const auto root_name=pose_name(root,36);const char* added_resource=chassis_actor_resource(root);
 for(const auto& registration:mw34::chassis::configured_catalog())if(!added_resource&&!registration.visual_template.empty()) {
  const auto& key=registration.resource;
  if(root_name==key||root_name=="mech_"+key+".flt"||root_name=="mech_"+key+"_1.flt")added_resource=key.c_str();
 }
 for(unsigned id=0;id<override_models().size();++id){const auto&m=override_models()[id];
  if(bool(m.resource)!=bool(added_resource)||(m.resource&&std::strcmp(m.resource,added_resource)))continue;
  if(!override_mesh_env(m))continue;''')
    change('mw34::skins::texture_skin(model.id,name)',
           'mw34::skins::texture_skin(model.source_chassis?model.source_chassis:model.id,name)')
    change('void override_emit(const D3DCmd*original=nullptr){',
           '#include "chassis_preview_stage.inc"\nvoid override_emit(const D3DCmd*original=nullptr){')
    change('\n const double near_scale=source_float(0x73fb80),scale_x=',
           '\n double near_scale=source_float(0x73fb80),scale_x=')
    change('if(load(0x72f348)==0)throw',
           'if(donor&&frontend_on()&&override_models()[o.scope.model].resource)'
           'chassis_preview_camera(o.scope.model,donor_root_camera,near_scale,scale_x,scale_y,center_x,center_y,near_clip);\n '
           'if(load(0x72f348)==0)throw')
    prepared['mesh_override_stage.inc'] = mesh
    for filename, old, new in (
        ('composition.cpp', '#include "additional_chassis.hpp"',
         '#include "additional_chassis.hpp"\n#include "additional_mech_preview.hpp"'),
    ):
        text = prepared[filename]
        if text.count(old) != 1 or new in text:
            raise ValueError('Chassis preview patch does not match source: ' + filename)
        prepared[filename] = text.replace(old, new)
    for name, text in prepared.items():
        (source / name).write_text(text, encoding='utf-8')
    (source / 'chassis_preview_stage.inc').write_bytes(
        (Path(__file__).parent / 'native-overrides/chassis_preview_stage.inc').read_bytes())
    from apply_chassis_sockets import apply as apply_sockets
    apply_sockets(source)
    (source / 'additional_skins.hpp').write_bytes(
        (Path(__file__).parent / 'native-overrides/additional_skins.hpp').read_bytes())
    (source / 'additional_mech_preview.hpp').write_bytes(
        (Path(__file__).parent / 'native-overrides/additional_mech_preview.hpp').read_bytes())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    apply(parser.parse_args().source)
