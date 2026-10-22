#pragma once
// Input/output observations for one selected flip interval, even if replay
// capture refuses an unsupported command. No command is translated here.
namespace surface_diagnostics {
static std::ofstream log;
static unsigned sequence=0, operations=0, owner=0;
static DWORD thread=0;
static bool active=false;
static std::ofstream pixelLog;
static unsigned pixelWrites=0;
static size_t pixelBytes=0;
struct PixelLock {IDirectDrawSurface4 *surface=nullptr;DDSURFACEDESC2 desc{};std::string before;bool captured=false;unsigned draws=0,scenes=0;};
static PixelLock pixelLock;
static std::string pixelCommand;
inline bool pixelCandidate(IDirectDrawSurface4 *surface,RECT *rect,DWORD flags) noexcept {
    return !observerSurfaceReads && active && frame_capture::active && surface==frame_capture::initialTarget && !rect && flags==DDLOCK_WAIT && thread==GetCurrentThreadId();
}
inline bool pixelLockReady(IDirectDrawSurface4 *surface) noexcept {return active && pixelLock.surface==surface && pixelLock.captured && !pixelLock.before.empty();}
inline std::string pixelSnapshot(const DDSURFACEDESC2 &desc,bool capture=false) {
    const size_t row=static_cast<size_t>(desc.dwWidth)*2,size=row*desc.dwHeight;
    if(!size || size>2U*1024U*1024U || pixelBytes+size>16U*1024U*1024U || !desc.lpSurface || desc.lPitch<static_cast<LONG>(row))throw std::runtime_error("pixel_snapshot_layout_budget");
    std::vector<unsigned char> data(size);
    for(DWORD y=0;y<desc.dwHeight;++y) {
        SIZE_T copied{};
        const auto *address=static_cast<const unsigned char *>(desc.lpSurface)+static_cast<size_t>(desc.lPitch)*y;
        if(!ReadProcessMemory(GetCurrentProcess(),address,data.data()+row*y,row,&copied) || copied!=row)throw std::runtime_error("pixel_snapshot_read");
    }
    const auto name=sha256(data.data(),data.size())+".bin";
    if(capture)frame_capture::payload(data.data(),data.size());
    const auto directory=(live?frame_capture::root.parent_path():frame_capture::root)/"surface-pixels";
    std::ofstream file(directory/name,std::ios::binary);file.write(reinterpret_cast<const char *>(data.data()),static_cast<std::streamsize>(data.size()));file.close();
    if(!file)throw std::runtime_error("pixel_snapshot_write");pixelBytes+=size;return name;
}
inline std::string bytes(const void *pointer,size_t size) {
    if(!pointer)return "null";
    if(size>sizeof(DDBLTFX) && size>sizeof(DDSURFACEDESC2))throw std::runtime_error("diagnostic_size");
    std::vector<unsigned char> data(size);SIZE_T copied{};
    if(!ReadProcessMemory(GetCurrentProcess(),pointer,data.data(),size,&copied) || copied!=size)
        throw std::runtime_error("diagnostic_input_read");
    const char digits[]="0123456789abcdef";std::string text="\"";
    for(auto value:data) {text+=digits[value>>4];text+=digits[value&15];}
    return text+'"';
}
inline std::string descriptor(IDirectDrawSurface4 *surface) {
    if(!surface)return "null";
    DDSURFACEDESC2 desc{};desc.dwSize=sizeof(desc);
    const auto hr=surface->lpVtbl->GetSurfaceDesc(surface,&desc);
    return "{\"hresult\":"+std::to_string(hr)+",\"raw\":"+(SUCCEEDED(hr)?bytes(&desc,sizeof(desc)):"null")+"}";
}
inline void write(const std::string &body) {
    log<<"{\"seq\":"<<++sequence<<",\"pid\":"<<GetCurrentProcessId()<<",\"tid\":"<<GetCurrentThreadId()<<','<<body<<"}\n";
    log.flush();if(!log)throw std::runtime_error("surface_diagnostic_write");
}
inline void fail() noexcept {
    active=false;log.close();pixelLog.close();line("\"event\":\"surface_diagnostics_failed\"");
}
inline void begin(IDirectDrawSurface4 *surface) {
    State guard;
    const auto path=(live?frame_capture::root.parent_path():frame_capture::root)/"surface-operations.jsonl";
    if(std::filesystem::exists(path))throw std::runtime_error("surface_diagnostics_not_fresh");
    log.open(path,std::ios::binary);if(!log)throw std::runtime_error("surface_diagnostics_open");
    owner=reinterpret_cast<unsigned>(surface);thread=GetCurrentThreadId();active=true;
    write("\"event\":\"begin\",\"schema_version\":1,\"live\":"+std::string(live?"true":"false")+",\"diagnostic_only\":true,\"command_coverage_complete\":false,\"primary\":"+std::to_string(owner));
}
inline std::string prepare(const char *method,IDirectDrawSurface4 *self,IDirectDrawSurface4 *source,DWORD flags,RECT *destination,RECT *sourceRect,DDBLTFX *fx,DWORD x,DWORD y) {
    State guard;
    if(!active || observerSurfaceReads)return {};
    try {
        if(thread!=GetCurrentThreadId())throw std::runtime_error("surface_diagnostic_thread");
        if(operations>=4096)throw std::runtime_error("surface_diagnostic_budget");
        return "\"event\":\"operation\",\"ordinal\":"+std::to_string(++operations)+",\"method\":\""+method+"\",\"destination\":"+std::to_string(reinterpret_cast<unsigned>(self))+",\"source\":"+std::to_string(reinterpret_cast<unsigned>(source))+",\"flags\":"+std::to_string(flags)+",\"destination_info\":"+descriptor(self)+",\"source_info\":"+descriptor(source)+",\"destination_rectangle\":"+bytes(destination,sizeof(RECT))+",\"source_rectangle\":"+bytes(sourceRect,sizeof(RECT))+",\"effects\":"+bytes(fx,sizeof(DDBLTFX))+",\"x\":"+std::to_string(x)+",\"y\":"+std::to_string(y)+",\"completed_scenes\":"+std::to_string(completedScenes)+",\"successful_draws\":"+std::to_string(successfulDraws)+",\"scene_open\":"+std::string(sceneOpen?"true":"false");
    } catch(...) {fail();return {};}
}
inline void complete(std::string &input,HRESULT hr,const void *output,size_t size) noexcept {
    State guard;
    if(!input.empty() && active) {
        try {write(input+",\"hresult\":"+std::to_string(hr)+",\"output\":"+bytes(output,size));}
        catch(...) {fail();}
    }
    // Destroy allocated observation storage while the provider's output FP
    // state and LastError are protected, before returning to the game.
    std::string{}.swap(input);
}
inline void finish(IDirectDrawSurface4 *surface,HRESULT hr) noexcept {
    State guard;
    if(!active)return;
    try {
        write("\"event\":\"end\",\"primary\":"+std::to_string(reinterpret_cast<unsigned>(surface))+",\"hresult\":"+std::to_string(hr)+",\"operations\":"+std::to_string(operations)+",\"boundary_matches\":"+std::string(owner==reinterpret_cast<unsigned>(surface) && thread==GetCurrentThreadId() && !sceneOpen && SUCCEEDED(hr)?"true":"false"));
        if(pixelLog.is_open()) {
            pixelLog<<"{\"event\":\"end\",\"writes\":"<<pixelWrites<<",\"open_lock\":"<<(pixelLock.surface?"true":"false")<<",\"boundary_matches\":"<<(owner==reinterpret_cast<unsigned>(surface) && thread==GetCurrentThreadId() && !sceneOpen && SUCCEEDED(hr)?"true":"false")<<"}\n";
            pixelLog.close();if(!pixelLog)throw std::runtime_error("pixel_log_close");
        }
        active=false;log.close();
    } catch(...) {fail();}
}
inline void lockPixels(IDirectDrawSurface4 *surface,RECT *rect,DDSURFACEDESC2 *output,DWORD flags,HRESULT hr) noexcept {
    State guard;
    if(!active || observerSurfaceReads || FAILED(hr) || rect || flags!=DDLOCK_WAIT || !output)return;
    try {
        DDSURFACEDESC2 desc{};SIZE_T copied{};
        if(!ReadProcessMemory(GetCurrentProcess(),output,&desc,sizeof(desc),&copied) || copied!=sizeof(desc))throw std::runtime_error("pixel_lock_descriptor");
        if(desc.ddpfPixelFormat.dwFlags!=DDPF_RGB || desc.ddpfPixelFormat.dwRGBBitCount!=16 || desc.ddpfPixelFormat.dwRBitMask!=0xf800 || desc.ddpfPixelFormat.dwGBitMask!=0x7e0 || desc.ddpfPixelFormat.dwBBitMask!=0x1f || desc.ddpfPixelFormat.dwRGBAlphaBitMask!=0 || !desc.dwWidth || !desc.dwHeight || desc.dwWidth>4096 || desc.dwHeight>4096)return;
        if(pixelLock.surface || pixelWrites>=16)throw std::runtime_error("pixel_lock_overlap_budget");
        if(!pixelLog.is_open()) {
            const auto directory=(live?frame_capture::root.parent_path():frame_capture::root)/"surface-pixels";
            if(!std::filesystem::create_directory(directory))throw std::runtime_error("pixel_directory_not_fresh");
            pixelLog.open(directory/"writes.jsonl",std::ios::binary);if(!pixelLog)throw std::runtime_error("pixel_log_open");
            pixelLog<<"{\"event\":\"begin\",\"live\":"<<(live?"true":"false")<<",\"pid\":"<<GetCurrentProcessId()<<",\"tid\":"<<GetCurrentThreadId()<<",\"diagnostic_only\":true,\"command_coverage_complete\":false}\n";
        }
        pixelLock.surface=surface;pixelLock.desc=desc;pixelLock.captured=pixelCandidate(surface,rect,flags);pixelLock.before=pixelSnapshot(desc,pixelLock.captured);
        pixelLock.draws=successfulDraws;pixelLock.scenes=completedScenes;
    } catch(...) {fail();}
}
inline std::string unlockPixels(IDirectDrawSurface4 *surface) noexcept {
    State guard;
    if(!active || observerSurfaceReads || !pixelLock.surface)return {};
    try {
        if(pixelLock.surface!=surface || thread!=GetCurrentThreadId() || pixelLock.draws!=successfulDraws || pixelLock.scenes!=completedScenes)throw std::runtime_error("pixel_unlock_owner_thread_draw_interleave");
        const bool captured=pixelLock.captured && frame_capture::active;
        const auto after=pixelSnapshot(pixelLock.desc,captured);
        auto text="\"event\":\"cpu_write\",\"ordinal\":"+std::to_string(++pixelWrites)+",\"surface\":"+std::to_string(reinterpret_cast<unsigned>(surface))+",\"width\":"+std::to_string(pixelLock.desc.dwWidth)+",\"height\":"+std::to_string(pixelLock.desc.dwHeight)+",\"source_pitch\":"+std::to_string(pixelLock.desc.lPitch)+",\"format\":\"RGB565\",\"before\":\""+pixelLock.before+"\",\"after\":\""+after+"\",\"completed_scenes\":"+std::to_string(completedScenes)+",\"successful_draws\":"+std::to_string(successfulDraws);
        if(captured)pixelCommand=text+",\"draws_so_far\":"+std::to_string(frame_capture::commandCount);
        pixelLock.surface=nullptr;pixelLock.captured=false;pixelLock.before.clear();return text;
    } catch(...) {fail();return {};}
}
inline void unlockPixelsResult(std::string &input,HRESULT hr) noexcept {
    State guard;
    if(active && !input.empty()) {
        pixelLog<<"{"<<input<<",\"unlock_hresult\":"<<hr<<"}\n";pixelLog.flush();if(!pixelLog)fail();
    }
    if(!pixelCommand.empty() && frame_capture::active) {
        try {
            if(FAILED(hr))throw std::runtime_error("cpu_write_unlock_failed");
            frame_capture::record("{"+pixelCommand+",\"unlock_hresult\":"+std::to_string(hr)+"}");
        } catch(const std::exception &e) {frame_capture::abort(e.what());}
    }
    std::string{}.swap(pixelCommand);
    std::string{}.swap(input);
}
}
