// Authored contracts and real Vulkan receiver tests. No original game media.
#define NOMINMAX
#include "vk_scene.hpp"
#include <iostream>
#include <sstream>
using namespace mw34::vkscene;
using namespace mw34::effects;
void require(bool value,const char*message){if(!value)throw std::runtime_error(message);}
template<class F>void rejects(F fn){bool rejected=false;try{fn();}catch(const std::runtime_error&){rejected=true;}require(rejected,"Malformed effect contract accepted");}
void contracts(){
 Clock clock;require(clock.update(100,false)==0,"Clock initializes without invented elapsed time");
 require(clock.update(100.25,false)==.25,"Live clock advances");
 require(clock.update(110,true)==.25&&clock.update(120,true)==.25,"Photo pause holds flash lifetime");
 require(clock.update(120.25,false)==.5,"Resume excludes paused wall time");
 require(clock.update(1,false)==0,"Rewound source clock resets elapsed time");
 const std::array<float,6>projection{1,40,40,32,32,.1f};
 const std::array<float,12>camera{1,0,0,10,0,1,0,20,0,0,1,30};
 require(reconstruct(52,12,.5f,projection,camera)==Point{11,19,32},"Effect reconstruction must use reciprocal TL depth and camera translation");
 rejects([&]{reconstruct(32,32,0,projection,camera);});
 require(closest({3,5,0},{0,0,0},{10,0,0})==Point{3,0,0},"Capsule closest point");
 Cache c;Emitter e{2,10,2,.1f,{1,.2f,0}};
 c.observe(e,{{0,0,0}},1);c.observe(e,{{.1f,0,0}},1.01);
 require(c.size()==1,"Repeated flash observations deduplicate");
 require(c.uniform(1.01,{0,0,0},16,1).params[0]==1,"Actual observed flash admitted");
 require(c.uniform(1.06,{0,0,0},16,1).lights[0].color[3]<1,"Flash fades after last observation");
 require(c.uniform(1.2,{0,0,0},16,1).params[0]==0,"Expired light removed");
 for(unsigned i=0;i<40;++i)c.observe(e,{{float(i*3),0,0}},2);
 auto budget=c.uniform(2,{100,0,0},4,1);require(budget.params[0]==4,"Bounded light count");
 require(budget.lights[0].start[0]>=99&&budget.lights[0].start[0]<=102,"Closest influential source ranked first");
 c.expire(1);require(c.size()==0,"Clock rewind discards stale lights");
 Emitter beam{1,10,1,.1f,{0,1,0}};c.observe(beam,{{10,0,0},{0,0,0}},3);
 auto capsule=c.uniform(3,{5,0,0},16,1);require(capsule.lights[0].start[0]==0&&capsule.lights[0].end[0]==10,"Beam preserves observed endpoints");
 std::string bytes("MWFX1\0\0\0",8);
 auto append=[&](const auto&v){bytes.append(reinterpret_cast<const char*>(&v),sizeof(v));};
 unsigned count=1,w=8,h=8,format=1,kind=2;std::uint64_t hash=123;
 append(count);append(w);append(h);append(format);append(kind);append(hash);
 append(e.radius);append(e.intensity);append(e.lifetime);for(float color:e.color)append(color);
 std::istringstream good(bytes);require(read_catalog(good).size()==1,"Valid exact material catalog");
 rejects([&]{std::istringstream f(bytes.substr(0,bytes.size()-1));read_catalog(f);});
 rejects([&]{std::istringstream f(bytes+"x");read_catalog(f);});
 auto bad=bytes;float nan=std::numeric_limits<float>::quiet_NaN();std::memcpy(bad.data()+36,&nan,4);
 rejects([&]{std::istringstream f(bad);read_catalog(f);});
}
struct Tl{float x,y,z,rhw;unsigned color,spec;float u,v;};
Scene receiver(){
 Scene s{};s.width=s.height=64;s.has_depth=true;s.color.assign(4096,0);s.depth.assign(4096,0);
 auto g=std::make_shared<ModelGeometry>();g->key=g->hash=1;
 g->vertices={{-1,-1,2,0,0,1,0,0},{1,-1,2,0,0,1,1,0},{1,1,2,0,0,1,1,1},
 {-1,-1,2,0,0,1,0,0},{1,1,2,0,0,1,1,1},{-1,1,2,0,0,1,0,1}};
 auto model=std::make_shared<ModelInstance>();model->geometry=g;model->color=0xffffffff;
 model->camera={1,0,0,0,0,1,0,0,0,0,1,0};model->projection={1,40,40,32,32,.1f};
 model->sun_normal=model->sun_world=model->camera;model->sun_eligible=true;
 Draw d{};d.count=6;d.texture=-1;d.model=model;d.scissor={{0,0},{64,64}};d.key.cull=1;d.key.zfunc=4;
 d.push.target[0]=d.push.target[1]=64;d.push.mode[0]=2|4;d.push.mode[1]=0x00000204;d.push.mode[2]=2;
 for(unsigned i=0;i<6;++i){Tl v{9000,9000,.5f,.5f,0xffffffff,0xff000000,0,0};auto*p=reinterpret_cast<const unsigned char*>(&v);s.vertices.insert(s.vertices.end(),p,p+sizeof(v));}
 s.draws.push_back(d);s.order.push_back({false,0});return s;
}
int main(){try{
 contracts();_putenv_s("MW34_GPU_MODELS","1");_putenv_s("MW34_SUN","1");_putenv_s("MW34_SUN_STRENGTH","0");_putenv_s("MW34_SUN_AMBIENT","0.05");_putenv_s("MW34_SKY_AUTO","0");
 _putenv_s("MW34_REMASTER_WIDTH","");_putenv_s("MW34_REMASTER_HEIGHT","");_putenv_s("MW34_REMASTER_AA","");_putenv_s("MW34_REMASTER_AF","");
 Renderer renderer;
 auto render=[&](Point location,bool hud=false,bool normal=false,bool beam=false){
  auto s=receiver();s.hud=hud;
  if(normal){TextureRef texture{};texture.key=2;texture.hash=2;texture.width=texture.height=1;texture.format=TexFormat::rgba8888;texture.pixels32={0xff8080ff};s.textures.push_back(texture);s.draws[0].normal_texture=0;}
  s.effect_lights.params[0]=1;auto&l=s.effect_lights.lights[0];l.start={location[0],location[1],location[2],5};l.end=l.start;l.color={1,0,0,2};
  if(beam){l.start[0]=-8;l.end[0]=8;l.end[3]=1;}
  renderer.render(s);return s.color[32*64+32];
 };
 auto dark=render({0,0,100}),red=render({0,0,4}),back=render({0,0,0});
 require((red>>11)>(dark>>11)+8,"Actual Vulkan local light must brighten receiver red channel");
 require((red&31)==(dark&31),"Red local light must not brighten blue channel");
 require(back==dark,"Back-facing local light rejected by surface normal");
 require((render({0,0,4},false,false,true)>>11)>(dark>>11)+8,"Capsule illuminates beam midpoint beyond endpoint radii");
 require(render({0,0,4},true)==render({0,0,100},true),"HUD excluded from local illumination");
 require(render({0,0,4},false,true)!=red,"Normal-map relief changes local-light response");
 require(render({0,0,100})==dark,"Light list replacement leaves no stale light");
 std::cout<<"Effect lighting contracts and actual Vulkan point-light, radius, normal-map, HUD and stale-list checks passed on "<<renderer.device_name<<"\n";
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 1;}}
