#pragma once
#include <array>
#include <cstdint>
#include <cstring>
namespace mw34::live_numeric {
inline constexpr std::uint32_t version=1, root=0x4c19f0, body=0x4c1a00, slot=0x5bb4fc, output=0x60b368;
inline constexpr std::uint32_t table_slot=0x5e016c, provider_base=0x780c0000, leaf=0x780c10f0;
inline constexpr std::uint32_t virtual_frame=0x20001800, broker=0x410a80;
inline constexpr char request_magic[8]={'M','W','N','M','X','R','0','1'};
inline constexpr char response_magic[8]={'M','W','N','M','X','A','0','1'};
#pragma pack(push,1)
struct Cpu {std::uint32_t eax,ecx,edx,ebx,esp,ebp,esi,edi,flags,eip;};
struct Request {
 char magic[8];std::uint32_t version,bytes,sequence,kind,pid,tid;
 Cpu cpu;std::array<std::uint8_t,512>fx;std::array<std::uint8_t,28>env;std::array<std::uint8_t,44>globals;
 std::uint32_t cs,ds,ss,fs_base,provider_base,provider_bits,iat_target,caller;
};
struct Event {std::uint32_t pc,address,value,width,write;};
struct Response {
 char magic[8];std::uint32_t version,bytes,sequence,status,worker_pid;
 Cpu cpu;std::array<std::uint8_t,512>fx;std::array<std::uint8_t,28>env;std::array<std::uint8_t,44>globals;
 std::array<Event,22>events;std::array<std::uint32_t,15>routes;std::uint32_t steps,complete;
 char error[192];
};
#pragma pack(pop)
static_assert(sizeof(Cpu)==40 && sizeof(Event)==20);
inline Request request(std::uint32_t sequence,std::uint32_t kind){Request r{};std::memcpy(r.magic,request_magic,8);r.version=version;r.bytes=sizeof(r);r.sequence=sequence;r.kind=kind;return r;}
inline Response response(std::uint32_t sequence){Response r{};std::memcpy(r.magic,response_magic,8);r.version=version;r.bytes=sizeof(r);r.sequence=sequence;return r;}
// kind 0: transport handshake, 1: synthetic preflight, 2: actual game callback.
// status 0: generated x64 execution completed, 2: rejected input, 3: execution failure.
// Only kind 2, status 0, verified original comparison, and native publication grant live credit.
}
