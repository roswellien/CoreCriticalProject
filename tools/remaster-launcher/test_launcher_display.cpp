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
static void presentation_bounds_check() {
    auto same = [](const RECT &a, const RECT &b) {
        return a.left == b.left && a.top == b.top && a.right == b.right && a.bottom == b.bottom;
    };
    struct Case {
        unsigned output_width, output_height, window_width, window_height;
        RECT expected;
    };
    // Include the observed window, tall/wide resizes, and an odd one-pixel bar.
    for (const auto &test : std::array<Case, 5>{{
             {3440, 1440, 3456, 1479, {0, 16, 3456, 1463}},
             {1920, 1080, 1920, 1080, {0, 0, 1920, 1080}},
             {1920, 1080, 1000, 1000, {0, 218, 1000, 781}},
             {1920, 1080, 2000, 1000, {111, 0, 1889, 1000}},
             {1920, 1080, 1920, 1081, {0, 0, 1920, 1080}},
         }}) {
        const auto uploaded = mw34::display::upload_presentation_rect(
            1024, 768, test.output_width, test.output_height, test.window_width,
            test.window_height, true);
        if (!same(uploaded, test.expected))
            throw std::runtime_error("World upload changed presentation bounds");
        for (const auto *aa : {"1", "2", "4"}) {
            const auto samples = mw34::display::samples(aa);
            const auto resident = mw34::display::presentation_rect(
                double(test.output_width * samples.x) / samples.x,
                double(test.output_height * samples.y) / samples.y,
                test.window_width, test.window_height);
            if (!same(resident, test.expected))
                throw std::runtime_error("Resident presentation changed bounds");
        }
    }
    const auto menu = mw34::display::upload_presentation_rect(640, 480, 3440, 1440,
                                                             1920, 1080, false);
    if (!same(menu, {240, 0, 1680, 1080}))
        throw std::runtime_error("Menu upload lost its original aspect ratio");
    std::cout << "PASS resident/upload presentation bounds, resize, SSAA and menu aspect\n";
}
static void world_resolution_check(bool persistent_hud = false, bool visible = false,
                                   bool partial_world = false) {
    using namespace mw34::vkscene;
    auto require = [](bool ok, const char *message) {
        if (!ok)
            throw std::runtime_error(message);
    };
    struct TestWindow {
        HWND handle{};
        ~TestWindow() {
            if (handle)
                ::DestroyWindow(handle);
        }
    } window;
    Renderer renderer;
    if (visible) {
        require(renderer.max_texture_dimension(nullptr) >= 640,
                "Pre-window capability query cannot support the guest target");
        window.handle = ::CreateWindowExW(0, L"STATIC", L"World resolution presentation check",
                                          WS_OVERLAPPEDWINDOW, 40, 40, 800, 600, nullptr, nullptr,
                                          ::GetModuleHandleW(nullptr), nullptr);
        require(window.handle != nullptr, "Cannot create presentation test window");
        require(renderer.max_texture_dimension(window.handle) >= 640,
                "Presenting adapter cannot support the guest target");
        ::ShowWindow(window.handle, SW_SHOWNOACTIVATE);
        std::vector<std::uint16_t> pixels(640 * 480);
        require(renderer.present(window.handle, reinterpret_cast<unsigned char *>(pixels.data()),
                                 640, 480, 1280),
                "Cannot initialize visible Vulkan presentation");
        require(renderer.presents > 0, "Visible upload did not reach the swapchain");
    }
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
    std::cout << "World resolution check GPU: " << renderer.device_name << '\n';
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
    if (Renderer::fxaa_enabled())
        require(renderer.fxaa_passes > 0, "Fresh world color did not receive FXAA");
    const unsigned x = output_width * 100 / 640, y = output_height * 150 / 480;
    auto red = [&](unsigned xx) { return rgb[(size_t(y) * w + xx) * 3]; };
    require(red(x) > 240 && red(x - 1) < 8 && red(x + output_width / 640) < 8,
            "Output-resolution HUD edge was filtered");
    // The HUD converts color keys to zero alpha and uses straight alpha for
    // masks/fades. Exercise those GPU inputs over a known world color.
    Scene panel{};
    panel.width = 640;
    panel.height = 480;
    panel.has_depth = true;
    panel.hud = true;
    Clear green{};
    green.flags = 1;
    green.color[1] = 1;
    green.color[3] = 1;
    green.rects.push_back({{200, 100}, {40, 40}});
    panel.clears.push_back(green);
    panel.order.push_back({true, 0});
    for (unsigned alpha : {0U, 128U, 255U}) {
        renderer.render(panel, false, false);
        Scene masked{};
        masked.width = 640;
        masked.height = 480;
        masked.has_depth = true;
        masked.hud = true;
        TextureRef texture{};
        texture.key = 1000 + alpha;
        texture.hash = 2000 + alpha;
        texture.width = texture.height = 1;
        texture.format = TexFormat::rgba8888;
        texture.pixels32.push_back(0x000000ffU | (alpha << 24));
        masked.textures.push_back(texture);
        triangle(masked, 0, 0xffffffff);
        auto &draw = masked.draws[0];
        draw.texture = 0;
        draw.sampler = (3U << 4) | (3U << 8);
        draw.key = {1, 5, 6, 0, 8, 0, 1};
        draw.push.mode[0] = 4;
        draw.push.mode[1] = draw.push.mode[2] = 2 | (2 << 8);
        draw.push.mode[3] = 0;
        renderer.render(masked, false, false);
        renderer.capture_fullres_rgb(rgb, w, h);
        const size_t pixel = (size_t(output_height * 120 / 480) * w + output_width * 220 / 640) * 3;
        require(std::abs(int(rgb[pixel]) - int(alpha)) <= 8 &&
                    std::abs(int(rgb[pixel + 1]) - int(255 - alpha)) <= 8,
                "HUD transparent/half-alpha/opaque composition changed");
    }
    renderer.render(panel, false, false);
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
    if (world.depth[150 * 640 + 100] != 49151)
        throw std::runtime_error("Guest depth conversion changed: expected 49151, got " +
                                 std::to_string(world.depth[150 * 640 + 100]));
    renderer.present_resident(nullptr, 640, 480); // Hidden presentation still ends the frame.
    renderer.render(depth_reset, false, false);
    require(renderer.raster_width() == output_width,
            "Depth-only frame reduced retained output pixels");
    if (persistent_hud) {
        const auto previous_fxaa = renderer.fxaa_passes;
        // This draw does not overlap the retained HUD line. Both a depth-only
        // frame and a partial world frame must leave that line unchanged.
        if (partial_world) {
            const auto previous_coverage = renderer.coverage_scenes;
            renderer.capture_fullres_rgb(rgb, w, h);
            const auto retained = rgb;
            Scene mixed = later;
            const auto original_vertex_bytes = mixed.vertices.size();
            mixed.vertices.resize(original_vertex_bytes * 2);
            std::memcpy(mixed.vertices.data() + original_vertex_bytes, mixed.vertices.data(),
                        original_vertex_bytes);
            for (size_t at = original_vertex_bytes; at < mixed.vertices.size(); at += 32) {
                float horizontal;
                std::memcpy(&horizontal, mixed.vertices.data() + at, 4);
                horizontal -= 150;
                std::memcpy(mixed.vertices.data() + at, &horizontal, 4);
                unsigned transparent_color = 0x0000ff00;
                std::memcpy(mixed.vertices.data() + at + 16, &transparent_color, 4);
            }
            Draw transparent_world = mixed.draws[0];
            transparent_world.first = unsigned(original_vertex_bytes / 32);
            transparent_world.key = {1, 5, 6, 0, 8, 0, 1};
            mixed.order.push_back({false, unsigned(mixed.draws.size())});
            mixed.draws.push_back(transparent_world);
            renderer.render(mixed, false, false);
            renderer.capture_fullres_rgb(rgb, w, h);
            if (percent < 100)
                require(renderer.coverage_scenes == previous_coverage + 1,
                        "Partial world did not use coverage reconstruction");
            // The opt-in reduced path guarantees untouched output pixels.
            // The unchanged 100% path retains its historical whole-image FXAA.
            if (percent < 100)
                for (unsigned yy = 0; yy < h; ++yy)
                    for (unsigned xx = 0; xx < w; ++xx) {
                        const double guest_x = (xx + .5) * 640 / w - .5;
                        const double guest_y = (yy + .5) * 480 / h - .5;
                        if (guest_x >= 199 && guest_y >= 99 && guest_x + guest_y <= 501)
                            continue;
                        const auto pixel = (size_t(yy) * w + xx) * 3;
                        require(std::equal(rgb.begin() + pixel, rgb.begin() + pixel + 3,
                                           retained.begin() + pixel),
                                "Coverage replay changed an untouched output pixel");
                    }
            Scene precise_depth = world;
            renderer.fetch_resident(precise_depth);
            require(precise_depth.depth[150 * 640 + 100] == 49151,
                    "Coverage reconstruction changed untouched guest depth");
            // A discarded world fragment must not replace the retained HUD,
            // even when its triangle geometrically overlaps the HUD line.
            if (percent < 100) {
                Scene discarded = later;
                for (size_t at = 0; at < discarded.vertices.size(); at += 32) {
                    float horizontal;
                    std::memcpy(&horizontal, discarded.vertices.data() + at, 4);
                    horizontal -= 150;
                    std::memcpy(discarded.vertices.data() + at, &horizontal, 4);
                }
                TextureRef transparent{};
                transparent.key = 0x9911;
                transparent.hash = 0x9911;
                transparent.width = transparent.height = 1;
                transparent.format = TexFormat::rgba8888;
                transparent.pixels32 = {0x00ffffff};
                discarded.textures.push_back(transparent);
                auto &alpha_draw = discarded.draws[0];
                alpha_draw.texture = 0;
                alpha_draw.push.mode[0] = 4 | 32;
                alpha_draw.push.mode[2] = 2 | (2 << 8);
                alpha_draw.push.mode[3] = 5 | (128 << 8);
                const auto before_discard = rgb;
                renderer.render(discarded, false, false);
                renderer.capture_fullres_rgb(rgb, w, h);
                require(rgb == before_discard, "World alpha rejection changed retained output");
            }
        }
        renderer.capture_fullres_rgb(rgb, w, h);
        if (percent < 100 && Renderer::fxaa_enabled())
            require(partial_world ? renderer.fxaa_passes > previous_fxaa :
                                    renderer.fxaa_passes == previous_fxaa,
                    "World AA did not follow covered versus untouched pixels");
        std::cout << "Persistent HUD red: center=" << unsigned(red(x))
                  << " outside=" << unsigned(red(x - 1)) << '\n';
        require(red(x) > 240 && red(x - 1) < 8 && red(x + output_width / 640) < 8,
                "Persistent HUD edge changed across the world-frame boundary");
    }
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
    if (visible) {
        auto present = [&] {
            const auto previous = renderer.presents;
            require(renderer.present_resident(window.handle, 640, 480),
                    "Resident presentation failed");
            require(renderer.presents > previous, "Resident frame did not reach the swapchain");
        };
        present();
        ::SetWindowPos(window.handle, nullptr, 0, 0, 960, 540,
                       SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE);
        present();
        ::ShowWindow(window.handle, SW_MINIMIZE);
        require(::IsIconic(window.handle), "Test window did not minimize");
        require(renderer.present_resident(window.handle, 640, 480),
                "Minimized presentation failed");
        ::ShowWindow(window.handle, SW_RESTORE);
        present();
        const auto before_hidden = renderer.presents;
        ::ShowWindow(window.handle, SW_HIDE);
        require(renderer.present_resident(window.handle, 640, 480), "Hidden presentation failed");
        require(renderer.presents == before_hidden, "Hidden window submitted presentation");
        ::ShowWindow(window.handle, SW_SHOWNOACTIVATE);
        present();
        std::cout << "PASS visible presentation, resize, minimize/restore and hide/restore; "
                     "swapchain presents "
                  << renderer.presents << '\n';
    }
    std::cout << "PASS world/output separation, HUD edges, mixed draws, readback and frontend "
                 "transitions\n";
}
int main(int argc, char **argv) {
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

    if (argc > 1 && std::string(argv[1]) == "--presentation-bounds") {
        try {
            presentation_bounds_check();
            return 0;
        } catch (const std::exception &error) {
            std::cerr << error.what() << '\n';
            return 1;
        }
    }
    if (argc > 1 && (std::string(argv[1]) == "--world-resolution" ||
                     std::string(argv[1]) == "--world-persistence" ||
                     std::string(argv[1]) == "--world-persistence-partial" ||
                     std::string(argv[1]) == "--world-present")) {
        try {
            world_resolution_check(std::string(argv[1]).starts_with("--world-persistence"),
                                   std::string(argv[1]) == "--world-present",
                                   std::string(argv[1]) == "--world-persistence-partial");
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
