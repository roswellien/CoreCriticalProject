// Included inside Stage. The first producer owns flat, opaque, unclipped static
// meshes under the existing per-pixel sun path. Cell/LOD dispatch remains original.
struct NativeStaticMaterial {
    unsigned material{}, texture{}, address_u{}, address_v{};
};
struct NativeStaticPlan {
    D3DDev *device{};
    OverrideMatrix predicted{};
    std::shared_ptr<mw34::native_static::Fog> fog;
    std::vector<NativeStaticMaterial> materials;
};
std::uint64_t native_static_meshes{}, native_static_polygons{}, native_static_vertices{};
std::map<const char *, std::uint64_t> native_static_rejections;
std::map<unsigned, std::uint64_t> native_static_unknown_lights;

// Extend the existing bridge receipt: an equal image with zero admission does
// not demonstrate that any original producer work was removed.
void native_static_metrics() {
    if (!mw34::native_static::enabled()) return;
    world_log << ",\"native_static\":{\"meshes\":" << native_static_meshes
              << ",\"polygons\":" << native_static_polygons
              << ",\"source_vertices\":" << native_static_vertices << ",\"rejections\":{";
    bool comma = false;
    for (const auto &[reason, count] : native_static_rejections) {
        if (comma) world_log << ',';
        world_log << '\"' << reason << "\":" << count;
        comma = true;
    }
    world_log << "},\"unknown_light_flags\":{";
    comma = false;
    for (const auto &[flags, count] : native_static_unknown_lights) {
        if (comma) world_log << ',';
        world_log << '\"' << flags << "\":" << count;
        comma = true;
    }
    world_log << "}}";
}

std::array<float, 3> native_static_point(const OverrideMatrix &matrix,
                                        const mw34::vkscene::ModelVertex &vertex) {
    std::array<float, 3> result{};
    for (unsigned row = 0; row < 3; ++row) {
        const auto offset = row * 4;
        const double xy = double(vertex.x) * matrix[offset] +
                          double(vertex.y) * matrix[offset + 1];
        result[row] = float((xy + double(vertex.z) * matrix[offset + 2]) + matrix[offset + 3]);
    }
    return result;
}

// This small CPU visibility decision remains until the shadow and temporal
// consumers can share GPU visibility. No per-frame transformed vertex stream is built.
bool native_static_visible(const WorldPolygon &polygon, const OverrideMatrix &matrix) {
    const auto count = polygon.corners.size();
    const auto a = native_static_point(matrix, polygon.corners[count - 1].vertex);
    const auto b = native_static_point(matrix, polygon.corners[count - 2].vertex);
    const auto c = native_static_point(matrix, polygon.corners[count - 3].vertex);
    const double ax = double(a[0]) - b[0], ay = double(a[1]) - b[1], az = double(a[2]) - b[2];
    const double bx = double(c[0]) - b[0], by = double(c[1]) - b[1], bz = double(c[2]) - b[2];
    const float nx = float(ay * bz - az * by);
    const float ny = float(az * bx - ax * bz);
    const float nz = float(ax * by - ay * bx);
    const float plane = float((double(nx) * a[0] + double(ny) * a[1]) + double(nz) * a[2]);
    const float epsilon = world_float(0x5ef73c);
    return plane < -epsilon || ((polygon.flags & 0x100) && plane > epsilon);
}

