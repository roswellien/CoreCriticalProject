// Read-only camera provenance; see docs/fidelityfx-camera-history.md for the
// original-image identity, controller/teleport chains and unsupported coverage.
std::uint64_t camera_flip_serial{}, camera_reset_epoch{}, camera_node_serial{};
struct CameraNodeEpoch {
    std::uint64_t epoch{};
    unsigned world{};
};
std::map<unsigned, CameraNodeEpoch> camera_node_epochs;
std::set<unsigned> camera_pause_instances;
unsigned camera_update_node{}, camera_terrain_node{};
std::shared_ptr<const mw34::temporal::Snapshot> camera_last_snapshot;
const char *camera_rejection{"none"};
std::array<char, 192> camera_rejection_text{};
std::uint64_t camera_rejection_frame{~std::uint64_t{}};
std::uint64_t camera_pause_entries{}, camera_pause_exits{}, camera_relocations{}, camera_presets{};
const char *camera_reset_signal{"none"};

void camera_advance(std::uint64_t &serial) {
    if (serial == ~std::uint64_t{})
        throw std::runtime_error("Camera epoch exhausted");
    ++serial;
}
void camera_reset(const char *signal = "transition") {
    camera_advance(camera_reset_epoch);
    camera_reset_signal = signal;
    camera_node_epochs.clear();
    camera_last_snapshot.reset();
    if (host.sren)
        host.sren->invalidate_camera_history(mw34::temporal::Reset::transition);
}
unsigned camera_context() {
    const unsigned context = load(0x5f4c8c);
    return context && readable(context, 0x7c) ? context : 0;
}
bool camera_mech(unsigned actor) {
    if (!actor || !readable(actor, 4))
        return false;
    const unsigned table = load(actor);
    return table == 0x5bcef8 || table == 0x5c3508;
}
bool camera_controller(unsigned context, unsigned controller) {
    return context && controller && readable(controller, 0x64) &&
           load(context + 0x58) == controller &&
           ((load(controller) == 0x5be9f0 && load(controller + 4) == 1) ||
            (load(controller) == 0x5bd2f8 && load(controller + 4) == 0)) &&
           load(controller + 0x60) == context && camera_mech(load(context + 0x64));
}
void camera_node_changed(unsigned node) {
    const auto found = camera_node_epochs.find(node);
    if (found == camera_node_epochs.end())
        return;
    camera_advance(camera_node_serial);
    found->second.epoch = camera_node_serial;
}
bool camera_hierarchy(unsigned node, unsigned data, unsigned controller) {
    const unsigned root = load(data);
    if (!root || !readable(root, 0x64) || load(root + 0x34) != 2 || load(root + 0x54))
        return false;
    const unsigned parents = load(node + 0x54);
    if (!parents)
        return true;
    // Original 4ED280 applies no pose transform at a type-2 world root. A
    // single reciprocal edge to that root is safe; arbitrary/head parents are not.
    if (parents != 1 || (load(controller + 4) == 1 &&
                         (!readable(controller + 0x64, 4) || (load(controller + 0x64) & 255))))
        return false;
    const unsigned parent_array = load(node + 0x58);
    if (!parent_array || !readable(parent_array, 4) || load(parent_array) != root)
        return false;
    const unsigned count = load(root + 0x5c), children = load(root + 0x60);
    if (!count || count > 65536 || !children || !readable(children, count * 4))
        return false;
    unsigned matches = 0;
    for (unsigned i = 0; i < count; ++i)
        matches += load(children + i * 4) == node;
    return matches == 1;
}
void camera_capture(D3DCmd &draw, unsigned target) {
    if (!mw34::temporal::enabled())
        return;
    SunCaptureFp preserve;
    mw34::vkscene::HostFpEnvironment fp;
    auto reject = [&](const char *reason) {
        camera_rejection = reason;
        if (draw.model && draw.model->world && host.sren)
            host.sren->invalidate_camera_history(mw34::temporal::Reset::invalid);
    };
    if (frontend_on() || !camera_pause_instances.empty() ||
        photo_replay.mode != mw34::photo_replay::Mode::Live || photo_replay_detached_cam() ||
        (draw.hud_role != WideWorld && draw.hud_role != WideZoom)) {
        reject("view-state");
        return;
    }
    const unsigned context = camera_context();
    if (!context || !camera_controller(context, load(context + 0x58))) {
        if (context && camera_rejection_frame != camera_flip_serial) {
            const unsigned controller = load(context + 0x58), actor = load(context + 0x64);
            auto word = [&](unsigned pointer, unsigned offset) {
                return pointer && readable(pointer + offset, 4) ? load(pointer + offset) : 0U;
            };
            std::snprintf(camera_rejection_text.data(), camera_rejection_text.size(),
                          "controller(ctx=%x,ptr=%x,table=%x,mode=%u,back=%x,actor=%x,table=%x)",
                          context, controller, word(controller, 0), word(controller, 4),
                          word(controller, 0x60), actor, word(actor, 0));
            camera_rejection_frame = camera_flip_serial;
        }
        reject(context ? camera_rejection_text.data() : "context");
        return;
    }
    if (::GetForegroundWindow() != host.display.window) {
        reject("unfocused");
        return;
    }
    OverrideMatrix world;
    if (!sun_camera_world(world)) {
        reject("activation");
        return;
    }
    const unsigned data = load(0x7402f4);
    unsigned node = load(context + 4);
    if (draw.hud_role == WideZoom) {
        const unsigned owner = distance_zoom_owner();
        if (!owner || !readable(owner, 0x3c))
            return;
        node = load(owner + 0x38);
    }
    // Only parentless or identity-world-root cameras are proven. Head/animated
    // parent matrices and alternate pose storage retain ordinary rendering.
    if (!node || !readable(node, 0x5c) || load(node + 0x38) != data || (load(data + 0x10) & 2) ||
        !camera_hierarchy(node, data, load(context + 0x58))) {
        reject("hierarchy");
        return;
    }
    const unsigned viewport = load(data + 4);
    if (!viewport || !readable(viewport, 0x3c))
        return;
    const unsigned rectangle = load(viewport + 0x38);
    if (!rectangle || !readable(rectangle, 16))
        return;
    if (!camera_node_epochs.count(node)) {
        if (camera_node_epochs.size() == mw34::temporal::History::capacity)
            throw std::runtime_error("Camera provenance view capacity exceeded");
        camera_advance(camera_node_serial);
        camera_node_epochs.emplace(node, CameraNodeEpoch{camera_node_serial, load(data)});
    }
    camera_node_epochs.at(node).world = load(data);
    mw34::temporal::Snapshot snapshot{};
    snapshot.view = {context, node, data, draw.hud_role};
    snapshot.frame = camera_flip_serial + 1;
    snapshot.load_epoch = mw34::campaign::CampaignManager::instance().reader_epoch();
    snapshot.reset_epoch = camera_reset_epoch;
    snapshot.camera_epoch = camera_node_epochs.at(node).epoch;
    snapshot.target = target;
    snapshot.attachment = load(data);
    snapshot.viewport = viewport;
    snapshot.controller = load(context + 0x58);
    snapshot.mode = load(snapshot.controller + 4);
    snapshot.camera = sun_view_binding.renderer;
    snapshot.inverse = sun_view_binding.inverse;
    snapshot.projection = {wide_float(0x73fb80), wide_float(0x73fc30), wide_float(0x73fb98),
                           wide_float(0x73fb88), wide_float(0x73fb8c), wide_float(0x740304)};
    snapshot.far_clip = wide_float(data + 0xb4);
    for (unsigned i = 0; i < 4; ++i)
        snapshot.viewport_rect[i] = load(rectangle + i * 4);
    if (!snapshot.finite())
        throw std::runtime_error("Invalid authenticated camera snapshot");
    if (!camera_last_snapshot || *camera_last_snapshot != snapshot)
        camera_last_snapshot = std::make_shared<const mw34::temporal::Snapshot>(snapshot);
    draw.camera_view = camera_last_snapshot;
}
// Use the existing selected-frame capture request, only after the real Flip.
// Binary outputs are private diagnostics; no guest memory is read here.
void temporal_dump_completed() {
    const char *list = std::getenv("MW34_HIRES_DUMP_FRAMES");
    const char *directory = std::getenv("MW34_HIRES_DUMP_DIR");
    if (!host.sren || !list || !directory)
        return;
    const auto frame = host.frames + 1;
    if (("," + std::string(list) + ",").find("," + std::to_string(frame) + ",") == std::string::npos)
        return;
    for (const auto &[view, pair] : host.sren->camera_history.pairs()) {
        const auto pixels = host.sren->capture_temporal(view);
        if (!pixels.width)
            continue;
        const auto prefix = std::filesystem::path(directory) /
                            ("temporal-" + std::to_string(frame) + "-" +
                             std::to_string(view.node) + "-" + std::to_string(view.role));
        auto write = [&](const char *suffix, const auto &values) {
            std::ofstream output(prefix.string() + suffix, std::ios::binary);
            output.exceptions(std::ios::badbit | std::ios::failbit);
            output.write(reinterpret_cast<const char *>(values.data()),
                         std::streamsize(values.size() * sizeof(values[0])));
        };
        write("-depth.f32", pixels.depth);
        write("-motion.f32", pixels.motion);
        write("-validity.u8", pixels.validity);
        std::ofstream metadata(prefix.string() + ".json");
        metadata.exceptions(std::ios::badbit | std::ios::failbit);
        metadata << "{\"frame\":" << pixels.frame << ",\"width\":" << pixels.width
                 << ",\"height\":" << pixels.height << ",\"history_valid\":"
                 << (pixels.history_valid ? "true" : "false") << ",\"jitter\":["
                 << pixels.jitter[0] << ',' << pixels.jitter[1] << "],\"previous_jitter\":["
                 << pixels.previous_jitter[0] << ',' << pixels.previous_jitter[1]
                 << "],\"depth_format\":\"R32_SFLOAT\",\"motion_format\":\"R32G32_SFLOAT\","
                    "\"validity_format\":\"R8_UNORM\",\"depth\":\"near_clip/camera_z\","
                    "\"motion\":\"previous-current unjittered render pixels; X right Y down\"}\n";
    }
}
void camera_present(unsigned flipped_target) {
    if (!mw34::temporal::enabled())
        return;
    SunCaptureFp preserve;
    if (!flipped_target) {
        camera_reset("non-flip");
        return;
    }
    camera_advance(camera_flip_serial);
    if (host.sren &&
        (!camera_pause_instances.empty() || photo_replay.mode != mw34::photo_replay::Mode::Live ||
         photo_replay_detached_cam() || ::GetForegroundWindow() != host.display.window))
        host.sren->invalidate_camera_history(mw34::temporal::Reset::transition);
    std::array<char, 384> diagnostic{};
    std::snprintf(diagnostic.data(), diagnostic.size(),
                  "%s signal=%s epoch=%llu pause=%llu/%llu relocations=%llu presets=%llu static=%llu/%llu/%llu types=%x cell=%llu/%llu/%llu source-reject=%s",
                  camera_rejection, camera_reset_signal, (unsigned long long)camera_reset_epoch,
                  (unsigned long long)camera_pause_entries, (unsigned long long)camera_pause_exits,
                  (unsigned long long)camera_relocations, (unsigned long long)camera_presets,
                  (unsigned long long)temporal_source_draws,(unsigned long long)temporal_source_admitted,
                  (unsigned long long)temporal_source_pairs,temporal_source_types,
                  (unsigned long long)temporal_cell_calls,(unsigned long long)temporal_placement_calls,
                  (unsigned long long)temporal_record_matches,temporal_source_rejection);
    if (host.sren)
        host.sren->complete_camera_history(camera_flip_serial, flipped_target, diagnostic.data());
    temporal_dump_completed();
    camera_rejection = "none";
    temporal_source_rejection="none";
}
void camera_surface_written(unsigned surface) {
    if (!mw34::temporal::enabled() || !host.sren || !camera_last_snapshot)
        return;
    if (surface == camera_last_snapshot->target || (host.res_zb && surface == host.res_zb))
        host.sren->invalidate_camera_history(mw34::temporal::Reset::external_write);
}
void camera_scene(mw34::vkscene::Scene &scene) {
    if (!mw34::temporal::enabled())
        return;
    SunCaptureFp preserve;
    if (scene.frontend_canvas || frontend_on()) {
        if (!effect_enabled())
            mw34::campaign::CampaignManager::instance().frontend();
        return;
    }
    for (const auto &draw : scene.draws) {
        if (!draw.camera_view || !draw.model || !draw.model->world)
            continue;
        if (!effect_enabled())
            mw34::campaign::CampaignManager::instance().enter_world();
        scene.world_frame = host.frames;
        scene.world_generation = draw.camera_view->load_epoch;
        scene.world_context = draw.camera_view->view.context;
        for (unsigned i = 0; i < 3; ++i)
            scene.world_eye[i] = std::bit_cast<float>(draw.camera_view->camera[9 + i]);
        scene.world_eye_valid = true;
        break;
    }
}
bool camera_hook_target(unsigned target) const {
    switch (target) {
    case 0x40adf0:
    case 0x40ae70:
    case 0x40af30:
    case 0x418f30:
    case 0x418e90:
    case 0x421c00:
    case 0x421d50:
    case 0x421e40:
    case 0x421760:
    case 0x421900:
    case 0x421d40:
    case 0x493040:
    case 0x4931e0:
    case 0x4f32e0:
    case 0x4f3390:
    case 0x4eb050:
    case 0x4eaf90:
    case 0x4f3560:
    case 0x4f3620:
    case 0x4f3870:
    case 0x4f36b0:
    case 0x4f3920:
        return true;
    default:
        return false;
    }
}
template <class Next> void *camera_body(State *, unsigned target, void *, Next &&next) {
    if (!camera_hook_target(target) || !mw34::temporal::enabled())
        return next();
    unsigned recipient{};
    bool leave_pause = false;
    unsigned normal_node{}, terrain_node{};
    {
        SunCaptureFp preserve;
        const unsigned context = camera_context(), object = state.gpr.rcx.dword;
        if(target==0x4eb050 || target==0x4eaf90)temporal_source_retire(object);
        if ((target == 0x40adf0 || target == 0x40ae70) && object == context)
            camera_reset("controller-switch");
        if ((target == 0x418f30 || target == 0x418e90) && context &&
            object == load(context + 0x64) && camera_mech(object)) {
            camera_advance(camera_relocations);
            camera_reset("relocation");
        }
        // Discrete look/recenter is separate from the continuous controller update.
        if ((target == 0x421c00 || target == 0x421d50 || target == 0x421900 ||
             target == 0x421d40) &&
            camera_controller(context, object)) {
            camera_advance(camera_presets);
            camera_reset("pose-preset");
        }
        if (target == 0x493040 && readable(object, 4) && load(object) == 0x5c40f0) {
            if (camera_pause_instances.size() == 8)
                throw std::runtime_error("Camera pause capacity exceeded");
            camera_pause_instances.insert(object);
            camera_advance(camera_pause_entries);
            camera_reset("pause-enter");
        }
        if (target == 0x4931e0 && camera_pause_instances.count(object)) {
            recipient = object;
            leave_pause = true;
            camera_advance(camera_pause_exits);
            camera_reset("pause-exit");
        }
        bool tracked_world = false;
        if (target == 0x4eb050 || target == 0x4eaf90)
            for (const auto &[node, epoch] : camera_node_epochs)
                tracked_world |= epoch.world == object;
        if (target == 0x4f32e0 || target == 0x4f3390 || tracked_world ||
            ((target == 0x4eb050 || target == 0x4eaf90) && readable(object, 0x3c) &&
             load(object + 0x34) == 1)) {
            camera_node_changed(object);
            camera_node_epochs.erase(object);
            camera_reset("camera-lifetime");
        }
        if (target == 0x4f3560 || target == 0x4f3620)
            camera_node_changed(object);
        if ((target == 0x4f3870 && object != camera_update_node) ||
            (target == 0x4f36b0 && object != camera_update_node) ||
            (target == 0x4f3920 && object != camera_terrain_node))
            camera_node_changed(object);
        if ((target == 0x421e40 || target == 0x421760) && camera_controller(context, object)) {
            const unsigned stack = state.gpr.rsp.dword;
            if (readable(stack + 8, 4) && load(stack + 8) == context)
                normal_node = load(context + 4);
        }
        if (target == 0x40af30 && context && object == context &&
            camera_controller(context, load(context + 0x58)))
            terrain_node = load(context + 4);
    }
    // Only integer scope ownership spans original execution. FP/LastError guards
    // enclose host observation, never the original body or its produced results.
    struct Scope {
        unsigned &slot;
        unsigned previous;
        Scope(unsigned &owner, unsigned node) : slot(owner), previous(owner) {
            if (node)
                slot = node;
        }
        ~Scope() { slot = previous; }
    } normal(camera_update_node, normal_node), terrain(camera_terrain_node, terrain_node);
    void *result = next();
    if (leave_pause) {
        SunCaptureFp preserve;
        camera_pause_instances.erase(recipient);
    }
    return result;
}
