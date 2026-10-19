"""Compile/run the authored sun adapter and GPU fixtures against a test host."""
from pathlib import Path
import argparse
import subprocess

ROOT=Path(__file__).resolve().parents[2]
def quote(path):return "'"+str(path).replace("'","''")+"'"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host-source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--fixture',type=Path,default=Path(__file__).with_suffix('.cpp'))
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    compiler=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/clang-cl.exe'
    exe=a.output/'sun-fixture.exe';obj=a.output/'sun-fixture.obj'
    script="""$ErrorActionPreference='Stop'
$vs='C:/Program Files/Microsoft Visual Studio/18/Community'
Import-Module "$vs/Common7/Tools/Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
"""
    script+=f"& {quote(compiler)} /nologo /std:c++20 /MD /EHsc /O2 /W4 /D_CRT_SECURE_NO_WARNINGS {quote('/I'+str(a.host_source.resolve()))} {quote('/I'+str(ROOT/'local/tools/vulkan-headers-v1.4.321/include'))} {quote(a.fixture.resolve())} {quote('/Fe:'+str(exe.resolve()))} {quote('/Fo:'+str(obj.resolve()))} /link user32.lib\n"
    script+="if($LASTEXITCODE){throw 'Sun fixture compile failed'}\n"
    subprocess.run(['powershell','-NoProfile','-Command',script],check=True)
    subprocess.run([str(exe.resolve())],check=True)

if __name__=='__main__':main()
