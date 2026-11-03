"""Compile authored temporal, native static and shared coverage shaders."""
import argparse
from pathlib import Path
import struct
import subprocess

def compile_shaders(host, compiler, output):
    output.mkdir(parents=True, exist_ok=True)
    for source, name in (("temporal_inputs.vert", "temporal_inputs_vert"),
                         ("temporal_inputs.frag", "temporal_inputs_frag"),
                         ("world_coverage.frag", "world_coverage_frag"),
                         ("native_static.vert", "native_static_vert")):
        binary = output / (name + ".spv")
        subprocess.run([str(compiler), "-V", "--target-env", "vulkan1.0", "-I" + str(host),
                        str(host / source), "-o", str(binary)], check=True)
        data = binary.read_bytes()
        words = struct.unpack("<" + "I" * (len(data) // 4), data)
        text = "// Compiled from authored " + source + "; use compile_temporal_shaders.py.\n"
        text += "inline constexpr std::uint32_t " + name + "_spv[]={\n"
        text += "\n".join("    " + ",".join(f"0x{x:08x}u" for x in words[i:i+8]) + ","
                           for i in range(0, len(words), 8)) + "\n};\n"
        (host / (name + ".h")).write_text(text, encoding="utf-8", newline="\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-source", type=Path, required=True)
    parser.add_argument("--compiler", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    compile_shaders(args.host_source.resolve(), args.compiler.resolve(), args.output.resolve())
