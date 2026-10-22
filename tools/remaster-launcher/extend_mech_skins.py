"""Stage per-instance original B-H skin selection for all registered chassis.

No artwork generation or publication. The active executable and profile remain
unchanged until the candidate host and its exact content checks pass.
"""
from pathlib import Path
import argparse,hashlib,json,shutil


def stage(source,output):
    source=Path(source);output=Path(output)
    if output.exists() and any(output.iterdir()):raise ValueError('Use a fresh staged source directory')
    output.mkdir(parents=True,exist_ok=True)
    path=source/'mesh_override_stage.inc';before=path.read_bytes();s=before.decode().replace('\r\n','\n')
    assert 'int skin_d_texture{-1};' in s and s.count('bool primary=false,skin_d=false;')==1
    s=s.replace('int skin_d_texture{-1};','std::array<int,8> skin_textures{{-1,-1,-1,-1,-1,-1,-1,-1}};')
    s=s.replace('const char*alternate_env=nullptr){','const char*alternate_env=nullptr,unsigned skin=0){')
    s=s.replace('if(alternate_env)o.batches[at].skin_d_texture=int(offset+index);','if(alternate_env)o.batches[at].skin_textures.at(skin)=int(offset+index);')
    # Parse the complete sidecar before assigning batch indices. Intern exact
    # unchanged images across skins/LODs instead of multiplying their GPU cost.
    a=s.index('void override_load_textures(');b=s.index('void override_load_normals(',a)
    s=s[:a]+'''void override_load_textures(const OverrideModel&model,size_t first,size_t end,const char*alternate_env=nullptr,unsigned skin=0){
 const char*path=std::getenv(alternate_env?alternate_env:model.texture_env);if(!path)return;
 auto&o=override_state();std::ifstream file(path,std::ios::binary);
 auto bytes=[&](void*p,size_t n){if(!file.read(static_cast<char*>(p),std::streamsize(n)))throw std::runtime_error("Replacement textures: incomplete sidecar");};
 char magic[8];bytes(magic,8);if(std::memcmp(magic,"BWTEX1\\0\\0",8))throw std::runtime_error("Replacement textures: wrong format");
 unsigned batches,count;bytes(&batches,4);bytes(&count,4);if(batches!=end-first||!count||count>64||skin>7)throw std::runtime_error("Replacement textures: material count/skin mismatch");
 std::vector<unsigned>bindings(batches),indices;
 for(auto&index:bindings){bytes(&index,4);if(index>=count)throw std::runtime_error("Replacement textures: invalid material index");}
 for(unsigned i=0;i<count;++i){char name[32];bytes(name,32);if(name[31])throw std::runtime_error("Replacement textures: invalid name");OverrideTexture t{};t.name=name;bytes(&t.width,4);bytes(&t.height,4);bytes(&t.hash,8);
  if(!t.width||!t.height||t.width>4096||t.height>4096)throw std::runtime_error("Replacement textures: invalid dimensions");
  t.pixels.resize(size_t(t.width)*t.height);bytes(t.pixels.data(),t.pixels.size()*2);
  indices.push_back(mw34::skins::intern_texture(o.textures,std::move(t)));
 }
 if(file.peek()!=std::char_traits<char>::eof())throw std::runtime_error("Replacement textures: trailing data");
 for(size_t at=first;at<end;++at){const auto index=indices[bindings[at-first]];if(alternate_env)o.batches[at].skin_textures.at(skin)=int(index);else o.batches[at].texture=int(index);o.batches[at].color=0xffffffff;}
 o.log<<"{\\"event\\":\\"textures_loaded\\",\\"model\\":\\""<<model.id<<"\\",\\"skin\\":"<<skin<<",\\"materials\\":"<<count<<",\\"format\\":\\"RGB565\\"}\\n";
}
''' +s[b:]
    old='  if(std::string(model.id)=="bushwacker")override_load_textures(model,first,o.batches.size(),model.lod?"MW34_BUSHWACKER_LOD1_SKIN_D_TEXTURES":"MW34_BUSHWACKER_SKIN_D_TEXTURES");'
    assert old in s
    s=s.replace(old,'  for(unsigned skin=1;skin<8;++skin){const auto key=mw34::skins::binding(model.id,model.lod!=0,skin);override_load_textures(model,first,o.batches.size(),key.c_str(),skin);}')
    start=s.index(' if(result>=0&&std::string(override_models[result].id)=="bushwacker"){')
    end=s.index('\n o.validated_roots.emplace(root,result);',start)
    block=s[start:end]
    block=block.replace('if(result>=0&&std::string(override_models[result].id)=="bushwacker")','if(result>=0)')
    block=block.replace('bool primary=false,skin_d=false;','mw34::skins::Selection selection;')
    block=block.replace('Bushwacker skin:','Mech skin:')
    old='    if(name.size()==14&&name.rfind("bushwacker",0)==0&&name.substr(12)=="_d")skin_d=true;\n    if(name.size()==12&&name.rfind("bushwacker",0)==0)primary=true;'
    assert old in block;block=block.replace(old,'    selection.observe(mw34::skins::texture_skin(model.id,name));')
    a=block.index('  const unsigned skin=skin_d?3:0;');b=block.index('  if(o.announced_roots.emplace',a)
    block=block[:a]+'''  const auto selected=selection.result();
  const unsigned skin=selected.value_or(0);o.source_skins[root]=skin;
  if(!selected)result=-1;
  else if(skin){bool loaded=true,seen=false;for(const auto&batch:o.batches)if(batch.model==unsigned(result)&&batch.texture>=0){seen=true;loaded&=batch.skin_textures.at(skin)>=0;}
   if(!seen||!loaded)result=-1; // Preserve the original skin if an optional alternate set is incomplete.
  }
'''+block[b:]
    s=s[:start]+block+s[end:]
    s=s.replace('if(std::string(model.id)=="bushwacker")o.scope.skin=o.source_skins.at(root);','o.scope.skin=o.source_skins.at(root);')
    s=s.replace('o.scope.skin==3?batch.skin_d_texture:batch.texture','o.scope.skin?batch.skin_textures.at(o.scope.skin):batch.texture')
    assert 'skin_d_texture' not in s and 'skin_d=false' not in s
    (output/path.name).write_text(s,encoding='utf-8')
    # mesh_override_stage.inc is inside Stage; namespace/library declarations
    # must be included at translation-unit scope instead.
    composition=(source/'composition.cpp').read_text()
    (output/'composition.cpp').write_text('#include "mech_skin_selection.hpp"\n'+composition,encoding='utf-8')
    helper=Path(__file__).parent/'native-overrides/mech_skin_selection.hpp';shutil.copy2(helper,output/helper.name)
    (output/'source-identity.json').write_text(json.dumps(dict(source=str(path.resolve()),sha256=hashlib.sha256(before).hexdigest(),scope='Optional replacement colour skin selection only; original simulation untouched.'),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();stage(a.source,a.output)
