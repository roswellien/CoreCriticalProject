"""Additive literal/transitive closure for original capture and primary comparison."""
from pathlib import Path
import hashlib,json,re,shutil,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def bind(path):
    p=Path(path).resolve();return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha(p)}
def require(ok,reason):
    if not ok:raise ValueError(reason)
def main():
    out=ROOT/'reports/m4-mixed-startup/original-author-review-r2';require(not out.exists(),'Fresh author seal required');out.mkdir()
    builds=[ROOT/'reports/m4-mixed-startup/original-build-r1/build.json',ROOT/'reports/m4-mixed-startup/original-build-r2/build.json']
    final=json.loads(builds[-1].read_text(encoding='utf-8-sig'));require(final['passed'],'Final original compilation required')
    capture=ROOT/'reports/m4-mixed-startup/original-capture-r1-normal-windows'
    observation=ROOT/'reports/m4-mixed-startup/original-observation-r1/report.json'
    comparison=ROOT/'reports/m4-mixed-startup/original-comparison-r4/report.json'
    controls=ROOT/'reports/m4-mixed-startup/original-causal-controls-r2-normal-windows/report.json'
    recipe=ROOT/'reports/m4-mixed-startup/original-recipe-controls-r1/report.json'
    for p in (capture/'report.json',observation,comparison,controls,recipe):require(json.loads(p.read_text())['passed'],'Required author check failed')
    # Copy current authored comparison/control/document sources separately from
    # the exact compiler-time copies already kept with r1/r2.
    literals=[];files={}
    for p in list(HERE.glob('*'))+[ROOT/'tools/analysis/pe.py']:
        if not p.is_file():continue
        destination=out/'source-copies'/p.relative_to(ROOT);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,destination)
        literals.append({'original_path':str(p),'preserved':str(destination),'sha256':sha(destination),'kind':'current authored source'});files[str(destination)]=bind(destination)
    # Actual MSVC read tlogs supply the selected include/library dependencies.
    # These additive current physical reads close replay provenance; they are
    # explicitly post-build, not falsely described as pre-compilation hashes.
    selected=[]
    for log in Path(final['build']).rglob('*.read.1.tlog'):
        encoded=log.read_bytes();text=encoded.decode('utf-16' if encoded.startswith(b'\xff\xfe') else 'utf-8')
        for line in text.splitlines():
            if line.startswith('^') or not line:continue
            p=Path(line)
            if p.is_file():selected.append(p.resolve())
    unique={str(p).casefold():p for p in selected};dependency_rows=[]
    for p in sorted(unique.values(),key=lambda p:str(p).casefold()):
        row=bind(p);row['capture_time']='additive post-build physical rehash of actual read-tlog dependency'
        if p.suffix.lower() in ('.h','.hpp','.hxx','.inl','.ixx','.cpp','.asm') and not p.is_relative_to(ROOT):
            dst=out/'sdk-source-copies'/(sha(p)+'-'+p.name.lower());dst.parent.mkdir(exist_ok=True);shutil.copyfile(p,dst)
            row['literal_source_copy']=str(dst);literals.append({'original_path':str(p),'preserved':str(dst),'sha256':sha(dst),'kind':'actual SDK/STL read dependency, post-build copy'});files[str(dst)]=bind(dst)
        dependency_rows.append(row);files[str(p)]=bind(p)
    # All assigned original reports, failure snapshots, commands, raw captures,
    # fixture bytes and complete original build artifacts remain physical pins.
    for folder in (ROOT/'reports/m4-mixed-startup').glob('original-*'):
        if folder==out:continue
        for p in folder.rglob('*'):
            if p.is_file():files[str(p.resolve())]=bind(p)
    for p in Path(final['build']).rglob('*'):
        if p.is_file():files[str(p.resolve())]=bind(p)
    # Recheck every recorded binding. Source identities superseded by authored
    # additive scripts resolve through their literal old snapshots, never via
    # the new mutable path. No old manifest is rewritten.
    index={}
    for p in (ROOT/'reports/m4-mixed-startup').glob('original-*'):
        for snapshot in p.rglob('*'):
            if snapshot.is_file() and ('sources' in snapshot.parts or 'source-copies' in snapshot.parts):index.setdefault((snapshot.name.casefold(),sha(snapshot)),[]).append(snapshot.resolve())
    resolutions=[]
    def admit_recorded(name,h):
        p=Path(name)
        if p.is_file() and sha(p)==h:physical=p.resolve()
        else:
            candidates=index.get((p.name.casefold(),h),[]);require(bool(candidates),'No literal resolution for historical source '+str(p));physical=candidates[0]
        files[str(physical)]=bind(physical);resolutions.append({'original_path':str(p),'sha256':h,'physical_path':str(physical)})
    for build_path in builds:
        build=json.loads(build_path.read_text(encoding='utf-8-sig'))
        for name,h in build['bindings'].items():admit_recorded(name,h)
    for folder in (ROOT/'reports/m4-mixed-startup').glob('original-*'):
        if folder==out:continue
        for p in folder.glob('*.json'):
            doc=json.loads(p.read_text(encoding='utf-8-sig'));bindings=doc.get('bindings',{})
            if isinstance(bindings,dict):
                for name,h in bindings.items():admit_recorded(name,h)
    # Comparison's exact native build/map and all literal native artifact/tool
    # bindings are held here; the separate native author closure owns semantics.
    native_build=ROOT/'reports/m4-mixed-startup/native-r3/build.json';native=json.loads(native_build.read_text())
    for key in ('artifacts','tools'):
        for name,h in native[key].items():admit_recorded(name,h)
    files[str(native_build.resolve())]=bind(native_build)
    worker=Path(final['worker']);worker_obj=next(Path(final['build']).rglob('reference.obj'));assembly_obj=next(Path(final['build']).rglob('reference_x86.obj'))
    result={'schema_version':1,'passed':True,'scope':'Author-reviewed selected26 connected original/native prerequisite; independent connected review pending; full M4/CRT/menu open',
            'original_build':bind(builds[-1]),'worker':bind(worker),'original_CPP_object':bind(worker_obj),'original_assembly_object':bind(assembly_obj),
            'pack':bind(Path(final['pack'])),'actual_original_capture':bind(capture/'original.bin'),'original_observer':bind(observation),'final_primary_comparison':bind(comparison),'observer_causal_controls':bind(controls),'recipe_controls':bind(recipe),
            'original_sequences':48,'original_phases':1248,'native_phases':2496,'compiled_original_protocol_checks':3,'actual_original_publisher_checks':2,'actual_original_identity_checks':2,'actual_recipe_no_mutation_checks':3,
            'original_observer_mutations':22,'native_observer_mutations_each_level':29,'native_positive_phase_checks_each_level':26,'positive_undefined_AF_checks_each_level':1,
            'reference_domain':'Exact default image operands;12 masked CW,emptyTOP0/7,initialcleanstatus,two repeats;fresh whole sequence but no phase resets',
            'synthetic_root_frame':{'ESP':0x20001800,'returned_ESP':0x20001804,'return_PC':0x410a80,'only_between_phase_CPU_overrides':['ESP','EIP']},
            'FP_provenance':'Actual original FX512 and legacyENV28 both carried; native State projection distinct; hardware metadata zero vs actual legacy pointer/opcode/selector metadata remains separate',
            'native_State_events':'Original opaque State/events unobserved. Native whole3504 State protection/carry/projection and actual ordered event/call snapshots checked independently against source schedule and hardware results',
            'defined_scope':'Defined CPU CD5 before first XOR thenCC5; FP core exceptions/SF/ES/TOP/B. C1/C0/C2/C3 and dead raw80 equality remain concrete observed domain, not arbitrary architectural guarantees',
            'publication_scope':'Fresh private ordinary directories, sequential writers, CREATE_NEW ownership; no production concurrency/reparse certification',
            'measured_failures_preserved':[str(ROOT/'reports/m4-mixed-startup/original-build-r1'),str(ROOT/'reports/m4-mixed-startup/original-comparison-r1'),str(ROOT/'reports/m4-mixed-startup/original-comparison-r3')],
            'source_copies':literals,'actual_build_read_dependencies':dependency_rows,'historical_binding_resolutions':resolutions,'physical_bindings':len(files),'native_build':bind(native_build)}
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');files[str((out/'report.json').resolve())]=bind(out/'report.json')
    (out/'pins.json').write_text(json.dumps({'schema_version':1,'bindings':list(sorted(files.values(),key=lambda x:x['path'].casefold()))},indent=2)+'\n')
    print(json.dumps({'passed':True,'report':bind(out/'report.json'),'pins':bind(out/'pins.json'),'source_copies':len(literals),'bindings':len(files)}))
if __name__=='__main__':main()
