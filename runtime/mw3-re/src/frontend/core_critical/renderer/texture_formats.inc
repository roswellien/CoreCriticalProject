// Private Renderer members: which 16-bit texture formats this device can use (#518).
// Included inside Renderer's private section.

static VkFormat format_for(mw34::texture_staging::Pack16 pack) {
  using mw34::texture_staging::Pack16;
  if (pack == Pack16::r5g6b5)
    return VK_FORMAT_R5G6B5_UNORM_PACK16;
  if (pack == Pack16::a1r5g5b5)
    return VK_FORMAT_A1R5G5B5_UNORM_PACK16;
  if (pack == Pack16::b4g4r4a4)
    return VK_FORMAT_B4G4R4A4_UNORM_PACK16;
  return VK_FORMAT_R8G8B8A8_UNORM;
}

// Run at device setup. A 16-bit format is used only where the device can
// sample and filter it and copy into and out of it (textures are created with
// both transfer usages), and, when anisotropy builds mip chains, blit it both
// ways. Vulkan requires all of that for R5G6B5 and A1R5G5B5, but only
// sampling, filtering and blit source for B4G4R4A4.
//
// With mip chains A1R5G5B5 stays off too. Each mip level is blitted into the
// image's own format, so its 1-bit alpha is rounded to fully clear or fully
// solid at every level, and a see-through texture's distant edges (leaves,
// fences) could come out thicker or thinner than its RGBA8 mips draw them
// (#518 code review). Such textures stay RGBA8 there.
void probe_pack16_formats() {
  using mw34::texture_staging::Pack16;
  using mw34::texture_staging::pack16_bit;
  const bool mip_chains = anisotropy() > 1;
  VkFormatFeatureFlags needed =
      VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT | VK_FORMAT_FEATURE_SAMPLED_IMAGE_FILTER_LINEAR_BIT |
      VK_FORMAT_FEATURE_TRANSFER_DST_BIT | VK_FORMAT_FEATURE_TRANSFER_SRC_BIT;
  if (mip_chains)
    needed |= VK_FORMAT_FEATURE_BLIT_SRC_BIT | VK_FORMAT_FEATURE_BLIT_DST_BIT;
  pack16_allowed_ = 0;
  for (const Pack16 pack : {Pack16::r5g6b5, Pack16::a1r5g5b5, Pack16::b4g4r4a4}) {
    VkFormatProperties properties{};
    f.vkGetPhysicalDeviceFormatProperties(gpu, format_for(pack), &properties);
    if ((properties.optimalTilingFeatures & needed) == needed)
      pack16_allowed_ |= pack16_bit(pack);
  }
  const bool device_has_a1r5g5b5 = (pack16_allowed_ & pack16_bit(Pack16::a1r5g5b5)) != 0;
  if (mip_chains)
    pack16_allowed_ &= ~pack16_bit(Pack16::a1r5g5b5);
  const auto usable = [this](Pack16 pack) {
    return (pack16_allowed_ & pack16_bit(pack)) ? "yes" : "no";
  };
  const char *a1r5g5b5 =
      device_has_a1r5g5b5 && mip_chains ? "no (mip chains)" : usable(Pack16::a1r5g5b5);
  std::fprintf(stderr, "mw3: 16-bit textures: r5g6b5 %s, a1r5g5b5 %s, b4g4r4a4 %s\n",
               usable(Pack16::r5g6b5), a1r5g5b5, usable(Pack16::b4g4r4a4));
}

// The formats textures may use now: what the device supports, less any a
// check switched off. Kept apart so device setup never undoes a check's mask.
unsigned pack16_allowed() const { return pack16_allowed_ & ~pack16_disabled_for_test_; }

// The storage for an upload of `texture_ref` over `existing` (null when the
// cache has no entry), under the preload or play rule. Only RGBA8 pixels from a
// source may_pack16 allows keep the 16-bit format the frontend gave them;
// anything else is stored as RGBA8, and an existing 16-bit image for it is
// remade. No texel is read here.
mw34::texture_staging::Pack16Choice choose_storage(mw34::texture_staging::Pack16Rule rule,
                                                   const Tex *existing,
                                                   const TextureRef &texture_ref) const {
  using mw34::texture_staging::Pack16;
  const bool has_image = existing && existing->image;
  const bool eligible =
      texture_ref.format == TexFormat::rgba8888 &&
      texture_ref.pixels32.size() == std::size_t(texture_ref.width) * texture_ref.height &&
      mw34::texture_staging::may_pack16(texture_ref.source);
  // Only a preload narrows an existing image, and only when that strands no
  // memory (choose_pack16): a new size remakes the image anyway.
  const bool narrowing_is_free =
      rule == mw34::texture_staging::Pack16Rule::from_content && has_image &&
      (existing->width != texture_ref.width || existing->height != texture_ref.height ||
       memory_freed_by_destroy(*existing));
  return mw34::texture_staging::choose_pack16(
      rule, has_image, has_image ? existing->pack : Pack16::none,
      eligible ? texture_ref.pack16 : Pack16::none, pack16_allowed(), narrowing_is_free);
}

// Whether destroying this texture's image gives its memory back to the card:
// always for an image with its own allocation (every play-time image), and for
// a slice of a shared preload block only when it is the block's last resource
// (release_memory frees a block with its last reference).
bool memory_freed_by_destroy(const Tex &texture) const {
  const auto block = preload_memory_blocks_.find(texture.memory);
  return block == preload_memory_blocks_.end() || block->second.references == 1;
}

unsigned pack16_allowed_{};
unsigned pack16_disabled_for_test_{};
