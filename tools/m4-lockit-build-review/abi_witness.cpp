#include "joint_protocol.hpp"
#include "registration_contract.hpp"
#include <cstddef>
#include <cstdio>

using namespace mw34::m4_mixed;
static_assert(sizeof(void *) == 8);
static_assert(sizeof(Cpu) == 40 && sizeof(Common) == 141540 && sizeof(Native) == 159716);
static_assert(alignof(Common) == 1 && alignof(Native) == 1);
static_assert(offsetof(Common,before)==36 && offsetof(Common,after)==76);
static_assert(offsetof(Common,fx_before)==116 && offsetof(Common,fx_after)==628);
static_assert(offsetof(Common,env_before)==2164 && offsetof(Common,env_after)==2192);
static_assert(offsetof(Common,memory_before)==2276 && offsetof(Common,memory_after)==71908);
static_assert(offsetof(Native,state_before)==141540 && offsetof(Native,state_after)==145044);
static_assert(entries.size()==124 && pages.size()==17 && registration_pages.size()==26 && registration_roots.size()==96);
int main(){
  std::printf("{\"pointer_bytes\":%zu,\"State\":%zu,\"Cpu\":%zu,\"Common\":%zu,\"Native\":%zu,\"SpiService\":%zu,",sizeof(void*),sizeof(State),sizeof(Cpu),sizeof(Common),sizeof(Native),sizeof(SpiService));
  std::printf("\"CPU_before\":[%zu,%zu],\"CPU_after\":[%zu,%zu],\"FX_before\":[%zu,%zu],\"FX_after\":[%zu,%zu],",offsetof(Common,before),offsetof(Common,before)+sizeof(Cpu),offsetof(Common,after),offsetof(Common,after)+sizeof(Cpu),offsetof(Common,fx_before),offsetof(Common,fx_before)+512,offsetof(Common,fx_after),offsetof(Common,fx_after)+512);
  std::printf("\"ENV_before\":[%zu,%zu],\"ENV_after\":[%zu,%zu],\"pages_before\":[%zu,%zu],\"pages_after\":[%zu,%zu],",offsetof(Common,env_before),offsetof(Common,env_before)+28,offsetof(Common,env_after),offsetof(Common,env_after)+28,offsetof(Common,memory_before),offsetof(Common,memory_before)+17*4096,offsetof(Common,memory_after),offsetof(Common,memory_after)+17*4096);
  std::printf("\"state_before\":[%zu,%zu],\"state_after\":[%zu,%zu],\"fixed_pages\":%zu,\"external_pages\":%zu,\"selected_roots\":%zu,\"registrations\":%zu}\n",offsetof(Native,state_before),offsetof(Native,state_before)+3504,offsetof(Native,state_after),offsetof(Native,state_after)+3504,pages.size(),registration_pages.size(),entries.size(),registration_roots.size());
}
