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
       (desc.ddsCaps.dwCaps & (DDSCAPS_PRIMARYSURFACE|DDSCAPS_BACKBUFFER|DDSCAPS_3DDEVICE)))
        observe(surface,Kind::surface4);
}
static void presentationRecord(const char *method,IDirectDrawSurface4 *self,IDirectDrawSurface4 *source,DWORD flags,HRESULT hr) noexcept {
    State guard;
    if(!live || presentationSequence>=2048)return;
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
    const auto result=call(self,target,flags);presentationRecord("Flip",self,target,flags,result);return result;
}
static HRESULT STDMETHODCALLTYPE surfaceBlt(IDirectDrawSurface4 *self,RECT *destination,IDirectDrawSurface4 *source,RECT *sourceRect,DWORD flags,DDBLTFX *fx) {
    const auto call=reinterpret_cast<decltype(IDirectDrawSurface4Vtbl::Blt)>(original(self,offsetof(IDirectDrawSurface4Vtbl,Blt)/sizeof(void *)));
    const auto result=call(self,destination,source,sourceRect,flags,fx);presentationRecord("Blt",self,source,flags,result);return result;
}
static HRESULT STDMETHODCALLTYPE surfaceBltFast(IDirectDrawSurface4 *self,DWORD x,DWORD y,IDirectDrawSurface4 *source,RECT *sourceRect,DWORD flags) {
    const auto call=reinterpret_cast<decltype(IDirectDrawSurface4Vtbl::BltFast)>(original(self,offsetof(IDirectDrawSurface4Vtbl,BltFast)/sizeof(void *)));
    const auto result=call(self,x,y,source,sourceRect,flags);presentationRecord("BltFast",self,source,flags,result);return result;
}
static void installPresentation(Entry &e) {
#define PRESENT_HOOK(table,method,handler) e.clone[offsetof(table,method)/sizeof(void *)]=reinterpret_cast<void *>(&handler)
    if(e.kind==Kind::draw4) {PRESENT_HOOK(IDirectDraw4Vtbl,CreateSurface,surfaceCreate);}
    if(e.kind==Kind::surface4) {
        PRESENT_HOOK(IDirectDrawSurface4Vtbl,GetAttachedSurface,surfaceAttached);
        PRESENT_HOOK(IDirectDrawSurface4Vtbl,Flip,surfaceFlip);
        PRESENT_HOOK(IDirectDrawSurface4Vtbl,Blt,surfaceBlt);
        PRESENT_HOOK(IDirectDrawSurface4Vtbl,BltFast,surfaceBltFast);
    }
#undef PRESENT_HOOK
}
