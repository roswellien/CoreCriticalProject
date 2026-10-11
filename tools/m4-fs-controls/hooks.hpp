#pragma once
#include "D:/Projects/MW34Recomp/tools/m4-strings-review/fixture_hooks_v2.hpp"
namespace mw34_fs_controls {
using mw34_onexit_review::check;
inline unsigned selected{},hits{};
inline std::array<std::uint64_t,32>trigger_frame{};
inline std::array<std::uint64_t,16>trigger_chain{},trigger_owner{};
inline std::array<std::byte,3504>trigger_state{};
inline std::array<std::byte,512>trigger_fx{};
inline std::array<std::byte,40>trigger_cpu{};
inline std::array<std::byte,28>trigger_env{};
inline std::array<std::byte,4096>trigger_stack{};
inline std::array<unsigned,5>trigger_tib{};
inline std::array<unsigned,3>trigger_record{};
inline std::vector<std::byte>trigger_native_before,trigger_native_after;
inline std::array<std::uint64_t,32>trigger_mfc{};
inline unsigned mutation_hits{};
inline void mutate_witness(std::string_view name,std::span<const std::byte>bytes,void*){
 const auto wanted=selected==21?"fs-owned-access-probe.bin":selected==22?"fs-owned-accesses.bin":"fs-native-input.bin";
 if(name!=wanted)return;check(bytes.size()>=128,"Genuine nonconst owned private witness span");
 auto*words=reinterpret_cast<std::uint64_t*>(const_cast<std::byte*>(bytes.data()));
 const auto word=selected==21?6:selected==22?(bytes.size()/8-16+6):8;
 words[word]^=1;++mutation_hits;
}
template<class Session>void observe(Session&s,unsigned point){
 if(!selected||hits)return;
 const auto frames=s.fs_witnesses();if(frames.empty())return;
 const auto chain=s.fs_chain_probe(),owned=s.fs_owner_probe();
 auto frame=frames.back();if(point>=80&&point<=85&&chain[4]==point&&chain[3]<frames.size())frame=frames[chain[3]];
 const auto pc=reinterpret_cast<State*>(s.runtime().remill_state().data())->gpr.rip.dword;
 unsigned target{};
 if(selected==21)target=86;else if(selected==22)target=87;else if(selected==23)target=81;
 else if(selected>=12&&selected<=19)target=80+selected-12;
 else {constexpr unsigned points[]{0,80,80,81,83,81,83,86,87,86,87,84};target=selected<12?points[selected]:83;}
 if(point!=target)return;
 if(selected==11){if(frame[3]!=0x4e78d0||frame[2]!=0x4d4830||!frame[13])return;}
 else if(selected==20){if(frame[3]!=0x4d48f0||frame[2]!=0x4d4830)return;}
 else if(selected==8){if(owned[2]!=0x4b4c10||owned[3]!=0x4e7977)return;}
 else {if(frame[2]!=0x46ab30||frame[3]!=0x4e78d0)return;}
 if(selected==7&&owned[3]!=0x4e7977)return;
 if(selected==9&&owned[3]!=0x4e7994)return;
 if(selected==10&&owned[3]!=0x4e796e)return;
 ++hits;trigger_frame=frame;trigger_chain=chain;trigger_owner=owned;
 auto&r=s.runtime();std::copy(r.remill_state().begin(),r.remill_state().end(),trigger_state.begin());std::copy(r.fx().begin(),r.fx().end(),trigger_fx.begin());std::memcpy(trigger_cpu.data(),&r.cpu(),40);
 trigger_env=ni::view(*reinterpret_cast<State*>(r.remill_state().data())).env;
 r.memory().read({0x20001000},trigger_stack);const auto base=r.fs_base().value;
 trigger_tib={base,r.memory().load<unsigned>({base}),r.memory().load<unsigned>({base+4}),r.memory().load<unsigned>({base+8}),r.memory().load<unsigned>({base+0x18})};
 r.memory().read({unsigned(frame[9])},std::as_writable_bytes(std::span(trigger_record)));
 const auto mfcs=s.mfc_witnesses();
 for(const auto&row:mfcs)if(row[18]==owned[11]&&row[17]&&row[19]){trigger_mfc=row;trigger_native_before.resize(row[19]);std::memcpy(trigger_native_before.data(),reinterpret_cast<const void*>(row[17]),row[19]);break;}
 if(selected==1){reinterpret_cast<State*>(r.remill_state().data())->addr.fs_base.dword^=4;return;}
 if(selected==2){r.memory().store<unsigned>({base},unsigned(frame[8])^4);return;}
 if(selected==3){r.memory().store<unsigned>({unsigned(frame[9]+4)},unsigned(frame[10])^4);return;}
 if(selected==4){r.memory().store<unsigned>({unsigned(frame[9])},unsigned(frame[8])^4);return;}
 if(selected==5||selected==6||selected==20){r.memory().protect({base},mw34::Permissions::read);return;}
 if(selected==8){const auto oldhead=reinterpret_cast<State*>(r.remill_state().data())->gpr.rdi.dword;for(const auto&row:mfcs)if(row[16]==oldhead){trigger_mfc=row;trigger_native_before.resize(row[19]);std::memcpy(trigger_native_before.data(),reinterpret_cast<const void*>(row[17]),row[19]);}check(trigger_mfc[16]==oldhead&&trigger_mfc[17],"Actual retained earlier append owner before second-link write");r.memory().protect({oldhead},mw34::Permissions::read);return;}
 if(selected==7||selected==9){check(owned[10]&&owned[7],"Actual precise shared-owned write target");r.memory().protect({unsigned(owned[10])},mw34::Permissions::read);return;}
 if(selected==10){check(trigger_mfc[17]&&trigger_mfc[19],"Actual privately owned fullnative backing");reinterpret_cast<unsigned char*>(trigger_mfc[17])[trigger_mfc[19]-1]^=0x55;trigger_native_after.resize(trigger_mfc[19]);std::memcpy(trigger_native_after.data(),reinterpret_cast<const void*>(trigger_mfc[17]),trigger_mfc[19]);return;}
 if(selected>=21){s.dump(&mutate_witness,nullptr);check(mutation_hits==1,"One precise research mutation of actual private observer span");return;}
 throw std::runtime_error("Deliberate precise normal-FS/shared-owner boundary observer failure");
}
}
