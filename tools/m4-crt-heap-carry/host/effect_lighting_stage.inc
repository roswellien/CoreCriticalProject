// Read-only observation of actual original effect draws. Never advances the
// source clock or changes weapon state, hits, damage or original effect sprites.
struct FixtureSourceProof {
 std::vector<std::pair<unsigned,std::vector<unsigned char>>> ranges;
 unsigned surface{};std::uint64_t version{};unsigned vehicle{},healthy{};
};
struct EffectLightingState {
 bool loaded{};mw34::effects::Catalog catalog;mw34::effects::Cache lights;mw34::effects::Clock clock;
 struct Surface {std::uint64_t version{};unsigned width{},height{},pitch{},memory{},format{};const mw34::effects::Emitter* emitter{};const mw34::fixtures::FixtureDef* fixture{};};
 std::map<unsigned,Surface> surfaces;
 std::array<float,12> camera{};std::array<float,6> projection{};
 unsigned frame{~0U},role{},context{};bool view{};
 unsigned observations{},invalid{};
 std::uint64_t dump_bytes{};
 std::map<std::uint64_t,FixtureSourceProof> fixture_proofs;
 unsigned fixture_frame{~0U};std::uint64_t fixture_generation{~0ULL};
} effect_lighting;
mw34::vehicle_lighting::State fixture_vehicle(unsigned node){
 return mw34::vehicle_lighting::inspect(node,[&](unsigned at)->std::optional<mw34::vehicle_lighting::Node>{
  if(!readable(at,100))return std::nullopt;
  return mw34::vehicle_lighting::Node{pose_name(at,36),override_parent(at),load(at+0x24)};
 });
}
bool fixture_proof_valid(const FixtureSourceProof& proof){
 if(proof.vehicle){if(!readable(proof.vehicle+0x24,4)||!readable(proof.healthy+0x24,4)||
   !(load(proof.vehicle+0x24)&4)||!(load(proof.healthy+0x24)&4))return false;}

 const auto* surface=vsurface(proof.surface);if(!surface||surface->version!=proof.version)return false;
 for(const auto& [address,bytes]:proof.ranges){if(!readable(address,unsigned(bytes.size())))return false;
  unsigned char current[128];if(bytes.size()>sizeof(current))return false;get_bytes(address,current,unsigned(bytes.size()));
  if(std::memcmp(current,bytes.data(),bytes.size()))return false;}
 return true;
}
void fixture_frame(){
 auto&s=effect_lighting;auto&manager=mw34::fixtures::FixtureManager::instance();
 const auto generation=mw34::campaign::CampaignManager::instance().generation();
 const unsigned context=load(0x5f4c8c);
 if(s.fixture_generation!=generation||s.context!=context){manager.clear();s.fixture_proofs.clear();s.fixture_generation=generation;s.context=context;s.lights.clear();}
 if(s.fixture_frame==host.frames)return;s.fixture_frame=host.frames;manager.begin_frame(host.frames,effect_time());
 for(auto it=s.fixture_proofs.begin();it!=s.fixture_proofs.end();){
  if(fixture_proof_valid(it->second)){++it;continue;}manager.remove_source(it->first);it=s.fixture_proofs.erase(it);}
}
bool fixture_capture_proof(const D3DCmd& draw,const VSurfaceRec& surface,FixtureSourceProof& proof){
 if(!draw.fixture_node||!draw.fixture_polygon)return false;
 proof={};proof.surface=surface.guest;proof.version=surface.version;
 if(!readable(draw.fixture_polygon,36))return false;
 std::vector<unsigned char> polygon(36);get_bytes(draw.fixture_polygon,polygon.data(),36);
 proof.ranges.push_back({draw.fixture_polygon,std::move(polygon)});
 if(!capture_node_ranges(draw.fixture_node,proof.ranges))return false;
 return true;
}
std::uint64_t fixture_source(const D3DCmd& draw,const VSurfaceRec& surface){
 if(!draw.fixture_node||!draw.fixture_polygon)return 0;
 const std::uint64_t id=(std::uint64_t(draw.fixture_node)<<32)|draw.fixture_polygon;
 auto&s=effect_lighting;auto old=s.fixture_proofs.find(id);
 if(old!=s.fixture_proofs.end()&&fixture_proof_valid(old->second))return id;
 FixtureSourceProof proof;if(!fixture_capture_proof(draw,surface,proof))return 0;
 const auto vehicle=fixture_vehicle(draw.fixture_node);
 if(vehicle.vehicle){if(!vehicle.alive)return 0;proof.vehicle=vehicle.vehicle;proof.healthy=vehicle.healthy;}

 if(s.fixture_proofs.size()>=4096){auto first=s.fixture_proofs.begin();mw34::fixtures::FixtureManager::instance().remove_source(first->first);s.fixture_proofs.erase(first);}
 s.fixture_proofs[id]=std::move(proof);return id;
}
std::shared_ptr<FixtureSourceProof> fixture_caster_proof(const D3DCmd& draw,const VSurfaceRec& surface){
 auto proof=std::make_shared<FixtureSourceProof>();if(!fixture_capture_proof(draw,surface,*proof))return {};
 return proof;
}

