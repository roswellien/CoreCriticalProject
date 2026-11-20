void check_gpu_donor_toes(SDL_Window *window, sdlfe::RendererBackend backend) {
    const auto folder = std::filesystem::temp_directory_path() /
        ("cc-gpu-donor-toes-" + std::to_string(SDL_GetPerformanceCounter()));
    require(std::filesystem::create_directory(folder), "Donor GPU fixture directory exists");
    struct Files {
        std::filesystem::path folder;
        ~Files() {
            std::error_code error;
            for (const char *name : {"mesh.bin", "textures.bin", "normals.bin", "materials.bin"})
                std::filesystem::remove(folder / name, error);
            std::filesystem::remove(folder, error);
        }
    } files{folder};
    const auto bytes = prepared_fixture::build_valid_v4_mesh("rtoe02", "control", "panel", .6);
    std::istringstream input(bytes, std::ios::binary);
    const auto mesh = platform::prepared::read_mesh(input);
    const auto mesh_hash = mw34::materials::compute_mesh_uv_hash(mesh.batches, 0, 1);
    std::ofstream(folder / "mesh.bin", std::ios::binary) << bytes;
    std::ofstream(folder / "textures.bin", std::ios::binary) << prepared_fixture::textures();
    std::ofstream(folder / "normals.bin", std::ios::binary) << prepared_fixture::normals(0xffd980d9);
    std::ofstream(folder / "materials.bin", std::ios::binary)
        << prepared_fixture::donor_materials(mesh_hash);
    require(SDL_SetWindowSize(window, 64, 64) && SDL_SyncWindow(window), SDL_GetError());
    std::array<std::vector<std::uint32_t>, 4> reference;
    unsigned cases = 0;
    auto same_pixels = [&](const auto &actual, const auto &expected) {
        require(actual.size() == expected.size(), "Donor comparison lost pixels");
        for (std::size_t i = 0; i < actual.size(); ++i)
            for (unsigned shift : {0U, 8U, 16U})
                require(std::abs(int((actual[i] >> shift) & 255) -
                                 int((expected[i] >> shift) & 255)) <= 2,
                        "Donor source/route pixels differ from full-source reference");
        ++cases;
    };
    for (const char *mode : {"cpu-reference", "partial"}) {
        sdlfe::CoreCriticalAssets assets;
        assets.geometry = mode;
        assets.lighting = "normal";
        assets.pom = true;
        assets.models.push_back({"authored", "1", (folder / "mesh.bin").u8string(),
                                 (folder / "textures.bin").u8string()});
        assets.normals.push_back({"authored", "1", (folder / "normals.bin").u8string()});
        assets.materials.push_back({"authored", "1", (folder / "materials.bin").u8string()});
        auto renderer = make_check_renderer(window, backend, {}, assets);
        renderer->set_viewport(0, 0, 64, 64);
        prepared_fixture::DonorTree distance("rtoe02", false), full("rtoe02", true);
        auto submit = [&](prepared_fixture::DonorTree &tree, bool early, bool reject) {
            const auto raw = tree.raw_state();
            const auto counts = tree.asset->nodes;
            const auto context = tree.context();
            std::fenv_t saved;
            require(std::fegetenv(&saved) == 0, "Cannot save donor caller FP environment");
            struct Restore {
                std::fenv_t &saved;
                ~Restore() { std::fesetenv(&saved); }
            } restore{saved};
            std::feclearexcept(FE_ALL_EXCEPT);
            std::feraiseexcept(FE_DIVBYZERO);
            const auto rounding = std::fegetround();
            std::string failure;
            try {
                if (early)
                    require(renderer->submit_prepared_geometry(context, {}) ==
                                cc::geometry::Submission::submitted,
                            "Donor early prepared route declined a valid rigid batch");
                else {
                    renderer->begin_model_draw(context);
                    require(renderer->replaces_model_geometry(), "Donor draw lost replacement scope");
                }
            } catch (const std::runtime_error &error) { failure = error.what(); }
            const auto flags = std::fetestexcept(FE_ALL_EXCEPT);
            const auto after_rounding = std::fegetround();
            std::fesetenv(&saved);
            renderer->end_model_draw();
            require(flags == FE_DIVBYZERO && after_rounding == rounding,
                    "Donor renderer callback changed original caller FP state");
            require(raw == tree.raw_state() && counts == tree.asset->nodes,
                    "Donor renderer callback mutated original node/data/counts");
            if (reject)
                require(failure.find("mech_authored_1.flt [donor reference 0]: rtoe02 (count 2)") !=
                            std::string::npos,
                        "Donor callback did not reject an ambiguous native toe");
            else if (!failure.empty())
                throw std::runtime_error("Donor callback rejected valid missing-only toe: " + failure);
            ++cases;
        };
        auto render = [&](prepared_fixture::DonorTree &tree, bool early) {
            renderer->clear(true, 0, 0, 0);
            submit(tree, early, false);
            std::vector<std::uint32_t> pixels;
            int width{}, height{};
            require(renderer->read_back(&pixels, &width, &height) && width == 64 && height == 64,
                    "Donor GPU fixture lost its readback extent");
            require(std::any_of(pixels.begin(), pixels.end(),
                               [](auto pixel) { return (pixel & 0xffffff) != 0; }),
                    "Donor witness rendered no model pixels");
            ++cases;
            return pixels;
        };
        for (unsigned pose = 0; pose < 2; ++pose) {
            if (pose) { distance.pose_foot(); full.pose_foot(); }
            for (bool early : {false, true}) {
                const auto complete = render(full, early);
                const auto absent = render(distance, early);
                same_pixels(absent, complete);
                const auto index = pose * 2 + unsigned(early);
                if (std::string_view(mode) == "cpu-reference")
                    reference[index] = complete;
                else
                    same_pixels(absent, reference[index]);
                if (pose)
                    require(absent != reference[unsigned(early)],
                            "Foot pose did not move visible donor pixels");
            }
        }
        const auto statistics = renderer->asset_statistics();
        require(statistics.normal_draws == 8 && statistics.early_prepared_models == 4,
                "Donor source emitted extra/missing batches or lost normal bindings");
        distance.asset->nodes["rtoe02"] = 2;
        for (bool early : {false, true})
            submit(distance, early, true);
    }

    const auto mixed_bytes = prepared_fixture::build_valid_v4_mesh(
        "rtoe02", "control", "panel", .6, 0.2, -0.1, "", true);
    std::istringstream mixed_input(mixed_bytes, std::ios::binary);
    const auto mixed_mesh = platform::prepared::read_mesh(mixed_input);
    require(mixed_mesh.batches.size() == 1 &&
                mixed_mesh.batches[0].donor_bone == 0xffffffff &&
                mixed_mesh.batches[0].donor_indices.size() == 3 &&
                mixed_mesh.batches[0].donor_indices[0] !=
                    mixed_mesh.batches[0].donor_indices[2],
            "Mixed-bone prepared fixture did not encode per-vertex donor bones");
    const auto mixed_mesh_hash =
        mw34::materials::compute_mesh_uv_hash(mixed_mesh.batches, 0, 1);
    std::ofstream(folder / "mesh.bin", std::ios::binary) << mixed_bytes;
    std::ofstream(folder / "materials.bin", std::ios::binary)
        << prepared_fixture::donor_materials(mixed_mesh_hash);
    sdlfe::CoreCriticalAssets mixed_assets;
    mixed_assets.geometry = "partial";
    mixed_assets.lighting = "normal";
    mixed_assets.pom = true;
    mixed_assets.models.push_back({"authored", "1", (folder / "mesh.bin").u8string(),
                                   (folder / "textures.bin").u8string()});
    mixed_assets.normals.push_back({"authored", "1", (folder / "normals.bin").u8string()});
    mixed_assets.materials.push_back({"authored", "1", (folder / "materials.bin").u8string()});
    auto mixed_renderer = make_check_renderer(window, backend, {}, mixed_assets);
    mixed_renderer->set_viewport(0, 0, 64, 64);
    prepared_fixture::DonorTree mixed_distance("rtoe02", false);
    producer_view_checks::Observer mixed_view_observer;
    require(cc_mw3_re::testing::observe_producer_views(*mixed_renderer,
                                                        &mixed_view_observer),
            "Deformed prepared scissor observer unsupported");
    struct MixedProducerViewCleanup {
        cc_mw3_re::VulkanFrameRenderer& renderer;
        ~MixedProducerViewCleanup() noexcept {
            try {
                cc_mw3_re::testing::observe_producer_views(renderer, nullptr);
            } catch (...) {
            }
        }
    } mixed_cleanup{*mixed_renderer};
    mixed_distance.pose_foot();
    mixed_renderer->clear(true, 0, 0, 0);
    const auto fallback_before = mixed_renderer->asset_statistics()
                                     .prepared_cpu_fallback_batches;
    const auto previous_stack = zmth::matrix_stack();
    const auto previous_projection = zmth::projection();
    const auto previous_view = zmth::view();
    const auto previous_draw_state = zmod::draw_state();
    const auto previous_producer_state = zvid::capture_producer_view_state_for_test();
    struct MixedModelStateCleanup {
        zmth::MatrixStack stack;
        zmth::Projection projection;
        zmth::View view;
        zmod::DrawState draw_state;
        zvid::ProducerViewStateForTest producer_view;
        ~MixedModelStateCleanup() {
            zmth::matrix_stack() = stack;
            zmth::projection() = projection;
            zmth::view() = view;
            zmod::draw_state() = draw_state;
            zvid::restore_producer_view_for_test(producer_view);
        }
    } model_state_cleanup{previous_stack, previous_projection, previous_view,
                         previous_draw_state, previous_producer_state};
    const auto previous_renderer = zvid::render3d();
    struct MixedRendererCleanup {
        platform::Render3D* renderer;
        ~MixedRendererCleanup() { zvid::set_render3d(renderer); }
    } renderer_cleanup{previous_renderer};
    zvid::set_render3d(mixed_renderer.get());
    require(zvid::render3d() == mixed_renderer.get(),
            "Mixed-bone production fixture did not install its renderer");
    zmth::Mat34 model_to_world{{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0}};
    zmth::view().view = {{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0}};
    zmth::matrix_stack() = {};
    zmth::matrix_stack().slot[0] = &model_to_world;
    zmth::matrix_stack().slot[1] = &zmth::view().view;
    zmth::matrix_stack().top = 1;
    zmth::projection() = {};
    zmth::projection().near_z = .1f;
    zmth::projection().far_z = 10;
    zmth::projection().fx_near = zmth::projection().fy_near = 50;
    zmth::projection().cx = zmth::projection().cy = 32;
    zmod::draw_state() = {};
    zmod::draw_state().clip.near_z = .1f;
    zvid::set_producer_canvas_rect(10, 20, 128, 64);
    zvid::set_producer_camera_rect(18, 24, 32, 24);
    ::platform::ProducerView expected_mixed_view{};
    // The renderer must receive the producer view around begin_model_draw.
    // Without that binding, the same deformed batch emits with a full-scene
    // scissor even while the producer is inside a WorldZoom emission.
    const auto unbound_fallback_before = mixed_renderer->asset_statistics()
                                             .prepared_cpu_fallback_batches;
    const auto unbound_appends_before = mixed_view_observer.rows(
        producer_view_checks::Stage::append).size();
    {
        zvid::ProducerPurposeScope purpose(::platform::ProducerPurpose::WorldZoom);
        zvid::ProducerWorldScope emission;
        emission.begin_emission();
        const auto context = mixed_distance.context();
        mixed_renderer->begin_model_draw(context);
        require(mixed_renderer->replaces_model_geometry(),
                "Unbound mixed-bone control missed prepared replacement");
        mixed_renderer->end_model_draw();
        emission.end_emission();
    }
    require(mixed_renderer->asset_statistics().prepared_cpu_fallback_batches >
                unbound_fallback_before,
            "Unbound control did not reach the deformed prepared fallback");
    std::vector<std::uint32_t> unbound_pixels;
    int unbound_width{}, unbound_height{};
    require(mixed_renderer->read_back(&unbound_pixels, &unbound_width,
                                      &unbound_height) &&
                unbound_width == 64 && unbound_height == 64,
            "Unbound mixed-bone control lost its readback extent");
    const auto unbound_rows = mixed_view_observer.rows(
        producer_view_checks::Stage::packet, true);
    const auto scissor_failure = [](const char* assertion,
                                    const auto& rows,
                                    std::array<std::int32_t, 2> expected_offset,
                                    std::array<std::uint32_t, 2> expected_extent) {
      std::ostringstream message;
      message << assertion << ": observed_rows=" << rows.size()
              << " expected_offset=(" << expected_offset[0] << ','
              << expected_offset[1] << ") expected_extent=("
              << expected_extent[0] << ',' << expected_extent[1] << ')';
      const auto stage_name = [](producer_view_checks::Stage stage) {
        switch (stage) {
        case producer_view_checks::Stage::exchange: return "exchange";
        case producer_view_checks::Stage::restore: return "restore";
        case producer_view_checks::Stage::append: return "append";
        case producer_view_checks::Stage::local_packet: return "local_packet";
        case producer_view_checks::Stage::packet: return "packet";
        case producer_view_checks::Stage::backend_group: return "backend_group";
        case producer_view_checks::Stage::abandon: return "abandon";
        case producer_view_checks::Stage::reset: return "reset";
        }
        return "unknown";
      };
      const auto purpose_name = [](auto purpose) {
        switch (purpose) {
        case ::platform::ProducerPurpose::Original: return "Original";
        case ::platform::ProducerPurpose::MainWorld: return "MainWorld";
        case ::platform::ProducerPurpose::WorldZoom: return "WorldZoom";
        }
        return "unknown";
      };
      for (std::size_t index = 0; index < rows.size(); ++index) {
        const auto& row = rows[index];
        message << " row[" << index << "]={stage=" << stage_name(row.stage)
                << " packet=" << row.packet << " first=" << row.first
                << " count=" << row.count
                << " purpose=" << purpose_name(row.view.purpose)
                << " present=" << row.view.present << " scissor_offset=("
                << row.scissor_offset[0] << ',' << row.scissor_offset[1]
                << ") scissor_extent=(" << row.scissor_extent[0] << ','
                << row.scissor_extent[1] << ") camera_rect=("
                << row.view.camera_rect.x << ',' << row.view.camera_rect.y << ','
                << row.view.camera_rect.width << ','
                << row.view.camera_rect.height
                << ") camera_rect_available=" << row.view.camera_rect_available
                << " canvas_rect=(" << row.view.canvas.x << ','
                << row.view.canvas.y << ',' << row.view.canvas.width << ','
                << row.view.canvas.height
                << ") canvas_available=" << row.view.canvas_available << '}';
      }
      return message.str();
    };
    const auto unbound_appends = mixed_view_observer.rows(
        producer_view_checks::Stage::append);
    std::vector<producer_view_checks::Observation> unbound_draws;
    if (unbound_appends_before <= unbound_appends.size())
      unbound_draws.assign(unbound_appends.begin() + unbound_appends_before,
                           unbound_appends.end());
    const auto unbound_append_matches =
        std::any_of(unbound_draws.begin(), unbound_draws.end(), [](const auto& row) {
          return row.count != 0 && !row.view.present &&
                 row.view.purpose == ::platform::ProducerPurpose::Original &&
                 row.scissor_offset == std::array<std::int32_t, 2>{0, 0} &&
                 row.scissor_extent == std::array<std::uint32_t, 2>{64, 64};
        });
    if (!unbound_append_matches)
      require(false,
              scissor_failure(
                  "Unbound begin_model_draw did not append a full-scene draw with an empty view",
                  unbound_draws, {0, 0}, {64, 64}).c_str());
    const auto unbound_scissor_matches =
        std::any_of(unbound_rows.begin(), unbound_rows.end(), [](const auto& row) {
          return !row.view.present &&
                 row.view.purpose == ::platform::ProducerPurpose::Original &&
                 row.scissor_offset == std::array<std::int32_t, 2>{0, 0} &&
                 row.scissor_extent == std::array<std::uint32_t, 2>{64, 64};
        });
    if (!unbound_scissor_matches)
      require(false,
              scissor_failure("Unbound begin_model_draw unexpectedly inherited the WorldZoom scissor",
                              unbound_rows, {0, 0}, {64, 64}).c_str());
    mixed_renderer->clear(true, 0, 0, 0);
    const auto production_fallback_before = mixed_renderer->asset_statistics()
                                                .prepared_cpu_fallback_batches;
    const auto production_appends_before = mixed_view_observer.rows(
        producer_view_checks::Stage::append).size();
    {
        zvid::ProducerPurposeScope purpose(::platform::ProducerPurpose::WorldZoom);
        zvid::ProducerWorldScope emission;
        emission.begin_emission();
        expected_mixed_view = zvid::capture_producer_view();
        require(expected_mixed_view.present &&
                    expected_mixed_view.purpose ==
                        ::platform::ProducerPurpose::WorldZoom &&
                    expected_mixed_view.producer_generation != 0 &&
                    expected_mixed_view.mission_epoch != 0 &&
                    expected_mixed_view.canvas_available &&
                    expected_mixed_view.camera_rect_available &&
                    expected_mixed_view.mission.world_index ==
                        previous_producer_state.mission.world_index &&
                    expected_mixed_view.mission.number ==
                        previous_producer_state.mission.number,
                "Mixed-bone production fixture lost its WorldZoom producer view");
        // The production caller (zmod::draw_model) wraps begin_model_draw in exactly this scope:
        // a ProducerBindingScope on the installed renderer. The fixture uses the same scope class
        // instead of a manual exchange; a full draw_model call needs a real model node whose
        // prepared asset is registered, which this asset-free fixture does not build.
        {
            const auto context = mixed_distance.context();
            const zvid::ProducerBindingScope producer_binding(mixed_renderer.get());
            mixed_renderer->begin_model_draw(context);
            require(mixed_renderer->replaces_model_geometry(),
                    "Bound mixed-bone draw missed prepared replacement");
            mixed_renderer->end_model_draw();
        }
        emission.end_emission();
    }
    const auto appended_draws = mixed_view_observer.rows(
        producer_view_checks::Stage::append);
    std::vector<producer_view_checks::Observation> production_draws;
    if (production_appends_before <= appended_draws.size())
      production_draws.assign(appended_draws.begin() + production_appends_before,
                              appended_draws.end());
    const auto production_append_matches =
        std::any_of(production_draws.begin(), production_draws.end(),
                    [&](const auto& row) {
                      return row.count != 0 &&
                             ::platform::same_producer_view_bits(
                                 row.view, expected_mixed_view) &&
                             row.scissor_offset ==
                                 std::array<std::int32_t, 2>{4, 4} &&
                             row.scissor_extent ==
                                 std::array<std::uint32_t, 2>{16, 24};
                    });
    if (!production_append_matches)
      require(false,
              scissor_failure(
                  "Deformed prepared WorldZoom draw missed its appended camera scissor",
                  production_draws, {4, 4}, {16, 24}).c_str());
    const auto mixed_statistics = mixed_renderer->asset_statistics();
    require(mixed_statistics.prepared_cpu_fallback_batches > production_fallback_before &&
                production_fallback_before > fallback_before,
            "Deformed prepared batch did not use the partial CPU fallback");
    std::vector<std::uint32_t> mixed_pixels;
    int mixed_width{}, mixed_height{};
    require(mixed_renderer->read_back(&mixed_pixels, &mixed_width, &mixed_height) &&
                mixed_width == 64 && mixed_height == 64,
            "Deformed prepared scissor lost its readback extent");
    // read_back() flushes the retained Scene; drain() also waits for the worker
    // packet observation before rows are copied below.
    mixed_renderer->drain();
    const auto observed_packets = mixed_view_observer.rows(
        producer_view_checks::Stage::packet, true);
    std::vector<producer_view_checks::Observation> mixed_rows;
    std::copy_if(observed_packets.begin(), observed_packets.end(),
                 std::back_inserter(mixed_rows), [&](const auto& row) {
                   return std::any_of(
                       production_draws.begin(), production_draws.end(),
                       [&](const auto& draw) {
                         return row.first == draw.first &&
                                row.count == draw.count;
                       });
                 });
    const auto mixed_scissor_matches =
        std::any_of(mixed_rows.begin(), mixed_rows.end(), [&](const auto& row) {
          return row.count != 0 &&
                 ::platform::same_producer_view_bits(row.view,
                                                      expected_mixed_view) &&
                 row.scissor_offset == std::array<std::int32_t, 2>{4, 4} &&
                 row.scissor_extent == std::array<std::uint32_t, 2>{16, 24};
        });
    if (!mixed_scissor_matches)
      require(false,
              scissor_failure("Deformed prepared WorldZoom batch missed its camera scissor",
                              mixed_rows, {4, 4}, {16, 24}).c_str());
    std::fprintf(stderr, "[DONOR_TOE_GPU] cases=%u failures=0\n", cases);
}

