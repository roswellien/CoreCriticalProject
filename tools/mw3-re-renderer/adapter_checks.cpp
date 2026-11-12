#include "frame_renderer.hpp"
#include "frontend/sdl/sdl_child.h"
#include "training_material.hpp"

#include <cstdio>
#include <filesystem>
#include <stdexcept>

namespace {

void require(bool condition, const char *message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

void quad(platform::Render3D &renderer, float low, float high, float depth, uint32_t color,
          const platform::DrawState &state = {}) {
    const platform::TLVertex vertices[] = {{low, low, depth, 1, color, 0, 0, 0},
                                           {high, low, depth, 1, color, 0, 1, 0},
                                           {high, high, depth, 1, color, 0, 1, 1},
                                           {low, high, depth, 1, color, 0, 0, 1}};
    renderer.draw(platform::Primitive::kFan, vertices, 4, state);
}

void check_scene(SDL_Window *window) {
    auto renderer = cc_mw3_re::make_renderer(window);
    renderer->set_viewport(0, 0, 32, 32);
    renderer->clear(true, 0, 0, 255);
    renderer->begin_scene();
    quad(*renderer, 8, 24, .75f, 0xff00ff00);
    quad(*renderer, 4, 28, .25f, 0xffff0000);
    renderer->end_scene();
    auto pixel = [&](int x, int y) {
        std::vector<uint32_t> pixels;
        int width = 0, height = 0;
        require(renderer->read_back(&pixels, &width, &height) && width == 32 && height == 32,
                "Could not read the Vulkan scene");
        return pixels.at(y * width + x);
    };
    require(pixel(16, 16) == 0xff00ff00 && pixel(6, 6) == 0xffff0000 && pixel(2, 2) == 0xff0000ff,
            "Draw order or reversed depth changed");

    require(renderer->hold_frame(), "Could not hold the composed frame");
    renderer->clear(false, 0, 0, 0);
    const uint8_t yellow[] = {255, 255, 0, 255};
    const uint8_t cyan[] = {0, 255, 255, 255};
    const auto first = renderer->create_texture(1, 1, yellow, 1);
    platform::DrawState textured{};
    textured.texture = first;
    quad(*renderer, 12, 20, .125f, 0xffffffff, textured);
    renderer->release_texture(first);
    require(pixel(16, 16) == 0xffffff00 && pixel(6, 6) == 0xffff0000,
            "Depth-only clear changed color or a released texture lost its queued draw");
    textured.texture = renderer->create_texture(1, 1, cyan, 1);
    quad(*renderer, 12, 20, .5f, 0xffffffff, textured);
    renderer->release_texture(textured.texture);
    require(pixel(16, 16) == 0xff00ffff, "Reused slot kept stale texture pixels");
    require(renderer->restore_frame() && pixel(16, 16) == 0xff00ff00,
            "Restored frame lost its saved pixels");
    renderer->drop_frame();
    renderer->reset_scene_resources();
    renderer->clear(true, 0, 0, 0);
    textured.texture = renderer->create_texture(1, 1, cyan, 1);
    quad(*renderer, 12, 20, .5f, 0xffffffff, textured);
    require(pixel(16, 16) == 0xff00ffff && pixel(6, 6) == 0xff000000,
            "A new scene inherited the previous color or texture");
    renderer->release_texture(textured.texture);

    renderer->clear(true, 0, 0, 255);
    const uint8_t premultiplied_red[] = {128, 0, 0, 128};
    platform::DrawState hud{};
    hud.texture = renderer->create_texture(1, 1, premultiplied_red, 4);
    hud.address_u = hud.address_v = 3;
    hud.sharp = hud.blend = hud.depth_always = true;
    hud.depth_write = false;
    quad(*renderer, 0, 32, 0, 0xffffffff, hud);
    renderer->release_texture(hud.texture);
    require((pixel(16, 16) & 0x00ffffff) == 0x0080007f,
            "The sharp HUD layer darkened premultiplied color twice");

    const auto ready = "cc-adapter-ready-" + std::to_string(SDL_GetPerformanceCounter());
    require(!std::filesystem::exists(ready), "Ready marker path already exists");
    sdlfe::set_ready_file(ready);
    renderer->present();
    sdlfe::set_ready_file("");
    require(!std::filesystem::remove(ready), "A hidden frame signaled first presentation");
}

void check_material_admission() {
    // The row-vector model-view rotates x into y and y into negative x.
    const float view[] = {0, 1, 0, -1, 0, 0, 0, 0, 1, 0, 0, 8};
    const float world[] = {1, 0, 0, 0, 1, 0, 0, 0, 1, 2, 4, 6};
    const float positions[] = {0, 0, 0, 2, 0, 0, 0, 2, 0};
    const uint32_t indices[] = {0, 1, 2};
    const platform::ModelSurface surface{"fixture", nullptr, "fixture", positions, nullptr, indices,
                                         nullptr,   world,   view,      1,         10,      10,
                                         16,        16,      100,       3};
    platform::TLVertex draw[] = {{13.5f, 16, .125f, .125f, 0, 0, 0, 1},
                                 {16, 18.5f, .125f, .125f, 0, 0, 1, 0},
                                 {16, 16, .125f, .125f, 0, 0, 0, 0}};
    const auto admitted = [&] {
        return bool(cc_mw3_re::model_for_draw(surface, platform::Primitive::kFan, draw, 3,
                                              {0, 0, 32, 32}, 32, 32));
    };
    require(admitted(), "Actual draw no longer matches its rotated source surface");
    draw[0].sx += .5f;
    require(!admitted(), "Modified projection incorrectly admitted an enhanced draw");

    sdlfe::CoreCriticalOptions invalid;
    invalid.lighting = "normal";
    invalid.node = "fixture";
    invalid.texture = "fixture";
    invalid.albedo_hash = "0123456789abcdef";
    bool rejected = false;
    try {
        const cc_mw3_re::TrainingMaterial material(invalid);
    } catch (const std::runtime_error &) {
        rejected = true;
    }
    require(rejected, "Normal lighting accepted a missing sidecar");
}

} // namespace

int main() {
    if (!SDL_Init(SDL_INIT_VIDEO)) {
        std::fprintf(stderr, "%s\n", SDL_GetError());
        return 1;
    }
    auto *window = SDL_CreateWindow("Core Critical adapter checks", 32, 32, SDL_WINDOW_HIDDEN);
    int result = 0;
    try {
        require(window != nullptr, SDL_GetError());
        check_material_admission();
        check_scene(window);
    } catch (const std::exception &error) {
        std::fprintf(stderr, "%s\n", error.what());
        result = 1;
    }
    if (window) {
        SDL_DestroyWindow(window);
    }
    SDL_Quit();
    return result;
}
