"""Apply a checked, development-only last-corner projection experiment."""
from pathlib import Path
import argparse,hashlib,re,shutil
from apply_world_direct import replace

PIN='88ec9534cc3d0a1fc4186715c3decceb4ab7aa2ac1bfd7fb9a1767ce03f7b9d7'

def transform(text):
    normalized=re.sub(r'^; ModuleID = .*\n','',text.replace('\r\n','\n'))
    if hashlib.sha256(normalized.encode()).hexdigest()!=PIN:raise ValueError('Projection bypass requires exact complete original host IR')
    old='  br i1 %51155, label %51156, label %51180'
    if text.count(old)!=1:raise ValueError('Projection positive edge changed')
    text=text.replace(old,'  br i1 %51155, label %51156, label %projection_gate')
    setup='''projection_gate:
  %projection_memory = load ptr, ptr %MEMORY, align 4
  %projection_result = call i32 @mw34_projection_gate(ptr %state, ptr %projection_memory)
  %projection_accepted = icmp eq i32 %projection_result, 1
  br i1 %projection_accepted, label %projection_last, label %51180

projection_last:
  %projection_n = load i32, ptr %ECX, align 4
  %projection_i = sub i32 %projection_n, 1
  %projection_xyz_offset = mul i32 %projection_i, 12
  %projection_tl_offset = mul i32 %projection_i, 32
  %projection_xyz = add i32 %projection_xyz_offset, 7632548
  %projection_tl = add i32 %projection_tl_offset, 7533600
  store i32 %projection_xyz, ptr %EAX, align 4
  store i32 %projection_tl, ptr %EDX, align 4
  store i32 1, ptr %ESI, align 4
  store i32 5507461, ptr %NEXT_PC, align 4
  br label %51193

'''
    text=text.replace('51180:                                            ; preds = %51133',setup+'51180:                                            ; preds = %projection_gate')
    return text+'\ndeclare i32 @mw34_projection_gate(ptr, ptr)\n'

WRAPPERS='''
extern "C" unsigned mw34_projection_gate(State*s,void*p){
 alignas(16) unsigned char saved[512];__asm__ volatile("fxsave64 %0":"=m"(saved)::"memory");
 unsigned result{};try{if(!mf::owner||s!=&mf::owner->state)throw std::runtime_error("Projection gate owner mismatch");mf::owner->guard(p);result=mf::owner->projection_begin();}
 catch(...){__asm__ volatile("fxrstor64 %0"::"m"(saved):"memory");throw;}
 __asm__ volatile("fxrstor64 %0"::"m"(saved):"memory");return result;
}
extern "C" void mw34_projection_access(unsigned a,unsigned n,unsigned write)noexcept(false){
 alignas(16) unsigned char saved[512];__asm__ volatile("fxsave64 %0":"=m"(saved)::"memory");
 try{if(mf::owner)mf::owner->projection_access(a,n,write);}
 catch(...){__asm__ volatile("fxrstor64 %0"::"m"(saved):"memory");throw;}
 __asm__ volatile("fxrstor64 %0"::"m"(saved):"memory");
}
extern "C" void mw34_projection_flat_access(State*s,void*p,unsigned a,unsigned n,unsigned write)noexcept(false){
 alignas(16) unsigned char saved[512];__asm__ volatile("fxsave64 %0":"=m"(saved)::"memory");
 try{
  if(!mf::owner||s!=&mf::owner->state)throw std::runtime_error("Projection observer State owner mismatch");
  mf::owner->guard(p);mf::owner->projection_access(a,n,write,s);
 }catch(...){__asm__ volatile("fxrstor64 %0"::"m"(saved):"memory");throw;}
 __asm__ volatile("fxrstor64 %0"::"m"(saved):"memory");
}
'''

