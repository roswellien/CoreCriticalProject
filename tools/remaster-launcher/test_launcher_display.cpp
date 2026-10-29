// Actual Vulkan target/scissor checks for the launcher's display and SSAA settings.
#include "vk_scene.hpp"
#include <cassert>
#include <iostream>
static void world_resolution_check() {
    using namespace mw34::vkscene;
    auto require = [](bool ok, const char *message) {
        if (!ok)
            throw std::runtime_error(message);
    };
    Renderer renderer;
    Scene world{};
    world.width = 640;
    world.height = 480;
    world.has_depth = true;
    world.color.assign(640 * 480, 0);
    world.depth.assign(640 * 480, 65535);
    Clear clear{};
    clear.flags = 3;
    clear.color[2] = 1;
    clear.color[3] = 1;
    clear.z = 0.75f;
    clear.rects.push_back({{0, 0}, {640, 480}});
    world.clears.push_back(clear);
    world.order.push_back({true, 0});
    auto triangle = [](Scene &scene, float depth, unsigned color) {
        struct Vertex {
            float x, y, z, rhw;
            unsigned color, specular;
            float u, v;
        };
        Draw draw{};
        draw.first = unsigned(scene.vertices.size() / sizeof(Vertex));
        draw.count = 3;
        draw.texture = -1;
        draw.key = {0, 2, 1, 1, 7, 1, 1};
        draw.scissor = {{0, 0}, {640, 480}};
        draw.push.target[0] = 640;
        draw.push.target[1] = 480;
        draw.push.target[2] = .5f;
        draw.push.mode[1] = 2;
        draw.push.mode[2] = 2;
        draw.push.mode[3] = 8;
        for (auto xy : {std::array<float, 2>{200, 100}, {400, 100}, {200, 300}}) {
            Vertex vertex{xy[0], xy[1], depth, 1, color, 0xff000000, 0, 0};
            auto bytes = reinterpret_cast<const unsigned char *>(&vertex);
            scene.vertices.insert(scene.vertices.end(), bytes, bytes + sizeof(Vertex));
        }
        scene.order.push_back({false, unsigned(scene.draws.size())});
        scene.draws.push_back(draw);
    };
    triangle(world, .800004f, 0xff00ff00);
    renderer.render(world, true, false);
    const char *configured_percent = std::getenv("MW34_WORLD_SCALE_PERCENT");
    const unsigned percent = configured_percent ? std::stoul(configured_percent) : 100;
    const unsigned output_width = Renderer::remaster_width();
    const unsigned output_height = Renderer::remaster_height();
    require(renderer.raster_width() == output_width * percent / 100 &&
                renderer.raster_height() == output_height * percent / 100,
            "World did not use independent raster resolution");
    Scene hud{};
    hud.width = 640;
    hud.height = 480;
    hud.has_depth = true;
    hud.hud = true;
    Clear line{};
    line.flags = 1;
    line.color[0] = 1;
    line.color[3] = 1;
    line.rects.push_back({{100, 100}, {1, 100}});
    hud.clears.push_back(line);
    hud.order.push_back({true, 0});
    renderer.render(hud, false, false);
    require(renderer.raster_width() == output_width && renderer.raster_height() == output_height,
            "HUD did not promote to output resolution");
    std::vector<unsigned char> rgb;
    unsigned w{}, h{};
    renderer.capture_fullres_rgb(rgb, w, h);
    const unsigned x = output_width * 100 / 640, y = output_height * 150 / 480;
    auto red = [&](unsigned xx) { return rgb[(size_t(y) * w + xx) * 3]; };
    require(red(x) > 240 && red(x - 1) < 8 && red(x + output_width / 640) < 8,
            "Output-resolution HUD edge was filtered");
    // A subsequent partial world pass cannot resample the HUD already drawn.
    Scene later{};
    later.width = 640;
    later.height = 480;
    later.has_depth = true;
    clear.flags = 1;
    clear.rects = {{{400, 300}, {20, 20}}};
    later.clears.push_back(clear);
    later.order.push_back({true, 0});
    triangle(later, .8f, 0xffff0000);
    renderer.render(later, false, false);
    require(renderer.raster_width() == output_width, "Mixed world pass downsampled the HUD");
    renderer.capture_fullres_rgb(rgb, w, h);
    require(red(x) > 240 && red(x - 1) < 8, "Mixed world pass changed the HUD edge");
    Scene depth_reset{};
    depth_reset.width = 640;
    depth_reset.height = 480;
    depth_reset.has_depth = true;
    Clear depth_clear{};
    depth_clear.flags = 2;
    depth_clear.z = .75f;
    depth_clear.rects.push_back({{0, 0}, {640, 480}});
    depth_reset.clears.push_back(depth_clear);
    depth_reset.order.push_back({true, 0});
    // Depth-only clears within the same frame cannot restart reduced composition.
    renderer.render(depth_reset, false, false);
    require(renderer.raster_width() == output_width, "Mid-frame depth reset reduced HUD");
    renderer.fetch_resident(world);
    require(world.color[120 * 640 + 220] == 0x07e0, "Promotion lost precise world depth");
    require(world.color[150 * 640 + 100] == 0xf800, "Guest readback lost HUD pixels");
    require(world.depth[150 * 640 + 100] == 49151, "Guest depth conversion changed");
    renderer.present_resident(nullptr, 640, 480); // Hidden presentation still ends the frame.
    renderer.render(depth_reset, false, false);
    require(renderer.raster_width() == output_width * percent / 100,
            "Presented frame followed by depth-only clear did not restart world");
    renderer.render(world, false, false);
    require(renderer.raster_width() == output_width * percent / 100,
            "Full clear did not restart reduced rendering");
    // Frontend transitions recreate both target sets and keep menus full resolution.
    world.frontend_canvas = true;
    renderer.render(world, true, false);
    require(renderer.raster_width() == output_width, "Frontend was reduced");
    world.frontend_canvas = false;
    renderer.render(world, true, false);
    require(renderer.raster_width() == output_width * percent / 100,
            "World target was not recreated");
    renderer.fetch_resident(world);
    require(world.color[0] == 0x001f && world.depth[0] == 49151,
            "Recreated target readback changed");
    require(percent == 100 ||
                (renderer.reduced_world_scenes >= 3 && renderer.world_promotions >= 2),
            "Reduced target path did not execute");
    std::cout << "PASS world/output separation, HUD edges, mixed draws, readback and frontend "
                 "transitions\n";
}
int main(int argc, char **argv) {
    if (argc > 1 && std::string(argv[1]) == "--world-resolution") {
        try {
            world_resolution_check();
            return 0;
        } catch (const std::exception &error) {
            std::cerr << error.what() << '\n';
            return 1;
        }
    }
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
