public:
void flush() override {
    // Abandoned CPU prefixes must never be submitted by drain/present/destruct.
    if (producer_failed_) return;
    if (scene_.order.empty()) {
        if (!scene_.draws.empty() || !scene_.clears.empty() ||
            !scene_.vertices.empty())
          throw std::runtime_error(
              "Command-empty producer Scene retains draw or clear work");
        // A wholly clipped producer may bind resources without emitting a
        // command. No packet owns those references, so discard them before a
        // texture update/release while retaining this view's other state.
        scene_.textures.clear();
        invalidate_scene_bindings();
        return;
    }
    if (!local_active_)
      local_lights_attach(scene_);
    CpuInterval interval(cpu_profile_ ? &render_ticks_ : nullptr);
    if (cpu_profile_)
        ++render_calls_;
    const bool initialize = scene_.width != resident_width_ || scene_.height != resident_height_;
    if (initialize) {
        const auto size = std::size_t(scene_.width) * scene_.height;
        scene_.color.assign(size, 0);
        scene_.depth.assign(size, 0);
    }
    // Validate before moving the scene or advancing upload/extent receipts.
    // A rejected submission retains all payloads for a consistent retry.
    (void)packet_height_bytes(scene_);
    std::size_t local_bytes = 0;
    if (local_active_) {
      // Compute the byte terms once per flush; the total is checked for overflow.
      const auto terms = packet_byte_terms(scene_);
      local_bytes = checked_packet_total(terms);
      if (staging_first_flush_pending_) {
        // First local-light flush after a mission change: whatever is still pending now would
        // be carried over from before the change. Record it and name the terms of this first
        // packet once, so a log shows what this mission's first frame is made of.
        staging_first_flush_pending_ = false;
        staging_first_flush_bytes_ = pending_local_bytes_;
        staging_first_flush_packets_ = pending_local_packets_.size();
        std::fprintf(stderr,
                     "Local light staging first flush after mission change: pending packets=%zu "
                     "pending_bytes=%zu recycled_scenes=%zu; first packet total=%zu scene=%zu "
                     "vertices=%zu color_depth=%zu draws=%zu order=%zu textures=%zu "
                     "texture_pixels=%zu geometry=%zu lit_normals=%zu height=%zu emissions=%zu "
                     "clears=%zu budget=%zu\n",
                     staging_first_flush_packets_, staging_first_flush_bytes_,
                     recycled_scene_count_for_test(), local_bytes, terms.scene, terms.vertices,
                     terms.color_depth, terms.draws, terms.order, terms.textures,
                     terms.texture_pixels, terms.geometry, terms.lit_normals,
                     terms.height_metadata + terms.height_packet, terms.emissions, terms.clears,
                     local_staging_budget_);
      }
      // A single packet that could never fit even an EMPTY staging area is a real invariant
      // failure: reject it before submitting any earlier packet.
      if (!staging::fits(local_bytes, 0, local_staging_budget_))
        throw std::runtime_error("Local light packet staging exceeds budget");
      if (!staging::fits(local_bytes, pending_local_bytes_, local_staging_budget_) &&
          !pending_local_packets_.empty()) {
        // The CPU staging area is full of earlier packets of this scene. Submit them now
        // with the local lights known so far (the same operation housekeeping performs
        // after a flush) instead of ending the game: packets stay in producer order, only
        // the lights attached to the earlier packets can be slightly older.
        const std::size_t early_packets = pending_local_packets_.size();
        const std::size_t early_pending_bytes = pending_local_bytes_;
        complete_local_light_packets();
        ++staging_early_completions_;
        if (!staging_early_logged_) {
          staging_early_logged_ = true;
          ++staging_early_log_lines_;
          std::fprintf(stderr,
                       "Local light staging: early completion packets=%zu pending_bytes=%zu "
                       "next_packet_bytes=%zu budget=%zu (earlier packets use the lights "
                       "known so far); next packet terms: scene=%zu vertices=%zu "
                       "color_depth=%zu draws=%zu order=%zu textures=%zu texture_pixels=%zu "
                       "emissions=%zu geometry=%zu lit_normals=%zu height_metadata=%zu "
                       "clears=%zu height_packet=%zu (capacity based)\n",
                       early_packets, early_pending_bytes, local_bytes, local_staging_budget_,
                       terms.scene, terms.vertices, terms.color_depth, terms.draws,
                       terms.order, terms.textures, terms.texture_pixels, terms.emissions,
                       terms.geometry, terms.lit_normals, terms.height_metadata,
                       terms.clears, terms.height_packet);
        }
      }
      // After any early completion the packet must fit the (now empty or smaller) area.
      if (!staging::fits(local_bytes, pending_local_bytes_, local_staging_budget_))
        throw std::runtime_error("Local light packet staging exceeds budget");
      if (worker_)
        for (const auto &draw : scene_.draws)
          if (draw.shadow_valid)
            throw std::runtime_error(
                "Render packet contains a live shadow callback");
    }
    std::uint64_t packet_id = 0;
    if (producer_observer_) {
      if (producer_packet_id_ == std::numeric_limits<std::uint64_t>::max())
        throw std::runtime_error("Producer packet observation identity exhausted");
      packet_id = ++producer_packet_id_;
      observe_producer_packet(scene_, packet_id, local_active_);
    }
    resident_width_ = scene_.width;
    resident_height_ = scene_.height;
    // Track the last ordered upload, not the worker's mutable Vulkan cache.
    // Every omitted payload refers to an earlier packet on this same queue.
    for (const auto &texture : scene_.textures)
        submitted_textures_[texture.key] = {texture.hash, texture.width, texture.height};
    if (local_active_) {
      auto packet = std::make_shared<vk::Scene>(std::move(scene_));
      pending_local_packets_.push_back(
          PendingLocalPacket{std::move(packet), initialize, local_bytes, packet_id});
      pending_local_bytes_ += local_bytes;
      if (pending_local_bytes_ > staging_peak_bytes_)
        staging_peak_bytes_ = pending_local_bytes_;
      scene_ = {};
      std::lock_guard<std::mutex> lock(recycle_mutex_);
      if (!recycled_scenes_.empty()) {
        scene_ = std::move(recycled_scenes_.back());
        recycled_scenes_.pop_back();
      }
      invalidate_scene_bindings();
      return;
    }
    if (worker_) {
        for (const auto &draw : scene_.draws)
            if (draw.shadow_valid)
                throw std::runtime_error("Render packet contains a live shadow callback");
        auto packet = std::make_shared<vk::Scene>(std::move(scene_));
        const auto bytes = packet_bytes(*packet);
        worker_->post(
            [this, packet, initialize, packet_id] {
                {
                    CpuInterval interval(cpu_profile_ ? &worker_render_ticks_ : nullptr);
                    observe_worker_packet(*packet, packet_id);
                    renderer_->render(*packet, initialize, false);
                }
                recycle_scene(*packet);
                std::lock_guard<std::mutex> lock(recycle_mutex_);
                store_recycled_scene(std::move(*packet));
            },
            bytes);
        scene_ = {};
        std::lock_guard<std::mutex> lock(recycle_mutex_);
        if (!recycled_scenes_.empty()) {
            scene_ = std::move(recycled_scenes_.back());
            recycled_scenes_.pop_back();
        }
    } else {
        observe_worker_packet(scene_, packet_id);
        renderer_->render(scene_, initialize, false);
        recycle_scene(scene_);
    }
    invalidate_scene_bindings();
}

