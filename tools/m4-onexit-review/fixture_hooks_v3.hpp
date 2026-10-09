// Independent causal input/permission observers. The candidate and the real
// typed Windows API calls remain unchanged. These hooks never supply an API result.
#pragma once
namespace mw34_onexit_review {
using mw34::Permissions;
inline unsigned selected{},hits{},checks{},thread_checks{};
inline std::uint64_t old_growth_guest{},new_growth_guest{};
inline std::vector<unsigned>owned_guest_aliases;
inline void check(bool value,const char*why){++checks;if(!value)throw std::runtime_error(why);}

// Research allocations have no guest aliases and are excluded from source owner
// credit. They occupy real blocks on the exact live private heap so a genuine
// HeapReAlloc can move; the source request, flags, API and result are unchanged.
inline HANDLE pressure_heap{};
inline std::vector<std::array<std::uint64_t,12>>pressure_rows;
inline std::array<mw34::m4_cmd_native::ApiIdentity,3>pressure_before,pressure_after;
inline mw34::m4_cmd_native::ApiIdentity pressure_identity(const char*requested,std::uintptr_t target){
 using namespace mw34::m4_cmd_native;
 auto kernel=GetModuleHandleW(L"kernel32.dll");check(kernel,"Research pressure named kernel module");
 ApiIdentity a;a.target=target;a.named_target=reinterpret_cast<std::uintptr_t>(GetProcAddress(kernel,requested));
 check(a.named_target==target,"Research pressure imported and named API match");a.region=region(reinterpret_cast<void*>(target));a.owner=a.region.allocation;
 const char*alias=std::string_view(requested)=="HeapAlloc"?"RtlAllocateHeap":std::string_view(requested)=="HeapSize"?"RtlSizeHeap":requested;
 a.owner_named_target=reinterpret_cast<std::uintptr_t>(GetProcAddress(reinterpret_cast<HMODULE>(a.owner),alias));
 check(a.owner_named_target==target&&a.region.state==MEM_COMMIT&&a.region.type==MEM_IMAGE,
       "Research pressure executable actual owning API export");
 std::array<wchar_t,32768>path{};auto n=GetModuleFileNameW(reinterpret_cast<HMODULE>(a.owner),path.data(),path.size());
 check(n&&n<path.size(),"Research pressure physical owning module path");a.module_path.assign(path.data(),n);
 a.module_sha=mw34::m4::sha256(readfile(std::filesystem::path(a.module_path),16*1024*1024));return a;
}
inline void pressure_start(std::uint64_t heap){
 check(!pressure_heap&&pressure_rows.empty()&&heap,"Fresh exact research pressure heap");pressure_heap=reinterpret_cast<HANDLE>(heap);
 mw34::m4_nmx_integration::NumericHostBoundary hardware(0x37f);mw34::m4_spi_connected::ErrorBoundary error;
 pressure_before={pressure_identity("HeapAlloc",reinterpret_cast<std::uintptr_t>(&::HeapAlloc)),
                  pressure_identity("HeapSize",reinterpret_cast<std::uintptr_t>(&::HeapSize)),
                  pressure_identity("HeapFree",reinterpret_cast<std::uintptr_t>(&::HeapFree))};
 for(unsigned n=0;n<256;++n){
  SetLastError(0x4D573354);auto p=::HeapAlloc(pressure_heap,0,128);const auto allocation_error=GetLastError();
  check(p!=nullptr,"Actual bounded research pressure allocation succeeded");
  auto capacity=::HeapSize(pressure_heap,0,p);check(capacity>=128&&capacity<=4096,"Actual bounded research pressure capacity");
  pressure_rows.push_back({1,n,heap,128,reinterpret_cast<std::uintptr_t>(p),capacity,allocation_error,0,0,0,0,0});
 }
}
inline void pressure_release(){
 if(!pressure_heap)return;
 for(auto&row:pressure_rows){SetLastError(0x4D573354);row[7]=1;row[8]=::HeapFree(pressure_heap,0,reinterpret_cast<void*>(row[4]));row[9]=GetLastError();check(row[8],"Every actual research pressure block released once");}
 pressure_after={pressure_identity("HeapAlloc",reinterpret_cast<std::uintptr_t>(&::HeapAlloc)),
                 pressure_identity("HeapSize",reinterpret_cast<std::uintptr_t>(&::HeapSize)),
                 pressure_identity("HeapFree",reinterpret_cast<std::uintptr_t>(&::HeapFree))};
 check(pressure_before==pressure_after,"Actual research pressure API identities unchanged");pressure_heap=nullptr;
}

struct Latest {
 std::array<std::uint64_t,32>api{},growth{};std::array<unsigned,32>summary{};bool have_api{},have_growth{};
};
inline void receive(std::string_view name,std::span<const std::byte>bytes,void*opaque){
 auto&v=*static_cast<Latest*>(opaque);
 if(name=="locale-summary.bin"){
  check(bytes.size()==sizeof(v.summary),"Independent exact current owner summary width");
  std::memcpy(v.summary.data(),bytes.data(),bytes.size());
 }
 if(name=="locale-allocations.bin"){
  check(bytes.size()%128==0,"Independent complete allocation identity rows");
  for(std::size_t offset=0;offset<bytes.size();offset+=128){
   std::array<std::uint64_t,16>allocation{};std::memcpy(allocation.data(),bytes.data()+offset,128);
   const auto address=unsigned(allocation[1]);
   if(address&&std::find(owned_guest_aliases.begin(),owned_guest_aliases.end(),address)==owned_guest_aliases.end())owned_guest_aliases.push_back(address);
  }
 }
 if(name.starts_with("locale-api-")&&name.ends_with("-witness.bin")){
  check(bytes.size()==sizeof(v.api),"Independent exact current API witness width");
  std::memcpy(v.api.data(),bytes.data(),bytes.size());v.have_api=true;
 }
 if(name.find("growth")!=std::string_view::npos&&name.ends_with("-witness.bin")){
  check(bytes.size()==sizeof(v.growth),"Independent exact changed growth witness width");
  std::memcpy(v.growth.data(),bytes.data(),bytes.size());v.have_growth=true;
 }
}
template<class Binding>Latest latest(Binding&b){Latest v;b.dump(&receive,&v);return v;}
template<class Binding>void observe(Binding&b,unsigned point){
 if(hits)return;
 if(point<40||point>45)return;
 auto v=latest(b);if(!v.have_api)return;const auto site=unsigned(v.api[2]);
 if(v.have_growth){
  for(const auto address:{unsigned(v.growth[3]),unsigned(v.growth[13])})
   if(address&&std::find(owned_guest_aliases.begin(),owned_guest_aliases.end(),address)==owned_guest_aliases.end())owned_guest_aliases.push_back(address);
 }
 const bool sizing=site==0x780015B5,reallocating=site==0x78011C27;
 if(selected==9&&point==40&&reallocating&&!pressure_heap&&pressure_rows.empty())pressure_start(b.summary()[15]);
 if(!selected&&point==41&&sizing&&!thread_checks){
  const auto before=b.summary();bool denied=false;
  std::thread foreign([&]{try{b.finish();}catch(const std::runtime_error&){denied=true;}});foreign.join();
  check(denied,"Independent foreign-thread finish refusal");
  check(b.summary()==before&&b.live_handle(),"Foreign thread cannot release or alter the live owner");++thread_checks;
 }
 if(selected==1&&point==40&&sizing){
  ++hits;b.runtime().memory().template store<unsigned>({unsigned(v.api[5])+12},0x31FFF004);
 }
 if(selected==2&&point==40&&sizing){
  ++hits;b.runtime().memory().template store<unsigned>({unsigned(v.api[5])},unsigned(v.api[6])^4);
 }
 if(selected==3&&point==40&&sizing){
  ++hits;const auto slot=unsigned(v.api[3]);b.runtime().memory().protect({slot&~4095U},Permissions::read|Permissions::write);
  b.runtime().memory().template store<unsigned>({slot},unsigned(v.api[4])^1);
 }
 if(selected==4&&point==40&&sizing){
  ++hits;b.runtime().memory().protect({site&~4095U},Permissions::read|Permissions::write);
  const auto old=b.runtime().memory().template load<unsigned char>({site});b.runtime().memory().template store<unsigned char>({site},old^1);
 }
 if(selected==5&&point==43&&sizing){
  ++hits;b.runtime().memory().protect({unsigned(v.api[22])&~4095U},Permissions::read);
 }
 if(selected==6&&point==41&&reallocating){
  ++hits;throw std::runtime_error("Independent exception after actual HeapReAlloc before alias/output admission");
 }
 if(selected==7&&point==44&&reallocating){
  check(v.have_growth&&v.growth[20]>0,"Independent partial transfer is actually committed");
  ++hits;new_growth_guest=v.growth[13];
  b.runtime().memory().protect({unsigned(new_growth_guest)&~4095U},Permissions::read);
 }
 if(selected==8&&point==43&&reallocating){
  ++hits;throw std::runtime_error("Independent exception after genuine HeapReAlloc stdcall return");
 }
 if(selected==9&&point==40&&sizing&&v.api[22]!=old_growth_guest&&old_growth_guest){
  ++hits;b.runtime().memory().template store<unsigned>({unsigned(v.api[5])+12},unsigned(old_growth_guest));
 }
 if(selected==10&&point==40&&reallocating){
  ++hits;b.finish();
 }
 if(selected==11&&point==45&&v.api[3]==0x7802E048){++hits;throw std::runtime_error("Independent exception after genuine registered provider RET");}
 if(selected==12&&point==40&&sizing){
  ++hits;b.runtime().memory().template store<unsigned>({unsigned(v.api[5])+12},unsigned(v.api[22])+4);
 }
 if(selected==13&&point==40&&reallocating){
  check(v.have_growth&&v.summary[28]&&v.growth[10],"Independent exact proposed growth alias and size");
  ++hits;const auto mapped=(unsigned(v.growth[10])+4095)&~4095U;
  b.runtime().memory().map({v.summary[28]},mapped,Permissions::read|Permissions::write);
 }
 if(v.have_growth){old_growth_guest=v.growth[3];new_growth_guest=v.growth[13];}
}
}
