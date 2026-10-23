"""Avoid per-draw shared_ptr copies in the atmosphere pass's local worklist."""
from pathlib import Path
import argparse

def apply(host):
    p=host/'vk_scene.hpp';source=p.read_text()
    include='#include "draw_emissions.hpp"'
    target=include+'\n#include "scene_view_references.hpp"'
    if target not in source:
        if source.count(include)!=1:raise RuntimeError('Expected the scene emissions predecessor')
        source=source.replace(include,target,1)
    original='    void apply_atmosphere(Scene &s, const mw34::sun::Settings &sun) {'
    replacement='''    void apply_atmosphere(Scene &s, const mw34::sun::Settings &sun) {
        static const bool reuse=[] {
            const char* value=std::getenv("MW34_ATMOSPHERE_VIEW_REUSE");
            if(!value||!*value||!std::strcmp(value,"0"))return false;
            if(!std::strcmp(value,"1"))return true;
            throw std::runtime_error("MW34_ATMOSPHERE_VIEW_REUSE must be 0 or 1");
        }();
        if(reuse)apply_atmosphere_views<true>(s,sun);else apply_atmosphere_views<false>(s,sun);
    }
    template<bool Reuse> void apply_atmosphere_views(Scene &s, const mw34::sun::Settings &sun) {'''
    if replacement not in source:
        if source.count(original)!=1:raise RuntimeError('Atmosphere entry changed')
        source=source.replace(original,replacement,1)
    start=source.index('    template<bool Reuse> void apply_atmosphere_views(')
    stop=source.index('    void record_shadow(',start)
    section=source[start:stop]
    changes=[
        ('std::vector<std::shared_ptr<const mw34::sun::Tl>> view(s.draws.size());',
         'using References=mw34::submission::SceneViewReferences<mw34::sun::Tl,Reuse>;\n        References references;\n        std::vector<typename References::Reference> view(s.draws.size());',1),
        ('std::shared_ptr<const mw34::sun::Tl> current;','typename References::Reference current;',1),
        ('current = d.sun_tl;','current = references.borrow(d.sun_tl);',2),
        ('current = std::move(tl);','current = references.own(std::move(tl));',2),
        ('view[at] = d.sky_view;','view[at] = references.borrow(d.sky_view);',1),
        ('d.sun_tl = view[at];','d.sun_tl = references.shared(view[at]);',3)]
    for before,after,count in changes:
        if section.count(after)==count:continue
        if section.count(before)!=count:raise RuntimeError(f'Atmosphere reference anchor changed: {before}')
        section=section.replace(before,after)
    source=source[:start]+section+source[stop:]
    helper=Path(__file__).parent/'native-overrides/scene_view_references.hpp';data=helper.read_bytes()
    if p.read_text()!=source:p.write_text(source)
    destination=host/helper.name
    if not destination.exists() or destination.read_bytes()!=data:destination.write_bytes(data)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('host',type=Path);apply(parser.parse_args().host)
