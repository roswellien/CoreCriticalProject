// Renderer-private height upload/descriptor assembly. Included after Tex.
// Weak ownership preserves the producer's decoded-budget retirement policy;
// Vulkan images retire only after the renderer has settled its scene fence.
struct HeightImageKey {
  std::weak_ptr<const mw34::materials::SurfaceMaterialImage> owner;
  const mw34::materials::SurfaceMaterialImage *image{};
  std::string source_sha256, sidecar_sha256, name;
  std::uint64_t mesh_uv_hash{}, image_version{}, producer_epoch{}, texture_version{}, hash{};
  unsigned width{}, height{}, role{};
  bool operator<(const HeightImageKey &other) const {
    if (owner.owner_before(other.owner)) return true;
    if (other.owner.owner_before(owner)) return false;
    // The alias address distinguishes multiple images in one immutable pack.
    if (std::less<const mw34::materials::SurfaceMaterialImage *>{}(image, other.image))
      return true;
    if (std::less<const mw34::materials::SurfaceMaterialImage *>{}(other.image, image))
      return false;
    return std::tie(source_sha256, sidecar_sha256, name, mesh_uv_hash, image_version,
                    producer_epoch, texture_version, hash, width, height, role) <
           std::tie(other.source_sha256, other.sidecar_sha256, other.name, other.mesh_uv_hash,
                    other.image_version, other.producer_epoch, other.texture_version,
                    other.hash, other.width, other.height, other.role);
  }
};
struct HeightImage {
  Tex texture;
  std::uint64_t bytes{};
};
struct HeightUpload {
  HeightImage *cached{};
  const mw34::materials::SurfaceMaterialImage *source{};
};
struct MaterialDescriptorKey {
  std::uint64_t normal_key{}, normal_version{}, normal_source_hash{};
  unsigned normal_width{}, normal_height{}, normal_sampler{}, height_sampler{};
  std::optional<HeightImageKey> height;
  bool operator<(const MaterialDescriptorKey &other) const {
    return std::tie(normal_key, normal_version, normal_source_hash, normal_width,
                    normal_height, normal_sampler, height_sampler, height) <
           std::tie(other.normal_key, other.normal_version, other.normal_source_hash,
                    other.normal_width, other.normal_height, other.normal_sampler,
                    other.height_sampler, other.height);
  }
};
std::map<HeightImageKey, HeightImage> height_images;
Buffer height_upload;
std::uint64_t height_resident_bytes{};

