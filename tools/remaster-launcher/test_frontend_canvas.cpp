#include "native-overrides/frontend_canvas.hpp"
#include <cassert>
#include <cmath>
#include <iostream>

int main() {
    using mw34::frontend::CanvasFit;
    const auto wide=CanvasFit::fit(640,480,3440,1440);
    assert(wide.x==760&&wide.y==0&&wide.width==1920&&wide.height==1440);
    assert(wide.physical_x(210)==1390&&wide.physical_x(430)==2050);
    assert(wide.physical_y(52)==156&&wide.physical_y(288)==864);
    assert(wide.logical_x(759)==-1&&wide.logical_x(2680)==640);
    assert(wide.logical_x(1720)==320&&wide.logical_y(720)==240);
    const auto original=CanvasFit::fit(640,480,1920,1440);
    assert(original.x==0&&original.width==1920&&original.height==1440);
    const auto hd=CanvasFit::fit(640,480,1920,1080);
    assert(hd.x==240&&hd.y==0&&hd.width==1440&&hd.height==1080);
    for(int x=0;x<640;++x)assert(hd.logical_x(hd.physical_x(x))==x);
    for(int y=0;y<480;++y)assert(hd.logical_y(hd.physical_y(y))==y);
    assert(hd.logical_x(hd.x-1)<0&&hd.logical_x(hd.x+hd.width)>=640);
    const auto portrait=CanvasFit::fit(640,480,1080,1920);
    assert(portrait.x==0&&portrait.y==555&&portrait.width==1080&&portrait.height==810);
    // Odd client sizes must keep input within a logical pixel of the displayed
    // widget. In particular a left bar must never truncate to control column0.
    const auto odd=CanvasFit::fit(640,480,983,531);
    assert(odd.logical_x(odd.x-1)<0);
    for(int x=0;x<=640;++x)assert(odd.logical_x(odd.physical_x(x))==x);
    for(int y=0;y<=480;++y)assert(odd.logical_y(odd.physical_y(y))==y);
    bool rejected=false;try{CanvasFit::fit(0,480,3440,1440);}catch(const std::runtime_error&){rejected=true;}
    assert(rejected);
    std::cout<<"Frontend canvas: placement, preview bounds, margins, inverse input and resize checks pass\n";
}