private:
  void invalidate_scene_bindings() {
    // Both slots name entries in exactly one producer Scene. Worker-owned
    // packets and ordered upload receipts have separate lifetimes.
    for (auto &entry : textures_)
      entry.scene_index = entry.sharp_index = no_binding;
  }

  struct PendingLocalPacket {
    std::shared_ptr<vk::Scene> packet;
    bool initialize;
    std::size_t bytes;
    std::uint64_t producer_packet_id;
  };
  std::vector<PendingLocalPacket> pending_local_packets_;
  std::size_t pending_local_bytes_{};
  // Staging pressure diagnostics (render-only): peak pending bytes, early completions of the
  // pending packets and the bounded log line state (one per mission).
  std::size_t staging_peak_bytes_{};
  bool staging_first_flush_pending_{true};
  std::size_t staging_first_flush_bytes_{}, staging_first_flush_packets_{};
  std::size_t staging_early_completions_{};
  std::size_t staging_early_log_lines_{};
  bool staging_early_logged_{};
  void complete_local_light_packets() {
    if (producer_failed_) return;
    // Detach the batch before posting: an exception must not cause a later
    // drain/destructor to replay packets already submitted to the worker.
    auto packets = std::move(pending_local_packets_);
    pending_local_packets_.clear();
    pending_local_bytes_ = 0;
    for (const auto &pending : packets) {
      auto packet = pending.packet;
      const bool initialize = pending.initialize;
      const auto packet_id = pending.producer_packet_id;
      local_lights_attach(*packet);
      if (worker_) {
        worker_->post(
            [this, packet, initialize, packet_id] {
              {
                CpuInterval interval(cpu_profile_ ? &worker_render_ticks_
                                                  : nullptr);
                observe_worker_packet(*packet, packet_id);
                renderer_->render(*packet, initialize, false);
              }
              recycle_scene(*packet);
              std::lock_guard<std::mutex> lock(recycle_mutex_);
              store_recycled_scene(std::move(*packet));
            },
            pending.bytes);
      } else {
        observe_worker_packet(*packet, packet_id);
        renderer_->render(*packet, initialize, false);
        recycle_scene(*packet);
        std::lock_guard<std::mutex> lock(recycle_mutex_);
        store_recycled_scene(std::move(*packet));
      }
    }
    packets.clear();
    pending_local_packets_.swap(packets);
    if (scene_.order.empty()) {
      std::lock_guard<std::mutex> lock(recycle_mutex_);
      if (!recycled_scenes_.empty()) {
        if (!scene_.draws.empty() || !scene_.clears.empty() ||
            !scene_.vertices.empty())
          throw std::runtime_error(
              "Command-empty producer Scene retains draw or clear work");
        // Adopt capacity, not the recycled packet's reset view. A clipped
        // batch may already have established this view's extent/light state.
        auto &recycled = recycled_scenes_.back();
        scene_.textures.clear();
        scene_.vertices.swap(recycled.vertices);
        scene_.draws.swap(recycled.draws);
        scene_.textures.swap(recycled.textures);
        scene_.order.swap(recycled.order);
        scene_.clears.swap(recycled.clears);
        recycled_scenes_.pop_back();
        invalidate_scene_bindings();
      }
    }
  }
