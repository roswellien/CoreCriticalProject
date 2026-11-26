// surface_normals_stage.inc
// Full-content material matching for original textured geometry on any map.

struct RegionSurfaceMaterialCatalog {
  std::string path;
  std::string sha256;
  std::uint64_t bytes{};
  std::shared_ptr<const mw34::materials::SurfaceMaterialPack> pack;
  std::map<std::string, std::size_t> by_material_name;
};

struct RegionHeightCacheKey {
  std::string region;
  std::uint64_t source_epoch{};
  std::uint64_t group_epoch{};
  int texture{-1};
  std::uint64_t texture_version{};
  mw34::materials::SurfaceKey albedo{};
  int normal_index{-1};
  bool operator<(const RegionHeightCacheKey &other) const {
    return std::tie(region, source_epoch, group_epoch, texture, texture_version,
                    albedo, normal_index) <
           std::tie(other.region, other.source_epoch, other.group_epoch,
                    other.texture, other.texture_version, other.albedo,
                    other.normal_index);
  }
};

struct SurfaceNormalState {
  bool loaded{false};
  bool preload_pending{false};
  std::uint64_t peak_decoded_bytes{};
  mw34::materials::WorldNormalCache cache{};
  std::string native_material_bytes;
  std::uint64_t expected_mesh_uv_hash{};
  std::uint32_t expected_polygon_count{};
  mw34::detail::Bindings detail_bindings;
  std::shared_ptr<mw34::materials::SurfaceMaterialPack> native_material_pack;
  std::map<std::string, RegionSurfaceMaterialCatalog> region_surface_materials;
  std::map<RegionHeightCacheKey,
           std::shared_ptr<const mw34::materials::HeightBinding>>
      region_height_cache;
  std::set<std::pair<std::uint64_t, std::uint64_t>> traced_native;
  std::set<std::tuple<std::uintptr_t, std::uintptr_t, std::uint64_t>>
      traced_sources;
} surface_normals_;

struct NativeBindingContext {
  const zcls::Node *node{};
  const zmod::Model *model{};
  ::platform::MaterialDrawContext material{};
  std::uint64_t epoch{};
  bool height_eligible{};
  bool material_active{};
  bool fingerprint_computed{};
  std::optional<std::uint64_t> fingerprint;
  // Borrowed source scope ends at end_model_draw; deferred fixture receipts
  // retain only the completed values, never these native pointers.
  ::platform::prepared::Matrix fixture_world{};
  bool fixture_eligible{};
} native_context_;
std::uint64_t binding_rejected_mismatch_{};
std::uint64_t native_fingerprint_evaluations_{};
struct NativeDeferredBinding final : ::platform::DeferredMaterialBinding {
  std::weak_ptr<const int> owner;
  mw34::materials::SurfaceKey key{};
  std::uint64_t epoch{}, version{};
  int texture{-1}, normal_index{-1};
  std::array<float, 4> surface_parameters{};
  std::shared_ptr<const mw34::materials::HeightBinding> height_binding;
  std::shared_ptr<const mw34::native_fixtures::Observation> fixture;
};
const std::shared_ptr<const int> material_binding_owner_ =
    std::make_shared<const int>(0);
std::shared_ptr<const ::platform::DeferredMaterialBinding>
    deferred_material_binding_;

bool reject_surface_binding(const char *reason) {
  ++binding_rejected_mismatch_;
  if (binding_rejected_mismatch_ <= 8)
    std::fprintf(stderr, "[SURFACE_BINDING_REJECT] epoch=%llu reason=%s\n",
                 (unsigned long long)group_load_epoch_, reason);
  return false;
}

#include "world_normals_pages.inc"

bool surface_normals_enabled() const { return lighting_.normals; }

mw34::detail::Settings surface_detail_settings() const {
  mw34::detail::Settings settings;
  settings.water = bridge_config_.water_detail;
  settings.clouds = bridge_config_.cloud_detail;
  return settings;
}

