// Original 43C6B0 obtains the target rectangle through 4425D0 and calls
// 576CE0 at 43C725; its player clear calls at 43C743. A native trace authenticates
// the player's 530..605 rectangle at 43C748; the paired target clear returns
// at 43C72A. The saved returns below
// survive 576CE0's tail jump to 577770, whose surface Blt uses DEPTHFILL.
// These calls precede the preview scopes used to classify geometry. A raw
// depth rectangle leaves cockpit depth over the moved schematic's right edge.
unsigned status_preview_clear_role() const {
    for (unsigned i = depth; i > 0; --i) {
        if (returns[i - 1] == 0x43c72a)
            return WideLeft;
        if (returns[i - 1] == 0x43c748)
            return WideRight;
    }
    return WideWorld;
}

RECT status_preview_depth_rect(RECT rect, unsigned width, unsigned height) {
    const unsigned role = status_preview_clear_role();
    if (!role || !wide_on() || frontend_on())
        return rect;
    SunCaptureFp preserve;
    mw34::vkscene::HostFpEnvironment fp;
    const RECT adjusted = wide_rect(rect, role, width, height);
    static const bool trace = [] {
        const char *value = std::getenv("MW34_STATUS_CLEAR_TRACE");
        return value && !std::strcmp(value, "1");
    }();
    static unsigned logged{};
    if (trace && (logged++ < 4 || host.frames % 100 == 0))
        std::fprintf(
            stderr,
            "Status depth clear frame=%u role=%u raw=%ld,%ld,%ld,%ld adjusted=%ld,%ld,%ld,%ld\n",
            host.frames, role, rect.left, rect.top, rect.right, rect.bottom, adjusted.left,
            adjusted.top, adjusted.right, adjusted.bottom);
    return adjusted;
}
