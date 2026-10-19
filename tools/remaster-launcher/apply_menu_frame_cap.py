"""Cap the presentation rate of frames without a 3D world scene (menus, briefings).

The original front end advances its animated backgrounds once per presented
frame, so with vsync off they scroll at hundreds of frames per second.
MW34_MENU_FPS=<n> (1..1000; unset or 0 = off) paces such presents with a
high-resolution waitable timer plus a short spin. Mission frames are not paced.
Apply after the widescreen stage exists (any sun/remaster test host).
"""
from pathlib import Path
import argparse

def edit(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError(f'Expected one menu-cap anchor in {path.name}: {old[:80]}')
    path.write_text(text.replace(old,new))

def apply(host):
    edit(host/'vdd.inc',' ++host.frames;mw34_frames_presented.store(host.frames,std::memory_order_relaxed);',
''' {static const double menu_period=[]{const char*p=std::getenv("MW34_MENU_FPS");if(!p||!*p)return 0.0;const double v=std::atof(p);return v>=1&&v<=1000?1.0/v:0.0;}();
  if(menu_period>0&&wide_world_frame!=host.frames){
   static LARGE_INTEGER freq{},last{};static HANDLE timer=::CreateWaitableTimerExW(nullptr,nullptr,CREATE_WAITABLE_TIMER_HIGH_RESOLUTION,TIMER_ALL_ACCESS);
   if(!freq.QuadPart)::QueryPerformanceFrequency(&freq);
   LARGE_INTEGER now{};::QueryPerformanceCounter(&now);
   const LONGLONG due=last.QuadPart+LONGLONG(menu_period*double(freq.QuadPart));
   if(last.QuadPart&&now.QuadPart<due){
    const double wait=double(due-now.QuadPart)/double(freq.QuadPart);
    if(wait>0.002&&timer){LARGE_INTEGER d{};d.QuadPart=-LONGLONG((wait-0.0015)*1e7);::SetWaitableTimer(timer,&d,0,nullptr,nullptr,FALSE);::WaitForSingleObject(timer,INFINITE);}
    do ::QueryPerformanceCounter(&now);while(now.QuadPart<due);
    last.QuadPart=due;
   }else last=now;
  }}
 ++host.frames;mw34_frames_presented.store(host.frames,std::memory_order_relaxed);''')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('host_source',type=Path);apply(p.parse_args().host_source)
