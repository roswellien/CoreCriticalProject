// dear imgui: Renderer Backend for Vulkan
// This needs to be used along with a Platform Backend (e.g. GLFW, SDL, Win32, custom..)

// Implemented features:
//  [!] Renderer: User texture binding. Use a VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE 'VkDescriptorSet' as texture identifier. Call ImGui_ImplVulkan_AddTexture() to register one. Read the FAQ about ImTextureID/ImTextureRef + https://github.com/ocornut/imgui/pull/914 for discussions.
//  [X] Renderer: Large meshes support (64k+ vertices) even with 16-bit indices (ImGuiBackendFlags_RendererHasVtxOffset).
//  [X] Renderer: Texture updates support for dynamic font atlas (ImGuiBackendFlags_RendererHasTextures).
//  [X] Renderer: Expose selected render state for draw callbacks to use. Access with ImGui_ImplVulkan_GetRenderState().

// The aim of imgui_impl_vulkan.h/.cpp is to be usable in your engine without any modification.
// IF YOU FEEL YOU NEED TO MAKE ANY CHANGE TO THIS CODE, please share them and your feedback at https://github.com/ocornut/imgui/

// You can use unmodified imgui_impl_* files in your project. See examples/ folder for examples of using this.
// Prefer including the entire imgui/ repository into your project (either as a copy or as a submodule), and only build the backends you need.
// Learn about Dear ImGui:
// - FAQ                  https://dearimgui.com/faq
// - Getting Started      https://dearimgui.com/getting-started
// - Documentation        https://dearimgui.com/docs (same as your local docs/ folder).
// - Introduction, links and more at the top of imgui.cpp

// Important note to the reader who wish to integrate imgui_impl_vulkan.cpp/.h in their own engine/app.
// - Common ImGui_ImplVulkan_XXX functions and structures are used to interface with imgui_impl_vulkan.cpp/.h.
//   You will use those if you want to use this rendering backend in your engine/app.
// - Helper ImGui_ImplVulkanH_XXX functions and structures are only used by this example (main.cpp) and by
//   the backend itself (imgui_impl_vulkan.cpp), but should PROBABLY NOT be used by your own engine/app code.
// Read comments in imgui_impl_vulkan.h.

// CHANGELOG
// (minor and older changes stripped away, please see git history for details)
//  2026-10-06: Added support for dynamic rendering with multiple color attachments (PipelineRenderingCreateInfo.colorAttachmentCount > 1): we render to the first one and leave the others untouched. (#9574)
//  2026-09-07: Round framebuffer dimensions to the nearest integer instead of truncating them. (#9538, 9515, #8628)
//  2026-09-03: Added for support for multiple Vulkan contexts with custom loaders. (#6616)
//  2026-04-23: Added support for standard draw callbacks (in platform_io): DrawCallback_ResetRenderState, DrawCallback_SetSamplerLinear, DrawCallback_SetSamplerNearest. (#9378)
//  2026-04-22: *BREAKING CHANGE* redesigned to use separate ImageView + Sampler instead of Combined Image Sampler. This change allows us to facilitate changing samplers, in line with other backends.
//              - When registering custom textures: changed ImGui_ImplVulkan_AddTexture() signature to remove Sampler.
//                - Before: ImGui_ImplVulkan_AddTexture(VkSampler, VkImageView, VkImageLayout)
//                - After:  ImGui_ImplVulkan_AddTexture(VkImageView, VkImageLayout)
//                - Kept inline redirection function that ignores the sampler.
//              - When creating your own descriptor pool (instead of letting backend creates its own):
//                - Before: need at least IMGUI_IMPL_VULKAN_MINIMUM_IMAGE_SAMPLER_POOL_SIZE descriptors of type VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER.
//                - After:  need at least IMGUI_IMPL_VULKAN_MINIMUM_SAMPLED_IMAGE_POOL_SIZE descriptors of type VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE.
//                                      + IMGUI_IMPL_VULKAN_MINIMUM_SAMPLER_POOL_SIZE       descriptors of type VK_DESCRIPTOR_TYPE_SAMPLER.
//  2026-03-11: Vulkan: Added ImGui_ImplVulkan_PipelineInfo::ExtraDynamicStates[] to allow specifying extra dynamic states to add when creating the VkPipeline. (#9211)
//  2025-09-26: [Helpers] *BREAKING CHANGE*: Vulkan: Helper ImGui_ImplVulkanH_DestroyWindow() does not call vkDestroySurfaceKHR(): as surface is created by caller of ImGui_ImplVulkanH_CreateOrResizeWindow(), it is more consistent that we don't destroy it. (#9163)
//  2026-01-05: [Helpers] *BREAKING CHANGE*: Vulkan: Helper for creating render pass uses ImGui_ImplVulkanH_Window::AttachmentDesc to create render pass. Removed ClearEnabled. (#9152)
//  2025-11-24: [Helpers] Vulkan: Helper for creating a swap-chain (used by examples and multi-viewports) selects VkSwapchainCreateInfoKHR's compositeAlpha based on cap.supportedCompositeAlpha. (#8784)
//  2025-10-15: Vulkan: Added IMGUI_IMPL_VULKAN_VOLK_FILENAME to configure path to volk.h header. (#9008)
//  2025-09-26: *BREAKING CHANGE*: moved some fields in ImGui_ImplVulkan_InitInfo: init_info.RenderPass --> init_info.PipelineInfoMain.RenderPass, init_info.Subpass --> init_info.PipelineInfoMain.Subpass, init_info.MSAASamples --> init_info.PipelineInfoMain.MSAASamples, init_info.PipelineRenderingCreateInfo --> init_info.PipelineInfoMain.PipelineRenderingCreateInfo.
//  2025-09-26: *BREAKING CHANGE*: renamed ImGui_ImplVulkan_MainPipelineCreateInfo to ImGui_ImplVulkan_PipelineInfo. Introduced very recently so shouldn't affect many users.
//  2025-09-26: [Helpers] *BREAKING CHANGE*: Helper ImGui_ImplVulkanH_CreateOrResizeWindow() added a VkImageUsageFlags image_usage` argument, default to VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT if 0.
//  2025-09-26: Vulkan: Added a way to customize shaders by filling ImGui_ImplVulkan_InitInfo::CustomShaderVertCreateInfo/CustomShaderFragCreateInfo. (#8585)
//  2025-09-18: Call platform_io.ClearRendererHandlers() on shutdown.
//  2025-09-04: Vulkan: Added ImGui_ImplVulkan_CreateMainPipeline(). (#8110, #8111)
//  2025-07-27: Vulkan: Fixed texture update corruption introduced on 2025-06-11. (#8801, #8755, #8840)
//  2025-07-07: Vulkan: Fixed texture synchronization issue introduced on 2025-06-11. (#8772)
//  2025-06-27: Vulkan: Fixed validation errors during texture upload/update by aligning upload size to 'nonCoherentAtomSize'. (#8743, #8744)
//  2025-06-11: Vulkan: Added support for ImGuiBackendFlags_RendererHasTextures, for dynamic font atlas. Removed ImGui_ImplVulkan_CreateFontsTexture() and ImGui_ImplVulkan_DestroyFontsTexture().
//  2025-05-07: Vulkan: Fixed validation errors during window detach in multi-viewport mode. (#8600, #8176)
//  2025-05-07: Vulkan: Load dynamic rendering functions using vkGetDeviceProcAddr() + try both non-KHR and KHR versions. (#8600, #8326, #8365)
//  2025-04-07: Vulkan: Deep-copy ImGui_ImplVulkan_InitInfo::PipelineRenderingCreateInfo's pColorAttachmentFormats buffer when set, in order to reduce common user-error of specifying a pointer to data that gets out of scope. (#8282)
//  2025-02-14: *BREAKING CHANGE*: Added uint32_t api_version to ImGui_ImplVulkan_LoadFunctions().
//  2025-02-13: Vulkan: Added ApiVersion field in ImGui_ImplVulkan_InitInfo. Default to header version if unspecified. Dynamic rendering path loads "vkCmdBeginRendering/vkCmdEndRendering" (without -KHR suffix) on API 1.3. (#8326)
//  2025-01-09: Vulkan: Added IMGUI_IMPL_VULKAN_MINIMUM_IMAGE_SAMPLER_POOL_SIZE to clarify how many image sampler descriptors are expected to be available in descriptor pool. (#6642)
//  2025-01-06: [Helpers] Vulkan: Added more ImGui_ImplVulkanH_XXXX helper functions to simplify our examples.
//  2024-12-11: [Helpers] Vulkan: Fixed setting VkSwapchainCreateInfoKHR::preTransform for platforms not supporting VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR. (#8222)
//  2024-11-27: Vulkan: Make user-provided descriptor pool optional. As a convenience, when setting init_info->DescriptorPoolSize the backend will create one itself. (#8172, #4867)
//  2024-10-07: Vulkan: Changed default texture sampler to Clamp instead of Repeat/Wrap.
//  2024-10-07: Vulkan: Expose selected render state in ImGui_ImplVulkan_RenderState, which you can access in 'void* platform_io.Renderer_RenderState' during draw callbacks.
//  2024-10-07: Vulkan: Compiling with '#define ImTextureID=ImU64' is unnecessary now that dear imgui defaults ImTextureID to u64 instead of void*.
//  2024-04-19: Vulkan: Added convenience support for Volk via IMGUI_IMPL_VULKAN_USE_VOLK define (you can also use IMGUI_IMPL_VULKAN_NO_PROTOTYPES + wrap Volk via ImGui_ImplVulkan_LoadFunctions().)
//  2024-02-14: *BREAKING CHANGE*: Moved RenderPass parameter from ImGui_ImplVulkan_Init() function to ImGui_ImplVulkan_InitInfo structure. Not required when using dynamic rendering.
//  2024-02-12: *BREAKING CHANGE*: Dynamic rendering now require filling PipelineRenderingCreateInfo structure.
//  2024-01-19: [Helpers] Vulkan: Fixed vkAcquireNextImageKHR() validation errors in VulkanSDK 1.3.275 by allocating one extra semaphore than in-flight frames. (#7236)
//  2024-01-11: Vulkan: Fixed vkMapMemory() calls unnecessarily using full buffer size (#3957). Fixed MinAllocationSize handing (#7189).
//  2024-01-03: Vulkan: Added MinAllocationSize field in ImGui_ImplVulkan_InitInfo to workaround zealous "best practice" validation layer. (#7189, #4238)
//  2024-01-03: Vulkan: Stopped creating command pools with VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT as we don't reset them.
//  2023-11-29: Vulkan: Fixed mismatching allocator passed to vkCreateCommandPool() vs vkDestroyCommandPool(). (#7075)
//  2023-11-10: *BREAKING CHANGE*: Removed parameter from ImGui_ImplVulkan_CreateFontsTexture(): backend now creates its own command-buffer to upload fonts.
//              *BREAKING CHANGE*: Removed ImGui_ImplVulkan_DestroyFontUploadObjects() which is now unnecessary as we create and destroy those objects in the backend.
//              ImGui_ImplVulkan_CreateFontsTexture() is automatically called by NewFrame() the first time.
//              You can call ImGui_ImplVulkan_CreateFontsTexture() again to recreate the font atlas texture.
//              Added ImGui_ImplVulkan_DestroyFontsTexture() but you probably never need to call this.
//  2023-07-04: Vulkan: Added optional support for VK_KHR_dynamic_rendering. User needs to set init_info->UseDynamicRendering = true and init_info->ColorAttachmentFormat.
//  2023-01-02: Vulkan: Fixed sampler passed to ImGui_ImplVulkan_AddTexture() not being honored + removed a bunch of duplicate code.
//  2022-10-11: Using 'nullptr' instead of 'NULL' as per our switch to C++11.
//  2022-10-04: Vulkan: Added experimental ImGui_ImplVulkan_RemoveTexture() for api symmetry. (#914, #5738).
//  2022-01-20: Vulkan: Added support for ImTextureID as VkDescriptorSet. User need to call ImGui_ImplVulkan_AddTexture(). Building for 32-bit targets requires '#define ImTextureID ImU64'. (#914).
//  2021-10-15: Vulkan: Call vkCmdSetScissor() at the end of render a full-viewport to reduce likelihood of issues with people using VK_DYNAMIC_STATE_SCISSOR in their app without calling vkCmdSetScissor() explicitly every frame.
//  2021-06-29: Reorganized backend to pull data from a single structure to facilitate usage with multiple-contexts (all g_XXXX access changed to bd->XXXX).
//  2021-03-22: Vulkan: Fix mapped memory validation error when buffer sizes are not multiple of VkPhysicalDeviceLimits::nonCoherentAtomSize.
//  2021-02-18: Vulkan: Change blending equation to preserve alpha in output buffer.
//  2021-01-27: Vulkan: Added support for custom function load and IMGUI_IMPL_VULKAN_NO_PROTOTYPES by using ImGui_ImplVulkan_LoadFunctions().
//  2020-11-11: Vulkan: Added support for specifying which subpass to reference during VkPipeline creation.
//  2020-09-07: Vulkan: Added VkPipeline parameter to ImGui_ImplVulkan_RenderDrawData (default to one passed to ImGui_ImplVulkan_Init).
//  2020-05-04: Vulkan: Fixed crash if initial frame has no vertices.
//  2020-04-26: Vulkan: Fixed edge case where render callbacks wouldn't be called if the ImDrawData didn't have vertices.
//  2019-08-01: Vulkan: Added support for specifying multisample count. Set ImGui_ImplVulkan_InitInfo::MSAASamples to one of the VkSampleCountFlagBits values to use, default is non-multisampled as before.
//  2019-05-29: Vulkan: Added support for large mesh (64K+ vertices), enable ImGuiBackendFlags_RendererHasVtxOffset flag.
//  2019-04-30: Vulkan: Added support for special ImDrawCallback_ResetRenderState callback to reset render state.
//  2019-04-04: *BREAKING CHANGE*: Vulkan: Added ImageCount/MinImageCount fields in ImGui_ImplVulkan_InitInfo, required for initialization (was previously a hard #define IMGUI_VK_QUEUED_FRAMES 2). Added ImGui_ImplVulkan_SetMinImageCount().
//  2019-04-04: [Helpers] Vulkan: Added VkInstance argument to ImGui_ImplVulkanH_CreateWindow() optional helper.
//  2019-04-04: Vulkan: Avoid passing negative coordinates to vkCmdSetScissor, which debug validation layers do not like.
//  2019-04-01: Vulkan: Support for 32-bit index buffer (#define ImDrawIdx unsigned int).
//  2019-02-16: Vulkan: Viewport and clipping rectangles correctly using draw_data->FramebufferScale to allow retina display.
//  2018-11-30: Misc: Setting up io.BackendRendererName so it can be displayed in the About Window.
//  2018-08-25: [Helpers] Vulkan: Fixed mishandled VkSurfaceCapabilitiesKHR::maxImageCount=0 case.
//  2018-06-22: Inverted the parameters to ImGui_ImplVulkan_RenderDrawData() to be consistent with other backends.
//  2018-06-08: Misc: Extracted imgui_impl_vulkan.cpp/.h away from the old combined GLFW+Vulkan example.
//  2018-06-08: Vulkan: Use draw_data->DisplayPos and draw_data->DisplaySize to setup projection matrix and clipping rectangle.
//  2018-03-03: [Helpers] Vulkan: Various refactor, created a couple of ImGui_ImplVulkanH_XXX helper that the example can use and that viewport support will use.
//  2018-03-01: Vulkan: Renamed ImGui_ImplVulkan_Init_Info to ImGui_ImplVulkan_InitInfo and fields to match more closely Vulkan terminology.
//  2018-02-16: Misc: Obsoleted the io.RenderDrawListsFn callback, ImGui_ImplVulkan_Render() calls ImGui_ImplVulkan_RenderDrawData() itself.
//  2018-02-06: Misc: Removed call to ImGui::Shutdown() which is not available from 1.60 WIP, user needs to call CreateContext/DestroyContext themselves.
//  2017-05-15: Vulkan: Fix scissor offset being negative. Fix new Vulkan validation warnings. Set required depth member for buffer image copy.
//  2016-11-13: Vulkan: Fix validation layer warnings and errors and redeclare gl_PerVertex.
//  2016-10-18: Vulkan: Add location decorators & change to use structs as in/out in glsl, update embedded spv (produced with glslangValidator -x). Null the released resources.
//  2016-08-27: Vulkan: Fix Vulkan example for use when a depth buffer is active.

#include "imgui.h"
#ifndef IMGUI_DISABLE
#include "imgui_impl_vulkan.h"
#include <stdio.h>
#include <cmath>        // std::isfinite
#include <cstdlib>      // std::_Exit
#include <exception>    // std::exception_ptr
#ifndef IM_MAX
#define IM_MAX(A, B)    (((A) >= (B)) ? (A) : (B))
#endif
#undef Status // X11 headers are leaking this.

// Visual Studio warnings
#ifdef _MSC_VER
#pragma warning (disable: 4127) // condition expression is constant
#endif

// Clang/GCC warnings with -Weverything
#if defined(__clang__)
#pragma clang diagnostic ignored "-Wold-style-cast"                 // warning: use of old-style cast
#pragma clang diagnostic ignored "-Wsign-conversion"                // warning: implicit conversion changes signedness
#pragma clang diagnostic ignored "-Wimplicit-int-float-conversion"  // warning: implicit conversion from 'xxx' to 'float' may lose precision
#pragma clang diagnostic ignored "-Wcast-function-type"             // warning: cast between incompatible function types (for loader)
#endif

// Forward Declarations
struct ImGui_ImplVulkan_FrameRenderBuffers;
struct ImGui_ImplVulkan_WindowRenderBuffers;
bool ImGui_ImplVulkan_CreateDeviceObjects();
void ImGui_ImplVulkan_DestroyDeviceObjects();
void ImGui_ImplVulkan_DestroyFrameRenderBuffers(VkDevice device, ImGui_ImplVulkan_FrameRenderBuffers* buffers, const VkAllocationCallbacks* allocator);
void ImGui_ImplVulkan_DestroyWindowRenderBuffers(VkDevice device, ImGui_ImplVulkan_WindowRenderBuffers* buffers, const VkAllocationCallbacks* allocator);
void ImGui_ImplVulkanH_DestroyFrame(VkDevice device, ImGui_ImplVulkanH_Frame* fd, const VkAllocationCallbacks* allocator);
void ImGui_ImplVulkanH_DestroyFrameSemaphores(VkDevice device, ImGui_ImplVulkanH_FrameSemaphores* fsd, const VkAllocationCallbacks* allocator);
void ImGui_ImplVulkanH_CreateWindowSwapChain(VkPhysicalDevice physical_device, VkDevice device, ImGui_ImplVulkanH_Window* wd, const VkAllocationCallbacks* allocator, int w, int h, uint32_t min_image_count, VkImageUsageFlags image_usage);
void ImGui_ImplVulkanH_CreateWindowCommandBuffers(VkPhysicalDevice physical_device, VkDevice device, ImGui_ImplVulkanH_Window* wd, uint32_t queue_family, const VkAllocationCallbacks* allocator);

