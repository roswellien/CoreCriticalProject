// Connected hardware-only observations. No expected-value execution is present.
#pragma once
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <bcrypt.h>
#include <array>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace mw34::m4_numeric_max {
inline constexpr std::uint32_t frame=0x20001800, returned_esp=frame+4;
inline constexpr std::uint32_t capture_pc=0x10000100;
inline constexpr unsigned sequences=432, roots=2, phase_count=sequences*roots;
inline constexpr unsigned page_size=4096, observed_page_count=4;
inline constexpr std::size_t memory_size=page_size*observed_page_count;
inline constexpr const char image_sha[]="95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf";
inline constexpr std::array<std::uint16_t,12> control_words{
    0x007f,0x047f,0x087f,0x0c7f,0x027f,0x067f,0x0a7f,0x0e7f,0x037f,0x077f,0x0b7f,0x0f7f};
inline constexpr std::array<std::uint32_t,4> observed_pages{0x5bb000,0x78115000,0x60b000,0x20001000};
struct Cpu {std::uint32_t eax,ecx,edx,ebx,esp,ebp,esi,edi,flags,pc;};
#pragma pack(push,1)
struct Header {char magic[8];std::uint32_t version,count,stride,pages;};
struct Tag {std::uint32_t repeat,input,entry,cw,top,depth,sticky,status,host_restored,checkpoint_seen;};
struct Record {
 Tag tag;Cpu before,after;
 std::array<std::uint8_t,512> guest_fx_before,guest_fx_after,host_fx_before,host_fx_after;
 std::array<std::uint8_t,28> guest_env_before,guest_env_after,host_env_before,host_env_after;
 std::array<std::uint8_t,memory_size> memory_before,memory_after;
 std::array<std::uint8_t,716> checkpoint_context;
};
#pragma pack(pop)
static_assert(sizeof(Cpu)==40 && sizeof(Header)==24 && sizeof(Tag)==40 && sizeof(Record)==35764);
inline void require(bool value,const char*reason){if(!value)throw std::runtime_error(reason);}
template<class T> inline T word(const std::uint8_t*p){T result{};std::memcpy(&result,p,sizeof(result));return result;}
inline std::string sha256(const std::vector<std::uint8_t>&bytes){
    BCRYPT_ALG_HANDLE algorithm{};BCRYPT_HASH_HANDLE hash{};
    require(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)==0,"SHA provider failed");
    struct Close {BCRYPT_ALG_HANDLE a;BCRYPT_HASH_HANDLE &h;~Close(){if(h)BCryptDestroyHash(h);BCryptCloseAlgorithmProvider(a,0);}} close{algorithm,hash};
    require(BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0)==0,"SHA object failed");
    require(bytes.size()<=0xffffffffULL&&BCryptHashData(hash,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0)==0,"SHA update failed");
    std::uint8_t result[32]{};require(BCryptFinishHash(hash,result,32,0)==0,"SHA final failed");
    std::ostringstream out;out<<std::hex<<std::setfill('0');for(auto value:result)out<<std::setw(2)<<unsigned(value);return out.str();
}
inline std::vector<std::uint8_t> read(const char*path,std::size_t maximum){
    std::ifstream file(path,std::ios::binary|std::ios::ate);require(bool(file),"Input unavailable");
    const auto size=file.tellg();require(size>=0&&static_cast<std::uint64_t>(size)<=maximum,"Input extent rejected");
    std::vector<std::uint8_t> result(static_cast<std::size_t>(size));file.seekg(0);
    file.read(reinterpret_cast<char*>(result.data()),static_cast<std::streamsize>(result.size()));require(bool(file),"Input read failed");return result;
}
struct Output {
    std::filesystem::path destination,stage;HANDLE handle{INVALID_HANDLE_VALUE};bool owns{};
    explicit Output(const char *path):destination(path),stage(destination.string()+".numeric-stage-"+std::to_string(GetCurrentProcessId())){
        const auto attributes=GetFileAttributesW(destination.c_str());
        require(attributes==INVALID_FILE_ATTRIBUTES&&GetLastError()==ERROR_FILE_NOT_FOUND,"Output exists or cannot establish absence");
        handle=CreateFileW(stage.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
        require(handle!=INVALID_HANDLE_VALUE,"Cannot own fresh staging file");owns=true;
    }
    ~Output(){if(handle!=INVALID_HANDLE_VALUE)CloseHandle(handle);if(owns)DeleteFileW(stage.c_str());}
    void write(const void*data,std::size_t size){DWORD written{};require(size<=0xffffffffULL&&WriteFile(handle,data,static_cast<DWORD>(size),&written,nullptr)&&written==size,"Output write failed");}
    template<class T> void write(const T&value){write(&value,sizeof(value));}
    void commit(){require(FlushFileBuffers(handle),"Output flush failed");require(CloseHandle(handle),"Output close failed");handle=INVALID_HANDLE_VALUE;
        require(MoveFileExW(stage.c_str(),destination.c_str(),MOVEFILE_WRITE_THROUGH),"Output commit failed");owns=false;}
};
inline bool host_restored(const Record&r){
    bool result=std::memcmp(r.host_fx_before.data(),r.host_fx_after.data(),5)==0&&
        std::memcmp(r.host_fx_before.data()+24,r.host_fx_after.data()+24,4)==0&&r.host_env_before==r.host_env_after;
    for(unsigned i=0;i<8;++i)result&=std::memcmp(r.host_fx_before.data()+32+i*16,r.host_fx_after.data()+32+i*16,10)==0;
    return result&&std::memcmp(r.host_fx_before.data()+160,r.host_fx_after.data()+160,128)==0;
}
inline unsigned protocol_controls(){
    require(sha256({})=="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","Empty SHA KAT failed");
    require(sha256({'a','b','c'})=="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad","ABC SHA KAT failed");
    require(frame+4==returned_esp&&capture_pc==0x10000100&&memory_size==16384,"Mixed framing constants differ");
    return 3;
}
inline void publication_controls(const char*directory){
    const std::filesystem::path root(directory);
    require(!std::filesystem::exists(root)&&std::filesystem::create_directory(root),"Fresh publication control directory required");
    const std::vector<std::uint8_t> sentinel{0x4d,0x57,0x33,0x34,0,0xff,0x80,0x42};
    for(unsigned mode=0;mode<2;++mode){
        const auto destination=root/(mode?"existing-stage.bin":"existing-output.bin");
        const auto stage=std::filesystem::path(destination.string()+".numeric-stage-"+std::to_string(GetCurrentProcessId()));
        const auto fixture=mode?stage:destination;
        {std::ofstream out(fixture,std::ios::binary);out.write(reinterpret_cast<const char*>(sentinel.data()),sentinel.size());require(bool(out),"Sentinel write failed");}
        bool rejected{};try{Output out(destination.string().c_str());}catch(const std::exception&){rejected=true;}
        require(rejected&&read(fixture.string().c_str(),sentinel.size())==sentinel&&!std::filesystem::exists(mode?destination:stage),"Pre-existing publication evidence lost");
    }
    std::cout<<"2 actual publisher admission controls passed\n";
}
} // namespace mw34::m4_numeric_max
