// Optional visual retarget only. Original simulation, joints and weapon origins are read-only.
#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

namespace mw34::donor {
using Vec=std::array<double,3>;
using Mat=std::array<double,16>;
inline Mat identity(){return {1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};}
inline Vec add(Vec a,Vec b){for(std::size_t i=0;i<3;++i)a[i]+=b[i];return a;}
inline Vec sub(Vec a,Vec b){for(std::size_t i=0;i<3;++i)a[i]-=b[i];return a;}
inline Vec scale(Vec a,double s){for(auto&v:a)v*=s;return a;}
inline double dot(Vec a,Vec b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
inline double length(Vec a){return std::sqrt(dot(a,a));}
inline Vec unit(Vec a){const auto n=length(a);if(n<1e-10)throw std::runtime_error("Visual retarget: degenerate vector");return scale(a,1/n);}
inline Vec cross(Vec a,Vec b){return {a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};}
inline Vec position(const Mat&m){return {m[3],m[7],m[11]};}
inline Mat translate(Mat m,Vec p){for(std::size_t i=0;i<3;++i)m[4*i+3]=p[i];return m;}
inline Mat product(const Mat&a,const Mat&b){Mat m{};for(std::size_t i=0;i<4;++i)for(std::size_t j=0;j<4;++j)for(std::size_t k=0;k<4;++k)m[i*4+j]+=a[i*4+k]*b[k*4+j];return m;}
inline Vec vector(const Mat&m,Vec p){return {m[0]*p[0]+m[1]*p[1]+m[2]*p[2],m[4]*p[0]+m[5]*p[1]+m[6]*p[2],m[8]*p[0]+m[9]*p[1]+m[10]*p[2]};}
inline Vec point(const Mat&m,Vec p){return add(vector(m,p),position(m));}
inline Mat inverse(const Mat&m){
 const double d=m[0]*(m[5]*m[10]-m[6]*m[9])-m[1]*(m[4]*m[10]-m[6]*m[8])+m[2]*(m[4]*m[9]-m[5]*m[8]);
 if(!std::isfinite(d)||std::abs(d)<1e-12)throw std::runtime_error("Visual retarget: singular affine matrix");
 auto r=identity();r[0]=(m[5]*m[10]-m[6]*m[9])/d;r[1]=(m[2]*m[9]-m[1]*m[10])/d;r[2]=(m[1]*m[6]-m[2]*m[5])/d;
 r[4]=(m[6]*m[8]-m[4]*m[10])/d;r[5]=(m[0]*m[10]-m[2]*m[8])/d;r[6]=(m[2]*m[4]-m[0]*m[6])/d;
 r[8]=(m[4]*m[9]-m[5]*m[8])/d;r[9]=(m[1]*m[8]-m[0]*m[9])/d;r[10]=(m[0]*m[5]-m[1]*m[4])/d;
 return translate(r,scale(vector(r,position(m)),-1));
}
inline Mat rotation(const Mat&m){auto r=identity();for(std::size_t c=0;c<3;++c){auto v=unit({m[c],m[4+c],m[8+c]});for(std::size_t i=0;i<3;++i)r[4*i+c]=v[i];}return r;}
inline Mat swing(Vec a,Vec b){
 a=unit(a);b=unit(b);const double c=std::clamp(dot(a,b),-1.,1.);auto v=cross(a,b);auto r=identity();
 if(c<-.999999){auto axis=unit(cross(a,std::abs(a[0])<.8?Vec{1,0,0}:Vec{0,1,0}));for(std::size_t i=0;i<3;++i)for(std::size_t j=0;j<3;++j)r[i*4+j]=2*axis[i]*axis[j]-(i==j?1.:0.);return r;}
 const double k=1/(1+c);const double vv[3][3]={{0,-v[2],v[1]},{v[2],0,-v[0]},{-v[1],v[0],0}};
 for(std::size_t i=0;i<3;++i)for(std::size_t j=0;j<3;++j){r[4*i+j]+=vv[i][j];for(std::size_t t=0;t<3;++t)r[4*i+j]+=vv[i][t]*vv[t][j]*k;}
 return r;
}
inline Mat axis(){return {0,0,-1,0,-1,0,0,0,0,1,0,0,0,0,0,1};}
struct Bone{std::string name,control;int parent{-1};Mat rest=identity();};
struct Rig{std::vector<Bone>bones;std::map<std::string,Mat>reference;std::array<double,2>walk_x{},walk_z{};double hip_drop{};bool ground_reference=true;bool hinge_axes=false;bool shoulder_limits=false;};
struct Pose{std::vector<Mat>world;unsigned reach_clamps{};};
inline double locomotion(const Rig&r,const std::map<std::string,Mat>&current){
 const auto h=position(current.at("hip")),h0=position(r.reference.at("hip"));double change=0;
 for(const char*name:{"lfoot","rfoot","lthigh","rthigh"}){const auto it=current.find(name);if(it==current.end())continue;
  change=std::max(change,length(sub(sub(position(it->second),h),sub(position(r.reference.at(name)),h0))));
  for(const auto i:std::array<std::size_t,9>{0,1,2,4,5,6,8,9,10})change=std::max(change,std::abs(it->second[i]-r.reference.at(name)[i]));
 }
 const double t=std::clamp((change-.005)/.075,0.,1.);return t*t*(3-2*t);
}
inline Mat hinge_rotation(Vec axis, double angle) {
 axis=unit(axis); const double c=std::cos(angle),s=std::sin(angle),v=1-c;
 auto result=identity();
 for(std::size_t i=0;i<3;++i)for(std::size_t j=0;j<3;++j)result[4*i+j]=v*axis[i]*axis[j]+(i==j?c:0.);
 result[1]-=s*axis[2];result[2]+=s*axis[1];result[4]+=s*axis[2];
 result[6]-=s*axis[0];result[8]-=s*axis[1];result[9]+=s*axis[0];
 return result;
}
inline double hinge_angle(Vec axis,Vec from,Vec to) {
 axis=unit(axis);from=sub(from,scale(axis,dot(axis,from)));to=sub(to,scale(axis,dot(axis,to)));
 if(length(from)<1e-10||length(to)<1e-10)return 0.;
 from=unit(from);to=unit(to);
 return std::atan2(dot(axis,cross(from,to)),std::clamp(dot(from,to),-1.,1.));
}
inline Vec hinge_axis(const Mat&frame) { return unit({frame[1],frame[5],frame[9]}); }
inline Mat hinge_constrained(const Mat&rest,const Mat&desired,const Mat&parent_delta,
                             const Mat&frame,Vec origin) {
 const auto relative=product(inverse(rotation(parent_delta)),product(rotation(desired),inverse(rotation(rest))));
 const auto axis=hinge_axis(frame);const Vec direction{frame[2],frame[6],frame[10]};
 const auto angle=hinge_angle(axis,direction,vector(relative,direction));
 return translate(product(parent_delta,product(hinge_rotation(axis,angle),rest)),origin);
}
inline void validate_shoulder_metadata(const Rig&rig) {
 if(!rig.shoulder_limits)return;
 if(!rig.hinge_axes)throw std::runtime_error("Visual retarget: shoulder limits require measured hinges");
 std::map<std::string,const Bone*> bones;
 for(const auto&bone:rig.bones)if(!bones.emplace(bone.name,&bone).second)
  throw std::runtime_error("Visual retarget: duplicate shoulder bone");
 for(const char*side:{"Left","Right"}) {
  const std::string upper_name="Upperarm_"+std::string(side);
  const auto&upper=*bones.at(upper_name);
  const auto&axis_frame=*bones.at("HingeAxis_"+upper_name);
  const auto&minimum=*bones.at("HingeMin_"+upper_name);
  const auto&maximum=*bones.at("HingeMax_"+upper_name);
  if(upper.parent<0||upper.parent>=int(rig.bones.size())||
     rig.bones[static_cast<std::size_t>(upper.parent)].name!="Torso_Twist")
   throw std::runtime_error("Visual retarget: invalid shoulder parent");
  for(double value:upper.rest)if(!std::isfinite(value))
   throw std::runtime_error("Visual retarget: nonfinite shoulder rest");
  for(const auto*marker:{&axis_frame,&minimum,&maximum}) {
   if(!marker->control.empty()||marker->parent<0||marker->parent>=int(rig.bones.size())||
      rig.bones[static_cast<std::size_t>(marker->parent)].name!="Torso_Twist")
    throw std::runtime_error("Visual retarget: invalid shoulder marker parent");
   for(double value:marker->rest)if(!std::isfinite(value))
    throw std::runtime_error("Visual retarget: nonfinite shoulder marker");
   if(marker->rest[12]!=0||marker->rest[13]!=0||marker->rest[14]!=0||marker->rest[15]!=1)
    throw std::runtime_error("Visual retarget: nonaffine shoulder marker");
   inverse(marker->rest);
   if(length(sub(position(marker->rest),position(upper.rest)))>1e-7)
    throw std::runtime_error("Visual retarget: shoulder marker is outside its socket");
  }
  const auto axis=hinge_axis(axis_frame.rest);
  const auto guide=unit({axis_frame.rest[2],axis_frame.rest[6],axis_frame.rest[10]});
  if(std::abs(dot(axis,guide))>1e-6)
   throw std::runtime_error("Visual retarget: invalid shoulder guide");
  for(const auto*marker:{&minimum,&maximum}) {
   const auto direction=unit({marker->rest[2],marker->rest[6],marker->rest[10]});
   if(std::abs(dot(axis,direction))>1e-6||dot(axis,hinge_axis(marker->rest))<1.-1e-6)
    throw std::runtime_error("Visual retarget: inconsistent shoulder limit axis");
  }
  const double lower=hinge_angle(axis,guide,{minimum.rest[2],minimum.rest[6],minimum.rest[10]});
  const double higher=hinge_angle(axis,guide,{maximum.rest[2],maximum.rest[6],maximum.rest[10]});
  constexpr double pi=3.14159265358979323846;
  if(lower>=-1e-6||higher<=1e-6||lower<=-pi+1e-4||higher>=pi-1e-4)
   throw std::runtime_error("Visual retarget: invalid shoulder motion envelope");
 }
}
inline Mat shoulder_constrained(const Mat&rest,const Mat&desired,const Mat&parent_delta,
                                const Mat&frame,const Mat&minimum,const Mat&maximum,Vec origin) {
 const auto axis=hinge_axis(frame);
 const Vec guide{frame[2],frame[6],frame[10]};
 const auto relative=product(inverse(rotation(parent_delta)),product(rotation(desired),inverse(rotation(rest))));
 const double requested=hinge_angle(axis,guide,vector(relative,guide));
 const double lower=hinge_angle(axis,guide,{minimum[2],minimum[6],minimum[10]});
 const double higher=hinge_angle(axis,guide,{maximum[2],maximum[6],maximum[10]});
 return translate(product(parent_delta,product(hinge_rotation(axis,std::clamp(requested,lower,higher)),rest)),origin);
}
// Metadata frames/points describe existing rigid surfaces; they draw no geometry.
inline void validate_hinge_metadata(const Rig&r) {
 validate_shoulder_metadata(r);
 std::map<std::string,const Bone*> bones;
 for(const auto&bone:r.bones)bones.emplace(bone.name,&bone);
 for(const auto&side:std::array<std::string,2>{"Left","Right"}) {
  for(const auto&joint:std::array<std::pair<std::string,std::string>,3>{{{"Calf_","Thigh_"},{"Forearm_","Upperarm_"},{"Foot0_","Calf_"}}}) {
   const auto found=bones.find("HingeAxis_"+joint.first+side);
   if(found==bones.end())throw std::runtime_error("Visual retarget: missing measured hinge axis");
   const auto&bone=*found->second;
   if(!bone.control.empty()||bone.parent<0||bone.parent>=int(r.bones.size())||r.bones[static_cast<std::size_t>(bone.parent)].name!=joint.second+side)
    throw std::runtime_error("Visual retarget: invalid hinge frame parent");
   const auto axis=hinge_axis(bone.rest);const Vec guide{bone.rest[2],bone.rest[6],bone.rest[10]};
   if(length(cross(axis,guide))<1e-8)throw std::runtime_error("Visual retarget: degenerate hinge guide");
  }
  unsigned points=0;const std::string prefix=side=="Left"?"l":"r";
  for(const auto&bone:r.bones)if(bone.name.rfind("Sole_"+side+"_",0)==0) {
   if(!bone.control.empty()||bone.parent<0||bone.parent>=int(r.bones.size()))
    throw std::runtime_error("Visual retarget: invalid sole parent");
   const auto&parent=r.bones[static_cast<std::size_t>(bone.parent)];
   if(parent.control!=prefix+"foot"&&parent.control!=prefix+"toe01"&&parent.control!=prefix+"toe02")
    throw std::runtime_error("Visual retarget: sole must bind to its foot or toe");
   ++points;
  }
  if(points<3||points>64)throw std::runtime_error("Visual retarget: invalid sole marker count");
 }
}
inline Pose retarget_hinged(const Rig&r,std::map<std::string,Mat>current,double gait) {
 validate_hinge_metadata(r);
 std::map<std::string,size_t> index;
 for(size_t i=0;i<r.bones.size();++i)if(!index.emplace(r.bones[i].name,i).second)
  throw std::runtime_error("Visual retarget: duplicate bone");
 auto rest=[&](const std::string&name)->const Mat& {return r.bones.at(index.at(name)).rest;};
 for(const char*name:{"HingeAxis_Calf_Left","HingeAxis_Calf_Right","HingeAxis_Forearm_Left","HingeAxis_Forearm_Right"})
  if(!index.count(name))throw std::runtime_error("Visual retarget: missing measured hinge axis");
 auto travel=sub(position(current.at("hip")),position(r.reference.at("hip")));travel[2]=0;
 for(auto&[name,matrix]:current)matrix=translate(matrix,sub(position(matrix),travel));
 auto root_delta=sub(position(current.at("hip")),position(r.reference.at("hip")));root_delta[2]-=gait*r.hip_drop;
 auto rotated=[&](const std::string&bone,const std::string&control,Vec origin) {
  return translate(product(product(rotation(current.at(control)),inverse(rotation(r.reference.at(control)))),rest(bone)),origin);
 };
 std::map<std::string,Mat>want;
 want["Pelvis"]=rotated("Pelvis","hip",add(position(rest("Pelvis")),root_delta));
 const auto body=product(want.at("Pelvis"),inverse(rest("Pelvis")));
 want["Torso_Twist"]=rotated("Torso_Twist","torso",point(body,position(rest("Torso_Twist"))));
 const auto torso=product(want.at("Torso_Twist"),inverse(rest("Torso_Twist")));
 for(const auto&side:std::array<std::pair<std::string,std::string>,2>{{{"Left","l"},{"Right","r"}}}) {
  const auto upper="Upperarm_"+side.first,lower="Forearm_"+side.first;
  const auto shoulder_origin=point(torso,position(rest(upper)));
  const auto requested_upper=rotated(upper,side.second+"arm",shoulder_origin);
  want[upper]=r.shoulder_limits?shoulder_constrained(rest(upper),requested_upper,torso,
    rest("HingeAxis_"+upper),rest("HingeMin_"+upper),rest("HingeMax_"+upper),shoulder_origin):requested_upper;
  const auto arm=product(want.at(upper),inverse(rest(upper)));
  auto raw=current.count(side.second+"hand")?rotated(lower,side.second+"hand",point(arm,position(rest(lower)))):product(arm,rest(lower));
  if(r.shoulder_limits&&current.count(side.second+"hand")) {
   // A shoulder limit must not turn the rejected shoulder angle into elbow flex.
   const auto requested_arm=product(requested_upper,inverse(rest(upper)));
   const auto correction=product(rotation(arm),inverse(rotation(requested_arm)));
   raw=translate(product(correction,raw),point(arm,position(rest(lower))));
  }
  want[lower]=hinge_constrained(rest(lower),raw,arm,rest("HingeAxis_"+lower),point(arm,position(rest(lower))));
 }
 if(index.count("Torso_Head")&&r.bones[index.at("Torso_Head")].control=="head"&&current.count("head"))
  want["Torso_Head"]=rotated("Torso_Head","head",point(torso,position(rest("Torso_Head"))));
 Pose output;
 for(unsigned side=0;side<2;++side) {
  const std::string suffix=side==0?"Left":"Right",prefix=side==0?"l":"r";
  const auto thigh="Thigh_"+suffix,calf="Calf_"+suffix,foot="Foot0_"+suffix;
  const auto h0=position(rest(thigh)),k0=position(rest(calf)),a0=position(rest(foot));
  auto reference=position(r.reference.at(prefix+"foot"));
  reference[0]+=(r.walk_x[side]-reference[0])*gait;
  if(r.ground_reference)reference[2]+=(r.walk_z[side]-reference[2])*gait;
  auto goal=add(a0,sub(position(current.at(prefix+"foot")),reference));
  auto foot_pose=[&](Vec ankle) {
   const auto raw_foot=rotated(foot,prefix+"foot",ankle);
   const auto calf_delta=want.count(calf)?product(want.at(calf),inverse(rest(calf))):identity();
   want[foot]=want.count(calf)?hinge_constrained(rest(foot),raw_foot,calf_delta,rest("HingeAxis_"+foot),ankle):raw_foot;
   const auto delta=product(want.at(foot),inverse(rest(foot)));
   for(const auto&bone:r.bones)if(bone.control.rfind(prefix+"toe",0)==0&&current.count(bone.control)) {
    const auto origin=point(delta,position(bone.rest));
    const auto raw=rotated(bone.name,bone.control,origin);
    const auto axis_name="HingeAxis_"+bone.name;
    want[bone.name]=index.count(axis_name)?hinge_constrained(bone.rest,raw,delta,rest(axis_name),origin):raw;
   }
  };
  foot_pose(goal);
  double lowest=1e300,rest_lowest=1e300;unsigned markers=0;
  for(const auto&bone:r.bones)if(bone.name.rfind("Sole_"+suffix+"_",0)==0) {
   if(bone.parent<0||bone.parent>=int(r.bones.size()))throw std::runtime_error("Visual retarget: invalid sole parent");
   const auto&parent=r.bones[static_cast<std::size_t>(bone.parent)];
   if(!want.count(parent.name))throw std::runtime_error("Visual retarget: sole must bind to its foot or toe");
   const auto delta=product(want.at(parent.name),inverse(parent.rest));
   lowest=std::min(lowest,point(delta,position(bone.rest))[2]);
   rest_lowest=std::min(rest_lowest,position(bone.rest)[2]);++markers;
  }
  if(markers<3||markers>64)throw std::runtime_error("Visual retarget: invalid sole marker count");
  // The original controller supplies lift and rotation. These measured source
  // points compensate the donor's different footprint; no guest state is written.
  // The controller's clearance belongs to its own proportions. Bound the
  // donor's lift by its leg length so short thighs do not march hip-high.
  const double maximum_lift=.08*(length(sub(k0,h0))+length(sub(a0,k0)));
  if(maximum_lift<1e-8)throw std::runtime_error("Visual retarget: degenerate leg length");
  const double original_lift=std::max(0.,goal[2]-a0[2]);
  const double low_lift=maximum_lift*std::tanh(original_lift/maximum_lift);
  // Long running strides may need more clearance to keep a rigid leg in reach.
  // Retain that necessary lift without exceeding the controller's request.
  const auto hip=point(body,h0);const auto horizontal=sub(goal,hip);
  const double reach=.97*(length(sub(k0,h0))+length(sub(a0,k0)));
  const double downward=std::sqrt(std::max(0.,reach*reach-horizontal[0]*horizontal[0]-horizontal[1]*horizontal[1]));
  const double needed_lift=std::max(0.,hip[2]-downward+(lowest-goal[2])-rest_lowest);
  const double lift=std::max(low_lift,std::min(original_lift,needed_lift));
  const double plane=rest_lowest+lift;
  goal[2]+=plane-lowest;
  bool clamped=false;
  auto solve_leg=[&](){
   clamped=false;
  auto ankle=point(inverse(body),goal);auto direction=sub(ankle,h0);
  const auto axis=hinge_axis(rest("HingeAxis_"+calf));
  const auto upper=sub(k0,h0),lower=sub(a0,k0),old_chain=sub(a0,h0);
  const double aa=dot(upper,lower)-dot(upper,axis)*dot(lower,axis);
  const double bb=dot(upper,cross(axis,lower));const double radius=std::hypot(aa,bb);
  if(radius<1e-12)throw std::runtime_error("Visual retarget: degenerate hinge chain");
  const double baseline=dot(upper,upper)+dot(lower,lower)+2*dot(upper,axis)*dot(lower,axis);
  const double minimum=std::sqrt(std::max(0.,baseline-2*radius))+1e-6;
  const double maximum=std::sqrt(std::max(0.,baseline+2*radius))-1e-6;
  if(minimum>=maximum)throw std::runtime_error("Visual retarget: invalid hinge reach");
  double distance=length(direction);
  if(distance<1e-10){direction=scale(unit(old_chain),minimum);distance=minimum;}
  const double reachable=std::clamp(distance,minimum,maximum);
  if(reachable!=distance){direction=scale(direction,reachable/distance);distance=reachable;clamped=true;}
  const double phase=std::atan2(bb,aa);
  const double offset=std::acos(std::clamp((distance*distance-baseline)/(2*radius),-1.,1.));
  const double original_bend=dot(axis,cross(upper,lower));
  double angle=phase+offset;
  for(double candidate:{phase+offset,phase-offset}) {
   const auto moved=vector(hinge_rotation(axis,candidate),lower);
   if(dot(axis,cross(upper,moved))*original_bend>=-1e-12){angle=candidate;break;}
  }
  const auto knee_rotation=hinge_rotation(axis,angle);
  const auto chain=add(upper,vector(knee_rotation,lower));
  auto hip_rotation=swing(chain,direction);
  auto pole=sub(upper,scale(old_chain,dot(upper,old_chain)/dot(old_chain,old_chain)));
  if(length(pole)<1e-8)pole={1,0,0};
  hip_rotation=product(hinge_rotation(direction,hinge_angle(direction,vector(hip_rotation,upper),pole)),hip_rotation);
  const auto knee_local=add(h0,vector(hip_rotation,upper));
  const auto ankle_local=add(h0,vector(hip_rotation,chain));
  want[thigh]=translate(product(product(rotation(body),hip_rotation),rest(thigh)),point(body,h0));
  want[calf]=translate(product(product(product(rotation(body),hip_rotation),knee_rotation),rest(calf)),point(body,knee_local));
  foot_pose(point(body,ankle_local));
  };
  // Ankle rotation changes the footprint. Re-solve vertical contact while
  // preserving the knee and ankle axes at every iteration, never the mesh.
  auto contact_error=[&](double height){
   goal[2]=height;solve_leg();
   double contact=1e300;
   for(const auto&bone:r.bones)if(bone.name.rfind("Sole_"+suffix+"_",0)==0){
    const auto&parent=r.bones[static_cast<std::size_t>(bone.parent)];
    const auto delta=product(want.at(parent.name),inverse(parent.rest));
    contact=std::min(contact,point(delta,position(bone.rest))[2]);
   }
   const double error=contact-plane;
   if(!std::isfinite(error))throw std::runtime_error("Visual retarget: nonfinite contact error");
   return error;
  };
  constexpr double contact_tolerance=1e-8;
  double first=goal[2],first_error=contact_error(first);
  if(std::abs(first_error)>=contact_tolerance){
   const double direction=first_error>0?-1.:1.;
   double step=maximum_lift,second=first,second_error=first_error;
   bool solved=false,bracketed=false;
   for(unsigned expansion=0;expansion<16;++expansion){
    second=first+direction*step;second_error=contact_error(second);
    if(std::abs(second_error)<contact_tolerance){solved=true;break;}
    if((first_error<0)!=(second_error<0)){bracketed=true;break;}
    first=second;first_error=second_error;step*=2;
   }
   if(!solved&&bracketed){
    for(unsigned iteration=0;iteration<40;++iteration){
     const double middle=first+(second-first)*.5;
     const double error=contact_error(middle);
     if(std::abs(error)<contact_tolerance){solved=true;break;}
     if((first_error<0)==(error<0)){first=middle;first_error=error;}
     else{second=middle;second_error=error;}
    }
   }
   if(!solved)throw std::runtime_error("Visual retarget: footprint contact did not converge");
  }
  if(clamped)++output.reach_clamps;
 }
 for(size_t i=0;i<r.bones.size();++i) {
  const auto&bone=r.bones[i];
  if(bone.parent>=int(i)||bone.parent< -1)throw std::runtime_error("Visual retarget: invalid bone order");
  auto matrix=want.count(bone.name)?want.at(bone.name):(bone.parent>=0?product(product(output.world.at(static_cast<std::size_t>(bone.parent)),inverse(r.bones[static_cast<std::size_t>(bone.parent)].rest)),bone.rest):bone.rest);
  output.world.push_back(matrix);
 }
 for(auto&matrix:output.world)matrix=translate(matrix,add(position(matrix),travel));
 for(const auto&matrix:output.world)for(double value:matrix)if(!std::isfinite(value))
  throw std::runtime_error("Visual retarget: nonfinite hinge pose");
 return output;
}
inline Pose retarget(const Rig&r,std::map<std::string,Mat>current,double gait){
 if(!std::isfinite(gait)||gait<0||gait>1)throw std::runtime_error("Visual retarget: invalid gait blend");
 if(r.shoulder_limits&&!r.hinge_axes)throw std::runtime_error("Visual retarget: shoulder limits require measured hinges");
 if(r.hinge_axes)return retarget_hinged(r,std::move(current),gait);
 std::map<std::string,size_t>index;for(size_t i=0;i<r.bones.size();++i)if(!index.emplace(r.bones[i].name,i).second)throw std::runtime_error("Visual retarget: duplicate bone");
 auto rest=[&](const std::string&n)->const Mat&{return r.bones.at(index.at(n)).rest;};
 auto travel=sub(position(current.at("hip")),position(r.reference.at("hip")));travel[2]=0;
 for(auto&[name,m]:current)m=translate(m,sub(position(m),travel));
 auto root_delta=sub(position(current.at("hip")),position(r.reference.at("hip")));root_delta[2]-=gait*r.hip_drop;
 auto rotated=[&](const std::string&bone,const std::string&control,Vec origin){return translate(product(product(rotation(current.at(control)),inverse(rotation(r.reference.at(control)))),rest(bone)),origin);};
 std::map<std::string,Mat>want;
 want["Pelvis"]=rotated("Pelvis","hip",add(position(rest("Pelvis")),root_delta));
 const auto body=product(want.at("Pelvis"),inverse(rest("Pelvis")));
 want["Torso_Twist"]=rotated("Torso_Twist","torso",point(body,position(rest("Torso_Twist"))));
 const auto torso=product(want.at("Torso_Twist"),inverse(rest("Torso_Twist")));
 for(const auto&side:std::array<std::pair<std::string,std::string>,2>{{{"Left","l"},{"Right","r"}}}){
  const auto upper="Upperarm_"+side.first,lower="Forearm_"+side.first;
  want[upper]=rotated(upper,side.second+"arm",point(torso,position(rest(upper))));const auto arm=product(want.at(upper),inverse(rest(upper)));
  want[lower]=current.count(side.second+"hand")?rotated(lower,side.second+"hand",point(arm,position(rest(lower)))):product(arm,rest(lower));
 }
 if(index.count("Torso_Head")&&r.bones[index.at("Torso_Head")].control=="head"&&current.count("head"))want["Torso_Head"]=rotated("Torso_Head","head",point(torso,position(rest("Torso_Head"))));
 Pose output;
 for(unsigned side=0;side<2;++side){
  const std::string suffix=side==0?"Left":"Right",prefix=side==0?"l":"r";
  const auto thigh="Thigh_"+suffix,calf="Calf_"+suffix,foot="Foot0_"+suffix,knee="Knee_"+suffix;
  const auto h0=position(rest(thigh)),k0=position(rest(calf)),a0=position(rest(foot));auto ref=position(r.reference.at(prefix+"foot"));
  ref[0]+=(r.walk_x[side]-ref[0])*gait;if(r.ground_reference)ref[2]+=(r.walk_z[side]-ref[2])*gait;
  auto goal=add(a0,sub(position(current.at(prefix+"foot")),ref));auto ankle=point(inverse(body),goal);
  const double upper=length(sub(k0,h0)),lower=length(sub(a0,k0)),ky=k0[1];
  const double r1=std::sqrt(std::max(1e-10,upper*upper-(ky-h0[1])*(ky-h0[1])));
  double dy=ankle[1]-ky;
  if(std::abs(dy)>=lower){dy=std::copysign(lower*.999,dy);ankle[1]=ky+dy;++output.reach_clamps;}
  const double r2=std::sqrt(std::max(1e-10,lower*lower-dy*dy));double dx=ankle[0]-h0[0],dz=ankle[2]-h0[2],distance=std::hypot(dx,dz);
  if(distance<1e-8){dx=1e-8;dz=0;distance=1e-8;}
  const double target=std::clamp(distance,std::abs(r1-r2)+1e-6,r1+r2-1e-6);
  if(target!=distance){dx*=target/distance;dz*=target/distance;distance=target;ankle[0]=h0[0]+dx;ankle[2]=h0[2]+dz;++output.reach_clamps;}
  goal=point(body,ankle);const double ux=dx/distance,uz=dz/distance,along=(r1*r1-r2*r2+distance*distance)/(2*distance);
  const double height=std::sqrt(std::max(0.,r1*r1-along*along));const auto old=sub(a0,h0);
  const double sign=((k0[0]-h0[0])*(-old[2])+(k0[2]-h0[2])*old[0])>=0?1.:-1.;
  const Vec k{h0[0]+ux*along-sign*uz*height,ky,h0[2]+uz*along+sign*ux*height};const auto kw=point(body,k);
  auto oldupper=sub(k0,h0),newupper=sub(k,h0);oldupper[1]=0;newupper[1]=0;
  want[thigh]=translate(product(product(rotation(body),swing(oldupper,newupper)),rest(thigh)),point(body,h0));
  want[calf]=translate(product(swing(sub(a0,k0),sub(goal,kw)),rest(calf)),kw);
  if(index.count(knee))want[knee]=product(product(want.at(calf),inverse(rest(calf))),rest(knee));
  want[foot]=rotated(foot,prefix+"foot",goal);const auto ff=product(want.at(foot),inverse(rest(foot)));
  for(const auto&b:r.bones)if(b.control.rfind(prefix+"toe",0)==0&&current.count(b.control))want[b.name]=rotated(b.name,b.control,point(ff,position(b.rest)));
 }
 for(size_t i=0;i<r.bones.size();++i){const auto&b=r.bones[i];if(b.parent>=int(i)||b.parent< -1)throw std::runtime_error("Visual retarget: invalid bone order");
  auto m=want.count(b.name)?want.at(b.name):(b.parent>=0?product(product(output.world.at(static_cast<std::size_t>(b.parent)),inverse(r.bones[static_cast<std::size_t>(b.parent)].rest)),b.rest):b.rest);
  // Restore actor-local root travel after the in-place donor solve.
  output.world.push_back(m);
 }
 for(auto&m:output.world)m=translate(m,add(position(m),travel));
 for(const auto&m:output.world)for(double v:m)if(!std::isfinite(v))throw std::runtime_error("Visual retarget: nonfinite pose");
 return output;
}
} // namespace mw34::donor