// Vulkan prototypes for use with custom loaders
// (see description of IMGUI_IMPL_VULKAN_NO_PROTOTYPES in imgui_impl_vulkan.h)
#if defined(VK_NO_PROTOTYPES) && !defined(VOLK_H_)
#define IMGUI_IMPL_VULKAN_USE_LOADER
static bool g_FunctionsLoaded = false;
#else
static bool g_FunctionsLoaded = true;
#endif
#ifdef IMGUI_IMPL_VULKAN_USE_LOADER
#define IMGUI_VULKAN_FUNC_MAP(IMGUI_VULKAN_FUNC_MAP_MACRO) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkAllocateCommandBuffers) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkAllocateDescriptorSets) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkAllocateMemory) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkBeginCommandBuffer) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkBindBufferMemory) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkBindImageMemory) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCmdBindDescriptorSets) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCmdBindIndexBuffer) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCmdBindPipeline) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCmdBindVertexBuffers) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCmdCopyBufferToImage) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCmdDrawIndexed) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCmdPipelineBarrier) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCmdPushConstants) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCmdSetScissor) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCmdSetViewport) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCreateBuffer) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCreateCommandPool) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCreateDescriptorPool) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCreateDescriptorSetLayout) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCreateFence) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCreateFramebuffer) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCreateGraphicsPipelines) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCreateImage) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCreateImageView) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCreatePipelineLayout) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCreateRenderPass) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCreateSampler) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCreateSemaphore) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCreateShaderModule) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkCreateSwapchainKHR) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkDestroyBuffer) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkDestroyCommandPool) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkDestroyDescriptorPool) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkDestroyDescriptorSetLayout) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkDestroyFence) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkDestroyFramebuffer) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkDestroyImage) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkDestroyImageView) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkDestroyPipeline) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkDestroyPipelineLayout) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkDestroyRenderPass) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkDestroySampler) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkDestroySemaphore) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkDestroyShaderModule) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkDestroySurfaceKHR) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkDestroySwapchainKHR) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkDeviceWaitIdle) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkEnumeratePhysicalDevices) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkEndCommandBuffer) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkFlushMappedMemoryRanges) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkFreeCommandBuffers) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkFreeDescriptorSets) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkFreeMemory) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkGetBufferMemoryRequirements) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkGetDeviceQueue) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkGetImageMemoryRequirements) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkGetPhysicalDeviceProperties) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkGetPhysicalDeviceMemoryProperties) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkGetPhysicalDeviceQueueFamilyProperties) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkGetPhysicalDeviceSurfaceCapabilitiesKHR) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkGetPhysicalDeviceSurfaceFormatsKHR) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkGetPhysicalDeviceSurfacePresentModesKHR) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkGetSwapchainImagesKHR) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkMapMemory) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkQueueSubmit) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkQueueWaitIdle) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkResetCommandPool) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkResetFences) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkUnmapMemory) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkUpdateDescriptorSets) \
    IMGUI_VULKAN_FUNC_MAP_MACRO(vkWaitForFences)

struct ImGui_ImplVulkan_Functions
{
// Define function pointers
#define IMGUI_VULKAN_FUNC_DEF(func) PFN_##func pfn_##func;
IMGUI_VULKAN_FUNC_MAP(IMGUI_VULKAN_FUNC_DEF)
#undef IMGUI_VULKAN_FUNC_DEF
};

// Globally available function pointers used for initialization of the backend data
static ImGui_ImplVulkan_Functions   ImGuiImplVulkanFuncs;

// Multi Vulkan contexts support: wrap each Vulkan function pointer to properly dispatch it using the current backend data
static ImGui_ImplVulkan_Functions&  ImGui_ImplVulkan_GetFunctions();
#define IMGUI_VULKAN_FUNC_WRAPPER(func) \
    template<typename... Args> \
    auto func(Args&&... args) -> decltype(ImGui_ImplVulkan_GetFunctions().pfn_##func(args...)) \
    { \
        return ImGui_ImplVulkan_GetFunctions().pfn_##func(args...); \
    }
IMGUI_VULKAN_FUNC_MAP(IMGUI_VULKAN_FUNC_WRAPPER)
#undef IMGUI_VULKAN_FUNC_WRAPPER

#endif // IMGUI_IMPL_VULKAN_USE_LOADER

#ifdef IMGUI_IMPL_VULKAN_HAS_DYNAMIC_RENDERING
static PFN_vkCmdBeginRenderingKHR   ImGuiImplVulkanFuncs_vkCmdBeginRenderingKHR;
static PFN_vkCmdEndRenderingKHR     ImGuiImplVulkanFuncs_vkCmdEndRenderingKHR;
#endif

// Actual function pointer the backend currently dispatches to (handed to the device memory routing hooks)
#ifdef IMGUI_IMPL_VULKAN_USE_LOADER
#define IMGUI_IMPL_VULKAN_PFN(func) (ImGui_ImplVulkan_GetFunctions().pfn_##func)
#else
#define IMGUI_IMPL_VULKAN_PFN(func) (func)
#endif

// Reusable buffers used for rendering 1 current in-flight frame, for ImGui_ImplVulkan_RenderDrawData()
// [Please zero-clear before use!]
struct ImGui_ImplVulkan_FrameRenderBuffers
{
    VkDeviceMemory      VertexBufferMemory;
    VkDeviceMemory      IndexBufferMemory;
    VkDeviceSize        VertexBufferSize;
    VkDeviceSize        IndexBufferSize;
    VkBuffer            VertexBuffer;
    VkBuffer            IndexBuffer;
};

// Each viewport will hold 1 ImGui_ImplVulkanH_WindowRenderBuffers
// [Please zero-clear before use!]
struct ImGui_ImplVulkan_WindowRenderBuffers
{
    uint32_t            Index;
    uint32_t            Count;
    ImVector<ImGui_ImplVulkan_FrameRenderBuffers> FrameRenderBuffers;
};

struct ImGui_ImplVulkan_Texture
{
    VkDeviceMemory              Memory;
    VkImage                     Image;
    VkImageView                 ImageView;
    VkDescriptorSet             DescriptorSet;
    int                         Width;                  // Extent the image was created with
    int                         Height;

    ImGui_ImplVulkan_Texture() { memset((void*)this, 0, sizeof(*this)); }
};

// Vulkan data
struct ImGui_ImplVulkan_Data
{
    ImGui_ImplVulkan_InitInfo   VulkanInitInfo;
    ImGui_ImplVulkan_RenderState* RenderState;          // == ImGui::GetPlatformIO().Renderer_RenderState during rendering.
    VkDeviceSize                BufferMemoryAlignment;
    VkDeviceSize                NonCoherentAtomSize;
    VkPipelineCreateFlags       PipelineCreateFlags;
    VkDescriptorSetLayout       DescriptorSetLayoutTexture;
    VkDescriptorSetLayout       DescriptorSetLayoutSampler;
    VkPipelineLayout            PipelineLayout;
    VkPipeline                  Pipeline;               // pipeline for main render pass (created by app)
    VkShaderModule              ShaderModuleVert;
    VkShaderModule              ShaderModuleFrag;
    VkDescriptorPool            DescriptorPool;
    ImVector<VkFormat>          PipelineRenderingCreateInfoColorAttachmentFormats; // Deep copy of format array

    // Texture management
    VkSampler                   SamplerLinear;
    VkSampler                   SamplerNearest;
    VkDescriptorSet             SamplerLinearDS;
    VkDescriptorSet             SamplerNearestDS;
    VkCommandPool               TexCommandPool;
    VkCommandBuffer             TexCommandBuffer;
    VkFence                     UploadFence;            // Owned upload completion primitive (created unsignaled by CreateDeviceObjects)

    // Single pending upload owner: staging buffer/memory are recorded here from successful creation until resolved completion
    VkBuffer                    UploadBuffer;
    VkDeviceMemory              UploadBufferMemory;
    bool                        UploadSubmitted;        // Owner referenced by a submission (or unknown outcome) whose completion is unresolved
    VkResult                    LastUploadSubmitResult;
    VkResult                    LastUploadWaitResult;
    VkResult                    TerminalResult;         // VK_ERROR_DEVICE_LOST once terminal for this backend instance
    uint32_t                    MaxImageDimension2D;    // Device limit (0 = unknown, e.g. Init bypassed)
    int                         SampledImageRegistrations;
    int                         SamplerRegistrations;

    // Render buffers for main window
    ImGui_ImplVulkan_WindowRenderBuffers MainWindowRenderBuffers;

    // Vulkan function pointers loaded for this context
#ifdef IMGUI_IMPL_VULKAN_USE_LOADER
    ImGui_ImplVulkan_Functions  Functions;
#endif

    ImGui_ImplVulkan_Data()
    {
        memset((void*)this, 0, sizeof(*this));
        BufferMemoryAlignment = 256;
        NonCoherentAtomSize = 64;
        LastUploadSubmitResult = VK_RESULT_MAX_ENUM;
        LastUploadWaitResult = VK_RESULT_MAX_ENUM;
    }
};

//-----------------------------------------------------------------------------
// SHADERS
//-----------------------------------------------------------------------------

// backends/vulkan/glsl_shader.vert, compiled with:
// # glslangValidator -V -x -o glsl_shader.vert.u32 glsl_shader.vert
/*
#version 450 core
layout(location = 0) in vec2 aPos;
layout(location = 1) in vec2 aUV;
layout(location = 2) in vec4 aColor;
layout(push_constant) uniform uPushConstant { vec2 uScale; vec2 uTranslate; } pc;

out gl_PerVertex { vec4 gl_Position; };
layout(location = 0) out struct { vec4 Color; vec2 UV; } Out;

void main()
{
    Out.Color = aColor;
    Out.UV = aUV;
    gl_Position = vec4(aPos * pc.uScale + pc.uTranslate, 0, 1);
}
*/
static uint32_t __glsl_shader_vert_spv[] =
{
    0x07230203,0x00010000,0x0008000b,0x0000002e,0x00000000,0x00020011,0x00000001,0x0006000b,
    0x00000001,0x4c534c47,0x6474732e,0x3035342e,0x00000000,0x0003000e,0x00000000,0x00000001,
    0x000a000f,0x00000000,0x00000004,0x6e69616d,0x00000000,0x0000000b,0x0000000f,0x00000015,
    0x0000001b,0x0000001c,0x00030003,0x00000002,0x000001c2,0x00040005,0x00000004,0x6e69616d,
    0x00000000,0x00030005,0x00000009,0x00000000,0x00050006,0x00000009,0x00000000,0x6f6c6f43,
    0x00000072,0x00040006,0x00000009,0x00000001,0x00005655,0x00030005,0x0000000b,0x0074754f,
    0x00040005,0x0000000f,0x6c6f4361,0x0000726f,0x00030005,0x00000015,0x00565561,0x00060005,
    0x00000019,0x505f6c67,0x65567265,0x78657472,0x00000000,0x00060006,0x00000019,0x00000000,
    0x505f6c67,0x7469736f,0x006e6f69,0x00030005,0x0000001b,0x00000000,0x00040005,0x0000001c,
    0x736f5061,0x00000000,0x00060005,0x0000001e,0x73755075,0x6e6f4368,0x6e617473,0x00000074,
    0x00050006,0x0000001e,0x00000000,0x61635375,0x0000656c,0x00060006,0x0000001e,0x00000001,
    0x61725475,0x616c736e,0x00006574,0x00030005,0x00000020,0x00006370,0x00040047,0x0000000b,
    0x0000001e,0x00000000,0x00040047,0x0000000f,0x0000001e,0x00000002,0x00040047,0x00000015,
    0x0000001e,0x00000001,0x00030047,0x00000019,0x00000002,0x00050048,0x00000019,0x00000000,
    0x0000000b,0x00000000,0x00040047,0x0000001c,0x0000001e,0x00000000,0x00030047,0x0000001e,
    0x00000002,0x00050048,0x0000001e,0x00000000,0x00000023,0x00000000,0x00050048,0x0000001e,
    0x00000001,0x00000023,0x00000008,0x00020013,0x00000002,0x00030021,0x00000003,0x00000002,
    0x00030016,0x00000006,0x00000020,0x00040017,0x00000007,0x00000006,0x00000004,0x00040017,
    0x00000008,0x00000006,0x00000002,0x0004001e,0x00000009,0x00000007,0x00000008,0x00040020,
    0x0000000a,0x00000003,0x00000009,0x0004003b,0x0000000a,0x0000000b,0x00000003,0x00040015,
    0x0000000c,0x00000020,0x00000001,0x0004002b,0x0000000c,0x0000000d,0x00000000,0x00040020,
    0x0000000e,0x00000001,0x00000007,0x0004003b,0x0000000e,0x0000000f,0x00000001,0x00040020,
    0x00000011,0x00000003,0x00000007,0x0004002b,0x0000000c,0x00000013,0x00000001,0x00040020,
    0x00000014,0x00000001,0x00000008,0x0004003b,0x00000014,0x00000015,0x00000001,0x00040020,
    0x00000017,0x00000003,0x00000008,0x0003001e,0x00000019,0x00000007,0x00040020,0x0000001a,
    0x00000003,0x00000019,0x0004003b,0x0000001a,0x0000001b,0x00000003,0x0004003b,0x00000014,
    0x0000001c,0x00000001,0x0004001e,0x0000001e,0x00000008,0x00000008,0x00040020,0x0000001f,
    0x00000009,0x0000001e,0x0004003b,0x0000001f,0x00000020,0x00000009,0x00040020,0x00000021,
    0x00000009,0x00000008,0x0004002b,0x00000006,0x00000028,0x00000000,0x0004002b,0x00000006,
    0x00000029,0x3f800000,0x00050036,0x00000002,0x00000004,0x00000000,0x00000003,0x000200f8,
    0x00000005,0x0004003d,0x00000007,0x00000010,0x0000000f,0x00050041,0x00000011,0x00000012,
    0x0000000b,0x0000000d,0x0003003e,0x00000012,0x00000010,0x0004003d,0x00000008,0x00000016,
    0x00000015,0x00050041,0x00000017,0x00000018,0x0000000b,0x00000013,0x0003003e,0x00000018,
    0x00000016,0x0004003d,0x00000008,0x0000001d,0x0000001c,0x00050041,0x00000021,0x00000022,
    0x00000020,0x0000000d,0x0004003d,0x00000008,0x00000023,0x00000022,0x00050085,0x00000008,
    0x00000024,0x0000001d,0x00000023,0x00050041,0x00000021,0x00000025,0x00000020,0x00000013,
    0x0004003d,0x00000008,0x00000026,0x00000025,0x00050081,0x00000008,0x00000027,0x00000024,
    0x00000026,0x00050051,0x00000006,0x0000002a,0x00000027,0x00000000,0x00050051,0x00000006,
    0x0000002b,0x00000027,0x00000001,0x00070050,0x00000007,0x0000002c,0x0000002a,0x0000002b,
    0x00000028,0x00000029,0x00050041,0x00000011,0x0000002d,0x0000001b,0x0000000d,0x0003003e,
    0x0000002d,0x0000002c,0x000100fd,0x00010038
};

// backends/vulkan/glsl_shader.frag, compiled with:
// # glslangValidator -V -x -o glsl_shader.frag.u32 glsl_shader.frag
/*
#version 450 core
layout(location = 0) out vec4 fColor;
layout(set=0, binding=0) uniform texture2D _Texture;
layout(set=1, binding=0) uniform sampler _Sampler;
layout(location = 0) in struct { vec4 Color; vec2 UV; } In;
void main()
{
    fColor = In.Color * texture(sampler2D(_Texture, _Sampler), In.UV.st);
}
*/
static uint32_t __glsl_shader_frag_spv[] =
{
    0x07230203,0x00010000,0x0008000b,0x00000023,0x00000000,0x00020011,0x00000001,0x0006000b,
    0x00000001,0x4c534c47,0x6474732e,0x3035342e,0x00000000,0x0003000e,0x00000000,0x00000001,
    0x0007000f,0x00000004,0x00000004,0x6e69616d,0x00000000,0x00000009,0x0000000d,0x00030010,
    0x00000004,0x00000007,0x00030003,0x00000002,0x000001c2,0x00040005,0x00000004,0x6e69616d,
    0x00000000,0x00040005,0x00000009,0x6c6f4366,0x0000726f,0x00030005,0x0000000b,0x00000000,
    0x00050006,0x0000000b,0x00000000,0x6f6c6f43,0x00000072,0x00040006,0x0000000b,0x00000001,
    0x00005655,0x00030005,0x0000000d,0x00006e49,0x00050005,0x00000015,0x7865545f,0x65727574,
    0x00000000,0x00050005,0x00000019,0x6d61535f,0x72656c70,0x00000000,0x00040047,0x00000009,
    0x0000001e,0x00000000,0x00040047,0x0000000d,0x0000001e,0x00000000,0x00040047,0x00000015,
    0x00000021,0x00000000,0x00040047,0x00000015,0x00000022,0x00000000,0x00040047,0x00000019,
    0x00000021,0x00000000,0x00040047,0x00000019,0x00000022,0x00000001,0x00020013,0x00000002,
    0x00030021,0x00000003,0x00000002,0x00030016,0x00000006,0x00000020,0x00040017,0x00000007,
    0x00000006,0x00000004,0x00040020,0x00000008,0x00000003,0x00000007,0x0004003b,0x00000008,
    0x00000009,0x00000003,0x00040017,0x0000000a,0x00000006,0x00000002,0x0004001e,0x0000000b,
    0x00000007,0x0000000a,0x00040020,0x0000000c,0x00000001,0x0000000b,0x0004003b,0x0000000c,
    0x0000000d,0x00000001,0x00040015,0x0000000e,0x00000020,0x00000001,0x0004002b,0x0000000e,
    0x0000000f,0x00000000,0x00040020,0x00000010,0x00000001,0x00000007,0x00090019,0x00000013,
    0x00000006,0x00000001,0x00000000,0x00000000,0x00000000,0x00000001,0x00000000,0x00040020,
    0x00000014,0x00000000,0x00000013,0x0004003b,0x00000014,0x00000015,0x00000000,0x0002001a,
    0x00000017,0x00040020,0x00000018,0x00000000,0x00000017,0x0004003b,0x00000018,0x00000019,
    0x00000000,0x0003001b,0x0000001b,0x00000013,0x0004002b,0x0000000e,0x0000001d,0x00000001,
    0x00040020,0x0000001e,0x00000001,0x0000000a,0x00050036,0x00000002,0x00000004,0x00000000,
    0x00000003,0x000200f8,0x00000005,0x00050041,0x00000010,0x00000011,0x0000000d,0x0000000f,
    0x0004003d,0x00000007,0x00000012,0x00000011,0x0004003d,0x00000013,0x00000016,0x00000015,
    0x0004003d,0x00000017,0x0000001a,0x00000019,0x00050056,0x0000001b,0x0000001c,0x00000016,
    0x0000001a,0x00050041,0x0000001e,0x0000001f,0x0000000d,0x0000001d,0x0004003d,0x0000000a,
    0x00000020,0x0000001f,0x00050057,0x00000007,0x00000021,0x0000001c,0x00000020,0x00050085,
    0x00000007,0x00000022,0x00000012,0x00000021,0x0003003e,0x00000009,0x00000022,0x000100fd,
    0x00010038
};

//-----------------------------------------------------------------------------
// FUNCTIONS
//-----------------------------------------------------------------------------

// Backend data stored in io.BackendRendererUserData to allow support for multiple Dear ImGui contexts
// It is STRONGLY preferred that you use docking branch with multi-viewports (== single Dear ImGui context + multiple windows) instead of multiple Dear ImGui contexts.
// FIXME: multi-context support is not tested and probably dysfunctional in this backend.
static ImGui_ImplVulkan_Data* ImGui_ImplVulkan_GetBackendData()
{
    return ImGui::GetCurrentContext() ? (ImGui_ImplVulkan_Data*)ImGui::GetIO().BackendRendererUserData : nullptr;
}

ImGui_ImplVulkan_RenderState* ImGui_ImplVulkan_GetRenderState()
{
    return (ImGui_ImplVulkan_RenderState*)ImGui::GetPlatformIO().Renderer_RenderState;
}

#ifdef IMGUI_IMPL_VULKAN_USE_LOADER
// Get the Vulkan function pointers used by the current backend.
// If no backend is available, return the currently loaded global function pointers (ImGuiImplVulkanFuncs).
static ImGui_ImplVulkan_Functions& ImGui_ImplVulkan_GetFunctions()
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    return bd ? bd->Functions : ImGuiImplVulkanFuncs;
}
#endif

