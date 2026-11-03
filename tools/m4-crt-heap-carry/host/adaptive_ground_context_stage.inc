// Included inside Stage. Authenticate a value copy for CPU geometry jobs without
// publishing camera history or advancing any history/jitter/presentation owner.
std::optional<mw34::adaptive_ground::FrameIdentity>
adaptive_ground_context(unsigned source, unsigned mesh, unsigned polygon, unsigned material) {
    SunCaptureFp preserve;
    if (!mw34::temporal::enabled() || !host.sren || frontend_on() ||
        !camera_pause_instances.empty() || photo_replay.mode != mw34::photo_replay::Mode::Live ||
        photo_replay_detached_cam() || ::GetForegroundWindow() != host.display.window ||
        wide_hud_role() != WideWorld)
        return {};
    // Initial jobs cover the native-size world route. Other configured scales
    // retain original execution until their effective dimensions can be proven.
    const char *percent = std::getenv("MW34_WORLD_SCALE_PERCENT");
    if ((percent && *percent && std::strcmp(percent, "100")) || host.sren->frontend_canvas())
        return {};
    const unsigned context = camera_context();
    if (!context || !camera_controller(context, load(context + 0x58)))
        return {};
    const unsigned data = load(0x7402f4), node = load(context + 4);
    if (!data || !readable(data, 0x100) || !node || !readable(node, 0x64) ||
        load(node + 0x38) != data || (load(data + 0x10) & 2) ||
        !camera_hierarchy(node, data, load(context + 0x58)))
        return {};
    const auto epoch = camera_node_epochs.find(node);
    // The first frame after a reset/lifetime change has no authenticated epoch
    // yet. Do not create one early merely to make a job eligible.
    if (epoch == camera_node_epochs.end() || epoch->second.world != load(data))
        return {};
    OverrideMatrix world;
    if (!sun_camera_world(world))
        return {};
    D3DDev *device{};
    for (auto &candidate : host.devices) {
        auto *object = host.com_object(candidate.guest);
        if (!candidate.in_scene || !object || !object->alive)
            continue;
        if (device)
            return {};
        device = &candidate;
    }
    if (!device)
        return {};
    const auto *surface = vsurf_of(device->target);
    const unsigned viewport = load(data + 4);
    if (!surface || !viewport || !readable(viewport, 0x3c))
        return {};
    const unsigned rectangle = load(viewport + 0x38);
    if (!rectangle || !readable(rectangle, 16))
        return {};
    mw34::adaptive_ground::FrameIdentity identity;
    auto &snapshot = identity.camera;
    snapshot.view = {context, node, data, WideWorld};
    snapshot.frame = camera_flip_serial + 1;
    snapshot.load_epoch = mw34::campaign::CampaignManager::instance().reader_epoch();
    snapshot.reset_epoch = camera_reset_epoch;
    snapshot.camera_epoch = epoch->second.epoch;
    snapshot.target = device->target;
    snapshot.attachment = load(data);
    snapshot.viewport = viewport;
    snapshot.controller = load(context + 0x58);
    snapshot.mode = load(snapshot.controller + 4);
    snapshot.camera = sun_view_binding.renderer;
    snapshot.inverse = sun_view_binding.inverse;
    snapshot.projection = {adaptive_ground_float(0x73fb80), adaptive_ground_float(0x73fc30),
                           adaptive_ground_float(0x73fb98), adaptive_ground_float(0x73fb88),
                           adaptive_ground_float(0x73fb8c), adaptive_ground_float(0x740304)};
    snapshot.far_clip = adaptive_ground_float(data + 0xb4);
    for (unsigned index = 0; index < 4; ++index)
        snapshot.viewport_rect[index] = load(rectangle + index * 4);
    const auto dimensions = host.sren->geometry_dimensions(surface->width, surface->height);
    if (!dimensions)
        return {};
    snapshot.sizes = *dimensions;
    if (!snapshot.finite(true))
        return {};
    identity.source_epoch = temporal_source_epoch;
    identity.heap_release_serial = host.gheap.frees;
    identity.memory_generation = mw34::fastmem::generation;
    identity.source_node = source;
    identity.mesh = mesh;
    identity.polygon = polygon;
    identity.material = material;
    identity.device = device->guest;
    for (unsigned index = 0; index < 4; ++index)
        identity.clip_rectangle[index] = load(0x74031c + index * 4);
    return identity;
}
