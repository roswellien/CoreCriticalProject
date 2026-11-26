// The report header: facts about the player's setup that playtest reports kept
// lacking (Vulkan device, video memory budgets, display, HDR, pack texture sizes,
// input devices). Only the fields below are kept, each with its type checked and
// its length bounded; anything else the launcher sends is dropped.
//
// Path redaction lives with the endpoint (api/crash-reports.js), which passes it
// in as redactText. This module must not import the endpoint.

function isPlainObject(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
}

function isCount(value, maximum = Number.MAX_SAFE_INTEGER) {
    return Number.isSafeInteger(value) && value >= 0 && value <= maximum;
}

function keepText(target, name, value, maxLength, redactText) {
    if (typeof value === "string") target[name] = redactText(value.slice(0, maxLength));
}

function validateHeap(heap) {
    if (!isPlainObject(heap)) return null;
    const kept = {};
    if (isCount(heap.index, 64)) kept.index = heap.index;
    if (isCount(heap.size_bytes)) kept.size_bytes = heap.size_bytes;
    if (isCount(heap.budget_bytes)) kept.budget_bytes = heap.budget_bytes;
    if (typeof heap.device_local === "boolean") kept.device_local = heap.device_local;
    return Object.keys(kept).length > 0 ? kept : null;
}

function validatePackTextures(pack, redactText) {
    if (!isPlainObject(pack)) return null;
    const kept = {};
    keepText(kept, "id", pack.id, 120, redactText);
    if (isCount(pack.bytes)) kept.bytes = pack.bytes;
    return Object.keys(kept).length > 0 ? kept : null;
}

// Returns only the fields that passed their checks; an empty object when none did.
export function validateHeader(header, redactText) {
    const source = isPlainObject(header) ? header : {};
    const kept = {};
    keepText(kept, "vulkan_device", source.vulkan_device, 200, redactText);
    keepText(kept, "vulkan_api_version", source.vulkan_api_version, 40, redactText);
    keepText(kept, "vulkan_driver_version", source.vulkan_driver_version, 80, redactText);
    if (Array.isArray(source.heaps)) {
        const heaps = source.heaps.slice(0, 16).map(validateHeap).filter(Boolean);
        if (heaps.length > 0) kept.heaps = heaps;
    }
    keepText(kept, "resolution", source.resolution, 40, redactText);
    keepText(kept, "window_mode", source.window_mode, 40, redactText);
    if (isCount(source.refresh_hz, 1000)) kept.refresh_hz = source.refresh_hz;
    if (typeof source.hdr === "boolean") kept.hdr = source.hdr;
    if (Array.isArray(source.pack_texture_bytes)) {
        const packs = source.pack_texture_bytes
            .slice(0, 64)
            .map((pack) => validatePackTextures(pack, redactText))
            .filter(Boolean);
        if (packs.length > 0) kept.pack_texture_bytes = packs;
    }
    if (Array.isArray(source.input_devices)) {
        const devices = source.input_devices
            .slice(0, 16)
            .filter((name) => typeof name === "string")
            .map((name) => redactText(name.slice(0, 80)));
        if (devices.length > 0) kept.input_devices = devices;
    }
    return kept;
}
