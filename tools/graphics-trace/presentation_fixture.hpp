#pragma once
static unsigned presentationCalls=0;
static HRESULT STDMETHODCALLTYPE fixtureSurfaceDesc(IDirectDrawSurface4 *,DDSURFACEDESC2 *desc) {
    desc->dwWidth=2;desc->dwHeight=2;desc->ddsCaps.dwCaps=DDSCAPS_PRIMARYSURFACE;return S_OK;
}
static HRESULT STDMETHODCALLTYPE fixtureSurfaceCreate(IDirectDraw4 *,DDSURFACEDESC2 *desc,IDirectDrawSurface4 **output,IUnknown *outer) {
    if(!desc || desc->dwWidth!=2 || outer)return E_INVALIDARG;
    *output=&fixtureSurface;SetLastError(0x66778899);return S_FALSE;
}
static HRESULT presentationReply(bool valid) {
    ++presentationCalls;SetLastError(0x778899aa);return valid?S_FALSE:E_INVALIDARG;
}
static HRESULT STDMETHODCALLTYPE fixtureFlip(IDirectDrawSurface4 *self,IDirectDrawSurface4 *target,DWORD flags) {
    return presentationReply(self==&fixtureSurface && target==nullptr && flags==99);
}
static HRESULT STDMETHODCALLTYPE fixtureBlt(IDirectDrawSurface4 *self,RECT *destination,IDirectDrawSurface4 *source,RECT *sourceRect,DWORD flags,DDBLTFX *fx) {
    return presentationReply(self==&fixtureSurface && destination && destination->right==2 && source==&fixtureSurface && sourceRect && sourceRect->bottom==2 && flags==99 && fx && fx->dwSize==sizeof(*fx));
}
static HRESULT STDMETHODCALLTYPE fixtureBltFast(IDirectDrawSurface4 *self,DWORD x,DWORD y,IDirectDrawSurface4 *source,RECT *sourceRect,DWORD flags) {
    return presentationReply(self==&fixtureSurface && x==3 && y==4 && source==&fixtureSurface && sourceRect && sourceRect->bottom==2 && flags==99);
}
static void setupPresentationFixture() {
    fixtureSurfaceTable.GetSurfaceDesc=fixtureSurfaceDesc;
    fixtureSurfaceTable.Flip=fixtureFlip;fixtureSurfaceTable.Blt=fixtureBlt;fixtureSurfaceTable.BltFast=fixtureBltFast;
    fake4[offsetof(IDirectDraw4Vtbl,CreateSurface)/sizeof(void *)]=reinterpret_cast<void *>(&fixtureSurfaceCreate);
}
static void presentationFixture(IDirectDraw4 *dd) {
    DDSURFACEDESC2 desc{};desc.dwSize=sizeof(desc);desc.dwWidth=2;
    IDirectDrawSurface4 *surface{};
    if(dd->lpVtbl->CreateSurface(dd,&desc,&surface,nullptr)!=S_FALSE || surface!=&fixtureSurface || GetLastError()!=0x66778899)
        throw std::runtime_error("Surface discovery forwarding failed");
    RECT rect{0,0,2,2};DDBLTFX fx{};fx.dwSize=sizeof(fx);
    auto test=[&](auto call,HRESULT expected) {
        if(call()!=expected || GetLastError()!=0x778899aa)
            throw std::runtime_error("Presentation forwarding/result/LastError failed");
    };
    for(DWORD flags:{99UL,0UL}) {
        const auto expected=flags?S_FALSE:E_INVALIDARG;
        test([&]{return surface->lpVtbl->Flip(surface,nullptr,flags);},expected);
        test([&]{return surface->lpVtbl->Blt(surface,&rect,surface,&rect,flags,&fx);},expected);
        test([&]{return surface->lpVtbl->BltFast(surface,3,4,surface,&rect,flags);},expected);
    }
    if(presentationCalls!=6 || rect.right!=2 || fx.dwSize!=sizeof(fx) || presentationSequence)
        throw std::runtime_error("Presentation fixture data/accounting changed");
    line("\"event\":\"presentation_fixture\",\"passed\":true,\"methods\":4,\"failed_results_preserved\":true,\"last_error_preserved\":true");
}
