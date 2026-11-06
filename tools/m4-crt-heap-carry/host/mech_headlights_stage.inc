// Included in Stage. All guest accesses are read-only; the original bodies run.
mw34::headlights::Owners headlight_owners;
mw34::headlights::Edge headlight_edge;
std::uint64_t headlight_generation{}, headlight_tick{};
unsigned headlight_world_depth{}, headlight_world_frame{~0U};
double headlight_seconds{};
std::array<unsigned char, 256> headlight_keys{};
bool headlight_keyboard_valid{};
unsigned headlight_key{};
int headlight_button{-1};
bool headlight_bindings_read{}, headlight_controller_connected{};

bool headlight_enabled() const {
    static const bool enabled = mw34::sun::flag("MW34_MECH_HEADLIGHTS");
    return enabled && mw34::effects::settings().enabled;
}
void headlight_clear() {
    headlight_owners.clear();
    headlight_edge = {};
    headlight_keyboard_valid = false;
    headlight_world_frame = ~0U;
}
void headlight_read_bindings() {
    if (headlight_bindings_read)
        return;
    headlight_bindings_read = true;
    const wchar_t *path = ::_wgetenv(L"MW34_HEADLIGHT_BINDINGS");
    if (!path || !*path)
        return;
    std::ifstream file{std::filesystem::path(path)};
    std::string magic, extra;
    if (!(file >> magic >> headlight_key >> headlight_button) || magic != "CC_MW3_HEADLIGHTS_V1" ||
        headlight_key > 0x7ff || (headlight_key && !(headlight_key & 255)) ||
        headlight_button < -1 || headlight_button > 25 || (file >> extra))
        throw std::runtime_error("Headlights: invalid input binding");
    const unsigned scan = headlight_key & 255;
    if (scan == 0x43 || scan == 0x44 || scan == 0x57)
        throw std::runtime_error("Headlights: key reserved for capture/replay");
}
void headlight_keyboard(unsigned size, const unsigned char *keys, bool success = true) {
    if (!headlight_enabled() || size != 256)
        return;
    headlight_keyboard_valid = success;
    if (success)
        std::copy_n(keys, 256, headlight_keys.begin());
    else
        headlight_edge = {};
}
unsigned headlight_player() {
    const unsigned context = load(0x60861c);
    return context && readable(context, 0x18) ? load(context + 0x14) : 0;
}
bool headlight_shutdown(unsigned actor) {
    if (!readable(actor, 0x579))

        return true;

    return runtime.memory().load<unsigned char>({actor + 0xde}) != 0 || load(actor + 0x578) == 10;
}
bool headlight_actor_root_matches(unsigned actor, unsigned root) {
    return readable(actor, 8) && load(actor + 4) == root;
}
bool headlight_node_in_root(unsigned node, unsigned root) {
    std::set<unsigned> seen;
    for (unsigned depth = 0; depth < 64; ++depth) {
        if (node == root)
            return true;
        if (!node || !seen.insert(node).second || !readable(node, 100))
            return false;
        const unsigned parent_link = load(node + 0x58);
        if (load(node + 0x54) != 1 || !readable(parent_link, 4))
            return false;
        node = load(parent_link);
    }
    return false;
}
struct HeadlightOwnerSnapshot {
    unsigned actor{}, root{};
    std::uint64_t generation{};
};
void headlight_input(bool gameplay) {
    if (!headlight_enabled())
        return;
    headlight_read_bindings();
    const bool focus = host.scripted || controller_focus();
    const bool connected = controller && controller->sample.connected;
    if (headlight_button >= 0 && connected != headlight_controller_connected)
        headlight_edge = {};
    headlight_controller_connected = connected;
    const bool allowed = gameplay && focus && !frontend_on() && !photo_replay_consume_input();
    auto down = [&](unsigned scan) { return (headlight_keys[scan] & 0x80) != 0; };
    const unsigned modifiers = ((down(0x38) || down(0xb8)) ? 0x100 : 0) |
                               ((down(0x1d) || down(0x9d)) ? 0x200 : 0) |
                               ((down(0x2a) || down(0x36)) ? 0x400 : 0);
    const bool key = headlight_keyboard_valid && headlight_key && down(headlight_key & 255) &&
                     modifiers == (headlight_key & 0x700);
    const bool button = headlight_button >= 0 && controller && controller->sample.connected &&
                        controller->sample.buttons[headlight_button];
    if (!headlight_edge.sample(key || button, allowed))
        return;
    auto owner = headlight_owners.find(headlight_player());
    if (owner != headlight_owners.end() && owner->second.ready &&
        !headlight_shutdown(owner->first)) {
        owner->second.envelope.desired = !owner->second.envelope.desired;
        if (effect_trace())
            std::fprintf(stderr, "Headlights toggle frame=%u actor=%08x desired=%u\n", host.frames,
                         owner->first, unsigned(owner->second.envelope.desired));
    }
}
const mw34::chassis::Registration *headlight_registration(unsigned actor) {
    if (!readable(actor, 0x688))
        return nullptr;
    const unsigned data = load(actor + 0x684);
    if (!data || !readable(data, 16))
        return nullptr;
    const unsigned id = load(data + 12);
    const auto &records = mw34::chassis::configured_catalog();
    if (id < mw34::chassis::first_runtime_id ||
        id - mw34::chassis::first_runtime_id >= records.size())
        return nullptr;
    return &records[id - mw34::chassis::first_runtime_id];
}
unsigned headlight_node(unsigned root, const std::string &name) {
    unsigned found = 0;
    std::vector<unsigned> queue{root};
    std::set<unsigned> seen;
    for (size_t at = 0; at < queue.size(); ++at) {
        const unsigned node = queue[at];
        if (at >= 512 || !seen.insert(node).second || !readable(node, 100))
            throw std::runtime_error("Headlights: malformed actor hierarchy");
        if (pose_name(node, 36) == name) {
            if (found)
                throw std::runtime_error("Headlights: ambiguous attachment " + name);
            found = node;
        }
        const unsigned count = load(node + 0x5c), children = load(node + 0x60);
        if (count > 64 || (count && !readable(children, count * 4)))
            throw std::runtime_error("Headlights: unreadable actor children");
        for (unsigned i = 0; i < count; ++i) {
            const unsigned child = load(children + i * 4);
            if (!readable(child, 100) || load(child + 0x54) != 1 ||
                !readable(load(child + 0x58), 4) || load(load(child + 0x58)) != node)
                throw std::runtime_error("Headlights: attachment has foreign parent");
            queue.push_back(child);
        }
    }
    return found;
}
std::vector<unsigned> headlight_ancestry(unsigned node, unsigned root) {
    std::vector<unsigned> result;
    std::set<unsigned> seen;
    for (;;) {
        if (result.size() >= 64 || !seen.insert(node).second || !readable(node, 100))
            throw std::runtime_error("Headlights: malformed mount ancestry");
        result.push_back(node);
        if (node == root)
            return result;
        if (load(node + 0x54) != 1 || !readable(load(node + 0x58), 4))
            throw std::runtime_error("Headlights: mount left its actor root");
        node = load(load(node + 0x58));
    }
}
void headlight_refresh(unsigned actor, mw34::headlights::Owner &owner) {
    const auto *record = headlight_registration(actor);
    if (!record || !owner.ready) {
        owner.emitters.clear();
        return;
    }
    const unsigned root = load(actor + 4);
    owner.bind_root(root);
    if (!root)
        return;
    owner.chassis = unsigned(record - mw34::chassis::configured_catalog().data());
    for (const auto &lamp : record->headlights) {
        if (owner.retired_emitters.count(lamp.id)) {
            owner.emitters[lamp.id].valid = false;
            continue;
        }
        OverrideMatrix world{};
        std::string control = lamp.attachment;
        std::optional<OverrideDonorInstance> pose;
        unsigned model = ~0U;
        size_t bone_index = 0;
        if (lamp.space == "donor_bone") {
            for (unsigned i = 0; i < override_models().size(); ++i)
                if (override_models()[i].lod == 0 && record->id == override_models()[i].id) {
                    if (model != ~0U)
                        throw std::runtime_error("Headlights: ambiguous donor model");
                    model = i;
                }
            if (model == ~0U)
                throw std::runtime_error("Headlights: unavailable donor model");
            override_load_model(model);
            const auto &rig = override_state().donor_rigs.at(model);
            auto bone = std::find_if(rig.bones.begin(), rig.bones.end(),
                                     [&](const auto &b) { return b.name == lamp.attachment; });
            if (bone == rig.bones.end())
                throw std::runtime_error("Headlights: unavailable donor bone");
            bone_index = size_t(bone - rig.bones.begin());
            // Unbound helper bones inherit their nearest bound ancestor's survival.
            auto parent = bone;
            while (parent->control.empty() && parent->parent >= 0)
                parent = rig.bones.begin() + parent->parent;
            control = parent->control;
            if (control.empty())
                throw std::runtime_error("Headlights: bone has no live controller");
            pose = chassis_socket_pose(root, model);
        }
        const unsigned node = headlight_node(root, control);
        if (!node || (pose && !pose->raw.count(control))) {
            // A previously authenticated mount can be unlinked before the
            // destruction callback. Initial missing bindings still fail visibly.
            if (owner.retire_missing_mount(lamp.id))
                continue;
            throw std::runtime_error("Headlights: unresolved required attachment " + control);
        }
        owner.source_ancestry[lamp.id] = headlight_ancestry(node, root);
        if (pose)
            world = override_product(override_product(chassis_socket_world(root),
                                                      mw34::donor::inverse(mw34::donor::axis())),
                                     pose->pose.world.at(bone_index));
        else
            world = chassis_socket_world(node);
        owner.emitters[lamp.id] = mw34::headlights::transform(lamp, world);
    }
}
std::vector<mw34::fixtures::MovingLight> headlight_lights(float strength) {
    std::vector<mw34::fixtures::MovingLight> result;
    if (!headlight_enabled())
        return result;
    for (const auto &[actor, owner] : headlight_owners) {
        if (!owner.ready || owner.envelope.current <= 0)
            continue;
        const auto *record = headlight_registration(actor);
        if (!record)
            continue;
        // Stable actor and emitter-ID ordering supplies deterministic ties.
        for (const auto &[id, emitter] : owner.emitters) {
            if (!emitter.valid)
                continue;
            const auto lamp = std::find_if(record->headlights.begin(), record->headlights.end(),
                                           [&](const auto &l) { return l.id == id; });
            if (lamp == record->headlights.end())
                continue;
            mw34::fixtures::MovingLight selected;
            selected.light.start = {emitter.position[0], emitter.position[1], emitter.position[2],
                                    lamp->range};
            selected.light.end = {emitter.direction[0], emitter.direction[1], emitter.direction[2],
                                  2};
            selected.light.color = {lamp->color[0], lamp->color[1], lamp->color[2],
                                    float(lamp->intensity * strength * owner.envelope.current)};
            constexpr double radians = 3.14159265358979323846 / 180;
            selected.cone = {float(std::cos(lamp->inner_angle * radians)),
                             float(std::cos(lamp->outer_angle * radians)), 1, 0};
            result.push_back(selected);
        }
    }
    return result;
}
unsigned headlight_ai_budget{};
void headlight_ai_candidate(unsigned actor) {
    if (!mw34::sun::flag("MW34_HEADLIGHT_AI") || !headlight_ai_budget)
        return;
    const unsigned player = headlight_player();
    auto owner = headlight_owners.find(actor);
    if (!player || actor == player || owner == headlight_owners.end() || !owner->second.ready ||
        !readable(actor, 0x688) || !runtime.memory().load<unsigned char>({actor + 8}) ||
        load(actor + 0x578) == 10)
        return;
    const auto *record = headlight_registration(actor);
    if (!record || record->headlights.empty())
        return;
    const unsigned table = load(actor);
    if (!readable(table, 0x68))
        throw std::runtime_error("Headlights: unreadable AI ownership method");
    // Original virtual ownership query and relation predicate; preserve subclass dispatch.
    if (chassis_call(load(table + 0x64), actor, {}) || chassis_call(0x4d6130, actor, {player}))
        return;
    const unsigned distance = load(actor + 0x98);
    const float squared = distance && readable(distance, 16) ? wide_float(distance + 12) : 640000.f;
    if (!std::isfinite(squared) || squared < 0 || squared >= 62500)
        return;
    --headlight_ai_budget; // PM consumes this actor slot even when shut down.
    owner->second.envelope.desired = !headlight_shutdown(actor);
}
template <class Next> void *headlight_body(State *s, unsigned target, void *p, Next &&next) {
    if (!headlight_enabled())
        return next();
    switch (target) {
    case 0x4149f0:
    case 0x414f40:
    case 0x4152d0:
    case 0x415b00:
    case 0x41b0d0:
    case 0x41de80:
    case 0x4a8cd0:
    case 0x41e870:
    case 0x4eaea0:
    case 0x4a1160:
    case 0x427d60:
    case 0x46b0a0:
        break;
    default:
        return next();
    }
    const unsigned actor = state.gpr.rcx.dword;
    std::optional<HeadlightOwnerSnapshot> retiring_actor;
    std::vector<HeadlightOwnerSnapshot> retiring_node_owners;
    if (target == 0x414f40 || target == 0x4152d0) {
        const auto owner = headlight_owners.find(actor);
        if (owner != headlight_owners.end() &&
            (!readable(actor, 8) || headlight_actor_root_matches(actor, owner->second.root)))
            retiring_actor = HeadlightOwnerSnapshot{actor, owner->second.root,
                                                     owner->second.generation};
    }
    if (target == 0x4eaea0)
        for (const auto &[owner_actor, owner] : headlight_owners)
            if (owner.root && headlight_actor_root_matches(owner_actor, owner.root))
                retiring_node_owners.push_back({owner_actor, owner.root, owner.generation});
    if (target == 0x4a8cd0) {
        headlight_ai_budget = 1;
        for (auto &[id, owner] : headlight_owners)
            if (id != headlight_player())
                owner.envelope.desired = false;
    }
    if (target == 0x4149f0) {
        ControllerFp preserve;
        mw34::vkscene::HostFpEnvironment fp;
        if (headlight_owners.size() >= 1024)
            throw std::runtime_error("Headlights: actor capacity exceeded");
        headlight_owners[actor] = {++headlight_generation};
    }
    if (target == 0x4a1160) {
        if (photo_replay_consume_input())
            return next();
        {
            ControllerFp preserve;
            mw34::vkscene::HostFpEnvironment fp;
            headlight_seconds = wide_float(0x72c52c);
            if (headlight_seconds < 0) {
                std::fprintf(stderr,
                             "Headlights: holding envelope for nonpositive engine delta %.9g (bits "
                             "%08x) frame=%u\n",
                             headlight_seconds, load(0x72c52c), host.frames);
                headlight_seconds = 0;
            }
        }
        ++headlight_tick;
        ++headlight_world_depth;
        headlight_world_frame = host.frames;
        headlight_input(true);
        try {
            void *result = next();
            const State returned = state;
            {
                ControllerFp preserve;
                mw34::vkscene::HostFpEnvironment fp;
                for (auto &[id, owner] : headlight_owners)
                    if (owner.ready) {
                        owner.envelope.advance(headlight_seconds, headlight_tick,
                                               headlight_shutdown(id));
                        headlight_refresh(id, owner);
                        if (effect_trace() && host.frames % 60 == 0 && !owner.emitters.empty())
                            std::fprintf(stderr,
                                         "Headlights frame=%u tick=%llu actor=%08x root=%08x "
                                         "emitters=%zu intensity=%.6f dt=%.6f\n",
                                         host.frames, (unsigned long long)headlight_tick, id,
                                         owner.root, owner.emitters.size(), owner.envelope.current,
                                         headlight_seconds);
                    }
            }
            state = returned;
            --headlight_world_depth;
            return result;
        } catch (...) {
            --headlight_world_depth;
            throw;
        }
    }

    void *result = next();
    const State returned = state;
    {
        ControllerFp preserve;
        mw34::vkscene::HostFpEnvironment fp;
        if (target == 0x4eaea0)
            for (const auto &snapshot : retiring_node_owners) {
                const auto owner = headlight_owners.find(snapshot.actor);
                if (owner != headlight_owners.end() &&
                    owner->second.generation == snapshot.generation &&
                    owner->second.root == snapshot.root &&
                    ((actor == snapshot.root &&
                      !headlight_actor_root_matches(snapshot.actor, snapshot.root)) ||
                     (actor != snapshot.root && !headlight_node_in_root(actor, snapshot.root))))
                    owner->second.retire_node(actor, snapshot.generation);
            }
        if (retiring_actor && headlight_shutdown(actor)) {
            const auto owner = headlight_owners.find(retiring_actor->actor);
            if (owner != headlight_owners.end() && owner->second.root == retiring_actor->root)
                mw34::headlights::erase_generation(headlight_owners, retiring_actor->actor,
                                                   retiring_actor->generation);
        }
        if (target == 0x41e870)
            headlight_ai_candidate(actor);
        auto found = headlight_owners.find(actor);
        if (found != headlight_owners.end()) {
            if (target == 0x415b00) {
                found->second.ready = (state.gpr.rax.dword & 255) != 0;
                if (found->second.ready && headlight_registration(actor))
                    headlight_refresh(actor, found->second);
                else
                    headlight_owners.erase(found);
            } else if (target == 0x41de80) {
                found->second.bind_root(load(actor + 4));
            } else if (target == 0x41b0d0) {
                found->second.envelope = {};
                found->second.emitters.clear();
                found->second.source_ancestry.clear();
                found->second.ready = false;
            }
        }
    }
    state = returned;
    return result;
}

