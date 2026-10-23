"""Reuse byte-identical widescreen lighting views in scene-owned immutable runs."""
from pathlib import Path
import argparse

def apply(host):
    scene=host/'vk_scene.hpp';wide=host/'widescreen_stage.inc'
    files={scene:scene.read_text(),wide:wide.read_text()}
    changes={scene:[('#include "draw_emissions.hpp"','#include "draw_emissions.hpp"\n#include "wide_lighting_reuse.hpp"'),
        ('mw34::submission::DrawEmissions emissions;','mw34::submission::DrawEmissions emissions;\n    mw34::submission::WideLightingViews<mw34::sun::Tl> wide_views;')],
        wide:[('void wide_adapt_tl(mw34::vkscene::Scene&sc,',
        '''static bool wide_lighting_reuse_enabled(){
 static const bool enabled=[]{const char*value=std::getenv("MW34_WIDE_LIGHT_REUSE");
  if(!value||!*value||!std::strcmp(value,"0"))return false;
  if(!std::strcmp(value,"1"))return true;
  throw std::runtime_error("MW34_WIDE_LIGHT_REUSE must be 0 or 1");}();return enabled;
}
void wide_adapt_tl(mw34::vkscene::Scene&sc,'''),
        ('if(d.sun_tl){auto light=std::make_shared<mw34::sun::Tl>(*d.sun_tl);light->projection[1]/=k;light->projection[3]=a+(light->projection[3]+.5f-a)/k-.5f;d.sun_tl=std::move(light);}',
         '''if(d.sun_tl){if(wide_lighting_reuse_enabled()){auto light=*d.sun_tl;light.projection[1]/=k;light.projection[3]=a+(light.projection[3]+.5f-a)/k-.5f;d.sun_tl=sc.wide_views.capture(light,false);}
   else{auto light=std::make_shared<mw34::sun::Tl>(*d.sun_tl);light->projection[1]/=k;light->projection[3]=a+(light->projection[3]+.5f-a)/k-.5f;d.sun_tl=std::move(light);}}'''),
        ('if(d.sky_view){auto view=std::make_shared<mw34::sun::Tl>(*d.sky_view);view->projection[1]/=k;view->projection[3]=a+(view->projection[3]+.5f-a)/k-.5f;d.sky_view=std::move(view);}',
         '''if(d.sky_view){if(wide_lighting_reuse_enabled()){auto view=*d.sky_view;view.projection[1]/=k;view.projection[3]=a+(view.projection[3]+.5f-a)/k-.5f;d.sky_view=sc.wide_views.capture(view,true);}
   else{auto view=std::make_shared<mw34::sun::Tl>(*d.sky_view);view->projection[1]/=k;view->projection[3]=a+(view->projection[3]+.5f-a)/k-.5f;d.sky_view=std::move(view);}}''')]}
    for path,replacements in changes.items():
        for before,after in replacements:
            if after in files[path]:continue
            if files[path].count(before)!=1:raise RuntimeError(f'Unexpected widescreen lighting anchor in {path.name}: {before[:60]}')
            files[path]=files[path].replace(before,after,1)
    helper=Path(__file__).parent/'native-overrides/wide_lighting_reuse.hpp';data=helper.read_bytes()
    for path,text in files.items():
        if path.read_text()!=text:path.write_text(text)
    destination=host/helper.name
    if not destination.exists() or destination.read_bytes()!=data:destination.write_bytes(data)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('host',type=Path);apply(parser.parse_args().host)
