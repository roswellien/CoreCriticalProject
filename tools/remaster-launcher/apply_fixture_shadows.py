"""Add retained fixtures and cube-atlas shadows to a compatible UV-aware host.

Only authored adapters are tracked. Native host/game-derived catalogs remain
local. Compile the edited fragment and fixture shaders, then rebuild the host.
This command does not launch or test the game or publish launcher settings.
"""
from pathlib import Path
import argparse,shutil
from fixture_retention_adapter import adapt

ROOT=Path(__file__).resolve().parents[2]
SHARED=Path(__file__).parent/'native-overrides'

def apply(host,backup):
    pending={}
    def edit(name,old,new):
        p=host/name;s=pending.get(p,p.read_text())
        if s.count(old)!=1:raise ValueError(f'{name}: missing/ambiguous adapter anchor: {old[:80]}')
        pending[p]=s.replace(old,new)
    pending[host/'fixture_lighting.hpp']=adapt((host/'fixture_lighting.hpp').read_text())
    edit('effect_lighting.hpp','std::array<Light,capacity> lights{};','std::array<Light,capacity> lights{};std::array<std::array<float,4>,capacity> shadow{};')
    edit('effect_lighting.hpp','sizeof(Uniform)==16+48*capacity','sizeof(Uniform)==16+64*capacity')
    edit('effect_lighting_settings.hpp','bool enabled{},fixtures{true};','bool enabled{},fixtures{true},fixture_shadows{};unsigned fixture_shadow_size{256};float fixture_retain_distance{160},fixture_fade_distance{32};')
    edit('effect_lighting_settings.hpp','  v.fixture_range_scale=sun::parameter("MW34_FIXTURE_LIGHT_RANGE_SCALE",1,.25f,4);','''  v.fixture_range_scale=sun::parameter("MW34_FIXTURE_LIGHT_RANGE_SCALE",1,.25f,4);
  v.fixture_shadows=sun::flag("MW34_FIXTURE_SHADOWS");
  const float shadowSize=sun::parameter("MW34_FIXTURE_SHADOW_SIZE",256,128,512);
  if(shadowSize!=128&&shadowSize!=256&&shadowSize!=512)throw std::runtime_error("Fixture shadow size must be 128, 256 or 512");
  v.fixture_shadow_size=unsigned(shadowSize);
  v.fixture_retain_distance=sun::parameter("MW34_FIXTURE_LIGHT_RETAIN_DISTANCE",160,32,2000);
  v.fixture_fade_distance=sun::parameter("MW34_FIXTURE_LIGHT_FADE_DISTANCE",32,1,256);
  if(v.fixture_fade_distance>=v.fixture_retain_distance)throw std::runtime_error("Fixture fade band must be smaller than retention distance");''')
    stage=(host/'effect_lighting_stage.inc').read_text()
    start=stage.index('std::uint64_t fixture_source(');end=stage.index('\ndouble effect_time()',start);old=stage[start:end]
    builder=old.replace('std::uint64_t fixture_source(const D3DCmd& draw,const VSurfaceRec& surface){','bool fixture_capture_proof(const D3DCmd& draw,const VSurfaceRec& surface,FixtureSourceProof& proof){')
    begin=builder.index(' const std::uint64_t id=');finish=builder.index(' FixtureSourceProof proof;',begin)
    builder=builder[:begin]+builder[finish:];builder=builder.replace(' FixtureSourceProof proof;proof.surface=',' proof={};proof.surface=')
    tail=builder.index(' if(s.fixture_proofs.size()>=512)');builder=builder[:tail]+' return true;\n}\n';builder=builder.replace('return 0;','return false;')
    builder=builder.replace('member=snapshot(parent+0x60,4)&&snapshot(children+i*4,4);','member=snapshot(parent+0x5c,8)&&snapshot(children+i*4,4);')
    builder=builder.replace('if(!snapshot(node,100))return false;','// Names, type/data/mesh identity and child ownership are stable.\n  // +0x24 visibility/render flags are deliberately not source lifetime.\n  if(!snapshot(node,36)||!snapshot(node+0x34,12)||!snapshot(node+0x5c,8))return false;')
    wrapper=r'''std::uint64_t fixture_source(const D3DCmd& draw,const VSurfaceRec& surface){
 if(!draw.fixture_node||!draw.fixture_polygon)return 0;
 const std::uint64_t id=(std::uint64_t(draw.fixture_node)<<32)|draw.fixture_polygon;
 auto&s=effect_lighting;auto old=s.fixture_proofs.find(id);
 if(old!=s.fixture_proofs.end()&&fixture_proof_valid(old->second))return id;
 FixtureSourceProof proof;if(!fixture_capture_proof(draw,surface,proof))return 0;
 if(s.fixture_proofs.size()>=4096){auto first=s.fixture_proofs.begin();mw34::fixtures::FixtureManager::instance().remove_source(first->first);s.fixture_proofs.erase(first);}
 s.fixture_proofs[id]=std::move(proof);return id;
}
std::shared_ptr<FixtureSourceProof> fixture_caster_proof(const D3DCmd& draw,const VSurfaceRec& surface){
 auto proof=std::make_shared<FixtureSourceProof>();if(!fixture_capture_proof(draw,surface,*proof))return {};
 return proof;
}
'''
    stage=stage[:start]+builder+wrapper+stage[end:]
    stage=stage.replace('manager.begin_frame(host.frames);','manager.begin_frame(host.frames,effect_time());')
    old='budget,settings.strength,settings.fixture_range_scale);';assert stage.count(old)==1
    stage=stage.replace(old,'budget,settings.strength,settings.fixture_range_scale,settings.fixture_retain_distance,settings.fixture_fade_distance);')
    old='mw34::campaign::CampaignManager::instance().enter_world();fixture_frame();';assert stage.count(old)==1
    stage=stage.replace(old,old+'\n scene.world_frame=host.frames;scene.world_generation=mw34::campaign::CampaignManager::instance().generation();scene.world_context=load(0x5f4c8c);\n scene.world_eye={s.camera[3],s.camera[7],s.camera[11]};scene.world_eye_valid=s.view;')
    pending[host/'effect_lighting_stage.inc']=stage
    tl=(host/'sun_tl_capture_stage.inc').read_text()
    old=' if(!world_cell_depth){auto*surface=draw.texture?vsurface(draw.texture):nullptr;if(!surface||!surface_normal_registered(*surface))return;}'
    assert old in tl;tl=tl.replace(old,' // Authenticated world-role opaque objects receive light even without authored normal maps.')
    old=' if(rs[D3DRENDERSTATE_ALPHATESTENABLE]){static const bool world_normals=std::getenv("MW34_WORLD_NORMALS")!=nullptr;if(!world_normals)return;auto*surface=draw.texture?vsurface(draw.texture):nullptr;if(!surface||!surface_world_normal_registered(*surface))return;}'
    assert old in tl;tl=tl.replace(old,' // Alpha-tested world objects retain their original cutout test in colour and shadow passes.')
    tl=tl.replace('||!draw.texture)return;',')return;')
    pending[host/'sun_tl_capture_stage.inc']=tl
    edit('sun_lighting_stage.inc','void sun_capture_model(mw34::vkscene::ModelInstance& instance,unsigned,','void sun_capture_model(mw34::vkscene::ModelInstance& instance,unsigned source_node,')
    p=host/'sun_lighting_stage.inc';s=pending[p];at=s.index('void sun_capture_model(');s=s[:at]+s[at:].replace(' instance.sun_normal=',' instance.shadow_source=source_node;\n instance.sun_normal=',1);pending[p]=s
    edit('vk_scene.hpp','#include "effect_lighting_settings.hpp"','#include "effect_lighting_settings.hpp"\n#include "fixture_shadow.hpp"\n#include "fixture_shadow_vert.h"\n#include "fixture_shadow_frag.h"\n#include <functional>')
    edit('vk_scene.hpp','bool sun_eligible{}; };','bool sun_eligible{};std::uint64_t shadow_source{}; };')
    edit('vk_scene.hpp','bool condition_schematic{};','std::uint64_t shadow_source{};std::function<bool()> shadow_valid;bool condition_schematic{};')
    edit('vk_scene.hpp','    double detail_time{};','    double detail_time{};\n    std::uint64_t world_frame{},world_generation{},world_context{};std::array<float,3> world_eye{};bool world_eye_valid{};')
    edit('vk_scene.hpp','    std::map<std::uint64_t,ModelBuffer> model_buffers;','    std::map<std::uint64_t,ModelBuffer> model_buffers;\n#include "fixture_shadow_stage.inc"')
    edit('vk_scene.hpp','        bool sunScene=false;','        const auto fixtureLights=prepare_fixture_shadows(s,bound);\n        bool sunScene=false;')
    edit('vk_scene.hpp','const auto& fx=s.hud||s.frontend_canvas?noEffects:s.effect_lights;','const auto& fx=s.hud||s.frontend_canvas?noEffects:fixtureLights;')
    edit('vk_scene.hpp','if (descriptorCapacity < s.draws.size() + 1) pool(unsigned(s.draws.size() + 64));','if (descriptorCapacity < s.draws.size()+fixtureFrameCasters.size()+1) pool(unsigned(s.draws.size()+fixtureFrameCasters.size()+64));')
    edit('vk_scene.hpp','        std::map<std::pair<Tex *, unsigned>, VkDescriptorSet> normalSets;','        fixture_shadow_sets(sets);\n        std::map<std::pair<Tex *, unsigned>, VkDescriptorSet> normalSets;')
    edit('vk_scene.hpp','std::array<VkWriteDescriptorSet,3> w{};','std::array<VkWriteDescriptorSet,4> w{};')
    edit('vk_scene.hpp','            f.vkUpdateDescriptorSets(device,3,w.data(),0,nullptr);','            VkDescriptorImageInfo fixtureInfo{fixtureShadowSampler,fixtureShadowView,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};\n            w[3].dstBinding=3;w[3].descriptorType=VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;w[3].pImageInfo=&fixtureInfo;\n            f.vkUpdateDescriptorSets(device,4,w.data(),0,nullptr);')
    edit('vk_scene.hpp','        if(shadowFrame.active&&!shadowFrame.reused)record_shadow(shadowFrame);','        if(shadowFrame.active&&!shadowFrame.reused)record_shadow(shadowFrame);\n        record_fixture_shadows(fixtureLights);')
    edit('vk_scene.hpp','const std::array<VkDescriptorSetLayoutBinding,3> sb','const std::array<VkDescriptorSetLayoutBinding,4> sb')
    edit('vk_scene.hpp','{2,VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,1,VK_SHADER_STAGE_FRAGMENT_BIT,nullptr}}};','{2,VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,1,VK_SHADER_STAGE_FRAGMENT_BIT,nullptr},\n                    {3,VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,1,VK_SHADER_STAGE_FRAGMENT_BIT,nullptr}}};')
    edit('vk_scene.hpp','si.bindingCount=3;si.pBindings=sb.data();','si.bindingCount=4;si.pBindings=sb.data();')
    edit('vk_scene.hpp','{init_shadow();const auto& sun=','{init_shadow();init_fixture_shadow();const auto& sun=')
    anchor='        if(shadowImage)barrier(shadowImage, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, 0, VK_ACCESS_SHADER_READ_BIT, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, VK_IMAGE_ASPECT_DEPTH_BIT);'
    edit('vk_scene.hpp',anchor,anchor+'\n        if(fixtureShadowImage)barrier(fixtureShadowImage,VK_IMAGE_LAYOUT_UNDEFINED,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,0,VK_ACCESS_SHADER_READ_BIT,VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT,VK_IMAGE_ASPECT_DEPTH_BIT);')
    edit('vk_scene.hpp','VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,n*2+1','VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER,n*2+2')
    edit('vk_scene.hpp','        if(shadowPipeline)f.vkDestroyPipeline(device,shadowPipeline,nullptr);','        drop_fixture_shadow();\n        if(shadowPipeline)f.vkDestroyPipeline(device,shadowPipeline,nullptr);')
    edit('vk_scene.hpp','return mw34::sun::settings().enabled&&(d.sky||(d.sun_tl&&(d.push.mode[0]&4))||(d.model&&d.model->sun_eligible&&(!d.model->world||(d.push.mode[0]&4))));','return mw34::sun::settings().enabled&&(d.sky||d.sun_tl||(d.model&&d.model->sun_eligible));')
    edit('d3d_provider.inc','  dr.sun_tl=c.sun_tl;dr.sky_view=c.sky_view;','''  if(mw34::effects::settings().fixture_shadows&&c.model&&c.model->world&&c.fixture_node&&c.fixture_polygon&&tex){
   SunCaptureFp preserve;mw34::vkscene::HostFpEnvironment fp;
   if(auto*surface=vsurface(tex))if(auto proof=fixture_caster_proof(c,*surface)){
    dr.shadow_source=(std::uint64_t(c.fixture_node)<<32)|c.fixture_polygon;
    dr.shadow_valid=[this,proof]{SunCaptureFp preserve;return fixture_proof_valid(*proof);};
   }
  }
  dr.sun_tl=c.sun_tl;dr.sky_view=c.sky_view;''')
    edit('sun_scene.frag',' EffectLight lights[64];',' EffectLight lights[64];\n vec4 shadowMeta[64];')
    edit('sun_scene.frag','vec3 effectIllumination(vec3 p,vec3 n){',(SHARED/'fixture_shadow_receiver.glsl').read_text()+'\nvec3 effectIllumination(vec3 p,vec3 n){')
    edit('sun_scene.frag','attenuation*attenuation*diffuse*spotFactor;','attenuation*attenuation*diffuse*spotFactor*fixtureVisibility(i,p,n);')
    tl=(SHARED/'sun_tl.vert').read_text().replace('sun.extra.w>1.5?unpack(diffuse)','(sun.extra.w>1.5||(draw.mode.x&4u)==0u)?unpack(diffuse)')
    pending[host/'sun_tl.vert']=tl
    pending[host/'fixture_shadow.hpp']=(ROOT/'runtime/graphics/fixture_shadow.hpp').read_text()
    for name in ['fixture_shadow.vert','fixture_shadow.frag','fixture_shadow_stage.inc']:pending[host/name]=(SHARED/name).read_text()
    backup.mkdir(parents=True,exist_ok=False)
    for p,text in pending.items():
        if p.exists():shutil.copy2(p,backup/p.name)
        p.write_text(text,encoding='utf-8',newline='\n')
    print('Applied retained fixtures, source-valid shadow casters, receiving objects and cube-atlas shadows to',host)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('host',type=Path);parser.add_argument('--backup',required=True,type=Path);args=parser.parse_args();apply(args.host.resolve(strict=True),args.backup.resolve())
