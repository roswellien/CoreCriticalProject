// Render resident replacement geometry with independent original damage factors.
#define NOMINMAX
#include "vk_scene.hpp"
#include <iostream>

int main() {
    try {
        _putenv_s("MW34_GPU_MODELS", "1");
        _putenv_s("MW34_SUN", "1");
        _putenv_s("MW34_SKY_AUTO", "0");
        _putenv_s("MW34_HAZE_COLOR", "0,0.5,0.5");
        _putenv_s("MW34_REMASTER_WIDTH", "1280");
        _putenv_s("MW34_REMASTER_HEIGHT", "720");
        _putenv_s("MW34_REMASTER_AA", "1");
        using namespace mw34::vkscene;
        auto renderer = std::make_unique<Renderer>();
        auto geometry = std::make_shared<ModelGeometry>();
        geometry->key = 0x535441545553ULL;
        geometry->hash = 1;
        geometry->vertices = {{0, 0, 1, .3f, .6f, -.74f, 0, 0},
                              {80, 0, 1, .3f, .6f, -.74f, 0, 0},
                              {0, 80, 1, .3f, .6f, -.74f, 0, 0}};
        unsigned checks = 0;
        auto check = [&](bool pass, const char *why) {
            ++checks;
            if (!pass)
                throw std::runtime_error(why);
        };
        for (unsigned pass = 0; pass < 3; ++pass) {
            Scene scene{};
            scene.width = 640;
            scene.height = 480;
            scene.color.assign(640 * 480, 0);
            scene.depth.assign(640 * 480, 0);
            auto add = [&](float x, unsigned fog) {
                Draw draw{};
                draw.count = 3;
                draw.texture = -1;
                draw.condition_schematic = true;
                draw.key = {0, 2, 1, 0, 8, 0, 1};
                draw.scissor = {{0, 0}, {640, 480}};
                draw.push.target[0] = 640;
                draw.push.target[1] = 480;
                draw.push.fog[0] = 1;
                draw.push.fog[3] = 1;
                draw.push.mode[0] = 16;
                draw.push.mode[1] = draw.push.mode[2] = 2;
                draw.push.mode[3] = 8;
                auto instance = std::make_shared<ModelInstance>();
                instance->geometry = geometry;
                instance->camera = {1, 0, 0, x, 0, 1, 0, 350, 0, 0, 1, 0};
                instance->projection = {1, 1, 1, 0, 0, .01f};
                instance->color = 0xffffffff;
                instance->diagnostic_fog_factor = float(fog) / 255;
                draw.model = instance;
                scene.order.push_back({false, unsigned(scene.draws.size())});
                scene.draws.push_back(draw);
            };
            const unsigned target_factor = pass == 1 ? 255 : 128;
            const unsigned player_factor = pass == 2 ? 128 : 32;
            add(30, target_factor);
            add(520, player_factor);
            add(420, 255);
            renderer->render(scene, true, true);
            auto pixel = [&](unsigned x, unsigned y) {
                const unsigned p = scene.color[size_t(y) * 640 + x];
                return std::array<unsigned, 3>{((p >> 11) & 31) * 255 / 31,
                                               ((p >> 5) & 63) * 255 / 63, (p & 31) * 255 / 31};
            };
            const auto target = pixel(40, 360), player = pixel(530, 360), healthy = pixel(430, 360),
                       absent = pixel(330, 360);
            check(target[0] > 240 && std::abs(int(target[1]) - int(target_factor)) < 10,
                  "target GPU damage factor or atmosphere isolation");
            check(player[0] > 240 && std::abs(int(player[1]) - int(player_factor)) < 10,
                  "player GPU damage factor or shared-geometry instance leak");
            check(healthy[0] > 240 && healthy[1] > 240 && healthy[2] > 240,
                  "healthy neighbouring component acquired damage");
            check(absent == std::array<unsigned, 3>{0, 0, 0}, "absent component reappeared");
            check(scene.vertices.empty(), "preview transformed vertices on the CPU");
            check(scene.draws[0].push.fog[0] == 1 && scene.draws[0].push.fog[1] == 0,
                  "world haze overwrote original diagnostic fog");
        }
        std::cout << "PASS: " << checks
                  << " resident GPU preview checks, independent player/target damage, "
                     "healthy/absent parts, "
                     "changing damage across frames, no TL vertices.\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 1;
    }
}