static uint32_t ImGui_ImplVulkan_MemoryType(VkMemoryPropertyFlags properties, uint32_t type_bits)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    VkPhysicalDeviceMemoryProperties prop;
    vkGetPhysicalDeviceMemoryProperties(v->PhysicalDevice, &prop);
    for (uint32_t i = 0; i < prop.memoryTypeCount; i++)
        if ((prop.memoryTypes[i].propertyFlags & properties) == properties && (type_bits & (1u << i)))
            return i;
    return 0xFFFFFFFF; // Unable to find memoryType
}

static void check_vk_result(VkResult err)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    if (!bd)
        return;
    // VK_ERROR_DEVICE_LOST reported by ANY checked operation is terminal for this current backend only (no process-global state).
    // Recorded before the possibly throwing callback, so the callback and any catcher already observe it via GetTerminalResult().
    if (err == VK_ERROR_DEVICE_LOST)
        bd->TerminalResult = VK_ERROR_DEVICE_LOST;
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    if (v->CheckVkResultFn)
        v->CheckVkResultFn(err);
    // A qualified CheckVkResultFn throws on failure. Never continue past a failed VkResult (outputs may be untouched/null/dirty).
    if (err < 0)
        throw ImGui_ImplVulkan_Failure{ err, "Failed VkResult was not thrown by CheckVkResultFn" };
}

// Same as IM_MEMALIGN(). 'alignment' must be a power of two.
static inline VkDeviceSize AlignBufferSize(VkDeviceSize size, VkDeviceSize alignment)
{
    return (size + alignment - 1) & ~(alignment - 1);
}

[[noreturn]] static void ImGui_ImplVulkan_Fail(VkResult result, const char* reason)
{
    throw ImGui_ImplVulkan_Failure{ result, reason };
}

// Report an unsuccessful VkResult: failures go through CheckVkResultFn first. Always leaves by exception.
[[noreturn]] static void ImGui_ImplVulkan_ReportResult(VkResult result, const char* reason)
{
    if (result < 0)
        check_vk_result(result);
    throw ImGui_ImplVulkan_Failure{ result, reason };
}

static bool ImGui_ImplVulkan_CheckedMul(VkDeviceSize a, VkDeviceSize b, VkDeviceSize* out)
{
    if (a != 0 && b > ~(VkDeviceSize)0 / a)
        return false;
    *out = a * b;
    return true;
}

static bool ImGui_ImplVulkan_CheckedAlign(VkDeviceSize size, VkDeviceSize alignment, VkDeviceSize* out)
{
    if (alignment == 0 || (alignment & (alignment - 1)) != 0)
        return false;
    if (size > ~(VkDeviceSize)0 - (alignment - 1))
        return false;
    *out = AlignBufferSize(size, alignment);
    return true;
}

// EVERY backend VkDeviceMemory allocation goes through here (routing hook, or direct legacy call when no hooks are set).
// *out_memory is written only on VK_SUCCESS with a non-null identity; a failed output is never read or acquired.
static VkResult ImGui_ImplVulkan_AllocateDeviceMemory(const VkMemoryAllocateInfo* allocate_info, VkDeviceMemory* out_memory)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    if (allocate_info->memoryTypeIndex == 0xFFFFFFFF)
        ImGui_ImplVulkan_Fail(VK_ERROR_FEATURE_NOT_PRESENT, "No compatible Vulkan memory type");
    VkDeviceMemory memory = VK_NULL_HANDLE;
    VkResult err;
    if (v->AllocateDeviceMemoryFn != nullptr)
        err = v->AllocateDeviceMemoryFn(v->DeviceMemoryUserData, v->Device, allocate_info, v->Allocator, IMGUI_IMPL_VULKAN_PFN(vkAllocateMemory), &memory);
    else
        err = vkAllocateMemory(v->Device, allocate_info, v->Allocator, &memory);
    if (err == VK_SUCCESS && memory == VK_NULL_HANDLE)
        err = VK_ERROR_INITIALIZATION_FAILED; // Contract violation: success without an identity. Nothing is acquired.
    if (err == VK_SUCCESS)
        *out_memory = memory;
    return err;
}

// EVERY backend VkDeviceMemory free goes through here. Does not throw (free hook contract).
static void ImGui_ImplVulkan_FreeDeviceMemory(VkDeviceMemory memory)
{
    if (memory == VK_NULL_HANDLE)
        return;
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    if (v->FreeDeviceMemoryFn != nullptr)
        v->FreeDeviceMemoryFn(v->DeviceMemoryUserData, v->Device, memory, v->Allocator, IMGUI_IMPL_VULKAN_PFN(vkFreeMemory));
    else
        vkFreeMemory(v->Device, memory, v->Allocator);
}

static void CreateOrResizeBuffer(VkBuffer& buffer, VkDeviceMemory& buffer_memory, VkDeviceSize& buffer_size, VkDeviceSize new_size, VkBufferUsageFlagBits usage)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    VkResult err;

    VkDeviceSize buffer_size_aligned = 0;
    if (!ImGui_ImplVulkan_CheckedAlign(IM_MAX(v->MinAllocationSize, new_size), bd->BufferMemoryAlignment, &buffer_size_aligned))
        ImGui_ImplVulkan_Fail(VK_ERROR_OUT_OF_DEVICE_MEMORY, "Render buffer size overflow");
    VkBuffer new_buffer = VK_NULL_HANDLE;
    VkDeviceMemory new_buffer_memory = VK_NULL_HANDLE;
    bool has_buffer = false;
    bool has_memory = false;

    try
    {
        VkBufferCreateInfo buffer_info = {};
        buffer_info.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
        buffer_info.size = buffer_size_aligned;
        buffer_info.usage = usage;
        buffer_info.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        VkBuffer temp_buffer = VK_NULL_HANDLE;
        err = vkCreateBuffer(v->Device, &buffer_info, v->Allocator, &temp_buffer);
        if (err == VK_SUCCESS)
        {
            new_buffer = temp_buffer;
            has_buffer = true;
        }
        check_vk_result(err);

        VkMemoryRequirements req;
        vkGetBufferMemoryRequirements(v->Device, new_buffer, &req);
        bd->BufferMemoryAlignment = (bd->BufferMemoryAlignment > req.alignment) ? bd->BufferMemoryAlignment : req.alignment;
        VkMemoryAllocateInfo alloc_info = {};
        alloc_info.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        alloc_info.allocationSize = req.size;
        alloc_info.memoryTypeIndex = ImGui_ImplVulkan_MemoryType(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT, req.memoryTypeBits);
        VkDeviceMemory temp_memory = VK_NULL_HANDLE;
        err = ImGui_ImplVulkan_AllocateDeviceMemory(&alloc_info, &temp_memory);
        if (err == VK_SUCCESS)
        {
            new_buffer_memory = temp_memory;
            has_memory = true;
        }
        check_vk_result(err);

        err = vkBindBufferMemory(v->Device, new_buffer, new_buffer_memory, 0);
        check_vk_result(err);
    }
    catch (...)
    {
        if (has_buffer)
            vkDestroyBuffer(v->Device, new_buffer, v->Allocator);
        if (has_memory)
            ImGui_ImplVulkan_FreeDeviceMemory(new_buffer_memory);
        throw;
    }

    VkBuffer old_buffer = buffer;
    VkDeviceMemory old_memory = buffer_memory;

    buffer = new_buffer;
    buffer_memory = new_buffer_memory;
    buffer_size = buffer_size_aligned;

    if (old_buffer != VK_NULL_HANDLE)
        vkDestroyBuffer(v->Device, old_buffer, v->Allocator);
    if (old_memory != VK_NULL_HANDLE)
        ImGui_ImplVulkan_FreeDeviceMemory(old_memory);
}

static void ImGui_ImplVulkan_SetupRenderState(ImDrawData* draw_data, VkPipeline pipeline, VkCommandBuffer command_buffer, ImGui_ImplVulkan_FrameRenderBuffers* rb, int fb_width, int fb_height)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();

    // Bind pipeline:
    vkCmdBindPipeline(command_buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline);

    // Bind Vertex And Index Buffer:
    if (draw_data->TotalVtxCount > 0)
    {
        VkBuffer vertex_buffers[1] = { rb->VertexBuffer };
        VkDeviceSize vertex_offset[1] = { 0 };
        vkCmdBindVertexBuffers(command_buffer, 0, 1, vertex_buffers, vertex_offset);
        vkCmdBindIndexBuffer(command_buffer, rb->IndexBuffer, 0, sizeof(ImDrawIdx) == 2 ? VK_INDEX_TYPE_UINT16 : VK_INDEX_TYPE_UINT32);
    }

    // Setup viewport:
    VkViewport viewport;
    viewport.x = 0;
    viewport.y = 0;
    viewport.width = (float)fb_width;
    viewport.height = (float)fb_height;
    viewport.minDepth = 0.0f;
    viewport.maxDepth = 1.0f;
    vkCmdSetViewport(command_buffer, 0, 1, &viewport);

    // Setup scale and translation:
    // Our visible imgui space lies from draw_data->DisplayPps (top left) to draw_data->DisplayPos+data_data->DisplaySize (bottom right). DisplayPos is (0,0) for single viewport apps.
    float constants[4];
    constants[0] = 2.0f / draw_data->DisplaySize.x; // Scale
    constants[1] = 2.0f / draw_data->DisplaySize.y;
    constants[2] = -1.0f - draw_data->DisplayPos.x * constants[0]; // Translate
    constants[3] = -1.0f - draw_data->DisplayPos.y * constants[1];
    vkCmdPushConstants(command_buffer, bd->PipelineLayout, VK_SHADER_STAGE_VERTEX_BIT, 0, (uint32_t)sizeof(float) * 4, constants);

    // Setup sampler
    vkCmdBindDescriptorSets(bd->RenderState->CommandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, bd->PipelineLayout, 1, 1, &bd->SamplerLinearDS, 0, nullptr);
}

// Draw callbacks
static void ImGui_ImplVulkan_DrawCallback_ResetRenderState(const ImDrawList*, const ImDrawCmd*)     {} // Intentionally empty. Used as an identifier for rendering loop to call its code. Simpler to implement this way.
static void ImGui_ImplVulkan_DrawCallback_SetSamplerLinear(const ImDrawList*, const ImDrawCmd*)     { ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData(); vkCmdBindDescriptorSets(bd->RenderState->CommandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, bd->RenderState->PipelineLayout, 1, 1, &bd->SamplerLinearDS, 0, nullptr); }
static void ImGui_ImplVulkan_DrawCallback_SetSamplerNearest(const ImDrawList*, const ImDrawCmd*)    { ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData(); vkCmdBindDescriptorSets(bd->RenderState->CommandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, bd->RenderState->PipelineLayout, 1, 1, &bd->SamplerNearestDS, 0, nullptr); }

// If you want to use your own sampler, you can create your own callback, access ImGui_ImplVulkan_RenderState for command-buffer and pipeline layout, e.g.
/*
void ImGui_ImplVulkan_DrawCallback_SetSamplerCustom(const ImDrawList*, const ImDrawCmd* cmd)
{
    ImGui_ImplVulkan_RenderState* render_state = (ImGui_ImplVulkan_RenderState*)ImGui::GetPlatformIO().Renderer_RenderState;
    vkCmdBindDescriptorSets(render_state->CommandBuffer, VK_PIPELINE_BIND_POINT_GRAPHICS, render_state->PipelineLayout, 1, 1, (VkDescriptorSet*)cmd->UserCallbackData, 0, nullptr);
}
*/

// Render function
void ImGui_ImplVulkan_RenderDrawData(ImDrawData* draw_data, VkCommandBuffer command_buffer, VkPipeline pipeline)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    IM_ASSERT(bd != nullptr && "Context or backend not initialized! Did you call ImGui_ImplVulkan_Init()?");
    if (bd->TerminalResult != VK_SUCCESS)
        ImGui_ImplVulkan_Fail(bd->TerminalResult, "Rendering blocked after terminal device loss");

    // Validate extents/scale before any conversion
    if (!std::isfinite(draw_data->DisplayPos.x) || !std::isfinite(draw_data->DisplayPos.y) ||
        !std::isfinite(draw_data->DisplaySize.x) || !std::isfinite(draw_data->DisplaySize.y) ||
        !std::isfinite(draw_data->FramebufferScale.x) || !std::isfinite(draw_data->FramebufferScale.y))
        ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "Non-finite draw data extents or framebuffer scale");

    // Avoid rendering when minimized, scale coordinates for retina displays (screen coordinates != framebuffer coordinates)
    if (draw_data->DisplaySize.x <= 0.0f || draw_data->DisplaySize.y <= 0.0f || draw_data->FramebufferScale.x <= 0.0f || draw_data->FramebufferScale.y <= 0.0f)
        return;
    const float fb_width_f = draw_data->DisplaySize.x * draw_data->FramebufferScale.x + 0.5f;
    const float fb_height_f = draw_data->DisplaySize.y * draw_data->FramebufferScale.y + 0.5f;
    if (!std::isfinite(fb_width_f) || !std::isfinite(fb_height_f) || !(fb_width_f < 2147483648.0f) || !(fb_height_f < 2147483648.0f))
        ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "Framebuffer extent out of range");
    int fb_width = (int)fb_width_f;
    int fb_height = (int)fb_height_f;
    if (fb_width <= 0 || fb_height <= 0)
        return;

    // Catch up with texture updates. Most of the times, the list will have 1 element with an OK status, aka nothing to do.
    // (This almost always points to ImGui::GetPlatformIO().Textures[] but is part of ImDrawData to allow overriding or disabling texture updates).
    if (draw_data->Textures != nullptr)
        for (ImTextureData* tex : *draw_data->Textures)
            if (tex->Status != ImTextureStatus_OK)
                ImGui_ImplVulkan_UpdateTexture(tex);

    // Validate signed counts, per-list sizes and draw command ranges before any allocation, copy or signed/offset conversion
    if (draw_data->TotalVtxCount < 0 || draw_data->TotalIdxCount < 0 || draw_data->CmdLists.Size < 0)
        ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "Negative draw data counts");
    if (draw_data->TotalVtxCount > IMGUI_IMPL_VULKAN_MAX_FRAME_VERTICES || draw_data->TotalIdxCount > IMGUI_IMPL_VULKAN_MAX_FRAME_INDICES)
        ImGui_ImplVulkan_Fail(VK_ERROR_TOO_MANY_OBJECTS, "Frame vertex/index count exceeds admission");
    {
        long long vtx_sum = 0;
        long long idx_sum = 0;
        for (const ImDrawList* draw_list : draw_data->CmdLists)
        {
            if (draw_list == nullptr || draw_list->VtxBuffer.Size < 0 || draw_list->IdxBuffer.Size < 0 || draw_list->CmdBuffer.Size < 0)
                ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "Invalid draw list");
            vtx_sum += draw_list->VtxBuffer.Size;
            idx_sum += draw_list->IdxBuffer.Size;
            if (vtx_sum > draw_data->TotalVtxCount || idx_sum > draw_data->TotalIdxCount)
                ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "Draw list sizes exceed draw data totals");
            for (const ImDrawCmd& cmd : draw_list->CmdBuffer)
            {
                if (cmd.UserCallback != nullptr)
                    continue;
                if ((long long)cmd.IdxOffset + (long long)cmd.ElemCount > (long long)draw_list->IdxBuffer.Size)
                    ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "Draw command index range out of bounds");
                if (cmd.ElemCount != 0 && (long long)cmd.VtxOffset >= (long long)draw_list->VtxBuffer.Size)
                    ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "Draw command vertex offset out of bounds");
            }
        }
        if (vtx_sum != draw_data->TotalVtxCount || idx_sum != draw_data->TotalIdxCount)
            ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "Draw data totals do not match draw lists");
    }

    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    if (pipeline == VK_NULL_HANDLE)
        pipeline = bd->Pipeline;

    // Allocate array to store enough vertex/index buffers (ring size follows the actual selected ImageCount)
    ImGui_ImplVulkan_WindowRenderBuffers* wrb = &bd->MainWindowRenderBuffers;
    if (wrb->FrameRenderBuffers.Size == 0)
    {
        if (v->ImageCount == 0 || v->ImageCount > IMGUI_IMPL_VULKAN_MAX_IMAGE_COUNT)
            ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "Invalid ImageCount for render buffer ring");
        wrb->Index = 0;
        wrb->Count = v->ImageCount;
        wrb->FrameRenderBuffers.resize((int)wrb->Count);
        memset((void*)wrb->FrameRenderBuffers.Data, 0, wrb->FrameRenderBuffers.size_in_bytes());
    }
    IM_ASSERT(wrb->Count == v->ImageCount);
    wrb->Index = (wrb->Index + 1) % wrb->Count;
    ImGui_ImplVulkan_FrameRenderBuffers* rb = &wrb->FrameRenderBuffers[wrb->Index];

    if (draw_data->TotalVtxCount > 0)
    {
        // Create or resize the vertex/index buffers (checked byte products)
        VkDeviceSize vertex_bytes = 0, index_bytes = 0, vertex_size = 0, index_size = 0;
        if (!ImGui_ImplVulkan_CheckedMul((VkDeviceSize)draw_data->TotalVtxCount, (VkDeviceSize)sizeof(ImDrawVert), &vertex_bytes) ||
            !ImGui_ImplVulkan_CheckedMul((VkDeviceSize)draw_data->TotalIdxCount, (VkDeviceSize)sizeof(ImDrawIdx), &index_bytes) ||
            !ImGui_ImplVulkan_CheckedAlign(vertex_bytes, bd->BufferMemoryAlignment, &vertex_size) ||
            !ImGui_ImplVulkan_CheckedAlign(index_bytes, bd->BufferMemoryAlignment, &index_size))
            ImGui_ImplVulkan_Fail(VK_ERROR_OUT_OF_DEVICE_MEMORY, "Render buffer size overflow");
        if (rb->VertexBuffer == VK_NULL_HANDLE || rb->VertexBufferSize < vertex_size)
            CreateOrResizeBuffer(rb->VertexBuffer, rb->VertexBufferMemory, rb->VertexBufferSize, vertex_size, VK_BUFFER_USAGE_VERTEX_BUFFER_BIT);
        if (rb->IndexBuffer == VK_NULL_HANDLE || rb->IndexBufferSize < index_size)
            CreateOrResizeBuffer(rb->IndexBuffer, rb->IndexBufferMemory, rb->IndexBufferSize, index_size, VK_BUFFER_USAGE_INDEX_BUFFER_BIT);

        // Upload vertex/index data into a single contiguous GPU buffer.
        // Only successful mappings are tracked and unmapped, exactly once, on every exit.
        ImDrawVert* vtx_dst = nullptr;
        ImDrawIdx* idx_dst = nullptr;
        bool vtx_mapped = false;
        bool idx_mapped = false;
        try
        {
            void* mapped = nullptr;
            VkResult err = vkMapMemory(v->Device, rb->VertexBufferMemory, 0, vertex_size, 0, &mapped);
            if (err == VK_SUCCESS)
            {
                vtx_mapped = true;
                vtx_dst = (ImDrawVert*)mapped;
            }
            check_vk_result(err);
            mapped = nullptr;
            err = vkMapMemory(v->Device, rb->IndexBufferMemory, 0, index_size, 0, &mapped);
            if (err == VK_SUCCESS)
            {
                idx_mapped = true;
                idx_dst = (ImDrawIdx*)mapped;
            }
            check_vk_result(err);
            for (const ImDrawList* draw_list : draw_data->CmdLists)
            {
                if (draw_list->VtxBuffer.Size > 0)
                    memcpy(vtx_dst, draw_list->VtxBuffer.Data, (size_t)draw_list->VtxBuffer.Size * sizeof(ImDrawVert));
                if (draw_list->IdxBuffer.Size > 0)
                    memcpy(idx_dst, draw_list->IdxBuffer.Data, (size_t)draw_list->IdxBuffer.Size * sizeof(ImDrawIdx));
                vtx_dst += draw_list->VtxBuffer.Size;
                idx_dst += draw_list->IdxBuffer.Size;
            }
            VkMappedMemoryRange range[2] = {};
            range[0].sType = VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE;
            range[0].memory = rb->VertexBufferMemory;
            range[0].size = VK_WHOLE_SIZE;
            range[1].sType = VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE;
            range[1].memory = rb->IndexBufferMemory;
            range[1].size = VK_WHOLE_SIZE;
            err = vkFlushMappedMemoryRanges(v->Device, 2, range);
            check_vk_result(err);
        }
        catch (...)
        {
            if (idx_mapped)
                vkUnmapMemory(v->Device, rb->IndexBufferMemory);
            if (vtx_mapped)
                vkUnmapMemory(v->Device, rb->VertexBufferMemory);
            throw;
        }
        vkUnmapMemory(v->Device, rb->VertexBufferMemory);
        vkUnmapMemory(v->Device, rb->IndexBufferMemory);
    }

    // Setup render state structure (for callbacks and custom texture bindings).
    // The previous values are restored on every exit, so no stale stack pointer is ever left published.
    ImGuiPlatformIO& platform_io = ImGui::GetPlatformIO();
    ImGui_ImplVulkan_RenderState* const prev_backend_render_state = bd->RenderState;
    void* const prev_platform_render_state = platform_io.Renderer_RenderState;
    ImGui_ImplVulkan_RenderState render_state;
    render_state.CommandBuffer = command_buffer;
    render_state.Pipeline = pipeline;
    render_state.PipelineLayout = bd->PipelineLayout;
    platform_io.Renderer_RenderState = bd->RenderState = &render_state;

    try
    {
        // Setup desired Vulkan state
        ImGui_ImplVulkan_SetupRenderState(draw_data, pipeline, command_buffer, rb, fb_width, fb_height);

        // Will project scissor/clipping rectangles into framebuffer space
        ImVec2 clip_off = draw_data->DisplayPos;         // (0,0) unless using multi-viewports
        ImVec2 clip_scale = draw_data->FramebufferScale; // (1,1) unless using retina display which are often (2,2)

        // Render command lists
        // (Because we merged all buffers into a single one, we maintain our own offset into them)
        VkDescriptorSet last_image_view = VK_NULL_HANDLE;
        int global_vtx_offset = 0;
        int global_idx_offset = 0;
        for (const ImDrawList* draw_list : draw_data->CmdLists)
        {
            for (int cmd_i = 0; cmd_i < draw_list->CmdBuffer.Size; cmd_i++)
            {
                const ImDrawCmd* pcmd = &draw_list->CmdBuffer[cmd_i];
                if (pcmd->UserCallback != nullptr)
                {
                    // User callback, registered via ImDrawList::AddCallback()
                    if (pcmd->UserCallback == ImGui_ImplVulkan_DrawCallback_ResetRenderState)
                    {
                        ImGui_ImplVulkan_SetupRenderState(draw_data, pipeline, command_buffer, rb, fb_width, fb_height);
                        last_image_view = VK_NULL_HANDLE;
                    }
                    else
                        pcmd->UserCallback(draw_list, pcmd);
                }
                else
                {
                    // Project scissor/clipping rectangles into framebuffer space
                    ImVec2 clip_min((pcmd->ClipRect.x - clip_off.x) * clip_scale.x, (pcmd->ClipRect.y - clip_off.y) * clip_scale.y);
                    ImVec2 clip_max((pcmd->ClipRect.z - clip_off.x) * clip_scale.x, (pcmd->ClipRect.w - clip_off.y) * clip_scale.y);

                    // Clamp to viewport as vkCmdSetScissor() won't accept values that are off bounds
                    if (clip_min.x < 0.0f) { clip_min.x = 0.0f; }
                    if (clip_min.y < 0.0f) { clip_min.y = 0.0f; }
                    if (clip_max.x > (float)fb_width) { clip_max.x = (float)fb_width; }
                    if (clip_max.y > (float)fb_height) { clip_max.y = (float)fb_height; }
                    if (clip_max.x <= clip_min.x || clip_max.y <= clip_min.y)
                        continue;

                    // Apply scissor/clipping rectangle
                    VkRect2D scissor;
                    scissor.offset.x = (int32_t)(clip_min.x);
                    scissor.offset.y = (int32_t)(clip_min.y);
                    scissor.extent.width = (uint32_t)(clip_max.x - clip_min.x);
                    scissor.extent.height = (uint32_t)(clip_max.y - clip_min.y);
                    vkCmdSetScissor(command_buffer, 0, 1, &scissor);

                    // Bind DescriptorSets for image view (font or user texture) and samplers
                    VkDescriptorSet image_view = (VkDescriptorSet)pcmd->GetTexID();
                    if (image_view != last_image_view)
                        vkCmdBindDescriptorSets(command_buffer, VK_PIPELINE_BIND_POINT_GRAPHICS, bd->PipelineLayout, 0, 1, &image_view, 0, nullptr);
                    last_image_view = image_view;

                    // Draw
                    vkCmdDrawIndexed(command_buffer, pcmd->ElemCount, 1, pcmd->IdxOffset + global_idx_offset, pcmd->VtxOffset + global_vtx_offset, 0);
                }
            }
            global_idx_offset += draw_list->IdxBuffer.Size;
            global_vtx_offset += draw_list->VtxBuffer.Size;
        }
    }
    catch (...)
    {
        platform_io.Renderer_RenderState = prev_platform_render_state;
        bd->RenderState = prev_backend_render_state;
        throw;
    }
    platform_io.Renderer_RenderState = prev_platform_render_state;
    bd->RenderState = prev_backend_render_state;

    // Note: at this point both vkCmdSetViewport() and vkCmdSetScissor() have been called.
    // Our last values will leak into user/application rendering IF:
    // - Your app uses a pipeline with VK_DYNAMIC_STATE_VIEWPORT or VK_DYNAMIC_STATE_SCISSOR dynamic state
    // - And you forgot to call vkCmdSetViewport() and vkCmdSetScissor() yourself to explicitly set that state.
    // If you use VK_DYNAMIC_STATE_VIEWPORT or VK_DYNAMIC_STATE_SCISSOR you are responsible for setting the values before rendering.
    // In theory we should aim to backup/restore those values but I am not sure this is possible.
    // We perform a call to vkCmdSetScissor() to set back a full viewport which is likely to fix things for 99% users but technically this is not perfect. (See github #4644)
    VkRect2D scissor = { { 0, 0 }, { (uint32_t)fb_width, (uint32_t)fb_height } };
    vkCmdSetScissor(command_buffer, 0, 1, &scissor);
}

