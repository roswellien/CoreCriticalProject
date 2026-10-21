"""Keep original condition-schematic blend state out of world atmosphere grading."""
import argparse
from pathlib import Path


def apply(host):
    pending = {}

    def edit(name, old, new):
        path = host / name
        source = pending.get(path, path.read_text(encoding='utf-8'))
        if source.count(new) == 1:
            return
        if source.count(old) != 1:
            raise ValueError(f'{name}: expected one status-colour integration anchor')
        pending[path] = source.replace(old, new, 1)

    # Capture ownership while the original preview ancestry still exists;
    # render_scene and apply_atmosphere run after those calls have returned.
    edit('mfc_stage.hpp', 'unsigned hud_role{};float zoom_anchor{};',
         'bool condition_schematic{};unsigned hud_role{};float zoom_anchor{};')
    edit('d3d_provider.inc', 'c.hud_role=hud_deferred_role(type,verts,vcount,wide_hud_role());',
         'c.hud_role=hud_deferred_role(type,verts,vcount,wide_hud_role());c.condition_schematic=override_status_preview();')
    edit('d3d_provider.inc', 'vs::Draw dr{};',
         'vs::Draw dr{};dr.condition_schematic=c.condition_schematic;')
    edit('vk_scene.hpp', 'unsigned detail_role{}; };',
         'unsigned detail_role{};bool condition_schematic{}; };')
    edit('vk_scene.hpp', 'for(size_t at=0;at<s.draws.size();++at){auto& d=s.draws[at];',
         'for(size_t at=0;at<s.draws.size();++at){auto& d=s.draws[at];\n'
         '            // Status previews use original fog colour/factors for per-part damage tint.\n'
         '            if(d.condition_schematic)continue;')
    for path, source in pending.items():
        path.write_text(source, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host', type=Path)
    apply(parser.parse_args().host.resolve(strict=True))
