// Authored bounded call-through instrumentation; proprietary observations stay local.
#define CINTERFACE
#include <initguid.h>
#include <ddraw.h>
#include <d3d.h>
#include <intrin.h>
#include <cstdio>
#include <algorithm>
#include "../in-game-hook/identity.hpp"

using namespace mw34::hook;
using Create = HRESULT(WINAPI *)(GUID *, IDirectDraw **, IUnknown *);
using Query = HRESULT(STDMETHODCALLTYPE *)(void *, REFIID, void **);
using Device = HRESULT(STDMETHODCALLTYPE *)(IDirect3D3 *, REFCLSID, IDirectDrawSurface4 *, IDirect3DDevice3 **, IUnknown *);
using Draw = HRESULT(STDMETHODCALLTYPE *)(IDirect3DDevice3 *, D3DPRIMITIVETYPE, DWORD, void *, DWORD, DWORD);
using Indexed = HRESULT(STDMETHODCALLTYPE *)(IDirect3DDevice3 *, D3DPRIMITIVETYPE, DWORD, void *, DWORD, WORD *, DWORD, DWORD);
using Scene = HRESULT(STDMETHODCALLTYPE *)(IDirect3DDevice3 *);
using RenderState = HRESULT(STDMETHODCALLTYPE *)(IDirect3DDevice3 *, D3DRENDERSTATETYPE, DWORD);
using StageState = HRESULT(STDMETHODCALLTYPE *)(IDirect3DDevice3 *, DWORD, D3DTEXTURESTAGESTATETYPE, DWORD);

enum class Kind { draw1, draw2, draw4, d3d3, device3, viewport3, surface4 };
struct Entry {
    void *object{};
    Kind kind{};
    void *original[64]{};
    void *clone[64]{};
    DWORD filterRender[3]{};
    DWORD filterStage[3]{};
    unsigned filterRenderSequence[3]{};
    unsigned filterStageSequence[3]{};
};
static Entry entries[512];
static unsigned entryCount = 0;
static SRWLOCK registryLock = SRWLOCK_INIT;
static SRWLOCK logLock = SRWLOCK_INIT;
static HANDLE logFile = INVALID_HANDLE_VALUE;
static Create originalCreate{};
static bool live = false;
static unsigned events = 0, draws = 0, scenes = 0, sequence = 0;
static unsigned mockDraws = 0, mockCreates = 0;
static unsigned filterSequence = 0, filterEvents = 0;
static unsigned completedScenes = 0, successfulDraws = 0;
static bool sceneOpen = false;

// Only instrumentation is guarded. The real method executes with its original
// incoming FP/vector state and its resulting state is preserved across logging.
struct State {
    __declspec(align(16)) unsigned char fp[512];
    DWORD error;
    State() : error(GetLastError()) { _fxsave(fp); }
    ~State() { _fxrstor(fp); SetLastError(error); }
};

