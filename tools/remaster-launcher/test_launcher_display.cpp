// Actual Vulkan target/scissor checks for the launcher's display and SSAA settings.
#include "vk_scene.hpp"
#include <cassert>
#include <iostream>
int main(int argc,char**argv){
    using namespace mw34::vkscene;
    HWND window{};
    if(argc>1){
        ::SetProcessDPIAware();
        window=::CreateWindowExW(0,L"STATIC",L"MW3 Launcher Display Validation",WS_POPUP,0,0,int(Renderer::remaster_width()),int(Renderer::remaster_height()),nullptr,nullptr,::GetModuleHandleW(nullptr),nullptr);
        assert(window);
        if(std::getenv("MW34_WINDOW_MODE")&&!std::strcmp(std::getenv("MW34_WINDOW_MODE"),"fullscreen"))mw34::display::exclusive().acquire(window,Renderer::remaster_width(),Renderer::remaster_height());
        ::ShowWindow(window,SW_SHOW);::SetForegroundWindow(window);
    }
    auto owner=std::make_unique<Renderer>();auto&renderer=*owner;
    Scene scene{};scene.width=640;scene.height=480;scene.has_depth=true;
    scene.color.assign(640*480,0);scene.depth.assign(640*480,65535);
    Clear red{};red.flags=1;red.color[0]=1;red.color[3]=1;red.rects.push_back({{0,0},{320,240}});
    scene.clears.push_back(red);scene.order.push_back({true,0});
    if(window)renderer.present(window,reinterpret_cast<const unsigned char*>(scene.color.data()),640,480,1280);
    renderer.render(scene,true,true);
    std::vector<unsigned char> rgb;unsigned w{},h{};renderer.capture_fullres_rgb(rgb,w,h);
    const auto ss=mw34::display::samples(std::getenv("MW34_REMASTER_AA"));
    assert(w==Renderer::remaster_width()*ss.x&&h==Renderer::remaster_height()*ss.y);
    auto pixel=[&](unsigned x,unsigned y,unsigned channel){return rgb[(size_t(y)*w+x)*3+channel];};
    assert(pixel(w/4,h/4,0)>240&&pixel(w/4,h/4,1)<8);
    assert(pixel(w*3/4,h/4,0)<8&&pixel(w/4,h*3/4,0)<8);
    // Guest-sized buffers are still returned at their original dimensions.
    assert(scene.color.size()==640*480&&scene.depth.size()==640*480);
    assert(scene.color[120*640+160]==0xf800&&scene.color[360*640+160]==0);
    if(window){renderer.present_resident(window,640,480);owner.reset();::DestroyWindow(window);mw34::display::exclusive().release();}
    std::cout<<"Vulkan output "<<Renderer::remaster_width()<<"x"<<Renderer::remaster_height()<<", raster "<<w<<"x"<<h<<": scissor and guest copy-back passed\n";
}
