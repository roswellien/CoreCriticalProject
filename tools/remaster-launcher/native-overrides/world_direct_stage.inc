// Direct binding at the original mesh frame's current-polygon local. The
// initial decoder remains as the checked source-array reader on cache misses.
std::uint64_t world_mesh_hits{},world_mesh_misses{},world_scope_ticks{},world_binding_ticks{};
#include "world_geometry_stage.inc"
mw34::world::SnapshotCache<WorldScope> world_meshes{512,16*1024*1024};
struct WorldTicks {
 std::uint64_t& total;std::uint64_t start;
 explicit WorldTicks(std::uint64_t& value):total(value),start(mw34::GeometryProfile::now()){}
 ~WorldTicks(){total+=mw34::GeometryProfile::now()-start;}
};
std::shared_ptr<WorldScope> world_begin(unsigned node,unsigned frame_base){
 if(!world_enabled()||frontend_on()||!node||!readable(node,0x64))return {};
 const auto name=pose_name(node,36);if(name!="ter"&&name!="wall"&&name!="healthy")return {};
 for(unsigned parent=node,depth_=0;parent&&depth_<32;++depth_){if(pose_name(parent,36)=="hip")return {};parent=override_parent(parent);}
 if(!mw34::vkscene::Renderer::gpu_models())throw std::runtime_error("World direct binding requires GPU model resources");
 WorldTicks timer(world_scope_ticks);
 const unsigned mesh=load(node+0x3c);if(!mesh||!readable(mesh,0x48))throw std::runtime_error("World direct mesh header unavailable");
 if(load(mesh)!=0||load(mesh+0x1c)||load(mesh+0x20))return {};
 const unsigned count=load(mesh+0x10),vertices=load(mesh+0x14),normals=load(mesh+0x18),polygons=load(mesh+0x34);
 if(!count||count>4096||!vertices||vertices>65535||normals>65535)throw std::runtime_error("World direct mesh counts outside contract");
 // Exact fresh byte snapshots, rather than pointer identity, guard mutation and
 // allocator reuse. Dynamic RGB/material state still travels through TL data.
 std::vector<unsigned char> bytes;
 auto span=[&](unsigned address,unsigned length){if(!length)return;if(bytes.size()+length>16*1024*1024||!readable(address,length))throw std::runtime_error("World direct snapshot outside contract");const auto at=bytes.size();bytes.resize(at+length);get_bytes(address,bytes.data()+at,length);};
 span(mesh,0x48);span(load(mesh+0x38),vertices*12);span(load(mesh+0x3c),normals*12);span(polygons,count*36);
 for(unsigned p=0;p<count;++p){const unsigned poly=polygons+p*36,flags=load(poly),n=flags&255;if(n<3||n>128)throw std::runtime_error("World direct corner count outside contract");span(load(poly+8),n*4);if(flags&0x200)span(load(poly+12),n*4);if(load(poly+16))span(load(poly+16),n*8);}
 auto found=world_meshes.find(mesh,bytes);
 if(!found){
  auto decoded=world_decode_begin(node);if(!decoded)throw std::runtime_error("World direct source changed during snapshot");
  decoded->polygon_base=polygons;decoded->polygon_lookup=std::make_shared<std::vector<int>>(count,-1);
  for(size_t i=0;i<decoded->polygons->size();++i){const auto address=(*decoded->polygons)[i].source;if(address<polygons||(address-polygons)%36||(address-polygons)/36>=count)throw std::runtime_error("World decoded polygon ownership mismatch");(*decoded->polygon_lookup)[(address-polygons)/36]=int(i);}
  world_meshes.put(mesh,std::move(bytes),decoded);found=std::move(decoded);++world_mesh_misses;
 }else ++world_mesh_hits;
 auto result=std::make_shared<WorldScope>(*found);result->node=node;result->name=name;result->frame_base=frame_base;return result;
}
void world_capture(D3DCmd&draw){
 if(!world_scope||override_suppress_draw()||draw.flags!=D3DPT_TRIANGLEFAN||!draw.indices.empty()||draw.hud_role!=WideWorld||frontend_on())return;
 if(!draw.state_snapshot||draw.state_snapshot->size()<256)throw std::runtime_error("World direct draw state unavailable");
 if((*draw.state_snapshot)[D3DRENDERSTATE_ALPHABLENDENABLE]||(*draw.state_snapshot)[D3DRENDERSTATE_ALPHATESTENABLE])return;
 WorldTicks timer(world_binding_ticks);
 const auto&scope=*world_scope;const unsigned count=unsigned(draw.vertices.size()/32);
 const unsigned frame=scope.frame_base;
 if(frame<0x120||!readable(frame-0x120,0x124)||load(frame-0x38)!=scope.mesh)throw std::runtime_error("World direct original frame ownership mismatch");
 const unsigned address=load(frame-0x34);
 const auto slot=mw34::world::polygon_slot(scope.polygon_base,scope.polygon_lookup->size(),address);
 if(!slot){++world_misses;return;}
 const int index=(*scope.polygon_lookup)[*slot];
 if(index<0){++world_misses;return;}const auto&polygon=(*scope.polygons)[size_t(index)];
 if(polygon.source!=address)throw std::runtime_error("World direct polygon identity mismatch");
 if(count<3||polygon.corners.size()!=count){++world_misses;return;}
 mw34::vkscene::HostFpEnvironment fp;
 const auto matrix=override_matrix(load(load(0x5eda90)));
 const double near_scale=world_float(0x73fb80),sx=world_float(0x73fc30),sy=world_float(0x73fb98),cx=world_float(0x73fb88),cy=world_float(0x73fb8c),near_clip=world_float(0x740304);
 if(near_scale<=0||near_clip<=0||sx==0||sy==0)throw std::runtime_error("World direct projection outside contract");
 struct Tl {float x,y,z,rhw;unsigned color,spec;float u,v;};static_assert(sizeof(Tl)==32);
 std::vector<mw34::vkscene::ModelVertex> matched;matched.reserve(count);
 // The original producer reverses polygon corners before submission. No search
 // by projected position is used, so coincident normals keep their own corner.
 // Retain a linear projection audit until all downstream clipping is owned.
 for(unsigned j=0;j<count;++j){const auto&v=polygon.corners[count-1-j].vertex;Tl tl;std::memcpy(&tl,draw.vertices.data()+j*32,32);
  const double z=matrix[8]*v.x+matrix[9]*v.y+matrix[10]*v.z+matrix[11];if(z<=near_clip){++world_misses;return;}
  const double r=near_scale/z,x=(matrix[0]*v.x+matrix[1]*v.y+matrix[2]*v.z+matrix[3])*sx*r+cx,y=(matrix[4]*v.x+matrix[5]*v.y+matrix[6]*v.z+matrix[7])*sy*r+cy;
  if(!std::isfinite(tl.x)||!std::isfinite(tl.y)||!std::isfinite(tl.z)||!std::isfinite(tl.rhw)||!std::isfinite(tl.u)||!std::isfinite(tl.v)||std::abs(x-tl.x)>.02||std::abs(y-tl.y)>.02||std::abs(r-tl.rhw)>std::max(1e-7,std::abs(r)*1e-5)||std::abs(r-tl.z)>std::max(1e-7,std::abs(r)*1e-5)||std::abs(v.u-tl.u)>1e-5||std::abs(v.v-tl.v)>1e-5){++world_misses;return;}
  matched.push_back(v);
 }
 auto geometry=std::make_shared<mw34::vkscene::ModelGeometry>();for(unsigned i=1;i+1<count;++i){geometry->vertices.push_back(matched[i]);geometry->vertices.push_back(matched[i+1]);geometry->vertices.push_back(matched[0]);}
 geometry->hash=0xcbf29ce484222325ULL;const auto*data=reinterpret_cast<const unsigned char*>(geometry->vertices.data());for(size_t i=0;i<geometry->vertices.size()*32;++i){geometry->hash^=data[i];geometry->hash*=0x100000001b3ULL;}
 geometry->key=0x5700000000000000ULL|(geometry->hash&0x00ffffffffffffffULL);
 auto found=world_geometry.find(geometry->hash);if(found==world_geometry.end()){
  if(world_geometry.size()>=4096)throw std::runtime_error("World direct geometry capacity exceeded");found=world_geometry.emplace(geometry->hash,geometry).first;
  world_log<<"{\"event\":\"geometry\",\"frame\":"<<host.frames<<",\"name\":\""<<scope.name<<"\",\"hash\":"<<geometry->hash<<",\"vertices\":"<<geometry->vertices.size()<<",\"material\":"<<polygon.material<<",\"texture\":"<<draw.texture<<"}\n";
 }else if(found->second->vertices.size()!=geometry->vertices.size()||std::memcmp(found->second->vertices.data(),geometry->vertices.data(),geometry->vertices.size()*32))throw std::runtime_error("World direct geometry content collision");
 auto instance=std::make_shared<mw34::vkscene::ModelInstance>();instance->geometry=found->second;instance->world=true;for(unsigned i=0;i<12;++i)instance->camera[i]=float(matrix[i]);
 instance->projection={float(near_scale),float(sx),float(sy),float(cx),float(cy),float(near_clip)};draw.model=std::move(instance);++world_draws;
}
