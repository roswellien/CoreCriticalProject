// Optional geometry-only test. Source simulation, pose and render-producer side effects continue.
struct OverrideSourceMesh{const char*name;unsigned vertices;const char*owner;};
#include "override_source_roster.inc"
#include "override_new_rosters.inc"
struct OverrideModel{const char*id;const char*mesh_env;const char*texture_env;const OverrideSourceMesh*roster;size_t count;};
inline static constexpr std::array<OverrideModel,4> override_models{{
 {"bushwacker","MW34_BUSHWACKER_TEST","MW34_BUSHWACKER_TEXTURES",override_source_meshes.data(),override_source_meshes.size()},
 {"madcat","MW34_MADCAT_MESH","MW34_MADCAT_TEXTURES",override_madcat_meshes.data(),override_madcat_meshes.size()},
 {"vulture","MW34_VULTURE_MESH","MW34_VULTURE_TEXTURES",override_vulture_meshes.data(),override_vulture_meshes.size()},
 {"thor","MW34_THOR_MESH","MW34_THOR_TEXTURES",override_thor_meshes.data(),override_thor_meshes.size()}
}};
using OverrideVertex=mw34::vkscene::ModelVertex;
struct OverrideBatch{std::string owner;unsigned color;std::vector<OverrideVertex>vertices;int texture{-1};unsigned model{};std::shared_ptr<const mw34::vkscene::ModelGeometry>geometry;std::array<float,3>lo{},hi{};};
using OverrideMatrix=std::array<double,16>;
struct OverrideScope{unsigned node{};std::string owner;OverrideMatrix owner_to_node{};unsigned root{},model{};};
struct OverrideMxcsr{unsigned value=_mm_getcsr();~OverrideMxcsr(){_mm_setcsr(value);}};
struct OverrideTexture{std::string name;unsigned width,height;std::uint64_t hash;std::vector<std::uint16_t>pixels;};
struct OverrideState{std::vector<OverrideTexture>textures;bool loaded{};std::vector<OverrideBatch>batches;OverrideScope scope;std::map<unsigned,int>validated_roots;std::set<std::pair<unsigned,unsigned>>announced_roots;std::set<std::pair<unsigned,std::string>>emitted;std::ofstream log;unsigned emitted_frames{},last_frame{~0U};};
static OverrideState&override_state(){static OverrideState state;return state;}
static bool override_enabled(){static const bool enabled=[](){for(const auto&m:override_models)if(std::getenv(m.mesh_env))return true;return false;}();return enabled;}
static OverrideMatrix override_identity(){return {1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};}
static OverrideMatrix override_product(const OverrideMatrix&a,const OverrideMatrix&b){OverrideMatrix result{};for(unsigned i=0;i<4;++i)for(unsigned j=0;j<4;++j)for(unsigned k=0;k<4;++k)result[i*4+j]+=a[i*4+k]*b[k*4+j];return result;}
OverrideMatrix override_matrix(unsigned address){if(!readable(address,48))throw std::runtime_error("Bushwacker test: unreadable source matrix");std::array<float,12>a{};for(unsigned i=0;i<12;++i){unsigned bits=load(address+4*i);std::memcpy(&a[i],&bits,4);if(!std::isfinite(a[i]))throw std::runtime_error("Bushwacker test: nonfinite source matrix");}
 return {a[0],a[3],a[6],a[9],a[1],a[4],a[7],a[10],a[2],a[5],a[8],a[11],0,0,0,1};}
static OverrideMatrix override_inverse(OverrideMatrix a){auto inverse=override_identity();for(unsigned col=0;col<4;++col){unsigned pivot=col;for(unsigned row=col+1;row<4;++row)if(std::abs(a[row*4+col])>std::abs(a[pivot*4+col]))pivot=row;if(std::abs(a[pivot*4+col])<1e-10)throw std::runtime_error("Bushwacker test: singular source matrix");for(unsigned j=0;j<4;++j){std::swap(a[col*4+j],a[pivot*4+j]);std::swap(inverse[col*4+j],inverse[pivot*4+j]);}double scale=a[col*4+col];for(unsigned j=0;j<4;++j){a[col*4+j]/=scale;inverse[col*4+j]/=scale;}for(unsigned row=0;row<4;++row)if(row!=col){scale=a[row*4+col];for(unsigned j=0;j<4;++j){a[row*4+j]-=scale*a[col*4+j];inverse[row*4+j]-=scale*inverse[col*4+j];}}}return inverse;}

