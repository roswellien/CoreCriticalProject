#pragma once
// Guest COM objects for the game's DirectDraw/Direct3D interfaces (included by mfc_stage.hpp).
//
// A guest object lives in the COM arena [37000000, 37100000): word 0 is its vtable, and every vtable
// slot is a service token resolved by (interface, method) in the SDK slot order. Each guest object
// proxies one host COM interface of the identified provider. The first provider is the real x64
// system ddraw.dll loaded from the system directory; a Vulkan provider (D7VK x64) can replace it
// behind the same proxy. Statuses and outputs are the provider's actual ones (outputs written on
// failure too, as COM requires); methods without marshalling stop typed.
#include <ddraw.h>
#include <dsound.h>
#include <d3d.h>
#include <cstring>
#define DIRECTINPUT_VERSION 0x0700
#include <dinput.h>
namespace com {
struct Iface{const char*name;GUID iid;std::vector<const char*>slots;};
inline const std::vector<Iface>&ifaces(){
 static const std::vector<const char*>dd1{"QueryInterface","AddRef","Release","Compact","CreateClipper","CreatePalette","CreateSurface","DuplicateSurface","EnumDisplayModes","EnumSurfaces","FlipToGDISurface","GetCaps","GetDisplayMode","GetFourCCCodes","GetGDISurface","GetMonitorFrequency","GetScanLine","GetVerticalBlankStatus","Initialize","RestoreDisplayMode","SetCooperativeLevel","SetDisplayMode","WaitForVerticalBlank"};
 auto dd2=dd1;dd2.push_back("GetAvailableVidMem");auto dd4=dd2;for(const char*x:{"GetSurfaceFromDC","RestoreAllSurfaces","TestCooperativeLevel","GetDeviceIdentifier"})dd4.push_back(x);
 static const std::vector<const char*>s1{"QueryInterface","AddRef","Release","AddAttachedSurface","AddOverlayDirtyRect","Blt","BltBatch","BltFast","DeleteAttachedSurface","EnumAttachedSurfaces","EnumOverlayZOrders","Flip","GetAttachedSurface","GetBltStatus","GetCaps","GetClipper","GetColorKey","GetDC","GetFlipStatus","GetOverlayPosition","GetPalette","GetPixelFormat","GetSurfaceDesc","Initialize","IsLost","Lock","ReleaseDC","Restore","SetClipper","SetColorKey","SetOverlayPosition","SetPalette","Unlock","UpdateOverlay","UpdateOverlayDisplay","UpdateOverlayZOrder"};
 auto s2=s1;for(const char*x:{"GetDDInterface","PageLock","PageUnlock"})s2.push_back(x);auto s3=s2;s3.push_back("SetSurfaceDesc");auto s4=s3;for(const char*x:{"SetPrivateData","GetPrivateData","FreePrivateData","GetUniquenessValue","ChangeUniquenessValue"})s4.push_back(x);
 // DirectPlay lobby (project-implemented service: no 64-bit DirectPlay provider exists on the host).
 static const std::vector<const char*>l1{"QueryInterface","AddRef","Release","Connect","CreateAddress","EnumAddress","EnumAddressTypes","EnumLocalApplications","GetConnectionSettings","ReceiveLobbyMessage","RunApplication","SendLobbyMessage","SetConnectionSettings","SetLobbyMessageEvent"};
 auto l2=l1;l2.push_back("CreateCompoundAddress");auto l3=l2;for(const char*x:{"ConnectEx","RegisterApplication","UnregisterApplication","WaitForConnectionSettings"})l3.push_back(x);
 static const GUID lobbyA{0x26c66a70,0xb367,0x11cf,{0xa0,0x24,0x00,0xaa,0x00,0x61,0x57,0xac}},lobby2A{0x1bb4af80,0xa303,0x11d0,{0x9c,0x4f,0x00,0xa0,0xc9,0x05,0x42,0x5e}},lobby3A{0x2db72491,0x652c,0x11d1,{0xa7,0xa8,0x00,0x00,0xf8,0x03,0xab,0xfc}};
 static const std::vector<const char*>ds1{"QueryInterface","AddRef","Release","CreateSoundBuffer","GetCaps","DuplicateSoundBuffer","SetCooperativeLevel","Compact","GetSpeakerConfig","SetSpeakerConfig","Initialize"};
 static const std::vector<const char*>dsb{"QueryInterface","AddRef","Release","GetCaps","GetCurrentPosition","GetFormat","GetVolume","GetPan","GetFrequency","GetStatus","Initialize","Lock","Play","SetCurrentPosition","SetFormat","SetVolume","SetPan","SetFrequency","Stop","Unlock","Restore"};
 static const std::vector<const char*>clip{"QueryInterface","AddRef","Release","GetClipList","GetHWnd","Initialize","IsClipListChanged","SetClipList","SetHWnd"};
 static const std::vector<const char*>pal{"QueryInterface","AddRef","Release","GetCaps","GetEntries","Initialize","SetEntries"};
 static const std::vector<const char*>d3{"QueryInterface","AddRef","Release","EnumDevices","CreateLight","CreateMaterial","CreateViewport","FindDevice","CreateDevice","CreateVertexBuffer","EnumZBufferFormats","EvictManagedTextures"};
 static const std::vector<const char*>dev3{"QueryInterface","AddRef","Release","GetCaps","GetStats","AddViewport","DeleteViewport","NextViewport","EnumTextureFormats","BeginScene","EndScene","GetDirect3D","SetCurrentViewport","GetCurrentViewport","SetRenderTarget","GetRenderTarget","Begin","BeginIndexed","Vertex","Index","End","GetRenderState","SetRenderState","GetLightState","SetLightState","SetTransform","GetTransform","MultiplyTransform","DrawPrimitive","DrawIndexedPrimitive","SetClipStatus","GetClipStatus","DrawPrimitiveStrided","DrawIndexedPrimitiveStrided","DrawPrimitiveVB","DrawIndexedPrimitiveVB","ComputeSphereVisibility","GetTexture","SetTexture","GetTextureStageState","SetTextureStageState","ValidateDevice"};
 static const std::vector<const char*>vp3{"QueryInterface","AddRef","Release","Initialize","GetViewport","SetViewport","TransformVertices","LightElements","SetBackground","GetBackground","SetBackgroundDepth","GetBackgroundDepth","Clear","AddLight","DeleteLight","NextLight","GetViewport2","SetViewport2","SetBackgroundDepth2","GetBackgroundDepth2","Clear2"};
 static const std::vector<const char*>tex2{"QueryInterface","AddRef","Release","GetHandle","PaletteChanged","Load"};
 static const std::vector<const char*>mat3{"QueryInterface","AddRef","Release","SetMaterial","GetMaterial","GetHandle"};
 static const std::vector<const char*>di{"QueryInterface","AddRef","Release","CreateDevice","EnumDevices","GetDeviceStatus","RunControlPanel","Initialize"};
 static const std::vector<const char*>did{"QueryInterface","AddRef","Release","GetCapabilities","EnumObjects","GetProperty","SetProperty","Acquire","Unacquire","GetDeviceState","GetDeviceData","SetDataFormat","SetEventNotification","SetCooperativeLevel","GetObjectInfo","GetDeviceInfo","RunControlPanel","Initialize"};
 auto did2=did;for(const char*x:{"CreateEffect","EnumEffects","GetEffectInfo","GetForceFeedbackState","SendForceFeedbackCommand","EnumCreatedEffectObjects","Escape","Poll","SendDeviceData"})did2.push_back(x);
 static const std::vector<Iface>v{{"IDirectDraw",IID_IDirectDraw,dd1},{"IDirectInputA",IID_IDirectInputA,di},{"IDirectInputDeviceA",IID_IDirectInputDeviceA,did},{"IDirectInputDevice2A",IID_IDirectInputDevice2A,did2},{"IDirect3D3",IID_IDirect3D3,d3},{"IDirect3DDevice3",IID_IDirect3DDevice3,dev3},{"IDirect3DViewport3",IID_IDirect3DViewport3,vp3},{"IDirect3DTexture2",IID_IDirect3DTexture2,tex2},{"IDirect3DMaterial3",IID_IDirect3DMaterial3,mat3},{"IDirectDrawClipper",IID_IDirectDrawClipper,clip},{"IDirectDrawPalette",IID_IDirectDrawPalette,pal},{"IDirectSound",IID_IDirectSound,ds1},{"IDirectSoundBuffer",IID_IDirectSoundBuffer,dsb},{"IDirectPlayLobbyA",lobbyA,l1},{"IDirectPlayLobby2A",lobby2A,l2},{"IDirectPlayLobby3A",lobby3A,l3},{"IDirectDraw2",IID_IDirectDraw2,dd2},{"IDirectDraw4",IID_IDirectDraw4,dd4},
  {"IDirectDrawSurface",IID_IDirectDrawSurface,s1},{"IDirectDrawSurface2",IID_IDirectDrawSurface2,s2},{"IDirectDrawSurface3",IID_IDirectDrawSurface3,s3},{"IDirectDrawSurface4",IID_IDirectDrawSurface4,s4}};return v;}
// x86 guest DDSURFACEDESC (108 bytes) / DDSURFACEDESC2 (124 bytes) field offsets; lpSurface is a guest
// pointer (offset 36) and is never carried across. DDCOLORKEY x4 at 40, DDPIXELFORMAT (32) at 72,
// DDSCAPS at 104 (DDSCAPS2: 16 bytes at 104, then dwTextureStage at 120).
inline constexpr unsigned desc1_size=108,desc2_size=124;
inline const Iface*by_iid(const GUID&g){for(const auto&i:ifaces())if(IsEqualGUID(i.iid,g))return &i;return nullptr;}
inline const Iface*by_name(const std::string&n){for(const auto&i:ifaces())if(n==i.name)return &i;return nullptr;}
inline constexpr unsigned arena=0x37000000,arena_end=0x37100000;
// owner: guest address of the root DirectDraw proxy whose object this belongs to (0 for that root).
// Releasing the last DirectDraw interface of a root destroys its surfaces implicitly (DirectDraw rule).
struct Object{unsigned guest;const Iface*iface;IUnknown*native;bool alive;unsigned owner;unsigned refs{};};  // refs: project-implemented service objects (native==nullptr)
inline bool is_d3d(const Iface*i){return std::strncmp(i->name,"IDirect3D",9)==0;}
inline bool is_lobby(const Iface*i){return std::strncmp(i->name,"IDirectPlayLobby",16)==0;}
inline constexpr unsigned dperr_notlobbied=0x8877042E;
inline bool is_dd(const Iface*i){const std::string n=i->name;return n.rfind("IDirectDraw",0)==0&&n.find("Surface")==std::string::npos;}
struct Provider{HMODULE module{};std::wstring path;std::string sha;HRESULT(WINAPI*create)(GUID*,LPDIRECTDRAW*,IUnknown*){};};
struct InputProvider{HMODULE module{};std::wstring path;std::string sha;HRESULT(WINAPI*create)(HINSTANCE,DWORD,LPDIRECTINPUTA*,LPUNKNOWN){};};
struct SoundProvider{HMODULE module{};std::wstring path;std::string sha;HRESULT(WINAPI*create)(LPCGUID,LPDIRECTSOUND*,LPUNKNOWN){};};
inline bool is_sound(const Iface*i){return std::string(i->name).rfind("IDirectSound",0)==0;}
}
