#pragma once
#include <array>
#include <cstdint>
#include <cstring>
namespace mw34::live_helper {
inline constexpr std::uint32_t version=1, root=0x409ed0, caller=0x405173;
inline constexpr std::uint32_t memory_base=0x20001000, memory_size=4096, virtual_frame=0x20001800, broker=0x10000100;
inline constexpr std::uint32_t arithmetic_mask=0x8d5, observed_mask=0xcd5;
inline constexpr char request_magic[8]={'M','W','H','L','P','R','0','1'};
inline constexpr char response_magic[8]={'M','W','H','L','P','A','0','1'};
#pragma pack(push,1)
struct Cpu {std::uint32_t eax,ecx,edx,ebx,esp,ebp,esi,edi,flags,eip;};
struct Request {
 char magic[8];std::uint32_t version,bytes,sequence,kind,pid,tid;
 Cpu cpu;std::array<std::uint8_t,512>fx;std::array<std::uint8_t,28>env;
 std::uint32_t n,caller,memory_seed;
};
struct Event {std::uint32_t address,value,width,write;};
struct Response {
 char magic[8];std::uint32_t version,bytes,sequence,status,worker_pid;
 Cpu cpu;std::array<std::uint8_t,512>fx;std::array<std::uint8_t,28>env;
 std::array<std::uint8_t,4096>memory;std::array<Event,2>events;
 std::uint32_t reads,returns,complete;char error[192];
};
#pragma pack(pop)
static_assert(sizeof(Cpu)==40 && sizeof(Request)==624 && sizeof(Response)==4940);
inline Request request(std::uint32_t sequence,std::uint32_t kind){Request r{};std::memcpy(r.magic,request_magic,8);r.version=version;r.bytes=sizeof(r);r.sequence=sequence;r.kind=kind;return r;}
inline Response response(std::uint32_t sequence){Response r{};std::memcpy(r.magic,response_magic,8);r.version=version;r.bytes=sizeof(r);r.sequence=sequence;return r;}
// Kind 0 handshake; kind 1 synthetic; kind 2 literal live game capture. Status
// 0 completed, 2 rejected, 3 execution failure. FP is opaque preserved transport:
// the admitted integer-only source neither observes nor modifies that state.
inline std::array<std::uint8_t,4096> initial_memory(const Request&r){
 std::array<std::uint8_t,4096>m{};
 for(std::uint32_t i=0;i<m.size();++i)m[i]=static_cast<std::uint8_t>(r.memory_seed+i*37U);
 const std::uint32_t ret=broker;std::memcpy(m.data()+virtual_frame-memory_base,&ret,4);
 std::memcpy(m.data()+virtual_frame-memory_base+4,&r.n,4);return m;
}
}