void override_load_textures(const OverrideModel&model,size_t first,size_t end){
 const char*path=std::getenv(model.texture_env);if(!path)return;auto&o=override_state();std::ifstream file(path,std::ios::binary);
 auto bytes=[&](void*p,size_t n){if(!file.read(static_cast<char*>(p),std::streamsize(n)))throw std::runtime_error("Replacement textures: incomplete sidecar");};
 char magic[8];bytes(magic,8);if(std::memcmp(magic,"BWTEX1\0\0",8))throw std::runtime_error("Replacement textures: wrong format");
 unsigned batches,count;bytes(&batches,4);bytes(&count,4);if(batches!=end-first||count!=5)throw std::runtime_error("Replacement textures: material count mismatch");
 const auto offset=o.textures.size();
 for(size_t at=first;at<end;++at){unsigned index;bytes(&index,4);if(index>=count)throw std::runtime_error("Replacement textures: invalid material index");o.batches[at].texture=int(offset+index);o.batches[at].color=0xffffffff;}
 for(unsigned i=0;i<count;++i){char name[32];bytes(name,32);if(name[31])throw std::runtime_error("Replacement textures: invalid name");OverrideTexture t{};t.name=name;bytes(&t.width,4);bytes(&t.height,4);bytes(&t.hash,8);
  if(!t.width||!t.height||t.width>4096||t.height>4096)throw std::runtime_error("Replacement textures: invalid dimensions");t.pixels.resize(size_t(t.width)*t.height);bytes(t.pixels.data(),t.pixels.size()*2);o.textures.push_back(std::move(t));}
 if(file.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Replacement textures: trailing data");
 o.log<<"{\"event\":\"textures_loaded\",\"model\":\""<<model.id<<"\",\"materials\":5,\"format\":\"RGB565\",\"scope\":\"base-color only\"}\n";
}
void override_prepare_geometry(OverrideBatch&b,size_t index){if(!mw34::vkscene::Renderer::gpu_models())return;
 auto g=std::make_shared<mw34::vkscene::ModelGeometry>();g->key=0x4d4f444c00000000ULL+index;g->vertices=b.vertices;g->hash=0xcbf29ce484222325ULL;
 const auto*bytes=reinterpret_cast<const unsigned char*>(g->vertices.data());for(size_t i=0;i<g->vertices.size()*sizeof(OverrideVertex);++i){g->hash^=bytes[i];g->hash*=0x100000001b3ULL;}
 b.lo=b.hi={b.vertices[0].x,b.vertices[0].y,b.vertices[0].z};for(const auto&v:b.vertices){const std::array<float,3>p{v.x,v.y,v.z};for(unsigned i=0;i<3;++i){b.lo[i]=std::min(b.lo[i],p[i]);b.hi[i]=std::max(b.hi[i],p[i]);}}b.geometry=std::move(g);}
void override_load(){auto&o=override_state();if(o.loaded)return;
 const char*log_path=std::getenv("MW34_MODELS_LOG");if(!log_path)log_path=std::getenv("MW34_BUSHWACKER_TEST_LOG");
 o.log.open(log_path?log_path:"local/remaster/model-runtime.jsonl",std::ios::trunc);if(!o.log)throw std::runtime_error("Replacement models: cannot open runtime log");
 for(unsigned id=0;id<override_models.size();++id){const auto&model=override_models[id];const char*path=std::getenv(model.mesh_env);if(!path)continue;
  std::ifstream file(path,std::ios::binary);auto bytes=[&](void*p,size_t n){if(!file.read(static_cast<char*>(p),std::streamsize(n)))throw std::runtime_error("Replacement models: incomplete mesh payload");};
  char magic[8];bytes(magic,8);if(std::memcmp(magic,"BWMESH1\0",8))throw std::runtime_error("Replacement models: wrong mesh payload");unsigned count;bytes(&count,4);if(!count||count>256)throw std::runtime_error("Replacement models: invalid batch count");const size_t first=o.batches.size();
  for(unsigned i=0;i<count;++i){char name[32];bytes(name,32);if(name[31])throw std::runtime_error("Replacement models: invalid controller name");
   bool owner=false;for(size_t r=0;r<model.count;++r)if(std::string(name)==model.roster[r].owner)owner=true;if(!owner)throw std::runtime_error("Replacement models: unknown source controller");
   unsigned size,color;bytes(&size,4);bytes(&color,4);if(!size||size>65535||size%3)throw std::runtime_error("Replacement models: invalid triangle count");OverrideBatch batch{name,color,{}};batch.model=id;batch.vertices.resize(size);bytes(batch.vertices.data(),size*sizeof(OverrideVertex));
   for(const auto&v:batch.vertices){for(float value:{v.x,v.y,v.z,v.nx,v.ny,v.nz,v.u,v.v})if(!std::isfinite(value))throw std::runtime_error("Replacement models: nonfinite mesh payload");if(v.nx*v.nx+v.ny*v.ny+v.nz*v.nz<.5f)throw std::runtime_error("Replacement models: invalid normal");}
   override_prepare_geometry(batch,o.batches.size());o.batches.push_back(std::move(batch));}
  if(file.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Replacement models: trailing mesh payload");
  for(size_t r=0;r<model.count;++r){bool present=false;for(size_t b=first;b<o.batches.size();++b)if(o.batches[b].owner==model.roster[r].owner)present=true;
   if(!present)throw std::runtime_error("Replacement models: missing required source controller geometry");}
  override_load_textures(model,first,o.batches.size());
  o.log<<"{\"event\":\"enabled\",\"model\":\""<<model.id<<"\",\"batches\":"<<count<<",\"scope\":\"optional visual replacement; source gameplay preserved\"}\n";
 }o.loaded=true;
}
unsigned override_parent(unsigned node){if(!readable(node,100)||load(node+0x54)!=1||!readable(load(node+0x58),4))return 0;return load(load(node+0x58));}

int override_validate_root(unsigned root){auto&o=override_state();auto cached=o.validated_roots.find(root);if(cached!=o.validated_roots.end())return cached->second;
 std::map<std::string,unsigned>meshes;std::vector<unsigned>queue{root};std::set<unsigned>seen;
 for(size_t i=0;i<queue.size();++i){if(i>=128)throw std::runtime_error("Replacement models: hierarchy too large");unsigned node=queue[i];if(!seen.insert(node).second)throw std::runtime_error("Replacement models: shared/cyclic hierarchy");
  if(!readable(node,100))throw std::runtime_error("Replacement models: incomplete instance hierarchy");unsigned count=load(node+0x5c),children=load(node+0x60);if(count>64||(count&&!readable(children,count*4)))throw std::runtime_error("Replacement models: invalid children");
  for(unsigned j=0;j<count;++j)queue.push_back(load(children+4*j));unsigned mesh=load(node+0x3c);if(mesh){if(!readable(mesh,24))throw std::runtime_error("Replacement models: unreadable source mesh");if(!meshes.emplace(pose_name(node,36),load(mesh+20)).second)throw std::runtime_error("Replacement models: duplicate source mesh name");}}
 // Live player instances attach these two auxiliary meshes after loading the chassis.
 // Keep their original draws; they are not part of chassis identity or replacement geometry.
 meshes.erase("left ski");meshes.erase("right ski");
 // The current host can attach the original cockpit to the same live root.
 // Exclude only its complete, observed mesh signature; keep its original draws.
 const std::array<std::pair<const char*,unsigned>,13> cockpit{{{"cpit_ania",4},{"cpit_anib",4},{"cpit_anic",4},{"crack01",4},{"crack02",4},{"crack03",4},{"dbase",138},{"ding01",4},{"ding02",4},{"ding03",4},{"g40",54},{"hcrack01",3},{"hcrack02",3}}};
 bool attached_cockpit=true;for(const auto&c:cockpit){auto it=meshes.find(c.first);if(it==meshes.end()||it->second!=c.second){attached_cockpit=false;break;}}
 if(attached_cockpit)for(const auto&c:cockpit)meshes.erase(c.first);
 int result=-1;
 for(unsigned id=0;id<override_models.size();++id){const auto&m=override_models[id];if(!std::getenv(m.mesh_env)||meshes.size()!=m.count)continue;bool match=true;
  for(size_t at=0;at<m.count;++at){const auto&r=m.roster[at];auto it=meshes.find(r.name);if(it==meshes.end()||it->second!=r.vertices){match=false;break;}}
  if(match){if(result>=0)throw std::runtime_error("Replacement models: ambiguous chassis identity");result=int(id);}}
 o.validated_roots.emplace(root,result);
 if(result<0&&o.announced_roots.emplace(root,~0U).second){
  o.log<<"{\"event\":\"identity_rejected\",\"root\":"<<root<<",\"meshes\":[";
  bool first=true;for(const auto&entry:meshes){if(!first)o.log<<',';first=false;o.log<<"{\"name\":\""<<entry.first<<"\",\"vertices\":"<<entry.second<<'}';}
  o.log<<"]}\n";o.log.flush();
 }
 if(result>=0&&o.announced_roots.emplace(root,unsigned(result)).second)o.log<<"{\"event\":\"instance_validated\",\"root\":"<<root<<",\"model\":\""<<override_models[result].id<<"\",\"source_meshes\":"<<meshes.size()<<"}\n";
 return result;
}
OverrideScope override_begin(unsigned node){OverrideMxcsr preserve;auto&o=override_state();OverrideScope previous=o.scope;o.scope={};if(!override_enabled())return previous;override_load();
 const auto name=pose_name(node,36);bool candidate=false;for(const auto&m:override_models)if(std::getenv(m.mesh_env))for(size_t at=0;at<m.count;++at)if(name==m.roster[at].name)candidate=true;if(!candidate)return previous;
 unsigned root=0,current=node;for(unsigned depth_=0;current&&depth_<32;++depth_){if(pose_name(current,36)=="hip"){root=override_parent(current);break;}current=override_parent(current);}if(!root)return previous;
 const int id=override_validate_root(root);if(id<0)return previous;const auto&model=override_models[id];const OverrideSourceMesh*mesh=nullptr;for(size_t at=0;at<model.count;++at)if(name==model.roster[at].name){mesh=&model.roster[at];break;}if(!mesh)return previous;
 OverrideMatrix owner_to_node=override_identity();current=node;for(unsigned depth_=0;pose_name(current,36)!=mesh->owner;++depth_){if(depth_>=16||!current||load(current+0x34)!=5)throw std::runtime_error("Replacement models: unsupported control ancestry");unsigned data_=load(current+0x38);if(!readable(data_,96))throw std::runtime_error("Replacement models: unreadable control data");auto local=(load(data_)&8)?override_identity():override_matrix(data_+0x30);owner_to_node=override_product(local,owner_to_node);current=override_parent(current);}
 o.scope={node,mesh->owner,owner_to_node,root,unsigned(id)};return previous;
}
void override_restore(const OverrideScope&scope){override_state().scope=scope;}
void override_scene_start(){if(override_enabled()){override_state().emitted.clear();override_state().validated_roots.clear();}}
bool override_suppress_draw(){if(!override_enabled()||!override_state().scope.node)return false;if(!override_state().emitted.count({override_state().scope.root,override_state().scope.owner}))throw std::runtime_error("Bushwacker test: source draw reached without replacement projection");return true;}
void override_emit(){if(!override_enabled())return;auto&o=override_state();if(!o.scope.node||o.emitted.count({o.scope.root,o.scope.owner}))return;
 // All arithmetic uses AMD64 SSE; retain the guest's MXCSR flags and rounding.
 struct PreserveMxcsr{unsigned value=_mm_getcsr();~PreserveMxcsr(){_mm_setcsr(value);}} preserve;
 D3DDev*device=nullptr;for(auto&d:host.devices)if(d.in_scene){if(device)throw std::runtime_error("Bushwacker test: ambiguous current scene");device=&d;}if(!device)throw std::runtime_error("Bushwacker test: no active native scene");
 const unsigned pointer=load(0x5eda90);if(!readable(pointer,4))throw std::runtime_error("Bushwacker test: missing model-view stack");auto node_to_camera=override_matrix(load(pointer));auto control_to_camera=override_product(node_to_camera,override_inverse(o.scope.owner_to_node));
 auto source_float=[&](unsigned address){unsigned bits=load(address);float value;std::memcpy(&value,&bits,4);if(!std::isfinite(value))throw std::runtime_error("Bushwacker test: invalid source projection");return double(value);};
 const double near_scale=source_float(0x73fb80),scale_x=source_float(0x73fc30),scale_y=source_float(0x73fb98),center_x=source_float(0x73fb88),center_y=source_float(0x73fb8c),near_clip=source_float(0x740304);
 if(load(0x72f348)==0)throw std::runtime_error("Bushwacker test: software projection profile is not supported");
 if(near_scale<=0||near_clip<=0||scale_x==0||scale_y==0)throw std::runtime_error("Bushwacker test: unsupported source projection");
 auto state_=snapshot(*device);state_[D3DRENDERSTATE_TEXTUREPERSPECTIVE]=1;state_[256+D3DTSS_MAGFILTER]=D3DTFG_LINEAR;state_[256+D3DTSS_MINFILTER]=D3DTFN_LINEAR;state_[D3DRENDERSTATE_ALPHABLENDENABLE]=0;state_[D3DRENDERSTATE_ALPHATESTENABLE]=0;state_[D3DRENDERSTATE_SPECULARENABLE]=0;state_[D3DRENDERSTATE_CULLMODE]=D3DCULL_NONE;state_[D3DRENDERSTATE_SHADEMODE]=D3DSHADE_GOURAUD;state_[256+D3DTSS_COLOROP]=o.textures.empty()?D3DTOP_SELECTARG1:D3DTOP_MODULATE;state_[256+D3DTSS_COLORARG1]=o.textures.empty()?D3DTA_DIFFUSE:D3DTA_TEXTURE;state_[256+D3DTSS_COLORARG2]=D3DTA_DIFFUSE;state_[256+D3DTSS_ALPHAOP]=D3DTOP_SELECTARG1;state_[256+D3DTSS_ALPHAARG1]=D3DTA_DIFFUSE;auto saved_state=std::make_shared<const std::vector<unsigned>>(std::move(state_));
 struct CameraVertex{double x,y,z,u,v,shade;};struct TlVertex{float x,y,z,rhw;unsigned diffuse,specular;float u,v;};static_assert(sizeof(TlVertex)==32);
 unsigned triangles=0,gpu_batches=0,cpu_near_batches=0;
 for(const auto&batch:o.batches)if(batch.model==o.scope.model&&batch.owner==o.scope.owner){D3DCmd draw{D3DCmd::Draw,D3DPT_TRIANGLELIST,0,0.f,{},{},0};draw.state_snapshot=saved_state;draw.texture=0;draw.override_texture=batch.texture;draw.hud_role=wide_hud_role();
  if(mw34::vkscene::Renderer::gpu_models()){if(!batch.geometry)throw std::runtime_error("Replacement GPU geometry was not prepared");
   double zlo=control_to_camera[11],zhi=zlo;for(unsigned i=0;i<3;++i){const double a=control_to_camera[8+i]*batch.lo[i],b=control_to_camera[8+i]*batch.hi[i];zlo+=std::min(a,b);zhi+=std::max(a,b);}
   // Conservative AABB: batches touching the near plane retain the current CPU
   // clipper. The common fully visible case never transforms CPU vertices.
   if(zhi<near_clip)continue;const double margin=std::max(1e-4,std::abs(near_clip)*1e-5);
   if(zlo>near_clip+margin){auto instance=std::make_shared<mw34::vkscene::ModelInstance>();instance->geometry=batch.geometry;for(unsigned i=0;i<12;++i){instance->camera[i]=float(control_to_camera[i]);if(!std::isfinite(instance->camera[i]))throw std::runtime_error("Replacement GPU camera matrix is not representable");}
    instance->projection={float(near_scale),float(scale_x),float(scale_y),float(center_x),float(center_y),float(near_clip)};for(float p:instance->projection)if(!std::isfinite(p))throw std::runtime_error("Replacement GPU projection is not representable");instance->color=batch.color;draw.model=std::move(instance);
    device->commands.push_back(std::move(draw));triangles+=unsigned(batch.vertices.size()/3);++gpu_batches;continue;}++cpu_near_batches;
  }draw.vertices.reserve(batch.vertices.size()*sizeof(TlVertex));
  for(size_t at=0;at<batch.vertices.size();at+=3){std::array<CameraVertex,3>polygon{};for(unsigned i=0;i<3;++i){const auto&v=batch.vertices[at+i];auto&m=control_to_camera;double nx=m[0]*v.nx+m[1]*v.ny+m[2]*v.nz,ny=m[4]*v.nx+m[5]*v.ny+m[6]*v.nz,nz=m[8]*v.nx+m[9]*v.ny+m[10]*v.nz;double length=std::sqrt(nx*nx+ny*ny+nz*nz);double shade=.35+.65*std::max(0.,(.3*nx+.6*ny-.74*nz)/length);polygon[i]={m[0]*v.x+m[1]*v.y+m[2]*v.z+m[3],m[4]*v.x+m[5]*v.y+m[6]*v.z+m[7],m[8]*v.x+m[9]*v.y+m[10]*v.z+m[11],v.u,v.v,shade};}
   std::array<CameraVertex,4>clipped{};size_t clipped_count=0;for(size_t i=0;i<polygon.size();++i){const auto&a=polygon[i];const auto&b=polygon[(i+1)%polygon.size()];bool in_a=a.z>=near_clip,in_b=b.z>=near_clip;if(in_a)clipped[clipped_count++]=a;if(in_a!=in_b){double t=(near_clip-a.z)/(b.z-a.z);clipped[clipped_count++]={a.x+t*(b.x-a.x),a.y+t*(b.y-a.y),near_clip,a.u+t*(b.u-a.u),a.v+t*(b.v-a.v),a.shade+t*(b.shade-a.shade)};}}
   auto add=[&](const CameraVertex&v){double rhw=near_scale/v.z;unsigned color=0xff000000U;for(unsigned shift:{0U,8U,16U})color|=unsigned(std::clamp(double((batch.color>>shift)&255)*v.shade,0.,255.))<<shift;TlVertex vertex{float(v.x*scale_x*rhw+center_x),float(v.y*scale_y*rhw+center_y),float(rhw),float(rhw),color,0xff000000U,float(v.u),float(v.v)};if(!std::isfinite(vertex.x)||!std::isfinite(vertex.y)||!std::isfinite(vertex.z))throw std::runtime_error("Bushwacker test: nonfinite projected vertex");const auto*p=reinterpret_cast<const unsigned char*>(&vertex);draw.vertices.insert(draw.vertices.end(),p,p+sizeof vertex);};
   for(size_t i=1;i+1<clipped_count;++i){add(clipped[0]);add(clipped[i]);add(clipped[i+1]);++triangles;}
  }
  if(!draw.vertices.empty())device->commands.push_back(std::move(draw));
 }
 o.emitted.insert({o.scope.root,o.scope.owner});if(o.last_frame!=host.frames){o.last_frame=host.frames;++o.emitted_frames;}if(o.emitted_frames<4||host.frames%100==0)o.log<<"{\"event\":\"replacement_queued\",\"frame\":"<<host.frames<<",\"node\":"<<o.scope.node<<",\"model\":\""<<override_models[o.scope.model].id<<"\",\"root\":"<<o.scope.root<<",\"owner\":\""<<o.scope.owner<<"\",\"triangles\":"<<triangles<<",\"gpu_batches\":"<<gpu_batches<<",\"cpu_near_batches\":"<<cpu_near_batches<<"}\n";
}
