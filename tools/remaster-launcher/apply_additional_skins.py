"""Add named skin resources to the original Mech Lab selector in a staged host."""
import argparse
from pathlib import Path


def apply(host):
    host = Path(host)
    pending = {}

    def edit(name, old, new):
        path = host / name
        text = pending.get(path, path.read_text(encoding='utf-8'))
        if new in text:
            return
        if text.count(old) != 1:
            raise ValueError(f'{name}: expected one additional-skin anchor: {old[:75]}')
        pending[path] = text.replace(old, new, 1)

    edit('composition.cpp', '#include "mech_skin_selection.hpp"',
         '#include "mech_skin_selection.hpp"\n#include "additional_skins.hpp"\n#include <filesystem>')
    edit('mfc_stage.hpp', '#include "mesh_override_stage.inc"',
         '#include "mesh_override_stage.inc"\n #include "additional_skins_stage.inc"\n #include "mechlab_skins_stage.inc"')
    edit('mfc_stage.hpp','void*remaster_body_inner(State*s,unsigned target,void*p,Body body){void*result{};',
         'void*remaster_body_inner(State*s,unsigned target,void*p,Body body){void*result{};\n'
         '  if(target==0x44cf70||target==0x44b1c0)return mechlab_skin_body(s,target,p,body);\n'
         '  if(target==0x448a20)mechlab_skin_closed();')
    edit('body_dispatch.hpp','0x448960U,0x448a20U,','0x448960U,0x448a20U,0x44b1c0U,0x44cf70U,')
    edit('mesh_override_stage.inc', 'std::array<int,8> skin_textures{{-1,-1,-1,-1,-1,-1,-1,-1}};',
         'std::vector<int> skin_textures=std::vector<int>(8,-1);')
    edit('mesh_override_stage.inc', 'const char*alternate_env=nullptr,unsigned skin=0){',
         'const char*alternate_env=nullptr,unsigned skin=0,const char*direct_path=nullptr){')
    edit('mesh_override_stage.inc', 'const char*path=std::getenv(alternate_env?alternate_env:model.texture_env);if(!path)return;',
         'const char*path=direct_path?direct_path:std::getenv(alternate_env?alternate_env:model.texture_env);if(!path)return;')
    edit('mesh_override_stage.inc',
         'const char*path=direct_path?direct_path:std::getenv(alternate_env?alternate_env:model.texture_env);if(!path)return;\n auto&o=override_state();std::ifstream file(path,std::ios::binary);',
         'const char*path=direct_path?direct_path:std::getenv(alternate_env?alternate_env:model.texture_env);if(!path)return;\n auto&o=override_state();std::ifstream file(std::filesystem::path(additional_skin_wide(path)),std::ios::binary);')
    edit('mesh_override_stage.inc', 'skin>7)', 'skin>135)')
    edit('mesh_override_stage.inc', 'if(alternate_env)o.batches[at].skin_textures.at(skin)=int(index);',
         'if(alternate_env||direct_path){auto& skins=o.batches[at].skin_textures;if(skins.size()<=skin)skins.resize(skin+1,-1);skins.at(skin)=int(index);}')
    edit('mesh_override_stage.inc', '  override_load_normals(model,first,o.batches.size());',
         '  override_load_normals(model,first,o.batches.size());\n  additional_skins_load(model,first,o.batches.size());')
    edit('mesh_override_stage.inc', 'o.scope.skin=o.source_skins.at(root);o.scope.preview=override_status_preview();',
         'o.scope.preview=override_status_preview();o.scope.skin=additional_skin_for(o.source_skins.at(root),root,unsigned(id),o.scope.preview);')
    for name in ('additional_skins.hpp', 'additional_skins_stage.inc', 'mechlab_skins_stage.inc'):
        pending[host/name] = (Path(__file__).parent/'native-overrides'/name).read_text(encoding='utf-8')
    for path, text in pending.items():
        path.write_text(text, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('host', type=Path)
    apply(p.parse_args().host)
