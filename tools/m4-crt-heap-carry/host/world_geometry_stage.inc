// Experimental static original-mesh bridge. Original producers still execute;
// clipped/unmatched polygons explicitly keep the established TL draw path.
struct WorldCorner { mw34::vkscene::ModelVertex vertex{}; unsigned index{}; };
struct WorldPolygon { std::vector<WorldCorner> corners; unsigned material{},flags{},source{};std::shared_ptr<const mw34::vkscene::ModelGeometry> resident; };
struct WorldScope { unsigned node{},mesh{},frame_base{},polygon_base{};std::shared_ptr<const mw34::world::SourceBytes> source_bytes;std::string name;std::shared_ptr<std::vector<WorldPolygon>> polygons=std::make_shared<std::vector<WorldPolygon>>();std::shared_ptr<std::vector<int>> polygon_lookup; };
std::shared_ptr<WorldScope> world_scope;
std::map<std::uint64_t,std::shared_ptr<const mw34::vkscene::ModelGeometry>> world_geometry;
std::ofstream world_log;
std::uint64_t world_draws{},world_misses{};
unsigned world_cell_depth{};
static bool world_enabled(){static const bool on=[]{const char*p=std::getenv("MW34_GPU_WORLD");if(p&&std::strcmp(p,"0")&&std::strcmp(p,"1"))throw std::runtime_error("MW34_GPU_WORLD must be 0 or 1");return p&&*p=='1';}();return on;}
void world_open(){if(world_log.is_open())return;const char*p=std::getenv("MW34_WORLD_LOG");if(!p||!*p)throw std::runtime_error("Experimental world geometry requires MW34_WORLD_LOG");world_log.open(p);if(!world_log)throw std::runtime_error("World geometry log unavailable");}
float world_float(unsigned address){if(!readable(address,4))throw std::runtime_error("World geometry float outside memory contract");unsigned bits=load(address);float value;std::memcpy(&value,&bits,4);if(!std::isfinite(value))throw std::runtime_error("World geometry nonfinite float");return value;}
bool is_admitted_world_name(const std::string& name) {
 if(!world_cell_depth)return false;
 if(name=="ter"||name=="wall"||name=="healthy")return true;
 static const bool gpu_terrain=[] {const char* value=std::getenv("MW34_GPU_TERRAIN");return value&&*value=='1';}();
 if(gpu_terrain){
  if(name.rfind("bwg",0)==0)return true;
 }
 return false;
}
std::shared_ptr<WorldScope> world_decode_begin(unsigned node){
 if(!world_enabled()||!world_cell_depth||frontend_on()||!node||!readable(node,0x64))return {};
 if(!mw34::vkscene::Renderer::gpu_models())throw std::runtime_error("World geometry prototype requires GPU model resources");
 const auto name=pose_name(node,36);if(!is_admitted_world_name(name))return {};
 // The initial bounded scope is scenery/damage-state meshes, never mech parts.
 unsigned parent=node;for(unsigned i=0;parent&&i<32;++i){if(pose_name(parent,36)=="hip")return {};parent=override_parent(parent);}
 const unsigned mesh=load(node+0x3c);if(!mesh||!readable(mesh,0x48))throw std::runtime_error("World mesh header unavailable");
 world_open();
 // Morphing, billboards and animated-light meshes retain original drawing.
 if(load(mesh)!=0||load(mesh+0x1c)||load(mesh+0x20))return {};
 const unsigned count=load(mesh+0x10),vertices=load(mesh+0x14),normals=load(mesh+0x18);
 const unsigned polygons=load(mesh+0x34),xyz=load(mesh+0x38),normal=load(mesh+0x3c);
 if(!count||count>4096||!vertices||vertices>65535||normals>65535||!readable(polygons,count*36)||!readable(xyz,vertices*12)||(normals&&!readable(normal,normals*12)))throw std::runtime_error("World mesh arrays outside bounded contract");
 mw34::vkscene::HostFpEnvironment fp;
 auto result=std::make_shared<WorldScope>();result->node=node;result->mesh=mesh;result->name=name;
 for(unsigned p=0;p<count;++p){const unsigned poly=polygons+p*36,flags=load(poly),n=flags&255,indices=load(poly+8),ni=load(poly+12),uv=load(poly+16);
  if(n<3||n>128||!readable(indices,n*4)||(uv&&!readable(uv,n*8))||((flags&0x200)&&(!normals||!readable(ni,n*4))))throw std::runtime_error("World polygon arrays outside bounded contract");
  WorldPolygon polygon;polygon.source=poly;polygon.material=load(poly+28);polygon.flags=flags;
  for(unsigned j=0;j<n;++j){const unsigned index=load(indices+j*4);if(index>=vertices)throw std::runtime_error("World position index out of range");
   WorldCorner corner;corner.index=index;auto&v=corner.vertex;v.x=world_float(xyz+index*12);v.y=world_float(xyz+index*12+4);v.z=world_float(xyz+index*12+8);
   if(uv){v.u=world_float(uv+j*8);v.v=world_float(uv+j*8+4);}
   if(flags&0x200){const unsigned index_n=load(ni+j*4);if(index_n>=normals)throw std::runtime_error("World normal index out of range");v.nx=world_float(normal+index_n*12);v.ny=world_float(normal+index_n*12+4);v.nz=world_float(normal+index_n*12+8);}
   polygon.corners.push_back(corner);
  }
  if(!(flags&0x200)){const auto&a=polygon.corners[0].vertex;const auto&b=polygon.corners[1].vertex;const auto&c=polygon.corners[2].vertex;
   const double x=(b.y-a.y)*(c.z-a.z)-(b.z-a.z)*(c.y-a.y),y=(b.z-a.z)*(c.x-a.x)-(b.x-a.x)*(c.z-a.z),z=(b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x),length=std::sqrt(x*x+y*y+z*z);
   if(length<1e-12)continue;for(auto&corner:polygon.corners){corner.vertex.nx=float(x/length);corner.vertex.ny=float(y/length);corner.vertex.nz=float(z/length);}
  }
  result->polygons->push_back(std::move(polygon));
 }
 static std::set<std::pair<unsigned,unsigned>>seen;
 if(seen.insert({node,mesh}).second){world_log<<"{\"event\":\"mesh\",\"frame\":"<<host.frames<<",\"node\":"<<node<<",\"name\":\""<<name<<"\",\"mesh\":"<<mesh<<",\"polygons\":"<<count<<",\"vertices\":"<<vertices<<",\"normals\":"<<normals<<",\"cell_scope\":"<<world_cell_depth<<"}\n";world_log.flush();}
 return result;
}
void world_search_capture(D3DCmd&draw){
 if(!world_scope||!world_cell_depth||override_suppress_draw()||draw.flags!=D3DPT_TRIANGLEFAN||!draw.indices.empty()||draw.hud_role!=WideWorld||frontend_on())return;
 if(!draw.state_snapshot||draw.state_snapshot->size()<256)throw std::runtime_error("World draw state unavailable");
 if((*draw.state_snapshot)[D3DRENDERSTATE_ALPHABLENDENABLE]||(*draw.state_snapshot)[D3DRENDERSTATE_ALPHATESTENABLE])return;
 const unsigned count=unsigned(draw.vertices.size()/32);if(count<3||count>128)return;
 mw34::vkscene::HostFpEnvironment fp;
 const auto matrix=override_matrix(load(load(0x5eda90)));
 const double near_scale=world_float(0x73fb80),sx=world_float(0x73fc30),sy=world_float(0x73fb98),cx=world_float(0x73fb88),cy=world_float(0x73fb8c),near_clip=world_float(0x740304);
 if(near_scale<=0||near_clip<=0||sx==0||sy==0)throw std::runtime_error("World projection outside contract");
 struct Tl {float x,y,z,rhw;unsigned color,spec;float u,v;};static_assert(sizeof(Tl)==32);
 std::vector<mw34::vkscene::ModelVertex> matched;unsigned material{};
 for(const auto&polygon:*world_scope->polygons){if(polygon.corners.size()!=count)continue;std::vector<bool>used(count);std::vector<mw34::vkscene::ModelVertex>candidate;bool valid=true;
  for(unsigned j=0;j<count&&valid;++j){Tl tl;std::memcpy(&tl,draw.vertices.data()+j*32,32);bool found=false;
   for(unsigned k=0;k<count;++k)if(!used[k]){const auto&v=polygon.corners[k].vertex;
    const double z=matrix[8]*v.x+matrix[9]*v.y+matrix[10]*v.z+matrix[11];if(z<=near_clip)continue;
    const double r=near_scale/z,x=(matrix[0]*v.x+matrix[1]*v.y+matrix[2]*v.z+matrix[3])*sx*r+cx,y=(matrix[4]*v.x+matrix[5]*v.y+matrix[6]*v.z+matrix[7])*sy*r+cy;
    if(std::abs(x-tl.x)>.02||std::abs(y-tl.y)>.02||std::abs(r-tl.rhw)>std::max(1e-7,std::abs(r)*1e-5)||std::abs(r-tl.z)>std::max(1e-7,std::abs(r)*1e-5)||std::abs(v.u-tl.u)>1e-5||std::abs(v.v-tl.v)>1e-5)continue;
    used[k]=true;candidate.push_back(v);found=true;break;
   }
   if(!found)valid=false;
  }
  if(valid){if(!matched.empty()){++world_misses;return;}matched=std::move(candidate);material=polygon.material;}
 }
 if(matched.empty()){++world_misses;return;}
 auto geometry=std::make_shared<mw34::vkscene::ModelGeometry>();for(unsigned i=1;i+1<count;++i){geometry->vertices.push_back(matched[i]);geometry->vertices.push_back(matched[i+1]);geometry->vertices.push_back(matched[0]);}
 geometry->hash=0xcbf29ce484222325ULL;const auto*bytes=reinterpret_cast<const unsigned char*>(geometry->vertices.data());for(size_t i=0;i<geometry->vertices.size()*32;++i){geometry->hash^=bytes[i];geometry->hash*=0x100000001b3ULL;}
 geometry->key=0x5700000000000000ULL|(geometry->hash&0x00ffffffffffffffULL);
 auto it=world_geometry.find(geometry->hash);if(it==world_geometry.end()){
  if(world_geometry.size()>=65536)throw std::runtime_error("World prototype geometry cache capacity exceeded");it=world_geometry.emplace(geometry->hash,geometry).first;
  world_log<<"{\"event\":\"geometry\",\"frame\":"<<host.frames<<",\"name\":\""<<world_scope->name<<"\",\"hash\":"<<geometry->hash<<",\"vertices\":"<<geometry->vertices.size()<<",\"material\":"<<material<<",\"texture\":"<<draw.texture<<"}\n";
 }else if(it->second->vertices.size()!=geometry->vertices.size()||std::memcmp(it->second->vertices.data(),geometry->vertices.data(),geometry->vertices.size()*32))throw std::runtime_error("World geometry content hash collision");
 auto instance=std::make_shared<mw34::vkscene::ModelInstance>();instance->geometry=it->second;instance->world=true;for(unsigned i=0;i<12;++i)instance->camera[i]=float(matrix[i]);
 instance->projection={float(near_scale),float(sx),float(sy),float(cx),float(cy),float(near_clip)};draw.model=std::move(instance);++world_draws;
}
void world_present(){if(!world_enabled())return;world_open();world_log<<"{\"event\":\"present\",\"frame\":"<<host.frames<<",\"draws\":"<<world_draws<<",\"executed\":"<<(host.sren?host.sren->world_gpu_draws:0)<<",\"sun_world\":"<<(host.sren?host.sren->sun_world_draws:0)<<",\"sun_tl\":"<<(host.sren?host.sren->sun_tl_draws:0)<<",\"sun_models\":"<<(host.sren?host.sren->sun_model_draws:0)<<",\"effect_light_peak\":"<<(host.sren?host.sren->effect_light_peak:0)<<",\"fixture_light_peak\":"<<(host.sren?host.sren->fixture_light_peak:0)<<",\"effect_light_peak\":"<<(host.sren?host.sren->effect_light_peak:0)<<",\"fixture_light_peak\":"<<(host.sren?host.sren->fixture_light_peak:0)<<",\"sun_shadow_scenes\":"<<(host.sren?host.sren->sun_shadow_scenes:0)<<",\"sun_shadow_casters\":"<<(host.sren?host.sren->sun_shadow_casters:0)<<",\"sun_shadow_reused\":"<<(host.sren?host.sren->sun_shadow_reused:0)<<",\"sky_draws\":"<<(host.sren?host.sren->sky_draws:0)<<",\"sky_tinted\":"<<(host.sren?host.sren->sky_tinted:0)<<",\"sky_untinted\":"<<(host.sren?host.sren->sky_untinted:0)<<",\"haze_draws\":"<<(host.sren?host.sren->haze_draws:0)<<",\"horizon_draws\":"<<(host.sren?host.sren->horizon_draws:0)<<",\"haze_routed\":"<<(host.sren?host.sren->haze_routed:0)<<",\"sky_own_view\":"<<(host.sren?host.sren->sky_own_view:0)<<",\"edge_admits\":"<<world_edge_admits<<",\"edge_rejects\":"<<world_edge_rejects<<",\"unmatched\":"<<world_misses<<",\"fast_corners\":"<<world_fast_corners<<",\"audited_corners\":"<<world_audited_corners<<",\"geometry_builds\":"<<world_geometry_builds<<",\"mesh_hits\":"<<world_mesh_hits<<",\"mesh_misses\":"<<world_mesh_misses<<",\"scope_ticks\":"<<world_scope_ticks<<",\"binding_ticks\":"<<world_binding_ticks<<",\"cached\":"<<world_geometry.size()<<"}\n";world_log.flush();}
