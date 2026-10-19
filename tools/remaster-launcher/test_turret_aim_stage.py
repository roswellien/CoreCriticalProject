"""Compile actual authored stage against asset-free guest/body mocks."""
from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'local/campaign2-platform-investigation-r1/turret-aim-contract'
LLVM = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/clang-cl.exe'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).with_suffix('.cpp')
    exe = OUT / 'turret-aim-stage-fixture.exe'
    script = """$ErrorActionPreference='Stop'
$vs='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module "$vs/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
""" + f"& '{LLVM}' /nologo /std:c++20 /MD /EHsc /O2 /W4 '{source}' '/Fe:{exe}' '/Fo:{OUT / 'turret-aim-stage-fixture.obj'}'\nif($LASTEXITCODE){{throw 'Turret aim stage fixture compile failed'}}\n"
    subprocess.run(['powershell', '-NoProfile', '-Command', script], check=True)
    for mode in ('off', 'on', 'off-logging'):
        env = os.environ.copy()
        env['MW34_TURRET_AIM_REPAIR'] = str(int(mode == 'on'))
        env.pop('MW34_TURRET_AIM_LOG', None)
        if mode == 'off-logging':
            env['MW34_TURRET_AIM_LOG'] = str(OUT / 'stage-fixture-observation.log')
        subprocess.run([str(exe), mode], env=env, check=True)

if __name__ == '__main__':
    main()
