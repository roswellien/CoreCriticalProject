"""Literal author association seal; prior maps and failed attempts stay immutable."""
import argparse,hashlib,json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-fdiv'
def need(v,m):
    if not v:raise ValueError(m)
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with open(p,'rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(out):
    out=pathlib.Path(out).resolve();need(out.parent==BASE and not out.exists(),'Fresh immediate private author seal');files={};versions=[];checks=[]
    def bind(p,expected=None):
        p=pathlib.Path(p).resolve();actual=sha(p);need(expected is None or actual==expected,'Literal identity '+str(p));key=str(p);need(key not in files or files[key]['sha256']==actual,'Conflicting physical versions '+key);files[key]={'path':key,'bytes':p.stat().st_size,'sha256':actual};return actual
    def flat(p):
        m=read(p);bind(p)
        entries=m.get('files',m)
        for path,h in entries.items():bind(path,h)
        return len(entries)
    def build(name,passed):
        p=BASE/name/'build.json';m=read(p);need(m['passed']==passed,'Literal build outcome '+name);bind(p)
        for path,h in m['sources'].items():
            original=pathlib.Path(path);copy=p.parent/'sources'/original.relative_to(ROOT);bind(copy,h)
            if original.is_file()and sha(original)==h:bind(original,h)
            else:versions.append({'build':str(p),'original_path':str(original),'physical_literal':str(copy),'sha256':h})
        for group in('tools','libraries','artifacts'):
            for path,h in m.get(group,{}).items():bind(path,h)
        for command in m['commands']:
            bind(command['log'],command['log_sha256'])
        return m
    for name,passed in(('native-build-r1',False),('native-build-r2',True),('native-build-r3',True),('native-boundary-r1',False),('native-boundary-r2',False),('native-boundary-r3',True)):build(name,passed)
    preservation=BASE/'pre-registry-refinement-r2/manifest.json';pv=read(preservation);need(pv['passed']and pv['source_copies']==50,'Literal pre-refinement preservation');bind(preservation,'4ee782b3803a7c964e31d9cb25e18f5f48f7bb11b76bb4bb810f2c23152acab5')
    for path,h in pv['files'].items():bind(path,h)
    for name in('source-recovery-r1','native-preparation-r1','native-preparation-r2','native-preparation-r3','native-preparation-r4','independent-static-scope-r1','independent-static-continuation-r2'):flat(BASE/name/'pins.json')
    for name in('native-validation-r1','native-entry-validation-r1','native-boundary-validation-r1','native-tooling-r1'):flat(BASE/name/'pins.json')
    raw=read(BASE/'native-validation-r1/report.json');entry=read(BASE/'native-entry-validation-r1/report.json');boundary=read(BASE/'native-boundary-validation-r1/report.json');need(raw['passed']and raw['native_records']==48 and raw['observed_events']==4656 and raw['observer_controls']==720 and len(raw['actual_reached_PCs'])==174,'Actual full source-instruction validation');need(entry['passed']and entry['native_rows']==48 and entry['causal_observers']==624,'Before-only literal seed admission');need(boundary['passed']and boundary['observed_rows']==4 and boundary['required_preservation_corruptions_rejected']==40 and boundary['volatile_SIMD_distinctions_accepted']==4,'Actual outside-call architectural/ABI boundary validation')
    primary=BASE/'native-build-r3/build.json';b=read(primary)
    for level in('O0','O2'):
        text=(primary.parent/f'tests-{level}.log').read_text(encoding='utf-8-sig');stats=json.loads(text.strip().splitlines()[-1]);need(stats=={'passed':True,'native_only':True,'checks':132866,'scenarios':59,'actual_writer_records':24,'FNCLEX_words':65536,'FNCLEX_incoherent_controls':12,'authored_route_units':12,'original_execution':False},'Actual positive and causal compiled assertions')
        controls=re.findall(r'^control (\d+) fault_pc (\d+) address (\d+) reason (\d+) events (\d+)$',text,re.M);units=re.findall(r'^route-unit (\d+) actual_preparation_lookups (\d+) fault_pc (\d+) address (\d+) reason (\d+)$',text,re.M);need([int(x[0])for x in controls]==list(range(23))and [int(x[0])for x in units]==list(range(12)),'All actual compiled denial diagnostics recorded')
        boundary_text=(BASE/'native-boundary-r3'/f'tests-{level}.log').read_text(encoding='utf-8-sig');need(json.loads(boundary_text.strip().splitlines()[-1])=={'passed':True,'checks':54,'scenarios':2,'direct_assembly_boundary':True,'original_execution':False,'volatile_XMM0_5_equality_claimed':False},'Actual compiled direct-boundary assertions')
    checks.append({'name':'Final source/objects/raw/checks and six historical build outcomes retain exact literal associations','passed':True})
    # Bind accepted lowering prerequisites transitively; this does not broaden
    # them or import their computational oracles into the native writer model.
    for report,pins,expected in((ROOT/'reports/m4-crt-control/independent-review-r4/report.json',ROOT/'reports/m4-crt-control/independent-review-r4/pins.json','b75abde48029efcdb8cb123c163c6bfb27a9b76dc62da014e620fca7c95bac56'),(ROOT/'reports/m4-guest-cw/independent-review-r1/report.json',ROOT/'reports/m4-guest-cw/independent-review-r1/pins.json','92d7ee2c40bedf808dd42179393a5fc455a95553f2c7c91b4a13571e5cd525e5')):bind(report,expected);flat(pins)
    runtime=ROOT/'reports/m4-runtime/context-r9/build.json';rm=read(runtime);bind(runtime,'12bd0f42d7fba2cc8b9f7cc4d6b9db795c98e196ae305ac23dbd7fe38b21abf5')
    for path,h in rm['source_files'].items():bind(path,h)
    # The exact imported transformation sources are supplementary current
    # associations; the frozen accepted control body is also independently bound.
    for path in(ROOT/'tools/lifting/host_adapter.py',ROOT/'tools/m4-crt-control/adapt.py',ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/LLVM-C.dll',ROOT/'reports/m4-crt-control/research-r1/host.ll',ROOT/'CMakePresets.json'):
        if path.is_file():bind(path)
    checks.append({'name':'Unchanged accepted r9, CW transfer, control lowering, exact source recovery and supplementary transformation association','passed':True})
    frozen=('adaptation-attempt-r1','adaptation-attempt-r2','adaptation-attempt-r3','source-recovery-attempt-r1','native-preparation-r1','native-preparation-r2','native-preparation-r3','native-preparation-r4','native-derived-r1','native-build-r1','native-build-r2','native-build-r3','native-boundary-r1','native-boundary-r2','native-boundary-r3','native-validation-r1','native-entry-validation-r1','native-boundary-validation-r1','native-tooling-r1','pre-registry-refinement-r2')
    for name in frozen:
        for p in(BASE/name).rglob('*'):
            if p.is_file()and'__pycache__'not in p.parts:bind(p)
    literal=[]
    for directory in(ROOT/'tools/m4-crt-fdiv',ROOT/'tests/m4-crt-fdiv'):
        for p in directory.rglob('*'):
            if p.is_file()and'__pycache__'not in p.parts:literal.append({'path':str(p),'sha256':bind(p)})
    doc=ROOT/'docs/m4-crt-fdiv-native.md';bind(doc);out.mkdir();report={'passed':True,'scope':'Author-tested native-only successful real Windows-query _adjust_fdiv writer and bounded FNCLEX prerequisite; independent closure pending','original_dynamic_writer_execution':False,'native_records':48,'actual_source_PCs':174,'preserved_original_dependency_PCs':204,'actual_events':4656,'actual_stdcall_routes':144,'compiled_checks_per_level':132866,'compiled_scenarios_per_level':59,'FNCLEX_words_per_level':65536,'FNCLEX_incoherent_controls_per_level':12,'early_faults_per_level':23,'authored_private_route_units_per_level':12,'observer_controls':{'source_native':720,'entry':624,'outside_boundary':40,'admitted_volatile_SIMD_distinctions':4},'direct_boundary':{'rows':4,'compiled_checks_per_level':54,'scope':'ENV28/x87/CW/SW/FTW/raw80/MXCSR and ABI XMM6..15, capture before harness cleanup','volatile_XMM0_5_equality':False},'internal_host_snapshots':'FullFX512/ENV28 restoration checkpoint inside initialize; not whole-public-call volatile SIMD equality','provider_sha256':'2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7','game_sha256':'95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf','final_native_build':str(primary),'final_native_build_sha256':sha(primary),'final_boundary_build':str(BASE/'native-boundary-r3/build.json'),'final_boundary_build_sha256':sha(BASE/'native-boundary-r3/build.json'),'checks':checks,'literal_sources':literal,'historical_replacements':len(versions),'physical_bindings_before_report':len(files),'limitations':['Native-only: no original dynamic-writer differential acceptance','Only12 masked IC0 empty TOP0/SW0 writer domain; broad primitive status tests do not expand it','Actual NULL fallback arithmetic denied, only negative bridge fixture/static edge proof','Native ECX/EDX/flags representative and undefined AF/x87 CC are explicit; future originals retain measured volatile residual halfwords','Serial stable Runtime/State and loaded host module borrowers; no concurrent loader/unload/hostile mapping/hotpatch/general SEH proof','Indirect provider hashes and SDK library candidates observed after build; RC child execution and historical linker file-search resolution not inferred','Complete DllMain/CRT entry/initterm tables/game data-consumer integration and startup/menu completion remain open'],'whole_M4_complete':False};(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');pins={'bindings':list(files.values()),'historical_replacements':versions,'literal_sources':literal,'immutable_report':str(out/'report.json'),'immutable_report_sha256':sha(out/'report.json')};(out/'pins.json').write_text(json.dumps(pins,indent=2)+'\n');print(json.dumps({'passed':True,'bindings':len(files),'versions':len(versions),'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json')}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();main(a.out)
