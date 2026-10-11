"""Prepare an isolated final-resolution Vulkan HUD pass from private v3 components."""
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class HudDraw:
    texture: int
    component_id: str
    logical_destination: tuple
    anchor: str
    clip: tuple
    layer: int
    color: int = 0xffffffff
    font_id: str | None = None


def build(components, output, width, height, user_scale, density, canvas_package, observed_state=None, counter_state=None, counter_scene=None, heat_state=None):
    if not (640 <= width <= 4096 and 480 <= height <= 4096 and .75 <= user_scale <= 1 and 1 <= density <= 8):
        raise ValueError('Unsupported HUD viewport, scale or density')
    data = json.loads(components.read_text())
    manifest = json.loads(components.with_name('manifest.json').read_text())
    if hashlib.sha256(components.read_bytes()).hexdigest() != manifest['outputs']['components.json']:
        raise ValueError('v3 component identity mismatch')
    output.mkdir(parents=True, exist_ok=False)
    scale = min(width / 640, height / 480) * user_scale
    entries, draws = [], []
    gauges = data['layouts']['V640x480']['GAUGES']
    # Explicit anchors for these known components; no generic x>=320 heuristic.
    for name, anchor in [('speed_frame','right-top'),('fuel_frame','right-top'),
                         ('coolant_frame','left-top'),('heat_meter','left-top')]:
        x, y = gauges[name]
        draws.append(HudDraw(len(entries), 'hud_'+name, (x,y), anchor, (0,0,width,height), len(entries)))
        entries.append({'componentId':'hud_'+name,**({'useBitmap':True} if name=='heat_meter' else {})})
    draws.append(HudDraw(len(entries),'sensor_reticule',(0,0),'center',(0,0,width,height),10))
    entries.append({'componentId':'sensor_reticule'})
    # Half-size polygon tip is x=6.5: place it exactly at meter x=16.
    draws.append(HudDraw(len(entries),'hud_allyarrow_right',(9.5,217.75),'left-top',(0,0,width,height),11))
    # User-reviewed preview correction; source package remains unchanged.
    entries.append({'componentId':'hud_allyarrow_right','logicalScale':.5,'vectorColor':'#00eb00'})
    # A diagnostic label tests fresh glyph coverage without invented telemetry.
    draws.append(HudDraw(len(entries),'diagnostic-label',(10,465),'left-top',(0,0,width,height),20,font_id='mech_string'))
    entries.append({'text':'HUD PASS','fontId':'mech_string'})
    state=None
    if observed_state:
        from observe_state import recover
        supplied=json.loads(observed_state.read_text())
        state=recover(Path(supplied['run']),Path(supplied['monitor']))
        if supplied!=state: raise ValueError('Recorded state differs from verified observation')
        placement=state['placement']
        destination=(placement['x'],placement['y']) if placement else (532,348)
        draws.append(HudDraw(len(entries),'recorded-speed',destination,'right-top',(0,0,width,height),21,font_id='observed-Arial-minus8'))
        entries.append({'text':state['selected_speed']['text'],'observed':state['selected_speed'],'fontId':'observed-Arial-minus8'})
    counter_evidence=None
    if counter_scene is not None and not counter_state: raise ValueError('Counter scene requires verified counter state')
    if counter_state:
        from recover_counters import counters
        supplied=json.loads(counter_state.read_text())
        counter_evidence=counters(Path(supplied['run']),Path(supplied['monitor']))
        if supplied!=counter_evidence: raise ValueError('Counter state differs from verified observation')
        for row in counter_evidence['rows']:
            sample=row['selected_render_sample']
            if counter_scene is not None:
                matches=[s for s in row['render_samples'] if s['completed_scenes']==counter_scene]
                if len(matches)!=1: raise ValueError('Counter scene lacks one correlated draw per row')
                sample=matches[0]
            x,y,_,_=sample['destination']
            draws.append(HudDraw(len(entries),f"recorded-counter-{row['source_y']}",(x,y),
                'right-top',(0,0,width,height),22,font_id='observed-Arial-minus10'))
            entries.append({'text':sample['text'],'observed':sample,'fontId':'observed-Arial-minus10'})
    heat_evidence=None
    if heat_state:
        from recover_heat import recover_heat
        supplied=json.loads(heat_state.read_text())
        heat_evidence=recover_heat(Path(supplied['run']),Path(supplied['monitor']))
        if supplied!=heat_evidence: raise ValueError('Heat state differs from verified observation')
        triangle=next(d for d in draws if d.component_id=='hud_allyarrow_right')
        triangle.logical_destination=(9.5,heat_evidence['selected']['result_arrow_y']+6.25)
        top=heat_evidence['selected']['result_crop'][1]
        if top<120:
            # Retain full logical source size; clip UVs to observed visible rows.
            draws.append(HudDraw(len(entries),'hud_heat_bar',(16,163),'left-top',
                (16*scale,(163+top)*scale,15*scale,(120-top)*scale),2))
            entries.append({'componentId':'hud_heat_bar'})
    request={'density':density,'entries':entries}
    request_path=output/'request.json';request_path.write_text(json.dumps(request,indent=2))
    subprocess.run(['node',str(Path(__file__).with_name('rasterize.cjs')),str(components.resolve()),
                    str(request_path.resolve()),str(output.resolve()),str(canvas_package.resolve())],check=True)
    textures=json.loads((output/'textures.json').read_text())['textures']
    initial=bytes((12,24,36,255))*width*height
    blob=bytearray(b'MW34SCN4'+struct.pack('<4I',width,height,len(textures),len(draws))+initial+bytes(width*height*4))
    for texture in textures:
        pixels=(output/texture['file']).read_bytes()
        blob+=struct.pack('<2I',texture['physicalWidth'],texture['physicalHeight'])+pixels
    commands=[(2,2,0,0,width,height,0,0,0,0)]
    records=[]
    for draw in sorted(draws,key=lambda d:d.layer):
        t=textures[draw.texture];lw,lh=t['logicalWidth'],t['logicalHeight'];x,y=draw.logical_destination
        if draw.anchor=='right-top': x=width-(640-x)*scale;y*=scale
        elif draw.anchor=='center': x=width/2-lw*scale/2;y=height/2-lh*scale/2
        elif draw.anchor=='left-center': x*=scale;y=height/2-lh*scale/2
        else: x*=scale;y*=scale
        # Padding expands the host quad, while component size stays logical.
        pad=t['padding']/density*scale
        left,top=x-pad,y-pad
        right=left+t['physicalWidth']/density*scale;bottom=top+t['physicalHeight']/density*scale
        cx,cy,cw,ch=draw.clip
        clipped=(max(left,cx),max(top,cy),min(right,cx+cw),min(bottom,cy+ch))
        l,u,r,b=clipped
        if not (r>l and b>u): raise ValueError('Empty HUD clip')
        uv=((l-left)/(right-left),(u-top)/(bottom-top),(r-left)/(right-left),(b-top)/(bottom-top))
        blob+=struct.pack('<11I',draw.texture,6,2,1,0,1,3,3,0,1,0)
        for vx,vy,tx,ty in [(l,u,uv[0],uv[1]),(r,u,uv[2],uv[1]),(r,b,uv[2],uv[3]),
                            (l,u,uv[0],uv[1]),(r,b,uv[2],uv[3]),(l,b,uv[0],uv[3])]:
            blob+=struct.pack('<4fII2f',vx-.5,vy-.5,1,1,draw.color,0,tx,ty)
        commands.append((1,len(records),0,0,0,0,0,0,0,0))
        records.append(dict(component_id=draw.component_id,font_id=draw.font_id,layer=draw.layer,
                            texture=draw.texture,logical_size=[lw,lh],component_rect=[x,y,lw*scale,lh*scale],
                            host_quad=[left,top,right,bottom],clip=list(draw.clip),clipped_quad=list(clipped),
                            alpha='straight',depth_write=False))
    blob+=struct.pack('<I',len(commands))+b''.join(struct.pack('<10I',*op) for op in commands)
    (output/'hud.replay').write_bytes(blob)
    receipt={'scope':'Isolated final-resolution HUD; no recovered telemetry or live replacement',
             'viewport':[width,height],'scale':scale,'density':density,'draws':records,
             'reticle_center':[width/2,height/2], 'telemetry_source':state,'counter_source':counter_evidence,'counter_scene':counter_scene,'heat_source':heat_evidence,
             'state_placement':(state['placement'] or 'Prototype placement; original screen destination unproven') if state else None,
             'depth':'isolated depth clear to zero; quads at one, no writes; world depth untouched by integration',
             'files':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                      [components,components.with_name('manifest.json'),Path(__file__),Path(__file__).with_name('rasterize.cjs'),ROOT/'tools/hud-prototype/renderer.js',
                       *([observed_state,Path(__file__).with_name('observe_state.py')] if observed_state else []),
                       *([counter_state,Path(__file__).with_name('recover_counters.py'),Path(__file__).with_name('observe_state.py')] if counter_state else []),
                       *([heat_state,Path(__file__).with_name('recover_heat.py'),Path(__file__).with_name('verify_heat.py')] if heat_state else [])]}}
    (output/'hud.json').write_text(json.dumps(receipt,indent=2))
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('components',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--width',type=int,default=3440);parser.add_argument('--height',type=int,default=1440)
    parser.add_argument('--scale',type=float,default=1);parser.add_argument('--density',type=float,default=3)
    parser.add_argument('--canvas-package',type=Path,required=True)
    parser.add_argument('--observed-state',type=Path)
    parser.add_argument('--counter-state',type=Path)
    parser.add_argument('--counter-scene',type=int)
    parser.add_argument('--heat-state',type=Path)
    a=parser.parse_args();print(json.dumps(build(a.components,a.output,a.width,a.height,a.scale,a.density,a.canvas_package,a.observed_state,a.counter_state,a.counter_scene,a.heat_state),indent=2))