void surface_normals_load() {
  if (surface_normals_.loaded) {
    return;
  }
  // Transactional build: fill a local cache first and publish only on success,
  // so an exception leaves no partial entries behind for a subsequent attempt.
  mw34::materials::WorldNormalCache cache{};
  mw34::detail::Bindings detail_bindings;
  std::vector<std::string> authored_paths;
  if (!bridge_config_.surface_normal_catalog.empty())
    authored_paths.push_back(bridge_config_.surface_normal_catalog);
  authored_paths.insert(authored_paths.end(),
                        bridge_config_.environment_authored_manifests.begin(),
                        bridge_config_.environment_authored_manifests.end());
  std::uint64_t authored_total{};
  for (const auto &authored_path : authored_paths) {
    const auto prior_owners = cache.authored;
    for (const auto &cat_path : mw34::materials::surface_normal_catalog_paths(
             std::filesystem::u8path(authored_path))) {
      const auto bytes = std::filesystem::file_size(cat_path);
      if (bytes > mw34::materials::authored_normal_budget - authored_total)
        throw std::runtime_error(
            "Combined authored normal catalogs exceed byte budget");
      authored_total += bytes;
      std::ifstream file(cat_path, std::ios::binary);
      if (!file) {
        throw std::runtime_error("Configured surface normal page is missing");
      }
      auto parsed = mw34::materials::read_surface_normals(file);
      const std::size_t base_idx = cache.textures.size();
      for (const auto &[key, idx] : parsed.bindings) {
        // Explicit catalog first, then deterministic region ownership order.
        if (prior_owners.count(key))
          continue;
        if (idx == mw34::materials::no_normal) {
          // Explicit no_normal precedence over any world binding.
          cache.register_authored(key, -1);
        } else {
          const std::uint64_t absolute = static_cast<std::uint64_t>(base_idx) +
                                         static_cast<std::uint64_t>(idx);
          if (absolute >
              std::uint64_t(
                  std::numeric_limits<int>::max())) { // overflow check before
                                                      // int conversion
            throw std::runtime_error("Surface normal texture index overflow");
          }
          cache.register_authored(key, static_cast<int>(absolute));
        }
      }
      for (auto &img : parsed.pack.images) {
        mw34::materials::WorldNormalCache::TextureRecord rec{};
        rec.name = std::move(img.name);
        rec.width = img.width;
        rec.height = img.height;
        rec.hash = img.hash;
        rec.pixels32 = std::move(img.pixels);
        cache.textures.push_back(std::move(rec));
      }
    }
  }
  surface_normals_load_world(cache);
  auto load_detail_role = [&](::platform::prepared::EnvironmentRole source_role,
                              unsigned detail_role, bool active) {
    if (!active)
      return;
    std::string path;
    if (environment_) {
      for (const auto &[region, resources] : environment_->resources) {
        const auto found = resources.find(source_role);
        if (found != resources.end()) {
          path = found->second;
          break;
        }
      }
    }
    if (path.empty())
      throw std::runtime_error("Enabled surface detail has no admitted role catalog");
    const auto digest = environment_->detail_digests.find(source_role);
    if (digest == environment_->detail_digests.end() ||
        ::platform::integrity::sha256_file(std::filesystem::u8path(path)) !=
            digest->second)
      throw std::runtime_error(
          "Surface detail catalog changed after environment admission");
    const auto size = std::filesystem::file_size(std::filesystem::u8path(path));
    if (size < 12 || size > 16ULL * 1024 * 1024)
      throw std::runtime_error("Surface detail catalog size is outside its limit");
    std::ifstream input(std::filesystem::u8path(path), std::ios::binary);
    if (!input)
      throw std::runtime_error("Admitted surface detail catalog cannot be opened");
    auto parsed = mw34::materials::read_surface_normals(input);
    const auto texture_base = cache.textures.size();
    mw34::detail::register_catalog(detail_bindings, parsed, detail_role,
                                   texture_base);
    for (auto &image : parsed.pack.images) {
      mw34::materials::WorldNormalCache::TextureRecord record{};
      record.name = std::move(image.name);
      record.width = image.width;
      record.height = image.height;
      record.hash = image.hash;
      record.pixels32 = std::move(image.pixels);
      cache.textures.push_back(std::move(record));
    }
  };
  load_detail_role(::platform::prepared::EnvironmentRole::water, 1,
                   bridge_config_.water_detail);
  load_detail_role(::platform::prepared::EnvironmentRole::surf, 2,
                   bridge_config_.water_detail);
  load_detail_role(::platform::prepared::EnvironmentRole::cloud, 3,
                   bridge_config_.cloud_detail);
  std::string native_bytes;
  std::uint64_t expected_hash{};
  std::uint32_t expected_polygons{};
  if (!bridge_config_.native_material_sidecar.empty()) {
    if (geometry_mode_ != cc::geometry::Mode::legacy)
      throw std::runtime_error(
          "Native UV-qualified materials require the legacy geometry route");
    if (!mw34::materials::valid_surface_identifier(
            bridge_config_.native_material_asset_id,
            mw34::materials::max_surface_identifier_bytes, true))
      throw std::runtime_error(
          "Native material sidecar requires an explicit valid asset ID");
    const auto &path = bridge_config_.native_material_sidecar;
    const auto size = std::filesystem::file_size(path);
    if (size < 32 || size > mw34::materials::max_surface_sidecar_bytes)
      throw std::runtime_error("Native material sidecar size is invalid");
    std::ifstream input(path, std::ios::binary);
    native_bytes.resize(std::size_t(size));
    if (!input.read(native_bytes.data(), std::streamsize(size)) ||
        input.peek() != std::char_traits<char>::eof())
      throw std::runtime_error(
          "Native material sidecar changed during admission");
    std::uint32_t version{};
    std::memcpy(&version, native_bytes.data() + 8, 4);
    std::memcpy(&expected_polygons, native_bytes.data() + 12, 4);
    std::memcpy(&expected_hash, native_bytes.data() + 24, 8);
    if (std::memcmp(native_bytes.data(), "BWSFM1\0\0", 8) ||
        (version != 1 && version != 2) ||
        !expected_polygons || expected_polygons > 4096)
      throw std::runtime_error("Native material sidecar header is invalid");
  }
  surface_normals_.native_material_bytes = std::move(native_bytes);
  surface_normals_.expected_mesh_uv_hash = expected_hash;
  surface_normals_.expected_polygon_count = expected_polygons;
  surface_normals_.cache = std::move(cache);
  surface_normals_.detail_bindings = std::move(detail_bindings);
  surface_normals_.region_surface_materials.clear();
  surface_normals_.region_height_cache.clear();
  surface_normals_.loaded = true;
}

const RegionSurfaceMaterialCatalog *
ensure_region_surface_materials(const std::string &region) {
  if (!bridge_config_.parallax_materials || !lighting_.normals || !environment_)
    return nullptr;
  const auto existing = surface_normals_.region_surface_materials.find(region);
  if (existing != surface_normals_.region_surface_materials.end())
    return &existing->second;
  const auto res_it = environment_->resources.find(region);
  if (res_it == environment_->resources.end())
    return nullptr;
  auto found = res_it->second.find(::platform::prepared::EnvironmentRole::surface_materials);
  if (found == res_it->second.end())
    found = res_it->second.find(::platform::prepared::EnvironmentRole::ground_materials);
  if (found == res_it->second.end())
    return nullptr;
  const auto digest_it = environment_->surface_material_digests.find(region);
  if (digest_it == environment_->surface_material_digests.end())
    throw std::runtime_error(
        "Environment surface-material catalog has no admitted manifest digest");
  const auto sidecar_path = std::filesystem::u8path(found->second);
  const auto size = std::filesystem::file_size(sidecar_path);
  if (size < 32 || size > mw34::materials::max_surface_sidecar_bytes)
    throw std::runtime_error("Environment surface-material sidecar size is invalid");
  std::ifstream input(sidecar_path, std::ios::binary);
  if (!input)
    throw std::runtime_error("Environment surface-material sidecar cannot be opened");
  std::string raw(static_cast<std::size_t>(size), '\0');
  if (!input.read(raw.data(), static_cast<std::streamsize>(size)) ||
      input.peek() != std::char_traits<char>::eof())
    throw std::runtime_error("Environment surface-material sidecar changed during load");
  ::platform::integrity::Sha256 sha;
  sha.update(raw.data(), raw.size());
  const auto actual_digest = sha.hex();
  if (actual_digest != digest_it->second)
    throw std::runtime_error(
        "Environment surface-material sidecar changed after environment admission");
  // Keep only the active region's catalog decoded to stay within the shared
  // 256 MiB SurfaceDecodedBudget across multi-region campaign packs.
  surface_normals_.region_surface_materials.clear();
  surface_normals_.region_height_cache.clear();
  std::istringstream stream(raw, std::ios::binary);
  auto parsed = mw34::materials::read_surface_material_catalog(
      stream, region, mw34::materials::max_surface_sidecar_bytes,
      mw34::materials::max_surface_sidecar_bytes, prepared_.surface_budget());
  RegionSurfaceMaterialCatalog catalog;
  catalog.path = found->second;
  catalog.sha256 = actual_digest;
  catalog.bytes = size;
  catalog.pack = std::make_shared<mw34::materials::SurfaceMaterialPack>(std::move(parsed));
  for (std::size_t idx = 0; idx < catalog.pack->records.size(); ++idx) {
    const auto &rec = *catalog.pack->records[idx];
    if (rec.height_image != mw34::materials::no_surface_image &&
        rec.height_amplitude != 0.0f) {
      catalog.by_material_name.emplace(rec.material_name, idx);
    }
  }
  std::fprintf(stderr,
               "[POM] Region surface materials loaded: region=%s records=%zu height_materials=%zu images=%zu\n",
               region.c_str(), catalog.pack->records.size(),
               catalog.by_material_name.size(), catalog.pack->images.size());
  return &surface_normals_.region_surface_materials.emplace(region, std::move(catalog)).first->second;
}

