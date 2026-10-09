// Independent controls modify source inputs/permissions or throw at witnessed
// native boundaries. They never inject an API response.
namespace {
struct ReviewApi {std::array<std::uint64_t,32>words{};bool found{};};
void review_api_capture(std::string_view name,std::span<const std::byte>bytes,void*opaque){
 auto&v=*static_cast<ReviewApi*>(opaque);if(name.starts_with("locale-api-")&&name.ends_with("-witness.bin")){
  require(bytes.size()==sizeof(v.words),"Exact current API witness width");std::memcpy(v.words.data(),bytes.data(),bytes.size());v.found=true;
 }
}
ReviewApi review_latest(lb::Binding&b){ReviewApi v;b.dump(&review_api_capture,&v);return v;}
void review_hook(lb::Binding&b,unsigned point){
 if(b.control==1006&&point==60){++review_hook_hits;throw std::runtime_error("Independent terminal fault after genuine argv builder RET");}
 if(point<40||point>43)return;auto v=review_latest(b);if(!v.found)return;const auto site=unsigned(v.words[2]);
 if(!b.control&&point==41&&site==0x7800109d){
  review_check(b.live_handle()&&b.known_handle()!=0&&b.live_allocations()==1&&b.live_critical_sections()==5,"Owned lazy native CS and backing share a full parent heap");
  review_check(v.words[16]!=0&&!(v.words[16]&7)&&v.words[17]==40&&v.words[14]==1,"Actual private native CS40 has SDK alignment");
  bool denied=false;std::thread other([&]{try{b.finish();}catch(const std::runtime_error&){denied=true;}});other.join();
  review_check(denied&&b.live_handle()&&b.live_allocations()==1&&b.live_critical_sections()==5,"Foreign-thread finish denies before native release and retains ownership");++review_thread_units;
 }
 if(b.control==1001&&point==41&&site==0x7800109d){++review_hook_hits;throw std::runtime_error("Independent fault after genuine lazy InitializeCriticalSection");}
 if(b.control==1002&&point==41&&site==0x7800106f&&v.words[20]>=0x31000000){++review_hook_hits;throw std::runtime_error("Independent fault after genuine lazy EnterCriticalSection");}
 if(b.control==1003&&point==41&&site==0x78003e29){++review_hook_hits;b.runtime.memory().protect({unsigned(v.words[21])&~4095U},Permissions::read);}
 if(b.control==1004&&point==40&&site==0x78003e29){++review_hook_hits;const auto slot=unsigned(v.words[3]);b.runtime.memory().protect({slot&~4095U},Permissions::read|Permissions::write);b.runtime.memory().store<unsigned>({slot},unsigned(v.words[4])^1);}
 if(b.control==1005&&point==43&&site==lb::alloc_site&&b.summary()[2]==3){++review_hook_hits;b.runtime.memory().protect({unsigned(v.words[12])},Permissions::read);}
}
void review_phase(Runtime&r,const char*name){
 (void)r;(void)name;
}
}
