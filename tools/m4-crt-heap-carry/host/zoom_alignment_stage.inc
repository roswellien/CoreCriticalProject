// Original zoom camera geometry is CPU-projected into an engine viewport.
// The D3D viewport remains full-target and is not that camera's screen anchor.
// Snapshot display metadata while 442F50's exact zoom owner is still active.
unsigned zoom_display_owner{};
float zoom_display_anchor() {
    // Follow the authenticated zoom owner to its camera and viewport records.
    // All offsets and type tags below are guest layout contracts, not host pointers.
    const unsigned owner = zoom_display_owner;
    if (!owner || !readable(owner, 0x3c) || load(owner) != 0x5c0608)
        deny("Widescreen zoom scene owner unavailable", owner);
    const unsigned camera_node = load(owner + 0x38);
    if (!camera_node || !readable(camera_node, 0x3c) || load(camera_node + 0x34) != 1 ||
        pose_name(camera_node, 36) != "zoomcam")
        deny("Widescreen zoom scene camera unavailable", camera_node);
    const unsigned camera_data = load(camera_node + 0x38),
                   viewport_node =
                       camera_data && readable(camera_data, 8) ? load(camera_data + 4) : 0;
    const unsigned viewport_data =
        viewport_node && readable(viewport_node, 0x3c) && load(viewport_node + 0x34) == 3
            ? load(viewport_node + 0x38)
            : 0;
    if (!viewport_data || !readable(viewport_data, 16))
        deny("Widescreen zoom scene viewport unavailable", viewport_node);
    const int viewport_x = int(load(viewport_data)), viewport_y = int(load(viewport_data + 4)),
              viewport_width = int(load(viewport_data + 8)),
              viewport_height = int(load(viewport_data + 12));
    if (viewport_x < 0 || viewport_y < 0 || viewport_width <= 0 || viewport_height <= 0 ||
        std::int64_t(viewport_x) + viewport_width > host.display.width ||
        std::int64_t(viewport_y) + viewport_height > host.display.height)
        deny("Widescreen zoom scene viewport outside target", viewport_data);
    return float(viewport_x) + float(viewport_width) * .5f;
}
void zoom_capture_command(D3DCmd &command) {
    // Attach the anchor to this draw while its camera owner is active. A later
    // renderer lookup cannot reconstruct which original zoom camera submitted it.
    if (!wide_on() || command.hud_role != WideZoom)
        return;
    command.zoom_anchor = zoom_display_anchor();
    command.zoom_anchor_known = true;
    if (FILE *log = wide_log_file(); log && host.frames % 100 == 0) {
        static unsigned last_logged_frame = ~0U;
        if (last_logged_frame != host.frames) {
            last_logged_frame = host.frames;
            std::fprintf(log, "zoom-capture frame %u owner %08x lock %u anchor %.9g\n", host.frames,
                         zoom_display_owner, load(zoom_display_owner + 0x174) & 255,
                         double(command.zoom_anchor));
            std::fflush(log);
        }
    }
}
void *zoom_scene_body(State *guest_state, unsigned target, void *memory_context, Body body) {
    // Nest the display owner around the translated body and restore it on both
    // return and exception. Only presentation metadata is scoped here.
    const unsigned previous_owner = zoom_display_owner;
    zoom_display_owner = state.gpr.rcx.dword;
    void *body_result{};
    try {
        body_result = body(guest_state, target, memory_context);
    } catch (...) {
        zoom_display_owner = previous_owner;
        throw;
    }
    zoom_display_owner = previous_owner;
    return body_result;
}
