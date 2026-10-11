"""Read the actual closed Ninja dependency databases without rebuilding."""
from pathlib import Path
import hashlib, json, re, subprocess, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PINS={}
def need(x,s):
    if not x: raise ValueError(s)
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Physical identity '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable identity');PINS[str(p)]=v;return p
def load(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def main(name):
    out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh owned output')
    pre=load(R/'reports/m4-tree-review/mfc1168-native-prelaunch-r4/report.json','f440e891805bca226f5106d0b33cfef884ad6abcbcc93c753cf06f3347d4289f')
    build=load(R/'reports/m4-mfc1168-native/fixture-build-r3/build.json','7558739f895205601dcbc1574754e1907ab3639d57ab871b743b92d8b7bb3938')
    need(pre['passed']and build['passed'],'Current passed bounded prelaunch/build')
    out.mkdir();rows=[]
    for level in('O0','O2'):
        w=build['workers'][level];worker=pin(w['path'],w['sha256']);folder=worker.parent
        deps=pin(folder/'.ninja_deps',build['artifacts'][str(folder/'.ninja_deps')]);db_hash=sha(deps)
        cache=pin(folder/'CMakeCache.txt',build['artifacts'][str(folder/'CMakeCache.txt')]).read_text()
        ninja=pin(re.search(r'^CMAKE_MAKE_PROGRAM:FILEPATH=(.+)$',cache,re.M).group(1))
        command=[str(ninja),'-t','deps'];result=subprocess.run(command,cwd=folder,capture_output=True,timeout=20)
        need(result.returncode==0 and not result.stderr,'Actual closed dependency database read')
        need(sha(deps)==db_hash,'Dependency database unchanged by read')
        q=out/f'{level}-actual-ninja-deps.txt';q.write_bytes(result.stdout);pin(q)
        objects=[];current=None
        for line in result.stdout.decode().splitlines():
            if not line:continue
            if not line.startswith('    '):
                m=re.fullmatch(r'(.+): #deps (\d+), deps mtime (\d+) \((VALID|STALE)\)',line)
                need(m and m[4]=='VALID','Exact valid actual object dependency header')
                current=dict(object=str(pin(folder/m[1])),declared_dependencies=int(m[2]),paths=[])
                objects.append(current)
            else:
                need(current is not None,'Dependency follows object')
                path=Path(line[4:]);path=path if path.is_absolute()else folder/path
                current['paths'].append(str(pin(path)))
        need(len(objects)==4,'Exactly four actually compiled source objects')
        for obj in objects:
            need(len(obj['paths'])==obj['declared_dependencies'],'Complete actual compiler include closure for object')
        paths={p for obj in objects for p in obj['paths']}
        header=folder/'fixture_spec.hpp'
        need(str(header.resolve())in paths,'Actually consumed generated fixture header')
        need(str((R/'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/X86/Runtime/State.h').resolve())in paths,'Actually consumed packed State header')
        rows.append(dict(level=level,actual_database_sha256=db_hash,compiler_objects=objects,
            unique_consumed_paths=len(paths),read_command=command,worker_sha256=w['sha256']))
    pin(__file__);pin(sys.executable)
    q=out/'report.json';q.write_text(json.dumps(dict(passed=True,prelaunch_sha256='f440e891805bca226f5106d0b33cfef884ad6abcbcc93c753cf06f3347d4289f',
        build_sha256='7558739f895205601dcbc1574754e1907ab3639d57ab871b743b92d8b7bb3938',
        levels=rows,actual_compiler_dependency_objects=8,actual_dependency_paths_physically_pinned=True,
        historical_build_time_include_content_observed=False,worker_executed=False,
        archive_opened=False,initializer_credit=0,
        scope='Actual read-only closed Ninja compiler dependency databases bind consumed path names and current physical header/source identities. '
              'No rebuild or guest execution. Build-time header-content observations are not invented; linked object/executable identities remain the frozen current build.',files=PINS),indent=2)+'\n')
    print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),files=len(PINS),level_paths=[x['unique_consumed_paths']for x in rows])))
if __name__=='__main__':main(sys.argv[1])
