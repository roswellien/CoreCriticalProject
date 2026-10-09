// Authored Vulkan bootstrap. No game assets or recovered game code.
#define VK_NO_PROTOTYPES
#include <vulkan/vulkan_core.h>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#else
#include <dlfcn.h>
#endif
#include <algorithm>
#include <array>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

static void check(VkResult result, const char* operation) {
    if (result != VK_SUCCESS)
        throw std::runtime_error(std::string(operation) + ": VkResult=" + std::to_string(result));
}

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "Usage: vulkan-probe output.ppm\n";
        return 2;
    }
#ifdef _WIN32
    const auto library = LoadLibraryExW(L"vulkan-1.dll", nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32);
    auto get = library ? reinterpret_cast<PFN_vkGetInstanceProcAddr>(GetProcAddress(library, "vkGetInstanceProcAddr")) : nullptr;
#else
    const auto library = dlopen("libvulkan.so.1", RTLD_NOW | RTLD_LOCAL);
    auto get = library ? reinterpret_cast<PFN_vkGetInstanceProcAddr>(dlsym(library, "vkGetInstanceProcAddr")) : nullptr;
#endif
    if (!get) { std::cerr << "Vulkan loader unavailable\n"; return 3; }
    VkInstance instance = VK_NULL_HANDLE;
    VkDevice device = VK_NULL_HANDLE;
    VkBuffer buffer = VK_NULL_HANDLE;
    VkDeviceMemory memory = VK_NULL_HANDLE;
    VkCommandPool pool = VK_NULL_HANDLE;
    VkFence fence = VK_NULL_HANDLE;
    PFN_vkDestroyInstance destroyInstance = nullptr;
    PFN_vkDestroyDevice destroyDevice = nullptr;
    PFN_vkDestroyBuffer destroyBuffer = nullptr;
    PFN_vkFreeMemory freeMemory = nullptr;
    PFN_vkDestroyCommandPool destroyPool = nullptr;
    PFN_vkDestroyFence destroyFence = nullptr;
    PFN_vkDeviceWaitIdle waitIdle = nullptr;
    PFN_vkUnmapMemory unmap = nullptr;
    bool mapped = false;
    int result = 0;
    try {
        auto createInstance = reinterpret_cast<PFN_vkCreateInstance>(get(nullptr, "vkCreateInstance"));
        if (!createInstance) throw std::runtime_error("vkCreateInstance unavailable");
        VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};
        app.pApplicationName = "MW34 authored Vulkan probe";
        app.apiVersion = VK_API_VERSION_1_0;
        VkInstanceCreateInfo ici{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
        ici.pApplicationInfo = &app;
        check(createInstance(&ici, nullptr, &instance), "create instance");
#define INSTANCE(type, name) auto name = reinterpret_cast<type>(get(instance, #name)); if (!name) throw std::runtime_error(#name " unavailable")
        destroyInstance = reinterpret_cast<PFN_vkDestroyInstance>(get(instance, "vkDestroyInstance"));
        INSTANCE(PFN_vkEnumeratePhysicalDevices, vkEnumeratePhysicalDevices);
        INSTANCE(PFN_vkGetPhysicalDeviceProperties, vkGetPhysicalDeviceProperties);
        INSTANCE(PFN_vkGetPhysicalDeviceQueueFamilyProperties, vkGetPhysicalDeviceQueueFamilyProperties);
        INSTANCE(PFN_vkGetPhysicalDeviceMemoryProperties, vkGetPhysicalDeviceMemoryProperties);
        INSTANCE(PFN_vkEnumerateDeviceExtensionProperties, vkEnumerateDeviceExtensionProperties);
        INSTANCE(PFN_vkCreateDevice, vkCreateDevice);
        INSTANCE(PFN_vkGetDeviceProcAddr, vkGetDeviceProcAddr);
        uint32_t count = 0;
        check(vkEnumeratePhysicalDevices(instance, &count, nullptr), "count devices");
        if (!count) throw std::runtime_error("No Vulkan devices");
        std::vector<VkPhysicalDevice> physical(count);
        check(vkEnumeratePhysicalDevices(instance, &count, physical.data()), "enumerate devices");
        physical.resize(count);
        VkPhysicalDevice selected = VK_NULL_HANDLE;
        uint32_t family = 0;
        for (const auto gpu : physical) {
            VkPhysicalDeviceProperties properties{};
            vkGetPhysicalDeviceProperties(gpu, &properties);
            std::cout << "Device: " << properties.deviceName << " Vulkan "
                      << VK_API_VERSION_MAJOR(properties.apiVersion) << '.'
                      << VK_API_VERSION_MINOR(properties.apiVersion) << '.'
                      << VK_API_VERSION_PATCH(properties.apiVersion) << '\n';
            uint32_t extensionCount = 0;
            check(vkEnumerateDeviceExtensionProperties(gpu, nullptr, &extensionCount, nullptr), "count extensions");
            std::vector<VkExtensionProperties> extensions(extensionCount);
            check(vkEnumerateDeviceExtensionProperties(gpu, nullptr, &extensionCount, extensions.data()), "enumerate extensions");
            for (const char* wanted : {"VK_KHR_swapchain", "VK_KHR_ray_query", "VK_KHR_ray_tracing_pipeline", "VK_KHR_acceleration_structure", "VK_KHR_portability_subset"}) {
                const bool present = std::any_of(extensions.begin(), extensions.end(), [wanted](const auto& e) { return std::strcmp(e.extensionName, wanted) == 0; });
                std::cout << "  " << wanted << ": " << (present ? "advertised" : "absent") << '\n';
            }
            uint32_t queueCount = 0;
            vkGetPhysicalDeviceQueueFamilyProperties(gpu, &queueCount, nullptr);
            std::vector<VkQueueFamilyProperties> queues(queueCount);
            vkGetPhysicalDeviceQueueFamilyProperties(gpu, &queueCount, queues.data());
            for (uint32_t i = 0; i < queueCount; ++i) {
                if (!selected && queues[i].queueCount && (queues[i].queueFlags & VK_QUEUE_GRAPHICS_BIT)) {
                    selected = gpu; family = i;
                }
            }
        }
        if (!selected) throw std::runtime_error("No graphics queue");
        const float priority = 1.0F;
        VkDeviceQueueCreateInfo qci{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
        qci.queueFamilyIndex = family; qci.queueCount = 1; qci.pQueuePriorities = &priority;
        VkDeviceCreateInfo dci{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
        dci.queueCreateInfoCount = 1; dci.pQueueCreateInfos = &qci;
        check(vkCreateDevice(selected, &dci, nullptr, &device), "create device");
#define DEVICE(type, name) auto name = reinterpret_cast<type>(vkGetDeviceProcAddr(device, #name)); if (!name) throw std::runtime_error(#name " unavailable")
        destroyDevice = reinterpret_cast<PFN_vkDestroyDevice>(vkGetDeviceProcAddr(device, "vkDestroyDevice"));
        destroyBuffer = reinterpret_cast<PFN_vkDestroyBuffer>(vkGetDeviceProcAddr(device, "vkDestroyBuffer"));
        freeMemory = reinterpret_cast<PFN_vkFreeMemory>(vkGetDeviceProcAddr(device, "vkFreeMemory"));
        destroyPool = reinterpret_cast<PFN_vkDestroyCommandPool>(vkGetDeviceProcAddr(device, "vkDestroyCommandPool"));
        destroyFence = reinterpret_cast<PFN_vkDestroyFence>(vkGetDeviceProcAddr(device, "vkDestroyFence"));
        waitIdle = reinterpret_cast<PFN_vkDeviceWaitIdle>(vkGetDeviceProcAddr(device, "vkDeviceWaitIdle"));
        unmap = reinterpret_cast<PFN_vkUnmapMemory>(vkGetDeviceProcAddr(device, "vkUnmapMemory"));
        DEVICE(PFN_vkGetDeviceQueue, vkGetDeviceQueue);
        DEVICE(PFN_vkCreateBuffer, vkCreateBuffer);
        DEVICE(PFN_vkGetBufferMemoryRequirements, vkGetBufferMemoryRequirements);
        DEVICE(PFN_vkAllocateMemory, vkAllocateMemory);
        DEVICE(PFN_vkBindBufferMemory, vkBindBufferMemory);
        DEVICE(PFN_vkCreateCommandPool, vkCreateCommandPool);
        DEVICE(PFN_vkAllocateCommandBuffers, vkAllocateCommandBuffers);
        DEVICE(PFN_vkBeginCommandBuffer, vkBeginCommandBuffer);
        DEVICE(PFN_vkCmdFillBuffer, vkCmdFillBuffer);
        DEVICE(PFN_vkCmdPipelineBarrier, vkCmdPipelineBarrier);
        DEVICE(PFN_vkEndCommandBuffer, vkEndCommandBuffer);
        DEVICE(PFN_vkCreateFence, vkCreateFence);
        DEVICE(PFN_vkQueueSubmit, vkQueueSubmit);
        DEVICE(PFN_vkWaitForFences, vkWaitForFences);
        DEVICE(PFN_vkMapMemory, vkMapMemory);
        constexpr uint32_t width = 256, height = 256;
        constexpr VkDeviceSize bytes = width * height * 4;
        VkBufferCreateInfo bci{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
        bci.size = bytes; bci.usage = VK_BUFFER_USAGE_TRANSFER_DST_BIT;
        check(vkCreateBuffer(device, &bci, nullptr, &buffer), "create buffer");
        VkMemoryRequirements requirements{};
        vkGetBufferMemoryRequirements(device, buffer, &requirements);
        VkPhysicalDeviceMemoryProperties properties{};
        vkGetPhysicalDeviceMemoryProperties(selected, &properties);
        uint32_t memoryType = properties.memoryTypeCount;
        for (uint32_t i = 0; i < properties.memoryTypeCount; ++i) {
            const auto required = VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT;
            if ((requirements.memoryTypeBits & (1U << i)) && (properties.memoryTypes[i].propertyFlags & required) == required) { memoryType = i; break; }
        }
        if (memoryType == properties.memoryTypeCount) throw std::runtime_error("No coherent host-visible buffer memory; noncoherent path not implemented");
        VkMemoryAllocateInfo mai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
        mai.allocationSize = requirements.size; mai.memoryTypeIndex = memoryType;
        check(vkAllocateMemory(device, &mai, nullptr, &memory), "allocate memory");
        check(vkBindBufferMemory(device, buffer, memory, 0), "bind buffer");
        VkCommandPoolCreateInfo pci{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
        pci.queueFamilyIndex = family;
        check(vkCreateCommandPool(device, &pci, nullptr, &pool), "create pool");
        VkCommandBufferAllocateInfo cai{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
        cai.commandPool = pool; cai.commandBufferCount = 1;
        VkCommandBuffer command = VK_NULL_HANDLE;
        check(vkAllocateCommandBuffers(device, &cai, &command), "allocate command");
        VkCommandBufferBeginInfo cbi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
        cbi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        check(vkBeginCommandBuffer(command, &cbi), "begin command");
        constexpr std::array<uint32_t, 4> colors{0xff334499U, 0xff449933U, 0xff994433U, 0xffbbbbbbU};
        for (size_t i = 0; i < colors.size(); ++i) vkCmdFillBuffer(command, buffer, i * bytes / 4, bytes / 4, colors[i]);
        VkMemoryBarrier barrier{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
        barrier.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT; barrier.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
        vkCmdPipelineBarrier(command, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT, 0, 1, &barrier, 0, nullptr, 0, nullptr);
        check(vkEndCommandBuffer(command), "end command");
        VkFenceCreateInfo fci{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
        check(vkCreateFence(device, &fci, nullptr, &fence), "create fence");
        VkQueue queue = VK_NULL_HANDLE;
        vkGetDeviceQueue(device, family, 0, &queue);
        VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO};
        submit.commandBufferCount = 1; submit.pCommandBuffers = &command;
        check(vkQueueSubmit(queue, 1, &submit, fence), "submit");
        check(vkWaitForFences(device, 1, &fence, VK_TRUE, 10000000000ULL), "wait fence");
        void* data = nullptr;
        check(vkMapMemory(device, memory, 0, bytes, 0, &data), "map readback");
        mapped = true;
        const auto* pixels = static_cast<const uint32_t*>(data);
        for (uint32_t i = 0; i < width * height; ++i) {
            if (pixels[i] != colors[i / (width * height / 4)]) throw std::runtime_error("GPU readback mismatch at pixel " + std::to_string(i));
        }
        std::ofstream output(argv[1], std::ios::binary);
        output << "P6\n" << width << ' ' << height << "\n255\n";
        for (uint32_t i = 0; i < width * height; ++i) {
            const char rgb[3]{static_cast<char>(pixels[i] & 255U), static_cast<char>((pixels[i] >> 8U) & 255U), static_cast<char>((pixels[i] >> 16U) & 255U)};
            output.write(rgb, 3);
        }
        output.close();
        if (!output) throw std::runtime_error("Cannot write output");
        std::cout << "PASS: 65536 GPU-written words verified; authored transfer swatch saved to " << argv[1] << "\n";
        std::cout << "Scope: no shaders, rasterization, swapchain, validation layers, game frame or ray-tracing feature enablement.\n";
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; result = 1; }
    if (device && waitIdle) waitIdle(device);
    if (mapped && unmap) unmap(device, memory);
    if (fence && destroyFence) destroyFence(device, fence, nullptr);
    if (pool && destroyPool) destroyPool(device, pool, nullptr);
    if (buffer && destroyBuffer) destroyBuffer(device, buffer, nullptr);
    if (memory && freeMemory) freeMemory(device, memory, nullptr);
    if (device && destroyDevice) destroyDevice(device, nullptr);
    if (instance && destroyInstance) destroyInstance(instance, nullptr);
#ifdef _WIN32
    FreeLibrary(library);
#else
    dlclose(library);
#endif
    return result;
}