bool height_enabled(const Scene &scene, const Draw &draw) const {
  if (!bridge_config.parallax_materials || !draw.height_binding || scene.hud ||
      scene.frontend_canvas || draw.sky || draw.native_sky || draw.detail_role ||
      draw.key.blend || !draw.key.zenable || !draw.key.zwrite || draw.key.points || draw.depth_only ||
      draw.condition_schematic || draw.geometry_debug_normals ||
      !(draw.push.mode[0] & 4U) || (draw.push.mode[0] & 32U))
    return false;
  if (!sun_lit(draw))
    throw std::runtime_error("POM receiver lacks its required supported world/normal route");
  return true;
}
void validate_height(const Scene &scene, const Draw &draw,
                      const std::vector<Tex *> &bound) const {
  using namespace mw34::materials;
  const auto &binding = *draw.height_binding;
  const auto &material = binding.material;
  const auto digest = [](const std::string &value) {
    return value.size() == 64 &&
           value.find_first_not_of("0123456789abcdef") == std::string::npos;
  };
  if (!binding.image || !digest(binding.source_sha256) || !digest(binding.sidecar_sha256) ||
      !binding.mesh_uv_hash || binding.image_version != 1 || !binding.producer_epoch ||
      !binding.texture_version || !binding.albedo.hash ||
      !binding.normal_hash || !binding.retained_decoded_bytes ||
      binding.retained_decoded_bytes > max_surface_sidecar_bytes ||
      material.height_image == no_surface_image ||
      !std::isfinite(material.height_reference) || material.height_reference < 0 ||
      material.height_reference > 1 || !std::isfinite(material.height_amplitude) ||
      std::abs(material.height_amplitude) > max_surface_world_amplitude ||
      !std::isfinite(material.max_displacement) ||
      material.max_displacement < std::abs(material.height_amplitude) ||
      material.max_displacement > max_surface_world_amplitude)
    throw std::runtime_error("POM requires a complete immutable height binding");
  const auto &image = *binding.image;
  if (image.role != surface_role_height || !image.hash || !image.width || !image.height ||
      image.width > max_surface_dimension || image.height > max_surface_dimension ||
      image.pixels.size() != std::uint64_t(image.width) * image.height ||
      image.pixels.size() * 4ULL > binding.retained_decoded_bytes)
    throw std::runtime_error("POM height image dimensions/role/reservation mismatch");
  VkPhysicalDeviceProperties properties{};
  f.vkGetPhysicalDeviceProperties(gpu, &properties);
  if (image.width > properties.limits.maxImageDimension2D ||
      image.height > properties.limits.maxImageDimension2D)
    throw std::runtime_error("POM height image exceeds the device limit");
  if (draw.texture < 0 || std::size_t(draw.texture) >= scene.textures.size() ||
      draw.normal_texture < 0 || std::size_t(draw.normal_texture) >= scene.textures.size())
    throw std::runtime_error("POM has no admitted albedo/normal texture");
  const auto &albedo = scene.textures[std::size_t(draw.texture)];
  const auto &normal = scene.textures[std::size_t(draw.normal_texture)];
  // TextureRef.hash is the upload VERSION, not the original source-pixel hash.
  // The producer authenticates SurfaceKey; compare its dimensions and its
  // versioned upload here without conflating those two independent identities.
  if (binding.albedo.width != albedo.width || binding.albedo.height != albedo.height ||
      binding.albedo.format != 1 || binding.normal_width != normal.width ||
      binding.normal_height != normal.height || !normal.width || !normal.height ||
      binding.texture_version != albedo.hash)
    throw std::runtime_error("POM admitted albedo/normal snapshot differs from this draw");
  if (bound[std::size_t(draw.texture)]->source_rgb565_hash != binding.albedo.hash ||
      bound[std::size_t(draw.normal_texture)]->source_rgba8_hash != binding.normal_hash)
    throw std::runtime_error("POM source albedo/normal hash differs from the immutable binding");
  for (unsigned axis = 0; axis < 2; ++axis) {
    const float scale = material.uv_scale[axis], offset = material.uv_offset[axis];
    const float low = material.atlas_rect[axis], high = material.atlas_rect[axis + 2];
    const unsigned dimension = axis ? image.height : image.width;
    const unsigned address = axis ? material.address_mode_v : material.address_mode_u;
    if (!std::isfinite(scale) || std::abs(scale) < 1e-6f ||
        std::abs(scale) > max_surface_uv_transform ||
        !std::isfinite(offset) || std::abs(offset) > max_surface_uv_transform ||
        !std::isfinite(low) || !std::isfinite(high) || low < 0 || high > 1 ||
        !(high - low > 1.f / dimension) || address < surface_address_wrap ||
        address > surface_address_clamp)
      throw std::runtime_error("POM chart/address has no filter-safe height interval");
  }
  if (!scene.world_eye_valid ||
      !std::all_of(scene.world_eye.begin(), scene.world_eye.end(),
                   [](float value) { return std::isfinite(value); }))
    throw std::runtime_error("POM requires the owned world-space scene eye");
}
HeightImageKey height_key(const mw34::materials::HeightBinding &binding) const {
  const auto &image = *binding.image;
  return {binding.image, &image, binding.source_sha256, binding.sidecar_sha256, image.name,
          binding.mesh_uv_hash, binding.image_version, binding.producer_epoch,
          binding.texture_version, image.hash, image.width, image.height, image.role};
}
void retire_height_images() {
  for (auto it = height_images.begin(); it != height_images.end();) {
    if (!it->first.owner.expired()) {
      ++it;
      continue;
    }
    destroy(it->second.texture);
    height_resident_bytes -= it->second.bytes;
    it = height_images.erase(it);
    ++height_retired_images;
  }
}
void height_uniform(const Scene &scene, const Draw &draw, mw34::sun::Uniform &uniform) const {
  // A freshly constructed uniform clears every field for Off/excluded draws.
  uniform.pom_params[3] = float(scene.pom_diagnostic_mode);
  if (!height_enabled(scene, draw)) return;
  const auto &material = draw.height_binding->material;
  uniform.pom_params = {1, material.height_reference, material.height_amplitude,
                        float(scene.pom_diagnostic_mode)};
  uniform.pom_uv = {material.uv_scale[0], material.uv_scale[1], material.uv_offset[0],
                    material.uv_offset[1]};
  uniform.pom_atlas = material.atlas_rect;
  uniform.pom_policy = {material.address_mode_u, material.address_mode_v, 8, 32};
  uniform.surface_eye = {scene.world_eye[0], scene.world_eye[1], scene.world_eye[2], 1};
}
std::vector<HeightImage *> prepare_height_images(const Scene &scene,
                                                const std::vector<Tex *> &bound,
                                                std::vector<HeightUpload> &pending) {
  std::vector<HeightImage *> result(scene.draws.size());
  VkDeviceSize bytes{};
  // Validate every active binding before allocating any height image. Off has
  // no height allocation/upload; A==0 also skips payloads, including UV capture.
  for (const auto &draw : scene.draws)
    if (height_enabled(scene, draw)) validate_height(scene, draw, bound);
  for (std::size_t at = 0; at < scene.draws.size(); ++at) {
    const auto &draw = scene.draws[at];
    if (!height_enabled(scene, draw) || draw.height_binding->material.height_amplitude == 0)
      continue;
    const auto key = height_key(*draw.height_binding);
    auto found = height_images.find(key);
    if (found == height_images.end()) {
      const auto &source = *draw.height_binding->image;
      const auto size = std::uint64_t(source.width) * source.height * 4;
      if (size > mw34::materials::max_surface_sidecar_bytes ||
          height_resident_bytes > mw34::materials::max_surface_sidecar_bytes - size)
        throw std::runtime_error("POM resident GPU height cache exceeds its byte bound");
      if (mw34::materials::normal_hash(source.pixels.data(), std::size_t(size)) != source.hash)
        throw std::runtime_error("POM immutable height image hash mismatch");
      found = height_images.emplace(key, HeightImage{}).first;
      auto &cached = found->second;
      cached.bytes = size;
      // Intentionally one mip and no AF: ordinary color/normal mip/sampler
      // behavior stays unchanged and atlas filtering has a bounded footprint.
      try {
        image(cached.texture.image, cached.texture.memory, cached.texture.view,
              source.width, source.height, VK_FORMAT_R8G8B8A8_UNORM,
              VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
              VK_IMAGE_ASPECT_COLOR_BIT);
      } catch (...) {
        destroy(cached.texture);
        height_images.erase(found);
        throw;
      }
      cached.texture.width = source.width;
      cached.texture.height = source.height;
      cached.texture.hash = source.hash;
      height_resident_bytes += size;
    }
    auto &cached = found->second;
    result[at] = &cached;
    if (!cached.texture.valid &&
        std::none_of(pending.begin(), pending.end(),
                      [&](const HeightUpload &upload) { return upload.cached == &cached; })) {
      pending.push_back({&cached, draw.height_binding->image.get()});
      bytes += cached.bytes;
    } else if (cached.texture.valid) {
      ++height_cache_hits;
    }
  }
  if (!pending.empty()) {
    ensure(height_upload, bytes, VK_BUFFER_USAGE_TRANSFER_SRC_BIT);
    auto *destination = static_cast<unsigned char *>(height_upload.mapped);
    for (const auto &upload : pending) {
      std::memcpy(destination, upload.source->pixels.data(), std::size_t(upload.cached->bytes));
      destination += upload.cached->bytes;
    }
  }
  return result;
}
void record_height_uploads(const std::vector<HeightUpload> &pending) {
  VkDeviceSize offset{};
  for (const auto &upload : pending) {
    auto &texture = upload.cached->texture;
    barrier(texture.image, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
            0, VK_ACCESS_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
            VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
    copyIn(height_upload.buffer, offset, texture.image, texture.width, texture.height,
            VK_IMAGE_ASPECT_COLOR_BIT);
    barrier(texture.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
            VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VK_ACCESS_TRANSFER_WRITE_BIT,
            VK_ACCESS_SHADER_READ_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT,
            VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
    offset += upload.cached->bytes;
  }
}
