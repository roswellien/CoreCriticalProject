#pragma once
#include "admission.hpp"
#include "core/guest_address.hpp"
#include <algorithm>
#include <limits>

namespace mw34::m4_runtime {
// Narrow literal-data admission for the recovered staged CRT. The frozen game
// loader intentionally admits fixed-base EXEs, not relocatable DLL modules.
// This does not load a DLL, relocate anything, parse/resolve imports, map its
// globals, run DllMain, or claim the host selected this provider for the game.
inline std::vector<std::byte> staged_crt_code(std::span<const std::byte> file,
                                              GuestAddress start,std::uint32_t size) {
    const auto require=[](bool ok,const char *why){if(!ok)throw std::invalid_argument(why);};
    require(file.size()==266293 && m4::sha256(file)=="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7",
            "Only exact recovered staged MSVCRT provider data is admitted");
    const auto word=[&](std::uint64_t offset){require(offset+2<=file.size(),"Provider word bounds");return std::uint16_t(std::to_integer<unsigned>(file[offset])|(std::to_integer<unsigned>(file[offset+1])<<8));};
    const auto dword=[&](std::uint64_t offset){require(offset+4<=file.size(),"Provider DWORD bounds");std::uint32_t result{};for(unsigned i=0;i<4;++i)result|=std::to_integer<std::uint32_t>(file[offset+i])<<(i*8);return result;};
    require(word(0)==0x5a4d,"Provider DOS header");const std::uint64_t pe=dword(0x3c);
    require(dword(pe)==0x4550 && word(pe+4)==0x14c,"Provider PE32 x86 header");
    const auto count=word(pe+6),optional_size=word(pe+20);const auto optional=pe+24;
    require(count>0&&count<=96&&optional_size>=224&&optional+optional_size+40ULL*count<=file.size(),"Provider complete section table bounds");
    require(word(optional)==0x10b&&dword(optional+28)==0x78000000&&(word(pe+22)&0x2000),"Recovered provider DLL preferred-address identity");
    const auto image_size=dword(optional+56),headers=dword(optional+60);
    require(headers<=file.size()&&headers>=optional+optional_size+40ULL*count&&image_size>headers&&image_size<=128*1024*1024,"Provider header/image bounds");
    struct Section {std::uint32_t address,mapped,raw_offset,raw_size,flags;};std::vector<Section> sections;
    for(unsigned i=0;i<count;++i){
        const auto o=optional+optional_size+40ULL*i;
        const auto virtual_size=dword(o+8),address=dword(o+12),raw_size=dword(o+16),raw_offset=dword(o+20),flags=dword(o+36);
        const auto mapped=std::max(virtual_size,raw_size);
        require(address>=headers&&std::uint64_t{address}+mapped<=image_size&&std::uint64_t{0x78000000}+address+mapped<=(std::uint64_t{1}<<32),"Provider section virtual bounds");
        require(!raw_size||(raw_offset>=headers&&std::uint64_t{raw_offset}+raw_size<=file.size()),"Provider section raw bounds");
        for(const auto &old:sections){
            require(!mapped||!old.mapped||std::uint64_t{address}+mapped<=old.address||std::uint64_t{old.address}+old.mapped<=address,"Provider virtual overlap");
            require(!raw_size||!old.raw_size||std::uint64_t{raw_offset}+raw_size<=old.raw_offset||std::uint64_t{old.raw_offset}+old.raw_size<=raw_offset,"Provider raw overlap");
        }
        sections.push_back({address,mapped,raw_offset,raw_size,flags});
    }
    require(size>0&&size<=65536&&start.value>=0x78000000&&std::uint64_t{start.value}+size<=(std::uint64_t{1}<<32),"Provider literal source bounds");
    const auto rva=start.value-0x78000000;
    for(const auto &section:sections){
        if(rva>=section.address&&std::uint64_t{rva}+size<=std::uint64_t{section.address}+section.raw_size){
            require((section.flags&0x60000000)==0x60000000&&!(section.flags&0x80000000),"Provider source must be file-backed read/execute, not writable");
            const auto offset=std::uint64_t{section.raw_offset}+rva-section.address;
            return {file.begin()+static_cast<std::ptrdiff_t>(offset),file.begin()+static_cast<std::ptrdiff_t>(offset+size)};
        }
    }
    throw std::invalid_argument("Provider source is not an exact file-backed RX slice");
}
} // namespace mw34::m4_runtime