bool native_static_bounds(const WorldScope &scope, const OverrideMatrix &matrix,
                          const mw34::native_static::Fog &fog, unsigned width, unsigned height,
                          const char **reason = nullptr) {
    auto reject = [&](const char *value) { if (reason) *reason = value; return false; };
    std::array<float, 3> lower{}, upper{};
    bool first = true;
    for (const auto &polygon : *scope.polygons)
        for (const auto &corner : polygon.corners) {
            const auto &v = corner.vertex;
            const std::array<float, 3> point{v.x, v.y, v.z};
            if (first) lower = upper = point;
            for (unsigned i = 0; i < 3; ++i) {
                lower[i] = std::min(lower[i], point[i]);
                upper[i] = std::max(upper[i], point[i]);
            }
            first = false;
        }
    if (first) return reject("empty-bounds");
    std::array<float, 3> camera_lower{}, camera_upper{};
    float maximum_height = -std::numeric_limits<float>::max();
    const float near_scale = world_float(0x73fb80), near_clip = world_float(0x740304);
    const float scale_x = world_float(0x73fc30), scale_y = world_float(0x73fb98);
    const float center_x = world_float(0x73fb88), center_y = world_float(0x73fb8c);
    const unsigned camera = load(0x7402f4);
    const float far_clip = world_float(camera + 0xb4);
    for (unsigned corner = 0; corner < 8; ++corner) {
        mw34::vkscene::ModelVertex vertex{};
        vertex.x = (corner & 1) ? upper[0] : lower[0];
        vertex.y = (corner & 2) ? upper[1] : lower[1];
        vertex.z = (corner & 4) ? upper[2] : lower[2];
        const auto p = native_static_point(matrix, vertex);
        if (!corner) camera_lower = camera_upper = p;
        for (unsigned i = 0; i < 3; ++i) {
            camera_lower[i] = std::min(camera_lower[i], p[i]);
            camera_upper[i] = std::max(camera_upper[i], p[i]);
        }
        if (!(p[2] > near_clip + 1.f && p[2] < far_clip - 1.f)) return reject("depth-bounds");
        const double x = double(p[0]) * scale_x * near_scale / p[2] + center_x;
        const double y = double(p[1]) * scale_y * near_scale / p[2] + center_y;
        if (!(x > 2 && y > 2 && x < double(width) - 2 && y < double(height) - 2)) return reject("screen-bounds");
        double h = double(p[0]) * fog.height_row[0] + double(p[1]) * fog.height_row[1];
        h = (h + double(p[2]) * fog.height_row[2]) + fog.height_row[3];
        maximum_height = std::max(maximum_height, float(h));
    }
    // A complete positive fog range makes the original fog-colour side effect
    // decidable without a vertex readback. Near/height-transition meshes stay original.
    if (!(maximum_height < fog.height[1] - 1.f)) return reject("height-bounds");
    double minimum_squared = 0, maximum_squared = 0;
    for (unsigned axis : {0U, 2U}) {
        const double lo = camera_lower[axis], hi = camera_upper[axis];
        minimum_squared += lo <= 0 && hi >= 0 ? 0 : std::min(lo * lo, hi * hi);
        maximum_squared += std::max(lo * lo, hi * hi);
    }
    if (!(minimum_squared > fog.distance[1] + 4 && maximum_squared < fog.distance[2] - 4)) return reject("radial-bounds");
    const float minimum_radius = std::bit_cast<float>((std::bit_cast<unsigned>(float(minimum_squared)) >> 1) + 0x1fc00000U);
    if (!((minimum_radius - fog.distance[0]) * fog.distance[3] > .01f)) return reject("fog-bounds");
    const unsigned lights = load(0x74981c);
    if (!lights || lights > 64) return reject("light-count");
    unsigned directional = 0;
    for (unsigned i = 0; i < lights; ++i) {
        const unsigned object = load(0x749824 + i * 20);
        if (!object || !readable(object + 0x78, 0x50)) return reject("light-source");
        const unsigned flags = load(object + 0xb0);
        if (flags & 8) {
            if (flags != 0x38a || load(object + 0xa4) != 0x3f800000 ||
                load(object + 0xa8) != 0x3f800000 || load(object + 0xac) != 0x3f800000)
                return reject("directional-light");
            ++directional;
            continue;
        }
        // sub_00543D90 clears both contribution words for this inactive
        // point-light family: bit2 is set, bit0x200 is clear. The original
        // required selection helper below still performs those writes.
        if (flags == 0x52) continue;
        if (flags != 0x252) {
            if (native_static_unknown_lights.size() < 16 || native_static_unknown_lights.count(flags))
                ++native_static_unknown_lights[flags];
            return reject("light-family");
        }
        double distance_squared = 0;
        for (unsigned axis = 0; axis < 3; ++axis) {
            const double position = world_float(object + 0x78 + axis * 4);
            const double distance = std::max({double(camera_lower[axis]) - position, 0.0,
                                              position - double(camera_upper[axis])});
            distance_squared += distance * distance;
        }
        const double radius = world_float(object + 0xb8);
        if (!(radius >= 0 && distance_squared > (radius + 2) * (radius + 2))) return reject("point-light-bounds");
    }
    return directional == 1 || reject("directional-count");
}

