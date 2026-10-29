// Actual Vulkan target/scissor checks for the launcher's display and SSAA settings.
#include "vk_scene.hpp"
#include <cassert>
#include <iostream>
static void dxgi_presentation_check() {
    using namespace mw34::vkscene;
    _putenv_s("MW34_DXGI_PRESENT", "1");
    _putenv_s("MW34_REMASTER_WIDTH", "1280");
    _putenv_s("MW34_REMASTER_HEIGHT", "960");
    _putenv_s("MW34_REMASTER_AA", "1");
    _putenv_s("MW34_REMASTER_AF", "1");
    _putenv_s("MW34_WINDOW_MODE", "windowed");
    _putenv_s("MW34_SUN", "0");
    auto require = [](bool condition, const char *message) {
        if (!condition)
            throw std::runtime_error(message);
    };
    struct Window {
        HWND handle{};
        ~Window() {
            if (handle)
                ::DestroyWindow(handle);
        }
    } window;
    Renderer renderer;
    require(renderer.max_texture_dimension(nullptr) >= 1280,
            "Insufficient pre-window texture limit");
    require(renderer.dxgi_presenting(), "DXGI presentation request was not selected");
    if (const char *expected = std::getenv("MW34_TEST_GPU"))
        require(renderer.device_name == expected, "Presentation selected the wrong GPU");
    window.handle =
        ::CreateWindowExW(0, L"STATIC", L"Vulkan/DXGI presentation check", WS_POPUP, 40, 40, 1280,
                          960, nullptr, nullptr, ::GetModuleHandleW(nullptr), nullptr);
    require(window.handle != nullptr, "Cannot create presentation window");
    ::ShowWindow(window.handle, SW_SHOWNOACTIVATE);
    std::vector<std::uint16_t> upload(640 * 480, 0x07e0);
    constexpr unsigned rgba_pitch = 640 * 4 + 16;
    std::vector<unsigned char> rgba(rgba_pitch * 480);
    const std::array<unsigned char, 4> rgba_color{27, 119, 213, 255};
    for (unsigned y = 0; y < 480; ++y)
        for (unsigned x = 0; x < 640; ++x)
            std::memcpy(rgba.data() + y * rgba_pitch + x * 4, rgba_color.data(), 4);
    bool rgba_mode = false;
    auto present_pixel = [&](bool resident, unsigned x, unsigned y, std::array<int, 4> expected) {
        renderer.request_presented_bgra_pixel(x, y);
        const auto previous = renderer.presents;
        const bool accepted =
            resident
                ? renderer.present_resident(window.handle, 640, 480)
                : renderer.present(window.handle,
                                   rgba_mode ? rgba.data()
                                             : reinterpret_cast<unsigned char *>(upload.data()),
                                   640, 480, rgba_mode ? rgba_pitch : 1280, rgba_mode, rgba_mode);
        require(accepted && renderer.presents == previous + 1,
                "Frame did not reach DXGI presentation");
        const auto pixel = renderer.presented_bgra_pixel();
        for (unsigned channel = 0; channel < 4; ++channel)
            if (expected[channel] >= 0)
                require(std::abs(int(pixel[channel]) - expected[channel]) <= (rgba_mode ? 1 : 8),
                        "DXGI presentation pixel changed color or placement");
    };
    present_pixel(false, 640, 480, {0, 255, 0, 255});
    Scene world{};
    world.width = 640;
    world.height = 480;
    world.has_depth = true;
    world.color.assign(640 * 480, 0);
    world.depth.assign(640 * 480, 65535);
    Clear background{};
    background.flags = 3;
    background.z = .75f;
    background.color[2] = background.color[3] = 1;
    background.rects.push_back({{0, 0}, {640, 480}});
    world.clears.push_back(background);
    world.order.push_back({true, 0});
    renderer.render(world, true, false);
    Scene hud{};
    hud.width = 640;
    hud.height = 480;
    hud.has_depth = hud.hud = true;
    Clear line{};
    line.flags = 1;
    line.color[0] = line.color[3] = 1;
    line.rects.push_back({{100, 100}, {1, 100}});
    hud.clears.push_back(line);
    hud.order.push_back({true, 0});
    Clear panel{};
    panel.flags = 1;
    panel.color[0] = panel.color[1] = .5f;
    panel.color[3] = 1;
    panel.rects.push_back({{200, 100}, {40, 40}});
    hud.clears.push_back(panel);
    hud.order.push_back({true, 1});
    renderer.render(hud, false, false);
    present_pixel(true, 200, 300, {0, 0, 255, 255});
    present_pixel(true, 440, 240, {0, 128, 128, 255});
    renderer.fetch_resident(world);
    require(world.depth[150 * 640 + 100] == 49151, "Presentation changed guest depth readback");
    ::SetWindowPos(window.handle, nullptr, 0, 0, 960, 540,
                   SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE);
    present_pixel(true, 0, 0, {0, 0, 0, -1});
    rgba_mode = true;
    present_pixel(false, 0, 0, {0, 0, 0, -1});
    present_pixel(false, 480, 270, {213, 119, 27, 255});
    rgba_mode = false;
    auto previous = renderer.presents;
    ::ShowWindow(window.handle, SW_MINIMIZE);
    require(::IsIconic(window.handle), "Presentation window did not minimize");
    require(renderer.present_resident(window.handle, 640, 480), "Minimized presentation failed");
    require(renderer.presents == previous, "Minimized window counted a frame");
    ::ShowWindow(window.handle, SW_RESTORE);
    present_pixel(true, 500, 400, {255, 0, 0, 255});
    previous = renderer.presents;
    ::ShowWindow(window.handle, SW_HIDE);
    require(renderer.present_resident(window.handle, 640, 480), "Hidden presentation failed");
    require(renderer.presents == previous, "Hidden window counted a frame");
    ::ShowWindow(window.handle, SW_SHOWNOACTIVATE);
    present_pixel(true, 500, 400, {255, 0, 0, 255});
    // Exercise the ordinary handoff without diagnostic readbacks serializing each frame.
    for (unsigned frame = 0; frame < 16; ++frame) {
        world.clears[0].color[0] = frame & 1 ? 1.f : 0.f;
        world.clears[0].color[2] = frame & 1 ? 0.f : 1.f;
        renderer.render(world, true, false);
        previous = renderer.presents;
        require(renderer.present_resident(window.handle, 640, 480), "Uncaptured frame failed");
        require(renderer.presents == previous + 1, "Uncaptured frame was not presented");
    }
    world.clears[0].color[0] = world.clears[0].color[2] = 0;
    world.clears[0].color[1] = 1;
    renderer.render(world, true, false);
    present_pixel(true, 480, 270, {0, 255, 0, 255});
    require(renderer.presents == 25, "Unexpected presentation count");
    std::cout << "PASS DXGI bridge on " << renderer.device_name
              << ": RGB565/RGBA upload, resident colors, HUD, depth, resize/minimize/hide; 25 "
                 "presents\n";
}
int main(int argc,char**argv){
    if (argc > 1 && (std::string(argv[1]) == "--dxgi-exclusive-reject" ||
                     std::string(argv[1]) == "--dxgi-setting-reject")) {
        const bool exclusive = std::string(argv[1]) == "--dxgi-exclusive-reject";
        _putenv_s("MW34_DXGI_PRESENT", exclusive ? "1" : "unsupported");
        _putenv_s("MW34_WINDOW_MODE", exclusive ? "fullscreen" : "windowed");
        _putenv_s("MW34_SUN", "0");
        try {
            mw34::vkscene::Renderer renderer;
            renderer.max_texture_dimension(nullptr);
            std::cerr << "Unsupported DXGI configuration was accepted\n";
            return 1;
        } catch (const std::runtime_error &error) {
            const std::string expected = exclusive ? "requires windowed or borderless mode" :
                                                    "MW34_DXGI_PRESENT requires 0 or 1";
            if (std::string(error.what()).find(expected) == std::string::npos) {
                std::cerr << error.what() << '\n';
                return 1;
            }
            std::cout << "PASS unsupported DXGI configuration rejected before window changes\n";
            return 0;
        }
    }
    if (argc > 1 && std::string(argv[1]) == "--dxgi-present") {
        try { dxgi_presentation_check(); return 0; }
        catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
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
