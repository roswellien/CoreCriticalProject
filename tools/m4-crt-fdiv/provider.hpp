#pragma once
#include "runtime.hpp"
#include "admission.hpp"
#include <algorithm>
#include <cctype>
#include <cstring>
namespace mw34::m4_crt_fdiv {
inline constexpr unsigned writer=0x78004254,outer_call=0x78004230,outer_return=0x78004232;
inline constexpr unsigned game_iat=0x5bb508,global=0x78037c2c,callback_global=0x78037c28;
inline constexpr unsigned module_iat=0x7802e098,proc_iat=0x7802e0d0;
inline constexpr unsigned module_route=0x11000100,proc_route=0x11000200,feature_route=0x11000300,module_token=0x11001000;
inline constexpr unsigned stack_begin=0x20001000,stack_bytes=4096,entry_esp=0x20001800;
inline constexpr char provider_sha[]="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7";
inline void require(bool ok,const char*detail){if(!ok)throw std::invalid_argument(detail);}
inline bool library(std::string s,const char*name){for(auto&v:s)v=static_cast<char>(std::tolower(static_cast<unsigned char>(v)));return s==name;}
class Provider {
    std::vector<std::byte>file_;unsigned optional_{};
    struct Section{unsigned address,virtual_bytes,raw,offset,flags;};std::vector<Section>sections_;
    unsigned word(unsigned p)const{require(std::uint64_t(p)+2<=file_.size(),"Provider WORD bound");return std::to_integer<unsigned>(file_[p])|(std::to_integer<unsigned>(file_[p+1])<<8);}
    unsigned dword(unsigned p)const{require(std::uint64_t(p)+4<=file_.size(),"Provider DWORD bound");unsigned v{};for(unsigned i=0;i<4;++i)v|=std::to_integer<unsigned>(file_[p+i])<<(i*8);return v;}
    unsigned offset(unsigned r,unsigned n)const{for(auto&s:sections_)if(r>=s.address&&std::uint64_t(r)+n<=std::uint64_t(s.address)+s.raw)return s.offset+r-s.address;throw std::invalid_argument("Provider file-backed extent required");}
    std::string name(unsigned r)const{std::string v;for(unsigned i=0;i<4096;++i){auto c=std::to_integer<unsigned>(file_[offset(r+i,1)]);if(!c)return v;require(c<128,"ASCII provider name");v.push_back(static_cast<char>(c));}throw std::invalid_argument("Provider string bound");}
    void import(unsigned slot,const char*symbol,unsigned raw)const{
        const unsigned directory=dword(optional_+104),size=dword(optional_+108);require(size>=20&&size<=20*256,"Provider import descriptor bound");unsigned matches{};bool ended{};
        for(unsigned i=0;i<size/20;++i){auto p=offset(directory+i*20,20);auto original=dword(p),nm=dword(p+12),first=dword(p+16);if(!original&&!nm&&!first){ended=true;break;}bool term{};
            for(unsigned j=0;j<8192;++j){auto value=dword(offset((original?original:first)+4*j,4));if(!value){term=true;break;}if(0x78000000U+first+4*j==slot){require(!(value&0x80000000)&&library(name(nm),"kernel32.dll")&&name(value+2)==symbol&&value==raw&&value==value_at(slot),"Exact unique named provider API owner");++matches;}}require(term,"Provider import thunk terminator");
        }require(ended&&matches==1,"One provider import owner and terminator");
    }
  public:
    explicit Provider(std::span<const std::byte>bytes):file_(bytes.begin(),bytes.end()){
        require(file_.size()==266293&&m4::sha256(file_)==provider_sha,"Exact staged provider identity");auto pe=dword(0x3c);require(word(0)==0x5a4d&&dword(pe)==0x4550&&word(pe+4)==0x14c,"Provider PE32 x86 headers");optional_=pe+24;auto count=word(pe+6),opt=word(pe+20);require(count&&count<=96&&opt>=224&&word(optional_)==0x10b&&dword(optional_+28)==0x78000000&&(word(pe+22)&0x2000),"Exact preferred-base provider DLL");
        for(unsigned i=0;i<count;++i){auto p=optional_+opt+i*40;Section s{dword(p+12),dword(p+8),dword(p+16),dword(p+20),dword(p+36)};require(std::uint64_t(s.offset)+s.raw<=file_.size()&&std::uint64_t(s.address)+std::max(s.raw,s.virtual_bytes)<=dword(optional_+56),"Provider section bounds");sections_.push_back(s);}
        import(module_iat,"GetModuleHandleA",0x345d2);import(proc_iat,"GetProcAddress",0x346ac);
        require(value_at(callback_global)==writer&&value_at(global)==0,"Literal provider callback/uninitialized data values");
        auto dir=dword(optional_+96),p=offset(dir,40);auto count_functions=dword(p+20),count_names=dword(p+24),functions=dword(p+28),names=dword(p+32),ordinals=dword(p+36);require(count_functions&&count_functions<=65536&&count_names<=count_functions,"Provider export bounds");unsigned found{};
        for(unsigned i=0;i<count_names;++i)if(name(dword(offset(names+4*i,4)))=="_adjust_fdiv"){auto index=word(offset(ordinals+2*i,2));require(index<count_functions&&0x78000000U+dword(offset(functions+4*index,4))==global,"Exact owned provider data export");++found;}require(found==1,"Unique provider data export");
    }
    [[nodiscard]] unsigned value_at(unsigned address)const{require(address>=0x78000000,"Provider address domain");return dword(offset(address-0x78000000,4));}
    [[nodiscard]] std::vector<std::byte>slice(unsigned address,unsigned bytes,unsigned permissions)const{
        require(address>=0x78000000&&bytes&&bytes<=65536&&std::uint64_t(address)+bytes<=0x100000000ULL,"Provider slice bounds");auto r=address-0x78000000;
        for(auto&s:sections_)if(r>=s.address&&std::uint64_t(r)+bytes<=std::uint64_t(s.address)+std::min(s.raw,s.virtual_bytes)){require((s.flags&0xe0000000)==permissions,"Provider source permission identity");auto p=offset(r,bytes);return {file_.begin()+p,file_.begin()+p+bytes};}throw std::invalid_argument("Provider complete source slice");
    }
};
}
