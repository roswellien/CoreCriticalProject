// Optional geometry-only test. Source simulation, pose and render-producer side effects continue.
struct OverrideSourceMesh{const char*name;unsigned vertices;const char*owner;};
#include "override_source_roster.inc"
#include "override_bushwacker_lod1.inc"
#include "override_new_rosters.inc"
#include "override_lod1_rosters.inc"
#include "override_next_rosters.inc"
#include "override_next_lod1_rosters.inc"
#include "override_additional_rosters.inc"
#include "override_additional_lod1_rosters.inc"
#include "override_cockpit_rosters.inc"
#include "override_avatar_rosters.inc"
#include "override_owens_firefly_rosters.inc"
struct OverrideModel{const char*id;const char*mesh_env;const char*texture_env;const OverrideSourceMesh*roster;size_t count;unsigned lod;const char*resource;const char*direct_mesh;const char*direct_texture;const char*source_chassis;};
inline static constexpr std::array<OverrideModel,36> stock_override_models{{
 {"bushwacker","MW34_BUSHWACKER_TEST","MW34_BUSHWACKER_TEXTURES",override_source_meshes.data(),override_source_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"madcat","MW34_MADCAT_MESH","MW34_MADCAT_TEXTURES",override_madcat_meshes.data(),override_madcat_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"vulture","MW34_VULTURE_MESH","MW34_VULTURE_TEXTURES",override_vulture_meshes.data(),override_vulture_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"thor","MW34_THOR_MESH","MW34_THOR_TEXTURES",override_thor_meshes.data(),override_thor_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"madcat","MW34_MADCAT_LOD1_MESH","MW34_MADCAT_LOD1_TEXTURES",override_madcat_lod1_meshes.data(),override_madcat_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr},
 {"vulture","MW34_VULTURE_LOD1_MESH","MW34_VULTURE_LOD1_TEXTURES",override_vulture_lod1_meshes.data(),override_vulture_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr},
 {"thor","MW34_THOR_LOD1_MESH","MW34_THOR_LOD1_TEXTURES",override_thor_lod1_meshes.data(),override_thor_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr},
 {"orion","MW34_ORION_MESH","MW34_ORION_TEXTURES",override_orion_meshes.data(),override_orion_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"daishi","MW34_DAISHI_MESH","MW34_DAISHI_TEXTURES",override_daishi_meshes.data(),override_daishi_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"shadowcat","MW34_SHADOWCAT_MESH","MW34_SHADOWCAT_TEXTURES",override_shadowcat_meshes.data(),override_shadowcat_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"orion","MW34_ORION_LOD1_MESH","MW34_ORION_LOD1_TEXTURES",override_orion_lod1_meshes.data(),override_orion_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr},
 {"daishi","MW34_DAISHI_LOD1_MESH","MW34_DAISHI_LOD1_TEXTURES",override_daishi_lod1_meshes.data(),override_daishi_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr},
 {"shadowcat","MW34_SHADOWCAT_LOD1_MESH","MW34_SHADOWCAT_LOD1_TEXTURES",override_shadowcat_lod1_meshes.data(),override_shadowcat_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr},
 {"puma","MW34_PUMA_MESH","MW34_PUMA_TEXTURES",override_puma_meshes.data(),override_puma_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"annihilator","MW34_ANNIHILATOR_MESH","MW34_ANNIHILATOR_TEXTURES",override_annihilator_meshes.data(),override_annihilator_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"cauldron","MW34_CAULDRON_MESH","MW34_CAULDRON_TEXTURES",override_cauldron_meshes.data(),override_cauldron_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"sunder","MW34_SUNDER_MESH","MW34_SUNDER_TEXTURES",override_sunder_meshes.data(),override_sunder_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"supernova","MW34_SUPERNOVA_MESH","MW34_SUPERNOVA_TEXTURES",override_supernova_meshes.data(),override_supernova_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"blackhawk","MW34_BLACKHAWK_MESH","MW34_BLACKHAWK_TEXTURES",override_blackhawk_meshes.data(),override_blackhawk_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"champion","MW34_CHAMPION_MESH","MW34_CHAMPION_TEXTURES",override_champion_meshes.data(),override_champion_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"strider","MW34_STRIDER_MESH","MW34_STRIDER_TEXTURES",override_strider_meshes.data(),override_strider_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"puma","MW34_PUMA_LOD1_MESH","MW34_PUMA_LOD1_TEXTURES",override_puma_lod1_meshes.data(),override_puma_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr},
 {"annihilator","MW34_ANNIHILATOR_LOD1_MESH","MW34_ANNIHILATOR_LOD1_TEXTURES",override_annihilator_lod1_meshes.data(),override_annihilator_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr},
 {"cauldron","MW34_CAULDRON_LOD1_MESH","MW34_CAULDRON_LOD1_TEXTURES",override_cauldron_lod1_meshes.data(),override_cauldron_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr},
 {"sunder","MW34_SUNDER_LOD1_MESH","MW34_SUNDER_LOD1_TEXTURES",override_sunder_lod1_meshes.data(),override_sunder_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr},
 {"supernova","MW34_SUPERNOVA_LOD1_MESH","MW34_SUPERNOVA_LOD1_TEXTURES",override_supernova_lod1_meshes.data(),override_supernova_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr},
 {"blackhawk","MW34_BLACKHAWK_LOD1_MESH","MW34_BLACKHAWK_LOD1_TEXTURES",override_blackhawk_lod1_meshes.data(),override_blackhawk_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr},
 {"champion","MW34_CHAMPION_LOD1_MESH","MW34_CHAMPION_LOD1_TEXTURES",override_champion_lod1_meshes.data(),override_champion_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr},
 {"strider","MW34_STRIDER_LOD1_MESH","MW34_STRIDER_LOD1_TEXTURES",override_strider_lod1_meshes.data(),override_strider_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr},
 {"bushwacker","MW34_BUSHWACKER_LOD1_MESH","MW34_BUSHWACKER_LOD1_TEXTURES",override_bushwacker_lod1_meshes.data(),override_bushwacker_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr},
 {"avatar","MW34_AVATAR_MESH","MW34_AVATAR_TEXTURES",override_avatar_meshes.data(),override_avatar_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"avatar","MW34_AVATAR_LOD1_MESH","MW34_AVATAR_LOD1_TEXTURES",override_avatar_lod1_meshes.data(),override_avatar_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr},
 {"owens","MW34_OWENS_MESH","MW34_OWENS_TEXTURES",override_owens_meshes.data(),override_owens_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"owens","MW34_OWENS_LOD1_MESH","MW34_OWENS_LOD1_TEXTURES",override_owens_lod1_meshes.data(),override_owens_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr},
 {"firefly","MW34_FIREFLY_MESH","MW34_FIREFLY_TEXTURES",override_firefly_meshes.data(),override_firefly_meshes.size(),0,nullptr,nullptr,nullptr,nullptr},
 {"firefly","MW34_FIREFLY_LOD1_MESH","MW34_FIREFLY_LOD1_TEXTURES",override_firefly_lod1_meshes.data(),override_firefly_lod1_meshes.size(),1,nullptr,nullptr,nullptr,nullptr}
}};
static const std::map<std::pair<std::string,unsigned>,std::vector<OverrideSourceMesh>>& owned_override_rosters() {
 static const auto rosters=[] {
  std::map<std::pair<std::string,unsigned>,std::vector<OverrideSourceMesh>> result;
  for(const auto& r:mw34::chassis::configured_catalog())if(r.owned_visuals)
   for(unsigned lod=0;lod<2;++lod) {
    auto& rows=result[{r.id,lod}];
    for(const auto& mesh:r.owned_rosters[lod])rows.push_back({mesh.name.c_str(),mesh.vertices,mesh.owner.c_str()});
   }
  return result;
 }();return rosters;
}
static const std::vector<OverrideModel>& override_models() {
 static const auto models=[] {
  std::vector<OverrideModel> result(stock_override_models.begin(),stock_override_models.end());
  for(const auto& record:mw34::chassis::configured_catalog()) {
   if(record.owned_visuals) {
    for(unsigned lod=0;lod<2;++lod) {
     const auto& roster=owned_override_rosters().at({record.id,lod});
     result.push_back({record.id.c_str(),"","",roster.data(),roster.size(),lod,
       record.resource.c_str(),record.meshes[lod].c_str(),record.textures[lod].c_str(),record.resource.c_str()});
    }
    continue;
   }
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

// Model slot paths and roster names are fixed for the process; read them once.
static const char*override_mesh_env(const OverrideModel&m){
 if(m.direct_mesh)return m.direct_mesh;
 static const auto paths=[]{std::vector<const char*>p(override_models().size());for(size_t i=0;i<p.size();++i)p[i]=std::getenv(override_models()[i].mesh_env);return p;}();
 return paths[size_t(&m-override_models().data())];}
static bool override_candidate_name(const std::string&name){
 static const auto names=[]{std::set<std::string>s;for(const auto&m:override_models())if(override_mesh_env(m))for(size_t at=0;at<m.count;++at)s.insert(m.roster[at].name);return s;}();
 return names.count(name)!=0;}
#include "override_arm_damage_plans.inc"
using OverrideVertex=mw34::vkscene::ModelVertex;
struct OverrideBatch{std::string owner;std::string visibility_node;unsigned color;std::vector<OverrideVertex>vertices;int texture{-1};int normal_texture{-1};unsigned model{};std::shared_ptr<const mw34::vkscene::ModelGeometry>geometry;std::array<float,3>lo{},hi{};std::string placement_frame;std::array<float,3>placement_offset{};unsigned donor_bone{~0U};std::vector<unsigned>vertex_bones;std::vector<int> skin_textures=std::vector<int>(8,-1);std::string joint_frame;std::array<float,3>joint_offset{};std::string anchor_control;std::array<float,3>anchor_position{};std::shared_ptr<const mw34::materials::SurfaceMaterialRecord>surface_material{};};
using OverrideMatrix=std::array<double,16>;
struct OverrideScope{unsigned node{};std::string owner;OverrideMatrix owner_to_node{};unsigned root{},model{};unsigned skin{};bool attached_cockpit{};bool preview{};OverrideMatrix preview_camera{};};
struct OverrideMxcsr{unsigned value=_mm_getcsr();~OverrideMxcsr(){_mm_setcsr(value);}};
struct OverrideTexture{std::string name;unsigned width,height;std::uint64_t hash;std::vector<std::uint16_t>pixels;std::vector<std::uint32_t>pixels32;};
struct OverrideDonorInstance{std::map<std::string,OverrideMatrix>raw;mw34::donor::Pose pose;double gait{};};
struct OverrideState{std::map<unsigned,std::pair<size_t,size_t>> model_ranges;std::set<std::pair<unsigned,unsigned>> skin_attempts;std::set<std::pair<unsigned,std::string>>attached_cockpit_nodes;std::map<unsigned,mw34::donor::Rig>donor_rigs;std::map<std::pair<unsigned,unsigned>,OverrideDonorInstance>donor_poses;std::set<std::pair<unsigned,unsigned>>retarget_clamp_roots;std::vector<OverrideTexture>textures,normal_textures,surface_material_textures;int ground_normal_texture{-1};std::vector<std::array<unsigned,5>> ground_normal_bindings;bool loaded{};std::vector<OverrideBatch>batches;OverrideScope scope;std::map<unsigned,int>validated_roots;std::map<unsigned,unsigned>source_skins;std::map<std::pair<unsigned,std::string>,bool>active_nodes;std::set<std::pair<unsigned,unsigned>>announced_roots;std::set<std::pair<unsigned,unsigned>>damage_announced;bool preview_active{},preview_has_bounds{},preview_fit_applied{};unsigned preview_role{};size_t preview_begin{};std::array<RECT,4>preview_boxes{};std::array<double,4>preview_bounds{};std::set<unsigned>preview_emitted;std::set<std::pair<unsigned,std::string>>emitted;std::ofstream log;unsigned emitted_frames{},last_frame{~0U};};
static OverrideState&override_state(){static OverrideState state;return state;}
static bool override_enabled(){static const bool enabled=[](){for(const auto&m:override_models())if(override_mesh_env(m))return true;if(std::getenv("MW34_GROUND_NORMALS")||std::getenv("MW34_SURFACE_NORMALS")||std::getenv("MW34_WORLD_NORMALS"))return true;return false;}();return enabled;}
static OverrideMatrix override_identity(){return {1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};}
static OverrideMatrix override_product(const OverrideMatrix&a,const OverrideMatrix&b){OverrideMatrix result{};for(unsigned i=0;i<4;++i)for(unsigned j=0;j<4;++j)for(unsigned k=0;k<4;++k)result[i*4+j]+=a[i*4+k]*b[k*4+j];return result;}
OverrideMatrix override_matrix(unsigned address){if(!readable(address,48))throw std::runtime_error("Bushwacker test: unreadable source matrix");std::array<float,12>a{};for(unsigned i=0;i<12;++i){unsigned bits=load(address+4*i);std::memcpy(&a[i],&bits,4);if(!std::isfinite(a[i]))throw std::runtime_error("Bushwacker test: nonfinite source matrix");}
 return {a[0],a[3],a[6],a[9],a[1],a[4],a[7],a[10],a[2],a[5],a[8],a[11],0,0,0,1};}
static OverrideMatrix override_inverse(OverrideMatrix a){auto inverse=override_identity();for(unsigned col=0;col<4;++col){unsigned pivot=col;for(unsigned row=col+1;row<4;++row)if(std::abs(a[row*4+col])>std::abs(a[pivot*4+col]))pivot=row;if(std::abs(a[pivot*4+col])<1e-10)throw std::runtime_error("Bushwacker test: singular source matrix");for(unsigned j=0;j<4;++j){std::swap(a[col*4+j],a[pivot*4+j]);std::swap(inverse[col*4+j],inverse[pivot*4+j]);}double scale=a[col*4+col];for(unsigned j=0;j<4;++j){a[col*4+j]/=scale;inverse[col*4+j]/=scale;}for(unsigned row=0;row<4;++row)if(row!=col){scale=a[row*4+col];for(unsigned j=0;j<4;++j){a[row*4+j]-=scale*a[col*4+j];inverse[row*4+j]-=scale*inverse[col*4+j];}}}return inverse;}

#include "donor_runtime.inc"
void override_load_textures(const OverrideModel&model,size_t first,size_t end,const char*alternate_env=nullptr,unsigned skin=0,const char*direct_path=nullptr){
 const char*path=direct_path?direct_path:model.direct_texture?model.direct_texture:std::getenv(alternate_env?alternate_env:model.texture_env);if(!path)return;
 auto&o=override_state();std::ifstream file(std::filesystem::path(additional_skin_wide(path)),std::ios::binary);
 auto bytes=[&](void*p,size_t n){if(!file.read(static_cast<char*>(p),std::streamsize(n)))throw std::runtime_error("Replacement textures: incomplete sidecar");};
 char magic[8];bytes(magic,8);if(std::memcmp(magic,"BWTEX1\0\0",8))throw std::runtime_error("Replacement textures: wrong format");
 unsigned batches,count;bytes(&batches,4);bytes(&count,4);if(batches!=end-first||!count||count>64||skin>135)throw std::runtime_error("Replacement textures: material count/skin mismatch");
 std::vector<unsigned>bindings(batches),indices;
 for(auto&index:bindings){bytes(&index,4);if(index>=count)throw std::runtime_error("Replacement textures: invalid material index");}
 for(unsigned i=0;i<count;++i){char name[32];bytes(name,32);if(name[31])throw std::runtime_error("Replacement textures: invalid name");OverrideTexture t{};t.name=name;bytes(&t.width,4);bytes(&t.height,4);bytes(&t.hash,8);
  if(!t.width||!t.height||t.width>4096||t.height>4096)throw std::runtime_error("Replacement textures: invalid dimensions");
  t.pixels.resize(size_t(t.width)*t.height);bytes(t.pixels.data(),t.pixels.size()*2);
  indices.push_back(mw34::skins::intern_texture(o.textures,std::move(t)));
 }
 if(file.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Replacement textures: trailing data");
 for(size_t at=first;at<end;++at){const auto index=indices[bindings[at-first]];if(alternate_env||direct_path){auto& skins=o.batches[at].skin_textures;if(skins.size()<=skin)skins.resize(skin+1,-1);skins.at(skin)=int(index);}else o.batches[at].texture=int(index);o.batches[at].color=0xffffffff;}
 o.log<<"{\"event\":\"textures_loaded\",\"model\":\""<<model.id<<"\",\"skin\":"<<skin<<",\"materials\":"<<count<<",\"format\":\"RGB565\"}\n";
}
void override_load_normals(const OverrideModel&model,size_t first,size_t end){
 if(!mw34::sun::settings().enabled||!mw34::materials::normal_maps_enabled())return;
 if(!model.texture_env||std::strlen(model.texture_env)<10)return;
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
 o.log<<"{\"event\":\"normals_loaded\",\"model\":\""<<model.id<<"\",\"lod\":"<<model.lod<<",\"materials\":"<<pack.images.size()<<",\"format\":\"RGBA8888\",\"binding\":\"material-name\"}\n";
}
void override_load_surface_materials(const OverrideModel&model,size_t first,size_t end){
 std::string env;
 if(model.texture_env&&std::strlen(model.texture_env)>=10){
  env=std::string(model.texture_env).substr(0,std::strlen(model.texture_env)-9)+"_SURFACE_MATERIALS";
 }else if(model.resource&&*model.resource){
  std::string resource_upper(model.resource);
  for(char&c:resource_upper)if(c>='a'&&c<='z')c=char(c-'a'+'A');
  env="MW34_CHASSIS_"+resource_upper+(model.lod?"_LOD1_SURFACE_MATERIALS":"_SURFACE_MATERIALS");
 }else return;
 const char*path=std::getenv(env.c_str());if(!path||!*path)return;
 std::ifstream file(std::filesystem::path(additional_skin_wide(path)),std::ios::binary);
 if(!file)throw std::runtime_error("Configured replacement surface-material sidecar is missing: "+env);
 auto&o=override_state();std::vector<std::string>materials;
 for(size_t at=first;at<end;++at){const int index=o.batches[at].texture;
  if(index<0||size_t(index)>=o.textures.size())throw std::runtime_error("Surface material requires its albedo material binding");
  materials.push_back(o.textures[index].name);}
 const std::string expected_asset=std::string(model.id)+(model.lod?":distance":":close");
 const auto expected_hash=mw34::materials::compute_mesh_uv_hash(o.batches,first,end);
 auto pack=mw34::materials::read_surface_materials(file,expected_asset,expected_hash,materials);
 const size_t offset=o.surface_material_textures.size();
 if(offset+pack.images.size()>size_t(std::numeric_limits<int>::max()))throw std::runtime_error("Surface-material image index overflow");
 std::vector<int>indices;
 for(auto&image:pack.images){auto found=std::find_if(o.surface_material_textures.begin(),o.surface_material_textures.end(),[&](const OverrideTexture&existing){return existing.width==image.width&&existing.height==image.height&&existing.hash==image.hash&&existing.pixels32==image.pixels;});
  if(found!=o.surface_material_textures.end()){indices.push_back(int(found-o.surface_material_textures.begin()));continue;}
  indices.push_back(int(o.surface_material_textures.size()));OverrideTexture t{};t.name=std::move(image.name);t.width=image.width;t.height=image.height;t.hash=image.hash;t.pixels32=std::move(image.pixels);o.surface_material_textures.push_back(std::move(t));}
 for(auto&record:pack.records){
  if(record->height_image!=mw34::materials::no_surface_image)record->host_height_texture=indices[record->height_image];
  if(record->thickness_image!=mw34::materials::no_surface_image)record->host_thickness_texture=indices[record->thickness_image];
 }
 for(size_t at=first;at<end;++at){const auto rec_index=pack.bindings[at-first];o.batches[at].surface_material=rec_index==mw34::materials::no_surface_material?nullptr:pack.records[rec_index];}
 o.log<<"{\"event\":\"surface_materials_loaded\",\"model\":\""<<model.id<<"\",\"lod\":"<<model.lod<<",\"records\":"<<pack.records.size()<<",\"images\":"<<pack.images.size()<<",\"format\":\"BWSFM1\"}\n";
}
void override_load_ground_normals(){
 auto& o=override_state();
 o.ground_normal_texture=-1;
 const char* path=std::getenv("MW34_GROUND_NORMALS");
 if(!path)return;
 std::ifstream file(path,std::ios::binary);
 if(!file)return;
 auto bytes=[&](void*p,size_t n){if(!file.read(static_cast<char*>(p),std::streamsize(n)))throw std::runtime_error("Ground normals: incomplete sidecar");};
 char magic[8];bytes(magic,8);if(std::memcmp(magic,"BWNRM1\0\0",8))throw std::runtime_error("Ground normals: wrong format");
 unsigned batches,count;bytes(&batches,4);bytes(&count,4);if(!count||count>64)throw std::runtime_error("Ground normals: count mismatch");
 o.ground_normal_bindings.clear();
 for(unsigned entry=0;entry<count;++entry){
  char name[32];bytes(name,32);if(name[31])throw std::runtime_error("Ground normals: invalid name");
  OverrideTexture t{};t.name=name;bytes(&t.width,4);bytes(&t.height,4);bytes(&t.hash,8);
  if(!t.width||!t.height||t.width>4096||t.height>4096)throw std::runtime_error("Ground normals: invalid dimensions");
  t.pixels32.resize(size_t(t.width)*t.height);bytes(t.pixels32.data(),t.pixels32.size()*4);
  const int index=int(o.normal_textures.size());
  if(!entry)o.ground_normal_texture=index;
  else o.ground_normal_bindings.push_back({t.width,t.height,unsigned(t.hash&0xffffffffu),unsigned(t.hash>>32),unsigned(index)});
  fprintf(stderr,"[GROUND_NORMALS_LOADED] name='%s' %ux%u normal_idx=%d tag=%016llx\n",name,t.width,t.height,index,(unsigned long long)t.hash);fflush(stderr);
  if(o.log.is_open())o.log<<"{\"event\":\"ground_normals_loaded\",\"name\":\""<<name<<"\",\"dimensions\":["<<t.width<<","<<t.height<<"],\"format\":\"RGBA8888\"}\n";
  o.normal_textures.push_back(std::move(t));
 }
 if(file.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Ground normals: trailing data");
}

void override_prepare_geometry(OverrideBatch&b,size_t index){if(!mw34::vkscene::Renderer::gpu_models()||!b.vertex_bones.empty())return;
 auto g=std::make_shared<mw34::vkscene::ModelGeometry>();g->key=0x4d4f444c00000000ULL+index;g->vertices=b.vertices;g->hash=0xcbf29ce484222325ULL;
 const auto*bytes=reinterpret_cast<const unsigned char*>(g->vertices.data());for(size_t i=0;i<g->vertices.size()*sizeof(OverrideVertex);++i){g->hash^=bytes[i];g->hash*=0x100000001b3ULL;}
 b.lo=b.hi={b.vertices[0].x,b.vertices[0].y,b.vertices[0].z};for(const auto&v:b.vertices){const std::array<float,3>p{v.x,v.y,v.z};for(unsigned i=0;i<3;++i){b.lo[i]=std::min(b.lo[i],p[i]);b.hi[i]=std::max(b.hi[i],p[i]);}}b.geometry=std::move(g);}
void override_load(){auto&o=override_state();if(o.loaded)return;
 const char*log_path=std::getenv("MW34_MODELS_LOG");if(!log_path)log_path=std::getenv("MW34_BUSHWACKER_TEST_LOG");
 o.log.open(log_path?log_path:"local/remaster/model-runtime.jsonl",std::ios::trunc);if(!o.log)throw std::runtime_error("Replacement models: cannot open runtime log");
 override_load_ground_normals();o.loaded=true;
}
void override_load_model(unsigned id){
 auto&o=override_state();override_load();if(o.model_ranges.count(id))return;
 const auto&model=override_models().at(id);const char*path=override_mesh_env(model);
 if(!path)throw std::runtime_error("Replacement models: requested disabled model");
 const auto started=::GetTickCount64();
 {
  std::ifstream file(path,std::ios::binary);auto bytes=[&](void*p,size_t n){if(!file.read(static_cast<char*>(p),std::streamsize(n)))throw std::runtime_error("Replacement models: incomplete mesh payload");};
  char magic[8];bytes(magic,8);const bool donor=std::memcmp(magic,"BWMESH4\0",8)==0;const bool anchored=std::memcmp(magic,"BWMESH6\0",8)==0;const bool layered=anchored||std::memcmp(magic,"BWMESH5\0",8)==0;const bool placement=layered||std::memcmp(magic,"BWMESH3\0",8)==0;const bool component_visibility=donor||placement||std::memcmp(magic,"BWMESH2\0",8)==0;if(!component_visibility&&std::memcmp(magic,"BWMESH1\0",8))throw std::runtime_error("Replacement models: wrong mesh payload");unsigned count;bytes(&count,4);if(!count||count>256)throw std::runtime_error("Replacement models: invalid batch count");const size_t first=o.batches.size();if(donor)o.donor_rigs.emplace(id,override_read_donor(bytes));
  for(unsigned i=0;i<count;++i){char name[32];bytes(name,32);if(name[31])throw std::runtime_error("Replacement models: invalid controller name");
   bool owner=false;for(size_t r=0;r<model.count;++r)if(std::string(name)==model.roster[r].owner)owner=true;if(!owner)throw std::runtime_error("Replacement models: unknown source controller");
   char visibility[32]{};if(component_visibility){bytes(visibility,32);if(!visibility[0]||visibility[31])throw std::runtime_error("Replacement models: invalid visibility node");bool bound=false;for(size_t r=0;r<model.count;++r)if(std::string(visibility)==model.roster[r].name&&std::string(name)==model.roster[r].owner)bound=true;if(!bound)throw std::runtime_error("Replacement models: visibility node is outside source controller");}
   // V3 adds a rigid translation in a named original ancestor frame.
   // Legacy V1/V2 payloads retain the exact prior projection path.
   char placement_name[32]{};std::array<float,3>placement_offset{};
   if(placement){bytes(placement_name,32);bytes(placement_offset.data(),12);if(placement_name[31])throw std::runtime_error("Replacement models: invalid placement frame");
    for(float value:placement_offset)if(!std::isfinite(value))throw std::runtime_error("Replacement models: nonfinite placement offset");
    if(!placement_name[0]){for(float value:placement_offset)if(value!=0)throw std::runtime_error("Replacement models: offset without placement frame");}
    else{bool found=false;for(size_t r=0;r<model.count;++r)if(std::string(placement_name)==model.roster[r].owner)found=true;if(!found)throw std::runtime_error("Replacement models: unknown placement frame");}}
   char joint_name[32]{};std::array<float,3>joint_offset{};
   if(layered){bytes(joint_name,32);bytes(joint_offset.data(),12);if(joint_name[31])throw std::runtime_error("Replacement models: invalid joint frame");
    for(float value:joint_offset)if(!std::isfinite(value))throw std::runtime_error("Replacement models: nonfinite joint offset");
    if(!joint_name[0]){for(float value:joint_offset)if(value!=0)throw std::runtime_error("Replacement models: joint offset without frame");}
    else{bool found=false;for(size_t r=0;r<model.count;++r)if(std::string(joint_name)==model.roster[r].owner)found=true;if(!found)throw std::runtime_error("Replacement models: unknown joint frame");}}
   char anchor_name[32]{};std::array<float,3>anchor_position{};
   if(anchored){bytes(anchor_name,32);bytes(anchor_position.data(),12);if(anchor_name[31])throw std::runtime_error("Replacement models: invalid anchor control");
    for(float value:anchor_position)if(!std::isfinite(value))throw std::runtime_error("Replacement models: nonfinite anchor position");
    if(!anchor_name[0]){for(float value:anchor_position)if(value!=0)throw std::runtime_error("Replacement models: anchor position without control");}
    else{if(!placement_name[0])throw std::runtime_error("Replacement models: anchor requires placement frame");bool found=false;for(size_t r=0;r<model.count;++r)if(std::string(anchor_name)==model.roster[r].owner)found=true;if(!found)throw std::runtime_error("Replacement models: unknown anchor control");}}
   unsigned donor_bone=~0U;if(donor){bytes(&donor_bone,4);if(donor_bone!=~0U&&donor_bone>=o.donor_rigs.at(id).bones.size())throw std::runtime_error("Visual retarget: invalid batch bone");}
   unsigned size,color;bytes(&size,4);bytes(&color,4);if(!size||size>65535||size%3)throw std::runtime_error("Replacement models: invalid triangle count");OverrideBatch batch{name,visibility,color,{}};batch.model=id;batch.placement_frame=placement_name;batch.placement_offset=placement_offset;batch.donor_bone=donor_bone;batch.joint_frame=joint_name;batch.joint_offset=joint_offset;batch.anchor_control=anchor_name;batch.anchor_position=anchor_position;batch.vertices.resize(size);bytes(batch.vertices.data(),size*sizeof(OverrideVertex));
   for(const auto&v:batch.vertices){for(float value:{v.x,v.y,v.z,v.nx,v.ny,v.nz,v.u,v.v})if(!std::isfinite(value))throw std::runtime_error("Replacement models: nonfinite mesh payload");if(v.nx*v.nx+v.ny*v.ny+v.nz*v.nz<.5f)throw std::runtime_error("Replacement models: invalid normal");}
   if(donor&&donor_bone==~0U){batch.vertex_bones.resize(size);bytes(batch.vertex_bones.data(),size*4);for(unsigned bone:batch.vertex_bones)if(bone>=o.donor_rigs.at(id).bones.size())throw std::runtime_error("Visual retarget: invalid seam bone");}
   override_prepare_geometry(batch,o.batches.size());o.batches.push_back(std::move(batch));}
  if(file.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Replacement models: trailing mesh payload");
  for(size_t r=0;r<model.count;++r){bool present=false;for(size_t b=first;b<o.batches.size();++b)if(o.batches[b].owner==model.roster[r].owner)present=true;
   if(!present)throw std::runtime_error("Replacement models: missing required source controller geometry");}
  override_load_textures(model,first,o.batches.size());
  override_load_normals(model,first,o.batches.size());
  override_load_surface_materials(model,first,o.batches.size());
  o.model_ranges.emplace(id,std::pair{first,o.batches.size()});
  std::fprintf(stderr,"Model resource ready: chassis=%s lod=%u batches=%zu elapsed_ms=%llu\n",model.id,model.lod,o.batches.size()-first,(unsigned long long)(::GetTickCount64()-started));
  o.log<<"{\"event\":\"enabled\",\"model\":\""<<model.id<<"\",\"lod\":"<<model.lod<<",\"batches\":"<<count<<",\"scope\":\"optional visual replacement; source gameplay preserved\"}\n";
 }
}
bool override_load_skin(unsigned id,unsigned skin){
 auto&o=override_state();override_load_model(id);if(!skin)return true;
 const auto&model=override_models().at(id);const auto [first,end]=o.model_ranges.at(id);
 if(!o.skin_attempts.count({id,skin})){
  const auto started=::GetTickCount64();
  if(skin<8){const auto key=mw34::skins::binding(model.id,model.lod!=0,skin);override_load_textures(model,first,end,key.c_str(),skin);}
  else additional_skins_load(model,first,end,skin);
  o.skin_attempts.emplace(id,skin);
  std::fprintf(stderr,"Skin resource checked: chassis=%s lod=%u skin=%u elapsed_ms=%llu\n",model.id,model.lod,skin,(unsigned long long)(::GetTickCount64()-started));
 }
 bool seen=false;for(size_t i=first;i<end;++i)if(o.batches[i].texture>=0){seen=true;
  if(skin>=o.batches[i].skin_textures.size()||o.batches[i].skin_textures[skin]<0)return false;}
 return seen;
}
unsigned override_parent(unsigned node){if(!readable(node,100)||load(node+0x54)!=1||!readable(load(node+0x58),4))return 0;return load(load(node+0x58));}

#include "model_arm_damage.inc"
int override_validate_root(unsigned root){auto&o=override_state();auto cached=o.validated_roots.find(root);if(cached!=o.validated_roots.end())return cached->second;
 std::map<std::string,unsigned>meshes,mesh_nodes;std::map<unsigned,bool>active;std::vector<unsigned>queue{root};std::set<unsigned>seen;active.emplace(root,true);
 for(size_t i=0;i<queue.size();++i){if(i>=128)throw std::runtime_error("Replacement models: hierarchy too large");unsigned node=queue[i];if(!seen.insert(node).second)throw std::runtime_error("Replacement models: shared/cyclic hierarchy");
  if(!readable(node,100))throw std::runtime_error("Replacement models: incomplete instance hierarchy");unsigned count=load(node+0x5c),children=load(node+0x60);if(count>64||(count&&!readable(children,count*4)))throw std::runtime_error("Replacement models: invalid children");
  const bool visible=active.at(node)&&(load(node+0x24)&4)!=0;
  for(unsigned j=0;j<count;++j){unsigned child=load(children+4*j);queue.push_back(child);active.emplace(child,visible);}unsigned mesh=load(node+0x3c);if(mesh){if(!readable(mesh,24))throw std::runtime_error("Replacement models: unreadable source mesh");const auto name=pose_name(node,36);if(!meshes.emplace(name,load(mesh+20)).second)throw std::runtime_error("Replacement models: duplicate source mesh name");if(name=="rarm_stub01"||name=="larm_stub01")mesh_nodes.emplace(name,node);o.active_nodes[{root,name}]=visible;}}
 // Live player instances attach these two auxiliary meshes after loading the chassis.
 // Keep their original draws; they are not part of chassis identity or replacement geometry.
 meshes.erase("left ski");meshes.erase("right ski");
 // The current host can attach the original cockpit to the same live root.
 // Exclude only its complete, observed mesh signature; keep its original draws.
 for(const auto&cockpit:override_cockpit_rosters){bool attached=true;
  for(size_t i=0;i<cockpit.count;++i){const auto&c=cockpit.meshes[i];const auto found=meshes.find(c.name);if(found==meshes.end()||found->second!=c.vertices){attached=false;break;}}
  if(attached){for(size_t i=0;i<cockpit.count;++i){o.attached_cockpit_nodes.emplace(root,cockpit.meshes[i].name);meshes.erase(cockpit.meshes[i].name);}break;}
 }
 int result=-1;unsigned damage_mask=0;
 const auto root_name=pose_name(root,36);const char* added_resource=chassis_actor_resource(root);
 for(const auto& registration:mw34::chassis::configured_catalog())if(!added_resource&&(!registration.visual_template.empty()||registration.owned_visuals)) {
  const auto& key=registration.resource;
  if(root_name==key||root_name=="mech_"+key+".flt"||root_name=="mech_"+key+"_1.flt")added_resource=key.c_str();
 }
 if(added_resource)for(const auto& r:mw34::chassis::configured_catalog())if(r.owned_visuals&&r.resource==added_resource&&!r.cockpit_roster.empty()) {
  bool complete=true;
  for(const auto& mesh:r.cockpit_roster){auto found=meshes.find(mesh.name);if(found==meshes.end()||found->second!=mesh.vertices){complete=false;break;}}
  if(complete)for(const auto& mesh:r.cockpit_roster){o.attached_cockpit_nodes.emplace(root,mesh.name);meshes.erase(mesh.name);}
 }
 for(unsigned id=0;id<override_models().size();++id){const auto&m=override_models()[id];
  if(bool(m.resource)!=bool(added_resource)||(m.resource&&std::strcmp(m.resource,added_resource)))continue;
  if(!override_mesh_env(m))continue;bool match=meshes.size()==m.count;
  if(match)for(size_t at=0;at<m.count;++at){const auto&r=m.roster[at];auto it=meshes.find(r.name);if(it==meshes.end()||it->second!=r.vertices){match=false;break;}}
  unsigned changed=0;if(!match)match=override_arm_damage_match(m,meshes,mesh_nodes,changed);
  if(match){if(result>=0)throw std::runtime_error("Replacement models: ambiguous chassis identity");result=int(id);damage_mask=changed;}}
 if(result>=0&&damage_mask){
  const auto&m=override_models()[result];
  for(size_t i=0;i<m.count;++i)if(!meshes.count(m.roster[i].name))o.active_nodes[{root,m.roster[i].name}]=false;
  if(o.damage_announced.emplace(root,damage_mask).second){
   o.log<<"{\"event\":\"arm_damage_identity\",\"frame\":"<<host.frames<<",\"root\":"<<root<<",\"model\":\""<<m.id<<"\",\"lod\":"<<m.lod<<",\"mask\":"<<damage_mask<<",\"source_stumps_retained\":true}\n";o.log.flush();
  }
 }


 // 53F2E0 reads polygon[7] as material*, material+16 as texture-ref*;
 // its 40-byte reference stores the original 32-byte name after data/handle.
 // Inspect only this validated chassis tree, freshly for each scene/LOD.
 if(result>=0){
  mw34::skins::Selection selection;
  for(unsigned node:queue){bool source_part=false;const auto part_name=pose_name(node,36);const auto&model=override_models()[result];for(size_t i=0;i<model.count;++i)if(part_name==model.roster[i].name){source_part=true;break;}if(!source_part)continue;const unsigned mesh=load(node+0x3c);if(!mesh)continue;
   if(!readable(mesh,0x38))throw std::runtime_error("Mech skin: unreadable source mesh");
   const unsigned count=load(mesh+0x10),polys=load(mesh+0x34);
   if(count>1000||(count&&!readable(polys,count*36)))throw std::runtime_error("Mech skin: invalid original polygon table");
   for(unsigned i=0;i<count;++i){const unsigned mat=load(polys+i*36+28);if(!readable(mat,20))throw std::runtime_error("Mech skin: invalid original material");
    if(!(load(mat)&0x100))continue;const unsigned ref=load(mat+16);if(!ref||!readable(ref,40))throw std::runtime_error("Mech skin: invalid original texture reference");
    const auto name=pose_name(ref+8,32);
    bool owned=false;
    if(model.resource)for(const auto& registration:mw34::chassis::configured_catalog())
     if(registration.owned_visuals&&registration.resource==model.resource) {
      owned=true;const auto found=registration.skin_textures.find(name);
      if(found!=registration.skin_textures.end())selection.observe(found->second);
      break;
     }
    if(!owned)selection.observe(mw34::skins::texture_skin(model.source_chassis?model.source_chassis:model.id,name));
   }
  }
  const auto selected=selection.result();
  const unsigned skin=selected.value_or(0);o.source_skins[root]=skin;
  if(!selected)result=-1;
  else if(!override_load_skin(unsigned(result),skin))result=-1; // Preserve an unavailable optional original appearance.
  if(o.announced_roots.emplace(root,0xffff0000U+skin).second){o.log<<"{\"event\":\"source_skin\",\"root\":"<<root<<",\"skin\":"<<skin<<",\"replacement_available\":"<<(result>=0?"true":"false")<<"}\n";o.log.flush();}
 }
 o.validated_roots.emplace(root,result);
 if(result<0&&o.announced_roots.emplace(root,~0U).second){
  o.log<<"{\"event\":\"identity_rejected\",\"root\":"<<root<<",\"meshes\":[";
  bool first=true;for(const auto&entry:meshes){if(!first)o.log<<',';first=false;o.log<<"{\"name\":\""<<entry.first<<"\",\"vertices\":"<<entry.second<<'}';}
  o.log<<"]}\n";o.log.flush();
 }
 if(result>=0&&o.announced_roots.emplace(root,unsigned(result)).second)o.log<<"{\"event\":\"instance_validated\",\"root\":"<<root<<",\"model\":\""<<override_models()[result].id<<"\",\"lod\":"<<override_models()[result].lod<<",\"source_meshes\":"<<meshes.size()<<"}\n";
 return result;
}
// These exact returns surround the original per-part condition schematic.
// Retain its original diagnostic material state when replacing the geometry.
bool override_status_preview() const {
 for(unsigned i=depth;i>0;--i)if(returns[i-1]==0x441480||returns[i-1]==0x442a87)return true;
 return false;
}

bool avatar_detached_interior_node(unsigned node){
 if(!photo_replay_detached_cam())return false;
 const auto name=pose_name(node,36);bool candidate=false;
 for(const auto&m:cockpit_avatar)if(name==m.name)candidate=true;
 if(!candidate)return false;
 unsigned root=0,current=node;
 for(unsigned depth_=0;current&&depth_<32;++depth_){if(pose_name(current,36)=="hip"){root=override_parent(current);break;}current=override_parent(current);}
 if(!root)return false;
 static unsigned frame=~0U;static std::map<unsigned,bool>cache;
 if(frame!=host.frames){frame=host.frames;cache.clear();}
 auto found=cache.find(root);if(found!=cache.end())return found->second;
 std::map<std::string,unsigned>meshes;std::vector<unsigned>todo{root};std::set<unsigned>seen;
 bool valid=true;
 for(size_t i=0;i<todo.size()&&valid;++i){
  if(i>=128||!seen.insert(todo[i]).second||!readable(todo[i],100)){valid=false;break;}
  const unsigned n=todo[i],count=load(n+0x5c),children=load(n+0x60);
  if(count>64||(count&&!readable(children,count*4))){valid=false;break;}
  for(unsigned j=0;j<count;++j)todo.push_back(load(children+4*j));
  const unsigned mesh=load(n+0x3c);
  if(mesh){if(!readable(mesh,24)||!meshes.emplace(pose_name(n,36),load(mesh+20)).second)valid=false;}
 }
 meshes.erase("left ski");meshes.erase("right ski");
 for(const auto&m:cockpit_avatar){auto f=meshes.find(m.name);if(f==meshes.end()||f->second!=m.vertices)valid=false;}
 bool chassis=false;
 auto match=[&](const auto&roster){
  if(meshes.size()!=roster.size()+cockpit_avatar.size())return false;
  for(const auto&m:roster){auto f=meshes.find(m.name);if(f==meshes.end()||f->second!=m.vertices)return false;}
  return true;
 };
 if(valid)chassis=match(override_avatar_meshes)||match(override_avatar_lod1_meshes);
 const bool hide=valid&&chassis;cache.emplace(root,hide);
 static std::set<unsigned>announced;
 if(hide&&announced.insert(root).second)std::cerr<<"Detached Avatar: authenticated interior omitted; original exterior retained\n";
 return hide;
}


bool strider_detached_interior_node(unsigned node){
 if(!photo_replay_detached_cam())return false;
 const auto name=pose_name(node,36);bool candidate=false;
 for(const auto&m:cockpit_strider)if(name==m.name)candidate=true;
 if(!candidate)return false;
 unsigned root=0,current=node;
 for(unsigned depth_=0;current&&depth_<32;++depth_){if(pose_name(current,36)=="hip"){root=override_parent(current);break;}current=override_parent(current);}
 if(!root)return false;
 static unsigned frame=~0U;static std::map<unsigned,bool>cache;
 if(frame!=host.frames){frame=host.frames;cache.clear();}
 auto found=cache.find(root);if(found!=cache.end())return found->second;
 std::map<std::string,unsigned>meshes;std::vector<unsigned>todo{root};std::set<unsigned>seen;
 bool valid=true;
 for(size_t i=0;i<todo.size()&&valid;++i){
  if(i>=128||!seen.insert(todo[i]).second||!readable(todo[i],100)){valid=false;break;}
  const unsigned n=todo[i],count=load(n+0x5c),children=load(n+0x60);
  if(count>64||(count&&!readable(children,count*4))){valid=false;break;}
  for(unsigned j=0;j<count;++j)todo.push_back(load(children+4*j));
  const unsigned mesh=load(n+0x3c);
  if(mesh){if(!readable(mesh,24)||!meshes.emplace(pose_name(n,36),load(mesh+20)).second)valid=false;}
 }
 meshes.erase("left ski");meshes.erase("right ski");
 for(const auto&m:cockpit_strider){auto f=meshes.find(m.name);if(f==meshes.end()||f->second!=m.vertices)valid=false;}
 bool chassis=false;
 auto match=[&](const auto&roster){
  if(meshes.size()!=roster.size()+cockpit_strider.size())return false;
  for(const auto&m:roster){auto f=meshes.find(m.name);if(f==meshes.end()||f->second!=m.vertices)return false;}
  return true;
 };
 if(valid)chassis=match(override_strider_meshes)||match(override_strider_lod1_meshes);
 const bool hide=valid&&chassis;cache.emplace(root,hide);
 static std::set<unsigned>announced;
 if(hide&&announced.insert(root).second)std::cerr<<"Detached Strider: authenticated interior omitted; original exterior retained\n";
 return hide;
}

#include "status_model_fit_stage.inc"
OverrideScope override_begin(unsigned node){OverrideMxcsr preserve;auto&o=override_state();OverrideScope previous=o.scope;o.scope={};if(!override_status_preview()&&(avatar_detached_interior_node(node)||strider_detached_interior_node(node))){o.scope={node,"",override_identity(),0,0,0,true};return previous;}if(!override_enabled())return previous;override_load();
 const auto name=pose_name(node,36);
 bool cockpit_candidate=false;
 if(photo_replay_detached_cam())for(const auto&roster:override_cockpit_rosters)for(size_t i=0;i<roster.count;++i)if(name==roster.meshes[i].name)cockpit_candidate=true;
 if(!override_candidate_name(name)&&!cockpit_candidate)return previous;
 unsigned root=0,current=node;for(unsigned depth_=0;current&&depth_<32;++depth_){if(pose_name(current,36)=="hip"){root=override_parent(current);break;}current=override_parent(current);}if(!root)return previous;
 const int id=override_validate_root(root);if(id<0)return previous;
 if(cockpit_candidate&&o.attached_cockpit_nodes.count({root,name})){
  o.scope={node,"",override_identity(),root,unsigned(id),0,true};
  if(o.announced_roots.emplace(root,0xfffd0000U).second){o.log<<"{\"event\":\"detached_attached_cockpit_suppressed\",\"root\":"<<root<<"}\n";o.log.flush();}
  return previous;
 }
 const auto&model=override_models()[id];const OverrideSourceMesh*mesh=nullptr;for(size_t at=0;at<model.count;++at)if(name==model.roster[at].name){mesh=&model.roster[at];break;}if(!mesh)return previous;
 OverrideMatrix owner_to_node=override_identity();current=node;for(unsigned depth_=0;pose_name(current,36)!=mesh->owner;++depth_){if(depth_>=16||!current||load(current+0x34)!=5)throw std::runtime_error("Replacement models: unsupported control ancestry");unsigned data_=load(current+0x38);if(!readable(data_,96))throw std::runtime_error("Replacement models: unreadable control data");auto local=(load(data_)&8)?override_identity():override_matrix(data_+0x30);owner_to_node=override_product(local,owner_to_node);current=override_parent(current);}
 o.scope={node,mesh->owner,owner_to_node,root,unsigned(id)};o.scope.preview=override_status_preview();o.scope.skin=additional_skin_for(o.source_skins.at(root),root,unsigned(id),o.scope.preview);return previous;
}
void override_preview_start(){auto&o=override_state();o.preview_emitted.clear();o.donor_poses.clear();o.preview_has_bounds=false;o.preview_fit_applied=false;o.preview_role=override_preview_role();o.preview_begin=0;for(auto&d:host.devices)if(d.in_scene)o.preview_begin=d.commands.size();}
void override_restore(const OverrideScope&scope){override_state().scope=scope;}
void override_scene_start(){if(override_enabled()){override_state().emitted.clear();override_state().validated_roots.clear();override_state().attached_cockpit_nodes.clear();override_state().source_skins.clear();override_state().active_nodes.clear();override_state().donor_poses.clear();}}
bool override_suppress_draw(){if(override_state().scope.node&&override_state().scope.attached_cockpit)return true;if(!override_enabled()||!override_state().scope.node)return false;if(override_state().scope.preview)return override_state().preview_emitted.count(override_state().scope.node)!=0;if(!override_state().emitted.count({override_state().scope.root,override_state().scope.owner}))throw std::runtime_error("Bushwacker test: source draw reached without replacement projection");return true;}
// Recover the requested ancestor's current camera basis from this exact
// instance and animation sample. Never reuse another actor's cached pose.
OverrideMatrix override_placement_frame_camera(const std::string&frame,const OverrideMatrix&owner_camera){
 const auto&scope=override_state().scope;unsigned current=scope.node;
 for(unsigned depth_=0;pose_name(current,36)!=scope.owner;++depth_){if(!current||depth_>=16)throw std::runtime_error("Replacement models: missing placement owner");current=override_parent(current);}
 auto owner_to_frame=override_identity();
 for(unsigned depth_=0;pose_name(current,36)!=frame;++depth_){
  if(!current||depth_>=16||!readable(current,100)||load(current+0x34)!=5)throw std::runtime_error("Replacement models: placement frame is not an ancestor");
  const unsigned data_=load(current+0x38);if(!readable(data_,96))throw std::runtime_error("Replacement models: unreadable placement ancestry");
  const auto local=(load(data_)&8)?override_identity():override_matrix(data_+0x30);owner_to_frame=override_product(local,owner_to_frame);current=override_parent(current);
 }
 return override_product(owner_camera,override_inverse(owner_to_frame));
}
#include "chassis_preview_stage.inc"
void override_emit(const D3DCmd*original=nullptr){if(!override_enabled())return;auto&o=override_state();if(o.scope.attached_cockpit)return;if(!o.scope.node)return;const bool preview=o.scope.preview;if(preview&&!original){const unsigned pointer=load(0x5eda90);if(!readable(pointer,4))throw std::runtime_error("Status models: missing model-view stack");o.scope.preview_camera=override_matrix(load(pointer));return;}if(preview?o.preview_emitted.count(o.scope.node)!=0:o.emitted.count({o.scope.root,o.scope.owner})!=0)return;unsigned preview_specular=0xff000000U;if(preview){if(original->vertices.empty())return;unsigned alpha_sum=0,alpha_count=0;for(size_t i=0;i+32<=original->vertices.size();i+=32){unsigned spec;std::memcpy(&spec,original->vertices.data()+i+20,4);alpha_sum+=spec>>24;++alpha_count;}if(!alpha_count)return;preview_specular=((alpha_sum+alpha_count/2)/alpha_count)<<24;}
 // All arithmetic uses AMD64 SSE; retain the guest's MXCSR flags and rounding.
 struct PreserveMxcsr{unsigned value=_mm_getcsr();~PreserveMxcsr(){_mm_setcsr(value);}} preserve;
 D3DDev*device=nullptr;for(auto&d:host.devices)if(d.in_scene){if(device)throw std::runtime_error("Bushwacker test: ambiguous current scene");device=&d;}if(!device)throw std::runtime_error("Bushwacker test: no active native scene");
 const unsigned pointer=load(0x5eda90);if(!readable(pointer,4))throw std::runtime_error("Bushwacker test: missing model-view stack");auto node_to_camera=preview?o.scope.preview_camera:override_matrix(load(pointer));auto control_to_camera=override_product(node_to_camera,override_inverse(o.scope.owner_to_node));
 OverrideDonorInstance*donor=nullptr;OverrideMatrix donor_root_camera{};if(o.donor_rigs.count(o.scope.model)){donor=&override_donor_pose();auto it=donor->raw.find(o.scope.owner);if(it==donor->raw.end())throw std::runtime_error("Visual retarget: missing live emission owner");donor_root_camera=override_product(override_product(control_to_camera,override_inverse(it->second)),mw34::donor::inverse(mw34::donor::axis()));}
 auto source_float=[&](unsigned address){unsigned bits=load(address);float value;std::memcpy(&value,&bits,4);if(!std::isfinite(value))throw std::runtime_error("Bushwacker test: invalid source projection");return double(value);};
 double near_scale=source_float(0x73fb80),scale_x=source_float(0x73fc30),scale_y=source_float(0x73fb98),center_x=source_float(0x73fb88),center_y=source_float(0x73fb8c),near_clip=source_float(0x740304);
 if(donor&&frontend_on()&&override_models()[o.scope.model].resource)chassis_preview_camera(o.scope.model,donor_root_camera,near_scale,scale_x,scale_y,center_x,center_y,near_clip);
 if(load(0x72f348)==0)throw std::runtime_error("Bushwacker test: software projection profile is not supported");
 if(near_scale<=0||near_clip<=0||scale_x==0||scale_y==0)throw std::runtime_error("Bushwacker test: unsupported source projection");
 auto state_=preview?*original->state_snapshot:snapshot(*device);state_[D3DRENDERSTATE_TEXTUREPERSPECTIVE]=1;state_[256+D3DTSS_MAGFILTER]=D3DTFG_LINEAR;state_[256+D3DTSS_MINFILTER]=D3DTFN_LINEAR;state_[D3DRENDERSTATE_ALPHABLENDENABLE]=0;state_[D3DRENDERSTATE_ALPHATESTENABLE]=0;state_[D3DRENDERSTATE_SPECULARENABLE]=0;state_[D3DRENDERSTATE_CULLMODE]=D3DCULL_NONE;state_[D3DRENDERSTATE_SHADEMODE]=D3DSHADE_GOURAUD;state_[256+D3DTSS_COLOROP]=o.textures.empty()?D3DTOP_SELECTARG1:D3DTOP_MODULATE;state_[256+D3DTSS_COLORARG1]=o.textures.empty()?D3DTA_DIFFUSE:D3DTA_TEXTURE;state_[256+D3DTSS_COLORARG2]=D3DTA_DIFFUSE;state_[256+D3DTSS_ALPHAOP]=D3DTOP_SELECTARG1;state_[256+D3DTSS_ALPHAARG1]=D3DTA_DIFFUSE;auto saved_state=std::make_shared<const std::vector<unsigned>>(std::move(state_));
 struct CameraVertex{double x,y,z,u,v,shade;};struct TlVertex{float x,y,z,rhw;unsigned diffuse,specular;float u,v;};static_assert(sizeof(TlVertex)==32);
 std::map<std::string,OverrideMatrix>placement_frames;
 unsigned triangles=0,gpu_batches=0,cpu_near_batches=0;
 for(const auto&batch:o.batches)if(batch.model==o.scope.model&&batch.owner==o.scope.owner){
  if(preview){const auto name=pose_name(o.scope.node,36);if(!batch.visibility_node.empty()?batch.visibility_node!=name:name!=batch.owner)continue;}
  if(!batch.visibility_node.empty()){const auto node=o.active_nodes.find({o.scope.root,batch.visibility_node});if(node==o.active_nodes.end())throw std::runtime_error("Replacement models: missing source visibility node");if(!node->second)continue;}
  auto batch_to_camera=control_to_camera;if(donor)batch_to_camera=batch.vertex_bones.empty()?override_product(donor_root_camera,donor->pose.world.at(batch.donor_bone)):donor_root_camera;
  if(!batch.placement_frame.empty()){
   auto found=placement_frames.find(batch.placement_frame);if(found==placement_frames.end())found=placement_frames.emplace(batch.placement_frame,override_placement_frame_camera(batch.placement_frame,control_to_camera)).first;
   for(unsigned row=0;row<3;++row)for(unsigned col=0;col<3;++col)batch_to_camera[row*4+3]+=found->second[row*4+col]*batch.placement_offset[col];
  }
  if(!batch.joint_frame.empty()){
   auto found=placement_frames.find(batch.joint_frame);if(found==placement_frames.end())found=placement_frames.emplace(batch.joint_frame,override_placement_frame_camera(batch.joint_frame,control_to_camera)).first;
   for(unsigned row=0;row<3;++row)for(unsigned col=0;col<3;++col)batch_to_camera[row*4+3]+=found->second[row*4+col]*batch.joint_offset[col];
  }
  if(!batch.anchor_control.empty()){
   auto anchor=placement_frames.find(batch.anchor_control);if(anchor==placement_frames.end())anchor=placement_frames.emplace(batch.anchor_control,override_placement_frame_camera(batch.anchor_control,control_to_camera)).first;
   const auto&parent=placement_frames.at(batch.placement_frame);
   for(unsigned row=0;row<3;++row){double desired=parent[row*4+3];for(unsigned col=0;col<3;++col)desired+=parent[row*4+col]*batch.anchor_position[col];batch_to_camera[row*4+3]+=desired-anchor->second[row*4+3];}
  }
  const int active_tex=o.scope.skin?batch.skin_textures.at(o.scope.skin):batch.texture;
  const auto active_surface_material=(batch.surface_material&&active_tex>=0&&size_t(active_tex)<o.textures.size()&&o.textures[active_tex].name==batch.surface_material->material_name)?batch.surface_material:nullptr;
  D3DCmd draw{D3DCmd::Draw,D3DPT_TRIANGLELIST,0,0.f,{},{},0};draw.state_snapshot=saved_state;draw.texture=0;draw.override_texture=active_tex;draw.override_normal_texture=batch.normal_texture;draw.surface_material=active_surface_material;draw.hud_role=wide_hud_role();draw.condition_schematic=preview;zoom_capture_command(draw);
  if(mw34::vkscene::Renderer::gpu_models()&&batch.vertex_bones.empty()){if(!batch.geometry)throw std::runtime_error("Replacement GPU geometry was not prepared");
   double zlo=batch_to_camera[11],zhi=zlo;for(unsigned i=0;i<3;++i){const double a=batch_to_camera[8+i]*batch.lo[i],b=batch_to_camera[8+i]*batch.hi[i];zlo+=std::min(a,b);zhi+=std::max(a,b);}
   // Conservative AABB: batches touching the near plane retain the current CPU
   // clipper. The common fully visible case never transforms CPU vertices.
   if(zhi<near_clip)continue;const double margin=std::max(1e-4,std::abs(near_clip)*1e-5);
   if(zlo>near_clip+margin){auto instance=std::make_shared<mw34::vkscene::ModelInstance>();instance->geometry=batch.geometry;instance->surface_material=active_surface_material;for(unsigned i=0;i<12;++i){instance->camera[i]=float(batch_to_camera[i]);if(!std::isfinite(instance->camera[i]))throw std::runtime_error("Replacement GPU camera matrix is not representable");}
    instance->projection={float(near_scale),float(scale_x),float(scale_y),float(center_x),float(center_y),float(near_clip)};for(float p:instance->projection)if(!std::isfinite(p))throw std::runtime_error("Replacement GPU projection is not representable");instance->color=batch.color;instance->diagnostic_fog_factor=float(preview_specular>>24)/255.f;sun_capture_model(*instance,o.scope.node,node_to_camera,batch_to_camera);draw.model=std::move(instance);
    if(preview)for(unsigned corner=0;corner<8;++corner){double p[3];for(unsigned a=0;a<3;++a)p[a]=(corner&(1U<<a))?batch.hi[a]:batch.lo[a];double camera[3];for(unsigned row=0;row<3;++row){camera[row]=batch_to_camera[row*4+3];for(unsigned a=0;a<3;++a)camera[row]+=batch_to_camera[row*4+a]*p[a];}const double rhw=near_scale/camera[2];override_preview_point(camera[0]*scale_x*rhw+center_x,camera[1]*scale_y*rhw+center_y);}device->commands.push_back(std::move(draw));triangles+=unsigned(batch.vertices.size()/3);++gpu_batches;if(geometry_profile.file){++geometry_profile.gpu_batches;geometry_profile.gpu_vertices+=batch.vertices.size();}continue;}++cpu_near_batches;if(geometry_profile.file)++geometry_profile.near_batches;
  }if(geometry_profile.file)geometry_profile.cpu_vertices+=batch.vertices.size();draw.vertices.reserve(batch.vertices.size()*sizeof(TlVertex));
  for(size_t at=0;at<batch.vertices.size();at+=3){std::array<CameraVertex,3>polygon{};for(unsigned i=0;i<3;++i){const auto&v=batch.vertices[at+i];auto m=batch_to_camera;if(donor&&!batch.vertex_bones.empty())m=override_product(m,donor->pose.world.at(batch.vertex_bones.at(at+i)));double nx=m[0]*v.nx+m[1]*v.ny+m[2]*v.nz,ny=m[4]*v.nx+m[5]*v.ny+m[6]*v.nz,nz=m[8]*v.nx+m[9]*v.ny+m[10]*v.nz;double length=std::sqrt(nx*nx+ny*ny+nz*nz);double shade=.35+.65*std::max(0.,(.3*nx+.6*ny-.74*nz)/length);polygon[i]={m[0]*v.x+m[1]*v.y+m[2]*v.z+m[3],m[4]*v.x+m[5]*v.y+m[6]*v.z+m[7],m[8]*v.x+m[9]*v.y+m[10]*v.z+m[11],v.u,v.v,shade};}
   std::array<CameraVertex,4>clipped{};size_t clipped_count=0;for(size_t i=0;i<polygon.size();++i){const auto&a=polygon[i];const auto&b=polygon[(i+1)%polygon.size()];bool in_a=a.z>=near_clip,in_b=b.z>=near_clip;if(in_a)clipped[clipped_count++]=a;if(in_a!=in_b){double t=(near_clip-a.z)/(b.z-a.z);clipped[clipped_count++]={a.x+t*(b.x-a.x),a.y+t*(b.y-a.y),near_clip,a.u+t*(b.u-a.u),a.v+t*(b.v-a.v),a.shade+t*(b.shade-a.shade)};}}
   auto add=[&](const CameraVertex&v){double rhw=near_scale/v.z;unsigned color=0xff000000U;for(unsigned shift:{0U,8U,16U})color|=unsigned(std::clamp(double((batch.color>>shift)&255)*v.shade,0.,255.))<<shift;TlVertex vertex{float(v.x*scale_x*rhw+center_x),float(v.y*scale_y*rhw+center_y),float(rhw),float(rhw),color,preview_specular,float(v.u),float(v.v)};if(!std::isfinite(vertex.x)||!std::isfinite(vertex.y)||!std::isfinite(vertex.z))throw std::runtime_error("Bushwacker test: nonfinite projected vertex");const auto*p=reinterpret_cast<const unsigned char*>(&vertex);draw.vertices.insert(draw.vertices.end(),p,p+sizeof vertex);};
   for(size_t i=1;i+1<clipped_count;++i){add(clipped[0]);add(clipped[i]);add(clipped[i+1]);++triangles;}
  }
  if(!draw.vertices.empty())device->commands.push_back(std::move(draw));
 }
 if(preview)o.preview_emitted.insert(o.scope.node);else o.emitted.insert({o.scope.root,o.scope.owner});if(o.last_frame!=host.frames){o.last_frame=host.frames;++o.emitted_frames;}if(o.emitted_frames<4||host.frames%100==0)o.log<<"{\"event\":\"replacement_queued\",\"frame\":"<<host.frames<<",\"node\":"<<o.scope.node<<",\"model\":\""<<override_models()[o.scope.model].id<<"\",\"lod\":"<<override_models()[o.scope.model].lod<<",\"root\":"<<o.scope.root<<",\"skin\":"<<o.scope.skin<<",\"owner\":\""<<o.scope.owner<<"\",\"triangles\":"<<triangles<<",\"preview\":"<<(preview?"true":"false")<<",\"role\":"<<wide_hud_role()<<",\"fog_factor\":"<<(preview_specular>>24)<<",\"gpu_batches\":"<<gpu_batches<<",\"cpu_near_batches\":"<<cpu_near_batches<<"}\n";
}

#include "model_geometry_warmup.inc"