void check_damage_tint_blend(SDL_Window *window, sdlfe::RendererBackend backend,
                             sdlfe::CoreCriticalAssets options, zcls::Node *root,
                             zcls::Node *panel) {
    // Use the real object walk and geometry producer: a context built by the test
    // alone would miss a leaked global tint or uncleared portrait blend flag.
    struct NativeState {
        std::unique_ptr<zcls::SceneWalk> scene = std::make_unique<zcls::SceneWalk>(zcls::scene_walk());
        zmod::WalkState walk = zmod::walk_state();
        zmod::DrawState draw = zmod::draw_state();
        zmod::Lighting lighting = zmod::lighting();
        zmod::Fog fog = zmod::fog();
        zmth::MatrixStack stack = zmth::matrix_stack();
        zmth::Projection projection = zmth::projection();
        platform::Render3D *renderer = zvid::render3d();
        ~NativeState() {
            zvid::set_render3d(renderer);
            zcls::scene_walk() = *scene;
            zmod::walk_state() = walk;
            zmod::draw_state() = draw;
            zmod::lighting() = lighting;
            zmod::fog() = fog;
            zmth::matrix_stack() = stack;
            zmth::projection() = projection;
        }
    } saved;
    auto &walk = zcls::scene_walk();
    walk.camera = nullptr;
    walk.hidden_surface = walk.ring = walk.recompute = walk.overlay = walk.morph = 0;
    walk.opacity_top = walk.color_top = -1;
    zmod::walk_state() = {};
    static bool force_green_tint = false;
    zmod::walk_state().draw = [](zcls::Node *node, std::uint32_t) -> int32_t {
        auto *renderer = zvid::render3d();
        if (force_green_tint) {
            auto &tint = zmod::lighting();
            tint.tint[0] = 0.f;
            tint.tint[1] = 1.f;
            tint.tint[2] = 0.f;
            tint.tint_weight = .3f;
            tint.tint_on = 1;
        }
        if (renderer->geometry_mode() != cc::geometry::Mode::legacy) {
            require(zmod::submit_geometry(*node), "Tint fixture missed the native geometry handoff");
            return 0;
        }
        // This fixture has no original polygon/vertex buffers. Supply the same
        // context as gmod_draw for the legacy prepared staging/shader route.
        platform::ModelDrawContext context;
        context.node = node;
        context.ordinary = true;
        context.model_to_world = zmth::matrix_stack().below().m;
        context.model_to_camera = zmth::matrix_stack().matrix().m;
        const auto &projection = zmth::projection();
        context.near_z = context.clip_near = projection.near_z;
        context.far_z = projection.far_z;
        context.fx_near = projection.fx_near;
        context.fy_near = projection.fy_near;
        context.cx = projection.cx;
        context.cy = projection.cy;
        context.opacity = zmod::draw_state().opacity;
        if (zmod::lighting().tint_on) {
            std::copy_n(zmod::lighting().tint, 3, context.damage_tint_rgb);
            context.damage_tint_weight = zmod::lighting().tint_weight;
        }
        if (force_green_tint) {
            context.damage_tint_rgb[0] = 0.f;
            context.damage_tint_rgb[1] = 1.f;
            context.damage_tint_rgb[2] = 0.f;
            context.damage_tint_weight = .3f;
        }
        renderer->begin_model_draw(context);
        require(renderer->replaces_model_geometry(), "Tint fixture missed legacy prepared staging");
        renderer->end_model_draw();
        return 0;
    };
    zmth::Mat34 matrix{{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0}};
    zmth::matrix_stack() = {};
    zmth::matrix_stack().slot[0] = zmth::matrix_stack().slot[1] = &matrix;
    zmth::matrix_stack().top = 1;
    zmth::projection() = {};
    auto &projection = zmth::projection();
    projection.near_z = 1;
    projection.far_z = 5;
    projection.fx_near = projection.fy_near = 20;
    projection.cx = projection.cy = 32;
    zmod::draw_state() = {};
    zmod::draw_state().clip.near_z = 1;
    zmod::fog().on = 0;
    zmod::set_tint(nullptr, 0.f);
    mech3::MechPart part;
    part.node = panel;
    part.internal = 0.f;
    const auto geometry_mode = options.geometry;
    for (const char *lighting : {"off", "normal"}) {
        if (std::string_view(lighting) == "off" && geometry_mode != "cpu-reference")
            continue; // One legacy witness; the sun shader covers both modern routes below.
        options.lighting = lighting;
        options.geometry = std::string_view(lighting) == "off" ? "legacy" : geometry_mode;
        // The sun shader's normal view bypasses SDR shadow lifting after the
        // tint, so its readback is a direct witness of the straight RGB blend.
        options.geometry_debug_normals = std::string_view(lighting) == "normal";
        auto renderer = make_check_renderer(window, backend, {}, options);
        renderer->set_viewport(0, 0, 64, 64);
        zvid::set_render3d(renderer.get());
        const auto render = [&](bool portrait, float opacity = 1.f,
                                bool green_tint = false) {
            force_green_tint = green_tint;
            if (portrait) mech3::part_view_tint(part, true);
            zcls::object3d_set_opacity(panel, opacity);
            zcls::object3d_use_opacity(panel, opacity < 1.f);
            renderer->clear(true, 0, 0, 0);
            zcls::render_node(root, 1);
            force_green_tint = false;
            require(!zmod::lighting().tint_on && walk.color_top == -1,
                    "Object walk leaked the HUD portrait lighting tint");
            if (portrait) mech3::part_view_tint(part, false);
            require(!(static_cast<zcls::Object3d *>(panel->data)->get<uint32_t>(0) & 4),
                    "Portrait cleanup left the world mech blend enabled");
            std::vector<std::uint32_t> pixels;
            int width{}, height{};
            require(renderer->read_back(&pixels, &width, &height) && width == 64 && height == 64,
                    "Damage tint blend lost its readback extent");
            return pixels;
        };
        const auto baseline = render(false);
        const auto portrait = render(true);
        const auto green_tint = render(true, 1.f, true);
        require(render(false) == baseline, "World draw inherited the preceding HUD portrait tint");
        require(render(true) == portrait, "Repeated HUD portrait changed after a world draw");
        const auto translucent = render(true, .375f);
        const auto rgba = [](std::uint32_t pixel) -> std::array<float, 4> {
            return {float((pixel >> 16) & 255), float((pixel >> 8) & 255),
                    float(pixel & 255), float(pixel >> 24)};
        };
        const auto require_pixel = [&](std::size_t index, std::uint32_t pixel,
                                       const std::array<float, 4> &expected,
                                       float rgb_tolerance, const char *reason) {
            const auto actual = rgba(pixel);
            if (std::abs(actual[0] - expected[0]) <= rgb_tolerance &&
                std::abs(actual[1] - expected[1]) <= rgb_tolerance &&
                std::abs(actual[2] - expected[2]) <= rgb_tolerance && actual[3] == expected[3])
                return;
            char message[768];
            std::snprintf(message, sizeof message,
                          "%s: geometry=%s lighting=%s pixel=(%zu,%zu) "
                          "measured RGBA=(%.0f,%.0f,%.0f,%.0f) "
                          "expected RGBA=(%.3f,%.3f,%.3f,%.0f) "
                          "baseline=0x%08x RGB tolerance=%.0f alpha tolerance=0",
                          reason, options.geometry.c_str(), lighting, index % 64, index / 64,
                          actual[0], actual[1], actual[2], actual[3], expected[0], expected[1],
                          expected[2], expected[3], unsigned(baseline[index]), rgb_tolerance);
            throw std::runtime_error(message);
        };
        unsigned covered = 0;
        for (std::size_t index = 0; index < baseline.size(); ++index) {
            const auto base = rgba(baseline[index]);
            if (!(baseline[index] & 0xffffff)) {
                require_pixel(index, portrait[index], base, 0.f,
                              "Damage tint changed portrait background coverage");
                require_pixel(index, green_tint[index], base, 0.f,
                              "Green tint changed prepared background coverage");
                require_pixel(index, translucent[index], base, 0.f,
                              "Damage tint changed translucent background coverage");
                continue;
            }
            ++covered;
            const std::array<float, 4> expected{
                base[0] * .4f + 153.f, base[1] * .4f, base[2] * .4f, base[3]};
            require_pixel(index, portrait[index], expected, 2.f,
                          "Portrait is not a 60 percent straight RGB red blend");
            const std::array<float, 4> expected_green{
                base[0] * .7f, base[1] * .7f + 76.5f, base[2] * .7f, base[3]};
            require_pixel(index, green_tint[index], expected_green, 2.f,
                          "Prepared model did not preserve its green 30 percent tint");
            // Black clear and source-alpha blending expose any tint-induced
            // alpha change even though the opaque target's alpha stays one.
            const std::array<float, 4> expected_translucent{
                expected[0] * .375f, expected[1] * .375f, expected[2] * .375f, base[3]};
            require_pixel(index, translucent[index], expected_translucent, 2.f,
                          "Damage tint changed fractional alpha or blended RGB");
        }
        require(covered > 10, "Damage tint blend rendered no useful model witness");
        zvid::set_render3d(saved.renderer);
    }
    zcls::object3d_set_opacity(panel, 1.f);
    zcls::object3d_use_opacity(panel, 0);
}

