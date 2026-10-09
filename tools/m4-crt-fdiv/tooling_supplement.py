"""Post-build provider/dependency supplement; never rewrites primary maps."""
import argparse,hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-fdiv'
def sha(p):
    with open(p,'rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
    if not v:raise ValueError(m)
def main(out):
    out=pathlib.Path(out).resolve();need(out.parent==BASE and not out.exists(),'Fresh private tooling report');out.mkdir();files={};builds=[];headers={};providers=[];libraries=[]
    for name in('native-build-r3','native-boundary-r3'):
        bp=BASE/name/'build.json';b=json.loads(bp.read_text(encoding='utf-8-sig'));need(b['passed'],'Successful literal final build');files[str(bp)]=sha(bp)
        for level in('O0','O2'):
            directory=ROOT/f'build/m4-fdiv-{name}-{level}';cache=(directory/'CMakeCache.txt').read_text();rules=directory/'CMakeFiles/rules.ninja';log=BASE/name/f'build-{level}.log';text=log.read_text(encoding='utf-8-sig');selected=[]
            for key in('CMAKE_CXX_COMPILER','CMAKE_AR','CMAKE_LINKER','CMAKE_MAKE_PROGRAM','CMAKE_MT','CMAKE_RC_COMPILER'):
                m=re.search('^'+key+r':(?:FILEPATH|STRING)=(.+)$',cache,re.M);need(m is not None,'Configured provider '+key);path=pathlib.Path(m[1]).resolve();files[str(path)]=sha(path);selected.append({'role':key,'path':str(path),'current_sha256':files[str(path)],'hash_time':'post-build observation','named_in_actual_build_log':path.name.lower()in text.lower(),'child_execution_proven':key in('CMAKE_CXX_COMPILER','CMAKE_AR','CMAKE_LINKER')})
            for match in re.findall(r'Note: including file:\s*([^\r\n]+)',text):
                path=pathlib.Path(match.strip()).resolve();need(path.is_file(),'Actual compiler-reported header exists');headers[str(path)]=sha(path);files[str(path)]=headers[str(path)]
            for path in(directory/'CMakeCache.txt',rules,directory/'build.ninja',log):files[str(path)]=sha(path)
            builds.append({'name':name,'level':level,'configured_providers':selected,'actual_verbose_log':str(log),'compiler_read_headers':'Actual /showIncludes paths; current hashes observed after build','RC_child_execution':'Wrapper --rc argument and generated RC provider are observed. No .res/.rc artifact exists; this supplement does not assert RC executed.'})
    # These are declared link names in actual verbose lld-link commands. Their
    # precise SDK paths below are a current configured-toolset association, not
    # an invented linker trace proving the historical search resolution.
    sdk=pathlib.Path('C:/Program Files (x86)/Windows Kits/10/Lib/10.0.26100.0/um/x64')
    for name in('bcrypt','kernel32','user32','gdi32','winspool','shell32','ole32','oleaut32','uuid','comdlg32','advapi32'):
        p=sdk/(name+'.lib');files[str(p)]=sha(p);libraries.append({'name':name+'.lib','current_path':str(p),'current_sha256':sha(p),'association':'Exact configured SDK10.0.26100.0 current candidate; resolved file not logged by historical linker'})
    files[str(pathlib.Path(__file__).resolve())]=sha(__file__)
    result={'passed':True,'scope':'Additive current tool/provider/header observations and actual generated/verbose command association','primary_maps_unchanged':True,'primary_tool_hashes':'Primary Run() directly records opt/llc/cmake/executable before invocation. Indirect compiler/archive/link/RC/MT/Ninja provider hashes here are post-build observations, not retroactively recorded hashes.','builds':builds,'unique_compiler_read_headers':len(headers),'current_link_library_candidates':libraries,'original_execution':False,'whole_M4_complete':False}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');files[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(files,indent=2)+'\n');print(json.dumps({'passed':True,'headers':len(headers),'bindings':len(files)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();main(a.out)
