#pragma once
// Win32 presentation for the authored replay. No original-game process is touched.
struct NativeWindow {
    HWND handle{};
    bool quit = false, resized = true, minimized = false, destroyed = false;
    bool minimizeSeen = false, restoreSeen = false, escapeSeen = false;
    static constexpr const wchar_t *className = L"MW34WindowedVulkanReplay";
    static LRESULT CALLBACK procedure(HWND hwnd, UINT message, WPARAM w, LPARAM l) {
        auto *self = reinterpret_cast<NativeWindow *>(GetWindowLongPtrW(hwnd, GWLP_USERDATA));
        if (message == WM_NCCREATE) {
            self = static_cast<NativeWindow *>(reinterpret_cast<CREATESTRUCTW *>(l)->lpCreateParams);
            SetWindowLongPtrW(hwnd, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(self));
        }
        if (self) {
            if (message == WM_SIZE) {
                self->resized = true;
                if (w == SIZE_MINIMIZED) {
                    self->minimized = true;
                    self->minimizeSeen = true;
                } else {
                    self->restoreSeen = self->restoreSeen || self->minimized;
                    self->minimized = false;
                }
                return 0;
            }
            if (message == WM_KEYDOWN && w == VK_ESCAPE) {
                self->escapeSeen = true;
                PostMessageW(hwnd, WM_CLOSE, 0, 0);
                return 0;
            }
            if (message == WM_CLOSE) {
                DestroyWindow(hwnd);
                return 0;
            }
            if (message == WM_DESTROY) {
                self->quit = true;
                self->destroyed = true;
                PostQuitMessage(0);
                return 0;
            }
            if (message == WM_ERASEBKGND)
                return 1;
        }
        return DefWindowProcW(hwnd, message, w, l);
    }
    NativeWindow(uint32_t width, uint32_t height) {
        SetProcessDPIAware();
        WNDCLASSEXW wc{};
        wc.cbSize = sizeof(wc);
        wc.style = CS_HREDRAW | CS_VREDRAW;
        wc.lpfnWndProc = procedure;
        wc.hInstance = GetModuleHandleW(nullptr);
        wc.hCursor = LoadCursorW(nullptr, MAKEINTRESOURCEW(32512));
        wc.lpszClassName = className;
        if (!RegisterClassExW(&wc))
            throw std::runtime_error("Cannot register replay window");
        RECT rectangle{0, 0, static_cast<LONG>(width), static_cast<LONG>(height)};
        AdjustWindowRect(&rectangle, WS_OVERLAPPEDWINDOW, FALSE);
        handle = CreateWindowExW(
            0, className, L"MW34 RECOMP - Vulkan Training capture replay - Esc to close",
            WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT,
            rectangle.right - rectangle.left, rectangle.bottom - rectangle.top,
            nullptr, nullptr, wc.hInstance, this);
        if (!handle) {
            UnregisterClassW(className, wc.hInstance);
            throw std::runtime_error("Cannot create replay window");
        }
    }
    ~NativeWindow() {
        if (IsWindow(handle))
            DestroyWindow(handle);
        UnregisterClassW(className, GetModuleHandleW(nullptr));
    }
    void pump() {
        MSG message{};
        while (PeekMessageW(&message, nullptr, 0, 0, PM_REMOVE)) {
            if (message.message == WM_QUIT)
                quit = true;
            TranslateMessage(&message);
            DispatchMessageW(&message);
        }
    }
    VkExtent2D size() const {
        RECT rectangle{};
        GetClientRect(handle, &rectangle);
        return {static_cast<uint32_t>(rectangle.right), static_cast<uint32_t>(rectangle.bottom)};
    }
    void resizeClient(uint32_t width, uint32_t height) {
        RECT r{0, 0, static_cast<LONG>(width), static_cast<LONG>(height)};
        AdjustWindowRect(&r, WS_OVERLAPPEDWINDOW, FALSE);
        if (!SetWindowPos(handle, nullptr, 0, 0, r.right - r.left, r.bottom - r.top,
                          SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE))
            throw std::runtime_error("Self-test resize failed");
    }
};

struct PresentationStats {
    uint64_t frames = 0, generations = 0, presentWaits = 0;
};

