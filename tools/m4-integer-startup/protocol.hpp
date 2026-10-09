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

namespace mw34::m4_integer_startup {
inline constexpr std::uint32_t entry = 0x43aec0;
inline constexpr std::uint32_t sentinel = 0x10000100, stack_base = 0x20001000;
inline constexpr std::uint32_t global_base = 0x605000, second_global_base = 0x60b000;
inline constexpr std::uint32_t input_flags = 0xcd5, defined_flags = 0xcd5;
inline constexpr std::size_t page_size = 4096, memory_size = 12288, state_size = 3504;
inline constexpr const char *image_hash = "95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf";
inline constexpr const char *code_hash = "8091fc698f5d5fc75afc1fc3f4926c9f98f2cbce614b5a667889320be799bd31";
inline constexpr std::array<std::uint32_t,14> entries{0x43aec0,0x43aee0,0x43af00,0x43af20,0x43af40,0x43af60,0x43af80,0x43afa0,0x467490,0x4674b0,0x4674d0,0x4b5b20,0x4c7940,0x4cfef0};
struct Fragment {std::uint32_t entry,size,offset,bundle;};
inline constexpr std::array<Fragment,15> fragments{{{4435648,26,238272,0},{4435680,26,238304,26},{4435712,26,238336,52},{4435744,26,238368,78},{4435776,26,238400,104},{4435808,26,238432,130},{4435840,26,238464,156},{4435872,26,238496,182},{4617360,17,419984,208},{4617392,17,420016,225},{4617424,17,420048,242},{4938528,49,741152,259},{5011776,27,814400,308},{5046000,29,848624,335},{4435504,25,238128,364}}};
struct Cpu { std::uint32_t registers[8], flags, eip; };
struct Request {
    Cpu state;
    std::uint32_t arg_a, arg_b, seed, full_tags;
    std::array<std::uint8_t, 512> fx;
};
struct Event {std::uint32_t address,value,width,operation;};
inline constexpr unsigned max_events=8;
struct Route { Cpu before, after; std::uint32_t entry_pc,return_pc,pop_bytes,complete; };
struct Result {
    Cpu cpu_before, cpu_after;
    std::uint32_t status, observation_mode, host_restored;
    std::array<std::uint8_t, memory_size> memory_before, memory_after;
    std::array<std::uint8_t, 512> fx_before, fx_after;
    std::array<std::uint8_t, 28> env_before, env_after;
    std::array<std::uint8_t, state_size> state_before, state_after;
    std::uint32_t trace_count;
    std::array<Event,max_events> events;
    std::uint32_t route_count;
    std::array<Route,1> routes;
};
struct Header { char magic[8]; std::uint32_t version, count, size, pointer_bits; };
static_assert(sizeof(Cpu)==40 && sizeof(Request)==568 && sizeof(Result)==32988 && sizeof(Header)==24);
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
    require(q.arg_a<entries.size() && q.arg_b<=1,"Invalid integer root/sequence mode");
    require(q.state.eip==entries[q.arg_a],"Wrong integer entry PC");
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
    require(in.peek()==std::char_traits<char>::eof(),"Trailing M4 input");
    for(std::size_t i=0;i<rows.size();++i)if(rows[i].arg_b){
        require(rows[i].arg_a==0&&i+14<=rows.size(),"Incomplete persistent integer batch");const auto &base=rows[i];
        for(unsigned j=0;j<14;++j){const auto &q=rows[i+j];require(q.arg_b==1&&q.arg_a==j&&q.seed==base.seed&&q.full_tags==base.full_tags&&q.fx==base.fx&&std::memcmp(&q.state,&base.state,36)==0,"Persistent batch request domain changed");}i+=13;
    }
    return rows;
}
inline std::array<std::uint8_t,memory_size> initial_memory(const Request &q) {
    validate_request(q);std::array<std::uint8_t,memory_size> bytes{};
    for(unsigned i=0;i<page_size;++i) bytes[i]=static_cast<std::uint8_t>(i*37+q.seed);
    for(unsigned p=1;p<3;++p)for(unsigned i=0;i<page_size;++i)bytes[p*page_size+i]=static_cast<std::uint8_t>(i*73+(q.seed>>8)+(i>>8)*19+0x5b+p*11);
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
    require(code.size()==389&&sha256(code)==code_hash,"Wrong complete M4 code identity");
    require(sha256(image)==image_hash,"Wrong M4 image identity");
    for(const auto &f:fragments)require(image.size()>=f.offset+f.size&&std::memcmp(image.data()+f.offset,code.data()+f.bundle,f.size)==0,"Integer code/image offset binding failed");
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
    unsigned checks{};auto reject=[&](auto f){try{f();}catch(const std::exception &){++checks;return;}throw std::runtime_error("Protocol invalid control admitted");};
    auto q=probe_request();for(unsigned i=0;i<14;++i){q.arg_a=i;q.state.eip=entries[i];validate_request(q);++checks;}
    q=probe_request();reject([&]{auto x=q;x.arg_a=14;validate_request(x);});reject([&]{auto x=q;x.arg_b=2;validate_request(x);});reject([&]{auto x=q;x.state.eip++;validate_request(x);});
    for(auto sp:{stack_base-1,stack_base+4093,0xffffffffU})reject([&]{auto x=q;x.state.registers[4]=sp;validate_request(x);});
    reject([&]{auto x=q;x.fx[0]&=0xfe;validate_request(x);});reject([&]{auto x=q;x.fx[5]=1;validate_request(x);});
    reject([&]{auto x=q;x.fx[6]=1;validate_request(x);});reject([&]{auto x=q;x.state.flags|=0x3000;validate_request(x);});
    require(sha256(std::span<const std::uint8_t>{})=="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","SHA known answer differs");++checks;
    return checks;
}
} // namespace mw34::m4_integer_startup
