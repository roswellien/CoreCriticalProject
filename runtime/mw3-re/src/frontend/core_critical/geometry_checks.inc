#include "renderer/geometry/reference.hpp"

std::array<float, 3> reference_haze_color(const mw34::sun::Settings &settings,
                                         const std::array<float, 3> &view) {
    // CPU mirror of sun_scene.frag's hazeColor, before target dithering/quantization.
    const auto uniform = mw34::sun::uniform({}, settings);
    const auto &direction = uniform.direction;
    const float view_length = std::hypot(view[0], view[2]);
    const float sun_length = std::hypot(direction[0], direction[2]);
    float side = .5f;
    if (view_length >= 1e-5f && sun_length >= 1e-5f)
        side = std::clamp(.5f + .5f * (view[0] * direction[0] + view[2] * direction[2]) /
                                     (view_length * sun_length), 0.f, 1.f);
    const float angle = std::acos(std::clamp(view[0] * direction[0] + view[1] * direction[1] +
                                               view[2] * direction[2], -1.f, 1.f));
    const float glow = settings.glow_strength *
        (std::exp(-angle * settings.glow_focus) +
         .35f * side * side * side * std::exp(-std::max(view[1], 0.f) * 4.f));
    auto result = mw34::sun::fog_color(settings, {.125f, .125f, .188f});
    for (unsigned channel = 0; channel < 3; ++channel)
        result[channel] = result[channel] * (settings.anti_haze + side * (1.f - settings.anti_haze)) +
                          settings.glow_color[channel] * glow * .6f;
    return result;
}

void check_campaign_fog_color() {
    namespace vk = mw34::vkscene;
    mw34::sun::Settings base;
    base.enabled = true;
    auto campaign = mw34::campaign::mission_sun_settings(
        base, mw34::campaign::resolve_mission_lighting("c3m3"), true, false);
    // Isolate distance haze from weather effects, keeping the real campaign haze/sky settings.
    campaign.dust_intensity = campaign.valley_fog_density = campaign.heat_shimmer = 0;
    campaign.rain_wetness = campaign.lava_glow = 0;
    constexpr std::array<float, 3> authored{.125f, .125f, .188f};
    require(mw34::sun::fog_color(base, authored) == authored,
            "Lighting without an atmosphere profile changed the ZBD colour");
    const auto haze = reference_haze_color(campaign, {0, 0, 1});
    require(campaign.haze_manual && campaign.haze_color == std::array<float, 3>{.42f, .25f, .22f},
            "c3m3 campaign haze fixture changed");
    for (bool lighting_on : {false, true}) {
        auto settings = campaign;
        settings.enabled = lighting_on;
        vk::Renderer renderer(vk::Renderer::ColorTarget::rgba8, {}, {1, 1, 1, false}, true, settings);
        const auto selected = mw34::sun::fog_color(settings, authored);
        require(selected == (lighting_on ? campaign.haze_color : authored),
                "Campaign lighting colour selection lost its ZBD fallback");
        std::uint16_t full_fog_pixel = 0;
        std::uint64_t expected_haze_draws = 0;
        for (float fraction : {.4f, .7f, 1.f}) {
            cc::geometry::Fog fog;
            fog.enabled = true;
            fog.near_range = 48;
            fog.inverse_range = 1.f / 1077.f;
            fog.low_altitude = 80;
            fog.inverse_altitude = 1.f / 20.f;
            fog.edge_start = 1050;
            fog.edge_inverse_range = 1.f / 150.f;
            const float distance = fog.near_range + fraction * 1077.f;
            const float amount = cc::geometry::fog_amount(fog, distance, 1.f);
            require(std::abs(amount - fraction) < 2e-6f,
                    "Proportional haze did not retain its linear density");
            vk::Scene scene{};
            scene.width = scene.height = 32;
            scene.has_depth = true;
            scene.color.resize(32 * 32);
            scene.depth.resize(32 * 32);
            scene.clears.push_back({3, {authored[0], authored[1], authored[2], 1}, 0,
                                    {{{0, 0}, {32, 32}}}});
            scene.order.push_back({true, 0});
            const auto visibility = std::uint32_t(std::lround((1.f - amount) * 255.f)) << 24;
            const platform::TLVertex vertices[]{
                {0, 0, .5f, .5f, 0xff000000, visibility, 0, 0},
                {32, 0, .5f, .5f, 0xff000000, visibility, 0, 0},
                {32, 32, .5f, .5f, 0xff000000, visibility, 0, 0},
                {0, 0, .5f, .5f, 0xff000000, visibility, 0, 0},
                {32, 32, .5f, .5f, 0xff000000, visibility, 0, 0},
                {0, 32, .5f, .5f, 0xff000000, visibility, 0, 0}};
            const auto *bytes = reinterpret_cast<const unsigned char *>(vertices);
            scene.vertices.assign(bytes, bytes + sizeof vertices);
            vk::Draw draw{};
            draw.count = 6;
            draw.texture = -1;
            draw.key = {0, 5, 6, 1, 7, 1, 1, 0};
            draw.push.target[0] = draw.push.target[1] = 32;
            draw.push.target[2] = .5f;
            std::copy(authored.begin(), authored.end(), draw.push.fog);
            draw.push.mode[0] = 2U | 16U;
            draw.push.mode[1] = draw.push.mode[2] = 2U;
            draw.scissor = {{0, 0}, {32, 32}};
            auto view = std::make_shared<mw34::sun::Tl>();
            view->camera_world = {1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0};
            view->projection = {1, 16, 16, 16, 16, 800};
            draw.sun_tl = view;
            scene.draws.push_back(draw);
            scene.order.push_back({false, 0});
            renderer.render(scene);
            if (lighting_on) ++expected_haze_draws;
            require(std::equal(selected.begin(), selected.end(), scene.draws[0].push.fog),
                    "Atmosphere did not apply the campaign/ZBD colour to push.fog");
            require(renderer.haze_draws == expected_haze_draws,
                    "Campaign haze draw routing changed");
            const auto pixel = scene.color[16 * 32 + 16];
            const std::array<float, 3> rgb{float((pixel >> 11) & 31) / 31.f,
                                          float((pixel >> 5) & 63) / 63.f, float(pixel & 31) / 31.f};
            for (unsigned channel = 0; channel < 3; ++channel) {
                const float expected = (lighting_on ? haze[channel] : authored[channel]) * amount;
                // One 5-bit step + sky dither (half a 5-bit step), RGBA8 rounding,
                // and the vertex visibility byte together fit inside .055 linear RGB.
                require(std::abs(rgb[channel] - expected) < .055f,
                        "Fogged pixel differs from CPU hazeColor/amount beyond dither precision");
            }
            if (lighting_on && fraction == 1.f) {
                full_fog_pixel = pixel;
                // At view.y == 0 < horizon_low, the actual dome must equal full haze.
                scene.draws[0].sky = 1;
                renderer.render(scene);
                require(scene.color[16 * 32 + 16] == full_fog_pixel,
                        "Fully fogged geometry did not match the below-horizon dome");
            }
        }
    }
}

