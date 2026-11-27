void present() override {
  auto* benchmark = benchmark_run_ && benchmark_run_->armed() ? benchmark_run_ : nullptr;
  const auto playback_time = std::exchange(benchmark_time_, std::nullopt);
  const auto reject = [&](const char* reason) {
    if (benchmark) benchmark->invalidate(benchmark->next_frame(playback_time.value_or(0)), reason);
  };
  if (benchmark && (!playback_time || !window_bound_ || !worker_ || !native_wsi_)) {
    reject("presentation outside the benchmark resident worker path");
    return;
  }
  if (benchmark && (benchmark->failed() ||
                    (!benchmark->strict() && benchmark->elapsed() >= benchmark->scene.end())))
    return;
  mw34::timing::PresentBoundaryScope<mw34::timing::ProducerResourceTiming>
      producer_timing_scope(producer_resource_timing_);
  if (editor_source_ || editor_present_active_) require_editor_producer();
  flush();
  complete_local_light_packets();
  // Retire one active-to-closed transition even during a capture/hidden frame.
  // Peek cannot create a CPU context or admit filesystem paths.
  if (editor_present_active_) {
    auto* existing = editor_source_ ? editor_source_->existing() : nullptr;
    if (!existing || !existing->active()) {
      if (worker_) worker_->drain();
      renderer_->detach_editor();
      editor_present_active_ = false;
    }
  }
  if (!resident_width_) {
    reject("no resident frame");
    return;
  }
  if (!capture_path_.empty()) {
    reject("capture requested during playback");
    if (benchmark) return;
    save_capture();
    return;
  }
  const auto window_state =
      window_state_tracker_
          ? window_state_tracker_->sample_and_get()
          : cc_mw3_re::platform::SdlWindowState{
                (SDL_GetWindowFlags(window_) &
                 (SDL_WINDOW_HIDDEN | SDL_WINDOW_MINIMIZED)) == 0,
                0, 0};
  if (!window_state.visible) {
    reject("benchmark window is no longer visible");
    return;
  }
  // Query after the event/game input path, so Shift+F12's first activation is
  // visible in this presentation, without moving the game's on_present hook.
  auto* editor = editor_source_ ? editor_source_->acquire_if_active() : nullptr;
  if (editor) {
    reject("editor activated during playback");
    if (benchmark) return;
    if (worker_) worker_->drain();
    editor_present_active_ = true;
  }
  CpuInterval interval(cpu_profile_ ? &transport_ticks_ : nullptr);
  if (!window_bound_) {
    std::vector<uint32_t> argb;
    int width = 0, height = 0;
    if (!read_back(&argb, &width, &height)) {
      throw std::runtime_error("First Vulkan frame could not be read back");
    }
    const auto rgba = rgba_copy(argb);
    // Window/surface creation stays on the SDL window owner. Readback
    // above is a queue barrier; the worker cannot race this cold path.
    const auto before = renderer_->presents;
    if (!renderer_->present(native_window_,
                            reinterpret_cast<const uint8_t *>(rgba.data()),
                            width, height, width * 4, false, true, editor)) {
      throw std::runtime_error(
          "Could not bind the selected Core Critical Vulkan presenter");
    }
    window_bound_ = renderer_->presents != before;
    presented_frames_ += renderer_->presents - before;
    if (window_bound_ && !presented_) {
      MW3_LOG(I, "%s first frame: %s (upload)\n", driver_name(),
                   renderer_->device_name.c_str());
      sdlfe::mark_ready();
    }
    presented_ = window_bound_;
  } else {
    int window_width = 0, window_height = 0;
    if (window_state_tracker_) {
      window_width = window_state.drawable_width;
      window_height = window_state.drawable_height;
    } else {
      SDL_GetWindowSizeInPixels(window_, &window_width, &window_height);
    }
    if (window_width != present_window_width_ ||
        window_height != present_window_height_) {
      if (benchmark && (window_width != benchmark->width || window_height != benchmark->height)) {
        reject("benchmark drawable resized");
        return;
      }
      if (worker_)
        worker_->drain();
      renderer_->resize_present_window(native_window_);
      present_window_width_ = window_width;
      present_window_height_ = window_height;
    }
    if (benchmark && (resident_width_ != unsigned(benchmark->width) ||
                      resident_height_ != unsigned(benchmark->height))) {
      reject("benchmark resident size changed");
      return;
    }
    const auto present = [this, width = resident_width_, height = resident_height_, window_state,
                          benchmark](sdlfe::benchmark::FrameTag tag) {
      CpuInterval interval(worker_ && cpu_profile_ ? &worker_present_ticks_
                                                   : nullptr);
      cc_mw3_re::platform::SdlWindowStateScope job_scope(
          window_state_tracker_.get(), window_state);
      const auto before = renderer_->presents;
      if (benchmark) {
        vk::Renderer::ResidentPresentResult status;
        try {
          const bool presented = renderer_->present_resident(native_window_, width, height, false,
                                                              nullptr, &status);
          const bool same_swapchain = renderer_->swapchain_generation == benchmark_swapchain_ &&
                                      renderer_->immediate_swapchain();
          const sdlfe::benchmark::PresentReceipt receipt{
              presented, same_swapchain, status.acquire, status.present,
              renderer_->presents - before, status.completion};
          if (benchmark->strict()) record_strict_present(tag, receipt, status);
          else benchmark->record_present(tag, receipt);
        } catch (const std::exception& error) {
          benchmark->invalidate(tag, error.what());
          throw;
        }
        const auto pressure = renderer_->memory_pressure;
        if (pressure.recoveries || pressure.model_omissions ||
            pressure.texture_substitutions || pressure.preload_stops)
          benchmark->invalidate(tag, "video memory pressure during playback");
      } else if (!renderer_->present_resident(native_window_, width, height, false)) {
        throw std::runtime_error("Core Critical resident present failed");
      }
      presented_frames_ += renderer_->presents - before;
      if (renderer_->resident_presents)
        resident_draws_.store(renderer_->draws);
    };
    if (editor) {
      // This is deliberately outside the worker closure: no source, CPU
      // context or ImDrawData borrow crosses the producer/worker boundary.
      const auto before = renderer_->presents;
      if (!renderer_->present_resident(native_window_, resident_width_,
                                       resident_height_, false, editor))
        throw std::runtime_error("Core Critical editor resident present failed");
      presented_frames_ += renderer_->presents - before;
      if (renderer_->resident_presents)
        resident_draws_.store(renderer_->draws);
    } else if (worker_) {
      // A flip is also the simulation's visible-frame boundary. With up to eight queued jobs the
      // game could run several frames ahead of the image on screen, so hits and deaths appeared
      // before their projectiles visibly arrived. Keep at most one presented frame in flight: wait
      // for the previous present before queueing this one, so rendering still overlaps the next
      // game frame but the screen is never more than one frame behind the simulation.
      if (last_present_job_ != 0) worker_->wait_for_job(last_present_job_);
      if (benchmark && (benchmark->failed() ||
                        (!benchmark->strict() && benchmark->elapsed() >= benchmark->scene.end())))
        return;
      const auto tag = benchmark ? benchmark->submit(*playback_time, benchmark_effects_)
                                 : sdlfe::benchmark::FrameTag{};
      last_present_job_ = worker_->post_numbered([present, tag] { present(tag); });
    } else {
      present({});
    }
  }
  if (!reported_resident_ && resident_draws_.load()) {
    MW3_LOG(I, "%s resident frame: %llu Vulkan draws\n",
                 driver_name(),
                 static_cast<unsigned long long>(resident_draws_.load()));
    reported_resident_ = true;
  }
}
