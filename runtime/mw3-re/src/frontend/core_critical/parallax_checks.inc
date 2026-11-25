// Authored relief fixtures use the production material SPIR-V and the actual
// owned binding API. The oracle solves an affine height plane analytically;
// it neither implements the GPU search nor reads expected values from it.
namespace pom_checks {
namespace vk = mw34::vkscene;
namespace mat = mw34::materials;
using Vector = std::array<double, 3>;
double dot(const Vector &a, const Vector &b) {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}
Vector cross(const Vector &a, const Vector &b) {
  return {a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
          a[0] * b[1] - a[1] * b[0]};
}
Vector normalized(Vector value) {
  const double length = std::sqrt(dot(value, value));
  for (auto &component : value) component /= length;
  return value;
}
std::string digest(const void *bytes, std::size_t length) {
  platform::integrity::Sha256 sha;
  sha.update(bytes, length);
  return sha.hex();
}
enum class Route { model, world, tl, native };
enum class Height { constant, zero, one, ramp_u, ramp_v, atlas, atlas_ramp };
struct Fixture {
  vk::Scene scene;
  Vector du{}, dv{}, normal{};
  std::array<double, 2> base{.5, .5};
  std::shared_ptr<mat::SurfaceDecodedBudget> budget;
};

// The reader validates the same BWSFM1 format, hashes, budget and batch binding
// used by production. No media or filesystem input is involved.
std::shared_ptr<const mat::HeightBinding>
binding(const std::vector<vk::ModelVertex> &vertices, const std::vector<std::uint16_t> &albedo,
        const std::vector<std::uint32_t> &normal, Height height,
        const mat::SurfaceMaterialRecord &material,
        const std::shared_ptr<mat::SurfaceDecodedBudget> &budget, bool ground) {
  struct Batch { std::vector<vk::ModelVertex> vertices; };
  const std::vector<Batch> batches{{vertices}};
  const auto uv_hash = mat::compute_mesh_uv_hash(batches, 0, 1);
  const unsigned width = (height == Height::atlas || height == Height::atlas_ramp) ? 64 : 32;
  const unsigned image_height = 32;
  std::vector<std::uint32_t> pixels(width * image_height);
  for (unsigned y = 0; y < image_height; ++y)
    for (unsigned x = 0; x < width; ++x) {
      const unsigned scalar = height == Height::zero ? 0
                              : height == Height::one ? 255
                              : height == Height::ramp_u ? 4 + 8 * x
                              : height == Height::ramp_v ? 4 + 8 * y
                              : height == Height::atlas ? (x < 32 ? 0 : 255)
                              : height == Height::atlas_ramp ? (x < 32 ? 4 + 8 * x : 255)
                                                         : 128;
      pixels[y * width + x] = scalar | scalar << 8 | scalar << 16 | 0xff000000U;
    }
  std::ostringstream encoded(std::ios::binary);
  auto u32 = [&](std::uint32_t value) {
    for (unsigned byte = 0; byte < 4; ++byte) encoded.put(char(value >> (byte * 8)));
  };
  auto u64 = [&](std::uint64_t value) { u32(std::uint32_t(value)); u32(std::uint32_t(value >> 32)); };
  auto scalar = [&](float value) { u32(std::bit_cast<std::uint32_t>(value)); };
  auto text = [&](std::string_view value) {
    u32(std::uint32_t(value.size()));
    encoded.write(value.data(), std::streamsize(value.size()));
  };
  encoded.write("BWSFM1\0\0", 8);
  u32(1); u32(1); u32(1); u32(1); u64(uv_hash); u32(0);
  text("fixture:pom"); text("PomFixture");
  u32(0); u32(mat::no_surface_image);
  scalar(material.height_reference); scalar(material.height_amplitude);
  scalar(std::abs(material.height_amplitude)); u32(1);
  for (auto value : material.uv_scale) scalar(value);
  for (auto value : material.uv_offset) scalar(value);
  u32(material.address_mode_u); u32(material.address_mode_v);
  for (auto value : material.atlas_rect) scalar(value);
  // No thickness/SSS in this relief-only fixture; retain independent PBR values.
  for (unsigned i = 0; i < 6; ++i) scalar(0);
  scalar(.7f); scalar(.04f); scalar(0);
  text("fixture-height"); u32(mat::surface_role_height); u32(width); u32(image_height);
  u64(mat::normal_hash(pixels.data(), pixels.size() * 4));
  encoded.write(reinterpret_cast<const char *>(pixels.data()), std::streamsize(pixels.size() * 4));
  const auto bytes = encoded.str();
  std::istringstream input(bytes, std::ios::binary);
  auto pack = std::make_shared<mat::SurfaceMaterialPack>(mat::read_surface_materials(
      input, "fixture:pom", uv_hash, {"PomFixture"}, mat::max_surface_sidecar_bytes,
      mat::max_surface_sidecar_bytes, budget));
  const auto source_sha = digest(vertices.data(), vertices.size() * sizeof(vertices[0]));
  const mat::SurfaceKey key{32, 32, 1, mat::normal_hash(albedo.data(), albedo.size() * 2)};
  if (ground) {
    // Original source polygon and independently authored expected corner stream
    // agree before rendering. The source guard reads no GPU/first-draw data.
    // Synthetic provenance tests the guard, not a real ZBD/sidecar file SHA.
    zcls::Node node{};
    zmod::Model model{};
    zvid::D3DTexture texture{};
    texture.handle = 7; texture.type = 1;
    zimg::Texture image{};
    zimg::TextureEntry entry{};
    std::strcpy(entry.name, "PomFixture");
    entry.surface = &texture; entry.image = &image;
    zmod::Material source_material{};
    source_material.alpha = 255; source_material.flags = 1;
    source_material.texture = &entry;
    std::array<float, 12> positions{}, normals{};
    std::array<float, 8> uv{};
    for (unsigned corner = 0; corner < 4; ++corner) {
      const auto &vertex = vertices.at(corner);
      positions[corner * 3] = vertex.x;
      positions[corner * 3 + 1] = vertex.y;
      positions[corner * 3 + 2] = vertex.z;
      normals[corner * 3] = vertex.nx;
      normals[corner * 3 + 1] = vertex.ny;
      normals[corner * 3 + 2] = vertex.nz;
      uv[corner * 2] = vertex.u; uv[corner * 2 + 1] = vertex.v;
    }
    std::array<std::uint32_t, 4> corners{0, 1, 2, 3};
    zmod::Polygon polygon{};
    polygon.flags = 4 | 0x200;
    polygon.vertex_indices = polygon.normal_indices = corners.data();
    polygon.uvs = uv.data(); polygon.material = &source_material;
    const std::uint32_t one = 1, four = 4;
    std::memcpy(model.header + 0x10, &one, 4);
    std::memcpy(model.header + 0x14, &four, 4);
    std::memcpy(model.header + 0x18, &four, 4);
    model.polygons = &polygon; model.vertices = positions.data(); model.normals = normals.data();
    node.model = &model;
    auto source = std::make_shared<zcls::SourceAsset>();
    source->world = zcls::WorldSourceIdentity{
        "gamez-zbd-v27", "authored/pom-gamez.zbd", source_sha,
        vertices.size() * sizeof(vertices[0]), 19, 37};
    node.source_asset = model.world_source_asset = source;
    platform::prepared::MaterialTarget target;
    target.asset_id = "fixture:pom";
    target.source = {"gamez-zbd-v27", "authored/pom-gamez.zbd", source_sha,
                     vertices.size() * sizeof(vertices[0]), 37};
    target.sidecar_path = "synthetic-only/pom.bwsfm";
    target.sidecar_sha256 = digest(bytes.data(), bytes.size());
    target.polygon_materials = {"PomFixture"};
    target.surface_keys = {key};
    target.mesh_uv_hash = uv_hash;
    target.pack = pack;
    cc_mw3_re::NativeGroundHeightInput input;
    input.node = &node; input.model = &model;
    input.material = {&model, &source_material, &entry, 0};
    input.key = input.slot_key = key;
    input.texture = 7; input.normal_index = 3;
    input.normal_width = input.normal_height = 32;
    input.normal_hash = mat::normal_hash(normal.data(), normal.size() * 4);
    input.source_epoch = 19;
    input.producer_epoch = input.slot_epoch = input.current_group_epoch = 1;
    input.texture_version = input.current_texture_version = 1;
    input.enabled = input.eligible = true;
    auto admitted = cc_mw3_re::admit_native_ground_height(target, input, budget);
    require(bool(admitted), "POM authored original ground admission returned no snapshot");
    return admitted;
  }
  const auto resolved = mat::resolve_height_binding(pack, 0, source_sha,
      digest(bytes.data(), bytes.size()), key, 32, 32,
      mat::normal_hash(normal.data(), normal.size() * 4));
  // This fixture acts as an owned producer epoch, never an engine pointer.
  auto snapshot = std::make_shared<mat::HeightBinding>(*resolved);
  snapshot->producer_epoch = 1;
  snapshot->texture_version = 1;
  return snapshot;
}

Fixture fixture(Route route, Height height, float amplitude = .04f, float reference = .5f,
                double incidence = .7, std::array<float, 2> chart_scale = {1, 1},
                std::array<float, 2> chart_offset = {0, 0},
                std::array<double, 2> world_scale = {1, 1}, bool normal_pattern = false,
                unsigned address = mat::surface_address_wrap,
                std::optional<std::array<float, 2>> constant_uv = std::nullopt,
                bool raster_exact_atlas = false,
                std::array<float, 3> position_offset = {0, 0, 0}) {
  Fixture fixture;
  auto &scene = fixture.scene;
  scene.width = scene.height = 32;
  scene.has_depth = true;
  scene.color.resize(32 * 32);
  scene.depth.resize(32 * 32);
  scene.world_eye = {0, 0, 0};
  scene.world_eye_valid = true;
  scene.pom_raw_readback = true;
  scene.pom_diagnostic_mode = 1;
  const double sine = std::sqrt(1 - incidence * incidence);
  // Rotate the texture chart within the tilted plane so BOTH U and V ramps
  // have a nonzero view-ray slope, even at the centre sample.
  const double cosine_chart = std::cos(.35), sine_chart = std::sin(.35);
  // This tilted atlas plane projects to integer pixel coordinates (8,8),
  // (20,12), (20,20), (8,24). Its centre UV is exactly (.5,.5), so the tight
  // atlas oracle does not also measure legal raster subpixel interpolation.
  const Vector local_du = raster_exact_atlas ? Vector{8.0 / 3, 0, 8.0 / 3}
      : Vector{3 * incidence * cosine_chart, 3 * sine_chart, 3 * sine * cosine_chart};
  const Vector local_dv = raster_exact_atlas ? Vector{0, 8.0 / 3, 0}
      : Vector{-6 * incidence * sine_chart, 6 * cosine_chart, -6 * sine * sine_chart};
  fixture.du = {local_du[0] * world_scale[0], local_du[1] * world_scale[1], local_du[2]};
  fixture.dv = {local_dv[0] * world_scale[0], local_dv[1] * world_scale[1], local_dv[2]};
  fixture.normal = normalized(cross(fixture.dv, fixture.du));
  static std::uint64_t geometry_identity = 1000;
  auto geometry = std::make_shared<vk::ModelGeometry>();
  geometry->key = ++geometry_identity;
  const std::array<std::array<float, 2>, 4> corners{{{0, 0}, {1, 0}, {1, 1}, {0, 1}}};
  for (const auto &uv : corners) {
    const double u = double(uv[0]) - .5, v = double(uv[1]) - .5;
    const auto texcoord = constant_uv.value_or(uv);
    geometry->vertices.push_back({float(u * local_du[0] + v * local_dv[0]),
        float(u * local_du[1] + v * local_dv[1]),
        float(4 + u * local_du[2] + v * local_dv[2]),
        float(sine), 0, float(-incidence), texcoord[0], texcoord[1]});
  }
  geometry->indices = {0, 1, 2, 0, 2, 3};
  // Spatial batching controls must be authored before hashing/admission, so
  // the source receipt describes the geometry that actually reaches the GPU.
  for (auto &vertex : geometry->vertices) {
    if (position_offset[0] != 0) vertex.x += position_offset[0];
    if (position_offset[1] != 0) vertex.y += position_offset[1];
    if (position_offset[2] != 0) vertex.z += position_offset[2];
  }
  geometry->hash = mat::normal_hash(geometry->vertices.data(), geometry->vertices.size() * 32);
  auto resource = std::make_shared<cc::geometry::Resource>();
  resource->identity = geometry->key;
  resource->vertices = geometry->vertices;
  resource->indices = geometry->indices;
  geometry->source = resource;
  auto instance = std::make_shared<vk::ModelInstance>();
  instance->geometry = geometry;
  instance->source = resource;
  instance->camera = instance->sun_world =
      {float(world_scale[0]), 0, 0, 0, 0, float(world_scale[1]), 0, 0, 0, 0, 1, 0};
  instance->sun_normal = {float(1 / world_scale[0]), 0, 0, 0,
                           0, float(1 / world_scale[1]), 0, 0, 0, 0, 1, 0};
  instance->projection = {1, 16, 16, 16, 16, 100};
  instance->color = 0xffffffff;
  instance->sun_eligible = true;
  instance->world = route == Route::world;
  instance->gpu_vertices = route == Route::native;
  instance->geometry_near = 1;
  std::vector<std::uint16_t> albedo(32 * 32);
  std::vector<std::uint32_t> normal(32 * 32, 0xffff8080U);
  for (unsigned y = 0; y < 32; ++y)
    for (unsigned x = 0; x < 32; ++x) {
      albedo[y * 32 + x] = std::uint16_t((x << 11) | ((y * 2) << 5) | (31 - x));
      if (normal_pattern)
        normal[y * 32 + x] = (96 + 2 * x) | ((96 + 2 * y) << 8) | (240U << 16) | 0xff000000U;
    }
  scene.textures.push_back({1, 1, 32, 32, vk::TexFormat::rgb565, albedo, {}});
  scene.textures.push_back({2, normal_pattern ? 2ULL : 1ULL, 32, 32,
                            vk::TexFormat::rgba8888, {}, normal});
  vk::Draw draw{};
  draw.count = 6;
  draw.texture = 0; draw.normal_texture = 1;
  draw.sampler = 3U | (3U << 4) | (3U << 8);
  draw.key = {0, 5, 6, 1, 7, 1, 1, 0};
  draw.scissor = {{0, 0}, {32, 32}};
  draw.push.target[0] = draw.push.target[1] = 32;
  draw.push.target[2] = .5f;
  draw.push.mode[0] = 6;
  draw.push.mode[1] = draw.push.mode[2] = 2U | (2U << 8);
  draw.surface_eye = {0, 0, 0, 1};
  draw.model = instance;
  mat::SurfaceMaterialRecord material;
  material.height_amplitude = amplitude;
  material.height_reference = reference;
  material.uv_scale = chart_scale; material.uv_offset = chart_offset;
  material.address_mode_u = material.address_mode_v = address;
  if (height == Height::atlas || height == Height::atlas_ramp)
    material.atlas_rect = {0, 0, .5f, 1};
  fixture.budget = std::make_shared<mat::SurfaceDecodedBudget>();
  draw.height_binding = binding(geometry->vertices, albedo, normal, height, material,
                                fixture.budget, route != Route::model);
  std::vector<platform::TLVertex> tl_vertices;
  for (unsigned index : geometry->indices) {
    const auto &vertex = geometry->vertices[index];
    const float depth = 1 / vertex.z;
    tl_vertices.push_back({vertex.x * float(world_scale[0]) * 16 * depth + 16,
        vertex.y * float(world_scale[1]) * 16 * depth + 16, depth, depth,
        0xffffffff, 0xff000000, vertex.u, vertex.v});
  }
  if (route == Route::tl) {
    draw.model.reset();
    auto tl = std::make_shared<mw34::sun::Tl>();
    tl->camera_world = {1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0};
    tl->projection = instance->projection;
    draw.sun_tl = tl;
    draw.lit_normals = std::make_shared<const std::vector<std::array<float, 3>>>(6,
        std::array<float, 3>{float(fixture.normal[0]), float(fixture.normal[1]),
                              float(fixture.normal[2])});
  } else if (route == Route::world) {
    tl_vertices.clear();
    for (const auto &vertex : geometry->vertices)
      tl_vertices.push_back({0, 0, 0, 0, 0xffffffff, 0xff000000, vertex.u, vertex.v});
  }
  scene.vertices.resize(tl_vertices.size() * sizeof(platform::TLVertex));
  std::memcpy(scene.vertices.data(), tl_vertices.data(), scene.vertices.size());
  scene.draws.push_back(draw);
  scene.order.push_back({false, 0});
  return fixture;
}

std::array<double, 2> decode(const vk::Scene &scene, unsigned x = 16, unsigned y = 16) {
  require(scene.pom_rgba8.size() == 32 * 32 * 4, "POM raw RGBA8 capture is missing");
  const auto *bytes = scene.pom_rgba8.data() + (y * 32 + x) * 4;
  return {double(unsigned(bytes[0]) | (unsigned(bytes[1]) << 8)) / 65535,
          double(unsigned(bytes[2]) | (unsigned(bytes[3]) << 8)) / 65535};
}
std::array<double, 2> expected(const Fixture &fixture, Height height,
                              Vector view = {0, 0, -1}) {
  const auto &material = fixture.scene.draws[0].height_binding->material;
  // Default centre P=(0,0,4) sees the origin along -Z. Other authored
  // samples supply eye-P; its length cancels in both analytic ratios.
  const double incidence = dot(fixture.normal, view);
  const auto reciprocal_u = cross(fixture.dv, fixture.normal);
  const auto reciprocal_v = cross(fixture.normal, fixture.du);
  const double determinant = dot(fixture.du, reciprocal_u);
  const std::array<double, 2> q{dot(reciprocal_u, view) / (incidence * determinant),
                                dot(reciprocal_v, view) / (incidence * determinant)};
  std::array<double, 2> gradient{};
  double h0 = double(float(128.f / 255.f));
  if (height == Height::zero) h0 = 0;
  if (height == Height::one) h0 = 1;
  if (height == Height::ramp_u || height == Height::ramp_v) {
    const unsigned axis = height == Height::ramp_u ? 0 : 1;
    // 32-wide byte ramp 4+8*x, linear texel centres: h = 256*u/255.
    gradient[axis] = 256.0 / 255 * material.uv_scale[axis];
    h0 = 256.0 / 255 * (fixture.base[axis] * material.uv_scale[axis] + material.uv_offset[axis]);
  } else if (height == Height::atlas) h0 = 0;
  else if (height == Height::atlas_ramp) {
    const double chart = fixture.base[0] * material.uv_scale[0] + material.uv_offset[0];
    require(chart > .51 && chart < .54, "POM atlas ramp oracle left its authored interval");
    double addressed{}, slope{};
    if (material.address_mode_u == mat::surface_address_wrap) {
      addressed = chart - .5; slope = 1;
    } else if (material.address_mode_u == mat::surface_address_mirror) {
      addressed = 1 - chart; slope = -1;
    } else {
      addressed = .5 - .5 / 64; slope = 0;
    }
    h0 = 512.0 / 255 * addressed;
    gradient[0] = 512.0 / 255 * slope * material.uv_scale[0];
  }
  const double denominator = 1 - material.height_amplitude *
      (gradient[0] * q[0] + gradient[1] * q[1]);
  require(std::abs(denominator) > .25, "POM analytic fixture denominator is not bounded");
  const double t = material.height_amplitude * (h0 - material.height_reference) / denominator;
  return {fixture.base[0] + q[0] * t, fixture.base[1] + q[1] * t};
}
void compare_uv(const std::array<double, 2> &actual, const std::array<double, 2> &wanted,
                const char *message, double tolerance = 1.5e-3) {
  for (unsigned axis = 0; axis < 2; ++axis)
    if (!std::isfinite(actual[axis]) || std::abs(actual[axis] - wanted[axis]) > tolerance) {
      std::fprintf(stderr, "%s axis %u actual %.9f expected %.9f\n", message, axis,
                   actual[axis], wanted[axis]);
      require(false, message);
    }
}

void per_draw_eye_affine_oracle(vk::Renderer &renderer, vk::Renderer &disabled) {
  // The existing integer-raster plane has centre UV(.5,.5). Scaling X/Y by
  // .5 and translating its source X by +/-2 puts its world-space centres at
  // (-1,0,4)/(1,0,4), precisely under pixels(12,16)/(20,16).
  auto left = fixture(Route::tl, Height::ramp_u, .08f, .1f, .7,
      {1, 1}, {0, 0}, {.5, .5}, false, mat::surface_address_wrap,
      std::nullopt, true, {-2, 0, 0});
  auto right = fixture(Route::tl, Height::ramp_u, .08f, .1f, .7,
      {1, 1}, {0, 0}, {.5, .5}, false, mat::surface_address_wrap,
      std::nullopt, true, {2, 0, 0});
  left.scene.draws[0].surface_eye = {-1.5f, .8f, -.5f, 1};
  right.scene.draws[0].surface_eye = {1.75f, -.6f, .25f, 1};
  // Independent eye-minus-known-surface-point vectors; neither expected UV
  // comes from renderer output or from rendering one draw as a golden image.
  const auto wanted_left = expected(left, Height::ramp_u, {-.5, .8, -4.5});
  const auto wanted_right = expected(right, Height::ramp_u, {.75, -.6, -3.75});
  const auto wrong_left = expected(left, Height::ramp_u, {1, 0, -4});
  const auto wrong_right = expected(right, Height::ramp_u, {-1, 0, -4});
  require(std::abs(wanted_left[0] - wrong_left[0]) > .006 &&
              std::abs(wanted_right[0] - wrong_right[0]) > .006 &&
              std::abs(wanted_left[0] - wanted_right[0]) > .006,
          "POM per-draw eye analytic control intervals overlap");
  auto mixed = left.scene;
  mixed.vertices.insert(mixed.vertices.end(), right.scene.vertices.begin(),
                         right.scene.vertices.end());
  mixed.draws.push_back(right.scene.draws[0]);
  mixed.draws[1].first = mixed.draws[0].count;
  mixed.order.push_back({false, 1});
  // This valid Scene eye differs from both owned draw eyes. One global eye
  // cannot satisfy these two analytic displacement expectations.
  mixed.world_eye = {0, 0, 0};
  mixed.world_eye_valid = true;
  // render() uploads and replaces Scene color/depth; compare two fresh inputs.
  auto replay = mixed;
  std::printf("pom_per_draw_eye_affine_oracle begin\n");
  renderer.render(mixed);
  for (unsigned x : {12U, 20U})
    require(mixed.pom_depth32.at(16 * 32 + x) > 0,
            "POM per-draw eye analytic sample is not covered");
  compare_uv(decode(mixed, 12, 16), wanted_left,
              "POM same-scene left draw used another eye");
  compare_uv(decode(mixed, 20, 16), wanted_right,
              "POM same-scene right draw used another eye");
  replay.world_eye = {std::numeric_limits<float>::quiet_NaN(),
                       std::numeric_limits<float>::infinity(), 0};
  replay.world_eye_valid = false;
  renderer.render(replay);
  require(replay.pom_rgba8 == mixed.pom_rgba8 &&
              replay.pom_depth32 == mixed.pom_depth32,
          "POM per-draw eyes depended on obsolete Scene camera metadata");

  for (auto route : {Route::model, Route::world, Route::tl, Route::native}) {
    auto origin = fixture(route, Height::ramp_u, .08f, .1f);
    origin.scene.world_eye_valid = false;
    renderer.render(origin.scene);
    compare_uv(decode(origin.scene), expected(origin, Height::ramp_u),
                "POM rejected or changed a valid world-origin draw eye");
    for (unsigned invalid = 0; invalid < 8; ++invalid) {
      auto test = fixture(route, Height::ramp_u, .08f, .1f);
      auto &eye = test.scene.draws[0].surface_eye;
      if (invalid == 0) eye = {};
      if (invalid == 1) eye[0] = std::numeric_limits<float>::quiet_NaN();
      if (invalid == 2) eye[1] = std::numeric_limits<float>::infinity();
      if (invalid == 3) eye[2] = -std::numeric_limits<float>::infinity();
      if (invalid == 4) eye[3] = std::numeric_limits<float>::quiet_NaN();
      if (invalid == 5) eye[3] = std::numeric_limits<float>::infinity();
      if (invalid == 6) eye[3] = 0;
      if (invalid == 7) eye[3] = 2;
      bool rejected{};
      try { renderer.render(test.scene); }
      catch (const std::runtime_error &) { rejected = true; }
      require(rejected, "POM admitted a missing/nonfinite/nonposition draw eye");
      // Off must not acquire a new required camera dependency.
      auto valid_off = fixture(route, Height::ramp_u, .08f, .1f);
      disabled.render(valid_off.scene);
      disabled.render(test.scene);
      require(test.scene.pom_rgba8 == valid_off.scene.pom_rgba8 &&
                  test.scene.pom_depth32 == valid_off.scene.pom_depth32 &&
                  disabled.height_uploads == 0,
              "POM Off inspected an excluded invalid draw eye");
    }
  }
  std::printf("pom_per_draw_eye_affine_oracle pass\n");
}

void shader_layout(const std::uint32_t *words, std::size_t count) {
  std::uint32_t block{};
  for (std::size_t at = 5; at < count;) {
    const auto length = words[at] >> 16, opcode = words[at] & 65535;
    require(length && length <= count - at, "POM malformed SPIR-V instruction");
    if (opcode == 5 && length >= 3 &&
        std::string_view(reinterpret_cast<const char *>(words + at + 2)) == "SunLighting")
      block = words[at + 1];
    at += length;
  }
  require(block != 0, "POM production shader has no SunLighting block");
  std::array<unsigned, 35> offsets;
  offsets.fill(UINT32_MAX);
  for (std::size_t at = 5; at < count;) {
    const auto length = words[at] >> 16, opcode = words[at] & 65535;
    if (opcode == 72 && length == 5 && words[at + 1] == block && words[at + 3] == 35) {
      require(words[at + 2] < offsets.size(), "POM shader has an unexpected uniform member");
      offsets[words[at + 2]] = words[at + 4];
    }
    at += length;
  }
  for (unsigned member = 0; member < offsets.size(); ++member) {
    const unsigned expected = member <= 27 ? member * 16 : 944 + (member - 28) * 16;
    require(offsets[member] == expected, "POM CPU/SPIR-V std140 layout mismatch");
  }
}
void uniform_layout_and_rgba16_roundtrip() {
  require(sizeof(mw34::sun::Uniform) == 1056 && alignof(mw34::sun::Uniform) == 16 &&
      offsetof(mw34::sun::Uniform, tiled_lights) == 976 &&
      offsetof(mw34::sun::Uniform, pom_params) == 992 &&
      offsetof(mw34::sun::Uniform, pom_uv) == 1008 &&
      offsetof(mw34::sun::Uniform, pom_atlas) == 1024 &&
      offsetof(mw34::sun::Uniform, pom_policy) == 1040,
      "POM host uniform layout changed");
  for (const auto module : {std::pair{effect_scene_frag_spv, std::size(effect_scene_frag_spv)},
      std::pair{sun_model_vert_spv, std::size(sun_model_vert_spv)},
      std::pair{sun_world_vert_spv, std::size(sun_world_vert_spv)},
      std::pair{sun_tl_vert_spv, std::size(sun_tl_vert_spv)},
      std::pair{native_geometry_vert_spv, std::size(native_geometry_vert_spv)}})
    shader_layout(module.first, module.second);
  for (unsigned value = 0; value <= 65535; ++value) {
    const double input = double(value) / 65535;
    const auto packed = unsigned(std::round(input * 65535));
    const unsigned low = packed & 255, high = packed >> 8;
    require(std::abs(double(low | high << 8) / 65535 - input) < 4e-5,
            "POM 16-bit UV byte roundtrip loses precision");
  }
  mw34::sun::Uniform uniform{};
  constexpr std::uint64_t limit = (std::uint64_t(UINT32_MAX) - 2) / 5;
  const auto counts = vk::Renderer::material_descriptor_counts(limit);
  require(counts[0] == limit * 5 + 2 && counts[1] == limit * 2 + 1 &&
              vk::Renderer::material_descriptor_capacity(limit - 64, 0) == limit,
          "POM material descriptor boundary changed");
  for (unsigned invalid = 0; invalid < 4; ++invalid) {
    bool rejected{};
    try {
      if (invalid == 0) (void)vk::Renderer::material_descriptor_counts(limit + 1);
      if (invalid == 1) (void)vk::Renderer::material_descriptor_capacity(UINT64_MAX, 0);
      if (invalid == 2) (void)vk::Renderer::material_descriptor_capacity(1, UINT64_MAX);
      if (invalid == 3) (void)vk::Renderer::material_descriptor_capacity(limit - 63, 0);
    } catch (const std::runtime_error &) { rejected = true; }
    require(rejected, "POM descriptor arithmetic overflow did not reject before allocation");
  }
  mw34::submission::ExactUniformRuns<mw34::sun::Uniform> runs;
  auto prior = runs.identify(uniform);
  for (unsigned field = 0; field < 4; ++field) {
    if (field == 0) uniform.pom_params[2] = -.25f;
    if (field == 1) uniform.pom_uv[0] = -1;
    if (field == 2) uniform.pom_atlas[2] = .5f;
    if (field == 3) uniform.pom_policy[0] = 2;
    const auto next = runs.identify(uniform);
    require(next != prior && runs.identify(uniform) == next,
            "POM exact uniform equality lost an appended field");
    prior = next;
  }
  std::printf("pom_uniform_layout_and_rgba16_roundtrip pass\n");
}

void constant_and_ramp_signed_uv(vk::Renderer &renderer) {
  for (auto route : {Route::model, Route::world, Route::tl, Route::native})
    for (auto height : {Height::constant, Height::zero, Height::one, Height::ramp_u, Height::ramp_v})
      for (float amplitude : {-.04f, 0.f, .04f})
        for (float reference : {0.f, .5f, 1.f})
          for (double incidence : {.15, .5, 1.0}) {
            auto test = fixture(route, height, amplitude, reference, incidence);
            renderer.render(test.scene);
            compare_uv(decode(test.scene), expected(test, height), "POM signed affine height oracle");
          }
  for (auto scale : {std::array<float, 2>{-1, 1}, std::array<float, 2>{1, -1},
                     std::array<float, 2>{.5f, 1.5f}}) {
    const std::array<float, 2> offset{.5f - .5f * scale[0], .5f - .5f * scale[1]};
    for (auto route : {Route::model, Route::tl, Route::native})
      for (auto height : {Height::ramp_u, Height::ramp_v}) {
        auto test = fixture(route, height, -.04f, .1f, .3, scale, offset, {2, .5});
        renderer.render(test.scene);
        compare_uv(decode(test.scene), expected(test, height), "POM mirrored/chart/world-scale oracle");
      }
  }
  std::printf("pom_constant_and_ramp_signed_uv pass\n");
}
void off_and_zero_amplitude_identity(vk::Renderer &renderer, vk::Renderer &disabled) {
  // Constant declared inputs isolate byte encoding from raster subpixel
  // interpolation. Author them before geometry hashing and source admission.
  for (auto codes : {std::array<unsigned, 2>{0x0000, 0xffff}, {0xffff, 0x0000},
                     {0x0001, 0xfffe}, {0x00ff, 0xff00}, {0x0100, 0xfeff},
                     {0x1234, 0xabcd}, {0x7fff, 0x8000}, {0xaaaa, 0x5555},
                     {0x1357, 0x2468}}) {
    const std::array<float, 2> uv{float(codes[0]) / 65535, float(codes[1]) / 65535};
    const std::array<double, 2> wanted{double(uv[0]), double(uv[1])};
    auto roundtrip = fixture(Route::tl, Height::constant, 0, .5f, 1, {1, 1},
                             {0, 0}, {1, 1}, false, mat::surface_address_wrap, uv);
    renderer.render(roundtrip.scene);
    for (unsigned y : {12U, 16U, 20U})
      for (unsigned x : {12U, 16U, 20U}) {
        compare_uv(decode(roundtrip.scene, x, y), wanted,
                    "POM actual shader RGBA16 roundtrip", 4e-5);
      }
  }
  for (auto route : {Route::model, Route::world, Route::tl, Route::native}) {
    auto base = fixture(route, Height::constant);
    base.scene.pom_diagnostic_mode = 0;
    auto off = base.scene;
    disabled.render(off);
    require(disabled.height_uploads == 0, "Off uploaded height bytes");
    auto normal_only = base.scene;
    normal_only.draws[0].height_binding.reset();
    renderer.render(normal_only);
    require(normal_only.pom_rgba8 == off.pom_rgba8 && normal_only.color == off.color &&
                normal_only.depth == off.depth && normal_only.pom_depth32 == off.pom_depth32,
            "Off/normal-only changed actual color or depth");
    auto neutral = fixture(route, Height::ramp_u, 0);
    neutral.scene.pom_diagnostic_mode = 0;
    const auto uploads = renderer.height_uploads;
    renderer.render(neutral.scene);
    require(neutral.scene.pom_rgba8 == off.pom_rgba8 && neutral.scene.color == off.color &&
                neutral.scene.depth == off.depth && neutral.scene.pom_depth32 == off.pom_depth32 &&
                renderer.height_uploads == uploads,
            "A==0 changed color/depth or uploaded an unused height image");
    auto active = base.scene;
    renderer.render(active);
    require(active.depth == off.depth && active.pom_depth32 == off.pom_depth32,
            "POM altered the production depth path");
  }
  for (unsigned excluded = 0; excluded < 9; ++excluded) {
    auto test = fixture(Route::tl, Height::constant);
    test.scene.pom_diagnostic_mode = 0;
    // An invalid height payload must remain entirely uninspected for excluded
    // draws; ordinary alpha, water/detail, HUD and debug paths still execute.
    auto poison = std::make_shared<mat::HeightBinding>(*test.scene.draws[0].height_binding);
    poison->image.reset();
    test.scene.draws[0].height_binding = poison;
    auto &draw = test.scene.draws[0];
    if (excluded == 0) test.scene.hud = true;
    if (excluded == 1) test.scene.frontend_canvas = true;
    if (excluded == 2) draw.key.blend = 1;
    if (excluded == 3) draw.key.zwrite = 0;
    if (excluded == 4) draw.detail_role = 1;
    if (excluded == 5) draw.condition_schematic = true;
    if (excluded == 6) draw.geometry_debug_normals = true;
    if (excluded == 7) draw.push.mode[0] |= 32U;
    if (excluded == 8) draw.native_sky = true;
    auto off = test.scene;
    disabled.render(off);
    const auto uploads = renderer.height_uploads;
    renderer.render(test.scene);
    require(test.scene.pom_rgba8 == off.pom_rgba8 && test.scene.depth == off.depth &&
                test.scene.pom_depth32 == off.pom_depth32 && renderer.height_uploads == uploads,
            "POM changed an excluded material path or inspected its height payload");
  }
  std::printf("pom_off_and_zero_amplitude_identity pass\n");
}

void inverse_chart_color_normal_correspondence(vk::Renderer &renderer) {
  for (auto route : {Route::model, Route::world, Route::tl, Route::native}) {
    auto test = fixture(route, Height::ramp_u, -.08f, .1f, .3,
                         {-1, .5f}, {1, .25f}, {2, .5}, true);
    test.scene.draws[0].surface_parameters = {.35f, .12f, .2f, 1};
    const auto wanted = expected(test, Height::ramp_u);
    test.scene.pom_diagnostic_mode = 0;
    renderer.render(test.scene);
    auto reference = test.scene;
    reference.draws[0].height_binding.reset();
    // Translate only the base chart by the independent analytic displacement.
    // Its derivatives, world metric and normal basis remain the originals.
    const float delta_u = float(wanted[0] - .5), delta_v = float(wanted[1] - .5);
    if (reference.draws[0].model) {
      auto instance = std::make_shared<vk::ModelInstance>(*reference.draws[0].model);
      auto geometry = std::make_shared<vk::ModelGeometry>(*instance->geometry);
      geometry->key |= std::uint64_t(1) << 63;
      for (auto &vertex : geometry->vertices) {
        vertex.u += delta_u; vertex.v += delta_v;
      }
      geometry->hash = mat::normal_hash(geometry->vertices.data(), geometry->vertices.size() * 32);
      auto source = std::make_shared<cc::geometry::Resource>(*instance->source);
      source->identity = geometry->key;
      source->vertices = geometry->vertices;
      geometry->source = source;
      instance->source = source;
      instance->geometry = geometry;
      reference.draws[0].model = instance;
    }
    for (std::size_t offset = 0; offset < reference.vertices.size(); offset += sizeof(platform::TLVertex)) {
      platform::TLVertex vertex;
      std::memcpy(&vertex, reference.vertices.data() + offset, sizeof(vertex));
      vertex.tu += delta_u; vertex.tv += delta_v;
      std::memcpy(reference.vertices.data() + offset, &vertex, sizeof(vertex));
    }
    reference.color.assign(32 * 32, 0);
    reference.depth.assign(32 * 32, 0);
    renderer.render(reference);
    constexpr unsigned pixel = (16 * 32 + 16) * 4;
    for (unsigned channel = 0; channel < 4; ++channel)
      require(std::abs(int(test.scene.pom_rgba8[pixel + channel]) -
                       int(reference.pom_rgba8[pixel + channel])) <= 2,
              "POM inverse chart/normal basis does not match analytic material sampling");
    require(test.scene.pom_depth32 == reference.pom_depth32,
            "POM material sampling correspondence changed depth");
  }
  std::printf("pom_inverse_chart_color_normal_correspondence pass\n");
}

void atlas_and_finite_fallback(vk::Renderer &renderer) {
  std::array<double, 3> addressed_u{};
  unsigned address_index{};
  for (auto address : {mat::surface_address_wrap, mat::surface_address_mirror,
                       mat::surface_address_clamp}) {
    auto test = fixture(Route::tl, Height::atlas, .04f, .5f, std::sqrt(.5),
                         {1, 1}, {0, 0}, {1, 1}, false, address, std::nullopt, true);
    renderer.render(test.scene);
    compare_uv(decode(test.scene), expected(test, Height::atlas), "POM atlas taps crossed the neighbor tile");
    // Keep all three address-policy expectations separated by more than two
    // error bounds, so substituting mirror/clamp cannot satisfy both oracles.
    auto ramp = fixture(Route::tl, Height::atlas_ramp, .02f, .5f, std::sqrt(.5),
                         {1, 1}, {.035f, 0}, {1, 1}, false, address, std::nullopt, true);
    renderer.render(ramp.scene);
    const auto wanted = expected(ramp, Height::atlas_ramp);
    addressed_u[address_index++] = wanted[0];
    compare_uv(decode(ramp.scene), wanted,
                "POM atlas wrap/mirror/clamp addressed the wrong height", 1e-4);
  }
  for (unsigned a = 0; a < addressed_u.size(); ++a)
    for (unsigned b = a + 1; b < addressed_u.size(); ++b)
      require(std::abs(addressed_u[a] - addressed_u[b]) > 2e-4,
              "POM atlas address-policy oracle intervals overlap");
  auto grazing = fixture(Route::tl, Height::constant, .04f, .5f, .05);
  renderer.render(grazing.scene);
  compare_uv(decode(grazing.scene), {.5, .5}, "POM grazing fallback is not finite/original");
  auto degenerate = fixture(Route::tl, Height::constant);
  for (unsigned i = 0; i < 6; ++i) {
    platform::TLVertex vertex;
    std::memcpy(&vertex, degenerate.scene.vertices.data() + i * sizeof(vertex), sizeof(vertex));
    vertex.tu = vertex.tv = .5f;
    std::memcpy(degenerate.scene.vertices.data() + i * sizeof(vertex), &vertex, sizeof(vertex));
  }
  renderer.render(degenerate.scene);
  compare_uv(decode(degenerate.scene), {.5, .5}, "POM singular chart did not preserve base UV");
  auto nonfinite = fixture(Route::tl, Height::constant);
  nonfinite.scene.draws[0].lit_normals =
      std::make_shared<const std::vector<std::array<float, 3>>>(6,
          std::array<float, 3>{std::numeric_limits<float>::quiet_NaN(), 0, 0});
  renderer.render(nonfinite.scene);
  compare_uv(decode(nonfinite.scene), {.5, .5}, "POM nonfinite normal fallback");
  for (unsigned invalid = 0; invalid < 7; ++invalid) {
    auto test = fixture(Route::tl, Height::constant);
    auto snapshot = std::make_shared<mat::HeightBinding>(*test.scene.draws[0].height_binding);
    if (invalid == 0) snapshot->material.uv_scale[0] = 0;
    if (invalid == 1) snapshot->material.address_mode_u = 0;
    if (invalid == 2) snapshot->material.atlas_rect[2] = 1.f / 32;
    if (invalid == 3) snapshot->normal_width = 31;
    if (invalid == 4) test.scene.draws[0].surface_eye = {};
    if (invalid == 5) snapshot->material.uv_scale[1] = std::numeric_limits<float>::infinity();
    if (invalid == 6) snapshot->material.uv_scale[1] = 1e-30f;
    test.scene.draws[0].height_binding = snapshot;
    bool rejected{};
    try { renderer.render(test.scene); } catch (const std::runtime_error &) { rejected = true; }
    require(rejected, "POM admitted an invalid chart/dimension/eye");
  }
  std::printf("pom_atlas_and_finite_fallback pass\n");
}

void descriptor_identity_and_mixed_draws(vk::Renderer &renderer, vk::Renderer &uncombined) {
  auto first = fixture(Route::tl, Height::constant, .04f, 0, .3);
  auto second = fixture(Route::tl, Height::ramp_u, -.04f, 1, .3, {-1, 1}, {1, 0});
  auto left = first.scene;
  auto right = second.scene;
  renderer.render(left); renderer.render(right);
  auto mixed = first.scene;
  const auto second_draw = second.scene.draws[0];
  mixed.vertices.insert(mixed.vertices.end(), second.scene.vertices.begin(), second.scene.vertices.end());
  mixed.draws.push_back(second_draw);
  mixed.draws[1].first = 6;
  mixed.draws[0].scissor = {{0, 0}, {16, 32}};
  mixed.draws[1].scissor = {{16, 0}, {16, 32}};
  mixed.order.push_back({false, 1});
  renderer.render(mixed);
  for (unsigned y = 4; y < 28; ++y)
    for (unsigned x : {15U, 16U}) {
      const auto &reference = x < 16 ? left : right;
      for (unsigned channel = 0; channel < 4; ++channel)
        require(mixed.pom_rgba8[(y * 32 + x) * 4 + channel] ==
                    reference.pom_rgba8[(y * 32 + x) * 4 + channel],
                "POM adjacent draw inherited a different descriptor/uniform");
    }
  require(decode(left) != decode(right), "POM mixed-draw controls do not distinguish their heights");
  // Equal scissors are essential: the earlier split-scissor control cannot
  // enter same_tl even if all height-sensitive merge comparisons are removed.
  // These translated planes occupy disjoint screen regions while retaining
  // identical pipeline, albedo, push constants and full-target scissors.
  auto merge_left = fixture(Route::tl, Height::zero, .2f, .5f, .7,
      {1, 1}, {0, 0}, {.5, .5}, false, mat::surface_address_wrap,
      std::nullopt, true, {-2, 0, 0});
  auto merge_right = fixture(Route::tl, Height::one, .2f, .5f, .7,
      {1, 1}, {0, 0}, {.5, .5}, false, mat::surface_address_wrap,
      std::nullopt, true, {2, 0, 0});
  auto wrong_right = fixture(Route::tl, Height::zero, .2f, .5f, .7,
      {1, 1}, {0, 0}, {.5, .5}, false, mat::surface_address_wrap,
      std::nullopt, true, {2, 0, 0});
  auto merge_scene = merge_left.scene;
  merge_scene.vertices.insert(merge_scene.vertices.end(), merge_right.scene.vertices.begin(),
                              merge_right.scene.vertices.end());
  merge_scene.draws.push_back(merge_right.scene.draws[0]);
  merge_scene.draws[1].first = merge_scene.draws[0].count;
  merge_scene.order.push_back({false, 1});
  const auto &left_draw = merge_scene.draws[0];
  const auto &right_draw = merge_scene.draws[1];
  require(!left_draw.model && !right_draw.model && left_draw.count == 6 && right_draw.count == 6 &&
              left_draw.first + left_draw.count == right_draw.first &&
              left_draw.key.packed() == right_draw.key.packed() &&
              left_draw.texture == right_draw.texture && left_draw.sampler == right_draw.sampler &&
              std::memcmp(&left_draw.push, &right_draw.push, sizeof(left_draw.push)) == 0 &&
              std::memcmp(&left_draw.scissor, &right_draw.scissor, sizeof(VkRect2D)) == 0 &&
              !mat::same_height_binding(left_draw.height_binding, right_draw.height_binding),
          "POM merge fixture does not isolate adjacent same-scissor height state");
  uncombined.render(merge_left.scene);
  uncombined.render(merge_right.scene);
  uncombined.render(wrong_right.scene);
  const auto correct_uv = decode(merge_right.scene, 20, 16);
  const auto wrong_uv = decode(wrong_right.scene, 20, 16);
  require(std::abs(correct_uv[0] - wrong_uv[0]) > .003 ||
              std::abs(correct_uv[1] - wrong_uv[1]) > .003,
          "POM same-scissor merge control cannot detect an inherited height");
  auto no_combine = merge_scene;
  uncombined.render(no_combine);
  renderer.render(merge_scene);
  require(merge_scene.pom_rgba8 == no_combine.pom_rgba8 &&
              merge_scene.pom_depth32 == no_combine.pom_depth32,
          "POM TL combine changed mixed-height readback");
  for (unsigned y : {15U, 16U, 17U})
    for (unsigned x : {11U, 12U, 13U, 19U, 20U}) {
      const auto &oracle = x < 16 ? merge_left.scene : merge_right.scene;
      const auto pixel = y * 32 + x;
      require(oracle.pom_depth32.size() == 32 * 32 &&
                  oracle.pom_depth32[pixel] > 0 && oracle.pom_depth32[pixel] < 1,
              "POM merge comparison pixel is not covered by its independent draw");
      for (unsigned channel = 0; channel < 4; ++channel)
        require(merge_scene.pom_rgba8[pixel * 4 + channel] ==
                    oracle.pom_rgba8[pixel * 4 + channel],
                "POM same-scissor TL merge inherited another height descriptor/uniform");
      require(merge_scene.pom_depth32[pixel] == oracle.pom_depth32[pixel],
              "POM same-scissor TL merge changed independent draw depth");
    }
  for (unsigned invalid = 0; invalid < 7; ++invalid) {
    auto test = first.scene;
    auto snapshot = std::make_shared<mat::HeightBinding>(*test.draws[0].height_binding);
    if (invalid == 0) snapshot->albedo.hash ^= 1;
    if (invalid == 1) ++snapshot->texture_version;
    if (invalid == 2) snapshot->normal_hash ^= 1;
    if (invalid == 3) snapshot->source_sha256.clear();
    if (invalid == 4) snapshot->producer_epoch = 0;
    if (invalid == 5) snapshot->texture_version = 0;
    if (invalid == 6) snapshot->image_version = 2;
    test.draws[0].height_binding = snapshot;
    bool rejected{};
    try { renderer.render(test); } catch (const std::runtime_error &) { rejected = true; }
    require(rejected, "POM ignored a wrong immutable source key/version");
  }
  std::printf("pom_descriptor_identity_and_mixed_draws pass\n");
}

void immutable_height_reuse_across_admission_stamps(vk::Renderer &renderer) {
  auto source = fixture(Route::tl, Height::ramp_u, .08f, .1f, .7);
  const auto immutable = source.scene.draws[0].height_binding;
  const auto payload_bytes = immutable->image->pixels.size() * sizeof(std::uint32_t);
  require(payload_bytes == 4096, "POM shared height fixture has an unexpected size");
  const auto uploads = renderer.height_uploads;
  const auto uploaded_bytes = renderer.height_uploaded_bytes;
  const auto hits = renderer.height_cache_hits;
  std::vector<std::shared_ptr<const mat::HeightBinding>> retained_snapshots;
  std::vector<unsigned char> expected_pixels;
  std::vector<float> expected_depth;
  // Every render starts from identical pristine color/depth. Only the admitted
  // albedo upload stamp changes; source pixels and the immutable pack stay live.
  for (std::uint64_t version = 1; version <= 5; ++version) {
    auto scene = source.scene;
    auto snapshot = std::make_shared<mat::HeightBinding>(*immutable);
    snapshot->texture_version = version;
    require(snapshot->image == immutable->image &&
                !snapshot->image.owner_before(immutable->image) &&
                !immutable->image.owner_before(snapshot->image),
            "POM stamp fixture changed its immutable payload owner");
    scene.textures[0].hash = version;
    scene.draws[0].height_binding = snapshot;
    retained_snapshots.push_back(snapshot);
    renderer.render(scene); // Readback settles the scene before the next version.
    compare_uv(decode(scene), expected(source, Height::ramp_u),
                "POM albedo version changed immutable height displacement");
    if (version == 1) {
      expected_pixels = scene.pom_rgba8;
      expected_depth = scene.pom_depth32;
    }
    require(scene.pom_rgba8 == expected_pixels && scene.pom_depth32 == expected_depth,
            "POM albedo version changed exact height readback");
  }
  std::printf("pom_shared_height_versions uploads=%llu bytes=%llu versions=5\n",
      static_cast<unsigned long long>(renderer.height_uploads - uploads),
      static_cast<unsigned long long>(renderer.height_uploaded_bytes - uploaded_bytes));
  require(renderer.height_uploads == uploads + 1 &&
              renderer.height_uploaded_bytes == uploaded_bytes + payload_bytes,
          "POM immutable height payload reuploaded for an albedo version");
  for (std::uint64_t epoch = 2; epoch <= 5; ++epoch) {
    auto scene = source.scene;
    auto snapshot = std::make_shared<mat::HeightBinding>(*immutable);
    snapshot->texture_version = 5;
    snapshot->producer_epoch = epoch;
    scene.textures[0].hash = 5;
    scene.draws[0].height_binding = snapshot;
    retained_snapshots.push_back(snapshot);
    renderer.render(scene);
    require(scene.pom_rgba8 == expected_pixels && scene.pom_depth32 == expected_depth,
            "POM producer epoch changed immutable height readback");
  }
  require(renderer.height_uploads == uploads + 1 && renderer.height_cache_hits >= hits + 8,
          "POM producer epoch duplicated an immutable height payload");
  auto shared = source.scene;
  auto first = std::make_shared<mat::HeightBinding>(*immutable);
  auto second = std::make_shared<mat::HeightBinding>(*immutable);
  first->texture_version = 11;
  second->texture_version = 12;
  second->producer_epoch = 19;
  shared.textures[0].hash = 11;
  auto second_albedo = shared.textures[0];
  second_albedo.key = 3;
  second_albedo.hash = 12;
  shared.textures.push_back(std::move(second_albedo));
  shared.draws[0].height_binding = first;
  shared.draws.push_back(shared.draws[0]);
  shared.draws[1].texture = 2;
  shared.draws[1].height_binding = second;
  shared.draws[0].scissor = {{0, 0}, {16, 32}};
  shared.draws[1].scissor = {{16, 0}, {16, 32}};
  shared.order.push_back({false, 1});
  renderer.render(shared);
  require(shared.pom_rgba8 == expected_pixels && shared.pom_depth32 == expected_depth &&
              renderer.height_uploads == uploads + 1 &&
              renderer.height_uploaded_bytes == uploaded_bytes + payload_bytes,
          "POM same-frame albedo contexts duplicated or changed shared height");
  auto other_owner = fixture(Route::tl, Height::ramp_u, .08f, .1f, .7);
  require(other_owner.scene.draws[0].height_binding->image != immutable->image,
          "POM distinct-owner control accidentally reused its decoded image");
  renderer.render(other_owner.scene);
  require(renderer.height_uploads == uploads + 2 &&
              other_owner.scene.pom_rgba8 == expected_pixels &&
              other_owner.scene.pom_depth32 == expected_depth,
          "POM distinct immutable owner failed to upload its payload");
  auto other_content = fixture(Route::tl, Height::one, .08f, .1f, .7);
  renderer.render(other_content.scene);
  compare_uv(decode(other_content.scene), expected(other_content, Height::one),
              "POM replacement content lost its independent displacement");
  require(renderer.height_uploads == uploads + 3 &&
              renderer.height_uploaded_bytes == uploaded_bytes + 3 * payload_bytes &&
              other_content.scene.pom_rgba8 != expected_pixels,
          "POM changed immutable height content failed to upload a new payload");
  std::printf("pom_immutable_height_reuse_across_admission_stamps pass\n");
}

// #496: a parallax draw whose albedo or normal texture didn't fit in video
// memory draws with a white stand-in and no parallax for that frame, instead of
// failing the height check, and gets its parallax back once the texture fits.
void parallax_stand_in_while_texture_waits(vk::Renderer &renderer) {
  auto reference = fixture(Route::tl, Height::ramp_u, .08f, .1f, .7);
  renderer.render(reference.scene);
  const auto reference_uv = decode(reference.scene);
  // The same textures under keys the renderer hasn't seen, so it must create
  // their images now; the height check compares content, not keys.
  auto with_new_keys = [] {
    auto moved = fixture(Route::tl, Height::ramp_u, .08f, .1f, .7);
    for (auto &texture : moved.scene.textures)
      texture.key += 0x4960000000000000ULL;
    return moved;
  };
  vk::PreloadFaultInjection fault{};
  fault.fail_next_play_texture_allocations = 2;
  fault.injected_result = VK_ERROR_OUT_OF_DEVICE_MEMORY;
  renderer.set_preload_fault(fault);
  auto waiting = with_new_keys();
  renderer.render(waiting.scene);
  require(!waiting.scene.draws[0].height_binding,
          "POM draw with a stand-in texture kept its height binding");
  renderer.set_preload_fault({});
  auto returned = with_new_keys();
  renderer.render(returned.scene);
  require(decode(returned.scene) == reference_uv,
          "POM did not return once the waiting texture fit again");
  std::printf("pom_stand_in_while_texture_waits pass\n");
}
void height_replacement_and_queued_retirement(vk::Renderer &renderer) {
  auto old = fixture(Route::tl, Height::constant, .04f, 0, .3);
  auto replacement = fixture(Route::tl, Height::ramp_u, .04f, 0, .3);
  auto queued = old.scene;
  renderer.render(old.scene);
  const auto old_uv = decode(old.scene);
  const auto old_depth = old.scene.depth;
  const auto uploads = renderer.height_uploads;
  const auto charged = old.budget->used();
  renderer.render(queued);
  require(decode(queued) == old_uv && renderer.height_uploads == uploads &&
              old.budget->used() == charged, "POM cache hit decoded/recharged/reuploaded height");
  renderer.render(replacement.scene);
  require(decode(replacement.scene) != old_uv, "POM replacement reused the old height image");
  // Submitted commands retain Vulkan storage through the fence. The cache
  // keeps only weak CPU ownership, so the final queued owner returns its budget.
  queued.pom_raw_readback = false;
  queued.pom_diagnostic_mode = 0;
  renderer.render(queued, true, false);
  auto budget = old.budget;
  old.scene = {}; queued = {};
  require(budget->used() == 0, "POM GPU cache retained the producer's decoded reservation");
  const auto retired = renderer.height_retired_images;
  renderer.render(replacement.scene);
  require(renderer.height_retired_images > retired && replacement.scene.depth == old_depth,
          "POM queued height image did not retire after its fence");
  std::printf("pom_height_replacement_and_queued_retirement pass\n");
}
} // namespace pom_checks