// Each scene samples a small patch around the given sightline. Reversed
// depth represents forward depth; deliberately unrelated texture RHWs prove
// the range test uses the position, including on legacy clip-fallback TL.
void check_radial_world_visibility() {
    namespace vk = mw34::vkscene;
    constexpr unsigned width = 640, height = 480;
    constexpr unsigned range = 1600;
    enum class Sample { world, sky, haze, crossing, layered, zoom };
    std::vector<std::uint16_t> reference_color, reference_depth;
    for (const unsigned scale : {100u, 75u}) {
        cc_mw3_re::RendererBridgeConfig config;
        config.draw_distance = range;
        config.remaster_width = width;
        config.remaster_height = height;
        config.world_scale_percent = scale;
        vk::Renderer renderer(vk::Renderer::ColorTarget::rgba8, {}, {1,1,1,false},
                              false, {}, false, config);
        auto sample = [&](float radius, float angle, Sample sample = Sample::world) {
            vk::Scene scene{};
            scene.width = width;
            scene.height = height;
            scene.has_depth = true;
            scene.color.assign(width * height, 0x001f);
            scene.depth.resize(width * height);
            if (sample == Sample::zoom)
                for (std::size_t i = 0; i < scene.color.size(); ++i)
                    scene.color[i] = i % width < width/2 ? 0x07e0 : 0x001f;
            // Start with a resident backdrop. A subsequent opaque batch
            // exercises the actual high-resolution coverage replay at 75%.
            renderer.render(scene, true, false);
            vk::Draw draw{};
            draw.count = 6;
            draw.texture = -1;
            draw.key = {0, 5, 6, 1, 7, 1, 1, 0};
            draw.push.target[0] = width;
            draw.push.target[1] = height;
            draw.push.target[2] = .5f;
            draw.push.mode[0] = 2;
            draw.push.mode[1] = draw.push.mode[2] = 2;
            draw.scissor = {{0,0}, {width,height}};
            draw.native_sky = sample == Sample::sky;
            draw.sky = sample == Sample::haze ? 3 : 0;
            auto& view = draw.producer_view;
            view.present = true;
            view.purpose = ::platform::ProducerPurpose::MainWorld;
            view.canvas_available = true;
            view.canvas = {0, 0, width, height};
            if (sample == Sample::zoom) {
                view.purpose = ::platform::ProducerPurpose::WorldZoom;
                view.camera_rect_available = true;
                view.camera_rect = {int(width/4), int(height/4), int(width/2), int(height/2)};
                draw.scissor = {{int(width/4), int(height/4)}, {width/2, height/2}};
            }
            auto& projection = view.projection;
            projection.near_z = 8;
            projection.fx_near = projection.fy_near = (sample == Sample::crossing || sample == Sample::layered) ? 20.f : 100000.f;
            projection.cx = width * .5f - std::tan(angle) * projection.fx_near * projection.near_z;
            projection.cy = height * .5f;
            const float depth = projection.near_z / (radius * std::cos(angle));
            const auto vertex = [depth](float x, float y, float rhw) {
                return ::platform::TLVertex{x, y, depth, rhw, 0xffff0000, 0, 0, 0};
            };
            ::platform::TLVertex vertices[]{vertex(-1,-1,.4f), vertex(width,-1,.8f),
                    vertex(width,height,.25f), vertex(-1,-1,.4f), vertex(width,height,.25f),
                    vertex(-1,height,.5f)};
            auto append = [&](bool sky, float z, std::uint32_t color) {
                auto layer = draw;
                layer.native_sky |= sky;
                layer.first = unsigned(scene.vertices.size() / sizeof(::platform::TLVertex));
                for (auto &v : vertices) {
                    v.sz = z;
                    v.diffuse = color;
                }
                const auto *bytes = reinterpret_cast<const unsigned char *>(vertices);
                scene.vertices.insert(scene.vertices.end(), bytes, bytes + sizeof(vertices));
                scene.order.push_back({false, unsigned(scene.draws.size())});
                scene.draws.push_back(layer);
            };
            if (sample == Sample::layered) {
                append(true, depth * .25f, 0xff00ff00);   // Two different authored sky regions.
                scene.draws.back().scissor = {{0, 0}, {width/2, height}};
                append(true, depth * .25f, 0xff0000ff);
                scene.draws.back().scissor = {{int(width/2), 0}, {width/2, height}};
                append(false, depth * .95f, 0xffffff00);  // A farther yellow surface.
            }
            append(false, depth, 0xffff0000);
            renderer.render(scene, false, false);
            renderer.fetch_resident(scene);
            unsigned drawn = 0;
            for (std::size_t i = 0; i < scene.depth.size(); ++i) {
                if (sample == Sample::zoom) {
                    const unsigned x = unsigned(i % width), y = unsigned(i / width);
                    const bool inside = x >= width/4 && x < 3*width/4 && y >= height/4 && y < 3*height/4;
                    const auto color = scene.color[i];
                    if (inside) {
                        ++drawn;
                        require(scene.depth[i] && ((color >> 11) == 3 || (color >> 11) == 4) &&
                            (x < width/2 ? ((color >> 5) & 63) >= 54 && !(color & 31) :
                                           (color & 31) >= 27 && !(color & 0x07e0)),
                            "Zoom fade did not sample its retained scissor backdrop");
                    } else {
                        require(!scene.depth[i] && color == (x < width/2 ? 0x07e0 : 0x001f),
                                "Zoom backdrop changed pixels outside its scissor");
                    }
                } else if (sample == Sample::layered) {
                    const float x = float(i % width) - projection.cx;
                    const float y = float(i / width) - projection.cy;
                    const float r = std::hypot(radius, x / (depth * projection.fx_near),
                                                       y / (depth * projection.fy_near));
                    const float fade = std::clamp((r / range - .8f) / .2f, 0.f, 1.f);
                    const float remaining = 1.f - fade * fade * (3.f - 2.f * fade);
                    const bool green = i % width < width/2;
                    const auto color = scene.color[i];
                    if (!(std::abs(int(color >> 11) - remaining * 31.f) <= 1.01f &&
                            std::abs(int((color >> 5) & 63) - (green ? (1.f - remaining) * 63.f : 0.f)) <= 1.01f &&
                            std::abs(int(color & 31) - (green ? 0.f : (1.f - remaining) * 31.f)) <= 1.01f)) {
                        std::fprintf(stderr, "range fixture scale=%u pixel=%zu,%zu color=%x expected=%.3f depth=%u r=%.2f\n",
                                     scale,i%width,i/width,color,remaining,scene.depth[i],r);
                        require(false, "World sample did not fade continuously against its own sky pixel");
                    }

                    const auto foreground = scene.depth[(height / 2) * width + width / 2];
                    const auto background = scene.depth[0];
                    require(foreground > background && background > 0, "Layered sky depth was lost");
                    if (std::abs(r - range) > .01f)
                        require(std::abs(int(scene.depth[i]) - int(r < range ? foreground : background)) <= 1,
                                "Smooth world fade wrote incorrect depth");
                    drawn += r < range;
                } else if (scene.depth[i]) {
                    ++drawn;
                    require(scene.color[i] == 0xf800, "Admitted world sample lost its surface color");
                } else {
                    require(scene.color[i] == 0x001f, "Culled world sample changed backdrop");
                }
            }
            if (sample == Sample::layered) {
                require(drawn > 0 && drawn < scene.depth.size(), "Layered fixture missed the fade boundary");
                if (scale == 100) {
                    reference_color = scene.color;
                    reference_depth = scene.depth;
                } else {
                    require(scene.color == reference_color && scene.depth == reference_depth,
                            "Reduced coverage changed color or depth along a varying radial boundary");
                }
            }
            if (sample == Sample::crossing) {
                require(scene.depth[(height / 2) * width + width / 2] && scene.depth[0] == 0,
                        "Triangle with distant vertices lost its in-range interior");
            }
            return drawn;
        };
        for (float angle : {0.f, .7f}) {
            require(sample(1150, angle) == width * height, "Near terrain lost radial coverage");
            const unsigned retained = sample(1530, angle);
            require(retained >= width * height * .115f && retained <= width * height * .135f, "1530 m coverage should be about 12 percent");
            require(sample(1620, angle) == 0, "Beyond-range world geometry still writes depth");
        }
        require(sample(1800, .7f, Sample::sky) == width * height, "Native sky acquired a scenery cutoff");
        require(sample(1800, .7f, Sample::haze) == 0,
                "Haze-routed scenery beyond the radial range remained visible");
        sample(1000, 0, Sample::crossing);
        sample(1000, 0, Sample::layered);
        require(sample(1530, 0, Sample::zoom) == width * height / 4, "Zoom scissor lost coverage");
        require(scale == 100 || renderer.coverage_scenes > 0, "Reduced world coverage pass was skipped");
        vk::Scene resized{};
        resized.width = resized.height = 32;
        resized.has_depth = true;
        resized.color.resize(32 * 32);
        resized.depth.resize(32 * 32);
        renderer.render(resized);
        sample(1000, 0, Sample::layered);  // Recreate both the guest and private targets.

    }
}