// BWSNR catalogs authenticate texel identity. BWSFM1 separately supplies the
// authored mesh/UV compatibility expectation; a first observed UV is not used
// as a substitute for that expectation.
bool native_surface_binding_matches(const mw34::materials::SurfaceKey &key,
                                    int texture_handle) {
  const bool strict = !bridge_config_.native_material_sidecar.empty();
  if (!strict && !bridge_config_.trace_native_bindings)
    return true;
  VisualFloatScope preserve;
  const auto &context = native_context_;
  if (!context.node || !context.model || !context.material_active ||
      context.epoch != group_load_epoch_ ||
      context.node->model != context.model ||
      context.material.model != context.model ||
      context.material.polygon >= context.model->count(0x10) ||
      !context.model->polygons)
    return strict
               ? reject_surface_binding("missing/stale native producer scope")
               : true;
  const auto &polygon = context.model->polygons[context.material.polygon];
  const auto *material = polygon.material;
  if (!material || context.material.material != material ||
      !material->texture ||
      context.material.texture_entry != material->texture ||
      !material->texture->surface)
    return strict ? reject_surface_binding(
                        "material/texture object identity mismatch")
                  : true;
  const auto &source_texture =
      *static_cast<const zvid::D3DTexture *>(material->texture->surface);
  if (source_texture.handle != texture_handle || texture_handle < 0 ||
      std::size_t(texture_handle) >= textures_.size())
    return strict ? reject_surface_binding(
                        "texture handle no longer belongs to material")
                  : true;
  const auto &source = textures_[std::size_t(texture_handle)];
  if (source.group_load_epoch != context.epoch || source.surface_key < key ||
      key < source.surface_key)
    return strict ? reject_surface_binding("surface content/epoch mismatch")
                  : true;
  // Inventory tracing is bounded and never supplies an expected compatibility
  // hash to the guard. Strict qualification always recomputes live source data.
  if (!strict && bridge_config_.trace_native_bindings) {
    if (surface_normals_.traced_sources.size() >= 512 ||
        !surface_normals_.traced_sources
             .emplace(reinterpret_cast<std::uintptr_t>(context.model),
                      reinterpret_cast<std::uintptr_t>(material), key.hash)
             .second)
      return true;
  }
  if (!native_context_.fingerprint_computed) {
    native_context_.fingerprint = native_mesh_uv_hash(*context.model);
    native_context_.fingerprint_computed = true;
    ++native_fingerprint_evaluations_;
  }
  const auto fingerprint = native_context_.fingerprint;
  if (!fingerprint)
    return strict ? reject_surface_binding(
                        "unsupported native source mesh/UV stream")
                  : true;
  if (bridge_config_.trace_native_bindings &&
      surface_normals_.traced_native.size() < 512 &&
      surface_normals_.traced_native.emplace(*fingerprint, key.hash).second)
    std::fprintf(
        stderr,
        "[NATIVE_SURFACE_IDENTITY] node=%.32s texture=%.20s polygon=%u "
        "polygons=%u mesh_uv_hash=0x%llx "
        "surface={%u,%u,%u,0x%llx} epoch=%llu uv_metadata=%s\n",
        context.node->name(), material->texture->name, context.material.polygon,
        context.model->count(0x10), (unsigned long long)*fingerprint, key.width,
        key.height, key.format, (unsigned long long)key.hash,
        (unsigned long long)context.epoch, strict ? "selected" : "absent");
  if (!strict)
    return true;
  // [WP02B R10: bypass only this live source/metadata UV equality guard.]
  if (*fingerprint != surface_normals_.expected_mesh_uv_hash)
    return reject_surface_binding(
        "authored mesh_uv_hash does not match live source");
  if (context.model->count(0x10) != surface_normals_.expected_polygon_count)
    return reject_surface_binding("authored native polygon count mismatch");
  if (!surface_normals_.native_material_pack) {
    std::vector<std::string> names;
    for (std::uint32_t i = 0; i < context.model->count(0x10); ++i) {
      const auto *candidate = context.model->polygons[i].material;
      if (!candidate)
        return reject_surface_binding("native material is missing");
      if (!(candidate->flags & 1)) {
        names.emplace_back("untextured");
        continue;
      }
      if (!candidate->texture || !std::memchr(candidate->texture->name, 0, 20))
        return reject_surface_binding(
            "native texture identity name is invalid");
      names.emplace_back(candidate->texture->name);
    }
    try {
      std::istringstream input(surface_normals_.native_material_bytes,
                               std::ios::binary);
      auto pack = mw34::materials::read_surface_materials(
          input, bridge_config_.native_material_asset_id,
          surface_normals_.expected_mesh_uv_hash, names,
          mw34::materials::max_surface_sidecar_bytes,
          mw34::materials::max_surface_sidecar_bytes, prepared_.surface_budget());
      surface_normals_.native_material_pack =
          std::make_shared<mw34::materials::SurfaceMaterialPack>(
              std::move(pack));
    } catch (const std::runtime_error &error) {
      return reject_surface_binding(error.what());
    }
  }
  const auto &pack = *surface_normals_.native_material_pack;
  const auto record = pack.bindings.at(context.material.polygon);
  if (record == mw34::materials::no_surface_material)
    return true; // Global UV expectation still applies; absence of extra
                 // material parameters is not the normal catalog's no_normal
                 // exclusion.
  if (!std::memchr(material->texture->name, 0, 20) ||
      pack.records.at(record)->material_name != material->texture->name)
    return reject_surface_binding(
        "authored material name no longer matches source");
  return true;
}

