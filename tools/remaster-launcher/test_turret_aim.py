"""Build/run the pure authored turret-aim math fixture without game assets."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'local/campaign2-platform-investigation-r1/turret-aim-contract'
LLVM = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/clang-cl.exe'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).with_suffix('.cpp')
    exe = OUT / 'turret-aim-fixture.exe'
    script = """$ErrorActionPreference='Stop'
$vs='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module "$vs/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
""" + f"& '{LLVM}' /nologo /std:c++20 /MD /EHsc /O2 /W4 '{source}' '/Fe:{exe}' '/Fo:{OUT / 'turret-aim-fixture.obj'}'\nif($LASTEXITCODE){{throw 'Turret aim fixture compile failed'}}\n"
    subprocess.run(['powershell', '-NoProfile', '-Command', script], check=True)
    subprocess.run([str(exe)], check=True)

if __name__ == '__main__':
    main()