// Exercise the actual model submission boundary, including the reference TL
// fallback. A camera plane beyond 800 m isolates radial discard from clipping.
void check_radial_model_views(SDL_Window *window, sdlfe::RendererBackend backend) {
    const float positions[]{-500,-500,0, 500,-500,0, 0,500,0};
    const std::uint32_t indices[]{2,1,0};
    const auto resource = cc::geometry::register_resource(
        positions, 3, nullptr, 0, {{3, indices, nullptr, nullptr, false, true}});
    cc::geometry::Material material;
    material.color = 0xffff0000;
    for (const char *mode : {"partial", "cpu-reference"}) {
        sdlfe::CoreCriticalAssets assets;
        assets.geometry = mode;
        auto renderer = make_check_renderer(window, backend, {}, assets);
        renderer->set_viewport(0, 0, 32, 32);
        auto sample = [&](float distance, platform::ProducerPurpose purpose) {
            std::array<float,12> camera{1,0,0, 0,1,0, 0,0,1, 0,0,distance};
            platform::ModelDrawContext context;
            context.model_to_camera = context.model_to_world = camera.data();
            context.ordinary = true;
            context.near_z = context.clip_near = 1;
            context.far_z = 1000;
            context.fx_near = context.fy_near = context.cx = context.cy = 16;
            const zvid::ProducerPurposeScope requested(purpose);
            zvid::ProducerWorldScope world;
            world.begin_emission();
            auto view = zvid::capture_producer_view();
            if (purpose != platform::ProducerPurpose::Original) {
                view.canvas_available = true;
                view.canvas = {0, 0, 32, 32};
                view.projection.near_z = 1;
                view.projection.fx_near = view.projection.fy_near = 16;
                view.projection.cx = view.projection.cy = 16;
            }
            renderer->begin_scene();
            renderer->clear(true, 0, 0, 255);
            {
                const zvid::ProducerBindingScope binding(renderer.get(), view);
                require(renderer->submit_model_geometry(resource, context, {material}, {}) ==
                        cc::geometry::Submission::submitted, "Radial model fixture was rejected");
            }
            renderer->end_scene();
            std::vector<std::uint32_t> pixels;
            int width{}, height{};
            require(renderer->read_back(&pixels, &width, &height) && width == 32 && height == 32,
                    "Radial model readback failed");
            return pixels[16 * 32 + 16] & 0xffffffu;
        };
        for (auto purpose : {platform::ProducerPurpose::MainWorld, platform::ProducerPurpose::WorldZoom}) {
            require(sample(560, purpose) == 0xff0000, "Near typed world model was lost");
            require(sample(840, purpose) == 0x0000ff, "Distant typed world model wrote over the backdrop");
        }
        require(sample(840, platform::ProducerPurpose::Original) == 0xff0000,
                "Untyped nested model acquired the world range");
    }
}

