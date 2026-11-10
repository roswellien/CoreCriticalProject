// Read-only observation of original beam lifetime. No original firing output,
// collision, RNG or animation state is changed by this presentation adapter.
struct WeaponVisualBeam {
    unsigned address{}, definition{}, source{}, mount{}, position{}, direction{}, segment{};
    std::uint64_t generation{};
    bool active{}, arm_retired{};
    unsigned weapon{}, profile{}, owner{}, mount_node{};
    std::string control;
};
std::map<unsigned, WeaponVisualBeam> weapon_visual_beams;
std::uint64_t weapon_visual_generation{};
unsigned weapon_visual_context{};
// 4B3F40 retains its weapon in ESI at the authenticated 4B3FA5 return.
// All fields below are read-only identity checks; no firing outputs are rewritten.
bool weapon_visual_authenticate(WeaponVisualBeam &binding, unsigned caller, unsigned weapon) {
    if (caller != 0x4b3fa5 || !readable(weapon, 0xa4) || binding.position != weapon + 0x40 ||
        binding.direction != weapon + 0x4c || binding.definition != load(weapon + 0x2c))
        return false;
    const unsigned mount = load(weapon + 0x24), profile = load(weapon + 0x80),
                   owner = load(weapon + 0x94);
    if (!mount || !profile || !owner || !readable(mount, 12) || !readable(profile, 32) ||
        !readable(owner, 0x88))
        return false;
    const unsigned node = load(mount + 8), actor = load(owner + 0x84);
    if (!node || !readable(node, 100) || node != load(weapon + 0x20) || !actor ||
        !readable(actor, 8) || load(actor + 4) != binding.source ||
        !additional_chassis.actor_roots.count(binding.source))
        return false;
    // 4B2530 scans the original manager's embedded 16-slot weapon array.
    // Require one owner entry and one definition/control key, even when a
    // second weapon sharing that key is currently idle.
    const unsigned count = load(owner + 0x24);
    if (!count || count > 16 || !readable(owner + 0x40, 4 * count))
        return false;
    unsigned identities = 0, keys = 0;
    std::set<unsigned> weapons;
    for (unsigned i = 0; i < count; ++i) {
        const unsigned item = load(owner + 0x40 + 4 * i);
        if (!item || !weapons.insert(item).second || !readable(item, 0xa4) ||
            load(item + 0x94) != owner)
            return false;
        identities += item == weapon;
        keys += load(item + 0x2c) == binding.definition && load(item + 0x20) == node;
    }
    if (identities != 1 || keys != 1)
        return false;
    const auto control = pose_name(node, 31), firepoint = pose_name(load(profile), 31);
    unsigned ancestor = node;
    std::set<unsigned> visited;
    for (unsigned depth = 0; ancestor && depth < 64; ++depth) {
        if (!visited.insert(ancestor).second || !readable(ancestor, 100))
            return false;
        if (ancestor == binding.source) {
            // A verified non-arm control is ordinary pass-through even if it
            // uses the same laser class as an authored arm attachment.
            binding.control = control;
            if ((control != "lhand" && control != "rhand") || firepoint.size() != 11 ||
                firepoint.compare(0, 9, "firepoint") || firepoint[9] < '0' || firepoint[9] > '9' ||
                firepoint[10] < '0' || firepoint[10] > '9')
                return false;
            binding.weapon = weapon;
            binding.profile = profile;
            binding.owner = owner;
            binding.mount_node = node;
            binding.control = control;
            return true;
        }
        if (load(ancestor + 0x54) != 1)
            return false;
        const unsigned parents = load(ancestor + 0x58);
        if (!parents || !readable(parents, 4))
            return false;
        ancestor = load(parents);
    }
    return false;
}
bool weapon_visual_live(const WeaponVisualBeam &binding) {
    if (!binding.active || !binding.weapon || !readable(binding.address, 0x150) ||
        !readable(binding.weapon, 0xa4) || !readable(binding.definition, 0x80) ||
        load(binding.weapon + 0xa0) != binding.address ||
        load(binding.address + 8) != binding.definition ||
        load(binding.address + 12) != binding.source ||
        load(binding.address + 0x20) != binding.position ||
        load(binding.address + 0x24) != binding.direction ||
        load(binding.address + 0x44) != binding.segment)
        return false;
    auto current = binding;
    if (!weapon_visual_authenticate(current, 0x4b3fa5, binding.weapon) ||
        current.profile != binding.profile || current.owner != binding.owner ||
        current.mount_node != binding.mount_node || current.control != binding.control)
        return false;
    unsigned item = load(binding.definition + 0x7c), previous = 0;
    std::set<unsigned> visited;
    for (unsigned count = 0; item && count < 4096; ++count) {
        if (!visited.insert(item).second || !readable(item, 0x150) ||
            load(item + 8) != binding.definition || load(item + 4) != previous)
            return false;
        if (item == binding.address)
            return true;
        previous = item;
        item = load(item);
    }
    return false;
}
FILE *weapon_visual_trace() {
    static FILE *file = [] {
        const char *path = std::getenv("MW34_WEAPON_VISUAL_TRACE");
        FILE *result = path && *path ? std::fopen(path, "w") : nullptr;
        if (path && *path && !result)
            throw std::runtime_error("Weapon visual trace unavailable");
        return result;
    }();
    return file;
}
bool weapon_visuals_enabled() {
    static const bool enabled = [] {
        for (const auto &record : mw34::chassis::configured_catalog())
            if (!record.weapon_visuals[0].empty())
                return true;
        return false;
    }();
    return enabled;
}
void weapon_visual_log(const char *event, unsigned beam) {
    auto *file = weapon_visual_trace();
    if (!file || !readable(beam, 0x150))
        return;
    const unsigned definition = load(beam + 8), source = load(beam + 12), mount = load(beam + 16);
    std::fprintf(file,
                 "%s frame=%u beam=%08x definition=%08x source=%08x mount=%08x position=%08x "
                 "direction=%08x segments=%u active_segments=%u first=%08x\n",
                 event, host.frames, beam, definition, source, mount, load(beam + 0x20),
                 load(beam + 0x24), load(beam + 0x3c), load(beam + 0x40), load(beam + 0x44));
    if (definition && readable(definition, 4))
        std::fprintf(file, " definition_name=%s\n", pose_name(load(definition), 31).c_str());
    for (unsigned at : {source, mount, load(beam + 0x44)}) {
        if (!at || !readable(at, 100))
            continue;
        std::fprintf(file,
                     " node=%08x name=%s kind=%u data=%08x mesh=%08x flags=%08x parents=%u "
                     "children=%u registered=%u\n",
                     at, pose_name(at, 36).c_str(), load(at + 0x34), load(at + 0x38),
                     load(at + 0x3c), load(at + 0x24), load(at + 0x54), load(at + 0x5c),
                     unsigned(additional_chassis.actor_roots.count(at)));
        const unsigned count = load(at + 0x5c), children = load(at + 0x60);
        if (count <= 16 && readable(children, count * 4))
            for (unsigned i = 0; i < count; ++i) {
                unsigned child = load(children + i * 4);
                if (readable(child, 100))
                    std::fprintf(file, "  child=%08x name=%s kind=%u mesh=%08x data=%08x\n", child,
                                 pose_name(child, 36).c_str(), load(child + 0x34),
                                 load(child + 0x3c), load(child + 0x38));
            }
    }
    std::fflush(file);
}
void *weapon_visual_body(State *s, unsigned target, void *p, Body body) {
    bool observe;
    {
        SunCaptureFp preserve;
        observe = weapon_visuals_enabled() || weapon_visual_trace();
    }
    if (!observe)
        return body(s, target, p);
    const unsigned object = state.gpr.rcx.dword;
    const unsigned caller = readable(state.gpr.rsp.dword, 4) ? load(state.gpr.rsp.dword) : 0;
    const unsigned source_weapon = state.gpr.rsi.dword;

    if (target == 0x581400 || target == 0x584b40) {
        SunCaptureFp preserve;
        weapon_visual_retire_light(object);
        weapon_visual_log(target == 0x581400 ? "stop" : "destroy", object);
        if (target == 0x584b40)
            weapon_visual_beams.erase(object);
        else if (auto found = weapon_visual_beams.find(object); found != weapon_visual_beams.end())
            found->second.active = false;
    }
    void *result = body(s, target, p);
    const State returned = state;
    SunCaptureFp preserve;
    const unsigned context = load(0x5f4c8c);
    if (context != weapon_visual_context) {
        for (const auto &[beam, binding] : weapon_visual_beams)
            weapon_visual_retire_light(beam);
        weapon_visual_beams.clear();
        weapon_visual_context = context;
    }
    if (target == 0x584a70) {
        const unsigned beam = state.gpr.rax.dword;
        if (beam && readable(beam, 0x150)) {
            if (weapon_visual_beams.size() >= 1024)
                throw std::runtime_error("Weapon visual beam capacity exceeded");
            weapon_visual_retire_light(beam);
            weapon_visual_beams[beam] = {beam,
                                         load(beam + 8),
                                         load(beam + 12),
                                         load(beam + 16),
                                         load(beam + 0x20),
                                         load(beam + 0x24),
                                         load(beam + 0x44),
                                         weapon_visual_next_generation(),
                                         false};
            const bool authenticated =
                weapon_visual_authenticate(weapon_visual_beams.at(beam), caller, source_weapon);
            if (auto *file = weapon_visual_trace())
                std::fprintf(file, " authenticated_source=%u control=%s weapon=%08x\n",
                             unsigned(authenticated), weapon_visual_beams.at(beam).control.c_str(),
                             source_weapon);
            weapon_visual_log("create", beam);
            if (auto *file = weapon_visual_trace()) {
                std::fprintf(file, " constructor_caller=%08x esi=%08x origin_minus40=%08x\n",
                             caller, source_weapon, load(beam + 0x20) - 0x40);
                if (readable(source_weapon, 0xa4)) {
                    const unsigned mount = load(source_weapon + 0x24),
                                   profile = load(source_weapon + 0x80),
                                   owner = load(source_weapon + 0x94);
                    std::fprintf(file,
                                 " weapon=%08x node=%08x mount=%08x profile=%08x owner=%08x\n",
                                 source_weapon, load(source_weapon + 0x20), mount, profile, owner);
                    if (mount && readable(mount, 12)) {
                        unsigned node = load(mount + 8);
                        if (node && readable(node, 100))
                            std::fprintf(file, " mount_node=%08x name=%s\n", node,
                                         pose_name(node, 36).c_str());
                    }
                    if (profile && readable(profile, 32))
                        std::fprintf(file, " profile_name=%s\n",
                                     pose_name(load(profile), 36).c_str());
                    if (owner && readable(owner, 0x88))
                        std::fprintf(file, " owner_actor=%08x owner_source=%08x\n",
                                     load(owner + 0x80), load(owner + 0x84));
                }
                std::fflush(file);
            }
        }
    } else if (target == 0x581230) {
        const auto found = weapon_visual_beams.find(object);
        if (found != weapon_visual_beams.end()) {
            found->second.active = true;
            found->second.generation = weapon_visual_next_generation();
            if (auto *file = weapon_visual_trace())
                std::fprintf(file, " authenticated_live=%u generation=%llu\n",
                             unsigned(weapon_visual_live(found->second)),
                             (unsigned long long)found->second.generation);
            if (auto *file = weapon_visual_trace())
                if (found->second.owner && readable(found->second.owner, 0x88))
                    std::fprintf(file, " weapon_owner_count=%u\n",
                                 load(found->second.owner + 0x24));
        }
        weapon_visual_log("start", object);
    } else if (target == 0x5814b0 && weapon_visual_trace()) {
        static unsigned last_frame = ~0U;
        if (last_frame != host.frames) {
            last_frame = host.frames;
            for (const auto &[beam, binding] : weapon_visual_beams)
                if (binding.active)
                    weapon_visual_log("updated", beam);
        }
    }
    state = returned;
    return result;
}

