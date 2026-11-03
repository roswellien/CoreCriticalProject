// Real Vulkan regression: guest ABI, scaled transfers, resident precision and clears.
#include "vk_scene.hpp"
#include <iostream>
#include <limits>

static void temporal_depth_checks(mw34::vkscene::Renderer &renderer) {
    using namespace mw34::vkscene;
    using namespace mw34::temporal;
    auto require=[](bool value,const char *message){if(!value)throw std::runtime_error(message);};
    require(enabled(),"Temporal depth fixture requires temporal inputs");
    renderer.complete_camera_history(1,7);
    unsigned frame=2;
    auto sample=[&](float z,float far_clip){
        Scene scene{};scene.width=640;scene.height=480;scene.has_depth=true;
        scene.color.assign(640*480,0);scene.depth.assign(640*480,0);
        scene.temporal_frame=frame;scene.temporal_target=7;
        Clear clear{};clear.flags=3;clear.rects={{{0,0},{640,480}}};
        scene.clears={clear};scene.order={{true,0},{false,0}};
        auto geometry=std::make_shared<ModelGeometry>();geometry->key=9000+frame;
        struct Vertex {float x,y,z,rhw;unsigned color,specular;float u,v;};
        for(auto xy:std::array<std::array<float,2>,6>{{{100,100},{300,100},{100,300},{300,100},{300,300},{100,300}}}){
            geometry->vertices.push_back({(xy[0]-320)*z/5,(xy[1]-240)*z/5,z,0,0,1,0,0});
            Vertex vertex{xy[0],xy[1],.05f/z,.05f/z,0xffffffff,0,0,0};
            const auto *bytes=reinterpret_cast<const unsigned char*>(&vertex);
            scene.vertices.insert(scene.vertices.end(),bytes,bytes+32);
        }
        auto model=std::make_shared<ModelInstance>();model->geometry=geometry;model->world=true;
        model->camera={1,0,0,0,0,1,0,0,0,0,1,0};model->projection={.05f,100,100,320,240,.1f};
        auto camera=std::make_shared<Snapshot>();camera->view={11,12,13,0};
        camera->target=7;camera->attachment=8;camera->viewport=9;camera->frame=frame;
        camera->camera[0]=camera->camera[4]=camera->camera[8]=std::bit_cast<unsigned>(1.f);
        camera->inverse=camera->camera;camera->projection=model->projection;camera->far_clip=far_clip;
        camera->viewport_rect={0,0,640,480};
        Draw draw{};draw.count=6;draw.texture=-1;draw.model=model;draw.camera_view=camera;
        draw.key={0,2,1,1,7,1,1};draw.scissor={{0,0},{640,480}};
        draw.push.target[0]=640;draw.push.target[1]=480;draw.push.mode[1]=draw.push.mode[2]=2;
        scene.draws={draw};renderer.render(scene,true,false);renderer.complete_camera_history(frame++,7);
        const auto pixels=renderer.capture_temporal(camera->view);
        require(pixels.width&&pixels.height,"No completed sampled depth attachment");
        const auto index=std::size_t(150*pixels.height/480)*pixels.width+150*pixels.width/640;
        require(pixels.validity[index]==0,"Unproved depth-only fixture source gained static validity");
        return pixels.depth[index];
    };
    for(float z:{.10001f,.15f,2.f,100.f})
        require(std::abs(sample(z,100)-.1f/z)<=2e-6f,"Temporal depth confused near scale with near clip");
    require(sample(.09999f,100)==0&&sample(100.01f,100)==0,"Temporal depth did not enforce guest near/far boundaries");
    const auto a=sample(700,1000),b=sample(700.01f,1000);
    require(a>b&&std::abs(a-.1f/700)<1e-9f,"R32 sampled depth lost distant-surface precision");
    std::cout<<"Temporal depth: independent near scale, near/far clipping and distant R32 precision pass\n";
}