void check_distance_fog(SDL_Window *window, sdlfe::RendererBackend backend) {
    const auto saved_fog = zmod::fog();
    const auto saved_calc = zmod::fog_calc();
    zmod::fog_calc() = {};
    zmod::fog_calc().camera_to_world[1][1] = 1.f;
    // All three vertices have horizontal radius 1 (the base uses a 3-4-5 triangle).
    // Scaling the camera transform therefore gives constant fog over the whole triangle,
    // allowing an independent numerical pixel check rather than just GPU/reference agreement.
    const float positions[]{-.6f, -.6f, .8f, .6f, -.6f, .8f, 0.f, .6f, 1.f};
    const std::uint32_t indices[]{2, 1, 0};
    const auto source = cc::geometry::register_resource(
        positions, 3, nullptr, 0, {{3, indices, nullptr, nullptr, false, true}});
    cc::geometry::Material material;
    material.color = 0xff000000;
    constexpr float fractions[]{.4f, .7f, .95f, 1.f};
    constexpr float mission_density[]{288.f / 718.f, 528.f / 718.f, 1.f, 1.f};
    constexpr float edge_at_95[]{.6f, .6f, 7.f / 15.f, .2f, 0.f};
    std::vector<std::uint32_t> gpu_pixels;
    for (bool cpu_reference : {false, true}) {
        sdlfe::CoreCriticalAssets options;
        options.geometry = cpu_reference ? "cpu-reference" : "partial";
        auto renderer = make_check_renderer(window, backend, {}, options);
        renderer->set_viewport(0, 0, 32, 32);
        std::size_t pixel_sample = 0;
        for (bool altitude_band : {false, true}) {
            for (bool mission_on : {false, true}) {
                zmod::fog() = {};
                zmod::fog_set_on(mission_on);
                zmod::fog_set_linear(1);
                zmod::fog_set_near(32.f);
                zmod::fog_set_far(750.f);
                zmod::fog_set_alt_low(altitude_band ? 80.f : 1000.f);
                zmod::fog_set_alt_high(altitude_band ? 100.f : 1001.f);
                for (std::size_t option_index = 0;
                     option_index < std::size(zcls::kViewDistanceOptions); ++option_index) {
                    const float view_distance =
                        float(zcls::kViewDistanceOptions[option_index].view_distance);
                    zmod::ScopedRenderFog scope(800.f, view_distance);
                    const auto &render = zmod::render_fog();
                    const auto edge = zmod::render_fog_edge();
                    cc::geometry::Fog fog;
                    fog.enabled = mission_on;
                    fog.color = {1, 1, 1};
                    fog.near_range = render.near_range;
                    fog.inverse_range = render.inv_range;
                    fog.low_altitude = render.alt_low;
                    fog.inverse_altitude = render.inv_alt;
                    fog.edge_start = edge.start;
                    fog.edge_inverse_range = edge.inverse_range;
                    for (std::size_t sample = 0; sample < std::size(fractions); ++sample) {
                        const float distance = view_distance * fractions[sample];
                        const float expected_edge = sample == 3 ? 1.f :
                            (sample == 2 ? edge_at_95[option_index] : 0.f);
                        for (float height : {1.f, 500.f}) {
                            const float mission = mission_on && (!altitude_band || height < 80.f)
                                                      ? mission_density[sample] : 0.f;
                            const float expected = 1.f - (1.f - mission) * (1.f - expected_edge);
                            const float vertex[]{0.f, height, distance};
                            require(std::abs(zmod::fog_at(vertex) - expected) < 2e-6f &&
                                        std::abs(cc::geometry::fog_amount(fog, distance, height) -
                                                 expected) < 2e-6f,
                                    "CPU/reference distance fog differs from the numerical fixture");
                            std::array<float, 12> camera{distance, 0, 0, 0, distance, 0,
                                                         0, 0, distance, 0, 0, 0};
                            std::array<float, 12> world{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, height, 0};
                            platform::ModelDrawContext context;
                            context.model_to_camera = camera.data();
                            context.model_to_world = world.data();
                            context.ordinary = true;
                            context.near_z = context.clip_near = 1;
                            context.far_z = view_distance + 1;
                            context.fx_near = context.fy_near = 16;
                            context.cx = context.cy = 16;
                            renderer->begin_scene();
                            // Magenta makes a missing/culled black triangle fail at amount zero.
                            renderer->clear(true, 255, 0, 255);
                            require(renderer->submit_model_geometry(source, context, {material}, fog) ==
                                        cc::geometry::Submission::submitted,
                                    "Distance fog geometry was not submitted");
                            renderer->end_scene();
                            std::vector<std::uint32_t> pixels;
                            int width{}, height_pixels{};
                            require(renderer->read_back(&pixels, &width, &height_pixels) &&
                                        width == 32 && height_pixels == 32,
                                    "Distance fog readback extent changed");
                            const auto pixel = pixels[16 * 32 + 16];
                            for (unsigned shift : {0U, 8U, 16U})
                                require(std::abs(float((pixel >> shift) & 255) - expected * 255.f) <= 8.f,
                                        "GPU/reference fog amount differs beyond RGB565 precision");
                            if (!cpu_reference)
                                gpu_pixels.push_back(pixel);
                            else {
                                for (unsigned shift : {0U, 8U, 16U})
                                    require(std::abs(int((pixel >> shift) & 255) -
                                                     int((gpu_pixels.at(pixel_sample) >> shift) & 255)) <= 8,
                                            "GPU/reference distance fog pixel mismatch");
                            }
                            ++pixel_sample;
                        }
                    }
                }
            }
        }
        require(pixel_sample == 160, "Distance fog fixture lost a scenario");
        // Unequal radii and depths expose endpoint clamping: the old edge factors
        // are 0/0/1, giving about half fog where the triangle reaches z == 3200.
        const float crossing_positions[]{-500, -100, 3000, 500, -100, 3000, 0, 100, 3400};
        const auto crossing = cc::geometry::register_resource(
            crossing_positions, 3, nullptr, 0, {{3, indices, nullptr, nullptr, false, true}});
        std::array<float, 12> camera{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};
        std::array<float, 12> world{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 500, 0};
        zmod::fog() = {};
        zmod::ScopedRenderFog scope(800, 3200);
        cc::geometry::Fog edge;
        edge.color = {1, 1, 1};
        edge.edge_start = 3050;
        edge.edge_inverse_range = 1.f / 150.f;
        std::vector<cc::geometry::ReferenceVertex> triangle(3);
        for (unsigned index = 0; index < 3; ++index) {
            auto &vertex = triangle[index];
            std::copy_n(crossing_positions + index * 3, 3, vertex.camera.begin());
            vertex.fog = cc::geometry::fog_factors(
                edge, std::hypot(vertex.camera[0], vertex.camera[2]), vertex.camera[1] + 500);
        }
        const auto clipped = cc::geometry::clip_reference(triangle, 3200, false);
        unsigned cut_vertices = 0;
        for (const auto &vertex : clipped) {
            if (vertex.camera[2] != 3200) continue;
            require(cc::geometry::fog_amount(vertex.fog) == 1.f &&
                        zmod::fog_at(vertex.camera.data()) == 1.f,
                    "Crossing GPU-reference/CPU cut vertices retained visibility");
            ++cut_vertices;
        }
        require(cut_vertices == 2, "Crossing fog fixture lost its cut vertices");
        platform::ModelDrawContext context;
        context.model_to_camera = camera.data();
        context.model_to_world = world.data();
        context.ordinary = true;
        context.near_z = context.clip_near = 1;
        context.far_z = 3200;
        context.fx_near = 64;
        // Magnify the y direction so row 15 is just inside the clipped edge.
        context.fy_near = 3200;
        context.cx = context.cy = 16;
        renderer->begin_scene();
        renderer->clear(true, 255, 0, 255);
        require(renderer->submit_model_geometry(crossing, context, {material}, edge) ==
                    cc::geometry::Submission::submitted,
                "Crossing fog geometry was not submitted");
        renderer->end_scene();
        std::vector<std::uint32_t> pixels;
        int width{}, height{};
        require(renderer->read_back(&pixels, &width, &height) && width == 32 && height == 32,
                "Crossing fog readback extent changed");
        for (unsigned shift : {0U, 8U, 16U})
            require(((pixels[15 * 32 + 16] >> shift) & 255) >= 247,
                    "Crossing GPU/reference triangle exposed the far cut");

        // The far cut must not spread fog into the interior before the edge band.
        // On the centreline y = (z - 2200) / 1200. This projection puts z == 2100
        // at pixel (16, 16); packed endpoint visibility incorrectly fogs that pixel.
        const float interior_positions[]{-1, -1, 1000, 1, -1, 1000, 0, 1, 3400};
        const auto interior = cc::geometry::register_resource(
            interior_positions, 3, nullptr, 0, {{3, indices, nullptr, nullptr, false, true}});
        context.fx_near = context.fy_near = 16000;
        context.cx = 16.5f;
        context.cy = 16.5f + 16000.f / 25200.f;
        require(cc::geometry::fog_amount(edge, 2100.f, 500.f - 1.f / 12.f) == 0.f,
                "Interior fog fixture is not before the edge band");
        renderer->begin_scene();
        renderer->clear(true, 255, 0, 255);
        require(renderer->submit_model_geometry(interior, context, {material}, edge) ==
                    cc::geometry::Submission::submitted,
                "Interior fog geometry was not submitted");
        renderer->end_scene();
        require(renderer->read_back(&pixels, &width, &height) && width == 32 && height == 32,
                "Interior fog readback extent changed");
        require((pixels[16 * 32 + 16] & 0xffffffU) == 0,
                "GPU/reference interior pixel acquired fog before the edge band");
    }
    zmod::fog() = saved_fog;
    zmod::fog_calc() = saved_calc;
}

