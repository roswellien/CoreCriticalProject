// Project-authored graphics contract fixture. No game code or assets are used.
#include <windows.h>
#include <ddraw.h>
#include <d3d.h>

#include <cstdint>
#include <cstdio>
#include <stdexcept>

template <typename T> struct Com {
    T *ptr = nullptr;
    ~Com() { if (ptr) ptr->Release(); }
    Com() = default;
    Com(const Com &) = delete;
    Com &operator=(const Com &) = delete;
    T *operator->() const { return ptr; }
};

static void check(const char *step, HRESULT hr) {
    std::printf("%s HRESULT=0x%08lX\n", step, static_cast<unsigned long>(hr));
    std::fflush(stdout);
    if (FAILED(hr)) throw std::runtime_error(step);
}

static DDSURFACEDESC2 color_desc(DWORD width, DWORD height, DWORD caps) {
    DDSURFACEDESC2 desc{};
    desc.dwSize = sizeof(desc);
    desc.dwFlags = DDSD_CAPS | DDSD_WIDTH | DDSD_HEIGHT | DDSD_PIXELFORMAT;
    desc.dwWidth = width;
    desc.dwHeight = height;
    desc.ddsCaps.dwCaps = caps;
    desc.ddpfPixelFormat.dwSize = sizeof(DDPIXELFORMAT);
    desc.ddpfPixelFormat.dwFlags = DDPF_RGB;
    desc.ddpfPixelFormat.dwRGBBitCount = 16;
    desc.ddpfPixelFormat.dwRBitMask = 0xF800;
    desc.ddpfPixelFormat.dwGBitMask = 0x07E0;
    desc.ddpfPixelFormat.dwBBitMask = 0x001F;
    return desc;
}

struct Vertex {
    float x, y, z, rhw;
    DWORD diffuse, specular;
    float u, v;
};
static_assert(sizeof(Vertex) == 32);
static_assert((D3DFVF_XYZRHW | D3DFVF_DIFFUSE | D3DFVF_SPECULAR | D3DFVF_TEX1) == 0x1C4);

static void quad(IDirect3DDevice3 *device, float lo, float hi, float z, DWORD color) {
    Vertex vertices[] = {{lo, lo, z, 1, color, 0, 0, 0},
                         {hi, lo, z, 1, color, 0, 1, 0},
                         {hi, hi, z, 1, color, 0, 1, 1},
                         {lo, hi, z, 1, color, 0, 0, 1}};
    check("BeginScene", device->BeginScene());
    check("DrawPrimitive fan FVF=0x1C4 flags=0x18",
          device->DrawPrimitive(D3DPT_TRIANGLEFAN, 0x1C4, vertices, 4, 0x18));
    check("EndScene", device->EndScene());
}

static void pixel(IDirectDrawSurface4 *surface, int x, int y, std::uint16_t expected) {
    DDSURFACEDESC2 locked{};
    locked.dwSize = sizeof(locked);
    check("Lock readback", surface->Lock(nullptr, &locked, DDLOCK_WAIT | DDLOCK_READONLY, nullptr));
    const auto *row = reinterpret_cast<const std::uint16_t *>(
        static_cast<const unsigned char *>(locked.lpSurface) + y * locked.lPitch);
    const auto actual = row[x];
    check("Unlock readback", surface->Unlock(nullptr));
    std::printf("pixel (%d,%d): actual=0x%04X expected=0x%04X\n", x, y,
                static_cast<unsigned>(actual), static_cast<unsigned>(expected));
    if (actual != expected) throw std::runtime_error("pixel mismatch");
}

