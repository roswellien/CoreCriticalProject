// Real Vulkan regression: guest ABI, scaled transfers, resident precision and clears.
#include "vk_scene.hpp"
#include <iostream>
#include <limits>

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
    _putenv_s("MW34_SUN","0");_putenv_s("MW34_REMASTER_AF","1");
    const bool scaled_output = mode == "scaled" || mode == "visible-scaled" || mode == "odd-scaled";
    const bool odd_guest = mode == "odd" || mode == "odd-scaled";
    const char *output_width = "", *output_height = "";
    if (scaled_output) {
        output_width = "1280";
        output_height = "960";
    } else if (mode.starts_with("ssaa")) {
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
    std::cout<<"PASS "<<mode<<": all 65536 guest depths, colour transfers, resident fetch, 64 close-surface positions, resident precision, depth clear.\n";
    return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
