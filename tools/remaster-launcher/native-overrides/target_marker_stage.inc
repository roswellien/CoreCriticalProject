// Display-only target-marker adaptation. Original 440B00 chooses the camera;
// 440510 receives that choice at [ESP+C]. Only the three triangle line draws
// under 441490 consume this provenance. Lead cues and offscreen arrows do not.
struct TargetMarkerProjection {
    unsigned frame{};
    bool zoom{};
    float anchor{};
};
std::map<unsigned, TargetMarkerProjection> target_marker_projections;
unsigned target_marker_update_owner{}, target_marker_draw_owner{};
unsigned target_marker_clip{}, target_marker_clip_output{};
void target_marker_owner(unsigned owner) {
    if (!owner || !readable(owner, 0x2408) || load(owner) != 0x5c03e8)
        deny("Widescreen target marker owner unavailable", owner);
}
float target_marker_camera_anchor(unsigned owner) {
    // Reuse the zoom-camera traversal without leaking a temporary owner into
    // subsequent draws. The original target owner and zoom owner are distinct.
    target_marker_owner(owner);
    const unsigned previous_owner = zoom_display_owner;
    zoom_display_owner = load(owner + 0x34) + 0x1508;
    try {
        const float anchor = zoom_display_anchor();
        zoom_display_owner = previous_owner;
        return anchor;
    } catch (...) {
        zoom_display_owner = previous_owner;
        throw;
    }
}
const TargetMarkerProjection &target_marker_projection() {
    // An address match alone is insufficient: provenance must come from a builder
    // call in this frame, so a retained object cannot reuse last frame's camera.
    target_marker_owner(target_marker_draw_owner);
    const auto it = target_marker_projections.find(target_marker_draw_owner);
    if (it == target_marker_projections.end() || it->second.frame != host.frames)
        deny("Widescreen target triangle has no current camera provenance",
             target_marker_draw_owner);
    return it->second;
}
bool target_marker_zoom() { return target_marker_projection().zoom; }
float target_marker_anchor() {
    const auto &projection = target_marker_projection();
    if (!projection.zoom)
        deny("Widescreen target triangle is not zoom-projected", target_marker_draw_owner);
    return projection.anchor;
}
void *target_marker_body(State *guest_state, unsigned target, void *memory_context, Body body) {
    // These addresses identify observed producer/consumer boundaries. Keep the
    // original bodies responsible for camera choice, target choice and clip flags.
    if (target == 0x440b00) {
        const unsigned owner = state.gpr.rcx.dword;
        target_marker_owner(owner);
        const unsigned previous_owner = target_marker_update_owner,
                       previous_clip_code = target_marker_clip,
                       previous_clip_output = target_marker_clip_output;
        target_marker_update_owner = owner;
        target_marker_clip = target_marker_clip_output = 0;
        target_marker_projections.erase(owner);
        try {
            void *body_result = body(guest_state, target, memory_context);
            target_marker_update_owner = previous_owner;
            target_marker_clip = previous_clip_code;
            target_marker_clip_output = previous_clip_output;
            return body_result;
        } catch (...) {
            target_marker_update_owner = previous_owner;
            target_marker_clip = previous_clip_code;
            target_marker_clip_output = previous_clip_output;
            throw;
        }
    }
    if (target == 0x441490) {
        const unsigned previous_owner = target_marker_draw_owner;
        target_marker_draw_owner = state.gpr.rcx.dword;
        target_marker_owner(target_marker_draw_owner);
        try {
            void *body_result = body(guest_state, target, memory_context);
            target_marker_draw_owner = previous_owner;
            return body_result;
        } catch (...) {
            target_marker_draw_owner = previous_owner;
            throw;
        }
    }
    if (target == 0x440510) {
        const unsigned owner = state.gpr.rcx.dword, stack_pointer = state.gpr.rsp.dword;
        target_marker_owner(owner);
        if (owner != target_marker_update_owner || !readable(stack_pointer, 16))
            deny("Widescreen target builder outside update scope", owner);
        const unsigned zoom = load(stack_pointer + 12) & 255;
        if (zoom > 1)
            deny("Unknown original target projection choice", zoom);
        const float anchor = zoom ? target_marker_camera_anchor(owner) : 0.f;
        void *body_result = body(guest_state, target, memory_context);
        target_marker_projections[owner] = {host.frames, zoom != 0, anchor};
        if (FILE *log = wide_log_file(); log && host.frames % 10 == 0)
            std::fprintf(log, "target-marker-built frame %u owner %08x zoom %u anchor %.9g\n",
                         host.frames, owner, zoom, double(anchor));
        return body_result;
    }
    if (target == 0x53cf10) {
        const unsigned return_address = load(state.gpr.rsp.dword),
                       output_address = state.gpr.rdx.dword;
        void *body_result = body(guest_state, target, memory_context);
        if (return_address == 0x440cc6) {
            target_marker_clip = state.gpr.rax.dword;
            target_marker_clip_output = output_address;
        }
        return body_result;
    }
    // Let 40DA30 finish the original coordinate conversion first. On the
    // nonzero zoom-clip branch this temporary X is used only by 440D21..D6C
    // to decide whether the normal marker lies underneath the zoom window.
    // Transform that comparison edge to the actual displayed footprint. Never
    // modify clip flags, the zoom-inside result, main projection or target choice.
    const unsigned return_address = load(state.gpr.rsp.dword), output_address = state.gpr.rcx.dword;
    void *body_result = body(guest_state, target, memory_context);
    if (return_address == 0x440cd1 && target_marker_clip <= 15 && (target_marker_clip & 3)) {
        if (output_address != target_marker_clip_output || !readable(output_address, 12) ||
            load(0x5f4d4c) != 0)
            deny("Widescreen target occlusion coordinate profile unavailable", output_address);
        mw34::vkscene::HostFpEnvironment host_fp_environment;
        const float center = target_marker_camera_anchor(target_marker_update_owner);
        const float original_x = wide_float(output_address),
                    hud_factor = wide_hud_factor(host.display.width, host.display.height);
        const float display_x = center + (original_x + .5f - center) / hud_factor - .5f;
        wide_store_float(output_address, display_x);
        if (FILE *log = wide_log_file(); log && host.frames % 10 == 0)
            std::fprintf(
                log,
                "target-marker-occlusion frame %u owner %08x code %u center %.9g edge %.9g -> %.9g\n",
                host.frames, target_marker_update_owner, target_marker_clip, double(center),
                double(original_x), double(display_x));
    }
    return body_result;
}
