#pragma once
#include <array>
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace mw34::mechpreview {
struct Framing {std::array<double,3> center{};double radius{};};
struct Camera {std::array<double,16> matrix{};std::array<double,6> projection{};};
inline Framing framing(const std::array<double,3>& lo,const std::array<double,3>& hi) {
    Framing result;double squared{};
    for(unsigned i=0;i<3;++i) {
        if(!std::isfinite(lo[i])||!std::isfinite(hi[i])||hi[i]<lo[i])
            throw std::runtime_error("Additional mech preview: invalid rest bounds");
        result.center[i]=(lo[i]+hi[i])*.5;
        const auto half=(hi[i]-lo[i])*.5;squared+=half*half;
    }
    result.radius=std::sqrt(squared);
    if(!std::isfinite(result.radius)||result.radius<1e-6)
        throw std::runtime_error("Additional mech preview: empty rest bounds");
    return result;
}
// Long-lens camera fitted once to immutable rest dimensions, never to the
// current frame's rotated silhouette. Preserve the original turntable yaw.
inline Camera camera(const Framing& frame,const std::array<double,16>& source,
                     double near_scale,double scale_x,double scale_y,double near_clip) {
    if(!std::isfinite(near_scale)||near_scale<=0||!std::isfinite(near_clip)||near_clip<=0||
       !std::isfinite(scale_x)||!std::isfinite(scale_y)||!scale_x||!scale_y)
        throw std::runtime_error("Additional mech preview: invalid projection");
    const double length=std::hypot(source[0],source[1]);
    if(!std::isfinite(length)||length<1e-8)
        throw std::runtime_error("Additional mech preview: invalid horizontal camera axis");
    const double rx=source[0]/length,ry=source[1]/length;
    double fx=-ry,fy=rx;
    if(fx*source[8]+fy*source[9]<0){fx=-fx;fy=-fy;}
    constexpr double pitch=.17453292519943295; // Ten degrees above the target.
    const double c=std::cos(pitch),s=std::sin(pitch),ysign=scale_y<0?-1.:1.;
    const double distance=std::max(frame.radius*24.,near_clip+frame.radius*2.);
    Camera result;
    result.matrix={rx,ry,0,0,-ysign*s*fx,-ysign*s*fy,-ysign*c,0,c*fx,c*fy,-s,0,0,0,0,1};
    for(unsigned row=0;row<3;++row) {
        result.matrix[row*4+3]=row==2?distance:0;
        for(unsigned axis=0;axis<3;++axis)result.matrix[row*4+3]-=result.matrix[row*4+axis]*frame.center[axis];
    }
    // Original logical Mech Lab panel with an eight-pixel margin.
    const double focal=99.5*std::sqrt(distance*distance-frame.radius*frame.radius)/frame.radius;
    result.projection={near_scale,(scale_x<0?-1.:1.)*focal/near_scale,ysign*focal/near_scale,317.5,167.5,near_clip};
    return result;
}
} // namespace mw34::mechpreview
