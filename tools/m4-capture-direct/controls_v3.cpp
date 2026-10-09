#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include "capture_direct_v3.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
namespace cd=mw34::capture_direct;
namespace fs=std::filesystem;
struct alignas(16) Capture {std::array<unsigned char,512> fx{};std::array<unsigned char,28> env{};std::array<unsigned char,4> pad{};std::uint64_t flags=0;};
static_assert(offsetof(Capture,env)==512&&offsetof(Capture,flags)==544&&sizeof(Capture)==560);
struct Context {cd::Writer* writer=nullptr;unsigned operation=0;bool threw=false;DWORD error_before=0,error_after=0;std::string_view name;const void* data=nullptr;std::size_t size=0;const cd::Receipt* receipt=nullptr;std::unique_ptr<cd::Writer>* owner=nullptr;const fs::path* target=nullptr;const cd::Options* options=nullptr;};
extern "C" void mw34_capture_test_boundary(Context*,Capture*,Capture*,const Capture*);
extern "C" void mw34_capture_test_operation(Context* c) noexcept{c->error_before=GetLastError();if(c->operation==0)c->threw=!c->writer->try_append(c->name,c->data,c->size);else if(c->operation==1)c->threw=!c->writer->try_close_batch();else if(c->operation==2){c->receipt=c->writer->try_finish();c->threw=c->receipt==nullptr;}else if(c->operation==3){*c->owner=cd::Writer::try_create(*c->target,*c->options);c->threw=!*c->owner;}else c->owner->reset();c->error_after=GetLastError();}
unsigned checks=0,hardware_pairs=0,refusals=0;
void need(bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);}
void save(Capture& c){__asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfldenv %1":"=m"(c.fx),"=m"(c.env)::"memory");}
void restore(const Capture& c){__asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(c.fx),"m"(c.env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
Capture seed(){Capture host{},r{};save(host);unsigned mxcsr=0x5fa5;unsigned short cw=0xa7f;__asm__ volatile("fninit\n\tfld1\n\tfldpi\n\tfldz\n\tfld1\n\tfdivp\n\tfldcw %0\n\tldmxcsr %1"::"m"(cw),"m"(mxcsr):"memory","st","st(1)","st(2)","st(3)");save(r);restore(host);for(unsigned i=6;i<16;++i)for(unsigned j=0;j<16;++j)r.fx[160+16*i+j]=static_cast<unsigned char>(i*31+j*17+7);return r;}
void checked(Context& c,std::ofstream& raw){Capture host{},before{},after{};save(host);auto seeded=seed();SetLastError(0x734612ab);mw34_capture_test_boundary(&c,&before,&after,&seeded);restore(host);++hardware_pairs;
 raw.write(reinterpret_cast<const char*>(&before),sizeof(before));raw.write(reinterpret_cast<const char*>(&after),sizeof(after));raw.write(reinterpret_cast<const char*>(&c.error_before),4);raw.write(reinterpret_cast<const char*>(&c.error_after),4);raw.flush();need(bool(raw),"Raw actual pair retained before strict validation");
 need(c.error_before==0x734612ab&&c.error_after==c.error_before,"Actual caller LastError preserved");need(before.env==after.env,"Actual full legacy ENV28 preserved");need(std::any_of(before.env.begin()+12,before.env.begin()+20,[](auto b){return b!=0;}),"Rich nonzero legacy instruction/data witness");need(std::equal(before.fx.begin(),before.fx.begin()+5,after.fx.begin()),"Actual x87 CW/SW/FTW preserved");need(std::equal(before.fx.begin()+24,before.fx.begin()+28,after.fx.begin()+24),"Actual full MXCSR preserved");for(unsigned i=0;i<8;++i)need(std::equal(before.fx.begin()+32+16*i,before.fx.begin()+42+16*i,after.fx.begin()+32+16*i),"Every physical raw80 register preserved");for(unsigned i=6;i<16;++i)need(std::equal(before.fx.begin()+160+16*i,before.fx.begin()+176+16*i,after.fx.begin()+160+16*i),"Actual nonvolatile XMM sentinel preserved");need((before.flags&0x400)==(after.flags&0x400),"Actual direction flag preserved");}
int main(int argc,char** argv){try{need(argc==2,"One fresh control output directory");fs::path out=fs::absolute(argv[1]);need(!fs::exists(out)&&fs::create_directories(out),"Fresh control report");std::ofstream raw(out/"hardware.bin",std::ios::binary);need(bool(raw),"Fresh hardware samples");
 std::array<unsigned char,256> bytes{};for(unsigned i=0;i<bytes.size();++i)bytes[i]=static_cast<unsigned char>(i);
 auto operation=[&](cd::Writer& w,unsigned op,std::string_view name,const void* data,std::size_t size,bool refusal){Context c{&w,op,false,0,0,name,data,size};checked(c,raw);need(c.threw==refusal,"Actual protected transport result");if(refusal)++refusals;return c.receipt;};
 {cd::Options o;o.files_per_part=2;cd::Writer w(out/"count-split",o);operation(w,0,"z/empty",nullptr,0,false);operation(w,0,"a/binary",bytes.data(),bytes.size(),false);operation(w,0,"b/binary",bytes.data(),bytes.size(),false);auto r=operation(w,2,"",nullptr,0,false);need(r&&r->parts.size()==2&&r->logical_files==3&&r->payload_bytes==512,"Count rollover actual two-part union");operation(w,2,"",nullptr,0,true);}
 for(unsigned mode=0;mode<3;++mode){cd::Options o;if(mode==0)o.bytes_per_part=3;if(mode==1)o.index_bytes_per_part=400;cd::Writer w(out/("split-"+std::to_string(mode)),o);for(auto name:{"a","b","c"}){operation(w,0,name,bytes.data(),mode==0?2:0,false);if(mode==2)operation(w,1,"",nullptr,0,false);}auto r=operation(w,2,"",nullptr,0,false);need(r&&r->parts.size()==(mode==1?2:3)&&r->logical_files==3,"Byte/index/explicit closure actual disjoint parts");}
 for(unsigned mode=0;mode<3;++mode){cd::Options o;if(mode==0)o.files_per_part=cd::max_files+1;if(mode==1)o.bytes_per_part=cd::max_total+1;if(mode==2)o.index_bytes_per_part=cd::max_index+1;auto target=out/("raised-"+std::to_string(mode));std::unique_ptr<cd::Writer> owner;Context c{};c.operation=3;c.owner=&owner;c.target=&target;c.options=&o;checked(c,raw);need(c.threw&&!owner&&!fs::exists(target),"Frozen maximum cannot be raised by checked factory");++refusals;}
 {cd::Options o;auto target=out/"factory";std::unique_ptr<cd::Writer> owner;Context c{};c.operation=3;c.owner=&owner;c.target=&target;c.options=&o;checked(c,raw);need(!c.threw&&bool(owner),"Protected factory succeeds");operation(*owner,0,"factory/empty",nullptr,0,false);auto r=operation(*owner,2,"",nullptr,0,false);need(r&&r->logical_files==1,"Protected factory completes");Context d{};d.operation=4;d.owner=&owner;checked(d,raw);need(!owner,"Protected destructor completes");}
 for(unsigned mode=0;mode<7;++mode){auto target=out/("fault-"+std::to_string(mode));{
  cd::Options o;if(mode==3)o.bytes_per_part=3;if(mode==4)o.fail_after_written_bytes=20;if(mode==5)o.fail_after_written_bytes=250;if(mode==6)o.fail_after_written_bytes=1u<<20;cd::Writer w(target,o);
  if(mode==0){operation(w,0,"same",bytes.data(),4,false);operation(w,1,"",nullptr,0,false);operation(w,0,"SAME",bytes.data(),4,true);}
  if(mode==1)operation(w,0,"oversize",nullptr,static_cast<std::size_t>(cd::max_file+1),true);
  if(mode==2)operation(w,0,"null",nullptr,1,true);
  if(mode==3)operation(w,0,"too-big",bytes.data(),4,true);
  if(mode==4||mode==5){operation(w,0,"record",bytes.data(),16,false);operation(w,2,"",nullptr,0,true);}
  if(mode==6){std::vector<unsigned char> big(2u<<20,0x57);operation(w,0,"partial",big.data(),big.size(),true);}
  operation(w,0,"retry",bytes.data(),1,true);operation(w,2,"",nullptr,0,true);
 }need(!fs::exists(target),"Poisoned partial capture publishes no output");}
 {auto target=out/"empty";{cd::Writer w(target);operation(w,2,"",nullptr,0,true);operation(w,0,"retry",nullptr,0,true);}need(!fs::exists(target),"Empty failure remains poisoned and unpublished");}
 {cd::Writer w(out/"default-overflow");for(unsigned i=0;i<=cd::max_files;++i)need(w.try_append("record-"+std::to_string(i),nullptr,0),"Checked full-limit record emitted");const auto* r=w.try_finish();need(r&&r->parts.size()==2&&r->logical_files==cd::max_files+1&&r->parts[0].logical_files==cd::max_files&&r->parts[1].logical_files==1,"Actual unchanged 200000-record maximum partitions compactly");}
 raw.close();need(!raw.fail(),"Closed complete hardware stream");for(const auto& p:fs::directory_iterator(out))need(p.path().filename().string().front()!='.',"No private partial debris after success/failure cleanup");
 std::ofstream result(out/"controls.json");result<<"{\"passed\":true,\"checks\":"<<checks<<",\"hardware_pairs\":"<<hardware_pairs<<",\"refusals\":"<<refusals<<",\"default_limit_records\":200001,\"native_transport_executed\":true,\"game_executed\":false,\"transport_only\":true,\"volatile_XMM0_5_equality_claimed\":false}\n";result.close();need(!result.fail(),"Closed complete transport control receipt");std::cout<<"transport controls passed: "<<checks<<" checks / "<<hardware_pairs<<" actual hardware pairs / "<<refusals<<" refusals\n";return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}}
