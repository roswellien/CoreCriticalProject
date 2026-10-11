#pragma once
#include "D:/Projects/MW34Recomp/tools/m4-strings-review/fixture_hooks_v2.hpp"
namespace mw34_container_controls {
using mw34_onexit_review::check;
inline unsigned selected{},hits{},mutation_hits{};
inline std::array<std::uint64_t,32>trigger_null{},trigger_borrowed{},trigger_string{},trigger_mfc{},trigger_frame{};
inline std::array<std::uint64_t,16>trigger_vector{};
inline std::array<std::byte,3504>trigger_state{};inline std::array<std::byte,512>trigger_fx{};
inline std::array<std::byte,40>trigger_cpu{};inline std::array<std::byte,28>trigger_env{};inline std::array<std::byte,4096>trigger_stack{};
inline std::array<unsigned,5>trigger_tib{};inline std::array<unsigned,3>trigger_record{};
inline std::vector<std::byte>trigger_native_before,trigger_native_after;
inline unsigned trigger_point{},trigger_PC{};
inline void mutate_witness(std::string_view name,std::span<const std::byte>bytes,void*){
 const char*wanted=selected==16?"container-borrowed-witnesses.bin":selected==17?"container-nullfree-witnesses.bin":selected==18?"container-import-ledger.bin":selected==19?"container-vector-probe.bin":selected==20?"container-vector-stores.bin":"container-null-active.bin";
 if(name!=wanted)return;
 if(selected==21){check(bytes.size()==4,"Actual private null-free active index");auto*words=reinterpret_cast<unsigned*>(const_cast<std::byte*>(bytes.data()));words[0]^=1;}
 else{check(bytes.size()>=64,"Actual nonconst container witness span");auto*words=reinterpret_cast<std::uint64_t*>(const_cast<std::byte*>(bytes.data()));const auto word=selected==16?18:selected==17?7:selected==18?bytes.size()/8-8+6:selected==20?bytes.size()/8-16+6:6;words[word]^=1;}
 ++mutation_hits;
}
template<class Session>void observe(Session&s,unsigned point){
 if(!selected||hits)return;
 unsigned target{};unsigned root{};
 if(selected>=22){target=90+selected-22;root=target<=93?0x4ada90:target<=99?0x47f5b0:0x4ada90;}
 else{constexpr unsigned points[]{0,82,82,94,97,90,91,92,91,100,100,100,54,101,81,83,97,91,94,100,101,90};target=points[selected];root=(selected==2||selected==3||selected==4||selected==12||selected==14||selected==16||selected==18)?0x47f5b0:0x4ada90;}
 if(point!=target)return;
 const auto nulls=s.container_nullfree_witnesses(),borrowed=s.container_borrowed_witnesses(),strings=s.string_witnesses(),mfcs=s.mfc_witnesses(),frames=s.fs_witnesses();const auto vector=s.container_vector_probe();
 if(point>=90&&point<=93){if(nulls.empty()||nulls.back()[2]!=root)return;trigger_null=nulls.back();}
 else if(point>=94&&point<=99){if(borrowed.empty()||borrowed.back()[2]!=root)return;trigger_borrowed=borrowed.back();}
 else if(point==100||point==101){if(vector[2]!=root)return;trigger_vector=vector;if(selected==9&&vector[3]!=0x4ad8eb)return;if(selected==10&&vector[3]!=0x4ad90c)return;if(selected==11&&vector[3]!=0x4ad91a)return;}
 else if(point==54){if(strings.empty()||strings.back()[2]!=root||strings.back()[16]!=4)return;trigger_string=strings.back();}
 else if(point>=80&&point<=85){if(frames.empty()||frames.back()[2]!=root)return;}
 if(!nulls.empty()&&!trigger_null[0])trigger_null=nulls.back();if(!borrowed.empty()&&!trigger_borrowed[0])trigger_borrowed=borrowed.back();if(!strings.empty()&&!trigger_string[0])trigger_string=strings.back();if(!frames.empty())trigger_frame=frames.back();
 ++hits;trigger_point=point;auto&r=s.runtime();auto*state=reinterpret_cast<State*>(r.remill_state().data());trigger_PC=state->gpr.rip.dword;
 std::copy(r.remill_state().begin(),r.remill_state().end(),trigger_state.begin());std::copy(r.fx().begin(),r.fx().end(),trigger_fx.begin());std::memcpy(trigger_cpu.data(),&r.cpu(),40);trigger_env=mw34::m4_nmx_integration::view(*state).env;
 r.memory().read({0x20001000},trigger_stack);const auto base=r.fs_base().value;trigger_tib={base,r.memory().load<unsigned>({base}),r.memory().load<unsigned>({base+4}),r.memory().load<unsigned>({base+8}),r.memory().load<unsigned>({base+0x18})};
 if(trigger_frame[9])r.memory().read({unsigned(trigger_frame[9])},std::as_writable_bytes(std::span(trigger_record)));
 for(const auto&row:mfcs)if(row[18]==vector[10]&&row[17]&&row[19]){trigger_mfc=row;trigger_native_before.resize(row[19]);std::memcpy(trigger_native_before.data(),reinterpret_cast<const void*>(row[17]),row[19]);break;}
 if(selected==1||selected==2){const auto slot=selected==1?0x5bb4c8U:0x5bb454U,raw=selected==1?0x80000339U:0x8000021cU;r.memory().protect({0x5bb000},mw34::Permissions::read|mw34::Permissions::write);r.memory().store<unsigned>({slot},raw^1);r.memory().protect({0x5bb000},mw34::Permissions::read);return;}
 if(selected==3){r.memory().store<unsigned>({0x5f4ccb54},0x5f4cecec^4);return;}
 if(selected==4){r.memory().protect({unsigned(trigger_borrowed[7])&~4095U},mw34::Permissions::read);return;}
 if(selected==5){r.memory().store<unsigned>({unsigned(trigger_null[5])+4},1);return;}
 if(selected==8||selected==14||selected==15){r.memory().protect({base},mw34::Permissions::read);return;}
 if(selected==9||selected==10||selected==11){r.memory().protect({unsigned(vector[4])&~4095U},mw34::Permissions::read);return;}
 if(selected==12){check(trigger_string[10]&&trigger_string[11]&&trigger_string[13],"Actual string-owned full native backing");trigger_native_before.resize(trigger_string[13]);std::memcpy(trigger_native_before.data(),reinterpret_cast<const void*>(trigger_string[11]),trigger_string[13]);r.memory().protect({unsigned(trigger_string[10])},mw34::Permissions::read);return;}
 if(selected==13){check(trigger_mfc[17]&&trigger_mfc[19],"Actual vector-owned full native backing");reinterpret_cast<unsigned char*>(trigger_mfc[17])[trigger_mfc[19]-1]^=0x55;trigger_native_after.resize(trigger_mfc[19]);std::memcpy(trigger_native_after.data(),reinterpret_cast<const void*>(trigger_mfc[17]),trigger_mfc[19]);return;}
 if(selected>=16&&selected<=21){s.dump(&mutate_witness,nullptr);check(mutation_hits==1,"One exact actual private witness mutation");return;}
 throw std::runtime_error("Deliberate precise container/borrowed/null-free boundary observer failure");
}
}
