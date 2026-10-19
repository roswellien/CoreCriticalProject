"""Optional visual adapter patch. Original material identity, pose and simulation remain source-owned."""
from pathlib import Path
import argparse,shutil
parser=argparse.ArgumentParser(description='Bind original Bushwacker distance geometry and per-instance skin D. Requires validated all-models adapter.')
parser.add_argument('host_source',type=Path);parser.add_argument('--lod1-roster',type=Path,required=True)
a=parser.parse_args();p=a.host_source/'mesh_override_stage.inc';s=p.read_text()
if 'std::array<OverrideModel,29>' not in s:raise RuntimeError('Expected the validated 29-binding all-models adapter')
roster=a.lod1_roster.read_text()
if 'std::array<OverrideSourceMesh,13> override_bushwacker_lod1_meshes' not in roster:raise RuntimeError('Expected recovered 13-part original Bushwacker LOD1 roster')
shutil.copy2(a.lod1_roster,a.host_source/'override_bushwacker_lod1.inc')
s=s.replace('#include "override_source_roster.inc"','#include "override_source_roster.inc"\n#include "override_bushwacker_lod1.inc"')
s=s.replace('std::array<OverrideModel,29>','std::array<OverrideModel,30>')
needle=' {"strider","MW34_STRIDER_LOD1_MESH","MW34_STRIDER_LOD1_TEXTURES",override_strider_lod1_meshes.data(),override_strider_lod1_meshes.size(),1}'
assert s.count(needle)==1
s=s.replace(needle,needle+',\n {"bushwacker","MW34_BUSHWACKER_LOD1_MESH","MW34_BUSHWACKER_LOD1_TEXTURES",override_bushwacker_lod1_meshes.data(),override_bushwacker_lod1_meshes.size(),1}')
s=s.replace('std::vector<unsigned>vertex_bones;};','std::vector<unsigned>vertex_bones;int skin_d_texture{-1};};')
s=s.replace('unsigned root{},model{};};','unsigned root{},model{};unsigned skin{};};')
s=s.replace('std::map<unsigned,int>validated_roots;','std::map<unsigned,int>validated_roots;std::map<unsigned,unsigned>source_skins;')
s=s.replace('void override_load_textures(const OverrideModel&model,size_t first,size_t end){','void override_load_textures(const OverrideModel&model,size_t first,size_t end,const char*alternate_env=nullptr){')
s=s.replace('std::getenv(model.texture_env);if(!path)return;','std::getenv(alternate_env?alternate_env:model.texture_env);if(!path)return;')
s=s.replace('o.batches[at].texture=int(offset+index);o.batches[at].color=0xffffffff;','if(alternate_env)o.batches[at].skin_d_texture=int(offset+index);else o.batches[at].texture=int(offset+index);o.batches[at].color=0xffffffff;')
s=s.replace('  override_load_textures(model,first,o.batches.size());','  override_load_textures(model,first,o.batches.size());\n  if(std::string(model.id)=="bushwacker")override_load_textures(model,first,o.batches.size(),model.lod?"MW34_BUSHWACKER_LOD1_SKIN_D_TEXTURES":"MW34_BUSHWACKER_SKIN_D_TEXTURES");')
needle=' o.validated_roots.emplace(root,result);'
impl='''

 // 53F2E0 reads polygon[7] as material*, material+16 as texture-ref*;
 // its 40-byte reference stores the original 32-byte name after data/handle.
 // Inspect only this validated chassis tree, freshly for each scene/LOD.
 if(result>=0&&std::string(override_models[result].id)=="bushwacker"){
  bool primary=false,skin_d=false;
  for(unsigned node:queue){bool source_part=false;const auto part_name=pose_name(node,36);const auto&model=override_models[result];for(size_t i=0;i<model.count;++i)if(part_name==model.roster[i].name){source_part=true;break;}if(!source_part)continue;const unsigned mesh=load(node+0x3c);if(!mesh)continue;
   if(!readable(mesh,0x38))throw std::runtime_error("Bushwacker skin: unreadable source mesh");
   const unsigned count=load(mesh+0x10),polys=load(mesh+0x34);
   if(count>1000||(count&&!readable(polys,count*36)))throw std::runtime_error("Bushwacker skin: invalid original polygon table");
   for(unsigned i=0;i<count;++i){const unsigned mat=load(polys+i*36+28);if(!readable(mat,20))throw std::runtime_error("Bushwacker skin: invalid original material");
    if(!(load(mat)&0x100))continue;const unsigned ref=load(mat+16);if(!ref||!readable(ref,40))throw std::runtime_error("Bushwacker skin: invalid original texture reference");
    const auto name=pose_name(ref+8,32);
    if(name.size()==14&&name.rfind("bushwacker",0)==0&&name.substr(12)=="_d")skin_d=true;
    if(name.size()==12&&name.rfind("bushwacker",0)==0)primary=true;
   }
  }
  const unsigned skin=skin_d?3:0;o.source_skins[root]=skin;
  if(skin_d&&primary)throw std::runtime_error("Bushwacker skin: mixed primary and D material identity");
  if(skin_d){bool loaded=false;for(const auto&b:o.batches)if(b.model==unsigned(result)&&b.skin_d_texture>=0){loaded=true;break;}
   if(!loaded)result=-1; // Keep original skin D visibly if its optional pack is absent.
  }
  if(o.announced_roots.emplace(root,0xffff0000U+skin).second){o.log<<"{\\"event\\":\\"source_skin\\",\\"root\\":"<<root<<",\\"skin\\":"<<skin<<",\\"replacement_available\\":"<<(result>=0?"true":"false")<<"}\\n";o.log.flush();}
 }
'''
assert s.count(needle)==1;s=s.replace(needle,impl+needle)
s=s.replace('o.scope={node,mesh->owner,owner_to_node,root,unsigned(id)};','o.scope={node,mesh->owner,owner_to_node,root,unsigned(id)};if(std::string(model.id)=="bushwacker")o.scope.skin=o.source_skins.at(root);')
s=s.replace('override_state().validated_roots.clear();','override_state().validated_roots.clear();override_state().source_skins.clear();')
s=s.replace('draw.override_texture=batch.texture;','draw.override_texture=o.scope.skin==3?batch.skin_d_texture:batch.texture;')
s=s.replace('<<o.scope.root<<",\\"owner\\":','<<o.scope.root<<",\\"skin\\":"<<o.scope.skin<<",\\"owner\\":')
p.write_text(s);print('PER_INSTANCE_SKIN_D_APPLIED')
