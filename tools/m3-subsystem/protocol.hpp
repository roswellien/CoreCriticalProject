#pragma once
#include "../m3-slice/protocol.hpp"
#include <bit>
namespace mw34::m3_subsystem {
using mw34::m3_slice::Cpu;using mw34::m3_slice::Header;
using mw34::m3_slice::require;using mw34::m3_slice::read_record;using mw34::m3_slice::write_record;
using mw34::m3_slice::word;using mw34::m3_slice::file_bytes;using mw34::m3_slice::sha256;using mw34::m3_slice::admit_output;
using mw34::m3_slice::occupied_tag;
inline constexpr std::uint32_t setter=0x558290,consumer=0x55a560,sentinel=0x10000100;
inline constexpr std::uint32_t stack_base=0x20001000,global_base=0x72c000,buffer_base=0x20003000;
inline constexpr std::size_t page_size=4096,memory_size=16384,state_size=3504,max_steps=16,max_events=2048;
inline constexpr auto image_hash=mw34::m3_slice::image_hash;
inline constexpr auto setter_hash=mw34::m3_slice::code_hash;
inline constexpr const char *consumer_hash="072fed4d6b5efe0ff7c3bfa1733c848a11f3ba5402fd05d18c2f1ebf8ff57adf";
struct Step{Cpu state;std::uint32_t arg_a,arg_b;};
struct Request{std::uint32_t step_count,seed,full_tags,reserved;std::array<std::uint8_t,512> fx;std::array<Step,max_steps> steps;};
struct Event{std::uint32_t address,value,width,op;};
struct Result{
 Cpu cpu_before,cpu_after;std::uint32_t sequence_index,step_index,status,observation_mode,host_restored,trace_count;
 std::array<std::uint8_t,memory_size> memory_before,memory_after;
 std::array<std::uint8_t,512> fx_before,fx_after;std::array<std::uint8_t,28> env_before,env_after;
 std::array<std::uint8_t,state_size> state_before,state_after;std::array<Event,max_events> events;
};
static_assert(sizeof(Step)==48&&sizeof(Request)==1296&&sizeof(Event)==16&&sizeof(Result)==73728);
static_assert(offsetof(Request,fx)==16&&offsetof(Request,steps)==528);
static_assert(offsetof(Result,memory_before)==104&&offsetof(Result,memory_after)==16488);
static_assert(offsetof(Result,fx_before)==32872&&offsetof(Result,fx_after)==33384);
static_assert(offsetof(Result,env_before)==33896&&offsetof(Result,env_after)==33924);
static_assert(offsetof(Result,state_before)==33952&&offsetof(Result,state_after)==37456&&offsetof(Result,events)==40960);
inline void validate_step(const Step&s){
 const auto pc=s.state.eip,esp=s.state.registers[4];require(!(s.state.flags&~0xed7U)&&(s.state.flags&0x202U)==0x202U,"Unsafe entry flags");
 if(pc==setter)require(esp>=stack_base&&std::uint64_t{esp}+12<=stack_base+page_size,"Invalid setter frame");
 else if(pc==consumer){require(!s.arg_a&&!s.arg_b,"Consumer unused argument fields");require(esp>=stack_base+24&&std::uint64_t{esp}+4<=stack_base+page_size,"Invalid consumer frame");}
 else throw std::runtime_error("Unknown operation entry");
}
inline void validate_request(const Request&q){
 require(q.step_count>=1&&q.step_count<=max_steps&&!q.reserved,"Invalid sequence step count/reserved");
 auto fp=mw34::m3_slice::probe_request();fp.fx=q.fx;fp.full_tags=q.full_tags;mw34::m3_slice::validate_request(fp);
 for(unsigned i=q.step_count;i<max_steps;++i){const auto*p=reinterpret_cast<const std::uint8_t *>(&q.steps[i]);for(unsigned n=0;n<sizeof(Step);++n)require(!p[n],"Nonzero unused step slots");}
 // Pre-entry domain admission only: track setter configuration and prove every
 // future consumer word span/budget. Neither execution nor observations use
 // this configuration model; both execute the statically generated code.
 std::uint32_t source{},columns_word{},rows_word{},stride{};
 for(unsigned i=0;i<q.step_count;++i){const auto&s=q.steps[i];validate_step(s);
  if(s.state.eip==setter){source=s.state.registers[1];columns_word=s.state.registers[2];rows_word=s.arg_a;stride=static_cast<std::uint32_t>(std::bit_cast<std::int32_t>(s.arg_b)/2);continue;}
  const auto rows=std::bit_cast<std::int32_t>(rows_word)>>1,columns=std::bit_cast<std::int32_t>(columns_word)>>1;
  require(rows<=16&&(rows<=0||columns<=32),"Consumer work budget exceeded");
  auto source_row=source,dest_row=s.state.registers[1]?s.state.registers[1]:source;
  const auto dest_stride=s.state.registers[1]?s.state.registers[2]:stride;
  for(int row=0;row<rows;++row){for(int col=0;col<columns;++col){const auto a=source_row+4U*col,b=dest_row+2U*col;
    require(a>=buffer_base&&std::uint64_t{a}+2<=buffer_base+8192&&b>=buffer_base&&std::uint64_t{b}+2<=buffer_base+8192,"Consumer access outside isolated buffer block");}
   source_row+=2*stride;dest_row+=2*dest_stride;}
 }
}
inline std::vector<Request> read_requests(std::istream&in){auto h=read_record<Header>(in);require(!std::memcmp(h.magic,"MW34S3RQ",8)&&h.version==1&&h.count>=1&&h.count<=100000&&h.size==sizeof(Request)&&h.pointer_bits==32,"Invalid request header");std::vector<Request> q;q.reserve(h.count);for(unsigned i=0;i<h.count;++i){auto r=read_record<Request>(in);validate_request(r);q.push_back(r);}require(in.peek()==std::char_traits<char>::eof(),"Request length/trailing bytes");return q;}
inline Header output_header(std::uint32_t count,std::uint32_t bits){Header h{};std::memcpy(h.magic,"MW34S3RS",8);h.version=1;h.count=count;h.size=sizeof(Result);h.pointer_bits=bits;return h;}
inline std::uint32_t output_count(std::span<const Request> rows){std::uint32_t n{};for(auto&q:rows)n+=q.step_count;return n;}
inline std::array<std::uint8_t,memory_size> initial_memory(const Request&q){std::array<std::uint8_t,memory_size>b{};for(unsigned i=0;i<4096;++i)b[i]=static_cast<std::uint8_t>(i*37+q.seed);for(unsigned i=0;i<8192;++i)b[8192+i]=static_cast<std::uint8_t>(i*73+(q.seed>>8)+(i>>8)*19+0x5b);return b;}
inline std::array<std::vector<std::uint8_t>,2> admit_codes(const char*a,const char*b,const char*image){auto first=mw34::m3_slice::admit_code(a,image),second=file_bytes(b),whole=file_bytes(image);require(second.size()==119&&sha256(second)==consumer_hash,"Wrong complete consumer code identity");require(whole.size()>=0x159960+119&&!std::memcmp(whole.data()+0x159960,second.data(),119),"Consumer image offset binding failed");return{std::move(first),std::move(second)};}
inline std::array<std::uint8_t,28> seed_env(const Request&q){std::array<std::uint8_t,28>e{};const auto put=[&](unsigned o,std::uint32_t v){std::memcpy(e.data()+o,&v,4);};put(0,0xffff0000U|word<std::uint16_t>(q.fx.data()));put(4,0xffff0000U|word<std::uint16_t>(q.fx.data()+2));put(8,0xffff0000U|q.full_tags);put(12,word<std::uint32_t>(q.fx.data()+8));put(16,std::uint32_t{word<std::uint16_t>(q.fx.data()+6)}<<16);put(20,word<std::uint32_t>(q.fx.data()+16));put(24,0xffff0000);return e;}
inline Request probe_request(){Request q{};q.step_count=2;q.seed=0x3434;const auto f=mw34::m3_slice::probe_request();q.fx=f.fx;q.full_tags=f.full_tags;q.steps[0].state=f.state;q.steps[0].state.registers[1]=buffer_base+32;q.steps[0].state.registers[2]=4;q.steps[0].arg_a=4;q.steps[0].arg_b=16;q.steps[1].state=f.state;q.steps[1].state.eip=consumer;q.steps[1].state.registers[1]=buffer_base+1024;q.steps[1].state.registers[2]=16;validate_request(q);return q;}
inline unsigned protocol_controls(){unsigned checks{};auto q=probe_request();validate_request(q);++checks;auto reject=[&](auto fn){try{fn();}catch(const std::exception&){++checks;return;}throw std::runtime_error("Invalid sequence control admitted");};
 reject([&]{auto r=q;r.step_count=0;validate_request(r);});reject([&]{auto r=q;r.step_count=17;validate_request(r);});reject([&]{auto r=q;r.reserved=1;validate_request(r);});reject([&]{auto r=q;r.steps[2].arg_a=1;validate_request(r);});
 reject([&]{auto r=q;r.steps[1].state.eip++;validate_request(r);});reject([&]{auto r=q;r.steps[1].arg_b=1;validate_request(r);});reject([&]{auto r=q;r.steps[1].state.registers[4]=stack_base+23;validate_request(r);});
 reject([&]{auto r=q;r.steps[0].arg_a=34;validate_request(r);});reject([&]{auto r=q;r.steps[0].state.registers[2]=66;validate_request(r);});reject([&]{auto r=q;r.steps[0].state.registers[1]=0xfffffffe;validate_request(r);});
 reject([&]{auto r=q;r.steps[1].state.registers[1]=buffer_base+8191;validate_request(r);});reject([&]{auto r=q;r.fx[5]=1;validate_request(r);});reject([&]{auto r=q;r.full_tags^=1;validate_request(r);});
 reject([&]{auto r=q;r.fx[6]=1;validate_request(r);});reject([&]{auto r=q;r.fx[8]=1;validate_request(r);});reject([&]{auto r=q;r.fx[16]=1;validate_request(r);});
 {auto r=q;r.steps[0].arg_a=0;r.steps[0].state.registers[1]=0xffffffff;r.steps[1].state.registers[1]=0xffffffff;validate_request(r);++checks;}
 return checks;
}
}
