// Diagnostic only: creates real FSR contexts; never dispatches game frames.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#define VK_NO_PROTOTYPES
#include <cstdio>
#include <cstdlib>
#include <ffx_api.h>
#include <ffx_upscale.h>
#include <filesystem>
#include <stdexcept>
#include <string>
#include <vector>
#include <vk/ffx_api_vk.h>
#include <vulkan/vulkan.h>
#include <windows.h>

static void require(bool condition, const char *message) {
    if (!condition)
        throw std::runtime_error(message);
}
static void vk_check(VkResult result, const char *operation) {
    std::printf("vulkan %s=%d\n", operation, result);
    require(result == VK_SUCCESS, operation);
}
static void ffx_check(ffxReturnCode_t result, const char *operation) {
    std::printf("fsr %s=%u\n", operation, unsigned(result));
    require(result == FFX_API_RETURN_OK, operation);
}
int wmain(int argc, wchar_t **argv) {
    // Flush every line so failures inside a provider retain their last operation.
    std::setvbuf(stdout, nullptr, _IONBF, 0);
    try {
        require(argc == 3, "Usage: probe.exe <absolute SDK signedbin directory> <GPU index>");
        const std::filesystem::path folder(argv[1]);
        require(folder.is_absolute(), "SDK directory must be absolute");
        const auto loader_path = folder / L"amd_fidelityfx_loader_vk.dll";
        auto sdk = LoadLibraryExW(loader_path.c_str(), nullptr,
                                  LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32);
        require(sdk != nullptr, "Cannot load the pinned FSR loader");
        auto create =
            reinterpret_cast<decltype(&ffxCreateContext)>(GetProcAddress(sdk, "ffxCreateContext"));
        auto destroy = reinterpret_cast<decltype(&ffxDestroyContext)>(
            GetProcAddress(sdk, "ffxDestroyContext"));
        auto query = reinterpret_cast<decltype(&ffxQuery)>(GetProcAddress(sdk, "ffxQuery"));
        require(create && destroy && query, "Missing FSR exports");
        auto vulkan = LoadLibraryExW(L"vulkan-1.dll", nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32);
        require(vulkan != nullptr, "Vulkan loader unavailable");
        auto get = reinterpret_cast<PFN_vkGetInstanceProcAddr>(
            GetProcAddress(vulkan, "vkGetInstanceProcAddr"));
        require(get != nullptr, "Vulkan entry point unavailable");
#define GLOBAL(name)                                                                               \
    auto name = reinterpret_cast<PFN_##name>(get(nullptr, #name));                                 \
    require(name != nullptr, #name)
        GLOBAL(vkCreateInstance);
        VkApplicationInfo app{};
        app.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
        app.pApplicationName = "MW34 FSR feasibility";
        app.apiVersion = VK_API_VERSION_1_3;
        VkInstanceCreateInfo instance_info{};
        instance_info.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
        instance_info.pApplicationInfo = &app;
        VkInstance instance{};
        vk_check(vkCreateInstance(&instance_info, nullptr, &instance), "create_instance_1_3");
#define INSTANCE(name)                                                                             \
    auto name = reinterpret_cast<PFN_##name>(get(instance, #name));                                \
    require(name != nullptr, #name)
        INSTANCE(vkEnumeratePhysicalDevices);
        INSTANCE(vkGetPhysicalDeviceProperties);
        INSTANCE(vkGetPhysicalDeviceFeatures2);
        INSTANCE(vkGetPhysicalDeviceQueueFamilyProperties);
        INSTANCE(vkGetPhysicalDeviceFormatProperties);
        INSTANCE(vkCreateDevice);
        INSTANCE(vkDestroyInstance);
        INSTANCE(vkGetDeviceProcAddr);
        uint32_t count{};
        vk_check(vkEnumeratePhysicalDevices(instance, &count, nullptr), "device_count");
        std::vector<VkPhysicalDevice> devices(count);
        vk_check(vkEnumeratePhysicalDevices(instance, &count, devices.data()), "devices");
        for (uint32_t i = 0; i < count; ++i) {
            VkPhysicalDeviceProperties properties{};
            vkGetPhysicalDeviceProperties(devices[i], &properties);
            std::printf("gpu[%u]=%s vendor=%x device=%x driver=%u api=%u\n", i,
                        properties.deviceName, properties.vendorID, properties.deviceID,
                        properties.driverVersion, properties.apiVersion);
        }
        wchar_t *end{};
        const auto index = std::wcstoul(argv[2], &end, 10);
        require(end != argv[2] && *end == 0 && index < count, "Invalid GPU index");
        const auto gpu = devices[index];
        uint32_t family_count{};
        vkGetPhysicalDeviceQueueFamilyProperties(gpu, &family_count, nullptr);
        std::vector<VkQueueFamilyProperties> families(family_count);
        vkGetPhysicalDeviceQueueFamilyProperties(gpu, &family_count, families.data());
        uint32_t family = 0;
        while (family < family_count && !(families[family].queueCount &&
                                          (families[family].queueFlags & VK_QUEUE_COMPUTE_BIT)))
            ++family;
        require(family < family_count, "No compute queue");
        std::printf("queue_family=%u flags=%u\n", family, families[family].queueFlags);
        // This is a broad feasibility profile, not the production minimum.
        // Enable only features returned as supported, keeping core versions chained.
        VkPhysicalDeviceVulkan13Features features13{};
        features13.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_3_FEATURES;
        VkPhysicalDeviceVulkan12Features features12{};
        features12.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_2_FEATURES;
        VkPhysicalDeviceVulkan11Features features11{};
        features11.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_1_FEATURES;
        VkPhysicalDeviceFeatures2 features{};
        features.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2;
        features.pNext = &features11;
        features11.pNext = &features12;
        features12.pNext = &features13;
        vkGetPhysicalDeviceFeatures2(gpu, &features);
        std::printf("profile=all_supported_core_1_1_1_2_1_3 float16=%u int8=%u subgroup_control=%u "
                    "synchronization2=%u\n",
                    features12.shaderFloat16, features12.shaderInt8, features13.subgroupSizeControl,
                    features13.synchronization2);
        const float priority = 1;
        VkDeviceQueueCreateInfo queue_info{};
        queue_info.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
        queue_info.queueFamilyIndex = family;
        queue_info.queueCount = 1;
        queue_info.pQueuePriorities = &priority;
        VkDeviceCreateInfo device_info{};
        device_info.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
        device_info.pNext = &features;
        device_info.queueCreateInfoCount = 1;
        device_info.pQueueCreateInfos = &queue_info;
        VkDevice device{};
        vk_check(vkCreateDevice(gpu, &device_info, nullptr, &device), "create_device");
        auto vkDestroyDevice =
            reinterpret_cast<PFN_vkDestroyDevice>(vkGetDeviceProcAddr(device, "vkDestroyDevice"));
        require(vkDestroyDevice != nullptr, "Missing destroy device");
        for (const auto format : {VK_FORMAT_R16G16B16A16_SFLOAT, VK_FORMAT_R16G16_SFLOAT,
                                  VK_FORMAT_R32_SFLOAT, VK_FORMAT_D32_SFLOAT}) {
            VkFormatProperties properties{};
            vkGetPhysicalDeviceFormatProperties(gpu, format, &properties);
            std::printf("format=%u optimal_features=%u\n", unsigned(format),
                        properties.optimalTilingFeatures);
            require((properties.optimalTilingFeatures & VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT) != 0,
                    "Required sampled format unavailable");
        }
        VkDeviceContext device_context{device, gpu, vkGetDeviceProcAddr};
        ffxQueryDescGetVersions versions{};
        versions.header.type = FFX_API_QUERY_DESC_TYPE_GET_VERSIONS;
        versions.createDescType = FFX_API_CREATE_CONTEXT_DESC_TYPE_UPSCALE;
        versions.device = &device_context;
        uint64_t version_count{};
        versions.outputCount = &version_count;
        ffx_check(query(nullptr, &versions.header), "version_count");
        require(version_count > 0 && version_count < 100,
                "No compatible providers or invalid count");
        std::vector<uint64_t> ids(version_count);
        std::vector<const char *> names(version_count);
        versions.versionIds = ids.data();
        versions.versionNames = names.data();
        ffx_check(query(nullptr, &versions.header), "versions");
        std::vector<std::string> copied_names;
        for (size_t i = 0; i < version_count; ++i)
            copied_names.emplace_back(names[i] ? names[i] : "unknown");
        for (size_t i = 0; i < version_count; ++i) {
            std::printf("provider=%s id=%llu\n", copied_names[i].c_str(), ids[i]);
            ffxCreateBackendVKDesc backend{};
            backend.header.type = FFX_API_CREATE_CONTEXT_DESC_TYPE_BACKEND_VK;
            backend.deviceContext = device_context;
            ffxOverrideVersion override_version{};
            override_version.header.type = FFX_API_DESC_TYPE_OVERRIDE_VERSION;
            override_version.versionId = ids[i];
            override_version.header.pNext = &backend.header;
            ffxQueryDescUpscaleGetResourceRequirements resources{};
            resources.header.type = FFX_API_QUERY_DESC_TYPE_UPSCALE_GET_RESOURCE_REQUIREMENTS;
            resources.header.pNext = &override_version.header;
            ffx_check(query(nullptr, &resources.header), "resource_requirements");
            std::printf("required_resources=%llu optional_resources=%llu\n",
                        resources.required_resources, resources.optional_resources);
            ffxCreateContextDescUpscaleVersion api_version{};
            api_version.header.type = FFX_API_CREATE_CONTEXT_DESC_TYPE_UPSCALE_VERSION;
            api_version.version = FFX_UPSCALER_VERSION;
            api_version.header.pNext = &override_version.header;
            ffxCreateContextDescUpscale upscale{};
            upscale.header.type = FFX_API_CREATE_CONTEXT_DESC_TYPE_UPSCALE;
            upscale.header.pNext = &api_version.header;
            upscale.flags = FFX_UPSCALE_ENABLE_AUTO_EXPOSURE;
            upscale.maxRenderSize = {1280, 720};
            upscale.maxUpscaleSize = {1920, 1080};
            ffxContext context{};
            ffx_check(create(&context, &upscale.header, nullptr), "create_upscaler");
            ffxQueryGetProviderVersion actual{};
            actual.header.type = FFX_API_QUERY_DESC_TYPE_GET_PROVIDER_VERSION;
            ffx_check(query(&context, &actual.header), "actual_provider");
            std::printf("created_provider=%s\n",
                        actual.versionName ? actual.versionName : "unknown");
            FfxApiEffectMemoryUsage memory{};
            ffxQueryDescUpscaleGetGPUMemoryUsage memory_query{};
            memory_query.header.type = FFX_API_QUERY_DESC_TYPE_UPSCALE_GPU_MEMORY_USAGE;
            memory_query.gpuMemoryUsageUpscaler = &memory;
            ffx_check(query(&context, &memory_query.header), "memory_usage");
            std::printf("context_memory_bytes=%llu\n", memory.totalUsageInBytes);
            ffx_check(destroy(&context, nullptr), "destroy_upscaler");
        }
        vkDestroyDevice(device, nullptr);
        vkDestroyInstance(instance, nullptr);
        FreeLibrary(sdk);
        FreeLibrary(vulkan);
        std::puts("PASS context/resource feasibility only; no dispatch or presentation");
        return 0;
    } catch (const std::exception &error) {
        std::fprintf(stderr, "FAIL: %s\n", error.what());
        // Process teardown releases any resources created before a diagnostic failure.
        return 1;
    }
}