std::vector<mw34::photo_replay::ReplayHeadlightState> headlight_snapshot() {
    std::vector<mw34::photo_replay::ReplayHeadlightState> result;
    if (headlight_enabled())
        for (const auto &[actor, owner] : headlight_owners)
            if (owner.ready && owner.root && headlight_registration(actor))
                result.push_back({actor, owner.root, owner.chassis,
                                  unsigned(owner.envelope.desired), owner.generation,
                                  float(owner.envelope.current), 0});
    for (auto &saved : result)
        saved.retired_mask = mw34::headlights::retirement_mask(
            headlight_owners.at(saved.actor), *headlight_registration(saved.actor));
    return result;
}
void headlight_restore(const std::vector<mw34::photo_replay::ReplayHeadlightState> &lamps) {
    headlight_clear();
    if (!headlight_enabled())
        return;
    for (const auto &lamp : lamps) {
        const auto *record = headlight_registration(lamp.actor);
        if (!record || load(lamp.actor + 4) != lamp.root ||
            size_t(record - mw34::chassis::configured_catalog().data()) != lamp.chassis)
            throw std::runtime_error("Headlights: replay actor identity mismatch");
        auto &owner = headlight_owners[lamp.actor];
        owner.generation = lamp.generation;
        owner.ready = true;
        owner.envelope = {lamp.desired != 0, lamp.intensity, headlight_tick};
        headlight_generation = std::max(headlight_generation, lamp.generation);
        mw34::headlights::restore_retirement(owner, *record, lamp.retired_mask);
        headlight_refresh(lamp.actor, owner);
    }
}
