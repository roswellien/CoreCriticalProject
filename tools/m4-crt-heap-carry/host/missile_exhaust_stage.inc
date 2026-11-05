// Authenticated original projectile visuals only; never changes the simulation.
struct MissileBinding {
    unsigned definition{}, descriptor{}, root{};
    std::uint64_t generation{};
};
struct MissileScope {
    MissileBinding binding;
    unsigned node{};
    double nozzle{}, radius{}, length{};
};
std::map<unsigned, MissileBinding> missile_roots;
std::map<unsigned, std::set<std::uint64_t>> missile_light_sources;
MissileScope missile_scope;
std::vector<MissileScope> missile_scope_stack;
std::uint64_t missile_generation{};
unsigned missile_context{}, missile_frame{~0U};
std::set<std::pair<unsigned, unsigned>> missile_emitted;
bool missile_enabled() {
    static const bool enabled = [] {
        const char *p = std::getenv("MW34_MISSILE_EXHAUST");
        if (!p || !*p || !std::strcmp(p, "1"))
            return true;
        if (!std::strcmp(p, "0"))
            return false;
        throw std::runtime_error("MW34_MISSILE_EXHAUST must be 0 or 1");
    }();
    return enabled;
}
bool missile_trace() {
    static const bool enabled = [] {
        const char *p = std::getenv("MW34_MISSILE_TRACE");
        return p && !std::strcmp(p, "1");
    }();
    return enabled;
}
void missile_retire(unsigned descriptor) {
    SunCaptureFp preserve;
    auto lights = missile_light_sources.find(descriptor);
    if (lights != missile_light_sources.end()) {
        for (auto id : lights->second)
            effect_lighting.lights.erase_tracked(id);
        missile_light_sources.erase(lights);
    }
    for (auto it = missile_roots.begin(); it != missile_roots.end();)
        if (it->second.descriptor == descriptor)
            it = missile_roots.erase(it);
        else
            ++it;
}
void missile_retire_root(unsigned root) {
    SunCaptureFp preserve;
    const auto found = missile_roots.find(root);
    if (found != missile_roots.end())
        missile_retire(found->second.descriptor);
}
void missile_sync() {
    const unsigned context = load(0x5f4c8c);
    if (context != missile_context || frontend_on()) {
        while (!missile_roots.empty())
            missile_retire(missile_roots.begin()->second.descriptor);
        missile_light_sources.clear();
        missile_scope = {};
        missile_context = context;
    }
    if (missile_frame != host.frames) {
        missile_frame = host.frames;
        missile_emitted.clear();
    }
}
bool missile_class(unsigned definition) {
    if (!definition || !readable(definition, 0x80))
        return false;
    const unsigned name = load(definition);
    if (!name || !readable(name, 16))
        return false;
    const auto text = pose_name(name, 16);
    return text == "LRM5" || text == "LRM10" || text == "LRM15" || text == "LRM20" ||
           text == "SRM2" || text == "SRM4" || text == "SRM6" || text == "StreakSRM2" ||
           text == "StreakSRM4" || text == "StreakSRM6";
}
void *missile_create_body(State *s, unsigned target, void *p, Body body) {
    const unsigned definition = state.gpr.rcx.dword;
    void *result = body(s, target, p);
    SunCaptureFp preserve;
    mw34::vkscene::HostFpEnvironment fp;
    missile_sync();
    const unsigned descriptor = state.gpr.rax.dword;
    if (!descriptor || !readable(descriptor, 0x590))
        return result;
    missile_retire(descriptor);
    if (!missile_class(definition))
        return result;
    const unsigned root = load(descriptor + 0x0c);
    if (!root || !readable(root, 0x64))
        return result;
    if (missile_roots.size() >= 256)
        missile_retire(missile_roots.begin()->second.descriptor);
    missile_retire_root(root);
    missile_roots[root] = {definition, descriptor, root, ++missile_generation};
    if (missile_trace())
        std::fprintf(stderr,
                     "MISSILE create frame=%u class=%s descriptor=%08x root=%08x generation=%llu\n",
                     host.frames, pose_name(load(definition), 16).c_str(), descriptor, root,
                     (unsigned long long)missile_generation);
    return result;
}
bool missile_live(const MissileBinding &b) {
    if (!readable(b.definition, 0x80) || !readable(b.descriptor, 0x590) ||
        !readable(b.root, 0x64) || load(b.descriptor + 0x0c) != b.root ||
        load(b.descriptor + 0x20) != 1 || world_float(b.descriptor + 0x58c) <= 0)
        return false;
    // State 1 alone is insufficient: the original pool also uses it for retired
    // descriptors. Require ownership by this definition's current active list.
    unsigned item = load(b.definition + 0x7c);
    for (unsigned i = 0; item && i < 4096; ++i) {
        if (item == b.descriptor)
            return true;
        if (!readable(item, 4))
            return false;
        item = load(item);
    }
    return false;
}
void missile_begin(unsigned node) {
    SunCaptureFp preserve;
    missile_scope_stack.push_back(missile_scope);
    missile_scope = {};
    if (missile_roots.empty() || !missile_enabled() || frontend_on() || override_status_preview())
        return;
    if (!readable(node, 0x64))
        return;
    // Reject all ordinary mech/scenery meshes before ancestor traversal or FP
    // preservation. Only the two complete original rocket body signatures enter.
    const unsigned mesh = load(node + 0x3c);
    if (!mesh || !readable(mesh, 0x48) || load(mesh) || load(mesh + 0x10) != 3 ||
        load(mesh + 0x14) != 9)
        return;
    const unsigned xyz = load(mesh + 0x38);
    if (!xyz || !readable(xyz, 108))
        return;
    unsigned char bytes[108];
    get_bytes(xyz, bytes, 108);
    std::uint64_t hash = 14695981039346656037ULL;
    for (unsigned char v : bytes) {
        hash ^= v;
        hash *= 1099511628211ULL;
    }
    if (hash != 0xaab40c79fd42c637ULL && hash != 0x1d8edb98d97dc01bULL)
        return;
    mw34::vkscene::HostFpEnvironment fp;
    missile_sync();
    const unsigned role = wide_hud_role();
    if (role != WideWorld && role != WideZoom)
        return;
    unsigned ancestor = node;
    auto binding = missile_roots.end();
    for (unsigned i = 0; ancestor && i < 16; ++i) {
        binding = missile_roots.find(ancestor);
        if (binding != missile_roots.end())
            break;
        ancestor = override_parent(ancestor);
    }
    if (binding == missile_roots.end())
        return;
    if (!missile_live(binding->second)) {
        missile_retire(binding->second.descriptor);
        return;
    }
    double lo = 1e20, hi = -1e20, radius = 0;
    for (unsigned i = 0; i < 9; ++i) {
        const double x = world_float(xyz + i * 12), y = world_float(xyz + i * 12 + 4),
                     z = world_float(xyz + i * 12 + 8);
        lo = std::min(lo, z);
        hi = std::max(hi, z);
        radius = std::max(radius, std::sqrt(x * x + y * y));
    }
    missile_scope = {binding->second, node, hi, radius, hi - lo};
}
void missile_end() {
    SunCaptureFp preserve;
    if (missile_scope_stack.empty())
        throw std::runtime_error("Missile exhaust scope underflow");
    missile_scope = missile_scope_stack.back();
    missile_scope_stack.pop_back();
}
void missile_emit() {
    if (!missile_scope.node || !missile_enabled())
        return;
    SunCaptureFp preserve;
    mw34::vkscene::HostFpEnvironment fp;
    const unsigned role = wide_hud_role();
    if (role != WideWorld && role != WideZoom)
        return;
    if (!missile_emitted.emplace(missile_scope.node, role).second)
        return;
    D3DDev *device = nullptr;
    for (auto &d : host.devices)
        if (d.in_scene) {
            if (device)
                throw std::runtime_error("Missile exhaust: ambiguous render scene");
            device = &d;
        }
    if (!device)
        return;
    const unsigned stack = load(0x5eda90);
    if (!stack || !readable(stack, 4) || !readable(load(stack), 48))
        throw std::runtime_error("Missile exhaust: original body matrix unavailable");
    const auto matrix = override_matrix(load(stack));
    mw34::missiles::Matrix flame_matrix{};
    std::copy_n(matrix.begin(), 12, flame_matrix.begin());
    const mw34::missiles::Projection projection{wide_float(0x73fb80), wide_float(0x73fc30),
                                                wide_float(0x73fb98), wide_float(0x73fb88),
                                                wide_float(0x73fb8c), wide_float(0x740304)};
    const auto &source = missile_scope;
    const auto id = (source.binding.generation << 32) | source.node;
    const double now = effect_time();
    const auto vertices = mw34::missiles::flame(flame_matrix, projection, source.nozzle,
                                                source.radius, source.length, now, id);
    if (vertices.empty())
        return;
    auto states = snapshot(*device);
    states[D3DRENDERSTATE_ALPHABLENDENABLE] = 1;
    states[D3DRENDERSTATE_SRCBLEND] = D3DBLEND_SRCALPHA;
    states[D3DRENDERSTATE_DESTBLEND] = D3DBLEND_ONE;
    states[D3DRENDERSTATE_ZENABLE] = D3DZB_TRUE;
    states[D3DRENDERSTATE_ZWRITEENABLE] = 0;
    states[D3DRENDERSTATE_ZFUNC] = D3DCMP_GREATEREQUAL;
    states[D3DRENDERSTATE_ALPHATESTENABLE] = 0;
    states[D3DRENDERSTATE_COLORKEYENABLE] = 0;
    states[D3DRENDERSTATE_SPECULARENABLE] = 0;
    states[D3DRENDERSTATE_FOGENABLE] = 0;
    states[D3DRENDERSTATE_CULLMODE] = D3DCULL_NONE;
    states[D3DRENDERSTATE_SHADEMODE] = D3DSHADE_GOURAUD;
    states[D3DRENDERSTATE_TEXTUREPERSPECTIVE] = 1;
    states[256 + D3DTSS_COLOROP] = D3DTOP_MODULATE;
    states[256 + D3DTSS_COLORARG1] = D3DTA_TEXTURE;
    states[256 + D3DTSS_COLORARG2] = D3DTA_DIFFUSE;
    states[256 + D3DTSS_ALPHAOP] = D3DTOP_MODULATE;
    states[256 + D3DTSS_ALPHAARG1] = D3DTA_TEXTURE;
    states[256 + D3DTSS_ALPHAARG2] = D3DTA_DIFFUSE;
    states[256 + D3DTSS_MAGFILTER] = D3DTFG_LINEAR;
    states[256 + D3DTSS_MINFILTER] = D3DTFN_LINEAR;
    states[256 + D3DTSS_ADDRESSU] = D3DTADDRESS_CLAMP;
    states[256 + D3DTSS_ADDRESSV] = D3DTADDRESS_CLAMP;
    D3DCmd draw{D3DCmd::Draw, D3DPT_TRIANGLELIST, 0, 0.f, {}, {}, 0};
    draw.missile_exhaust = true;
    draw.hud_role = role;
    zoom_capture_command(draw);
    draw.state_snapshot = std::make_shared<const std::vector<unsigned>>(std::move(states));
    const auto *first = reinterpret_cast<const unsigned char *>(vertices.data());
    draw.vertices.assign(first, first + vertices.size() * sizeof(vertices[0]));
    device->commands.push_back(std::move(draw));
    if (effect_enabled()) {
        fixture_frame();
        OverrideMatrix camera;
        if (sun_camera_world(camera)) {
            const auto world = override_product(camera, matrix);
            mw34::missiles::Matrix flame_world{};
            std::copy_n(world.begin(), 12, flame_world.begin());
            const auto nozzle = mw34::missiles::transform(
                flame_world, 0, 0, source.nozzle + source.length * .15, 0, 0);
            const mw34::effects::Emitter emitter{
                7, 8, mw34::missiles::light_intensity, .055f, {1, .36f, .06f}};
            effect_lighting.lights.observe_tracked(
                id, emitter, {{float(nozzle.x), float(nozzle.y), float(nozzle.z)}}, now);
            missile_light_sources[source.binding.descriptor].insert(id);
        }
    }
    if (missile_trace())
        std::fprintf(
            stderr,
            "MISSILE exhaust frame=%u node=%08x descriptor=%08x role=%u vertices=%zu nozzle=%.5f "
            "size_scale=%.1f strength_scale=%.1f light_intensity=%.1f\n",
            host.frames, source.node, source.binding.descriptor, role, vertices.size(),
            source.nozzle, mw34::missiles::exhaust_size_scale,
            mw34::missiles::exhaust_strength_scale, double(mw34::missiles::light_intensity));
}
void missile_texture(mw34::vkscene::Scene &scene, mw34::vkscene::Draw &draw) {
    SunCaptureFp preserve;
    mw34::vkscene::HostFpEnvironment fp;
    constexpr std::uint64_t key = 0x4d5733464c414d45ULL, hash = 0x2026102302ULL;
    auto found = std::find_if(scene.textures.begin(), scene.textures.end(),
                              [](const auto &t) { return t.key == key; });
    if (found == scene.textures.end()) {
        mw34::vkscene::TextureRef texture{};
        texture.key = key;
        texture.hash = hash;
        texture.width = 64;
        texture.height = 128;
        texture.format = mw34::vkscene::TexFormat::rgba8888;
        if (!host.sren || !host.sren->sent_current(key, hash, 64, 128)) {
            static const auto pixels = mw34::missiles::texture();
            texture.pixels32 = pixels;
        }
        scene.textures.push_back(std::move(texture));
        draw.texture = int(scene.textures.size() - 1);
    } else
        draw.texture = int(found - scene.textures.begin());
}
