"""Build the isolated authored C++ lab; never compose or launch a game host."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import base64
import struct
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True,
                        help='Dedicated lab output directory (outside existing game builds)')
    args = parser.parse_args()
    out = args.out.resolve()
    # Refuse the existing playable/build namespaces even if accidentally supplied.
    protected = [ROOT / 'local' / 'remaster', ROOT / 'build', ROOT / 'runtime', ROOT / 'tools']
    if out == ROOT or any(out == p or p in out.parents for p in protected):
        parser.error('Choose a separate lab output directory, not a game/source build namespace')
    out.mkdir(parents=True, exist_ok=True)
    marker = out / 'weapon-effects-lab.marker'
    if not marker.exists() and any(out.iterdir()):
        parser.error('Output directory must be empty or already owned by this lab')
    marker.write_text('MW34 isolated authored particle lab r1\n', encoding='utf-8')
    if os.name == 'nt':
        vswhere = Path('C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe')
        vs = Path(subprocess.check_output([str(vswhere), '-latest', '-products', '*',
                  '-requires', 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
                  '-property', 'installationPath'], text=True).strip())
        if not vs.is_dir():
            raise RuntimeError('Visual Studio C++ tools not found')
        cmake = vs / 'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
        def ps(value):
            return "'" + str(value).replace("'", "''") + "'"
        script = "\n".join([
            "$ErrorActionPreference='Stop'",
            f"Import-Module {ps(vs / 'Common7/Tools/Microsoft.VisualStudio.DevShell.dll')}",
            f"Enter-VsDevShell -VsInstallPath {ps(vs)} -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null",
            f"& {ps(cmake)} -S {ps(HERE)} -B {ps(out / 'build')} -G Ninja -DCMAKE_BUILD_TYPE=Release",
            "if($LASTEXITCODE){throw 'Lab configure failed'}",
            f"& {ps(cmake)} --build {ps(out / 'build')}",
            "if($LASTEXITCODE){throw 'Lab build failed'}",
            f"& {ps(cmake.with_name('ctest.exe'))} --test-dir {ps(out / 'build')} --output-on-failure",
            "if($LASTEXITCODE){throw 'Lab contracts failed'}",
        ])
        subprocess.run(['powershell', '-NoProfile', '-Command', script], check=True)
        exporter = out / 'build/effects_preview_export.exe'
    else:
        subprocess.run(['cmake', '-S', str(HERE), '-B', str(out/'build'), '-DCMAKE_BUILD_TYPE=Release'], check=True)
        subprocess.run(['cmake', '--build', str(out/'build')], check=True)
        subprocess.run(['ctest', '--test-dir', str(out/'build'), '--output-on-failure'], check=True)
        exporter = out / 'build/effects_preview_export'
    data = out / 'preview-data.json'
    subprocess.run([str(exporter), str(data)], check=True)
    # Embed the actual C++ output, not a second particle simulation in JavaScript.
    preview_data = json.loads(data.read_text(encoding='utf-8'))
    def png(width, height, pixels):
        if len(pixels) != width*height*4:
            raise RuntimeError('Wrong native flow plane size')
        def chunk(kind, blob):
            return struct.pack('>I', len(blob))+kind+blob+struct.pack('>I', zlib.crc32(kind+blob))
        rows = b''.join(b'\0'+pixels[y*width*4:(y+1)*width*4] for y in range(height))
        return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')
    for scene in preview_data['scenes']:
        for frame in scene['frames']:
            field = frame.get('field')
            if field:
                for layer in ('fire', 'smoke'):
                    raw = out / field[layer]
                    if raw.parent.resolve() != out:
                        raise RuntimeError('Native plane path escaped lab output')
                    encoded = png(field['width'],field['height'],raw.read_bytes())
                    raw.with_suffix('.png').write_bytes(encoded)
                    field[layer] = 'data:image/png;base64,'+base64.b64encode(encoded).decode('ascii')
    payload = json.dumps(preview_data, separators=(',', ':'), allow_nan=False)
    template = (HERE / 'preview.html').read_text(encoding='utf-8')
    if template.count('/*NATIVE_DATA*/null') != 1:
        raise RuntimeError('Preview data insertion marker missing or ambiguous')
    preview = out / 'preview.html'
    preview.write_text(template.replace('/*NATIVE_DATA*/null', payload), encoding='utf-8')
    print(f'Preview: {preview}\nStandalone authored fixture; no game integration or lighting-engine changes.')


if __name__ == '__main__':
    main()
