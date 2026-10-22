#pragma once
static unsigned presentationCalls=0;
static IDirectDrawSurface4Vtbl fixtureDepthTable{};
static IDirectDrawSurface4 fixtureDepth{&fixtureDepthTable};
static HRESULT STDMETHODCALLTYPE fixtureSurfaceDesc(IDirectDrawSurface4 *self,DDSURFACEDESC2 *desc) {
    desc->dwFlags=DDSD_CAPS|DDSD_WIDTH|DDSD_HEIGHT|DDSD_PIXELFORMAT;desc->ddpfPixelFormat.dwSize=sizeof(DDPIXELFORMAT);
    desc->dwWidth=2;desc->dwHeight=2;desc->ddsCaps.dwCaps=self==&fixtureDepth?DDSCAPS_ZBUFFER:DDSCAPS_PRIMARYSURFACE;
    desc->ddpfPixelFormat.dwFlags=self==&fixtureDepth?DDPF_ZBUFFER:DDPF_RGB;
    if(self==&fixtureDepth)desc->ddpfPixelFormat.dwZBitMask=65535;
    desc->ddpfPixelFormat.dwRGBBitCount=self==&fixtureDepth?16:32;return S_OK;
}
static HRESULT STDMETHODCALLTYPE fixtureSurfaceCreate(IDirectDraw4 *,DDSURFACEDESC2 *desc,IDirectDrawSurface4 **output,IUnknown *outer) {
    if(!desc || desc->dwWidth!=2 || outer)return E_INVALIDARG;
    *output=desc->ddsCaps.dwCaps&DDSCAPS_ZBUFFER?&fixtureDepth:&fixtureSurface;SetLastError(0x66778899);return S_FALSE;
}
static unsigned accessCalls=0;
static HRESULT STDMETHODCALLTYPE fixtureAccessLock(IDirectDrawSurface4 *self,RECT *rect,DDSURFACEDESC2 *desc,DWORD flags,HANDLE event) {
    ++accessCalls;SetLastError(0x778899aa);
    if(self!=&fixtureDepth || event || !rect || rect->right!=2 || flags!=DDLOCK_WRITEONLY)return E_INVALIDARG;
    desc->dwWidth=2;desc->dwHeight=2;desc->lPitch=4;desc->lpSurface=const_cast<unsigned char *>(fixturePixels);
    desc->ddsCaps.dwCaps=DDSCAPS_ZBUFFER;desc->ddpfPixelFormat.dwFlags=DDPF_ZBUFFER;desc->ddpfPixelFormat.dwZBufferBitDepth=16;
    return S_FALSE;
}
static HRESULT STDMETHODCALLTYPE fixtureAccessUnlock(IDirectDrawSurface4 *self,RECT *rect) {
    ++accessCalls;SetLastError(0x778899aa);return self==&fixtureDepth && rect && rect->right==2?S_FALSE:E_INVALIDARG;
}
static HRESULT STDMETHODCALLTYPE fixtureAccessDC(IDirectDrawSurface4 *self,HDC *output) {
    ++accessCalls;SetLastError(0x778899aa);
    if(self!=&fixtureDepth)return E_INVALIDARG;
    *output=reinterpret_cast<HDC>(0x1234);return S_FALSE;
}
static HRESULT STDMETHODCALLTYPE fixtureAccessReleaseDC(IDirectDrawSurface4 *self,HDC dc) {
    ++accessCalls;SetLastError(0x778899aa);return self==&fixtureDepth && dc==reinterpret_cast<HDC>(0x1234)?S_FALSE:E_INVALIDARG;
}
static HRESULT presentationReply(bool valid) {
    ++presentationCalls;SetLastError(0x778899aa);return valid?S_FALSE:E_INVALIDARG;
}
static HRESULT STDMETHODCALLTYPE fixtureFlip(IDirectDrawSurface4 *self,IDirectDrawSurface4 *target,DWORD flags) {
    return presentationReply(self==&fixtureSurface && target==nullptr && flags==99);
}
static HRESULT STDMETHODCALLTYPE fixtureBlt(IDirectDrawSurface4 *self,RECT *destination,IDirectDrawSurface4 *source,RECT *sourceRect,DWORD flags,DDBLTFX *fx) {
    if(self==&fixtureDepth)return presentationReply(destination && destination->right==2 && !source && !sourceRect && flags==DDBLT_DEPTHFILL && fx && fx->dwSize==sizeof(*fx) && (fx->dwFillDepth==65535 || fx->dwFillDepth==0));
    return presentationReply(self==&fixtureSurface && destination && destination->right==2 && source==&fixtureSurface && sourceRect && sourceRect->bottom==2 && flags==99 && fx && fx->dwSize==sizeof(*fx));
}
static void depthCommandFixture() {
    const auto savedRoot=frame_capture::root;
    frame_capture::root=savedRoot/"depth-command";
    if(!std::filesystem::create_directory(frame_capture::root))throw std::runtime_error("Depth command fixture directory not fresh");
    frame_capture::manifest.open(frame_capture::root/"depth-command-fixture.jsonl",std::ios::binary);
    if(!frame_capture::manifest)throw std::runtime_error("Depth command fixture open failed");
    frame_capture::active=true;frame_capture::presentationThread=GetCurrentThreadId();
    frame_capture::initialTarget=&fixtureSurface;fixtureAttachedDepth=&fixtureDepth;
    present_capture::window.active=true;
    RECT rect{0,0,2,2};DDBLTFX effects{};effects.dwSize=sizeof(effects);
    if(fixtureDepth.lpVtbl->Blt(&fixtureDepth,&rect,nullptr,nullptr,DDBLT_DEPTHFILL,&effects)!=S_FALSE || !frame_capture::active || GetLastError()!=0x778899aa)
        throw std::runtime_error("Observed depth command forwarding failed");
    auto refused=[&](IDirectDrawSurface4 *self,IDirectDrawSurface4 *source,DWORD flags,RECT *region) {
        if(!present_capture::depthFill(self,source,flags,region,nullptr,&effects).empty())throw std::runtime_error("Unsupported depth fill admitted");
    };
    effects.dwFillDepth=1;refused(&fixtureDepth,nullptr,DDBLT_DEPTHFILL,&rect);effects.dwFillDepth=0;
    refused(&fixtureDepth,&fixtureSurface,DDBLT_DEPTHFILL,&rect);
    refused(&fixtureDepth,nullptr,DDBLT_DEPTHFILL|DDBLT_WAIT,&rect);
    RECT bad{-1,0,2,2};refused(&fixtureDepth,nullptr,DDBLT_DEPTHFILL,&bad);
    refused(&fixtureSurface,nullptr,DDBLT_DEPTHFILL,&rect);
    fixtureAttachedDepth=nullptr;refused(&fixtureDepth,nullptr,DDBLT_DEPTHFILL,&rect);
    frame_capture::active=false;frame_capture::manifest.close();frame_capture::presentationThread=0;present_capture::window={};frame_capture::root=savedRoot;
    frame_capture::commandCount=0;frame_capture::storedBytes=frame_capture::scannedBytes=0;frame_capture::stored.clear();frame_capture::initialTarget=nullptr;
    line("\"event\":\"depth_command_fixture\",\"passed\":true,\"refused_profiles\":6,\"actual_provider_forwarded\":true");
}
static HRESULT STDMETHODCALLTYPE fixtureBltFast(IDirectDrawSurface4 *self,DWORD x,DWORD y,IDirectDrawSurface4 *source,RECT *sourceRect,DWORD flags) {
    return presentationReply(self==&fixtureSurface && x==3 && y==4 && source==&fixtureSurface && sourceRect && sourceRect->bottom==2 && flags==99);
}
static void setupPresentationFixture() {
    fixtureSurfaceTable.GetSurfaceDesc=fixtureSurfaceDesc;
    fixtureSurfaceTable.Flip=fixtureFlip;fixtureSurfaceTable.Blt=fixtureBlt;fixtureSurfaceTable.BltFast=fixtureBltFast;
    fake4[offsetof(IDirectDraw4Vtbl,CreateSurface)/sizeof(void *)]=reinterpret_cast<void *>(&fixtureSurfaceCreate);
    fixtureDepthTable=fixtureSurfaceTable;fixtureDepthTable.Lock=fixtureAccessLock;fixtureDepthTable.Unlock=fixtureAccessUnlock;
    fixtureDepthTable.GetDC=fixtureAccessDC;fixtureDepthTable.ReleaseDC=fixtureAccessReleaseDC;
}
static void surfaceAccessFixture(IDirectDraw4 *dd) {
    DDSURFACEDESC2 creation{};creation.dwSize=sizeof(creation);creation.dwWidth=2;creation.ddsCaps.dwCaps=DDSCAPS_ZBUFFER;
    IDirectDrawSurface4 *depth{};
    if(dd->lpVtbl->CreateSurface(dd,&creation,&depth,nullptr)!=S_FALSE || depth!=&fixtureDepth || depth->lpVtbl==&fixtureDepthTable || GetLastError()!=0x66778899)
        throw std::runtime_error("Depth surface discovery failed");
    surface_diagnostics::begin(&fixtureSurface);
    RECT rect{0,0,2,2};DDSURFACEDESC2 output{};output.dwSize=sizeof(output);HDC dc{};
    auto test=[&](auto call,HRESULT expected) {
        frame_capture::active=true;
        if(call()!=expected || GetLastError()!=0x778899aa || frame_capture::active)
            throw std::runtime_error("Surface access forwarding/refusal failed");
    };
    test([&]{return depth->lpVtbl->Lock(depth,&rect,&output,DDLOCK_WRITEONLY,nullptr);},S_FALSE);
    if(output.dwWidth!=2 || output.lPitch!=4 || output.ddpfPixelFormat.dwZBufferBitDepth!=16)
        throw std::runtime_error("Depth lock output changed");
    test([&]{return depth->lpVtbl->Unlock(depth,&rect);},S_FALSE);
    test([&]{return depth->lpVtbl->GetDC(depth,&dc);},S_FALSE);
    if(dc!=reinterpret_cast<HDC>(0x1234))throw std::runtime_error("GDI output changed");
    test([&]{return depth->lpVtbl->ReleaseDC(depth,dc);},S_FALSE);
    const auto saved=output;
    test([&]{return depth->lpVtbl->Lock(depth,&rect,&output,DDLOCK_WRITEONLY,reinterpret_cast<HANDLE>(1));},E_INVALIDARG);
    if(std::memcmp(&saved,&output,sizeof(output)))throw std::runtime_error("Failed lock output changed");
    test([&]{return depth->lpVtbl->Unlock(depth,nullptr);},E_INVALIDARG);
    test([&]{return depth->lpVtbl->ReleaseDC(depth,nullptr);},E_INVALIDARG);
    frame_capture::active=false;
    DDBLTFX effects{};effects.dwSize=sizeof(effects);effects.dwFillDepth=65535;
    if(depth->lpVtbl->Blt(depth,&rect,nullptr,nullptr,DDBLT_DEPTHFILL,&effects)!=S_FALSE || GetLastError()!=0x778899aa || effects.dwFillDepth!=65535)
        throw std::runtime_error("Depth fill diagnostic forwarding failed");
    const auto savedRoot=frame_capture::root;
    frame_capture::root=savedRoot/"cpu-command";
    if(!std::filesystem::create_directory(frame_capture::root))throw std::runtime_error("CPU command directory not fresh");
    frame_capture::manifest.open(frame_capture::root/"cpu-command-fixture.jsonl",std::ios::binary);
    if(!frame_capture::manifest)throw std::runtime_error("CPU command fixture open failed");
    frame_capture::active=true;frame_capture::initialTarget=&fixtureSurface;
    DDSURFACEDESC2 writable{};writable.dwSize=sizeof(writable);
    SetLastError(0x55667788);
    if(fixtureSurface.lpVtbl->Lock(&fixtureSurface,nullptr,&writable,DDLOCK_WAIT,nullptr)!=S_OK || GetLastError()!=0x55667788)
        throw std::runtime_error("RGB565 lock forwarding failed");
    fixtureWritePixels[2]=0xe0;fixtureWritePixels[3]=0x07;
    if(fixtureSurface.lpVtbl->Unlock(&fixtureSurface,nullptr)!=S_OK || !frame_capture::active || GetLastError()!=0x55667788 || surface_diagnostics::pixelWrites!=1)
        throw std::runtime_error("CPU pixel write observation failed");
    frame_capture::active=false;frame_capture::manifest.close();frame_capture::root=savedRoot;
    // An actual snapshot traverses the cloned Lock/Unlock slots, but must not
    // create game-operation records or refuse the capture.
    frame_capture::active=true;SetLastError(0x55667788);
    {State snapshotGuard;frame_capture::surface(&fixtureSurface);}
    if(!frame_capture::active || observerSurfaceReads || surface_diagnostics::operations!=10 || GetLastError()!=0x55667788)
        throw std::runtime_error("Observer snapshot attributed to game");
    frame_capture::active=false;
    surface_diagnostics::finish(&fixtureSurface,S_OK);
    if(surface_diagnostics::active || accessCalls!=7)throw std::runtime_error("Surface diagnostic lifecycle failed");
    surface_diagnostics::sequence=surface_diagnostics::operations=surface_diagnostics::owner=0;
    surface_diagnostics::thread=0;
    surface_diagnostics::pixelWrites=0;surface_diagnostics::pixelBytes=0;
    line("\"event\":\"surface_access_fixture\",\"passed\":true,\"depth_discovered\":true,\"forwarded_calls\":7,\"snapshot_excluded\":true,\"failed_outputs_preserved\":true");
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