static void ImGui_ImplVulkan_DestroyTexture(ImTextureData* tex)
{
    if (ImGui_ImplVulkan_Texture* backend_tex = (ImGui_ImplVulkan_Texture*)tex->BackendUserData)
    {
        IM_ASSERT(backend_tex->DescriptorSet == (VkDescriptorSet)tex->TexID);
        ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
        ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
        ImGui_ImplVulkan_RemoveTexture(backend_tex->DescriptorSet);
        if (backend_tex->ImageView != VK_NULL_HANDLE)
            vkDestroyImageView(v->Device, backend_tex->ImageView, v->Allocator);
        if (backend_tex->Image != VK_NULL_HANDLE)
            vkDestroyImage(v->Device, backend_tex->Image, v->Allocator);
        ImGui_ImplVulkan_FreeDeviceMemory(backend_tex->Memory);
        IM_DELETE(backend_tex);

        // Clear identifiers and mark as destroyed (in order to allow e.g. calling InvalidateDeviceObjects while running)
        tex->SetTexID(ImTextureID_Invalid);
        tex->BackendUserData = nullptr;
    }
    tex->SetStatus(ImTextureStatus_Destroyed);
}

// Free the single upload staging owner (buffer first, then its memory) exactly once. Never throws.
static void ImGui_ImplVulkan_ReleaseUploadStaging()
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    if (bd->UploadBuffer != VK_NULL_HANDLE)
    {
        VkBuffer buffer = bd->UploadBuffer;
        bd->UploadBuffer = VK_NULL_HANDLE;
        vkDestroyBuffer(v->Device, buffer, v->Allocator);
    }
    if (bd->UploadBufferMemory != VK_NULL_HANDLE)
    {
        VkDeviceMemory memory = bd->UploadBufferMemory;
        bd->UploadBufferMemory = VK_NULL_HANDLE;
        ImGui_ImplVulkan_FreeDeviceMemory(memory);
    }
    bd->UploadSubmitted = false;
}

// VK_ERROR_DEVICE_LOST is a terminal failed run. It is success-equivalent ONLY for pending/in-use lifetime determination.
static void ImGui_ImplVulkan_EnterTerminal(VkResult result)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    bd->TerminalResult = result; // Current backend only: no process-global latch, no cross-context poisoning
}

// Completion/device-loss disposition remains unknown after the single exceptional wait: possibly live GPU objects must not be freed
// by any destructor. Flush diagnostics and end the process with a nonzero result (not a recoverable editor-disable path).
[[noreturn]] static void ImGui_ImplVulkan_FatalUnresolvedUpload(const char* stage, VkResult initiating_result, VkResult exceptional_wait_result)
{
    fprintf(stderr, "[imgui_impl_vulkan] FATAL: texture upload completion unresolved (stage=%s, initiating_result=%d%s, exceptional_fence_wait_result=%d%s, wait_ns=%llu). Terminating before GPU objects can be freed.\n",
        stage, (int)initiating_result, (initiating_result == VK_RESULT_MAX_ENUM) ? " (exception/not reached)" : "",
        (int)exceptional_wait_result, (exceptional_wait_result == VK_RESULT_MAX_ENUM) ? " (exception)" : "",
        (unsigned long long)IMGUI_IMPL_VULKAN_UPLOAD_WAIT_NS);
    fflush(stderr);
    fflush(stdout);
    std::_Exit(3);
}

// Unknown outcome or timeout: make AT MOST ONE exceptional finite wait on the real owning fence.
// Returns only when the pending lifetime is resolved (completed => owner freed; device lost => terminal, owner freed). Never throws.
static void ImGui_ImplVulkan_ResolveUnknownUpload(const char* stage, VkResult initiating_result)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    VkResult wait_result = VK_RESULT_MAX_ENUM;
    try
    {
        wait_result = vkWaitForFences(v->Device, 1, &bd->UploadFence, VK_TRUE, IMGUI_IMPL_VULKAN_UPLOAD_WAIT_NS);
    }
    catch (...)
    {
        wait_result = VK_RESULT_MAX_ENUM;
    }
    if (wait_result == VK_SUCCESS)
    {
        ImGui_ImplVulkan_ReleaseUploadStaging();
        return;
    }
    if (wait_result == VK_ERROR_DEVICE_LOST)
    {
        ImGui_ImplVulkan_EnterTerminal(VK_ERROR_DEVICE_LOST);
        ImGui_ImplVulkan_ReleaseUploadStaging();
        return;
    }
    ImGui_ImplVulkan_FatalUnresolvedUpload(stage, initiating_result, wait_result);
}

// Resolve the single upload owner before reuse/reset/destroy/shutdown. Never throws.
static void ImGui_ImplVulkan_ResolvePendingUpload()
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    if (bd->UploadSubmitted)
        ImGui_ImplVulkan_ResolveUnknownUpload("pending upload at reuse/destroy", VK_RESULT_MAX_ENUM);
    else
        ImGui_ImplVulkan_ReleaseUploadStaging(); // Never submitted: unreferenced by the device
}

static void ImGui_ImplVulkan_ValidateTexture(const ImTextureData* tex)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    int max_dimension = IMGUI_IMPL_VULKAN_MAX_TEXTURE_DIMENSION;
    if (bd->MaxImageDimension2D != 0 && bd->MaxImageDimension2D < (uint32_t)max_dimension)
        max_dimension = (int)bd->MaxImageDimension2D;
    if (tex->Format != ImTextureFormat_RGBA32 || tex->BytesPerPixel != 4)
        ImGui_ImplVulkan_Fail(VK_ERROR_FORMAT_NOT_SUPPORTED, "Only RGBA32 (4 bytes per pixel) textures are supported");
    if (tex->Width <= 0 || tex->Height <= 0 || tex->Width > max_dimension || tex->Height > max_dimension)
        ImGui_ImplVulkan_Fail(VK_ERROR_TOO_MANY_OBJECTS, "Texture dimensions outside admission (1..4096, device limit)");
    if (tex->Pixels == nullptr)
        ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "Texture has no CPU pixels");
}

// Shared upload algorithm for WantCreate (full rect, from UNDEFINED) and WantUpdates (UpdateRect, from SHADER_READ_ONLY).
// The staging owner, command buffer and fence are recorded in backend data before vkQueueSubmit(); completion is resolved before return.
static void ImGui_ImplVulkan_UploadTextureRect(ImTextureData* tex, ImGui_ImplVulkan_Texture* backend_tex, int upload_x, int upload_y, int upload_w, int upload_h, VkImageLayout old_layout)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    VkResult err;

    // A previous owner must be resolved before the staging slot, command pool and fence are reused.
    ImGui_ImplVulkan_ResolvePendingUpload();
    if (bd->TerminalResult != VK_SUCCESS)
        ImGui_ImplVulkan_Fail(bd->TerminalResult, "Texture upload blocked after terminal device loss");
    if (bd->UploadFence == VK_NULL_HANDLE || bd->TexCommandPool == VK_NULL_HANDLE || bd->TexCommandBuffer == VK_NULL_HANDLE)
        ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "Texture upload requires the owned upload fence and command buffer");
    bd->LastUploadSubmitResult = VK_RESULT_MAX_ENUM;
    bd->LastUploadWaitResult = VK_RESULT_MAX_ENUM;

    // Validate the rectangle and every size/alignment before allocation and memcpy
    if (upload_x < 0 || upload_y < 0 || upload_w <= 0 || upload_h <= 0 || upload_x > tex->Width - upload_w || upload_y > tex->Height - upload_h)
        ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "Texture upload rectangle out of bounds");
    VkDeviceSize upload_pitch = 0, upload_bytes = 0, upload_size = 0;
    if (!ImGui_ImplVulkan_CheckedMul((VkDeviceSize)upload_w, (VkDeviceSize)tex->BytesPerPixel, &upload_pitch) ||
        !ImGui_ImplVulkan_CheckedMul(upload_pitch, (VkDeviceSize)upload_h, &upload_bytes))
        ImGui_ImplVulkan_Fail(VK_ERROR_OUT_OF_DEVICE_MEMORY, "Texture upload size overflow");
    if (upload_bytes > IMGUI_IMPL_VULKAN_MAX_UPLOAD_BYTES)
        ImGui_ImplVulkan_Fail(VK_ERROR_TOO_MANY_OBJECTS, "Texture upload exceeds the 64 MiB staging admission");
    if (!ImGui_ImplVulkan_CheckedAlign(upload_bytes, bd->NonCoherentAtomSize, &upload_size))
        ImGui_ImplVulkan_Fail(VK_ERROR_OUT_OF_DEVICE_MEMORY, "Texture upload alignment overflow");
    const size_t src_pitch = (size_t)tex->Width * (size_t)tex->BytesPerPixel; // Bounded by ValidateTexture()
    const size_t row_bytes = (size_t)upload_pitch;

    try
    {
        // Create the Upload Buffer (each output committed to the backend-owned slot only after VK_SUCCESS):
        {
            VkBufferCreateInfo buffer_info = {};
            buffer_info.sType = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO;
            buffer_info.size = upload_size;
            buffer_info.usage = VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
            buffer_info.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
            VkBuffer buffer = VK_NULL_HANDLE;
            err = vkCreateBuffer(v->Device, &buffer_info, v->Allocator, &buffer);
            if (err == VK_SUCCESS)
                bd->UploadBuffer = buffer;
            check_vk_result(err);
            VkMemoryRequirements req;
            vkGetBufferMemoryRequirements(v->Device, bd->UploadBuffer, &req);
            bd->BufferMemoryAlignment = (bd->BufferMemoryAlignment > req.alignment) ? bd->BufferMemoryAlignment : req.alignment;
            VkMemoryAllocateInfo alloc_info = {};
            alloc_info.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
            alloc_info.allocationSize = IM_MAX(v->MinAllocationSize, req.size);
            alloc_info.memoryTypeIndex = ImGui_ImplVulkan_MemoryType(VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT, req.memoryTypeBits);
            VkDeviceMemory memory = VK_NULL_HANDLE;
            err = ImGui_ImplVulkan_AllocateDeviceMemory(&alloc_info, &memory);
            if (err == VK_SUCCESS)
                bd->UploadBufferMemory = memory;
            check_vk_result(err);
            err = vkBindBufferMemory(v->Device, bd->UploadBuffer, bd->UploadBufferMemory, 0);
            check_vk_result(err);
        }

        // Upload to Buffer (a failed map output is never read; a successful map is unmapped exactly once):
        {
            void* mapped = nullptr;
            err = vkMapMemory(v->Device, bd->UploadBufferMemory, 0, upload_size, 0, &mapped);
            check_vk_result(err);
            try
            {
                char* map = (char*)mapped;
                const char* src = (const char*)tex->GetPixelsAt(upload_x, upload_y);
                for (int y = 0; y < upload_h; y++)
                    memcpy(map + row_bytes * (size_t)y, src + src_pitch * (size_t)y, row_bytes);
                VkMappedMemoryRange range[1] = {};
                range[0].sType = VK_STRUCTURE_TYPE_MAPPED_MEMORY_RANGE;
                range[0].memory = bd->UploadBufferMemory;
                range[0].size = upload_size;
                err = vkFlushMappedMemoryRanges(v->Device, 1, range);
                check_vk_result(err);
            }
            catch (...)
            {
                vkUnmapMemory(v->Device, bd->UploadBufferMemory);
                throw;
            }
            vkUnmapMemory(v->Device, bd->UploadBufferMemory);
        }

        // Start command buffer (any previous upload is resolved, so the fence and command pool may be reset)
        {
            err = vkResetFences(v->Device, 1, &bd->UploadFence);
            check_vk_result(err);
            err = vkResetCommandPool(v->Device, bd->TexCommandPool, 0);
            check_vk_result(err);
            VkCommandBufferBeginInfo begin_info = {};
            begin_info.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
            begin_info.flags |= VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
            err = vkBeginCommandBuffer(bd->TexCommandBuffer, &begin_info);
            check_vk_result(err);
        }

        // Copy to Image:
        {
            VkBufferMemoryBarrier upload_barrier[1] = {};
            upload_barrier[0].sType = VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER;
            upload_barrier[0].srcAccessMask = VK_ACCESS_HOST_WRITE_BIT;
            upload_barrier[0].dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT;
            upload_barrier[0].srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            upload_barrier[0].dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            upload_barrier[0].buffer = bd->UploadBuffer;
            upload_barrier[0].offset = 0;
            upload_barrier[0].size = upload_size;

            VkImageMemoryBarrier copy_barrier[1] = {};
            copy_barrier[0].sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
            copy_barrier[0].dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
            copy_barrier[0].oldLayout = old_layout;
            copy_barrier[0].newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
            copy_barrier[0].srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            copy_barrier[0].dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            copy_barrier[0].image = backend_tex->Image;
            copy_barrier[0].subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
            copy_barrier[0].subresourceRange.levelCount = 1;
            copy_barrier[0].subresourceRange.layerCount = 1;
            vkCmdPipelineBarrier(bd->TexCommandBuffer, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT | VK_PIPELINE_STAGE_HOST_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, nullptr, 1, upload_barrier, 1, copy_barrier);

            VkBufferImageCopy region = {};
            region.imageSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
            region.imageSubresource.layerCount = 1;
            region.imageExtent.width = (uint32_t)upload_w;
            region.imageExtent.height = (uint32_t)upload_h;
            region.imageExtent.depth = 1;
            region.imageOffset.x = upload_x;
            region.imageOffset.y = upload_y;
            vkCmdCopyBufferToImage(bd->TexCommandBuffer, bd->UploadBuffer, backend_tex->Image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &region);

            VkImageMemoryBarrier use_barrier[1] = {};
            use_barrier[0].sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
            use_barrier[0].srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
            use_barrier[0].dstAccessMask = VK_ACCESS_SHADER_READ_BIT;
            use_barrier[0].oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
            use_barrier[0].newLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
            use_barrier[0].srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            use_barrier[0].dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
            use_barrier[0].image = backend_tex->Image;
            use_barrier[0].subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
            use_barrier[0].subresourceRange.levelCount = 1;
            use_barrier[0].subresourceRange.layerCount = 1;
            vkCmdPipelineBarrier(bd->TexCommandBuffer, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, 0, 0, nullptr, 0, nullptr, 1, use_barrier);
        }

        // End command buffer
        err = vkEndCommandBuffer(bd->TexCommandBuffer);
        check_vk_result(err);
    }
    catch (...)
    {
        // Nothing was submitted: the staging owner is unreferenced by the device.
        ImGui_ImplVulkan_ReleaseUploadStaging();
        throw;
    }

    // Submit. Staging, command buffer and fence are all owned by backend data at this point (no local handles can be lost).
    VkSubmitInfo submit_info = {};
    submit_info.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    submit_info.commandBufferCount = 1;
    submit_info.pCommandBuffers = &bd->TexCommandBuffer;
    VkResult submit_result = VK_RESULT_MAX_ENUM;
    bool submit_threw = false;
    std::exception_ptr submit_exception;
    try
    {
        submit_result = vkQueueSubmit(v->Queue, 1, &submit_info, bd->UploadFence);
    }
    catch (...)
    {
        submit_threw = true;
        submit_exception = std::current_exception();
    }
    bd->LastUploadSubmitResult = submit_threw ? VK_RESULT_MAX_ENUM : submit_result;
    if (submit_threw)
    {
        // An arbitrary exception is not evidence of 'not submitted': resolve on the real fence, then rethrow the original exception.
        bd->UploadSubmitted = true;
        ImGui_ImplVulkan_ResolveUnknownUpload("vkQueueSubmit threw", VK_RESULT_MAX_ENUM);
        std::rethrow_exception(submit_exception);
    }
    if (submit_result == VK_ERROR_OUT_OF_HOST_MEMORY || submit_result == VK_ERROR_OUT_OF_DEVICE_MEMORY)
    {
        // Known vkQueueSubmit out-of-memory return: referenced state is unaffected, clean up as not submitted.
        ImGui_ImplVulkan_ReleaseUploadStaging();
        ImGui_ImplVulkan_ReportResult(submit_result, "vkQueueSubmit out of memory (not submitted)");
    }
    if (submit_result == VK_ERROR_DEVICE_LOST)
    {
        ImGui_ImplVulkan_EnterTerminal(VK_ERROR_DEVICE_LOST);
        ImGui_ImplVulkan_ReleaseUploadStaging(); // Lifetime-only success equivalence
        ImGui_ImplVulkan_ReportResult(submit_result, "vkQueueSubmit device lost (terminal)");
    }
    bd->UploadSubmitted = true;
    if (submit_result != VK_SUCCESS)
    {
        ImGui_ImplVulkan_ResolveUnknownUpload("vkQueueSubmit", submit_result);
        ImGui_ImplVulkan_ReportResult(submit_result, "vkQueueSubmit failed with unknown submission outcome");
    }

    // Normal completion wait on the owned fence (replaces the former vkQueueWaitIdle()).
    VkResult wait_result = VK_RESULT_MAX_ENUM;
    bool wait_threw = false;
    std::exception_ptr wait_exception;
    try
    {
        wait_result = vkWaitForFences(v->Device, 1, &bd->UploadFence, VK_TRUE, IMGUI_IMPL_VULKAN_UPLOAD_WAIT_NS);
    }
    catch (...)
    {
        wait_threw = true;
        wait_exception = std::current_exception();
    }
    bd->LastUploadWaitResult = wait_threw ? VK_RESULT_MAX_ENUM : wait_result;
    if (wait_threw)
    {
        ImGui_ImplVulkan_ResolveUnknownUpload("vkWaitForFences threw", VK_RESULT_MAX_ENUM);
        std::rethrow_exception(wait_exception);
    }
    if (wait_result == VK_SUCCESS)
    {
        ImGui_ImplVulkan_ReleaseUploadStaging(); // Completed: buffer then memory, once
        return;
    }
    if (wait_result == VK_ERROR_DEVICE_LOST)
    {
        ImGui_ImplVulkan_EnterTerminal(VK_ERROR_DEVICE_LOST);
        ImGui_ImplVulkan_ReleaseUploadStaging();
        ImGui_ImplVulkan_ReportResult(wait_result, "Upload fence wait device lost (terminal)");
    }
    // VK_TIMEOUT or another failure: completion unknown
    ImGui_ImplVulkan_ResolveUnknownUpload("vkWaitForFences", wait_result);
    ImGui_ImplVulkan_ReportResult(wait_result, "Upload fence wait did not complete normally");
}