std::array<float, 4>
native_surface_parameters(const mw34::materials::SurfaceKey &key, int texture) {
  if (!lighting_.normals || bridge_config_.native_material_sidecar.empty())
    return {};
  surface_normals_load();
  if (!native_surface_binding_matches(key, texture))
    return {};
  const auto &pack = *surface_normals_.native_material_pack;
  const auto index = pack.bindings.at(native_context_.material.polygon);
  if (index == mw34::materials::no_surface_material)
    return {};
  const auto &record = *pack.records.at(index);
  return {record.roughness, record.reflectivity, record.metallic, 1.f};
}

std::shared_ptr<const mw34::materials::HeightBinding>
native_height_binding(const mw34::materials::SurfaceKey &key, int texture) {
  VisualFloatScope preserve;
  if (!bridge_config_.parallax_materials || !lighting_.normals ||
      !native_context_.height_eligible || geometry_debug_)
    return {};
  if (native_context_.material_active && native_context_.model &&
      native_context_.model->polygons &&
      native_context_.material.polygon < native_context_.model->count(0x10)) {
    const auto *material = native_context_.model->polygons[native_context_.material.polygon].material;
    if (material && !native_ground_material_eligible(*material))
      return {};
  }
  if (environment_ && !current_mission_id_.empty()) {
    const auto region = ::platform::prepared::environment_region(current_mission_id_);
    const auto selected = environment_->material_targets.find(region);
    if (selected != environment_->material_targets.end()) {
      const auto *target = select_native_ground_target(
          selected->second, native_context_.node, native_context_.model);
      if (target) {
        NativeGroundHeightInput input;
        input.enabled = true;
        input.eligible = true;
        input.node = native_context_.node;
        input.model = native_context_.model;
        input.material = native_context_.material;
        if (!native_context_.material_active)
          input.material = {};
        input.key = key;
        input.texture = texture;
        input.source_epoch = zcls::world_source_epoch();
        input.producer_epoch = native_context_.epoch;
        input.current_group_epoch = group_load_epoch_;
        if (texture >= 0 && std::size_t(texture) < textures_.size()) {
          const auto &slot = textures_[texture];
          input.slot_key = slot.surface_key;
          input.slot_epoch = slot.group_load_epoch;
          input.texture_version = input.current_texture_version = slot.version;
          input.normal_index = surface_normal_index(key, true, texture);
          if (input.normal_index >= 0) {
            const auto &normal = surface_normals_.cache.normal_record(input.normal_index);
            input.normal_width = normal.width;
            input.normal_height = normal.height;
            input.normal_hash = normal.hash;
          }
        }
        try {
          return admit_native_ground_height(*target, input, prepared_.surface_budget());
        } catch (const std::runtime_error &error) {
          reject_surface_binding(error.what());
          throw;
        }
      }
    }
    // Fall back to the region's admitted BWSFM1 surface-material catalog, bound
    // through the authenticated SurfaceKey -> BWSNR normal image hash/name.
    surface_normals_load();
    const auto *catalog = ensure_region_surface_materials(region);
    if (catalog && texture >= 0 && std::size_t(texture) < textures_.size() &&
        key.width > 0 && key.height > 0 && key.format == 1U && key.hash != 0) {
      const auto &slot = textures_[std::size_t(texture)];
      if (!slot.replacement && slot.width == key.width && slot.height == key.height &&
          slot.group_load_epoch == group_load_epoch_ && slot.surface_key == key) {
        const int normal_idx = surface_normal_index(key, true, texture);
        if (normal_idx >= 0) {
          const auto source_epoch = zcls::world_source_epoch();
          RegionHeightCacheKey cache_key{
              region, source_epoch, group_load_epoch_, texture, slot.version, key, normal_idx};
          auto cached = surface_normals_.region_height_cache.find(cache_key);
          if (cached != surface_normals_.region_height_cache.end())
            return cached->second;
          const auto &normal = surface_normal_image(normal_idx);
          std::shared_ptr<const mw34::materials::HeightBinding> resolved;
          auto rec_it = catalog->by_material_name.end();
          if (normal.hash != 0) {
            char hash_name[24];
            std::snprintf(hash_name, sizeof(hash_name), "n_%016llx",
                          static_cast<unsigned long long>(normal.hash));
            rec_it = catalog->by_material_name.find(hash_name);
          }
          if (rec_it == catalog->by_material_name.end())
            rec_it = catalog->by_material_name.find(normal.name);
          if (rec_it != catalog->by_material_name.end()) {
            auto binding = mw34::materials::resolve_catalog_height_binding(
                catalog->pack, rec_it->second, catalog->sha256, key,
                normal.width, normal.height, normal.hash);
            if (binding) {
              auto owned = std::make_shared<mw34::materials::HeightBinding>(*binding);
              owned->sidecar_path = catalog->path;
              owned->producer_epoch = group_load_epoch_;
              owned->texture_version = slot.version;
              owned->world_source = mw34::materials::HeightWorldSource{
                  "env-surface-bwsfm1", catalog->path, catalog->bytes, source_epoch, 0};
              resolved = std::move(owned);
            }
          }
          if (surface_normals_.region_height_cache.size() >= 4096)
            surface_normals_.region_height_cache.clear();
          surface_normals_.region_height_cache.emplace(std::move(cache_key), resolved);
          return resolved;
        }
      }
    }
  }
  // Diagnostic sidecar bytes never supply a source-aware environment target.
  return {};
}

void preload_surface_normal(const mw34::materials::SurfaceKey &key) {
  if (!surface_normals_enabled() || !key.hash) {
    return;
  }
  surface_normals_load();
  // Only mark the mission preload pending here. Decoding each texture's world
  // page as the texture arrives read pages in arrival order, and once a
  // mission's pages outgrew the resident limit that re-read the same pages
  // many times (issue 461: 806 page reads for c1m1's 52 pages). The post-load
  // mission preload reads each page once, grouped, before the first visible
  // turn, so the first turn still doesn't stall on disk reads.
  surface_normals_.preload_pending = true;
}