double weapon_visual_opacity(unsigned node) {
    std::set<unsigned> seen;
    for (unsigned i = 0; node && i < 64; ++i) {
        if (!seen.insert(node).second || !readable(node, 100))
            throw std::runtime_error("Weapon visuals: invalid opacity ancestry");
        if (load(node + 0x34) == 5) {
            const unsigned data = load(node + 0x38);
            if (!readable(data, 96))
                throw std::runtime_error("Weapon visuals: missing opacity");
            if (load(data) & 2) {
                const double opacity = chassis_socket_value(data + 4);
                if (!std::isfinite(opacity) || opacity < 0 || opacity > 1)
                    throw std::runtime_error("Weapon visuals: invalid opacity");
                return opacity;
            }
        }
        node = override_parent(node);
    }
    return 1;
}
// Original 555A70 distance/height fog. Preserve the original point's attributes
// when the source geometry is adapted; never infer fog from clipped TL pixels.
double weapon_visual_original_fog(const mw34::donor::Vec &camera, double world_height) {
    if (!load(0x74a22c))
        return 0;
    const float distance2 =
        float(float(camera[0]) * float(camera[0]) + float(camera[2]) * float(camera[2]));
    if (distance2 <= chassis_socket_value(0x74a244) ||
        world_height >= chassis_socket_value(0x74a254))
        return 0;
    double fog;
    if (distance2 < chassis_socket_value(0x74a24c)) {
        unsigned bits;
        std::memcpy(&bits, &distance2, 4);
        bits = (bits >> 1) + 0x1fc00000;
        float approximate_distance;
        std::memcpy(&approximate_distance, &bits, 4);
        fog = float((approximate_distance - float(chassis_socket_value(0x74a240))) *
                    float(chassis_socket_value(0x74a250)));
        if (world_height > chassis_socket_value(0x74a258))
            fog = float(float(chassis_socket_value(0x74a254) - world_height) *
                        float(chassis_socket_value(0x74a25c)) * float(fog));
    } else if (world_height <= chassis_socket_value(0x74a258))
        fog = 1;
    else
        fog = float(float(chassis_socket_value(0x74a254) - world_height) *
                    float(chassis_socket_value(0x74a25c)));
    return std::clamp(fog, 0., 1.);
}
// 53DAA0 admits fog per source-mesh sphere through 555640 before
// 555A70 evaluates individual vertices. A culled source still needs this gate.
bool weapon_visual_fog_candidate(unsigned mesh, const OverrideMatrix &camera,
                                 const OverrideMatrix &world) {
    if (!load(0x74a22c) || !(load(mesh + 8) & 2))
        return false;
    if (!readable(mesh + 0x48, 16))
        throw std::runtime_error("Weapon visuals: missing source sphere");
    mw34::donor::Vec center{};
    for (unsigned i = 0; i < 3; ++i)
        center[i] = chassis_socket_value(mesh + 0x48 + 4 * i);
    const auto point = mw34::donor::point(camera, center);
    const double height = mw34::donor::point(world, center)[1];
    const float radius = float(chassis_socket_value(mesh + 0x54));
    if (radius < 0)
        throw std::runtime_error("Weapon visuals: negative source sphere");
    const float square =
        float(float(point[0]) * float(point[0]) + float(point[2]) * float(point[2]));
    unsigned bits;
    std::memcpy(&bits, &square, 4);
    bits = (bits >> 1) + 0x1fc00000;
    float distance;
    std::memcpy(&distance, &bits, 4);
    const double high_distance = float(distance + radius), low_height = float(height - radius);
    if (high_distance <= chassis_socket_value(0x74a240) ||
        low_height >= chassis_socket_value(0x74a254))
        return false;
    double amount;
    if (float(distance - radius) < chassis_socket_value(0x74a248)) {
        amount = (std::min(high_distance, chassis_socket_value(0x74a248)) -
                  chassis_socket_value(0x74a240)) *
                 chassis_socket_value(0x74a250);
        if (height + radius > chassis_socket_value(0x74a258))
            amount *= (chassis_socket_value(0x74a254) -
                       std::max(low_height, chassis_socket_value(0x74a258))) *
                      chassis_socket_value(0x74a25c);
    } else if (height + radius <= chassis_socket_value(0x74a258))
        amount = 1;
    else
        amount = (chassis_socket_value(0x74a254) -
                  std::max(low_height, chassis_socket_value(0x74a258))) *
                 chassis_socket_value(0x74a25c);
    return std::clamp(amount, 0., 1.) > chassis_socket_value(0x5ce1f8);
}
std::vector<mw34::weapon_visuals::Vertex>
weapon_visual_copy_polygon(unsigned node, unsigned polygon, const OverrideMatrix &camera_world,
                           const OverrideMatrix &world, double opacity,
                           const std::optional<OverrideMatrix> &adaptation = {}) {
    namespace w = mw34::weapon_visuals;
    const unsigned mesh = load(node + 0x3c), count = load(polygon) & 255,
                   indices = load(polygon + 8), uv = load(polygon + 16),
                   colors = load(polygon + 20), material = load(polygon + 28),
                   points = load(mesh + 0x38);
    if (load(mesh) || (load(mesh + 8) & ~2U) || load(mesh + 0x20) || count < 3 || count > 128 ||
        !readable(indices, count * 4) || !readable(uv, count * 8) ||
        !readable(colors, count * 12) || !readable(material, 44) || load(0x74a270))
        throw std::runtime_error("Weapon visuals: unsupported original material path");
    const unsigned vertex_count = load(mesh + 0x14);
    if (!vertex_count || vertex_count > 65535 ||
        std::uint64_t(points) + std::uint64_t(vertex_count) * 12 > 0x100000000ULL ||
        !readable(points, vertex_count * 12))
        throw std::runtime_error("Weapon visuals: invalid original position table");
    const auto to_camera = override_product(mw34::donor::inverse(camera_world), world);
    const bool fog_candidate = weapon_visual_fog_candidate(mesh, to_camera, world);
    std::vector<w::Vertex> vertices;
    for (unsigned i = 0; i < count; ++i) {
        const unsigned at = count - 1 - i, k = load(indices + 4 * at);
        if (k >= load(mesh + 0x14) || !readable(points + 12 * k, 12))
            throw std::runtime_error("Weapon visuals: original vertex out of bounds");
        mw34::donor::Vec local{};
        for (unsigned j = 0; j < 3; ++j)
            local[j] = chassis_socket_value(points + 12 * k + 4 * j);
        for (double value : local)
            if (!std::isfinite(value) || std::abs(value) > 1000000)
                throw std::runtime_error("Weapon visuals: invalid original position");
        const auto camera = mw34::donor::point(to_camera, local),
                   position = mw34::donor::point(world, local);
        const auto adapted = adaptation
                                 ? mw34::donor::point(mw34::donor::inverse(camera_world),
                                                      mw34::donor::point(*adaptation, position))
                                 : camera;
        w::Vertex v{adapted[0], adapted[1], adapted[2], chassis_socket_value(uv + 8 * at),
                    chassis_socket_value(uv + 8 * at + 4)};
        const double fog = fog_candidate ? weapon_visual_original_fog(camera, position[1]) : 0;
        v.color = {chassis_socket_value(colors + 12 * at + 8),
                   chassis_socket_value(colors + 12 * at + 4),
                   chassis_socket_value(colors + 12 * at), double(load(material) & 255) * opacity};
        v.fog = {0, 0, 0, 255 * (1 - fog)};
        vertices.push_back(v);
    }
    return vertices;
}
struct WeaponVisualDescriptor {
    unsigned beam{}, node{}, frame{}, type{}, count{}, material{}, vertices{};
    mw34::weapon_visuals::Identity identity;
    bool required{};
};
std::map<unsigned, WeaponVisualDescriptor> weapon_visual_descriptors;
struct WeaponVisualScope {
    unsigned node{}, frame{}, beam{};
    mw34::weapon_visuals::Identity identity;
    bool required{};
};
WeaponVisualScope weapon_visual_scope;
bool weapon_visual_parent_edge(unsigned parent, unsigned child) {
    if (!readable(parent, 100) || !readable(child, 100))
        return false;
    const unsigned count = load(child + 0x54), parents = load(child + 0x58);
    if (!count || count > 64 || !readable(parents, count * 4))
        return false;
    unsigned matches = 0;
    for (unsigned i = 0; i < count; ++i)
        matches += load(parents + 4 * i) == parent;
    return matches == 1;
}
WeaponVisualScope weapon_visual_begin(unsigned node, unsigned frame) {
    SunCaptureFp preserve;
    const auto previous = weapon_visual_scope;
    weapon_visual_scope = {};
    // Resource nodes are instanced under multiple beam segments. Inherit the
    // authenticated producer path rather than choosing a node's first parent.
    if (previous.beam &&
        (node == previous.node || weapon_visual_parent_edge(previous.node, node))) {
        weapon_visual_scope = previous;
        weapon_visual_scope.node = node;
        weapon_visual_scope.frame = frame;
        return previous;
    }
    for (const auto &[beam, binding] : weapon_visual_beams)
        if (binding.active && binding.segment == node) {
            if (weapon_visual_scope.beam)
                throw std::runtime_error("Weapon visuals: ambiguous segment producer");
            weapon_visual_scope = {node, frame, beam, weapon_visual_identity(binding),
                                   weapon_visual_required(binding)};
        }
    return previous;
}
void *weapon_visual_node_body(State *s, unsigned target, void *p, Body body) {
    bool observe;
    {
        SunCaptureFp preserve;
        observe = weapon_visuals_enabled() || weapon_visual_trace();
    }
    if (!observe)
        return body(s, target, p);
    const auto previous = weapon_visual_begin(state.gpr.rcx.dword, state.gpr.rsp.dword - 4);
    const unsigned queued_before = load(0x803550);
    try {
        void *result = body(s, target, p);
        SunCaptureFp preserve;
        if (weapon_visual_scope.beam && readable(weapon_visual_scope.node, 100) &&
            load(weapon_visual_scope.node + 0x3c)) {
            const unsigned queued_after = load(0x803550);
            if (queued_after < queued_before || queued_after > 6000)
                throw std::runtime_error("Weapon visuals: invalid original deferred queue");
            for (unsigned i = queued_before; i < queued_after; ++i) {
                const unsigned descriptor = 0x80cd9c + i * 16;
                hud_deferred_record(descriptor, WideWorld, false);
                weapon_visual_descriptors[descriptor] = {weapon_visual_scope.beam,
                                                         weapon_visual_scope.node,
                                                         host.frames,
                                                         load(descriptor),
                                                         load(descriptor + 4),
                                                         load(descriptor + 8),
                                                         load(descriptor + 12),
                                                         weapon_visual_scope.identity,
                                                         weapon_visual_scope.required};
            }
        }
        weapon_visual_scope = previous;
        return result;
    } catch (...) {
        weapon_visual_scope = previous;
        throw;
    }
}

