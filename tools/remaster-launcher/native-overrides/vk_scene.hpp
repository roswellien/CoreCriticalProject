// Vulkan scene renderer for the Direct3D 6 provider (adapted from tools/vulkan-probe/replay.cpp).
// The provider records a scene (transformed-and-lit vertices, fixed-function state, clears) and the
// renderer draws it into the guest render target: the target's 16-bit pixels and the guest z-buffer are
// uploaded, the scene is rasterized on the GPU, and both are read back into guest memory, where the game's
// own 2D code and Flip continue to use them. Colour uses R5G6B5 (the target's format, so blending happens
// at the target's precision) and depth D16 (the game's 16-bit z-buffer). The Vulkan loader is opened at
// run time; no validation layer is required (MW34_VK_VALIDATION=1 enables it when installed).
// The same device presents flipped frames: the guest front buffer (R5G6B5) is uploaded and blitted to a
// FIFO swapchain on the game's window (Flip waits for the vertical blank, as DDFLIP_WAIT did).
#pragma once
#include "capture_pixels.hpp"
#define VK_NO_PROTOTYPES
#include <vulkan/vulkan_core.h>
#include <windows.h>
#include <vulkan/vulkan_win32.h>
#include <algorithm>
#include <cstdlib>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
#include <memory>
#include <cstddef>
#include "model_scene_vert.h"
#include "d3d_scene_vert.h"
#include "d3d_scene_frag.h"
#include "fxaa_vert.h"
#include "fxaa_frag.h"
#include "frontend_canvas.hpp"

