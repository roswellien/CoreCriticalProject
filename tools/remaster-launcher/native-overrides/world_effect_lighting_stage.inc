// Read-only observation of actual original effect draws. Never advances the
// source clock or changes weapon state, hits, damage or original effect sprites.
struct FixtureSourceProof {
 std::vector<std::pair<unsigned,std::vector<unsigned char>>> ranges;
 unsigned surface{};std::uint64_t version{};
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
bool fixture_proof_valid(const FixtureSourceProof& proof){
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
 if(s.fixture_frame==host.frames)return;s.fixture_frame=host.frames;manager.begin_frame(host.frames);
 for(auto it=s.fixture_proofs.begin();it!=s.fixture_proofs.end();){
  if(fixture_proof_valid(it->second)){++it;continue;}manager.remove_source(it->first);it=s.fixture_proofs.erase(it);}
}
std::uint64_t fixture_source(const D3DCmd& draw,const VSurfaceRec& surface){
 if(!draw.fixture_node||!draw.fixture_polygon)return 0;
 const std::uint64_t id=(std::uint64_t(draw.fixture_node)<<32)|draw.fixture_polygon;
 auto&s=effect_lighting;auto old=s.fixture_proofs.find(id);
 if(old!=s.fixture_proofs.end()&&fixture_proof_valid(old->second))return id;
 FixtureSourceProof proof;proof.surface=surface.guest;proof.version=surface.version;
 auto snapshot=[&](unsigned address,unsigned bytes){if(!readable(address,bytes))return false;
  std::vector<unsigned char> data(bytes);get_bytes(address,data.data(),bytes);proof.ranges.push_back({address,std::move(data)});return true;};
 const unsigned context=load(0x5f4c8c),root=context&&readable(context,4)?load(context):0;
 if(!root||!snapshot(draw.fixture_polygon,36))return 0;
 unsigned node=draw.fixture_node;
 for(unsigned depth=0;node!=root&&depth<32;++depth){
  if(!snapshot(node,100))return 0;
  if(load(node+0x34)==5&&!snapshot(load(node+0x38),96))return 0;
  const unsigned parent=override_parent(node);if(!parent||!readable(parent,100))return 0;
  const unsigned count=load(parent+0x5c),children=load(parent+0x60);
  if(count>65536||!count||!readable(children,count*4))return 0;
  bool member=false;for(unsigned i=0;i<count;++i)if(load(children+i*4)==node){member=snapshot(parent+0x60,4)&&snapshot(children+i*4,4);break;}
  if(!member)return 0;node=parent;
 }
 if(node!=root)return 0;
 if(s.fixture_proofs.size()>=512){auto first=s.fixture_proofs.begin();mw34::fixtures::FixtureManager::instance().remove_source(first->first);s.fixture_proofs.erase(first);}
 s.fixture_proofs[id]=std::move(proof);return id;
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
 for(unsigned y=0;y<surface.height;++y)get_bytes(surface.mem+y*surface.pitch,pixels.data()+size_t(y)*surface.width*2,surface.width*2);
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
  for(size_t at=0;at<draw.vertices.size();at+=32){Vertex v;std::memcpy(&v,draw.vertices.data()+at,32);points.push_back(mw34::effects::reconstruct(v.x,v.y,v.z,s.projection,s.camera));}
 }catch(const std::runtime_error&){++s.invalid;return;}
 if(emitter){s.lights.observe(*emitter,points,effect_time());++s.observations;}
 if(fixture&&mw34::effects::settings().fixtures){
  std::vector<mw34::fixtures::Point> fix_pts;
  fix_pts.reserve(points.size());
  if(draw.model&&draw.model->world&&draw.model->sun_eligible){
   const auto& matrix=draw.model->sun_world;
   for(const auto& v:draw.model->geometry->vertices)fix_pts.push_back({matrix[0]*v.x+matrix[1]*v.y+matrix[2]*v.z+matrix[3],matrix[4]*v.x+matrix[5]*v.y+matrix[6]*v.z+matrix[7],matrix[8]*v.x+matrix[9]*v.y+matrix[10]*v.z+matrix[11]});
  }else for(const auto& p : points) fix_pts.push_back({p[0], p[1], p[2]});
  mw34::fixtures::FixtureManager::instance().observe_polygon(*fixture, fix_pts, host.frames,fixture_source(draw,*surface));
 }
}
void effect_scene(mw34::vkscene::Scene&scene){
 if(!effect_enabled())return;
 SunCaptureFp preserve;mw34::vkscene::HostFpEnvironment fp;
 auto&s=effect_lighting;if(frontend_on()||scene.frontend_canvas){s.view=false;s.lights.clear();mw34::campaign::CampaignManager::instance().frontend();mw34::fixtures::FixtureManager::instance().clear();s.fixture_proofs.clear();return;}
 if(scene.hud)return; // HUD passes never erase the world's fading lights.
 effect_load();
 mw34::campaign::CampaignManager::instance().enter_world();fixture_frame();
 if(s.frame!=host.frames||!s.view)return;
 scene.effect_lights=s.lights.uniform(effect_time(),{s.camera[3],s.camera[7],s.camera[11]},mw34::effects::settings().limit,mw34::effects::settings().strength);
 const auto& settings=mw34::effects::settings();
 unsigned count=std::min(unsigned(scene.effect_lights.params[0]),settings.limit);
 const unsigned weapons=count;
 // Unverified hard-coded map emitters are not admitted as scene fixtures.
 if(settings.fixtures&&count<settings.limit){
  const unsigned budget=mw34::effects::fixture_slots(count,settings.limit,settings.weapon_reserve);
  auto lights=mw34::fixtures::FixtureManager::instance().select_lights({s.camera[3],s.camera[7],s.camera[11]},budget,settings.strength,settings.fixture_range_scale);
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
