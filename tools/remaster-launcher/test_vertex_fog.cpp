// Authored Vulkan readback fixture. No game assets or translated game code.
#define NOMINMAX
#include "vk_scene.hpp"
#include <iostream>
using namespace mw34::vkscene;
struct Vertex {float x,y,z,rhw;unsigned diffuse,specular;float u,v;};
static_assert(sizeof(Vertex)==32);
int main(){try{
 _putenv_s("MW34_GPU_MODELS","1");
 for(const char* key:{"MW34_REMASTER_WIDTH","MW34_REMASTER_HEIGHT","MW34_REMASTER_AA","MW34_REMASTER_AF","MW34_RENDER_SCALE"})_putenv_s(key,"");
 Scene scene{};scene.width=scene.height=64;scene.has_depth=true;scene.color.assign(4096,0);scene.depth.assign(4096,0);
 for(unsigned column=0;column<4;++column){
  const unsigned alpha=column==0?0:column==1?128:255;
  const float x=float(column*16+2);
  for(auto point:std::array<std::array<float,2>,3>{{{x,2},{x+12,2},{x,14}}}){
   Vertex v{point[0],point[1],.5f,.5f,0xffff0000,alpha<<24,0,0};const auto* p=reinterpret_cast<const unsigned char*>(&v);scene.vertices.insert(scene.vertices.end(),p,p+sizeof(v));
  }
  Draw draw{};draw.first=column*3;draw.count=3;draw.texture=-1;draw.key.cull=1;draw.key.zfunc=4;draw.push.target[0]=draw.push.target[1]=64;draw.push.target[2]=.5f;
  draw.push.fog[2]=draw.push.fog[3]=1;draw.push.mode[0]=2|(column==3?0:16);draw.push.mode[1]=draw.push.mode[2]=2;draw.scissor={{0,0},{64,64}};
  scene.order.push_back({false,unsigned(scene.draws.size())});scene.draws.push_back(draw);
 }
#ifdef MW34_TEST_WORLD_FOG
 for(unsigned column=0;column<3;++column){
  const unsigned alpha=column==0?0:column==1?128:255;
  auto geometry=std::make_shared<ModelGeometry>();geometry->key=geometry->hash=0x5700000000000100ULL+column;
  const float x=float(column*16+2);
  for(auto point:std::array<std::array<float,2>,3>{{{x,22},{x+12,22},{x,34}}}){
   geometry->vertices.push_back({(point[0]-32)/10,(point[1]-32)/10,2,0,0,1,0,0});
   Vertex v{5000,5000,.5f,.5f,0xffff0000,alpha<<24,0,0};const auto*p=reinterpret_cast<const unsigned char*>(&v);scene.vertices.insert(scene.vertices.end(),p,p+sizeof(v));
  }
  auto instance=std::make_shared<ModelInstance>();instance->geometry=geometry;instance->world=true;instance->camera={1,0,0,0,0,1,0,0,0,0,1,0};instance->projection={1,20,20,32,32,.1f};
  auto draw=scene.draws[column];draw.first=12+column*3;draw.model=instance;scene.order.push_back({false,unsigned(scene.draws.size())});scene.draws.push_back(draw);
 }
#endif
 Renderer renderer;renderer.render(scene);
 const std::array<unsigned,4> expected{0x001f,0x800f,0xf800,0xf800};
 for(unsigned i=0;i<4;++i){const unsigned pixel=scene.color[4*64+i*16+4];if(pixel!=expected[i])throw std::runtime_error("Fog pixel "+std::to_string(i)+" expected="+std::to_string(expected[i])+" actual="+std::to_string(pixel));}
#ifdef MW34_TEST_WORLD_FOG
 for(unsigned i=0;i<3;++i){const unsigned pixel=scene.color[24*64+i*16+4];if(pixel!=expected[i])throw std::runtime_error("Raw world fog pixel "+std::to_string(i)+" expected="+std::to_string(expected[i])+" actual="+std::to_string(pixel));}
 if(renderer.world_gpu_draws!=3)throw std::runtime_error("Raw world fog draws not executed");
 std::cout<<"Raw world GPU fog fixture passed: full, partial and zero fog from original TL attributes\n";
#endif
 std::cout<<"Vertex fog fixture passed: full, partial, zero and disabled fog with specular lighting disabled on "<<renderer.device_name<<"\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
