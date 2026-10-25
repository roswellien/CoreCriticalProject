// Authored all-20 campaign Vulkan regression scenes; not gameplay captures.
#define NOMINMAX
#include "vk_scene.hpp"
#include <fstream>
#include <iostream>
using namespace mw34::vkscene;
struct Vertex { float x,y,z,rhw; unsigned color,spec; float u,v; };
static Scene scene(unsigned pattern,unsigned role,bool hud) {
    Scene s{};s.width=s.height=128;s.has_depth=true;s.hud=hud;
    s.color.assign(128*128,0);s.depth.assign(128*128,0);
    TextureRef tex{};tex.key=0xc300+pattern;tex.hash=pattern+1;
    tex.width=tex.height=32;tex.format=TexFormat::rgba8888;
    for(unsigned y=0;y<32;++y)for(unsigned x=0;x<32;++x)
        tex.pixels32.push_back(pattern?0xff20c0f0u:(((x/4+y/4)%2)?0xff303038u:0xff080810u));
    s.textures.push_back(tex);
    Draw d{};d.count=6;d.texture=0;d.detail_role=role;
    d.scissor={{0,0},{128,128}};d.key.cull=1;d.key.zfunc=4;
    d.push.target[0]=d.push.target[1]=128;d.push.target[2]=.5f;
    d.push.mode[0]=2|4;d.push.mode[1]=0x202;d.push.mode[2]=2;
    auto view=std::make_shared<mw34::sun::Tl>();
    view->projection={1,64,-64,64,64,.1f};
    view->camera_world={1,0,0,0,0,1,0,0,0,0,1,0};d.sky_view=view;
    for(auto p:std::array<std::array<float,2>,6>{{{0,0},{128,0},{128,128},{0,0},{128,128},{0,128}}}){
        Vertex v{p[0],p[1],.00001f,1,0xffffffff,0xff000000,p[0]/128,p[1]/128};
        auto bytes=reinterpret_cast<unsigned char*>(&v);s.vertices.insert(s.vertices.end(),bytes,bytes+sizeof v);
    }
    s.draws.push_back(d);s.order.push_back({false,0});return s;
}
int main(int argc,char**argv){try{
    if(argc!=2)throw std::runtime_error("Output prefix required");
    _putenv_s("MW34_GPU_MODELS","1");
    _putenv_s("MW34_SUN","1");_putenv_s("MW34_CAMPAIGN_LIGHTING","1");
    _putenv_s("MW34_MANUAL_LIGHTING","0");_putenv_s("MW34_WEATHER","1");
    _putenv_s("MW34_CLOUD_DETAIL","1");_putenv_s("MW34_EFFECT_LIGHTS","0");
    _putenv_s("MW34_REMASTER_WIDTH","");_putenv_s("MW34_REMASTER_HEIGHT","");
    _putenv_s("MW34_REMASTER_AA","");_putenv_s("MW34_REMASTER_AF","");
    Renderer renderer;
    for(unsigned op=1;op<=4;++op)for(unsigned mission=1;mission<=(op<3?4:6);++mission){
        auto& manager=mw34::campaign::CampaignManager::instance();
        const auto region=op==4&&mission>3?"c4b":"c"+std::to_string(op);
        manager.observe_file("D:/authored/zbd/"+region+"/readerm"+std::to_string(mission)+".zbd");
        manager.frontend();manager.enter_world();
        for(unsigned control=0;control<4;++control)for(unsigned pattern=0;pattern<2;++pattern){
            auto s=scene(pattern,control==1?0:3,control==2);
            if(control==3)s.draws[0].texture=-1;
            renderer.render(s);
            if((control==0||control==3)&&s.draws[0].sky!=(control==3?2:1))throw std::runtime_error("Sky not routed through actual dome path");
            if((control==1||control==2)&&s.draws[0].sky)throw std::runtime_error("Terrain/HUD misclassified as sky");
            std::string name=std::string(argv[1])+"-c"+std::to_string(op)+"m"+std::to_string(mission)+"-"+std::to_string(control)+"-"+std::to_string(pattern)+".bin";
            std::ofstream out(name,std::ios::binary);out.write(reinterpret_cast<const char*>(s.color.data()),s.color.size()*2);
            if(!out)throw std::runtime_error("Output failed");
        }
    }
    std::cout<<"160 actual Vulkan sky/horizon/terrain/HUD regression scenes rendered\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