void check_parallax(SDL_Window *window, sdlfe::RendererBackend backend) {
  using namespace pom_checks;
  require(backend == sdlfe::RendererBackend::core_critical_wsi,
          "POM qualification requires the explicit --wsi SDL surface harness");
  uniform_layout_and_rgba16_roundtrip();
  auto tracker = std::make_shared<cc_mw3_re::platform::SdlWindowStateTracker>(window);
  tracker->sample_owner();
  const auto snapshot = tracker->current_state();
  const auto native = cc_mw3_re::platform::get_window_native_handle(window);
  const auto extensions = cc_mw3_re::platform::get_instance_extensions();
  std::atomic<unsigned> created{};
  auto source = [&] {
    vk::Renderer::WindowSurface surface;
    surface.extensions = extensions;
    surface.create = [&](VkInstance instance) {
      ++created;
      return cc_mw3_re::platform::create_surface(window, instance);
    };
    surface.destroy = cc_mw3_re::platform::destroy_surface;
    surface.is_visible = [tracker](auto) { return tracker->worker_visible(); };
    surface.get_drawable_size = [snapshot](auto, long *width, long *height) {
      if (width) *width = snapshot.drawable_width;
      if (height) *height = snapshot.drawable_height;
    };
    return surface;
  };
  auto run = [&] {
    cc_mw3_re::platform::SdlWindowStateScope scope(tracker.get(), snapshot);
    mw34::sun::Settings settings;
    settings.enabled = settings.normals = true;
    cc_mw3_re::RendererBridgeConfig config;
    config.dxgi_present = false;
    config.parallax_materials = true;
    config.tl_combine = true;
    require(config.tl_combine, "POM merge qualification requires TL combine enabled");
    vk::Renderer renderer(vk::Renderer::ColorTarget::rgba8, source(),
        {1, 1, 1, false}, true, settings, true, config);
    config.parallax_materials = false;
    vk::Renderer disabled(vk::Renderer::ColorTarget::rgba8, source(),
        {1, 1, 1, false}, true, settings, true, config);
    auto uncombined_config = config;
    uncombined_config.parallax_materials = true;
    uncombined_config.tl_combine = false;
    vk::Renderer uncombined(vk::Renderer::ColorTarget::rgba8, source(),
        {1, 1, 1, false}, true, settings, true, uncombined_config);
    require(renderer.max_texture_dimension(native) >= 64 &&
                disabled.max_texture_dimension(native) >= 64 &&
                uncombined.max_texture_dimension(native) >= 64,
            "POM authored textures exceed the selected WSI device");
    off_and_zero_amplitude_identity(renderer, disabled);
    per_draw_eye_affine_oracle(renderer, disabled);
    constant_and_ramp_signed_uv(renderer);
    inverse_chart_color_normal_correspondence(renderer);
    atlas_and_finite_fallback(renderer);
    descriptor_identity_and_mixed_draws(renderer, uncombined);
    immutable_height_reuse_across_admission_stamps(renderer);
    height_replacement_and_queued_retirement(renderer);
    parallax_stand_in_while_texture_waits(renderer);
    for (const auto quality : {vk::Renderer::Quality{1, 1, 16, true},
                               vk::Renderer::Quality{2, 1, 16, false},
                               vk::Renderer::Quality{2, 2, 16, false}}) {
      auto quality_config = config;
      quality_config.parallax_materials = true;
      vk::Renderer quality_renderer(vk::Renderer::ColorTarget::rgba8, source(), quality,
                                     true, settings, true, quality_config);
      require(quality_renderer.max_texture_dimension(native) >= 32,
              "POM AA fixture cannot select its WSI device");
      for (auto route : {Route::model, Route::world, Route::tl, Route::native}) {
        auto normal_only = fixture(route, Height::constant);
        normal_only.scene.pom_diagnostic_mode = 0;
        normal_only.scene.pom_raw_readback = false;
        normal_only.scene.draws[0].height_binding.reset();
        normal_only.scene.draws[0].sampler |= 0x10000U;
        quality_renderer.render(normal_only.scene);
        auto zero = fixture(route, Height::ramp_u, 0);
        zero.scene.pom_diagnostic_mode = 0;
        zero.scene.pom_raw_readback = false;
        zero.scene.draws[0].sampler |= 0x10000U;
        quality_renderer.render(zero.scene);
        require(normal_only.scene.color == zero.scene.color &&
                    normal_only.scene.depth == zero.scene.depth && quality_renderer.height_uploads == 0,
                "POM A==0 changed FXAA/SSAA/AF color or depth, or uploaded height");
      }
    }
    std::printf("pom_aa_off_zero_identity pass\n");
  };
  if (threaded_checks) {
    std::exception_ptr failure;
    std::thread worker([&] { try { run(); } catch (...) { failure = std::current_exception(); } });
    worker.join();
    if (failure) std::rethrow_exception(failure);
  } else run();
  require(created == 6, "POM qualification did not select its six actual SDL WSI devices");
}
