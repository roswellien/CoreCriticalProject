"""Apply the original-layout frontend canvas to a fresh native host snapshot."""
from pathlib import Path
import argparse
import shutil


def replace(path, old, new):
    text=path.read_text()
    if text.count(old)!=1:raise RuntimeError(f'{path.name}: expected one source contract: {old[:70]}')
    path.write_text(text.replace(old,new))


def apply(host):
    for name in ('frontend_canvas.hpp','frontend_stage.inc'):
        shutil.copyfile(Path(__file__).parent/'native-overrides'/name,host/name)
    stage=host/'mfc_stage.hpp'
    replace(stage,' #include "widescreen_stage.inc"',' #include "widescreen_stage.inc"\n #include "frontend_stage.inc"')
    replace(stage,' void*remaster_body(State*s,unsigned target,void*p,Body body){void*result{};',
            ' void*remaster_body(State*s,unsigned target,void*p,Body body){void*result{};\n  if(target==0x448960||target==0x448a20)return frontend_body(s,target,p,body);')
    replace(stage,'POINT pt{LONG(load(a)),LONG(load(a+4))};BOOL ok=n=="ClientToScreen"?',
            'POINT pt{LONG(load(a)),LONG(load(a+4))};if(n=="ClientToScreen")frontend_input_point(pt,true,W2(0));BOOL ok=n=="ClientToScreen"?')
    replace(stage,'::ScreenToClient(W2(0),&pt);store(a,unsigned(pt.x));',
            '::ScreenToClient(W2(0),&pt);if(ok&&n=="ScreenToClient")frontend_input_point(pt,false,W2(0));store(a,unsigned(pt.x));')
    wide=host/'widescreen_stage.inc'
    replace(wide,'unsigned wide_hud_role(){if(!wide_on())return WideWorld;',
            'unsigned wide_hud_role(){if(frontend_on()||!wide_on())return WideWorld;')
    replace(wide,'if(!wide_on()||!role)return;','if(frontend_on()||!wide_on()||!role)return;')
    vk=host/'vk_scene.hpp'
    replace(vk,'#include "fxaa_frag.h"','#include "fxaa_frag.h"\n#include "frontend_canvas.hpp"')
    replace(vk,'    bool hud{};','    bool frontend_canvas{};\n    bool hud{};')
    replace(vk,'    float current_scale() const { return scale; }','    bool frontend_canvas() const { return target_frontend; }\n    float current_scale() const { return scale; }')
    replace(vk,'if (s.width != width || s.height != height || scale_req != scale) target(s.width, s.height);',
            'if (s.width != width || s.height != height || scale_req != scale || s.frontend_canvas != target_frontend) target(s.width, s.height, s.frontend_canvas);')
    replace(vk,'    unsigned rw{}, rh{};','    bool target_frontend{};\n    unsigned rw{}, rh{};')
    replace(vk,'    void target(unsigned w, unsigned h) {','    void target(unsigned w, unsigned h, bool frontend) {\n        target_frontend=frontend;')
    replace(vk,'if(widescreen()){rw=3440;rh=1440;}',
            'if(widescreen()){if(target_frontend){const auto fit=mw34::frontend::CanvasFit::fit(w,h,remaster_width(),remaster_height());rw=unsigned(fit.width);rh=unsigned(fit.height);}else{rw=3440;rh=1440;}}')
    provider=host/'d3d_provider.inc'
    replace(provider,'vs::Scene sc{};sc.width=rt->width;',
            'vs::Scene sc{};sc.frontend_canvas=frontend_on();sc.width=rt->width;')
    replace(provider,'if(want!=sr->current_scale()){rescale=true;',
            'if(want!=sr->current_scale()||sr->frontend_canvas()!=frontend_on()){rescale=true;')
    replace(host/'gpu_hud.inc','hud_sc.hud=true;hud_sc.width=rt.width;',
            'hud_sc.hud=true;hud_sc.frontend_canvas=host.sren&&host.sren->frontend_canvas();hud_sc.width=rt.width;')
    vdd=host/'vdd.inc'
    replace(vdd,'void gpu_fill(const VSurface&d,RECT r,unsigned c){auto*rt=vsurface(host.res_rt);namespace vs=mw34::vkscene;vs::Scene sc{};',
            'void gpu_fill(const VSurface&d,RECT r,unsigned c){auto*rt=vsurface(host.res_rt);namespace vs=mw34::vkscene;vs::Scene sc{};sc.frontend_canvas=host.sren->frontend_canvas();')
    replace(vdd,'v.pitch,wide_on()&&wide_world_frame==host.frames)',
            'v.pitch,wide_on()&&!frontend_on()&&wide_world_frame==host.frames)')
    replace(vdd,'if(wide_on()&&wide_world_frame!=host.frames){',
            'if(wide_on()&&(frontend_on()||wide_world_frame!=host.frames)){')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('host_source',type=Path)
    apply(parser.parse_args().host_source.resolve(strict=True))
