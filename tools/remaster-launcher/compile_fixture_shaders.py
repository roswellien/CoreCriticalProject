"""Compile authored fixture-shadow shaders and the compatible private host shaders."""
from pathlib import Path
import argparse,struct,subprocess

def compile_shaders(host,compiler,output):
    output.mkdir(parents=True,exist_ok=True)
    jobs=[('sun_scene.frag','sun_scene_frag',False),('sun_scene.frag','effect_scene_frag',True),
          ('fixture_shadow.vert','fixture_shadow_vert',False),('fixture_shadow.frag','fixture_shadow_frag',False),
          ('sun_tl.vert','sun_tl_vert',False)]
    for source,name,effect in jobs:
        binary=output/(name+'.spv')
        args=[str(compiler.resolve()),'-V','--target-env','vulkan1.0','-S',source.rsplit('.',1)[1]]
        if effect:args.append('-DMW34_EFFECT_LIGHTING=1')
        subprocess.run(args+[str((host/source).resolve()),'-o',str(binary.resolve())],check=True)
        data=binary.read_bytes();words=struct.unpack('<'+'I'*(len(data)//4),data)
        text='// Compiled with compile_fixture_shaders.py from '+source+'.\n'
        text+='inline constexpr std::uint32_t '+name+'_spv[]={\n'
        text+='\n'.join('    '+','.join(f'0x{x:08x}u' for x in words[i:i+8])+',' for i in range(0,len(words),8))+'\n};\n'
        (host/(name+'.h')).write_text(text,encoding='utf-8',newline='\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--host-source',type=Path,required=True);parser.add_argument('--compiler',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();compile_shaders(args.host_source,args.compiler,args.output)