// Immutable, host-owned copies cross the deferred queue and render submission.
// The renderer receives only copied geometry, attributes, pose and device state.
std::map<unsigned, std::shared_ptr<const WeaponVisualSnapshot>> weapon_visual_snapshots;
struct WeaponVisualLights {
    std::uint64_t generation{};
    std::set<std::uint64_t> tokens;
};
std::map<unsigned, WeaponVisualLights> weapon_visual_light_tokens;
std::uint64_t weapon_visual_next_generation() {
    if (weapon_visual_generation == 0xffffffffULL)
        throw std::runtime_error("Weapon visuals: binding generation exhausted");
    return ++weapon_visual_generation;
}
void weapon_visual_sync() {
    SunCaptureFp preserve;
    if (!weapon_visuals_enabled() && !weapon_visual_trace())
        return;
    const unsigned context = load(0x5f4c8c);
    if (context == weapon_visual_context && !frontend_on())
        return;
    for (const auto &[address, binding] : weapon_visual_beams)
        weapon_visual_retire_light(address);
    weapon_visual_beams.clear();
    weapon_visual_descriptors.clear();
    weapon_visual_snapshots.clear();
    weapon_visual_context = context;
}
void weapon_visual_retire_root(unsigned root) {
    SunCaptureFp preserve;
    if (!weapon_visuals_enabled() && !weapon_visual_trace())
        return;
    if (additional_chassis.actor_roots.count(root)) {
        auto &visuals = override_state();
        visuals.arm_damage_masks.erase(root);
        visuals.validated_roots.erase(root);
        visuals.source_skins.erase(root);
        // A reused actor address must not inherit another instance's rig pose,
        // part visibility or source-roster result within the same scene.
        std::erase_if(visuals.donor_poses,
                      [&](const auto &item) { return item.first.first == root; });
        std::erase_if(visuals.active_nodes,
                      [&](const auto &item) { return item.first.first == root; });
        std::erase_if(visuals.attached_cockpit_nodes,
                      [&](const auto &item) { return item.first == root; });
        std::erase_if(visuals.emitted, [&](const auto &item) { return item.first == root; });
    }
    for (auto item = weapon_visual_beams.begin(); item != weapon_visual_beams.end();) {
        if (item->second.source != root) {
            ++item;
            continue;
        }
        weapon_visual_retire_light(item->first);
        weapon_visual_snapshots.erase(item->first);
        item = weapon_visual_beams.erase(item);
    }
}
bool weapon_visual_required(const WeaponVisualBeam &binding) {
    const auto *record = weapon_visual_registration(binding.source);
    if (!record || record->weapon_visuals[0].empty())
        return false;
    if (!readable(binding.definition, 0x80))
        return true;
    const auto name = pose_name(load(binding.definition), 31);
    return std::any_of(
        record->weapon_visuals[0].begin(), record->weapon_visuals[0].end(), [&](const auto &entry) {
            return entry.weapon == name &&
                   (binding.control.empty() || entry.source_control == binding.control);
        });
}

