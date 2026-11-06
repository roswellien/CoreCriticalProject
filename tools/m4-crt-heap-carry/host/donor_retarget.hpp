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
inline Vec add(Vec a,Vec b){for(unsigned i=0;i<3;++i)a[i]+=b[i];return a;}
inline Vec sub(Vec a,Vec b){for(unsigned i=0;i<3;++i)a[i]-=b[i];return a;}
inline Vec scale(Vec a,double s){for(auto&v:a)v*=s;return a;}
inline double dot(Vec a,Vec b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
inline double length(Vec a){return std::sqrt(dot(a,a));}
inline Vec unit(Vec a){const auto n=length(a);if(n<1e-10)throw std::runtime_error("Visual retarget: degenerate vector");return scale(a,1/n);}
inline Vec cross(Vec a,Vec b){return {a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]};}
inline Vec position(const Mat&m){return {m[3],m[7],m[11]};}
inline Mat translate(Mat m,Vec p){for(unsigned i=0;i<3;++i)m[4*i+3]=p[i];return m;}
inline Mat product(const Mat&a,const Mat&b){Mat m{};for(unsigned i=0;i<4;++i)for(unsigned j=0;j<4;++j)for(unsigned k=0;k<4;++k)m[i*4+j]+=a[i*4+k]*b[k*4+j];return m;}
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
inline Mat rotation(const Mat&m){auto r=identity();for(unsigned c=0;c<3;++c){auto v=unit({m[c],m[4+c],m[8+c]});for(unsigned i=0;i<3;++i)r[4*i+c]=v[i];}return r;}
inline Mat swing(Vec a,Vec b){
 a=unit(a);b=unit(b);const double c=std::clamp(dot(a,b),-1.,1.);auto v=cross(a,b);auto r=identity();
 if(c<-.999999){auto axis=unit(cross(a,std::abs(a[0])<.8?Vec{1,0,0}:Vec{0,1,0}));for(unsigned i=0;i<3;++i)for(unsigned j=0;j<3;++j)r[i*4+j]=2*axis[i]*axis[j]-(i==j?1.:0.);return r;}
 const double k=1/(1+c);const double vv[3][3]={{0,-v[2],v[1]},{v[2],0,-v[0]},{-v[1],v[0],0}};
 for(unsigned i=0;i<3;++i)for(unsigned j=0;j<3;++j){r[4*i+j]+=vv[i][j];for(unsigned t=0;t<3;++t)r[4*i+j]+=vv[i][t]*vv[t][j]*k;}
 return r;
}
inline Mat axis(){return {0,0,-1,0,-1,0,0,0,0,1,0,0,0,0,0,1};}
struct Bone{std::string name,control;int parent{-1};Mat rest=identity();};
struct Rig{std::vector<Bone>bones;std::map<std::string,Mat>reference;std::array<double,2>walk_x{},walk_z{};double hip_drop{};bool ground_reference=true;bool source_joint_pose=false;bool authored_arm_rest=false;};
struct Pose{std::vector<Mat>world;unsigned reach_clamps{};};
inline bool arm_control(const std::string& control) {
    return control == "larm" || control == "rarm" || control == "lhand" || control == "rhand";
}
inline int bound_parent(const Rig& rig, size_t index) {
    int parent = rig.bones.at(index).parent;
    while (parent >= 0) {
        if (size_t(parent) >= index)
            throw std::runtime_error("Visual retarget: invalid bound ancestry");
        if (!rig.bones.at(size_t(parent)).control.empty()) return parent;
        index = size_t(parent);
        parent = rig.bones[index].parent;
    }
    return -1;
}
inline void validate_arm_rest(const Rig& rig) {
    if (!rig.authored_arm_rest) return;
    if (!rig.source_joint_pose)
        throw std::runtime_error("Visual retarget: arm rest requires original joint motion");
    std::map<std::string, size_t> controls;
    for (size_t i = 0; i < rig.bones.size(); ++i) {
        const auto& bone = rig.bones[i];
        if (bone.parent < -1 || bone.parent >= int(i))
            throw std::runtime_error("Visual retarget: invalid arm hierarchy");
        if (!bone.control.empty() && !controls.emplace(bone.control, i).second)
            throw std::runtime_error("Visual retarget: duplicate arm policy control");
        const int parent = bound_parent(rig, i);
        if (!bone.control.empty() && !arm_control(bone.control) && parent >= 0 &&
            arm_control(rig.bones[size_t(parent)].control))
            throw std::runtime_error("Visual retarget: unsupported bound arm descendant");
    }
    for (const auto& [control, name, parent] :
         std::array<std::array<std::string, 3>, 4>{{
             {"larm", "Upperarm_Left", "torso"}, {"rarm", "Upperarm_Right", "torso"},
             {"lhand", "Forearm_Left", "larm"}, {"rhand", "Forearm_Right", "rarm"}}}) {
        const auto found = controls.find(control);
        if (found == controls.end())
            throw std::runtime_error("Visual retarget: missing authored arm control");
        const auto index = found->second;
        const int ancestor = bound_parent(rig, index);
        if (rig.bones[index].name != name || ancestor < 0 ||
            rig.bones[size_t(ancestor)].control != parent)
            throw std::runtime_error("Visual retarget: authored arm parent mismatch");
    }
}
inline Mat arm_rest_pose(const Rig& rig, const std::map<std::string, Mat>& current,
                         const Pose& output, size_t index) {
    const auto& bone = rig.bones.at(index);
    const auto parent_index = size_t(bound_parent(rig, index));
    const auto& parent = rig.bones.at(parent_index);
    const auto local_rest = product(inverse(parent.rest), bone.rest);
    const auto local_reference = product(inverse(rig.reference.at(parent.control)),
                                         rig.reference.at(bone.control));
    const auto local_current = product(inverse(current.at(parent.control)), current.at(bone.control));
    for (double value : local_current)
        if (!std::isfinite(value))
            throw std::runtime_error("Visual retarget: nonfinite original arm pose");
    // Original animations translate their elbows. Those offsets belong to the
    // original mesh: copying them would separate a differently proportioned arm.
    const auto articulation = translate(product(inverse(local_reference), local_current), {0, 0, 0});
    return product(product(output.world.at(parent_index), local_rest), articulation);
}
inline double locomotion(const Rig&r,const std::map<std::string,Mat>&current){
 const auto h=position(current.at("hip")),h0=position(r.reference.at("hip"));double change=0;
 for(const char*name:{"lfoot","rfoot","lthigh","rthigh"}){const auto it=current.find(name);if(it==current.end())continue;
  change=std::max(change,length(sub(sub(position(it->second),h),sub(position(r.reference.at(name)),h0))));
  for(unsigned i:{0U,1U,2U,4U,5U,6U,8U,9U,10U})change=std::max(change,std::abs(it->second[i]-r.reference.at(name)[i]));
 }
 const double t=std::clamp((change-.005)/.075,0.,1.);return t*t*(3-2*t);
}
inline Pose retarget(const Rig&r,std::map<std::string,Mat>current,double gait){
 if(!std::isfinite(gait)||gait<0||gait>1)throw std::runtime_error("Visual retarget: invalid gait blend");
 // A fitted replacement may use the complete original joint pose. This is
 // forward kinematics: no foot goal, gait correction or knee pole is inferred.
 if(r.source_joint_pose){
  validate_arm_rest(r);
  Pose output;
  for(size_t i=0;i<r.bones.size();++i){const auto&b=r.bones[i];
   if(b.parent>=int(i)||b.parent< -1)throw std::runtime_error("Visual retarget: invalid bone order");
   const auto m=r.authored_arm_rest&&arm_control(b.control)?arm_rest_pose(r,current,output,i):
    !b.control.empty()?product(product(current.at(b.control),inverse(r.reference.at(b.control))),b.rest):
    (b.parent>=0?product(product(output.world.at(size_t(b.parent)),inverse(r.bones[size_t(b.parent)].rest)),b.rest):b.rest);
   for(double value:m)if(!std::isfinite(value))throw std::runtime_error("Visual retarget: nonfinite source pose");
   output.world.push_back(m);
  }
  return output;
 }
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
  auto m=want.count(b.name)?want.at(b.name):(b.parent>=0?product(product(output.world.at(size_t(b.parent)),inverse(r.bones[size_t(b.parent)].rest)),b.rest):b.rest);
  // Restore actor-local root travel after the in-place donor solve.
  output.world.push_back(m);
 }
 for(auto&m:output.world)m=translate(m,add(position(m),travel));
 for(const auto&m:output.world)for(double v:m)if(!std::isfinite(v))throw std::runtime_error("Visual retarget: nonfinite pose");
 return output;
}
} // namespace mw34::donor
