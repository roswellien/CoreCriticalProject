#pragma once
// Bounded presentation-candidate timeline. A primary-surface transfer is a
// candidate boundary, not automatically proof of a physically displayed frame.
static std::ofstream presentationLog;
static unsigned presentationSequence=0;
static void observeSurface(IDirectDrawSurface4 *surface) {
    State guard;
    if(!surface)return;
    DDSURFACEDESC2 desc{};desc.dwSize=sizeof(desc);
    if(SUCCEEDED(surface->lpVtbl->GetSurfaceDesc(surface,&desc)) &&
       (desc.ddsCaps.dwCaps & (DDSCAPS_PRIMARYSURFACE|DDSCAPS_BACKBUFFER|DDSCAPS_3DDEVICE|DDSCAPS_ZBUFFER)))
        observe(surface,Kind::surface4);
}
static void presentationRecord(const char *method,IDirectDrawSurface4 *self,IDirectDrawSurface4 *source,DWORD flags,HRESULT hr) noexcept {
    State guard;
    // Menu animation must not consume the finite gameplay timeline before the
    // user enters Training. Capture arming already uses the same scene gate.
    if(!live || completedScenes==0 || presentationSequence>=2048)return;
    try {
        if(!presentationLog.is_open()) {
            const auto path=std::filesystem::path(environment(L"MW34_HOOK_LOG")).parent_path()/"presentation.jsonl";
            if(std::filesystem::exists(path))throw std::runtime_error("presentation_log_not_fresh");
            presentationLog.open(path,std::ios::binary);
            if(!presentationLog)throw std::runtime_error("presentation_log_open");
        }
        DDSURFACEDESC2 desc{};desc.dwSize=sizeof(desc);
        const auto info=self->lpVtbl->GetSurfaceDesc(self,&desc);
        presentationLog<<"{\"seq\":"<<++presentationSequence<<",\"pid\":"<<GetCurrentProcessId()
            <<",\"tid\":"<<GetCurrentThreadId()<<",\"method\":\""<<method<<"\",\"destination\":"<<reinterpret_cast<unsigned>(self)
            <<",\"source\":"<<reinterpret_cast<unsigned>(source)<<",\"flags\":"<<flags<<",\"hresult\":"<<hr
            <<",\"surface_info_hresult\":"<<info<<",\"caps\":"<<(SUCCEEDED(info)?desc.ddsCaps.dwCaps:0)
            <<",\"width\":"<<(SUCCEEDED(info)?desc.dwWidth:0)<<",\"height\":"<<(SUCCEEDED(info)?desc.dwHeight:0)
            <<",\"completed_scenes\":"<<completedScenes<<",\"successful_draws\":"<<successfulDraws
            <<",\"scene_open\":"<<(sceneOpen?"true":"false")<<"}\n";
        presentationLog.flush();
        if(!presentationLog)throw std::runtime_error("presentation_log_write");
    } catch(...) {presentationSequence=2048;line("\"event\":\"presentation_observer_failed\"");}
}
static HRESULT STDMETHODCALLTYPE surfaceCreate(IDirectDraw4 *self,DDSURFACEDESC2 *desc,IDirectDrawSurface4 **output,IUnknown *outer) {
    const auto call=reinterpret_cast<decltype(IDirectDraw4Vtbl::CreateSurface)>(original(self,offsetof(IDirectDraw4Vtbl,CreateSurface)/sizeof(void *)));
    const auto result=call(self,desc,output,outer);
    {State guard;if(SUCCEEDED(result) && output)observeSurface(*output);}
    return result;
}
static HRESULT STDMETHODCALLTYPE surfaceAttached(IDirectDrawSurface4 *self,DDSCAPS2 *caps,IDirectDrawSurface4 **output) {
    const auto call=reinterpret_cast<decltype(IDirectDrawSurface4Vtbl::GetAttachedSurface)>(original(self,offsetof(IDirectDrawSurface4Vtbl,GetAttachedSurface)/sizeof(void *)));
    const auto result=call(self,caps,output);
    {State guard;if(SUCCEEDED(result) && output)observeSurface(*output);}
    return result;
}
static HRESULT STDMETHODCALLTYPE surfaceFlip(IDirectDrawSurface4 *self,IDirectDrawSurface4 *target,DWORD flags) {
    const auto call=reinterpret_cast<decltype(IDirectDrawSurface4Vtbl::Flip)>(original(self,offsetof(IDirectDrawSurface4Vtbl,Flip)/sizeof(void *)));
    present_capture::before(self);
    const auto result=call(self,target,flags);presentationRecord("Flip",self,target,flags,result);
    surface_diagnostics::finish(self,result);
    present_capture::after(self,result);return result;
}
static HRESULT STDMETHODCALLTYPE surfaceBlt(IDirectDrawSurface4 *self,RECT *destination,IDirectDrawSurface4 *source,RECT *sourceRect,DWORD flags,DDBLTFX *fx) {
    const auto call=reinterpret_cast<decltype(IDirectDrawSurface4Vtbl::Blt)>(original(self,offsetof(IDirectDrawSurface4Vtbl,Blt)/sizeof(void *)));
    auto diagnostic=surface_diagnostics::prepare("Blt",self,source,flags,destination,sourceRect,fx,0,0);
    auto depthCommand=present_capture::depthFill(self,source,flags,destination,sourceRect,fx);
    if(depthCommand.empty())present_capture::surfaceOperation("Blt",self,source,flags,destination,sourceRect,fx,0,0);
    const auto result=call(self,destination,source,sourceRect,flags,fx);surface_diagnostics::complete(diagnostic,result);
    present_capture::depthFillResult(depthCommand,result);
    presentationRecord("Blt",self,source,flags,result);return result;
}
static HRESULT STDMETHODCALLTYPE surfaceBltFast(IDirectDrawSurface4 *self,DWORD x,DWORD y,IDirectDrawSurface4 *source,RECT *sourceRect,DWORD flags) {
    const auto call=reinterpret_cast<decltype(IDirectDrawSurface4Vtbl::BltFast)>(original(self,offsetof(IDirectDrawSurface4Vtbl,BltFast)/sizeof(void *)));
    auto diagnostic=surface_diagnostics::prepare("BltFast",self,source,flags,nullptr,sourceRect,nullptr,x,y);
    present_capture::surfaceOperation("BltFast",self,source,flags,nullptr,sourceRect,nullptr,x,y);
    const auto result=call(self,x,y,source,sourceRect,flags);surface_diagnostics::complete(diagnostic,result);
    presentationRecord("BltFast",self,source,flags,result);return result;
}
static HRESULT STDMETHODCALLTYPE surfaceLock(IDirectDrawSurface4 *self,RECT *rect,DDSURFACEDESC2 *desc,DWORD flags,HANDLE event) {
    const auto call=reinterpret_cast<decltype(IDirectDrawSurface4Vtbl::Lock)>(original(self,offsetof(IDirectDrawSurface4Vtbl,Lock)/sizeof(void *)));
    auto diagnostic=surface_diagnostics::prepare("Lock",self,nullptr,flags,rect,nullptr,nullptr,0,0);
    const bool pixelCandidate=surface_diagnostics::pixelCandidate(self,rect,flags);
    if(!observerSurfaceReads && !(flags&DDLOCK_READONLY) && !pixelCandidate)coverageViolation("unsupported_surface_write_lock");
    const auto result=call(self,rect,desc,flags,event);
    surface_diagnostics::lockPixels(self,rect,desc,flags,result);
    if(pixelCandidate && (!surface_diagnostics::pixelLockReady(self) || FAILED(result)))coverageViolation("unsupported_surface_write_lock_output");
    surface_diagnostics::complete(diagnostic,result,SUCCEEDED(result)?desc:nullptr,SUCCEEDED(result)?sizeof(DDSURFACEDESC2):0);
    return result;
}
static HRESULT STDMETHODCALLTYPE surfaceUnlock(IDirectDrawSurface4 *self,RECT *rect) {
    const auto call=reinterpret_cast<decltype(IDirectDrawSurface4Vtbl::Unlock)>(original(self,offsetof(IDirectDrawSurface4Vtbl,Unlock)/sizeof(void *)));
    auto diagnostic=surface_diagnostics::prepare("Unlock",self,nullptr,0,rect,nullptr,nullptr,0,0);
    auto pixels=surface_diagnostics::unlockPixels(self);
    if(!observerSurfaceReads && (pixels.empty() || rect))coverageViolation("unsupported_game_surface_unlock");
    const auto result=call(self,rect);surface_diagnostics::complete(diagnostic,result);
    surface_diagnostics::unlockPixelsResult(pixels,result);return result;
}
static HRESULT STDMETHODCALLTYPE surfaceGetDC(IDirectDrawSurface4 *self,HDC *dc) {
    const auto call=reinterpret_cast<decltype(IDirectDrawSurface4Vtbl::GetDC)>(original(self,offsetof(IDirectDrawSurface4Vtbl,GetDC)/sizeof(void *)));
    auto diagnostic=surface_diagnostics::prepare("GetDC",self,nullptr,0,nullptr,nullptr,nullptr,0,0);
    coverageViolation("unsupported_surface_gdi_access");
    const auto result=call(self,dc);surface_diagnostics::complete(diagnostic,result,SUCCEEDED(result)?dc:nullptr,SUCCEEDED(result)?sizeof(HDC):0);return result;
}
static HRESULT STDMETHODCALLTYPE surfaceReleaseDC(IDirectDrawSurface4 *self,HDC dc) {
    const auto call=reinterpret_cast<decltype(IDirectDrawSurface4Vtbl::ReleaseDC)>(original(self,offsetof(IDirectDrawSurface4Vtbl,ReleaseDC)/sizeof(void *)));
    auto diagnostic=surface_diagnostics::prepare("ReleaseDC",self,nullptr,0,nullptr,nullptr,nullptr,reinterpret_cast<DWORD>(dc),0);
    coverageViolation("unsupported_surface_gdi_release");
    const auto result=call(self,dc);surface_diagnostics::complete(diagnostic,result);return result;
}
static void installPresentation(Entry &e) {
#define PRESENT_HOOK(table,method,handler) e.clone[offsetof(table,method)/sizeof(void *)]=reinterpret_cast<void *>(&handler)
    if(e.kind==Kind::draw4) {PRESENT_HOOK(IDirectDraw4Vtbl,CreateSurface,surfaceCreate);}
    if(e.kind==Kind::surface4) {
        PRESENT_HOOK(IDirectDrawSurface4Vtbl,GetAttachedSurface,surfaceAttached);
        PRESENT_HOOK(IDirectDrawSurface4Vtbl,Flip,surfaceFlip);
        PRESENT_HOOK(IDirectDrawSurface4Vtbl,Blt,surfaceBlt);
        PRESENT_HOOK(IDirectDrawSurface4Vtbl,BltFast,surfaceBltFast);
        PRESENT_HOOK(IDirectDrawSurface4Vtbl,Lock,surfaceLock);
        PRESENT_HOOK(IDirectDrawSurface4Vtbl,Unlock,surfaceUnlock);
        PRESENT_HOOK(IDirectDrawSurface4Vtbl,GetDC,surfaceGetDC);
        PRESENT_HOOK(IDirectDrawSurface4Vtbl,ReleaseDC,surfaceReleaseDC);
    }
#undef PRESENT_HOOK
}
