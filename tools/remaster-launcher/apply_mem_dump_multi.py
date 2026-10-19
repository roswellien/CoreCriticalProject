"""Diagnostic: dump the game's static data image (0x5E0000-0x9A2000) at several frames.

MW34_MEM_DUMP_FRAMES=<f1,f2,...> with MW34_MEM_DUMP=<path prefix> writes
<prefix>.<frame>.bin. Output stays local (original game memory).
"""
from pathlib import Path
import argparse

def edit(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError(f'Expected one dump anchor in {path.name}: {old[:80]}')
    path.write_text(text.replace(old,new))

def apply(host):
    edit(host/'vdd.inc',' if(df&&dp&&host.frames==df){',''' {static const std::string frames_list=[]{const char*e=std::getenv("MW34_MEM_DUMP_FRAMES");return std::string(e?e:"");}();
  if(dp&&!frames_list.empty()&&(","+frames_list+",").find(","+std::to_string(host.frames)+",")!=std::string::npos){
   std::vector<std::byte>b(0x9a2000-0x5e0000);runtime.memory().read({0x5e0000},b);
   if(FILE*f=std::fopen((std::string(dp)+"."+std::to_string(host.frames)+".bin").c_str(),"wb")){std::fwrite(b.data(),1,b.size(),f);std::fclose(f);}
   if(!px.empty())if(FILE*f=std::fopen((std::string(dp)+"."+std::to_string(host.frames)+".frame").c_str(),"wb")){const unsigned hdr[3]={w,h,v.pitch};std::fwrite(hdr,4,3,f);std::fwrite(px.data(),1,px.size(),f);std::fclose(f);}
   // Guest heap (0x50000000..mapped) as a second file.
   const unsigned hb=GuestHeap::lo,he=host.gheap.mapped;if(he>hb){std::vector<std::byte>h(he-hb);
    for(unsigned at=hb;at<he;at+=0x10000){const unsigned n=std::min(0x10000u,he-at);if(readable(at,n)){std::vector<std::byte>c(n);runtime.memory().read({at},c);std::memcpy(h.data()+(at-hb),c.data(),n);}}
    if(FILE*f=std::fopen((std::string(dp)+"."+std::to_string(host.frames)+".heap").c_str(),"wb")){std::fwrite(h.data(),1,h.size(),f);std::fclose(f);}}}}
 if(df&&dp&&host.frames==df){''')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('host_source',type=Path);apply(p.parse_args().host_source)