// A destroyed mech fades through native node opacity (mech_dead dead_fade).
// Over a black clear with SRCALPHA/INVSRCALPHA blending, a fading draw must
// equal the opaque image scaled by its opacity, and zero opacity must leave only
// the clear. Before the fade fix, both prepared routes drew the fade opaque.
// The sun renderer skips its SDR shadow lift for blended draws only, so lit
// output is not proportional; the normal debug view bypasses the lift for both.
void check_gpu_prepared_fade(SDL_Window *window, sdlfe::RendererBackend backend,
                             sdlfe::CoreCriticalAssets options,
                             platform::ModelDrawContext context, const char *mode) {
    options.geometry_debug_normals = true;
    const auto renderer_owner = make_check_renderer(window, backend, {}, options);
    auto &renderer = *renderer_owner;
    renderer.set_viewport(0, 0, 64, 64);
    std::array<float, 12> matrix{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};
    context.model_to_camera = context.model_to_world = matrix.data();
    context.clip_near = 1;
    const auto render = [&](float opacity) {
        context.opacity = opacity;
        renderer.clear(true, 0, 0, 0);
        require(renderer.submit_prepared_geometry(context, {}) ==
                    cc::geometry::Submission::submitted,
                "Fading prepared model was not admitted at the early handoff");
        std::vector<std::uint32_t> pixels;
        int width{}, height{};
        require(renderer.read_back(&pixels, &width, &height) && width == 64 && height == 64,
                "Fading prepared packet lost its extent");
        return pixels;
    };
    const auto opaque = render(1.f);
    unsigned covered = 0;
    for (const auto pixel : opaque)
        if (pixel & 0xffffff)
            ++covered;
    require(covered > 10, "Prepared fade check rendered no useful opaque witness");
    for (const float opacity : {.375f, 0.f}) {
        const auto faded = render(opacity);
        for (std::size_t index = 0; index < faded.size(); ++index)
            for (unsigned shift : {0U, 8U, 16U}) {
                // The CPU-reference route stages opacity as 8-bit diffuse alpha
                // (96/255 for 0.375); two levels covers that and output rounding.
                const float expected_channel = float((opaque[index] >> shift) & 255) * opacity;
                const float measured_channel = float((faded[index] >> shift) & 255);
                if (std::abs(measured_channel - expected_channel) > 2.f) {
                    char message[256];
                    std::snprintf(message, sizeof message,
                                  "Prepared fade ignored node opacity: geometry=%s opacity=%.3f "
                                  "pixel=(%zu,%zu) opaque=0x%08x faded=0x%08x",
                                  mode, opacity, index % 64, index / 64, unsigned(opaque[index]),
                                  unsigned(faded[index]));
                    throw std::runtime_error(message);
                }
            }
    }
}

