#include "../native-overrides/texture_staging.hpp"
#include <cassert>
#include <stdexcept>
#include <vector>
#include <cstdio>

unsigned reference(unsigned p,unsigned f){
 unsigned channels[4];
 if(f==0){channels[0]=((p>>11)&31)*255/31;channels[1]=((p>>5)&63)*255/63;channels[2]=(p&31)*255/31;channels[3]=255;}
 else if(f==1){channels[0]=((p>>10)&31)*255/31;channels[1]=((p>>5)&31)*255/31;channels[2]=(p&31)*255/31;channels[3]=(p&0x8000)?255:0;}
 else {channels[0]=((p>>8)&15)*17;channels[1]=((p>>4)&15)*17;channels[2]=(p&15)*17;channels[3]=((p>>12)&15)*17;}
 return channels[0]|channels[1]<<8|channels[2]<<16|channels[3]<<24;
}
int main(){
 for(unsigned format=0;format<3;++format){
  for(std::size_t count: {std::size_t(0),std::size_t(1),std::size_t(4095),std::size_t(4096),std::size_t(4097),std::size_t(65536),std::size_t(65553)}){
   std::vector<std::uint16_t> input(count);for(std::size_t i=0;i<count;++i)input[i]=std::uint16_t(i);const auto original=input;
   for(unsigned offset: {0U,1U,3U}){
    std::vector<unsigned char> bytes(count*4+offset+7,0xcd);
    mw34::texture_staging::copy(bytes.data()+offset,input.data(),count,format);
    assert(input==original);
    for(unsigned i=0;i<offset;++i)assert(bytes[i]==0xcd);
    for(std::size_t i=offset+count*4;i<bytes.size();++i)assert(bytes[i]==0xcd);
    for(std::size_t i=0;i<count;++i){std::uint32_t actual;std::memcpy(&actual,bytes.data()+offset+4*i,4);assert(actual==reference(input[i],format));}
   }
  }
 }
 std::array<unsigned char,4> sentinel{1,2,3,4};const auto before=sentinel;std::uint16_t source=0;
 bool rejected=false;try{mw34::texture_staging::copy(sentinel.data(),&source,1,3);}catch(const std::out_of_range&){rejected=true;}
 assert(rejected&&sentinel==before);
 std::puts("All 196608 source color/alpha combinations and chunk/alignment/guard cases pass");
}
