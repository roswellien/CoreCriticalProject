// Actual Vulkan rendering: original per-part fog blending survives world haze.
#include "vk_scene.hpp"
#include <iostream>

int main(){try{
    _putenv_s("MW34_GPU_MODELS","1");
    _putenv_s("MW34_SUN","1");_putenv_s("MW34_SKY_AUTO","0");
    _putenv_s("MW34_HAZE_COLOR","0,0.5,0.5");
    _putenv_s("MW34_REMASTER_WIDTH","1280");_putenv_s("MW34_REMASTER_HEIGHT","720");
    _putenv_s("MW34_REMASTER_AA","1");
    using namespace mw34::vkscene;
    auto renderer=std::make_unique<Renderer>();
    Scene s{};s.width=640;s.height=480;s.has_depth=false;
    s.color.assign(640*480,0);s.depth.assign(640*480,0);
    struct Vertex{float x,y,z,rhw;unsigned color,spec;float u,v;};
    auto add=[&](float x,float y,unsigned fog_factor,bool schematic){
        Draw d{};d.first=unsigned(s.vertices.size()/32);d.count=3;d.texture=-1;
        d.key={0,2,1,0,8,0,1};d.scissor={{0,0},{640,480}};
        d.push.target[0]=640;d.push.target[1]=480;d.push.target[2]=.5f;
        d.push.fog[0]=1;d.push.fog[3]=1;
        d.push.mode[0]=16;d.push.mode[1]=2;d.push.mode[2]=2;d.push.mode[3]=8;
#ifndef MW34_TEST_BASELINE
        d.condition_schematic=schematic;
#endif
        for(auto pos:{std::array<float,2>{x,y},std::array<float,2>{x+80,y},std::array<float,2>{x,y+80}}){
            Vertex v{pos[0],pos[1],.07f,.07f,0xffffffff,fog_factor<<24,0,0};
            const auto* bytes=reinterpret_cast<const unsigned char*>(&v);
            s.vertices.insert(s.vertices.end(),bytes,bytes+sizeof v);
        }
        s.order.push_back({false,unsigned(s.draws.size())});s.draws.push_back(d);
    };
    add(30,350,128,true);  // Injured target component: partial red.
    add(520,350,32,true);  // More damaged player component: stronger red.
    add(420,350,255,true); // Undamaged neighbouring component stays white.
    add(200,100,128,false); // World control still receives cyan haze.
    renderer->render(s,true,true);
    auto rgb=[&](unsigned x,unsigned y){unsigned p=s.color[size_t(y)*640+x];return std::array<unsigned,3>{((p>>11)&31)*255/31,((p>>5)&63)*255/63,(p&31)*255/31};};
    const auto target=rgb(40,360),player=rgb(530,360),healthy=rgb(430,360),world=rgb(210,110);
    auto check=[](bool pass,const char* why){if(!pass)throw std::runtime_error(why);};
    check(s.draws[0].push.fog[0]==1&&s.draws[0].push.fog[1]==0,"target diagnostic fog colour overwritten");
    check(target[0]>240&&target[1]>110&&target[1]<145&&target[2]<145,"target damage shading");
    check(player[0]>240&&player[1]<45&&player[2]<45,"player damage shading");
    check(player[1]<target[1],"component damage intensity progression");
    check(healthy[0]>240&&healthy[1]>240&&healthy[2]>240,"undamaged component changed");
    check(world[0]<150&&world[1]>175&&world[2]>175,"world haze no longer applied");
    std::cout<<"PASS: both damage displays retain independent red tint, undamaged parts stay white, world haze remains active.\n";
    return 0;
}catch(const std::exception& e){std::cerr<<"FAIL: "<<e.what()<<'\n';return 1;}}
