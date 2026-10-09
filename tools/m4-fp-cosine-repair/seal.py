"""Additive physical source/artifact/history association for cosine review."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'reports/m4-fp-transcendental'
CACHE={}

def digest(path):
    path=Path(path).resolve()
    if path not in CACHE:
        with path.open('rb') as stream:CACHE[path]=hashlib.file_digest(stream,'sha256').hexdigest()
    return CACHE[path]

def require(ok,why):
    if not ok:raise ValueError(why)

def main():
    directory=Path(sys.argv[1]).resolve();require(directory.is_relative_to(AREA) and not directory.exists(),'Fresh private closure required')
    # Replacements associate literal consumed sources with old maps; the old
    # map and current accepted source are never rewritten to claim continuity.
    archive={}
    for path in AREA.rglob('*'):
        if path.is_file() and path.suffix in ('.cpp','.hpp','.py','.ps1','.txt','.asm','.h'):
            archive.setdefault(digest(path),[]).append(path)
    files={};replacements=[];maps=[]
    def bind(path,expected):
        path=Path(path).resolve();require(path.is_file(),'Missing physical binding '+str(path))
        if digest(path)!=expected:
            options=archive.get(expected,[]);require(options,'Unpreserved historical binding '+str(path))
            literal=options[0];files[str(literal)]=expected
            item={'historical_source_path':str(path),'expected_sha256':expected,'literal_source':str(literal)}
            if item not in replacements:replacements.append(item)
        else:files[str(path)]=expected
    def collect(value):
        if isinstance(value,dict):
            for field in ('bindings','files','sources'):
                candidate=value.get(field)
                if isinstance(candidate,dict):
                    for path,sha in candidate.items():
                        if isinstance(sha,str) and re.fullmatch('[0-9a-f]{64}',sha):bind(path,sha)
            if isinstance(value.get('path'),str) and isinstance(value.get('sha256'),str):bind(value['path'],value['sha256'])
            for child in value.values():collect(child)
        elif isinstance(value,list):
            for child in value:collect(child)
    for path in sorted(AREA.rglob('*.json')):
        collect(json.loads(path.read_text(encoding='utf-8-sig')));files[str(path)]=digest(path);maps.append(str(path))
    original_closure=ROOT/'reports/m4-fp-startup/run-r1/closure/pins.json'
    require(digest(original_closure)=='2e62afe363336541379664032cc6d09ae75382caf4337e63578a3a8dc3d2a3fd','Exact original ten-root closure required')
    collect(json.loads(original_closure.read_text()));files[str(original_closure)]=digest(original_closure)
    for path in AREA.rglob('*'):
        if path.is_file():files[str(path)]=digest(path)
    directory.mkdir(parents=True);sources={}
    public=[]
    for name in ['tools/m4-fp-transcendental','tools/m4-fp-cosine-repair','tests/m4-fp-transcendental']:
        public.extend(p for p in (ROOT/name).rglob('*') if p.is_file() and p.suffix!='.pyc')
    public.extend([ROOT/'docs/m4-fp-cosine-experiment.md',ROOT/'tools/m4-fp-store-repair/store_test.cpp'])
    for path in public:
        target=directory/'sources'/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
        sources[str(path)]=digest(path);files[str(path)]=digest(path);files[str(target)]=digest(target)
    objdump=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
    commands=[]
    for level in ('O0','O2'):
        build=ROOT/f'build/m4-fp-cosine-repair-cosine-repaired-r1-{level}'
        objects=[AREA/f'cosine-repaired-r1/{entry}-{level}.obj' for entry in ('4ce5a0','4ce5c0','4ce5e0','4ce600')]
        objects.extend(sorted(build.rglob('raw80_status.cpp.obj')));objects.extend(sorted(build.rglob('store_test.cpp.obj')))
        for index,path in enumerate(objects):
            command=[str(objdump),'--disassemble','--reloc',str(path)]
            result=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=30);require(result.returncode==0,'Object observation failed')
            output=directory/f'object-{level}-{index}.txt';stderr=directory/f'object-{level}-{index}.stderr';output.write_bytes(result.stdout);stderr.write_bytes(result.stderr)
            commands.append({'command':command,'exit_code':result.returncode,'stdout':str(output),'stderr':str(stderr)})
            for p in (path,output,stderr):files[str(p)]=digest(p)
    files[str(objdump)]=digest(objdump)
    # AMD64 MSBuild appears in the exact recorded original build command.
    # This current hash is explicitly later than execution, not an invented
    # execution-time pin or complete dynamic process dependency closure.
    msbuild=Path('C:/Program Files/Microsoft Visual Studio/18/Community/MSBuild/Current/Bin/amd64/MSBuild.exe')
    log=(AREA/'directed-baseline-r2/build-x86.log').read_text().replace('\\','/').lower()
    require(str(msbuild).replace('\\','/').lower() in log,'Recorded AMD64 MSBuild invocation required')
    files[str(msbuild)]=digest(msbuild)
    for leaf in ['directed-repaired-comparison-r1/report.json','repaired-full-comparison-r1/report.json','observer-controls-r2/report.json',
      'worker-controls-O0-r1/report.json','worker-controls-O2-r1/report.json','worker-controls-original-normal-r1/report.json']:
        report=json.loads((AREA/leaf).read_text());require(report.get('passed',report.get('passed_observed_domain',False)),'Required positive evidence incomplete '+leaf)
    report={'passed':True,'scope':'Author cosine source/tool/actual-artifact and preserved-history association; independent admission remains open',
      'original_directed_records':6144,'native_directed_records':12288,'default_original_records':192,'default_native_records':384,
      'primary_observer_controls':32,'actual_worker_denials':15,'actual_compiled_context_controls':64,
      'historical_source_replacements':replacements,'literal_sources':sources,'consumed_maps':maps,'actual_object_commands':commands,
      'post_build_tool_identity':{'path':str(msbuild),'sha256':digest(msbuild),'scope':'Current hash of log-recorded AMD64 MSBuild; measured after build'},
      'physical_bindings_before_report':len(files),'independent_review':False,'shared_Runtime_admitted':False,
      'limitations':['Empty x87/TOP0and7/masked only; this hardware','Original State/events unobserved',
       'Final C0/C2/C3 and dead raw80 are observed only; C1 requires conservative per-record review',
       'Fresh ordinary sequential output only; no concurrent/reparse production claim','No connected FP order, full startup or native menus']}
    path=directory/'report.json';path.write_text(json.dumps(report,indent=2)+'\n');files[str(path)]=digest(path)
    (directory/'pins.json').write_text(json.dumps({'files':files},indent=2)+'\n')
    print(json.dumps({'passed':True,'bindings':len(files),'literal_sources':len(sources),'historical_replacements':len(replacements),
      'report_sha256':digest(path),'pins_sha256':digest(directory/'pins.json')}))

if __name__=='__main__':main()
