#include "native-overrides/world_fast_binding.hpp"
#include <iostream>
#include <stdexcept>
int main(){
    using mw34::world::unchanged_polygon;
    if(!unchanged_polygon(0,3,0,0,0)||!unchanged_polygon(0x100,0x203,0,0,0))
        throw std::runtime_error("Unclipped ordinary polygon rejected");
    for(unsigned bit=1;bit<=0x20;bit<<=1)
        if(unchanged_polygon(bit,3,0,0,0))throw std::runtime_error("Clip dependency admitted");
    if(unchanged_polygon(0,0x403,0,0,0)||unchanged_polygon(0,3,1,0,0)||
       unchanged_polygon(0,3,0xffffffff,0,0)||unchanged_polygon(0,3,0,1,0)||
       unchanged_polygon(0,3,0,0,1))
        throw std::runtime_error("Decomposition, depth bias or layers admitted");
    std::cout<<"World fast admission: all clip bits, decomposition, signed bias, secondary layers and special paths pass\n";
}