void ImGui_ImplVulkan_UpdateTexture(ImTextureData* tex)
{
    if (tex->Status == ImTextureStatus_OK)
        return;
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    VkResult err;

    if (tex->Status == ImTextureStatus_WantCreate || tex->Status == ImTextureStatus_WantUpdates)
    {
        if (bd->TerminalResult != VK_SUCCESS)
            ImGui_ImplVulkan_Fail(bd->TerminalResult, "Texture update blocked after terminal device loss");
        ImGui_ImplVulkan_ValidateTexture(tex); // Before any allocation
    }

    // (A texture already holding backend objects in WantCreate state is a retry after a failed upload: its objects are reused.)
    if (tex->Status == ImTextureStatus_WantCreate && tex->BackendUserData == nullptr)
    {
        // Create and upload new texture to graphics system
        //IMGUI_DEBUG_LOG("UpdateTexture #%03d: WantCreate %dx%d\n", tex->UniqueID, tex->Width, tex->Height);
        IM_ASSERT(tex->TexID == ImTextureID_Invalid);
        ImGui_ImplVulkan_Texture* backend_tex = IM_NEW(ImGui_ImplVulkan_Texture)();
        backend_tex->Width = tex->Width;
        backend_tex->Height = tex->Height;
        bool has_image = false;
        bool has_memory = false;
        bool has_view = false;
        bool has_descriptor = false;

        try
        {
            // Create the Image:
            {
                VkImageCreateInfo info = {};
                info.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
                info.imageType = VK_IMAGE_TYPE_2D;
                info.format = VK_FORMAT_R8G8B8A8_UNORM;
                info.extent.width = (uint32_t)tex->Width;
                info.extent.height = (uint32_t)tex->Height;
                info.extent.depth = 1;
                info.mipLevels = 1;
                info.arrayLayers = 1;
                info.samples = VK_SAMPLE_COUNT_1_BIT;
                info.tiling = VK_IMAGE_TILING_OPTIMAL;
                info.usage = VK_IMAGE_USAGE_SAMPLED_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT;
                info.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
                info.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
                VkImage image = VK_NULL_HANDLE;
                err = vkCreateImage(v->Device, &info, v->Allocator, &image);
                if (err == VK_SUCCESS)
                {
                    backend_tex->Image = image;
                    has_image = true;
                }
                check_vk_result(err);
                VkMemoryRequirements req;
                vkGetImageMemoryRequirements(v->Device, backend_tex->Image, &req);
                VkMemoryAllocateInfo alloc_info = {};
                alloc_info.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
                alloc_info.allocationSize = IM_MAX(v->MinAllocationSize, req.size);
                alloc_info.memoryTypeIndex = ImGui_ImplVulkan_MemoryType(VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, req.memoryTypeBits);
                VkDeviceMemory memory = VK_NULL_HANDLE;
                err = ImGui_ImplVulkan_AllocateDeviceMemory(&alloc_info, &memory);
                if (err == VK_SUCCESS)
                {
                    backend_tex->Memory = memory;
                    has_memory = true;
                }
                check_vk_result(err);
                err = vkBindImageMemory(v->Device, backend_tex->Image, backend_tex->Memory, 0);
                check_vk_result(err);
            }

            // Create the Image View:
            {
                VkImageViewCreateInfo info = {};
                info.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
                info.image = backend_tex->Image;
                info.viewType = VK_IMAGE_VIEW_TYPE_2D;
                info.format = VK_FORMAT_R8G8B8A8_UNORM;
                info.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
                info.subresourceRange.levelCount = 1;
                info.subresourceRange.layerCount = 1;
                VkImageView image_view = VK_NULL_HANDLE;
                err = vkCreateImageView(v->Device, &info, v->Allocator, &image_view);
                if (err == VK_SUCCESS)
                {
                    backend_tex->ImageView = image_view;
                    has_view = true;
                }
                check_vk_result(err);
            }

            // Create the Descriptor Set (only a successful, counted registration is returned)
            backend_tex->DescriptorSet = ImGui_ImplVulkan_AddTexture(backend_tex->ImageView, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL);
            has_descriptor = (backend_tex->DescriptorSet != VK_NULL_HANDLE);
        }
        catch (...)
        {
            if (has_descriptor)
                ImGui_ImplVulkan_RemoveTexture(backend_tex->DescriptorSet);
            if (has_view)
                vkDestroyImageView(v->Device, backend_tex->ImageView, v->Allocator);
            if (has_image)
                vkDestroyImage(v->Device, backend_tex->Image, v->Allocator);
            if (has_memory)
                ImGui_ImplVulkan_FreeDeviceMemory(backend_tex->Memory);
            IM_DELETE(backend_tex);
            throw;
        }

        // Store identifiers
        tex->SetTexID((ImTextureID)backend_tex->DescriptorSet);
        tex->BackendUserData = backend_tex;
    }

    if (tex->Status == ImTextureStatus_WantCreate || tex->Status == ImTextureStatus_WantUpdates)
    {
        ImGui_ImplVulkan_Texture* backend_tex = (ImGui_ImplVulkan_Texture*)tex->BackendUserData;
        if (backend_tex == nullptr || backend_tex->Width != tex->Width || backend_tex->Height != tex->Height)
            ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "Texture update has no matching backend texture");

        // Update full texture or selected blocks. We only ever write to textures regions which have never been used before!
        // This backend choose to use tex->UpdateRect but you can use tex->Updates[] to upload individual regions.
        // We could use the smaller rect on _WantCreate but using the full rect allows us to clear the texture.
        const bool full_upload = (tex->Status == ImTextureStatus_WantCreate);
        const int upload_x = full_upload ? 0 : tex->UpdateRect.x;
        const int upload_y = full_upload ? 0 : tex->UpdateRect.y;
        const int upload_w = full_upload ? tex->Width : tex->UpdateRect.w;
        const int upload_h = full_upload ? tex->Height : tex->UpdateRect.h;
        if (upload_w > 0 && upload_h > 0) // An empty update rectangle has no pixels to copy
            ImGui_ImplVulkan_UploadTextureRect(tex, backend_tex, upload_x, upload_y, upload_w, upload_h, full_upload ? VK_IMAGE_LAYOUT_UNDEFINED : VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL);
        tex->SetStatus(ImTextureStatus_OK);
    }

    if (tex->Status == ImTextureStatus_WantDestroy && tex->UnusedFrames >= (int)bd->VulkanInitInfo.ImageCount)
        ImGui_ImplVulkan_DestroyTexture(tex);
}

static void ImGui_ImplVulkan_CreateShaderModules(VkDevice device, const VkAllocationCallbacks* allocator)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    if (bd->ShaderModuleVert == VK_NULL_HANDLE)
    {
        VkShaderModuleCreateInfo default_vert_info = {};
        default_vert_info.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
        default_vert_info.codeSize = sizeof(__glsl_shader_vert_spv);
        default_vert_info.pCode = (uint32_t*)__glsl_shader_vert_spv;
        VkShaderModuleCreateInfo* p_vert_info = (v->CustomShaderVertCreateInfo.sType == VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO) ? &v->CustomShaderVertCreateInfo : &default_vert_info;
        VkShaderModule shader_module = VK_NULL_HANDLE;
        VkResult err = vkCreateShaderModule(device, p_vert_info, allocator, &shader_module);
        if (err == VK_SUCCESS)
            bd->ShaderModuleVert = shader_module;
        check_vk_result(err);
    }
    if (bd->ShaderModuleFrag == VK_NULL_HANDLE)
    {
        VkShaderModuleCreateInfo default_frag_info = {};
        default_frag_info.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
        default_frag_info.codeSize = sizeof(__glsl_shader_frag_spv);
        default_frag_info.pCode = (uint32_t*)__glsl_shader_frag_spv;
        VkShaderModuleCreateInfo* p_frag_info = (v->CustomShaderFragCreateInfo.sType == VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO) ? &v->CustomShaderFragCreateInfo : &default_frag_info;
        VkShaderModule shader_module = VK_NULL_HANDLE;
        VkResult err = vkCreateShaderModule(device, p_frag_info, allocator, &shader_module);
        if (err == VK_SUCCESS)
            bd->ShaderModuleFrag = shader_module;
        check_vk_result(err);
    }
}

#if !defined(IMGUI_IMPL_VULKAN_HAS_DYNAMIC_RENDERING) && !(defined(VK_VERSION_1_3) || defined(VK_KHR_dynamic_rendering))
typedef void VkPipelineRenderingCreateInfoKHR;
#endif

static VkPipeline ImGui_ImplVulkan_CreatePipeline(VkDevice device, const VkAllocationCallbacks* allocator, VkPipelineCache pipelineCache, const ImGui_ImplVulkan_PipelineInfo* info)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_CreateShaderModules(device, allocator);

    VkPipelineShaderStageCreateInfo stage[2] = {};
    stage[0].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stage[0].stage = VK_SHADER_STAGE_VERTEX_BIT;
    stage[0].module = bd->ShaderModuleVert;
    stage[0].pName = "main";
    stage[1].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
    stage[1].stage = VK_SHADER_STAGE_FRAGMENT_BIT;
    stage[1].module = bd->ShaderModuleFrag;
    stage[1].pName = "main";

    VkVertexInputBindingDescription binding_desc[1] = {};
    binding_desc[0].stride = sizeof(ImDrawVert);
    binding_desc[0].inputRate = VK_VERTEX_INPUT_RATE_VERTEX;

    VkVertexInputAttributeDescription attribute_desc[3] = {};
    attribute_desc[0].location = 0;
    attribute_desc[0].binding = binding_desc[0].binding;
    attribute_desc[0].format = VK_FORMAT_R32G32_SFLOAT;
    attribute_desc[0].offset = offsetof(ImDrawVert, pos);
    attribute_desc[1].location = 1;
    attribute_desc[1].binding = binding_desc[0].binding;
    attribute_desc[1].format = VK_FORMAT_R32G32_SFLOAT;
    attribute_desc[1].offset = offsetof(ImDrawVert, uv);
    attribute_desc[2].location = 2;
    attribute_desc[2].binding = binding_desc[0].binding;
    attribute_desc[2].format = VK_FORMAT_R8G8B8A8_UNORM;
    attribute_desc[2].offset = offsetof(ImDrawVert, col);

    VkPipelineVertexInputStateCreateInfo vertex_info = {};
    vertex_info.sType = VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO;
    vertex_info.vertexBindingDescriptionCount = 1;
    vertex_info.pVertexBindingDescriptions = binding_desc;
    vertex_info.vertexAttributeDescriptionCount = 3;
    vertex_info.pVertexAttributeDescriptions = attribute_desc;

    VkPipelineInputAssemblyStateCreateInfo ia_info = {};
    ia_info.sType = VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO;
    ia_info.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;

    VkPipelineViewportStateCreateInfo viewport_info = {};
    viewport_info.sType = VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO;
    viewport_info.viewportCount = 1;
    viewport_info.scissorCount = 1;

    VkPipelineRasterizationStateCreateInfo raster_info = {};
    raster_info.sType = VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO;
    raster_info.polygonMode = VK_POLYGON_MODE_FILL;
    raster_info.cullMode = VK_CULL_MODE_NONE;
    raster_info.frontFace = VK_FRONT_FACE_COUNTER_CLOCKWISE;
    raster_info.lineWidth = 1.0f;

    VkPipelineMultisampleStateCreateInfo ms_info = {};
    ms_info.sType = VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO;
    ms_info.rasterizationSamples = (info->MSAASamples != 0) ? info->MSAASamples : VK_SAMPLE_COUNT_1_BIT;

    // Blend into the first color attachment. With dynamic rendering, other color attachments of the rendering are left untouched (requires independentBlend feature).
    int color_attachment_count = 1;
#ifdef IMGUI_IMPL_VULKAN_HAS_DYNAMIC_RENDERING
    if (bd->VulkanInitInfo.UseDynamicRendering && info->PipelineRenderingCreateInfo.colorAttachmentCount > 1)
        color_attachment_count = (int)info->PipelineRenderingCreateInfo.colorAttachmentCount;
#endif
    ImVector<VkPipelineColorBlendAttachmentState> color_attachment;
    color_attachment.resize(color_attachment_count, VkPipelineColorBlendAttachmentState()); // colorWriteMask = 0
    color_attachment[0].blendEnable = VK_TRUE;
    color_attachment[0].srcColorBlendFactor = VK_BLEND_FACTOR_SRC_ALPHA;
    color_attachment[0].dstColorBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
    color_attachment[0].colorBlendOp = VK_BLEND_OP_ADD;
    color_attachment[0].srcAlphaBlendFactor = VK_BLEND_FACTOR_ONE;
    color_attachment[0].dstAlphaBlendFactor = VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA;
    color_attachment[0].alphaBlendOp = VK_BLEND_OP_ADD;
    color_attachment[0].colorWriteMask = VK_COLOR_COMPONENT_R_BIT | VK_COLOR_COMPONENT_G_BIT | VK_COLOR_COMPONENT_B_BIT | VK_COLOR_COMPONENT_A_BIT;

    VkPipelineDepthStencilStateCreateInfo depth_info = {};
    depth_info.sType = VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO;

    VkPipelineColorBlendStateCreateInfo blend_info = {};
    blend_info.sType = VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO;
    blend_info.attachmentCount = (uint32_t)color_attachment.Size;
    blend_info.pAttachments = color_attachment.Data;

    ImVector<VkDynamicState> dynamic_states = info->ExtraDynamicStates;
    dynamic_states.push_back(VK_DYNAMIC_STATE_VIEWPORT);
    dynamic_states.push_back(VK_DYNAMIC_STATE_SCISSOR);
    VkPipelineDynamicStateCreateInfo dynamic_state = {};
    dynamic_state.sType = VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO;
    dynamic_state.dynamicStateCount = dynamic_states.Size;
    dynamic_state.pDynamicStates = dynamic_states.Data;

    VkGraphicsPipelineCreateInfo create_info = {};
    create_info.sType = VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO;
    create_info.flags = bd->PipelineCreateFlags;
    create_info.stageCount = 2;
    create_info.pStages = stage;
    create_info.pVertexInputState = &vertex_info;
    create_info.pInputAssemblyState = &ia_info;
    create_info.pViewportState = &viewport_info;
    create_info.pRasterizationState = &raster_info;
    create_info.pMultisampleState = &ms_info;
    create_info.pDepthStencilState = &depth_info;
    create_info.pColorBlendState = &blend_info;
    create_info.pDynamicState = &dynamic_state;
    create_info.layout = bd->PipelineLayout;
    create_info.renderPass = info->RenderPass;
    create_info.subpass = info->Subpass;