class SwapchainPresenter {
    VkInstance instance;
    VkPhysicalDevice gpu;
    VkDevice device;
    VkQueue queue;
    uint32_t family;
    VkSurfaceKHR surface;
    uint32_t sourceWidth, sourceHeight;
    std::string outputPrefix;
    VkSwapchainKHR swapchain{};
    VkExtent2D extent{};
    VkFormat format{};
    std::vector<VkImage> images;
    std::vector<VkSemaphore> finished;
    std::vector<VkFence> presentFences;
    std::vector<bool> presentPending;
    VkSemaphore available{};
    VkFence copyFence{};
    VkCommandPool pool{};
    VkCommandBuffer command{};
    VkBuffer readback{};
    VkDeviceMemory readbackMemory{};
    bool closed = false, generationCaptured = false;
#define F(name) PFN_##name name{};
    F(vkGetPhysicalDeviceSurfaceCapabilitiesKHR)
    F(vkGetPhysicalDeviceSurfaceFormatsKHR)
    F(vkGetPhysicalDeviceFormatProperties)
    F(vkGetPhysicalDeviceMemoryProperties)
    F(vkCreateSwapchainKHR) F(vkDestroySwapchainKHR) F(vkGetSwapchainImagesKHR)
    F(vkAcquireNextImageKHR) F(vkQueuePresentKHR)
    F(vkCreateSemaphore) F(vkDestroySemaphore) F(vkCreateFence) F(vkDestroyFence)
    F(vkWaitForFences) F(vkResetFences) F(vkDeviceWaitIdle) F(vkQueueSubmit)
    F(vkCreateCommandPool) F(vkDestroyCommandPool) F(vkAllocateCommandBuffers)
    F(vkResetCommandBuffer) F(vkBeginCommandBuffer) F(vkEndCommandBuffer)
    F(vkCmdPipelineBarrier) F(vkCmdClearColorImage) F(vkCmdBlitImage) F(vkCmdCopyImageToBuffer)
    F(vkCreateBuffer) F(vkDestroyBuffer) F(vkGetBufferMemoryRequirements)
    F(vkAllocateMemory) F(vkFreeMemory) F(vkBindBufferMemory) F(vkMapMemory) F(vkUnmapMemory)
#undef F
    void waitPresent(size_t index) {
        if (presentPending[index]) {
            check(vkWaitForFences(device, 1, &presentFences[index], VK_TRUE, 10000000000ULL),
                  "presentation completion fence");
            presentPending[index] = false;
            ++stats.presentWaits;
        }
    }
    void releaseSwapchain() {
        // Device fences cover submission; maintenance1 fences separately cover presentation.
        check(vkDeviceWaitIdle(device), "idle before swapchain release");
        for (size_t i = 0; i < presentPending.size(); ++i)
            waitPresent(i);
        if (readback) {
            vkDestroyBuffer(device, readback, nullptr);
            readback = VK_NULL_HANDLE;
        }
        if (readbackMemory) {
            vkFreeMemory(device, readbackMemory, nullptr);
            readbackMemory = VK_NULL_HANDLE;
        }
        for (auto semaphore : finished)
            if (semaphore)
                vkDestroySemaphore(device, semaphore, nullptr);
        for (auto fence : presentFences)
            if (fence)
                vkDestroyFence(device, fence, nullptr);
        finished.clear();
        presentFences.clear();
        presentPending.clear();
        images.clear();
        if (swapchain) {
            vkDestroySwapchainKHR(device, swapchain, nullptr);
            swapchain = VK_NULL_HANDLE;
        }
    }
    void createSwapchain(VkExtent2D windowSize) {
        releaseSwapchain();
        VkSurfaceCapabilitiesKHR caps{};
        check(vkGetPhysicalDeviceSurfaceCapabilitiesKHR(gpu, surface, &caps), "surface capabilities");
        const auto usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT;
        if ((caps.supportedUsageFlags & usage) != usage)
            throw std::runtime_error("Surface lacks transfer/readback usage");
        extent = caps.currentExtent.width != UINT32_MAX ? caps.currentExtent :
            VkExtent2D{std::clamp(windowSize.width, caps.minImageExtent.width, caps.maxImageExtent.width),
                       std::clamp(windowSize.height, caps.minImageExtent.height, caps.maxImageExtent.height)};
        if (!extent.width || !extent.height)
            throw std::runtime_error("Cannot create zero-sized swapchain");
        uint32_t count = 0;
        check(vkGetPhysicalDeviceSurfaceFormatsKHR(gpu, surface, &count, nullptr), "format count");
        std::vector<VkSurfaceFormatKHR> formats(count);
        check(vkGetPhysicalDeviceSurfaceFormatsKHR(gpu, surface, &count, formats.data()), "formats");
        VkSurfaceFormatKHR selected{};
        bool found = false;
        for (auto f : formats)
            if ((f.format == VK_FORMAT_B8G8R8A8_UNORM || f.format == VK_FORMAT_R8G8B8A8_UNORM) &&
                f.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR) {
                selected = f;
                found = true;
                break;
            }
        if (!found)
            throw std::runtime_error("Surface has no supported RGBA/BGRA8 UNORM format");
        format = selected.format;
        VkFormatProperties destination{}, source{};
        vkGetPhysicalDeviceFormatProperties(gpu, format, &destination);
        vkGetPhysicalDeviceFormatProperties(gpu, VK_FORMAT_R8G8B8A8_UNORM, &source);
        if (!(destination.optimalTilingFeatures & VK_FORMAT_FEATURE_BLIT_DST_BIT) ||
            !(source.optimalTilingFeatures & VK_FORMAT_FEATURE_BLIT_SRC_BIT))
            throw std::runtime_error("Replay-to-swapchain blit unsupported");
        VkCompositeAlphaFlagBitsKHR alpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR;
        for (auto candidate : {VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR,
                               VK_COMPOSITE_ALPHA_PRE_MULTIPLIED_BIT_KHR,
                               VK_COMPOSITE_ALPHA_POST_MULTIPLIED_BIT_KHR,
                               VK_COMPOSITE_ALPHA_INHERIT_BIT_KHR})
            if (caps.supportedCompositeAlpha & candidate) {
                alpha = candidate;
                break;
            }
        uint32_t imageCount = caps.minImageCount + 1;
        if (caps.maxImageCount)
            imageCount = std::min(imageCount, caps.maxImageCount);
        VkSwapchainCreateInfoKHR info{VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR};
        info.surface = surface;
        info.minImageCount = imageCount;
        info.imageFormat = selected.format;
        info.imageColorSpace = selected.colorSpace;
        info.imageExtent = extent;
        info.imageArrayLayers = 1;
        info.imageUsage = usage;
        info.imageSharingMode = VK_SHARING_MODE_EXCLUSIVE;
        info.preTransform = caps.currentTransform;
        info.compositeAlpha = alpha;
        info.presentMode = VK_PRESENT_MODE_FIFO_KHR;
        info.clipped = VK_TRUE;
        check(vkCreateSwapchainKHR(device, &info, nullptr, &swapchain), "create swapchain");
        check(vkGetSwapchainImagesKHR(device, swapchain, &count, nullptr), "swapchain image count");
        images.resize(count);
        check(vkGetSwapchainImagesKHR(device, swapchain, &count, images.data()), "swapchain images");
        finished.resize(count);
        presentFences.resize(count);
        presentPending.assign(count, false);
        VkSemaphoreCreateInfo semaphoreInfo{VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO};
        VkFenceCreateInfo fenceInfo{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
        for (uint32_t i = 0; i < count; ++i) {
            check(vkCreateSemaphore(device, &semaphoreInfo, nullptr, &finished[i]), "present semaphore");
            check(vkCreateFence(device, &fenceInfo, nullptr, &presentFences[i]), "present fence");
        }
        VkBufferCreateInfo bufferInfo{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
        bufferInfo.size = static_cast<VkDeviceSize>(extent.width) * extent.height * 4;
        bufferInfo.usage = VK_BUFFER_USAGE_TRANSFER_DST_BIT;
        check(vkCreateBuffer(device, &bufferInfo, nullptr, &readback), "presentation readback");
        VkMemoryRequirements requirements{};
        vkGetBufferMemoryRequirements(device, readback, &requirements);
        VkPhysicalDeviceMemoryProperties memory{};
        vkGetPhysicalDeviceMemoryProperties(gpu, &memory);
        uint32_t type = memory.memoryTypeCount;
        for (uint32_t i = 0; i < memory.memoryTypeCount; ++i)
            if ((requirements.memoryTypeBits & (1U << i)) &&
                (memory.memoryTypes[i].propertyFlags &
                 (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) ==
                 (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT)) {
                type = i;
                break;
            }
        if (type == memory.memoryTypeCount)
            throw std::runtime_error("No coherent presentation readback memory");
        VkMemoryAllocateInfo allocation{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
        allocation.allocationSize = requirements.size;
        allocation.memoryTypeIndex = type;
        check(vkAllocateMemory(device, &allocation, nullptr, &readbackMemory), "readback memory");
        check(vkBindBufferMemory(device, readback, readbackMemory, 0), "bind readback");
        generationCaptured = false;
        ++stats.generations;
        std::cout << "SWAPCHAIN: {\"generation\":" << stats.generations << ",\"width\":"
                  << extent.width << ",\"height\":" << extent.height
                  << ",\"images\":" << count << ",\"format\":" << format << "}\n";
    }
    void dumpPresented() {
        void *pointer = nullptr;
        const size_t bytes = static_cast<size_t>(extent.width) * extent.height * 4;
        check(vkMapMemory(device, readbackMemory, 0, bytes, 0, &pointer), "map presented pixels");
        std::vector<uint8_t> pixels(bytes);
        std::memcpy(pixels.data(), pointer, bytes);
        vkUnmapMemory(device, readbackMemory);
        std::ofstream file(outputPrefix + ".presented-" + std::to_string(stats.generations) + ".ppm",
                           std::ios::binary);
        file << "P6\n" << extent.width << " " << extent.height << "\n255\n";
        for (size_t i = 0; i < pixels.size(); i += 4) {
            const char rgb[3] = {
                static_cast<char>(pixels[i + (format == VK_FORMAT_B8G8R8A8_UNORM ? 2 : 0)]),
                static_cast<char>(pixels[i + 1]),
                static_cast<char>(pixels[i + (format == VK_FORMAT_B8G8R8A8_UNORM ? 0 : 2)])};
            file.write(rgb, 3);
        }
        file.close();
        if (!file)
            throw std::runtime_error("Cannot write presented-image witness");
        generationCaptured = true;
    }
public:
    PresentationStats stats;
    SwapchainPresenter(VkInstance instanceValue, VkPhysicalDevice gpuValue, VkDevice deviceValue,
                       VkQueue queueValue, uint32_t familyValue, VkSurfaceKHR surfaceValue,
                       PFN_vkGetInstanceProcAddr get, PFN_vkGetDeviceProcAddr getDevice,
                       uint32_t width, uint32_t height, const char *prefix)
        : instance(instanceValue), gpu(gpuValue), device(deviceValue), queue(queueValue),
          family(familyValue), surface(surfaceValue), sourceWidth(width), sourceHeight(height),
          outputPrefix(prefix) {
#define LI(name) name = reinterpret_cast<PFN_##name>(get(instance, #name)); \
    if (!name) throw std::runtime_error(#name " missing")
        LI(vkGetPhysicalDeviceSurfaceCapabilitiesKHR);
        LI(vkGetPhysicalDeviceSurfaceFormatsKHR);
        LI(vkGetPhysicalDeviceFormatProperties);
        LI(vkGetPhysicalDeviceMemoryProperties);
#undef LI
#define LD(name) name = reinterpret_cast<PFN_##name>(getDevice(device, #name)); \
    if (!name) throw std::runtime_error(#name " missing")
        LD(vkCreateSwapchainKHR); LD(vkDestroySwapchainKHR); LD(vkGetSwapchainImagesKHR);
        LD(vkAcquireNextImageKHR); LD(vkQueuePresentKHR);
        LD(vkCreateSemaphore); LD(vkDestroySemaphore); LD(vkCreateFence); LD(vkDestroyFence);
        LD(vkWaitForFences); LD(vkResetFences); LD(vkDeviceWaitIdle); LD(vkQueueSubmit);
        LD(vkCreateCommandPool); LD(vkDestroyCommandPool); LD(vkAllocateCommandBuffers);
        LD(vkResetCommandBuffer); LD(vkBeginCommandBuffer); LD(vkEndCommandBuffer);
        LD(vkCmdPipelineBarrier); LD(vkCmdClearColorImage); LD(vkCmdBlitImage); LD(vkCmdCopyImageToBuffer);
        LD(vkCreateBuffer); LD(vkDestroyBuffer); LD(vkGetBufferMemoryRequirements);
        LD(vkAllocateMemory); LD(vkFreeMemory); LD(vkBindBufferMemory); LD(vkMapMemory); LD(vkUnmapMemory);
#undef LD
        try {
            VkSemaphoreCreateInfo si{VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO};
            check(vkCreateSemaphore(device, &si, nullptr, &available), "acquire semaphore");
            VkFenceCreateInfo fi{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
            fi.flags = VK_FENCE_CREATE_SIGNALED_BIT;
            check(vkCreateFence(device, &fi, nullptr, &copyFence), "copy fence");
            VkCommandPoolCreateInfo pi{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
            pi.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
            pi.queueFamilyIndex = family;
            check(vkCreateCommandPool(device, &pi, nullptr, &pool), "presentation command pool");
            VkCommandBufferAllocateInfo ai{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
            ai.commandPool = pool;
            ai.commandBufferCount = 1;
            check(vkAllocateCommandBuffers(device, &ai, &command), "presentation command buffer");
        } catch (...) {
            close();
            throw;
        }
    }
    ~SwapchainPresenter() {
        if (!closed)
            try { close(); } catch (const std::exception &e) {
                std::cerr << "Presentation teardown: " << e.what() << '\n';
            }
    }
    void close() {
        if (closed)
            return;
        releaseSwapchain();
        if (pool)
            vkDestroyCommandPool(device, pool, nullptr);
        if (copyFence)
            vkDestroyFence(device, copyFence, nullptr);
        if (available)
            vkDestroySemaphore(device, available, nullptr);
        closed = true;
    }
    void run(NativeWindow &window, VkImage source, const std::function<void()> &redraw,
             double seconds, bool selfTest) {
        ShowWindow(window.handle, SW_SHOW);
        if (!IsWindowVisible(window.handle))
            ShowWindow(window.handle, SW_SHOW);
        if (!IsWindowVisible(window.handle))
            throw std::runtime_error("Replay window did not become visible");
        std::cout << "WINDOW_VISIBLE: true\n";
        const auto started = std::chrono::steady_clock::now();
        uint32_t testStage = 0;
        bool closeRequested = false;
        while (!window.quit) {
            window.pump();
            if (window.quit)
                break;
            const double elapsed = std::chrono::duration<double>(
                std::chrono::steady_clock::now() - started).count();
            if (selfTest) {
                if (testStage == 0 && elapsed > 0.6) {
                    window.resizeClient(853, 480);
                    ++testStage;
                } else if (testStage == 1 && elapsed > 1.4) {
                    ShowWindow(window.handle, SW_MINIMIZE);
                    ++testStage;
                } else if (testStage == 2 && elapsed > 1.9) {
                    ShowWindow(window.handle, SW_RESTORE);
                    ++testStage;
                } else if (testStage == 3 && elapsed > 2.7) {
                    window.resizeClient(640, 480);
                    ++testStage;
                }
            }
            if (seconds > 0 && elapsed >= seconds && !closeRequested) {
                PostMessageW(window.handle, selfTest ? WM_KEYDOWN : WM_CLOSE,
                             selfTest ? VK_ESCAPE : 0, 0);
                closeRequested = true;
            }
            const auto size = window.size();
            if (window.minimized || !size.width || !size.height) {
                // Own-window message wait, not a busy render loop or zero-size swapchain.
                MsgWaitForMultipleObjects(0, nullptr, FALSE, 50, QS_ALLINPUT);
                continue;
            }
            if (!swapchain || window.resized) {
                createSwapchain(size);
                window.resized = false;
            }
            uint32_t index = 0;
            const auto acquire = vkAcquireNextImageKHR(device, swapchain, 100000000ULL,
                                                       available, VK_NULL_HANDLE, &index);
            if (acquire == VK_TIMEOUT || acquire == VK_NOT_READY)
                continue;
            if (acquire == VK_ERROR_OUT_OF_DATE_KHR) {
                window.resized = true;
                continue;
            }
            if (acquire != VK_SUCCESS && acquire != VK_SUBOPTIMAL_KHR)
                check(acquire, "acquire swapchain image");
            waitPresent(index);
            check(vkResetFences(device, 1, &presentFences[index]), "reset present fence");
            check(vkWaitForFences(device, 1, &copyFence, VK_TRUE, 10000000000ULL), "previous copy");
            // The complete saved draw sequence is executed anew for every presentation.
            redraw();
            check(vkResetCommandBuffer(command, 0), "reset presentation commands");
            VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
            check(vkBeginCommandBuffer(command, &begin), "begin presentation");
            auto barrier = [&](VkImageLayout oldLayout, VkImageLayout newLayout,
                               VkAccessFlags src, VkAccessFlags dst,
                               VkPipelineStageFlags srcStage, VkPipelineStageFlags dstStage) {
                VkImageMemoryBarrier b{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};
                b.oldLayout = oldLayout;
                b.newLayout = newLayout;
                b.srcAccessMask = src;
                b.dstAccessMask = dst;
                b.srcQueueFamilyIndex = b.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
                b.image = images[index];
                b.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
                vkCmdPipelineBarrier(command, srcStage, dstStage, 0, 0, nullptr, 0, nullptr, 1, &b);
            };
            barrier(VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 0,
                    VK_ACCESS_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT,
                    VK_PIPELINE_STAGE_TRANSFER_BIT);
            VkClearColorValue black{{0, 0, 0, 1}};
            VkImageSubresourceRange range{VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
            vkCmdClearColorImage(command, images[index], VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                                &black, 1, &range);
            barrier(VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                    VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_TRANSFER_WRITE_BIT,
                    VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT);
            const double fit = std::min(static_cast<double>(extent.width) / sourceWidth,
                                        static_cast<double>(extent.height) / sourceHeight);
            const int32_t w = std::max(1, static_cast<int32_t>(sourceWidth * fit));
            const int32_t h = std::max(1, static_cast<int32_t>(sourceHeight * fit));
            const int32_t left = (static_cast<int32_t>(extent.width) - w) / 2;
            const int32_t top = (static_cast<int32_t>(extent.height) - h) / 2;
            VkImageBlit blit{};
            blit.srcSubresource = blit.dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
            blit.srcOffsets[1] = {static_cast<int32_t>(sourceWidth), static_cast<int32_t>(sourceHeight), 1};
            blit.dstOffsets[0] = {left, top, 0};
            blit.dstOffsets[1] = {left + w, top + h, 1};
            vkCmdBlitImage(command, source, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                           images[index], VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &blit, VK_FILTER_NEAREST);
            barrier(VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                    VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT,
                    VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT);
            if (!generationCaptured) {
                VkBufferImageCopy copy{};
                copy.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
                copy.imageExtent = {extent.width, extent.height, 1};
                vkCmdCopyImageToBuffer(command, images[index], VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                                       readback, 1, &copy);
                VkMemoryBarrier host{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
                host.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
                host.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
                vkCmdPipelineBarrier(command, VK_PIPELINE_STAGE_TRANSFER_BIT,
                                     VK_PIPELINE_STAGE_HOST_BIT, 0, 1, &host, 0, nullptr, 0, nullptr);
            }
            barrier(VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
                    VK_ACCESS_TRANSFER_READ_BIT, 0, VK_PIPELINE_STAGE_TRANSFER_BIT,
                    VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT);
            check(vkEndCommandBuffer(command), "end presentation");
            check(vkResetFences(device, 1, &copyFence), "reset copy fence");
            const VkPipelineStageFlags waitStage = VK_PIPELINE_STAGE_TRANSFER_BIT;
            VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO};
            submit.waitSemaphoreCount = 1;
            submit.pWaitSemaphores = &available;
            submit.pWaitDstStageMask = &waitStage;
            submit.commandBufferCount = 1;
            submit.pCommandBuffers = &command;
            submit.signalSemaphoreCount = 1;
            submit.pSignalSemaphores = &finished[index];
            check(vkQueueSubmit(queue, 1, &submit, copyFence), "copy to swapchain");
            VkSwapchainPresentFenceInfoEXT fenceInfo{VK_STRUCTURE_TYPE_SWAPCHAIN_PRESENT_FENCE_INFO_EXT};
            fenceInfo.swapchainCount = 1;
            fenceInfo.pFences = &presentFences[index];
            VkPresentInfoKHR present{VK_STRUCTURE_TYPE_PRESENT_INFO_KHR};
            present.pNext = &fenceInfo;
            present.waitSemaphoreCount = 1;
            present.pWaitSemaphores = &finished[index];
            present.swapchainCount = 1;
            present.pSwapchains = &swapchain;
            present.pImageIndices = &index;
            const auto result = vkQueuePresentKHR(queue, &present);
            if (result != VK_SUCCESS && result != VK_SUBOPTIMAL_KHR &&
                result != VK_ERROR_OUT_OF_DATE_KHR)
                check(result, "queue presentation");
            presentPending[index] = true;
            ++stats.frames;
            check(vkWaitForFences(device, 1, &copyFence, VK_TRUE, 10000000000ULL), "swapchain copy completion");
            if (!generationCaptured)
                dumpPresented();
            if (result != VK_SUCCESS || acquire == VK_SUBOPTIMAL_KHR)
                window.resized = true;
        }
        if (!stats.frames || (selfTest && (stats.generations < 3 || !window.minimizeSeen ||
                                          !window.restoreSeen || !window.escapeSeen)))
            throw std::runtime_error("Window presentation/lifecycle self-test incomplete");
    }
};
