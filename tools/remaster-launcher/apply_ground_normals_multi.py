"""Allow several terrain normal maps in the ground-normal sidecar (BWNRM1).

Entry 0 keeps the existing desert-ground (txgter_1) matching. Every further
entry stores its texture's RGB565 signature (first two 32-bit pixel words) in
the 8-byte tag field and binds to TL draws whose texture has the same size and
signature. Apply after the sun/shadow/atmosphere host edits.
"""
from pathlib import Path
import argparse

def edit(path,old,new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError(f'Expected one ground-normal anchor in {path.name}: {old[:80]}')
    path.write_text(text.replace(old,new))

def apply(host):
    stage=host/'mesh_override_stage.inc'
    edit(stage,'int ground_normal_texture{-1};','int ground_normal_texture{-1};std::vector<std::array<unsigned,5>> ground_normal_bindings;')
    edit(stage,''' unsigned batches,count;bytes(&batches,4);bytes(&count,4);if(count!=1)throw std::runtime_error("Ground normals: count mismatch");
 char name[32];bytes(name,32);OverrideTexture t{};t.name=name;bytes(&t.width,4);bytes(&t.height,4);bytes(&t.hash,8);
 if(!t.width||!t.height||t.width>4096||t.height>4096)throw std::runtime_error("Ground normals: invalid dimensions");
 t.pixels32.resize(size_t(t.width)*t.height);bytes(t.pixels32.data(),t.pixels32.size()*4);
 o.ground_normal_texture=int(o.normal_textures.size());
 fprintf(stderr,"[GROUND_NORMALS_LOADED] name='%s' %ux%u normal_idx=%d\\n",name,t.width,t.height,o.ground_normal_texture);fflush(stderr);
 o.normal_textures.push_back(std::move(t));
 if(o.log.is_open())o.log<<"{\\"event\\":\\"ground_normals_loaded\\",\\"name\\":\\""<<name<<"\\",\\"dimensions\\":["<<t.width<<","<<t.height<<"],\\"format\\":\\"RGBA8888\\"}\\n";
}''',''' unsigned batches,count;bytes(&batches,4);bytes(&count,4);if(!count||count>64)throw std::runtime_error("Ground normals: count mismatch");
 o.ground_normal_bindings.clear();
 for(unsigned entry=0;entry<count;++entry){
  char name[32];bytes(name,32);if(name[31])throw std::runtime_error("Ground normals: invalid name");
  OverrideTexture t{};t.name=name;bytes(&t.width,4);bytes(&t.height,4);bytes(&t.hash,8);
  if(!t.width||!t.height||t.width>4096||t.height>4096)throw std::runtime_error("Ground normals: invalid dimensions");
  t.pixels32.resize(size_t(t.width)*t.height);bytes(t.pixels32.data(),t.pixels32.size()*4);
  const int index=int(o.normal_textures.size());
  // Entry 0: legacy desert-ground match. Others: tag = RGB565 signature of the colour texture.
  if(!entry)o.ground_normal_texture=index;
  else o.ground_normal_bindings.push_back({t.width,t.height,unsigned(t.hash&0xffffffffu),unsigned(t.hash>>32),unsigned(index)});
  fprintf(stderr,"[GROUND_NORMALS_LOADED] name='%s' %ux%u normal_idx=%d tag=%016llx\\n",name,t.width,t.height,index,(unsigned long long)t.hash);fflush(stderr);
  if(o.log.is_open())o.log<<"{\\"event\\":\\"ground_normals_loaded\\",\\"name\\":\\""<<name<<"\\",\\"dimensions\\":["<<t.width<<","<<t.height<<"],\\"format\\":\\"RGBA8888\\"}\\n";
  o.normal_textures.push_back(std::move(t));
 }
 if(file.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Ground normals: trailing data");
}''')
    edit(host/'d3d_provider.inc','''    if(is_ground){
     bind_normal_idx=o.ground_normal_texture;''','''    if(!is_ground&&t&&readable(t->mem,8)){const unsigned s0=load(t->mem),s1=load(t->mem+4);
     for(const auto& g:o.ground_normal_bindings)if(g[0]==t->width&&g[1]==t->height&&g[2]==s0&&g[3]==s1){bind_normal_idx=int(g[4]);break;}}
    if(is_ground){
     bind_normal_idx=o.ground_normal_texture;''')

def apply_world(host):
    # GPU-retained world terrain (c.model->world) uses the same textures and UVs but has
    # no c.sun_tl; without this it never received the ground normal map, leaving a flat
    # band of terrain near the camera that changed with movement speed.
    edit(host/'d3d_provider.inc','}else if(c.sun_tl&&tex&&override_enabled()){','}else if((c.sun_tl||(c.model&&c.model->world))&&tex&&override_enabled()){')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('host_source',type=Path);h=p.parse_args().host_source;apply(h);apply_world(h)
