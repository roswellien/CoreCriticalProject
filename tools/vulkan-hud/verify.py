"""Independent straight-alpha/bilinear oracle for the isolated Vulkan HUD pass."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
from PIL import Image, ImageChops
from prepare import build, ROOT


def oracle(directory, receipt):
    width,height=receipt['viewport']
    result=bytearray(bytes((12,24,36))*width*height)
    textures=json.loads((directory/'textures.json').read_text())['textures']
    for draw in receipt['draws']:
        t=textures[draw['texture']];tw,th=t['physicalWidth'],t['physicalHeight']
        data=(directory/t['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==t['sha256']
        # All sides of the two-pixel border must be fully transparent.
        for yy in range(th):
            for xx in range(tw):
                if xx<2 or yy<2 or xx>=tw-2 or yy>=th-2:
                    assert data[(yy*tw+xx)*4+3]==0, 'Raster escaped padded logical extent'
        left,top,right,bottom=draw['host_quad'];l,u,r,b=draw['clipped_quad']
        for y in range(max(0,math.ceil(u-.5)),min(height,math.ceil(b-.5))):
            sy=(y+.5-top)/(bottom-top)*th-.5;iy=math.floor(sy);fy=sy-iy
            for x in range(max(0,math.ceil(l-.5)),min(width,math.ceil(r-.5))):
                sx=(x+.5-left)/(right-left)*tw-.5;ix=math.floor(sx);fx=sx-ix
                color=[0.0]*4
                for dx,dy,weight in [(0,0,(1-fx)*(1-fy)),(1,0,fx*(1-fy)),(0,1,(1-fx)*fy),(1,1,fx*fy)]:
                    start=(max(0,min(th-1,iy+dy))*tw+max(0,min(tw-1,ix+dx)))*4
                    for c in range(4): color[c]+=data[start+c]*weight
                start=(y*width+x)*3;alpha=color[3]/255
                for c in range(3): result[start+c]=max(0,min(255,round(color[c]*alpha+result[start+c]*(1-alpha))))
    return Image.frombytes('RGB',(width,height),bytes(result))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('components',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--canvas-package',type=Path,required=True)
    a=parser.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    executable=ROOT/'build/vulkan-replay/Release/mw34_vulkan_replay.exe'
    shaders=ROOT/'build/vulkan-replay'
    env=os.environ.copy();env['VK_LAYER_PATH']=str(ROOT/'local/tools/vulkan-sdk-portable/Bin')
    env['VK_IMPLICIT_LAYER_PATH']=str(ROOT/'local/tools/empty-implicit-layers')
    results=[]
    for width,height,size,density in [(640,480,1,1),(1920,1440,1,3),(2560,1440,1,3),
                                      (3440,1440,1,3),(3440,1440,.75,3),(640,480,1,4)]:
        directory=a.output/f'{width}x{height}-size{size}-density{density}'
        receipt=build(a.components,directory,width,height,size,density,a.canvas_package)
        output=directory/'vulkan.ppm'
        run=subprocess.run([str(executable),str((directory/'hud.replay').resolve()),str(shaders),str(output.resolve()),
                            '0.5','captured','1','d32','rgba8'],capture_output=True,text=True,env=env,timeout=30)
        (directory/'run.txt').write_text(run.stdout+run.stderr)
        assert run.returncode==0 and 'zero validation warnings/errors' in run.stdout
        expected=oracle(directory,receipt);actual=Image.open(output).convert('RGB')
        expected.save(directory/'oracle.png');actual.save(directory/'vulkan.png')
        difference=ImageChops.difference(expected,actual);difference.save(directory/'difference.png')
        maximum=max(high for low,high in difference.getextrema())
        if maximum>2: raise ValueError(f'{directory}: GPU/oracle discrepancy {maximum}')
        reticle=next(d for d in receipt['draws'] if d['component_id']=='sensor_reticule')['component_rect']
        assert reticle[0]+reticle[2]/2==width/2 and reticle[1]+reticle[3]/2==height/2
        assert receipt['draws'][0]['logical_size']==[28,78]
        results.append({'viewport':[width,height],'size':size,'density':density,'maximum_channel_error':maximum,
                        'checked_pixels':width*height,'reticle_center':receipt['reticle_center']})
    report={'scope':'Isolated v3 HUD assets, fresh diagnostic glyphs, no gameplay telemetry or replacement',
            'cases':results,'validation_messages':0,
            'files':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                     [Path(__file__),executable,*shaders.glob('*.spv')]}}
    (a.output/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))


if __name__=='__main__': main()