static void line(const char *payload) {
    State state;
    AcquireSRWLockExclusive(&logLock);
    if (events < 1024 && logFile != INVALID_HANDLE_VALUE) {
        char text[4096];
        const auto n = std::snprintf(text, sizeof(text), "{\"seq\":%u,\"pid\":%lu,\"tid\":%lu,\"live\":%s,%s}\n",
            ++sequence, GetCurrentProcessId(), GetCurrentThreadId(), live ? "true" : "false", payload);
        DWORD written{};
        if (n > 0 && n < static_cast<int>(sizeof(text))) {
            WriteFile(logFile, text, static_cast<DWORD>(n), &written, nullptr);
        }
        ++events;
    }
    ReleaseSRWLockExclusive(&logLock);
}
static unsigned words(Kind kind) {
    switch (kind) {
    case Kind::draw1: return sizeof(IDirectDrawVtbl) / sizeof(void *);
    case Kind::draw2: return sizeof(IDirectDraw2Vtbl) / sizeof(void *);
    case Kind::draw4: return sizeof(IDirectDraw4Vtbl) / sizeof(void *);
    case Kind::d3d3: return sizeof(IDirect3D3Vtbl) / sizeof(void *);
    case Kind::device3: return sizeof(IDirect3DDevice3Vtbl) / sizeof(void *);
    case Kind::viewport3: return sizeof(IDirect3DViewport3Vtbl) / sizeof(void *);
    case Kind::surface4: return sizeof(IDirectDrawSurface4Vtbl) / sizeof(void *);
    }
    return 0;
}
static const char *name(Kind kind) {
    switch (kind) {
    case Kind::draw1: return "IDirectDraw";
    case Kind::draw2: return "IDirectDraw2";
    case Kind::draw4: return "IDirectDraw4";
    case Kind::d3d3: return "IDirect3D3";
    case Kind::device3: return "IDirect3DDevice3";
    case Kind::viewport3: return "IDirect3DViewport3";
    case Kind::surface4: return "IDirectDrawSurface4";
    }
    return "unknown";
}
static void *original(void *object, unsigned slot) {
    State state;
    void *result = nullptr;
    AcquireSRWLockShared(&registryLock);
    for (unsigned i = 0; i < entryCount; ++i)
        if (entries[i].object == object && *static_cast<void ***>(object) == entries[i].clone) {
            result = entries[i].original[slot]; break;
        }
    ReleaseSRWLockShared(&registryLock);
    // A wrapper without its immutable record cannot safely forward.
    if (!result) { line("\"event\":\"fatal\",\"reason\":\"missing_original\""); ExitProcess(92); }
    return result;
}
static HRESULT STDMETHODCALLTYPE query(void *, REFIID, void **);
static HRESULT STDMETHODCALLTYPE createDevice(IDirect3D3 *, REFCLSID, IDirectDrawSurface4 *, IDirect3DDevice3 **, IUnknown *);
static HRESULT STDMETHODCALLTYPE draw(IDirect3DDevice3 *, D3DPRIMITIVETYPE, DWORD, void *, DWORD, DWORD);
static HRESULT STDMETHODCALLTYPE indexed(IDirect3DDevice3 *, D3DPRIMITIVETYPE, DWORD, void *, DWORD, WORD *, DWORD, DWORD);
static HRESULT STDMETHODCALLTYPE beginScene(IDirect3DDevice3 *);
static HRESULT STDMETHODCALLTYPE endScene(IDirect3DDevice3 *);
static HRESULT STDMETHODCALLTYPE setRenderState(IDirect3DDevice3 *, D3DRENDERSTATETYPE, DWORD);
static HRESULT STDMETHODCALLTYPE setStageState(IDirect3DDevice3 *, DWORD, D3DTEXTURESTAGESTATETYPE, DWORD);
static void observe(void *, Kind);
static void coverageViolation(const char *);
static void clearDiagnostic(bool,DWORD,D3DRECT *,DWORD,D3DCOLOR,D3DVALUE,DWORD) noexcept;
#include "coverage.hpp"
namespace present_capture {
inline void before(IDirectDrawSurface4 *) noexcept;
inline void after(IDirectDrawSurface4 *,HRESULT) noexcept;
inline void surfaceOperation(const char *,IDirectDrawSurface4 *,IDirectDrawSurface4 *,DWORD,RECT *,RECT *,DDBLTFX *,DWORD,DWORD) noexcept;
}
#include "presentation.hpp"

