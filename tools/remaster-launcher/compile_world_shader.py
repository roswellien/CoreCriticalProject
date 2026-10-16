"""Compile the project-authored world bridge shader using an existing compiler."""
from pathlib import Path
import argparse
import struct
import subprocess

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',type=Path,required=True)
    parser.add_argument('--binary',type=Path,required=True,help='Private local SPIR-V output')
    args=parser.parse_args()
    source=Path(__file__).parent/'native-overrides/world_scene.vert'
    args.binary.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run([str(args.compiler.resolve()),'-V','--target-env','vulkan1.0','-S','vert',str(source.resolve()),'-o',str(args.binary.resolve())],check=True)
    code=args.binary.read_bytes()
    words=struct.unpack('<'+'I'*(len(code)//4),code)
    header='// Compiled from authored world_scene.vert with glslangValidator.\n'
    header+='inline constexpr std::uint32_t world_scene_vert_spv[]={\n'
    header+='\n'.join('    '+','.join(f'0x{v:08x}u' for v in words[i:i+8])+',' for i in range(0,len(words),8))+'\n};\n'
    source.with_name('world_scene_vert.h').write_text(header)