#ifdef IMGUI_IMPL_VULKAN_HAS_DYNAMIC_RENDERING
    if (bd->VulkanInitInfo.UseDynamicRendering)
    {
        IM_ASSERT(info->PipelineRenderingCreateInfo.sType == VK_STRUCTURE_TYPE_PIPELINE_RENDERING_CREATE_INFO_KHR && "PipelineRenderingCreateInfo::sType must be VK_STRUCTURE_TYPE_PIPELINE_RENDERING_CREATE_INFO_KHR");
        IM_ASSERT(info->PipelineRenderingCreateInfo.pNext == nullptr && "PipelineRenderingCreateInfo::pNext must be nullptr");
        create_info.pNext = &info->PipelineRenderingCreateInfo;
        create_info.renderPass = VK_NULL_HANDLE; // Just make sure it's actually nullptr.
    }
#endif
    VkPipeline pipeline = VK_NULL_HANDLE;
    VkPipeline created_pipeline = VK_NULL_HANDLE;
    VkResult err = vkCreateGraphicsPipelines(device, pipelineCache, 1, &create_info, allocator, &created_pipeline);
    if (err == VK_SUCCESS)
        pipeline = created_pipeline;
    check_vk_result(err);
    return pipeline;
}

static void ImGui_ImplVulkan_CreateDescriptorSetLayout(VkDescriptorSetLayout* p_layout, VkDescriptorType descriptor_type)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;

    VkDescriptorSetLayoutBinding binding[1] = {};
    binding[0].descriptorType = descriptor_type;
    binding[0].descriptorCount = 1;
    binding[0].stageFlags = VK_SHADER_STAGE_FRAGMENT_BIT;
    VkDescriptorSetLayoutCreateInfo info = {};
    info.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
    info.bindingCount = 1;
    info.pBindings = binding;
    VkDescriptorSetLayout layout = VK_NULL_HANDLE;
    VkResult err = vkCreateDescriptorSetLayout(v->Device, &info, v->Allocator, &layout);
    if (err == VK_SUCCESS)
        *p_layout = layout;
    check_vk_result(err);
}

// Allocate and write one sampler descriptor set. *out_owned (and the registration count) is committed only after VK_SUCCESS.
static void ImGui_ImplVulkan_CreateSamplerDS(VkSampler sampler, VkDescriptorSet* out_owned)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    if (bd->SamplerRegistrations >= IMGUI_IMPL_VULKAN_MAX_SAMPLER_REGISTRATIONS)
        ImGui_ImplVulkan_Fail(VK_ERROR_TOO_MANY_OBJECTS, "Sampler descriptor registrations exceed admission");

    VkDescriptorSetAllocateInfo alloc_info = {};
    alloc_info.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
    alloc_info.descriptorPool = bd->DescriptorPool ? bd->DescriptorPool : v->DescriptorPool;
    alloc_info.descriptorSetCount = 1;
    alloc_info.pSetLayouts = &bd->DescriptorSetLayoutSampler;
    VkDescriptorSet descriptor_set = VK_NULL_HANDLE;
    VkResult err = vkAllocateDescriptorSets(v->Device, &alloc_info, &descriptor_set);
    if (err == VK_SUCCESS && descriptor_set != VK_NULL_HANDLE)
    {
        *out_owned = descriptor_set;
        bd->SamplerRegistrations++;
    }
    check_vk_result(err);
    if (*out_owned == VK_NULL_HANDLE)
        ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "Sampler descriptor allocation returned no identity");

    VkDescriptorImageInfo desc_image = {};
    desc_image.sampler = sampler;
    VkWriteDescriptorSet sampler_write_desc = {};
    sampler_write_desc.sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
    sampler_write_desc.dstSet = *out_owned;
    sampler_write_desc.descriptorCount = 1;
    sampler_write_desc.dstBinding = 0;
    sampler_write_desc.descriptorType = VK_DESCRIPTOR_TYPE_SAMPLER;
    sampler_write_desc.pImageInfo = &desc_image;
    vkUpdateDescriptorSets(v->Device, 1, &sampler_write_desc, 0, nullptr);
}

// Every created/allocated Vulkan output starts null and is committed to its owned backend field only after VK_SUCCESS, before the result
// callback. Already-owned (non-null) fields are kept. On throw, exactly the committed fields are owned (see ImGui_ImplVulkan_DestroyCoreObjects()).
bool ImGui_ImplVulkan_CreateDeviceObjects()
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    VkResult err;

    if (!bd->DescriptorSetLayoutTexture)
        ImGui_ImplVulkan_CreateDescriptorSetLayout(&bd->DescriptorSetLayoutTexture, VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE);
    if (!bd->DescriptorSetLayoutSampler)
        ImGui_ImplVulkan_CreateDescriptorSetLayout(&bd->DescriptorSetLayoutSampler, VK_DESCRIPTOR_TYPE_SAMPLER);

    if (v->DescriptorPoolSize != 0 && bd->DescriptorPool == VK_NULL_HANDLE)
    {
        if (v->DescriptorPoolSize < IMGUI_IMPL_VULKAN_MINIMUM_SAMPLED_IMAGE_POOL_SIZE || v->DescriptorPoolSize > UINT32_MAX - IMGUI_IMPL_VULKAN_MINIMUM_SAMPLER_POOL_SIZE)
            ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "Invalid DescriptorPoolSize");
        VkDescriptorPoolSize pool_sizes[] =
        {
            { VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE, v->DescriptorPoolSize },
            { VK_DESCRIPTOR_TYPE_SAMPLER, IMGUI_IMPL_VULKAN_MINIMUM_SAMPLER_POOL_SIZE },
        };
        VkDescriptorPoolCreateInfo pool_info = {};
        pool_info.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
        pool_info.flags = VK_DESCRIPTOR_POOL_CREATE_FREE_DESCRIPTOR_SET_BIT;
        pool_info.maxSets = v->DescriptorPoolSize + IMGUI_IMPL_VULKAN_MINIMUM_SAMPLER_POOL_SIZE;
        pool_info.poolSizeCount = (uint32_t)IM_COUNTOF(pool_sizes);
        pool_info.pPoolSizes = pool_sizes;
        VkDescriptorPool descriptor_pool = VK_NULL_HANDLE;
        err = vkCreateDescriptorPool(v->Device, &pool_info, v->Allocator, &descriptor_pool);
        if (err == VK_SUCCESS)
            bd->DescriptorPool = descriptor_pool;
        check_vk_result(err);
    }

    // Create samplers (bilinear sampling is required) and their two descriptor registrations
    {
        VkSamplerCreateInfo info = {};
        info.sType = VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO;
        info.magFilter = VK_FILTER_LINEAR;
        info.minFilter = VK_FILTER_LINEAR;
        info.mipmapMode = VK_SAMPLER_MIPMAP_MODE_LINEAR;
        info.addressModeU = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
        info.addressModeV = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
        info.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
        info.minLod = -1000;
        info.maxLod = 1000;
        info.maxAnisotropy = 1.0f;
        if (!bd->SamplerLinear)
        {
            VkSampler sampler = VK_NULL_HANDLE;
            err = vkCreateSampler(v->Device, &info, v->Allocator, &sampler);
            if (err == VK_SUCCESS)
                bd->SamplerLinear = sampler;
            check_vk_result(err);
        }
        if (!bd->SamplerLinearDS)
            ImGui_ImplVulkan_CreateSamplerDS(bd->SamplerLinear, &bd->SamplerLinearDS);

        info.magFilter = VK_FILTER_NEAREST;
        info.minFilter = VK_FILTER_NEAREST;
        info.mipmapMode = VK_SAMPLER_MIPMAP_MODE_NEAREST;
        if (!bd->SamplerNearest)
        {
            VkSampler sampler = VK_NULL_HANDLE;
            err = vkCreateSampler(v->Device, &info, v->Allocator, &sampler);
            if (err == VK_SUCCESS)
                bd->SamplerNearest = sampler;
            check_vk_result(err);
        }
        if (!bd->SamplerNearestDS)
            ImGui_ImplVulkan_CreateSamplerDS(bd->SamplerNearest, &bd->SamplerNearestDS);
    }

    if (!bd->PipelineLayout)
    {
        // Constants: we are using 'vec2 offset' and 'vec2 scale' instead of a full 3d projection matrix
        VkPushConstantRange push_constants[1] = {};
        push_constants[0].stageFlags = VK_SHADER_STAGE_VERTEX_BIT;
        push_constants[0].offset = sizeof(float) * 0;
        push_constants[0].size = sizeof(float) * 4;
        VkDescriptorSetLayout set_layout[2] = { bd->DescriptorSetLayoutTexture, bd->DescriptorSetLayoutSampler };
        VkPipelineLayoutCreateInfo layout_info = {};
        layout_info.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
        layout_info.setLayoutCount = 2;
        layout_info.pSetLayouts = set_layout;
        layout_info.pushConstantRangeCount = 1;
        layout_info.pPushConstantRanges = push_constants;
        VkPipelineLayout pipeline_layout = VK_NULL_HANDLE;
        err = vkCreatePipelineLayout(v->Device, &layout_info, v->Allocator, &pipeline_layout);
        if (err == VK_SUCCESS)
            bd->PipelineLayout = pipeline_layout;
        check_vk_result(err);
    }

    // Create pipeline
    bool create_main_pipeline = (v->PipelineInfoMain.RenderPass != VK_NULL_HANDLE);
#ifdef IMGUI_IMPL_VULKAN_HAS_DYNAMIC_RENDERING
    create_main_pipeline |= (v->UseDynamicRendering && v->PipelineInfoMain.PipelineRenderingCreateInfo.sType == VK_STRUCTURE_TYPE_PIPELINE_RENDERING_CREATE_INFO_KHR);
#endif
    if (create_main_pipeline)
        ImGui_ImplVulkan_CreateMainPipeline(&v->PipelineInfoMain);

    // Create command pool/buffer and owned completion fence for texture upload
    if (!bd->TexCommandPool)
    {
        VkCommandPoolCreateInfo info = {};
        info.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
        info.flags = 0;
        info.queueFamilyIndex = v->QueueFamily;
        VkCommandPool command_pool = VK_NULL_HANDLE;
        err = vkCreateCommandPool(v->Device, &info, v->Allocator, &command_pool);
        if (err == VK_SUCCESS)
            bd->TexCommandPool = command_pool;
        check_vk_result(err);
    }
    if (!bd->TexCommandBuffer)
    {
        VkCommandBufferAllocateInfo info = {};
        info.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
        info.commandPool = bd->TexCommandPool;
        info.commandBufferCount = 1;
        VkCommandBuffer command_buffer = VK_NULL_HANDLE;
        err = vkAllocateCommandBuffers(v->Device, &info, &command_buffer);
        if (err == VK_SUCCESS)
            bd->TexCommandBuffer = command_buffer;
        check_vk_result(err);
    }
    if (!bd->UploadFence)
    {
        VkFenceCreateInfo info = {};
        info.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
        info.flags = 0; // Unsignaled
        VkFence fence = VK_NULL_HANDLE;
        err = vkCreateFence(v->Device, &info, v->Allocator, &fence);
        if (err == VK_SUCCESS)
            bd->UploadFence = fence;
        check_vk_result(err);
    }

    return true;
}

// Transactional: the previous pipeline, stored pipeline info and deep-copied formats are only replaced after the new pipeline was created.
void ImGui_ImplVulkan_CreateMainPipeline(const ImGui_ImplVulkan_PipelineInfo* pipeline_info_in)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    ImGui_ImplVulkan_PipelineInfo pipeline_info = *pipeline_info_in; // Local copy (pipeline_info_in may alias v->PipelineInfoMain)
    ImVector<VkFormat> formats;
    bool formats_copied = false;

#ifdef IMGUI_IMPL_VULKAN_HAS_DYNAMIC_RENDERING
    VkPipelineRenderingCreateInfoKHR* pipeline_rendering_create_info = &pipeline_info.PipelineRenderingCreateInfo;
    if (v->UseDynamicRendering && pipeline_rendering_create_info->pColorAttachmentFormats != nullptr)
    {
        // Deep copy buffer to reduce error-rate for end user (#8282)
        if (pipeline_rendering_create_info->colorAttachmentCount > 1024u)
            ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "Invalid colorAttachmentCount");
        formats.resize((int)pipeline_rendering_create_info->colorAttachmentCount);
        if (formats.Size > 0)
            memcpy(formats.Data, pipeline_rendering_create_info->pColorAttachmentFormats, (size_t)formats.size_in_bytes());
        pipeline_rendering_create_info->pColorAttachmentFormats = formats.Data;
        formats_copied = true;
    }
#endif
    VkPipeline pipeline = ImGui_ImplVulkan_CreatePipeline(v->Device, v->Allocator, v->PipelineCache, &pipeline_info);

    // Commit (no failing Vulkan operation below)
    if (bd->Pipeline)
        vkDestroyPipeline(v->Device, bd->Pipeline, v->Allocator);
    bd->Pipeline = pipeline;
    if (formats_copied)
        formats.swap(bd->PipelineRenderingCreateInfoColorAttachmentFormats); // Data pointer referenced by pipeline_info moves with the swap
    v->PipelineInfoMain = pipeline_info;
}

// Destroy backend-owned device objects other than textures, render buffers and upload staging, dependency-first.
// Only committed (non-null) fields are owned. An external descriptor pool is never destroyed, but the sampler descriptor sets the
// backend allocated from it are freed. Never throws.
static void ImGui_ImplVulkan_DestroyCoreObjects()
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    VkDescriptorPool descriptor_pool = bd->DescriptorPool ? bd->DescriptorPool : v->DescriptorPool;
    if (bd->SamplerLinearDS)      { vkFreeDescriptorSets(v->Device, descriptor_pool, 1, &bd->SamplerLinearDS); bd->SamplerLinearDS = VK_NULL_HANDLE; if (bd->SamplerRegistrations > 0) bd->SamplerRegistrations--; }
    if (bd->SamplerNearestDS)     { vkFreeDescriptorSets(v->Device, descriptor_pool, 1, &bd->SamplerNearestDS); bd->SamplerNearestDS = VK_NULL_HANDLE; if (bd->SamplerRegistrations > 0) bd->SamplerRegistrations--; }
    if (bd->TexCommandBuffer)     { vkFreeCommandBuffers(v->Device, bd->TexCommandPool, 1, &bd->TexCommandBuffer); bd->TexCommandBuffer = VK_NULL_HANDLE; }
    if (bd->TexCommandPool)       { vkDestroyCommandPool(v->Device, bd->TexCommandPool, v->Allocator); bd->TexCommandPool = VK_NULL_HANDLE; }
    if (bd->UploadFence)          { vkDestroyFence(v->Device, bd->UploadFence, v->Allocator); bd->UploadFence = VK_NULL_HANDLE; }
    if (bd->Pipeline)             { vkDestroyPipeline(v->Device, bd->Pipeline, v->Allocator); bd->Pipeline = VK_NULL_HANDLE; }
    if (bd->PipelineLayout)       { vkDestroyPipelineLayout(v->Device, bd->PipelineLayout, v->Allocator); bd->PipelineLayout = VK_NULL_HANDLE; }
    if (bd->DescriptorSetLayoutTexture)  { vkDestroyDescriptorSetLayout(v->Device, bd->DescriptorSetLayoutTexture, v->Allocator); bd->DescriptorSetLayoutTexture = VK_NULL_HANDLE; }
    if (bd->DescriptorSetLayoutSampler)  { vkDestroyDescriptorSetLayout(v->Device, bd->DescriptorSetLayoutSampler, v->Allocator); bd->DescriptorSetLayoutSampler = VK_NULL_HANDLE; }
    if (bd->SamplerLinear)        { vkDestroySampler(v->Device, bd->SamplerLinear, v->Allocator); bd->SamplerLinear = VK_NULL_HANDLE; }
    if (bd->SamplerNearest)       { vkDestroySampler(v->Device, bd->SamplerNearest, v->Allocator); bd->SamplerNearest = VK_NULL_HANDLE; }
    if (bd->ShaderModuleVert)     { vkDestroyShaderModule(v->Device, bd->ShaderModuleVert, v->Allocator); bd->ShaderModuleVert = VK_NULL_HANDLE; }
    if (bd->ShaderModuleFrag)     { vkDestroyShaderModule(v->Device, bd->ShaderModuleFrag, v->Allocator); bd->ShaderModuleFrag = VK_NULL_HANDLE; }
    if (bd->DescriptorPool)       { vkDestroyDescriptorPool(v->Device, bd->DescriptorPool, v->Allocator); bd->DescriptorPool = VK_NULL_HANDLE; }
}

void    ImGui_ImplVulkan_DestroyDeviceObjects()
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;

    // Resolve the upload owner first: nothing it references may be reset or freed while its completion is unknown.
    ImGui_ImplVulkan_ResolvePendingUpload();
    ImGui_ImplVulkan_DestroyWindowRenderBuffers(v->Device, &bd->MainWindowRenderBuffers, v->Allocator);

    // Destroy all textures
    for (ImTextureData* tex : ImGui::GetPlatformIO().Textures)
        if (tex->RefCount == 1)
            ImGui_ImplVulkan_DestroyTexture(tex);

    ImGui_ImplVulkan_DestroyCoreObjects();
}

#ifdef IMGUI_IMPL_VULKAN_HAS_DYNAMIC_RENDERING
static void ImGui_ImplVulkan_LoadDynamicRenderingFunctions(uint32_t api_version, PFN_vkVoidFunction(*loader_func)(const char* function_name, void* user_data), void* user_data)
{
    IM_UNUSED(api_version);

    // Manually load those two (see #5446, #8326, #8365, #8600)
    // - Try loading core (non-KHR) versions first (this will work for Vulkan 1.3+ and the device supports dynamic rendering)
    ImGuiImplVulkanFuncs_vkCmdBeginRenderingKHR = reinterpret_cast<PFN_vkCmdBeginRenderingKHR>(loader_func("vkCmdBeginRendering", user_data));
    ImGuiImplVulkanFuncs_vkCmdEndRenderingKHR = reinterpret_cast<PFN_vkCmdEndRenderingKHR>(loader_func("vkCmdEndRendering", user_data));

    // - Fallback to KHR versions if core not available (this will work if KHR extension is available and enabled and also the device supports dynamic rendering)
    if (ImGuiImplVulkanFuncs_vkCmdBeginRenderingKHR == nullptr || ImGuiImplVulkanFuncs_vkCmdEndRenderingKHR == nullptr)
    {
        ImGuiImplVulkanFuncs_vkCmdBeginRenderingKHR = reinterpret_cast<PFN_vkCmdBeginRenderingKHR>(loader_func("vkCmdBeginRenderingKHR", user_data));
        ImGuiImplVulkanFuncs_vkCmdEndRenderingKHR = reinterpret_cast<PFN_vkCmdEndRenderingKHR>(loader_func("vkCmdEndRenderingKHR", user_data));
    }
}
#endif

// If unspecified by user, assume that ApiVersion == HeaderVersion
 // We don't care about other versions than 1.3 for our checks, so don't need to make this exhaustive (e.g. with all #ifdef VK_VERSION_1_X checks)
static uint32_t ImGui_ImplVulkan_GetDefaultApiVersion()
{
#ifdef VK_HEADER_VERSION_COMPLETE
    return VK_HEADER_VERSION_COMPLETE;
#else
    return VK_API_VERSION_1_0;
#endif
}