namespace mw34::vkscene {
// The stage mirrors the guest's x87 control word and MXCSR into the host while guest code runs; driver
// and window-system code must run under the host's default floating-point environment.
struct HostFpEnvironment {
    unsigned short cw;
    unsigned mxcsr;
    HostFpEnvironment() {
        __asm__ volatile("fnstcw %0\n\tstmxcsr %1" : "=m"(cw), "=m"(mxcsr));
        const unsigned short dcw = 0x27f;
        const unsigned dmx = 0x1f80;
        __asm__ volatile("fnclex\n\tfldcw %0\n\tldmxcsr %1" ::"m"(dcw), "m"(dmx));
    }
    ~HostFpEnvironment() { __asm__ volatile("fnclex\n\tfldcw %0\n\tldmxcsr %1" ::"m"(cw), "m"(mxcsr)); }
};
// rgba8888: host-composed straight-alpha RGBA (GPU HUD images: RGB565 colour with the image's alpha mask or colour key),
// carried in pixels32 (R, G, B, A bytes in memory order).
enum class TexFormat { rgb565, argb1555, argb4444, rgba8888 };
struct TextureRef { std::uint64_t key, hash; unsigned width, height; TexFormat format; std::vector<std::uint16_t> pixels; std::vector<std::uint32_t> pixels32; };
// Fixed-function state that selects a pipeline: blend enable/source/destination (D3DBLEND), depth
// enable/function (D3DCMP)/write, cull mode (D3DCULL).
struct PipelineKey {
    std::uint8_t blend, src, dst, zenable, zfunc, zwrite, cull, points = 0;  // points: D3DPT_POINTLIST input assembly
    std::uint64_t packed() const { return std::uint64_t(blend) | std::uint64_t(src) << 8 | std::uint64_t(dst) << 16 | std::uint64_t(zenable) << 24 | std::uint64_t(zfunc) << 32 | std::uint64_t(zwrite) << 40 | std::uint64_t(cull) << 48 | std::uint64_t(points) << 56; }
};
struct Push { float target[4], fog[4], factor[4]; std::uint32_t mode[4]; };
static_assert(sizeof(Push) == 64);
struct ModelVertex { float x,y,z,nx,ny,nz,u,v; };
static_assert(sizeof(ModelVertex)==32);
struct ModelGeometry { std::uint64_t key{},hash{};std::vector<ModelVertex> vertices; };
struct ModelInstance { std::shared_ptr<const ModelGeometry> geometry;std::array<float,12> camera{};std::array<float,6> projection{};std::uint32_t color{}; };
struct ModelPush { Push base;std::array<float,12> camera;std::array<float,4> projection; };
static_assert(sizeof(ModelPush)==128&&offsetof(ModelPush,camera)==64&&offsetof(ModelPush,projection)==112);
struct Draw { unsigned first, count; int texture; unsigned sampler; PipelineKey key; Push push; VkRect2D scissor;std::shared_ptr<const ModelInstance> model{}; };
struct Clear { unsigned flags; float color[4]; float z; std::vector<VkRect2D> rects; };
struct Command { bool clear; unsigned index; };
struct Scene {
    unsigned width, height;
    std::vector<std::uint16_t> color, depth;  // in/out, tightly packed width*height
    bool has_depth;
    bool frontend_canvas{};
    bool hud{}; // Host HUD/overlay draws keep their original sampling and follow world AA.
    std::vector<unsigned char> vertices;      // 32-byte TL vertices, triangle list
    std::vector<TextureRef> textures;
    std::vector<Draw> draws;
    std::vector<Clear> clears;
    std::vector<Command> order;
};

class Renderer {
public:
    std::string device_name;
    std::uint64_t scenes{}, draws{}, uploads{};
    // Optional host performance overlay (MW34_PERF_OVERLAY=1, play.ps1 -Overlay; off by default). It is drawn into the
    // host upload copy of each presented frame, never into guest memory: presented frames per second, and the mean and
    // worst time between presents over the last second, refreshed four times a second.
    struct PerfOverlay {
        bool on = [] { const char *e = std::getenv("MW34_PERF_OVERLAY"); return e && *e && std::strcmp(e, "0") != 0; }();
        std::vector<std::int64_t> t; std::int64_t qpf{}, shown{}; char text[48]{};
        unsigned box_w{}, box_h{};  // drawn box of the last draw() (the GPU path uploads just this region)
        static const std::uint8_t *glyph(char c) {
            static const std::uint8_t g[][8] = {
                {'0',0x0E,0x11,0x13,0x15,0x19,0x11,0x0E},{'1',0x04,0x0C,0x04,0x04,0x04,0x04,0x0E},{'2',0x0E,0x11,0x01,0x02,0x04,0x08,0x1F},
                {'3',0x1F,0x02,0x04,0x02,0x01,0x11,0x0E},{'4',0x02,0x06,0x0A,0x12,0x1F,0x02,0x02},{'5',0x1F,0x10,0x1E,0x01,0x01,0x11,0x0E},
                {'6',0x06,0x08,0x10,0x1E,0x11,0x11,0x0E},{'7',0x1F,0x01,0x02,0x04,0x08,0x08,0x08},{'8',0x0E,0x11,0x11,0x0E,0x11,0x11,0x0E},
                {'9',0x0E,0x11,0x11,0x0F,0x01,0x02,0x0C},{'.',0,0,0,0,0,0x0C,0x0C},{'F',0x1F,0x10,0x10,0x1E,0x10,0x10,0x10},
                {'P',0x1E,0x11,0x11,0x1E,0x10,0x10,0x10},{'S',0x0F,0x10,0x10,0x0E,0x01,0x01,0x1E},{'A',0x0E,0x11,0x11,0x1F,0x11,0x11,0x11},
                {'V',0x11,0x11,0x11,0x11,0x11,0x0A,0x04},{'G',0x0E,0x11,0x10,0x17,0x11,0x11,0x0F},{'M',0x11,0x1B,0x15,0x15,0x11,0x11,0x11},
                {'X',0x11,0x11,0x0A,0x04,0x0A,0x11,0x11},{' ',0,0,0,0,0,0,0}};
            for (const auto &e : g) if (e[0] == std::uint8_t(c)) return e + 1;
            return g[19] + 1;
        }
        void draw(std::uint16_t *px, unsigned w, unsigned h) {
            LARGE_INTEGER q{}; ::QueryPerformanceCounter(&q); if (!qpf) { LARGE_INTEGER f{}; ::QueryPerformanceFrequency(&f); qpf = f.QuadPart; }
            const std::int64_t now = q.QuadPart; t.push_back(now);
            std::size_t first = 0; while (first < t.size() && now - t[first] > qpf) ++first;
            if (first) t.erase(t.begin(), t.begin() + std::ptrdiff_t(first));
            if (now - shown >= qpf / 4 && t.size() >= 2) {
                shown = now; double worst = 0;
                for (std::size_t i = 1; i < t.size(); ++i) worst = std::max(worst, double(t[i] - t[i - 1]) * 1000.0 / double(qpf));
                const double span = double(t.back() - t.front()) / double(qpf), n = double(t.size() - 1);
                std::snprintf(text, sizeof text, "FPS %.1f  AVG %.1fMS  MAX %.1fMS", n / span, span * 1000.0 / n, worst);
            }
            if (!text[0]) return;
            const unsigned sc = w >= 400 ? 2 : 1, len = unsigned(std::strlen(text)), bw = (len * 6 + 2) * sc, bh = 10 * sc;
            box_w = std::min(bw, w); box_h = std::min(bh, h);
            for (unsigned y = 0; y < bh && y < h; ++y) for (unsigned x = 0; x < bw && x < w; ++x) px[size_t(y) * w + x] = 0;
            for (unsigned i = 0; i < len; ++i) { const std::uint8_t *g = glyph(text[i]);
                for (unsigned r = 0; r < 7; ++r) for (unsigned c = 0; c < 5; ++c) if (g[r] & (0x10 >> c))
                    for (unsigned dy = 0; dy < sc; ++dy) for (unsigned dx = 0; dx < sc; ++dx) {
                        const unsigned x = (2 + i * 6 + c) * sc + dx, y = (2 + r) * sc + dy; if (x < w && y < h) px[size_t(y) * w + x] = 0xFFE0; } }
        }
    } overlay;
    ~Renderer() { HostFpEnvironment fp; shutdown(); }
    // Presents a 16-bit RGB565 frame (rows of `pitch` bytes) to the window. False when this device cannot
    // present to the window (no surface/swapchain support); the caller then uses its other presenter.
    bool present(HWND hwnd, const std::uint8_t *pixels, unsigned w, unsigned h, unsigned pitch,bool wide_world=false) {
        HostFpEnvironment fp;
        if (!::IsWindowVisible(hwnd)) return true;  // hidden: nothing to present
        // The swapchain lives on a host-owned child window covering the game window's client area (the game
        // window itself was associated with the system DirectDraw by the original's cooperative-level call).
        // The child is disabled, hit-test transparent and sends no parent notifications, so the game window's
        // messages and input are unchanged.
        if (hwnd != presentParent) {
            if (device) { dropSwapchain(); dropSurface(); }
            if (child) ::DestroyWindow(child);
            child = makeChild(hwnd); presentParent = hwnd;
            if (!child) return false;
            // A presenting instance selects the device that can present to this window (on hybrid systems
            // the display may belong to another adapter than the one rendering scenes).
            if (!device) init(child); else if (presentable && !surface(child)) return false;
        }
        if (!presentable || !windowSurface) return false;
        // The previous Flip's copy/blit is waited for here, before its upload buffer, command pool or source image
        // are reused, instead of right after vkQueuePresentKHR (presentation stays one frame per Flip).
        if (presentInFlight) { check(f.vkWaitForFences(device, 1, &presentFence, VK_TRUE, 10000000000ULL), "wait present"); presentInFlight = false; }
        { RECT rc{}; ::GetClientRect(hwnd, &rc); RECT cc{}; ::GetClientRect(child, &cc);
          if (cc.right != rc.right || cc.bottom != rc.bottom) ::SetWindowPos(child, nullptr, 0, 0, rc.right, rc.bottom, SWP_NOZORDER | SWP_NOACTIVATE); }
        if (!swapchainReady()) return true;  // minimized: nothing to present
        if (w != srcWidth || h != srcHeight) presentSource(w, h);
        ensure(presentUpload, VkDeviceSize(w) * h * 2, VK_BUFFER_USAGE_TRANSFER_SRC_BIT);
        auto *dst = static_cast<std::uint8_t *>(presentUpload.mapped);
        for (unsigned y = 0; y < h; ++y) std::memcpy(dst + size_t(y) * w * 2, pixels + size_t(y) * pitch, size_t(w) * 2);
        if (overlay.on) overlay.draw(reinterpret_cast<std::uint16_t *>(dst), w, h);
        unsigned index = 0;
        VkResult r = f.vkAcquireNextImageKHR(device, swapchain, UINT64_MAX, acquired, VK_NULL_HANDLE, &index);
        if (r == VK_ERROR_OUT_OF_DATE_KHR) { dropSwapchain(); if (!swapchainReady()) return true; r = f.vkAcquireNextImageKHR(device, swapchain, UINT64_MAX, acquired, VK_NULL_HANDLE, &index); }
        if (r != VK_SUCCESS && r != VK_SUBOPTIMAL_KHR) check(r, "acquire swapchain image");
        check(f.vkResetCommandPool(device, presentPool, 0), "reset present pool");
        VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
        bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        check(f.vkBeginCommandBuffer(presentCmd, &bi), "begin present");
        auto bar = [&](VkImage img, VkImageLayout from, VkImageLayout to, VkAccessFlags sa, VkAccessFlags da) {
            VkImageMemoryBarrier b{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};
            b.srcAccessMask = sa; b.dstAccessMask = da; b.oldLayout = from; b.newLayout = to;
            b.srcQueueFamilyIndex = b.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED; b.image = img; b.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
            f.vkCmdPipelineBarrier(presentCmd, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, nullptr, 0, nullptr, 1, &b);
        };
        bar(srcImage.image, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 0, VK_ACCESS_TRANSFER_WRITE_BIT);
        VkBufferImageCopy c{};
        c.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1}; c.imageExtent = {w, h, 1};
        f.vkCmdCopyBufferToImage(presentCmd, presentUpload.buffer, srcImage.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &c);
        bar(srcImage.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT);
        bar(swapImages[index], VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 0, VK_ACCESS_TRANSFER_WRITE_BIT);
        // Scaled to the window's client area with nearest sampling (the GDI presenter's COLORONCOLOR).
        VkImageBlit blit{};
        blit.srcSubresource = blit.dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
        blit.srcOffsets[1] = {int(w), int(h), 1}; blit.dstOffsets[1] = {int(swapExtent.width), int(swapExtent.height), 1};
        // Original menu/movie rasters retain their proportions in the centre.
        // A guest-resolution readback of the corrected world spans the wide view.
        if(widescreen()&&!wide_world){const double fit=std::min(double(swapExtent.width)/w,double(swapExtent.height)/h);
            const int dw=int(std::lround(w*fit)),dh=int(std::lround(h*fit)),dx=(int(swapExtent.width)-dw)/2,dy=(int(swapExtent.height)-dh)/2;
            const VkClearColorValue black{};const VkImageSubresourceRange all{VK_IMAGE_ASPECT_COLOR_BIT,0,1,0,1};
            f.vkCmdClearColorImage(presentCmd,swapImages[index],VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,&black,1,&all);
            bar(swapImages[index],VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_TRANSFER_WRITE_BIT);
            blit.dstOffsets[0]={dx,dy,0};blit.dstOffsets[1]={dx+dw,dy+dh,1};}
        f.vkCmdBlitImage(presentCmd, srcImage.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, swapImages[index], VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &blit, VK_FILTER_NEAREST);
        bar(swapImages[index], VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_PRESENT_SRC_KHR, VK_ACCESS_TRANSFER_WRITE_BIT, 0);
        check(f.vkEndCommandBuffer(presentCmd), "end present");
        const VkPipelineStageFlags waitStage = VK_PIPELINE_STAGE_TRANSFER_BIT;
        VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};
        si.waitSemaphoreCount = 1; si.pWaitSemaphores = &acquired; si.pWaitDstStageMask = &waitStage;
        si.commandBufferCount = 1; si.pCommandBuffers = &presentCmd; si.signalSemaphoreCount = 1; si.pSignalSemaphores = &swapRendered[index];
        check(f.vkResetFences(device, 1, &presentFence), "reset present fence");
        check(f.vkQueueSubmit(queue, 1, &si, presentFence), "submit present");
        VkPresentInfoKHR pi{VK_STRUCTURE_TYPE_PRESENT_INFO_KHR};
        pi.waitSemaphoreCount = 1; pi.pWaitSemaphores = &swapRendered[index]; pi.swapchainCount = 1; pi.pSwapchains = &swapchain; pi.pImageIndices = &index;
        r = f.vkQueuePresentKHR(queue, &pi);
        if (r == VK_ERROR_OUT_OF_DATE_KHR || r == VK_SUBOPTIMAL_KHR) { check(f.vkWaitForFences(device, 1, &presentFence, VK_TRUE, 10000000000ULL), "wait present"); dropSwapchain(); return true; }
        check(r, "present");
        presentInFlight = true;
        ++presents;
        return true;
    }
    // Presents the resident scene target (lazy residency on this device: the 3D scenes and the GPU HUD of the frame)
    // directly: no guest copy, no upload. False when this device cannot present to the window yet (the caller then
    // synchronizes guest memory and uses present()). The target returns to attachment layout for the next scene.
    bool present_resident(HWND hwnd, unsigned w, unsigned h) {
        HostFpEnvironment fp;
        if (!::IsWindowVisible(hwnd)) return true;
        if (hwnd != presentParent || !child || !presentable || !windowSurface || !colorImage.image || w != width || h != height) return false;
        if (presentInFlight) { check(f.vkWaitForFences(device, 1, &presentFence, VK_TRUE, 10000000000ULL), "wait present"); presentInFlight = false; }
        { RECT rc{}; ::GetClientRect(hwnd, &rc); RECT cc{}; ::GetClientRect(child, &cc);
          if (cc.right != rc.right || cc.bottom != rc.bottom) ::SetWindowPos(child, nullptr, 0, 0, rc.right, rc.bottom, SWP_NOZORDER | SWP_NOACTIVATE); }
        if (!swapchainReady()) return true;
        unsigned index = 0;
        VkResult r = f.vkAcquireNextImageKHR(device, swapchain, UINT64_MAX, acquired, VK_NULL_HANDLE, &index);
        if (r == VK_ERROR_OUT_OF_DATE_KHR) { dropSwapchain(); if (!swapchainReady()) return true; r = f.vkAcquireNextImageKHR(device, swapchain, UINT64_MAX, acquired, VK_NULL_HANDLE, &index); }
        if (r != VK_SUCCESS && r != VK_SUBOPTIMAL_KHR) check(r, "acquire swapchain image");
        check(f.vkResetCommandPool(device, presentPool, 0), "reset present pool");
        VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
        bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        check(f.vkBeginCommandBuffer(presentCmd, &bi), "begin resident present");
        auto bar = [&](VkImage img, VkImageLayout from, VkImageLayout to, VkAccessFlags sa, VkAccessFlags da, VkPipelineStageFlags ss, VkPipelineStageFlags ds,VkImageAspectFlags aspect=VK_IMAGE_ASPECT_COLOR_BIT) {
            VkImageMemoryBarrier b{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};
            b.srcAccessMask = sa; b.dstAccessMask = da; b.oldLayout = from; b.newLayout = to;
            b.srcQueueFamilyIndex = b.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED; b.image = img; b.subresourceRange = {aspect, 0, 1, 0, 1};
            f.vkCmdPipelineBarrier(presentCmd, ss, ds, 0, 0, nullptr, 0, nullptr, 1, &b);
        };
        if (in_attachment_layout)
            bar(colorImage.image, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT,
                VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT);
        bar(swapImages[index], VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 0, VK_ACCESS_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT);
        // The frame keeps its aspect ratio (side or top bars are cleared to black when the window's differs).
        const double sx = double(swapExtent.width) / rw, sy = double(swapExtent.height) / rh, fit = std::min(sx, sy);
        const int dw = int(std::lround(rw * fit)), dh = int(std::lround(rh * fit)), dx = (int(swapExtent.width) - dw) / 2, dy = (int(swapExtent.height) - dh) / 2;
        if (dx > 0 || dy > 0) {
            const VkClearColorValue black{};
            const VkImageSubresourceRange all{VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
            f.vkCmdClearColorImage(presentCmd, swapImages[index], VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, &black, 1, &all);
            bar(swapImages[index],VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,VK_ACCESS_TRANSFER_WRITE_BIT,VK_ACCESS_TRANSFER_WRITE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT);
        }
        VkImageBlit blit{};
        blit.srcSubresource = blit.dstSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1};
        blit.srcOffsets[1] = {int(rw), int(rh), 1}; blit.dstOffsets[0] = {dx, dy, 0}; blit.dstOffsets[1] = {dx + dw, dy + dh, 1};
        f.vkCmdBlitImage(presentCmd, colorImage.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, swapImages[index], VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &blit,
                         (dw == int(rw) && dh == int(rh)) ? VK_FILTER_NEAREST : VK_FILTER_LINEAR);
        bar(swapImages[index], VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_PRESENT_SRC_KHR, VK_ACCESS_TRANSFER_WRITE_BIT, 0, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_BOTTOM_OF_PIPE_BIT);
        bar(colorImage.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, VK_ACCESS_TRANSFER_READ_BIT,
            VK_ACCESS_COLOR_ATTACHMENT_READ_BIT | VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT);
        if(!in_attachment_layout)bar(depthImage.image,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,VK_ACCESS_TRANSFER_READ_BIT,VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT|VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT|VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT,VK_IMAGE_ASPECT_DEPTH_BIT);
        in_attachment_layout = true;
        check(f.vkEndCommandBuffer(presentCmd), "end resident present");
        const VkPipelineStageFlags waitStage = VK_PIPELINE_STAGE_TRANSFER_BIT;
        VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};
        si.waitSemaphoreCount = 1; si.pWaitSemaphores = &acquired; si.pWaitDstStageMask = &waitStage;
        si.commandBufferCount = 1; si.pCommandBuffers = &presentCmd; si.signalSemaphoreCount = 1; si.pSignalSemaphores = &swapRendered[index];
        check(f.vkResetFences(device, 1, &presentFence), "reset present fence");
        check(f.vkQueueSubmit(queue, 1, &si, presentFence), "submit resident present");
        VkPresentInfoKHR pi{VK_STRUCTURE_TYPE_PRESENT_INFO_KHR};
        pi.waitSemaphoreCount = 1; pi.pWaitSemaphores = &swapRendered[index]; pi.swapchainCount = 1; pi.pSwapchains = &swapchain; pi.pImageIndices = &index;
        r = f.vkQueuePresentKHR(queue, &pi);
        if (r == VK_ERROR_OUT_OF_DATE_KHR || r == VK_SUBOPTIMAL_KHR) { check(f.vkWaitForFences(device, 1, &presentFence, VK_TRUE, 10000000000ULL), "wait present"); dropSwapchain(); return true; }
        check(r, "present");
        presentInFlight = true;
        ++presents;
        ++resident_presents;
        return true;
    }
    std::uint64_t resident_presents{};
    // Diagnostic: the resident colour image at the render resolution as a binary PPM.
    void dump_fullres(const char *path) {
        HostFpEnvironment fp;
        finish_world();
        settle();
        const VkDeviceSize bytes = VkDeviceSize(rw) * rh * (rgba ? 4 : 2);
        ensure(readback, std::max<VkDeviceSize>(bytes, VkDeviceSize(width) * height * 4), VK_BUFFER_USAGE_TRANSFER_DST_BIT);
        check(f.vkResetCommandPool(device, commandPool, 0), "reset command pool");
        VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
        bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        check(f.vkBeginCommandBuffer(cmd, &bi), "begin dump");
        if (in_attachment_layout) {
            barrier(colorImage.image, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT,
                    VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
            barrier(depthImage.image,VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,VK_ACCESS_TRANSFER_READ_BIT,VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_IMAGE_ASPECT_DEPTH_BIT);
        }
        VkBufferImageCopy c{};
        c.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1}; c.imageExtent = {rw, rh, 1};
        f.vkCmdCopyImageToBuffer(cmd, colorImage.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, readback.buffer, 1, &c);
        VkMemoryBarrier hb{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
        hb.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT; hb.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
        f.vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT, 0, 1, &hb, 0, nullptr, 0, nullptr);
        check(f.vkEndCommandBuffer(cmd), "end dump");
        check(f.vkResetFences(device, 1, &fence), "reset fence");
        VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};
        si.commandBufferCount = 1; si.pCommandBuffers = &cmd;
        check(f.vkQueueSubmit(queue, 1, &si, fence), "submit dump");
        check(f.vkWaitForFences(device, 1, &fence, VK_TRUE, 10000000000ULL), "wait dump");
        in_attachment_layout = false;
        FILE *out = std::fopen(path, "wb");
        if (!out) return;
        std::fprintf(out, "P6\n%u %u\n255\n", rw, rh);
        const auto *src = static_cast<const unsigned char *>(readback.mapped);
        std::vector<unsigned char> row(size_t(rw) * 3);
        for (unsigned y = 0; y < rh; ++y) {
            for (unsigned x = 0; x < rw; ++x) {
                unsigned char *o = &row[size_t(x) * 3];
                if (rgba) { const unsigned char *p = src + (size_t(y) * rw + x) * 4; o[0] = p[0]; o[1] = p[1]; o[2] = p[2]; }
                else { const unsigned p = src[(size_t(y) * rw + x) * 2] | src[(size_t(y) * rw + x) * 2 + 1] << 8; o[0] = ((p >> 11) & 31) * 255 / 31; o[1] = ((p >> 5) & 63) * 255 / 63; o[2] = (p & 31) * 255 / 31; }
            }
            std::fwrite(row.data(), row.size(), 1, out);
        }
        std::fclose(out);
    }
    void capture_fullres_rgb(std::vector<std::uint8_t> &out_rgb, unsigned &out_w, unsigned &out_h) {
        HostFpEnvironment fp;
        finish_world();
        settle();
        out_w = rw;
        out_h = rh;
        if (!rw || !rh || !colorImage.image) { out_rgb.clear(); return; }
        const VkDeviceSize bytes = VkDeviceSize(rw) * rh * (rgba ? 4 : 2);
        ensure(readback, std::max<VkDeviceSize>(bytes, VkDeviceSize(width) * height * 4), VK_BUFFER_USAGE_TRANSFER_DST_BIT);
        check(f.vkResetCommandPool(device, commandPool, 0), "reset command pool");
        VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
        bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        check(f.vkBeginCommandBuffer(cmd, &bi), "begin capture");
        if (in_attachment_layout) {
            barrier(colorImage.image, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT,
                    VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
            barrier(depthImage.image, VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT,
                    VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_DEPTH_BIT);
        }
        VkBufferImageCopy c{};
        c.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1}; c.imageExtent = {rw, rh, 1};
        f.vkCmdCopyImageToBuffer(cmd, colorImage.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, readback.buffer, 1, &c);
        VkMemoryBarrier hb{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
        hb.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT; hb.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
        f.vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT, 0, 1, &hb, 0, nullptr, 0, nullptr);
        check(f.vkEndCommandBuffer(cmd), "end capture");
        check(f.vkResetFences(device, 1, &fence), "reset fence");
        VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};
        si.commandBufferCount = 1; si.pCommandBuffers = &cmd;
        check(f.vkQueueSubmit(queue, 1, &si, fence), "submit capture");
        check(f.vkWaitForFences(device, 1, &fence, VK_TRUE, 10000000000ULL), "wait capture");
        in_attachment_layout = false;
        const auto *src = static_cast<const unsigned char *>(readback.mapped);
        out_rgb.resize(size_t(rw) * rh * 3);
        for (unsigned y = 0; y < rh; ++y) {
            for (unsigned x = 0; x < rw; ++x) {
                std::uint8_t *o = &out_rgb[(size_t(y) * rw + x) * 3];
                if (rgba) { const unsigned char *p = src + (size_t(y) * rw + x) * 4; o[0] = p[0]; o[1] = p[1]; o[2] = p[2]; }
                else { const unsigned p = src[(size_t(y) * rw + x) * 2] | (src[(size_t(y) * rw + x) * 2 + 1] << 8); o[0] = ((p >> 11) & 31) * 255 / 31; o[1] = ((p >> 5) & 63) * 255 / 63; o[2] = (p & 31) * 255 / 31; }
            }
        }
    }
    void capture_fullres_bgra(std::vector<std::uint8_t> &out_rgba, unsigned &out_w, unsigned &out_h) {
        HostFpEnvironment fp;
        finish_world();
        settle();
        out_w = rw;
        out_h = rh;
        if (!rw || !rh || !colorImage.image) { out_rgba.clear(); return; }
        const VkDeviceSize bytes = VkDeviceSize(rw) * rh * (rgba ? 4 : 2);
        ensure(readback, std::max<VkDeviceSize>(bytes, VkDeviceSize(width) * height * 4), VK_BUFFER_USAGE_TRANSFER_DST_BIT);
        check(f.vkResetCommandPool(device, commandPool, 0), "reset command pool");
        VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
        bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        check(f.vkBeginCommandBuffer(cmd, &bi), "begin capture");
        if (in_attachment_layout) {
            barrier(colorImage.image, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT,
                    VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
            barrier(depthImage.image, VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT,
                    VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_DEPTH_BIT);
        }
        VkBufferImageCopy c{};
        c.imageSubresource = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1}; c.imageExtent = {rw, rh, 1};
        f.vkCmdCopyImageToBuffer(cmd, colorImage.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, readback.buffer, 1, &c);
        VkMemoryBarrier hb{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
        hb.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT; hb.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
        f.vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT, 0, 1, &hb, 0, nullptr, 0, nullptr);
        check(f.vkEndCommandBuffer(cmd), "end capture");
        check(f.vkResetFences(device, 1, &fence), "reset fence");
        VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};
        si.commandBufferCount = 1; si.pCommandBuffers = &cmd;
        check(f.vkQueueSubmit(queue, 1, &si, fence), "submit capture");
        check(f.vkWaitForFences(device, 1, &fence, VK_TRUE, 10000000000ULL), "wait capture");
        in_attachment_layout = false;
        const auto *src = static_cast<const unsigned char *>(readback.mapped);
        out_rgba.resize(size_t(rw) * rh * 4);
        mw34::capture::to_bgra({src, size_t(bytes)}, out_rgba,
            rgba ? mw34::capture::ColorFormat::rgba8 : mw34::capture::ColorFormat::rgb565);
    }
    // Enhanced settings are explicit; sample counts are not aliases for FXAA.
    static unsigned remaster_setting(const char *name,unsigned fallback){const char*p=std::getenv(name);if(!p)return fallback;char*end{};const unsigned long n=std::strtoul(p,&end,10);
        if(!*p||*end||n>16384)throw std::runtime_error(std::string("Invalid Remaster setting ")+name);return unsigned(n);}
    static unsigned remaster_width(){const unsigned w=remaster_setting("MW34_REMASTER_WIDTH",0),h=remaster_setting("MW34_REMASTER_HEIGHT",0);
        if((w||h)&&((w!=1920&&w!=3440)||h!=1440))throw std::runtime_error("This GPU Remaster candidate supports 1920x1440 or 3440x1440");
        if((fxaa_enabled()||anisotropy()>1)&&!w)throw std::runtime_error("AA/AF require an explicit native Remaster resolution");return w;}
    static unsigned remaster_height(){return remaster_width()?1440:0;}
    static bool widescreen(){return remaster_width()==3440;}
    static bool fxaa_enabled(){static const bool on=[]{const char*p=std::getenv("MW34_REMASTER_AA");if(!p||!std::strcmp(p,"1")||!std::strcmp(p,"off"))return false;
        if(std::strcmp(p,"fxaa"))throw std::runtime_error("MW34_REMASTER_AA supports 1/off or fxaa; SSAA sample counts are not supported");
        for(const char*name:{"MW34_LAZY_RT","MW34_GPU_HUD"}){const char*v=std::getenv(name);if(!v||std::strcmp(v,"1"))throw std::runtime_error("FXAA requires resident Vulkan rendering and the GPU HUD");}return true;}();return on;}
    static unsigned anisotropy(){static const unsigned n=[]{const unsigned n=remaster_setting("MW34_REMASTER_AF",1);if(n!=1&&n!=2&&n!=4&&n!=8&&n!=16)throw std::runtime_error("MW34_REMASTER_AF supports 1, 2, 4, 8 or 16");return n;}();return n;}
    // Called before the performance overlay/presentation if no HUD followed the world.
    void finish_world(){HostFpEnvironment fp;if(!fxaa_enabled()||!quality_world_dirty||!colorImage.image)return;settle();
        check(f.vkResetCommandPool(device,commandPool,0),"reset quality pool");VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};bi.flags=VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        check(f.vkBeginCommandBuffer(cmd,&bi),"begin quality");record_fxaa();check(f.vkEndCommandBuffer(cmd),"end quality");check(f.vkResetFences(device,1,&fence),"reset quality fence");
        VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};si.commandBufferCount=1;si.pCommandBuffers=&cmd;check(f.vkQueueSubmit(queue,1,&si,fence),"submit quality");scene_pending=true;}
    std::uint64_t fxaa_passes{},af_samplers{},mip_levels_uploaded{};
    // Query the actual scene/presenter device, avoiding a throwaway render device
    // when enhanced texture banks need dimensions beyond the original 256 cap.
    unsigned max_texture_dimension(HWND){HostFpEnvironment fp;if(!device)init();
        if(!device)throw std::runtime_error("Vulkan device unavailable for enhanced texture capabilities");
        VkPhysicalDeviceProperties p{};f.vkGetPhysicalDeviceProperties(gpu,&p);return p.limits.maxImageDimension2D;}
    static bool gpu_models(){static const bool on=[]{const char*p=std::getenv("MW34_GPU_MODELS");if(p&&std::strcmp(p,"0")&&std::strcmp(p,"1"))throw std::runtime_error("MW34_GPU_MODELS must be 0 or 1");return p&&*p=='1';}();return on;}
    std::uint64_t model_uploads{},model_uploaded_bytes{},model_draws{};
    std::uint64_t presents{};
    bool presentInFlight{};
    // True when the cached texture for this guest surface already holds content version `hash` at this size.
    bool current(std::uint64_t key, std::uint64_t hash, unsigned w, unsigned h) const {
        auto it = textures.find(key);
        return it != textures.end() && it->second.valid && it->second.hash == hash && it->second.width == w && it->second.height == h;
    }
    // Lazy residency (provider MW34_LAZY_RT): with upload_in false the target images keep the content of the previous
    // scene (no guest upload); with readback_out false nothing is copied back and the images stay in attachment layout
    // until readback() copies them out on demand.
    bool in_attachment_layout{};
    bool frontend_canvas() const { return target_frontend; }
    float current_scale() const { return scale; }
    void request_scale(float s) { scale_req = s; }
    std::uint64_t readbacks{}, target_uploads{};
    // A scene without copy-back is not waited for; the next scene or copy-back waits before reusing the command pool,
    // upload, vertex and descriptor resources, so the game computes the next scene while the GPU renders this one.
    bool scene_pending{};
    void settle() {
        if (!scene_pending) return;
        check(f.vkWaitForFences(device, 1, &fence, VK_TRUE, 10000000000ULL), "wait previous scene");
        scene_pending = false;
    }
    void render(Scene &s, bool upload_in = true, bool readback_out = true) {
        HostFpEnvironment fp;
        settle();
        if (!device) init();
        if (s.width != width || s.height != height || scale_req != scale || s.frontend_canvas != target_frontend) target(s.width, s.height, s.frontend_canvas);
        if(upload_in)quality_world_dirty=false;
        const VkDeviceSize pixels = VkDeviceSize(width) * height;
        // The host-side buffers carry pixels only for an upload or a readback; a GPU-resident scene leaves them empty.
        if ((upload_in || readback_out) && (s.color.size() != pixels || s.depth.size() != pixels)) throw std::runtime_error("Scene buffers do not match the target");
        const VkDeviceSize colorBytes = pixels * (rgba ? 4 : 2), depthBytes = pixels * 2;
        ensure(upload, colorBytes + depthBytes, VK_BUFFER_USAGE_TRANSFER_SRC_BIT);
        ensure(readback, colorBytes + depthBytes, VK_BUFFER_USAGE_TRANSFER_DST_BIT);
        ensure(vertexBuffer, std::max<VkDeviceSize>(s.vertices.size(), 32), VK_BUFFER_USAGE_VERTEX_BUFFER_BIT);
        auto *up = static_cast<unsigned char *>(upload.mapped);
        if (upload_in) ++target_uploads;
        if (!upload_in) {
        } else if (rgba) {
            for (VkDeviceSize i = 0; i < pixels; ++i) {
                const unsigned p = s.color[i];
                const std::uint32_t r = ((p >> 11) & 31) * 255 / 31, g = ((p >> 5) & 63) * 255 / 63, b = (p & 31) * 255 / 31;
                const std::uint32_t v = r | g << 8 | b << 16 | 0xff000000u;
                std::memcpy(up + 4 * i, &v, 4);
            }
        } else std::memcpy(up, s.color.data(), colorBytes);
        if (upload_in) std::memcpy(up + colorBytes, s.depth.data(), depthBytes);
        if (!s.vertices.empty()) std::memcpy(vertexBuffer.mapped, s.vertices.data(), s.vertices.size());
        std::vector<ModelBuffer*> model_pending;
        for(const auto&d:s.draws)if(d.model){if(!gpu_models()||!d.model->geometry)throw std::runtime_error("GPU model draw without the enabled model path");
            auto&b=model_buffer(*d.model->geometry);if(!b.uploaded&&std::find(model_pending.begin(),model_pending.end(),&b)==model_pending.end())model_pending.push_back(&b);}
        // Textures: content-hashed cache keyed by guest surface; changed or new ones are uploaded.
        VkDeviceSize texBytes = 0;
        std::vector<std::pair<Tex *, const TextureRef *>> changed;
        std::vector<Tex *> bound(s.textures.size());
        for (size_t i = 0; i < s.textures.size(); ++i) {
            const auto &t = s.textures[i];
            auto &c = textures[t.key];
            if (c.image && (c.width != t.width || c.height != t.height)) destroy(c);
            if (!c.image) create(c, t.width, t.height);
            if (c.hash != t.hash || !c.valid) {
                if ((t.format == TexFormat::rgba8888 ? t.pixels32.size() : t.pixels.size()) != size_t(t.width) * t.height) throw std::runtime_error("Vulkan scene renderer: changed texture without pixels");
                changed.push_back({&c, &t}); texBytes += VkDeviceSize(t.width) * t.height * 4;
            }
            bound[i] = &c;
        }
        ensure(texUpload, std::max<VkDeviceSize>(texBytes, 4), VK_BUFFER_USAGE_TRANSFER_SRC_BIT);
        {
            auto *tp = static_cast<unsigned char *>(texUpload.mapped);
            for (auto &[c, t] : changed) {
                if (t->format == TexFormat::rgba8888) {
                    std::memcpy(tp, t->pixels32.data(), t->pixels32.size() * 4);
                    tp += VkDeviceSize(t->width) * t->height * 4;
                    continue;
                }
                for (size_t i = 0; i < t->pixels.size(); ++i) {
                    const unsigned p = t->pixels[i];
                    std::uint32_t r, g, b, a;
                    if (t->format == TexFormat::rgb565) { r = ((p >> 11) & 31) * 255 / 31; g = ((p >> 5) & 63) * 255 / 63; b = (p & 31) * 255 / 31; a = 255; }
                    else if (t->format == TexFormat::argb1555) { r = ((p >> 10) & 31) * 255 / 31; g = ((p >> 5) & 31) * 255 / 31; b = (p & 31) * 255 / 31; a = (p & 0x8000) ? 255 : 0; }
                    else { r = ((p >> 8) & 15) * 17; g = ((p >> 4) & 15) * 17; b = (p & 15) * 17; a = ((p >> 12) & 15) * 17; }
                    const std::uint32_t v = r | g << 8 | b << 16 | a << 24;
                    std::memcpy(tp + 4 * i, &v, 4);
                }
                tp += VkDeviceSize(t->width) * t->height * 4;
            }
        }
        // Descriptor sets: one per distinct (texture, sampler).
        if (descriptorCapacity < s.draws.size() + 1) pool(unsigned(s.draws.size() + 64));
        check(f.vkResetDescriptorPool(device, descriptorPool, 0), "reset descriptor pool");
        std::map<std::pair<Tex *, unsigned>, VkDescriptorSet> sets;
        std::vector<VkDescriptorSet> drawSets(s.draws.size());
        for (size_t i = 0; i < s.draws.size(); ++i) {
            const auto &d = s.draws[i];
            Tex *t = d.texture >= 0 ? bound[size_t(d.texture)] : &white;
            auto it = sets.find({t, d.sampler});
            if (it == sets.end()) {
                VkDescriptorSetAllocateInfo ai{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO};
                ai.descriptorPool = descriptorPool; ai.descriptorSetCount = 1; ai.pSetLayouts = &setLayout;
                VkDescriptorSet set{};
                check(f.vkAllocateDescriptorSets(device, &ai, &set), "descriptor set");
                VkDescriptorImageInfo info{sampler(d.sampler), t->view, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
                VkWriteDescriptorSet w{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};
                w.dstSet = set; w.descriptorCount = 1; w.descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER; w.pImageInfo = &info;
                f.vkUpdateDescriptorSets(device, 1, &w, 0, nullptr);
                it = sets.emplace(std::make_pair(t, d.sampler), set).first;
            }
            drawSets[i] = it->second;
        }
        check(f.vkResetCommandPool(device, commandPool, 0), "reset command pool");
        VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
        bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        check(f.vkBeginCommandBuffer(cmd, &bi), "begin");
        // Static model geometry reaches device-local memory once. Subsequent
        // frames send only controller matrices and projection constants.
        for(auto*b:model_pending){VkBufferCopy c{0,0,b->local.size};f.vkCmdCopyBuffer(cmd,b->staging.buffer,b->local.buffer,1,&c);b->uploaded=true;++model_uploads;model_uploaded_bytes+=c.size;}
        if(!model_pending.empty()){VkMemoryBarrier mb{VK_STRUCTURE_TYPE_MEMORY_BARRIER};mb.srcAccessMask=VK_ACCESS_TRANSFER_WRITE_BIT;mb.dstAccessMask=VK_ACCESS_VERTEX_ATTRIBUTE_READ_BIT;
            f.vkCmdPipelineBarrier(cmd,VK_PIPELINE_STAGE_TRANSFER_BIT,VK_PIPELINE_STAGE_VERTEX_INPUT_BIT,0,1,&mb,0,nullptr,0,nullptr);}
        {
            VkDeviceSize off = 0;
            for (auto &[c, t] : changed) {
                barrier(c->image, c->valid ? VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL : VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                        c->valid?VK_ACCESS_SHADER_READ_BIT:0, VK_ACCESS_TRANSFER_WRITE_BIT, c->valid?VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT:VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_COLOR_BIT,0,c->levels);
                copyIn(texUpload.buffer, off, c->image, t->width, t->height, VK_IMAGE_ASPECT_COLOR_BIT);
                generate_mips(*c);
                c->hash = t->hash; c->valid = true; ++uploads;
                off += VkDeviceSize(t->width) * t->height * 4;
            }
        }
        if (!upload_in) {
            // Keep the resident content: from the layout the previous scene left (attachment, or transfer source after a copy-out).
            const bool att = in_attachment_layout;
            barrier(colorImage.image, att ? VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL : VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL,
                    att ? VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT : VK_ACCESS_TRANSFER_READ_BIT, VK_ACCESS_COLOR_ATTACHMENT_READ_BIT | VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT,
                    att ? VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT : VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
            barrier(depthImage.image, att ? VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL : VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL,
                    att ? VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT : VK_ACCESS_TRANSFER_READ_BIT, VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT | VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,
                    att ? VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT : VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT | VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT,
                    VK_IMAGE_ASPECT_DEPTH_BIT);
        } else {
        barrier(colorImage.image, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 0, VK_ACCESS_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
        barrier(depthImage.image, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 0, VK_ACCESS_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_DEPTH_BIT);
        copy_in_scaled(colorBytes);
        barrier(colorImage.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, VK_ACCESS_TRANSFER_WRITE_BIT,
                VK_ACCESS_COLOR_ATTACHMENT_READ_BIT | VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
        barrier(depthImage.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL, VK_ACCESS_TRANSFER_WRITE_BIT,
                VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_READ_BIT | VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT,
                VK_PIPELINE_STAGE_EARLY_FRAGMENT_TESTS_BIT | VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT, VK_IMAGE_ASPECT_DEPTH_BIT);
        }
        in_attachment_layout=true;
        if(s.hud&&quality_world_dirty&&fxaa_enabled())record_fxaa();
        VkRenderPassBeginInfo rb{VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO};
        rb.renderPass = renderPass; rb.framebuffer = framebuffer; rb.renderArea = {{0, 0}, {rw, rh}};
        f.vkCmdBeginRenderPass(cmd, &rb, VK_SUBPASS_CONTENTS_INLINE);
        VkViewport vp{0, 0, float(rw), float(rh), 0, 1};
        f.vkCmdSetViewport(cmd, 0, 1, &vp);
        VkDeviceSize zero = 0;
        f.vkCmdBindVertexBuffers(cmd, 0, 1, &vertexBuffer.buffer, &zero);
        VkBuffer boundVertices=vertexBuffer.buffer;
        for (const auto &o : s.order) {
            if (o.clear) {
                const auto &c = s.clears[o.index];
                std::vector<VkClearAttachment> at;
                if (c.flags & 1) { VkClearAttachment a{VK_IMAGE_ASPECT_COLOR_BIT, 0, {}}; std::memcpy(a.clearValue.color.float32, c.color, 16); at.push_back(a); }
                if ((c.flags & 2) && s.has_depth) { VkClearAttachment a{VK_IMAGE_ASPECT_DEPTH_BIT, 0, {}}; a.clearValue.depthStencil.depth = c.z; at.push_back(a); }
                std::vector<VkClearRect> rects;
                for (const auto &r : c.rects) rects.push_back({scaled(r), 0, 1});
                if (!at.empty() && !rects.empty()) f.vkCmdClearAttachments(cmd, unsigned(at.size()), at.data(), unsigned(rects.size()), rects.data());
                continue;
            }
            const auto &d = s.draws[o.index];
            if (!d.count || !d.scissor.extent.width || !d.scissor.extent.height) continue;
            const bool model=bool(d.model);const VkPipelineLayout layout=model?modelLayout:pipelineLayout;
            f.vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline(d.key,model));
            f.vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_GRAPHICS, layout, 0, 1, &drawSets[o.index], 0, nullptr);
            { const VkRect2D sc = scaled(d.scissor); f.vkCmdSetScissor(cmd, 0, 1, &sc); }
            if(model){const auto&i=*d.model;const auto&b=model_buffers.at(i.geometry->key);if(!b.uploaded||d.first||d.count!=b.count)throw std::runtime_error("GPU model draw range mismatch");
                if(boundVertices!=b.local.buffer){f.vkCmdBindVertexBuffers(cmd,0,1,&b.local.buffer,&zero);boundVertices=b.local.buffer;}ModelPush mp{};mp.base=d.push;mp.camera=i.camera;
                mp.base.target[2]=i.projection[0];mp.base.target[3]=i.projection[5];mp.projection={i.projection[1],i.projection[2],i.projection[3],i.projection[4]};
                mp.base.factor[0]=float((i.color>>16)&255)/255.f;mp.base.factor[1]=float((i.color>>8)&255)/255.f;mp.base.factor[2]=float(i.color&255)/255.f;mp.base.factor[3]=1.f;
                f.vkCmdPushConstants(cmd,layout,VK_SHADER_STAGE_VERTEX_BIT|VK_SHADER_STAGE_FRAGMENT_BIT,0,sizeof(ModelPush),&mp);++model_draws;
            }else{ // A model draw binds its own VBO; ordinary TL draws must restore theirs.
                if(boundVertices!=vertexBuffer.buffer){f.vkCmdBindVertexBuffers(cmd,0,1,&vertexBuffer.buffer,&zero);boundVertices=vertexBuffer.buffer;}
                f.vkCmdPushConstants(cmd,layout,VK_SHADER_STAGE_VERTEX_BIT|VK_SHADER_STAGE_FRAGMENT_BIT,0,sizeof(Push),&d.push);}
            f.vkCmdDraw(cmd, d.count, 1, d.first, 0);
            ++draws;
        }
        f.vkCmdEndRenderPass(cmd);
        if(!s.hud&&!s.draws.empty())quality_world_dirty=true;
        if (readback_out) {
        barrier(colorImage.image, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT,
                VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
        barrier(depthImage.image, VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,
                VK_ACCESS_TRANSFER_READ_BIT, VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_DEPTH_BIT);
        copy_out_scaled(colorBytes);
        VkMemoryBarrier hb{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
        hb.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT; hb.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
        f.vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT, 0, 1, &hb, 0, nullptr, 0, nullptr);
        }
        in_attachment_layout = !readback_out;
        check(f.vkEndCommandBuffer(cmd), "end");
        check(f.vkResetFences(device, 1, &fence), "reset fence");
        VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};
        si.commandBufferCount = 1; si.pCommandBuffers = &cmd;
        check(f.vkQueueSubmit(queue, 1, &si, fence), "submit");
        ++scenes;
        if (readback_out) {
            check(f.vkWaitForFences(device, 1, &fence, VK_TRUE, 10000000000ULL), "wait");
            copy_back(s);
        } else scene_pending = true;
    }
    // Copies the resident target images into s.color/s.depth (s sized to the target).
    void fetch_resident(Scene &s) {
        HostFpEnvironment fp;
        finish_world();
        settle();
        if (s.width != width || s.height != height) throw std::runtime_error("Readback size differs from the resident target");
        check(f.vkResetCommandPool(device, commandPool, 0), "reset command pool");
        VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
        bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        check(f.vkBeginCommandBuffer(cmd, &bi), "begin readback");
        const VkDeviceSize pixels = VkDeviceSize(width) * height, colorBytes = pixels * (rgba ? 4 : 2);
        if (in_attachment_layout) {
            barrier(colorImage.image, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT,
                    VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
            barrier(depthImage.image, VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_DEPTH_STENCIL_ATTACHMENT_WRITE_BIT,
                    VK_ACCESS_TRANSFER_READ_BIT, VK_PIPELINE_STAGE_LATE_FRAGMENT_TESTS_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_DEPTH_BIT);
        }
        copy_out_scaled(colorBytes);
        VkMemoryBarrier hb{VK_STRUCTURE_TYPE_MEMORY_BARRIER};
        hb.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT; hb.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
        f.vkCmdPipelineBarrier(cmd, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT, 0, 1, &hb, 0, nullptr, 0, nullptr);
        check(f.vkEndCommandBuffer(cmd), "end readback");
        check(f.vkResetFences(device, 1, &fence), "reset fence");
        VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};
        si.commandBufferCount = 1; si.pCommandBuffers = &cmd;
        check(f.vkQueueSubmit(queue, 1, &si, fence), "submit readback");
        check(f.vkWaitForFences(device, 1, &fence, VK_TRUE, 10000000000ULL), "wait readback");
        in_attachment_layout = false;
        ++readbacks;
        copy_back(s);
    }
    void copy_back(Scene &s) {
        const VkDeviceSize pixels = VkDeviceSize(width) * height, colorBytes = pixels * (rgba ? 4 : 2), depthBytes = pixels * 2;
        const auto *rd = static_cast<const unsigned char *>(readback.mapped);
        if (rgba) {
            for (VkDeviceSize i = 0; i < pixels; ++i) {
                const std::uint32_t r = rd[4 * i], g = rd[4 * i + 1], b = rd[4 * i + 2];
                s.color[i] = std::uint16_t(((r * 31 + 127) / 255) << 11 | ((g * 63 + 127) / 255) << 5 | ((b * 31 + 127) / 255));
            }
        } else std::memcpy(s.color.data(), rd, colorBytes);
        std::memcpy(s.depth.data(), rd + colorBytes, depthBytes);
    }

private:
    struct Fns {
#define MW34_VK_FNS(X) X(vkDestroyInstance) X(vkEnumeratePhysicalDevices) X(vkGetPhysicalDeviceQueueFamilyProperties) X(vkGetPhysicalDeviceProperties) X(vkGetPhysicalDeviceFeatures) \
    X(vkGetPhysicalDeviceMemoryProperties) X(vkGetPhysicalDeviceFormatProperties) X(vkCreateDevice) X(vkGetDeviceProcAddr) X(vkEnumerateDeviceExtensionProperties)
#define MW34_VK_WSI_FNS(X) X(vkCreateWin32SurfaceKHR) X(vkDestroySurfaceKHR) X(vkGetPhysicalDeviceSurfaceSupportKHR) X(vkGetPhysicalDeviceSurfaceCapabilitiesKHR) \
    X(vkGetPhysicalDeviceSurfaceFormatsKHR)
#define MW34_VK_SWAP_FNS(X) X(vkCreateSwapchainKHR) X(vkDestroySwapchainKHR) X(vkGetSwapchainImagesKHR) X(vkAcquireNextImageKHR) X(vkQueuePresentKHR) \
    X(vkCreateSemaphore) X(vkDestroySemaphore) X(vkCmdBlitImage) X(vkCmdClearColorImage)
#define MW34_VK_DEV_FNS(X) X(vkDestroyDevice) X(vkDeviceWaitIdle) X(vkGetDeviceQueue) X(vkCreateBuffer) X(vkDestroyBuffer) X(vkGetBufferMemoryRequirements) \
    X(vkGetImageMemoryRequirements) X(vkAllocateMemory) X(vkFreeMemory) X(vkBindBufferMemory) X(vkBindImageMemory) X(vkMapMemory) X(vkUnmapMemory) \
    X(vkCreateImage) X(vkDestroyImage) X(vkCreateImageView) X(vkDestroyImageView) X(vkCreateSampler) X(vkDestroySampler) X(vkCreateDescriptorSetLayout) \
    X(vkDestroyDescriptorSetLayout) X(vkCreateDescriptorPool) X(vkDestroyDescriptorPool) X(vkResetDescriptorPool) X(vkAllocateDescriptorSets) \
    X(vkUpdateDescriptorSets) X(vkCreateRenderPass) X(vkDestroyRenderPass) X(vkCreateFramebuffer) X(vkDestroyFramebuffer) X(vkCreateShaderModule) \
    X(vkDestroyShaderModule) X(vkCreatePipelineLayout) X(vkDestroyPipelineLayout) X(vkCreateGraphicsPipelines) X(vkDestroyPipeline) X(vkCreateCommandPool) \
    X(vkDestroyCommandPool) X(vkResetCommandPool) X(vkAllocateCommandBuffers) X(vkBeginCommandBuffer) X(vkEndCommandBuffer) X(vkCmdPipelineBarrier) \
    X(vkCmdCopyBuffer) X(vkCmdCopyBufferToImage) X(vkCmdCopyImageToBuffer) X(vkCmdBeginRenderPass) X(vkCmdEndRenderPass) X(vkCmdBindPipeline) X(vkCmdBindDescriptorSets) \
    X(vkCmdPushConstants) X(vkCmdDraw) X(vkCmdClearAttachments) X(vkCmdBindVertexBuffers) X(vkCmdSetViewport) X(vkCmdSetScissor) X(vkCreateFence) \
    X(vkDestroyFence) X(vkResetFences) X(vkQueueSubmit) X(vkWaitForFences)
#define MW34_VK_DECL(n) PFN_##n n{};
        MW34_VK_FNS(MW34_VK_DECL) MW34_VK_DEV_FNS(MW34_VK_DECL) MW34_VK_WSI_FNS(MW34_VK_DECL) MW34_VK_SWAP_FNS(MW34_VK_DECL)
    } f;
    struct Buffer { VkBuffer buffer{}; VkDeviceMemory memory{}; VkDeviceSize size{}; void *mapped{}; };
    struct Image { VkImage image{}; VkDeviceMemory memory{}; VkImageView view{}; };
    struct Tex { VkImage image{}; VkDeviceMemory memory{}; VkImageView view{}; unsigned width{}, height{},levels{1}; std::uint64_t hash{}; bool valid{}; };
    void *library{};
    VkInstance instance{};
    VkPhysicalDevice gpu{};
    VkPhysicalDeviceMemoryProperties memory{};
    VkDevice device{};
    VkQueue queue{};
    unsigned family{}, width{}, height{}, descriptorCapacity{};
    bool rgba{};
    Buffer upload, readback, vertexBuffer, texUpload;
    struct ModelBuffer { Buffer local,staging;std::uint64_t hash{};unsigned count{};bool uploaded{}; };
    std::map<std::uint64_t,ModelBuffer> model_buffers;
    Image colorImage, depthImage;
    Image qualitySource;
    VkDescriptorPool qualityPool{};
    VkDescriptorSet qualitySet{};
    VkPipelineLayout qualityLayout{};
    VkPipeline qualityPipeline{};
    VkShaderModule qualityVert{},qualityFrag{};
    bool quality_world_dirty{};
    // Render scale (lazy residency on the presenter device): the target images are rw x rh = round(width/height * scale);
    // guest-resolution staging images (colorLo/depthLo) carry uploads and copy-backs through blits. scale_req is set by
    // the provider before a scene; it applies when the target is (re)created.
    Image colorLo, depthLo;
    float scale = 1.f, scale_req = 1.f,scale_x=1.f;
    bool target_frontend{};
    unsigned rw{}, rh{};
    Tex white;
    std::map<std::uint64_t, Tex> textures;
    std::map<std::uint64_t, VkPipeline> pipelines;
    std::map<unsigned, VkSampler> samplers;
    VkRenderPass renderPass{};
    VkFramebuffer framebuffer{};
    VkDescriptorSetLayout setLayout{};
    VkDescriptorPool descriptorPool{};
    VkPipelineLayout pipelineLayout{},modelLayout{};
    VkShaderModule vert{}, frag{},modelVert{};
    VkCommandPool commandPool{};
    VkCommandBuffer cmd{};
    VkFence fence{};
    // presentation
    bool presentable{};
    HWND presentWindow{}, presentParent{}, child{};
    VkSurfaceKHR windowSurface{};
    VkSwapchainKHR swapchain{};
    std::vector<VkImage> swapImages;
    // A render-finished semaphore is reusable only after its own image has been
    // acquired again; a render fence alone does not complete presentation waits.
    std::vector<VkSemaphore> swapRendered;
    VkExtent2D swapExtent{};
    VkSemaphore acquired{};
    VkCommandPool presentPool{};
    VkCommandBuffer presentCmd{};
    VkFence presentFence{};
    Image srcImage;
    unsigned srcWidth{}, srcHeight{};
    Buffer presentUpload;

    static void check(VkResult r, const char *what) { if (r != VK_SUCCESS) throw std::runtime_error(std::string("Vulkan scene renderer: ") + what + " failed (" + std::to_string(int(r)) + ")"); }
    void init(HWND forPresent = nullptr) {
        library = ::LoadLibraryExW(L"vulkan-1.dll", nullptr, LOAD_LIBRARY_SEARCH_SYSTEM32);
        if (!library) throw std::runtime_error("Vulkan scene renderer: system Vulkan loader unavailable");
        auto get = reinterpret_cast<PFN_vkGetInstanceProcAddr>(::GetProcAddress(static_cast<HMODULE>(library), "vkGetInstanceProcAddr"));
        if (!get) throw std::runtime_error("Vulkan scene renderer: vkGetInstanceProcAddr unavailable");
        auto createInstance = reinterpret_cast<PFN_vkCreateInstance>(get(nullptr, "vkCreateInstance"));
        VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};
        app.pApplicationName = "MW34 Direct3D scene renderer"; app.apiVersion = VK_API_VERSION_1_0;
        VkInstanceCreateInfo ici{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO};
        ici.pApplicationInfo = &app;
        const char *layer = "VK_LAYER_KHRONOS_validation";
        const char *v = std::getenv("MW34_VK_VALIDATION");
        if (v && *v == '1') { ici.enabledLayerCount = 1; ici.ppEnabledLayerNames = &layer; }
        std::vector<const char *> instanceExtensions;
        {
            auto enumerate = reinterpret_cast<PFN_vkEnumerateInstanceExtensionProperties>(get(nullptr, "vkEnumerateInstanceExtensionProperties"));
            unsigned n = 0;
            std::vector<VkExtensionProperties> props;
            if (enumerate && enumerate(nullptr, &n, nullptr) == VK_SUCCESS) { props.resize(n); enumerate(nullptr, &n, props.data()); }
            auto has = [&](const char *e) { for (const auto &p : props) if (!std::strcmp(p.extensionName, e)) return true; return false; };
            if (has(VK_KHR_SURFACE_EXTENSION_NAME) && has(VK_KHR_WIN32_SURFACE_EXTENSION_NAME)) instanceExtensions = {VK_KHR_SURFACE_EXTENSION_NAME, VK_KHR_WIN32_SURFACE_EXTENSION_NAME};
        }
        ici.enabledExtensionCount = unsigned(instanceExtensions.size()); ici.ppEnabledExtensionNames = instanceExtensions.data();
        check(createInstance(&ici, nullptr, &instance), "create instance");
#define MW34_VK_LOAD(n) f.n = reinterpret_cast<PFN_##n>(get(instance, #n)); if (!f.n) throw std::runtime_error("Vulkan scene renderer: " #n " missing");
        MW34_VK_FNS(MW34_VK_LOAD)
#define MW34_VK_OPT(n) f.n = reinterpret_cast<PFN_##n>(get(instance, #n));
        if (!instanceExtensions.empty()) { MW34_VK_WSI_FNS(MW34_VK_OPT) }
        VkSurfaceKHR probe{};
        if (forPresent && !instanceExtensions.empty() && f.vkCreateWin32SurfaceKHR) {
            VkWin32SurfaceCreateInfoKHR ci{VK_STRUCTURE_TYPE_WIN32_SURFACE_CREATE_INFO_KHR};
            ci.hinstance = ::GetModuleHandleW(nullptr); ci.hwnd = forPresent;
            if (f.vkCreateWin32SurfaceKHR(instance, &ci, nullptr, &probe) != VK_SUCCESS) probe = {};
        }
        unsigned count = 0;
        check(f.vkEnumeratePhysicalDevices(instance, &count, nullptr), "enumerate devices");
        std::vector<VkPhysicalDevice> gpus(count);
        check(f.vkEnumeratePhysicalDevices(instance, &count, gpus.data()), "enumerate devices");
        // Prefer a discrete GPU with a graphics queue, then any device with one.
        int best = -1;
        for (auto g : gpus) {
            unsigned n = 0;
            f.vkGetPhysicalDeviceQueueFamilyProperties(g, &n, nullptr);
            std::vector<VkQueueFamilyProperties> q(n);
            f.vkGetPhysicalDeviceQueueFamilyProperties(g, &n, q.data());
            VkPhysicalDeviceProperties p{};
            f.vkGetPhysicalDeviceProperties(g, &p);
            for (unsigned i = 0; i < n; ++i)
                if (q[i].queueCount && (q[i].queueFlags & VK_QUEUE_GRAPHICS_BIT)) {
                    if (forPresent) {
                        VkBool32 ok = VK_FALSE;
                        VkSurfaceCapabilitiesKHR c{};
                        if (!probe || f.vkGetPhysicalDeviceSurfaceSupportKHR(g, i, probe, &ok) != VK_SUCCESS || !ok ||
                            f.vkGetPhysicalDeviceSurfaceCapabilitiesKHR(g, probe, &c) != VK_SUCCESS) continue;
                    }
                    const int score = p.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU ? 2 : 1;
                    if (score > best) { best = score; gpu = g; family = i; device_name = p.deviceName; }
                    break;
                }
        }
        if (!gpu && forPresent) { if (probe) f.vkDestroySurfaceKHR(instance, probe, nullptr); presentable = false; return; }
        if (!gpu) throw std::runtime_error("Vulkan scene renderer: no graphics device");
        f.vkGetPhysicalDeviceMemoryProperties(gpu, &memory);
        VkFormatProperties cp{};
        f.vkGetPhysicalDeviceFormatProperties(gpu, VK_FORMAT_R5G6B5_UNORM_PACK16, &cp);
        const VkFormatFeatureFlags need = VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BIT | VK_FORMAT_FEATURE_COLOR_ATTACHMENT_BLEND_BIT;
        rgba = (cp.optimalTilingFeatures & need) != need;
        float priority = 1;
        VkDeviceQueueCreateInfo q{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
        q.queueFamilyIndex = family; q.queueCount = 1; q.pQueuePriorities = &priority;
        VkDeviceCreateInfo dci{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
        dci.queueCreateInfoCount = 1; dci.pQueueCreateInfos = &q;
        VkPhysicalDeviceFeatures enabled{};
        if(anisotropy()>1){VkPhysicalDeviceFeatures supported{};f.vkGetPhysicalDeviceFeatures(gpu,&supported);VkPhysicalDeviceProperties props{};f.vkGetPhysicalDeviceProperties(gpu,&props);
            if(!supported.samplerAnisotropy||props.limits.maxSamplerAnisotropy<float(anisotropy()))throw std::runtime_error("GPU does not support the requested anisotropic filtering level");
            VkFormatProperties tex{};f.vkGetPhysicalDeviceFormatProperties(gpu,VK_FORMAT_R8G8B8A8_UNORM,&tex);const auto bits=VK_FORMAT_FEATURE_BLIT_SRC_BIT|VK_FORMAT_FEATURE_BLIT_DST_BIT|VK_FORMAT_FEATURE_SAMPLED_IMAGE_FILTER_LINEAR_BIT;
            if((tex.optimalTilingFeatures&bits)!=bits)throw std::runtime_error("GPU cannot generate the RGBA8 mip chain required for AF");enabled.samplerAnisotropy=VK_TRUE;dci.pEnabledFeatures=&enabled;}
        if(fxaa_enabled()){VkFormatProperties src{},dst{};f.vkGetPhysicalDeviceFormatProperties(gpu,rgba?VK_FORMAT_R8G8B8A8_UNORM:VK_FORMAT_R5G6B5_UNORM_PACK16,&src);f.vkGetPhysicalDeviceFormatProperties(gpu,VK_FORMAT_R8G8B8A8_UNORM,&dst);
            if(!(src.optimalTilingFeatures&VK_FORMAT_FEATURE_BLIT_SRC_BIT)||(dst.optimalTilingFeatures&(VK_FORMAT_FEATURE_BLIT_DST_BIT|VK_FORMAT_FEATURE_SAMPLED_IMAGE_FILTER_LINEAR_BIT))!=(VK_FORMAT_FEATURE_BLIT_DST_BIT|VK_FORMAT_FEATURE_SAMPLED_IMAGE_FILTER_LINEAR_BIT))throw std::runtime_error("GPU cannot provide the FXAA color-copy/sampling contract");}
        const char *swapExt = VK_KHR_SWAPCHAIN_EXTENSION_NAME;
        {
            unsigned n = 0;
            std::vector<VkExtensionProperties> props;
            if (f.vkEnumerateDeviceExtensionProperties(gpu, nullptr, &n, nullptr) == VK_SUCCESS) { props.resize(n); f.vkEnumerateDeviceExtensionProperties(gpu, nullptr, &n, props.data()); }
            for (const auto &p : props) if (!std::strcmp(p.extensionName, swapExt)) presentable = !instanceExtensions.empty() && f.vkCreateWin32SurfaceKHR;
        }
        if (presentable) { dci.enabledExtensionCount = 1; dci.ppEnabledExtensionNames = &swapExt; }
        check(f.vkCreateDevice(gpu, &dci, nullptr, &device), "create device");
#define MW34_VK_DLOAD(n) f.n = reinterpret_cast<PFN_##n>(f.vkGetDeviceProcAddr(device, #n)); if (!f.n) throw std::runtime_error("Vulkan scene renderer: " #n " missing");
        MW34_VK_DEV_FNS(MW34_VK_DLOAD)
        // Blits are core rendering commands too (mips, FXAA and scaled targets),
        // even when this device does not have a window surface.
        f.vkCmdBlitImage=reinterpret_cast<PFN_vkCmdBlitImage>(f.vkGetDeviceProcAddr(device,"vkCmdBlitImage"));if(!f.vkCmdBlitImage)throw std::runtime_error("Vulkan image blits unavailable");
        if (presentable) {
            MW34_VK_SWAP_FNS(MW34_VK_DLOAD)
            VkSemaphoreCreateInfo sci{VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO};
            check(f.vkCreateSemaphore(device, &sci, nullptr, &acquired), "semaphore");
            VkCommandPoolCreateInfo ppi{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
            ppi.queueFamilyIndex = family;
            check(f.vkCreateCommandPool(device, &ppi, nullptr, &presentPool), "present command pool");
            VkCommandBufferAllocateInfo pai{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
            pai.commandPool = presentPool; pai.commandBufferCount = 1;
            check(f.vkAllocateCommandBuffers(device, &pai, &presentCmd), "present command buffer");
            VkFenceCreateInfo pfi{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
            check(f.vkCreateFence(device, &pfi, nullptr, &presentFence), "present fence");
        }
        f.vkGetDeviceQueue(device, family, 0, &queue);
        if (probe) { if (presentable) { windowSurface = probe; presentWindow = forPresent; } else f.vkDestroySurfaceKHR(instance, probe, nullptr); }
        VkCommandPoolCreateInfo cpi{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
        cpi.queueFamilyIndex = family;
        check(f.vkCreateCommandPool(device, &cpi, nullptr, &commandPool), "command pool");
        VkCommandBufferAllocateInfo cai{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
        cai.commandPool = commandPool; cai.commandBufferCount = 1;
        check(f.vkAllocateCommandBuffers(device, &cai, &cmd), "command buffer");
        VkFenceCreateInfo fci{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO};
        check(f.vkCreateFence(device, &fci, nullptr, &fence), "fence");
        VkDescriptorSetLayoutBinding b{0, VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 1, VK_SHADER_STAGE_FRAGMENT_BIT, nullptr};
        VkDescriptorSetLayoutCreateInfo li{VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO};
        li.bindingCount = 1; li.pBindings = &b;
        check(f.vkCreateDescriptorSetLayout(device, &li, nullptr, &setLayout), "descriptor set layout");
        VkPushConstantRange pr{VK_SHADER_STAGE_VERTEX_BIT | VK_SHADER_STAGE_FRAGMENT_BIT, 0, sizeof(Push)};
        VkPipelineLayoutCreateInfo pli{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
        pli.setLayoutCount = 1; pli.pSetLayouts = &setLayout; pli.pushConstantRangeCount = 1; pli.pPushConstantRanges = &pr;
        check(f.vkCreatePipelineLayout(device, &pli, nullptr, &pipelineLayout), "pipeline layout");
        if(gpu_models()){VkPhysicalDeviceProperties p{};f.vkGetPhysicalDeviceProperties(gpu,&p);if(p.limits.maxPushConstantsSize<sizeof(ModelPush)||p.limits.maxVertexInputAttributes<3||p.limits.maxVertexInputBindingStride<sizeof(ModelVertex))throw std::runtime_error("GPU cannot provide the model vertex/push contract");
            VkPushConstantRange mr{VK_SHADER_STAGE_VERTEX_BIT|VK_SHADER_STAGE_FRAGMENT_BIT,0,sizeof(ModelPush)};pli.pPushConstantRanges=&mr;
            check(f.vkCreatePipelineLayout(device,&pli,nullptr,&modelLayout),"model pipeline layout");}
        auto module = [&](const std::uint32_t *code, size_t bytes) {
            VkShaderModuleCreateInfo mi{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};
            mi.codeSize = bytes; mi.pCode = code;
            VkShaderModule m{};
            check(f.vkCreateShaderModule(device, &mi, nullptr, &m), "shader module");
            return m;
        };
        vert = module(d3d_scene_vert_spv, sizeof(d3d_scene_vert_spv));
        frag = module(d3d_scene_frag_spv, sizeof(d3d_scene_frag_spv));
        if(gpu_models())modelVert=module(model_scene_vert_spv,sizeof(model_scene_vert_spv));
        std::array<VkAttachmentDescription, 2> at{};
        at[0].format = rgba ? VK_FORMAT_R8G8B8A8_UNORM : VK_FORMAT_R5G6B5_UNORM_PACK16;
        at[1].format = VK_FORMAT_D16_UNORM;
        for (auto &a : at) {
            a.samples = VK_SAMPLE_COUNT_1_BIT; a.loadOp = VK_ATTACHMENT_LOAD_OP_LOAD; a.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
            a.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE; a.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
        }
        at[0].initialLayout = at[0].finalLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
        at[1].initialLayout = at[1].finalLayout = VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL;
        VkAttachmentReference cr{0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL}, dr{1, VK_IMAGE_LAYOUT_DEPTH_STENCIL_ATTACHMENT_OPTIMAL};
        VkSubpassDescription sp{};
        sp.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS; sp.colorAttachmentCount = 1; sp.pColorAttachments = &cr; sp.pDepthStencilAttachment = &dr;
        VkRenderPassCreateInfo rpi{VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO};
        rpi.attachmentCount = 2; rpi.pAttachments = at.data(); rpi.subpassCount = 1; rpi.pSubpasses = &sp;
        check(f.vkCreateRenderPass(device, &rpi, nullptr, &renderPass), "render pass");
        if(fxaa_enabled())init_quality();
        if(fxaa_enabled()||anisotropy()>1)std::fprintf(stderr,"Remaster quality: %s, %ux AF, samplerAnisotropy %u, GPU %s\n",fxaa_enabled()?"FXAA (native resolution)":"AA off",anisotropy(),enabled.samplerAnisotropy,device_name.c_str());
        pool(256);
        // 1x1 opaque white texture for draws without a texture (D3DTA_TEXTURE then reads 1.0).
        create(white, 1, 1);
        ensure(texUpload, 4, VK_BUFFER_USAGE_TRANSFER_SRC_BIT);
        const std::uint32_t one = 0xffffffffu;
        std::memcpy(texUpload.mapped, &one, 4);
        check(f.vkResetCommandPool(device, commandPool, 0), "reset command pool");
        VkCommandBufferBeginInfo bi{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
        check(f.vkBeginCommandBuffer(cmd, &bi), "begin");
        barrier(white.image, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 0, VK_ACCESS_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
        copyIn(texUpload.buffer, 0, white.image, 1, 1, VK_IMAGE_ASPECT_COLOR_BIT);
        barrier(white.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL, VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_FRAGMENT_SHADER_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
        check(f.vkEndCommandBuffer(cmd), "end");
        VkSubmitInfo si{VK_STRUCTURE_TYPE_SUBMIT_INFO};
        si.commandBufferCount = 1; si.pCommandBuffers = &cmd;
        check(f.vkQueueSubmit(queue, 1, &si, fence), "submit");
        check(f.vkWaitForFences(device, 1, &fence, VK_TRUE, 10000000000ULL), "wait");
        white.valid = true;
    }
    unsigned type(VkMemoryRequirements r, VkMemoryPropertyFlags flags) {
        for (unsigned i = 0; i < memory.memoryTypeCount; ++i)
            if ((r.memoryTypeBits & (1U << i)) && (memory.memoryTypes[i].propertyFlags & flags) == flags) return i;
        throw std::runtime_error("Vulkan scene renderer: required memory type unavailable");
    }
    bool has_type(VkMemoryRequirements r, VkMemoryPropertyFlags flags) const {
        for (unsigned i = 0; i < memory.memoryTypeCount; ++i)
            if ((r.memoryTypeBits & (1U << i)) && (memory.memoryTypes[i].propertyFlags & flags) == flags) return true;
        return false;
    }
    void ensure(Buffer &b, VkDeviceSize size, VkBufferUsageFlags usage) {
        if (b.buffer && b.size >= size) return;
        if (b.buffer) { f.vkDestroyBuffer(device, b.buffer, nullptr); f.vkFreeMemory(device, b.memory, nullptr); b = {}; }
        VkBufferCreateInfo bi{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
        bi.size = size; bi.usage = usage;
        check(f.vkCreateBuffer(device, &bi, nullptr, &b.buffer), "buffer");
        VkMemoryRequirements r{};
        f.vkGetBufferMemoryRequirements(device, b.buffer, &r);
        VkMemoryAllocateInfo ai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
        // Readback buffers are read by the CPU every scene: prefer host-cached memory (uncached, write-combined
        // memory makes those reads several times slower). Upload buffers take the first host-visible type.
        const VkMemoryPropertyFlags visible = VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT;
        ai.allocationSize = r.size;
        ai.memoryTypeIndex = (usage & VK_BUFFER_USAGE_TRANSFER_DST_BIT) && has_type(r, visible | VK_MEMORY_PROPERTY_HOST_CACHED_BIT)
            ? type(r, visible | VK_MEMORY_PROPERTY_HOST_CACHED_BIT) : type(r, visible);
        check(f.vkAllocateMemory(device, &ai, nullptr, &b.memory), "buffer memory");
        check(f.vkBindBufferMemory(device, b.buffer, b.memory, 0), "bind buffer");
        check(f.vkMapMemory(device, b.memory, 0, VK_WHOLE_SIZE, 0, &b.mapped), "map buffer");
        b.size = size;
    }
    // A cached immutable device-local model buffer and its one-time upload.
    ModelBuffer&model_buffer(const ModelGeometry&g){if(g.vertices.empty()||g.vertices.size()>65535||g.vertices.size()%3)throw std::runtime_error("GPU model geometry size mismatch");
        auto&b=model_buffers[g.key];if(b.local.buffer){if(b.hash!=g.hash||b.count!=g.vertices.size())throw std::runtime_error("GPU model geometry identity changed");return b;}
        const VkDeviceSize bytes=VkDeviceSize(g.vertices.size())*sizeof(ModelVertex);ensure(b.staging,bytes,VK_BUFFER_USAGE_TRANSFER_SRC_BIT);std::memcpy(b.staging.mapped,g.vertices.data(),size_t(bytes));
        VkBufferCreateInfo ci{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};ci.size=bytes;ci.usage=VK_BUFFER_USAGE_TRANSFER_DST_BIT|VK_BUFFER_USAGE_VERTEX_BUFFER_BIT;
        check(f.vkCreateBuffer(device,&ci,nullptr,&b.local.buffer),"model vertex buffer");VkMemoryRequirements r{};f.vkGetBufferMemoryRequirements(device,b.local.buffer,&r);
        VkMemoryAllocateInfo ai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};ai.allocationSize=r.size;ai.memoryTypeIndex=type(r,VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
        check(f.vkAllocateMemory(device,&ai,nullptr,&b.local.memory),"model vertex memory");check(f.vkBindBufferMemory(device,b.local.buffer,b.local.memory,0),"bind model vertex memory");
        b.local.size=bytes;b.hash=g.hash;b.count=unsigned(g.vertices.size());return b;}
    void image(VkImage &img, VkDeviceMemory &mem, VkImageView &view, unsigned w, unsigned h, VkFormat format, VkImageUsageFlags usage, VkImageAspectFlags aspect,unsigned levels=1) {
        VkImageCreateInfo ii{VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO};
        ii.imageType = VK_IMAGE_TYPE_2D; ii.format = format; ii.extent = {w, h, 1}; ii.mipLevels = levels; ii.arrayLayers = 1;
        ii.samples = VK_SAMPLE_COUNT_1_BIT; ii.tiling = VK_IMAGE_TILING_OPTIMAL; ii.usage = usage;
        check(f.vkCreateImage(device, &ii, nullptr, &img), "image");
        VkMemoryRequirements r{};
        f.vkGetImageMemoryRequirements(device, img, &r);
        VkMemoryAllocateInfo ai{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
        ai.allocationSize = r.size; ai.memoryTypeIndex = type(r, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
        check(f.vkAllocateMemory(device, &ai, nullptr, &mem), "image memory");
        check(f.vkBindImageMemory(device, img, mem, 0), "bind image");
        if(!(usage&(VK_IMAGE_USAGE_SAMPLED_BIT|VK_IMAGE_USAGE_STORAGE_BIT|VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT|VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT|VK_IMAGE_USAGE_INPUT_ATTACHMENT_BIT)))return;
        VkImageViewCreateInfo vi{VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO};
        vi.image = img; vi.viewType = VK_IMAGE_VIEW_TYPE_2D; vi.format = format; vi.subresourceRange = {aspect, 0, levels, 0, 1};
        check(f.vkCreateImageView(device, &vi, nullptr, &view), "image view");
    }
    void create(Tex &t, unsigned w, unsigned h) {
        t.levels=1;if(anisotropy()>1)for(unsigned n=std::max(w,h);n>1;n>>=1)++t.levels;
        image(t.image, t.memory, t.view, w, h, VK_FORMAT_R8G8B8A8_UNORM, VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_SAMPLED_BIT, VK_IMAGE_ASPECT_COLOR_BIT,t.levels);
        t.width = w; t.height = h; t.valid = false; t.hash = 0;
    }
    void destroy(Tex &t) {
        if (t.view) f.vkDestroyImageView(device, t.view, nullptr);
        if (t.image) f.vkDestroyImage(device, t.image, nullptr);
        if (t.memory) f.vkFreeMemory(device, t.memory, nullptr);
        t = {};
    }
    void target(unsigned w, unsigned h, bool frontend) {
        target_frontend=frontend;
        f.vkDeviceWaitIdle(device);
        if (framebuffer) f.vkDestroyFramebuffer(device, framebuffer, nullptr);
        for (Image *i : {&colorImage, &depthImage, &colorLo, &depthLo,&qualitySource}) {
            if (i->view) f.vkDestroyImageView(device, i->view, nullptr);
            if (i->image) f.vkDestroyImage(device, i->image, nullptr);
            if (i->memory) f.vkFreeMemory(device, i->memory, nullptr);
            *i = {};
        }
        scale = scale_req;
        if (scale != 1.f||widescreen()) {  // scaling needs blits of both formats
            VkFormatProperties cp{}, dp{};
            f.vkGetPhysicalDeviceFormatProperties(gpu, rgba ? VK_FORMAT_R8G8B8A8_UNORM : VK_FORMAT_R5G6B5_UNORM_PACK16, &cp);
            f.vkGetPhysicalDeviceFormatProperties(gpu, VK_FORMAT_D16_UNORM, &dp);
            const VkFormatFeatureFlags need = VK_FORMAT_FEATURE_BLIT_SRC_BIT | VK_FORMAT_FEATURE_BLIT_DST_BIT;
            if ((cp.optimalTilingFeatures & need) != need || (dp.optimalTilingFeatures & need) != need){if(remaster_width())throw std::runtime_error("GPU cannot provide the requested native-resolution color/depth blits");scale=1.f;}
        }
        rw = unsigned(std::lround(double(w) * scale)); rh = unsigned(std::lround(double(h) * scale));
        // Guest buffers remain at the selected original resolution. A wider
        // physical world target is paired with the original camera/frustum's
        // explicit Hor+ correction; HUD coordinates are handled separately.
        if(widescreen()){if(target_frontend){const auto fit=mw34::frontend::CanvasFit::fit(w,h,remaster_width(),remaster_height());rw=unsigned(fit.width);rh=unsigned(fit.height);}else{rw=3440;rh=1440;}}
        scale_x=float(rw)/float(w);
        if (rw!=w||rh!=h) {
            image(colorLo.image, colorLo.memory, colorLo.view, w, h, rgba ? VK_FORMAT_R8G8B8A8_UNORM : VK_FORMAT_R5G6B5_UNORM_PACK16,
                  VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
            image(depthLo.image, depthLo.memory, depthLo.view, w, h, VK_FORMAT_D16_UNORM,
                  VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT, VK_IMAGE_ASPECT_DEPTH_BIT);
        }
        image(colorImage.image, colorImage.memory, colorImage.view, rw, rh, rgba ? VK_FORMAT_R8G8B8A8_UNORM : VK_FORMAT_R5G6B5_UNORM_PACK16,
              VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
        image(depthImage.image, depthImage.memory, depthImage.view, rw, rh, VK_FORMAT_D16_UNORM,
              VK_IMAGE_USAGE_DEPTH_STENCIL_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT, VK_IMAGE_ASPECT_DEPTH_BIT);
        const std::array<VkImageView, 2> views{colorImage.view, depthImage.view};
        VkFramebufferCreateInfo fi{VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO};
        fi.renderPass = renderPass; fi.attachmentCount = 2; fi.pAttachments = views.data(); fi.width = rw; fi.height = rh; fi.layers = 1;
        check(f.vkCreateFramebuffer(device, &fi, nullptr, &framebuffer), "framebuffer");
        quality_world_dirty=false;
        if(fxaa_enabled()){
            image(qualitySource.image,qualitySource.memory,qualitySource.view,rw,rh,VK_FORMAT_R8G8B8A8_UNORM,VK_IMAGE_USAGE_TRANSFER_DST_BIT|VK_IMAGE_USAGE_SAMPLED_BIT,VK_IMAGE_ASPECT_COLOR_BIT);
            VkDescriptorImageInfo info{sampler(3U|(3U<<4)|(3U<<8)),qualitySource.view,VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
            VkWriteDescriptorSet wr{VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET};wr.dstSet=qualitySet;wr.descriptorCount=1;wr.descriptorType=VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;wr.pImageInfo=&info;
            f.vkUpdateDescriptorSets(device,1,&wr,0,nullptr);}
        width = w; height = h;
    }
    void pool(unsigned n) {
        if (descriptorPool) f.vkDestroyDescriptorPool(device, descriptorPool, nullptr);
        VkDescriptorPoolSize ps{VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, n};
        VkDescriptorPoolCreateInfo pi{VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO};
        pi.maxSets = n; pi.poolSizeCount = 1; pi.pPoolSizes = &ps;
        check(f.vkCreateDescriptorPool(device, &pi, nullptr, &descriptorPool), "descriptor pool");
        descriptorCapacity = n;
    }
    // Sampler key: bit 0 magnification linear, bit 1 minification linear, bits 4..7 U address, 8..11 V address
    // (D3DTADDRESS: 1 wrap, 2 mirror, 3 clamp). Bit16 tags world draws for AF;
    // HUD, text and the FXAA input use their own level-zero sampling unchanged.
    VkSampler sampler(unsigned key) {
        auto it = samplers.find(key);
        if (it != samplers.end()) return it->second;
        auto mode = [](unsigned a) { return a == 2 ? VK_SAMPLER_ADDRESS_MODE_MIRRORED_REPEAT : a == 3 ? VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE : VK_SAMPLER_ADDRESS_MODE_REPEAT; };
        VkSamplerCreateInfo si{VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO};
        si.magFilter = (key & 1) ? VK_FILTER_LINEAR : VK_FILTER_NEAREST;
        si.minFilter = (key & 2) ? VK_FILTER_LINEAR : VK_FILTER_NEAREST;
        si.mipmapMode = VK_SAMPLER_MIPMAP_MODE_NEAREST;
        si.addressModeU = mode((key >> 4) & 15); si.addressModeV = mode((key >> 8) & 15); si.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
        if((key&0x10000U)&&anisotropy()>1){si.magFilter=si.minFilter=VK_FILTER_LINEAR;si.mipmapMode=VK_SAMPLER_MIPMAP_MODE_LINEAR;
            si.anisotropyEnable=VK_TRUE;si.maxAnisotropy=float(anisotropy());si.maxLod=VK_LOD_CLAMP_NONE;++af_samplers;}
        VkSampler s{};
        check(f.vkCreateSampler(device, &si, nullptr, &s), "sampler");
        return samplers[key] = s;
    }
    VkPipeline pipeline(const PipelineKey &k,bool model=false) {
        // points uses bit56 (0/1); bit57 distinguishes this private model pipeline.
        const std::uint64_t key=k.packed()|(model?(1ULL<<57):0ULL);
        auto it = pipelines.find(key);
        if (it != pipelines.end()) return it->second;
        std::array<VkPipelineShaderStageCreateInfo, 2> st{};
        for (int i = 0; i < 2; ++i) {
            st[i].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
            st[i].stage = i ? VK_SHADER_STAGE_FRAGMENT_BIT : VK_SHADER_STAGE_VERTEX_BIT;
            st[i].module = i ? frag : (model?modelVert:vert); st[i].pName = "main";
        }
        VkVertexInputBindingDescription vb{0, 32, VK_VERTEX_INPUT_RATE_VERTEX};
        const std::array<VkVertexInputAttributeDescription, 4> va{{{0, 0, VK_FORMAT_R32G32B32A32_SFLOAT, 0}, {1, 0, VK_FORMAT_R32_UINT, 16},
                                                                  {2, 0, VK_FORMAT_R32_UINT, 20}, {3, 0, VK_FORMAT_R32G32_SFLOAT, 24}}};
        VkPipelineVertexInputStateCreateInfo vi{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};
        const std::array<VkVertexInputAttributeDescription,3> ma{{{0,0,VK_FORMAT_R32G32B32_SFLOAT,0},{1,0,VK_FORMAT_R32G32B32_SFLOAT,12},{2,0,VK_FORMAT_R32G32_SFLOAT,24}}};
        vi.vertexBindingDescriptionCount = 1; vi.pVertexBindingDescriptions = &vb; vi.vertexAttributeDescriptionCount = model?3:4; vi.pVertexAttributeDescriptions = model?ma.data():va.data();
        VkPipelineInputAssemblyStateCreateInfo ia{VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO};
        ia.topology = k.points ? VK_PRIMITIVE_TOPOLOGY_POINT_LIST : VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
        VkPipelineViewportStateCreateInfo vps{VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};
        vps.viewportCount = 1; vps.scissorCount = 1;
        VkPipelineRasterizationStateCreateInfo rs{VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};
        rs.polygonMode = VK_POLYGON_MODE_FILL; rs.lineWidth = 1;
        // D3DCULL_CW culls clockwise screen-space triangles, D3DCULL_CCW counter-clockwise ones (y down in both APIs).
        rs.cullMode = k.cull == 1 ? VK_CULL_MODE_NONE : VK_CULL_MODE_BACK_BIT;
        rs.frontFace = k.cull == 3 ? VK_FRONT_FACE_CLOCKWISE : VK_FRONT_FACE_COUNTER_CLOCKWISE;
        VkPipelineMultisampleStateCreateInfo ms{VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};
        ms.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;
        VkPipelineDepthStencilStateCreateInfo ds{VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO};
        ds.depthTestEnable = k.zenable; ds.depthWriteEnable = k.zenable && k.zwrite; ds.depthCompareOp = VkCompareOp(k.zfunc - 1);
        auto factor = [](unsigned b) {
            static const VkBlendFactor t[] = {VK_BLEND_FACTOR_ZERO, VK_BLEND_FACTOR_ZERO, VK_BLEND_FACTOR_ONE, VK_BLEND_FACTOR_SRC_COLOR, VK_BLEND_FACTOR_ONE_MINUS_SRC_COLOR,
                                              VK_BLEND_FACTOR_SRC_ALPHA, VK_BLEND_FACTOR_ONE_MINUS_SRC_ALPHA, VK_BLEND_FACTOR_DST_ALPHA, VK_BLEND_FACTOR_ONE_MINUS_DST_ALPHA,
                                              VK_BLEND_FACTOR_DST_COLOR, VK_BLEND_FACTOR_ONE_MINUS_DST_COLOR, VK_BLEND_FACTOR_SRC_ALPHA_SATURATE};
            return t[b];
        };
        VkPipelineColorBlendAttachmentState cb{};
        cb.colorWriteMask = 15; cb.blendEnable = k.blend;
        unsigned src = k.src, dst = k.dst;
        if (src == 12) { src = 5; dst = 6; } else if (src == 13) { src = 6; dst = 5; }  // D3DBLEND_BOTHSRCALPHA / BOTHINVSRCALPHA
        cb.srcColorBlendFactor = cb.srcAlphaBlendFactor = factor(src);
        cb.dstColorBlendFactor = cb.dstAlphaBlendFactor = factor(dst);
        VkPipelineColorBlendStateCreateInfo bs{VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};
        bs.attachmentCount = 1; bs.pAttachments = &cb;
        const std::array<VkDynamicState, 2> dyn{VK_DYNAMIC_STATE_VIEWPORT, VK_DYNAMIC_STATE_SCISSOR};
        VkPipelineDynamicStateCreateInfo dy{VK_STRUCTURE_TYPE_PIPELINE_DYNAMIC_STATE_CREATE_INFO};
        dy.dynamicStateCount = 2; dy.pDynamicStates = dyn.data();
        VkGraphicsPipelineCreateInfo pi{VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO};
        pi.stageCount = 2; pi.pStages = st.data(); pi.pVertexInputState = &vi; pi.pInputAssemblyState = &ia; pi.pViewportState = &vps;
        pi.pRasterizationState = &rs; pi.pMultisampleState = &ms; pi.pDepthStencilState = &ds; pi.pColorBlendState = &bs; pi.pDynamicState = &dy;
        pi.layout = model?modelLayout:pipelineLayout; pi.renderPass = renderPass;
        VkPipeline p{};
        check(f.vkCreateGraphicsPipelines(device, VK_NULL_HANDLE, 1, &pi, nullptr, &p), "graphics pipeline");
        return pipelines[key] = p;
    }
    void barrier(VkImage img, VkImageLayout from, VkImageLayout to, VkAccessFlags src, VkAccessFlags dst, VkPipelineStageFlags ss, VkPipelineStageFlags ds, VkImageAspectFlags aspect,unsigned base=0,unsigned levels=1) {
        VkImageMemoryBarrier b{VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER};
        b.srcAccessMask = src; b.dstAccessMask = dst; b.oldLayout = from; b.newLayout = to;
        b.srcQueueFamilyIndex = b.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED; b.image = img; b.subresourceRange = {aspect, base, levels, 0, 1};
        f.vkCmdPipelineBarrier(cmd, ss, ds, 0, 0, nullptr, 0, nullptr, 1, &b);
    }
    VkRect2D scaled(const VkRect2D &r) const {
        if (scale == 1.f&&scale_x==1.f) return r;
        const int x0 = int(std::lround(r.offset.x * double(scale_x))), y0 = int(std::lround(r.offset.y * double(scale)));
        const int x1 = int(std::lround((r.offset.x + int(r.extent.width)) * double(scale_x))), y1 = int(std::lround((r.offset.y + int(r.extent.height)) * double(scale)));
        return {{x0, y0}, {unsigned(std::max(x1 - x0, 0)), unsigned(std::max(y1 - y0, 0))}};
    }
    void blit_img(VkImage src, unsigned sw, unsigned sh, VkImage dst, unsigned dw, unsigned dh, VkImageAspectFlags aspect, VkFilter filter) {
        VkImageBlit b{};
        b.srcSubresource = b.dstSubresource = {aspect, 0, 0, 1};
        b.srcOffsets[1] = {int(sw), int(sh), 1}; b.dstOffsets[1] = {int(dw), int(dh), 1};
        f.vkCmdBlitImage(cmd, src, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, dst, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &b, filter);
    }
    // Guest-resolution upload into the target images (which are in transfer-destination layout).
    void copy_in_scaled(VkDeviceSize colorBytes) {
        if (rw==width&&rh==height) {
            copyIn(upload.buffer, 0, colorImage.image, width, height, VK_IMAGE_ASPECT_COLOR_BIT);
            copyIn(upload.buffer, colorBytes, depthImage.image, width, height, VK_IMAGE_ASPECT_DEPTH_BIT);
            return;
        }
        for (auto [img, aspect] : {std::pair{colorLo.image, VkImageAspectFlags(VK_IMAGE_ASPECT_COLOR_BIT)}, {depthLo.image, VkImageAspectFlags(VK_IMAGE_ASPECT_DEPTH_BIT)}})
            barrier(img, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 0, VK_ACCESS_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, aspect);
        copyIn(upload.buffer, 0, colorLo.image, width, height, VK_IMAGE_ASPECT_COLOR_BIT);
        copyIn(upload.buffer, colorBytes, depthLo.image, width, height, VK_IMAGE_ASPECT_DEPTH_BIT);
        for (auto [img, aspect] : {std::pair{colorLo.image, VkImageAspectFlags(VK_IMAGE_ASPECT_COLOR_BIT)}, {depthLo.image, VkImageAspectFlags(VK_IMAGE_ASPECT_DEPTH_BIT)}})
            barrier(img, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, aspect);
        blit_img(colorLo.image, width, height, colorImage.image, rw, rh, VK_IMAGE_ASPECT_COLOR_BIT, VK_FILTER_NEAREST);
        blit_img(depthLo.image, width, height, depthImage.image, rw, rh, VK_IMAGE_ASPECT_DEPTH_BIT, VK_FILTER_NEAREST);
    }
    // Guest-resolution copy of the target images (which are in transfer-source layout) into the readback buffer.
    void copy_out_scaled(VkDeviceSize colorBytes) {
        if (rw==width&&rh==height) {
            copyOut(colorImage.image, readback.buffer, 0, VK_IMAGE_ASPECT_COLOR_BIT);
            copyOut(depthImage.image, readback.buffer, colorBytes, VK_IMAGE_ASPECT_DEPTH_BIT);
            return;
        }
        for (auto [img, aspect] : {std::pair{colorLo.image, VkImageAspectFlags(VK_IMAGE_ASPECT_COLOR_BIT)}, {depthLo.image, VkImageAspectFlags(VK_IMAGE_ASPECT_DEPTH_BIT)}})
            barrier(img, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 0, VK_ACCESS_TRANSFER_WRITE_BIT, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, aspect);
        blit_img(colorImage.image, rw, rh, colorLo.image, width, height, VK_IMAGE_ASPECT_COLOR_BIT, VK_FILTER_LINEAR);
        blit_img(depthImage.image, rw, rh, depthLo.image, width, height, VK_IMAGE_ASPECT_DEPTH_BIT, VK_FILTER_NEAREST);
        for (auto [img, aspect] : {std::pair{colorLo.image, VkImageAspectFlags(VK_IMAGE_ASPECT_COLOR_BIT)}, {depthLo.image, VkImageAspectFlags(VK_IMAGE_ASPECT_DEPTH_BIT)}})
            barrier(img, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, aspect);
        copyOut(colorLo.image, readback.buffer, 0, VK_IMAGE_ASPECT_COLOR_BIT);
        copyOut(depthLo.image, readback.buffer, colorBytes, VK_IMAGE_ASPECT_DEPTH_BIT);
    }
    void copyIn(VkBuffer buf, VkDeviceSize off, VkImage img, unsigned w, unsigned h, VkImageAspectFlags aspect) {
        VkBufferImageCopy c{};
        c.bufferOffset = off; c.imageSubresource = {aspect, 0, 0, 1}; c.imageExtent = {w, h, 1};
        f.vkCmdCopyBufferToImage(cmd, buf, img, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &c);
    }
    void copyOut(VkImage img, VkBuffer buf, VkDeviceSize off, VkImageAspectFlags aspect) {
        VkBufferImageCopy c{};
        c.bufferOffset = off; c.imageSubresource = {aspect, 0, 0, 1}; c.imageExtent = {width, height, 1};
        f.vkCmdCopyImageToBuffer(cmd, img, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, buf, 1, &c);
    }
    static LRESULT CALLBACK childProc(HWND h, UINT m, WPARAM w, LPARAM l) {
        if (m == WM_NCHITTEST) return HTTRANSPARENT;
        if (m == WM_ERASEBKGND) return 1;
        return ::DefWindowProcW(h, m, w, l);
    }
    static HWND makeChild(HWND parent) {
        static const ATOM cls = [] {
            WNDCLASSW wc{};
            wc.lpfnWndProc = childProc; wc.hInstance = ::GetModuleHandleW(nullptr); wc.lpszClassName = L"MW34VulkanPresent";
            return ::RegisterClassW(&wc);
        }();
        if (!cls) return nullptr;
        RECT rc{}; ::GetClientRect(parent, &rc);
        return ::CreateWindowExW(WS_EX_NOPARENTNOTIFY, L"MW34VulkanPresent", L"", WS_CHILD | WS_VISIBLE | WS_DISABLED | WS_CLIPSIBLINGS,
                                 0, 0, rc.right, rc.bottom, parent, nullptr, ::GetModuleHandleW(nullptr), nullptr);
    }
    bool surface(HWND hwnd) {
        VkWin32SurfaceCreateInfoKHR ci{VK_STRUCTURE_TYPE_WIN32_SURFACE_CREATE_INFO_KHR};
        ci.hinstance = ::GetModuleHandleW(nullptr); ci.hwnd = hwnd;
        check(f.vkCreateWin32SurfaceKHR(instance, &ci, nullptr, &windowSurface), "window surface");
        VkBool32 ok = VK_FALSE;
        check(f.vkGetPhysicalDeviceSurfaceSupportKHR(gpu, family, windowSurface, &ok), "surface support");
        if (!ok) { dropSurface(); return false; }
        presentWindow = hwnd;
        return true;
    }
    void dropSurface() { if (windowSurface) f.vkDestroySurfaceKHR(instance, windowSurface, nullptr); windowSurface = {}; presentWindow = {}; }
    void dropSwapchain() {
        if (!swapchain) return;
        f.vkDeviceWaitIdle(device);
        f.vkDestroySwapchainKHR(device, swapchain, nullptr);
        for(auto sem:swapRendered)f.vkDestroySemaphore(device,sem,nullptr);swapRendered.clear();
        swapchain = {}; swapImages.clear();
    }
    bool swapchainReady() {
        VkSurfaceCapabilitiesKHR caps{};
        if (const VkResult r = f.vkGetPhysicalDeviceSurfaceCapabilitiesKHR(gpu, windowSurface, &caps); r != VK_SUCCESS) {
            RECT rc{}; ::GetClientRect(presentWindow, &rc);
            throw std::runtime_error("Vulkan presenter: surface capabilities failed (" + std::to_string(int(r)) + ") for window " +
                std::to_string(reinterpret_cast<std::uintptr_t>(presentWindow)) + " valid " + std::to_string(::IsWindow(presentWindow)) + " visible " +
                std::to_string(::IsWindowVisible(presentWindow)) + " client " + std::to_string(rc.right) + "x" + std::to_string(rc.bottom) + " style " +
                std::to_string(::GetWindowLongW(presentWindow, GWL_STYLE)) + " exstyle " + std::to_string(::GetWindowLongW(presentWindow, GWL_EXSTYLE)));
        }
        VkExtent2D e = caps.currentExtent;
        if (e.width == 0xffffffffu) { RECT rc{}; ::GetClientRect(presentWindow, &rc); e = {unsigned(rc.right), unsigned(rc.bottom)}; }
        if (!e.width || !e.height) return false;
        if (swapchain && e.width == swapExtent.width && e.height == swapExtent.height) return true;
        dropSwapchain();
        if (!(caps.supportedUsageFlags & VK_IMAGE_USAGE_TRANSFER_DST_BIT)) throw std::runtime_error("Vulkan presenter: swapchain images cannot be transfer destinations");
        unsigned n = 0;
        check(f.vkGetPhysicalDeviceSurfaceFormatsKHR(gpu, windowSurface, &n, nullptr), "surface formats");
        std::vector<VkSurfaceFormatKHR> formats(n);
        check(f.vkGetPhysicalDeviceSurfaceFormatsKHR(gpu, windowSurface, &n, formats.data()), "surface formats");
        VkSurfaceFormatKHR fmt = formats.at(0);
        for (const auto &x : formats) if (x.format == VK_FORMAT_B8G8R8A8_UNORM) fmt = x;
        VkSwapchainCreateInfoKHR sc{VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR};
        sc.surface = windowSurface;
        sc.minImageCount = std::max(caps.minImageCount, 2u);
        if (caps.maxImageCount) sc.minImageCount = std::min(sc.minImageCount, caps.maxImageCount);
        sc.imageFormat = fmt.format; sc.imageColorSpace = fmt.colorSpace; sc.imageExtent = e; sc.imageArrayLayers = 1;
        sc.imageUsage = VK_IMAGE_USAGE_TRANSFER_DST_BIT; sc.imageSharingMode = VK_SHARING_MODE_EXCLUSIVE;
        sc.preTransform = caps.currentTransform;
        sc.compositeAlpha = (caps.supportedCompositeAlpha & VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR) ? VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR : VkCompositeAlphaFlagBitsKHR(caps.supportedCompositeAlpha & -caps.supportedCompositeAlpha);
        sc.presentMode = VK_PRESENT_MODE_FIFO_KHR; sc.clipped = VK_TRUE;
        check(f.vkCreateSwapchainKHR(device, &sc, nullptr, &swapchain), "swapchain");
        check(f.vkGetSwapchainImagesKHR(device, swapchain, &n, nullptr), "swapchain images");
        swapImages.resize(n);
        check(f.vkGetSwapchainImagesKHR(device, swapchain, &n, swapImages.data()), "swapchain images");
        swapRendered.resize(n);VkSemaphoreCreateInfo semaphoreInfo{VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO};
        for(auto&sem:swapRendered)check(f.vkCreateSemaphore(device,&semaphoreInfo,nullptr,&sem),"per-image presentation semaphore");
        swapExtent = e;
        return true;
    }
    void presentSource(unsigned w, unsigned h) {
        f.vkDeviceWaitIdle(device);
        if (srcImage.view) f.vkDestroyImageView(device, srcImage.view, nullptr);
        if (srcImage.image) f.vkDestroyImage(device, srcImage.image, nullptr);
        if (srcImage.memory) f.vkFreeMemory(device, srcImage.memory, nullptr);
        srcImage = {};
        image(srcImage.image, srcImage.memory, srcImage.view, w, h, VK_FORMAT_R5G6B5_UNORM_PACK16, VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT, VK_IMAGE_ASPECT_COLOR_BIT);
        srcWidth = w; srcHeight = h;
    }
    void shutdown() {
        if (!device) { if (instance && f.vkDestroyInstance) f.vkDestroyInstance(instance, nullptr); if (library) ::FreeLibrary(static_cast<HMODULE>(library)); return; }
        f.vkDeviceWaitIdle(device);
        if(qualityPipeline)f.vkDestroyPipeline(device,qualityPipeline,nullptr);
        if(qualityLayout)f.vkDestroyPipelineLayout(device,qualityLayout,nullptr);
        if(qualityPool)f.vkDestroyDescriptorPool(device,qualityPool,nullptr);
        if(qualityVert)f.vkDestroyShaderModule(device,qualityVert,nullptr);
        if(qualityFrag)f.vkDestroyShaderModule(device,qualityFrag,nullptr);
        for(auto&[key,b]:model_buffers)for(Buffer*p:{&b.local,&b.staging}){if(p->buffer)f.vkDestroyBuffer(device,p->buffer,nullptr);if(p->memory)f.vkFreeMemory(device,p->memory,nullptr);}model_buffers.clear();
        for (auto &[k, t] : textures) destroy(t);
        destroy(white);
        for (auto &[k, p] : pipelines) f.vkDestroyPipeline(device, p, nullptr);
        for (auto &[k, s] : samplers) f.vkDestroySampler(device, s, nullptr);
        dropSwapchain();
        dropSurface();
        if (child) ::DestroyWindow(child);
        if (srcImage.view) f.vkDestroyImageView(device, srcImage.view, nullptr);
        if (srcImage.image) f.vkDestroyImage(device, srcImage.image, nullptr);
        if (srcImage.memory) f.vkFreeMemory(device, srcImage.memory, nullptr);
        if (acquired) f.vkDestroySemaphore(device, acquired, nullptr);
        if (presentFence) f.vkDestroyFence(device, presentFence, nullptr);
        if (presentPool) f.vkDestroyCommandPool(device, presentPool, nullptr);
        for (Buffer *b : {&upload, &readback, &vertexBuffer, &texUpload, &presentUpload})
            if (b->buffer) { f.vkDestroyBuffer(device, b->buffer, nullptr); f.vkFreeMemory(device, b->memory, nullptr); }
        if (framebuffer) f.vkDestroyFramebuffer(device, framebuffer, nullptr);
        for (Image *i : {&colorImage, &depthImage, &colorLo, &depthLo,&qualitySource}) {
            if (i->view) f.vkDestroyImageView(device, i->view, nullptr);
            if (i->image) f.vkDestroyImage(device, i->image, nullptr);
            if (i->memory) f.vkFreeMemory(device, i->memory, nullptr);
        }
        f.vkDestroyRenderPass(device, renderPass, nullptr);
        f.vkDestroyDescriptorPool(device, descriptorPool, nullptr);
        if(modelLayout)f.vkDestroyPipelineLayout(device,modelLayout,nullptr);
        f.vkDestroyPipelineLayout(device, pipelineLayout, nullptr);
        f.vkDestroyDescriptorSetLayout(device, setLayout, nullptr);
        if(modelVert)f.vkDestroyShaderModule(device,modelVert,nullptr);
        f.vkDestroyShaderModule(device, vert, nullptr);
        f.vkDestroyShaderModule(device, frag, nullptr);
        f.vkDestroyFence(device, fence, nullptr);
        f.vkDestroyCommandPool(device, commandPool, nullptr);
        f.vkDestroyDevice(device, nullptr);
        f.vkDestroyInstance(instance, nullptr);
        ::FreeLibrary(static_cast<HMODULE>(library));
        device = {};
    }
    #include "quality_stage.inc"
};
}  // namespace mw34::vkscene