void check_gpu_prepared(SDL_Window *window, sdlfe::RendererBackend backend) {
    const auto folder = std::filesystem::temp_directory_path() /
                        ("cc-gpu-prepared-" + std::to_string(SDL_GetPerformanceCounter()));
    require(std::filesystem::create_directory(folder), "GPU fixture directory already exists");
    struct Files {
        std::filesystem::path folder;
        ~Files() {
            std::error_code error;
            for (const char *name : {"mesh.bin", "textures.bin", "normals.bin"})
                std::filesystem::remove(folder / name, error);
            std::filesystem::remove(folder, error);
        }
    } files{folder};
    std::ofstream(folder / "mesh.bin", std::ios::binary) << prepared_fixture::mesh(2);
    std::ofstream(folder / "textures.bin", std::ios::binary) << prepared_fixture::textures();
    std::ofstream(folder / "normals.bin", std::ios::binary)
        << prepared_fixture::normals(0xffd980d9);
    std::unique_ptr<zcls::Node, int (*)(zcls::Node *)> root(zcls::object3d_create(),
                                                            zcls::tree_destroy);
    auto *control = zcls::object3d_create(), *panel = zcls::object3d_create();
    require(root && control && panel && zcls::object3d_add_child(root.get(), control) == 0 &&
                zcls::object3d_add_child(control, panel) == 0,
            "GPU fixture hierarchy failed");
    zcls::node_set_name(root.get(), "actor");
    zcls::node_set_name(control, "control");
    zcls::node_set_name(panel, "panel");
    auto asset = std::make_shared<zcls::SourceAsset>();
    asset->name = "mech_authored.flt";
    asset->nodes = {{"actor", 1}, {"control", 1}, {"panel", 1}};
    root->source_asset = control->source_asset = panel->source_asset = asset;
    root->source_asset_root = true;
    zmod::Model model{};
    const std::uint32_t count = 3;
    std::memcpy(model.header + 0x14, &count, sizeof count);
    const std::uint32_t polygons = 1;
    std::memcpy(model.header + 0x10, &polygons, sizeof polygons);
    panel->model = &model;
    panel->source_model_vertices = count;
    struct ModelPointer {
        zcls::Node *node;
        ~ModelPointer() { node->model = nullptr; }
    } model_pointer{panel};
    require(SDL_SetWindowSize(window, 64, 64) && SDL_SyncWindow(window), SDL_GetError());
    std::array<float, 12> matrix{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};
    platform::ModelDrawContext context;
    context.node = panel;
    context.ordinary = true;
    context.source_vertices = 3;
    context.source_polygons = 1;
    context.model_to_camera = context.model_to_world = matrix.data();
    context.near_z = context.clip_near = 1;
    context.far_z = 5;
    context.fx_near = context.fy_near = 20;
    context.cx = context.cy = 32;
    std::vector<std::vector<std::uint32_t>> expected;
    for (const char *mode : {"cpu-reference", "partial"}) {
        sdlfe::CoreCriticalAssets options;
        options.geometry = mode;
        options.models.push_back({"authored", "0", (folder / "mesh.bin").u8string(),
                                  (folder / "textures.bin").u8string()});
        options.normals.push_back({"authored", "0", (folder / "normals.bin").u8string()});
        options.lighting = "normal";
        auto renderer = make_check_renderer(window, backend, {}, options);
        renderer->set_viewport(0, 0, 64, 64);
        for (float weight : {-.1f, std::numeric_limits<float>::quiet_NaN(),
                             std::numeric_limits<float>::infinity(),
                             -std::numeric_limits<float>::infinity(), 1.1f}) {
            context.damage_tint_weight = weight;
            bool rejected = false;
            try {
                renderer->submit_prepared_geometry(context, {});
            } catch (const std::runtime_error &error) {
                rejected = std::string_view(error.what()) == "Model has an invalid native tint weight";
            }
            require(rejected, "Prepared geometry adapter accepted an invalid tint weight");
        }
        for (float channel : {-.1f, std::numeric_limits<float>::quiet_NaN(),
                              std::numeric_limits<float>::infinity(), 1.1f}) {
            context.damage_tint_rgb[1] = channel;
            bool rejected = false;
            try {
                renderer->submit_prepared_geometry(context, {});
            } catch (const std::runtime_error &error) {
                rejected = std::string_view(error.what()) == "Model has an invalid native tint color";
            }
            require(rejected, "Prepared geometry adapter accepted an invalid tint color");
        }
        context.damage_tint_rgb[1] = 0.f;
        for (unsigned scenario = 0; scenario < 7; ++scenario) {
            matrix[2] = scenario == 5 ? 1.5f : 0;
            matrix[9] = scenario == 1 ? .5f : 0;
            matrix[11] = scenario == 3 ? 8.f : 0;
            context.clip_near = scenario == 4 ? 3.f : 1.f;
            context.damage_tint_weight = scenario == 6 ? .6f : 0.f;
            cc::geometry::Fog fog;
            fog.enabled = scenario == 2;
            fog.color = {0, 0, 1};
            fog.near_range = 1;
            fog.inverse_range = .2f;
            fog.low_altitude = 2;
            fog.inverse_altitude = .2f;
            renderer->clear(true, 0, 0, 0);
            require(renderer->submit_prepared_geometry(context, fog) ==
                        cc::geometry::Submission::submitted,
                    "Rigid prepared model was not admitted at the early handoff");
            std::vector<std::uint32_t> pixels;
            int width{}, height{};
            require(renderer->read_back(&pixels, &width, &height) && width == 64 && height == 64,
                    "GPU prepared packet lost its extent");
            if (expected.size() < 7)
                expected.push_back(pixels);
            else {
                require(pixels.size() == expected[scenario].size(),
                        "GPU prepared comparison lost pixels");
                for (std::size_t index = 0; index < pixels.size(); ++index)
                    for (unsigned shift : {0U, 8U, 16U})
                        require(
                            std::abs(int((pixels[index] >> shift) & 255) -
                                     int((expected[scenario][index] >> shift) & 255)) <= 2,
                            "GPU prepared transform/fog/normal/clipping differs from reference");
            }
        }
        const auto statistics = renderer->asset_statistics();
        require(statistics.early_prepared_models == 7 && !statistics.prepared_cpu_fallback_batches,
                "Early prepared submission used an unreported CPU fallback");
        if (std::string_view(mode) == "partial")
            require(
                statistics.gpu_prepared_vertices == 21 && statistics.geometry_uploads == 1 &&
                    statistics.cpu_clipped_triangles == 0 && statistics.normal_draws == 7,
                "GPU prepared vertices still use CPU clipping or lost immutable material draws");
        {
            // Extend coverage after the original seven-scenario accounting checks above.
            // Both prepared routes must fog high terrain even when mission fog is off.
            const auto saved_context = context;
            const auto saved_matrix = matrix;
            std::array<float, 12> elevated_world{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 500, 0};
            context.model_to_world = elevated_world.data();
            context.damage_tint_weight = 0;
            for (bool mission_on : {false, true}) {
                cc::geometry::Fog edge;
                edge.enabled = mission_on;
                edge.color = {0, 0, 1};
                edge.low_altitude = 80;
                edge.inverse_altitude = 1.f / 20.f;
                edge.edge_inverse_range = 1;
                renderer->clear(true, 0, 0, 0);
                require(renderer->submit_prepared_geometry(context, edge) ==
                            cc::geometry::Submission::submitted,
                        "Prepared edge-fog geometry was not submitted");
                std::vector<std::uint32_t> pixels;
                int width{}, height{};
                require(renderer->read_back(&pixels, &width, &height) && width == 64 && height == 64,
                        "Prepared edge-fog readback extent changed");
                unsigned witnesses = 0;
                for (const auto pixel : pixels) {
                    if (!(pixel & 0xffffff)) continue;
                    require(pixel == 0xff0000ff,
                            "Prepared high terrain escaped fully opaque edge fog");
                    ++witnesses;
                }
                require(witnesses > 10, "Prepared edge fog rendered no geometry witness");
            }
            // Map the fixture's y == -1/+1 vertices to camera depths 3000/3400.
            // This crosses the 3200 cut with unequal radii, unlike constant-fog fixtures.
            matrix = {500, 0, 0, 0, 100, 200, 0, 0, 1, 0, 0, 3198};
            context.far_z = 3200;
            context.fx_near = 64;
            context.fy_near = 3200;
            cc::geometry::Fog crossing_edge;
            crossing_edge.color = {0, 0, 1};
            crossing_edge.edge_start = 3050;
            crossing_edge.edge_inverse_range = 1.f / 150.f;
            renderer->clear(true, 255, 0, 255);
            require(renderer->submit_prepared_geometry(context, crossing_edge) ==
                        cc::geometry::Submission::submitted,
                    "Crossing prepared fog geometry was not submitted");
            std::vector<std::uint32_t> crossing_pixels;
            int crossing_width{}, crossing_height{};
            require(renderer->read_back(&crossing_pixels, &crossing_width, &crossing_height) &&
                        crossing_width == 64 && crossing_height == 64,
                    "Crossing prepared fog readback extent changed");
            const auto cut_pixel = crossing_pixels[31 * 64 + 32];
            require((cut_pixel & 255) >= 247 && ((cut_pixel >> 8) & 255) <= 8 &&
                        ((cut_pixel >> 16) & 255) <= 8,
                    "Crossing prepared GPU/reference triangle exposed the far cut");
            matrix = saved_matrix;
            context = saved_context;
        }
        producer_view_checks::Observer view_observer;
        require(cc_mw3_re::testing::observe_producer_views(*renderer,
                                                            &view_observer),
                "Prepared scissor observer unsupported");
        zvid::set_producer_canvas_rect(10, 20, 128, 64);
        zvid::set_producer_camera_rect(18, 24, 32, 24);
        renderer->clear(true, 0, 0, 0);
        {
            producer_view_checks::Emission emission(
                ::platform::ProducerPurpose::WorldZoom);
            require(zvid::submit_prepared_geometry_for_current_view(
                        renderer.get(), context, {}) ==
                        cc::geometry::Submission::submitted,
                    "Prepared WorldZoom geometry was not submitted");
        }
        std::vector<std::uint32_t> scissor_pixels;
        int scissor_width{}, scissor_height{};
        require(renderer->read_back(&scissor_pixels, &scissor_width,
                                    &scissor_height) &&
                    scissor_width == 64 && scissor_height == 64,
                "Prepared WorldZoom scissor lost the scene extent");
        const auto prepared_rows =
            view_observer.rows(producer_view_checks::Stage::packet, true);
        require(std::any_of(prepared_rows.begin(), prepared_rows.end(),
                            [](const auto& row) {
                              return row.scissor_offset ==
                                         std::array<std::int32_t, 2>{4, 4} &&
                                     row.scissor_extent ==
                                         std::array<std::uint32_t, 2>{16, 24};
                            }),
                "Prepared WorldZoom draw missed the mapped camera scissor");
        require(cc_mw3_re::testing::observe_producer_views(*renderer, nullptr),
                "Prepared scissor observer removal failed");
        check_damage_tint_blend(window, backend, options, root.get(), panel);
        check_gpu_prepared_fade(window, backend, options, context, mode);
    }
    require(expected[0] != expected[1] && expected[0] != expected[2],
            "Prepared reference did not exercise motion or fog");
    require(expected[6] != expected[0],
            "Prepared model lost its per-node damage tint");
    for (unsigned scenario : {3U, 4U})
        require(std::all_of(expected[scenario].begin(), expected[scenario].end(),
                            [](auto pixel) { return (pixel & 0xffffff) == 0; }),
                "Prepared depth rejection did not remove geometry");
    check_gpu_donor_toes(window, backend);
}

