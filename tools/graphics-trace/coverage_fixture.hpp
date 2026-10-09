#pragma once
static unsigned coverageCalls=0;
static HRESULT coverageReply(bool valid) {
    ++coverageCalls;SetLastError(0x44556677);return valid?S_FALSE:E_INVALIDARG;
}
static HRESULT STDMETHODCALLTYPE fixtureBegin(IDirect3DDevice3 *,D3DPRIMITIVETYPE type,DWORD fvf,DWORD flags) {
    return coverageReply(type==D3DPT_TRIANGLELIST && fvf==D3DFVF_TLVERTEX && flags==99);
}
static HRESULT STDMETHODCALLTYPE fixtureBeginIndexed(IDirect3DDevice3 *,D3DPRIMITIVETYPE type,DWORD fvf,void *vertices,DWORD count,DWORD flags) {
    return coverageReply(type==D3DPT_TRIANGLELIST && fvf==D3DFVF_TLVERTEX && vertices && count==3 && flags==99);
}
static HRESULT STDMETHODCALLTYPE fixtureStrided(IDirect3DDevice3 *,D3DPRIMITIVETYPE type,DWORD fvf,D3DDRAWPRIMITIVESTRIDEDDATA *vertices,DWORD count,DWORD flags) {
    return coverageReply(type==D3DPT_TRIANGLELIST && fvf==D3DFVF_TLVERTEX && vertices && count==3 && flags==99);
}
static HRESULT STDMETHODCALLTYPE fixtureIndexedStrided(IDirect3DDevice3 *,D3DPRIMITIVETYPE type,DWORD fvf,D3DDRAWPRIMITIVESTRIDEDDATA *vertices,DWORD count,WORD *indices,DWORD indexCount,DWORD flags) {
    return coverageReply(type==D3DPT_TRIANGLELIST && fvf==D3DFVF_TLVERTEX && vertices && count==3 && indices && indices[2]==2 && indexCount==3 && flags==99);
}
static HRESULT STDMETHODCALLTYPE fixtureVB(IDirect3DDevice3 *,D3DPRIMITIVETYPE type,IDirect3DVertexBuffer *buffer,DWORD start,DWORD count,DWORD flags) {
    return coverageReply(type==D3DPT_TRIANGLELIST && buffer && start==7 && count==3 && flags==99);
}
static HRESULT STDMETHODCALLTYPE fixtureIndexedVB(IDirect3DDevice3 *,D3DPRIMITIVETYPE type,IDirect3DVertexBuffer *buffer,WORD *indices,DWORD count,DWORD flags) {
    return coverageReply(type==D3DPT_TRIANGLELIST && buffer && indices && indices[2]==2 && count==3 && flags==99);
}
static HRESULT STDMETHODCALLTYPE fixtureClear(IDirect3DViewport3 *,DWORD count,D3DRECT *rects,DWORD flags) {
    return coverageReply(count==1 && rects && rects->x2==2 && flags==D3DCLEAR_TARGET);
}
static HRESULT STDMETHODCALLTYPE fixtureClear2(IDirect3DViewport3 *,DWORD count,D3DRECT *rects,DWORD flags,D3DCOLOR color,D3DVALUE depth,DWORD stencil) {
    return coverageReply(count==1 && rects && rects->x2==2 && flags==D3DCLEAR_TARGET && color==0x12345678 && depth==0.5F && stencil==7);
}
static void setupCoverageFixture() {
#define MOCK(method,handler) fakeDevice[offsetof(IDirect3DDevice3Vtbl,method)/sizeof(void *)]=reinterpret_cast<void *>(&handler)
    MOCK(Begin,fixtureBegin);MOCK(BeginIndexed,fixtureBeginIndexed);
    MOCK(DrawPrimitiveStrided,fixtureStrided);MOCK(DrawIndexedPrimitiveStrided,fixtureIndexedStrided);
    MOCK(DrawPrimitiveVB,fixtureVB);MOCK(DrawIndexedPrimitiveVB,fixtureIndexedVB);
#undef MOCK
    fixtureViewportTable.Clear=fixtureClear;fixtureViewportTable.Clear2=fixtureClear2;
}
static void coverageFixture(IDirect3DDevice3 *device,void *vertices,WORD *indices) {
    D3DDRAWPRIMITIVESTRIDEDDATA strided{};
    auto *buffer=reinterpret_cast<IDirect3DVertexBuffer *>(vertices);
    IDirect3DViewport3 *viewport{};
    if(device->lpVtbl->GetCurrentViewport(device,&viewport)!=S_OK || !viewport)
        throw std::runtime_error("Viewport guard discovery failed");
    D3DRECT rect{0,0,2,2};
    auto test=[&](auto call) {
        frame_capture::active=true;
        if(call()!=S_FALSE || GetLastError()!=0x44556677 || frame_capture::active)
            throw std::runtime_error("Coverage forwarding/abort guard failed");
    };
    test([&]{return device->lpVtbl->Begin(device,D3DPT_TRIANGLELIST,D3DFVF_TLVERTEX,99);});
    test([&]{return device->lpVtbl->BeginIndexed(device,D3DPT_TRIANGLELIST,D3DFVF_TLVERTEX,vertices,3,99);});
    test([&]{return device->lpVtbl->DrawPrimitiveStrided(device,D3DPT_TRIANGLELIST,D3DFVF_TLVERTEX,&strided,3,99);});
    test([&]{return device->lpVtbl->DrawIndexedPrimitiveStrided(device,D3DPT_TRIANGLELIST,D3DFVF_TLVERTEX,&strided,3,indices,3,99);});
    test([&]{return device->lpVtbl->DrawPrimitiveVB(device,D3DPT_TRIANGLELIST,buffer,7,3,99);});
    test([&]{return device->lpVtbl->DrawIndexedPrimitiveVB(device,D3DPT_TRIANGLELIST,buffer,indices,3,99);});
    test([&]{return viewport->lpVtbl->Clear(viewport,1,&rect,D3DCLEAR_TARGET);});
    test([&]{return viewport->lpVtbl->Clear2(viewport,1,&rect,D3DCLEAR_TARGET,0x12345678,0.5F,7);});
    if(device->lpVtbl->Begin(device,D3DPT_TRIANGLELIST,D3DFVF_TLVERTEX,0)!=E_INVALIDARG || GetLastError()!=0x44556677)
        throw std::runtime_error("Coverage failed-command forwarding changed result");
    if(coverageCalls!=9 || indices[2]!=2 || rect.x2!=2)
        throw std::runtime_error("Coverage fixture accounting/data changed");
    line("\"event\":\"coverage_fixture\",\"passed\":true,\"guarded_commands\":8,\"forwarded_calls\":9,\"last_error_preserved\":true");
}
