"""Close audited host direct-access gaps in a private projection-watch host."""
from pathlib import Path
import argparse
from apply_world_direct import replace

WRAPPERS = r'''
extern "C" void mw34_projection_memory_access(const void*memory,unsigned a,unsigned long long n,unsigned write)noexcept(false){
 if(!mf::owner||memory!=&mf::owner->runtime.memory())return;
 if(n>0xffffffffULL)throw std::runtime_error("Projection watch transfer exceeds guest address space");
 mw34_projection_access(a,unsigned(n),write);
}
extern "C" void mw34_projection_memory_lifecycle(const void*a,const void*b)noexcept{
 if(mf::owner&&(a==&mf::owner->runtime.memory()||b==&mf::owner->runtime.memory())){
  std::fputs("Projection watch forbids active guest address-space copy/move\n",stderr);std::abort();
 }
}
'''

def replace_n(path,old,new,count):
 text=path.read_text()
 if text.count(old)!=count:raise ValueError(f'{path.name}: expected {count} audited sites for {old}')
 path.write_text(text.replace(old,new))

def apply(host):
 stage=host/'mfc_stage.hpp'
 replace(stage,'inline bool ftol_core(State*st,unsigned pc,void*p,unsigned&ret_out){',r'''inline void projection_ftol_span(unsigned ss,unsigned esp){
 const std::uint64_t top=std::uint64_t(ss)+esp;
 if(top<16||top+4>0x100000000ULL||(top-16<0x73041cULL&&top+4>0x72f41cULL))
  throw std::runtime_error("Projection watch: direct FTOL stack overlaps scratch or wraps");
}
inline bool ftol_core(State*st,unsigned pc,void*p,unsigned&ret_out){''')
 replace(stage,'auto mem=[&](unsigned a){return M+a;};','projection_ftol_span(ss,esp0);\n auto mem=[&](unsigned a){return M+a;};')
 replace(stage,'unsigned char*mb=static_cast<unsigned char*>(p)+(ss+esp0-0x10);','projection_ftol_span(ss,esp0);\n unsigned char*mb=static_cast<unsigned char*>(p)+(ss+esp0-0x10);')
 memory=host/'guest_memory_cached.cpp'
 replace(memory,'extern "C" void mw34_projection_access(unsigned,unsigned,unsigned)noexcept(false);',
  'extern "C" void mw34_projection_memory_access(const void*,unsigned,unsigned long long,unsigned)noexcept(false);\nextern "C" void mw34_projection_memory_lifecycle(const void*,const void*)noexcept;')
 replace(memory,'mw34_projection_access(address.value,unsigned(destination.size()),0);','mw34_projection_memory_access(this,address.value,destination.size(),0);')
 replace_n(memory,'mw34_projection_access(address.value,unsigned(source.size()),1);','mw34_projection_memory_access(this,address.value,source.size(),1);',2)
 replace(memory,'GuestMemory &GuestMemory::operator=(const GuestMemory &other) {','GuestMemory &GuestMemory::operator=(const GuestMemory &other) {\n    mw34_projection_memory_lifecycle(this,&other);')
 replace(memory,'GuestMemory &GuestMemory::operator=(GuestMemory &&other) noexcept {','GuestMemory &GuestMemory::operator=(GuestMemory &&other) noexcept {\n    mw34_projection_memory_lifecycle(this,&other);')
 replace_n(memory,'    other.base_ = nullptr;', '    mw34_projection_memory_lifecycle(this,&other);\n    other.base_ = nullptr;',2)
 cpp=host/'composition.cpp'
 replace(cpp,'throw std::runtime_error("Active raw80 x87 bridge scratch");',r'''throw std::runtime_error("Active raw80 x87 bridge scratch");
 const auto base=reinterpret_cast<std::uintptr_t>(mf::owner->runtime.memory().flat_base());
 for(const void*q:{in,out}){const auto v=reinterpret_cast<std::uintptr_t>(q);
  if(v>=base&&v-base<0x100000000ULL)throw std::runtime_error("Projection watch: raw80 operand aliases guest reservation");}
''')
 cpp.write_text(cpp.read_text()+WRAPPERS)

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('host_source',type=Path)
 apply(parser.parse_args().host_source.resolve(strict=True))
