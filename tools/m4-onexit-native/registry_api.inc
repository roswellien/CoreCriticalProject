
void Binding::native_heap_size(unsigned site,unsigned frame,unsigned argc){
 auto&api=native_apis_.back();const auto guest=unsigned(api.words[22]);auto*a=allocation_for(guest);
 if(argc!=3||api.words[20]!=token||api.words[21]||!a||a->guest!=guest||!owned_handle_||a->pending)deny("Actual HeapSize requires exact live heap/allocation association",guest,site);
 api.words[16]=a->acquired;api.inputs.push_back(guest_bytes(guest,a->extent));
 NativeExportProof before;api.before=measured_api("HeapSize",reinterpret_cast<std::uintptr_t>(&::HeapSize),&before);std::memcpy(api.export_before.data(),&before,sizeof(before));
 checkpoint(runtime,("locale-api-"+std::to_string(native_apis_.size()-1)+"-before").c_str());stable_hook(40);guard();source_identity();
 if(runtime.memory().load<unsigned>({frame})!=api.words[6]||runtime.memory().load<unsigned>({frame+4})!=token||runtime.memory().load<unsigned>({frame+8})||runtime.memory().load<unsigned>({frame+12})!=guest||allocation_for(guest)!=a)deny("Immediate actual HeapSize frame and allocation identity",frame,site);
 SIZE_T result;{InvocationHostBoundary hardware;fn::LastErrorBoundary errors;SetLastError(caller_error);api.words[9]=GetLastError();result=::HeapSize(owned_handle_,0,a->native);api.words[10]=GetLastError();SetLastError(caller_error);api.words[11]=GetLastError();}
 api.words[8]=result;api.words[14]=1;api.words[17]=result;
 NativeExportProof after;api.after=measured_api("HeapSize",reinterpret_cast<std::uintptr_t>(&::HeapSize),&after);std::memcpy(api.export_after.data(),&after,sizeof(after));
 if(api.before!=api.after||api.export_before!=api.export_after)deny("Measured HeapSize export owner remained identical",guest,site);
 if(result!=SIZE_T(-1)){
  if(result<a->extent||result>1024*1024||result>a->mapped_bytes)deny("Actual capacity must fit bounded guest backing",guest,site);
  std::vector<std::byte>capacity_bytes(static_cast<unsigned>(result));std::memcpy(capacity_bytes.data(),a->native,unsigned(result));api.outputs.push_back(std::move(capacity_bytes));
  preflight_write(guest,unsigned(result));api_transfer(guest,api.outputs.back());a->capacity=a->extent=unsigned(result);
 }
 checkpoint(runtime,("locale-api-"+std::to_string(native_apis_.size()-1)+"-after").c_str());stable_hook(41);guard();source_identity();
 if(result!=SIZE_T(-1)&&result>UINT32_MAX)deny("Actual HeapSize result fits original DWORD",guest,site);
 api.words[12]=result==SIZE_T(-1)?UINT32_MAX:unsigned(result);api.words[13]=a->extent;api_return(frame,argc,unsigned(api.words[12]));
 checkpoint(runtime,("locale-api-"+std::to_string(native_apis_.size()-1)+"-returned").c_str());stable_hook(43);
}
void Binding::native_heap_realloc(unsigned site,unsigned frame,unsigned argc){
 auto&api=native_apis_.back();const auto guest=unsigned(api.words[22]),rounded=unsigned(api.words[23]);auto*a=allocation_for(guest);
 if(argc!=4||api.words[20]!=token||api.words[21]||!a||a->guest!=guest||!owned_handle_||a->pending||!rounded||rounded>1024*1024||runtime.memory().load<unsigned>({global+4})!=1||runtime.memory().load<unsigned>({0x78037150}))deny("Actual positive mode1 HeapReAlloc needs exact current alias and source zero newmode",guest,site);
 unsigned source_request{};for(auto it=calls_.rbegin();it!=calls_.rend();++it)if(it->entry==0x780019f1){source_request=runtime.memory().load<unsigned>({it->frame+8});break;}
 if(!source_request||source_request>1024*1024||((source_request+15)&~15U)!=rounded)deny("Actual source realloc rounded request",rounded,site);
 const auto oldnative=a->native;const auto oldacquired=a->acquired;const auto oldextent=a->extent,oldcapacity=a->capacity,oldgeneration=a->generation;
 const auto mapped=(rounded+4095)&~4095U,newguest=allocation_cursor_;
 if(std::uint64_t(newguest)+mapped>0x32000000ULL)deny("Bounded disjoint relocation alias space",newguest,site);
 auto permission=runtime.memory();permission.map({newguest},mapped,Permissions::read|Permissions::write);preflight_write(guest,a->mapped_bytes);
 std::vector<std::byte>oldbytes(a->extent);std::memcpy(oldbytes.data(),a->native,a->extent);api.inputs.push_back(oldbytes);
 std::vector<std::byte>newbytes(rounded),newexpected(mapped,std::byte{});
 registry_growth_.push_back({1,native_apis_.size()-1,site,guest,oldacquired,oldgeneration,a->requested,oldextent,oldcapacity,source_request,rounded,0,0,guest,oldacquired,oldgeneration,oldextent,oldcapacity,0,0,0,0,1,0,0,0,0,0,0,0,0,0});auto&g=registry_growth_.back();
 api.words[16]=oldacquired;api.words[17]=oldcapacity;
 NativeExportProof before;api.before=measured_api("HeapReAlloc",reinterpret_cast<std::uintptr_t>(&::HeapReAlloc),&before);std::memcpy(api.export_before.data(),&before,sizeof(before));
 checkpoint(runtime,("locale-api-"+std::to_string(native_apis_.size()-1)+"-before").c_str());stable_hook(40);guard();source_identity();
 if(runtime.memory().load<unsigned>({frame})!=api.words[6]||runtime.memory().load<unsigned>({frame+4})!=token||runtime.memory().load<unsigned>({frame+8})||runtime.memory().load<unsigned>({frame+12})!=guest||runtime.memory().load<unsigned>({frame+16})!=rounded||allocation_for(guest)!=a)deny("Immediate actual HeapReAlloc frame and owner identity",frame,site);
 {auto final=runtime.memory();final.map({newguest},mapped,Permissions::read|Permissions::write);preflight_write(guest,a->mapped_bytes);}
 void*result{};{InvocationHostBoundary hardware;fn::LastErrorBoundary errors;SetLastError(caller_error);api.words[9]=GetLastError();result=::HeapReAlloc(owned_handle_,0,a->native,rounded);if(result){a->native=result;a->acquired=reinterpret_cast<std::uintptr_t>(result);a->pending=true;}api.words[10]=GetLastError();SetLastError(caller_error);api.words[11]=GetLastError();}
 // The pointer is privately owned before any allocation, observer, export read or transfer.
 api.words[8]=reinterpret_cast<std::uintptr_t>(result);api.words[14]=1;g[11]=api.words[8];g[12]=api.words[10];g[14]=result?api.words[8]:oldacquired;g[18]=result&&result!=oldnative;g[23]=!result;
 if(result){
  if((reinterpret_cast<std::uintptr_t>(result)&15)||rounded<oldextent)deny("Actual growth pointer alignment and preserved extent",guest,site);
  std::memcpy(newbytes.data(),result,rounded);if(!std::equal(oldbytes.begin(),oldbytes.end(),newbytes.begin()))deny("Actual growth preserves all preceding measured-capacity bytes",guest,site);
  std::copy(newbytes.begin(),newbytes.end(),newexpected.begin());a->pending_native=newbytes;api.outputs.push_back(newbytes);g[13]=g[18]?newguest:guest;g[15]=oldgeneration+1;g[16]=rounded;g[17]=0;
 }else{if(a->native!=oldnative||a->acquired!=oldacquired||std::memcmp(a->native,oldbytes.data(),oldextent))deny("Actual null realloc retains original native allocation and bytes",guest,site);api.outputs.push_back(oldbytes);}
 NativeExportProof after;api.after=measured_api("HeapReAlloc",reinterpret_cast<std::uintptr_t>(&::HeapReAlloc),&after);std::memcpy(api.export_after.data(),&after,sizeof(after));if(api.before!=api.after||api.export_before!=api.export_after)deny("Measured HeapReAlloc export owner remained identical",guest,site);
 checkpoint(runtime,("locale-api-"+std::to_string(native_apis_.size()-1)+"-after").c_str());stable_hook(41);guard();source_identity();
 if(result){
  const auto destination=unsigned(g[13]);
  if(destination==guest&&mapped>a->mapped_bytes)deny("In-place relocation exceeds currently owned mapped alias",guest,site);
  if(destination!=guest){runtime.memory().map({destination},mapped,Permissions::read|Permissions::write);a->guest=destination;a->mapped_bytes=mapped;a->expected.assign(mapped,std::byte{});a->retired_guest=guest;allocation_cursor_+=mapped;}
  else{preflight_write(guest,a->mapped_bytes);}
  a->extent=rounded;a->capacity=0;a->requested=source_request;a->generation=++generation_;a->initial=newbytes;g[15]=a->generation;
  for(unsigned offset=0;offset<rounded;){const auto width=std::min(4U,rounded-offset);runtime.memory().write({destination+offset},std::span(newbytes).subspan(offset,width));api_transports_.push_back({site,destination+offset,0,width,1});std::memcpy(&api_transports_.back().value,newbytes.data()+offset,width);std::memcpy(a->expected.data()+offset,newbytes.data()+offset,width);offset+=width;g[20]=offset;stable_hook(44);}
  if(destination!=guest){runtime.memory().unmap({guest});a->retired_guest=0;}a->pending=false;a->pending_native.clear();g[19]=1;api.words[12]=destination;api.words[13]=rounded;
 }else api.words[12]=0;
 guard();source_identity();api_return(frame,argc,unsigned(api.words[12]));
 checkpoint(runtime,("locale-api-"+std::to_string(native_apis_.size()-1)+"-returned").c_str());stable_hook(43);
}