void check_strict_geometry(SDL_Window *window, sdlfe::RendererBackend backend) {
    sdlfe::CoreCriticalAssets options;
    options.geometry = "gpu";
    auto renderer = make_check_renderer(window, backend, {}, options);
    renderer->set_viewport(0, 0, 32, 32);
    renderer->begin_scene();
    renderer->clear(true, 0, 0, 0);
    for (bool overlay : {false, true}) {
        platform::DrawState state;
        state.depth_always = overlay;
        bool rejected = false;
        try {
            quad(*renderer, 4, 28, .5f, 0xffff0000, state);
        } catch (const std::runtime_error &error) {
            rejected = std::string_view(error.what()).find("Strict GPU geometry: CPU 3D draw") == 0;
        }
        require(rejected, "Strict mode silently admitted CPU geometry or a 3D overlay");
    }
    platform::DrawState hud;
    hud.sharp = hud.depth_always = true;
    hud.depth_write = false;
    quad(*renderer, 4, 28, 0, 0xff00ff00, hud);
    renderer->end_scene();
    std::vector<std::uint32_t> pixels;
    int width{}, height{};
    require(renderer->read_back(&pixels, &width, &height) && width == 32 && height == 32 &&
                pixels[16 * 32 + 16] == 0xff00ff00,
            "Strict mode lost the permitted output-resolution HUD");
    require(renderer->geometry_statistics().cpu_draw_calls == 2,
            "Residual CPU draw attempts were not reported");
}

