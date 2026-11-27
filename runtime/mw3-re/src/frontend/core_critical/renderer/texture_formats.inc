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
void probe_pack16_formats() {
  using mw34::texture_staging::Pack16;
  VkFormatFeatureFlags needed =
      VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT | VK_FORMAT_FEATURE_SAMPLED_IMAGE_FILTER_LINEAR_BIT |
      VK_FORMAT_FEATURE_TRANSFER_DST_BIT | VK_FORMAT_FEATURE_TRANSFER_SRC_BIT;
  if (anisotropy() > 1)
    needed |= VK_FORMAT_FEATURE_BLIT_SRC_BIT | VK_FORMAT_FEATURE_BLIT_DST_BIT;
  pack16_allowed_ = 0;
  for (const Pack16 pack : {Pack16::r5g6b5, Pack16::a1r5g5b5, Pack16::b4g4r4a4}) {
    VkFormatProperties properties{};
    f.vkGetPhysicalDeviceFormatProperties(gpu, format_for(pack), &properties);
    if ((properties.optimalTilingFeatures & needed) == needed)
      pack16_allowed_ |= mw34::texture_staging::pack16_bit(pack);
  }
  const auto usable = [this](Pack16 pack) {
    return (pack16_allowed_ & mw34::texture_staging::pack16_bit(pack)) ? "yes" : "no";
  };
  std::fprintf(stderr, "mw3: 16-bit textures: r5g6b5 %s, a1r5g5b5 %s, b4g4r4a4 %s\n",
               usable(Pack16::r5g6b5), usable(Pack16::a1r5g5b5), usable(Pack16::b4g4r4a4));
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
  return mw34::texture_staging::choose_pack16(
      rule, has_image, has_image ? existing->pack : Pack16::none,
      eligible ? texture_ref.pack16 : Pack16::none, pack16_allowed());
}

unsigned pack16_allowed_{};
unsigned pack16_disabled_for_test_{};
