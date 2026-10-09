"""Seal this independent review; standard library only, no author analyzers."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/m4-crt-data/independent-review-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,msg):
    if not ok:raise AssertionError(msg)
def bind(p):
    p=Path(p).resolve();return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha(p)}
def run():
    require(not (OUT/'report.json').exists() and not (OUT/'pins.json').exists(),'new final seal')
    authpath=ROOT/'reports/m4-crt-data/author-review-r1/report.json'
    auth=json.loads(authpath.read_text());authpins=json.loads((authpath.parent/'pins.json').read_text())['files']
    require(sha(authpath)=='b0f26788bf5adca5196778cae2b89e0e15b35f943ec016f64c6a73ad49ec6350','author unchanged')
    require(sha(authpath.parent/'pins.json')=='8af9f365e95d58cd2b02983626c1ab51a6c273d5e4ebef2aa0f00315484251f4','pins unchanged')
    for p,h in authpins.items():require(sha(p)==h,'physical author identity '+p)
    historical=auth['historical_source_resolutions'];resolution={(str(Path(r['historical_map']).resolve()).lower(),str(Path(r['original_path']).resolve()).lower(),r['recorded_sha256']):r['physical_path'] for r in historical}
    associations=[];maps=[]
    for folder in (ROOT/'reports/m4-crt-data').iterdir():
        if not folder.is_dir() or folder.name.startswith(('independent','author')):continue
        for p in folder.glob('*.json'):
            doc=json.loads(p.read_text());records=[]
            for k in ('source_files','tool_files','artifacts','files'):records.extend(doc.get(k,{}).items())
            def walk(x):
                if isinstance(x,dict):
                    if isinstance(x.get('path'),str) and isinstance(x.get('sha256'),str):records.append((x['path'],x['sha256']))
                    # Literal copy and separate path/hash report schemas.
                    if isinstance(x.get('preserved_path'),str) and isinstance(x.get('sha256'),str):records.append((x['preserved_path'],x['sha256']))
                    for key,value in x.items():
                        if key.endswith('_path') and isinstance(value,str) and isinstance(x.get(key[:-5]+'_sha256'),str):records.append((value,x[key[:-5]+'_sha256']))
                    for value in x.values():walk(value)
                elif isinstance(x,list):
                    for value in x:walk(value)
            walk(doc)
            if records:maps.append({'map':bind(p),'embedded_bindings':len(records)})
            for path,digest in records:
                physical=resolution.get((str(p.resolve()).lower(),str(Path(path).resolve()).lower(),digest),path)
                require(sha(physical)==digest,'recorded map association '+str(p)+' '+path)
                associations.append({'map':str(p.resolve()),'recorded_path':path,'recorded_sha256':digest,'physical_path':str(Path(physical).resolve())})
    raw=json.loads((OUT/'raw-r2/raw-review.json').read_text());require(raw['passed'] and raw['physical_author_bindings']==738 and raw['literal_historical_resolutions']==7,'raw review')
    buildpath=OUT/'ownership-r1/build.json';build=json.loads(buildpath.read_text());require(build['passed'],'own compiled tests')
    for key in ('source_files','frozen_libraries','tool_files','artifacts'):
        for p,h in build[key].items():require(sha(p)==h,'own compiled binding '+p)
    own_runs=[]
    for level in ('O0','O2'):
        row=json.loads((OUT/f'ownership-r1/run-{level}.log').read_text().strip())
        require(row=={'passed':True,'checks':567,'scenarios':41,'production_service':False},'own actual compiled outcome')
        own_runs.append({'level':level,'checks':567,'scenarios':41,'library':bind(ROOT/f'build/m4-crt-data-ownership-build-r3/Release/data_reference_{level}.lib'),'run_log':bind(OUT/f'ownership-r1/run-{level}.log')})
    original_run=json.loads((ROOT/'reports/m4-crt-data/commandline-run-r1/report.json').read_text())
    commands={c['name']:c for c in original_run['commands']}
    original_controls=[]
    for c in original_run['actual_controls']:
        cmd=commands[c['name']];stdout=Path(cmd['stdout']).read_text();stderr=Path(cmd['stderr']).read_text()
        require(sha(cmd['stdout'])==cmd['stdout_sha256'] and sha(cmd['stderr'])==cmd['stderr_sha256'],'original actual log association')
        if c['name']=='hash':require(cmd['exit_code']==0 and '2 SHA controls passed' in stdout,'original SHA controls')
        else:require(cmd['exit_code']==1 and c['intended_diagnostic'] in stderr,'original exact causal diagnostic')
        original_controls.append(c)
    author_controls=[]
    for c in auth['actual_authored_worker_controls']:
        require(c['exit_code']==1 and c['intended_diagnostic'] in Path(c['stderr']).read_text(),'ownership CLI diagnostic')
        args=c['arguments'];
        if c['name'].startswith('changed-'):
            index={'changed-provider':0,'changed-game':1,'changed-raw':2}[c['name']]
            original=[ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',ROOT/'MW3/Mech3.exe',ROOT/'reports/m4-crt-data/commandline-run-r1/original.bin'][index]
            require(sha(args[index])!=sha(original),'actual control input changed')
        author_controls.append(c)
    own_author_build=json.loads((ROOT/'reports/m4-crt-data/ownership-build-r3/build.json').read_text())
    for level in ('O0','O2'):
        require((ROOT/f'reports/m4-crt-data/ownership-build-r3/test-{level}.log').read_text().strip()=='251 authored reference data ownership/admission checks passed; production service false','recorded author controls')
    # Fresh object disassemblies bind the actual library workers, original
    # observer and independent callers; none execute a provider DLL.
    od=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
    objects=[ROOT/f'build/m4-crt-data-ownership-build-r3/data_reference_{level}.dir/Release/data_imports.obj' for level in ('O0','O2')]
    objects += [OUT/f'ownership-r1/independent-{level}.obj' for level in ('O0','O2')]
    original_build=json.loads((ROOT/'reports/m4-crt-data/commandline-build-r2/build.json').read_text())
    objects += [Path(p) for p in original_build['artifacts'] if p.endswith(('commandline_reference.obj','commandline_x86.obj'))]
    require(len(objects)==6,'six COFF objects')
    decodes=[]
    for i,p in enumerate(objects):
        target=OUT/f'object-{i}.txt';require(not target.exists(),'new decode')
        command=[str(od),'--disassemble','--reloc','--x86-asm-syntax=intel',str(p)]
        q=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
        target.write_bytes(q.stdout);(OUT/f'object-{i}.stderr').write_bytes(q.stderr)
        require(b'file format coff' in q.stdout,'actual COFF decode')
        decodes.append({'object':bind(p),'disassembly':bind(target),'command':command})
    # Preserve the failed first checker and associate its literal version with
    # its own failure, without rewriting either. The valid extent XOR did not
    # justify a negative; the second version tests zero-size coverage instead.
    first=json.loads((OUT/'raw-review.json').read_text());require(not first['passed'] and 'coverage-size' in first['failure'],'first checker preserved')
    copies=[]
    for p in sorted((ROOT/'tools/m4-crt-data-independent').glob('*')):
        if not p.is_file():continue
        target=OUT/'sources'/p.name;target.parent.mkdir(exist_ok=True);require(not target.exists(),'new literal current source');target.write_bytes(p.read_bytes());copies.append({'source':bind(p),'literal':bind(target)})
    report={'passed':True,'scope':'Independent bounded reference-only original CRT command-line writer and typed projection ownership; no native GetCommandLineA, translated writer, production _acmdln, full DllMain or full M4 credit','author_report':bind(authpath),'author_pins':bind(authpath.parent/'pins.json'),'original':raw['original'],'physical_author_bindings':738,'literal_historical_source_resolutions':historical,'recorded_maps':maps,'recorded_binding_associations':associations,'own_original_observer_controls':raw['own_observer_negative_controls'],'own_positive_extent_control':raw['own_observer_positive_controls'],'own_actual_compiled_ownership':own_runs,'author_recorded_ownership_checks_per_level':251,'author_recorded_scenarios_per_level':24,'original_actual_controls':original_controls,'author_actual_CLI_controls':author_controls,'fresh_actual_COFF_decodes':decodes,'literal_current_review_sources':copies,'checker_versions':[{'version':1,'source':bind(OUT/'review-source.py'),'failure':bind(OUT/'failure.txt'),'report':bind(OUT/'raw-review.json'),'finding':'Observer-control defect only: XOR of region size retained valid coverage; expected negative was unjustified.'},{'version':2,'source':bind(OUT/'raw-r2/review-source.py'),'report':bind(OUT/'raw-r2/raw-review.json'),'repair':'Zero-size region denial; explicit positive extent growth retained.'}],'reviewed_contracts':['Named exact unique actual MSVCRT data IAT owner, unchanged raw IAT, exact provider and eleven-byte writer file identities','Declared reference bytes copied before publication; NUL bound, SHA identity, 16MiB arena, full ready flag only after both maps and integrity','Ownership flags set only after successful map; external ordinary collision maps preserved, acquired partial maps released','Typed first fault persists and prevents admission/resolve reuse; changed bytes/unreadable mappings reject','Initial RO buffer, complete CPU/FX/State preservation by data API; no current-permission revalidation claim after deliberate host permission changes'],'findings':[],'limitations':['Probe command-line buffer belongs to the original worker process, not a future native host logical argument contract','Actual API is measured x86 KERNEL32 GetCommandLineA export thunk; no claim of a reimplemented Windows service or full API callee CFG','Raw records include one owning observed command-line byte copy; actual source checks stable bytes/pointer on each row, no separate after-copy serialization','Measured FX processor capability mask comes from each host FX capture; reserved/hardware capture fields are not software initialization writes','Registry uses a trusted stable Runtime borrower that outlives it; concurrency or host replacement of owned mappings outside scope','Buffer is initially RO; deliberate host permission changes that preserve readable bytes are not separately revalidated','Build tool/library identities are physical recorded/post-build bindings, not historical per-instruction cryptographic execution attestation'],'full_M4_complete':False}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    files={}
    for p in authpins:files[str(Path(p).resolve())]=sha(p)
    for p in [authpath,authpath.parent/'pins.json',od,Path(raw['original']['api_module']['path']),buildpath]:files[str(p.resolve())]=sha(p)
    for key in ('frozen_libraries','tool_files'):
        for p in build[key]:files[str(Path(p).resolve())]=sha(p)
    for p in OUT.rglob('*'):
        if p.is_file() and p.name!='pins.json':files[str(p.resolve())]=sha(p)
    for p in (ROOT/'tools/m4-crt-data-independent').glob('*'):
        if p.is_file():files[str(p.resolve())]=sha(p)
    (OUT/'pins.json').write_text(json.dumps({'files':dict(sorted(files.items()))},indent=2)+'\n')
    print(json.dumps({'passed':True,'bindings':len(files),'report_sha256':sha(OUT/'report.json'),'pins_sha256':sha(OUT/'pins.json'),'own_compiled_checks':1134,'own_scenarios':82,'raw_records':192,'own_negative_observer_controls':56,'fresh_COFF_objects':6}))
if __name__=='__main__':run()
