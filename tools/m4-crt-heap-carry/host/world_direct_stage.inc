// Direct binding at the original mesh frame's current-polygon local. The
// initial decoder remains as the checked source-array reader on cache misses.
#include "world_fast_binding.hpp"
std::uint64_t world_fast_corners{},world_audited_corners{},world_geometry_builds{};
static bool world_fast_enabled(){static const bool value=[]{const char*p=std::getenv("MW34_WORLD_FAST_BINDING");if(p&&std::strcmp(p,"0")&&std::strcmp(p,"1"))throw std::runtime_error("MW34_WORLD_FAST_BINDING must be 0 or 1");return p&&*p=='1';}();return value;}
std::uint64_t world_mesh_hits{},world_mesh_misses{},world_scope_ticks{},world_binding_ticks{};
#include "world_geometry_stage.inc"
std::shared_ptr<const mw34::vkscene::ModelGeometry> world_resident(const WorldPolygon& polygon,const std::string& name){const unsigned count=unsigned(polygon.corners.size());
 auto geometry=std::make_shared<mw34::vkscene::ModelGeometry>();for(unsigned i=1;i+1<count;++i){geometry->vertices.push_back(polygon.corners[count-1-i].vertex);geometry->vertices.push_back(polygon.corners[count-2-i].vertex);geometry->vertices.push_back(polygon.corners[count-1].vertex);}
 geometry->hash=0xcbf29ce484222325ULL;const auto*data=reinterpret_cast<const unsigned char*>(geometry->vertices.data());for(size_t i=0;i<geometry->vertices.size()*32;++i){geometry->hash^=data[i];geometry->hash*=0x100000001b3ULL;}
 geometry->key=0x5700000000000000ULL|(geometry->hash&0x00ffffffffffffffULL);
 auto found=world_geometry.find(geometry->hash);if(found==world_geometry.end()){
  if(world_geometry.size()>=65536)throw std::runtime_error("World direct geometry capacity exceeded");found=world_geometry.emplace(geometry->hash,geometry).first;
  world_log<<"{\"event\":\"geometry\",\"frame\":"<<host.frames<<",\"name\":\""<<name<<"\",\"hash\":"<<geometry->hash<<",\"vertices\":"<<geometry->vertices.size()<<",\"material\":"<<polygon.material<<",\"texture\":"<<0<<"}\n";
 }else if(found->second->vertices.size()!=geometry->vertices.size()||std::memcmp(found->second->vertices.data(),geometry->vertices.data(),geometry->vertices.size()*32))throw std::runtime_error("World direct geometry content collision");
 ++world_geometry_builds;return found->second;
}
mw34::world::SnapshotCache<WorldScope> world_meshes{2048,64*1024*1024};
struct WorldTicks {
 std::uint64_t& total;std::uint64_t start;
 explicit WorldTicks(std::uint64_t& value):total(value),start(mw34::GeometryProfile::now()){}
 ~WorldTicks(){total+=mw34::GeometryProfile::now()-start;}
};
std::shared_ptr<WorldScope> world_begin(unsigned node,unsigned frame_base){
 if(!world_enabled()||!world_cell_depth||frontend_on()||!node||!readable(node,0x64))return {};
 const auto name=pose_name(node,36);if(!is_admitted_world_name(name))return {};
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
  for(auto& polygon:*decoded->polygons)polygon.resident=world_resident(polygon,name);
  decoded->polygon_base=polygons;decoded->polygon_lookup=std::make_shared<std::vector<int>>(count,-1);
  for(size_t i=0;i<decoded->polygons->size();++i){const auto address=(*decoded->polygons)[i].source;if(address<polygons||(address-polygons)%36||(address-polygons)/36>=count)throw std::runtime_error("World decoded polygon ownership mismatch");(*decoded->polygon_lookup)[(address-polygons)/36]=int(i);}
  world_meshes.put(mesh,std::move(bytes),decoded);found=std::move(decoded);++world_mesh_misses;
 }else ++world_mesh_hits;
 auto result=std::make_shared<WorldScope>(*found);result->node=node;result->name=name;result->frame_base=frame_base;return result;
}
bool world_edge_enabled(){static const bool on=[]{const char*p=std::getenv("MW34_WORLD_EDGE_ADMIT");return p&&*p=='1';}();return on;}
std::uint64_t world_edge_admits{},world_edge_rejects{};
bool world_edge_admit(D3DCmd& draw,const WorldPolygon& polygon,const OverrideMatrix& m,double near_scale,double sx,double sy,double cx,double cy,double near_clip){
 if(!world_edge_enabled()||!mw34::sun::settings().enabled)return false;
 struct Tl {float x,y,z,rhw;unsigned color,spec;float u,v;};
 const unsigned n=unsigned(polygon.corners.size()),k=unsigned(draw.vertices.size()/32);
 if(n<3||k<3||n>64)return false;
 const unsigned camera=load(0x7402f4);if(!camera||!readable(camera+0xb4,4))return false;
 const double far_limit=wide_float(camera+0xb4);if(!(far_limit>near_clip))return false;
 std::vector<std::array<double,3>> cam(n);
 for(unsigned j=0;j<n;++j){const auto&v=polygon.corners[n-1-j].vertex;
  cam[j]={m[0]*v.x+m[1]*v.y+m[2]*v.z+m[3],m[4]*v.x+m[5]*v.y+m[6]*v.z+m[7],m[8]*v.x+m[9]*v.y+m[10]*v.z+m[11]};
  if(!(cam[j][2]>near_clip*1.001)||!(cam[j][2]<far_limit*0.999)){++world_edge_rejects;return false;}}
 std::array<double,3> nrm{0,0,0},c0{0,0,0};
 for(unsigned j=0;j<n;++j){const auto&a=cam[j];const auto&b=cam[(j+1)%n];
  nrm[0]+=(a[1]-b[1])*(a[2]+b[2]);nrm[1]+=(a[2]-b[2])*(a[0]+b[0]);nrm[2]+=(a[0]-b[0])*(a[1]+b[1]);for(unsigned i=0;i<3;++i)c0[i]+=a[i]/n;}
 const double nl=std::sqrt(nrm[0]*nrm[0]+nrm[1]*nrm[1]+nrm[2]*nrm[2]);if(!(nl>1e-12))return false;
 std::vector<Tl> in(k);double sz=0,sf=0,szz=0,szf=0;unsigned cnt=0,ones=0,zeros=0;
 for(unsigned i=0;i<k;++i){std::memcpy(&in[i],draw.vertices.data()+i*32,32);const auto&t=in[i];
  if(!std::isfinite(t.x)||!std::isfinite(t.y)||!std::isfinite(t.rhw)||!(t.rhw>0)){++world_edge_rejects;return false;}
  const double p[3]={(t.x-cx)/(sx*t.rhw),(t.y-cy)/(sy*t.rhw),near_scale/t.rhw};
  const double d=((p[0]-c0[0])*nrm[0]+(p[1]-c0[1])*nrm[1]+(p[2]-c0[2])*nrm[2])/nl;
  if(!std::isfinite(d)||std::abs(d)>std::max(0.02,p[2]*2e-3)){++world_edge_rejects;return false;}
  const unsigned fa=t.spec>>24;if(fa>=255)++ones;else if(!fa)++zeros;else{const double f=fa/255.0;sz+=p[2];sf+=f;szz+=p[2]*p[2];szf+=p[2]*f;++cnt;}}
 // Vertex fog (specular alpha): linear in depth from the unclamped clipped vertices.
 double fa=1,fb=0;
 if(cnt>=2&&std::abs(cnt*szz-sz*sz)>1e-9){fb=(cnt*szf-sz*sf)/(cnt*szz-sz*sz);fa=(sf-fb*sz)/cnt;}
 else if(cnt)fa=sf/cnt;
 else if(ones&&!zeros)fa=1;else if(zeros&&!ones)fa=0;else{++world_edge_rejects;return false;}
 std::vector<unsigned char> out(size_t(n)*32);
 for(unsigned j=0;j<n;++j){const auto&v=polygon.corners[n-1-j].vertex;Tl t;const double r=near_scale/cam[j][2];
  t.x=float(cam[j][0]*sx*r+cx);t.y=float(cam[j][1]*sy*r+cy);t.z=t.rhw=float(r);t.color=in[0].color;
  const double f=std::min(1.0,std::max(0.0,fa+fb*cam[j][2]));t.spec=(in[0].spec&0xffffffu)|(unsigned(std::lround(f*255))<<24);
  t.u=v.u;t.v=v.v;std::memcpy(out.data()+size_t(j)*32,&t,32);}
 draw.vertices=std::move(out);++world_edge_admits;return true;
}
void world_capture(D3DCmd&draw){
 if(!world_scope||!world_cell_depth||override_suppress_draw()||draw.flags!=D3DPT_TRIANGLEFAN||!draw.indices.empty()||draw.hud_role!=WideWorld||frontend_on())return;
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
 if(count<3){++world_misses;return;}bool exact=polygon.corners.size()==count;
 mw34::vkscene::HostFpEnvironment fp;
 const auto matrix=override_matrix(load(load(0x5eda90)));
 const double near_scale=world_float(0x73fb80),sx=world_float(0x73fc30),sy=world_float(0x73fb98),cx=world_float(0x73fb88),cy=world_float(0x73fb8c),near_clip=world_float(0x740304);
 if(near_scale<=0||near_clip<=0||sx==0||sy==0)throw std::runtime_error("World direct projection outside contract");
 struct Tl {float x,y,z,rhw;unsigned color,spec;float u,v;};static_assert(sizeof(Tl)==32);
 const bool fast=world_fast_enabled()&&load(frame-0x44)==polygon.material&&readable(polygon.material,4)&&(load(polygon.material)&0x100)&&mw34::world::unchanged_polygon(load(frame-0x74),polygon.flags,load(address+4),load(0x7489a8),load(frame-0x54));
 // The original producer reverses polygon corners before submission. No search
 // by projected position is used, so coincident normals keep their own corner.
 // Retain a linear projection audit until all downstream clipping is owned.
 if(exact)for(unsigned j=0;j<count;++j){const auto&v=polygon.corners[count-1-j].vertex;Tl tl;std::memcpy(&tl,draw.vertices.data()+j*32,32);
  if(!std::isfinite(tl.u)||!std::isfinite(tl.v)||std::abs(v.u-tl.u)>1e-5||std::abs(v.v-tl.v)>1e-5){exact=false;break;}
  if(fast){++world_fast_corners;continue;}++world_audited_corners;
  const double z=matrix[8]*v.x+matrix[9]*v.y+matrix[10]*v.z+matrix[11];if(z<=near_clip){exact=false;break;}
  const double r=near_scale/z,x=(matrix[0]*v.x+matrix[1]*v.y+matrix[2]*v.z+matrix[3])*sx*r+cx,y=(matrix[4]*v.x+matrix[5]*v.y+matrix[6]*v.z+matrix[7])*sy*r+cy;
  if(!std::isfinite(tl.x)||!std::isfinite(tl.y)||!std::isfinite(tl.z)||!std::isfinite(tl.rhw)||!std::isfinite(tl.u)||!std::isfinite(tl.v)||std::abs(x-tl.x)>.02||std::abs(y-tl.y)>.02||std::abs(r-tl.rhw)>std::max(1e-7,std::abs(r)*1e-5)||std::abs(r-tl.z)>std::max(1e-7,std::abs(r)*1e-5)||std::abs(v.u-tl.u)>1e-5||std::abs(v.v-tl.v)>1e-5){exact=false;break;}

 }
 if(!exact&&!world_edge_admit(draw,polygon,matrix,near_scale,sx,sy,cx,cy,near_clip)){++world_misses;return;}
 auto instance=std::make_shared<mw34::vkscene::ModelInstance>();instance->geometry=polygon.resident;instance->world=true;for(unsigned i=0;i<12;++i)instance->camera[i]=float(matrix[i]);
 instance->projection={float(near_scale),float(sx),float(sy),float(cx),float(cy),float(near_clip)};sun_capture_world(*instance,scope.node);draw.fixture_node=scope.node;draw.fixture_polygon=polygon.source;draw.model=std::move(instance);++world_draws;
}