std::optional<NativeStaticPlan> native_static_plan() {
    SunCaptureFp preserve;
    mw34::vkscene::HostFpEnvironment fp;
    auto reject = [&](const char *reason) -> std::optional<NativeStaticPlan> {
        ++native_static_rejections[reason];
        return std::nullopt;
    };
    if (!world_scope || world_scope->temporal_only || !world_cell_depth || frontend_on() ||
        wide_hud_role() != WideWorld || override_suppress_draw() ||
        photo_replay.mode != mw34::photo_replay::Mode::Live)
        return reject("scope");
    const char *replay = std::getenv("MW34_INSTANT_REPLAY");
    if (!replay || std::strcmp(replay, "0")) return reject("replay");
    if (!mw34::sun::settings().enabled || !mw34::vkscene::Renderer::gpu_models()) return reject("lighting");
    const auto &scope = *world_scope;
    if (load(scope.mesh) || load(scope.mesh + 8) != 3 || load(scope.mesh + 0xc) < 2 ||
        load(scope.mesh + 0x18) || load(scope.mesh + 0x1c) || load(scope.mesh + 0x20) ||
        scope.polygons->size() != load(scope.mesh + 0x10)) return reject("mesh-family");
    unsigned short control{};
    std::memcpy(&control, reinterpret_cast<const unsigned char *>(&state) + 0xad0, 2);
    if ((control & 0xf3f) != 0x23f) return reject("fp-domain");
    if (load(0x7489a8) || load(0x74a264) || load(0x5ef860) || load(0x74a270) ||
        !load(0x74a22c) || load(0x74a268) || load(0x74a26c) != 0x3f800000 ||
        load(0x72f3c4) != 0x57d160 || load(0x72f3c8) != 0x57d690)
        return reject("render-domain");
    NativeStaticPlan plan;
    plan.device = device(vsurf_root(load(0x809370)));
    if (!plan.device || !plan.device->in_scene ||
        plan.device->rs[D3DRENDERSTATE_ALPHATESTENABLE] ||
        plan.device->rs[D3DRENDERSTATE_ALPHABLENDENABLE]) return reject("opaque-scene");
    const auto *surface = vsurface(plan.device->target);
    if (!surface) return reject("target");
    OverrideMatrix camera_world;
    if (!sun_camera_world(camera_world)) return reject("camera");
    plan.predicted = override_product(override_matrix(0x73fbc0), override_matrix(load(load(0x5eda90))));
    for (auto &value : plan.predicted) value = float(value);
    plan.fog = std::make_shared<mw34::native_static::Fog>();
    plan.fog->distance = {world_float(0x74a240), world_float(0x74a244),
                          world_float(0x74a24c), world_float(0x74a250)};
    plan.fog->height = {world_float(0x74a254), world_float(0x74a258), world_float(0x74a25c), 1};
    plan.fog->height_row = {world_float(0x73fc04), world_float(0x73fc10),
                            world_float(0x73fc1c), world_float(0x73fc28)};
    if (!(plan.fog->distance[0] >= 0 && plan.fog->distance[3] > 0 &&
          plan.fog->height[0] > plan.fog->height[1] && plan.fog->height[2] > 0)) return reject("fog");
    const char *bounds_rejection{};
    if (!native_static_bounds(scope, plan.predicted, *plan.fog, surface->width, surface->height,
                              &bounds_rejection)) return reject(bounds_rejection);
    for (const auto &polygon : *scope.polygons) {
        if ((polygon.flags & ~0x1ffU) || !polygon.resident || load(polygon.source + 4) ||
            !polygon.material || !readable(polygon.material, 20) ||
            load(polygon.material) != 0x7fff11ff) return reject("polygon-material");
        const unsigned reference = load(polygon.material + 16);
        if (!reference || !readable(reference, 8)) return reject("texture-reference");
        const unsigned wrapper = load(reference + 4);
        if (!wrapper || !readable(wrapper, 24) || load(wrapper + 12) != 1)
            return reject("texture-family");
        const unsigned texture = vsurf_root(load(wrapper + 8));
        if (!texture || !vsurface(texture) || texture != load(wrapper + 4)) return reject("texture-owner");
        const unsigned u = load(wrapper + 16), v = load(wrapper + 20);
        if (u < 1 || u > 3 || v < 1 || v > 3) return reject("texture-address");
        plan.materials.push_back({polygon.material, texture, u, v});
    }
    return plan;
}

