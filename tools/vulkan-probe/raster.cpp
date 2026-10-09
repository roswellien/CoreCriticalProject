// Authored offscreen Vulkan raster experiment. No MW3 assets or game code.
#define VK_NO_PROTOTYPES
#include <vulkan/vulkan_core.h>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#else
#include <dlfcn.h>
#endif
#include <array>
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
static uint32_t validationMessages = 0;
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

int main(int argc, char **argv) {
    if (argc != 4 && argc != 5) {
        std::cerr << "Usage: vulkan-raster scene.vert.spv scene.frag.spv output.ppm "
                     "[default|depth-off|fog-off|opaque-front]\n";
        return 2;
    }
    const std::string mode = argc == 5 ? argv[4] : "default";
    if (mode != "default" && mode != "depth-off" && mode != "fog-off" && mode != "opaque-front") {
        std::cerr << "Unknown experiment mode\n";
        return 2;
    }
    try {
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
        const std::array<const char *, 2> extensions{VK_EXT_DEBUG_UTILS_EXTENSION_NAME,
                                                   VK_EXT_VALIDATION_FEATURES_EXTENSION_NAME};
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
        app.pApplicationName = "MW34 authored raster";
        app.apiVersion = VK_API_VERSION_1_0;
        VkInstanceCreateInfo ici{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
        ici.pApplicationInfo = &app;
        ici.pNext = &debugInfo;
        ici.enabledLayerCount = 1;
        ici.ppEnabledLayerNames = &layer;
        ici.enabledExtensionCount = 2;
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
            for (uint32_t i = 0; i < n; ++i)
                if (!gpu && queues[i].queueCount &&
                    (queues[i].queueFlags & VK_QUEUE_GRAPHICS_BIT)) {
                    gpu = candidate;
                    family = i;
                }
        }
        if (!gpu)
            throw std::runtime_error("No graphics device");
        VkPhysicalDeviceProperties props{};
        vkGetPhysicalDeviceProperties(gpu, &props);
        std::cout << "Device: " << props.deviceName << '\n';
        VkFormatProperties depthProperties{};
        vkGetPhysicalDeviceFormatProperties(gpu, VK_FORMAT_D32_SFLOAT, &depthProperties);
        if (!(depthProperties.optimalTilingFeatures &
              VK_FORMAT_FEATURE_DEPTH_STENCIL_ATTACHMENT_BIT))
            throw std::runtime_error("D32 depth unsupported");
        float priority = 1;
        VkDeviceQueueCreateInfo qci{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
        qci.queueFamilyIndex = family;
        qci.queueCount = 1;
        qci.pQueuePriorities = &priority;
        VkDeviceCreateInfo dci{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
        dci.queueCreateInfoCount = 1;
        dci.pQueueCreateInfos = &qci;
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
        D(vkCreateFence);
        D(vkDestroyFence);
        D(vkQueueSubmit);
        D(vkWaitForFences);
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
        constexpr uint32_t width = 256, height = 256;
        auto upload = makeBuffer(16, VK_BUFFER_USAGE_TRANSFER_SRC_BIT);
        auto readback = makeBuffer(width * height * 4, VK_BUFFER_USAGE_TRANSFER_DST_BIT);
        const std::array<uint8_t, 16> texels{255, 0, 0,   255, 0,   255, 0,   255,
                                             0,   0, 255, 255, 255, 255, 255, 255};
        void *pointer = nullptr;
        check(vkMapMemory(device, upload.memory, 0, 16, 0, &pointer), "map upload");
        std::memcpy(pointer, texels.data(), 16);
        vkUnmapMemory(device, upload.memory);
        auto texture = makeImage(2, 2, VK_FORMAT_R8G8B8A8_UNORM,
                                 VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT,
                                 VK_IMAGE_ASPECT_COLOR_BIT);
        auto color =
            makeImage(width, height, VK_FORMAT_R8G8B8A8_UNORM,
                      VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT,
                      VK_IMAGE_ASPECT_COLOR_BIT);
        auto depth =
            makeImage(width, height, VK_FORMAT_D32_SFLOAT,
                      VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT, VK_IMAGE_ASPECT_DEPTH_BIT);
        VkSamplerCreateInfo si{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};
        si.magFilter = si.minFilter = VK_FILTER_NEAREST;
        si.mipmapMode = VK_SAMPLER_MIPMAP_MODE_NEAREST;
        si.addressModeU = si.addressModeV = si.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
        VkSampler sampler{};
        check(vkCreateSampler(device, &si, nullptr, &sampler), "sampler");
        cleanup.actions.push_back([=] { vkDestroySampler(device, sampler, nullptr); });
        VkDescriptorSetLayoutBinding binding{0, VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 1,
                                             VK_SHADER_STAGE_FRAGMENT_BIT, nullptr};
        VkDescriptorSetLayoutCreateInfo li{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
        li.bindingCount = 1;
        li.pBindings = &binding;
        VkDescriptorSetLayout layout{};
        check(vkCreateDescriptorSetLayout(device, &li, nullptr, &layout), "descriptor layout");
        cleanup.actions.push_back([=] { vkDestroyDescriptorSetLayout(device, layout, nullptr); });
        VkDescriptorPoolSize poolSize{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 1};
        VkDescriptorPoolCreateInfo dpi{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
        dpi.maxSets = 1;
        dpi.poolSizeCount = 1;
        dpi.pPoolSizes = &poolSize;
        VkDescriptorPool descriptorPool{};
        check(vkCreateDescriptorPool(device, &dpi, nullptr, &descriptorPool), "descriptor pool");
        cleanup.actions.push_back(
            [=] { vkDestroyDescriptorPool(device, descriptorPool, nullptr); });
        VkDescriptorSetAllocateInfo dai{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
        dai.descriptorPool = descriptorPool;
        dai.descriptorSetCount = 1;
        dai.pSetLayouts = &layout;
        VkDescriptorSet set{};
        check(vkAllocateDescriptorSets(device, &dai, &set), "descriptor set");
        VkDescriptorImageInfo imageInfo{sampler, texture.view,
                                        VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
        VkWriteDescriptorSet write{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};
        write.dstSet = set;
        write.descriptorCount = 1;
        write.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
        write.pImageInfo = &imageInfo;
        vkUpdateDescriptorSets(device, 1, &write, 0, nullptr);
        std::array<VkAttachmentDescription, 2> attachments{};
        attachments[0].format = VK_FORMAT_R8G8B8A8_UNORM;
        attachments[0].samples = VK_SAMPLE_COUNT_1_BIT;
        attachments[0].loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
        attachments[0].storeOp = VK_ATTACHMENT_STORE_OP_STORE;
        attachments[0].finalLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
        attachments[1].format = VK_FORMAT_D32_SFLOAT;
        attachments[1].samples = VK_SAMPLE_COUNT_1_BIT;
        attachments[1].loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
        attachments[1].storeOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
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
        std::array<VkPipelineShaderStageCreateInfo, 2> stages{};
        for (size_t i = 0; i < 2; ++i) {
            auto words = shader(argv[i + 1]);
            VkShaderModuleCreateInfo mi{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};
            mi.codeSize = words.size() * 4;
            mi.pCode = words.data();
            VkShaderModule module{};
            check(vkCreateShaderModule(device, &mi, nullptr, &module), "shader module");
            cleanup.actions.push_back([=] { vkDestroyShaderModule(device, module, nullptr); });
            stages[i].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
            stages[i].stage = i == 0 ? VK_SHADER_STAGE_VERTEX_BIT : VK_SHADER_STAGE_FRAGMENT_BIT;
            stages[i].module = module;
            stages[i].pName = "main";
        }
        VkPushConstantRange push{VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT, 0, 32};
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
        ds.depthTestEnable = mode == "depth-off" ? VK_FALSE : VK_TRUE;
        ds.depthWriteEnable = VK_TRUE;
        ds.depthCompareOp = VK_COMPARE_OP_LESS;
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
        VkPipeline pipeline{};
        check(vkCreateGraphicsPipelines(device, VK_NULL_HANDLE, 1, &pi, nullptr, &pipeline),
              "pipeline");
        cleanup.actions.push_back([=] { vkDestroyPipeline(device, pipeline, nullptr); });
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
                              VkPipelineStageFlags dstStage) {
            VkImageMemoryBarrier b{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};
            b.srcAccessMask = src;
            b.dstAccessMask = dst;
            b.oldLayout = oldLayout;
            b.newLayout = newLayout;
            b.srcQueueFamilyIndex = b.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            b.image = image;
            b.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
            vkCmdPipelineBarrier(command, srcStage, dstStage, 0, 0, nullptr, 0, nullptr, 1, &b);
        };
        transition(texture.handle, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                   0, VK_ACCESS_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT,
                   VK_PIPELINE_STAGE_TRANSFER_BIT);
        VkBufferImageCopy copy{};
        copy.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
        copy.imageExtent = {2, 2, 1};
        vkCmdCopyBufferToImage(command, upload.handle, texture.handle,
                               VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &copy);
        transition(texture.handle, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                   VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VK_ACCESS_TRANSFER_WRITE_BIT,
                   VK_ACCESS_SHADER_READ_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT,
                   VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT);
        std::array<VkClearValue, 2> clears{};
        clears[1].depthStencil.depth = 1;
        VkRenderPassBeginInfo begin{VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO};
        begin.renderPass = renderPass;
        begin.framebuffer = framebuffer;
        begin.renderArea = scissor;
        begin.clearValueCount = 2;
        begin.pClearValues = clears.data();
        vkCmdBeginRenderPass(command, &begin, VK_SUBPASS_CONTENTS_INLINE);
        vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline);
        vkCmdBindDescriptorSets(command, VK_PIPELINE_BIND_POINT_GRAPHICS, pipelineLayout, 0, 1,
                                &set, 0, nullptr);
        auto draw = [&](float z, float fog, float alpha, float tint) {
            const std::array<float, 8> values{tint, tint, tint, alpha, z, fog, 0, 0};
            vkCmdPushConstants(command, pipelineLayout, push.stageFlags, 0, 32, values.data());
            vkCmdDraw(command, 6, 1, 0, 0);
        };
        draw(0.5F, 0, 1, 1);  // opaque texture baseline
        draw(0.75F, 0, 1, 0); // must be rejected by depth, otherwise destroys baseline
        draw(0.25F, mode == "fog-off" ? 0.0F : 0.5F, mode == "opaque-front" ? 1.0F : 0.5F,
             1); // foreground fog + alpha blend
        vkCmdEndRenderPass(command);
        transition(color.handle, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
                   VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                   VK_ACCESS_TRANSFER_READ_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT,
                   VK_PIPELINE_STAGE_TRANSFER_BIT);
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
        check(vkMapMemory(device, readback.memory, 0, width * height * 4, 0, &pointer),
              "map readback");
        std::vector<uint8_t> pixels(width * height * 4);
        std::memcpy(pixels.data(), pointer, pixels.size());
        vkUnmapMemory(device, readback.memory);
        std::ofstream output(argv[3], std::ios::binary);
        output << "P6\n256 256\n255\n";
        for (size_t i = 0; i < pixels.size(); i += 4)
            output.write(reinterpret_cast<const char *>(pixels.data() + i), 3);
        output.close();
        if (!output)
            throw std::runtime_error("Cannot write output");
        cleanup.run();
        if (validationMessages)
            throw std::runtime_error("Validation warnings/errors: " +
                                     std::to_string(validationMessages));
        std::cout << "PASS: raster mode=" << mode
                  << "; zero validation warnings/errors including teardown; run verify_raster.py "
                     "for pixel acceptance\n";
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
