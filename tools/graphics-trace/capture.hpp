#pragma once
#include <sstream>
#include <set>
#include <utility>

// One explicitly armed BeginScene/EndScene interval. All payloads stay local.
namespace frame_capture {
static std::filesystem::path root;
static std::ofstream manifest;
static bool active = false, attempted = false;
static unsigned commandCount = 0;
static size_t storedBytes = 0, scannedBytes = 0;
static std::set<std::string> stored;
static IDirectDrawSurface4 *initialTarget = nullptr;
static unsigned skippedScenes = 0, requestedSkip = 0;
static bool armRead = false;
static bool presentationMode = false;
static DWORD presentationThread = 0;
static unsigned minimumDraws = 0, candidateCount = 0;

inline void record(const std::string &text) {
    manifest << text << '\n'; manifest.flush();
    if (!manifest) throw std::runtime_error("manifest_write");
}
inline std::string payload(const void *data, size_t size) {
    if (size > 16U * 1024U * 1024U || scannedBytes + size > 512U * 1024U * 1024U)
        throw std::runtime_error("payload_scan_budget");
    scannedBytes += size;
    const auto hash = sha256(data,size);
    const auto filename = hash + ".bin";
    if (stored.insert(filename).second) {
        if (storedBytes + size > 64U * 1024U * 1024U) throw std::runtime_error("payload_storage_budget");
        std::ofstream file(root / filename,std::ios::binary);
        file.write(static_cast<const char *>(data),static_cast<std::streamsize>(size));file.close();
        if (!file) throw std::runtime_error("payload_write");
        storedBytes += size;
    }
    return filename;
}
inline std::string memory(const void *address, size_t size) {
    if (!size || size > 16U * 1024U * 1024U) throw std::runtime_error("draw_memory_size");
    std::vector<unsigned char> bytes(size);SIZE_T copied{};
    if (!ReadProcessMemory(GetCurrentProcess(),address,bytes.data(),size,&copied) || copied != size)
        throw std::runtime_error("draw_memory_read");
    return payload(bytes.data(),bytes.size());
}
inline void abort(const char *reason) noexcept {
    active = false;
    try {
        if (manifest.is_open()) { manifest << "{\"event\":\"abort\",\"reason\":\"" << reason << "\"}\n"; manifest.close(); }
        line("\"event\":\"capture_incomplete\"");
    } catch (...) {}
}
struct SurfaceRef {
    IDirectDrawSurface4 *surface{};
    SurfaceRef() = default;
    SurfaceRef(const SurfaceRef &) = delete;
    SurfaceRef &operator=(const SurfaceRef &) = delete;
    SurfaceRef(SurfaceRef &&other) noexcept : surface(std::exchange(other.surface,nullptr)) {}
    ~SurfaceRef() { if(surface) surface->lpVtbl->Release(surface); }
};
inline std::string surface(IDirectDrawSurface4 *object) {
    DDSURFACEDESC2 desc{};desc.dwSize=sizeof(desc);
    const auto result=object->lpVtbl->Lock(object,nullptr,&desc,DDLOCK_READONLY | DDLOCK_WAIT,nullptr);
    if(FAILED(result)) throw std::runtime_error("surface_lock");
    std::string text;
    try {
        const auto bits=desc.ddpfPixelFormat.dwRGBBitCount;
        if(!desc.dwWidth || !desc.dwHeight || desc.dwWidth>4096 || desc.dwHeight>4096 ||
           (bits!=8 && bits!=16 && bits!=24 && bits!=32) || !desc.lpSurface)
            throw std::runtime_error("surface_layout");
        const size_t row=static_cast<size_t>(desc.dwWidth)*(bits/8);
        const auto pitch=static_cast<int64_t>(desc.lPitch);
        if(pitch==0 || (pitch<0 ? -pitch : pitch)<static_cast<int64_t>(row) || row*desc.dwHeight>16U*1024U*1024U)
            throw std::runtime_error("surface_pitch");
        std::vector<unsigned char> bytes(row*desc.dwHeight);
        for(DWORD y=0;y<desc.dwHeight;++y) {
            const auto address=reinterpret_cast<uintptr_t>(desc.lpSurface)+static_cast<intptr_t>(pitch*y);
            SIZE_T copied{};
            if(!ReadProcessMemory(GetCurrentProcess(),reinterpret_cast<void *>(address),bytes.data()+row*y,row,&copied) || copied!=row)
                throw std::runtime_error("surface_read");
        }
        std::ostringstream out;
        out<<"{\"width\":"<<desc.dwWidth<<",\"height\":"<<desc.dwHeight<<",\"source_pitch\":"<<desc.lPitch
           <<",\"row_bytes\":"<<row<<",\"flags\":"<<desc.ddpfPixelFormat.dwFlags<<",\"bits\":"<<bits
           <<",\"r_mask\":"<<desc.ddpfPixelFormat.dwRBitMask<<",\"g_mask\":"<<desc.ddpfPixelFormat.dwGBitMask
           <<",\"b_mask\":"<<desc.ddpfPixelFormat.dwBBitMask<<",\"a_mask\":"<<desc.ddpfPixelFormat.dwRGBAlphaBitMask
           <<",\"fourcc\":"<<desc.ddpfPixelFormat.dwFourCC<<",\"caps\":"<<desc.ddsCaps.dwCaps
           <<",\"file\":\""<<payload(bytes.data(),bytes.size())<<"\"}";
        text=out.str();
    } catch(...) { object->lpVtbl->Unlock(object,nullptr);throw; }
    if(FAILED(object->lpVtbl->Unlock(object,nullptr))) throw std::runtime_error("surface_unlock");
    return text;
}
inline SurfaceRef target(IDirect3DDevice3 *device) {
    SurfaceRef result;
    if(FAILED(device->lpVtbl->GetRenderTarget(device,&result.surface)) || !result.surface)
        throw std::runtime_error("get_render_target");
    return result;
}
inline void begin(IDirect3DDevice3 *device, HRESULT result, bool authored=false) noexcept {
    State guard;
    if(active && presentationMode) {
        try {
            if(FAILED(result) || GetCurrentThreadId()!=presentationThread)throw std::runtime_error("present_scene_begin_failed_or_thread_changed");
            auto renderTarget=target(device);
            if(renderTarget.surface!=initialTarget)throw std::runtime_error("render_target_changed");
            record("{\"event\":\"scene_begin\"}");
        } catch(const std::exception &e) {abort(e.what());}
        return;
    }
    if((!live && !authored) || attempted || FAILED(result)) return;
    try {
        root=std::filesystem::path(environment(L"MW34_HOOK_LOG")).parent_path()/
            (authored ? "fixture-frame-"+std::to_string(GetCurrentProcessId()) : "frame");
        const auto marker=root.parent_path()/"capture.request";
        if(!authored && !std::filesystem::exists(marker)) return;
        if(!authored) {
            if(!armRead) {
                std::ifstream request(marker);std::string value,minimum;
                if(!request)throw std::runtime_error("capture_request_read");
                request>>value;
                if(!value.empty()) {
                    if(value.size()>5 || value.find_first_not_of("0123456789")!=std::string::npos)
                        throw std::runtime_error("invalid_capture_delay");
                    requestedSkip=static_cast<unsigned>(std::stoul(value));
                    if(requestedSkip>36000)throw std::runtime_error("capture_delay_limit");
                }
                if(request>>minimum) {
                    if(minimum.size()>4 || minimum.find_first_not_of("0123456789")!=std::string::npos)
                        throw std::runtime_error("invalid_capture_minimum");
                    minimumDraws=static_cast<unsigned>(std::stoul(minimum));
                    if(minimumDraws>2048)throw std::runtime_error("capture_minimum_limit");
                }
                armRead=true;
            }
            if(skippedScenes<requestedSkip) {++skippedScenes;return;}
        }
        attempted=true;
        if(!std::filesystem::create_directory(root)) throw std::runtime_error("fresh_capture_directory");
        manifest.open(root/"capture.jsonl",std::ios::binary);
        if(!manifest) throw std::runtime_error("capture_manifest_open");
        record("{\"event\":\"begin\",\"schema_version\":1,\"live\":"+std::string(authored?"false":"true")+",\"pid\":"+std::to_string(GetCurrentProcessId())+",\"skipped_scenes\":"+std::to_string(authored?0:skippedScenes)+",\"requested_skip\":"+std::to_string(authored?0:requestedSkip)+",\"minimum_draws\":"+std::to_string(authored?0:minimumDraws)+",\"candidate\":"+std::to_string(authored?0:++candidateCount)+",\"scope\":\"one_BeginScene_EndScene_interval\"}");
        auto renderTarget=target(device);initialTarget=renderTarget.surface;
        record("{\"event\":\"initial_target\",\"surface\":"+surface(renderTarget.surface)+"}");
        SurfaceRef depth;
        DDSCAPS2 caps{};caps.dwCaps=DDSCAPS_ZBUFFER;
        auto depthResult=renderTarget.surface->lpVtbl->GetAttachedSurface(renderTarget.surface,&caps,&depth.surface);
        if(SUCCEEDED(depthResult) && depth.surface)
            record("{\"event\":\"initial_depth\",\"surface\":"+surface(depth.surface)+"}");
        else record("{\"event\":\"initial_depth\",\"absent\":true}");
        active=true;line("\"event\":\"capture_started\"");
    } catch(const std::exception &e) { attempted=true;abort(e.what()); }
    catch(...) { attempted=true;abort("unexpected_begin"); }
}
inline void draw(IDirect3DDevice3 *device,D3DPRIMITIVETYPE primitive,DWORD fvf,void *vertices,DWORD vertexCount,WORD *indices,DWORD indexCount,DWORD flags) noexcept {
    State guard;
    if(!active) return;
    try {
        if(presentationMode && GetCurrentThreadId()!=presentationThread)throw std::runtime_error("present_draw_thread_changed");
        // A presentation window can contain substantially more geometry than
        // the bounded single-scene replay format. Keep its diagnostic separate
        // while retaining the same storage and scan budgets.
        if(++commandCount>(presentationMode?8192u:2048u)) throw std::runtime_error("draw_budget");
        const unsigned vertexStride=::stride(fvf);
        if(!vertexStride || !vertexCount || vertexCount>65536 || indexCount>196608) throw std::runtime_error("unsupported_draw_layout");
        auto renderTarget=target(device);
        if(renderTarget.surface!=initialTarget) throw std::runtime_error("render_target_changed");
        IDirect3DViewport3 *viewport{};
        if(FAILED(device->lpVtbl->GetCurrentViewport(device,&viewport)) || !viewport) throw std::runtime_error("get_viewport");
        D3DVIEWPORT2 vp{};vp.dwSize=sizeof(vp);
        const auto vpResult=viewport->lpVtbl->GetViewport2(viewport,&vp);viewport->lpVtbl->Release(viewport);
        if(FAILED(vpResult)) throw std::runtime_error("get_viewport2");
        auto floatBits=[](float value){DWORD bits;std::memcpy(&bits,&value,4);return bits;};
        std::ostringstream out;
        out<<"{\"event\":\"draw\",\"ordinal\":"<<commandCount<<",\"primitive\":"<<static_cast<unsigned>(primitive)
           <<",\"fvf\":"<<fvf<<",\"stride\":"<<vertexStride<<",\"vertex_count\":"<<vertexCount
           <<",\"index_count\":"<<indexCount<<",\"flags\":"<<flags<<",\"vertices\":\""
           <<memory(vertices,static_cast<size_t>(vertexCount)*vertexStride)<<"\",\"indices\":";
        if(indexCount) out<<'"'<<memory(indices,static_cast<size_t>(indexCount)*2)<<'"';else out<<"null";
        out<<",\"viewport\":{\"x\":"<<vp.dwX<<",\"y\":"<<vp.dwY<<",\"width\":"<<vp.dwWidth<<",\"height\":"<<vp.dwHeight
           <<",\"clip_x_bits\":"<<floatBits(vp.dvClipX)<<",\"clip_y_bits\":"<<floatBits(vp.dvClipY)
           <<",\"clip_width_bits\":"<<floatBits(vp.dvClipWidth)<<",\"clip_height_bits\":"<<floatBits(vp.dvClipHeight)
           <<",\"min_z_bits\":"<<floatBits(vp.dvMinZ)<<",\"max_z_bits\":"<<floatBits(vp.dvMaxZ)<<"},\"render_states\":{";
        const D3DRENDERSTATETYPE states[]{D3DRENDERSTATE_ZENABLE,D3DRENDERSTATE_ZWRITEENABLE,D3DRENDERSTATE_ZFUNC,
            D3DRENDERSTATE_ALPHATESTENABLE,D3DRENDERSTATE_ALPHAREF,D3DRENDERSTATE_ALPHAFUNC,D3DRENDERSTATE_ALPHABLENDENABLE,
            D3DRENDERSTATE_SRCBLEND,D3DRENDERSTATE_DESTBLEND,D3DRENDERSTATE_CULLMODE,D3DRENDERSTATE_SHADEMODE,
            D3DRENDERSTATE_DITHERENABLE,D3DRENDERSTATE_FOGENABLE,D3DRENDERSTATE_FOGCOLOR,D3DRENDERSTATE_FOGTABLEMODE,
            D3DRENDERSTATE_FOGSTART,D3DRENDERSTATE_FOGEND,D3DRENDERSTATE_FOGDENSITY,D3DRENDERSTATE_RANGEFOGENABLE,
            D3DRENDERSTATE_SPECULARENABLE,D3DRENDERSTATE_TEXTUREPERSPECTIVE,D3DRENDERSTATE_ANTIALIAS,
            D3DRENDERSTATE_EDGEANTIALIAS,D3DRENDERSTATE_COLORKEYENABLE,D3DRENDERSTATE_ZBIAS,
            D3DRENDERSTATE_STENCILENABLE,D3DRENDERSTATE_STENCILFAIL,D3DRENDERSTATE_STENCILZFAIL,D3DRENDERSTATE_STENCILPASS,
            D3DRENDERSTATE_STENCILFUNC,D3DRENDERSTATE_STENCILREF,D3DRENDERSTATE_STENCILMASK,D3DRENDERSTATE_STENCILWRITEMASK,
            D3DRENDERSTATE_WRAP0,D3DRENDERSTATE_WRAP1,D3DRENDERSTATE_WRAP2,D3DRENDERSTATE_WRAP3,
            D3DRENDERSTATE_WRAP4,D3DRENDERSTATE_WRAP5,D3DRENDERSTATE_WRAP6,D3DRENDERSTATE_WRAP7};
        bool first=true;
        for(auto state:states) {
            DWORD value{};
            if(FAILED(device->lpVtbl->GetRenderState(device,state,&value))) throw std::runtime_error("get_render_state");
            if(!first)out<<',';first=false;out<<'"'<<static_cast<unsigned>(state)<<"\":"<<value;
        }
        out<<"},\"filter_setter_history\":"<<filteringHistory(device)<<",\"legacy_filter_getters\":[";
        // Older render-state filtering can coexist with texture-stage getters.
        // Record failures explicitly: unsupported diagnostic getters do not abort.
        const D3DRENDERSTATETYPE legacyFilters[]{D3DRENDERSTATE_TEXTUREMAG,D3DRENDERSTATE_TEXTUREMIN,D3DRENDERSTATE_TEXTUREMAPBLEND};
        for(unsigned i=0;i<3;++i) {
            DWORD value{};const auto hr=device->lpVtbl->GetRenderState(device,legacyFilters[i],&value);
            if(i)out<<',';
            out<<"{\"state\":"<<static_cast<unsigned>(legacyFilters[i])<<",\"hresult\":"<<hr<<",\"value\":";
            if(SUCCEEDED(hr))out<<value;else out<<"null";
            out<<'}';
        }
        out<<"],\"stages\":[";
        for(DWORD stage=0;stage<8;++stage) {
            if(stage)out<<',';
            out<<"{\"stage\":"<<stage<<",\"states\":{";
            const D3DTEXTURESTAGESTATETYPE stageStates[]{D3DTSS_COLOROP,D3DTSS_COLORARG1,D3DTSS_COLORARG2,
                D3DTSS_ALPHAOP,D3DTSS_ALPHAARG1,D3DTSS_ALPHAARG2,D3DTSS_TEXCOORDINDEX,D3DTSS_ADDRESSU,D3DTSS_ADDRESSV,
                D3DTSS_MAGFILTER,D3DTSS_MINFILTER,D3DTSS_MIPFILTER,D3DTSS_MIPMAPLODBIAS,D3DTSS_MAXMIPLEVEL,D3DTSS_MAXANISOTROPY};
            first=true;
            for(auto state:stageStates) {
                DWORD value{};
                if(FAILED(device->lpVtbl->GetTextureStageState(device,stage,state,&value))) throw std::runtime_error("get_texture_stage_state");
                if(!first)out<<',';first=false;out<<'"'<<static_cast<unsigned>(state)<<"\":"<<value;
            }
            IDirect3DTexture2 *texture{};
            if(FAILED(device->lpVtbl->GetTexture(device,stage,&texture))) throw std::runtime_error("get_texture");
            out<<"},\"texture\":";
            if(!texture)out<<"null";
            else {
                SurfaceRef resource;
                const auto hr=texture->lpVtbl->QueryInterface(texture,IID_IDirectDrawSurface4,reinterpret_cast<void **>(&resource.surface));
                texture->lpVtbl->Release(texture);
                if(FAILED(hr) || !resource.surface) throw std::runtime_error("texture_surface_query");
                out<<surface(resource.surface);
            }
            out<<'}';
        }
        out<<"]}";record(out.str());
    } catch(const std::exception &e) { abort(e.what()); }
    catch(...) { abort("unexpected_draw"); }
}
inline void result(HRESULT hr) noexcept {
    State guard;
    if(active && FAILED(hr)) abort("original_draw_failed");
}
inline void end(IDirect3DDevice3 *device,HRESULT hr) noexcept {
    State guard;
    if(!active) return;
    try {
        if(FAILED(hr)) throw std::runtime_error("original_end_failed");
        auto renderTarget=target(device);
        if(presentationMode) {
            if(GetCurrentThreadId()!=presentationThread)throw std::runtime_error("present_end_thread_changed");
            if(renderTarget.surface!=initialTarget)throw std::runtime_error("render_target_changed");
            record("{\"event\":\"scene_end\",\"draws_so_far\":"+std::to_string(commandCount)+"}");
            return;
        }
        record("{\"event\":\"final_target\",\"surface\":"+surface(renderTarget.surface)+"}");
        record("{\"event\":\"end\",\"draws\":"+std::to_string(commandCount)+",\"stored_bytes\":"+std::to_string(storedBytes)+",\"resource_files\":"+std::to_string(stored.size())+",\"complete\":true}");
        active=false;manifest.close();
        if(live && commandCount<minimumDraws) {
            std::filesystem::rename(root,root.parent_path()/ ("short-interval-"+std::to_string(candidateCount)));
            line("\"event\":\"capture_selection_rejected\",\"reason\":\"minimum_draws\"");
            if(candidateCount>=4) {line("\"event\":\"capture_selection_exhausted\"");return;}
            commandCount=0;storedBytes=0;scannedBytes=0;stored.clear();attempted=false;
        } else line("\"event\":\"capture_closed\"");
    } catch(const std::exception &e) { abort(e.what()); }
    catch(...) { abort("unexpected_end"); }
}
} // namespace frame_capture
