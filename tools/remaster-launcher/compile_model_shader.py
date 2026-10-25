"""Compile the authored resident-model shader into a private compatible host."""
from pathlib import Path
import argparse
import shutil
import struct
import subprocess


def compile_shader(host, compiler, binary):
    source = Path(__file__).parent / 'native-overrides/model_scene.vert'
    binary.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(compiler.resolve()), '-V', '--target-env', 'vulkan1.0',
                    '-S', 'vert', str(source.resolve()), '-o', str(binary.resolve())], check=True)
    code = binary.read_bytes()
    words = struct.unpack('<' + 'I' * (len(code) // 4), code)
    header = '// Compiled from authored model_scene.vert with compile_model_shader.py.\n'
    header += 'inline constexpr std::uint32_t model_scene_vert_spv[]={\n'
    header += '\n'.join('    ' + ','.join(f'0x{v:08x}u' for v in words[i:i + 8]) + ','
                        for i in range(0, len(words), 8)) + '\n};\n'
    (host / 'model_scene_vert.h').write_text(header, encoding='utf-8', newline='\n')
    shutil.copy2(source, host / source.name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host-source', type=Path, required=True)
    parser.add_argument('--compiler', type=Path, required=True)
    parser.add_argument('--binary', type=Path, required=True)
    args = parser.parse_args()
    compile_shader(args.host_source.resolve(strict=True), args.compiler, args.binary)
