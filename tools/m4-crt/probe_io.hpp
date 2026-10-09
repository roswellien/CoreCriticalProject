#pragma once
#include <windows.h>
#include <bcrypt.h>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <span>
#include "probe_common.hpp"
namespace mw34::m4_crt_probe {
inline std::string digest(std::span<const std::uint8_t> bytes){
 BCRYPT_ALG_HANDLE a{};BCRYPT_HASH_HANDLE h{};need(BCryptOpenAlgorithmProvider(&a,BCRYPT_SHA256_ALGORITHM,nullptr,0)==0,"SHA provider failed");
 struct Close {BCRYPT_ALG_HANDLE a;BCRYPT_HASH_HANDLE &h;~Close(){if(h)BCryptDestroyHash(h);BCryptCloseAlgorithmProvider(a,0);}} close{a,h};
 need(BCryptCreateHash(a,&h,nullptr,0,nullptr,0,0)==0,"SHA object failed");need(bytes.size()<=0xffffffffULL&&BCryptHashData(h,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0)==0,"SHA update failed");
 std::uint8_t result[32]{};need(BCryptFinishHash(h,result,32,0)==0,"SHA final failed");std::ostringstream out;out<<std::hex<<std::setfill('0');for(auto v:result)out<<std::setw(2)<<unsigned(v);return out.str();
}
inline std::vector<std::uint8_t> read(const char*path,std::size_t maximum){
 std::ifstream f(path,std::ios::binary|std::ios::ate);need(bool(f),"Input unavailable");auto n=f.tellg();need(n>=0&&static_cast<std::uint64_t>(n)<=maximum,"Input extent rejected");std::vector<std::uint8_t>b(static_cast<std::size_t>(n));f.seekg(0);f.read(reinterpret_cast<char*>(b.data()),static_cast<std::streamsize>(b.size()));need(bool(f),"Input read failed");return b;
}
struct Output {
 std::filesystem::path destination,stage;HANDLE handle{INVALID_HANDLE_VALUE};bool owns{};
 explicit Output(const char*path):destination(path),stage(destination.string()+".crt-stage-"+std::to_string(GetCurrentProcessId())){
  const auto attributes=GetFileAttributesW(destination.c_str());need(attributes==INVALID_FILE_ATTRIBUTES&&GetLastError()==ERROR_FILE_NOT_FOUND,"Output exists or cannot establish absence");
  handle=CreateFileW(stage.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);need(handle!=INVALID_HANDLE_VALUE,"Cannot own fresh staging file");owns=true;
 }
 ~Output(){if(handle!=INVALID_HANDLE_VALUE)CloseHandle(handle);if(owns)DeleteFileW(stage.c_str());}
 void write(const void *data,std::size_t n){DWORD count{};need(n<=0xffffffffULL&&WriteFile(handle,data,static_cast<DWORD>(n),&count,nullptr)&&count==n,"Output write failed");}
 void commit(){need(FlushFileBuffers(handle),"Output flush failed");need(CloseHandle(handle),"Output close failed");handle=INVALID_HANDLE_VALUE;need(MoveFileExW(stage.c_str(),destination.c_str(),MOVEFILE_WRITE_THROUGH),"Output commit failed");owns=false;}
};
inline void hash_controls(){need(digest({})=="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","Empty SHA control failed");const std::array<std::uint8_t,3> abc{'a','b','c'};need(digest(abc)=="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad","ABC SHA control failed");}
} // namespace mw34::m4_crt_probe
