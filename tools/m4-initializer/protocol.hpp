// Exact private-image M4 startup initializer harness. No proprietary instruction bytes here.
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
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <sstream>
#include <span>
#include <stdexcept>
#include <string>
#include <vector>

namespace mw34::m4_initializer {
inline constexpr std::uint32_t entry = 0x410910, code_page = 0x410000;
inline constexpr std::uint32_t sentinel = 0x10000100, stack_base = 0x20001000;
inline constexpr std::uint32_t global_base = 0x604000, global_first = 0x604130;
inline constexpr std::uint32_t input_flags = 0xcd5, defined_flags = 0xcd5;
inline constexpr std::size_t page_size = 4096, memory_size = 8192, state_size = 3504;
inline constexpr const char *image_hash = "95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf";
inline constexpr const char *code_hash = "f5a91456f4eb0ecab7e5cd689b1d1465dc4e2610bc879397e500b02d00946af7";
struct Cpu { std::uint32_t registers[8], flags, eip; };
struct Request {
    Cpu state;
    std::uint32_t arg_a, arg_b, seed, full_tags;
    std::array<std::uint8_t, 512> fx;
};
struct Event {std::uint32_t address,value,width,operation;};
inline constexpr unsigned max_events=168;
struct Result {
    Cpu cpu_before, cpu_after;
    std::uint32_t status, observation_mode, host_restored;
    std::array<std::uint8_t, memory_size> memory_before, memory_after;
    std::array<std::uint8_t, 512> fx_before, fx_after;
    std::array<std::uint8_t, 28> env_before, env_after;
    std::array<std::uint8_t, state_size> state_before, state_after;
    std::uint32_t trace_count;
    std::array<Event,max_events> events;
};
struct Header { char magic[8]; std::uint32_t version, count, size, pointer_bits; };
static_assert(sizeof(Cpu)==40 && sizeof(Request)==568 && sizeof(Result)==27256 && sizeof(Header)==24);
static_assert(offsetof(Request,arg_a)==40 && offsetof(Request,arg_b)==44 && offsetof(Request,seed)==48);
static_assert(offsetof(Request,full_tags)==52 && offsetof(Request,fx)==56);
static_assert(offsetof(Result,cpu_after)==40 && offsetof(Result,status)==80 && offsetof(Result,observation_mode)==84);
static_assert(offsetof(Result,host_restored)==88 && offsetof(Result,memory_before)==92 && offsetof(Result,memory_after)==8284);
static_assert(offsetof(Result,fx_before)==16476 && offsetof(Result,fx_after)==16988);
static_assert(offsetof(Result,env_before)==17500 && offsetof(Result,env_after)==17528);
static_assert(offsetof(Result,state_before)==17556 && offsetof(Result,state_after)==21060);

inline void require(bool ok,const char *reason) { if (!ok) throw std::runtime_error(reason); }
template<class T> inline T read_record(std::istream &in) {
    T value{}; require(bool(in.read(reinterpret_cast<char *>(&value),sizeof(value))),"Truncated M4 input"); return value;
}
template<class T> inline void write_record(std::ostream &out,const T &value) {
    require(bool(out.write(reinterpret_cast<const char *>(&value),sizeof(value))),"M4 output failed");
}
template<class T> inline T word(const std::uint8_t *bytes) { T v{}; std::memcpy(&v,bytes,sizeof(v)); return v; }
inline bool legal_cw(std::uint16_t cw) {
    for (unsigned pc:{0U,2U,3U}) for(unsigned rc=0;rc<4;++rc)
        if(cw==(0x7fU|(pc<<8)|(rc<<10))) return true;
    return false;
}
inline unsigned occupied_tag(const std::uint8_t *raw) {
    const auto sig=word<std::uint64_t>(raw);
    const auto exp=word<std::uint16_t>(raw+8)&0x7fff;
    if(!exp && !sig) return 1;
    if(exp && exp!=0x7fff && (sig>>63)) return 0;
    if(exp==0x7fff && (sig>>63) && (sig==0x8000000000000000ULL || (sig&(1ULL<<62)))) return 2;
    throw std::runtime_error("Unsupported occupied raw80 encoding");
}
inline void validate_request(const Request &q) {
    require(!q.arg_a&&!q.arg_b,"Unused M4 arguments must be zero");
    require(q.state.eip==entry,"Wrong M4 entry PC");
    const auto esp=q.state.registers[4];
    require(esp>=stack_base && std::uint64_t{esp}+4<=std::uint64_t{stack_base}+page_size,"Unsafe M4 stack frame span");
    require(!(q.state.flags&~(input_flags|0x202U)) && (q.state.flags&0x202U)==0x202U,"Unsafe M4 entry flags");
    require(q.full_tags<=0xffff,"Invalid full physical tags");
    const auto cw=word<std::uint16_t>(q.fx.data()), sw=word<std::uint16_t>(q.fx.data()+2);
    require(legal_cw(cw),"Unsupported masked M4 control word");
    require(!(sw&~0x7f7fU),"Unsupported M4 status word");
    require(!(word<std::uint16_t>(q.fx.data()+6)&~0x7ffU),"Invalid guest FOP metadata");
    require(word<std::uint16_t>(q.fx.data()+6)==0&&word<std::uint32_t>(q.fx.data()+8)==0&&word<std::uint32_t>(q.fx.data()+16)==0,
            "Unsupported nonzero guest instruction metadata");
    require(word<std::uint32_t>(q.fx.data()+24)==0x1f80 && word<std::uint32_t>(q.fx.data()+28)==0,"Unsupported guest MXCSR input");
    const unsigned top=(sw>>11)&7,ftw=q.fx[4];
    for(unsigned i=0;i<8;++i) {
        const unsigned physical=(top+i)&7;
        const unsigned tag=(ftw&(1U<<physical))?occupied_tag(q.fx.data()+32+i*16):3;
        require(((q.full_tags>>(physical*2))&3U)==tag,"Incoherent M4 physical FTW/full tags");
    }
    for(unsigned i=0;i<512;++i) {
        const bool allowed=(i<5)||(i>=6&&i<12)||(i>=16&&i<20)||(i>=24&&i<32)||
                           (i>=32&&i<160&&((i-32)%16)<10)||(i>=160&&i<288);
        require(allowed || q.fx[i]==0,"Nonzero reserved/selectors in M4 FX input");
    }
}
inline Header input_header(std::istream &in) {
    auto h=read_record<Header>(in);
    require(!std::memcmp(h.magic,"MW34I4RQ",8)&&h.version==1&&h.count>=1&&h.count<=100000&&h.size==sizeof(Request)&&h.pointer_bits==32,"Invalid M4 request header");
    return h;
}
inline Header output_header(std::uint32_t count,std::uint32_t bits=sizeof(void *)*8) {
    require(count>=1&&count<=100000&&(bits==32||bits==64),"Invalid M4 output count/width");
    Header h{};std::memcpy(h.magic,"MW34I4RS",8);h.version=1;h.count=count;h.size=sizeof(Result);h.pointer_bits=bits;return h;
}
inline std::vector<Request> read_requests(std::istream &in) {
    auto h=input_header(in);std::vector<Request> rows;rows.reserve(h.count);
    for(std::uint32_t i=0;i<h.count;++i) { auto q=read_record<Request>(in);validate_request(q);rows.push_back(q); }
    require(in.peek()==std::char_traits<char>::eof(),"Trailing M4 input");return rows;
}
inline std::array<std::uint8_t,memory_size> initial_memory(const Request &q) {
    validate_request(q);std::array<std::uint8_t,memory_size> bytes{};
    for(unsigned i=0;i<page_size;++i) bytes[i]=static_cast<std::uint8_t>(i*37+q.seed);
    for(unsigned i=0;i<page_size;++i)bytes[page_size+i]=static_cast<std::uint8_t>(i*73+(q.seed>>8)+(i>>8)*19+0x5b);
    const std::uint32_t frame[]{sentinel};
    std::memcpy(bytes.data()+q.state.registers[4]-stack_base,frame,4);
    return bytes; // Authored nonzero data seeding observes untouched record padding.
}
inline std::vector<std::uint8_t> file_bytes(const char *path) {
    std::ifstream in(path,std::ios::binary);require(bool(in),"Missing M4 private input");
    return std::vector<std::uint8_t>((std::istreambuf_iterator<char>(in)),{});
}
inline std::string sha256(std::span<const std::uint8_t> bytes) {
    BCRYPT_ALG_HANDLE alg{};BCRYPT_HASH_HANDLE hash{};
    require(BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0,"SHA256 provider failed");
    struct Close { BCRYPT_ALG_HANDLE a;BCRYPT_HASH_HANDLE *h;~Close(){if(*h)BCryptDestroyHash(*h);BCryptCloseAlgorithmProvider(a,0);} } close{alg,&hash};
    // Windows 7+ allocates the object with the hash handle when nullptr/0 is
    // supplied. BCryptDestroyHash frees it before the provider is closed.
    // No caller-owned object buffer can outlive or precede this handle.
    std::array<std::uint8_t,32> digest{};
    require(BCryptCreateHash(alg,&hash,nullptr,0,nullptr,0,0)>=0,"SHA256 create failed");
    require(bytes.size()<=0xffffffffULL&&BCryptHashData(hash,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0)>=0&&BCryptFinishHash(hash,digest.data(),32,0)>=0,"SHA256 digest failed");
    constexpr char hex[]="0123456789abcdef";std::string result;result.reserve(64);
    for(auto b:digest){result+=hex[b>>4];result+=hex[b&15];}return result;
}
inline std::vector<std::uint8_t> admit_code(const char *slice_path,const char *image_path) {
    auto code=file_bytes(slice_path),image=file_bytes(image_path);
    require(code.size()==36&&sha256(code)==code_hash,"Wrong complete M4 code identity");
    require(sha256(image)==image_hash,"Wrong M4 image identity");
    require(image.size()>=0xfd10+36&&std::memcmp(image.data()+0xfd10,code.data(),36)==0,"M4 code/image offset binding failed");
    return code;
}
inline void admit_output(const char *path) {
    require(!std::filesystem::exists(path),"M4 output already exists; frozen evidence cannot be replaced");
}
inline Request probe_request(unsigned pc=3,unsigned rc=0,unsigned top=0,unsigned ftw=255) {
    Request q{};q.state.eip=entry;q.state.flags=0x202;q.state.registers[4]=stack_base+1024;
    const std::uint16_t cw=static_cast<std::uint16_t>(0x7f|(pc<<8)|(rc<<10)),sw=static_cast<std::uint16_t>(top<<11);
    std::memcpy(q.fx.data(),&cw,2);std::memcpy(q.fx.data()+2,&sw,2);q.fx[4]=static_cast<std::uint8_t>(ftw);
    const std::uint32_t mxcsr=0x1f80;std::memcpy(q.fx.data()+24,&mxcsr,4);
    for(unsigned i=0;i<8;++i) {
        const std::uint64_t sig=0x8000000000000001ULL+i*2;const std::uint16_t exp=0x3fff;
        std::memcpy(q.fx.data()+32+i*16,&sig,8);std::memcpy(q.fx.data()+40+i*16,&exp,2);
        const unsigned physical=(top+i)&7;q.full_tags|=((ftw&(1U<<physical))?0U:3U)<<(physical*2);
    }
    for(unsigned i=0;i<128;++i)q.fx[160+i]=static_cast<std::uint8_t>(i*17+3);
    validate_request(q);return q;
}
inline unsigned protocol_controls() {
    unsigned checks{};
    require(sha256(std::span<const std::uint8_t>{})=="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","Empty SHA256 known answer differs");++checks;
    const std::array<std::uint8_t,3> abc{'a','b','c'};
    require(sha256(abc)=="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad","ABC SHA256 known answer differs");++checks;
    auto reject=[&](auto f){try{f();}catch(const std::exception &){++checks;return;}throw std::runtime_error("Protocol control admitted invalid request");};
    auto q=probe_request();validate_request(q);++checks;
    for(auto sp:std::array<std::uint32_t,5>{stack_base,stack_base+1,stack_base+2,stack_base+3,stack_base+4092}) {q.state.registers[4]=sp;validate_request(q);++checks;}
    q=probe_request();
    reject([&]{auto x=q;x.arg_a=1;validate_request(x);});
    reject([&]{auto x=q;x.arg_b=1;validate_request(x);});
    reject([&]{auto x=q;x.state.eip++;validate_request(x);});
    reject([&]{auto x=q;x.state.registers[4]=0xfffffff8;validate_request(x);});
    reject([&]{auto x=q;x.state.registers[4]=stack_base+4093;validate_request(x);});
    reject([&]{auto x=q;x.state.flags|=0x3000;validate_request(x);});
    reject([&]{auto x=q;x.state.flags&=~0x200U;validate_request(x);});
    reject([&]{auto x=q;x.fx[0]&=0xfe;validate_request(x);});
    reject([&]{auto x=q;x.fx[3]|=0x80;validate_request(x);});
    reject([&]{auto x=q;x.fx[5]=1;validate_request(x);});
    reject([&]{auto x=q;x.full_tags=0x10000;validate_request(x);});
    reject([&]{auto x=q;x.full_tags^=1;validate_request(x);});
    reject([&]{auto x=q;x.fx[32]=0;x.fx[39]=0;validate_request(x);});
    reject([&]{auto x=q;x.fx[12]=1;validate_request(x);});
    reject([&]{auto x=q;x.fx[24]=0;validate_request(x);});
    reject([&]{auto x=q;x.fx[6]=1;validate_request(x);});
    reject([&]{auto x=q;x.fx[8]=1;validate_request(x);});
    reject([&]{auto x=q;x.fx[16]=1;validate_request(x);});
    auto stream=[&](Request last,bool trailing=false){std::ostringstream out(std::ios::binary);Header h{};std::memcpy(h.magic,"MW34I4RQ",8);h.version=1;h.count=2;h.size=sizeof(Request);h.pointer_bits=32;write_record(out,h);write_record(out,q);write_record(out,last);if(trailing)out.put('x');return out.str();};
    {std::istringstream in(stream(q),std::ios::binary);require(read_requests(in).size()==2,"Valid whole corpus rejected");++checks;}
    reject([&]{auto last=q;last.fx[5]=1;std::istringstream in(stream(last),std::ios::binary);read_requests(in);});
    reject([&]{std::istringstream in(stream(q,true),std::ios::binary);read_requests(in);});
    reject([&]{auto bytes=stream(q);bytes.pop_back();std::istringstream in(bytes,std::ios::binary);read_requests(in);});
    reject([&]{auto bytes=stream(q);bytes[0]='X';std::istringstream in(bytes,std::ios::binary);read_requests(in);});
    reject([&]{auto bytes=stream(q);bytes[20]=64;std::istringstream in(bytes,std::ios::binary);read_requests(in);});
    return checks;
}
} // namespace mw34::m4_initializer
