#include "data_imports.hpp"
#include "provider_data.hpp"
#include "service_provider.hpp"
#include <cctype>

namespace mw34::m4_crt_data {
namespace {
constexpr GuestAddress acmdln_slot{0x5bb518},adjust_slot{0x5bb508},acmdln_global{0x78037174};
bool hash(const std::string&s){return s.size()==64&&s!=std::string(64,'0')&&std::all_of(s.begin(),s.end(),[](char c){return(c>='0'&&c<='9')||(c>='a'&&c<='f');});}
bool library(std::string s){std::transform(s.begin(),s.end(),s.begin(),[](unsigned char c){return static_cast<char>(std::tolower(c));});return s=="msvcrt.dll";}
}
[[noreturn]]void DataImportRegistry::fail(DataFaultReason r,GuestAddress a,const char*w){if(!fault_)fault_.emplace(r,a,w);throw *fault_;}
const m4::ImportSymbol&DataImportRegistry::named(const char*name,GuestAddress slot){
 const m4::ImportSymbol*found{};for(const auto&i:runtime_.image_metadata().imports)if(std::uint64_t{runtime_.image_metadata().image_base}+i.iat_rva==slot.value){if(found||!i.name||*i.name!=name||!library(i.library))fail(DataFaultReason::invalid_admission,slot,"Exact unique MSVCRT named data IAT owner required");found=&i;}
 if(!found)fail(DataFaultReason::invalid_admission,slot,"Declared data IAT owner missing");return *found;
}
DataImportRegistry::~DataImportRegistry(){
 // Trusted borrower lifetime: Runtime outlives this registry and callers do
 // not replace its owned mappings. Deliberate mutation is a required fault.
 try{if(owns_buffer_&&record_)runtime_.memory().unmap(record_->owned_guest_pointer);}catch(...){}
 try{if(owns_global_)runtime_.memory().unmap(acmdln_global);}catch(...){}
}
void DataImportRegistry::admit_reference_projection(std::span<const std::byte>provider,ReferenceProjection p){
 if(fault_)throw *fault_;
 if(record_)fail(DataFaultReason::invalid_admission,acmdln_slot,"Reference projection may be admitted once only");
 try{
  const auto&owner=named("_acmdln",acmdln_slot);(void)named("_adjust_fdiv",adjust_slot);
  if(runtime_.memory().load<std::uint32_t>(acmdln_slot)!=owner.original_iat_value)fail(DataFaultReason::changed_identity,acmdln_slot,"Raw named data IAT bytes changed");
  if(!p.observed_original_pointer||p.observed_buffer.empty()||p.observed_buffer.size()>131072||p.observed_buffer.back()!=std::byte{}||std::find(p.observed_buffer.begin(),p.observed_buffer.end()-1,std::byte{})!=p.observed_buffer.end()-1||!hash(p.original_measurement_sha256)||!hash(p.original_buffer_sha256)||m4::sha256(p.observed_buffer)!=p.original_buffer_sha256)fail(DataFaultReason::invalid_admission,p.owned_guest_pointer,"Bounded exact measured NUL-terminated reference bytes required");
  if(p.owned_guest_pointer.value<0x32000000||std::uint64_t{p.owned_guest_pointer.value}+p.observed_buffer.size()>0x33000000)fail(DataFaultReason::invalid_admission,p.owned_guest_pointer,"Explicit bounded guest reference-data arena required");
  auto source=staged_crt_data(provider,acmdln_global,4);if(std::any_of(source.begin(),source.end(),[](std::byte b){return b!=std::byte{};}))fail(DataFaultReason::invalid_admission,acmdln_global,"Exact file source DWORD identity required; zero is not initialized-value authority");
  if(m4::sha256(m4_runtime::staged_crt_code(provider,GuestAddress{0x7800188c},11))!="6300f3f77dc2f2ce6ea36590028dd7f3b078c721a08d6daac27ebc8c636b5ac3")fail(DataFaultReason::invalid_admission,acmdln_global,"Exact observed writer identity required");
  DataRecord r{acmdln_slot,acmdln_global,p.owned_guest_pointer,owner.original_iat_value,p.observed_original_pointer,static_cast<std::uint32_t>(p.observed_buffer.size()),p.original_measurement_sha256,p.original_buffer_sha256};
  owned_reference_=std::move(p.observed_buffer);record_=std::move(r);
  runtime_.memory().map(record_->owned_guest_pointer,record_->buffer_bytes,Permissions::read|Permissions::write);owns_buffer_=true;runtime_.memory().write(record_->owned_guest_pointer,owned_reference_);runtime_.memory().protect(record_->owned_guest_pointer,Permissions::read);
  runtime_.memory().map(acmdln_global,4,Permissions::read|Permissions::write);owns_global_=true;
  // Explicitly authored reference projection, not native writer execution.
  runtime_.memory().store<std::uint32_t>(acmdln_global,record_->owned_guest_pointer.value);integrity();record_->reference_projection_ready=true;
 }catch(const DataFault&){throw;}catch(const MemoryFault&){fail(DataFaultReason::memory_fault,acmdln_global,"Required checked reference data mapping/access fault");}catch(const std::exception&){fail(DataFaultReason::invalid_admission,acmdln_global,"Exact reference data admission failed");}
}
void DataImportRegistry::integrity(){
 if(!record_||!owns_global_||!owns_buffer_)fail(DataFaultReason::unresolved_data,acmdln_slot,"Reference data projection is incomplete");
 const auto&owner=named("_acmdln",acmdln_slot);if(owner.original_iat_value!=record_->original_iat_value||runtime_.memory().load<std::uint32_t>(acmdln_slot)!=record_->original_iat_value||runtime_.memory().load<std::uint32_t>(acmdln_global)!=record_->owned_guest_pointer.value)fail(DataFaultReason::changed_identity,acmdln_slot,"Reference IAT/provider-global projection identity changed");
 std::vector<std::byte>current(record_->buffer_bytes);runtime_.memory().read(record_->owned_guest_pointer,current);if(current!=owned_reference_||m4::sha256(current)!=record_->buffer_sha256)fail(DataFaultReason::changed_identity,record_->owned_guest_pointer,"Owned measured reference bytes changed");
}
std::uint32_t DataImportRegistry::resolve_reference_load32(GuestAddress address){
 if(fault_)throw *fault_;
 try{
  if(address==adjust_slot)fail(DataFaultReason::unresolved_data,address,"_adjust_fdiv initialized contract remains unresolved");
  if(address!=acmdln_slot)fail(DataFaultReason::unresolved_data,address,"Only the explicitly declared reference data IAT load is admitted");
  if(!record_||!record_->reference_projection_ready)fail(DataFaultReason::unresolved_data,address,"Reference projection has not completed admission");
  integrity();return record_->provider_global.value;
 }catch(const DataFault&){throw;}catch(const MemoryFault&){fail(DataFaultReason::memory_fault,address,"Required checked reference data load fault");}catch(const std::exception&){fail(DataFaultReason::invalid_admission,address,"Reference data identity validation failed");}
}
} // namespace mw34::m4_crt_data
