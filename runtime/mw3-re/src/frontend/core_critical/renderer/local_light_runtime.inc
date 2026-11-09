// Producer-owned local light state; packets receive only the fixed Uniform.
mw34::effects::Catalog local_catalog_;
mw34::effects::ObservedLights local_observed_;
std::vector<mw34::effects::Candidate> local_native_;
std::vector<mw34::headlights::StockProfile> headlight_catalog_;
std::vector<mw34::effects::Candidate> headlight_candidates_;
mw34::headlights::PlayerState headlight_player_;
unsigned headlight_key_{};
std::size_t headlight_peak_{};
std::array<float, 6> local_projection_{};
std::array<float, 12> local_camera_{};
bool local_active_{};
double local_time_{};
std::uint64_t local_observations_{}, local_native_peak_{}, local_packet_peak_{};

void local_lights_load() {
  if (!bridge_config_.effect_lights) {
    if (bridge_config_.mech_headlights)
      fprintf(stderr, "[HEADLIGHTS] inactive: local lights disabled\n");
    return;
  }
  VisualFloatScope guard;
  if (!lighting_.enabled || bridge_config_.effect_light_catalog.empty())
    throw std::runtime_error("Local lights require lighting and a catalog");
  std::ifstream stream(
      std::filesystem::u8path(bridge_config_.effect_light_catalog),
      std::ios::binary);
  if (!stream)
    throw std::runtime_error("effect light catalog missing");
  local_catalog_ = mw34::effects::read_catalog(stream);
  if (!bridge_config_.mech_headlights)
    return;
  if (bridge_config_.stock_headlights.empty()) {
    fprintf(stderr, "[HEADLIGHTS] inactive: no stock catalog selected\n");
    return;
  }
  std::ifstream catalog(std::filesystem::u8path(bridge_config_.stock_headlights),
                        std::ios::binary);
  if (!catalog)
    throw std::runtime_error("Headlights: cannot open stock catalog");
  headlight_catalog_ = mw34::headlights::read_stock_catalog(catalog);
  if (bridge_config_.headlight_bindings.empty()) {
    fprintf(stderr, "[HEADLIGHTS] inactive: no input binding selected\n");
    return;
  }
  std::ifstream bindings(std::filesystem::u8path(bridge_config_.headlight_bindings));
  std::string magic, extra;
  int button = -1;
  if (!(bindings >> magic >> headlight_key_ >> button) ||
      magic != "CC_MW3_HEADLIGHTS_V1" || headlight_key_ >= zin::kKeys ||
      (headlight_key_ && !(headlight_key_ & 255)) || button < -1 || button > 25 ||
      (bindings >> extra))
    throw std::runtime_error("Headlights: invalid input binding");
  const auto scan = headlight_key_ & 255;
  if (scan == 0x43 || scan == 0x44 || scan == 0x57)
    throw std::runtime_error("Headlights: key reserved for capture/replay");
  if (!headlight_key_ || headlight_catalog_.empty())
    fprintf(stderr, "[HEADLIGHTS] inactive: no keyboard binding or stock profile\n");
}

bool wants_player_headlight_ticks() const override {
  return headlight_key_ && !headlight_catalog_.empty() && !current_mission_id_.empty();
}

void player_headlight_tick(const ::platform::PlayerHeadlightTick &tick) override {
  VisualFloatScope guard;
  headlight_candidates_.clear();
  const auto *node = static_cast<const zcls::Node *>(tick.node);
  const auto *asset = node && node->source_asset_root ? node->source_asset.get() : nullptr;
  const auto *profile = asset ? mw34::headlights::match_original(
      headlight_catalog_, asset->name, asset->member_sha256) : nullptr;
  const auto &input = zin::state();
  const auto key = zin::key_state(headlight_key_);
  const bool pressed = (key & (zin::kPressed | zin::kHeld)) && !(key & zin::kReleased) &&
                       input.modifiers == (headlight_key_ & 0x700);
  headlight_player_.update(tick.generation, reinterpret_cast<std::uintptr_t>(node),
                           tick.tick, std::max(0.0f, tick.dt), tick.shutdown, pressed,
                           profile && tick.dt >= 0 && input.kbd_ready && !input.char_callback);
  const auto intensity = headlight_player_.owner.envelope.current;
  if (!profile || intensity <= 0)
    return;
  zmth::Mat34 world;
  zmth::push(&world);
  zmth::load_identity();
  const auto transformed = zcls::node_to_world(const_cast<zcls::Node *>(node), 1);
  zmth::pop();
  if (transformed)
    return;
  ::platform::ModelDrawContext context{};
  context.node = node;
  context.model_to_world = world.m;
  context.ordinary = true;
  for (std::size_t i = 0; i < profile->lamps.size(); ++i) {
    const auto &lamp = profile->lamps[i];
    if (headlight_player_.owner.retired_emitters.count(lamp.id))
      continue;
    std::vector<std::uintptr_t> ancestry;
    const auto pose = original_headlight_socket(context, lamp.attachment, &ancestry);
    if (!pose)
      continue;
    if (context.ordinary && !ancestry.empty()) {
      headlight_player_.owner.source_ancestry[lamp.id] = std::move(ancestry);
    }
    // Native fixture IDs occupy the low range, while weapons have a separate namespace.
    if (auto candidate = mw34::headlights::spotlight(lamp, *pose, intensity, (1ULL << 63) + i))
      headlight_candidates_.push_back(*candidate);
  }
  headlight_peak_ = std::max(headlight_peak_, headlight_candidates_.size());
}

