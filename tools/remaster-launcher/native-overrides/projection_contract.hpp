#pragma once
#include <array>
#include <algorithm>
#include <cstdint>
#include <cstddef>
namespace mw34::projection {
inline constexpr unsigned scratch=0x72f41c,extent=128*32;
inline bool operand(unsigned bits){bits&=0x7fffffff;return !bits||(bits>=0x3b800000&&bits<=0x47800000);}
inline bool positive(unsigned bits){return bits>=0x3b800000&&bits<=0x47800000;}
inline bool overlaps(unsigned address,std::uint64_t size){return size&&address<std::uint64_t(scratch)+extent&&std::uint64_t(address)+size>scratch;}
struct Dirty {
 std::array<unsigned char,extent> bytes{};
 bool any(unsigned address,unsigned size)const{for(unsigned i=0;i<size;++i)if(std::uint64_t(address)+i>=scratch&&std::uint64_t(address)+i<scratch+extent&&bytes[address+i-scratch])return true;return false;}
 void set(unsigned address,unsigned size,bool value){const auto lo=std::max(std::uint64_t(address),std::uint64_t(scratch)),hi=std::min(std::uint64_t(address)+size,std::uint64_t(scratch)+extent);for(auto i=lo;i<hi;++i)bytes[std::size_t(i-scratch)]=value;}
 void prefix(unsigned count){for(unsigned i=0;i+1<count;++i)set(scratch+32*i,12,true);}
};
}
