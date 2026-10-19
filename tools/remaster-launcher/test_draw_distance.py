"""Build/run the authored camera-distance helper with asset-free mock state."""
from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'local/campaign2-platform-investigation-r1/fog-contract'
LLVM = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/clang-cl.exe'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).with_suffix('.cpp')
    exe = OUT / 'draw-distance-fixture.exe'
    script = """$ErrorActionPreference='Stop'
$vs='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module "$vs/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
""" + f"& '{LLVM}' /nologo /std:c++20 /MD /EHsc /O2 '{source}' '/Fe:{exe}' '/Fo:{OUT / 'draw-distance-fixture.obj'}'\nif($LASTEXITCODE){{throw 'Distance fixture compile failed'}}\n"
    subprocess.run(['powershell', '-NoProfile', '-Command', script], check=True)
    env = os.environ.copy()
    env.pop('MW34_VIEW_DISTANCE_LOG', None)
    for draw, fog, args in [('1200', '1100', []), ('800', '0', ['stock']), ('1600', '0', ['legacy'])]:
        env.update(MW34_REMASTER_DRAW_DISTANCE=draw, MW34_REMASTER_FOG_DISTANCE=fog)
        subprocess.run([str(exe), *args], env=env, check=True)

if __name__ == '__main__':
    main()