double effect_time(){
 // Read the clock without vclock_query(), which would advance guest time.
 // Explicitly freeze presentation fades in photo mode. The prior 72C528
 // field did not supply elapsed live time and left stale lights behind.
 const double raw=host.vclock()?double(host.vclock_us)*.000001:double(GetTickCount64())*.001;
 return effect_lighting.clock.update(raw,photo_replay.mode!=mw34::photo_replay::Mode::Live);
}
bool effect_trace(){static const bool enabled=[] {const char*p=std::getenv("MW34_EFFECT_LIGHT_TRACE");return p&&std::string(p)=="1";}();return enabled;}
void effect_load(){
 auto&s=effect_lighting;if(s.loaded)return;
 const char*path=std::getenv("MW34_EFFECT_LIGHT_CATALOG");
 if(!path||!*path)throw std::runtime_error("Enabled effect lighting requires a material catalog");
 std::ifstream f(path,std::ios::binary);if(!f)throw std::runtime_error("Effect-light material catalog missing");
 s.catalog=mw34::effects::read_catalog(f);s.loaded=true;
 std::fprintf(stderr,"Effect lights: %zu full-content material keys; limit %u\n",s.catalog.size(),mw34::effects::settings().limit);
}
const mw34::effects::Emitter* effect_material(VSurfaceRec&surface){
 auto&s=effect_lighting;
 const unsigned format=surface.tex_masks[0]==0xf800?1:surface.tex_masks[0]==0x7c00?2:surface.tex_masks[0]==0x0f00?3:0;
 if(surface.bpp!=16||!format||!surface.width||!surface.height||surface.width>4096||surface.height>4096||surface.pitch<surface.width*2)return nullptr;
 if(std::uint64_t(surface.mem)+std::uint64_t(surface.pitch)*(surface.height-1)+std::uint64_t(surface.width)*2>0x100000000ULL)return nullptr;
 const auto found=s.surfaces.find(surface.guest);
 if(found!=s.surfaces.end()){
  const auto&e=found->second;
  if(e.version==surface.version&&e.width==surface.width&&e.height==surface.height&&e.pitch==surface.pitch&&e.memory==surface.mem&&e.format==format)return e.emitter;
 }
 gpu_sync(surface.guest);std::vector<unsigned char>pixels(size_t(surface.width)*surface.height*2);
 for(unsigned y=0;y<surface.height;++y)surface_read(surface,y*surface.pitch,pixels.data()+size_t(y)*surface.width*2,surface.width*2);
 const mw34::materials::SurfaceKey key{surface.width,surface.height,format,mw34::materials::normal_hash(pixels.data(),pixels.size())};
 const auto match=s.catalog.find(key);const auto*emitter=match==s.catalog.end()?nullptr:&match->second;
 const auto*fixture=mw34::fixtures::match_fixture(surface.width,surface.height,format,key.hash);
 s.surfaces[surface.guest]={surface.version,surface.width,surface.height,surface.pitch,surface.mem,format,emitter,fixture};
 if(fixture)std::fprintf(stderr,"[FIXTURE] Bound %s (%ux%u hash=0x%llx) on surface %u\n",fixture->name,surface.width,surface.height,(unsigned long long)key.hash,surface.guest);
 if(effect_trace())std::fprintf(stderr,"FX material %s texture=%u size=%ux%u format=%u hash=%llu kind=%u\n",emitter?"MATCH":"MISS",surface.guest,key.width,key.height,key.format,(unsigned long long)key.hash,emitter?emitter->kind:0);
 // Bounded opt-in evidence for a material that failed exact admission. These
 // local native words diagnose upload conversion; they never admit a source.
 if(!emitter&&format==3&&effect_trace())if(const char*root=std::getenv("MW34_EFFECT_LIGHT_DUMP");root&&*root&&s.dump_bytes+pixels.size()<=64ULL*1024*1024){
  std::filesystem::create_directories(root);
  const auto path=std::filesystem::path(root)/(std::to_string(key.width)+"_"+std::to_string(key.height)+"_"+std::to_string(key.format)+"_"+std::to_string(key.hash)+".bin");
  if(!std::filesystem::exists(path)){std::ofstream file(path,std::ios::binary);file.write(reinterpret_cast<const char*>(pixels.data()),std::streamsize(pixels.size()));if(!file)throw std::runtime_error("Effect-light diagnostic write failed");s.dump_bytes+=pixels.size();}
 }
 return emitter;
}
const mw34::fixtures::FixtureDef* fixture_of(VSurfaceRec&surface){
 auto&s=effect_lighting;
 const auto found=s.surfaces.find(surface.guest);
 if(found!=s.surfaces.end()){
  const auto&e=found->second;
  if(e.version==surface.version&&e.width==surface.width&&e.height==surface.height&&e.pitch==surface.pitch&&e.memory==surface.mem)return e.fixture;
 }
 effect_material(surface);
 const auto found2=s.surfaces.find(surface.guest);
 return found2!=s.surfaces.end()?found2->second.fixture:nullptr;
}
// Static lamp placement uses original, unclipped polygon corners. Screen TL
// corners vary with the camera and cannot identify or position a retained lamp.
bool fixture_original_polygon(const D3DCmd& draw,D3DCmd& identity,
 std::vector<mw34::fixtures::FixtureManager::UvPoint>& vertices){
 if(!world_cell_depth||!fixture_mesh_node||fixture_mesh_frame<0x120||
    draw.hud_role!=WideWorld||draw.flags!=D3DPT_TRIANGLEFAN||!draw.indices.empty())return false;
 const unsigned node=fixture_mesh_node,frame=fixture_mesh_frame;
 if(!readable(node,0x64)||!readable(frame-0x120,0x124))return false;
 const unsigned mesh=load(node+0x3c);
 if(!mesh||!readable(mesh,0x48)||load(frame-0x38)!=mesh)return false;
 // Billboards, morphs and animated-light meshes keep their existing path.
 if(load(mesh)||load(mesh+0x1c)||load(mesh+0x20))return false;
 const unsigned count=load(mesh+0x10),nvertices=load(mesh+0x14),base=load(mesh+0x34),xyz=load(mesh+0x38),poly=load(frame-0x34);
 if(!count||count>4096||!nvertices||nvertices>65535||poly<base||(poly-base)%36||
    (poly-base)/36>=count||!readable(poly,36)||!readable(xyz,nvertices*12))return false;
 if(load(frame-0x44)!=load(poly+28))return false;
 const unsigned flags=load(poly),n=flags&255,indices=load(poly+8),uv=load(poly+16);
 if(n<3||n>128||!uv||!readable(indices,n*4)||!readable(uv,n*8))return false;
 const unsigned stack=load(0x5eda90);if(!stack||!readable(stack,4)||!readable(load(stack),48))return false;
 OverrideMatrix camera;if(!sun_camera_world(camera))return false;
 const auto matrix=override_product(camera,override_matrix(load(stack)));
 for(unsigned i=0;i<n;++i){const unsigned k=load(indices+i*4);if(k>=nvertices)return false;
  const float x=world_float(xyz+k*12),y=world_float(xyz+k*12+4),z=world_float(xyz+k*12+8);
  mw34::fixtures::FixtureManager::UvPoint v;
  for(unsigned r=0;r<3;++r)v.p[r]=float(matrix[r*4]*x+matrix[r*4+1]*y+matrix[r*4+2]*z+matrix[r*4+3]);
  v.u=world_float(uv+i*8);v.v=world_float(uv+i*8+4);vertices.push_back(v);
 }
 identity.fixture_node=node;identity.fixture_polygon=poly;return true;
}
bool effect_enabled(){static const bool enabled=[] {SunCaptureFp preserve;mw34::vkscene::HostFpEnvironment fp;return mw34::effects::settings().enabled;}();return enabled;}
void effect_observe(const D3DCmd&draw){
 if(!effect_enabled())return;
 SunCaptureFp preserve;mw34::vkscene::HostFpEnvironment fp;
 auto&s=effect_lighting;
 if(frontend_on()){s.view=false;s.lights.clear();return;}
 fixture_frame();
 if(override_suppress_draw())return;
 if(draw.hud_role!=WideWorld&&draw.hud_role!=WideZoom){
  if(effect_trace()&&draw.texture){effect_load();if(auto*surface=vsurface(draw.texture))if(const auto*emitter=effect_material(*surface))std::fprintf(stderr,"FX skipped non-world role=%u kind=%u\n",draw.hud_role,emitter->kind);}
  return;
 }
 effect_load();
 const unsigned context=load(0x5f4c8c);
 if(s.context!=context){s.context=context;s.view=false;s.lights.clear();}
 if(s.frame!=host.frames||s.role!=draw.hud_role){s.frame=host.frames;s.role=draw.hud_role;s.view=false;}
 const auto&captured=draw.sun_tl?draw.sun_tl:draw.sky_view;
 if(captured){s.camera=captured->camera_world;s.projection=captured->projection;s.view=true;}
 OverrideMatrix camera;
 if(!s.view&&sun_camera_world(camera)){
  for(unsigned i=0;i<12;++i)s.camera[i]=float(camera[i]);
  s.projection={wide_float(0x73fb80),wide_float(0x73fc30),wide_float(0x73fb98),wide_float(0x73fb88),wide_float(0x73fb8c),wide_float(0x740304)};s.view=true;
 }
 if(!draw.state_snapshot||draw.state_snapshot->size()<256||!draw.texture||draw.vertices.size()%32||draw.vertices.size()>32768)return;
 // Some original effects use alpha test, others additive blending or source
 // clipping with hardware Z off. Their render-state combination is not an
 // identity. Admit only complete luminous material keys in a validated view.
 auto*surface=vsurface(draw.texture);if(!surface)return;
 const auto*emitter=effect_material(*surface);
 const auto*fixture=fixture_of(*surface);
 if(!emitter&&!fixture)return;
 if(!s.view){++s.invalid;return;}
 struct Vertex{float x,y,z,rhw;unsigned rgb,spec;float u,v;};std::vector<mw34::effects::Point>points;
 try{
  if(draw.model&&draw.model->world&&draw.model->sun_eligible){const auto&m=draw.model->sun_world;for(const auto&v:draw.model->geometry->vertices)points.push_back({m[0]*v.x+m[1]*v.y+m[2]*v.z+m[3],m[4]*v.x+m[5]*v.y+m[6]*v.z+m[7],m[8]*v.x+m[9]*v.y+m[10]*v.z+m[11]});}
  else for(size_t at=0;at<draw.vertices.size();at+=32){Vertex v;std::memcpy(&v,draw.vertices.data()+at,32);points.push_back(mw34::effects::reconstruct(v.x,v.y,v.z,s.projection,s.camera));}
 }catch(const std::runtime_error&){++s.invalid;return;}
 if(emitter){s.lights.observe(*emitter,points,effect_time());++s.observations;}
 if(fixture&&mw34::effects::settings().fixtures){
  std::vector<mw34::fixtures::Point> fix_pts;
  fix_pts.reserve(points.size());
  if(draw.model&&draw.model->world&&draw.model->sun_eligible){
   const auto& matrix=draw.model->sun_world;
   for(const auto& v:draw.model->geometry->vertices)fix_pts.push_back({matrix[0]*v.x+matrix[1]*v.y+matrix[2]*v.z+matrix[3],matrix[4]*v.x+matrix[5]*v.y+matrix[6]*v.z+matrix[7],matrix[8]*v.x+matrix[9]*v.y+matrix[10]*v.z+matrix[11]});
  }else for(const auto& p : points) fix_pts.push_back({p[0], p[1], p[2]});
  auto& manager=mw34::fixtures::FixtureManager::instance();
  D3DCmd identity;std::vector<mw34::fixtures::FixtureManager::UvPoint> original;
  if(fixture_original_polygon(draw,identity,original)){
   const auto vehicle=fixture_vehicle(identity.fixture_node);
   if(vehicle.vehicle&&!vehicle.alive)return;
   mw34::fixtures::Point forward{};const mw34::fixtures::Point* direction=nullptr;
   if(vehicle.vehicle&&mw34::vehicle_lighting::headlamp(fixture->name)){
    OverrideMatrix view;if(!sun_camera_world(view))return;
    const auto world=override_product(view,override_matrix(load(load(0x5eda90))));
    forward={float(-world[2]),float(-world[6]),float(-world[10])};
    const float length=std::sqrt(mw34::effects::distance2(forward,{0,0,0}));
    if(!(length>1e-6f))return;for(float&v:forward)v/=length;
    fixture=&manager.directional(*fixture);direction=&forward;
   }
   const auto source=fixture_source(identity,*surface);
   // A stable owner is required before replacing the screen-space fallback.
   if(source){
    if(fixture->emission_regions.empty()){
     std::vector<mw34::fixtures::Point> polygon;for(const auto& v:original)polygon.push_back(v.p);
     manager.observe_polygon(*fixture,polygon,host.frames,source);
    }else if(!fixture->emission_only){
     std::vector<mw34::fixtures::FixtureManager::UvPoint> triangles;
     for(size_t i=1;i+1<original.size();++i){triangles.push_back(original[0]);triangles.push_back(original[i]);triangles.push_back(original[i+1]);}
     manager.observe_regions(*fixture,triangles,host.frames,source,direction);
    }
    return;
   }
  }
  // Vehicle sources require proven original geometry/lifetime, never retained anonymous observations.
  if(fixture_vehicle(draw.fixture_node?draw.fixture_node:fixture_mesh_node).vehicle)return;
  const auto source=fixture_source(draw,*surface);
  // Restore source winding: original TL/GPU submissions reverse the
  // polygon corners. A positive offset must point out of the wall.
  std::reverse(fix_pts.begin(),fix_pts.end());
  if(fixture->emission_regions.empty())manager.observe_polygon(*fixture,fix_pts,host.frames,source);
  else if(!fixture->emission_only){
   std::vector<mw34::fixtures::FixtureManager::UvPoint> vertices,triangles;
   if(draw.model&&draw.model->world&&draw.model->sun_eligible){const auto&m=draw.model->sun_world;for(const auto&v:draw.model->geometry->vertices)vertices.push_back({{m[0]*v.x+m[1]*v.y+m[2]*v.z+m[3],m[4]*v.x+m[5]*v.y+m[6]*v.z+m[7],m[8]*v.x+m[9]*v.y+m[10]*v.z+m[11]},v.u,v.v});triangles=vertices;}
   else{for(size_t i=0;i<points.size();++i){Vertex v;std::memcpy(&v,draw.vertices.data()+i*32,32);vertices.push_back({{points[i][0],points[i][1],points[i][2]},v.u,v.v});}
    const size_t count=draw.indices.empty()?vertices.size():draw.indices.size();auto add=[&](size_t i){const size_t k=draw.indices.empty()?i:draw.indices[i];if(k>=vertices.size())throw std::runtime_error("Fixture UV index outside captured vertices");triangles.push_back(vertices[k]);};
    if(draw.flags==D3DPT_TRIANGLELIST){for(size_t i=0;i+2<count;i+=3){add(i);add(i+1);add(i+2);}}
    else if(draw.flags==D3DPT_TRIANGLEFAN){for(size_t i=1;i+1<count;++i){add(0);add(i);add(i+1);}}
    else if(draw.flags==D3DPT_TRIANGLESTRIP){for(size_t i=0;i+2<count;++i){add(i);add(i+(i&1?2:1));add(i+(i&1?1:2));}}
   }
   for(size_t at=0;at+2<triangles.size();at+=3)std::swap(triangles[at+1],triangles[at+2]);
   manager.observe_regions(*fixture,triangles,host.frames,source);
  }
 }
}
void effect_scene(mw34::vkscene::Scene&scene){
 if(!effect_enabled())return;
 SunCaptureFp preserve;mw34::vkscene::HostFpEnvironment fp;
 auto&s=effect_lighting;if(frontend_on()||scene.frontend_canvas){s.view=false;s.lights.clear();mw34::campaign::CampaignManager::instance().frontend();mw34::fixtures::FixtureManager::instance().clear();s.fixture_proofs.clear();return;}
 if(scene.hud)return; // HUD passes never erase the world's fading lights.
 effect_load();
 mw34::campaign::CampaignManager::instance().enter_world();fixture_frame();
 scene.world_frame=host.frames;scene.world_generation=mw34::campaign::CampaignManager::instance().generation();scene.world_context=load(0x5f4c8c);
 scene.world_eye={s.camera[3],s.camera[7],s.camera[11]};scene.world_eye_valid=s.view;
 if(s.frame!=host.frames||!s.view)return;
 scene.effect_lights=s.lights.uniform(effect_time(),{s.camera[3],s.camera[7],s.camera[11]},mw34::effects::settings().limit,mw34::effects::settings().strength);
 const auto& settings=mw34::effects::settings();
 unsigned count=std::min(unsigned(scene.effect_lights.params[0]),settings.limit);
 const unsigned weapons=count;
 // Unverified hard-coded map emitters are not admitted as scene fixtures.
 if(settings.fixtures&&count<settings.limit){
  const unsigned budget=mw34::effects::fixture_slots(count,settings.limit,settings.weapon_reserve);
  auto lights=mw34::fixtures::FixtureManager::instance().select_lights({s.camera[3],s.camera[7],s.camera[11]},budget,settings.strength,settings.fixture_range_scale,settings.fixture_retain_distance,settings.fixture_fade_distance);
  for(const auto& light:lights)scene.effect_lights.lights[count++]=light;
 }
 if(effect_trace())std::fprintf(stderr,"Light budget frame=%u weapons=%u fixtures=%u total=%u limit=%u cached=%zu\n",host.frames,weapons,count-weapons,count,settings.limit,mw34::fixtures::FixtureManager::instance().active_count());
 scene.effect_lights.params[0]=float(count);
 scene.effect_lights.params[1]=float(weapons);
 scene.effect_lights.params[2]=float(count-weapons);
 scene.effect_lights.params[3]=float(settings.limit);
 if(effect_trace()&&(s.observations||unsigned(scene.effect_lights.params[0])||host.frames%60==0))std::fprintf(stderr,"FX scene frame=%u lights=%u observed=%u invalid=%u\n",host.frames,unsigned(scene.effect_lights.params[0]),s.observations,s.invalid);
 s.observations=s.invalid=0;
}
