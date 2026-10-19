"""Diagnostic: dump each unique sun-lit terrain (TL) texture to a PPM.

Apply to a test host that already has the sun/ground-normal edits. Active only
when MW34_TL_TEXTURE_DUMP names an existing directory; files are named
<guest texture id>_<width>x<height>_<first pixel words>.ppm. Output stays local
(original game artwork must not be committed or shared).
"""
from pathlib import Path
import argparse

def edit(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError(f'Expected one dump anchor in {path.name}: {old[:80]}')
    path.write_text(text.replace(old,new))

def apply(host):
    edit(host/'d3d_provider.inc','''     fprintf(stderr, "[UNIQUE_TL_TEX] tex=%u w=%u h=%u pitch=%u mem=0x%x d0=0x%08x d1=0x%08x ground_n=%d\\n",''','''     if(const char* dump_dir=std::getenv("MW34_TL_TEXTURE_DUMP");dump_dir&&*dump_dir&&t->width&&t->height&&t->width<=4096&&t->height<=4096){
      char name[96];std::snprintf(name,sizeof name,"\\\\%u_%ux%u_%08x%08x.ppm",tex,t->width,t->height,d0,d1);
      std::ofstream ppm(std::string(dump_dir)+name,std::ios::binary);
      if(ppm){ppm<<"P6\\n"<<t->width<<" "<<t->height<<"\\n255\\n";std::vector<unsigned char> row(size_t(t->width)*2),rgb(size_t(t->width)*3);
       for(unsigned y=0;y<t->height;++y){get_bytes(t->mem+y*t->pitch,row.data(),unsigned(row.size()));
        for(unsigned x=0;x<t->width;++x){const unsigned short p=*reinterpret_cast<const unsigned short*>(row.data()+x*2);
         rgb[x*3]=((p>>11)&0x1f)*255/31;rgb[x*3+1]=((p>>5)&0x3f)*255/63;rgb[x*3+2]=(p&0x1f)*255/31;}
        ppm.write(reinterpret_cast<const char*>(rgb.data()),std::streamsize(rgb.size()));}}
     }
     fprintf(stderr, "[UNIQUE_TL_TEX] tex=%u w=%u h=%u pitch=%u mem=0x%x d0=0x%08x d1=0x%08x ground_n=%d\\n",''')

def apply_mark(host):
    # MW34_TL_TEXTURE_MARK=<16 hex digits of the first two pixel words>: paint that texture magenta (diagnostic).
    edit(host/'d3d_provider.inc','rows_in(*t,r.pixels);}','''rows_in(*t,r.pixels);
     if(const char* mark=std::getenv("MW34_TL_TEXTURE_MARK");mark&&*mark&&readable(t->mem,8)){char sig[20];std::snprintf(sig,sizeof sig,"%08x%08x",load(t->mem),load(t->mem+4));
      // Comma-separated signatures; the n-th gets the n-th solid colour.
      static const unsigned short colours[]={0xF81F,0x07E0,0x001F,0xFFE0,0x07FF,0xF800,0xFFFF,0x8010,0x0410,0xFC00,0x841F,0x0000};
      std::string list(mark);size_t at=0;unsigned n=0;
      while(at<=list.size()){size_t end=list.find(',',at);if(end==std::string::npos)end=list.size();
       if(list.compare(at,end-at,sig)==0){for(auto& px:r.pixels)px=colours[n%12];std::fprintf(stderr,"[TL_TEXTURE_MARK] %s colour %u\\n",sig,n);break;}
       at=end+1;++n;}}}''')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('host_source',type=Path);h=p.parse_args().host_source;apply(h);apply_mark(h)