def apply(host):
    for name in ['projection_stage.inc','projection_contract.hpp']:
        shutil.copyfile(Path(__file__).parent/'native-overrides'/name,host/name)
    replace(host/'vk_scene.hpp','#include "world_fast_binding.hpp"','#include "world_fast_binding.hpp"\n#include "projection_contract.hpp"')
    stage=host/'mfc_stage.hpp'
    replace(stage,'#include "world_direct_stage.inc"','#include "world_direct_stage.inc"\n#include "projection_stage.inc"')
    replace(stage,'void*r=remaster_body_inner(s,target,p,body);world_scope=std::move(previous);',
            'void*r=remaster_body_inner(s,target,p,body);if(projection_token)throw std::runtime_error("Unconsumed projection token at mesh return");world_scope=std::move(previous);')
    replace(stage,'template<class T>T read(unsigned a,void*p){guard(p);','template<class T>T read(unsigned a,void*p){guard(p);projection_access(a,sizeof(T),0);')
    replace(stage,'std::memcpy(fp,&v,sizeof(T));++writes;return;', 'std::memcpy(fp,&v,sizeof(T));projection_access(a,sizeof(T),1);++writes;return;')
    replace(host/'world_direct_stage.inc','void world_capture(D3DCmd&draw){','void world_capture(D3DCmd&draw){\n if(draw.model)return;')
    provider=host/'d3d_provider.inc'
    replace(provider,'get_bytes(verts,c.vertices.data(),32*vcount);','projection_vertices(c.vertices.data(),verts,vcount,type,fvf,load(state.gpr.rsp.dword));')
    replace(provider,'zoom_capture_command(c);divergence_trace(c);world_capture(c);',
            'zoom_capture_command(c);projection_submit(c,root,load(state.gpr.rsp.dword),verts,fvf,vcount);divergence_trace(c);world_capture(c);')
    replace(host/'vdd.inc',' world_present();',' world_present();projection_present();')
    # Cover actual scalar fast transfers, not just the slow Stage methods.
    fast=host/'fast_bridges.cpp'
    replace(fast,'namespace {\nusing Hit', 'extern "C" void mw34_projection_access(unsigned,unsigned,unsigned)noexcept(false);\nnamespace {\nusing Hit')
    replace(fast,'    const unsigned char *b = cached(g, a, sizeof(T), 1);','    if(a<0x73041cU&&(unsigned long long)a+sizeof(T)>0x72f41cU)mw34_projection_access(a,sizeof(T),0);\n    const unsigned char *b = cached(g, a, sizeof(T), 1);')
    replace(fast,'    __builtin_memcpy(b, &v, sizeof(T));','    __builtin_memcpy(b, &v, sizeof(T));\n    if(a<0x73041cU&&(unsigned long long)a+sizeof(T)>0x72f41cU)mw34_projection_access(a,sizeof(T),1);')
    memory=host/'guest_memory_cached.cpp'
    text=memory.read_text();memory.write_text('extern "C" void mw34_projection_access(unsigned,unsigned,unsigned)noexcept(false);\n'+text)
    replace(memory,'void GuestMemory::read(GuestAddress address, std::span<std::byte> destination) const {',
            'void GuestMemory::read(GuestAddress address, std::span<std::byte> destination) const {\n    if(address.value<0x73041cU&&std::uint64_t(address.value)+destination.size()>0x72f41cU)mw34_projection_access(address.value,unsigned(destination.size()),0);')
    replace(memory,'std::copy_n(source.data(), source.size(), h->bytes + (address.value - h->start));',
            'std::copy_n(source.data(), source.size(), h->bytes + (address.value - h->start));\n        if(address.value<0x73041cU&&std::uint64_t(address.value)+source.size()>0x72f41cU)mw34_projection_access(address.value,unsigned(source.size()),1);')
    replace(memory,'std::copy_n(source.data(), source.size(), base_ + address.value);',
            'std::copy_n(source.data(), source.size(), base_ + address.value);\n    if(address.value<0x73041cU&&std::uint64_t(address.value)+source.size()>0x72f41cU)mw34_projection_access(address.value,unsigned(source.size()),1);')
    cpp=host/'composition.cpp';cpp.write_text(cpp.read_text()+WRAPPERS)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('host_source',type=Path)
    apply(parser.parse_args().host_source.resolve(strict=True))
