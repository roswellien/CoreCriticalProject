#pragma once
#include "flip_window.hpp"
namespace present_capture {
static FlipWindow window;
static bool requested=false, checked=false;
static unsigned skipped=0, delay=0;
static frame_capture::SurfaceRef backbuffer;
static bool pending=false;
inline void releaseBackbuffer() noexcept {
    if(backbuffer.surface) {backbuffer.surface->lpVtbl->Release(backbuffer.surface);backbuffer.surface=nullptr;}
}
inline bool enabled() {
    if(!checked) {
        checked=true;
        const auto marker=std::filesystem::path(environment(L"MW34_HOOK_LOG")).parent_path()/"present.request";
        if(std::filesystem::exists(marker)) {
            std::ifstream file(marker);std::string value,extra;file>>value;
            if(value.empty() || value.size()>5 || value.find_first_not_of("0123456789")!=std::string::npos || (file>>extra))
                throw std::runtime_error("invalid_present_request");
            delay=static_cast<unsigned>(std::stoul(value));
            if(delay>36000)throw std::runtime_error("present_delay_limit");
            requested=true;
        }
    }
    return requested;
}
inline void before(IDirectDrawSurface4 *self) noexcept {
    State guard;
    if(!live || !window.active || !frame_capture::active)return;
    try {
        if(window.owner!=reinterpret_cast<unsigned>(self) || window.thread!=GetCurrentThreadId() || sceneOpen)
            throw std::runtime_error("present_boundary_mismatch");
        frame_capture::record("{\"event\":\"final_target\",\"surface\":"+frame_capture::surface(backbuffer.surface)+"}");
        pending=true;
    } catch(const std::exception &e) {frame_capture::abort(e.what());window.done=true;window.active=false;releaseBackbuffer();}
}
inline void after(IDirectDrawSurface4 *self,HRESULT hr) noexcept {
    State guard;
    if(!live)return;
    try {
        if(!enabled() || window.done)return;
        DDSURFACEDESC2 desc{};desc.dwSize=sizeof(desc);
        if(FAILED(self->lpVtbl->GetSurfaceDesc(self,&desc)) || !(desc.ddsCaps.dwCaps&DDSCAPS_PRIMARYSURFACE))return;
        // Count delay only after 3D scene work has started; menu transfers are
        // not evidence of a gameplay-frame capture.
        if(!window.active && completedScenes==0)return;
        if(!window.active && SUCCEEDED(hr) && !sceneOpen && skipped<delay) {++skipped;return;}
        const auto decision=window.after(reinterpret_cast<unsigned>(self),GetCurrentThreadId(),true,!sceneOpen,SUCCEEDED(hr));
        if(decision==FlipWindow::Decision::ignore)return;
        if(decision==FlipWindow::Decision::reject)throw std::runtime_error("present_flip_failed_or_changed");
        if(decision==FlipWindow::Decision::finish) {
            if(!pending || !frame_capture::active)throw std::runtime_error("present_payload_incomplete");
            frame_capture::record("{\"event\":\"end\",\"draws\":"+std::to_string(frame_capture::commandCount)+",\"complete\":true,\"command_coverage_complete\":false,\"resource_files\":"+std::to_string(frame_capture::stored.size())+",\"stored_bytes\":"+std::to_string(frame_capture::storedBytes)+"}");
            frame_capture::active=false;frame_capture::manifest.close();
            releaseBackbuffer();
            line("\"event\":\"present_capture_closed\",\"full_frame_replay_accepted\":false");return;
        }
        if(frame_capture::active || frame_capture::attempted)throw std::runtime_error("conflicting_capture_modes");
        frame_capture::attempted=true;frame_capture::presentationMode=true;
        frame_capture::presentationThread=GetCurrentThreadId();
        frame_capture::root=std::filesystem::path(environment(L"MW34_HOOK_LOG")).parent_path()/"present-frame";
        if(!std::filesystem::create_directory(frame_capture::root))throw std::runtime_error("present_directory_not_fresh");
        frame_capture::manifest.open(frame_capture::root/"capture.jsonl",std::ios::binary);
        if(!frame_capture::manifest)throw std::runtime_error("present_manifest_open");
        DDSCAPS2 caps{};caps.dwCaps=DDSCAPS_BACKBUFFER;
        if(FAILED(self->lpVtbl->GetAttachedSurface(self,&caps,&backbuffer.surface)) || !backbuffer.surface)
            throw std::runtime_error("present_backbuffer_unavailable");
        frame_capture::initialTarget=backbuffer.surface;
        frame_capture::record("{\"event\":\"begin\",\"schema_version\":2,\"live\":true,\"scope\":\"bounded_primary_flip_interval\",\"pid\":"+std::to_string(GetCurrentProcessId())+",\"tid\":"+std::to_string(GetCurrentThreadId())+",\"skipped_flips\":"+std::to_string(skipped)+",\"command_coverage_complete\":false}");
        frame_capture::record("{\"event\":\"initial_target\",\"object\":"+std::to_string(reinterpret_cast<unsigned>(backbuffer.surface))+",\"surface\":"+frame_capture::surface(backbuffer.surface)+"}");
        frame_capture::SurfaceRef depth;caps.dwCaps=DDSCAPS_ZBUFFER;
        if(SUCCEEDED(backbuffer.surface->lpVtbl->GetAttachedSurface(backbuffer.surface,&caps,&depth.surface)) && depth.surface)
            frame_capture::record("{\"event\":\"initial_depth\",\"object\":"+std::to_string(reinterpret_cast<unsigned>(depth.surface))+",\"surface\":"+frame_capture::surface(depth.surface)+"}");
        else frame_capture::record("{\"event\":\"initial_depth\",\"absent\":true}");
        frame_capture::active=true;
        surface_diagnostics::begin(self);
        line("\"event\":\"present_capture_started\"");
    } catch(const std::exception &e) {frame_capture::abort(e.what());window.done=true;window.active=false;releaseBackbuffer();}
}
inline void surfaceOperation(const char *method,IDirectDrawSurface4 *self,IDirectDrawSurface4 *source,DWORD flags,RECT *destination,RECT *sourceRect,DDBLTFX *fx,DWORD x,DWORD y) noexcept {
    State guard;
    if(window.active && frame_capture::active) {
        try {
            auto rect=[](RECT *pointer){return pointer?"\""+frame_capture::memory(pointer,sizeof(RECT))+"\"":std::string("null");};
            const auto effects=fx?"\""+frame_capture::memory(fx,sizeof(DDBLTFX))+"\"":std::string("null");
            frame_capture::record("{\"event\":\"unsupported_surface_transfer\",\"method\":\""+std::string(method)+"\",\"destination\":"+std::to_string(reinterpret_cast<unsigned>(self))+",\"source\":"+std::to_string(reinterpret_cast<unsigned>(source))+",\"flags\":"+std::to_string(flags)+",\"selected_target\":"+std::string(self==frame_capture::initialTarget?"true":"false")+",\"destination_rectangle\":"+rect(destination)+",\"source_rectangle\":"+rect(sourceRect)+",\"effects\":"+effects+",\"x\":"+std::to_string(x)+",\"y\":"+std::to_string(y)+"}");
        } catch(...) {}
        frame_capture::abort("unsupported_present_surface_transfer");
        window.done=true;window.active=false;releaseBackbuffer();
    }
}
// The observed profile is D16, exact DEPTHFILL, null source, fill value zero.
// Return a pending command only after checking actual depth attachment identity.
inline std::string depthFill(IDirectDrawSurface4 *self,IDirectDrawSurface4 *source,DWORD flags,RECT *destination,RECT *sourceRect,DDBLTFX *fx) noexcept {
    State guard;
    if(!window.active || !frame_capture::active || GetCurrentThreadId()!=frame_capture::presentationThread || source || sourceRect || flags!=DDBLT_DEPTHFILL || !fx)return {};
    try {
        DDBLTFX effects{};SIZE_T copied{};
        if(!ReadProcessMemory(GetCurrentProcess(),fx,&effects,sizeof(effects),&copied) || copied!=sizeof(effects) || effects.dwSize!=sizeof(effects) || effects.dwFillDepth!=0)return {};
        frame_capture::SurfaceRef depth;DDSCAPS2 caps{};caps.dwCaps=DDSCAPS_ZBUFFER;
        if(FAILED(frame_capture::initialTarget->lpVtbl->GetAttachedSurface(frame_capture::initialTarget,&caps,&depth.surface)) || depth.surface!=self)return {};
        DDSURFACEDESC2 desc{};desc.dwSize=sizeof(desc);
        if(FAILED(self->lpVtbl->GetSurfaceDesc(self,&desc)) || !desc.dwWidth || !desc.dwHeight || desc.dwWidth>4096 || desc.dwHeight>4096 || desc.ddpfPixelFormat.dwFlags!=DDPF_ZBUFFER || desc.ddpfPixelFormat.dwZBufferBitDepth!=16 || desc.ddpfPixelFormat.dwZBitMask!=65535)return {};
        RECT rect{0,0,static_cast<LONG>(desc.dwWidth),static_cast<LONG>(desc.dwHeight)};
        if(destination && (!ReadProcessMemory(GetCurrentProcess(),destination,&rect,sizeof(rect),&copied) || copied!=sizeof(rect)))return {};
        if(rect.left<0 || rect.top<0 || rect.right<=rect.left || rect.bottom<=rect.top || static_cast<DWORD>(rect.right)>desc.dwWidth || static_cast<DWORD>(rect.bottom)>desc.dwHeight)return {};
        return "\"event\":\"depth_fill\",\"destination\":"+std::to_string(reinterpret_cast<unsigned>(self))+",\"flags\":"+std::to_string(flags)+",\"rectangle\":["+std::to_string(rect.left)+","+std::to_string(rect.top)+","+std::to_string(rect.right)+","+std::to_string(rect.bottom)+"],\"fill_depth\":0,\"bits\":16,\"depth_bits\":0,\"draws_so_far\":"+std::to_string(frame_capture::commandCount)+",\"effects\":\""+frame_capture::memory(&effects,sizeof(effects))+"\"";
    } catch(...) {return {};}
}
inline void depthFillResult(std::string &command,HRESULT hr) noexcept {
    State guard;
    if(!command.empty() && frame_capture::active) {
        try {
            if(FAILED(hr))throw std::runtime_error("depth_fill_provider_failed");
            frame_capture::record("{"+command+",\"hresult\":"+std::to_string(hr)+"}");
        } catch(const std::exception &e) {frame_capture::abort(e.what());}
    }
    std::string{}.swap(command);
}
} // namespace present_capture