static void observe(void *object, Kind kind) {
    State state;
    if (!object) return;
    char record[512];
    AcquireSRWLockExclusive(&registryLock);
    auto *current = *static_cast<void ***>(object);
    for (unsigned i = 0; i < entryCount; ++i) if (current == entries[i].clone) {
        ReleaseSRWLockExclusive(&registryLock); return;
    }
    if (entryCount == 512 || words(kind) > 64) {
        ReleaseSRWLockExclusive(&registryLock);
        line("\"event\":\"coverage_limit\",\"reason\":\"object_budget\""); return;
    }
    auto &e = entries[entryCount];
    SIZE_T copied{};
    if (!ReadProcessMemory(GetCurrentProcess(), current, e.original, words(kind) * sizeof(void *), &copied) || copied != words(kind) * sizeof(void *)) {
        ReleaseSRWLockExclusive(&registryLock);
        line("\"event\":\"coverage_limit\",\"reason\":\"vtable_read\""); return;
    }
    e.object = object; e.kind = kind;
    std::memcpy(e.clone, e.original, words(kind) * sizeof(void *));
    e.clone[0] = reinterpret_cast<void *>(&query);
    installCoverage(e);
    installPresentation(e);
    if (kind == Kind::d3d3)
        e.clone[offsetof(IDirect3D3Vtbl, CreateDevice) / sizeof(void *)] = reinterpret_cast<void *>(&createDevice);
    if (kind == Kind::device3) {
        e.clone[offsetof(IDirect3DDevice3Vtbl, DrawPrimitive) / sizeof(void *)] = reinterpret_cast<void *>(&draw);
        e.clone[offsetof(IDirect3DDevice3Vtbl, DrawIndexedPrimitive) / sizeof(void *)] = reinterpret_cast<void *>(&indexed);
        e.clone[offsetof(IDirect3DDevice3Vtbl, BeginScene) / sizeof(void *)] = reinterpret_cast<void *>(&beginScene);
        e.clone[offsetof(IDirect3DDevice3Vtbl, EndScene) / sizeof(void *)] = reinterpret_cast<void *>(&endScene);
        e.clone[offsetof(IDirect3DDevice3Vtbl, SetRenderState) / sizeof(void *)] = reinterpret_cast<void *>(&setRenderState);
        e.clone[offsetof(IDirect3DDevice3Vtbl, SetTextureStageState) / sizeof(void *)] = reinterpret_cast<void *>(&setStageState);
    }
    ++entryCount; // Publish immutable forwarding metadata before changing object.
    auto *previous = InterlockedCompareExchangePointer(reinterpret_cast<void *volatile *>(object), e.clone, current);
    const bool installed = previous == current;
    ReleaseSRWLockExclusive(&registryLock);
    std::snprintf(record, sizeof(record), "\"event\":\"object\",\"interface\":\"%s\",\"object\":%u,\"original_vtable\":%u,\"slots\":%u,\"installed\":%s",
        name(kind), reinterpret_cast<unsigned>(object), reinterpret_cast<unsigned>(current), words(kind), installed ? "true" : "false");
    line(record);
}
static void guidText(REFIID id, char (&text)[40]) {
    std::snprintf(text, sizeof(text), "%08lx-%04x-%04x-%02x%02x-%02x%02x%02x%02x%02x%02x",
        id.Data1, id.Data2, id.Data3, id.Data4[0], id.Data4[1], id.Data4[2], id.Data4[3], id.Data4[4], id.Data4[5], id.Data4[6], id.Data4[7]);
}
static HRESULT STDMETHODCALLTYPE query(void *self, REFIID id, void **output) {
    const auto call = reinterpret_cast<Query>(original(self, 0));
    const auto result = call(self, id, output);
    {
        State state;
        if (SUCCEEDED(result) && output && *output) {
            if (IsEqualGUID(id, IID_IDirectDraw)) observe(*output, Kind::draw1);
            else if (IsEqualGUID(id, IID_IDirectDraw2)) observe(*output, Kind::draw2);
            else if (IsEqualGUID(id, IID_IDirectDraw4)) observe(*output, Kind::draw4);
            else if (IsEqualGUID(id, IID_IDirect3D3)) observe(*output, Kind::d3d3);
            else if (IsEqualGUID(id, IID_IDirect3DDevice3)) observe(*output, Kind::device3);
            else if (IsEqualGUID(id, IID_IDirect3DViewport3)) observe(*output, Kind::viewport3);
            else if (IsEqualGUID(id, IID_IDirectDrawSurface4)) observeSurface(static_cast<IDirectDrawSurface4 *>(*output));
        }
        char guid[40], text[384]; guidText(id, guid);
        std::snprintf(text, sizeof(text), "\"event\":\"query_interface\",\"object\":%u,\"iid\":\"%s\",\"hresult\":%ld,\"output\":%u",
            reinterpret_cast<unsigned>(self), guid, result, SUCCEEDED(result) && output ? reinterpret_cast<unsigned>(*output) : 0U);
        line(text);
    }
    return result;
}
static HRESULT WINAPI create(GUID *adapter, IDirectDraw **output, IUnknown *outer) {
    const auto result = originalCreate(adapter, output, outer);
    {
        State state;
        char text[384];
        std::snprintf(text, sizeof(text), "\"event\":\"direct_draw_create\",\"hresult\":%ld,\"adapter_pointer\":%u,\"outer\":%u,\"output\":%u,\"provider_entry\":%u",
            result, reinterpret_cast<unsigned>(adapter), reinterpret_cast<unsigned>(outer), SUCCEEDED(result) && output ? reinterpret_cast<unsigned>(*output) : 0U, reinterpret_cast<unsigned>(originalCreate));
        line(text);
        if (SUCCEEDED(result) && output) observe(*output, Kind::draw1);
    }
    return result;
}
static HRESULT STDMETHODCALLTYPE createDevice(IDirect3D3 *self, REFCLSID id, IDirectDrawSurface4 *target, IDirect3DDevice3 **output, IUnknown *outer) {
    const auto call = reinterpret_cast<Device>(original(self, offsetof(IDirect3D3Vtbl, CreateDevice) / sizeof(void *)));
    const auto result = call(self, id, target, output, outer);
    {
        State state;
        char guid[40], text[384]; guidText(id, guid);
        std::snprintf(text, sizeof(text), "\"event\":\"create_device\",\"device_guid\":\"%s\",\"hresult\":%ld,\"target\":%u,\"output\":%u",
            guid, result, reinterpret_cast<unsigned>(target), SUCCEEDED(result) && output ? reinterpret_cast<unsigned>(*output) : 0U);
        line(text);
        if (SUCCEEDED(result) && output) observe(*output, Kind::device3);
        if (SUCCEEDED(result))observeSurface(target);
    }
    return result;
}
static unsigned stride(DWORD fvf) {
    // Only the documented XYZ/XYZRHW non-blended layouts, 2D texture coords.
    const auto position = fvf & D3DFVF_POSITION_MASK;
    if (position != D3DFVF_XYZ && position != D3DFVF_XYZRHW) return 0;
    if (fvf & ~(D3DFVF_POSITION_MASK | D3DFVF_NORMAL | D3DFVF_DIFFUSE | D3DFVF_SPECULAR | D3DFVF_TEXCOUNT_MASK)) return 0;
    unsigned size = position == D3DFVF_XYZRHW ? 16U : 12U;
    if (fvf & D3DFVF_NORMAL) size += 12;
    if (fvf & D3DFVF_DIFFUSE) size += 4;
    if (fvf & D3DFVF_SPECULAR) size += 4;
    const auto textures = (fvf & D3DFVF_TEXCOUNT_MASK) >> D3DFVF_TEXCOUNT_SHIFT;
    if (textures > 8) return 0;
    return size + textures * 8;
}
static std::string filteringHistory(void *object);
#include "capture.hpp"
#include "present_capture.hpp"
static void clearDiagnostic(bool explicitValues,DWORD count,D3DRECT *rects,DWORD flags,D3DCOLOR color,D3DVALUE depth,DWORD stencil) noexcept {
    State guard;
    if(!live || !frame_capture::active)return;
    try {
        if(count>64)throw std::runtime_error("clear_rectangle_budget");
        DWORD bits{};std::memcpy(&bits,&depth,4);
        std::string rectangles="null";
        if(count)rectangles="\""+frame_capture::memory(rects,static_cast<size_t>(count)*sizeof(D3DRECT))+"\"";
        frame_capture::record("{\"event\":\"unsupported_clear\",\"explicit_values\":"+std::string(explicitValues?"true":"false")+",\"count\":"+std::to_string(count)+",\"rectangles\":"+rectangles+",\"flags\":"+std::to_string(flags)+",\"color_argb\":"+std::to_string(color)+",\"depth_bits\":"+std::to_string(bits)+",\"stencil\":"+std::to_string(stencil)+"}");
    } catch(const std::exception &e) {frame_capture::abort(e.what());}
}
static void coverageViolation(const char *method) {
    State guard;
    if(frame_capture::active)frame_capture::abort(method);
}
// Track successful requests from device creation onward, including before arming.
// Never infer an effective state from a failed setter or from another device.
static void rememberFiltering(void *object, bool stage, unsigned index, DWORD value, HRESULT hr) {
    State guard;
    AcquireSRWLockExclusive(&registryLock);
    const auto serial = ++filterSequence;
    if (SUCCEEDED(hr)) {
        for (unsigned i = 0; i < entryCount; ++i)
            if (entries[i].object == object && *static_cast<void ***>(object) == entries[i].clone) {
                auto &e = entries[i];
                (stage ? e.filterStage : e.filterRender)[index] = value;
                (stage ? e.filterStageSequence : e.filterRenderSequence)[index] = serial;
                break;
            }
    }
    const bool log = filterEvents++ < 128;
    ReleaseSRWLockExclusive(&registryLock);
    if (log) {
        char text[384];
        std::snprintf(text,sizeof(text),"\"event\":\"filter_setter\",\"object\":%u,\"api\":\"%s\",\"index\":%u,\"value\":%lu,\"hresult\":%ld,\"serial\":%u",
            reinterpret_cast<unsigned>(object),stage?"stage0":"legacy_render",index,value,hr,serial);
        line(text);
    }
}
static std::string filteringHistory(void *object) {
    State guard;
    std::ostringstream out;
    out << "{\"legacy_render\":[";
    AcquireSRWLockShared(&registryLock);
    Entry *entry=nullptr;
    for(unsigned i=0;i<entryCount;++i)
        if(entries[i].object==object && *static_cast<void ***>(object)==entries[i].clone) {entry=&entries[i];break;}
    for(unsigned group=0;group<2;++group) {
        if(group)out<<"],\"stage0\":[";
        for(unsigned i=0;i<3;++i) {
            if(i)out<<',';
            const auto serial=entry?(group?entry->filterStageSequence:entry->filterRenderSequence)[i]:0;
            if(!serial)out<<"null";
            else out<<"{\"value\":"<<(group?entry->filterStage:entry->filterRender)[i]<<",\"serial\":"<<serial<<'}';
        }
    }
    ReleaseSRWLockShared(&registryLock);
    out<<"]}";return out.str();
}
static HRESULT STDMETHODCALLTYPE setRenderState(IDirect3DDevice3 *self,D3DRENDERSTATETYPE type,DWORD value) {
    const auto call=reinterpret_cast<RenderState>(original(self,offsetof(IDirect3DDevice3Vtbl,SetRenderState)/sizeof(void *)));
    const auto result=call(self,type,value);
    if(type==D3DRENDERSTATE_TEXTUREMAG)rememberFiltering(self,false,0,value,result);
    else if(type==D3DRENDERSTATE_TEXTUREMIN)rememberFiltering(self,false,1,value,result);
    else if(type==D3DRENDERSTATE_TEXTUREMAPBLEND)rememberFiltering(self,false,2,value,result);
    return result;
}
static HRESULT STDMETHODCALLTYPE setStageState(IDirect3DDevice3 *self,DWORD stage,D3DTEXTURESTAGESTATETYPE type,DWORD value) {
    const auto call=reinterpret_cast<StageState>(original(self,offsetof(IDirect3DDevice3Vtbl,SetTextureStageState)/sizeof(void *)));
    const auto result=call(self,stage,type,value);
    if(stage==0 && type==D3DTSS_MAGFILTER)rememberFiltering(self,true,0,value,result);
    else if(stage==0 && type==D3DTSS_MINFILTER)rememberFiltering(self,true,1,value,result);
    else if(stage==0 && type==D3DTSS_MIPFILTER)rememberFiltering(self,true,2,value,result);
    return result;
}
static void drawRecord(const char *event, IDirect3DDevice3 *self, D3DPRIMITIVETYPE type, DWORD fvf, void *vertices, DWORD vertexCount, WORD *indices, DWORD indexCount, DWORD flags, HRESULT result) {
    State state;
    if (InterlockedIncrement(reinterpret_cast<volatile LONG *>(&draws)) > 64) return;
    const unsigned vertexStride = stride(fvf);
    unsigned char sample[256]{}; SIZE_T copied{};
    const unsigned sampleSize = vertexStride ? (std::min)(256U, vertexStride * static_cast<unsigned>((std::min)(vertexCount, 3UL))) : 0;
    if (sampleSize && !ReadProcessMemory(GetCurrentProcess(), vertices, sample, sampleSize, &copied)) copied = 0;
    char hex[513]{};
    for (unsigned i = 0; i < copied; ++i) std::snprintf(hex + i * 2, 3, "%02x", sample[i]);
    char text[1600];
    std::snprintf(text, sizeof(text), "\"event\":\"%s\",\"object\":%u,\"primitive\":%u,\"fvf\":%lu,\"vertex_count\":%lu,\"index_count\":%lu,\"flags\":%lu,\"hresult\":%ld,\"vertex_stride\":%u,\"transformed\":%s,\"vertex_pointer\":%u,\"index_pointer\":%u,\"sample_bytes\":%u,\"sample_hex\":\"%s\"",
        event, reinterpret_cast<unsigned>(self), static_cast<unsigned>(type), fvf, vertexCount, indexCount, flags, result, vertexStride,
        (fvf & D3DFVF_POSITION_MASK) == D3DFVF_XYZRHW ? "true" : "false", reinterpret_cast<unsigned>(vertices), reinterpret_cast<unsigned>(indices), static_cast<unsigned>(copied), hex);
    line(text);
}
static HRESULT STDMETHODCALLTYPE draw(IDirect3DDevice3 *self, D3DPRIMITIVETYPE type, DWORD fvf, void *vertices, DWORD count, DWORD flags) {
    auto call = reinterpret_cast<Draw>(original(self, offsetof(IDirect3DDevice3Vtbl, DrawPrimitive) / sizeof(void *)));
    frame_capture::draw(self,type,fvf,vertices,count,nullptr,0,flags);
    const auto result = call(self, type, fvf, vertices, count, flags);
    {State guard;if(live && SUCCEEDED(result))++successfulDraws;}
    frame_capture::result(result);
    drawRecord("draw_primitive", self, type, fvf, vertices, count, nullptr, 0, flags, result);
    return result;
}
static HRESULT STDMETHODCALLTYPE indexed(IDirect3DDevice3 *self, D3DPRIMITIVETYPE type, DWORD fvf, void *vertices, DWORD count, WORD *indices, DWORD indexCount, DWORD flags) {
    auto call = reinterpret_cast<Indexed>(original(self, offsetof(IDirect3DDevice3Vtbl, DrawIndexedPrimitive) / sizeof(void *)));
    frame_capture::draw(self,type,fvf,vertices,count,indices,indexCount,flags);
    const auto result = call(self, type, fvf, vertices, count, indices, indexCount, flags);
    {State guard;if(live && SUCCEEDED(result))++successfulDraws;}
    frame_capture::result(result);
    drawRecord("draw_indexed_primitive", self, type, fvf, vertices, count, indices, indexCount, flags, result);
    return result;
}
static HRESULT scene(IDirect3DDevice3 *self, unsigned slot, const char *event) {
    auto call = reinterpret_cast<Scene>(original(self, slot));
    const auto result = call(self);
    {
        State state;
        if (InterlockedIncrement(reinterpret_cast<volatile LONG *>(&scenes)) <= 64) {
            char text[192]; std::snprintf(text, sizeof(text), "\"event\":\"%s\",\"hresult\":%ld,\"object\":%u", event, result, reinterpret_cast<unsigned>(self)); line(text);
        }
    }
    return result;
}
static HRESULT STDMETHODCALLTYPE beginScene(IDirect3DDevice3 *self) {
    const auto result=scene(self, offsetof(IDirect3DDevice3Vtbl, BeginScene) / sizeof(void *), "begin_scene");
    {State guard;if(live && SUCCEEDED(result))sceneOpen=true;}
    frame_capture::begin(self,result);return result;
}
static HRESULT STDMETHODCALLTYPE endScene(IDirect3DDevice3 *self) {
    const auto result=scene(self, offsetof(IDirect3DDevice3Vtbl, EndScene) / sizeof(void *), "end_scene");
    frame_capture::end(self,result);
    {State guard;if(live && SUCCEEDED(result)){sceneOpen=false;++completedScenes;}}
    return result;
}