void native_static_fog_state(unsigned below) {
    std::array<unsigned, 3> colors{};
    {
        SunCaptureFp preserve;
        mw34::vkscene::HostFpEnvironment fp;
        const float scale = world_float(0x5ce550);
        for (unsigned i = 0; i < 3; ++i) {
            const float value = float(double(world_float(0x74a234 + i * 4)) * scale);
            colors[i] = std::bit_cast<unsigned>(value);
        }
    }
    bool changed = false;
    for (unsigned i = 0; i < 3; ++i) {
        store(0x72f3f4 + i * 4, colors[i]);
        changed |= load(0x72f400 + i * 4) != colors[i];
    }
    if (changed) {
        for (unsigned i = 0; i < 3; ++i) store(0x72f400 + i * 4, colors[i]);
        (void)call_guest(load(0x72f3f0), {}, false, "native static fog colour", below);
    }
}

void native_static_bind(D3DDev &device, const NativeStaticMaterial &material) {
    const bool reuse = render_reuse_enabled();
    auto assign = [&](unsigned &slot, unsigned value) {
        if (!reuse || slot != value) { slot = value; ++device.epoch; }
    };
    if (load(0x80938c) != 2) {
        assign(device.rs[D3DRENDERSTATE_SHADEMODE], 2);
        store(0x80938c, 2);
    }
    device.textures[0] = material.texture;
    if (load(0x809390) != 2) {
        store(0x809390, 2);
        assign(device.tss[0][D3DTSS_ALPHAOP], 2);
    }
    for (const auto [address, state, value] : {
             std::array<unsigned,3>{0x809394, D3DTSS_ADDRESSU, material.address_u},
             std::array<unsigned,3>{0x809398, D3DTSS_ADDRESSV, material.address_v}}) {
        if (load(address) != value) { assign(device.tss[0][state], value); store(address, value); }
    }
}