void retire_headlight_node(std::uintptr_t node) override {
  headlight_player_.owner.retire_node(node, headlight_player_.owner.generation);
}

void local_lights_clear() {
  headlight_player_ = {};
  headlight_candidates_.clear();
  local_observed_.clear();
  local_native_.clear();
  local_active_ = false;
  local_camera_ = {};
  local_projection_ = {};
  local_time_ = 0.0;
}

void local_lights_begin() {
  local_active_ = false;
  local_native_.clear();
  if (!bridge_config_.effect_lights || current_mission_id_.empty())
    return;
  VisualFloatScope guard;
  const auto p = zmth::projection();
  local_projection_ = {p.near_z, p.fx_near, p.fy_near, p.cx, p.cy, p.far_z};
  if (!std::isfinite(local_projection_[0]) ||
      !std::isfinite(local_projection_[1]) ||
      !std::isfinite(local_projection_[2]) ||
      !std::isfinite(local_projection_[3]) ||
      !std::isfinite(local_projection_[4]) ||
      !std::isfinite(local_projection_[5]))
    throw std::runtime_error("Local lights: non-finite projection");
  if (local_projection_[0] <= 0.0f || local_projection_[1] <= 0.0f ||
      local_projection_[2] <= 0.0f || local_projection_[5] <= 0.0f)
    throw std::runtime_error("Local lights: invalid projection");
  const float *m = zmth::view().camera.m;
  local_camera_ = {m[0], m[3],  m[6], m[9], m[1], m[4],
                   m[7], m[10], m[2], m[5], m[8], m[11]};
  for (float v : local_camera_)
    if (!std::isfinite(v))
      throw std::runtime_error("Local lights: invalid camera");
  local_time_ = ztimer::state().total_scaled;
  if (!std::isfinite(local_time_) || local_time_ < 0.0)
    throw std::runtime_error("Local lights: invalid time");
  if (bridge_config_.fixture_lights) {
    local_native_ = mw34::effects::collect_native_lights(zmod::light_list());
    local_native_peak_ = std::max(local_native_peak_,
                                  static_cast<uint64_t>(local_native_.size()));
  }
  local_active_ = true;
}

void local_lights_observe(const TLVertex *vertices, int count,
                          const DrawState &state) {
  if (!bridge_config_.effect_lights || !local_active_ || state.sharp ||
      state.texture < 0 ||
      state.texture >= static_cast<int>(textures_.size()) || count <= 0) {
    return;
  }
  auto it = local_catalog_.find(textures_[state.texture].surface_key);
  if (it == local_catalog_.end()) {
    return;
  }
  if (!vertices || count > 1024) {
    throw std::runtime_error("local_lights_observe: invalid vertex buffer");
  }
  VisualFloatScope guard;
  std::vector<mw34::effects::Point> points;
  points.reserve(static_cast<size_t>(count));
  for (int i = 0; i < count; ++i) {
    points.push_back(mw34::effects::reconstruct(
        vertices[i].sx, vertices[i].sy, vertices[i].sz, local_projection_,
        local_camera_));
  }
  local_observed_.observe(it->second, points, local_time_);
  ++local_observations_;
}

void local_lights_attach(vk::Scene &target) {
  target.effect_lights = {};
  if (!bridge_config_.effect_lights || !local_active_ || target.hud ||
      target.frontend_canvas) {
    return;
  }
  VisualFloatScope guard;
  std::vector<mw34::effects::Candidate> sources = local_native_;
  auto candidates = local_observed_.candidates(local_time_);
  sources.insert(sources.end(), headlight_candidates_.begin(), headlight_candidates_.end());
  // Keep within the ranker's 384-source cap without unsigned wraparound.
  const std::size_t room = sources.size() < 384 ? 384 - sources.size() : 0;
  const auto observed_count = std::min(candidates.size(), room);
  sources.insert(sources.end(), candidates.begin(), candidates.begin() + observed_count);
  mw34::effects::Point eye = {local_camera_[3], local_camera_[7],
                              local_camera_[11]};
  target.effect_lights = mw34::effects::rank_frame_lights(sources, eye, 64, 16);
  local_packet_peak_ =
      std::max(local_packet_peak_,
               static_cast<std::uint64_t>(target.effect_lights.params[0]));
}

void local_lights_report() {
  if (!bridge_config_.effect_lights) {
    return;
  }
  fprintf(
      stderr,
      "[LOCAL_LIGHTS] observations=%llu native_peak=%llu packet_peak=%llu\n",
      static_cast<unsigned long long>(local_observations_),
      static_cast<unsigned long long>(local_native_peak_),
      static_cast<unsigned long long>(local_packet_peak_));
  if (bridge_config_.mech_headlights)
    fprintf(stderr, "[HEADLIGHTS] candidate_peak=%zu\n", headlight_peak_);
}
