// Asset-free tests for the optional visual solver. No game inputs or guest state.
#include "donor_retarget.hpp"
#include <iostream>
#include <limits>

using namespace mw34::donor;
unsigned checks=0;
void check(bool value,const char*label){++checks;if(!value)throw std::runtime_error(label);}
double error(const Mat&a,const Mat&b){double e=0;for(unsigned i=0;i<16;++i)e=std::max(e,std::abs(a[i]-b[i]));return e;}
Rig fixture(){
 Rig r;
 auto bone=[&](const char*name,const char*control,int parent,Vec p){r.bones.push_back({name,control,parent,translate(identity(),p)});r.reference.emplace(control,r.bones.back().rest);};
 bone("Pelvis","hip",-1,{0,0,4});bone("Torso_Twist","torso",0,{0,0,5});
 bone("Upperarm_Left","larm",1,{0,2,5});bone("Forearm_Left","lhand",2,{1,2,4});
 bone("Upperarm_Right","rarm",1,{0,-2,5});bone("Forearm_Right","rhand",4,{1,-2,4});
 bone("Thigh_Left","lthigh",0,{0,1,4});bone("Calf_Left","lcalf",6,{1,1,2});bone("Foot0_Left","lfoot",7,{0,1,.5});
 bone("Thigh_Right","rthigh",0,{0,-1,4});bone("Calf_Right","rcalf",9,{1,-1,2});bone("Foot0_Right","rfoot",10,{0,-1,.5});
 r.walk_z={.5,.5};return r;
}
void lengths(const Rig&r,const Pose&p){for(auto edge:std::array<std::pair<unsigned,unsigned>,4>{{{6,7},{7,8},{9,10},{10,11}}}){
 check(std::abs(length(sub(position(r.bones[edge.first].rest),position(r.bones[edge.second].rest)))-length(sub(position(p.world[edge.first]),position(p.world[edge.second]))))<1e-9,"fixed donor limb length");}}
int main(){try{
 auto r=fixture();const auto original=r.reference;auto p=retarget(r,original,0);check(!p.reach_clamps,"stand reachable");
 for(size_t i=0;i<r.bones.size();++i)check(error(p.world[i],r.bones[i].rest)<1e-9,"stand matches donor rest");
 check(r.reference==original,"reference transforms unchanged");check(locomotion(r,original)==0,"stand gait blend zero");
 auto walking=original;walking.at("lfoot")[3]=.35;walking.at("lfoot")[11]+=.2;walking.at("rfoot")[3]=-.35;
 p=retarget(r,walking,1);lengths(r,p);check(!p.reach_clamps,"ordinary stride reachable");check(locomotion(r,walking)==1,"stride gait blend one");
 auto moved=walking;for(auto&[name,m]:moved)m=translate(m,add(position(m),{7,-3,0}));auto q=retarget(r,moved,1);
 for(size_t i=0;i<p.world.size();++i)check(error(q.world[i],translate(p.world[i],add(position(p.world[i]),{7,-3,0})))<1e-9,"root travel restored without changing stride");
 walking.at("lfoot")[3]=100;p=retarget(r,walking,1);check(p.reach_clamps>0,"unreachable visual goal explicitly clamped");lengths(r,p);
 auto m=identity();m[0]=m[5]=m[10]=.6;m=translate(m,{2,-3,7});check(error(product(m,inverse(m)),identity())<1e-9,"scaled affine inverse");
 check(length(sub(vector(swing({1,0,0},{-1,0,0}),{1,0,0}),{-1,0,0}))<1e-9,"opposite-direction swing finite");
 bool rejected=false;try{retarget(r,original,std::numeric_limits<double>::quiet_NaN());}catch(const std::runtime_error&){rejected=true;}check(rejected,"NaN gait rejected");
 rejected=false;try{auto singular=identity();singular[0]=0;inverse(singular);}catch(const std::runtime_error&){rejected=true;}check(rejected,"singular affine matrix rejected");
 std::cout<<"donor retarget checks="<<checks<<" failures=0\n";return 0;
 }catch(const std::exception&e){std::cerr<<"donor retarget failure: "<<e.what()<<'\n';return 1;}}