bool native_static_produce(void *&result) {
    if (!mw34::native_static::enabled()) return false;
    auto selected = native_static_plan();
    if (!selected) return false;
    auto &plan = *selected;
    const auto &scope = *world_scope;
    const unsigned entry = state.gpr.rsp.dword, returned_pc = load(entry);
    const unsigned clip_flags = state.gpr.rdx.dword, below = entry - 0xc00;
    if (!writable(below - 128, 0xc84)) deny("Native static producer stack outside contract", entry);
    // sub_0051E9D0/0051FB30/0051EA00: original matrix push/compose/pop
    // (confirmed; source-bound helper decompilation and consumer audit, issue177).
    state.gpr.rcx.dword = scope.frame_base - 0xd0;
    (void)call_guest(0x51e9d0, {}, false, "native static matrix push", below);
    (void)call_guest(0x51fb30, {}, false, "native static matrix composition", below);
    store(0x74a3cc, 1);
    state.gpr.rcx.dword = scope.mesh;
    // sub_0053DAA0: required fog/light selection and initialization (confirmed;
    // original helper analysis retained privately for issue177; original call
    // site 0053F86C passes ESI, the mesh header, rather than the scene node).
    const unsigned lighting = call_guest(0x53daa0, {}, false, "native static light selection", below);
    if (lighting != 3) deny("Native static producer light selection changed", lighting);
    OverrideMatrix matrix;
    {
        SunCaptureFp preserve;
        mw34::vkscene::HostFpEnvironment fp;
        matrix = override_matrix(load(load(0x5eda90)));
        const auto *surface = vsurface(plan.device->target);
        if (!surface || !native_static_bounds(scope, matrix, *plan.fog, surface->width, surface->height))
            deny("Native static producer matrix changed its admitted bounds", scope.node);
    }
    native_static_fog_state(below);
    store(0x7402f8, clip_flags);
    store(scope.frame_base - 0x38, scope.mesh);
    for (size_t i = 0; i < scope.polygons->size(); ++i) {
        const auto &polygon = scope.polygons->at(i);
        bool visible;
        {
            SunCaptureFp preserve;
            mw34::vkscene::HostFpEnvironment fp;
            visible = native_static_visible(polygon, matrix);
        }
        if (!visible) continue;
        const auto &material = plan.materials.at(i);
        store(scope.frame_base - 0x34, polygon.source);
        store(scope.frame_base - 0x44, polygon.material);
        store(0x72f418, 6);
        native_static_bind(*plan.device, material);
        if (!plan.device->snap || plan.device->snap_epoch != plan.device->epoch) {
            plan.device->snap = std::make_shared<const std::vector<unsigned>>(snapshot(*plan.device));
            plan.device->snap_epoch = plan.device->epoch;
        }
        D3DCmd draw{};
        draw.kind = D3DCmd::Draw;
        draw.flags = D3DPT_TRIANGLEFAN;
        draw.texture = material.texture;
        draw.state_snapshot = plan.device->snap;
        draw.hud_role = WideWorld;
        draw.fixture_node = scope.node;
        draw.fixture_polygon = polygon.source;
        auto instance = std::make_shared<mw34::vkscene::ModelInstance>();
        instance->geometry = polygon.resident;
        instance->world = true;
        instance->native_fog = plan.fog;
        {
            SunCaptureFp preserve;
            mw34::vkscene::HostFpEnvironment fp;
            for (unsigned word = 0; word < 12; ++word) instance->camera[word] = float(matrix[word]);
            instance->projection = {world_float(0x73fb80), world_float(0x73fc30), world_float(0x73fb98),
                                    world_float(0x73fb88), world_float(0x73fb8c), world_float(0x740304)};
        }
        sun_capture_world(*instance, scope.node);
        if (!instance->sun_eligible) deny("Native static producer lost its authenticated world camera", scope.node);
        draw.model = std::move(instance);
        camera_capture(draw, plan.device->target);
        temporal_source_capture(draw);
        effect_observe(draw);
        plan.device->commands.push_back(std::move(draw));
        ++native_static_polygons;
        ++world_draws;
    }
    store(0x72f418, 6);
    (void)call_guest(0x51ea00, {}, false, "native static matrix pop", below);
    ++native_static_meshes;
    native_static_vertices += load(scope.mesh + 0x14);
    state.gpr.rax.dword = 0; // Native implementation completed the original void-like mesh operation.
    state.gpr.rsp.dword = entry + 4;
    state.gpr.rip.dword = returned_pc;
    result = __remill_function_return(&state, returned_pc, token_ptr);
    return true;
}
