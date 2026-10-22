#pragma once
static IDirectDrawSurface4Vtbl fixtureSurfaceTable{};
static IDirectDrawSurface4 fixtureSurface{&fixtureSurfaceTable};
static IDirect3DViewport3Vtbl fixtureViewportTable{};
static IDirect3DViewport3 fixtureViewport{&fixtureViewportTable};
static const unsigned char fixturePixels[16]{255,0,0,255,0,255,0,255,0,0,255,255,255,255,255,255};
static unsigned char fixtureWritePixels[8]{};
static IDirectDrawSurface4 *fixtureAttachedDepth=nullptr;
static ULONG STDMETHODCALLTYPE fixtureSurfaceRelease(IDirectDrawSurface4 *) { return 1; }
static HRESULT STDMETHODCALLTYPE fixtureLock(IDirectDrawSurface4 *,RECT *,DDSURFACEDESC2 *desc,DWORD flags,HANDLE) {
    if(flags==DDLOCK_WAIT) {
        desc->dwWidth=2;desc->dwHeight=2;desc->lPitch=4;desc->lpSurface=fixtureWritePixels;
        desc->ddpfPixelFormat.dwFlags=DDPF_RGB;desc->ddpfPixelFormat.dwRGBBitCount=16;
        desc->ddpfPixelFormat.dwRBitMask=0xf800;desc->ddpfPixelFormat.dwGBitMask=0x7e0;desc->ddpfPixelFormat.dwBBitMask=0x1f;
        return S_OK;
    }
    if(flags!=(DDLOCK_READONLY|DDLOCK_WAIT))return E_INVALIDARG;
    desc->dwWidth=2;desc->dwHeight=2;desc->lPitch=8;desc->lpSurface=const_cast<unsigned char *>(fixturePixels);
    desc->ddpfPixelFormat.dwFlags=DDPF_RGB|DDPF_ALPHAPIXELS;desc->ddpfPixelFormat.dwRGBBitCount=32;
    desc->ddpfPixelFormat.dwRBitMask=255;desc->ddpfPixelFormat.dwGBitMask=65280;
    desc->ddpfPixelFormat.dwBBitMask=16711680;desc->ddpfPixelFormat.dwRGBAlphaBitMask=4278190080;
    return S_OK;
}
static HRESULT STDMETHODCALLTYPE fixtureUnlock(IDirectDrawSurface4 *,RECT *) { return S_OK; }
static HRESULT STDMETHODCALLTYPE fixtureAttached(IDirectDrawSurface4 *,DDSCAPS2 *caps,IDirectDrawSurface4 **output) { *output=caps->dwCaps==DDSCAPS_ZBUFFER?fixtureAttachedDepth:nullptr;return *output?S_OK:DDERR_NOTFOUND; }
static ULONG STDMETHODCALLTYPE fixtureViewportRelease(IDirect3DViewport3 *) { return 1; }
static HRESULT STDMETHODCALLTYPE fixtureGetViewport(IDirect3DViewport3 *,D3DVIEWPORT2 *vp) { vp->dwWidth=2;vp->dwHeight=2;vp->dvMaxZ=1;return S_OK; }
static HRESULT STDMETHODCALLTYPE fixtureTarget(IDirect3DDevice3 *,IDirectDrawSurface4 **output) { *output=&fixtureSurface;return S_OK; }
static HRESULT STDMETHODCALLTYPE fixtureViewportGet(IDirect3DDevice3 *,IDirect3DViewport3 **output) { *output=&fixtureViewport;return S_OK; }
static HRESULT STDMETHODCALLTYPE fixtureState(IDirect3DDevice3 *,D3DRENDERSTATETYPE,DWORD *output) { *output=0;return S_OK; }
static HRESULT STDMETHODCALLTYPE fixtureStage(IDirect3DDevice3 *,DWORD,D3DTEXTURESTAGESTATETYPE,DWORD *output) { *output=0;return S_OK; }
static HRESULT STDMETHODCALLTYPE fixtureTexture(IDirect3DDevice3 *,DWORD,IDirect3DTexture2 **output) { *output=nullptr;return S_OK; }
static void setupCaptureFixture() {
    fixtureSurfaceTable.Release=fixtureSurfaceRelease;fixtureSurfaceTable.Lock=fixtureLock;
    fixtureSurfaceTable.Unlock=fixtureUnlock;fixtureSurfaceTable.GetAttachedSurface=fixtureAttached;
    fixtureViewportTable.Release=fixtureViewportRelease;fixtureViewportTable.GetViewport2=fixtureGetViewport;
    fakeDevice[offsetof(IDirect3DDevice3Vtbl,GetRenderTarget)/sizeof(void *)]=reinterpret_cast<void *>(fixtureTarget);
    fakeDevice[offsetof(IDirect3DDevice3Vtbl,GetCurrentViewport)/sizeof(void *)]=reinterpret_cast<void *>(fixtureViewportGet);
    fakeDevice[offsetof(IDirect3DDevice3Vtbl,GetRenderState)/sizeof(void *)]=reinterpret_cast<void *>(fixtureState);
    fakeDevice[offsetof(IDirect3DDevice3Vtbl,GetTextureStageState)/sizeof(void *)]=reinterpret_cast<void *>(fixtureStage);
    fakeDevice[offsetof(IDirect3DDevice3Vtbl,GetTexture)/sizeof(void *)]=reinterpret_cast<void *>(fixtureTexture);
}
static void captureFixture(IDirect3DDevice3 *device,void *vertices,WORD *indices) {
    frame_capture::begin(device,S_OK,true);
    if(!frame_capture::active)throw std::runtime_error("Fixture capture begin failed");
    frame_capture::draw(device,D3DPT_TRIANGLELIST,D3DFVF_TLVERTEX,vertices,3,indices,3,0x1234);
    if(!frame_capture::active)throw std::runtime_error("Fixture capture draw failed");
    frame_capture::end(device,S_OK);
    if(frame_capture::active || frame_capture::commandCount!=1)throw std::runtime_error("Fixture capture close failed");
    const auto textPath=frame_capture::root/"capture.jsonl";
    std::ifstream input(textPath);std::string text((std::istreambuf_iterator<char>(input)),{});
    if(text.find("\"complete\":true")==std::string::npos)throw std::runtime_error("Fixture capture incomplete");
    frame_capture::attempted=false;frame_capture::commandCount=0;frame_capture::storedBytes=0;
    frame_capture::scannedBytes=0;frame_capture::stored.clear();
    line("\"event\":\"capture_fixture\",\"passed\":true,\"draws\":1,\"texture_fixture\":false");
}
