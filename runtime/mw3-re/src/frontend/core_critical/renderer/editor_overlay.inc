// Private Renderer members. Included only on Windows, after its device/queue
// fields. The producer drains RenderWorker before passing a nonnull EditorUi.
public:
  struct EditorGpuStatistics {
    VkDeviceSize bytes{}, peak_bytes{};
    std::uint64_t allocations{}, waits{}, frames{}, retirements{};
    unsigned live_allocations{};
    VkExtent2D extent{};
    VkFormat format{VK_FORMAT_UNDEFINED};
    unsigned image_count{};
    bool failed{};
    VkResult first_result{VK_RESULT_MAX_ENUM};
    VkResult backend_terminal{VK_RESULT_MAX_ENUM};
    VkResult upload_submit{VK_RESULT_MAX_ENUM}, upload_wait{VK_RESULT_MAX_ENUM};
  };

  EditorGpuStatistics editor_gpu_statistics() const {
    if (editor_.cpu && editor_.thread != std::this_thread::get_id())
      throw std::logic_error("Core editor statistics require their owner thread");
    auto result = editor_.statistics;
    result.failed = editor_.failed;
    result.extent = editor_.composition.extent;
    result.format = editor_.composition.format;
    result.image_count = editor_.composition.image_count;
    return result;
  }

  // The attachment guard calls this on the producer, after draining its worker,
  // while the borrowed CPU owner is still alive. This never creates a context.
  void detach_editor() { retire_editor(); }