// The terms of packet_bytes, kept separate so a staging diagnostic can name the dominant one.
  // Vector terms count CAPACITY, not size: a recycled Scene keeps its grown capacity, which is
  // real retained memory but can outlast the packet that grew it.
  struct PacketByteTerms {
    std::size_t scene{}, vertices{}, color_depth{}, draws{}, order{}, textures{}, texture_pixels{},
        emissions{}, geometry{}, lit_normals{}, height_metadata{}, clears{}, height_packet{};
    std::size_t total() const {
      return scene + vertices + color_depth + draws + order + textures + texture_pixels +
             emissions + geometry + lit_normals + height_metadata + clears + height_packet;
    }
  };
static PacketByteTerms packet_byte_terms(const vk::Scene &scene) {
  PacketByteTerms terms;
  // sizeof(scene) includes the owned fixed local-light Uniform.
  terms.scene = sizeof(scene);
  terms.vertices = scene.vertices.capacity();
  terms.color_depth = (scene.color.capacity() + scene.depth.capacity()) * sizeof(uint16_t);
  terms.draws = scene.draws.capacity() * sizeof(vk::Draw);
  terms.order = scene.order.capacity() * sizeof(vk::Command);
  terms.textures = scene.textures.capacity() * sizeof(vk::TextureRef);
  std::size_t running = terms.scene + terms.vertices + terms.color_depth + terms.draws +
                        terms.order + terms.textures;
  const auto emission_bytes = scene.emissions.allocated_bytes();
  if (emission_bytes > std::numeric_limits<std::size_t>::max() - running)
    throw std::runtime_error("Emission packet byte count overflow");
  terms.emissions = emission_bytes;
  for (const auto &texture : scene.textures)
    terms.texture_pixels += texture.pixels.capacity() * sizeof(uint16_t) +
                            texture.pixels32.capacity() * sizeof(uint32_t);
  // A model drawn thousands of times shares one geometry (and one lit-normal array): charge each
  // distinct allocation once per packet, not once per draw.
  std::unordered_set<const void *> counted_geometry, counted_lit_normals;
  for (const auto &draw : scene.draws) {
    if (draw.model && draw.model->geometry) {
      const auto &geometry = *draw.model->geometry;
      if (counted_geometry.insert(&geometry).second)
        terms.geometry += geometry.vertices.capacity() * sizeof(vk::ModelVertex) +
                          geometry.indices.capacity() * sizeof(uint32_t);
    }
    if (draw.lit_normals && counted_lit_normals.insert(draw.lit_normals.get()).second)
      terms.lit_normals += draw.lit_normals->capacity() * sizeof(std::array<float, 3>);
  }
  std::set<const mw34::materials::HeightBinding *> height_snapshots;
  for (const auto &draw : scene.draws) {
    const auto &binding = draw.height_binding;
    if (binding && height_snapshots.insert(binding.get()).second) {
      const auto metadata = mw34::materials::height_binding_metadata_bytes(*binding);
      if (metadata > std::numeric_limits<std::size_t>::max() - terms.height_metadata)
        throw std::runtime_error("Height snapshot byte count overflow");
      terms.height_metadata += metadata;
    }
  }
  for (const auto &clear : scene.clears)
    terms.clears += clear.rects.capacity() * sizeof(VkRect2D);
  const auto height_bytes = packet_height_bytes(scene);
  if (height_bytes > std::numeric_limits<std::size_t>::max() - terms.total())
    throw std::runtime_error("Height packet byte count overflow");
  terms.height_packet = std::size_t(height_bytes);
  return terms;
}
// Sum the terms with an overflow check on every addition (the unchecked total() is only for
// diagnostics that cannot wrap).
static std::size_t checked_packet_total(const PacketByteTerms &terms) {
  std::size_t total = 0;
  for (const std::size_t term :
       {terms.scene, terms.vertices, terms.color_depth, terms.draws, terms.order, terms.textures,
        terms.texture_pixels, terms.emissions, terms.geometry, terms.lit_normals,
        terms.height_metadata, terms.clears, terms.height_packet}) {
    if (term > std::numeric_limits<std::size_t>::max() - total)
      throw std::runtime_error("Packet byte count overflow");
    total += term;
  }
  return total;
}
static std::size_t packet_bytes(const vk::Scene &scene) {
  return checked_packet_total(packet_byte_terms(scene));
}
static std::uint64_t packet_height_bytes(const vk::Scene &scene) {
  std::vector<std::shared_ptr<const mw34::materials::HeightBinding>> bindings;
  bindings.reserve(scene.draws.size());
  for (const auto &draw : scene.draws)
    if (draw.height_binding)
      bindings.push_back(draw.height_binding);
  return mw34::materials::height_binding_bytes(bindings);
}
// Bounded pool of recycled Scenes. A Scene keeps the capacity of its vectors, so an unbounded pool
// would carry the largest earlier frames into every later packet (packet_bytes charges capacity).
// Callers hold recycle_mutex_.
static constexpr std::size_t recycled_scene_limit = 8;
void store_recycled_scene(vk::Scene &&scene) {
  if (recycled_scenes_.size() < recycled_scene_limit)
    recycled_scenes_.push_back(std::move(scene));
  // Otherwise drop it, which releases its retained capacity.
}
std::size_t recycled_scene_count_for_test() {
  std::lock_guard<std::mutex> lock(recycle_mutex_);
  return recycled_scenes_.size();
}
// Release every retained Scene capacity. Only call at a synchronized point, after the workers
// have finished (mission change drains first).
void release_recycled_scenes() {
  std::lock_guard<std::mutex> lock(recycle_mutex_);
  recycled_scenes_.clear();
  recycled_scenes_.shrink_to_fit();
}
static void recycle_scene(vk::Scene &scene) {
    // Reuse hot submission storage, like the SDL renderer. Reset every
    // scene value and release its resource references while keeping capacity.
    vk::Scene next{};
    next.vertices.swap(scene.vertices);
    next.vertices.clear();
    next.draws.swap(scene.draws);
    next.draws.clear();
    next.textures.swap(scene.textures);
    next.textures.clear();
    next.order.swap(scene.order);
    next.order.clear();
    next.clears.swap(scene.clears);
    next.clears.clear();
    scene = std::move(next);
}

public:
