// Authored guest-memory/callback fixture: no original code or assets.
#include "../../m4-crt-heap-carry/host/donor_retarget.hpp"
#include <optional>
#include <cstring>
#include <set>
#include <cstdio>
using OverrideMatrix=mw34::donor::Mat;
struct Register{unsigned dword{};};struct State{struct{Register rcx,rsp,rax;}gpr;unsigned rng{};}state;
using Body=void*(*)(State*,unsigned,void*);struct OverrideMxcsr{};
std::vector<unsigned char>memory(0x20000);
void check(bool yes,const char* what){if(!yes)throw std::runtime_error(what);}
bool readable(unsigned at,unsigned size){return at<=memory.size()&&size<=memory.size()-at;}
unsigned load(unsigned at){check(readable(at,4),"fixture read");unsigned v;std::memcpy(&v,memory.data()+at,4);return v;}
void store(unsigned at,unsigned v){check(readable(at,4),"fixture write");std::memcpy(memory.data()+at,&v,4);}
float real(unsigned at){unsigned bits=load(at);float x;std::memcpy(&x,&bits,4);return x;}
void put(unsigned at,float x){unsigned bits;std::memcpy(&bits,&x,4);store(at,bits);}
struct Memory {struct Address{unsigned value;};template<class T>T load(Address a){check(readable(a.value,sizeof(T)),"fixture byte read");T result;std::memcpy(&result,memory.data()+a.value,sizeof(T));return result;}};
struct Runtime{Memory bytes;Memory&memory(){return bytes;}}runtime;
std::map<unsigned,std::string>names;
std::string pose_name(unsigned at,unsigned){return names[at];}
unsigned override_parent(unsigned node){return readable(node,100)&&load(node+0x54)==1?load(load(node+0x58)):0;}
auto override_identity(){return mw34::donor::identity();}
auto override_product(const OverrideMatrix&a,const OverrideMatrix&b){return mw34::donor::product(a,b);}
OverrideMatrix override_matrix(unsigned at){OverrideMatrix m=override_identity();for(unsigned c=0;c<4;++c)for(unsigned r=0;r<3;++r)m[r*4+c]=real(at+4*(c*3+r));return m;}
struct OverrideScope{unsigned root{},model{};std::string owner;};
struct OverrideDonorInstance{mw34::donor::Pose pose;};
struct OverrideState{OverrideScope scope;std::map<unsigned,mw34::donor::Rig>donor_rigs;std::map<std::pair<unsigned,unsigned>,OverrideDonorInstance>donor_poses;}overrides;
auto& override_state(){return overrides;}
struct Model{const char*id;unsigned lod;const char*resource;};
std::vector<Model>models{{"author:added",0,"added"}};
const auto& override_models(){return models;}
void override_load_model(unsigned){}
bool fail_pose{};unsigned solves{};
OverrideDonorInstance& override_donor_pose(){
 ++solves;if(fail_pose)throw std::runtime_error("authored pose fault");
 OverrideDonorInstance value;auto bone=override_identity();bone[3]=1;bone[7]=2;bone[11]=3;value.pose.world.push_back(bone);
 return overrides.donor_poses.emplace(std::make_pair(overrides.scope.root,overrides.scope.model),value).first->second;
}
namespace mw34::chassis{
constexpr unsigned first_runtime_id=32;
struct Socket{std::string node,bone;std::array<double,3>position;};
struct Registration{std::string id,resource,visual_template;std::vector<Socket>sockets;};
std::vector<Registration>records{{"author:added","added","madcat",{{"firepoint02","Muzzle",{0,0,0}}}}};
const auto& configured_catalog(){return records;}
}
struct{std::map<unsigned,unsigned>actor_roots;}additional_chassis;
#include "../../m4-crt-heap-carry/host/chassis_sockets_stage.inc"
constexpr unsigned root=0x1000,node=0x2000,data=0x3000,rootdata=0x4000,weapon=0x5000,stack=0x6000,origin=0x7000,direction=0x7100,mount=0x8000,profile=0xa000,profile_name=0xb000;
void matrix(unsigned at,float x,float y,float z){for(unsigned i=0;i<12;++i)put(at+i*4,(i==0||i==4||i==8)?1.f:0.f);put(at+36,x);put(at+40,y);put(at+44,z);}
bool success=true;
void* original(State*,unsigned,void*){
 if(load(weapon+0x80)==profile) {
  const bool random=load(weapon+0x68)!=0;
  for(unsigned i=0;i<3;++i) {
   const float root_component=real(rootdata+0x30+36+i*4),mount_component=real(data+0x30+36+i*4);
   const float nominal=real(profile+0x14+i*4)+(random?0.f:real(weapon+0x84+i*4));
   const float spread[3]{.25f,-.5f,.75f};put(origin+i*4,root_component+mount_component+nominal+spread[i]);
  }
 }else {put(origin,104.25f);put(origin+4,204.5f);put(origin+8,306.75f);}
 store(direction,0x80000000);store(direction+4,0x3f123456);store(direction+8,0xbf765432);
 state.gpr.rax.dword=success?0xaabbcc01:0xaabbcc00;state.gpr.rsp.dword+=20;state.rng=42;return reinterpret_cast<void*>(123);
}
void run(){state.gpr.rcx.dword=weapon;state.gpr.rsp.dword=stack;store(stack+8,origin);chassis_socket_body(&state,0x4b36e0,nullptr,original);}
int main(){
 names[root]="added";names[node]="firepoint02";
 store(root+0x34,5);store(root+0x38,rootdata);matrix(rootdata+0x30,100,200,300);
 store(node+0x34,5);store(node+0x38,data);matrix(data+0x30,4,5,6);store(node+0x54,1);store(node+0x58,0x9000);store(0x9000,root);
 store(weapon+0x20,node);additional_chassis.actor_roots[root]=32;
 mw34::donor::Bone bone;bone.name="Muzzle";overrides.donor_rigs[0].bones.push_back(bone);
 overrides.scope={77,88,"saved"};OverrideDonorInstance cached;cached.pose.world.push_back(mw34::donor::translate(override_identity(),{999,999,999}));overrides.donor_poses[{root,0}]=cached;
 store(stack+8,origin);original(&state,0,nullptr);const auto original_memory=memory;
 run();
 for(unsigned at=0;at<memory.size();++at)if(at<origin||at>=origin+12)check(memory[at]==original_memory[at],"Adapter wrote outside muzzle origin");
 check(real(origin)==98.25f&&real(origin+4)==202.5f&&real(origin+8)==299.75f,"Fresh donor delta/spread mismatch");
 check(load(direction)==0x80000000&&load(direction+4)==0x3f123456&&load(direction+8)==0xbf765432,"Direction bits changed");
 check(state.gpr.rax.dword==0xaabbcc01&&state.gpr.rsp.dword==stack+20&&state.rng==42,"Original result/ABI/RNG changed");
 check(overrides.scope.root==77&&overrides.scope.owner=="saved"&&overrides.donor_poses.at({root,0}).pose.world[0][3]==999,"Render scope/cache changed");
 check(solves==1,"Stale render pose reused");
 matrix(rootdata+0x30,101,200,300);run();check(solves==2,"Physics pose not refreshed");
 store(weapon+0x20,0);store(weapon+0x24,mount);store(weapon+0x80,profile);store(mount+8,node);
 names[node]="rhand";store(profile,profile_name);std::memcpy(memory.data()+profile_name,"firepoint01",12);
 mw34::chassis::records[0].sockets[0].node="firepoint01";
 put(profile+0x14,2);put(profile+0x18,3);put(profile+0x1c,4);
 put(weapon+0x84,1);put(weapon+0x88,-2);put(weapon+0x8c,.5f);
 store(weapon,0x5c9088);run();check(solves==3,"Profile rhand path missed");
 check(real(origin)==99.25f&&real(origin+4)==202.5f&&real(origin+8)==299.75f,"Nominal profile/fixed offsets counted twice");
 store(weapon,0x5c90c0);names[node]="lhand";run();check(solves==4&&real(origin)==99.25f,"Beam profile did not share muzzle adapter");
 store(weapon+0x68,1);run();check(solves==5&&real(origin+8)==299.75f,"Random spread path incorrectly subtracted fixed offsets");
 store(weapon+0x68,0);
 success=false;run();check(solves==5&&real(origin)==108.25f,"Failed original modified");success=true;
 additional_chassis.actor_roots.clear();run();check(solves==5&&real(origin)==108.25f,"Stock actor modified");additional_chassis.actor_roots[root]=32;
 std::memcpy(memory.data()+profile_name,"unmapped000",12);run();check(solves==5,"Unmapped profile modified");std::memcpy(memory.data()+profile_name,"firepoint01",12);
 fail_pose=true;bool failed=false;try{run();}catch(const std::runtime_error&){failed=true;}
 check(failed&&overrides.scope.root==77&&overrides.donor_poses.at({root,0}).pose.world[0][3]==999,"Pose exception leaked scope/cache");
 check(real(origin)==108.25f&&state.gpr.rax.dword==0xaabbcc01&&state.rng==42,"Fault changed original result");
 fail_pose=false;
 auto fault_without_write=[&](){bool rejected=false;try{run();}catch(const std::runtime_error&){rejected=true;}check(rejected&&real(origin)==108.25f,"Invalid profile accepted or changed origin");};
 memory[profile_name+3]=1;fault_without_write();std::memcpy(memory.data()+profile_name,"firepoint01",12);
 store(profile+0x14,0x7f800000);bool nonfinite=false;try{run();}catch(const std::runtime_error&){nonfinite=true;}
 check(nonfinite&&std::isinf(real(origin)),"Nonfinite nominal offset accepted");put(profile+0x14,2);
 std::memcpy(memory.data()+memory.size()-4,"fire",4);store(profile,unsigned(memory.size()-4));fault_without_write();store(profile,profile_name);
 std::puts("Pack socket checks passed: origin-only delta, spread/direction/ABI/RNG, fresh pose, scope/cache cleanup and stock/profile paths.");
}