std::vector<std::vector<std::uint32_t>> check_native_geometry(SDL_Window *window,
                                                              sdlfe::RendererBackend backend,
                                                              bool cpu_reference = false) {
    sdlfe::CoreCriticalAssets options;
    options.geometry = cpu_reference ? "cpu-reference" : "partial";
    auto renderer = make_check_renderer(window, backend, {}, options);
    renderer->set_viewport(0, 0, 32, 32);
    std::array<float, 12> matrix{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};
    platform::ModelDrawContext context;
    context.model_to_camera = context.model_to_world = matrix.data();
    context.ordinary = true;
    context.near_z = context.clip_near = 1;
    context.far_z = 10;
    context.fx_near = context.fy_near = 16;
    context.cx = context.cy = 16;
    float positions[]{-1, -1, 3, 1, -1, 3, 0, 1, 3};
    std::uint32_t indices[]{2, 1, 0};
    bool two_sided = false;
    const auto make = [&] {
        return cc::geometry::register_resource(positions, 3, nullptr, 0,
                                               {{3, indices, nullptr, nullptr, false, two_sided}});
    };
    auto source = make();
    cc::geometry::Material material;
    material.color = 0xffff0000;
    for (float weight : {-.1f, std::numeric_limits<float>::quiet_NaN(),
                         std::numeric_limits<float>::infinity(),
                         -std::numeric_limits<float>::infinity(), 1.1f}) {
        context.damage_tint_weight = weight;
        bool rejected = false;
        try {
            renderer->submit_model_geometry(source, context, {material}, {});
        } catch (const std::runtime_error &error) {
            rejected = std::string_view(error.what()) == "Model has an invalid native tint weight";
        }
        require(rejected, "Native geometry adapter accepted an invalid tint weight");
    }
    for (float channel : {-.1f, std::numeric_limits<float>::quiet_NaN(),
                          std::numeric_limits<float>::infinity(), 1.1f}) {
        context.damage_tint_rgb[1] = channel;
        bool rejected = false;
        try {
            renderer->submit_model_geometry(source, context, {material}, {});
        } catch (const std::runtime_error &error) {
            rejected = std::string_view(error.what()) == "Model has an invalid native tint color";
        }
        require(rejected, "Native geometry adapter accepted an invalid tint color");
    }
    context.damage_tint_rgb[1] = 0.f;
    context.damage_tint_weight = 0.f;
    const auto frame = [&](const cc::geometry::Fog &fog = cc::geometry::Fog{}) {
        renderer->begin_scene();
        renderer->clear(true, 0, 0, 0);
        require(renderer->submit_model_geometry(source, context, {material}, fog) ==
                    cc::geometry::Submission::submitted,
                "Authored native geometry rejected");
        renderer->end_scene();
        std::vector<std::uint32_t> pixels;
        int width{}, height{};
        require(renderer->read_back(&pixels, &width, &height) && width == 32 && height == 32,
                "Native geometry readback changed dimensions");
        return pixels;
    };
    const auto first = frame();
    require(std::count_if(first.begin(), first.end(),
                          [](auto p) { return (p & 0x00ff0000) > 0x00800000; }) > 10,
            "Indexed native GPU geometry produced no red pixels");
    material.color = 0xffffffff;
    const auto untinted_white = frame();
    context.damage_tint_rgb[0] = 0.f;
    context.damage_tint_rgb[1] = 1.f;
    context.damage_tint_rgb[2] = 0.f;
    context.damage_tint_weight = .3f;
    const auto green_tint = frame();
    context.damage_tint_rgb[0] = 1.f;
    context.damage_tint_rgb[1] = 0.f;
    const auto red_tint = frame();
    unsigned green_witnesses = 0;
    for (std::size_t index = 0; index < untinted_white.size(); ++index) {
        if (!(untinted_white[index] & 0x00ffffff))
            continue;
        require(green_tint[index] != untinted_white[index] &&
                    green_tint[index] != red_tint[index],
                "Green tint did not differ from untinted and red tint pixels");
        require(((green_tint[index] >> 8) & 255) > ((green_tint[index] >> 16) & 255),
                "Green tint pixel did not retain green greater than red");
        ++green_witnesses;
    }
    require(green_witnesses > 10, "Green tint rendered no useful geometry witness");
    context.damage_tint_weight = 0.f;
    context.damage_tint_rgb[0] = context.damage_tint_rgb[1] = 0.f;
    material.color = 0xffff0000;
    require(frame() == first &&
                renderer->asset_statistics().geometry_uploads == (cpu_reference ? 0 : 1),
            "Immutable native geometry changed or reuploaded every frame");
    matrix[9] = .75f;
    const auto moved = frame();
    require(moved != first &&
                renderer->asset_statistics().geometry_uploads == (cpu_reference ? 0 : 1),
            "GPU instance transform was ignored or rebuilt vertices");
    matrix[9] = 0;
    cc::geometry::Fog fog;
    fog.enabled = true;
    fog.inverse_range = 1;
    fog.low_altitude = 10;
    fog.inverse_altitude = 1;
    fog.color = {0, 0, 1};
    const auto fogged = frame(fog);
    require(std::count_if(fogged.begin(), fogged.end(), [](auto p) { return (p & 255) > 128; }) >
                10,
            "Vertex fog was not evaluated on the GPU");
    positions[2] = .25f;
    source = make();
    const auto clipped = frame();
    require(std::count_if(clipped.begin(), clipped.end(),
                          [](auto p) { return (p & 0x00ff0000) > 0x00800000; }) > 0,
            "Near-plane crossing was dropped instead of GPU-clipped");
    context.clip_near = 4;
    const auto near_rejected = frame();
    require(std::none_of(near_rejected.begin(), near_rejected.end(),
                         [](auto p) { return (p & 0x00ffffff) != 0; }),
            "View near plane distinct from projection near scale was ignored");
    context.clip_near = 1;
    positions[2] = positions[5] = positions[8] = 20;
    source = make();
    const auto far = frame();
    require(std::none_of(far.begin(), far.end(), [](auto p) { return (p & 0x00ffffff) != 0; }),
            "Hardware far clipping was omitted");
    const auto statistics = renderer->geometry_statistics();
    require(statistics.submitted_models == 10 && !statistics.unsupported_models &&
                (cpu_reference ? renderer->asset_statistics().cpu_clipped_triangles > 0
                               : renderer->asset_statistics().cpu_clipped_triangles == 0),
            "Native indexed geometry used an unreported CPU route");
    if (!cpu_reference)
        require(renderer->asset_statistics().retired_geometry_buffers >= 2,
                "Expired native GPU resources were not retired after completion");
    renderer.reset();
    options.geometry_debug_normals = true;
    renderer = make_check_renderer(window, backend, {}, options);
    renderer->set_viewport(0, 0, 32, 32);
    positions[2] = positions[5] = positions[8] = 3;
    two_sided = true;
    source = make();
    const auto normal_debug = frame();
    require(normal_debug != first &&
                std::count_if(normal_debug.begin(), normal_debug.end(),
                              [](auto p) { return ((p >> 8) & 255) > 100; }) > 10,
            "GPU normal debug view was not evaluated");
    const auto front_normal = normal_debug[16 * 32 + 16];
    require(((front_normal >> 16) & 255) > 100 && ((front_normal >> 8) & 255) > 100 &&
                (front_normal & 255) < 10,
            "Two-sided front normal points away from the camera");
    std::swap(indices[0], indices[1]);
    source = make();
    const auto back_normal = frame();
    require(back_normal == normal_debug, "Two-sided back normal did not face the viewer");
    std::printf("Native %s transforms, fog and near/far clipping pass\n",
                cpu_reference ? "CPU reference" : "indexed GPU");
    return {first, moved, fogged, clipped, near_rejected, far, normal_debug, back_normal};
}
