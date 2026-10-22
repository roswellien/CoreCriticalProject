#pragma once
// Guest COM objects for the game's DirectDraw/Direct3D interfaces (included by mfc_stage.hpp).
//
// A guest object lives in the COM arena [37000000, 37100000): word 0 is its vtable, and every
// vtable slot is a service token resolved by (interface, method) in the SDK slot order. Each guest
// object proxies one host COM interface of the identified provider. The first provider is the real
// x64 system ddraw.dll loaded from the system directory; a Vulkan provider (D7VK x64) can replace
// it behind the same proxy. Statuses and outputs are the provider's actual ones (outputs written on
// failure too, as COM requires); methods without marshalling stop typed.
#include <ddraw.h>
#include <dsound.h>
#include <d3d.h>
#include <cstring>
#define DIRECTINPUT_VERSION 0x0700
#include <dinput.h>
namespace com {
struct Iface {
    const char *name;
    GUID iid;
    std::vector<const char *> slots;
};
// Table order and slot order are distinct. Each slots vector must preserve the
// SDK vtable order; the host resolves a guest service token to that exact method.
// Build later interface revisions by extending the earlier revision's slots.
inline const std::vector<Iface> &ifaces() {
    static const std::vector<const char *> direct_draw1_slots{"QueryInterface",
                                                              "AddRef",
                                                              "Release",
                                                              "Compact",
                                                              "CreateClipper",
                                                              "CreatePalette",
                                                              "CreateSurface",
                                                              "DuplicateSurface",
                                                              "EnumDisplayModes",
                                                              "EnumSurfaces",
                                                              "FlipToGDISurface",
                                                              "GetCaps",
                                                              "GetDisplayMode",
                                                              "GetFourCCCodes",
                                                              "GetGDISurface",
                                                              "GetMonitorFrequency",
                                                              "GetScanLine",
                                                              "GetVerticalBlankStatus",
                                                              "Initialize",
                                                              "RestoreDisplayMode",
                                                              "SetCooperativeLevel",
                                                              "SetDisplayMode",
                                                              "WaitForVerticalBlank"};
    auto direct_draw2_slots = direct_draw1_slots;
    direct_draw2_slots.push_back("GetAvailableVidMem");
    auto direct_draw4_slots = direct_draw2_slots;
    for (const char *method_name :
         {"GetSurfaceFromDC", "RestoreAllSurfaces", "TestCooperativeLevel", "GetDeviceIdentifier"})
        direct_draw4_slots.push_back(method_name);
    auto direct_draw7_slots = direct_draw4_slots;
    for (const char *method_name : {"StartModeTest", "EvaluateMode"})
        direct_draw7_slots.push_back(method_name);
    static const std::vector<const char *> surface1_slots{"QueryInterface",
                                                          "AddRef",
                                                          "Release",
                                                          "AddAttachedSurface",
                                                          "AddOverlayDirtyRect",
                                                          "Blt",
                                                          "BltBatch",
                                                          "BltFast",
                                                          "DeleteAttachedSurface",
                                                          "EnumAttachedSurfaces",
                                                          "EnumOverlayZOrders",
                                                          "Flip",
                                                          "GetAttachedSurface",
                                                          "GetBltStatus",
                                                          "GetCaps",
                                                          "GetClipper",
                                                          "GetColorKey",
                                                          "GetDC",
                                                          "GetFlipStatus",
                                                          "GetOverlayPosition",
                                                          "GetPalette",
                                                          "GetPixelFormat",
                                                          "GetSurfaceDesc",
                                                          "Initialize",
                                                          "IsLost",
                                                          "Lock",
                                                          "ReleaseDC",
                                                          "Restore",
                                                          "SetClipper",
                                                          "SetColorKey",
                                                          "SetOverlayPosition",
                                                          "SetPalette",
                                                          "Unlock",
                                                          "UpdateOverlay",
                                                          "UpdateOverlayDisplay",
                                                          "UpdateOverlayZOrder"};
    auto surface2_slots = surface1_slots;
    for (const char *method_name : {"GetDDInterface", "PageLock", "PageUnlock"})
        surface2_slots.push_back(method_name);
    auto surface3_slots = surface2_slots;
    surface3_slots.push_back("SetSurfaceDesc");
    auto surface4_slots = surface3_slots;
    for (const char *method_name : {"SetPrivateData", "GetPrivateData", "FreePrivateData",
                                    "GetUniquenessValue", "ChangeUniquenessValue"})
        surface4_slots.push_back(method_name);
    // DirectPlay lobby (project-implemented service: no 64-bit DirectPlay provider exists on the
    // host).
    static const std::vector<const char *> lobby1_slots{"QueryInterface",
                                                        "AddRef",
                                                        "Release",
                                                        "Connect",
                                                        "CreateAddress",
                                                        "EnumAddress",
                                                        "EnumAddressTypes",
                                                        "EnumLocalApplications",
                                                        "GetConnectionSettings",
                                                        "ReceiveLobbyMessage",
                                                        "RunApplication",
                                                        "SendLobbyMessage",
                                                        "SetConnectionSettings",
                                                        "SetLobbyMessageEvent"};
    auto lobby2_slots = lobby1_slots;
    lobby2_slots.push_back("CreateCompoundAddress");
    auto lobby3_slots = lobby2_slots;
    for (const char *method_name :
         {"ConnectEx", "RegisterApplication", "UnregisterApplication", "WaitForConnectionSettings"})
        lobby3_slots.push_back(method_name);
    static const GUID lobbyA{
        0x26c66a70, 0xb367, 0x11cf, {0xa0, 0x24, 0x00, 0xaa, 0x00, 0x61, 0x57, 0xac}},
        lobby2A{0x1bb4af80, 0xa303, 0x11d0, {0x9c, 0x4f, 0x00, 0xa0, 0xc9, 0x05, 0x42, 0x5e}},
        lobby3A{0x2db72491, 0x652c, 0x11d1, {0xa7, 0xa8, 0x00, 0x00, 0xf8, 0x03, 0xab, 0xfc}};
    static const std::vector<const char *> sound_slots{
        "QueryInterface",      "AddRef",    "Release",
        "CreateSoundBuffer",   "GetCaps",   "DuplicateSoundBuffer",
        "SetCooperativeLevel", "Compact",   "GetSpeakerConfig",
        "SetSpeakerConfig",    "Initialize"};
    static const std::vector<const char *> sound_buffer_slots{"QueryInterface",
                                                              "AddRef",
                                                              "Release",
                                                              "GetCaps",
                                                              "GetCurrentPosition",
                                                              "GetFormat",
                                                              "GetVolume",
                                                              "GetPan",
                                                              "GetFrequency",
                                                              "GetStatus",
                                                              "Initialize",
                                                              "Lock",
                                                              "Play",
                                                              "SetCurrentPosition",
                                                              "SetFormat",
                                                              "SetVolume",
                                                              "SetPan",
                                                              "SetFrequency",
                                                              "Stop",
                                                              "Unlock",
                                                              "Restore"};
    static const std::vector<const char *> clipper_slots{
        "QueryInterface",    "AddRef",      "Release", "GetClipList", "GetHWnd", "Initialize",
        "IsClipListChanged", "SetClipList", "SetHWnd"};
    static const std::vector<const char *> palette_slots{
        "QueryInterface", "AddRef", "Release", "GetCaps", "GetEntries", "Initialize", "SetEntries"};
    static const std::vector<const char *> direct3d3_slots{"QueryInterface",
                                                           "AddRef",
                                                           "Release",
                                                           "EnumDevices",
                                                           "CreateLight",
                                                           "CreateMaterial",
                                                           "CreateViewport",
                                                           "FindDevice",
                                                           "CreateDevice",
                                                           "CreateVertexBuffer",
                                                           "EnumZBufferFormats",
                                                           "EvictManagedTextures"};
    static const std::vector<const char *> device3_slots{"QueryInterface",
                                                         "AddRef",
                                                         "Release",
                                                         "GetCaps",
                                                         "GetStats",
                                                         "AddViewport",
                                                         "DeleteViewport",
                                                         "NextViewport",
                                                         "EnumTextureFormats",
                                                         "BeginScene",
                                                         "EndScene",
                                                         "GetDirect3D",
                                                         "SetCurrentViewport",
                                                         "GetCurrentViewport",
                                                         "SetRenderTarget",
                                                         "GetRenderTarget",
                                                         "Begin",
                                                         "BeginIndexed",
                                                         "Vertex",
                                                         "Index",
                                                         "End",
                                                         "GetRenderState",
                                                         "SetRenderState",
                                                         "GetLightState",
                                                         "SetLightState",
                                                         "SetTransform",
                                                         "GetTransform",
                                                         "MultiplyTransform",
                                                         "DrawPrimitive",
                                                         "DrawIndexedPrimitive",
                                                         "SetClipStatus",
                                                         "GetClipStatus",
                                                         "DrawPrimitiveStrided",
                                                         "DrawIndexedPrimitiveStrided",
                                                         "DrawPrimitiveVB",
                                                         "DrawIndexedPrimitiveVB",
                                                         "ComputeSphereVisibility",
                                                         "GetTexture",
                                                         "SetTexture",
                                                         "GetTextureStageState",
                                                         "SetTextureStageState",
                                                         "ValidateDevice"};
    static const std::vector<const char *> viewport3_slots{"QueryInterface",
                                                           "AddRef",
                                                           "Release",
                                                           "Initialize",
                                                           "GetViewport",
                                                           "SetViewport",
                                                           "TransformVertices",
                                                           "LightElements",
                                                           "SetBackground",
                                                           "GetBackground",
                                                           "SetBackgroundDepth",
                                                           "GetBackgroundDepth",
                                                           "Clear",
                                                           "AddLight",
                                                           "DeleteLight",
                                                           "NextLight",
                                                           "GetViewport2",
                                                           "SetViewport2",
                                                           "SetBackgroundDepth2",
                                                           "GetBackgroundDepth2",
                                                           "Clear2"};
    static const std::vector<const char *> texture2_slots{
        "QueryInterface", "AddRef", "Release", "GetHandle", "PaletteChanged", "Load"};
    static const std::vector<const char *> material3_slots{
        "QueryInterface", "AddRef", "Release", "SetMaterial", "GetMaterial", "GetHandle"};
    static const std::vector<const char *> input_slots{
        "QueryInterface", "AddRef",          "Release",         "CreateDevice",
        "EnumDevices",    "GetDeviceStatus", "RunControlPanel", "Initialize"};
    static const std::vector<const char *> input_device_slots{"QueryInterface",
                                                              "AddRef",
                                                              "Release",
                                                              "GetCapabilities",
                                                              "EnumObjects",
                                                              "GetProperty",
                                                              "SetProperty",
                                                              "Acquire",
                                                              "Unacquire",
                                                              "GetDeviceState",
                                                              "GetDeviceData",
                                                              "SetDataFormat",
                                                              "SetEventNotification",
                                                              "SetCooperativeLevel",
                                                              "GetObjectInfo",
                                                              "GetDeviceInfo",
                                                              "RunControlPanel",
                                                              "Initialize"};
    auto input_device2_slots = input_device_slots;
    for (const char *method_name : {"CreateEffect", "EnumEffects", "GetEffectInfo",
                                    "GetForceFeedbackState", "SendForceFeedbackCommand",
                                    "EnumCreatedEffectObjects", "Escape", "Poll", "SendDeviceData"})
        input_device2_slots.push_back(method_name);
    // The returned table is immutable after first construction. Lookup helpers
    // return borrowed pointers into this process-lifetime table, not COM AddRefs.
    static const std::vector<Iface> interfaces{
        {"IDirectDraw", IID_IDirectDraw, direct_draw1_slots},
        {"IDirectInputA", IID_IDirectInputA, input_slots},
        {"IDirectInputDeviceA", IID_IDirectInputDeviceA, input_device_slots},
        {"IDirectInputDevice2A", IID_IDirectInputDevice2A, input_device2_slots},
        {"IDirect3D3", IID_IDirect3D3, direct3d3_slots},
        {"IDirect3DDevice3", IID_IDirect3DDevice3, device3_slots},
        {"IDirect3DViewport3", IID_IDirect3DViewport3, viewport3_slots},
        {"IDirect3DTexture2", IID_IDirect3DTexture2, texture2_slots},
        {"IDirect3DMaterial3", IID_IDirect3DMaterial3, material3_slots},
        {"IDirectDrawClipper", IID_IDirectDrawClipper, clipper_slots},
        {"IDirectDrawPalette", IID_IDirectDrawPalette, palette_slots},
        {"IDirectSound", IID_IDirectSound, sound_slots},
        {"IDirectSoundBuffer", IID_IDirectSoundBuffer, sound_buffer_slots},
        {"IDirectPlayLobbyA", lobbyA, lobby1_slots},
        {"IDirectPlayLobby2A", lobby2A, lobby2_slots},
        {"IDirectPlayLobby3A", lobby3A, lobby3_slots},
        {"IDirectDraw2", IID_IDirectDraw2, direct_draw2_slots},
        {"IDirectDraw4", IID_IDirectDraw4, direct_draw4_slots},
        {"IDirectDrawSurface", IID_IDirectDrawSurface, surface1_slots},
        {"IDirectDrawSurface2", IID_IDirectDrawSurface2, surface2_slots},
        {"IDirectDrawSurface3", IID_IDirectDrawSurface3, surface3_slots},
        {"IDirectDrawSurface4", IID_IDirectDrawSurface4, surface4_slots},
        {"IDirectDraw7", IID_IDirectDraw7, direct_draw7_slots}};
    return interfaces;
}
// x86 guest DDSURFACEDESC (108 bytes) / DDSURFACEDESC2 (124 bytes) field offsets; lpSurface is a
// guest pointer (offset 36) and is never carried across. DDCOLORKEY x4 at 40, DDPIXELFORMAT (32) at
// 72, DDSCAPS at 104 (DDSCAPS2: 16 bytes at 104, then dwTextureStage at 120).
inline constexpr unsigned desc1_size = 108, desc2_size = 124;
inline const Iface *by_iid(const GUID &g) {
    for (const auto &i : ifaces())
        if (IsEqualGUID(i.iid, g))
            return &i;
    return nullptr;
}
inline const Iface *by_name(const std::string &n) {
    for (const auto &i : ifaces())
        if (n == i.name)
            return &i;
    return nullptr;
}
inline constexpr unsigned arena = 0x37000000, arena_end = 0x37100000;
// Object addresses and owner links are 32-bit guest addresses. The native field
// is a host interface pointer and must never be stored in a guest vtable slot.
// owner: guest address of the root DirectDraw proxy whose object this belongs to (0 for that root).
// Releasing the last DirectDraw interface of a root destroys its surfaces implicitly (DirectDraw
// rule).
struct Object {
    unsigned guest;
    const Iface *iface;
    IUnknown *native;
    bool alive;
    unsigned owner;
    unsigned refs{};
}; // refs: project-implemented service objects (native==nullptr)
inline bool is_d3d(const Iface *i) { return std::strncmp(i->name, "IDirect3D", 9) == 0; }
inline bool is_lobby(const Iface *i) { return std::strncmp(i->name, "IDirectPlayLobby", 16) == 0; }
inline constexpr unsigned dperr_notlobbied = 0x8877042E;
inline bool is_dd(const Iface *i) {
    const std::string n = i->name;
    return n.rfind("IDirectDraw", 0) == 0 && n.find("Surface") == std::string::npos;
}
struct Provider {
    HMODULE module{};
    std::wstring path;
    std::string sha;
    HRESULT(WINAPI *create)(GUID *, LPDIRECTDRAW *, IUnknown *) {};
    HRESULT(WINAPI *create_ex)(GUID *, void **, REFIID, IUnknown *) {};
};
// These records describe loaded providers; they do not implement RAII unloading.
// Their owning host service must keep the module alive while objects use it.
struct InputProvider {
    HMODULE module{};
    std::wstring path;
    std::string sha;
    HRESULT(WINAPI *create)(HINSTANCE, DWORD, LPDIRECTINPUTA *, LPUNKNOWN) {};
};
struct SoundProvider {
    HMODULE module{};
    std::wstring path;
    std::string sha;
    HRESULT(WINAPI *create)(LPCGUID, LPDIRECTSOUND *, LPUNKNOWN) {};
};
inline bool is_sound(const Iface *i) { return std::string(i->name).rfind("IDirectSound", 0) == 0; }
} // namespace com
