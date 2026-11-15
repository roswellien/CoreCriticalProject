// owned_rigid_capture_checks.inc

void check_owned_rigid_capture(SDL_Window *window, sdlfe::RendererBackend backend) {
  using Hook = cc_mw3_re::testing::RigidCaptureTestHook;
  unsigned exercised_cases = 0;

  const std::string valid_source_sha(64, 'a');
  const std::string valid_sidecar_sha(64, 'b');
  const mw34::materials::SurfaceKey key_a{4, 4, 1, 0x1122334455667788ULL};
  const mw34::materials::SurfaceKey key_b{2, 2, 1, 0x99aabbccddeeff00ULL};

  sdlfe::CoreCriticalAssets assets{};
  assets.lighting = "normal";
  assets.geometry = "gpu";
  assets.pom = true;

  auto renderer = make_check_renderer(window, backend, {}, assets);
  auto other_renderer = make_check_renderer(window, backend, {}, assets);
  const auto budget = Hook::surface_budget(*renderer);
  require(budget != nullptr, "Renderer surface decoded budget is missing");

  std::vector<std::uint32_t> albedo_a(64, 0xff228844u);
  std::vector<std::uint32_t> albedo_b(16, 0xff446688u);
  mw34::materials::set_active_surface_key(key_a);
  const int handle_a = renderer->create_named_texture(
      "ggter1", 8, 8, reinterpret_cast<const std::uint8_t *>(albedo_a.data()), 1);
  mw34::materials::set_active_surface_key(key_b);
  const int handle_b = renderer->create_named_texture(
      "ggter2", 4, 4, reinterpret_cast<const std::uint8_t *>(albedo_b.data()), 1);
  mw34::materials::clear_active_surface_key();
  require(handle_a >= 0 && handle_b >= 0, "Failed to create authored test textures");

  mw34::materials::WorldNormalCache::TextureRecord norm_a{};
  norm_a.name = "ggter1_n";
  norm_a.width = 4;
  norm_a.height = 4;
  norm_a.hash = 0xabcdef0123456789ULL;
  norm_a.pixels32.assign(16, 0xff8080ffu);
  Hook::seed_authored_normal(*renderer, key_a, norm_a);

  mw34::materials::WorldNormalCache::TextureRecord norm_b{};
  norm_b.name = "ggter2_n";
  norm_b.width = 2;
  norm_b.height = 2;
  norm_b.hash = 0xfedcba9876543210ULL;
  norm_b.pixels32.assign(4, 0xff7f7fffu);
  Hook::seed_authored_normal(*renderer, key_b, norm_b);

  struct RigFixture {
    std::vector<float> positions{-1.f, -1.f, 3.f, 1.f, -1.f, 3.f, 0.f, 1.f, 3.f, 1.f, 1.f, 3.f};
    std::vector<float> normals{0.f, 0.f, -1.f, 0.f, 0.f, -1.f, 0.f, 0.f, -1.f, 0.f, 0.f, -1.f};
    std::vector<float> uvs{0.f, 0.f, 1.f, 0.f, 0.f, 1.f, 1.f, 1.f};
    std::vector<std::uint32_t> indices{0, 1, 2, 3};
    std::vector<std::uint32_t> normal_indices{0, 1, 2, 3};
    zvid::D3DTexture d3d_a{}, d3d_b{};
    zimg::TextureEntry entry_a{}, entry_b{};
    zmod::Material mat_a{}, mat_b{};
    std::vector<zmod::Polygon> polygons;
    zmod::Model model{};
    zcls::Node node{};
    std::shared_ptr<zcls::SourceAsset> source_asset;
    std::array<float, 12> world{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};
    std::array<float, 12> camera{1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0};
    ::platform::ModelDrawContext context{};
    zmod::RigidGeometryEligibility eligibility{false, false, 1.f};

    RigFixture(int ha, int hb, std::uint32_t poly_count = 3) : polygons(poly_count) {
      d3d_a.type = d3d_b.type = 1;
      d3d_a.handle = ha;
      d3d_b.handle = hb;
      d3d_a.address_u = d3d_a.address_v = 1;
      d3d_b.address_u = d3d_b.address_v = 3;
      std::strcpy(entry_a.name, "ggter1");
      std::strcpy(entry_b.name, "ggter2");
      entry_a.surface = &d3d_a;
      entry_b.surface = &d3d_b;
      mat_a.alpha = mat_b.alpha = 255;
      mat_a.flags = mat_b.flags = 1;
      mat_a.r = 255.f;
      mat_a.g = 128.f;
      mat_a.b = 64.f;
      mat_b.r = 32.f;
      mat_b.g = 200.f;
      mat_b.b = 100.f;
      mat_a.texture = &entry_a;
      mat_b.texture = &entry_b;
      const unsigned first_a = poly_count == 3 ? 2u : 3u;
      for (unsigned i = 0; i < poly_count; ++i) {
        auto &p = polygons[i];
        p.flags = 3u | 0x200u;
        p.vertex_indices = indices.data();
        p.normal_indices = normal_indices.data();
        p.uvs = uvs.data();
        p.material = (i < first_a) ? &mat_a : &mat_b;
      }
      model.vertices = positions.data();
      model.normals = normals.data();
      model.polygons = polygons.data();
      const std::uint32_t vcount = 4, ncount = 4;
      std::memcpy(model.header + 0x10, &poly_count, 4);
      std::memcpy(model.header + 0x14, &vcount, 4);
      std::memcpy(model.header + 0x18, &ncount, 4);

      source_asset = std::make_shared<zcls::SourceAsset>();
      source_asset->name = "world/t1m1.zbd";
      zcls::WorldSourceIdentity world_id{};
      world_id.kind = "gamez-zbd-v27";
      world_id.member = "t1m1_ground.zmd";
      world_id.sha256 = std::string(64, 'a');
      world_id.bytes = 4096;
      world_id.model_slot = 7;
      world_id.load_epoch = zcls::world_source_epoch();
      source_asset->world = world_id;
      model.world_source_asset = source_asset;
      node.model = &model;
      node.source_asset = source_asset;
      node.put<std::int32_t>(0x3c, 7);

      context.node = &node;
      context.model_to_world = world.data();
      context.model_to_camera = camera.data();
      context.near_z = 1.f;
      context.clip_near = 1.f;
      context.far_z = 100.f;
      context.fx_near = context.fy_near = 16.f;
      context.cx = context.cy = 16.f;
      context.opacity = 1.f;
      context.ordinary = true;
      context.morphing = false;
      context.overlay = false;
      context.source_vertices = vcount;
      context.source_polygons = poly_count;
    }
  };

  auto make_target = [&](const RigFixture &rig,
                         const std::shared_ptr<mw34::materials::SurfaceDecodedBudget> &b,
                         bool third_untextured = false,
                         bool third_no_height = false) {
    const auto hash = cc_mw3_re::native_mesh_uv_hash(rig.model);
    require(hash.has_value(), "Fixture mesh_uv_hash unavailable");
    auto pack = std::make_shared<mw34::materials::SurfaceMaterialPack>();
    pack->version = 1;
    pack->mesh_uv_hash = *hash;
    pack->decoded_reservation =
        std::make_shared<mw34::materials::SurfaceDecodedReservation>(b);
    mw34::materials::SurfaceMaterialImage img{};
    img.name = "ggter1_h";
    img.role = mw34::materials::surface_role_height;
    img.width = 4;
    img.height = 4;
    img.hash = 0x13572468ace02468ULL;
    img.pixels.assign(16, 0x00000080u);
    pack->decoded_reservation->grow(img.pixels.size() * sizeof(std::uint32_t));
    pack->images.push_back(std::move(img));

    auto rec_a = std::make_shared<mw34::materials::SurfaceMaterialRecord>();
    rec_a->asset_id = "env:t1m1_ground";
    rec_a->material_name = "ggter1";
    rec_a->height_image = 0;
    rec_a->height_amplitude = 0.25f;
    rec_a->max_displacement = 0.25f;
    rec_a->roughness = 0.65f;
    rec_a->reflectivity = 0.05f;
    rec_a->metallic = 0.1f;

    auto rec_b = std::make_shared<mw34::materials::SurfaceMaterialRecord>();
    rec_b->asset_id = "env:t1m1_ground";
    rec_b->material_name = "ggter2";
    rec_b->height_image = third_no_height ? mw34::materials::no_surface_image : 0u;
    rec_b->height_amplitude = 0.2f;
    rec_b->max_displacement = 0.2f;
    rec_b->roughness = 0.8f;
    rec_b->reflectivity = 0.03f;
    rec_b->metallic = 0.0f;

    pack->records.push_back(rec_a);
    pack->records.push_back(rec_b);

    ::platform::prepared::MaterialTarget target{};
    target.asset_id = "env:t1m1_ground";
    target.source.kind = "gamez-zbd-v27";
    target.source.member = "t1m1_ground.zmd";
    target.source.sha256 = valid_source_sha;
    target.source.bytes = 4096;
    target.source.model_slot = 7;
    target.mesh_uv_hash = *hash;
    target.sidecar_path = "env/t1m1_ground.bwsfm1";
    target.sidecar_sha256 = valid_sidecar_sha;
    const std::uint32_t poly_count = rig.model.count(0x10);
    const unsigned first_a = poly_count == 3 ? 2u : 3u;
    for (unsigned i = 0; i < poly_count; ++i) {
      if (third_untextured && i == poly_count - 1) {
        target.polygon_materials.push_back("untextured");
        target.surface_keys.push_back(std::nullopt);
        pack->bindings.push_back(mw34::materials::no_surface_material);
      } else if (i < first_a) {
        target.polygon_materials.push_back("ggter1");
        target.surface_keys.push_back(key_a);
        pack->bindings.push_back(0);
      } else {
        target.polygon_materials.push_back("ggter2");
        target.surface_keys.push_back(key_b);
        pack->bindings.push_back(1);
      }
    }
    target.pack = pack;
    return target;
  };

  auto install_targets = [&](std::vector<::platform::prepared::MaterialTarget> targets) {
    auto env = std::make_shared<::platform::prepared::EnvironmentSelection>();
    const auto region = ::platform::prepared::environment_region("t1m1");
    env->material_targets[region] = std::move(targets);
    Hook::set_mission_and_environment(*renderer, "t1m1", std::move(env));
  };

  // Match the decoder's source-proof initialization before admitting a world fixture.
  if (zcls::world_source_epoch() == 0) {
    require(zcls::invalidate_world_source_proofs() != 0,
            "Authored world source epoch initialization failed");
  }

  // 1. Empty model caches: positive capture + old native_geometry_admissions rejection.
  {
    RigFixture rig(handle_a, handle_b, 3);
    install_targets({make_target(rig, budget)});
    const auto scene_before = renderer->scene_binding_statistics();
    std::fesetround(FE_UPWARD);
    std::feclearexcept(FE_ALL_EXCEPT);
    std::feraiseexcept(FE_DIVBYZERO);
    const auto captured = Hook::capture_original_rigid(
        *renderer, rig.node, rig.context, rig.eligibility, 1024 * 1024);
    require(std::fegetround() == FE_UPWARD && std::fetestexcept(FE_ALL_EXCEPT) == FE_DIVBYZERO,
            "capture_original_rigid leaked FP state");
    std::fesetround(FE_TONEAREST);
    std::feclearexcept(FE_ALL_EXCEPT);
    require(captured != nullptr, "Positive capture returned null");
    require(!rig.model.render_geometry && rig.model.render_materials.empty(),
            "capture_original_rigid populated empty model caches");
    const auto scene_after = renderer->scene_binding_statistics();
    require(scene_after.commands == scene_before.commands &&
                scene_after.draws == scene_before.draws &&
                scene_after.textures == scene_before.textures,
            "capture_original_rigid mutated scene commands/draws/textures");
    require(captured->ranges().size() == 3 && captured->resource()->ranges.size() == 3,
            "Captured range count mismatch");
    require(captured->ranges()[0].albedo_image != nullptr &&
                captured->ranges()[0].albedo_image == captured->ranges()[1].albedo_image &&
                captured->ranges()[0].albedo_image != captured->ranges()[2].albedo_image &&
                captured->ranges()[0].albedo_image->width == 8 &&
                captured->ranges()[0].albedo_image->height == 8 &&
                captured->ranges()[0].albedo_image->pixels32 == albedo_a &&
                captured->ranges()[2].albedo_image->width == 4 &&
                captured->ranges()[2].albedo_image->height == 4 &&
                captured->ranges()[2].albedo_image->pixels32 == albedo_b,
            "Captured albedo replacement dimensions or pixels mismatch");
    require(captured->ranges()[0].normal_image != nullptr &&
                captured->ranges()[0].normal_image->pixels32 == norm_a.pixels32 &&
                captured->ranges()[2].normal_image != nullptr &&
                captured->ranges()[2].normal_image->pixels32 == norm_b.pixels32,
            "Captured normal pixels mismatch");
    require(captured->ranges()[0].height_binding != nullptr &&
                captured->ranges()[0].height_binding->image != nullptr &&
                captured->ranges()[0].surface_parameters[0] == 0.65f &&
                captured->ranges()[2].height_binding != nullptr &&
                captured->ranges()[2].surface_parameters[0] == 0.8f,
            "Captured height binding or surface parameters missing");
    require(Hook::validate_captured_original_rigid(*renderer, *captured),
            "Fresh capture failed producer validation");
    require(!Hook::validate_captured_original_rigid(*other_renderer, *captured),
            "Cross-renderer owner validation succeeded");

    const auto mats = zmod::copy_rigid_materials(rig.model, *captured->resource());
    bool old_rejected = false;
    try {
      (void)Hook::native_geometry_admissions(*renderer, captured->resource(), rig.context, mats);
    } catch (const std::runtime_error &e) {
      old_rejected = std::string_view(e.what()).find("not its live original model") !=
                     std::string_view::npos;
    }
    require(old_rejected,
            "Old native_geometry_admissions accepted uncached independent resource");

    // Baseline cache identity guard positive + negative behavior.
    auto reg_base = zmod::register_rigid_source(rig.model);
    rig.model.render_geometry = reg_base.resource;
    rig.model.render_materials = reg_base.original_materials;
    const auto base_adm =
        Hook::native_geometry_admissions(*renderer, reg_base.resource, rig.context, mats);
    require(base_adm.size() == 3 && base_adm[0].height_binding != nullptr,
            "Baseline native_geometry_admissions failed with matching live caches");
    rig.model.render_materials[1] = &rig.mat_b;
    bool slot_rejected = false;
    try {
      (void)Hook::native_geometry_admissions(*renderer, reg_base.resource, rig.context, mats);
    } catch (const std::runtime_error &e) {
      slot_rejected =
          std::string_view(e.what()).find("material-slot mismatch") != std::string_view::npos;
    }
    require(slot_rejected,
            "Baseline native_geometry_admissions missed mismatched render_materials slot");
    rig.model.invalidate_render_geometry();
    ++exercised_cases;
  }

  // 2. Poisoned model caches + 14-polygon pattern + reordered polygon rejection.
  {
    RigFixture rig14(handle_a, handle_b, 14);
    install_targets({make_target(rig14, budget)});
    float poison_pos[]{9, 9, 9, 8, 8, 8, 7, 7, 7};
    std::uint32_t poison_idx[]{0, 1, 2};
    const auto poison_res = cc::geometry::register_resource(
        poison_pos, 3, nullptr, 0, {{3, poison_idx, nullptr, nullptr, false, false, 0}});
    zmod::Material poison_mat{};
    const std::vector<const zmod::Material *> poison_mats{&poison_mat};
    rig14.model.render_geometry = poison_res;
    rig14.model.render_materials = poison_mats;

    const auto captured14 = Hook::capture_original_rigid(
        *renderer, rig14.node, rig14.context, rig14.eligibility, 2 * 1024 * 1024);
    require(captured14 != nullptr && captured14->ranges().size() == 14 &&
                captured14->resource() != poison_res &&
                rig14.model.render_geometry == poison_res &&
                rig14.model.render_materials == poison_mats,
            "14-polygon capture failed or altered poisoned model caches");

    std::swap(rig14.polygons[2].material, rig14.polygons[3].material);
    bool reorder_rejected = false;
    try {
      (void)Hook::capture_original_rigid(
          *renderer, rig14.node, rig14.context, rig14.eligibility, 2 * 1024 * 1024);
    } catch (const std::runtime_error &) {
      reorder_rejected = true;
    }
    std::swap(rig14.polygons[2].material, rig14.polygons[3].material);
    require(reorder_rejected && rig14.model.render_geometry == poison_res &&
                rig14.model.render_materials == poison_mats,
            "Reordered polygon materials did not reject or altered poisoned caches");
    ++exercised_cases;
  }

  // 3. Retained capture immunity to source/target mutation + fresh capture rejection on mutated mesh/UV.
  {
    RigFixture rig(handle_a, handle_b, 3);
    const auto orig_target = make_target(rig, budget);
    install_targets({orig_target});
    const auto budget_before = budget->used();
    const auto captured = Hook::capture_original_rigid(
        *renderer, rig.node, rig.context, rig.eligibility, 1024 * 1024);
    require(captured != nullptr && budget_before > 0,
            "Capture before post-mutation checks failed");

    // Release environment target pack: captured height image alias keeps decoded reservation alive.
    Hook::set_mission_and_environment(*renderer, "t1m1", nullptr);
    require(budget->used() == budget_before,
            "Captured height binding did not retain decoded pack reservation after target drop");

    // Mutate source UV/position arrays after capture: owned snapshot stays intact.
    rig.positions[0] = -99.f;
    rig.uvs[0] = 0.5f;
    require(captured->resource()->vertices[2].x == -1.f &&
                captured->resource()->vertices[2].u == 0.f &&
                captured->ranges()[0].albedo_image->pixels32 == albedo_a &&
                Hook::validate_captured_original_rigid(*renderer, *captured),
            "Source array mutation after capture altered owned capture or broke stamp validation");

    // Fresh capture with original target must reject changed source.
    install_targets({orig_target});
    bool changed_source_rejected = false;
    try {
      (void)Hook::capture_original_rigid(
          *renderer, rig.node, rig.context, rig.eligibility, 1024 * 1024);
    } catch (const std::runtime_error &e) {
      changed_source_rejected =
          std::string_view(e.what()).find("mesh/UV mismatch") != std::string_view::npos;
    }
    require(changed_source_rejected,
            "Fresh capture after source mutation did not reject incompatible authored target");
    ++exercised_cases;
  }

  // 4. Individual identity/stamp/image rejections and distinct untextured/no_normal policies.
  {
    RigFixture base_rig(handle_a, handle_b, 3);
    const auto base_target = make_target(base_rig, budget);

    auto expect_capture_throws = [&](auto setup_fn, const char *label) {
      RigFixture rig(handle_a, handle_b, 3);
      auto target = base_target;
      setup_fn(rig, target);
      install_targets({std::move(target)});
      const auto scene_before = renderer->scene_binding_statistics();
      std::fesetround(FE_DOWNWARD);
      bool threw = false;
      try {
        (void)Hook::capture_original_rigid(
            *renderer, rig.node, rig.context, rig.eligibility, 1024 * 1024);
      } catch (const std::runtime_error &) {
        threw = true;
      }
      require(std::fegetround() == FE_DOWNWARD, "Failed capture did not restore FP state");
      std::fesetround(FE_TONEAREST);
      const auto scene_after = renderer->scene_binding_statistics();
      require(threw && scene_after.commands == scene_before.commands &&
                  !rig.model.render_geometry && rig.model.render_materials.empty(),
              label);
      ++exercised_cases;
    };

    auto expect_known_unselected = [&](auto change_source, const char *label) {
      RigFixture rig(handle_a, handle_b, 3);
      change_source(rig);
      install_targets({base_target});
      const auto scene_before = renderer->scene_binding_statistics();
      struct RestoreFloat {
        std::fenv_t saved{};
        RestoreFloat() {
          require(std::fegetenv(&saved) == 0, "Cannot preserve unselected fixture FP state");
        }
        ~RestoreFloat() { std::fesetenv(&saved); }
      } restore_float;
      std::fesetround(FE_DOWNWARD);
      std::feclearexcept(FE_ALL_EXCEPT);
      std::feraiseexcept(FE_DIVBYZERO);
      const auto captured = Hook::capture_original_rigid(
          *renderer, rig.node, rig.context, rig.eligibility, 1024 * 1024);
      require(captured && !captured->resource()->vertices.empty() &&
                  captured->ranges().size() == 3 &&
                  Hook::validate_captured_original_rigid(*renderer, *captured) &&
                  std::all_of(captured->ranges().begin(), captured->ranges().end(),
                              [](const auto &range) { return !range.height_binding; }),
              label);
      require(std::fegetround() == FE_DOWNWARD &&
                  std::fetestexcept(FE_ALL_EXCEPT) == FE_DIVBYZERO,
              "Unselected capture changed caller FP state");

      // Selection leaves this known source ordinary. Direct selected admission
      // must still reject its identity against the original target.
      const auto &range = captured->ranges().front();
      cc_mw3_re::NativeGroundHeightInput input;
      input.enabled = assets.pom;
      input.eligible = cc_mw3_re::native_ground_eligible(rig.context);
      input.node = &rig.node;
      input.model = &rig.model;
      input.material = {&rig.model, rig.polygons[0].material,
                        rig.polygons[0].material->texture, 0};
      input.key = input.slot_key = range.albedo_key;
      input.texture = range.texture_handle;
      input.normal_index = range.normal_index;
      input.normal_width = range.normal_width;
      input.normal_height = range.normal_height;
      input.normal_hash = range.normal_hash;
      input.source_epoch = zcls::world_source_epoch();
      input.producer_epoch = captured->group_load_epoch();
      input.current_group_epoch = Hook::group_epoch(*renderer);
      input.slot_epoch = range.texture_group_epoch;
      input.texture_version = input.current_texture_version = range.texture_version;
      bool selected_identity_rejected = false;
      try {
        (void)cc_mw3_re::admit_native_ground_height(base_target, input, budget);
      } catch (const std::runtime_error &error) {
        selected_identity_rejected = std::string_view(error.what()) ==
                                     "Native ground source identity/epoch mismatch";
      }
      const auto scene_after = renderer->scene_binding_statistics();
      require(selected_identity_rejected && !rig.model.render_geometry &&
                  rig.model.render_materials.empty() &&
                  scene_after.commands == scene_before.commands &&
                  scene_after.draws == scene_before.draws &&
                  scene_after.textures == scene_before.textures &&
                  std::fegetround() == FE_DOWNWARD &&
                  std::fetestexcept(FE_ALL_EXCEPT) == FE_DIVBYZERO,
              "Unselected source weakened direct selected admission or changed producer state");
      ++exercised_cases;
    };

    expect_capture_throws(
        [](RigFixture &, ::platform::prepared::MaterialTarget &t) { t.source.bytes += 4; },
        "Wrong source bytes did not reject");
    expect_capture_throws(
        [](RigFixture &, ::platform::prepared::MaterialTarget &t) {
          t.source.sha256[0] = 'f';
        },
        "Wrong source SHA-256 did not reject");
    expect_capture_throws(
        [](RigFixture &, ::platform::prepared::MaterialTarget &t) { t.source.kind = "bad"; },
        "Wrong source kind did not reject");
    expect_capture_throws(
        [](RigFixture &r, ::platform::prepared::MaterialTarget &) {
          r.mat_a.r = std::numeric_limits<float>::quiet_NaN();
        },
        "Owned factory accepted nonfinite RGB after geometry preflight");
    expect_known_unselected(
        [](RigFixture &r) { r.source_asset->world->member = "other.zmd"; },
        "Known foreign member did not retain ordinary owned capture without height");
    expect_known_unselected(
        [](RigFixture &r) { r.source_asset->world->model_slot = 99; },
        "Known foreign model slot did not retain ordinary owned capture without height");
    expect_capture_throws(
        [](RigFixture &r, ::platform::prepared::MaterialTarget &) {
          r.source_asset->world->load_epoch += 5;
        },
        "Wrong source load_epoch did not reject");
    expect_capture_throws(
        [](RigFixture &r, ::platform::prepared::MaterialTarget &) {
          r.node.source_asset = std::make_shared<zcls::SourceAsset>(*r.source_asset);
        },
        "Node/model source_asset owner mismatch did not reject");
    expect_capture_throws(
        [](RigFixture &r, ::platform::prepared::MaterialTarget &) {
          r.node.source_asset.reset();
          r.model.world_source_asset.reset();
        },
        "Missing source owner for selected raw model slot did not reject");
    expect_capture_throws(
        [](RigFixture &, ::platform::prepared::MaterialTarget &t) {
          t.polygon_materials[2] = "wrong_name";
        },
        "Wrong ordered polygon material name did not reject");
    expect_capture_throws(
        [](RigFixture &, ::platform::prepared::MaterialTarget &t) { t.sidecar_path.clear(); },
        "Empty sidecar path did not reject");
    expect_capture_throws(
        [](RigFixture &, ::platform::prepared::MaterialTarget &t) { t.sidecar_sha256 = "bad"; },
        "Invalid sidecar SHA-256 did not reject");
    expect_capture_throws(
        [&](RigFixture &r, ::platform::prepared::MaterialTarget &t) {
          auto other_budget = std::make_shared<mw34::materials::SurfaceDecodedBudget>();
          t = make_target(r, other_budget);
        },
        "Wrong sidecar decoded-budget owner did not reject");
    expect_capture_throws(
        [&](RigFixture &, ::platform::prepared::MaterialTarget &t) {
          t.surface_keys[2] = key_a; // Later range 2 fails after ranges 0 and 1 succeed.
        },
        "Later-range surface key mismatch did not reject cleanly");

    // Ambiguous duplicate target rejection.
    {
      RigFixture rig(handle_a, handle_b, 3);
      install_targets({base_target, base_target});
      bool ambiguous_threw = false;
      try {
        (void)Hook::capture_original_rigid(
            *renderer, rig.node, rig.context, rig.eligibility, 1024 * 1024);
      } catch (const std::runtime_error &e) {
        ambiguous_threw =
            std::string_view(e.what()).find("Ambiguous") != std::string_view::npos;
      }
      require(ambiguous_threw, "Ambiguous duplicate target did not reject");
      ++exercised_cases;
    }

    // Texture group epoch, released pixels, normal record corruption, and no_normal rejections.
    {
      RigFixture rig(handle_a, handle_b, 3);
      install_targets({base_target});
      const auto orig_epoch = Hook::group_epoch(*renderer);
      Hook::set_slot_group_epoch(*renderer, handle_b, orig_epoch + 1);
      bool epoch_threw = false;
      try {
        (void)Hook::capture_original_rigid(
            *renderer, rig.node, rig.context, rig.eligibility, 1024 * 1024);
      } catch (const std::runtime_error &) {
        epoch_threw = true;
      }
      Hook::set_slot_group_epoch(*renderer, handle_b, orig_epoch);
      require(epoch_threw, "Mismatched texture slot group epoch did not reject");

      Hook::set_slot_pixels(*renderer, handle_b, 4, 4, {});
      bool empty_pixels_threw = false;
      try {
        (void)Hook::capture_original_rigid(
            *renderer, rig.node, rig.context, rig.eligibility, 1024 * 1024);
      } catch (const std::runtime_error &) {
        empty_pixels_threw = true;
      }
      Hook::set_slot_pixels(*renderer, handle_b, 4, 4, albedo_b);
      require(empty_pixels_threw, "Released empty texture slot pixels did not reject");

      Hook::mutate_normal_record(*renderer, 1, 2, 2, 0ULL, norm_b.pixels32);
      bool zero_norm_hash_threw = false;
      try {
        (void)Hook::capture_original_rigid(
            *renderer, rig.node, rig.context, rig.eligibility, 1024 * 1024);
      } catch (const std::runtime_error &) {
        zero_norm_hash_threw = true;
      }
      Hook::mutate_normal_record(*renderer, 1, norm_b.width, norm_b.height, norm_b.hash,
                                 norm_b.pixels32);
      require(zero_norm_hash_threw, "Corrupted normal hash did not reject selected height");

      Hook::seed_authored_no_normal(*renderer, key_b);
      bool no_normal_height_threw = false;
      try {
        (void)Hook::capture_original_rigid(
            *renderer, rig.node, rig.context, rig.eligibility, 1024 * 1024);
      } catch (const std::runtime_error &) {
        no_normal_height_threw = true;
      }
      require(no_normal_height_threw,
              "Required height binding with authored no_normal did not reject");

      // Distinct valid policy: no-height + authored no_normal on polygon 2.
      install_targets({make_target(rig, budget, false, true)});
      const auto no_norm_cap = Hook::capture_original_rigid(
          *renderer, rig.node, rig.context, rig.eligibility, 1024 * 1024);
      require(no_norm_cap != nullptr && no_norm_cap->ranges()[2].albedo_image != nullptr &&
                  no_norm_cap->ranges()[2].normal_index == -1 &&
                  no_norm_cap->ranges()[2].normal_image == nullptr &&
                  no_norm_cap->ranges()[2].height_binding == nullptr &&
                  Hook::validate_captured_original_rigid(*renderer, *no_norm_cap),
              "Valid absent-height + no_normal policy failed capture or validation");
      Hook::seed_authored_normal(*renderer, key_b, norm_b);

      // Distinct valid policy: untextured polygon 2.
      RigFixture untex_rig(handle_a, handle_b, 3);
      untex_rig.mat_b.flags = 0;
      untex_rig.mat_b.texture = nullptr;
      untex_rig.polygons[2].uvs = nullptr;
      install_targets({make_target(untex_rig, budget, true, false)});
      const auto untex_cap = Hook::capture_original_rigid(
          *renderer, untex_rig.node, untex_rig.context, untex_rig.eligibility, 1024 * 1024);
      require(untex_cap != nullptr && untex_cap->ranges()[0].height_binding != nullptr &&
                  untex_cap->ranges()[2].texture_handle == -1 &&
                  untex_cap->ranges()[2].albedo_image == nullptr &&
                  untex_cap->ranges()[2].normal_index == -1 &&
                  untex_cap->ranges()[2].normal_image == nullptr &&
                  untex_cap->ranges()[2].height_binding == nullptr &&
                  Hook::validate_captured_original_rigid(*renderer, *untex_cap),
              "Valid untextured range policy failed capture or validation");
      ++exercised_cases;
    }
  }

  // 5. Exact logical byte budget admission vs one-byte-under rejection.
  {
    RigFixture rig(handle_a, handle_b, 3);
    const auto target = make_target(rig, budget);
    install_targets({target});
    const auto probe = Hook::capture_original_rigid(
        *renderer, rig.node, rig.context, rig.eligibility, 1024 * 1024);
    require(probe != nullptr, "Budget probe capture failed");
    std::size_t exact_bytes = zmod::preflight_rigid_source_bytes(rig.model) +
                              sizeof(cc_mw3_re::CapturedNativeRigid) +
                              3 * sizeof(cc_mw3_re::CapturedNativeRigidRange) +
                              4 * sizeof(cc_mw3_re::CapturedRgbaImage) +
                              (albedo_a.size() + albedo_b.size() + norm_a.pixels32.size() +
                               norm_b.pixels32.size()) *
                                  sizeof(std::uint32_t) +
                              std::size_t(probe->ranges()[0].height_binding->retained_decoded_bytes);
    for (const auto &r : probe->ranges())
      exact_bytes += mw34::materials::height_binding_metadata_bytes(*r.height_binding);

    const auto exact_cap = Hook::capture_original_rigid(
        *renderer, rig.node, rig.context, rig.eligibility, exact_bytes);
    require(exact_cap != nullptr, "Exact logical byte budget was rejected");

    const auto scene_before = renderer->scene_binding_statistics();
    bool under_budget_threw = false;
    try {
      (void)Hook::capture_original_rigid(
          *renderer, rig.node, rig.context, rig.eligibility, exact_bytes - 1);
    } catch (const std::runtime_error &e) {
      under_budget_threw =
          std::string_view(e.what()).find("maximum_owned_bytes") != std::string_view::npos;
    }
    const auto scene_after = renderer->scene_binding_statistics();
    require(under_budget_threw && scene_after.commands == scene_before.commands &&
                !rig.model.render_geometry && rig.model.render_materials.empty(),
            "One-byte-under budget did not reject cleanly");
    ++exercised_cases;
  }

  // 6. Unsupported rigid family returns nullptr; malformed context/counts throw.
  {
    RigFixture rig(handle_a, handle_b, 3);
    install_targets({make_target(rig, budget)});
    rig.eligibility.second_pass = true;
    require(Hook::capture_original_rigid(
                *renderer, rig.node, rig.context, rig.eligibility, 1024 * 1024) == nullptr,
            "Second-pass eligibility did not return nullptr");
    rig.eligibility.second_pass = false;

    rig.polygons[2].priority = 1;
    require(Hook::capture_original_rigid(
                *renderer, rig.node, rig.context, rig.eligibility, 1024 * 1024) == nullptr,
            "Unsupported polygon priority did not return nullptr");
    rig.polygons[2].priority = 0;

    rig.context.source_vertices = 99;
    bool bad_context_threw = false;
    try {
      (void)Hook::capture_original_rigid(
          *renderer, rig.node, rig.context, rig.eligibility, 1024 * 1024);
    } catch (const std::runtime_error &) {
      bad_context_threw = true;
    }
    rig.context.source_vertices = 4;
    require(bad_context_threw, "Mismatched context vertex count did not throw");
    ++exercised_cases;
  }

  // 7. Producer stamp invalidation and post-capture lifetime retirement.
  {
    std::shared_ptr<const cc_mw3_re::CapturedNativeRigid> retained;
    {
      RigFixture rig(handle_a, handle_b, 3);
      install_targets({make_target(rig, budget)});
      retained = Hook::capture_original_rigid(
          *renderer, rig.node, rig.context, rig.eligibility, 1024 * 1024);
      require(retained != nullptr && Hook::validate_captured_original_rigid(*renderer, *retained),
              "Retained capture failed initial validation");
      Hook::set_mission_and_environment(*renderer, "t1m1", nullptr);
    }
    require(budget->used() > 0 && retained->resource()->vertices.size() == 9 &&
                retained->ranges()[0].albedo_image->pixels32 == albedo_a &&
                retained->ranges()[0].normal_image->pixels32 == norm_a.pixels32 &&
                retained->ranges()[0].height_binding->image->pixels.size() == 16,
            "Destroyed producer fixture invalidated owned capture or decoded reservation");

    const auto orig_ver = retained->ranges()[0].texture_version;
    Hook::set_slot_version(*renderer, handle_a, orig_ver + 1);
    require(!Hook::validate_captured_original_rigid(*renderer, *retained),
            "Texture version advance did not invalidate producer replay check");
    Hook::set_slot_version(*renderer, handle_a, orig_ver);
    require(Hook::validate_captured_original_rigid(*renderer, *retained),
            "Restored texture version did not pass validation");

    Hook::advance_group_epoch(*renderer);
    require(!Hook::validate_captured_original_rigid(*renderer, *retained),
            "Group epoch advance did not invalidate producer replay check");

    (void)zcls::invalidate_world_source_proofs();
    require(!Hook::validate_captured_original_rigid(*renderer, *retained),
            "World source epoch advance did not invalidate producer replay check");

    retained.reset();
    require(budget->used() == 0,
            "Retiring last captured height binding alias did not release decoded budget");
    ++exercised_cases;
  }

  require(exercised_cases >= 20, "Owned rigid capture check suite ran too few cases");
  std::fprintf(stderr, "Owned rigid capture checks: %u cases passed\n", exercised_cases);
}