int surface_normal_index(const mw34::materials::SurfaceKey &input_key,
                         bool enabled = true, int texture_handle = -1) {
  if (!enabled || !surface_normals_enabled()) {
    return -1;
  }
  surface_normals_load();
  mw34::materials::SurfaceKey key = input_key;
  // [R10 / V2-02 FAULT INJECTION TARGET: key.hash ^= 1ULL;]
  const auto &cache = surface_normals_.cache;
  const auto authored = cache.bindings.find(key);
  if (authored != cache.bindings.end() && authored->second < 0)
    return -1;
  const bool candidate =
      cache.bindings.count(key) || cache.world_bindings.count(key);
  if (bridge_config_.trace_native_bindings && !candidate &&
      bridge_config_.native_material_sidecar.empty())
    native_surface_binding_matches(key, texture_handle);
  if (candidate && !native_surface_binding_matches(key, texture_handle))
    return -1;
  mw34::timing::ScopedDuration decode_timer(
      producer_resource_timing_.page_decode_target());
  // Draws need only the index; the GPU copy is uploaded once per index by
  // surface_normal_texture(), so an evicted page must not be read again here.
  const int index = surface_normals_.cache.resident_normal_index(key, enabled);
  surface_normals_.peak_decoded_bytes = std::max(
      surface_normals_.peak_decoded_bytes, surface_normals_.cache.world_bytes);
  return index;
}

const mw34::materials::WorldNormalCache::TextureRecord &
surface_normal_image(int index) {
  mw34::timing::ScopedDuration decode_timer(
      producer_resource_timing_.page_decode_target());
  surface_normals_.cache.require_image(index);
  surface_normals_.peak_decoded_bytes = std::max(
      surface_normals_.peak_decoded_bytes, surface_normals_.cache.world_bytes);
  return surface_normals_.cache.textures.at(static_cast<std::size_t>(index));
}

std::uint64_t resident_normal_decoded_bytes() const {
  return surface_normals_.cache.world_bytes;
}

const NativeDeferredBinding *
validated_deferred_binding(const mw34::materials::SurfaceKey &key, int texture,
                            bool require_height = false) {
  const auto *binding = dynamic_cast<const NativeDeferredBinding *>(
      deferred_material_binding_.get());
  if (!binding || binding->owner.lock() != material_binding_owner_ ||
      binding->epoch != group_load_epoch_ || binding->texture != texture ||
      texture < 0 || std::size_t(texture) >= textures_.size() ||
      binding->version != textures_[texture].version ||
      textures_[texture].group_load_epoch != group_load_epoch_ || binding->key < key ||
      key < binding->key) {
    reject_surface_binding("stale or foreign deferred material admission");
    if (require_height && binding && binding->height_binding &&
        bridge_config_.parallax_materials && lighting_.normals)
      throw std::runtime_error("Deferred native ground texture admission is stale or foreign");
    return nullptr;
  }
  if (require_height && binding->height_binding && bridge_config_.parallax_materials && lighting_.normals &&
      !mw34::materials::height_binding_stamps_match(
          *binding->height_binding, zcls::world_source_epoch(), binding->epoch,
          binding->version, key)) {
    reject_surface_binding("deferred height source/image snapshot mismatch");
    throw std::runtime_error("Deferred native ground height admission is stale");
  }
  if (require_height && binding->height_binding && bridge_config_.parallax_materials && lighting_.normals) {
    if (binding->normal_index < 0)
      throw std::runtime_error("Deferred native ground normal identity is missing");
    const auto &normal = surface_normals_.cache.normal_record(binding->normal_index);
    const auto &height = *binding->height_binding;
    if (normal.width != height.normal_width || normal.height != height.normal_height ||
        normal.hash != height.normal_hash)
      throw std::runtime_error("Deferred native ground normal identity changed");
  }
  return binding;
}

int deferred_surface_normal_index(const mw34::materials::SurfaceKey &key,
                                  int texture) {
  if (!deferred_material_binding_)
    return surface_normal_index(key, true, texture);
  const auto *binding = validated_deferred_binding(key, texture);
  return binding ? binding->normal_index : -1;
}

std::array<float, 4>
deferred_surface_parameters(const mw34::materials::SurfaceKey &key, int texture) {
  if (!deferred_material_binding_)
    return native_surface_parameters(key, texture);
  const auto *binding = validated_deferred_binding(key, texture);
  return binding ? binding->surface_parameters : std::array<float, 4>{};
}

std::shared_ptr<const mw34::materials::HeightBinding>
deferred_height_binding(const mw34::materials::SurfaceKey &key, int texture) {
  if (!bridge_config_.parallax_materials || !lighting_.normals)
    return {};
  if (!deferred_material_binding_)
    return native_height_binding(key, texture);
  const auto *binding = validated_deferred_binding(key, texture, true);
  return binding ? binding->height_binding : nullptr;
}

bool authenticated_deferred_world_draw() const {
  const auto *binding = dynamic_cast<const NativeDeferredBinding *>(
      deferred_material_binding_.get());
  return binding && (binding->normal_index >= 0 || binding->fixture ||
                     binding->surface_parameters[3] > .5f) &&
         binding->owner.lock() == material_binding_owner_ &&
         binding->epoch == group_load_epoch_ && binding->texture >= 0 &&
         std::size_t(binding->texture) < textures_.size() &&
         binding->version == textures_[binding->texture].version &&
         !(binding->key < textures_[binding->texture].surface_key) &&
         !(textures_[binding->texture].surface_key < binding->key);
}