// The staging-pressure checks live in their own function so the --materials variants run them
// (check_local_light_gpu only runs in the default variant). Defined after the producer-view
// checks because it observes the worker packets.
void check_local_light_staging(SDL_Window *window, sdlfe::RendererBackend backend) {
  // Per-packet byte accounting: a shared geometry / lit-normal allocation is charged once, however
  // many draws use it, and K distinct allocations are charged K times; the total is the checked sum
  // of the named terms. Counting per draw (the previous behaviour) fails the one-copy check.
  {
    const auto make_instance = [](std::size_t vertices, std::size_t indices) {
      auto geometry = std::make_shared<mw34::vkscene::ModelGeometry>();
      geometry->vertices.resize(vertices);
      geometry->indices.resize(indices);
      auto instance = std::make_shared<mw34::vkscene::ModelInstance>();
      instance->geometry = geometry;
      return instance;
    };
    const auto normals = std::make_shared<const std::vector<std::array<float, 3>>>(64);
    const auto one_scene = [&](std::size_t draws, std::size_t distinct) {
      mw34::vkscene::Scene scene;
      std::vector<std::shared_ptr<mw34::vkscene::ModelInstance>> instances;
      for (std::size_t index = 0; index < distinct; ++index)
        instances.push_back(make_instance(100, 300));
      scene.draws.resize(draws);
      for (std::size_t draw = 0; draw < draws; ++draw) {
        scene.draws[draw].model = instances[draw % distinct];
        scene.draws[draw].lit_normals = normals;
      }
      return cc_mw3_re::testing::packet_byte_breakdown(scene);
    };
    const auto single = one_scene(1, 1);
    const auto shared_many = one_scene(50, 1);
    const auto three = one_scene(50, 3);
    require(single.geometry > 0 && single.lit_normals > 0, "Breakdown fixture counted no bytes");
    require(shared_many.geometry == single.geometry && shared_many.lit_normals == single.lit_normals,
            "A shared geometry or lit-normal allocation was charged once per draw");
    require(three.geometry == 3 * single.geometry && three.lit_normals == single.lit_normals,
            "Distinct geometries were not charged separately");
    require(shared_many.total >= shared_many.geometry + shared_many.lit_normals,
            "The packet total is smaller than its named terms");
    // A raw-fog stream shared by many draws is charged once, and the checked total includes it
    // (staging admission and render-worker queue charging use that total).
    const auto raw_fog = std::make_shared<const std::vector<std::array<float, 4>>>(64);
    const auto fog_scene = [&](std::size_t draws, bool with_fog) {
      mw34::vkscene::Scene scene;
      scene.draws.resize(draws);
      if (with_fog)
        for (auto &draw : scene.draws)
          draw.raw_fog = raw_fog;
      return cc_mw3_re::testing::packet_byte_breakdown(scene);
    };
    const auto no_fog = fog_scene(2, false);
    const auto shared_fog = fog_scene(2, true);
    const auto one_fog = fog_scene(1, true);
    require(no_fog.raw_fog == 0 && shared_fog.raw_fog > 0 && shared_fog.raw_fog == one_fog.raw_fog,
            "A shared raw-fog stream was not charged exactly once");
    require(shared_fog.total == no_fog.total + shared_fog.raw_fog,
            "The packet total left out the raw-fog bytes");
  }
  // Local-light packet staging only runs while effect lights are enabled with a catalog and a
  // valid world projection, so set up the same minimal environment as check_local_light_gpu.
  const auto old_projection = zmth::projection();
  const auto old_view = zmth::view();
  struct Env {
    const char *name;
    std::optional<std::string> prior;
    explicit Env(const char *n) : name(n) {
      if (const char *v = std::getenv(n))
        prior = v;
    }
    ~Env() { local_light_test_env(name, prior ? prior->c_str() : nullptr); }
  } catalog_env("MW34_EFFECT_LIGHT_CATALOG"), enabled_env("MW34_EFFECT_LIGHTS");
  // Unique across concurrent test processes: a random 64-bit nonce per call, a per-process counter
  // and the tick count (the catalog file is removed by the Restore guard below).
  static std::atomic<unsigned> staging_catalog_counter{0};
  std::random_device staging_random;
  const unsigned long long staging_nonce =
      (static_cast<unsigned long long>(staging_random()) << 32) | staging_random();
  const auto catalog_path =
      std::filesystem::temp_directory_path() /
      ("mw34-staging-" + std::to_string(staging_nonce) + "-" +
       std::to_string(staging_catalog_counter.fetch_add(1)) + "-" +
       std::to_string(SDL_GetTicksNS()) + ".bin");
  struct Restore {
    std::function<void()> f;
    ~Restore() {
      if (f) f();
    }
  } restore{[&] {
    zmth::projection() = old_projection;
    zmth::view() = old_view;
    std::error_code ignored;
    std::filesystem::remove(catalog_path, ignored);
  }};
  {
    std::ofstream f(catalog_path, std::ios::binary);
    auto u32 = [&](uint32_t n) {
      for (unsigned i = 0; i < 4; ++i)
        f.put(char(n >> (i * 8)));
    };
    auto scalar = [&](float n) {
      uint32_t bits;
      std::memcpy(&bits, &n, 4);
      u32(bits);
    };
    f.write("MWFX1\0\0\0", 8);
    u32(1);
    u32(1);
    u32(1);
    u32(1);
    u32(2);
    u32(123);
    u32(0);
    scalar(10);
    scalar(1);
    scalar(1);
    scalar(1);
    scalar(1);
    scalar(1);
    f.flush();
    require(bool(f), "Could not write the staging fixture catalog");
  }
  local_light_test_env("MW34_EFFECT_LIGHT_CATALOG", catalog_path.string().c_str());
  local_light_test_env("MW34_EFFECT_LIGHTS", "1");
  zmth::projection() = {};
  auto &projection = zmth::projection();
  projection.near_z = 1;
  projection.fx_near = projection.fy_near = 16;
  projection.cx = projection.cy = 16;
  projection.far_z = 100;
  const float camera[12] = {1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};
  std::memcpy(zmth::view().camera.m, camera, sizeof camera);
  struct ObserverCleanup {
    cc_mw3_re::VulkanFrameRenderer &renderer;
    ~ObserverCleanup() noexcept {
      try {
        cc_mw3_re::testing::observe_producer_views(renderer, nullptr);
      } catch (...) {
      }
    }
  };
  const auto distinct_pixels = [](int index) {
    return std::vector<uint8_t>(std::size_t(128) * 128 * 4, uint8_t(40 + index * 30));
  };
  // Staging pressure across SEVERAL packets of one scene must degrade instead of ending the game:
  // when the next packet does not fit, the pending earlier packets are submitted early with the
  // lights known so far. The 128 KiB allowance holds one 128-square RGBA payload packet but not
  // two, so every flush after the first forces an early completion. Every packet must reach the
  // worker exactly once and in producer order; a version that dropped earlier packets fails the
  // packet-count and id-order checks below.
  {
    sdlfe::CoreCriticalAssets assets{};
    assets.lighting = "flat";
    auto renderer = make_check_renderer(window, backend, {}, assets, 128u * 1024u);
    producer_view_checks::Observer observer;
    require(cc_mw3_re::testing::observe_producer_views(*renderer, &observer),
            "Staging fixture could not observe worker packets");
    ObserverCleanup observer_cleanup{*renderer};
    renderer->mission_changed({5, 1});
    renderer->set_viewport(0, 0, 32, 32);
    renderer->clear(true, 0, 0, 0);
    renderer->begin_scene();
    for (int packet = 0; packet < 4; ++packet) {
      const auto pixels = distinct_pixels(packet);
      platform::DrawState state{};
      state.texture = renderer->create_texture(128, 128, pixels.data(), 1);
      quad(*renderer, 4, 28, .5f, 0xffffffff, state);
      renderer->flush();
    }
    renderer->end_scene();
    renderer->drain();
    const auto staging = cc_mw3_re::testing::staging_state(*renderer);
    const std::string pressure_message =
        "Staging pressure did not complete earlier local-light packets early: early=" +
        std::to_string(staging.early_completions) + " peak=" + std::to_string(staging.peak_bytes) +
        " log_lines=" + std::to_string(staging.early_log_lines);
    require(staging.early_completions >= 2, pressure_message.c_str());
    require(staging.early_log_lines == 1,
            "Early staging completions were not logged exactly once");
    require(staging.peak_bytes > 0 && staging.peak_bytes <= 128u * 1024u,
            "Staging peak left the allowance");
    const auto delivered = observer.rows(producer_view_checks::Stage::packet, true);
    require(delivered.size() == 4, "Early completion dropped or duplicated a staged packet");
    for (std::size_t index = 1; index < delivered.size(); ++index)
      require(delivered[index].packet > delivered[index - 1].packet,
              "Early completion delivered packets out of producer order");
  }

  // A single packet larger than the whole allowance (the owner's c3m3 crash) must not end the
  // game. The pending earlier packet is completed first, in producer order, and the oversized
  // packet is then staged alone and delivered once.
  {
    sdlfe::CoreCriticalAssets assets{};
    assets.lighting = "flat";
    auto renderer = make_check_renderer(window, backend, {}, assets, 128u * 1024u);
    producer_view_checks::Observer observer;
    require(cc_mw3_re::testing::observe_producer_views(*renderer, &observer),
            "Staging fixture could not observe worker packets");
    ObserverCleanup observer_cleanup{*renderer};
    renderer->mission_changed({5, 1});
    renderer->set_viewport(0, 0, 32, 32);
    renderer->clear(true, 0, 0, 0);
    renderer->begin_scene();
    {
      const auto pixels = distinct_pixels(0);
      platform::DrawState little_state{};
      little_state.texture = renderer->create_texture(128, 128, pixels.data(), 1);
      quad(*renderer, 4, 28, .5f, 0xffffffff, little_state);
      renderer->flush(); // one packet pending
    }
    const std::vector<uint8_t> big(std::size_t(256) * 256 * 4, 77);
    platform::DrawState oversized{};
    oversized.texture = renderer->create_texture(256, 256, big.data(), 1);
    quad(*renderer, 4, 28, .5f, 0xffffffff, oversized);
    renderer->end_scene();
    renderer->drain();
    const auto staging = cc_mw3_re::testing::staging_state(*renderer);
    require(staging.oversized_packets == 1, "An oversized single packet was not staged alone");
    require(staging.early_completions == 1,
            "The packet pending before an oversized packet was not completed first");
    const auto delivered = observer.rows(producer_view_checks::Stage::packet, true);
    require(delivered.size() == 2, "An oversized packet or its predecessor was dropped");
    require(delivered[1].packet > delivered[0].packet,
            "An oversized packet was delivered before its predecessor");
    std::vector<std::uint32_t> frame;
    int width{}, height{};
    require(renderer->read_back(&frame, &width, &height) && !frame.empty(),
            "A scene with an oversized packet did not render");
  }

  // Several oversized packets in a row: each one completes the one before it, so at most one is
  // ever held. Every 256-square RGBA payload is 256 KiB, so holding two at once would need at
  // least 512 KiB. Every packet is delivered once and in order, the warning is written once per
  // mission, and later frames keep rendering.
  {
    sdlfe::CoreCriticalAssets assets{};
    assets.lighting = "flat";
    auto renderer = make_check_renderer(window, backend, {}, assets, 128u * 1024u);
    producer_view_checks::Observer observer;
    require(cc_mw3_re::testing::observe_producer_views(*renderer, &observer),
            "Staging fixture could not observe worker packets");
    ObserverCleanup observer_cleanup{*renderer};
    renderer->mission_changed({5, 1});
    renderer->set_viewport(0, 0, 32, 32);
    renderer->clear(true, 0, 0, 0);
    renderer->begin_scene();
    constexpr int oversized_packet_count = 3;
    std::vector<platform::DrawState> states;
    for (int packet = 0; packet < oversized_packet_count; ++packet) {
      const std::vector<uint8_t> big(std::size_t(256) * 256 * 4, uint8_t(60 + packet * 40));
      platform::DrawState state{};
      state.texture = renderer->create_texture(256, 256, big.data(), 1);
      states.push_back(state);
      quad(*renderer, 4, 28, .5f, 0xffffffff, state);
      renderer->flush();
    }
    renderer->end_scene();
    renderer->drain();
    const auto staging = cc_mw3_re::testing::staging_state(*renderer);
    const std::string accumulation_message =
        "Oversized packets were not completed one at a time: oversized=" +
        std::to_string(staging.oversized_packets) +
        " early=" + std::to_string(staging.early_completions) +
        " peak=" + std::to_string(staging.peak_bytes) +
        " log_lines=" + std::to_string(staging.oversized_log_lines);
    require(staging.oversized_packets == oversized_packet_count, accumulation_message.c_str());
    require(staging.early_completions == oversized_packet_count - 1,
            accumulation_message.c_str());
    const std::size_t two_payload_bytes = std::size_t(2) * 256 * 256 * 4;
    require(staging.peak_bytes > 128u * 1024u && staging.peak_bytes < two_payload_bytes,
            accumulation_message.c_str());
    require(staging.oversized_log_lines == 1, accumulation_message.c_str());
    const auto delivered = observer.rows(producer_view_checks::Stage::packet, true);
    require(delivered.size() == std::size_t(oversized_packet_count),
            "Oversized packets were dropped or duplicated");
    for (std::size_t index = 1; index < delivered.size(); ++index)
      require(delivered[index].packet > delivered[index - 1].packet,
              "Oversized packets were delivered out of producer order");
    // The textures are resident now, so the next frame's packet carries no payload and fits.
    renderer->clear(true, 0, 0, 0);
    renderer->begin_scene();
    for (const auto &state : states)
      quad(*renderer, 4, 28, .5f, 0xffffffff, state);
    renderer->end_scene();
    renderer->drain();
    std::vector<std::uint32_t> frame;
    int width{}, height{};
    require(renderer->read_back(&frame, &width, &height) && !frame.empty(),
            "The frame after oversized packets did not render");
    require(cc_mw3_re::testing::staging_state(*renderer).oversized_packets ==
                oversized_packet_count,
            "A frame with resident textures was still oversized");
  }

  // Nothing may be carried from one mission into the next. Mission A completes some packets
  // (filling the recycled-scene pool) and leaves one more pending (flushed but never ended). The
  // mission change must discard the pending packet without delivering it, release the pool, and
  // mission B's first flush must start with an empty staging area.
  {
    sdlfe::CoreCriticalAssets assets{};
    assets.lighting = "flat";
    auto renderer = make_check_renderer(window, backend, {}, assets, 1024u * 1024u);
    producer_view_checks::Observer observer;
    require(cc_mw3_re::testing::observe_producer_views(*renderer, &observer),
            "Staging fixture could not observe worker packets");
    ObserverCleanup observer_cleanup{*renderer};
    renderer->set_viewport(0, 0, 32, 32);
    renderer->mission_changed({5, 1});
    renderer->clear(true, 0, 0, 0);
    // Several packets in ONE scene, so several Scenes are recycled into the pool at once (the next
    // scene adopts at most one of them).
    renderer->begin_scene();
    for (int packet = 0; packet < 3; ++packet) {
      const auto pixels = distinct_pixels(packet);
      platform::DrawState state{};
      state.texture = renderer->create_texture(128, 128, pixels.data(), 1);
      quad(*renderer, 4, 28, .5f, 0xffffffff, state);
      renderer->flush();
    }
    renderer->end_scene();
    renderer->drain();
    // The retained capacity lives in the pool and in the producer Scene that adopted one.
    const auto populated = cc_mw3_re::testing::staging_state(*renderer);
    const std::string pool_message =
        "Mission A did not leave retained Scene capacity: pool=" +
        std::to_string(populated.recycled_scenes) +
        " scene_bytes=" + std::to_string(populated.retained_scene_bytes);
    // The roomy 1 MiB allowance lets all three packets complete together at end_scene, so three
    // Scenes are recycled at once. The pool must hold them (the producer Scene may or may not
    // have adopted one, depending on whether a render thread already recycled it).
    require(populated.recycled_scenes > 0, pool_message.c_str());
    const auto early_before_b = populated.early_completions;
    const auto delivered_a = observer.rows(producer_view_checks::Stage::packet, true).size();
    renderer->begin_scene();
    const auto pending_pixels = distinct_pixels(3);
    platform::DrawState pending_state{};
    pending_state.texture = renderer->create_texture(128, 128, pending_pixels.data(), 1);
    quad(*renderer, 4, 28, .5f, 0xffffffff, pending_state);
    renderer->flush(); // mission A's packet left pending
    renderer->mission_changed({5, 2});
    const auto released = cc_mw3_re::testing::staging_state(*renderer);
    require(released.recycled_scenes == 0 && released.retained_scene_bytes == 0,
            "A mission change kept retained Scene capacity");
    renderer->set_viewport(0, 0, 32, 32);
    renderer->clear(true, 0, 0, 0);
    renderer->begin_scene();
    const auto second_pixels = distinct_pixels(4);
    platform::DrawState second{};
    second.texture = renderer->create_texture(128, 128, second_pixels.data(), 1);
    quad(*renderer, 4, 28, .5f, 0xffffffff, second);
    renderer->flush();
    renderer->end_scene();
    renderer->drain();
    const auto staging = cc_mw3_re::testing::staging_state(*renderer);
    require(staging.first_flush_pending_bytes == 0 && staging.first_flush_pending_packets == 0,
            "A mission change carried staged local-light packets into the next mission");
    require(staging.early_completions == early_before_b,
            "The second mission's first frame needed an early staging completion");
    // Mission A's pending packet was discarded: only mission B's own packet was delivered.
    require(observer.rows(producer_view_checks::Stage::packet, true).size() == delivered_a + 1,
            "Mission A's discarded packet was delivered, or mission B's packet was lost");
  }
}