bool    ImGui_ImplVulkan_LoadFunctions(uint32_t api_version, PFN_vkVoidFunction(*loader_func)(const char* function_name, void* user_data), void* user_data)
{
    // Load function pointers
    // You can use the default Vulkan loader using:
    //      ImGui_ImplVulkan_LoadFunctions(VK_API_VERSION_1_3, [](const char* function_name, void*) { return vkGetInstanceProcAddr(your_vk_isntance, function_name); });
    // But this would be roughly equivalent to not setting VK_NO_PROTOTYPES.
    if (api_version == 0)
        api_version = ImGui_ImplVulkan_GetDefaultApiVersion();

#ifdef IMGUI_IMPL_VULKAN_USE_LOADER
#define IMGUI_VULKAN_FUNC_LOAD(func) \
    ImGuiImplVulkanFuncs.pfn_##func = reinterpret_cast<PFN_##func>(loader_func(#func, user_data)); \
    if (ImGuiImplVulkanFuncs.pfn_##func == nullptr)   \
        return false;
    IMGUI_VULKAN_FUNC_MAP(IMGUI_VULKAN_FUNC_LOAD)
#undef IMGUI_VULKAN_FUNC_LOAD

#ifdef IMGUI_IMPL_VULKAN_HAS_DYNAMIC_RENDERING
    ImGui_ImplVulkan_LoadDynamicRenderingFunctions(api_version, loader_func, user_data);
#endif
#else
    IM_UNUSED(loader_func);
    IM_UNUSED(user_data);
#endif

    g_FunctionsLoaded = true;
    return true;
}

bool    ImGui_ImplVulkan_Init(ImGui_ImplVulkan_InitInfo* info)
{
    IM_ASSERT(g_FunctionsLoaded && "Need to call ImGui_ImplVulkan_LoadFunctions() if IMGUI_IMPL_VULKAN_NO_PROTOTYPES or VK_NO_PROTOTYPES are set!");
    IM_ASSERT(info != nullptr);
    if (info == nullptr)
        return false;

    // Rejections below happen before any publication (no side effects).
    if ((info->AllocateDeviceMemoryFn == nullptr) != (info->FreeDeviceMemoryFn == nullptr))
        return false; // Mismatched device memory hook pair
    if (info->AllocateDeviceMemoryFn != nullptr && info->CheckVkResultFn == nullptr)
        return false; // Routed (ledger) mode requires a throwing CheckVkResultFn
    if (info->ImageCount > IMGUI_IMPL_VULKAN_MAX_IMAGE_COUNT)
        return false;
    if (info->DescriptorPoolSize > UINT32_MAX - IMGUI_IMPL_VULKAN_MINIMUM_SAMPLER_POOL_SIZE)
        return false;

    if (info->ApiVersion == 0)
        info->ApiVersion = ImGui_ImplVulkan_GetDefaultApiVersion();

    if (info->UseDynamicRendering)
    {
#ifdef IMGUI_IMPL_VULKAN_HAS_DYNAMIC_RENDERING
#ifndef IMGUI_IMPL_VULKAN_USE_LOADER
        ImGui_ImplVulkan_LoadDynamicRenderingFunctions(info->ApiVersion, [](const char* function_name, void* user_data) { return vkGetDeviceProcAddr((VkDevice)user_data, function_name); }, (void*)info->Device);
#endif
        IM_ASSERT(ImGuiImplVulkanFuncs_vkCmdBeginRenderingKHR != nullptr);
        IM_ASSERT(ImGuiImplVulkanFuncs_vkCmdEndRenderingKHR != nullptr);
#else
        IM_ASSERT(0 && "Can't use dynamic rendering when neither VK_VERSION_1_3 or VK_KHR_dynamic_rendering is defined.");
#endif
    }

    ImGuiIO& io = ImGui::GetIO();
    IMGUI_CHECKVERSION();
    IM_ASSERT(io.BackendRendererUserData == nullptr && "Already initialized a renderer backend!");

    // Sanity checks
    IM_ASSERT(info->Instance != VK_NULL_HANDLE);
    IM_ASSERT(info->PhysicalDevice != VK_NULL_HANDLE);
    IM_ASSERT(info->Device != VK_NULL_HANDLE);
    IM_ASSERT(info->Queue != VK_NULL_HANDLE);
    IM_ASSERT(info->MinImageCount >= 2);
    IM_ASSERT(info->ImageCount >= info->MinImageCount);
    if (info->DescriptorPool != VK_NULL_HANDLE) // Either DescriptorPool or DescriptorPoolSize must be set, not both!
        IM_ASSERT(info->DescriptorPoolSize == 0);
    else
        IM_ASSERT(info->DescriptorPoolSize > 0);
    if (info->UseDynamicRendering)
        IM_ASSERT(info->PipelineInfoMain.RenderPass == VK_NULL_HANDLE);
    if (io.BackendRendererUserData != nullptr || info->Instance == VK_NULL_HANDLE || info->PhysicalDevice == VK_NULL_HANDLE || info->Device == VK_NULL_HANDLE || info->Queue == VK_NULL_HANDLE ||
        info->MinImageCount < 2 || info->ImageCount < info->MinImageCount ||
        (info->DescriptorPool != VK_NULL_HANDLE) == (info->DescriptorPoolSize != 0) ||
        (info->DescriptorPoolSize != 0 && info->DescriptorPoolSize < IMGUI_IMPL_VULKAN_MINIMUM_SAMPLED_IMAGE_POOL_SIZE) ||
        (info->UseDynamicRendering && info->PipelineInfoMain.RenderPass != VK_NULL_HANDLE))
        return false;

    // Remember exactly what this initialization publishes, so a failure can undo only that.
    ImGuiPlatformIO& platform_io = ImGui::GetPlatformIO();
    const ImGuiBackendFlags backend_flags_mask = ImGuiBackendFlags_RendererHasVtxOffset | ImGuiBackendFlags_RendererHasTextures;
    const char* const prev_renderer_name = io.BackendRendererName;
    const ImGuiBackendFlags prev_backend_flags = io.BackendFlags;
    const decltype(platform_io.DrawCallback_ResetRenderState) prev_reset_render_state = platform_io.DrawCallback_ResetRenderState;
    const decltype(platform_io.DrawCallback_SetSamplerLinear) prev_set_sampler_linear = platform_io.DrawCallback_SetSamplerLinear;
    const decltype(platform_io.DrawCallback_SetSamplerNearest) prev_set_sampler_nearest = platform_io.DrawCallback_SetSamplerNearest;

    // Setup backend data (per-context PFN table copied before any Vulkan call made on behalf of this backend)
    ImGui_ImplVulkan_Data* bd = IM_NEW(ImGui_ImplVulkan_Data)();
    bd->VulkanInitInfo = *info;
#ifdef IMGUI_IMPL_VULKAN_USE_LOADER
    bd->Functions = ImGuiImplVulkanFuncs;
#endif

    // Setup backend capabilities flags
    io.BackendRendererUserData = (void*)bd;
    io.BackendRendererName = "imgui_impl_vulkan";
    io.BackendFlags |= ImGuiBackendFlags_RendererHasVtxOffset;  // We can honor the ImDrawCmd::VtxOffset field, allowing for large meshes.
    io.BackendFlags |= ImGuiBackendFlags_RendererHasTextures;   // We can honor ImGuiPlatformIO::Textures[] requests during render.

    platform_io.DrawCallback_ResetRenderState = ImGui_ImplVulkan_DrawCallback_ResetRenderState;
    platform_io.DrawCallback_SetSamplerLinear = ImGui_ImplVulkan_DrawCallback_SetSamplerLinear;
    platform_io.DrawCallback_SetSamplerNearest = ImGui_ImplVulkan_DrawCallback_SetSamplerNearest;

    try
    {
        VkPhysicalDeviceProperties properties;
        vkGetPhysicalDeviceProperties(info->PhysicalDevice, &properties);
        const VkDeviceSize atom = properties.limits.nonCoherentAtomSize;
        if (atom == 0 || (atom & (atom - 1)) != 0)
            ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "Invalid nonCoherentAtomSize");
        bd->NonCoherentAtomSize = atom;
        bd->MaxImageDimension2D = properties.limits.maxImageDimension2D;

        if (!ImGui_ImplVulkan_CreateDeviceObjects())
            ImGui_ImplVulkan_Fail(VK_ERROR_INITIALIZATION_FAILED, "ImGui_ImplVulkan_CreateDeviceObjects() failed");
    }
    catch (...)
    {
        // Reclaim exactly the success-committed children (dependency-first) while this backend's PFN table is still current,
        // then undo only this initialization's publication and free the CPU backend state. Caller context is preserved.
        ImGui_ImplVulkan_DestroyCoreObjects();
        io.BackendRendererUserData = nullptr;
        io.BackendRendererName = prev_renderer_name;
        io.BackendFlags = (io.BackendFlags & ~backend_flags_mask) | (prev_backend_flags & backend_flags_mask);
        platform_io.DrawCallback_ResetRenderState = prev_reset_render_state;
        platform_io.DrawCallback_SetSamplerLinear = prev_set_sampler_linear;
        platform_io.DrawCallback_SetSamplerNearest = prev_set_sampler_nearest;
        IM_DELETE(bd);
        throw;
    }

    return true;
}

void ImGui_ImplVulkan_Shutdown()
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    IM_ASSERT(bd != nullptr && "No renderer backend to shutdown, or already shutdown?");
    ImGuiIO& io = ImGui::GetIO();
    ImGuiPlatformIO& platform_io = ImGui::GetPlatformIO();

    ImGui_ImplVulkan_DestroyDeviceObjects();

    io.BackendRendererName = nullptr;
    io.BackendRendererUserData = nullptr;
    io.BackendFlags &= ~(ImGuiBackendFlags_RendererHasVtxOffset | ImGuiBackendFlags_RendererHasTextures);
    platform_io.ClearRendererHandlers();
    IM_DELETE(bd);
}

void ImGui_ImplVulkan_NewFrame()
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    IM_ASSERT(bd != nullptr && "Context or backend not initialized! Did you call ImGui_ImplVulkan_Init()?");
    IM_UNUSED(bd);
    if (bd != nullptr && bd->TerminalResult != VK_SUCCESS)
        ImGui_ImplVulkan_Fail(bd->TerminalResult, "Frame blocked after terminal device loss");
}

void ImGui_ImplVulkan_SetMinImageCount(uint32_t min_image_count)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    IM_ASSERT(min_image_count >= 2);
    if (bd->VulkanInitInfo.MinImageCount == min_image_count)
        return;

    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    VkResult err = vkDeviceWaitIdle(v->Device);
    check_vk_result(err);
    ImGui_ImplVulkan_DestroyWindowRenderBuffers(v->Device, &bd->MainWindowRenderBuffers, v->Allocator);
    bd->VulkanInitInfo.MinImageCount = min_image_count;
}

// Register a texture by creating a descriptor
// FIXME: This is experimental in the sense that we are unsure how to best design/tackle this problem, please post to https://github.com/ocornut/imgui/pull/914 if you have suggestions.
VkDescriptorSet ImGui_ImplVulkan_AddTexture(VkImageView image_view, VkImageLayout image_layout)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    VkDescriptorPool pool = bd->DescriptorPool ? bd->DescriptorPool : v->DescriptorPool;

    // Admission: at most IMGUI_IMPL_VULKAN_MAX_SAMPLED_IMAGE_REGISTRATIONS live successful registrations (checked before allocation)
    if (bd->SampledImageRegistrations >= IMGUI_IMPL_VULKAN_MAX_SAMPLED_IMAGE_REGISTRATIONS)
        ImGui_ImplVulkan_Fail(VK_ERROR_TOO_MANY_OBJECTS, "Sampled image descriptor registrations exceed admission");

    // Create Descriptor Set (a failed allocation output is never acquired, returned or counted):
    VkDescriptorSet descriptor_set = VK_NULL_HANDLE;
    {
        VkDescriptorSetAllocateInfo alloc_info = {};
        alloc_info.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
        alloc_info.descriptorPool = pool;
        alloc_info.descriptorSetCount = 1;
        alloc_info.pSetLayouts = &bd->DescriptorSetLayoutTexture;
        VkDescriptorSet allocated_set = VK_NULL_HANDLE;
        VkResult err = vkAllocateDescriptorSets(v->Device, &alloc_info, &allocated_set);
        if (err == VK_SUCCESS && allocated_set != VK_NULL_HANDLE)
        {
            descriptor_set = allocated_set;
            bd->SampledImageRegistrations++;
        }
        check_vk_result(err);
    }

    // Update the Descriptor Set:
    if (descriptor_set != VK_NULL_HANDLE)
    {
        VkDescriptorImageInfo desc_image[1] = {};
        desc_image[0].imageView = image_view;
        desc_image[0].imageLayout = image_layout;
        VkWriteDescriptorSet write_desc[1] = {};
        write_desc[0].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
        write_desc[0].dstSet = descriptor_set;
        write_desc[0].descriptorCount = 1;
        write_desc[0].descriptorType = VK_DESCRIPTOR_TYPE_SAMPLED_IMAGE;
        write_desc[0].pImageInfo = desc_image;
        vkUpdateDescriptorSets(v->Device, 1, write_desc, 0, nullptr);
    }
    return descriptor_set;
}

#ifndef IMGUI_DISABLE_OBSOLETE_FUNCTIONS
VkDescriptorSet ImGui_ImplVulkan_AddTexture(VkSampler sampler, VkImageView image_view, VkImageLayout image_layout)
{
    IM_UNUSED(sampler);
    return ImGui_ImplVulkan_AddTexture(image_view, image_layout);
}
#endif

void ImGui_ImplVulkan_RemoveTexture(VkDescriptorSet descriptor_set)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    ImGui_ImplVulkan_InitInfo* v = &bd->VulkanInitInfo;
    if (descriptor_set == VK_NULL_HANDLE)
        return;
    VkDescriptorPool pool = bd->DescriptorPool ? bd->DescriptorPool : v->DescriptorPool;
    vkFreeDescriptorSets(v->Device, pool, 1, &descriptor_set);
    if (bd->SampledImageRegistrations > 0)
        bd->SampledImageRegistrations--;
}

VkResult ImGui_ImplVulkan_GetTerminalResult()
{
    // Reads ONLY the current ImGui context's live backend. VK_RESULT_MAX_ENUM = unavailable (no current backend), NOT success.
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    return bd ? bd->TerminalResult : VK_RESULT_MAX_ENUM;
}

void ImGui_ImplVulkan_GetLastUploadResults(VkResult* out_submit_result, VkResult* out_wait_result)
{
    ImGui_ImplVulkan_Data* bd = ImGui_ImplVulkan_GetBackendData();
    if (out_submit_result != nullptr)
        *out_submit_result = bd ? bd->LastUploadSubmitResult : VK_RESULT_MAX_ENUM;
    if (out_wait_result != nullptr)
        *out_wait_result = bd ? bd->LastUploadWaitResult : VK_RESULT_MAX_ENUM;
}

void ImGui_ImplVulkan_DestroyFrameRenderBuffers(VkDevice device, ImGui_ImplVulkan_FrameRenderBuffers* buffers, const VkAllocationCallbacks* allocator)
{
    if (buffers->VertexBuffer) { vkDestroyBuffer(device, buffers->VertexBuffer, allocator); buffers->VertexBuffer = VK_NULL_HANDLE; }
    if (buffers->VertexBufferMemory) { ImGui_ImplVulkan_FreeDeviceMemory(buffers->VertexBufferMemory); buffers->VertexBufferMemory = VK_NULL_HANDLE; }
    if (buffers->IndexBuffer) { vkDestroyBuffer(device, buffers->IndexBuffer, allocator); buffers->IndexBuffer = VK_NULL_HANDLE; }
    if (buffers->IndexBufferMemory) { ImGui_ImplVulkan_FreeDeviceMemory(buffers->IndexBufferMemory); buffers->IndexBufferMemory = VK_NULL_HANDLE; }
    buffers->VertexBufferSize = 0;
    buffers->IndexBufferSize = 0;
}

void ImGui_ImplVulkan_DestroyWindowRenderBuffers(VkDevice device, ImGui_ImplVulkan_WindowRenderBuffers* buffers, const VkAllocationCallbacks* allocator)
{
    for (uint32_t n = 0; n < buffers->Count; n++)
        ImGui_ImplVulkan_DestroyFrameRenderBuffers(device, &buffers->FrameRenderBuffers[n], allocator);
    buffers->FrameRenderBuffers.clear();
    buffers->Index = 0;
    buffers->Count = 0;
}

//-------------------------------------------------------------------------
// Internal / Miscellaneous Vulkan Helpers
// (Used by example's main.cpp. Used by multi-viewport features. PROBABLY NOT used by your own engine/app.)
//-------------------------------------------------------------------------
// You probably do NOT need to use or care about those functions.
// Those functions only exist because:
//   1) they facilitate the readability and maintenance of the multiple main.cpp examples files.
//   2) the upcoming multi-viewport feature will need them internally.
// Generally we avoid exposing any kind of superfluous high-level helpers in the backends,
// but it is too much code to duplicate everywhere so we exceptionally expose them.
//
// Your engine/app will likely _already_ have code to setup all that stuff (swap chain, render pass, frame buffers, etc.).
// You may read this code to learn about Vulkan, but it is recommended you use your own custom tailored code to do equivalent work.
// (The ImGui_ImplVulkanH_XXX functions do not interact with any of the state used by the regular ImGui_ImplVulkan_XXX functions)
//-------------------------------------------------------------------------

VkSurfaceFormatKHR ImGui_ImplVulkanH_SelectSurfaceFormat(VkPhysicalDevice physical_device, VkSurfaceKHR surface, const VkFormat* request_formats, int request_formats_count, VkColorSpaceKHR request_color_space)
{
    IM_ASSERT(g_FunctionsLoaded && "Need to call ImGui_ImplVulkan_LoadFunctions() if IMGUI_IMPL_VULKAN_NO_PROTOTYPES or VK_NO_PROTOTYPES are set!");
    IM_ASSERT(request_formats != nullptr);
    IM_ASSERT(request_formats_count > 0);

    // Per Spec Format and View Format are expected to be the same unless VK_IMAGE_CREATE_MUTABLE_BIT was set at image creation
    // Assuming that the default behavior is without setting this bit, there is no need for separate Swapchain image and image view format
    // Additionally several new color spaces were introduced with Vulkan Spec v1.0.40,
    // hence we must make sure that a format with the mostly available color space, VK_COLOR_SPACE_SRGB_NONLINEAR_KHR, is found and used.
    uint32_t avail_count;
    vkGetPhysicalDeviceSurfaceFormatsKHR(physical_device, surface, &avail_count, nullptr);
    ImVector<VkSurfaceFormatKHR> avail_format;
    avail_format.resize((int)avail_count);
    vkGetPhysicalDeviceSurfaceFormatsKHR(physical_device, surface, &avail_count, avail_format.Data);

    // First check if only one format, VK_FORMAT_UNDEFINED, is available, which would imply that any format is available
    if (avail_count == 1)
    {
        if (avail_format[0].format == VK_FORMAT_UNDEFINED)
        {
            VkSurfaceFormatKHR ret;
            ret.format = request_formats[0];
            ret.colorSpace = request_color_space;
            return ret;
        }
        else
        {
            // No point in searching another format
            return avail_format[0];
        }
    }
    else
    {
        // Request several formats, the first found will be used
        for (int request_i = 0; request_i < request_formats_count; request_i++)
            for (uint32_t avail_i = 0; avail_i < avail_count; avail_i++)
                if (avail_format[avail_i].format == request_formats[request_i] && avail_format[avail_i].colorSpace == request_color_space)
                    return avail_format[avail_i];

        // If none of the requested image formats could be found, use the first available
        return avail_format[0];
    }
}

VkPresentModeKHR ImGui_ImplVulkanH_SelectPresentMode(VkPhysicalDevice physical_device, VkSurfaceKHR surface, const VkPresentModeKHR* request_modes, int request_modes_count)
{
    IM_ASSERT(g_FunctionsLoaded && "Need to call ImGui_ImplVulkan_LoadFunctions() if IMGUI_IMPL_VULKAN_NO_PROTOTYPES or VK_NO_PROTOTYPES are set!");
    IM_ASSERT(request_modes != nullptr);
    IM_ASSERT(request_modes_count > 0);

    // Request a certain mode and confirm that it is available. If not use VK_PRESENT_MODE_FIFO_KHR which is mandatory
    uint32_t avail_count = 0;
    vkGetPhysicalDeviceSurfacePresentModesKHR(physical_device, surface, &avail_count, nullptr);
    ImVector<VkPresentModeKHR> avail_modes;
    avail_modes.resize((int)avail_count);
    vkGetPhysicalDeviceSurfacePresentModesKHR(physical_device, surface, &avail_count, avail_modes.Data);
    //for (uint32_t avail_i = 0; avail_i < avail_count; avail_i++)
    //    printf("[vulkan] avail_modes[%d] = %d\n", avail_i, avail_modes[avail_i]);

    for (int request_i = 0; request_i < request_modes_count; request_i++)
        for (uint32_t avail_i = 0; avail_i < avail_count; avail_i++)
            if (request_modes[request_i] == avail_modes[avail_i])
                return request_modes[request_i];

    return VK_PRESENT_MODE_FIFO_KHR; // Always available
}