std::vector<NativeGroundRangeAdmission> native_geometry_admissions(
    const std::shared_ptr<const cc::geometry::Resource> &resource,
    const ::platform::ModelDrawContext &context,
    const std::vector<cc::geometry::Material> &materials) {
  VisualFloatScope preserve;
  // This scope is synchronous even when submit_model_geometry precedes the
  // normal begin_model_draw callback. Restore the caller's existing scope.
  struct Restore {
    NativeBindingContext &destination;
    NativeBindingContext saved;
    ~Restore() { destination = std::move(saved); }
  } restore{native_context_, native_context_};
  native_context_ = {};
  native_context_.node = static_cast<const zcls::Node *>(context.node);
  native_context_.model = native_context_.node ? native_context_.node->model : nullptr;
  native_context_.epoch = group_load_epoch_;
  native_context_.height_eligible = native_ground_eligible(context) && !geometry_debug_;
  const auto *model = native_context_.model;
  const ::platform::prepared::MaterialTarget *target{};
  if (bridge_config_.parallax_materials && lighting_.normals &&
      native_context_.height_eligible && environment_ && !current_mission_id_.empty()) {
    const auto region = ::platform::prepared::environment_region(current_mission_id_);
    const auto selected = environment_->material_targets.find(region);
    if (selected != environment_->material_targets.end())
      target = select_native_ground_target(selected->second, native_context_.node, model);
  }
  if (target && (!model || model->render_geometry != resource ||
                 resource->source_vertices != model->count(0x14) ||
                 resource->source_polygons != model->count(0x10) ||
                 context.source_vertices != model->count(0x14) ||
                 context.source_polygons != model->count(0x10)))
    throw std::runtime_error("Selected native ground resource is not its live original model");
  return admit_native_ground_ranges(resource->ranges, resource->source_polygons,
      [&](std::size_t index, std::uint32_t polygon) {
        const auto &range = resource->ranges[index];
        const auto &material = materials[index];
        native_context_.height_eligible = native_ground_eligible(context) && !geometry_debug_ &&
                                          (material.color >> 24) == 255;
        native_context_.material = {};
        native_context_.material_active = false;
        if (model && model->polygons && polygon < model->count(0x10)) {
          const auto *original = model->polygons[polygon].material;
          if (target && (range.material_slot >= model->render_materials.size() ||
                         model->render_materials[range.material_slot] != original))
            throw std::runtime_error("Selected native ground original material-slot mismatch");
          native_context_.material = {model, original, original ? original->texture : nullptr,
                                      polygon};
          native_context_.material_active = true;
        } else if (target) {
          throw std::runtime_error("Selected native ground original polygon is missing");
        }
        NativeGroundRangeAdmission admission;
        if (material.texture < 0) {
          if (target)
            admission.height_binding = native_height_binding({}, material.texture);
          return admission;
        }
        const auto &slot = textures_.at(std::size_t(material.texture));
        admission.normal_index = surface_normal_index(slot.surface_key, true, material.texture);
        admission.surface_parameters = native_surface_parameters(slot.surface_key, material.texture);
        admission.height_binding = native_height_binding(slot.surface_key, material.texture);
        if (admission.height_binding) {
          const auto &record = admission.height_binding->material;
          admission.surface_parameters = {record.roughness, record.reflectivity, record.metallic, 1.f};
        }
        return admission;
      });
}

void apply_native_geometry_admission(vk::Draw &draw,
                                     const NativeGroundRangeAdmission &admission) {
  draw.height_binding = admission.height_binding;
  draw.surface_parameters = admission.surface_parameters;
  if (admission.normal_index >= 0) {
    const bool first_normal_handle =
        surface_normal_textures_.find(admission.normal_index) ==
        surface_normal_textures_.end();
    const int32_t normal_handle =
        surface_normal_texture(admission.normal_index);
    mw34::timing::ScopedDuration upload_timer(
        first_normal_handle ? producer_resource_timing_.page_upload_target()
                            : nullptr);
    draw.normal_texture = int(bind_texture(normal_handle, false));
  }
}

private:
friend struct testing::RigidCaptureTestAccess;

static void add_capture_bytes(std::size_t &used, std::size_t bytes, std::size_t limit) {
  if (bytes > limit || used > limit - bytes)
    throw std::runtime_error("Owned rigid capture exceeds maximum_owned_bytes budget");
  used += bytes;
}

