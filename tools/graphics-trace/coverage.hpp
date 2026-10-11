#pragma once
// These typed call-through guards deliberately reject a selected capture when
// an unsupported rendering command occurs. They never block the game command.
static HRESULT STDMETHODCALLTYPE guardedBegin(IDirect3DDevice3 *self,D3DPRIMITIVETYPE type,DWORD fvf,DWORD flags) {
    auto call=reinterpret_cast<decltype(IDirect3DDevice3Vtbl::Begin)>(original(self,offsetof(IDirect3DDevice3Vtbl,Begin)/sizeof(void *)));
    coverageViolation("unsupported_immediate_begin");return call(self,type,fvf,flags);
}
static HRESULT STDMETHODCALLTYPE guardedBeginIndexed(IDirect3DDevice3 *self,D3DPRIMITIVETYPE type,DWORD fvf,void *vertices,DWORD count,DWORD flags) {
    auto call=reinterpret_cast<decltype(IDirect3DDevice3Vtbl::BeginIndexed)>(original(self,offsetof(IDirect3DDevice3Vtbl,BeginIndexed)/sizeof(void *)));
    coverageViolation("unsupported_immediate_indexed");return call(self,type,fvf,vertices,count,flags);
}
static HRESULT STDMETHODCALLTYPE guardedStrided(IDirect3DDevice3 *self,D3DPRIMITIVETYPE type,DWORD fvf,D3DDRAWPRIMITIVESTRIDEDDATA *vertices,DWORD count,DWORD flags) {
    auto call=reinterpret_cast<decltype(IDirect3DDevice3Vtbl::DrawPrimitiveStrided)>(original(self,offsetof(IDirect3DDevice3Vtbl,DrawPrimitiveStrided)/sizeof(void *)));
    coverageViolation("unsupported_strided_draw");return call(self,type,fvf,vertices,count,flags);
}
static HRESULT STDMETHODCALLTYPE guardedIndexedStrided(IDirect3DDevice3 *self,D3DPRIMITIVETYPE type,DWORD fvf,D3DDRAWPRIMITIVESTRIDEDDATA *vertices,DWORD count,WORD *indices,DWORD indexCount,DWORD flags) {
    auto call=reinterpret_cast<decltype(IDirect3DDevice3Vtbl::DrawIndexedPrimitiveStrided)>(original(self,offsetof(IDirect3DDevice3Vtbl,DrawIndexedPrimitiveStrided)/sizeof(void *)));
    coverageViolation("unsupported_indexed_strided_draw");return call(self,type,fvf,vertices,count,indices,indexCount,flags);
}
static HRESULT STDMETHODCALLTYPE guardedVB(IDirect3DDevice3 *self,D3DPRIMITIVETYPE type,IDirect3DVertexBuffer *buffer,DWORD start,DWORD count,DWORD flags) {
    auto call=reinterpret_cast<decltype(IDirect3DDevice3Vtbl::DrawPrimitiveVB)>(original(self,offsetof(IDirect3DDevice3Vtbl,DrawPrimitiveVB)/sizeof(void *)));
    coverageViolation("unsupported_vertex_buffer_draw");return call(self,type,buffer,start,count,flags);
}
static HRESULT STDMETHODCALLTYPE guardedIndexedVB(IDirect3DDevice3 *self,D3DPRIMITIVETYPE type,IDirect3DVertexBuffer *buffer,WORD *indices,DWORD count,DWORD flags) {
    auto call=reinterpret_cast<decltype(IDirect3DDevice3Vtbl::DrawIndexedPrimitiveVB)>(original(self,offsetof(IDirect3DDevice3Vtbl,DrawIndexedPrimitiveVB)/sizeof(void *)));
    coverageViolation("unsupported_indexed_vertex_buffer_draw");return call(self,type,buffer,indices,count,flags);
}
static HRESULT STDMETHODCALLTYPE guardedClear(IDirect3DViewport3 *self,DWORD count,D3DRECT *rects,DWORD flags) {
    auto call=reinterpret_cast<decltype(IDirect3DViewport3Vtbl::Clear)>(original(self,offsetof(IDirect3DViewport3Vtbl,Clear)/sizeof(void *)));
    clearDiagnostic(false,count,rects,flags,0,0,0);
    coverageViolation("unsupported_viewport_clear");return call(self,count,rects,flags);
}
static HRESULT STDMETHODCALLTYPE guardedClear2(IDirect3DViewport3 *self,DWORD count,D3DRECT *rects,DWORD flags,D3DCOLOR color,D3DVALUE depth,DWORD stencil) {
    auto call=reinterpret_cast<decltype(IDirect3DViewport3Vtbl::Clear2)>(original(self,offsetof(IDirect3DViewport3Vtbl,Clear2)/sizeof(void *)));
    clearDiagnostic(true,count,rects,flags,color,depth,stencil);
    coverageViolation("unsupported_viewport_clear2");return call(self,count,rects,flags,color,depth,stencil);
}
static HRESULT STDMETHODCALLTYPE observedViewport(IDirect3DDevice3 *self,IDirect3DViewport3 **output) {
    auto call=reinterpret_cast<decltype(IDirect3DDevice3Vtbl::GetCurrentViewport)>(original(self,offsetof(IDirect3DDevice3Vtbl,GetCurrentViewport)/sizeof(void *)));
    const auto result=call(self,output);
    {State guard;if(SUCCEEDED(result) && output && *output)observe(*output,Kind::viewport3);}
    return result;
}
static HRESULT STDMETHODCALLTYPE observedAddViewport(IDirect3DDevice3 *self,IDirect3DViewport3 *viewport) {
    auto call=reinterpret_cast<decltype(IDirect3DDevice3Vtbl::AddViewport)>(original(self,offsetof(IDirect3DDevice3Vtbl,AddViewport)/sizeof(void *)));
    const auto result=call(self,viewport);
    {State guard;if(SUCCEEDED(result))observe(viewport,Kind::viewport3);}
    return result;
}
static HRESULT STDMETHODCALLTYPE observedSetViewport(IDirect3DDevice3 *self,IDirect3DViewport3 *viewport) {
    auto call=reinterpret_cast<decltype(IDirect3DDevice3Vtbl::SetCurrentViewport)>(original(self,offsetof(IDirect3DDevice3Vtbl,SetCurrentViewport)/sizeof(void *)));
    const auto result=call(self,viewport);
    {State guard;if(SUCCEEDED(result))observe(viewport,Kind::viewport3);}
    return result;
}
static void installCoverage(Entry &e) {
#define HOOK(table,method,handler) e.clone[offsetof(table,method)/sizeof(void *)]=reinterpret_cast<void *>(&handler)
    if(e.kind==Kind::device3) {
        HOOK(IDirect3DDevice3Vtbl,Begin,guardedBegin);
        HOOK(IDirect3DDevice3Vtbl,BeginIndexed,guardedBeginIndexed);
        HOOK(IDirect3DDevice3Vtbl,DrawPrimitiveStrided,guardedStrided);
        HOOK(IDirect3DDevice3Vtbl,DrawIndexedPrimitiveStrided,guardedIndexedStrided);
        HOOK(IDirect3DDevice3Vtbl,DrawPrimitiveVB,guardedVB);
        HOOK(IDirect3DDevice3Vtbl,DrawIndexedPrimitiveVB,guardedIndexedVB);
        HOOK(IDirect3DDevice3Vtbl,GetCurrentViewport,observedViewport);
        HOOK(IDirect3DDevice3Vtbl,AddViewport,observedAddViewport);
        HOOK(IDirect3DDevice3Vtbl,SetCurrentViewport,observedSetViewport);
    } else if(e.kind==Kind::viewport3) {
        HOOK(IDirect3DViewport3Vtbl,Clear,guardedClear);
        HOOK(IDirect3DViewport3Vtbl,Clear2,guardedClear2);
    }
#undef HOOK
}
