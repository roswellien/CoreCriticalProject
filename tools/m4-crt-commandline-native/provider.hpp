#pragma once
#include "runtime.hpp"
#include "admission.hpp"
#include <algorithm>
#include <cctype>
#include <cstring>
namespace mw34::m4_cmd_native {
inline constexpr GuestAddress writer{0x7800188c},provider_iat{0x7802e034},provider_global{0x78037174},game_iat{0x5bb518},service_gate{0x10000200},capture_gate{0x10000100},return_pc{0x78001892},buffer_start{0x33000000};
inline constexpr char exact_provider_sha[]="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7";
inline constexpr char exact_writer_sha[]="6300f3f77dc2f2ce6ea36590028dd7f3b078c721a08d6daac27ebc8c636b5ac3";
inline void require(bool ok,const char*why){if(!ok)throw std::invalid_argument(why);}
inline bool library(std::string s,const char*expected){for(auto&x:s)x=static_cast<char>(std::tolower(static_cast<unsigned char>(x)));return s==expected;}
class Provider {
    std::vector<std::byte> bytes_;std::uint32_t optional_{};
    struct Section {std::uint32_t rva,size,offset,raw,flags;};std::vector<Section> sections_;
    std::uint32_t u32(std::uint64_t a)const{require(a+4<=bytes_.size(),"Provider DWORD bounds");std::uint32_t v{};for(unsigned i=0;i<4;++i)v|=std::to_integer<unsigned>(bytes_[a+i])<<(8*i);return v;}
    std::uint16_t u16(std::uint64_t a)const{require(a+2<=bytes_.size(),"Provider WORD bounds");return std::uint16_t(std::to_integer<unsigned>(bytes_[a])|(std::to_integer<unsigned>(bytes_[a+1])<<8));}
    std::uint64_t offset(std::uint32_t rva,unsigned size)const{for(auto&s:sections_)if(rva>=s.rva&&std::uint64_t(rva)+size<=std::uint64_t(s.rva)+s.raw)return std::uint64_t(s.offset)+rva-s.rva;throw std::invalid_argument("Provider file-backed RVA required");}
    std::string name(std::uint32_t rva)const{std::string result;for(unsigned n=0;n<4096;++n){auto o=offset(rva+n,1);auto c=std::to_integer<unsigned char>(bytes_[o]);if(!c)return result;require(c<128,"ASCII provider metadata required");result.push_back(static_cast<char>(c));}throw std::invalid_argument("Provider name bound");}
  public:
    explicit Provider(std::span<const std::byte>file):bytes_(file.begin(),file.end()){
        require(bytes_.size()==266293&&m4::sha256(bytes_)==exact_provider_sha,"Exact staged provider required");const auto pe=u32(0x3c);require(u16(0)==0x5a4d&&u32(pe)==0x4550&&u16(pe+4)==0x14c,"Provider PE32 headers");optional_=pe+24;const auto count=u16(pe+6),os=u16(pe+20);require(count&&count<=96&&os>=224&&u16(optional_)==0x10b&&u32(optional_+28)==0x78000000&&(u16(pe+22)&0x2000),"Preferred-base provider DLL identity");
        for(unsigned i=0;i<count;++i){auto o=optional_+os+i*40;Section s{u32(o+12),u32(o+8),u32(o+20),u32(o+16),u32(o+36)};require(std::uint64_t(s.offset)+s.raw<=bytes_.size()&&std::uint64_t(s.rva)+std::max(s.size,s.raw)<=u32(optional_+56),"Provider section bounds");sections_.push_back(s);}
        require(m4::sha256(slice(writer,11,0x60000000))==exact_writer_sha,"Exact RX CALL/MOV required");require(dword(provider_global)==0,"Provider global file identity only");(void)slice(provider_global,4,0xc0000000);(void)slice(provider_iat,4,0x40000000);
        unsigned found{};const auto dir=u32(optional_+104),size=u32(optional_+108);require(size>=20&&size<=20*256,"Provider descriptor bound");bool ended{};
        for(unsigned d=0;d<size/20;++d){const auto o=offset(dir+d*20,20);const auto original=u32(o),nm=u32(o+12),iat=u32(o+16);if(!original&&!nm&&!iat){ended=true;break;}auto lib=name(nm);bool term{};
            for(unsigned j=0;j<8192;++j){auto value=u32(offset((original?original:iat)+j*4,4));if(!value){term=true;break;}auto slot=0x78000000U+iat+j*4;if(slot==provider_iat.value){require(!(value&0x80000000)&&library(lib,"kernel32.dll")&&name(value+2)=="GetCommandLineA"&&dword(provider_iat)==value,"Exact unique provider KERNEL32 GetCommandLineA owner required");++found;}}
            require(term,"Provider thunk terminator bound");
        }require(ended&&found==1,"One provider import and descriptor terminator required");
        const auto ex=u32(optional_+96);const auto eo=offset(ex,40);const auto nf=u32(eo+20),nn=u32(eo+24),fs=u32(eo+28),ns=u32(eo+32),oslots=u32(eo+36);require(nf&&nf<=65536&&nn<=nf,"Provider export bound");unsigned exports{};
        for(unsigned i=0;i<nn;++i)if(name(u32(offset(ns+i*4,4)))=="_acmdln"){auto ord=u16(offset(oslots+i*2,2));require(ord<nf&&u32(offset(fs+ord*4,4))+0x78000000U==provider_global.value,"Exact _acmdln data export required");++exports;}require(exports==1,"One exact provider data export required");
    }
    [[nodiscard]] std::vector<std::byte> slice(GuestAddress a,unsigned n,std::uint32_t flags)const{
        require(n&&n<=65536&&a.value>=0x78000000&&std::uint64_t(a.value)+n<=0x100000000ULL,"Provider slice bounds");auto r=a.value-0x78000000;
        for(auto&s:sections_)if(r>=s.rva&&std::uint64_t(r)+n<=std::uint64_t(s.rva)+std::min(s.size,s.raw)){require((s.flags&0xe0000000)==flags,"Provider source permissions identity");auto o=offset(r,n);return {bytes_.begin()+o,bytes_.begin()+o+n};}throw std::invalid_argument("Complete file-backed provider section required");
    }
    [[nodiscard]] std::uint32_t dword(GuestAddress a)const{return u32(offset(a.value-0x78000000,4));}
};
}
