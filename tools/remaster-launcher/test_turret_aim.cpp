// Pure authored contract fixture; no game assets, original code or game launch.
#include "native-overrides/turret_aim_math.hpp"
#include <algorithm>
#include <iostream>
#include <limits>
#include <string>
using namespace mw34::turret_aim;
static void check(bool ok,const char*message){if(!ok)throw std::runtime_error(message);}
static std::uint32_t bits(float x){return std::bit_cast<std::uint32_t>(x);}
static YawBits yaw(float a,float b,float c,float d){return {bits(a),bits(b),bits(c),bits(d)};}
static void intervals(){
 const float t0=1.f,t1=float(std::exp(-double(1.f/51.f)));
 for(unsigned speed:{3U,8U})for(unsigned fps:{30U,60U,120U,144U,153U,165U,240U,1000U}){
  const float x=float(speed)*(1.f/float(fps));const double index=double(x)*51;
  const float original=index<1?1.f:float(std::exp(-std::floor(index)/51.0));
  const auto r=first_interval(x,original,t0,t1);
  if(index<1){check(r.changed&&r.value<1&&r.value>t1,"first interval must move toward target");check(bits(r.value)==bits(float(1.+index*(double(t1)-1.))),"interpolation rounds once");}
  else check(!r.changed&&bits(r.value)==bits(original),"normal-FPS bucket changed");
 }
 const float boundary=1.f/51.f;
 for(float x:{std::nextafter(boundary,0.f),boundary,std::nextafter(boundary,1.f)}){
  auto r=first_interval(x,1,t0,t1);const bool eligible=double(x)*51<1;
  check(r.changed==eligible,"first interval boundary selection");
  if(eligible)check(std::abs(r.value-t1)<=std::numeric_limits<float>::epsilon(),"first interval endpoint continuity");
 }
 const float nan=std::numeric_limits<float>::quiet_NaN(),inf=std::numeric_limits<float>::infinity();
 for(float x:{0.f,-0.f,-1.f,inf,-inf,nan}){auto r=first_interval(x,1,t0,t1);check(!r.changed&&r.value==1,"invalid/nonpositive x changed");}
 for(auto a:std::array<std::array<float,3>,7>{{{.5f,1,t1},{1,.5f,t1},{1,1,0},{1,1,1},{1,1,-1},{1,1,nan},{1,1,inf}}}){
  auto r=first_interval(.001f,a[0],a[1],a[2]);check(!r.changed&&bits(r.value)==bits(a[0]),"ineligible helper contract changed");
 }
 auto tiny=first_interval(std::numeric_limits<float>::denorm_min(),1,t0,t1);check(!tiny.changed&&tiny.value==1,"rounded-identical value marked changed");
}
static void yaw_guards(){
 const auto valid=yaw(1,0,0,1),zero=yaw(0,-0.f,-0.f,0),singular=yaw(1,1,1,1);
 check(valid_yaw(valid)&&valid_yaw(yaw(0,-1,1,0))&&valid_yaw(yaw(1,0,0,-1)),"valid finite determinant rejected");
 for(const auto&v:{zero,singular,yaw(.5f,0,0,1),yaw(2,0,0,1),yaw(std::numeric_limits<float>::infinity(),0,0,1),yaw(std::numeric_limits<float>::quiet_NaN(),0,0,1)})check(!valid_yaw(v),"invalid determinant accepted");
 check(collapsed_yaw(zero)&&!collapsed_yaw(valid)&&!collapsed_yaw(yaw(std::numeric_limits<float>::denorm_min(),0,0,0)),"signed-zero collapse predicate");
 check(should_keep_yaw(0,valid,zero)&&should_keep_yaw(-0.f,valid,zero),"zero-dt valid yaw not retained");
 check(!should_keep_yaw(.001f,valid,zero)&&!should_keep_yaw(-.001f,valid,zero)&&!should_keep_yaw(0,singular,zero)&&!should_keep_yaw(0,valid,singular),"yaw retention scope too broad");
 // Model the loss of horizontal direction, then verify the guard's matrix
 // supports an inverse and finite round-tripped bounds. This is authored
 // mathematical coverage, not a substitute for the lifted controller fixture.
 const float x=3.f/240.f,t1=float(std::exp(-double(1.f/51.f)));
 const auto blend=first_interval(x,1,1,t1);float horizontal=1-blend.value,vertical=blend.value;
 float length=std::sqrt(horizontal*horizontal+vertical*vertical);horizontal/=length;
 check(horizontal>0,"high-FPS interpolation leaves direction vertical");
 const float radius=std::hypot(horizontal,0.f),cosine=-0.f/radius,sine=-horizontal/radius;
 const auto updated=yaw(cosine,-sine,sine,cosine);check(valid_yaw(updated),"updated yaw singular");
 double a=std::bit_cast<float>(updated[0]),b=std::bit_cast<float>(updated[1]),c=std::bit_cast<float>(updated[2]),d=std::bit_cast<float>(updated[3]);
 const double det=a*d-b*c;check(std::isfinite(1/det),"yaw inverse nonfinite");
 double lo=std::numeric_limits<double>::infinity(),hi=-lo;
 for(double px:{-10.,10.})for(double pz:{-20.,20.}){double qx=a*px+b*pz,qz=c*px+d*pz;
  double rx=(d*qx-b*qz)/det,rz=(-c*qx+a*qz)/det;check(std::abs(rx-px)<1e-12&&std::abs(rz-pz)<1e-12,"inverse bounds roundtrip");lo=std::min(lo,qx);hi=std::max(hi,qx);}
 check(std::isfinite(lo)&&std::isfinite(hi)&&hi-lo==40,"transformed bounds nonfinite/collapsed");
}
static void extended_payloads(){
 const std::array<std::uint8_t,10>one{0,0,0,0,0,0,0,0x80,0xff,0x3f};
 check(encode_f32(1)==one,"f80 one payload");
 auto two=one;two[8]=0;two[9]=0x40;check(encode_f32(2)==two,"f80 two payload");
 auto half=one;half[8]=0xfe;check(encode_f32(.5f)==half,"f80 half payload");
 auto denorm=one;denorm[8]=0x6a;denorm[9]=0x3f;check(encode_f32(std::numeric_limits<float>::denorm_min())==denorm,"f80 minimum subnormal");
 // Independently decode the payload as an integer significand times a power
 // of two. Binary64 represents every binary32 input exactly, including subnormals.
 for(std::uint32_t word:{1U,2U,0x007fffffU,0x00800000U,0x3f012345U,0x3f7fffffU,0x3f800001U,0x7f7fffffU}){
  const float value=std::bit_cast<float>(word);const auto p=encode_f32(value);std::uint64_t significand=0;
  for(unsigned i=0;i<8;++i)significand|=std::uint64_t(p[i])<<(8*i);
  const int exponent=int(p[8])+(int(p[9])<<8);check((significand>>63)==1&&!(p[9]&128),"f80 normalization/sign");
  check(std::ldexp(double(significand),exponent-16383-63)==double(value),"f80 exact input representation");
 }
 for(float x:{0.f,-0.f,-1.f,std::numeric_limits<float>::infinity(),std::numeric_limits<float>::quiet_NaN()}){
  bool rejected=false;try{(void)encode_f32(x);}catch(const std::invalid_argument&){rejected=true;}check(rejected,"invalid f80 input accepted");
 }
}
int main(){try{intervals();yaw_guards();extended_payloads();std::cout<<"turret aim math: intervals, signed-zero yaw, inverse/bounds and exact f80 payloads passed\n";}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
