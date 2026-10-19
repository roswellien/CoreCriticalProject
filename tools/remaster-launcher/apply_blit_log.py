"""Diagnostic: log DirectDraw blits during the first frames (MW34_BLIT_LOG=<file>, MW34_BLIT_LOG_FRAMES=<n>)."""
from pathlib import Path
import argparse
def edit(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError(f'Expected one blit-log anchor in {path.name}: {old[:80]}')
    path.write_text(text.replace(old,new))
def apply(host):
    edit(host/'vdd.inc','void blit(const VSurface&d,RECT dr,const VSurface&s,RECT sr,bool key,unsigned klo,unsigned khi){','''void blit(const VSurface&d,RECT dr,const VSurface&s,RECT sr,bool key,unsigned klo,unsigned khi){
 {static FILE*bl=[]{const char*p=std::getenv("MW34_BLIT_LOG");return p&&*p?std::fopen(p,"w"):nullptr;}();static const unsigned lim=[]{const char*p=std::getenv("MW34_BLIT_LOG_FRAMES");return p?unsigned(std::atoi(p)):0u;}();
  if(bl&&host.frames<lim){std::fprintf(bl,"%u src %u %ux%u [%ld %ld %ld %ld] -> dst %u %ux%u [%ld %ld %ld %ld] key %d\\n",host.frames,s.guest,s.width,s.height,sr.left,sr.top,sr.right,sr.bottom,d.guest,d.width,d.height,dr.left,dr.top,dr.right,dr.bottom,int(key));std::fflush(bl);}}''')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('host_source',type=Path);apply(p.parse_args().host_source)
