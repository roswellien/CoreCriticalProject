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
Rig hinged_fixture(){
 auto r=fixture();r.hinge_axes=true;
 auto helper=[&](const std::string&name,int parent,Vec p){r.bones.push_back({name,"",parent,translate(identity(),p)});};
 for(const auto&side:std::array<std::string,2>{"Left","Right"}){
  const bool left=side=="Left";const int thigh=left?6:9,calf=left?7:10,foot=left?8:11,arm=left?2:4,forearm=left?3:5;
  helper("HingeAxis_Calf_"+side,thigh,position(r.bones[static_cast<std::size_t>(calf)].rest));
  helper("HingeAxis_Foot0_"+side,calf,position(r.bones[static_cast<std::size_t>(foot)].rest));
  helper("HingeAxis_Forearm_"+side,arm,position(r.bones[static_cast<std::size_t>(forearm)].rest));
  helper("KneeHousing_"+side,thigh,position(r.bones[static_cast<std::size_t>(calf)].rest));
  for(int i=0;i<4;++i)helper("Sole_"+side+"_"+std::to_string(i),foot,{(i&1)?.8:-.8,(left?1.:-1.)+((i&2)?.3:-.3),0});
 }
 return r;
}
void hinge_checks(){
 auto r=hinged_fixture();const auto original=r.reference;const auto stand=retarget(r,original,0);
 for(size_t i=0;i<r.bones.size();++i)check(error(stand.world[i],r.bones[i].rest)<1e-9,"hinged stand retains every rest frame");
 for(int sample=0;sample<40;++sample){
  auto pose=original;const double t=sample*.157;
  for(const auto&name:std::array<std::string,2>{"lfoot","rfoot"}){
   pose.at(name)[3]+=.3*std::sin(t);pose.at(name)[7]+=.4*std::cos(t);pose.at(name)[11]+=.25;
   pose.at(name)=translate(product(hinge_rotation({0,1,0},.2*std::sin(t)),rotation(pose.at(name))),position(pose.at(name)));
  }
  // Intentionally request a compound elbow rotation; its hinge must reject twist.
  pose.at("lhand")=translate(product(hinge_rotation({1,0,0},.4),hinge_rotation({0,1,0},.5)),position(pose.at("lhand")));
  const auto p=retarget(r,pose,1);lengths(r,p);
  for(auto edge:std::array<std::pair<unsigned,unsigned>,6>{{{6,7},{9,10},{2,3},{4,5},{7,8},{10,11}}})
   check(length(sub(vector(p.world[edge.first],{0,1,0}),vector(p.world[edge.second],{0,1,0})))<1e-9,"measured hinge axle stays coaxial");
  for(size_t i=0;i<r.bones.size();++i)if(r.bones[i].name.rfind("Sole_",0)==0)
   check(position(p.world[i])[2]>=-1e-8,"footprint contact does not penetrate ground");
  auto moved=pose;for(auto&[name,m]:moved)m=translate(m,add(position(m),{4,-2,0}));const auto q=retarget(r,moved,1);
  for(size_t i=0;i<p.world.size();++i)check(error(q.world[i],translate(p.world[i],add(position(p.world[i]),{4,-2,0})))<1e-9,"hinged root travel remains controller driven");
 }
 // A tall controller swing must not pull a short donor's knee up to its hip.
 auto marching=original;marching.at("lfoot")[11]+=3.;marching.at("rfoot")[11]+=3.;
 const auto low_step=retarget(r,marching,1);
 for(auto side:std::array<std::array<unsigned,3>,2>{{{6,7,8},{9,10,11}}}){
  const double leg=length(sub(position(r.bones[side[0]].rest),position(r.bones[side[1]].rest)))+length(sub(position(r.bones[side[1]].rest),position(r.bones[side[2]].rest)));
  double minimum=1e300;
  for(size_t i=0;i<r.bones.size();++i)if(r.bones[i].parent==static_cast<int>(side[2])&&r.bones[i].name.rfind("Sole_",0)==0)minimum=std::min(minimum,position(low_step.world[i])[2]);
  check(minimum>0&&minimum<=.08*leg+1e-8,"controller lift is bounded to donor leg proportions");
  check(position(low_step.world[side[1]])[2]<position(low_step.world[side[0]])[2]-.5,"walking knee remains below the hip");
 }
 // A long stride must retain the clearance needed to avoid a new reach clamp.
 auto long_stride=marching;long_stride.at("lfoot")[3]=3.;
 const auto long_step=retarget(r,long_stride,1);lengths(r,long_step);
 check(!long_step.reach_clamps,"long strides retain necessary controller clearance");
 // An oblique, valid ankle frame exposed an oscillating contact solve. Never
 // silently return that last pose with penetrated soles and no reach warning.
 auto oblique=r;
 for(auto&bone:oblique.bones)if(bone.name=="HingeAxis_Foot0_Left")
  bone.rest=translate(product(hinge_rotation({1,0,0},.7),hinge_rotation({0,0,1},.7)),position(bone.rest));
 auto adverse=original;
 adverse.at("lfoot")=translate(product(product(hinge_rotation({1,0,0},-1.2604103704185106),hinge_rotation({0,1,0},-.28769548245009124)),hinge_rotation({0,0,1},-.44237892405550272)),{-.18757766967971279,1.65310343749380917,.5});
 const auto oblique_pose=retarget(oblique,adverse,0);
 double oblique_floor=1e300;
 for(size_t i=0;i<oblique.bones.size();++i)if(oblique.bones[i].name.rfind("Sole_Left_",0)==0)
  oblique_floor=std::min(oblique_floor,position(oblique_pose.world[i])[2]);
 check(std::abs(oblique_floor)<1e-8,"oblique contact converges instead of oscillating below ground");
 auto impossible=original;impossible.at("hip")[11]+=100.;
 bool unresolved=false;
 try{retarget(r,impossible,0);}catch(const std::runtime_error&e){unresolved=std::string(e.what()).find("contact did not converge")!=std::string::npos;}
 check(unresolved,"impossible contact is rejected instead of silently penetrating");
 check(r.reference==original,"hinged solver does not change original controller inputs");
 for(int kind=0;kind<3;++kind){auto invalid=r;
  if(kind==0)invalid.bones[12].name="MissingAxis";
  if(kind==1)invalid.bones[16].parent=0;
  if(kind==2)invalid.bones.resize(18);
  bool rejected=false;try{retarget(invalid,original,0);}catch(const std::exception&){rejected=true;}
  check(rejected,"malformed hinge metadata rejected");
 }
}
int main(){try{
 hinge_checks();
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
