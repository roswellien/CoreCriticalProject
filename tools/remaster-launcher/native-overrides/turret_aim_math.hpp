// Authored first-interval interpolation and degenerate-yaw guards.
// Callers own authentication, guest-memory access and the FP environment.
#pragma once
#include <array>
#include <bit>
#include <cmath>
#include <cstdint>
#include <stdexcept>

namespace mw34::turret_aim {
struct IntervalResult {float value;bool changed;};
inline IntervalResult first_interval(float x,float original,float t0,float t1){
 if(original!=1.f||t0!=1.f||!(t1>0.f&&t1<1.f)||!std::isfinite(x)||!(x>0.f))return {original,false};
 const double scaled=double(x)*51.0;
 if(!(scaled<1.0))return {original,false};
 const float value=float(double(t0)+scaled*(double(t1)-double(t0)));
 return {value,value!=original};
}
using YawBits=std::array<std::uint32_t,4>; // m00,m02,m20,m22
inline bool valid_yaw(const YawBits&bits){
 std::array<float,4>v{};
 for(unsigned i=0;i<4;++i){v[i]=std::bit_cast<float>(bits[i]);if(!std::isfinite(v[i]))return false;}
 const double determinant=double(v[0])*double(v[3])-double(v[1])*double(v[2]);
 const double magnitude=std::abs(determinant);
 return magnitude>.5&&magnitude<2.0;
}
inline bool collapsed_yaw(const YawBits&bits){
 for(auto word:bits)if(word&0x7fffffffU)return false;
 return true;
}
inline bool should_keep_yaw(float dt,const YawBits&before,const YawBits&after){
 return (std::bit_cast<std::uint32_t>(dt)&0x7fffffffU)==0&&valid_yaw(before)&&collapsed_yaw(after);
}
// Exact little-endian x87 80-bit payload; no host long-double layout dependency.
inline std::array<std::uint8_t,10> encode_f32(float value){
 const std::uint32_t bits=std::bit_cast<std::uint32_t>(value);
 const unsigned exponent=(bits>>23)&255U,fraction=bits&0x7fffffU;
 if((bits>>31)||exponent==255U||(!exponent&&!fraction))throw std::invalid_argument("Expected a positive finite nonzero float");
 std::uint64_t significand{};unsigned extended_exponent{};
 if(exponent){significand=std::uint64_t(0x800000U|fraction)<<40;extended_exponent=exponent+16383U-127U;}
 else{const unsigned highest=31U-unsigned(std::countl_zero(fraction));significand=std::uint64_t(fraction)<<(63U-highest);extended_exponent=highest+16383U-149U;}
 std::array<std::uint8_t,10>out{};
 for(unsigned i=0;i<8;++i)out[i]=std::uint8_t(significand>>(8*i));
 out[8]=std::uint8_t(extended_exponent);out[9]=std::uint8_t(extended_exponent>>8);
 return out;
}
}
