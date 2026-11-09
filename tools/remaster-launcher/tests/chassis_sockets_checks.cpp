// Authored guest-memory/callback fixture: no original code or assets.
#include "../../m4-crt-heap-carry/host/donor_retarget.hpp"
#include <array>
#include <cmath>
#include <cstdint>
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
// A settable read-only range stands in for guest memory the stage may read but not write.
unsigned readonly_begin{},readonly_end{};
bool writable(unsigned at,unsigned size){
 const bool touches_readonly=at<readonly_end&&readonly_begin<at+size;
 return readable(at,size)&&!touches_readonly;
}
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
constexpr unsigned root=0x1000,node=0x2000,data=0x3000,rootdata=0x4000,weapon=0x5000,stack=0x6000,origin=0x7000,direction=0x7100,aim=0x7200,mount=0x8000,profile=0xa000,profile_name=0xb000;
void matrix(unsigned at,float x,float y,float z){for(unsigned i=0;i<12;++i)put(at+i*4,(i==0||i==4||i==8)?1.f:0.f);put(at+36,x);put(at+40,y);put(at+44,z);}
bool success=true,throw_inside{},move_torso{};
unsigned original_calls{},aim_pointer=aim,seen_aim_pointer{};std::array<float,3>seen_aim{};
// Guest address 0 as the original saw it: a null aim point must not be shifted in place, even
// if it would be put back afterwards.
bool low_memory_zero_during_call{};
// Stands in for 0x4B36E0: muzzle from the nominal firepoint plus spread, then the shot
// direction from that muzzle to whatever the caller's aim point holds while it runs.
void* original(State*,unsigned,void*){
 ++original_calls;
 seen_aim_pointer=load(stack+4);
 low_memory_zero_during_call=load(0)==0&&load(4)==0&&load(8)==0;
 if(seen_aim_pointer)for(unsigned i=0;i<3;++i)seen_aim[i]=real(seen_aim_pointer+4*i);
 if(throw_inside)throw std::runtime_error("authored original fault");
 // 0x4ED280 brings a changed torso node up to date inside the original call.
 if(move_torso)put(data+0x30+36,real(data+0x30+36)+3.f);
 if(load(weapon+0x80)==profile) {
  const bool random=load(weapon+0x68)!=0;
  for(unsigned i=0;i<3;++i) {
   const float root_component=real(rootdata+0x30+36+i*4),mount_component=real(data+0x30+36+i*4);
   const float nominal=real(profile+0x14+i*4)+(random?0.f:real(weapon+0x84+i*4));
   const float spread[3]{.25f,-.5f,.75f};put(origin+i*4,root_component+mount_component+nominal+spread[i]);
  }
 }else {put(origin,104.25f);put(origin+4,204.5f);put(origin+8,306.75f);}
 if(seen_aim_pointer) {
  std::array<double,3> toward_aim{};double length=0;
  for(unsigned i=0;i<3;++i){toward_aim[i]=double(seen_aim[i])-real(origin+4*i);length+=toward_aim[i]*toward_aim[i];}
  length=std::sqrt(length);
  for(unsigned i=0;i<3;++i)put(direction+4*i,float(toward_aim[i]/length));
 }else {store(direction,0x80000000);store(direction+4,0x3f123456);store(direction+8,0xbf765432);}
 state.gpr.rax.dword=success?0xaabbcc01:0xaabbcc00;state.gpr.rsp.dword+=20;state.rng=42;return reinterpret_cast<void*>(123);
}
void run(){state.gpr.rcx.dword=weapon;state.gpr.rsp.dword=stack;store(stack+4,aim_pointer);store(stack+8,origin);store(stack+12,direction);chassis_socket_body(&state,0x4b36e0,nullptr,original);}
bool aim_holds(){return real(aim)==500.f&&real(aim+4)==600.f&&real(aim+8)==700.f;}
bool saw_aim(float x,float y,float z){return seen_aim[0]==x&&seen_aim[1]==y&&seen_aim[2]==z;}
bool saw_unshifted_aim(){return seen_aim_pointer==aim&&saw_aim(500.f,600.f,700.f);}
// The direction the original wrote, compared with the line from the final (socket) muzzle
// to the caller's real aim point; float rounding of the shifted aim point allows 1e-5.
bool aims_from_muzzle(){
 std::array<double,3> toward_aim{};double length=0;
 for(unsigned i=0;i<3;++i){toward_aim[i]=double(real(aim+4*i))-real(origin+4*i);length+=toward_aim[i]*toward_aim[i];}
 length=std::sqrt(length);
 for(unsigned i=0;i<3;++i)if(std::fabs(real(direction+4*i)-toward_aim[i]/length)>1e-5)return false;
 return true;
}
void run_checks(){
 names[root]="added";names[node]="firepoint02";
 store(root+0x34,5);store(root+0x38,rootdata);matrix(rootdata+0x30,100,200,300);
 store(node+0x34,5);store(node+0x38,data);matrix(data+0x30,4,5,6);store(node+0x54,1);store(node+0x58,0x9000);store(0x9000,root);
 store(weapon+0x20,node);additional_chassis.actor_roots[root]=32;
 mw34::donor::Bone bone;bone.name="Muzzle";overrides.donor_rigs[0].bones.push_back(bone);
 overrides.scope={77,88,"saved"};OverrideDonorInstance cached;cached.pose.world.push_back(mw34::donor::translate(override_identity(),{999,999,999}));overrides.donor_poses[{root,0}]=cached;
 put(aim,500.f);put(aim+4,600.f);put(aim+8,700.f);
 store(stack+4,aim);store(stack+8,origin);store(stack+12,direction);original(&state,0,nullptr);const auto original_memory=memory;
 run();
 check(aim_holds(),"Aim point not restored");
 // The direction bytes differ by design: the fake writes them from the shifted aim point.
 for(unsigned at=0;at<memory.size();++at) {
  const bool muzzle_or_direction=(at>=origin&&at<origin+12)||(at>=direction&&at<direction+12);
  if(!muzzle_or_direction)check(memory[at]==original_memory[at],"Adapter wrote outside muzzle origin");
 }
 check(real(origin)==98.25f&&real(origin+4)==202.5f&&real(origin+8)==299.75f,"Fresh donor delta/spread mismatch");
 check(aims_from_muzzle(),"Direction not aimed from the socket barrel");
 check(state.gpr.rax.dword==0xaabbcc01&&state.gpr.rsp.dword==stack+20&&state.rng==42,"Original result/ABI/RNG changed");
 check(overrides.scope.root==77&&overrides.scope.owner=="saved"&&overrides.donor_poses.at({root,0}).pose.world[0][3]==999,"Render scope/cache changed");
 // Two fresh pose solves per successful call: one to aim before the original, one for the muzzle after it.
 check(solves==2,"Stale render pose reused");
 matrix(rootdata+0x30,101,200,300);run();check(solves==4,"Physics pose not refreshed");
 store(weapon+0x20,0);store(weapon+0x24,mount);store(weapon+0x80,profile);store(mount+8,node);
 names[node]="rhand";store(profile,profile_name);std::memcpy(memory.data()+profile_name,"firepoint01",12);
 mw34::chassis::records[0].sockets[0].node="firepoint01";
 put(profile+0x14,2);put(profile+0x18,3);put(profile+0x1c,4);
 put(weapon+0x84,1);put(weapon+0x88,-2);put(weapon+0x8c,.5f);
 store(weapon,0x5c9088);run();check(solves==6,"Profile rhand path missed");
 check(real(origin)==99.25f&&real(origin+4)==202.5f&&real(origin+8)==299.75f,"Nominal profile/fixed offsets counted twice");
 store(weapon,0x5c90c0);names[node]="lhand";run();check(solves==8&&real(origin)==99.25f,"Beam profile did not share muzzle adapter");
 store(weapon+0x68,1);run();check(solves==10&&real(origin+8)==299.75f,"Random spread path incorrectly subtracted fixed offsets");
 store(weapon+0x68,0);
 success=false;run();check(solves==11&&real(origin)==108.25f&&aim_holds(),"Failed original modified");success=true;
 additional_chassis.actor_roots.clear();run();check(solves==11&&real(origin)==108.25f&&saw_unshifted_aim(),"Stock actor modified");additional_chassis.actor_roots[root]=32;
 std::memcpy(memory.data()+profile_name,"unmapped000",12);run();check(solves==11&&saw_unshifted_aim(),"Unmapped profile modified");std::memcpy(memory.data()+profile_name,"firepoint01",12);
 fail_pose=true;bool failed=false;const unsigned calls_before_fault=original_calls;try{run();}catch(const std::runtime_error&){failed=true;}
 check(failed&&overrides.scope.root==77&&overrides.donor_poses.at({root,0}).pose.world[0][3]==999,"Pose exception leaked scope/cache");
 check(original_calls==calls_before_fault&&real(origin)==108.25f&&aim_holds(),"Pose fault ran the original or touched its outputs");
 fail_pose=false;
 auto fault_without_write=[&](){bool rejected=false;try{run();}catch(const std::runtime_error&){rejected=true;}check(rejected&&real(origin)==108.25f&&aim_holds(),"Invalid profile accepted or changed origin");};
 memory[profile_name+3]=1;fault_without_write();std::memcpy(memory.data()+profile_name,"firepoint01",12);
 store(profile+0x14,0x7f800000);bool nonfinite=false;try{run();}catch(const std::runtime_error&){nonfinite=true;}
 check(nonfinite&&real(origin)==108.25f&&aim_holds(),"Nonfinite nominal offset accepted");put(profile+0x14,2);
 std::memcpy(memory.data()+memory.size()-4,"fire",4);store(profile,unsigned(memory.size()-4));fault_without_write();store(profile,profile_name);
 run();check(real(origin)==99.25f&&real(origin+4)==202.5f&&real(origin+8)==299.75f&&aims_from_muzzle(),"Profile path not aimed from the socket barrel");
 throw_inside=true;bool original_fault=false;try{run();}catch(const std::runtime_error&){original_fault=true;}throw_inside=false;
 check(original_fault&&!saw_aim(500.f,600.f,700.f)&&aim_holds(),"Aim point not restored after an original fault");
 aim_pointer=0;run();aim_pointer=aim;
 check(seen_aim_pointer==0&&low_memory_zero_during_call&&load(direction)==0x80000000&&load(direction+4)==0x3f123456,"Null aim point touched");
 readonly_begin=aim;readonly_end=aim+12;run();readonly_begin=readonly_end=0;
 check(saw_unshifted_aim()&&aim_holds(),"Read-only aim point shifted");
 const float muzzle_before[3]{real(origin),real(origin+4),real(origin+8)};
 aim_pointer=origin;run();aim_pointer=aim;
 check(saw_aim(muzzle_before[0],muzzle_before[1],muzzle_before[2]),"Aim point overlapping the muzzle shifted");
 // The fake moves the torso during the call; the muzzle must use the delta computed after it.
 // Only the muzzle is checked here: the aim uses the pose from before the call by design.
 move_torso=true;run();move_torso=false;matrix(data+0x30,4,5,6);
 check(real(origin)==99.25f&&real(origin+4)==202.5f&&real(origin+8)==299.75f,"Muzzle used a stale torso pose");
 store(mount+8,0);const unsigned solves_before_null=solves;run();store(mount+8,node);
 check(solves==solves_before_null&&saw_unshifted_aim()&&aim_holds(),"Null node touched the aim point");
 std::puts("Pack socket checks passed: aim from the socket barrel, aim point restored, origin-only delta, spread/ABI/RNG, fresh pose, scope/cache cleanup and stock/profile paths.");
}
// Name the failing check: an uncaught exception would end the run without its message.
int main(){
 try{run_checks();}
 catch(const std::exception& failure){std::printf("Pack socket check failed: %s\n",failure.what());return 1;}
 return 0;
}
