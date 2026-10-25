"""Defer replacement mesh/skin reads until an original instance needs them.

Apply to a fresh completed Mech Lab additional-skins host snapshot. Existing
roster/skin identification, payload validation and renderer paths are retained.
The maintained base mesh template predates current readers; never copy it over
a completed host to apply this change.
"""
import argparse
from pathlib import Path


def apply(host):
    host = Path(host)
    pending = {}

    def edit(name, old, new):
        path = host / name
        text = pending.get(path, path.read_text(encoding='utf-8'))
        if text.count(old) != 1:
            raise ValueError(f'{name}: missing/ambiguous lazy resource anchor: {old[:75]}')
        pending[path] = text.replace(old, new, 1)

    mesh = 'mesh_override_stage.inc'
    edit(mesh, 'struct OverrideState{',
         'struct OverrideState{std::map<unsigned,std::pair<size_t,size_t>> model_ranges;'
         'std::set<std::pair<unsigned,unsigned>> skin_attempts;')
    edit(mesh, ' for(unsigned id=0;id<override_models.size();++id){const auto&model=override_models[id];const char*path=std::getenv(model.mesh_env);if(!path)continue;',
         ''' override_load_ground_normals();o.loaded=true;
}
void override_load_model(unsigned id){
 auto&o=override_state();override_load();if(o.model_ranges.count(id))return;
 const auto&model=override_models.at(id);const char*path=override_mesh_env(model);
 if(!path)throw std::runtime_error("Replacement models: requested disabled model");
 const auto started=::GetTickCount64();
 {''')
    edit(mesh, '''  for(unsigned skin=1;skin<8;++skin){const auto key=mw34::skins::binding(model.id,model.lod!=0,skin);override_load_textures(model,first,o.batches.size(),key.c_str(),skin);}
  override_load_normals(model,first,o.batches.size());
  additional_skins_load(model,first,o.batches.size());''',
         '''  override_load_normals(model,first,o.batches.size());
  o.model_ranges.emplace(id,std::pair{first,o.batches.size()});
  std::fprintf(stderr,"Model resource ready: chassis=%s lod=%u batches=%zu elapsed_ms=%llu\\n",model.id,model.lod,o.batches.size()-first,(unsigned long long)(::GetTickCount64()-started));''')
    edit(mesh, ''' }override_load_ground_normals();
 o.loaded=true;
}
unsigned override_parent''', ''' }
}
bool override_load_skin(unsigned id,unsigned skin){
 auto&o=override_state();override_load_model(id);if(!skin)return true;
 const auto&model=override_models.at(id);const auto [first,end]=o.model_ranges.at(id);
 if(!o.skin_attempts.count({id,skin})){
  const auto started=::GetTickCount64();
  if(skin<8){const auto key=mw34::skins::binding(model.id,model.lod!=0,skin);override_load_textures(model,first,end,key.c_str(),skin);}
  else additional_skins_load(model,first,end,skin);
  o.skin_attempts.emplace(id,skin);
  std::fprintf(stderr,"Skin resource checked: chassis=%s lod=%u skin=%u elapsed_ms=%llu\\n",model.id,model.lod,skin,(unsigned long long)(::GetTickCount64()-started));
 }
 bool seen=false;for(size_t i=first;i<end;++i)if(o.batches[i].texture>=0){seen=true;
  if(skin>=o.batches[i].skin_textures.size()||o.batches[i].skin_textures[skin]<0)return false;}
 return seen;
}
unsigned override_parent''')
    edit(mesh, '''  if(!selected)result=-1;
  else if(skin){bool loaded=true,seen=false;for(const auto&batch:o.batches)if(batch.model==unsigned(result)&&batch.texture>=0){seen=true;loaded&=batch.skin_textures.at(skin)>=0;}
   if(!seen||!loaded)result=-1; // Preserve the original skin if an optional alternate set is incomplete.
  }''', '''  if(!selected)result=-1;
  else if(!override_load_skin(unsigned(result),skin))result=-1; // Preserve an unavailable optional original appearance.''')
    # Retain current maintained catalog/preference support and load the selected
    # addition before its existing per-material completeness check.
    path = host / 'additional_skins_stage.inc'
    text = (Path(__file__).parent / 'native-overrides' / path.name).read_text(encoding='utf-8')
    old = '    if(selected&&(player||local_preview)&&result&&!additional_skins.verified.count({model,result})){'
    if text.count(old) != 1:
        raise ValueError('Missing additional skin completeness anchor')
    pending[path] = text.replace(old, old + '\n        if(!override_load_skin(model,result))throw std::runtime_error("Selected mech skin textures are unavailable");', 1)
    for path, text in pending.items():
        path.write_text(text, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host)