int main(int argc,char**argv){try{
    using namespace mw34::vkscene;
    {
        const std::array<float, 8> raster{0, .1f, .2f, .3f, .4f, .5f, .6f, .75f};
        std::array<std::uint16_t, 2> guest{};
        mw34::depth::readback_scaled(guest.data(),
            reinterpret_cast<const unsigned char *>(raster.data()), 2, 1, 4, 2);
        if (guest != std::array<std::uint16_t, 2>{32768, 49151})
            throw std::runtime_error("D32 center sampling selected the wrong raster texel");
        const std::array<float, 2> narrow{0, 1};
        std::array<std::uint16_t, 3> wide{};
        mw34::depth::readback_scaled(wide.data(),
            reinterpret_cast<const unsigned char *>(narrow.data()), 3, 1, 2, 1);
        if (wide != std::array<std::uint16_t, 3>{0, 65535, 65535})
            throw std::runtime_error("D32 odd-ratio sampling changed");
    }
    const std::string mode=argc>1?argv[1]:"native";
    if(mode=="temporal")_putenv_s("MW34_GPU_MODELS","1");
    _putenv_s("MW34_SUN","0");_putenv_s("MW34_REMASTER_AF","1");
    const bool scaled_output = mode == "scaled" || mode == "visible-scaled" || mode == "odd-scaled";
    const bool odd_guest = mode == "odd" || mode == "odd-scaled";
    const char *output_width = "", *output_height = "";
    if (scaled_output) {
        output_width = "1280";
        output_height = "960";
    } else if (mode.starts_with("ssaa") || mode=="temporal") {
        output_width = "640";
        output_height = "480";
    }
    _putenv_s("MW34_REMASTER_WIDTH", output_width);
    _putenv_s("MW34_REMASTER_HEIGHT", output_height);
    _putenv_s("MW34_REMASTER_AA",mode=="ssaa"?"4":mode=="ssaa2"?"2":"1");
    auto require=[](bool b,const char* why){if(!b)throw std::runtime_error(why);};
    std::vector<std::uint16_t> values(65536),back(65536);for(unsigned i=0;i<65536;++i)values[i]=std::uint16_t(i);
    std::vector<unsigned char> packed(values.size()*4);mw34::depth::upload(packed.data(),values.data(),values.size());mw34::depth::readback(back.data(),packed.data(),back.size());require(values==back,"CPU depth ABI round trip");
    float nan=std::numeric_limits<float>::quiet_NaN();std::memcpy(packed.data(),&nan,4);bool rejected=false;try{mw34::depth::readback(back.data(),packed.data(),1);}catch(const std::runtime_error&){rejected=true;}require(rejected,"non-finite depth accepted");
    struct Window { HWND handle{}; ~Window(){if(handle)::DestroyWindow(handle);} } window;
    auto renderer=std::make_unique<Renderer>();
    if(mode=="visible-scaled") {
        window.handle=::CreateWindowExW(0,L"STATIC",L"Depth transfer check",WS_OVERLAPPEDWINDOW,
            40,40,800,600,nullptr,nullptr,::GetModuleHandleW(nullptr),nullptr);
        require(window.handle!=nullptr,"Cannot create depth test window");
        ::ShowWindow(window.handle,SW_SHOWNOACTIVATE);
        std::vector<std::uint16_t> pixels(640*480);
        require(renderer->present(window.handle,reinterpret_cast<unsigned char*>(pixels.data()),640,480,1280),"Cannot initialize depth presentation");
        require(renderer->presents>0,"Depth test did not reach swapchain");
        std::cout<<"Depth check GPU: "<<renderer->device_name<<'\n';
    }
    Scene s{};
    s.width = odd_guest ? 641 : 640;
    s.height = odd_guest ? 479 : 480;
    s.has_depth = true;
    s.color.assign(size_t(s.width) * s.height, 0x07e0);
    s.depth.resize(s.color.size());
    for(size_t i=0;i<s.depth.size();++i)s.depth[i]=std::uint16_t(i%65536);const auto expected=s.depth;
    renderer->render(s,true,true);require(s.depth==expected,"Vulkan depth upload/readback changed guest D16 values");for(auto p:s.color)require(p==0x07e0,"colour transfer corrupted");
    Scene resident{};resident.width=s.width;resident.height=s.height;resident.has_depth=true;renderer->render(resident,false,false);renderer->fetch_resident(s);require(s.depth==expected,"resident fetch changed guest depth");
    struct V{float x,y,z,rhw;unsigned color,spec;float u,v;};
    auto scene=[](){Scene a{};a.width=640;a.height=480;a.has_depth=true;a.color.assign(640*480,0);a.depth.assign(640*480,0);return a;};
    auto triangle=[](Scene&a,float z,unsigned colour){Draw d{};d.first=unsigned(a.vertices.size()/32);d.count=3;d.texture=-1;d.key={0,2,1,1,7,1,1};d.scissor={{0,0},{640,480}};d.push.target[0]=640;d.push.target[1]=480;d.push.target[2]=.5f;d.push.mode[1]=2;d.push.mode[2]=2;d.push.mode[3]=8;
        for(auto xy:{std::array<float,2>{100,100},std::array<float,2>{300,100},std::array<float,2>{100,300}}){V v{xy[0],xy[1],z,1,colour,0xff000000,0,0};auto b=reinterpret_cast<const unsigned char*>(&v);a.vertices.insert(a.vertices.end(),b,b+32);}a.order.push_back({false,unsigned(a.draws.size())});a.draws.push_back(d);};
    for(unsigned frame=0;frame<64;++frame){auto a=scene();float z=.07f+frame*.0000005f;triangle(a,z+.000004f,0xffff0000);triangle(a,z,0xff0000ff);renderer->render(a,true,true);require(a.color[120*640+120]==0xf800,"close surfaces fight at D32 precision");}
    auto a=scene();triangle(a,.070004f,0xffff0000);renderer->render(a,true,false);
    auto b=scene();triangle(b,.07f,0xff0000ff);renderer->render(b,false,false);renderer->fetch_resident(b);require(b.color[120*640+120]==0xf800,"resident scene discarded precise depth");
    auto c=scene();Clear clear{};clear.flags=2;clear.z=0;clear.rects.push_back({{0,0},{640,480}});c.clears.push_back(clear);c.order.push_back({true,0});triangle(c,.07f,0xff0000ff);renderer->render(c,false,true);require(c.color[120*640+120]==0x001f,"depth clear did not reset occlusion");
    if(mode=="temporal")temporal_depth_checks(*renderer);
    std::cout<<"PASS "<<mode<<": all 65536 guest depths, colour transfers, resident fetch, 64 close-surface positions, resident precision, depth clear.\n";
    return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