// Authored typed COM fixtures. They are never counted as live observations.
static void *fake1[64], *fake4[64], *fake3[64], *fakeDevice[64];
static void **object1 = fake1, **object4 = fake4, **object3 = fake3, **objectDevice = fakeDevice;
static HRESULT STDMETHODCALLTYPE fakeQuery(void *, REFIID id, void **output) {
    SetLastError(0x12345678);
    if (IsEqualGUID(id, IID_IDirectDraw4)) { *output = &object4; return S_OK; }
    if (IsEqualGUID(id, IID_IDirect3D3)) { *output = &object3; return S_OK; }
    return E_NOINTERFACE;
}
static HRESULT WINAPI fakeCreate(GUID *, IDirectDraw **output, IUnknown *) { ++mockCreates; *output = reinterpret_cast<IDirectDraw *>(&object1); SetLastError(0x87654321); return S_OK; }
static HRESULT STDMETHODCALLTYPE fakeDeviceCreate(IDirect3D3 *, REFCLSID, IDirectDrawSurface4 *, IDirect3DDevice3 **output, IUnknown *) { *output = reinterpret_cast<IDirect3DDevice3 *>(&objectDevice); SetLastError(0x33445566); return S_OK; }
static HRESULT STDMETHODCALLTYPE fakeDraw(IDirect3DDevice3 *self, D3DPRIMITIVETYPE type, DWORD fvf, void *vertices, DWORD count, DWORD flags) {
    if (self != reinterpret_cast<IDirect3DDevice3 *>(&objectDevice) || type != D3DPT_TRIANGLELIST || fvf != D3DFVF_TLVERTEX || !vertices || count != 3 || flags != 0x1234) return E_INVALIDARG;
    ++mockDraws; SetLastError(0x55667788); return S_FALSE;
}
static HRESULT STDMETHODCALLTYPE fakeIndexed(IDirect3DDevice3 *self, D3DPRIMITIVETYPE type, DWORD fvf, void *vertices, DWORD count, WORD *indices, DWORD indexCount, DWORD flags) {
    if (!indices || indexCount != 3 || indices[2] != 2) return E_INVALIDARG;
    return fakeDraw(self, type, fvf, vertices, count, flags);
}
static HRESULT STDMETHODCALLTYPE fakeScene(IDirect3DDevice3 *) { SetLastError(0x11223344); return S_FALSE; }
static HRESULT STDMETHODCALLTYPE fakeRenderState(IDirect3DDevice3 *,D3DRENDERSTATETYPE type,DWORD value) {
    SetLastError(0x99aabbcc);
    return type==D3DRENDERSTATE_TEXTUREMAG && value==D3DFILTER_LINEAR ? S_FALSE : E_INVALIDARG;
}
static HRESULT STDMETHODCALLTYPE fakeStageState(IDirect3DDevice3 *,DWORD stage,D3DTEXTURESTAGESTATETYPE type,DWORD value) {
    SetLastError(0xddeeff11);
    return stage==0 && type==D3DTSS_MAGFILTER && value==D3DTFG_LINEAR ? S_FALSE : E_INVALIDARG;
}
#include "capture_fixture.hpp"
#include "coverage_fixture.hpp"
#include "presentation_fixture.hpp"
#include "hud_text.hpp"
#include "hud_draw.hpp"
#include "hud_heat.hpp"
static void tests() {
    __declspec(align(16)) unsigned char before[512]{}, after[512]{};
    SetLastError(0xaabbccdd);
    _fxsave(before);
    {
        State preservation;
        SetLastError(0);
        _mm_setcsr(_mm_getcsr() ^ 0x6000U);
    }
    _fxsave(after);
    if (std::memcmp(before,after,512) || GetLastError() != 0xaabbccdd)
        throw std::runtime_error("FP/vector/last-error guard failed");
    setupCaptureFixture();
    setupCoverageFixture();
    setupPresentationFixture();
    flipWindowFixture();
    hud_text::fixture();
    hud_draw::fixture();
    hud_heat::fixture();
    fake1[0] = fake4[0] = fake3[0] = fakeDevice[0] = reinterpret_cast<void *>(&fakeQuery);
    fake3[offsetof(IDirect3D3Vtbl, CreateDevice) / sizeof(void *)] = reinterpret_cast<void *>(&fakeDeviceCreate);
    fakeDevice[offsetof(IDirect3DDevice3Vtbl, DrawPrimitive) / sizeof(void *)] = reinterpret_cast<void *>(&fakeDraw);
    fakeDevice[offsetof(IDirect3DDevice3Vtbl, DrawIndexedPrimitive) / sizeof(void *)] = reinterpret_cast<void *>(&fakeIndexed);
    fakeDevice[offsetof(IDirect3DDevice3Vtbl, BeginScene) / sizeof(void *)] = reinterpret_cast<void *>(&fakeScene);
    fakeDevice[offsetof(IDirect3DDevice3Vtbl, EndScene) / sizeof(void *)] = reinterpret_cast<void *>(&fakeScene);
    fakeDevice[offsetof(IDirect3DDevice3Vtbl, SetRenderState) / sizeof(void *)] = reinterpret_cast<void *>(&fakeRenderState);
    fakeDevice[offsetof(IDirect3DDevice3Vtbl, SetTextureStageState) / sizeof(void *)] = reinterpret_cast<void *>(&fakeStageState);
    auto saved = originalCreate; originalCreate = fakeCreate;
    IDirectDraw *dd{}; if (create(nullptr, &dd, nullptr) != S_OK || GetLastError() != 0x87654321) throw std::runtime_error("Create forwarding failed");
    void *dd4{}; if (dd->lpVtbl->QueryInterface(dd, IID_IDirectDraw4, &dd4) != S_OK || dd4 != &object4 || GetLastError() != 0x12345678) throw std::runtime_error("QI forwarding failed");
    auto *four = static_cast<IDirectDraw4 *>(dd4); void *d3d{};
    if (four->lpVtbl->QueryInterface(four, IID_IDirect3D3, &d3d) != S_OK) throw std::runtime_error("D3D QI failed");
    void *denied = reinterpret_cast<void *>(0x1234);
    if (four->lpVtbl->QueryInterface(four, IID_IDirectDraw7, &denied) != E_NOINTERFACE || denied != reinterpret_cast<void *>(0x1234)) throw std::runtime_error("QI failure changed output");
    auto *three = static_cast<IDirect3D3 *>(d3d); IDirect3DDevice3 *device{};
    if (three->lpVtbl->CreateDevice(three, IID_IDirect3DHALDevice, nullptr, &device, nullptr) != S_OK || GetLastError() != 0x33445566) throw std::runtime_error("Device forwarding failed");
    std::array<unsigned char,96> vertices{}; const auto previous = vertices;
    WORD indices[3]{0,1,2};
    if (device->lpVtbl->DrawPrimitive(device,D3DPT_TRIANGLELIST,D3DFVF_TLVERTEX,vertices.data(),3,0x1234) != S_FALSE || GetLastError() != 0x55667788) throw std::runtime_error("Draw forwarding failed");
    if (device->lpVtbl->DrawIndexedPrimitive(device,D3DPT_TRIANGLELIST,D3DFVF_TLVERTEX,vertices.data(),3,indices,3,0x1234) != S_FALSE || GetLastError() != 0x55667788 || vertices != previous || indices[2] != 2) throw std::runtime_error("Indexed forwarding failed");
    if (device->lpVtbl->DrawPrimitive(device,D3DPT_TRIANGLELIST,D3DFVF_TLVERTEX,vertices.data(),3,0) != E_INVALIDARG || vertices != previous)
        throw std::runtime_error("Failed draw forwarding changed result/data");
    if (device->lpVtbl->BeginScene(device) != S_FALSE || device->lpVtbl->EndScene(device) != S_FALSE || GetLastError() != 0x11223344) throw std::runtime_error("Scene forwarding failed");
    if (stride(D3DFVF_TLVERTEX) != 32 || stride(D3DFVF_VERTEX) != 32 || stride(0) != 0 || mockDraws != 2 || mockCreates != 1) throw std::runtime_error("Fixture/stride accounting failed");
    captureFixture(device,vertices.data(),indices);
    if(device->lpVtbl->SetRenderState(device,D3DRENDERSTATE_TEXTUREMAG,D3DFILTER_LINEAR)!=S_FALSE || GetLastError()!=0x99aabbcc)
        throw std::runtime_error("Legacy filter setter forwarding failed");
    if(device->lpVtbl->SetTextureStageState(device,0,D3DTSS_MAGFILTER,D3DTFG_LINEAR)!=S_FALSE || GetLastError()!=0xddeeff11)
        throw std::runtime_error("Stage filter setter forwarding failed");
    const auto filterBefore=filteringHistory(device);
    if(filterBefore.find("\"value\":2")==std::string::npos || filterBefore.find("\"serial\":")==std::string::npos)
        throw std::runtime_error("Filter tracking failed");
    if(device->lpVtbl->SetRenderState(device,D3DRENDERSTATE_TEXTUREMAG,0)!=E_INVALIDARG || GetLastError()!=0x99aabbcc || filteringHistory(device)!=filterBefore)
        throw std::runtime_error("Failed legacy filter setter changed history");
    if(device->lpVtbl->SetTextureStageState(device,0,D3DTSS_MAGFILTER,0)!=E_INVALIDARG || GetLastError()!=0xddeeff11 || filteringHistory(device)!=filterBefore)
        throw std::runtime_error("Failed stage filter setter changed history");
    line("\"event\":\"filter_fixture\",\"passed\":true,\"failed_setters_preserved\":true,\"last_error_preserved\":true");
    coverageFixture(device,vertices.data(),indices);
    presentationFixture(four);
    originalCreate = saved;
    line("\"event\":\"selftest\",\"passed\":true,\"typed_methods\":7,\"draws\":2,\"last_error_preserved\":true,\"failed_qi_preserved\":true,\"failed_draw_preserved\":true,\"fp_vector_guard_verified\":true");
}
static void openLog() {
    logFile = CreateFileW(environment(L"MW34_HOOK_LOG").c_str(), GENERIC_WRITE, FILE_SHARE_READ, nullptr, CREATE_NEW, FILE_ATTRIBUTE_NORMAL, nullptr);
    if (logFile == INVALID_HANDLE_VALUE) throw std::runtime_error("Cannot create fresh trace");
}
extern "C" DWORD WINAPI mw34_selftest(void *) {
    try { admitted_image(environment(L"MW34_GAME_FILE")); openLog(); tests(); return 0; }
    catch (const std::exception &e) { OutputDebugStringA(e.what()); return 90; }
}
extern "C" DWORD WINAPI mw34_install(void *) {
    try {
        wchar_t path[32768]; const auto count = GetModuleFileNameW(nullptr, path, 32768);
        if (!count || count >= 32768 || reinterpret_cast<unsigned>(GetModuleHandleW(nullptr)) != 0x400000) throw std::runtime_error("Unsupported loaded image");
        admitted_image(std::wstring(path,count)); openLog(); tests();
        auto *slot = reinterpret_cast<void **>(0x5bb044);
        originalCreate = reinterpret_cast<Create>(*slot);
        // Identify the exact loaded provider separately from admitted game identity.
        HMODULE provider{};
        if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
            reinterpret_cast<LPCWSTR>(originalCreate), &provider)) throw std::runtime_error("Provider module missing");
        wchar_t providerPath[32768]; const auto length = GetModuleFileNameW(provider,providerPath,32768);
        if (!length || length >= 32768) throw std::runtime_error("Provider path missing");
        std::ifstream file(std::filesystem::path(std::wstring(providerPath,length)),std::ios::binary|std::ios::ate);
        if (!file || file.tellg() <= 0 || file.tellg() > 128*1024*1024) throw std::runtime_error("Provider file unavailable");
        std::vector<unsigned char> bytes(static_cast<size_t>(file.tellg()));file.seekg(0);file.read(reinterpret_cast<char *>(bytes.data()),static_cast<std::streamsize>(bytes.size()));
        if (!file) throw std::runtime_error("Provider read failed");
        const auto hash = sha256(bytes.data(),bytes.size());
        char text[384];std::snprintf(text,sizeof(text),"\"event\":\"provider\",\"base\":%u,\"entry\":%u,\"sha256\":\"%s\",\"size\":%u",reinterpret_cast<unsigned>(provider),reinterpret_cast<unsigned>(originalCreate),hash.c_str(),static_cast<unsigned>(bytes.size()));line(text);
        DWORD old{};if(!VirtualProtect(slot,4,PAGE_READWRITE,&old)) throw std::runtime_error("IAT protection failed");
        auto *previous = InterlockedExchangePointer(slot,reinterpret_cast<void *>(&create));
        DWORD ignored{};
        if(previous != reinterpret_cast<void *>(originalCreate) || !VirtualProtect(slot,4,old,&ignored)) throw std::runtime_error("IAT publication failed");
        hud_text::install();
        hud_draw::install();
        hud_heat::install();
        draws = scenes = 0; live = true;
        line("\"event\":\"installed\",\"iat_va\":6008900,\"on_disk_game_unchanged\":true,\"mode\":\"bounded_call_through\"");
        return 0;
    } catch(const std::exception &e) { OutputDebugStringA(e.what()); return 90; }
}
BOOL WINAPI DllMain(HINSTANCE,DWORD,LPVOID) { return TRUE; }
