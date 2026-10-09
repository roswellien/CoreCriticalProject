"""Fresh independent compiled tests using exact immutable guest COFF inputs."""
import hashlib,json,os,re,subprocess,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
VS=Path('C:/Program Files/Microsoft Visual Studio/18/Community')
CMAKE=VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe'
NINJA=VS/'Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe'
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
BASE=ROOT/'reports/m4-crt-control-carry'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(out):
    out=Path(out).resolve();out.relative_to(BASE/'independent-source-r1')
    builds={level:ROOT/f'build/m4-control-carry-peer-{out.name}-{level}' for level in ('O0','O2')}
    if out.exists() or any(p.exists() for p in builds.values()):raise ValueError('Fresh private review/build directories required')
    build_path=BASE/'native-build-r4/build.json'
    build=json.loads(build_path.read_text(encoding='utf-8-sig'))
    pins={str(build_path):sha(build_path)}
    for group in ('sources','tools','artifacts'):
        for p,h in build[group].items():
            if sha(p)!=h:raise ValueError('Changed exact authored build dependency '+p)
            pins[p]=h
    own=ROOT/'tools/m4-crt-control-carry-independent'
    for name in ('causal.cpp','CMakeLists.txt','build_peer.py','build_peer.ps1'):
        p=own/name;pins[str(p)]=sha(p)
    out.mkdir(parents=True)
    copies=out/'literal-sources';copies.mkdir()
    for name in ('causal.cpp','CMakeLists.txt','build_peer.py','build_peer.ps1'):(copies/name).write_bytes((own/name).read_bytes())
    logs=[];results=[];failure=None
    def run(args,name):
        args=list(map(str,args));p=subprocess.run(args,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        path=out/name;path.write_bytes(p.stdout);pins[str(path)]=sha(path)
        logs.append(dict(command=args,exit_code=p.returncode,log=str(path),sha256=sha(path)))
        if Path(args[0]).is_file():pins[args[0]]=sha(args[0])
        print(json.dumps(dict(step=name,exit_code=p.returncode)),flush=True)
        if p.returncode:raise ValueError('Actual compiled review step failed: '+name+'\n'+p.stdout.decode(errors='replace')[-3000:])
        return p.stdout
    try:
        os.environ['TEMP']=str(out);os.environ['TMP']=str(out);os.environ['TMPDIR']=str(out)
        for level,directory in builds.items():
            objects=build['objects'][level]
            for p,h in objects.items():
                if sha(p)!=h:raise ValueError('Guest object changed '+p)
                pins[p]=h
            run([CMAKE,'-G','Ninja','-S',own,'-B',directory,'-DCMAKE_CXX_COMPILER=clang-cl','-DCMAKE_BUILD_TYPE=Release',
                 f'-DCMAKE_CXX_FLAGS_RELEASE={"/Od" if level=="O0" else "/O2"} /DNDEBUG -Wno-invalid-offset'+'of',
                 f'-DPEER_DERIVED={BASE}/research-r4',f'-DPEER_BINDINGS={BASE}/native-build-r4/{level}',
                 f'-DPEER_OBJECTS={";".join(objects)}',f'-DPEER_REMILL={ROOT}/local/tools/remill-v6.0.1/remill-6.0.1/include'],level+'-configure.log')
            run([CMAKE,'--build',directory,'--parallel','8'],level+'-build.log')
            worker=directory/'carry_peer.exe';pins[str(worker)]=sha(worker)
            result=run([worker,ROOT/'MW3/Mech3.exe',ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',BASE/'research-r4/pack.bin',BASE/'original-run-r1/original.bin'],level+'-actual.json')
            results.append(dict(level=level,**json.loads(result)))
            deps=run([NINJA,'-C',directory,'-t','deps'],level+'-actual-dependencies.txt').decode(errors='replace')
            for line in deps.splitlines():
                if line.startswith('    '):
                    p=Path(line.strip())
                    if not p.is_absolute():p=directory/p
                    p=p.resolve()
                    if p.is_file():pins[str(p)]=sha(p)
            for p in directory.rglob('*'):
                if p.is_file() and p.suffix in ('.obj','.lib','.exe','.ninja'):pins[str(p)]=sha(p)
            cache=directory/'CMakeCache.txt';pins[str(cache)]=sha(cache)
            for match in re.finditer(r'^CMAKE_(?:CXX_COMPILER|AR|LINKER|MT|RC_COMPILER|MAKE_PROGRAM):(?:FILEPATH|STRING)=(.+)$',cache.read_text(encoding='utf-8-sig'),re.M):
                p=Path(match[1]);pins[str(p)]=sha(p)
        for p,h in list(pins.items()):
            if sha(p)!=h:raise ValueError('Review input changed during causal execution '+p)
    except Exception as error:
        failure=str(error);(out/'failure.txt').write_text(traceback.format_exc())
    report=dict(passed=failure is None,scope='Independent exact-r4 compiled controls; no original/provider instructions, numerical oracle or full startup execution',failure=failure,results=results,commands=logs,author_build_sha256=sha(build_path),binding_scope='Exact guest objects; current post-build compiler dependency identities, not complete process trace')
    rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');pins[str(rp)]=sha(rp)
    for p in out.rglob('*'):
        if p.is_file():pins[str(p)]=sha(p)
    (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(pins.items()))),indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],results=results,report_sha256=sha(rp))))
    if failure:raise SystemExit(1)
if __name__=='__main__':main(sys.argv[1])