private:
  static constexpr VkDeviceSize editor_budget_bytes = 512ull * 1024 * 1024;
  static constexpr std::uint64_t editor_max_pixels = 35389440;
  static constexpr std::uint64_t editor_wait_ns = 10000000000ULL;
  struct EditorMemory {
    VkDeviceMemory memory{};
    VkDeviceSize bytes{};
  };
  struct EditorComposition {
    Image color;
    VkRenderPass pass{};
    VkFramebuffer framebuffer{};
    VkExtent2D extent{};
    VkFormat format{VK_FORMAT_UNDEFINED};
    unsigned image_count{};
  };
  struct EditorOwner {
    sdlfe::EditorUi *cpu{}; // Borrowed; the attachment guard retires us first.
    std::thread::id thread{};
    bool initialized{}, pending{}, failed{};
    std::exception_ptr first_failure;
    std::array<EditorMemory, 64> memory{};
    EditorComposition composition;
    EditorGpuStatistics statistics;
  } editor_;

  [[noreturn]] static void editor_fatal(const char *operation, VkResult initiating,
                                       VkResult completion) noexcept {
    MW3_LOG(E,
                 "Core editor FATAL: %s; initiating=%d completion=%d; "
                 "terminating before unsafe resource/context/device unwinding\n",
                 operation, int(initiating), int(completion));
    std::fflush(stderr);
    std::fflush(stdout);
    std::_Exit(3);
  }
  static void editor_check(VkResult result, const char *operation) {
    if (result != VK_SUCCESS)
      throw ImGui_ImplVulkan_Failure{result, operation};
  }
  static void editor_backend_result(VkResult result) {
    // The qualified backend callback returns on success and throws on error.
    if (result < 0)
      throw ImGui_ImplVulkan_Failure{result, "Core editor Vulkan backend"};
  }
  [[noreturn]] static void editor_rethrow(std::exception_ptr failure) {
    try {
      std::rethrow_exception(failure);
    } catch (const ImGui_ImplVulkan_Failure &error) {
      throw std::runtime_error(std::string("Core editor: ") + error.Reason +
                               " (VkResult=" + std::to_string(int(error.Result)) + ")");
    }
  }
  void editor_save_current_results() noexcept {
    editor_.statistics.backend_terminal = ImGui_ImplVulkan_GetTerminalResult();
    ImGui_ImplVulkan_GetLastUploadResults(&editor_.statistics.upload_submit,
                                         &editor_.statistics.upload_wait);
  }
  void editor_note_failure(std::exception_ptr failure) noexcept {
    const bool first = !editor_.failed;
    if (first) {
      editor_.failed = true;
      editor_.first_failure = failure;
      try {
        std::rethrow_exception(failure);
      } catch (const ImGui_ImplVulkan_Failure &error) {
        editor_.statistics.first_result = error.Result;
      } catch (...) {
        // The original C++ exception remains owned, even without a VkResult.
      }
    }
    try {
      if (editor_.cpu)
        editor_.cpu->with_current([&] { editor_save_current_results(); });
    } catch (...) {
      editor_fatal("cannot inspect the live owning CPU context",
                   editor_.statistics.first_result, VK_RESULT_MAX_ENUM);
    }
    if (first)
      MW3_LOG(E,
                   "Core editor failure: first=%d backend_terminal=%d "
                   "upload_submit=%d upload_wait=%d bytes=%llu peak=%llu\n",
                   int(editor_.statistics.first_result),
                   int(editor_.statistics.backend_terminal),
                   int(editor_.statistics.upload_submit), int(editor_.statistics.upload_wait),
                   (unsigned long long)editor_.statistics.bytes,
                   (unsigned long long)editor_.statistics.peak_bytes);
  }

  // The records are reserved before Vulkan allocation. Committing a successful
  // identity uses no map insertion, heap allocation or other fallible operation.
  static VkResult editor_allocate(void *user, VkDevice selected_device,
                                 const VkMemoryAllocateInfo *info,
                                 const VkAllocationCallbacks *callbacks,
                                 PFN_vkAllocateMemory allocate, VkDeviceMemory *output) {
    auto &owner = *static_cast<Renderer *>(user);
    if (selected_device != owner.device || !info || !output || !allocate ||
        info->allocationSize == 0)
      return VK_ERROR_INITIALIZATION_FAILED;
    auto &state = owner.editor_;
    if (state.statistics.bytes > editor_budget_bytes ||
        info->allocationSize > editor_budget_bytes - state.statistics.bytes)
      return VK_ERROR_OUT_OF_DEVICE_MEMORY;
    EditorMemory *slot = nullptr;
    for (auto &record : state.memory)
      if (!record.memory) {
        slot = &record;
        break;
      }
    if (!slot)
      return VK_ERROR_TOO_MANY_OBJECTS;
    VkDeviceMemory acquired = VK_NULL_HANDLE;
    const VkResult result = owner.allocate_memory(selected_device, info, callbacks, &acquired, allocate);
    if (result != VK_SUCCESS)
      return result; // Failed dirty/null/untouched outputs do not prove ownership.
    if (!acquired)
      return VK_ERROR_INITIALIZATION_FAILED;
    *slot = {acquired, info->allocationSize};
    state.statistics.bytes += info->allocationSize;
    state.statistics.peak_bytes =
        std::max(state.statistics.peak_bytes, state.statistics.bytes);
    ++state.statistics.live_allocations;
    ++state.statistics.allocations;
    *output = acquired;
    return VK_SUCCESS;
  }
  static void editor_free(void *user, VkDevice selected_device, VkDeviceMemory allocation,
                          const VkAllocationCallbacks *callbacks,
                          PFN_vkFreeMemory free_memory) noexcept {
    auto &owner = *static_cast<Renderer *>(user);
    if (selected_device != owner.device || !allocation || !free_memory)
      editor_fatal("invalid editor allocation owner", VK_ERROR_UNKNOWN, VK_RESULT_MAX_ENUM);
    for (auto &record : owner.editor_.memory)
      if (record.memory == allocation) {
        owner.release_memory(selected_device, allocation, callbacks, free_memory);
        owner.editor_.statistics.bytes -= record.bytes;
        --owner.editor_.statistics.live_allocations;
        record = {};
        return;
      }
    editor_fatal("unowned editor memory release", VK_ERROR_UNKNOWN, VK_RESULT_MAX_ENUM);
  }

  void editor_clear_pending() noexcept {
    editor_.pending = false;
    presentInFlight = false;
  }
  // A failed wait is not completion evidence. At most one exceptional wait uses
  // the same real owning fence; unresolved lifetime terminates before unwinding.
  void editor_exceptional_completion(const char *operation, VkResult initiating) {
    VkResult completion = VK_RESULT_MAX_ENUM;
    try {
      ++editor_.statistics.waits;
      completion = f.vkWaitForFences(device, 1, &presentFence, VK_TRUE, editor_wait_ns);
    } catch (...) {
      completion = VK_RESULT_MAX_ENUM;
    }
    if (completion != VK_SUCCESS && completion != VK_ERROR_DEVICE_LOST)
      editor_fatal(operation, initiating, completion);
    editor_clear_pending();
    if (completion == VK_ERROR_DEVICE_LOST)
      MW3_LOG(E, "Core editor lifetime disposition: device lost after %s (%d)\n",
                   operation, int(initiating));
  }
  void editor_wait_present() {
    if (!editor_.pending)
      return;
    VkResult result = VK_RESULT_MAX_ENUM;
    std::exception_ptr failure;
    try {
      ++editor_.statistics.waits;
      result = f.vkWaitForFences(device, 1, &presentFence, VK_TRUE, editor_wait_ns);
    } catch (...) {
      failure = std::current_exception();
    }
    if (!failure && (result == VK_SUCCESS || result == VK_ERROR_DEVICE_LOST)) {
      editor_clear_pending();
      editor_check(result, "owning present fence");
      return;
    }
    editor_exceptional_completion("owning present fence did not complete", result);
    if (failure)
      std::rethrow_exception(failure);
    editor_check(result, "owning present fence did not complete normally");
  }
  void editor_submit(const VkSubmitInfo &submit) {
    // Set the lifetime record before the attempt; an arbitrary exception cannot
    // be mistaken for the known Vulkan OOM no-submit contract.
    editor_.pending = true;
    VkResult result = VK_RESULT_MAX_ENUM;
    std::exception_ptr failure;
    try {
      result = f.vkQueueSubmit(queue, 1, &submit, presentFence);
    } catch (...) {
      failure = std::current_exception();
    }
    if (failure) {
      editor_exceptional_completion("present submit threw", VK_RESULT_MAX_ENUM);
      std::rethrow_exception(failure);
    }
    if (result == VK_ERROR_OUT_OF_HOST_MEMORY || result == VK_ERROR_OUT_OF_DEVICE_MEMORY ||
        result == VK_ERROR_DEVICE_LOST) {
      editor_clear_pending();
      editor_check(result, "present submit");
    }
    if (result != VK_SUCCESS) {
      editor_exceptional_completion("present submit outcome unknown", result);
      editor_check(result, "present submit outcome unknown");
    }
    presentInFlight = true; // Also protects the owner if queue presentation throws.
  }

  void editor_destroy_composition(EditorComposition &composition) noexcept {
    if (composition.framebuffer)
      f.vkDestroyFramebuffer(device, composition.framebuffer, nullptr);
    if (composition.pass)
      f.vkDestroyRenderPass(device, composition.pass, nullptr);
    if (composition.color.view)
      f.vkDestroyImageView(device, composition.color.view, nullptr);
    if (composition.color.image)
      f.vkDestroyImage(device, composition.color.image, nullptr);
    if (composition.color.memory)
      editor_free(this, device, composition.color.memory, nullptr, f.vkFreeMemory);
    composition = {};
  }
  void editor_shutdown_backend() {
    if (!editor_.initialized)
      return;
    if (!editor_.cpu || !editor_.cpu->with_current([&] {
          editor_save_current_results(); // Consume diagnostics before deleting bd.
          ImGui_ImplVulkan_Shutdown();
        }))
      editor_fatal("backend outlived its CPU context", VK_ERROR_UNKNOWN, VK_RESULT_MAX_ENUM);
    editor_.initialized = false;
  }
  void retire_editor() {
    if (!editor_.cpu && !editor_.composition.color.image && !editor_.initialized)
      return;
    if (editor_.thread != std::this_thread::get_id())
      throw std::logic_error("Core editor retirement requires the CPU owner thread");
    std::exception_ptr failure;
    try {
      editor_wait_present();
    } catch (...) {
      failure = std::current_exception();
      editor_note_failure(failure);
    }
    // The wait either proved completion/device loss or terminated the process.
    // No destructor can reach the following frees with unresolved ownership.
    editor_shutdown_backend();
    editor_destroy_composition(editor_.composition);
    if (editor_.statistics.bytes || editor_.statistics.live_allocations)
      editor_fatal("editor allocations outlived shutdown", VK_ERROR_UNKNOWN, VK_RESULT_MAX_ENUM);
    editor_.cpu = nullptr;
    ++editor_.statistics.retirements;
    if (failure)
      editor_rethrow(failure);
  }
  void editor_retire_for_shutdown() noexcept {
    try {
      retire_editor();
    } catch (...) {
      // Known failed completion is already safe to retire; still make the failed
      // run nonzero. Unknown completion never returned to this destructor.
      editor_fatal("editor shutdown failed", editor_.statistics.first_result,
                   editor_.statistics.backend_terminal);
    }
  }
  bool editor_requested(sdlfe::EditorUi *cpu) {
    if (editor_.failed)
      editor_rethrow(editor_.first_failure);
    const bool active = cpu && cpu->active(); // CPU-only owner/FP check, no startup.
    if (editor_.cpu && (editor_.cpu != cpu || !active))
      retire_editor();
    if (active && editor_.cpu && editor_.thread != std::this_thread::get_id())
      throw std::logic_error("Core editor rendering requires the CPU owner thread");
    return active;
  }

  void editor_create_composition(EditorComposition &result, VkExtent2D extent,
                                  VkFormat format, unsigned image_count) {
    result.extent = extent;
    result.format = format;
    result.image_count = image_count;
    try {
      VkImageCreateInfo image_info{};
      image_info.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
      image_info.imageType = VK_IMAGE_TYPE_2D;
      image_info.format = format;
      image_info.extent = {extent.width, extent.height, 1};
      image_info.mipLevels = image_info.arrayLayers = 1;
      image_info.samples = VK_SAMPLE_COUNT_1_BIT;
      image_info.tiling = VK_IMAGE_TILING_OPTIMAL;
      image_info.usage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT |
                         VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT;
      VkImage image_handle = VK_NULL_HANDLE;
      VkResult status = f.vkCreateImage(device, &image_info, nullptr, &image_handle);
      if (status == VK_SUCCESS)
        result.color.image = image_handle;
      editor_check(status, "composition image");
      if (!result.color.image)
        editor_check(VK_ERROR_INITIALIZATION_FAILED, "null successful composition image");
      VkMemoryRequirements requirements{};
      f.vkGetImageMemoryRequirements(device, result.color.image, &requirements);
      VkMemoryAllocateInfo allocation{};
      allocation.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
      allocation.allocationSize = requirements.size;
      allocation.memoryTypeIndex = type(requirements, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
      VkDeviceMemory memory_handle = VK_NULL_HANDLE;
      status = editor_allocate(this, device, &allocation, nullptr, f.vkAllocateMemory, &memory_handle);
      if (status == VK_SUCCESS)
        result.color.memory = memory_handle;
      editor_check(status, "composition allocation admission/memory");
      editor_check(f.vkBindImageMemory(device, result.color.image, result.color.memory, 0),
                   "composition image binding");
      VkImageViewCreateInfo view_info{};
      view_info.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
      view_info.image = result.color.image;
      view_info.viewType = VK_IMAGE_VIEW_TYPE_2D;
      view_info.format = format;
      view_info.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
      VkImageView view_handle = VK_NULL_HANDLE;
      status = f.vkCreateImageView(device, &view_info, nullptr, &view_handle);
      if (status == VK_SUCCESS)
        result.color.view = view_handle;
      editor_check(status, "composition image view");
      if (!result.color.view)
        editor_check(VK_ERROR_INITIALIZATION_FAILED, "null successful composition view");
      VkAttachmentDescription attachment{};
      attachment.format = format;
      attachment.samples = VK_SAMPLE_COUNT_1_BIT;
      attachment.loadOp = VK_ATTACHMENT_LOAD_OP_LOAD;
      attachment.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
      attachment.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
      attachment.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
      attachment.initialLayout = attachment.finalLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
      VkAttachmentReference color{0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL};
      VkSubpassDescription subpass{};
      subpass.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
      subpass.colorAttachmentCount = 1;
      subpass.pColorAttachments = &color;
      VkRenderPassCreateInfo pass_info{};
      pass_info.sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
      pass_info.attachmentCount = pass_info.subpassCount = 1;
      pass_info.pAttachments = &attachment;
      pass_info.pSubpasses = &subpass;
      VkRenderPass pass_handle = VK_NULL_HANDLE;
      status = f.vkCreateRenderPass(device, &pass_info, nullptr, &pass_handle);
      if (status == VK_SUCCESS)
        result.pass = pass_handle;
      editor_check(status, "composition render pass");
      if (!result.pass)
        editor_check(VK_ERROR_INITIALIZATION_FAILED, "null successful composition pass");
      VkFramebufferCreateInfo framebuffer_info{};
      framebuffer_info.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
      framebuffer_info.renderPass = result.pass;
      framebuffer_info.attachmentCount = 1;
      framebuffer_info.pAttachments = &result.color.view;
      framebuffer_info.width = extent.width;
      framebuffer_info.height = extent.height;
      framebuffer_info.layers = 1;
      VkFramebuffer framebuffer_handle = VK_NULL_HANDLE;
      status = f.vkCreateFramebuffer(device, &framebuffer_info, nullptr, &framebuffer_handle);
      if (status == VK_SUCCESS)
        result.framebuffer = framebuffer_handle;
      editor_check(status, "composition framebuffer");
      if (!result.framebuffer)
        editor_check(VK_ERROR_INITIALIZATION_FAILED, "null successful composition framebuffer");
    } catch (...) {
      editor_destroy_composition(result);
      throw;
    }
  }
  bool prepare_editor(sdlfe::EditorUi *cpu, bool requested) {
    if (!requested)
      return false;
    if (!cpu || presentInFlight || editor_.pending)
      throw std::logic_error("Core editor preparation requires visible output and owning completion");
    editor_.cpu = cpu;
    editor_.thread = std::this_thread::get_id();
    const VkFormat format = dxgi.active() ? VK_FORMAT_B8G8R8A8_UNORM : swapFormat;
    const unsigned image_count = dxgi.active() ? dxgi.presentation_image_count()
                                               : unsigned(swapImages.size());
    if (image_count < 2 || image_count > IMGUI_IMPL_VULKAN_MAX_IMAGE_COUNT)
      editor_check(VK_ERROR_INITIALIZATION_FAILED, "actual presentation image count outside editor admission");
    if (format != VK_FORMAT_B8G8R8A8_UNORM && format != VK_FORMAT_R8G8B8A8_UNORM &&
        format != VK_FORMAT_B8G8R8A8_SRGB && format != VK_FORMAT_R8G8B8A8_SRGB)
      editor_check(VK_ERROR_FORMAT_NOT_SUPPORTED, "selected output format is unsupported for editor composition");
    VkPhysicalDeviceProperties limits{};
    f.vkGetPhysicalDeviceProperties(gpu, &limits);
    const auto extent = swapExtent;
    if (!extent.width || !extent.height ||
        std::uint64_t(extent.width) * extent.height > editor_max_pixels ||
        extent.width > 2147483647u || extent.height > 2147483647u ||
        extent.width > limits.limits.maxImageDimension2D ||
        extent.height > limits.limits.maxImageDimension2D ||
        extent.width > limits.limits.maxFramebufferWidth ||
        extent.height > limits.limits.maxFramebufferHeight)
      editor_check(VK_ERROR_INITIALIZATION_FAILED, "physical editor output extent exceeds admission");
    VkFormatProperties properties{};
    f.vkGetPhysicalDeviceFormatProperties(gpu, format, &properties);
    const VkFormatFeatureFlags needed = VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BIT |
        VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BLEND_BIT | VK_FORMAT_FEATURE_BLIT_DST_BIT |
        VK_FORMAT_FEATURE_TRANSFER_SRC_BIT | VK_FORMAT_FEATURE_TRANSFER_DST_BIT;
    if ((properties.optimalTilingFeatures & needed) != needed)
      editor_check(VK_ERROR_FORMAT_NOT_SUPPORTED, "output format lacks editor attachment/blend/transfer support");
    const auto &current = editor_.composition;
    if (!current.color.image || current.extent.width != extent.width ||
        current.extent.height != extent.height || current.format != format ||
        current.image_count != image_count) {
      EditorComposition replacement;
      editor_create_composition(replacement, extent, format, image_count);
      try {
        // The old composition and all old backend allocations remain charged
        // until replacement succeeded, so admission includes the true peak.
        editor_shutdown_backend();
      } catch (...) {
        editor_destroy_composition(replacement);
        throw;
      }
      editor_destroy_composition(editor_.composition);
      editor_.composition = replacement;
    }
    return true;
  }

  static std::mutex &editor_init_mutex() {
    static std::mutex mutex;
    return mutex;
  }
  static PFN_vkVoidFunction editor_load_function(const char *name, void *user) {
    auto &owner = *static_cast<Renderer *>(user);
    if (!std::strncmp(name, "vkGetPhysicalDevice", 19) ||
        !std::strcmp(name, "vkEnumeratePhysicalDevices") ||
        !std::strcmp(name, "vkDestroySurfaceKHR"))
      return owner.loader.get_instance_proc_addr()(owner.instance, name);
    return owner.f.vkGetDeviceProcAddr(owner.device, name);
  }
  void editor_new_frame() {
    if (!editor_.initialized) {
      if (ImGui::GetIO().BackendRendererUserData)
        throw std::logic_error("Core editor CPU context already has a renderer owner");
      ImGui_ImplVulkan_InitInfo info{};
      info.ApiVersion = VK_API_VERSION_1_1;
      info.Instance = instance;
      info.PhysicalDevice = gpu;
      info.Device = device;
      info.QueueFamily = family;
      info.Queue = queue;
      info.DescriptorPoolSize = IMGUI_IMPL_VULKAN_MINIMUM_SAMPLED_IMAGE_POOL_SIZE;
      info.MinImageCount = 2;
      info.ImageCount = editor_.composition.image_count;
      info.PipelineInfoMain.RenderPass = editor_.composition.pass;
      info.PipelineInfoMain.MSAASamples = VK_SAMPLE_COUNT_1_BIT;
      info.CheckVkResultFn = editor_backend_result;
      info.DeviceMemoryUserData = this;
      info.AllocateDeviceMemoryFn = editor_allocate;
      info.FreeDeviceMemoryFn = editor_free;
      if (editor_.composition.format == VK_FORMAT_B8G8R8A8_SRGB ||
          editor_.composition.format == VK_FORMAT_R8G8B8A8_SRGB) {
        info.CustomShaderFragCreateInfo.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
        info.CustomShaderFragCreateInfo.codeSize = sizeof(editor_srgb_frag_spv);
        info.CustomShaderFragCreateInfo.pCode = editor_srgb_frag_spv;
      }
      // The global loader table is copied by Init into this actual CPU context.
      // Serialize only this real LoadFunctions/Init pair across renderer owners.
      std::lock_guard<std::mutex> lock(editor_init_mutex());
      if (!ImGui_ImplVulkan_LoadFunctions(info.ApiVersion, editor_load_function, this))
        editor_check(VK_ERROR_INITIALIZATION_FAILED, "required editor Vulkan function unavailable");
      if (!ImGui_ImplVulkan_Init(&info))
        editor_check(VK_ERROR_INITIALIZATION_FAILED, "editor backend Init rejected actual device/format configuration");
      editor_.initialized = true;
    }
    ImGui_ImplVulkan_NewFrame();
  }
  struct EditorFrameBackend final : sdlfe::EditorFrameBackend {
    Renderer &owner;
    explicit EditorFrameBackend(Renderer &value) : owner(value) {}
    void new_frame() override { owner.editor_new_frame(); }
  };
  void editor_barrier(VkImage image, VkImageLayout before, VkImageLayout after,
                       VkAccessFlags source_access, VkAccessFlags destination_access,
                       VkPipelineStageFlags source_stage, VkPipelineStageFlags destination_stage) {
    VkImageMemoryBarrier barrier{};
    barrier.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
    barrier.oldLayout = before;
    barrier.newLayout = after;
    barrier.srcAccessMask = source_access;
    barrier.dstAccessMask = destination_access;
    barrier.srcQueueFamilyIndex = barrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
    barrier.image = image;
    barrier.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    f.vkCmdPipelineBarrier(presentCmd, source_stage, destination_stage, 0,
                           0, nullptr, 0, nullptr, 1, &barrier);
  }
  void editor_begin_composition() {
    const auto image = editor_.composition.color.image;
    editor_barrier(image, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                     0, VK_ACCESS_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
                     VK_PIPELINE_STAGE_TRANSFER_BIT);
    const VkClearColorValue black{};
    const VkImageSubresourceRange all{VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
    f.vkCmdClearColorImage(presentCmd, image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, &black, 1, &all);
    editor_barrier(image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                     VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_TRANSFER_WRITE_BIT,
                     VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT);
  }
  void editor_finish_composition(VkImage output) {
    auto &composition = editor_.composition;
    bool rendered = false;
    EditorFrameBackend backend(*this);
    editor_.cpu->frame(backend, [&](ImDrawData *data) {
      if (!data || !std::isfinite(data->DisplayPos.x) || !std::isfinite(data->DisplayPos.y) ||
          data->DisplayPos.x != 0 || data->DisplayPos.y != 0 ||
          !std::isfinite(data->DisplaySize.x) || !std::isfinite(data->DisplaySize.y) ||
          !std::isfinite(data->FramebufferScale.x) || !std::isfinite(data->FramebufferScale.y) ||
          data->DisplaySize.x <= 0 || data->DisplaySize.y <= 0 ||
          data->FramebufferScale.x <= 0 || data->FramebufferScale.y <= 0)
        editor_check(VK_ERROR_INITIALIZATION_FAILED, "editor logical/physical coordinates are invalid");
      const double physical_width = double(data->DisplaySize.x) * data->FramebufferScale.x;
      const double physical_height = double(data->DisplaySize.y) * data->FramebufferScale.y;
      if (std::floor(physical_width + .5) != composition.extent.width ||
          std::floor(physical_height + .5) != composition.extent.height)
        editor_check(VK_ERROR_INITIALIZATION_FAILED, "editor framebuffer scale does not match actual output extent");
      // Real texture uploads own a separate command/fence and must complete
      // before entering the UI pass. RenderDrawData then sees only OK textures.
      if (data->Textures)
        for (ImTextureData *texture : *data->Textures)
          if (texture->Status != ImTextureStatus_OK)
            ImGui_ImplVulkan_UpdateTexture(texture);
      // A deferred destroy may retain a non-OK status. Suppress the backend's
      // automatic catch-up inside the pass, restoring this synchronous borrow
      // on every exit; all queued updates above ran outside the render pass.
      struct RestoreTextures {
        ImDrawData &data;
        ImVector<ImTextureData *> *previous;
        ~RestoreTextures() { data.Textures = previous; }
      } restore_textures{*data, data->Textures};
      data->Textures = nullptr;
      editor_barrier(composition.color.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                       VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, VK_ACCESS_TRANSFER_WRITE_BIT,
                       VK_ACCESS_COLOR_ATTACHMENT_READ_BIT | VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                       VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT);
      VkRenderPassBeginInfo pass{};
      pass.sType = VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO;
      pass.renderPass = composition.pass;
      pass.framebuffer = composition.framebuffer;
      pass.renderArea = {{0, 0}, composition.extent};
      f.vkCmdBeginRenderPass(presentCmd, &pass, VK_SUBPASS_CONTENTS_INLINE);
      try {
        ImGui_ImplVulkan_RenderDrawData(data, presentCmd);
      } catch (...) {
        f.vkCmdEndRenderPass(presentCmd);
        throw;
      }
      f.vkCmdEndRenderPass(presentCmd);
      editor_barrier(composition.color.image, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
                       VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                       VK_ACCESS_TRANSFER_READ_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
                       VK_PIPELINE_STAGE_TRANSFER_BIT);
      editor_save_current_results();
      rendered = true;
      ++editor_.statistics.frames;
    });
    if (!rendered)
      editor_barrier(composition.color.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                       VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_TRANSFER_WRITE_BIT,
                       VK_ACCESS_TRANSFER_READ_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT,
                       VK_PIPELINE_STAGE_TRANSFER_BIT);
    VkImageCopy copy{};
    copy.srcSubresource = copy.dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
    copy.extent = {composition.extent.width, composition.extent.height, 1};
    // Same-format copy preserves the selected UNORM/sRGB encoding byte-for-byte;
    // game scaling and UI compositing have already happened exactly once.
    f.vkCmdCopyImage(presentCmd, composition.color.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                     output, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &copy);
  }