VkPhysicalDevice ImGui_ImplVulkanH_SelectPhysicalDevice(VkInstance instance)
{
    uint32_t gpu_count;
    VkResult err = vkEnumeratePhysicalDevices(instance, &gpu_count, nullptr);
    check_vk_result(err);
    IM_ASSERT(gpu_count > 0);

    ImVector<VkPhysicalDevice> gpus;
    gpus.resize(gpu_count);
    err = vkEnumeratePhysicalDevices(instance, &gpu_count, gpus.Data);
    check_vk_result(err);

    // If a number >1 of GPUs got reported, find discrete GPU if present, or use first one available. This covers
    // most common cases (multi-gpu/integrated+dedicated graphics). Handling more complicated setups (multiple
    // dedicated GPUs) is out of scope of this sample.
    for (VkPhysicalDevice& device : gpus)
    {
        VkPhysicalDeviceProperties properties;
        vkGetPhysicalDeviceProperties(device, &properties);
        if (properties.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU)
            return device;
    }

    // Use first GPU (Integrated) is a Discrete one is not available.
    if (gpu_count > 0)
        return gpus[0];
    return VK_NULL_HANDLE;
}


uint32_t ImGui_ImplVulkanH_SelectQueueFamilyIndex(VkPhysicalDevice physical_device)
{
    uint32_t count;
    vkGetPhysicalDeviceQueueFamilyProperties(physical_device, &count, nullptr);
    ImVector<VkQueueFamilyProperties> queues_properties;
    queues_properties.resize((int)count);
    vkGetPhysicalDeviceQueueFamilyProperties(physical_device, &count, queues_properties.Data);
    for (uint32_t i = 0; i < count; i++)
        if (queues_properties[i].queueFlags & VK_QUEUE_GRAPHICS_BIT)
            return i;
    return (uint32_t)-1;
}

void ImGui_ImplVulkanH_CreateWindowCommandBuffers(VkPhysicalDevice physical_device, VkDevice device, ImGui_ImplVulkanH_Window* wd, uint32_t queue_family, const VkAllocationCallbacks* allocator)
{
    IM_ASSERT(physical_device != VK_NULL_HANDLE && device != VK_NULL_HANDLE);
    IM_UNUSED(physical_device);

    // Create Command Buffers
    VkResult err;
    for (uint32_t i = 0; i < wd->ImageCount; i++)
    {
        ImGui_ImplVulkanH_Frame* fd = &wd->Frames[i];
        {
            VkCommandPoolCreateInfo info = {};
            info.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
            info.flags = 0;
            info.queueFamilyIndex = queue_family;
            err = vkCreateCommandPool(device, &info, allocator, &fd->CommandPool);
            check_vk_result(err);
        }
        {
            VkCommandBufferAllocateInfo info = {};
            info.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
            info.commandPool = fd->CommandPool;
            info.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
            info.commandBufferCount = 1;
            err = vkAllocateCommandBuffers(device, &info, &fd->CommandBuffer);
            check_vk_result(err);
        }
        {
            VkFenceCreateInfo info = {};
            info.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
            info.flags = VK_FENCE_CREATE_SIGNALED_BIT;
            err = vkCreateFence(device, &info, allocator, &fd->Fence);
            check_vk_result(err);
        }
    }

    for (uint32_t i = 0; i < wd->SemaphoreCount; i++)
    {
        ImGui_ImplVulkanH_FrameSemaphores* fsd = &wd->FrameSemaphores[i];
        {
            VkSemaphoreCreateInfo info = {};
            info.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;
            err = vkCreateSemaphore(device, &info, allocator, &fsd->ImageAcquiredSemaphore);
            check_vk_result(err);
            err = vkCreateSemaphore(device, &info, allocator, &fsd->RenderCompleteSemaphore);
            check_vk_result(err);
        }
    }
}

int ImGui_ImplVulkanH_GetMinImageCountFromPresentMode(VkPresentModeKHR present_mode)
{
    if (present_mode == VK_PRESENT_MODE_MAILBOX_KHR)
        return 3;
    if (present_mode == VK_PRESENT_MODE_FIFO_KHR || present_mode == VK_PRESENT_MODE_FIFO_RELAXED_KHR)
        return 2;
    if (present_mode == VK_PRESENT_MODE_IMMEDIATE_KHR)
        return 1;
    IM_ASSERT(0);
    return 1;
}

// Also destroy old swap chain and in-flight frames data, if any.
void ImGui_ImplVulkanH_CreateWindowSwapChain(VkPhysicalDevice physical_device, VkDevice device, ImGui_ImplVulkanH_Window* wd, const VkAllocationCallbacks* allocator, int w, int h, uint32_t min_image_count, VkImageUsageFlags image_usage)
{
    VkResult err;
    VkSwapchainKHR old_swapchain = wd->Swapchain;
    wd->Swapchain = VK_NULL_HANDLE;
    err = vkDeviceWaitIdle(device);
    check_vk_result(err);

    // We don't use ImGui_ImplVulkanH_DestroyWindow() because we want to preserve the old swapchain to create the new one.
    // Destroy old Framebuffer
    for (uint32_t i = 0; i < wd->ImageCount; i++)
        ImGui_ImplVulkanH_DestroyFrame(device, &wd->Frames[i], allocator);
    for (uint32_t i = 0; i < wd->SemaphoreCount; i++)
        ImGui_ImplVulkanH_DestroyFrameSemaphores(device, &wd->FrameSemaphores[i], allocator);
    wd->Frames.clear();
    wd->FrameSemaphores.clear();
    wd->ImageCount = 0;
    if (wd->RenderPass)
        vkDestroyRenderPass(device, wd->RenderPass, allocator);
    if (wd->Pipeline)
        vkDestroyPipeline(device, wd->Pipeline, allocator);

    // If min image count was not specified, request different count of images dependent on selected present mode
    if (min_image_count == 0)
        min_image_count = ImGui_ImplVulkanH_GetMinImageCountFromPresentMode(wd->PresentMode);

    // Create Swapchain
    {
        VkSurfaceCapabilitiesKHR cap;
        err = vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physical_device, wd->Surface, &cap);
        check_vk_result(err);

        VkSwapchainCreateInfoKHR info = {};
        info.sType = VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR;
        info.surface = wd->Surface;
        info.minImageCount = min_image_count;
        info.imageFormat = wd->SurfaceFormat.format;
        info.imageColorSpace = wd->SurfaceFormat.colorSpace;
        info.imageArrayLayers = 1;
        info.imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | image_usage;
        info.imageSharingMode = VK_SHARING_MODE_EXCLUSIVE;           // Assume that graphics family == present family
        info.preTransform = (cap.supportedTransforms & VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR) ? VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR : cap.currentTransform;
        if (cap.supportedCompositeAlpha & VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR)
            info.compositeAlpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR;
        else if (cap.supportedCompositeAlpha & VK_COMPOSITE_ALPHA_INHERIT_BIT_KHR)
            info.compositeAlpha = VK_COMPOSITE_ALPHA_INHERIT_BIT_KHR;
        else
            IM_ASSERT(false && "No supported composite alpha mode found!");
        info.presentMode = wd->PresentMode;
        info.clipped = VK_TRUE;
        info.oldSwapchain = old_swapchain;
        if (info.minImageCount < cap.minImageCount)
            info.minImageCount = cap.minImageCount;
        else if (cap.maxImageCount != 0 && info.minImageCount > cap.maxImageCount)
            info.minImageCount = cap.maxImageCount;
        if (cap.currentExtent.width == 0xffffffff)
        {
            info.imageExtent.width = wd->Width = w;
            info.imageExtent.height = wd->Height = h;
        }
        else
        {
            info.imageExtent.width = wd->Width = cap.currentExtent.width;
            info.imageExtent.height = wd->Height = cap.currentExtent.height;
        }
        err = vkCreateSwapchainKHR(device, &info, allocator, &wd->Swapchain);
        check_vk_result(err);
        err = vkGetSwapchainImagesKHR(device, wd->Swapchain, &wd->ImageCount, nullptr);
        check_vk_result(err);
        VkImage backbuffers[16] = {};
        IM_ASSERT(wd->ImageCount >= min_image_count);
        IM_ASSERT(wd->ImageCount < IM_COUNTOF(backbuffers));
        err = vkGetSwapchainImagesKHR(device, wd->Swapchain, &wd->ImageCount, backbuffers);
        check_vk_result(err);

        wd->SemaphoreCount = wd->ImageCount + 1;
        wd->Frames.resize(wd->ImageCount);
        wd->FrameSemaphores.resize(wd->SemaphoreCount);
        memset(wd->Frames.Data, 0, wd->Frames.size_in_bytes());
        memset(wd->FrameSemaphores.Data, 0, wd->FrameSemaphores.size_in_bytes());
        for (uint32_t i = 0; i < wd->ImageCount; i++)
            wd->Frames[i].Backbuffer = backbuffers[i];
    }
    if (old_swapchain)
        vkDestroySwapchainKHR(device, old_swapchain, allocator);

    // Create the Render Pass
    if (wd->UseDynamicRendering == false)
    {
        VkAttachmentDescription attachment = wd->AttachmentDesc;
        if (attachment.format == VK_FORMAT_UNDEFINED)
            attachment.format = wd->SurfaceFormat.format;
        VkAttachmentReference color_attachment = {};
        color_attachment.attachment = 0;
        color_attachment.layout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
        VkSubpassDescription subpass = {};
        subpass.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
        subpass.colorAttachmentCount = 1;
        subpass.pColorAttachments = &color_attachment;
        VkSubpassDependency dependency = {};
        dependency.srcSubpass = VK_SUBPASS_EXTERNAL;
        dependency.dstSubpass = 0;
        dependency.srcStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
        dependency.dstStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
        dependency.srcAccessMask = 0;
        dependency.dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
        VkRenderPassCreateInfo info = {};
        info.sType = VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO;
        info.attachmentCount = 1;
        info.pAttachments = &attachment;
        info.subpassCount = 1;
        info.pSubpasses = &subpass;
        info.dependencyCount = 1;
        info.pDependencies = &dependency;
        err = vkCreateRenderPass(device, &info, allocator, &wd->RenderPass);
        check_vk_result(err);

        // We do not create a pipeline by default as this is also used by examples' main.cpp,
        // but secondary viewport in multi-viewport mode may want to create one with:
        //ImGui_ImplVulkan_CreatePipeline(device, allocator, VK_NULL_HANDLE, wd->RenderPass, VK_SAMPLE_COUNT_1_BIT, &wd->Pipeline, v->Subpass);
    }

    // Create The Image Views
    {
        VkImageViewCreateInfo info = {};
        info.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        info.viewType = VK_IMAGE_VIEW_TYPE_2D;
        info.format = wd->SurfaceFormat.format;
        info.components.r = VK_COMPONENT_SWIZZLE_R;
        info.components.g = VK_COMPONENT_SWIZZLE_G;
        info.components.b = VK_COMPONENT_SWIZZLE_B;
        info.components.a = VK_COMPONENT_SWIZZLE_A;
        VkImageSubresourceRange image_range = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 };
        info.subresourceRange = image_range;
        for (uint32_t i = 0; i < wd->ImageCount; i++)
        {
            ImGui_ImplVulkanH_Frame* fd = &wd->Frames[i];
            info.image = fd->Backbuffer;
            err = vkCreateImageView(device, &info, allocator, &fd->BackbufferView);
            check_vk_result(err);
        }
    }

    // Create Framebuffer
    if (wd->UseDynamicRendering == false)
    {
        VkImageView attachment[1];
        VkFramebufferCreateInfo info = {};
        info.sType = VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO;
        info.renderPass = wd->RenderPass;
        info.attachmentCount = 1;
        info.pAttachments = attachment;
        info.width = wd->Width;
        info.height = wd->Height;
        info.layers = 1;
        for (uint32_t i = 0; i < wd->ImageCount; i++)
        {
            ImGui_ImplVulkanH_Frame* fd = &wd->Frames[i];
            attachment[0] = fd->BackbufferView;
            err = vkCreateFramebuffer(device, &info, allocator, &fd->Framebuffer);
            check_vk_result(err);
        }
    }
}

// Create or resize window
// - 2025/09/26: v1.92.4 added a trailing 'VkImageUsageFlags image_usage' parameter which is usually VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT.
void ImGui_ImplVulkanH_CreateOrResizeWindow(VkInstance instance, VkPhysicalDevice physical_device, VkDevice device, ImGui_ImplVulkanH_Window* wd, uint32_t queue_family, const VkAllocationCallbacks* allocator, int width, int height, uint32_t min_image_count, VkImageUsageFlags image_usage)
{
    IM_ASSERT(g_FunctionsLoaded && "Need to call ImGui_ImplVulkan_LoadFunctions() if IMGUI_IMPL_VULKAN_NO_PROTOTYPES or VK_NO_PROTOTYPES are set!");
    IM_ASSERT(wd->Surface != VK_NULL_HANDLE);
    IM_UNUSED(instance);

    ImGui_ImplVulkanH_CreateWindowSwapChain(physical_device, device, wd, allocator, width, height, min_image_count, image_usage);
    ImGui_ImplVulkanH_CreateWindowCommandBuffers(physical_device, device, wd, queue_family, allocator);

    // FIXME: to submit the command buffer, we need a queue. In the examples folder, the ImGui_ImplVulkanH_CreateOrResizeWindow function is called
    // before the ImGui_ImplVulkan_Init function, so we don't have access to the queue yet. Here we have the queue_family that we can use to grab
    // a queue from the device and submit the command buffer. It would be better to have access to the queue as suggested in the FIXME below.
    VkCommandPool command_pool;
    VkCommandPoolCreateInfo pool_info = {};
    pool_info.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
    pool_info.queueFamilyIndex = queue_family;
    VkResult err = vkCreateCommandPool(device, &pool_info, allocator, &command_pool);
    check_vk_result(err);

    VkFenceCreateInfo fence_info = {};
    fence_info.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
    VkFence fence;
    err = vkCreateFence(device, &fence_info, allocator, &fence);
    check_vk_result(err);

    VkCommandBufferAllocateInfo alloc_info = {};
    alloc_info.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    alloc_info.commandPool = command_pool;
    alloc_info.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    alloc_info.commandBufferCount = 1;
    VkCommandBuffer command_buffer;
    err = vkAllocateCommandBuffers(device, &alloc_info, &command_buffer);
    check_vk_result(err);

    VkCommandBufferBeginInfo begin_info = {};
    begin_info.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    begin_info.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    err = vkBeginCommandBuffer(command_buffer, &begin_info);
    check_vk_result(err);

    // Transition the images to the correct layout for rendering
    for (uint32_t i = 0; i < wd->ImageCount; i++)
    {
        VkImageMemoryBarrier barrier = {};
        barrier.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
        barrier.image = wd->Frames[i].Backbuffer;
        barrier.oldLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        barrier.newLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
        barrier.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        barrier.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        barrier.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        barrier.subresourceRange.levelCount = 1;
        barrier.subresourceRange.layerCount = 1;
        vkCmdPipelineBarrier(command_buffer, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, 0, 0, nullptr, 0, nullptr, 1, &barrier);
    }

    err = vkEndCommandBuffer(command_buffer);
    check_vk_result(err);
    VkSubmitInfo submit_info = {};
    submit_info.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
    submit_info.commandBufferCount = 1;
    submit_info.pCommandBuffers = &command_buffer;

    VkQueue queue;
    vkGetDeviceQueue(device, queue_family, 0, &queue);
    err = vkQueueSubmit(queue, 1, &submit_info, fence);
    check_vk_result(err);
    err = vkWaitForFences(device, 1, &fence, VK_TRUE, UINT64_MAX);
    check_vk_result(err);
    err = vkResetFences(device, 1, &fence);
    check_vk_result(err);

    err = vkResetCommandPool(device, command_pool, 0);
    check_vk_result(err);

    // Destroy command buffer and fence and command pool
    vkFreeCommandBuffers(device, command_pool, 1, &command_buffer);
    vkDestroyCommandPool(device, command_pool, allocator);
    vkDestroyFence(device, fence, allocator);
    command_pool = VK_NULL_HANDLE;
    command_buffer = VK_NULL_HANDLE;
    fence = VK_NULL_HANDLE;
    queue = VK_NULL_HANDLE;
}

void ImGui_ImplVulkanH_DestroyWindow(VkInstance instance, VkDevice device, ImGui_ImplVulkanH_Window* wd, const VkAllocationCallbacks* allocator)
{
    IM_UNUSED(instance);
    vkDeviceWaitIdle(device); // FIXME: We could wait on the Queue if we had the queue in wd-> (otherwise VulkanH functions can't use globals)
    //vkQueueWaitIdle(bd->Queue);

    for (uint32_t i = 0; i < wd->ImageCount; i++)
        ImGui_ImplVulkanH_DestroyFrame(device, &wd->Frames[i], allocator);
    for (uint32_t i = 0; i < wd->SemaphoreCount; i++)
        ImGui_ImplVulkanH_DestroyFrameSemaphores(device, &wd->FrameSemaphores[i], allocator);
    wd->Frames.clear();
    wd->FrameSemaphores.clear();
    vkDestroyPipeline(device, wd->Pipeline, allocator);
    vkDestroyRenderPass(device, wd->RenderPass, allocator);
    vkDestroySwapchainKHR(device, wd->Swapchain, allocator);
    wd->RenderPass = VK_NULL_HANDLE;
    wd->Swapchain = VK_NULL_HANDLE;
    wd->Width = wd->Height = 0;
    wd->FrameIndex = wd->ImageCount = wd->SemaphoreCount = wd->SemaphoreIndex = 0;
    //vkDestroySurfaceKHR(instance, wd->Surface, allocator); // v1.92.6 (~2026-01-16): because wd->Surface is user provided we don't attempt to destroy it ourself.
}

void ImGui_ImplVulkanH_DestroyFrame(VkDevice device, ImGui_ImplVulkanH_Frame* fd, const VkAllocationCallbacks* allocator)
{
    vkDestroyFence(device, fd->Fence, allocator);
    vkFreeCommandBuffers(device, fd->CommandPool, 1, &fd->CommandBuffer);
    vkDestroyCommandPool(device, fd->CommandPool, allocator);
    fd->Fence = VK_NULL_HANDLE;
    fd->CommandBuffer = VK_NULL_HANDLE;
    fd->CommandPool = VK_NULL_HANDLE;

    vkDestroyImageView(device, fd->BackbufferView, allocator);
    vkDestroyFramebuffer(device, fd->Framebuffer, allocator);
}

void ImGui_ImplVulkanH_DestroyFrameSemaphores(VkDevice device, ImGui_ImplVulkanH_FrameSemaphores* fsd, const VkAllocationCallbacks* allocator)
{
    vkDestroySemaphore(device, fsd->ImageAcquiredSemaphore, allocator);
    vkDestroySemaphore(device, fsd->RenderCompleteSemaphore, allocator);
    fsd->ImageAcquiredSemaphore = fsd->RenderCompleteSemaphore = VK_NULL_HANDLE;
}

//-----------------------------------------------------------------------------

#endif // #ifndef IMGUI_DISABLE
