// Display provenance for the original translucent queue. Source meshes and HUD
// producers have returned before it flushes. Keep their display policy without
// changing the original descriptors, vertices, sorting or return values.
// Several material backends enqueue; 57E110 later sorts and draws descriptors.
struct HudDeferredPanel {
    unsigned role, type, count, material_reference, vertices, frame;
    bool suppress_source;
};
std::map<unsigned, HudDeferredPanel> hud_deferred_panels;
unsigned hud_deferred_restored{};
unsigned hud_panel_producer_role() const {
    // Walk the translated return stack from the innermost caller. These return
    // sites identify the panel's original producer before deferred sorting loses
    // that context; they are not inferred from a texture or screen position.
    for (unsigned stack_index = depth; stack_index > 0; --stack_index)
        switch (returns[stack_index - 1]) {
        case 0x43c767:
            return WideLeft;
        case 0x43c77d:
        case 0x43c797:
        case 0x43c7c2:
            return WideRight;
        }
    return WideWorld;
}
void hud_deferred_record(unsigned descriptor, unsigned role, bool suppress_source) {
    if (!readable(descriptor, 16))
        deny("Deferred descriptor unavailable", descriptor);
    const unsigned type = load(descriptor), count = load(descriptor + 4),
                   material_reference = load(descriptor + 8), vertices = load(descriptor + 12);
    if ((role && material_reference) || !count || count > 24000 || vertices < 0x82449c ||
        std::uint64_t(vertices) + 32ULL * count > 0x82449c + 32ULL * 24000 ||
        !readable(vertices, 32 * count))
        deny("Deferred draw outside original queue contract", descriptor);
    auto existing = hud_deferred_panels.find(descriptor);
    if (existing != hud_deferred_panels.end()) {
        auto &record = existing->second;
        if (record.frame != host.frames || record.type != type || record.count != count ||
            record.material_reference != material_reference || record.vertices != vertices ||
            (role && record.role && role != record.role))
            deny("Deferred provenance disagrees with an existing descriptor", descriptor);
        if (role)
            record.role = role;
        record.suppress_source = record.suppress_source || suppress_source;
    } else {
        hud_deferred_panels[descriptor] = {
            role, type, count, material_reference, vertices, host.frames, suppress_source};
    }
}
void *hud_panel_body(State *guest_state, unsigned target, void *memory_context, Body body) {
    // A zero original queue count starts a fresh set of descriptor metadata.
    // Record provenance only after the original body appends exactly one entry.
    const unsigned queued_before = load(0x803550);
    const unsigned role = wide_on() ? hud_panel_producer_role() : unsigned(WideWorld);
    if (!queued_before)
        hud_deferred_panels.clear();
    void *body_result = body(guest_state, target, memory_context);
    const unsigned queued_after = load(0x803550);
    if (role && queued_before < 6000 && queued_after == queued_before + 1)
        hud_deferred_record(0x80cd9c + 16 * queued_before, role, false);
    return body_result;
}
void *hud_deferred_source_body(State *guest_state, unsigned target, void *memory_context, Body body) {
    // The authenticated source-mesh producer owns every polygon it appends,
    // irrespective of which original material backend performs the enqueue.
    const unsigned queued_before = load(0x803550);
    if (!queued_before)
        hud_deferred_panels.clear();
    try {
        void *body_result = body(guest_state, target, memory_context);
        // Preview sources without an emitted replacement and original/fallback
        // appearances retain their existing eligibility.
        if (!override_suppress_draw())
            return body_result;
        const unsigned queued_after = load(0x803550);
        if (queued_after < queued_before || queued_after > 6000)
            deny("Deferred source queue changed lifetime inside its mesh producer", queued_after);
        for (unsigned index = queued_before; index < queued_after; ++index)
            hud_deferred_record(0x80cd9c + 16 * index, WideWorld, true);
        return body_result;
    } catch (...) {
        hud_deferred_panels.clear();
        throw;
    }
}
const HudDeferredPanel *hud_deferred_panel(unsigned type, unsigned vertices, unsigned count) {
    // Provider calls bypass enter(); their CALL return is on the guest stack,
    // while returns[] still describes the surrounding translated flush.
    if (!readable(state.gpr.rsp.dword, 4) || load(state.gpr.rsp.dword) != 0x57e2ed)
        return nullptr;
    const unsigned descriptor = state.gpr.rsi.dword;
    auto queued_panel = hud_deferred_panels.find(descriptor);
    if (queued_panel == hud_deferred_panels.end())
        return nullptr;
    // A known descriptor must still match this frame and the live guest record.
    // Unknown submissions use fallback; changed known records fail visibly rather
    // than being stretched using another panel's stale presentation metadata.
    const auto &panel = queued_panel->second;
    if (panel.frame != host.frames || panel.type != type || panel.count != count ||
        panel.vertices != vertices || !readable(descriptor, 16) || load(descriptor) != type ||
        load(descriptor + 4) != count || load(descriptor + 8) != panel.material_reference ||
        load(descriptor + 12) != vertices || !readable(vertices, 32 * count))
        deny("Deferred draw identity changed before flush", descriptor);
    return &panel;
}
unsigned hud_deferred_role(unsigned type, unsigned vertices, unsigned count, unsigned fallback) {
    if (!wide_on())
        return fallback;
    const auto *panel = hud_deferred_panel(type, vertices, count);
    if (!panel || !panel->role)
        return fallback;
    const unsigned descriptor = state.gpr.rsi.dword;
    if (FILE *log = wide_log_file();
        log && (hud_deferred_restored < 8 || host.frames == hud_detail_frame)) {
        std::fprintf(
            log,
            "deferred-panel frame %u descriptor %08x vertices %08x count %u role %u (late %u)\n",
            host.frames, descriptor, vertices, count, panel->role, fallback);
        std::fflush(log);
    }
    ++hud_deferred_restored;
    return panel->role;
}
bool hud_deferred_source_suppressed(unsigned type, unsigned vertices, unsigned count) {
    const auto *panel = hud_deferred_panel(type, vertices, count);
    return panel && panel->suppress_source;
}
