// Additive Win32 windowed replay; raster body retains the offscreen prototype's semantics.
// Original offscreen sources and receipts remain unchanged.
#define VK_NO_PROTOTYPES
#define VK_USE_PLATFORM_WIN32_KHR
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <vulkan/vulkan.h>
#include <algorithm>
#include <atomic>
#include <chrono>
#include <array>
#include <cmath>
#include <cstring>
#include <fstream>
#include <functional>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static void check(VkResult r, const char *name) {
    if (r != VK_SUCCESS)
        throw std::runtime_error(std::string(name) + ": " + std::to_string(r));
}
static std::atomic<uint32_t> validationMessages{0};
static VKAPI_ATTR VkBool32 VKAPI_CALL debug(VkDebugUtilsMessageSeverityFlagBitsEXT,
                                            VkDebugUtilsMessageTypeFlagsEXT,
                                            const VkDebugUtilsMessengerCallbackDataEXT *data,
                                            void *) {
    ++validationMessages;
    std::cerr << "VALIDATION: " << data->pMessage << '\n';
    return VK_FALSE;
}
struct Cleanup {
    std::vector<std::function<void()>> actions;
    void run() {
        for (auto i = actions.rbegin(); i != actions.rend(); ++i)
            (*i)();
        actions.clear();
    }
    ~Cleanup() { run(); }
};
static std::vector<uint32_t> shader(const char *filename) {
    std::ifstream input(filename, std::ios::binary | std::ios::ate);
    if (!input)
        throw std::runtime_error(std::string("Cannot open shader: ") + filename);
    const auto size = input.tellg();
    if (size < 20 || size % 4 != 0)
        throw std::runtime_error("Invalid SPIR-V size");
    std::vector<uint32_t> words(static_cast<size_t>(size) / 4);
    input.seekg(0);
    input.read(reinterpret_cast<char *>(words.data()), size);
    if (!input || words[0] != 0x07230203)
        throw std::runtime_error("Invalid SPIR-V payload");
    return words;
}

#include "../vulkan-probe/replay_scene.hpp"
#include "presenter.hpp"

