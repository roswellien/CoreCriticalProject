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
      local_bytes = packet_bytes(scene_);
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
                recycled_scenes_.push_back(std::move(*packet));
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
              recycled_scenes_.push_back(std::move(*packet));
            },
            pending.bytes);
      } else {
        observe_worker_packet(*packet, packet_id);
        renderer_->render(*packet, initialize, false);
        recycle_scene(*packet);
        std::lock_guard<std::mutex> lock(recycle_mutex_);
        recycled_scenes_.push_back(std::move(*packet));
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
static std::size_t packet_bytes(const vk::Scene &scene) {
  // sizeof(scene) includes the owned fixed local-light Uniform.
  std::size_t bytes =
      sizeof(scene) + scene.vertices.capacity() +
      (scene.color.capacity() + scene.depth.capacity()) * sizeof(uint16_t) +
      scene.draws.capacity() * sizeof(vk::Draw) +
      scene.order.capacity() * sizeof(vk::Command) +
      scene.textures.capacity() * sizeof(vk::TextureRef);
  const auto emission_bytes = scene.emissions.allocated_bytes();
  if (emission_bytes > std::numeric_limits<std::size_t>::max() - bytes)
    throw std::runtime_error("Emission packet byte count overflow");
  bytes += emission_bytes;
  for (const auto &texture : scene.textures)
    bytes += texture.pixels.capacity() * sizeof(uint16_t) +
             texture.pixels32.capacity() * sizeof(uint32_t);
  for (const auto &draw : scene.draws) {
    if (draw.model && draw.model->geometry) {
      const auto &geometry = *draw.model->geometry;
      bytes += geometry.vertices.capacity() * sizeof(vk::ModelVertex) +
               geometry.indices.capacity() * sizeof(uint32_t);
    }
    if (draw.lit_normals)
      bytes += draw.lit_normals->capacity() * sizeof(std::array<float, 3>);
  }
  std::set<const mw34::materials::HeightBinding *> height_snapshots;
  for (const auto &draw : scene.draws) {
    const auto &binding = draw.height_binding;
    if (binding && height_snapshots.insert(binding.get()).second) {
      const auto metadata = mw34::materials::height_binding_metadata_bytes(*binding);
      if (metadata > std::numeric_limits<std::size_t>::max() - bytes)
        throw std::runtime_error("Height snapshot byte count overflow");
      bytes += metadata;
    }
  }
    for (const auto &clear : scene.clears)
        bytes += clear.rects.capacity() * sizeof(VkRect2D);
  const auto height_bytes = packet_height_bytes(scene);
  if (height_bytes > std::numeric_limits<std::size_t>::max() - bytes)
    throw std::runtime_error("Height packet byte count overflow");
  return bytes + std::size_t(height_bytes);
}
static std::uint64_t packet_height_bytes(const vk::Scene &scene) {
  std::vector<std::shared_ptr<const mw34::materials::HeightBinding>> bindings;
  bindings.reserve(scene.draws.size());
  for (const auto &draw : scene.draws)
    if (draw.height_binding)
      bindings.push_back(draw.height_binding);
  return mw34::materials::height_binding_bytes(bindings);
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