static void exercise(HMODULE module, HWND window) {
    using Create = HRESULT(WINAPI *)(GUID *, LPDIRECTDRAW *, IUnknown *);
    auto create = reinterpret_cast<Create>(GetProcAddress(module, "DirectDrawCreate"));
    if (!create) throw std::runtime_error("DirectDrawCreate export missing");
    Com<IDirectDraw> dd;
    Com<IDirectDraw4> dd4;
    Com<IDirect3D3> d3d;
    Com<IDirectDrawSurface4> target;
    Com<IDirectDrawSurface4> depth;
    Com<IDirect3DDevice3> device;
    Com<IDirect3DViewport3> viewport;
    Com<IDirectDrawSurface4> texture_surface;
    Com<IDirect3DTexture2> texture;
    check("DirectDrawCreate", create(nullptr, &dd.ptr, nullptr));
    check("QI IDirectDraw4", dd->QueryInterface(IID_IDirectDraw4, reinterpret_cast<void **>(&dd4.ptr)));
    check("QI IDirect3D3", dd4->QueryInterface(IID_IDirect3D3, reinterpret_cast<void **>(&d3d.ptr)));
    check("SetCooperativeLevel normal", dd4->SetCooperativeLevel(window, DDSCL_NORMAL));
    auto desc = color_desc(64, 64, DDSCAPS_OFFSCREENPLAIN | DDSCAPS_3DDEVICE | DDSCAPS_VIDEOMEMORY);
    check("Create RGB565 render target", dd4->CreateSurface(&desc, &target.ptr, nullptr));
    DDSURFACEDESC2 zdesc{};
    zdesc.dwSize = sizeof(zdesc);
    zdesc.dwFlags = DDSD_CAPS | DDSD_WIDTH | DDSD_HEIGHT | DDSD_PIXELFORMAT;
    zdesc.dwWidth = zdesc.dwHeight = 64;
    zdesc.ddsCaps.dwCaps = DDSCAPS_ZBUFFER | DDSCAPS_VIDEOMEMORY;
    zdesc.ddpfPixelFormat.dwSize = sizeof(DDPIXELFORMAT);
    zdesc.ddpfPixelFormat.dwFlags = DDPF_ZBUFFER;
    zdesc.ddpfPixelFormat.dwZBufferBitDepth = 16;
    zdesc.ddpfPixelFormat.dwZBitMask = 0xFFFF;
    check("Create D16 depth", dd4->CreateSurface(&zdesc, &depth.ptr, nullptr));
    check("Attach D16 depth", target->AddAttachedSurface(depth.ptr));
    check("Create HAL IDirect3DDevice3", d3d->CreateDevice(IID_IDirect3DHALDevice, target.ptr, &device.ptr, nullptr));
    check("CreateViewport", d3d->CreateViewport(&viewport.ptr, nullptr));
    check("AddViewport", device->AddViewport(viewport.ptr));
    D3DVIEWPORT2 vp{};
    vp.dwSize = sizeof(vp);
    vp.dwWidth = vp.dwHeight = 64;
    vp.dvClipX = -1; vp.dvClipY = 1;
    vp.dvClipWidth = vp.dvClipHeight = 2;
    vp.dvMinZ = 0; vp.dvMaxZ = 1;
    check("SetViewport2", viewport->SetViewport2(&vp));
    check("SetCurrentViewport", device->SetCurrentViewport(viewport.ptr));
    check("Disable culling", device->SetRenderState(D3DRENDERSTATE_CULLMODE, D3DCULL_NONE));
    check("Enable depth", device->SetRenderState(D3DRENDERSTATE_ZENABLE, TRUE));
    check("Enable depth writes", device->SetRenderState(D3DRENDERSTATE_ZWRITEENABLE, TRUE));
    check("Greater depth comparison", device->SetRenderState(D3DRENDERSTATE_ZFUNC, D3DCMP_GREATER));
    check("Disable fog", device->SetRenderState(D3DRENDERSTATE_FOGENABLE, FALSE));
    check("Disable alpha blend", device->SetRenderState(D3DRENDERSTATE_ALPHABLENDENABLE, FALSE));
    check("Diffuse color", device->SetTextureStageState(0, D3DTSS_COLOROP, D3DTOP_SELECTARG2));
    check("Diffuse argument", device->SetTextureStageState(0, D3DTSS_COLORARG2, D3DTA_DIFFUSE));
    DDBLTFX fill{};
    fill.dwSize = sizeof(fill);
    check("Full depth fill zero", depth->Blt(nullptr, nullptr, nullptr, DDBLT_DEPTHFILL | DDBLT_WAIT, &fill));
    quad(device.ptr, 2, 62, 0.75F, 0xFFFF0000);
    pixel(target.ptr, 10, 10, 0xF800);
    RECT partial{20, 20, 44, 44};
    check("Partial depth fill zero", depth->Blt(&partial, nullptr, nullptr, DDBLT_DEPTHFILL | DDBLT_WAIT, &fill));
    quad(device.ptr, 2, 62, 0.5F, 0xFF0000FF);
    pixel(target.ptr, 30, 30, 0x001F);
    pixel(target.ptr, 10, 10, 0xF800);
    DDSURFACEDESC2 locked{};
    locked.dwSize = sizeof(locked);
    check("Lock CPU overlay", target->Lock(nullptr, &locked, DDLOCK_WAIT, nullptr));
    auto *row = reinterpret_cast<std::uint16_t *>(static_cast<unsigned char *>(locked.lpSurface) + 10 * locked.lPitch);
    row[10] = 0x07E0;
    check("Unlock CPU overlay", target->Unlock(nullptr));
    quad(device.ptr, 48, 60, 0.9F, 0xFFFFFF00);
    pixel(target.ptr, 10, 10, 0x07E0);
    pixel(target.ptr, 30, 30, 0x001F);
    pixel(target.ptr, 54, 54, 0xFFE0);
    auto texture_desc = color_desc(2, 2, DDSCAPS_TEXTURE | DDSCAPS_SYSTEMMEMORY);
    check("Create RGB565 texture", dd4->CreateSurface(&texture_desc, &texture_surface.ptr, nullptr));
    check("QI IDirect3DTexture2", texture_surface->QueryInterface(IID_IDirect3DTexture2,
                                                                reinterpret_cast<void **>(&texture.ptr)));
    auto fill_texture = [&](std::uint16_t value) {
        DDSURFACEDESC2 bits{};
        bits.dwSize = sizeof(bits);
        check("Lock texture", texture_surface->Lock(nullptr, &bits, DDLOCK_WAIT, nullptr));
        for (int y = 0; y < 2; ++y) {
            auto *tex_row = reinterpret_cast<std::uint16_t *>(
                static_cast<unsigned char *>(bits.lpSurface) + y * bits.lPitch);
            tex_row[0] = tex_row[1] = value;
        }
        check("Unlock texture", texture_surface->Unlock(nullptr));
    };
    fill_texture(0x07FF);
    check("Bind texture", device->SetTexture(0, texture.ptr));
    check("Texture color", device->SetTextureStageState(0, D3DTSS_COLOROP, D3DTOP_SELECTARG1));
    check("Texture argument", device->SetTextureStageState(0, D3DTSS_COLORARG1, D3DTA_TEXTURE));
    quad(device.ptr, 4, 8, 0.95F, 0xFFFFFFFF);
    pixel(target.ptr, 6, 6, 0x07FF);
    fill_texture(0xF81F);
    check("Rebind updated texture", device->SetTexture(0, texture.ptr));
    quad(device.ptr, 4, 8, 0.98F, 0xFFFFFFFF);
    pixel(target.ptr, 6, 6, 0xF81F);
    check("Unbind texture", device->SetTexture(0, nullptr));
    check("Restore diffuse", device->SetTextureStageState(0, D3DTSS_COLOROP, D3DTOP_SELECTARG2));
    HDC dc = nullptr;
    check("GetDC on RGB565 target", target->GetDC(&dc));
    const COLORREF gdi_result = SetPixel(dc, 14, 14, RGB(0, 0, 255));
    check("ReleaseDC on RGB565 target", target->ReleaseDC(dc));
    if (gdi_result == CLR_INVALID) throw std::runtime_error("GDI SetPixel failed");
    quad(device.ptr, 48, 60, 0.99F, 0xFFFFFF00);
    pixel(target.ptr, 14, 14, 0x001F);
    pixel(target.ptr, 10, 10, 0x07E0);
    pixel(target.ptr, 6, 6, 0xF81F);
    check("DeleteViewport", device->DeleteViewport(viewport.ptr));
}

int main(int argc, char **argv) {
    if (argc != 2) { std::fprintf(stderr, "Usage: mw34_d7vk_fixture <absolute ddraw.dll path>\n"); return 2; }
    HMODULE module = LoadLibraryExA(argv[1], nullptr, LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32);
    if (!module) { std::fprintf(stderr, "LoadLibrary failed: %lu\n", GetLastError()); return 3; }
    HWND window = CreateWindowExA(0, "STATIC", "MW34 authored D7VK fixture", WS_OVERLAPPEDWINDOW,
                                  0, 0, 64, 64, nullptr, nullptr, GetModuleHandleA(nullptr), nullptr);
    int result = 0;
    try {
        if (!window) throw std::runtime_error("hidden window creation failed");
        exercise(module, window);
        std::puts("PASS: authored offscreen draw/depth/CPU/texture/GDI fixture; no native game credit");
    } catch (const std::exception &error) {
        std::fprintf(stderr, "FAIL: %s\n", error.what());
        result = 1;
    }
    if (window) DestroyWindow(window);
    FreeLibrary(module);
    return result;
}
