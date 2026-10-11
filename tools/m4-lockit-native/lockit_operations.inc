// Genuine loaded x86 input is associated with a distinct native CS resource.
// The association does not claim to execute MSVCP DllMain or its lazy path.
void Binding::lockit_bootstrap(){
 if(lockit_admitted_||runtime.memory().load<unsigned>({0x78145658})!=2||section_for(0x78145640))deny("Authentic loaded Lockit state2 and fresh distinct resource required",0x78145658);
 auto initial=guest_bytes(0x78145640,24);if(initial!=std::vector<std::byte>(lockit_loaded_page.begin()+0x640,lockit_loaded_page.begin()+0x658))deny("Exact observed loaded Lockit CS input required",0x78145640);
 auto object=std::make_unique<CriticalSection>();object->guest=0x78145640;object->generation=++generation_;auto*section=object.get();owned_sections_.push_back(std::move(object));lockit_generation_=section->generation;
 checkpoint(runtime,"lockit-resource-association-before");
 if(!lifecycle_api("InitializeCriticalSection",0x78146190,0x866ce,reinterpret_cast<std::uintptr_t>(&section->native),[&](){::InitializeCriticalSection(&section->native);section->initialized=true;++section->initializes;++sections_initialized_;return true;}))deny("Measured native Lockit resource association required",0x78145640);
 lockit_admitted_=true;lockit_source_cs_=initial;lockit_guard();checkpoint(runtime,"lockit-resource-association-after");
}
void Binding::lockit_guard(){
 if(!lockit_admitted_){if(lockit_generation_)deny("Published Lockit admission cannot be revoked",0x78145640);return;}
 auto*section=section_for(0x78145640);
 if(!section||section->generation!=lockit_generation_||!section->initialized||section->deleted||section->initializes!=1||section->deletes||section->enters<section->leaves||section->depth!=section->enters-section->leaves||section->depth>8||section->native.RecursionCount!=LONG(section->depth)||runtime.memory().load<unsigned>({0x78145658})!=2||guest_bytes(0x78145640,24)!=lockit_source_cs_)deny("Distinct live loaded Lockit source/native generation and recursive depth required",0x78145640);
 const auto thread=static_cast<unsigned>(reinterpret_cast<std::uintptr_t>(section->native.OwningThread));if((section->depth&&(section->owner_thread!=thread_||thread!=GetCurrentThreadId()))||(!section->depth&&thread))deny("Actual Lockit native owner thread and depth required",0x78145640);
}
std::uint64_t Binding::lockit_read(unsigned address,std::uint64_t value,unsigned width){
 if(width!=4||(address!=0x5bb4f8&&address!=0x5bb4f4))return value;
 const auto*input=lockit_input(registry_root_);const auto ctor=address==0x5bb4f8;const auto pc=state.gpr.rip.dword;
 if(!input||pc!=(ctor?input->ctor:input->dtor)||value!=(ctor?0x1df582U:0x1df568U))deny("Exact root and loaded-image named Lockit import projection required",address,pc);
 if(!lockit_admitted_||!section_for(0x78145640))deny("Explicit live Lockit resource admission required",address,pc);lockit_guard();const auto target=ctor?0x7810a290U:0x7810a350U;research_projections_.push_back({5,pc,address,unsigned(value),target,0,0,0});lockit_imports_.push_back({1,registry_root_,pc,address,value,target,source_accesses_.size(),0});return target;
}
void Binding::lockit_called(unsigned target,unsigned site,unsigned frame){
 if(target!=0x7810a290&&target!=0x7810a350)return;if(!lockit_admitted_||!section_for(0x78145640))deny("Explicit live Lockit resource CALL admission required",target,site);lockit_guard();const auto*input=lockit_input(registry_root_);const bool ctor=target==0x7810a290;
 if(!input||site!=(ctor?input->ctor:input->dtor)||state.gpr.rcx.dword!=frame+(ctor?input->ctor_offset:input->dtor_offset))deny("Genuine Lockit scratch ECX and source CALL frame required",frame,site);
 std::array<std::uint64_t,16>row{1,lockit_calls_.size(),registry_root_,target,site,frame,runtime.memory().load<unsigned>({frame}),state.gpr.rcx.dword,section_for(0x78145640)->depth,source_accesses_.size(),native_apis_.size(),0,0,0,0,0};lockit_calls_.push_back(row);
}
void Binding::lockit_returned(unsigned entry,unsigned result,unsigned frame){
 if(entry!=0x7810a290&&entry!=0x7810a350)return;lockit_guard();if(lockit_calls_.empty())deny("Retained actual Lockit CALL required",entry);auto&w=lockit_calls_.back();
 if(w[3]!=entry||w[5]!=frame||w[11]||(entry==0x7810a290&&result!=w[7]))deny("Literal Lockit RET and returned constructor ECX required",frame);
 const auto depth=section_for(0x78145640)->depth;if(depth!=(entry==0x7810a290?w[8]+1:w[8]-1))deny("Balanced genuine Lockit source/native recursion required",frame);w[11]=1;w[12]=result;w[13]=depth;w[14]=source_accesses_.size();w[15]=native_apis_.size();
}
void Binding::lockit_section_after(unsigned site){
 if(site!=0x7810a30b&&site!=0x7810a35e)return;
 auto*section=section_for(0x78145640);if(!section||section->generation!=lockit_generation_)deny("Exact current Lockit API resource required",0x78145640,site);
 // DWORD fields follow the observed serial x86 CS domain; opaque DebugInfo,
 // semaphore and spin flags remain genuine loaded inputs. Native resource is40B.
 auto bytes=lockit_source_cs_;auto put=[&](unsigned offset,unsigned value){std::memcpy(bytes.data()+offset,&value,4);};put(4,static_cast<unsigned>(section->native.LockCount));put(8,section->depth);put(12,section->depth?GetCurrentThreadId():0);
 native_apis_.back().outputs.push_back(bytes);preflight_write(0x78145640,24);
 for(unsigned offset=0;offset<24;offset+=4){unsigned value{};std::memcpy(&value,bytes.data()+offset,4);runtime.memory().write({0x78145640+offset},std::span(bytes).subspan(offset,4));expected_store(0x78145640+offset,bytes.data()+offset,4);std::memcpy(lockit_source_cs_.data()+offset,bytes.data()+offset,4);api_transports_.push_back({site,0x78145640+offset,value,4,1});}
 std::array<std::byte,40>actual{};std::memcpy(actual.data(),&section->native,40);lockit_native_images_.push_back(actual);lockit_guard();
}
void Binding::dump_lockit(CaptureSink sink,void*context)const{
 sink("lockit-imports.bin",std::as_bytes(std::span(lockit_imports_)),context);sink("lockit-calls.bin",std::as_bytes(std::span(lockit_calls_)),context);sink("lockit-native-images.bin",std::as_bytes(std::span(lockit_native_images_)),context);sink("lockit-source-CS.bin",lockit_source_cs_,context);
 const std::array<std::uint64_t,8>v{1,unsigned(lockit_admitted_),lockit_generation_,0x78145640,24,40,GetCurrentThreadId(),0};sink("lockit-resource.bin",std::as_bytes(std::span(v)),context);
}
