// Independent original MFC call, partial owner and source-free controls.
#pragma once
#include "D:/Projects/MW34Recomp/tools/m4-strings-review/fixture_hooks_v2.hpp"
namespace mw34_mfc_review {
using mw34_onexit_review::check;
using mw34_onexit_review::add_alias;
using mw34::Permissions;
inline unsigned selected{},hits{},thread_checks{},probe_calls{};
inline std::array<std::uint64_t,32>trigger_mfc{};
inline std::array<std::uint64_t,8>trigger_store{};
inline std::vector<std::byte>trigger_native_before;
inline std::vector<std::byte>trigger_native_after;
template<class Session>void observe(Session&s,unsigned point){
 if(hits||!selected||selected==1||selected>=16&&selected<=19)return;
 const auto rows=s.mfc_witnesses();if(rows.empty())return;
 const std::array<unsigned,21>points{0,0,71,70,72,73,74,73,70,71,72,75,73,74,76,77,0,0,0,0,74};
 if(point!=points[selected])return;
 const auto probe=s.mfc_store_probe();const auto row=selected==20?rows.back():rows.front();
 if(selected==20){if(row[2]!=0x4a8c20||probe[3]!=0x4a8c55||row[24]!=4)return;}
 else if(row[2]!=0x40ffe0||row[1]!=0)return;
 if(selected==5||selected==12){if(probe[3]!=0x4c7b91)return;}
 if(selected==6||selected==13){if(probe[3]!=0x4c7b91||row[24]!=4)return;}
 if(selected==7&&probe[3]!=0x4c7b99)return;
 ++hits;trigger_mfc=row;trigger_store=probe;add_alias(unsigned(row[16]));
 if(row[17]&&row[19]&&!row[30]){trigger_native_before.resize(row[19]);std::memcpy(trigger_native_before.data(),reinterpret_cast<const void*>(row[17]),row[19]);}
 auto&r=s.runtime();
 if(selected==2){unsigned bad=0x78001390;std::memcpy(r.remill_state().data()+2232,&bad,4);return;}
 if(selected==3){r.memory().protect({0x5f498000},Permissions::read|Permissions::write);r.memory().store<unsigned>({0x5f498970},0);r.memory().protect({0x5f498000},Permissions::read);return;}
 if(selected==4){check(row[17]&&row[19],"Actual private full-width object allocation");*reinterpret_cast<unsigned char*>(row[17])^=0x55;trigger_native_after.resize(row[19]);std::memcpy(trigger_native_after.data(),reinterpret_cast<const void*>(row[17]),row[19]);return;}
 if(selected==5||selected==6||selected==20){r.memory().protect({unsigned(row[16])},Permissions::read);return;}
 if(selected==7){r.memory().protect({0x5e0000},Permissions::read);return;}
 throw std::runtime_error("Independent deliberate MFC source boundary observer failure");
}
}
