"""Compile the authored sun shaders; original game data is not involved."""
from pathlib import Path
import argparse
import struct
import subprocess

def compile_shaders(compiler, output):
    source=Path(__file__).parent/'native-overrides'
    output.mkdir(parents=True,exist_ok=True)
    for stem,stage in [('sun_world','vert'),('sun_model','vert'),('sun_tl','vert'),('sun_scene','frag'),('sun_shadow','vert'),('effect_scene','frag')]:
        effect=stem=='effect_scene'
        path=source/f'{"sun_scene" if effect else stem}.{stage}';binary=output/f'{stem}.{stage}.spv'
        defines=['-DMW34_EFFECT_LIGHTING=1'] if effect else []
        subprocess.run([str(compiler),'-V','--target-env','vulkan1.0',*defines,'-S',stage,str(path),'-o',str(binary)],check=True)
        data=binary.read_bytes();words=struct.unpack('<'+'I'*(len(data)//4),data)
        header=f'// Compiled from authored {path.name}.\ninline constexpr std::uint32_t {stem}_{stage}_spv[]={{\n'
        header+='\n'.join(' '+','.join(f'0x{x:08x}u' for x in words[i:i+8])+',' for i in range(0,len(words),8))+'\n};\n'
        (source/f'{stem}_{stage}.h').write_text(header)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--compiler',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();compile_shaders(a.compiler,a.output)
