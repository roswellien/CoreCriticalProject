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
    std::fprintf(stderr, "[DONOR_TOE_GPU] cases=%u failures=0\n", cases);
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
