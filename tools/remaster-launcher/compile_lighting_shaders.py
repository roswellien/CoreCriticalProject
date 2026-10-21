"""Compile the authored sun/effect fragment variants using the existing compiler."""
from pathlib import Path
import argparse
import struct
import subprocess

def compile_shaders(compiler,output):
    source=Path(__file__).parent/'native-overrides'
    output.mkdir(parents=True,exist_ok=True)
    for effect in (False,True):
        name='effect_scene_frag' if effect else 'sun_scene_frag'
        binary=output/(name+'.spv')
        args=[str(compiler.resolve()),'-V','--target-env','vulkan1.0','-S','frag']
        if effect:args.append('-DMW34_EFFECT_LIGHTING=1')
        subprocess.run(args+[str((source/'sun_scene.frag').resolve()),'-o',str(binary.resolve())],check=True)
        data=binary.read_bytes();words=struct.unpack('<'+'I'*(len(data)//4),data)
        text='// Compiled from authored sun_scene.frag; use compile_lighting_shaders.py.\n'
        text+=f'inline constexpr std::uint32_t {name}_spv[]={{\n'
        text+='\n'.join('    '+','.join(f'0x{v:08x}u' for v in words[i:i+8])+',' for i in range(0,len(words),8))+'\n};\n'
        (source/(name+'.h')).write_text(text,encoding='utf-8',newline='\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--compiler',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();compile_shaders(a.compiler,a.output)