int main(int argc, char **argv) {
    if (argc < 4 || argc > 6) {
        std::cerr << "Usage: windowed-replay scene.replay shader-directory output.ppm "
                     "[auto-close-seconds 0..600] [self-test]\n";
        return 2;
    }
    std::cout << std::unitbuf;
    try {
        auto scene = readScene(argv[1]);
        size_t consumed = 0;
        const double seconds = argc >= 5 ? std::stod(argv[4], &consumed) : 0;
        const bool selfTest = argc == 6 && std::string(argv[5]) == "self-test";
        if ((argc >= 5 && consumed != std::strlen(argv[4])) ||
            !std::isfinite(seconds) || seconds < 0 || seconds > 600 ||
            (argc == 6 && !selfTest) || (selfTest && seconds < 4))
            throw std::runtime_error("Invalid close duration or self-test arguments");
        const float offset = 0.5F;
        const std::string sampling = "captured", depthMode = "d32", colorMode = "rgba8";
        const uint32_t scale = 1;
        const VkFormat colorFormat = VK_FORMAT_R8G8B8A8_UNORM;
        const VkFormat depthFormat = VK_FORMAT_D32_SFLOAT;
        NativeWindow window(selfTest ? 640U : 960U, selfTest ? 480U : 720U);
        Cleanup cleanup;
#ifdef _WIN32
        const auto library = LoadLibraryExW(L"vulkan-1.dll", nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32);
        if (!library)
            throw std::runtime_error("Vulkan loader unavailable");
        cleanup.actions.push_back([=] { FreeLibrary(library); });
        auto get = reinterpret_cast<PFN_vkGetInstanceProcAddr>(
            GetProcAddress(library, "vkGetInstanceProcAddr"));
#else
        const auto library = dlopen("libvulkan.so.1", RTLD_NOW | RTLD_LOCAL);
        if (!library)
            throw std::runtime_error("Vulkan loader unavailable");
        cleanup.actions.push_back([=] { dlclose(library); });
        auto get =
            reinterpret_cast<PFN_vkGetInstanceProcAddr>(dlsym(library, "vkGetInstanceProcAddr"));
#endif
        if (!get)
            throw std::runtime_error("Loader entry unavailable");
        auto createInstance =
            reinterpret_cast<PFN_vkCreateInstance>(get(nullptr, "vkCreateInstance"));
        const char *layer = "VK_LAYER_KHRONOS_validation";
        if (!createInstance)
            throw std::runtime_error("vkCreateInstance unavailable");
        auto enumerateInstanceExtensions = reinterpret_cast<PFN_vkEnumerateInstanceExtensionProperties>(
            get(nullptr, "vkEnumerateInstanceExtensionProperties"));
        if (!enumerateInstanceExtensions)
            throw std::runtime_error("Instance extension enumeration unavailable");
        uint32_t instanceExtensionCount = 0;
        check(enumerateInstanceExtensions(nullptr, &instanceExtensionCount, nullptr),
              "instance extension count");
        std::vector<VkExtensionProperties> instanceExtensions(instanceExtensionCount);
        check(enumerateInstanceExtensions(nullptr, &instanceExtensionCount, instanceExtensions.data()),
              "instance extensions");
        auto supportsInstanceExtension = [&](const char *name) {
            return std::any_of(instanceExtensions.begin(), instanceExtensions.end(), [&](const auto &e) {
                return std::strcmp(e.extensionName, name) == 0;
            });
        };
        const bool khrMaintenance = supportsInstanceExtension(VK_KHR_SURFACE_MAINTENANCE_1_EXTENSION_NAME);
        if (!khrMaintenance && !supportsInstanceExtension(VK_EXT_SURFACE_MAINTENANCE_1_EXTENSION_NAME))
            throw std::runtime_error("Driver lacks KHR/EXT surface maintenance1");
        const char *surfaceMaintenance = khrMaintenance ? VK_KHR_SURFACE_MAINTENANCE_1_EXTENSION_NAME :
                                                        VK_EXT_SURFACE_MAINTENANCE_1_EXTENSION_NAME;
        const char *swapchainMaintenance = khrMaintenance ? VK_KHR_SWAPCHAIN_MAINTENANCE_1_EXTENSION_NAME :
                                                          VK_EXT_SWAPCHAIN_MAINTENANCE_1_EXTENSION_NAME;
        std::cout << "Presentation extension: " << swapchainMaintenance << '\n';
        const std::array<const char *, 6> extensions{
            VK_EXT_DEBUG_UTILS_EXTENSION_NAME, VK_EXT_VALIDATION_FEATURES_EXTENSION_NAME,
            VK_KHR_SURFACE_EXTENSION_NAME, VK_KHR_WIN32_SURFACE_EXTENSION_NAME,
            VK_KHR_GET_SURFACE_CAPABILITIES_2_EXTENSION_NAME,
            surfaceMaintenance};
        VkDebugUtilsMessengerCreateInfoEXT debugInfo{
            VK_STRUCTURE_TYPE_DEBUG_UTILS_MESSENGER_CREATE_INFO_EXT};
        debugInfo.messageSeverity = VK_DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT |
                                    VK_DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT;
        debugInfo.messageType = VK_DEBUG_UTILS_MESSAGE_TYPE_GENERAL_BIT_EXT |
                                VK_DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT |
                                VK_DEBUG_UTILS_MESSAGE_TYPE_PERFORMANCE_BIT_EXT;
        debugInfo.pfnUserCallback = debug;
        VkValidationFeatureEnableEXT synchronization =
            VK_VALIDATION_FEATURE_ENABLE_SYNCHRONIZATION_VALIDATION_EXT;
        VkValidationFeaturesEXT validation{VK_STRUCTURE_TYPE_VALIDATION_FEATURES_EXT};
        validation.enabledValidationFeatureCount = 1;
        validation.pEnabledValidationFeatures = &synchronization;
        debugInfo.pNext = &validation;
        VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};
        app.pApplicationName = "MW34 windowed Vulkan Training replay";
        app.apiVersion = VK_API_VERSION_1_1;
        VkInstanceCreateInfo ici{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
        ici.pApplicationInfo = &app;
        ici.pNext = &debugInfo;
        ici.enabledLayerCount = 1;
        ici.ppEnabledLayerNames = &layer;
        ici.enabledExtensionCount = static_cast<uint32_t>(extensions.size());
        ici.ppEnabledExtensionNames = extensions.data();
        VkInstance instance{};
        check(createInstance(&ici, nullptr, &instance), "create instance (validation required)");
#define I(name)                                                                                    \
    auto name = reinterpret_cast<PFN_##name>(get(instance, #name));                                \
    if (!name)                                                                                     \
    throw std::runtime_error(#name " missing")
        I(vkDestroyInstance);
        cleanup.actions.push_back([=] { vkDestroyInstance(instance, nullptr); });
        I(vkCreateDebugUtilsMessengerEXT);
        I(vkDestroyDebugUtilsMessengerEXT);
        debugInfo.pNext = nullptr;
        VkDebugUtilsMessengerEXT messenger{};
        check(vkCreateDebugUtilsMessengerEXT(instance, &debugInfo, nullptr, &messenger),
              "debug messenger");
        cleanup.actions.push_back(
            [=] { vkDestroyDebugUtilsMessengerEXT(instance, messenger, nullptr); });
        I(vkCreateWin32SurfaceKHR);
        I(vkDestroySurfaceKHR);
        I(vkGetPhysicalDeviceSurfaceSupportKHR);
        I(vkEnumerateDeviceExtensionProperties);
        I(vkGetPhysicalDeviceFeatures2);
        VkWin32SurfaceCreateInfoKHR sci{VK_STRUCTURE_TYPE_WIN32_SURFACE_CREATE_INFO_KHR};
        sci.hinstance = GetModuleHandleW(nullptr);
        sci.hwnd = window.handle;
        VkSurfaceKHR surface{};
        check(vkCreateWin32SurfaceKHR(instance, &sci, nullptr, &surface), "Win32 Vulkan surface");
        cleanup.actions.push_back([=] { vkDestroySurfaceKHR(instance, surface, nullptr); });
        I(vkEnumeratePhysicalDevices);
        I(vkGetPhysicalDeviceQueueFamilyProperties);
        I(vkGetPhysicalDeviceProperties);
        I(vkGetPhysicalDeviceMemoryProperties);
        I(vkGetPhysicalDeviceFormatProperties);
        I(vkCreateDevice);
        I(vkGetDeviceProcAddr);
        uint32_t count = 0;
        check(vkEnumeratePhysicalDevices(instance, &count, nullptr), "device count");
        std::vector<VkPhysicalDevice> devices(count);
        check(vkEnumeratePhysicalDevices(instance, &count, devices.data()), "devices");
        VkPhysicalDevice gpu{};
        uint32_t family = 0;
        for (auto candidate : devices) {
            uint32_t n = 0;
            vkGetPhysicalDeviceQueueFamilyProperties(candidate, &n, nullptr);
            std::vector<VkQueueFamilyProperties> queues(n);
            vkGetPhysicalDeviceQueueFamilyProperties(candidate, &n, queues.data());
            uint32_t extensionCount = 0;
            check(vkEnumerateDeviceExtensionProperties(candidate, nullptr, &extensionCount, nullptr),
                  "device extension count");
            std::vector<VkExtensionProperties> available(extensionCount);
            check(vkEnumerateDeviceExtensionProperties(candidate, nullptr, &extensionCount,
                                                       available.data()), "device extensions");
            auto supports = [&](const char *name) {
                return std::any_of(available.begin(), available.end(), [&](const auto &e) {
                    return std::strcmp(e.extensionName, name) == 0;
                });
            };
            if (!supports(VK_KHR_SWAPCHAIN_EXTENSION_NAME) ||
                !supports(swapchainMaintenance))
                continue;
            VkPhysicalDeviceSwapchainMaintenance1FeaturesEXT maintenance{
                VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SWAPCHAIN_MAINTENANCE_1_FEATURES_EXT};
            VkPhysicalDeviceFeatures2 features{VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2};
            features.pNext = &maintenance;
            vkGetPhysicalDeviceFeatures2(candidate, &features);
            if (!maintenance.swapchainMaintenance1)
                continue;
            for (uint32_t i = 0; i < n; ++i) {
                VkBool32 present = VK_FALSE;
                check(vkGetPhysicalDeviceSurfaceSupportKHR(candidate, i, surface, &present),
                      "surface queue support");
                if (!gpu && queues[i].queueCount && (queues[i].queueFlags & VK_QUEUE_GRAPHICS_BIT)
                    && present) {
                    gpu = candidate;
                    family = i;
                }
            }
        }
        if (!gpu)
            throw std::runtime_error("No graphics/present queue with swapchain maintenance1");
        VkPhysicalDeviceProperties props{};
        vkGetPhysicalDeviceProperties(gpu, &props);
        std::cout << "Device: " << props.deviceName << '\n';
        VkFormatProperties colorProperties{};
        vkGetPhysicalDeviceFormatProperties(gpu, colorFormat, &colorProperties);
        const auto requiredColor =
            VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BIT | VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BLEND_BIT;
        if ((colorProperties.optimalTilingFeatures & requiredColor) != requiredColor)
            throw std::runtime_error("Selected color attachment/blending unsupported");
        VkFormatProperties depthProperties{};
        vkGetPhysicalDeviceFormatProperties(gpu, depthFormat, &depthProperties);
        if (!(depthProperties.optimalTilingFeatures &
              VK_FORMAT_FEATURE_DEPTH_STENCIL_ATTACHMENT_BIT))
            throw std::runtime_error("Selected depth format unsupported");
        float priority = 1;
        VkDeviceQueueCreateInfo qci{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
        qci.queueFamilyIndex = family;
        qci.queueCount = 1;
        qci.pQueuePriorities = &priority;
        VkDeviceCreateInfo dci{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
        dci.queueCreateInfoCount = 1;
        dci.pQueueCreateInfos = &qci;
        const std::array<const char *, 2> deviceExtensions{
            VK_KHR_SWAPCHAIN_EXTENSION_NAME, swapchainMaintenance};
        VkPhysicalDeviceSwapchainMaintenance1FeaturesEXT maintenance{
            VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_SWAPCHAIN_MAINTENANCE_1_FEATURES_EXT};
        maintenance.swapchainMaintenance1 = VK_TRUE;
        dci.pNext = &maintenance;
        dci.enabledExtensionCount = static_cast<uint32_t>(deviceExtensions.size());
        dci.ppEnabledExtensionNames = deviceExtensions.data();
        VkDevice device{};
        check(vkCreateDevice(gpu, &dci, nullptr, &device), "device");
#define D(name)                                                                                    \
    auto name = reinterpret_cast<PFN_##name>(vkGetDeviceProcAddr(device, #name));                  \
    if (!name)                                                                                     \
    throw std::runtime_error(#name " missing")
        D(vkDestroyDevice);
        cleanup.actions.push_back([=] { vkDestroyDevice(device, nullptr); });
        D(vkDeviceWaitIdle);
        D(vkGetDeviceQueue);
        D(vkCreateBuffer);
        D(vkDestroyBuffer);
        D(vkGetBufferMemoryRequirements);
        D(vkGetImageMemoryRequirements);
        D(vkAllocateMemory);
        D(vkFreeMemory);
        D(vkBindBufferMemory);
        D(vkBindImageMemory);
        D(vkMapMemory);
        D(vkUnmapMemory);
        D(vkCreateImage);
        D(vkDestroyImage);
        D(vkCreateImageView);
        D(vkDestroyImageView);
        D(vkCreateSampler);
        D(vkDestroySampler);
        D(vkCreateDescriptorSetLayout);
        D(vkDestroyDescriptorSetLayout);
        D(vkCreateDescriptorPool);
        D(vkDestroyDescriptorPool);
        D(vkAllocateDescriptorSets);
        D(vkUpdateDescriptorSets);
        D(vkCreateRenderPass);
        D(vkDestroyRenderPass);
        D(vkCreateFramebuffer);
        D(vkDestroyFramebuffer);
        D(vkCreateShaderModule);
        D(vkDestroyShaderModule);
        D(vkCreatePipelineLayout);
        D(vkDestroyPipelineLayout);
        D(vkCreateGraphicsPipelines);
        D(vkDestroyPipeline);
        D(vkCreateCommandPool);
        D(vkDestroyCommandPool);
        D(vkAllocateCommandBuffers);
        D(vkBeginCommandBuffer);
        D(vkEndCommandBuffer);
        D(vkCmdPipelineBarrier);
        D(vkCmdCopyBufferToImage);
        D(vkCmdCopyImageToBuffer);
        D(vkCmdBeginRenderPass);
        D(vkCmdEndRenderPass);
        D(vkCmdBindPipeline);
        D(vkCmdBindDescriptorSets);
        D(vkCmdPushConstants);
        D(vkCmdDraw);
        D(vkCmdClearAttachments);
        D(vkCmdBlitImage);
        D(vkCmdBindVertexBuffers);
        D(vkCreateFence);
        D(vkDestroyFence);
        D(vkQueueSubmit);
        D(vkWaitForFences);
        D(vkResetFences);
        VkPhysicalDeviceMemoryProperties memProps{};
        vkGetPhysicalDeviceMemoryProperties(gpu, &memProps);
        auto allocate = [&](VkMemoryRequirements req, VkMemoryPropertyFlags flags) {
            uint32_t type = memProps.memoryTypeCount;
            for (uint32_t i = 0; i < memProps.memoryTypeCount; ++i)
                if ((req.memoryTypeBits & (1U << i)) &&
                    (memProps.memoryTypes[i].propertyFlags & flags) == flags) {
                    type = i;
                    break;
                }
            if (type == memProps.memoryTypeCount)
                throw std::runtime_error("Required memory type unavailable");
            VkMemoryAllocateInfo info{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
            info.allocationSize = req.size;
            info.memoryTypeIndex = type;
            VkDeviceMemory memory{};
            check(vkAllocateMemory(device, &info, nullptr, &memory), "memory");
            return memory;
        };
        struct Buffer {
            VkBuffer handle;
            VkDeviceMemory memory;
        };
        auto makeBuffer = [&](VkDeviceSize size, VkBufferUsageFlags usage) {
            VkBufferCreateInfo info{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
            info.size = size;
            info.usage = usage;
            VkBuffer handle{};
            check(vkCreateBuffer(device, &info, nullptr, &handle), "buffer");
            VkMemoryRequirements req{};
            vkGetBufferMemoryRequirements(device, handle, &req);
            VkDeviceMemory memory{};
            try {
                memory = allocate(req, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT |
                                           VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
            } catch (...) {
                vkDestroyBuffer(device, handle, nullptr);
                throw;
            }
            cleanup.actions.push_back([=] {
                vkDestroyBuffer(device, handle, nullptr);
                vkFreeMemory(device, memory, nullptr);
            });
            check(vkBindBufferMemory(device, handle, memory, 0), "bind buffer");
            return Buffer{handle, memory};
        };
        struct Image {
            VkImage handle;
            VkImageView view;
        };
        auto makeImage = [&](uint32_t w, uint32_t h, VkFormat format, VkImageUsageFlags usage,
                             VkImageAspectFlags aspect) {
            VkImageCreateInfo info{VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO};
            info.imageType = VK_IMAGE_TYPE_2D;
            info.format = format;
            info.extent = {w, h, 1};
            info.mipLevels = 1;
            info.arrayLayers = 1;
            info.samples = VK_SAMPLE_COUNT_1_BIT;
            info.tiling = VK_IMAGE_TILING_OPTIMAL;
            info.usage = usage;
            VkImage handle{};
            check(vkCreateImage(device, &info, nullptr, &handle), "image");
            VkMemoryRequirements req{};
            vkGetImageMemoryRequirements(device, handle, &req);
            VkDeviceMemory memory{};
            try {
                memory = allocate(req, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
            } catch (...) {
                vkDestroyImage(device, handle, nullptr);
                throw;
            }
            cleanup.actions.push_back([=] {
                vkDestroyImage(device, handle, nullptr);
                vkFreeMemory(device, memory, nullptr);
            });
            check(vkBindImageMemory(device, handle, memory, 0), "bind image");
            VkImageViewCreateInfo vi{VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO};
            vi.image = handle;
            vi.viewType = VK_IMAGE_VIEW_TYPE_2D;
            vi.format = format;
            vi.subresourceRange = {aspect, 0, 1, 0, 1};
            VkImageView view{};
            check(vkCreateImageView(device, &vi, nullptr, &view), "view");
            cleanup.actions.push_back([=] { vkDestroyImageView(device, view, nullptr); });
            return Image{handle, view};
        };
        const uint32_t width = scene.width * scale, height = scene.height * scale;
        auto upscale = [&](const std::vector<uint8_t> &input) {
            std::vector<uint8_t> output(static_cast<size_t>(width) * height * 4);
            for (uint32_t y = 0; y < height; ++y)
                for (uint32_t x = 0; x < width; ++x)
                    std::memcpy(output.data() + (static_cast<size_t>(y) * width + x) * 4,
                                input.data() +
                                    (static_cast<size_t>(y / scale) * scene.width + x / scale) * 4,
                                4);
            return output;
        };
        void *pointer = nullptr;
        auto uploadBytes = [&](const std::vector<uint8_t> &bytes, VkBufferUsageFlags usage) {
            auto buffer = makeBuffer(bytes.size(), usage);
            check(vkMapMemory(device, buffer.memory, 0, bytes.size(), 0, &pointer), "map upload");
            std::memcpy(pointer, bytes.data(), bytes.size());
            vkUnmapMemory(device, buffer.memory);
            return buffer;
        };
        auto colorBytes = upscale(scene.color);
        if (colorMode == "rgb565") {
            std::vector<uint8_t> compact(colorBytes.size() / 2);
            for (size_t i = 0; i < compact.size() / 2; ++i) {
                const auto r = (static_cast<uint32_t>(colorBytes[i * 4]) * 31 + 127) / 255;
                const auto g = (static_cast<uint32_t>(colorBytes[i * 4 + 1]) * 63 + 127) / 255;
                const auto b = (static_cast<uint32_t>(colorBytes[i * 4 + 2]) * 31 + 127) / 255;
                const auto encoded = static_cast<uint16_t>((r << 11) | (g << 5) | b);
                std::memcpy(compact.data() + i * 2, &encoded, 2);
            }
            colorBytes = std::move(compact);
        }
        auto colorUpload = uploadBytes(colorBytes, VK_BUFFER_USAGE_TRANSFER_SRC_BIT);
        auto depthBytes = upscale(scene.depth);
        if (depthMode == "d16") {
            std::vector<uint8_t> compact(depthBytes.size() / 2);
            for (size_t i = 0; i < compact.size() / 2; ++i) {
                float value;
                std::memcpy(&value, depthBytes.data() + i * 4, 4);
                if (!std::isfinite(value) || value < 0 || value > 1)
                    throw std::runtime_error("Invalid initial depth value");
                const auto encoded = static_cast<uint16_t>(std::lround(value * 65535.0F));
                std::memcpy(compact.data() + i * 2, &encoded, 2);
            }
            depthBytes = std::move(compact);
        }
        auto depthUpload = uploadBytes(depthBytes, VK_BUFFER_USAGE_TRANSFER_SRC_BIT);
        const VkDeviceSize readbackSize =
            static_cast<VkDeviceSize>(width) * height * (colorMode == "rgb565" ? 2 : 4);
        auto readback = makeBuffer(readbackSize, VK_BUFFER_USAGE_TRANSFER_DST_BIT);
        std::vector<Image> textures;
        std::vector<Buffer> uploads;
        for (const auto &t : scene.textures) {
            uploads.push_back(uploadBytes(t.pixels, VK_BUFFER_USAGE_TRANSFER_SRC_BIT));
            textures.push_back(
                makeImage(t.width, t.height, VK_FORMAT_R8G8B8A8_UNORM,
                          VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
                          VK_IMAGE_ASPECT_COLOR_BIT));
        }
        std::vector<uint8_t> vertices;
        std::vector<uint32_t> firstVertices;
        for (const auto &draw : scene.draws) {
            firstVertices.push_back(static_cast<uint32_t>(vertices.size() / 32));
            vertices.insert(vertices.end(), draw.vertices.begin(), draw.vertices.end());
        }
        auto vertexBuffer = uploadBytes(vertices, VK_BUFFER_USAGE_VERTEX_BUFFER_BIT);
        auto color =
            makeImage(width, height, colorFormat,
                      VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT |
                          VK_IMAGE_USAGE_TRANSFER_DST_BIT,
                      VK_IMAGE_ASPECT_COLOR_BIT);
        auto depth =
            makeImage(width, height, depthFormat,
                      VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT,
                      VK_IMAGE_ASPECT_DEPTH_BIT);
        std::array<VkSampler, 8> samplers{};
        for (uint32_t i = 0; i < 8; ++i) {
            VkSamplerCreateInfo si{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};
            si.magFilter = si.minFilter = (i & 4) ? VK_FILTER_LINEAR : VK_FILTER_NEAREST;
            si.mipmapMode = VK_SAMPLER_MIPMAP_MODE_NEAREST;
            si.addressModeU =
                (i & 1) ? VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE : VK_SAMPLER_ADDRESS_MODE_REPEAT;
            si.addressModeV =
                (i & 2) ? VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE : VK_SAMPLER_ADDRESS_MODE_REPEAT;
            si.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
            check(vkCreateSampler(device, &si, nullptr, &samplers[i]), "sampler");
            auto sampler = samplers[i];
            cleanup.actions.push_back([=] { vkDestroySampler(device, sampler, nullptr); });
        }
        VkDescriptorSetLayoutBinding binding{0, VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 1,
                                             VK_SHADER_STAGE_FRAGMENT_BIT, nullptr};
        VkDescriptorSetLayoutCreateInfo li{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
        li.bindingCount = 1;
        li.pBindings = &binding;
        VkDescriptorSetLayout layout{};
        check(vkCreateDescriptorSetLayout(device, &li, nullptr, &layout), "descriptor layout");
        cleanup.actions.push_back([=] { vkDestroyDescriptorSetLayout(device, layout, nullptr); });
        const auto setCount = static_cast<uint32_t>(scene.draws.size());
        VkDescriptorPoolSize poolSize{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, setCount};
        VkDescriptorPoolCreateInfo dpi{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
        dpi.maxSets = setCount;
        dpi.poolSizeCount = 1;
        dpi.pPoolSizes = &poolSize;
        VkDescriptorPool descriptorPool{};
        check(vkCreateDescriptorPool(device, &dpi, nullptr, &descriptorPool), "descriptor pool");
        cleanup.actions.push_back(
            [=] { vkDestroyDescriptorPool(device, descriptorPool, nullptr); });
        std::vector<VkDescriptorSetLayout> layouts(setCount, layout);
        std::vector<VkDescriptorSet> sets(setCount);
        VkDescriptorSetAllocateInfo dai{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
        dai.descriptorPool = descriptorPool;
        dai.descriptorSetCount = setCount;
        dai.pSetLayouts = layouts.data();
        check(vkAllocateDescriptorSets(device, &dai, sets.data()), "descriptor sets");
        for (uint32_t i = 0; i < setCount; ++i) {
            const auto &d = scene.draws[i];
            const bool linear = sampling == "captured" ? d.filtering != 0 : sampling == "linear";
            const uint32_t samplerIndex =
                (d.u == 3 ? 1U : 0U) | (d.v == 3 ? 2U : 0U) | (linear ? 4U : 0U);
            VkDescriptorImageInfo info{samplers[samplerIndex], textures[d.texture].view,
                                       VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
            VkWriteDescriptorSet write{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};
            write.dstSet = sets[i];
            write.descriptorCount = 1;
            write.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
            write.pImageInfo = &info;
            vkUpdateDescriptorSets(device, 1, &write, 0, nullptr);
        }
        std::array<VkAttachmentDescription, 2> attachments{};
        attachments[0].format = colorFormat;
        attachments[0].samples = VK_SAMPLE_COUNT_1_BIT;
        attachments[0].loadOp = VK_ATTACHMENT_LOAD_OP_LOAD;
        attachments[0].storeOp = VK_ATTACHMENT_STORE_OP_STORE;
        attachments[0].initialLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
        attachments[0].finalLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
        attachments[1].format = depthFormat;
        attachments[1].samples = VK_SAMPLE_COUNT_1_BIT;
        attachments[1].loadOp = VK_ATTACHMENT_LOAD_OP_LOAD;
        attachments[1].storeOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
        attachments[1].initialLayout = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;
        attachments[1].finalLayout = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;
        VkAttachmentReference cr{0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL},
            dr{1, VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL};
        VkSubpassDescription subpass{};
        subpass.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
        subpass.colorAttachmentCount = 1;
        subpass.pColorAttachments = &cr;
        subpass.pDepthStencilAttachment = &dr;
        VkRenderPassCreateInfo ri{VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO};
        ri.attachmentCount = 2;
        ri.pAttachments = attachments.data();
        ri.subpassCount = 1;
        ri.pSubpasses = &subpass;
        VkRenderPass renderPass{};
        check(vkCreateRenderPass(device, &ri, nullptr, &renderPass), "render pass");
        cleanup.actions.push_back([=] { vkDestroyRenderPass(device, renderPass, nullptr); });
        const std::array<VkImageView, 2> views{color.view, depth.view};
        VkFramebufferCreateInfo fi{VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO};
        fi.renderPass = renderPass;
        fi.attachmentCount = 2;
        fi.pAttachments = views.data();
        fi.width = width;
        fi.height = height;
        fi.layers = 1;
        VkFramebuffer framebuffer{};
        check(vkCreateFramebuffer(device, &fi, nullptr, &framebuffer), "framebuffer");
        cleanup.actions.push_back([=] { vkDestroyFramebuffer(device, framebuffer, nullptr); });
        std::array<VkPipelineShaderStageCreateInfo, 4> stages{};
        for (size_t i = 0; i < 4; ++i) {
            const std::array<const char *, 4> names{"replay.vert.spv", "replay.frag.spv",
                                                    "replay-flat.vert.spv", "replay-flat.frag.spv"};
            auto filename = std::string(argv[2]) + "/" + names[i];
            auto words = shader(filename.c_str());
            VkShaderModuleCreateInfo mi{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};
            mi.codeSize = words.size() * 4;
            mi.pCode = words.data();
            VkShaderModule module{};
            check(vkCreateShaderModule(device, &mi, nullptr, &module), "shader module");
            cleanup.actions.push_back([=] { vkDestroyShaderModule(device, module, nullptr); });
            stages[i].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
            stages[i].stage =
                i % 2 == 0 ? VK_SHADER_STAGE_VERTEX_BIT : VK_SHADER_STAGE_FRAGMENT_BIT;
            stages[i].module = module;
            stages[i].pName = "main";
        }
        VkPushConstantRange push{VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT, 0, 48};
        VkPipelineLayoutCreateInfo pli{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
        pli.setLayoutCount = 1;
        pli.pSetLayouts = &layout;
        pli.pushConstantRangeCount = 1;
        pli.pPushConstantRanges = &push;
        VkPipelineLayout pipelineLayout{};
        check(vkCreatePipelineLayout(device, &pli, nullptr, &pipelineLayout), "pipeline layout");
        cleanup.actions.push_back(
            [=] { vkDestroyPipelineLayout(device, pipelineLayout, nullptr); });
        VkPipelineVertexInputStateCreateInfo vertex{
            VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};
        VkVertexInputBindingDescription vb{0, 32, VK_VERTEX_INPUT_RATE_VERTEX};
        const std::array<VkVertexInputAttributeDescription, 4> attributes{
            {{0, 0, VK_FORMAT_R32G32B32A32_SFLOAT, 0},
             {1, 0, VK_FORMAT_R32_UINT, 16},
             {2, 0, VK_FORMAT_R32_UINT, 20},
             {3, 0, VK_FORMAT_R32G32_SFLOAT, 24}}};
        vertex.vertexBindingDescriptionCount = 1;
        vertex.pVertexBindingDescriptions = &vb;
        vertex.vertexAttributeDescriptionCount = 4;
        vertex.pVertexAttributeDescriptions = attributes.data();
        VkPipelineInputAssemblyStateCreateInfo assembly{
            VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO};
        assembly.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
        VkViewport viewport{0, 0, static_cast<float>(width), static_cast<float>(height), 0, 1};
        VkRect2D scissor{{0, 0}, {width, height}};
        VkPipelineViewportStateCreateInfo vp{VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};
        vp.viewportCount = 1;
        vp.pViewports = &viewport;
        vp.scissorCount = 1;
        vp.pScissors = &scissor;
        VkPipelineRasterizationStateCreateInfo raster{
            VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};
        raster.polygonMode = VK_POLYGON_MODE_FILL;
        raster.lineWidth = 1;
        VkPipelineMultisampleStateCreateInfo ms{
            VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};
        ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;
        VkPipelineDepthStencilStateCreateInfo ds{
            VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO};
        ds.depthTestEnable = VK_TRUE;
        ds.depthWriteEnable = VK_TRUE;
        ds.depthCompareOp = VK_COMPARE_OP_GREATER;
        VkPipelineColorBlendAttachmentState blend{};
        blend.colorWriteMask = 15;
        blend.blendEnable = VK_TRUE;
        blend.srcColorBlendFactor = VK_BLEND_FACTOR_SRC_ALPHA;
        blend.dstColorBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
        blend.srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE;
        blend.dstAlphaBlendFactor = VK_BLEND_FACTOR_ZERO;
        VkPipelineColorBlendStateCreateInfo bs{
            VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};
        bs.attachmentCount = 1;
        bs.pAttachments = &blend;
        VkGraphicsPipelineCreateInfo pi{VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO};
        pi.stageCount = 2;
        pi.pStages = stages.data();
        pi.pVertexInputState = &vertex;
        pi.pInputAssemblyState = &assembly;
        pi.pViewportState = &vp;
        pi.pRasterizationState = &raster;
        pi.pMultisampleState = &ms;
        pi.pDepthStencilState = &ds;
        pi.pColorBlendState = &bs;
        pi.layout = pipelineLayout;
        pi.renderPass = renderPass;
        std::array<VkPipeline, 8> pipelines{};
        for (uint32_t i = 0; i < 8; ++i) {
            pi.pStages = stages.data() + (i & 2);
            blend.blendEnable = (i & 1) ? VK_TRUE : VK_FALSE;
            ds.depthWriteEnable = (i & 4) ? VK_FALSE : VK_TRUE;
            check(vkCreateGraphicsPipelines(device, VK_NULL_HANDLE, 1, &pi, nullptr, &pipelines[i]),
                  "pipeline");
            auto pipeline = pipelines[i];
            cleanup.actions.push_back([=] { vkDestroyPipeline(device, pipeline, nullptr); });
        }
        VkCommandPoolCreateInfo cpi{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
        cpi.queueFamilyIndex = family;
        VkCommandPool commandPool{};
        check(vkCreateCommandPool(device, &cpi, nullptr, &commandPool), "command pool");
        cleanup.actions.push_back([=] { vkDestroyCommandPool(device, commandPool, nullptr); });
        VkCommandBufferAllocateInfo cai{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
        cai.commandPool = commandPool;
        cai.commandBufferCount = 1;
        VkCommandBuffer command{};
        check(vkAllocateCommandBuffers(device, &cai, &command), "command buffer");
        VkCommandBufferBeginInfo cbi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
        check(vkBeginCommandBuffer(command, &cbi), "begin");
        auto transition = [&](VkImage image, VkImageLayout oldLayout, VkImageLayout newLayout,
                              VkAccessFlags src, VkAccessFlags dst, VkPipelineStageFlags srcStage,
                              VkPipelineStageFlags dstStage,
                              VkImageAspectFlags aspect = VK_IMAGE_ASPECT_COLOR_BIT) {
            VkImageMemoryBarrier b{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};
            b.srcAccessMask = src;
            b.dstAccessMask = dst;
            b.oldLayout = oldLayout;
            b.newLayout = newLayout;
            b.srcQueueFamilyIndex = b.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            b.image = image;
            b.subresourceRange = {aspect, 0, 1, 0, 1};
            vkCmdPipelineBarrier(command, srcStage, dstStage, 0, 0, nullptr, 0, nullptr, 1, &b);
        };
        VkBufferImageCopy copy{};
        auto uploadImage = [&](Image image, Buffer buffer, uint32_t w, uint32_t h,
                               VkImageAspectFlags aspect, VkImageLayout layout,
                               VkAccessFlags access, VkPipelineStageFlags stage) {
            transition(image.handle, VK_IMAGE_LAYOUT_UNDEFINED,
                       VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 0, VK_ACCESS_TRANSFER_WRITE_BIT,
                       VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, aspect);
            copy.imageSubresource = {aspect, 0, 0, 1};
            copy.imageExtent = {w, h, 1};
            vkCmdCopyBufferToImage(command, buffer.handle, image.handle,
                                   VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &copy);
            transition(image.handle, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, layout,
                       VK_ACCESS_TRANSFER_WRITE_BIT, access, VK_PIPELINE_STAGE_TRANSFER_BIT, stage,
                       aspect);
        };
        for (size_t i = 0; i < textures.size(); ++i)
            uploadImage(textures[i], uploads[i], scene.textures[i].width, scene.textures[i].height,
                        VK_IMAGE_ASPECT_COLOR_BIT, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
                        VK_ACCESS_SHADER_READ_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT);
        uploadImage(color, colorUpload, width, height, VK_IMAGE_ASPECT_COLOR_BIT,
                    VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
                    VK_ACCESS_COLOR_ATTACHMENT_READ_BIT | VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                    VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT);
        uploadImage(depth, depthUpload, width, height, VK_IMAGE_ASPECT_DEPTH_BIT,
                    VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,
                    VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT |
                        VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,
                    VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT |
                        VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT);
        std::array<VkClearValue, 2> clears{};
        clears[1].depthStencil.depth = 1;
        VkRenderPassBeginInfo begin{VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO};
        begin.renderPass = renderPass;
        begin.framebuffer = framebuffer;
        begin.renderArea = scissor;
        begin.clearValueCount = 2;
        begin.pClearValues = clears.data();
        vkCmdBeginRenderPass(command, &begin, VK_SUBPASS_CONTENTS_INLINE);
        VkDeviceSize vertexOffset = 0;
        vkCmdBindVertexBuffers(command, 0, 1, &vertexBuffer.handle, &vertexOffset);
        struct Push {
            float viewport[4], fogColor[4];
            uint32_t alpha, fog;
            float offset;
            uint32_t padding;
        };
        static_assert(sizeof(Push) == 48);
        auto replayDraw = [&](size_t i) {
            const auto &d = scene.draws[i];
            const auto pipeline =
                pipelines[(d.shade == 1 ? 2 : 0) + d.blend + (d.depthWrite ? 0 : 4)];
            vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline);
            vkCmdBindDescriptorSets(command, VK_PIPELINE_BIND_POINT_GRAPHICS, pipelineLayout, 0, 1,
                                    &sets[i], 0, nullptr);
            Push values{{0, 0, static_cast<float>(scene.width), static_cast<float>(scene.height)},
                        {static_cast<float>((d.fogColor >> 16) & 255) / 255,
                         static_cast<float>((d.fogColor >> 8) & 255) / 255,
                         static_cast<float>(d.fogColor & 255) / 255, 1},
                        d.alpha,
                        d.fog,
                        offset,
                        0};
            vkCmdPushConstants(command, pipelineLayout, push.stageFlags, 0, sizeof(values),
                               &values);
            vkCmdDraw(command, d.count, 1, firstVertices[i], 0);
        };
        #include "../vulkan-probe/ordered_commands.inc"
        vkCmdEndRenderPass(command);
        transition(color.handle, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
                   VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                   VK_ACCESS_TRANSFER_READ_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
                   VK_PIPELINE_STAGE_TRANSFER_BIT);
        copy.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
        copy.imageExtent = {width, height, 1};
        vkCmdCopyImageToBuffer(command, color.handle, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                               readback.handle, 1, &copy);
        VkMemoryBarrier host{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
        host.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
        host.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
        vkCmdPipelineBarrier(command, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT, 0,
                             1, &host, 0, nullptr, 0, nullptr);
        check(vkEndCommandBuffer(command), "end");
        VkFenceCreateInfo fci{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
        VkFence fence{};
        check(vkCreateFence(device, &fci, nullptr, &fence), "fence");
        cleanup.actions.push_back([=] { vkDestroyFence(device, fence, nullptr); });
        // Registered last: wait before freeing any submitted resources on errors.
        cleanup.actions.push_back([=] { vkDeviceWaitIdle(device); });
        VkQueue queue{};
        vkGetDeviceQueue(device, family, 0, &queue);
        VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO};
        submit.commandBufferCount = 1;
        submit.pCommandBuffers = &command;
        check(vkQueueSubmit(queue, 1, &submit, fence), "submit");
        check(vkWaitForFences(device, 1, &fence, VK_TRUE, 10000000000ULL), "wait");
        check(vkMapMemory(device, readback.memory, 0, readbackSize, 0, &pointer), "map readback");
        std::vector<uint8_t> pixels(width * height * 4);
        if (colorMode == "rgb565") {
            for (size_t i = 0; i < pixels.size() / 4; ++i) {
                uint16_t packed;
                std::memcpy(&packed, static_cast<const uint8_t *>(pointer) + i * 2, 2);
                pixels[i * 4] = static_cast<uint8_t>((((packed >> 11) & 31) * 255 + 15) / 31);
                pixels[i * 4 + 1] = static_cast<uint8_t>((((packed >> 5) & 63) * 255 + 31) / 63);
                pixels[i * 4 + 2] = static_cast<uint8_t>(((packed & 31) * 255 + 15) / 31);
                pixels[i * 4 + 3] = 255;
            }
        } else
            std::memcpy(pixels.data(), pointer, pixels.size());
        vkUnmapMemory(device, readback.memory);
        std::ofstream output(argv[3], std::ios::binary);
        output << "P6\n" << width << " " << height << "\n255\n";
        for (size_t i = 0; i < pixels.size(); i += 4)
            output.write(reinterpret_cast<const char *>(pixels.data() + i), 3);
        output.close();
        if (!output)
            throw std::runtime_error("Cannot write output");
        uint64_t renderPasses = 1;
        PresentationStats statistics{};
        {
            SwapchainPresenter presenter(instance, gpu, device, queue, family, surface, get,
                                         vkGetDeviceProcAddr, width, height, argv[3]);
            auto redraw = [&] {
                check(vkResetFences(device, 1, &fence), "reset render fence");
                check(vkQueueSubmit(queue, 1, &submit, fence), "replay scene submit");
                check(vkWaitForFences(device, 1, &fence, VK_TRUE, 10000000000ULL),
                      "replay scene completion");
                ++renderPasses;
            };
            presenter.run(window, color.handle, redraw, seconds, selfTest);
            presenter.close();
            statistics = presenter.stats;
        }
        cleanup.run();
        if (validationMessages)
            throw std::runtime_error("Validation warnings/errors: " +
                                     std::to_string(validationMessages.load()));
        std::cout << "WINDOWED_RESULT: {\"presented_frames\":" << statistics.frames
                  << ",\"swapchain_generations\":" << statistics.generations
                  << ",\"present_fence_waits\":" << statistics.presentWaits
                  << ",\"render_passes\":" << renderPasses
                  << ",\"draws_per_pass\":" << scene.draws.size()
                  << ",\"scene_width\":" << width << ",\"scene_height\":" << height
                  << ",\"self_test\":" << (selfTest ? "true" : "false")
                  << ",\"window_destroyed\":" << (window.destroyed ? "true" : "false")
                  << ",\"minimize_observed\":" << (window.minimizeSeen ? "true" : "false")
                  << ",\"restore_observed\":" << (window.restoreSeen ? "true" : "false")
                  << ",\"escape_observed\":" << (window.escapeSeen ? "true" : "false")
                  << ",\"validation_messages\":" << validationMessages.load()
                  << ",\"resources_released\":true,\"live_gameplay\":false}\n";
        std::cout << "PASS: windowed replay draws=" << scene.draws.size() << "; offset=" << offset
                  << "; sampling=" << sampling << "; scale=" << scale << "; depth=" << depthMode
                  << "; color=" << colorMode
                  << "; zero validation warnings/errors including teardown; equivalence unproven\n";
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
