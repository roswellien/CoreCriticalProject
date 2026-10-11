"""Independent pixel/depth oracle for authored ordered clears and opaque copies."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
from PIL import Image

def command(*values):
    return tuple(values)+(0,)*(10-len(values))

def depth_bits(value):
    return struct.unpack('<I',struct.pack('<f',value))[0]

def package(ops):
    data=bytearray(b'MW34SCN4'+struct.pack('<4I',8,8,2,2))
    data+=bytes((0,0,0,255))*64+struct.pack('<64f',*([0]*64))
    data+=struct.pack('<2I',1,1)+bytes((255,255,255,255))
    source=bytes(channel for y in range(4) for x in range(4) for channel in (x*85,y*85,255,255))
    data+=struct.pack('<2I',4,4)+source
    for z,color in ((.75,0xffff0000),(.5,0xff00ff00)):
        data+=struct.pack('<11I',0,6,2,1,0,0,3,3,0,0,1)
        for x,y in ((-.5,-.5),(7.5,-.5),(7.5,7.5),(-.5,-.5),(7.5,7.5),(-.5,7.5)):
            data+=struct.pack('<4fII2f',x,y,z,1,color,0,.5,.5)
    data+=struct.pack('<I',len(ops))
    for op in ops:data+=struct.pack('<10I',*op)
    return data

def oracle(ops,scale):
    pixels=[(0,0,0)]*64;depth=[0]*64
    for op in ops:
        if op[0]==1:
            z,color=((.75,(255,0,0)),(.5,(0,255,0)))[op[1]]
            for i in range(64):
                if z>depth[i]:pixels[i]=color;depth[i]=z
        elif op[0]==2:
            _,flags,x,y,w,h,argb,bits,*_=op
            z=struct.unpack('<f',struct.pack('<I',bits))[0]
            for yy in range(y,y+h):
                for xx in range(x,x+w):
                    i=yy*8+xx
                    if flags&1:pixels[i]=((argb>>16)&255,(argb>>8)&255,argb&255)
                    if flags&2:depth[i]=z
        else:
            _,_,sx,sy,dx,dy,w,h,*_=op
            for y in range(h):
                for x in range(w):pixels[(dy+y)*8+dx+x]=((sx+x)*85,(sy+y)*85,255)
    return bytes(c for y in range(8*scale) for x in range(8*scale) for c in pixels[(y//scale)*8+x//scale])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable',type=Path);parser.add_argument('shaders',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).resolve().parents[2];env=os.environ.copy()
    env['VK_LAYER_PATH']=str(root/'local/tools/vulkan-sdk-portable/Bin')
    env['VK_IMPLICIT_LAYER_PATH']=str(root/'local/tools/empty-implicit-layers')
    draw0=command(1,0);draw1=command(1,1)
    copy=command(3,1,1,1,3,3,2,2)
    cases={
        'color_clear_between_draws':[draw0,command(2,1,2,2,4,4,0xff0000ff,depth_bits(0)),draw1],
        'depth_clear_between_draws':[draw0,command(2,2,2,2,4,4,0,depth_bits(0)),draw1],
        'combined_clear_between_draws':[draw0,command(2,3,2,2,4,4,0xff0000ff,depth_bits(0)),draw1],
        'copy_retains_depth':[draw0,copy,draw1],
        'copy_then_clear':[draw0,copy,command(2,1,4,4,1,1,0xffffff00,depth_bits(0)),draw1],
        'copy_before_geometry':[copy,draw0,draw1],
    }
    results=[]
    def run(name,data,depth,scale,color='rgba8'):
        path=args.output/(name+'.replay');path.write_bytes(data)
        output=args.output/(name+'.ppm')
        result=subprocess.run([str(args.executable.resolve()),str(path.resolve()),str(args.shaders.resolve()),str(output.resolve()),'0.5','captured',str(scale),depth,color],env=env,capture_output=True,text=True,timeout=30)
        (args.output/(name+'.log')).write_text(result.stdout+result.stderr)
        return result,output
    for depth in ('d32','d16'):
        for scale in (1,3):
            for name,ops in cases.items():
                key=f'{name}-{depth}-{scale}';result,output=run(key,package(ops),depth,scale)
                if result.returncode or 'zero validation warnings/errors' not in result.stdout:raise ValueError(f'{key}: render/validation failed')
                actual=Image.open(output).convert('RGB').tobytes();expected=oracle(ops,scale)
                if actual!=expected:raise ValueError(f'{key}: pixel mismatch')
                results.append({'case':key,'exact_pixels':64*scale*scale})
    controls={
        'unknown_command':([command(99),draw0,draw1],'Unknown replay command'),
        'overflow_rectangle':([command(2,1,0xffffffff,0,2,2,0,0),draw0,draw1],'Clear command limits'),
        'nan_depth':([command(2,2,0,0,8,8,0,0x7fc00000),draw0,draw1],'Clear command limits'),
        'copy_out_of_bounds':([command(3,1,3,3,0,0,2,2),draw0,draw1],'Copy rectangle limits'),
        'duplicate_draw':([draw0,draw0,draw1],'Repeated/invalid ordered draw'),
        'omitted_draw':([draw0],'Omitted ordered draw'),
    }
    rejected=[]
    for name,(ops,reason) in controls.items():
        result,_=run(name,package(ops),'d32',1)
        if not result.returncode or reason not in result.stderr:raise ValueError(f'{name}: incorrect rejection')
        rejected.append(name)
    result,_=run('rgb565_copy_unsupported',package(cases['copy_retains_depth']),'d32',1,'rgb565')
    if not result.returncode or 'require RGBA8' not in result.stderr:raise ValueError('RGB565 copy was not rejected')
    rejected.append('rgb565_copy_unsupported')
    report={'scope':'Authored ordered GPU commands; no live MW3 clear/HUD equivalence claim',
            'executable_sha256':hashlib.sha256(args.executable.read_bytes()).hexdigest(),
            'cases':results,'rejected_controls':rejected,'exact_pixels':sum(r['exact_pixels'] for r in results)}
    (args.output/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
