// Public Renderer members: the texture memory line (#518).
// Included inside Renderer's public section; it reads the texture cache, the
// parallax height total and the tracked device-local allocations.

// The driver's device-local usage and budget (VK_EXT_memory_budget), summed
// over the device-local heaps; empty when the driver gives no figures.
std::optional<DriverFigures> device_local_budget() const {
  DriverFigures figures;
  bool any_heap = false;
  for (unsigned heap = 0; heap < memory.memoryHeapCount; ++heap) {
    if (!(memory.memoryHeaps[heap].flags & VK_MEMORY_HEAP_DEVICE_LOCAL_BIT))
      continue;
    VkDeviceSize usage = 0, budget = 0;
    if (!heap_budget(heap, usage, budget))
      return std::nullopt;
    figures.usage_bytes += usage;
    figures.budget_bytes += budget;
    any_heap = true;
  }
  if (!any_heap)
    return std::nullopt;
  return figures;
}

// Prints one "mw3: texture memory" line to stderr (and so to mw3.log): bytes
// per texture source, the 16-bit share, the largest sizes, and the tracked and
// driver totals beside them. It never throws: losing the line is better than
// stopping a mission over a report.
void log_texture_memory(const char *reason) noexcept {
  try {
    std::vector<TextureMemoryRow> rows;
    rows.reserve(textures.size() + 1);
    for (const auto &[key, texture] : textures) {
      if (!texture.image)
        continue;
      rows.push_back({texture.source, texture.width, texture.height, texture.memory_size,
                      texture.pack != mw34::texture_staging::Pack16::none});
    }
    rows.push_back({TextureSource::height, 0, 0, height_resident_bytes, false});
    const auto line =
        texture_memory_line(reason, rows, tracked_device_local_bytes(), device_local_budget());
    std::fprintf(stderr, "%s\n", line.c_str());
  } catch (...) {
  }
}