std::shared_ptr<const CapturedNativeRigid> capture_original_rigid(
    const zcls::Node &node, const ::platform::ModelDrawContext &context,
    const zmod::RigidGeometryEligibility &eligibility, std::size_t maximum_owned_bytes) {
  VisualFloatScope preserve;
  struct Restore {
    NativeBindingContext &destination;
    NativeBindingContext saved;
    ~Restore() { destination = std::move(saved); }
  } restore{native_context_, native_context_};

  if (context.node != &node || !node.model)
    throw std::runtime_error("Owned rigid capture node/model scope is invalid");
  const zmod::Model &model = *node.model;
  const std::uint32_t vertex_count = model.count(0x14);
  const std::uint32_t polygon_count = model.count(0x10);
  if (!model.vertices || !model.polygons || !vertex_count || !polygon_count ||
      context.source_vertices != vertex_count || context.source_polygons != polygon_count)
    throw std::runtime_error("Owned rigid capture source counts do not match live model");

  const bool actual_ordinary = model.count(0) == 0;
  const bool actual_morphing = model.count(0x20) != 0;
  if (context.ordinary != actual_ordinary || context.morphing != actual_morphing ||
      context.overlay != eligibility.overlay || context.opacity != eligibility.opacity)
    throw std::runtime_error("Owned rigid capture context disagrees with model/eligibility");

  if (geometry_mode_ == cc::geometry::Mode::legacy)
    return {};
  if (prepared_.has_binding(context))
    return {};
  if (!native_ground_eligible(context) || eligibility.overlay || eligibility.second_pass ||
      eligibility.opacity != 1.f)
    return {};
  const zmod::RigidGeometryEligibility derived_eligibility{
      context.overlay || eligibility.overlay, eligibility.second_pass, context.opacity};
  if (!zmod::rigid_source_supported(model, derived_eligibility))
    return {};

  std::size_t owned_bytes = 0;
  add_capture_bytes(owned_bytes, zmod::preflight_rigid_source_bytes(model), maximum_owned_bytes);
  add_capture_bytes(owned_bytes, sizeof(CapturedNativeRigid), maximum_owned_bytes);
  if (polygon_count > std::numeric_limits<std::size_t>::max() / sizeof(CapturedNativeRigidRange))
    throw std::runtime_error("Owned rigid capture range table overflow");
  add_capture_bytes(owned_bytes, std::size_t(polygon_count) * sizeof(CapturedNativeRigidRange),
                    maximum_owned_bytes);

  const std::uint64_t sampled_world_epoch = zcls::world_source_epoch();
  const std::uint64_t sampled_group_epoch = group_load_epoch_;

  auto registered = zmod::register_rigid_source(model);
  if (!registered.resource || registered.resource->source_vertices != vertex_count ||
      registered.resource->source_polygons != polygon_count ||
      registered.resource->ranges.size() != polygon_count ||
      registered.original_materials.size() != polygon_count)
    throw std::runtime_error("Owned rigid capture registration cardinality mismatch");

  const auto copied_materials = zmod::copy_rigid_materials(model, *registered.resource);
  if (copied_materials.size() != polygon_count)
    throw std::runtime_error("Owned rigid capture material count mismatch");

  for (std::uint32_t i = 0; i < polygon_count; ++i) {
    const auto &range = registered.resource->ranges[i];
    const auto *original = model.polygons[i].material;
    if (!original || range.polygon != i || range.material_slot != i ||
        registered.original_materials[range.material_slot] != original)
      throw std::runtime_error("Owned rigid capture polygon/material-slot correspondence mismatch");
  }

  native_context_ = {};
  native_context_.node = &node;
  native_context_.model = &model;
  native_context_.epoch = sampled_group_epoch;
  native_context_.height_eligible = native_ground_eligible(context) && !geometry_debug_;

  const ::platform::prepared::MaterialTarget *target{};
  if (bridge_config_.parallax_materials && lighting_.normals &&
      native_context_.height_eligible && environment_ && !current_mission_id_.empty()) {
    const auto region = ::platform::prepared::environment_region(current_mission_id_);
    const auto selected = environment_->material_targets.find(region);
    if (selected != environment_->material_targets.end())
      target = select_native_ground_target(selected->second, &node, &model);
  }

  std::map<int, std::shared_ptr<const CapturedRgbaImage>> local_albedo_images;
  std::map<int, std::shared_ptr<const CapturedRgbaImage>> local_normal_images;
  std::set<std::shared_ptr<const mw34::materials::SurfaceMaterialImage>,
           std::owner_less<std::shared_ptr<const mw34::materials::SurfaceMaterialImage>>>
      charged_height_images;
  std::vector<CapturedNativeRigidRange> captured_ranges;
  captured_ranges.reserve(polygon_count);

  for (std::uint32_t i = 0; i < polygon_count; ++i) {
    const auto &range = registered.resource->ranges[i];
    const auto &material = copied_materials[i];
    const auto *original = model.polygons[i].material;
    if (!original || registered.original_materials[range.material_slot] != original)
      throw std::runtime_error("Owned rigid capture original material mutated during capture");

    native_context_.height_eligible =
        native_ground_eligible(context) && !geometry_debug_ && (material.color >> 24) == 255;
    native_context_.material = {&model, original, original->texture, i};
    native_context_.material_active = true;

    CapturedNativeRigidRange out_range{};
    out_range.polygon = range.polygon;
    out_range.material_slot = range.material_slot;
    out_range.material = material;

    if (material.texture < 0) {
      if (target)
        out_range.height_binding = native_height_binding({}, material.texture);
    } else {
      if (std::size_t(material.texture) >= textures_.size())
        throw std::runtime_error("Owned rigid capture references out-of-range texture slot");
      const auto &slot = textures_[std::size_t(material.texture)];
      if (!slot.width || !slot.height || slot.pixels.empty() ||
          slot.pixels.size() != std::uint64_t(slot.width) * slot.height ||
          slot.group_load_epoch != sampled_group_epoch)
        throw std::runtime_error("Owned rigid capture references released or invalid albedo slot");

      out_range.texture_handle = material.texture;
      out_range.albedo_key = slot.surface_key;
      out_range.texture_version = slot.version;
      out_range.texture_group_epoch = slot.group_load_epoch;

      out_range.normal_index = surface_normal_index(slot.surface_key, true, material.texture);
      out_range.surface_parameters = native_surface_parameters(slot.surface_key, material.texture);
      out_range.height_binding = native_height_binding(slot.surface_key, material.texture);
      if (out_range.height_binding) {
        const auto &record = out_range.height_binding->material;
        out_range.surface_parameters =
            {record.roughness, record.reflectivity, record.metallic, 1.f};
      }

      auto albedo_it = local_albedo_images.find(material.texture);
      if (albedo_it == local_albedo_images.end()) {
        const std::uint64_t pixel_count = std::uint64_t(slot.width) * slot.height;
        if (pixel_count > std::numeric_limits<std::size_t>::max() / sizeof(std::uint32_t))
          throw std::runtime_error("Owned rigid capture albedo byte count overflow");
        add_capture_bytes(owned_bytes, sizeof(CapturedRgbaImage), maximum_owned_bytes);
        add_capture_bytes(owned_bytes, std::size_t(pixel_count) * sizeof(std::uint32_t),
                          maximum_owned_bytes);
        auto img = std::make_shared<CapturedRgbaImage>();
        img->width = slot.width;
        img->height = slot.height;
        img->pixels32 = slot.pixels;
        albedo_it = local_albedo_images.emplace(material.texture, std::move(img)).first;
      }
      out_range.albedo_image = albedo_it->second;

      if (out_range.normal_index >= 0) {
        const auto &normal = surface_normal_image(out_range.normal_index);
        if (!normal.width || !normal.height || !normal.hash ||
            normal.pixels32.size() != std::uint64_t(normal.width) * normal.height)
          throw std::runtime_error("Owned rigid capture references invalid normal image record");
        out_range.normal_width = normal.width;
        out_range.normal_height = normal.height;
        out_range.normal_hash = normal.hash;
        auto norm_it = local_normal_images.find(out_range.normal_index);
        if (norm_it == local_normal_images.end()) {
          const std::uint64_t norm_pixels = std::uint64_t(normal.width) * normal.height;
          if (norm_pixels > std::numeric_limits<std::size_t>::max() / sizeof(std::uint32_t))
            throw std::runtime_error("Owned rigid capture normal byte count overflow");
          add_capture_bytes(owned_bytes, sizeof(CapturedRgbaImage), maximum_owned_bytes);
          add_capture_bytes(owned_bytes, std::size_t(norm_pixels) * sizeof(std::uint32_t),
                            maximum_owned_bytes);
          auto img = std::make_shared<CapturedRgbaImage>();
          img->width = normal.width;
          img->height = normal.height;
          img->pixels32 = normal.pixels32;
          norm_it = local_normal_images.emplace(out_range.normal_index, std::move(img)).first;
        }
        out_range.normal_image = norm_it->second;
      }
    }

    if (out_range.height_binding) {
      const auto &hb = *out_range.height_binding;
      if (!hb.image || !hb.image->width || !hb.image->height ||
          hb.image->pixels.size() != std::uint64_t(hb.image->width) * hb.image->height ||
          !hb.retained_decoded_bytes || out_range.texture_handle < 0 ||
          out_range.normal_index < 0 || !out_range.normal_image ||
          hb.normal_width != out_range.normal_width ||
          hb.normal_height != out_range.normal_height ||
          hb.normal_hash != out_range.normal_hash ||
          !mw34::materials::height_binding_stamps_match(
              hb, sampled_world_epoch, sampled_group_epoch, out_range.texture_version,
              out_range.albedo_key))
        throw std::runtime_error("Owned rigid capture height binding failed stamp verification");
      add_capture_bytes(owned_bytes, mw34::materials::height_binding_metadata_bytes(hb),
                        maximum_owned_bytes);
      if (charged_height_images.insert(hb.image).second) {
        if (hb.retained_decoded_bytes > std::numeric_limits<std::size_t>::max())
          throw std::runtime_error("Owned rigid capture height byte count overflow");
        add_capture_bytes(owned_bytes, std::size_t(hb.retained_decoded_bytes),
                          maximum_owned_bytes);
      }
    }
    captured_ranges.push_back(std::move(out_range));
  }

  if (zcls::world_source_epoch() != sampled_world_epoch ||
      group_load_epoch_ != sampled_group_epoch)
    throw std::runtime_error("Owned rigid capture producer epoch changed before seal");

  for (const auto &r : captured_ranges) {
    if (r.texture_handle >= 0) {
      if (std::size_t(r.texture_handle) >= textures_.size())
        throw std::runtime_error("Owned rigid capture texture slot disappeared before seal");
      const auto &slot = textures_[std::size_t(r.texture_handle)];
      if (slot.version != r.texture_version || slot.group_load_epoch != sampled_group_epoch ||
          slot.surface_key < r.albedo_key || r.albedo_key < slot.surface_key ||
          !r.albedo_image || slot.width != r.albedo_image->width ||
          slot.height != r.albedo_image->height || slot.pixels != r.albedo_image->pixels32)
        throw std::runtime_error("Owned rigid capture texture slot mutated before seal");
    }
    if (r.normal_index >= 0) {
      const auto &normal = surface_normal_image(r.normal_index);
      if (!r.normal_image || normal.width != r.normal_width ||
          normal.height != r.normal_height || normal.hash != r.normal_hash ||
          normal.pixels32 != r.normal_image->pixels32)
        throw std::runtime_error("Owned rigid capture normal record mutated before seal");
    }
    if (r.height_binding &&
        !mw34::materials::height_binding_stamps_match(
            *r.height_binding, sampled_world_epoch, sampled_group_epoch, r.texture_version,
            r.albedo_key))
      throw std::runtime_error("Owned rigid capture height binding became stale before seal");
  }

  registered.original_materials.clear();
  return RigidCaptureSeal::seal(
      std::move(registered.resource), std::move(captured_ranges), material_binding_owner_,
      sampled_world_epoch, sampled_group_epoch);
}