mw34::weapon_visuals::Identity weapon_visual_identity(const WeaponVisualBeam &beam) {
    return {beam.address,  beam.source,    beam.weapon,    beam.definition,
            beam.position, beam.direction, beam.generation};
}
void weapon_visual_retire_light(unsigned beam, std::uint64_t generation = 0) {
    const auto light = weapon_visual_light_tokens.find(beam);
    if (light != weapon_visual_light_tokens.end() &&
        (!generation || light->second.generation == generation)) {
        for (auto token : light->second.tokens)
            effect_lighting.lights.erase_tracked(token);
        weapon_visual_light_tokens.erase(light);
    }
}
bool weapon_visual_adapt() {
    static const bool enabled = [] {
        const char *value = std::getenv("MW34_WEAPON_VISUAL_ADAPTER");
        if (!value || !*value || !std::strcmp(value, "1"))
            return true;
        if (!std::strcmp(value, "0"))
            return false;
        throw std::runtime_error("MW34_WEAPON_VISUAL_ADAPTER must be 0 or 1");
    }();
    return enabled;
}
const mw34::chassis::Registration *weapon_visual_registration(unsigned root) {
    const auto found = additional_chassis.actor_roots.find(root);
    if (found == additional_chassis.actor_roots.end())
        return nullptr;
    const auto &catalog = mw34::chassis::configured_catalog();
    if (found->second < mw34::chassis::first_runtime_id ||
        found->second - mw34::chassis::first_runtime_id >= catalog.size())
        throw std::runtime_error("Weapon visuals: actor registration out of bounds");
    return &catalog[found->second - mw34::chassis::first_runtime_id];
}
bool weapon_visual_arm_gone(const WeaponVisualBeam &binding) {
    if (!weapon_visual_registration(binding.source) || !readable(binding.source, 100))
        return true;
    (void)override_validate_root(binding.source);
    const auto &original = override_state();
    const auto mask = original.arm_damage_masks.find(binding.source);
    const auto part = original.active_nodes.find({binding.source, binding.control});
    std::optional<bool> mesh_visible, control_visible;
    if (part != original.active_nodes.end())
        mesh_visible = part->second;
    if (binding.mount_node && readable(binding.mount_node, 100))
        control_visible = bool(load(binding.mount_node + 0x24) & 4);
    return mw34::weapon_visuals::arm_retired(
        binding.control, mask == original.arm_damage_masks.end() ? 0 : mask->second,
        !(load(binding.source + 0x24) & 4), mesh_visible, control_visible);
}
void weapon_visual_add_light(std::vector<WeaponVisualLight> &lights, unsigned texture,
                             const std::vector<mw34::effects::Point> &points) {
    if (!effect_enabled() || points.empty())
        return;
    effect_load();
    auto *surface = vsurface(texture);
    const auto *emitter = surface ? effect_material(*surface) : nullptr;
    if (!emitter)
        return;
    auto found = std::find_if(lights.begin(), lights.end(),
                              [&](const auto &light) { return light.texture == texture; });
    if (found == lights.end()) {
        if (lights.size() == 128)
            throw std::runtime_error("Weapon visuals: source light group bound exceeded");
        lights.push_back({texture, *emitter, points});
    } else
        found->points.insert(found->points.end(), points.begin(), points.end());
}
std::optional<mw34::donor::Vec> weapon_visual_muzzle(const WeaponVisualBeam &binding) {
    const auto *record = weapon_visual_registration(binding.source);
    if (!record || record->weapon_visuals[0].empty())
        return {};
    const int model = override_validate_root(binding.source);
    if (model < 0)
        return {}; // Original or an unavailable optional appearance.
    const auto &definition = override_models().at(unsigned(model));
    if (!definition.resource || record->resource != definition.resource ||
        record->id != definition.id)
        throw std::runtime_error("Weapon visuals: selected model identity disagrees");
    override_load_model(unsigned(model));
    const auto weapon = pose_name(load(binding.definition), 31);
    const auto &entries = record->weapon_visuals[definition.lod];
    const auto entry = std::find_if(entries.begin(), entries.end(), [&](const auto &value) {
        return value.source_control == binding.control && value.weapon == weapon;
    });
    if (entry == entries.end())
        return {};
    const auto pose = chassis_socket_pose(binding.source, unsigned(model));
    const auto &rig = override_state().donor_rigs.at(unsigned(model));
    const auto bone = std::find_if(rig.bones.begin(), rig.bones.end(),
                                   [&](const auto &value) { return value.name == entry->bone; });
    if (bone == rig.bones.end())
        throw std::runtime_error("Weapon visuals: required donor bone missing");
    const auto world = override_product(override_product(chassis_socket_world(binding.source),
                                                         mw34::donor::inverse(mw34::donor::axis())),
                                        pose.pose.world.at(size_t(bone - rig.bones.begin())));
    return mw34::donor::point(world, entry->position);
}
struct WeaponVisualMesh {
    unsigned node{};
    OverrideMatrix world;
    double opacity{};
};
WeaponVisualMesh weapon_visual_mesh(unsigned segment) {
    std::vector<WeaponVisualMesh> pending{
        {segment, chassis_socket_world(segment), weapon_visual_opacity(segment)}};
    std::set<unsigned> visited;
    WeaponVisualMesh result{};
    while (!pending.empty()) {
        auto entry = pending.back();
        pending.pop_back();
        const unsigned node = entry.node;
        if (!node || !visited.insert(node).second || visited.size() > 64 || !readable(node, 100))
            throw std::runtime_error("Weapon visuals: malformed first-segment hierarchy");
        if (load(node + 0x3c)) {
            if (result.node)
                throw std::runtime_error("Weapon visuals: ambiguous segment mesh");
            result = entry;
        }
        const unsigned count = load(node + 0x5c), children = load(node + 0x60);
        if (count > 16 || (count && !readable(children, count * 4)))
            throw std::runtime_error("Weapon visuals: invalid segment children");
        for (unsigned i = 0; i < count; ++i) {
            const unsigned child = load(children + i * 4);
            if (!weapon_visual_parent_edge(node, child))
                throw std::runtime_error("Weapon visuals: nonreciprocal segment edge");
            auto next = entry;
            next.node = child;
            const unsigned type = load(child + 0x34);
            if (type == 5) {
                const unsigned data = load(child + 0x38);
                if (!readable(data, 96))
                    throw std::runtime_error("Weapon visuals: missing instance transform");
                if (!(load(data) & 8))
                    next.world = override_product(entry.world, override_matrix(data + 0x30));
                if (load(data) & 2) {
                    next.opacity = chassis_socket_value(data + 4);
                    if (!std::isfinite(next.opacity) || next.opacity < 0 || next.opacity > 1)
                        throw std::runtime_error("Weapon visuals: invalid instance opacity");
                }
            } else if (type != 2 && type != 6)
                throw std::runtime_error("Weapon visuals: unsupported instance transform");
            pending.push_back(std::move(next));
        }
    }
    if (!result.node)
        throw std::runtime_error("Weapon visuals: required first-segment mesh missing");
    return result;
}
std::set<mw34::weapon_visuals::View> weapon_visual_views;
std::optional<mw34::weapon_visuals::View> weapon_visual_current_view(const D3DDev &device) {
    if (frontend_on() || !device.in_scene ||
        (wide_hud_role() != WideWorld && wide_hud_role() != WideZoom))
        return {};
    const unsigned data = load(0x7402f4);
    if (!data || !readable(data, 0x100))
        return {};
    OverrideMatrix camera;
    if (!sun_camera_world(camera))
        return {};
    unsigned policy = 2;
    if (!photo_replay_detached_cam()) {
        const unsigned context = camera_context(), controller = context ? load(context + 0x58) : 0;
        if (!camera_controller(context, controller))
            return {};
        policy = load(controller + 4) == 0 ? 1 : 0;
    }
    const std::array<float, 6> projection{wide_float(0x73fb80), wide_float(0x73fc30),
                                          wide_float(0x73fb98), wide_float(0x73fb88),
                                          wide_float(0x73fb8c), wide_float(0x740304)};
    for (float value : projection)
        if (!std::isfinite(value))
            return {};
    if (projection[0] <= 0 || !projection[1] || !projection[2] || projection[5] <= 0)
        return {};
    return mw34::weapon_visuals::View{
        device.target, device.weapon_scene,    wide_hud_role(), camera, projection,
        policy,        sun_view_binding.source};
}
void weapon_visual_scene_start() {
    weapon_visual_sync();
    weapon_visual_views.clear();
}
void weapon_visual_activate_view() {
    SunCaptureFp preserve;
    if (!weapon_visuals_enabled())
        return;
    for (const auto &device : host.devices)
        if (const auto view = weapon_visual_current_view(device))
            weapon_visual_views.insert(*view);
}
void weapon_visual_world_view(const D3DDev &device) {
    SunCaptureFp preserve;
    if (!weapon_visuals_enabled())
        return;
    const auto &scope = override_state().scope;
    if (!world_scope && !world_cell_depth &&
        !(scope.node && scope.root && !scope.preview && !scope.attached_cockpit &&
          additional_chassis.actor_roots.count(scope.root)))
        return;
    if (const auto view = weapon_visual_current_view(device))
        weapon_visual_views.insert(*view);
}
bool weapon_visual_gpu() {
    static const bool enabled = [] {
        const char *value = std::getenv("MW34_WEAPON_VISUAL_GPU");
        if (!value || !*value || !std::strcmp(value, "1"))
            return true;
        if (!std::strcmp(value, "0"))
            return false;
        throw std::runtime_error("MW34_WEAPON_VISUAL_GPU must be 0 or 1");
    }();
    return enabled && mw34::vkscene::Renderer::gpu_models();
}
void weapon_visual_gpu_command(D3DCmd &command, unsigned node, unsigned polygon,
                               const OverrideMatrix &camera, const OverrideMatrix &adaptation,
                               const OverrideMatrix &world,
                               const std::vector<mw34::weapon_visuals::Vertex> &vertices,
                               const std::array<float, 6> &projection) {
    if (!weapon_visual_gpu())
        return;
    const auto colour =
        mw34::weapon_visuals::gpu_colour(vertices, projection[5], bool(command.sky_view));
    if (!colour || !command.state_snapshot)
        return;
    auto states = *command.state_snapshot;
    if (states[256 + D3DTSS_COLOROP] != D3DTOP_MODULATE ||
        states[256 + D3DTSS_COLORARG1] != D3DTA_TEXTURE ||
        states[256 + D3DTSS_COLORARG2] != D3DTA_DIFFUSE ||
        states[256 + D3DTSS_ALPHAOP] != D3DTOP_MODULATE ||
        states[256 + D3DTSS_ALPHAARG1] != D3DTA_TEXTURE ||
        states[256 + D3DTSS_ALPHAARG2] != D3DTA_DIFFUSE || states[D3DRENDERSTATE_SPECULARENABLE])
        return;
    const auto transform =
        override_product(mw34::donor::inverse(camera), override_product(adaptation, world));
    unsigned normal_axis = 0;
    double normal_length = 0;
    for (unsigned column = 0; column < 3; ++column) {
        double length = 0;
        for (unsigned row = 0; row < 3; ++row)
            length += transform[row * 4 + column] * transform[row * 4 + column];
        if (length > normal_length) {
            normal_length = length;
            normal_axis = column;
        }
    }
    if (normal_length < 1e-12)
        return;
    auto geometry = std::make_shared<mw34::vkscene::ModelGeometry>();
    geometry->key = 0x5756504f00000000ULL | polygon;
    const unsigned mesh = load(node + 0x3c), indices = load(polygon + 8),
                   positions = load(mesh + 0x38), count = load(polygon) & 255;
    std::vector<mw34::vkscene::ModelVertex> corners;
    for (unsigned i = 0; i < count; ++i) {
        const unsigned index = load(indices + (count - 1 - i) * 4);
        mw34::vkscene::ModelVertex vertex{};
        vertex.x = float(chassis_socket_value(positions + 12 * index));
        vertex.y = float(chassis_socket_value(positions + 12 * index + 4));
        vertex.z = float(chassis_socket_value(positions + 12 * index + 8));
        if (normal_axis == 0)
            vertex.nx = 1;
        else if (normal_axis == 1)
            vertex.ny = 1;
        else
            vertex.nz = 1;
        vertex.u = float(vertices[i].u);
        vertex.v = float(vertices[i].v);
        corners.push_back(vertex);
    }
    for (unsigned i = 1; i + 1 < count; ++i)
        geometry->vertices.insert(geometry->vertices.end(),
                                  {corners[0], corners[i], corners[i + 1]});
    geometry->hash = 0xcbf29ce484222325ULL;
    const auto *bytes = reinterpret_cast<const unsigned char *>(geometry->vertices.data());
    for (size_t i = 0; i < geometry->vertices.size() * sizeof(geometry->vertices[0]); ++i) {
        geometry->hash ^= bytes[i];
        geometry->hash *= 0x100000001b3ULL;
    }
    auto model = std::make_shared<mw34::vkscene::ModelInstance>();
    model->geometry = std::move(geometry);
    for (unsigned i = 0; i < 12; ++i)
        model->camera[i] = float(transform[i]);
    model->projection = projection;
    model->color = *colour;
    // The existing unlit model shader's factor-alpha lane is also its fog
    // factor. Reuse it for opacity only when source fog is identically absent,
    // and select constant TFACTOR to bypass that shader's diagnostic shading.
    model->diagnostic_fog_factor = float(*colour >> 24) / 255.f;
    states[D3DRENDERSTATE_FOGENABLE] = 0;
    states[D3DRENDERSTATE_TEXTUREFACTOR] = *colour;
    states[256 + D3DTSS_COLORARG2] = D3DTA_TFACTOR;
    states[256 + D3DTSS_ALPHAARG2] = D3DTA_TFACTOR;
    command.state_snapshot = std::make_shared<const std::vector<unsigned>>(std::move(states));
    command.model = std::move(model);
}
void weapon_visual_seed_view() {
    if (!weapon_visuals_enabled() || frontend_on())
        return;
    SunCaptureFp preserve;
    mw34::vkscene::HostFpEnvironment fp;
    bool active = false;
    for (const auto &[address, binding] : weapon_visual_beams) {
        const auto *registration = weapon_visual_registration(binding.source);
        if (binding.active && registration && weapon_visual_required(binding))
            active = true;
    }
    if (!active || (wide_hud_role() != WideWorld && wide_hud_role() != WideZoom))
        return;
    D3DDev *device = nullptr;
    for (auto &candidate : host.devices)
        if (candidate.in_scene) {
            if (device)
                throw std::runtime_error("Weapon visuals: ambiguous scene");
            device = &candidate;
        }
    if (!device)
        return;
    const auto view = weapon_visual_current_view(*device);
    if (!view)
        throw std::runtime_error("Weapon visuals: required original world camera unavailable");
    if (!weapon_visual_views.count(*view))
        return;
    const auto &camera = std::get<3>(*view);
    const auto &projection = std::get<4>(*view);
    const bool external = std::get<5>(*view) != 0;
    for (auto &[address, binding] : weapon_visual_beams) {
        const auto *record = weapon_visual_registration(binding.source);
        if (!binding.active || !record || !weapon_visual_required(binding))
            continue;
        binding.arm_retired = weapon_visual_arm_gone(binding);
        if (binding.arm_retired) {
            weapon_visual_retire_light(address);
            continue;
        }
        if (!weapon_visual_live(binding)) {
            weapon_visual_retire_light(address);
            throw std::runtime_error(
                "Weapon visuals: active source authentication failed for actor " +
                std::to_string(binding.source) + " attachment " + binding.control);
        }
        const auto muzzle =
            external ? weapon_visual_muzzle(binding) : std::optional<mw34::donor::Vec>{};
        if (!load(binding.address + 0x40))
            continue; // Original update has not activated a segment.
        auto snapshot = std::make_shared<WeaponVisualSnapshot>();
        snapshot->identity = weapon_visual_identity(binding);
        snapshot->view = *view;
        snapshot->external = external && muzzle.has_value() && weapon_visual_adapt();
        if (snapshot->external) {
            const auto instance = weapon_visual_mesh(binding.segment);
            const unsigned node = instance.node, mesh = load(node + 0x3c);
            if (!readable(mesh, 0x58) || load(mesh + 0x10) > 128 || !load(mesh + 0x10) ||
                !readable(load(mesh + 0x34), load(mesh + 0x10) * 36))
                throw std::runtime_error("Weapon visuals: invalid original polygon table");
            const auto segment = chassis_socket_world(binding.segment);
            const auto source = mw34::donor::point(segment, {0, 0, 0}),
                       end = mw34::donor::point(segment, {0, 0, -1});
            const auto adaptation =
                mw34::weapon_visuals::attachment_transform(source, end, *muzzle);
            if (auto *file = weapon_visual_trace()) {
                const auto a = mw34::donor::point(adaptation, source),
                           b = mw34::donor::point(adaptation, end);
                std::fprintf(file,
                             " adapter frame=%u beam=%08x actor=%08x control=%s generation=%llu "
                             "policy=%u S=%.9g,%.9g,%.9g D=%.9g,%.9g,%.9g E=%.9g,%.9g,%.9g "
                             "source_error=%.9g end_error=%.9g\n",
                             host.frames, address, binding.source, binding.control.c_str(),
                             (unsigned long long)binding.generation, std::get<5>(*view), source[0],
                             source[1], source[2], (*muzzle)[0], (*muzzle)[1], (*muzzle)[2], end[0],
                             end[1], end[2],
                             std::sqrt(mw34::donor::dot(mw34::donor::sub(a, *muzzle),
                                                        mw34::donor::sub(a, *muzzle))),
                             std::sqrt(mw34::donor::dot(mw34::donor::sub(b, end),
                                                        mw34::donor::sub(b, end))));
            }
            for (unsigned i = 0; i < load(mesh + 0x10); ++i) {
                const unsigned polygon = load(mesh + 0x34) + 36 * i, material = load(polygon + 28);
                if (!readable(material, 44) || !(load(material) & 0x100))
                    throw std::runtime_error(
                        "Weapon visuals: unsupported required untextured material");
                const unsigned reference = load(material + 16);
                if (!readable(reference, 40) || !readable(load(reference + 4), 24))
                    throw std::runtime_error("Weapon visuals: original texture state unavailable");
                const unsigned texture_state = load(reference + 4),
                               texture = vsurf_root(load(texture_state + 8));
                if (!texture || !vsurface(texture))
                    throw std::runtime_error("Weapon visuals: live original texture unavailable");
                const auto corrected = weapon_visual_copy_polygon(
                    node, polygon, camera, instance.world, instance.opacity, adaptation);
                std::vector<mw34::effects::Point> points;
                for (const auto &vertex : corrected) {
                    const auto point = mw34::donor::point(camera, {vertex.x, vertex.y, vertex.z});
                    points.push_back({float(point[0]), float(point[1]), float(point[2])});
                }
                weapon_visual_add_light(snapshot->lights, texture, points);
                auto states = this->snapshot(*device);
                states[D3DRENDERSTATE_SHADEMODE] = D3DSHADE_GOURAUD;
                states[D3DRENDERSTATE_ALPHABLENDENABLE] = 1;
                states[D3DRENDERSTATE_ZWRITEENABLE] = 0;
                states[256 + D3DTSS_ALPHAOP] =
                    mw34::weapon_visuals::packed(corrected.front().color) > 0xff000000U
                        ? D3DTOP_MODULATE
                        : load(texture_state + 12);
                states[256 + D3DTSS_MAGFILTER] = load(texture_state + 16);
                states[256 + D3DTSS_MINFILTER] = load(texture_state + 20);
                D3DCmd command{D3DCmd::Draw, D3DPT_TRIANGLELIST, 0, 0.f, {}, {}, 0};
                command.state_snapshot =
                    std::make_shared<const std::vector<unsigned>>(std::move(states));
                command.texture = texture;
                command.hud_role = wide_hud_role();
                zoom_capture_command(command);
                // Original one-sided polygons retain their source winding decision.
                const auto &vertices = corrected;
                const auto a = mw34::donor::Vec{vertices[0].x, vertices[0].y, vertices[0].z},
                           b = mw34::donor::Vec{vertices[1].x, vertices[1].y, vertices[1].z},
                           c = mw34::donor::Vec{vertices[2].x, vertices[2].y, vertices[2].z};
                const auto facing = mw34::donor::dot(
                    mw34::donor::cross(mw34::donor::sub(a, b), mw34::donor::sub(c, b)), a);
                if ((load(polygon) & 0x500) || facing < 0) {
                    const auto tl = mw34::weapon_visuals::project(vertices, projection);
                    const auto *data = reinterpret_cast<const unsigned char *>(tl.data());
                    if (!tl.empty())
                        command.vertices.assign(data, data + tl.size() * sizeof(tl[0]));
                    if (!command.vertices.empty()) {
                        camera_capture(command, device->target);
                        sun_capture_sky(command);
                        weapon_visual_gpu_command(command, node, polygon, camera, adaptation,
                                                  instance.world, vertices, projection);
                        snapshot->replacement.push_back(std::move(command));
                    }
                }
            }
        }
        weapon_visual_snapshots[address] = snapshot;
        D3DCmd seed{D3DCmd::Draw, D3DPT_TRIANGLELIST, 0, 0.f, {}, {}, 0};
        seed.weapon_visual = std::move(snapshot);
        seed.weapon_visual_seed = true;
        seed.hud_role = wide_hud_role();
        device->commands.push_back(std::move(seed));
    }
}
void weapon_visual_capture(D3DCmd &draw, unsigned type, unsigned vertices, unsigned count) {
    if (!weapon_visuals_enabled())
        return;
    SunCaptureFp preserve;
    const auto descriptor = weapon_visual_descriptors.find(state.gpr.rsi.dword);
    if (descriptor == weapon_visual_descriptors.end() || !descriptor->second.required)
        return;
    if (!hud_deferred_panel(type, vertices, count))
        throw std::runtime_error("Weapon visuals: deferred source identity unavailable");
    const auto &source = descriptor->second;
    const auto snapshot = weapon_visual_snapshots.find(source.beam);
    if (source.frame != host.frames)
        throw std::runtime_error("Weapon visuals: deferred source snapshot expired");
    if (snapshot == weapon_visual_snapshots.end() ||
        !mw34::weapon_visuals::current(source.identity, snapshot->second->identity)) {
        const auto binding = weapon_visual_beams.find(source.beam);
        if (binding == weapon_visual_beams.end() || !binding->second.active ||
            binding->second.arm_retired ||
            binding->second.generation != source.identity.generation) {
            auto retired = std::make_shared<WeaponVisualSnapshot>();
            retired->identity = source.identity;
            retired->external = true;
            draw.weapon_visual = std::move(retired);
            return;
        }
        throw std::runtime_error(
            "Weapon visuals: required deferred world-view snapshot unavailable");
    }
    draw.weapon_visual = snapshot->second;
}
void weapon_visual_finish_view() {
    if (weapon_visual_snapshots.empty())
        return;
    SunCaptureFp preserve;
    const auto source = weapon_visual_snapshots.begin()->second;
    for (auto &device : host.devices)
        if (device.in_scene && device.target == std::get<0>(source->view) &&
            device.weapon_scene == std::get<1>(source->view)) {
            D3DCmd end{D3DCmd::Draw, D3DPT_TRIANGLELIST, 0, 0.f, {}, {}, 0};
            end.weapon_visual = source;
            end.weapon_visual_seed = true;
            end.weapon_visual_end = true;
            device.commands.push_back(std::move(end));
            return;
        }
    throw std::runtime_error("Weapon visuals: deferred view ended on a different target");
}
void weapon_visual_prepare(D3DDev &device) {
    if (!weapon_visuals_enabled() ||
        std::none_of(device.commands.begin(), device.commands.end(),
                     [](const auto &command) { return bool(command.weapon_visual); }))
        return;
    SunCaptureFp preserve;
    mw34::vkscene::HostFpEnvironment fp;
    auto composed =
        mw34::weapon_visuals::compose_deferred(device.commands, [&](const auto &identity) {
            using mw34::weapon_visuals::Status;
            const auto binding = weapon_visual_beams.find(identity.beam);
            if (binding == weapon_visual_beams.end() || !binding->second.active ||
                binding->second.arm_retired || binding->second.generation != identity.generation)
                return Status::retired;
            if (!weapon_visual_live(binding->second) ||
                !mw34::weapon_visuals::current(identity, weapon_visual_identity(binding->second)))
                return Status::invalid;
            return Status::current;
        });
    for (const auto &identity : composed.retired)
        weapon_visual_retire_light(identity.beam, identity.generation);
    for (const auto &source : composed.observations) {
        weapon_visual_retire_light(source->identity.beam);
        if (!effect_enabled())
            continue;
        auto lights = source->lights;
        if (!source->external) {
            const auto camera = mw34::sun::world_matrix(std::get<3>(source->view));
            const auto &projection = std::get<4>(source->view);
            for (const auto &command : device.commands)
                if (command.weapon_visual == source && !command.weapon_visual_seed) {
                    std::vector<mw34::effects::Point> points;
                    for (size_t at = 0; at < command.vertices.size(); at += 32) {
                        mw34::weapon_visuals::TlVertex vertex;
                        std::memcpy(&vertex, command.vertices.data() + at, 32);
                        points.push_back(mw34::effects::reconstruct(vertex.x, vertex.y, vertex.z,
                                                                    projection, camera));
                    }
                    weapon_visual_add_light(lights, command.texture, points);
                }
        }
        for (unsigned i = 0; i < lights.size(); ++i) {
            // Source tokens occupy distinct byte offsets inside this live
            // original0x150-byte beam allocation, never another actor's node.
            const auto token = (source->identity.generation << 32) | (source->identity.beam + i);
            effect_lighting.lights.observe_tracked(token, lights[i].emitter, lights[i].points,
                                                   effect_time());
            auto &owner = weapon_visual_light_tokens[source->identity.beam];
            owner.generation = source->identity.generation;
            owner.tokens.insert(token);
        }
    }
    device.commands = std::move(composed.commands);
}
