"""Make the front-end scrolling background move by real time instead of per frame.

Original 0x40A210 (scrolling image widget update, thiscall) adds the widget's
integer velocity (+0xBC, +0xC0) to its source rectangle (+0xE8..+0xF4) once
per call (once per presented frame) when scrolling is enabled (+0x138), wraps
it around the image size and derives the split rectangles. With vsync off the
background therefore scrolled at hundreds of steps per second.

MW34_MENU_SCROLL_HZ=<rate> (e.g. 60): for each widget, the number of whole
<rate>-per-second steps elapsed since its previous update (fractional
remainder carried) multiplies the velocity for that one original call; the
velocity is restored afterwards. The original routine still performs the move,
wrap and split. Presentation is not capped.

Original 0x42FB30 (horizontal text ticker update) moves the text left by
ftol(float speed at +0xBC) pixels per call and wraps it to the right edge.
The same rate applies: the pixels due for the elapsed real time (sub-pixel
remainder carried) replace the speed for one call, then it is restored.
"""
from pathlib import Path
import argparse

def edit(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError(f'Expected one scroll anchor in {path.name}: {old[:80]}')
    path.write_text(text.replace(old,new))

HOOK = r'''  if(target==0x40a210){static const double hz=[]{const char*p=std::getenv("MW34_MENU_SCROLL_HZ");const double v=p?std::atof(p):0.0;return v>0&&v<=1000?v:0.0;}();
   const unsigned w=state.gpr.rcx.dword;
   if(hz>0&&w&&readable(w,0x140)&&(load(w+0x138)&0xff)){
    struct Clock{LARGE_INTEGER last{};double carry{};};static std::map<unsigned,Clock> clocks;static LARGE_INTEGER freq{};
    if(!freq.QuadPart)::QueryPerformanceFrequency(&freq);
    LARGE_INTEGER now{};::QueryPerformanceCounter(&now);auto& c=clocks[w];mw34::vkscene::HostFpEnvironment fp;
    const double elapsed=c.last.QuadPart?std::min(0.25,double(now.QuadPart-c.last.QuadPart)/double(freq.QuadPart)):1.0/hz;
    c.last=now;const double steps=c.carry+elapsed*hz;unsigned n=unsigned(steps);c.carry=steps-n;
    const int dx=int(load(w+0xbc)),dy=int(load(w+0xc0));
    const unsigned image=load(w+0x3c);const int iw=image&&readable(image,8)?int(short(load(image+4)&0xffff)):0,ih=image&&readable(image,8)?int(short(load(image+4)>>16)):0;
    while(n>1&&((iw>0&&std::abs(dx)*int(n)>=iw)||(ih>0&&std::abs(dy)*int(n)>=ih)))--n;
    store(w+0xbc,unsigned(dx*int(n)));store(w+0xc0,unsigned(dy*int(n)));
    try{void*r=remaster_body_inner(s,target,p,body);store(w+0xbc,unsigned(dx));store(w+0xc0,unsigned(dy));return r;}
    catch(...){store(w+0xbc,unsigned(dx));store(w+0xc0,unsigned(dy));throw;}
   }}
'''

TICKER = r'''  if(target==0x42fb30){static const double hz=[]{const char*p=std::getenv("MW34_MENU_SCROLL_HZ");const double v=p?std::atof(p):0.0;return v>0&&v<=1000?v:0.0;}();
   const unsigned w=state.gpr.rcx.dword;
   if(hz>0&&w&&readable(w,0xc0)){
    struct Clock{LARGE_INTEGER last{};double carry{};};static std::map<unsigned,Clock> clocks;static LARGE_INTEGER freq{};
    const unsigned bits=load(w+0xbc);float speed;std::memcpy(&speed,&bits,4);float due=0;
    {mw34::vkscene::HostFpEnvironment fp;
     if(!freq.QuadPart)::QueryPerformanceFrequency(&freq);
     LARGE_INTEGER now{};::QueryPerformanceCounter(&now);auto& c=clocks[w];
     const double elapsed=c.last.QuadPart?std::min(0.25,double(now.QuadPart-c.last.QuadPart)/double(freq.QuadPart)):1.0/hz;
     c.last=now;
     if(std::isfinite(speed)&&std::abs(speed)<1000){const double px=c.carry+double(speed)*elapsed*hz;const double whole=std::trunc(px);c.carry=px-whole;due=float(whole);}else due=speed;}
    unsigned due_bits;std::memcpy(&due_bits,&due,4);store(w+0xbc,due_bits);
    try{void*r=remaster_body_inner(s,target,p,body);store(w+0xbc,bits);return r;}catch(...){store(w+0xbc,bits);throw;}
   }}
'''

def apply(host):
    edit(host/'mfc_stage.hpp','  return remaster_body_inner(s,target,p,body);',HOOK+TICKER+'  return remaster_body_inner(s,target,p,body);')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('host_source',type=Path);apply(p.parse_args().host_source)