bool validate_captured_original_rigid(const CapturedNativeRigid &captured) {
  VisualFloatScope preserve;
  if (captured.renderer_owner().lock() != material_binding_owner_)
    return false;
  const std::uint64_t current_world_epoch = zcls::world_source_epoch();
  if (captured.world_source_epoch() != current_world_epoch ||
      captured.group_load_epoch() != group_load_epoch_)
    return false;
  const auto &res = captured.resource();
  const auto &ranges = captured.ranges();
  if (!res || ranges.empty() || res->ranges.size() != ranges.size() ||
      res->source_polygons != ranges.size())
    return false;
  for (std::size_t i = 0; i < ranges.size(); ++i) {
    const auto &r = ranges[i];
    const auto &rr = res->ranges[i];
    if (r.polygon != i || r.material_slot != i || rr.polygon != i || rr.material_slot != i)
      return false;
    if (r.texture_handle < 0) {
      if (r.material.texture >= 0 || r.albedo_image || r.normal_index >= 0 || r.normal_image ||
          r.height_binding)
        return false;
      continue;
    }
    if (r.material.texture != r.texture_handle ||
        std::size_t(r.texture_handle) >= textures_.size())
      return false;
    const auto &slot = textures_[std::size_t(r.texture_handle)];
    if (slot.group_load_epoch != group_load_epoch_ ||
        r.texture_group_epoch != group_load_epoch_ || slot.version != r.texture_version ||
        slot.surface_key < r.albedo_key || r.albedo_key < slot.surface_key || !r.albedo_image ||
        !r.albedo_image->width || !r.albedo_image->height ||
        slot.width != r.albedo_image->width || slot.height != r.albedo_image->height ||
        r.albedo_image->pixels32.size() !=
            std::uint64_t(r.albedo_image->width) * r.albedo_image->height ||
        slot.pixels != r.albedo_image->pixels32)
      return false;
    if (r.normal_index >= 0) {
      if (std::size_t(r.normal_index) >= surface_normals_.cache.textures.size() ||
          !r.normal_image)
        return false;
      const auto &normal = surface_normal_image(r.normal_index);
      if (!r.normal_width || !r.normal_height || !r.normal_hash ||
          normal.width != r.normal_width || normal.height != r.normal_height ||
          normal.hash != r.normal_hash || r.normal_image->width != r.normal_width ||
          r.normal_image->height != r.normal_height ||
          r.normal_image->pixels32 != normal.pixels32)
        return false;
    } else if (r.normal_image || r.normal_width || r.normal_height || r.normal_hash) {
      return false;
    }
    if (r.height_binding) {
      const auto &hb = *r.height_binding;
      if (r.normal_index < 0 || !r.normal_image || !hb.image ||
          hb.image->pixels.size() != std::uint64_t(hb.image->width) * hb.image->height ||
          !hb.retained_decoded_bytes || !prepared_.surface_budget() ||
          prepared_.surface_budget()->used() < hb.retained_decoded_bytes ||
          hb.normal_width != r.normal_width || hb.normal_height != r.normal_height ||
          hb.normal_hash != r.normal_hash ||
          !mw34::materials::height_binding_stamps_match(
              hb, current_world_epoch, group_load_epoch_, r.texture_version, r.albedo_key))
        return false;
    }
  }
  return true;
}
public:
