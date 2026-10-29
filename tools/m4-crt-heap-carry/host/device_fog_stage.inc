// Optional repair of the original fog cache lifetime across main-device creation.
// Original 57A900 creates the device into 809370 at return57AA9E, then calls
// 57BB70(1). That setter suppresses the call when cached8093B0 already equals1.
// A replacement device starts with FOGENABLE=0. Reconcile the cache with that
// real state and let original initialization decide whether to enable fog.
static bool device_fog_rebind_enabled() {
    // Capture the explicit 0/1 option once. Missing means disabled; unsupported
    // values fail instead of silently enabling a change to the original cache.
    static const bool enabled = [] {
        const char *setting_value = std::getenv("MW34_DEVICE_FOG_REBIND");
        if (!setting_value || !std::strcmp(setting_value, "0"))
            return false;
        if (!std::strcmp(setting_value, "1"))
            return true;
        throw std::runtime_error("MW34_DEVICE_FOG_REBIND must be 0 or 1");
    }();
    return enabled;
}
void device_fog_created(unsigned output_address, unsigned device_fog_enabled) {
    // Apply only to the observed main-device output slot and original return site.
    // The provider supplies actual fog state; this does not force fog on or call
    // a replacement render-state setter in place of original initialization.
    if (!device_fog_rebind_enabled() || output_address != 0x809370 ||
        load(state.gpr.rsp.dword) != 0x57aa9e)
        return;
    const unsigned cached_fog_enabled = load(0x8093b0);
    if (cached_fog_enabled > 1 || device_fog_enabled > 1)
        deny("Unknown original/device fog-enable state at main-device creation",
             cached_fog_enabled);
    store(0x8093b0, device_fog_enabled);
    if (const char *trace_path = std::getenv("MW34_FOG_TRACE")) {
        if (FILE *trace_file = std::fopen(trace_path, "a")) {
            std::fprintf(trace_file, "cache-sync frame %u old %u actual %u\n", host.frames,
                         cached_fog_enabled, device_fog_enabled);
            std::fclose(trace_file);
        }
    }
}
