"""Compile the frozen numeric fixture; no target execution here."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import traceback
ROOT=Path(__file__).resolve().parents[2]


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main(preparation,digest,name):
    assert re.fullmatch('fixture-build-r[1-9][0-9]*',name)
    out=ROOT/'reports/m4-hypot-native'/name;assert not out.exists();out.mkdir()
    pins={};commands=[];workers={};passed=False
    def pin(p,h=None):
        p=Path(p).resolve();a=sha(p);assert h is None or a==h,p
        assert str(p) not in pins or pins[str(p)]==a;pins[str(p)]=a;return p
    def run(args,label):
        args=list(map(str,args));pin(args[0]);r=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=180,creationflags=0x08000000)
        (out/label).write_bytes(r.stdout+r.stderr);commands.append(dict(arguments=args,exit_code=r.returncode,log=label))
        print(json.dumps(dict(log=label,exit_code=r.returncode)),flush=True);assert r.returncode==0,label
    try:
        p=json.loads(pin(preparation,digest).read_bytes());assert p['passed'];prep=Path(preparation).parent
        for q,h in p['files'].items():pin(q,h)
        pin(__file__);pin(ROOT/'tools/m4-hypot-native/build_fixture.ps1');os.environ['TEMP']=os.environ['TMP']=str(out)
        llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
        vs=Path('C:/Program Files/Microsoft Visual Studio/18/Community')
        cmake=vs/'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
        ninja=vs/'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
        for level in ('O0','O2'):
            tree=out/('build-'+level)
            flags=('/Od' if level=='O0' else '/O2')+' /DNDEBUG /showIncludes -Wno-invalid- offsetof'.replace('- offsetof','-offsetof')
            run([cmake,'-G','Ninja','-S',prep,'-B',tree,'-DCMAKE_MAKE_PROGRAM='+str(ninja),
                '-DCMAKE_CXX_COMPILER='+str(llvm/'clang-cl.exe'),'-DCMAKE_BUILD_TYPE=Release',
                '-DCMAKE_CXX_FLAGS_RELEASE='+flags,'-DMW34_ROOT='+str(ROOT),'-DMW34_LEVEL='+level,
                '-DMW34_REMILL='+p['remill_include'],'-DMW34_OBJECTS='+';'.join(p['objects'][level])],level+'-configure.log')
            run([cmake,'--build',tree,'--parallel','4'],level+'-build.log')
            worker=pin(tree/'hypot-native.exe');workers[level]=dict(path=str(worker),sha256=sha(worker),literal_objects=p['objects'][level])
        for q,h in pins.items():assert sha(q)==h,q
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        report=dict(passed=passed,scope='Compiled literal numeric registered Runtime workers; writer unlaunched',
            preparation=str(preparation),preparation_sha256=digest,workers=workers,commands=commands,files=pins,
            artifacts={str(q):sha(q) for q in out.rglob('*') if q.is_file()},native_executed=False,initializer_credit=0)
        q=out/'build.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q))))


if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
