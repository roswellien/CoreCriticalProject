"""Independent final causal/source closure; no author executable imports.

The frozen root original/native input models are immutable prior evidence.
This additive closure checks their physical maps, exact linked static bodies,
actual recorded worker controls, and a separate compiled causal harness.
"""
from pathlib import Path
import hashlib,importlib.util,json,re,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
GATE=ROOT/'reports/m4-crt-control-integration'
OUT=GATE/'independent-final-review-r1'
ATTEMPT=OUT/'seal-attempt-r2'
PINS={}
def need(ok,why):
    if not ok:raise ValueError(why)
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def bind(path,expected=None):
    p=Path(path).resolve();h=sha(p)
    need(expected is None or expected==h,'Physical identity '+str(p))
    need(str(p) not in PINS or PINS[str(p)]==h,'Conflicting physical version '+str(p))
    PINS[str(p)]=h;return {'path':str(p),'sha256':h,'size_bytes':p.stat().st_size}
def read(path,expected=None):bind(path,expected);return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def entries(doc):
    result=[]
    for key in ('files','source_files','tool_files','artifacts','sources','tools','bindings'):
        if isinstance(doc.get(key),dict):
            result.extend((p,h) for p,h in doc[key].items() if isinstance(h,str) and re.fullmatch('[0-9a-f]{64}',h))
    def visit(x):
        if isinstance(x,dict):
            if isinstance(x.get('path'),str) and re.fullmatch('[0-9a-f]{64}',str(x.get('sha256',''))):result.append((x['path'],x['sha256']))
            for key,value in x.items():
                if key.endswith('_path') and isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',str(x.get(key[:-5]+'_sha256',''))):result.append((value,x[key[:-5]+'_sha256']))
            for value in x.values():visit(value)
        elif isinstance(x,list):
            for value in x:visit(value)
    visit(doc);return list(dict.fromkeys(result))
def main():
    need(not (OUT/'report.json').exists() and not (OUT/'pins.json').exists() and not ATTEMPT.exists(),'Fresh final independent seal attempt')
    ATTEMPT.mkdir();(ATTEMPT/'seal-source.py').write_bytes(Path(__file__).read_bytes());bind(ATTEMPT/'seal-source.py')
    authorpath=GATE/'author-review-r1/report.json';author=read(authorpath,'5224a32cc92ba202aed8d8465f736533aff3f206116b67b7711a705b21ce65ed')
    authorpins=GATE/'author-review-r1/pins.json';ap=read(authorpins,'e81c837c7640003c4197c86ea881127e22193ab09fd19490153302586c194dcb')['files']
    need(author['passed'] and len(ap)==2493,'Final frozen author closure')
    for p,h in ap.items():bind(p,h)
    print('All2493 final author physical pins verified',flush=True)
    hist=author['historical_source_resolutions'];need(len(hist)==4,'Four exact author historical source versions')
    resolutions={}
    for row in hist:
        map_path=Path(row['historical_map']).resolve();doc=read(map_path,row['historical_map_sha256'])
        need(doc['source_files'][row['original_path']]==row['recorded_sha256'],'Historical owning source map')
        bind(row['physical_path'],row['recorded_sha256'])
        resolutions[(str(map_path).lower(),str(Path(row['original_path']).resolve()).lower(),row['recorded_sha256'])]=row['physical_path']
    associations=[];maps=[]
    def audit_map(path,private=False):
        doc=read(path);claims=entries(doc)
        local={}
        for copy in doc.get('literal_source_copies',[]):
            bind(copy['preserved_path'],copy['sha256']);local[(str(Path(copy['original_path']).resolve()).lower(),copy['sha256'])]=copy['preserved_path']
        # Own direct-compiler recipes preserve sources at an exact relative
        # source pathname. Validate each owning-map hash before using a copy.
        if private:
            for p,h in doc.get('sources',{}).items():
                cp=Path(path).parent/'sources'/Path(p).relative_to(ROOT)
                bind(cp,h);local[(str(Path(p).resolve()).lower(),h)]=str(cp)
        for p,h in claims:
            actual=resolutions.get((str(Path(path).resolve()).lower(),str(Path(p).resolve()).lower(),h),p)
            if sha(actual)!=h:
                actual=local.get((str(Path(p).resolve()).lower(),h),actual)
            bind(actual,h);associations.append({'owning_map':str(Path(path).resolve()),'recorded_path':p,'recorded_sha256':h,'physical_path':str(Path(actual).resolve())})
        maps.append({'map':bind(path),'recorded_associations':len(claims)})
    # Reconcile actual preparation/build/run/failure maps rather than trusting
    # the aggregate author's pass bits or executing its comparator.
    for folder in sorted(GATE.iterdir()):
        if not folder.is_dir() or folder.name.startswith(('independent','author')):continue
        for path in sorted(folder.glob('*.json')):audit_map(path)
    original_path=GATE/'independent-original-model-r1/report.json'
    native_path=GATE/'independent-native-model-r1/report.json'
    originals=read(original_path,'d0cd6207cd940de2f17c0a80242eefd876aab49e3fb35119929f4d37f4da59fb')
    natives=read(native_path,'9849d7d11a06e75b365a63257b70188e042a9f3fe63cda9d80cac0a135b0ebb9')
    need(originals['passed'] and originals['records']==192 and natives['passed'] and natives['native_records']==384,'Frozen own root complete raw models')
    for path,h in ((original_path.parent/'pins.json','2b939c9c10246918deb349d00e20a44c7022c981d71f9200efcd7959abd689fe'),(native_path.parent/'pins.json','23022f630ca431130707f99b1e07e550504e42c4f2159cc7b6d747860aabb14c')):
        for p,d in read(path,h)['files'].items():bind(p,d)
    staticpath=GATE/'independent-static-review-r3/report.json';static=read(staticpath,'f1d5d19fc7080ae389ae017c0d12cda8f0340e4bc274353b7c5d9d8eb54a2c22')
    need(static['passed'] and static['complete_State_bytes']==3504 and static['complete_layout_types']==34 and static['complete_IR_State_alignment']==8,'Independent complete six-PC/ABI proof')
    for p,h in read(staticpath.parent/'pins.json','e67ab8498f76747eade1317898a1879ba48abd4bb132ba27c43ce2edd717709d')['files'].items():bind(p,h)
    # Literal unchanged accepted provider helpers as well as all four bodies.
    rp=ROOT/'tools/m4-crt-control-independent/review.py';bind(rp,'49eea1a0c6615d685acad629c4ef10bab32c6f14aa960a0c1e1d01c6750f6e61')
    spec=importlib.util.spec_from_file_location('own_frozen_provider_static',rp);review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
    old=(ROOT/'reports/m4-crt-control/research-r1/host.ll').read_text();linked=(GATE/'research-r1/host.ll').read_text()
    prior=review.strip_body(old);actual=review.strip_body(linked)
    need(len(prior)==11,'Four accepted provider functions plus seven actual helpers')
    for name,body in prior.items():need(name in actual and review.canonical(body)==review.canonical(actual[name]),'Entire unchanged linked provider body/helper '+name)
    need(set(actual)==set(prior)|{'sub_5ac5a0','sub_5ac5d6',*static['linker_alias_proof']['helper_aliases']},'Complete17 actual linked definitions')
    ownbuilds=[]
    for i in range(1,5):
        path=OUT/f'controls-build-r{i}/build.json';audit_map(path,True);ownbuilds.append({'version':i,'build':bind(path),'passed':read(path)['passed']})
    build=read(OUT/'controls-build-r4/build.json');need(build['passed'] and all(c['exit_code']==0 for c in build['commands']),'Fresh own controls final build/run')
    causal=[];consumed=set()
    for level in ('O0','O2'):
        log=OUT/f'controls-build-r4/{level}/controls.log';need(log.read_text().strip()=='347 independent compiled controls across 33 scenarios passed','Independent compiled controls count')
        causal.append({'level':level,'checks':347,'scenarios':33,'masked_boundary_unaligned_positives':6,'native_only_unmasked_positive':1,'repaired_trigger_poisoned_reuse_scenarios':26,'log':bind(log)})
        for p in re.findall(r'^Note: including file:\s+(.+)$',(OUT/f'controls-build-r4/{level}/compile.log').read_text(),re.M):
            q=Path(p.strip()).resolve();bind(q);consumed.add(str(q))
    need(len(consumed)>100,'Actual postbuild read header closure')
    worker=[]
    for path,levels,marker in ((GATE/'original-normal-windows-r2/report.json',(None,),b'owned connected sentinel\n'),(GATE/'native-run-r1/report.json',('O0','O2'),b'owned native connected sentinel\n')):
        doc=read(path);need(doc['passed'],'Actual successful worker run')
        for command in doc['commands']:
            bind(command['stdout'],command['stdout_sha256']);bind(command['stderr'],command['stderr_sha256'])
            why=command.get('expected_diagnostic');need(command['exit_code']==(1 if why else 0),'Intended exact worker exit '+command['name'])
            if why:need(why in Path(command['stderr']).read_text(),'Actual intended worker diagnostic '+command['name'])
            if 'existing-' in command['name']:
                dest=Path(command['arguments'][-1]);sentinel=dest/'sentinel' if dest.is_dir() else dest
                need(sentinel.read_bytes()==marker,'Exact existing output sentinel preserved');bind(sentinel)
            elif why and command['name'] not in ('bad-cli','extra'):
                dest=Path(command['arguments'][-1]);positives=([doc['raw']] if 'raw' in doc else list(doc['raws'].values()))
                same=[r for r in positives if dest.resolve()==Path(r['path']).resolve()]
                if same:
                    # Missing-pack intentionally reuses the successful output
                    # pathname. Its literal previously bound raw stream must
                    # remain unchanged; absence is not a valid assertion.
                    need(len(same)==1,'Exact existing positive output owner');bind(dest,same[0]['sha256'])
                else:need(not dest.exists(),'Denied worker produced no new result '+command['name'])
        worker.extend(doc['actual_controls'])
    need(len(worker)==29,'Twenty-nine distinct recorded worker controls')
    # Fresh reviewer object decodes include original ASM, full linked guest at
    # both levels, and new independent harness; no author decode reuse.
    tool=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe';bind(tool)
    ob=read(GATE/'original-build-normal-r3/build.json');objects=[Path(p) for p in ob['artifacts'] if Path(p).suffix=='.obj' and ('reference' in Path(p).name)]
    objects.extend(GATE/f'native-build-r1/native-{level}.obj' for level in ('O0','O2'))
    objects.extend(OUT/f'controls-build-r4/{level}/controls.obj' for level in ('O0','O2'))
    need(len(objects)==6,'Complete six distinct compiled original/native/independent objects')
    decodes=[]
    for i,path in enumerate(objects):
        dest=OUT/f'object-{i}.txt';need(not dest.exists(),'Fresh reviewer object decode')
        command=[str(tool),'--disassemble','--reloc','--x86-asm-syntax=intel',str(path)]
        result=subprocess.run(command,capture_output=True);dest.write_bytes(result.stdout);dest.with_suffix('.stderr').write_bytes(result.stderr)
        need(result.returncode==0 and b'file format coff' in result.stdout,'Fresh actual COFF decode')
        decodes.append({'object':bind(path),'decode':bind(dest),'stderr':bind(dest.with_suffix('.stderr')),'command':command})
    copies=[]
    for path in sorted(Path(__file__).parent.glob('*')):
        if not path.is_file():continue
        target=OUT/'sources'/path.name;target.parent.mkdir(exist_ok=True);need(not target.exists(),'New literal reviewer source')
        target.write_bytes(path.read_bytes());copies.append({'current':bind(path),'literal':bind(target)})
    for folder in (GATE/'independent-static-review-r1',GATE/'independent-static-review-r2',GATE/'independent-static-diagnostic-r1'):
        for path in folder.rglob('*'):
            if path.is_file():bind(path)
    (OUT/'report.json').write_text(json.dumps({'passed':True,'scope':'Independent accepted connected complete game control wrapper/thunk plus four actual MSVCRT control bodies through unchanged r9 typed import; no following numerical callback/full startup admission',
        'author_report':bind(authorpath),'author_pins':bind(authorpins),'author_physical_pins_verified':2493,'historical_author_sources':hist,'recorded_maps':maps,'all_recorded_associations':associations,
        'frozen_own_original_model':bind(original_path),'frozen_own_native_model':bind(native_path),'frozen_own_static_proof':bind(staticpath),'original_records':192,'native_records':384,'native_phase_events':sum(x['phase_events'] for x in natives['levels']),'native_completed_Runtime_records':sum(x['r9_records'] for x in natives['levels']),
        'own_raw_corruption_controls':len(originals['observer_controls'])+len(natives['observer_controls']),'own_static_causal_controls':static['static_causal_controls'],'State_bytes':3504,'IR_alignment':8,'all_types':34,'source_PCs':sorted(pc for f in static['game_functions'] for pc in f['source_PCs']),'linked_provider_definitions_unchanged':11,
        'own_compiled_controls':causal,'own_build_versions':ownbuilds,'actual_worker_control_count':29,'actual_worker_controls':worker,'postbuild_actual_header_dependencies':[bind(p) for p in sorted(consumed)],'fresh_COFFs':decodes,'literal_reviewer_sources':copies,
        'checker_failures_preserved':[{'path':str(GATE/'independent-static-review-r1'),'cause':'Strict spelling equality omitted four actual LLVM-renamed identity helpers; exact separate one-to-one helper ABI/body proof now closes it. Initial reviewer also expected seven game helpers; complete game module has exactly four.'},{'path':str(GATE/'independent-static-review-r2'),'cause':'One negative-control literal used wrong unnamed SSA operand, changed no module bytes; caught as noncausal before credit. r3 uses exact measured identifier.'},{'path':str(OUT/'controls-build-r1'),'cause':'Own unsupported assertion expected empty normalized unmasked CW0x037E denial.'},{'path':str(OUT/'controls-build-r2'),'cause':'Diagnostic-only version located that unsupported assertion at scenario18; actual route completed13 events/two calls.'},{'source':bind(OUT/'seal-source.py'),'failure':bind(OUT/'seal-failure.txt'),'cause':'Own initial closure assumed missing-pack output absent; recorded missing-pack uses prior positive output. Repaired check requires that exact positive stream SHA remain unchanged, with distinct result paths still absent.'}],
        'findings':[],'native_only_domain_observation':{'CW':0x37e,'result_CW':0x27e,'empty_state_accepted':True,'actual_original_equivalence_credit':False,'statement':'Frozen typed bridge checks CW normalization and empty/pending state; it does not deny every normalized unmasked CW. Proven actual-original domain remains the twelve masked words.'},
        'ret_frame_convention':'Compiled CALL writes5AC5AF atS-12. r9 orchestration projects callerESP one word above then rewrites the same word at the same address; no additional guest CALL claimed.',
        'capture_PC_projection':'Only actual original instrumentation10000100 projects to actual native return5AC436; original broker source/ASM provenance separately preserved.',
        'quantified_equivalence_domain':{'incoming_CW':[0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f],'incoming_SW':0,'TOP':0,'empty_FTW':True,'MXCSR':0x1f80,'CPU_stack_cases':8,'repeats':2,'final_flags_defined_mask':0xcd5,'undefined_flag_exclusions':0},
        'limitations':['Serial trusted stable Runtime/Context with exact owned mappings; arbitrary host permission/mapping replacement, concurrent/cross-thread invocation and swallowed arbitrary raw memory faults excluded','Fresh sequential private ordinary filesystem paths, no concurrent publisher/reparse/dangling-link credit','Only twelve masked incoming CW equivalence; native-only unmasked positive grants no actual original or numerical x87 credit','Hardware original State/per-access events unobserved; complete native State and source/supervisor route phases checked by frozen independent models','Host restoration requires explicit preserved FX/ENV restore; it does not imply all host code leaves FP untouched','Recorded invocation logs and postbuild physical tools/header identities, no historical per-instruction/module attestation','Same-word import-tail framing is explicit orchestration; no general typed tail-call ABI or complete CRT/SEH/startup table/menu credit'],
        'following_numerical_callback_integrated':False,'whole_M4_complete':False},indent=2)+'\n')
    bind(OUT/'report.json')
    for path in OUT.rglob('*'):
        if path.is_file() and path.name!='pins.json':bind(path)
    (OUT/'pins.json').write_text(json.dumps({'files':dict(sorted(PINS.items()))},indent=2)+'\n')
    print(json.dumps({'passed':True,'bindings':len(PINS),'report_sha256':sha(OUT/'report.json'),'pins_sha256':sha(OUT/'pins.json'),'independent_compiled_checks':694,'independent_compiled_scenarios':66,'fresh_COFFs':6}))
if __name__=='__main__':
    try:main()
    except Exception:
        if ATTEMPT.exists():(ATTEMPT/'seal-failure.txt').write_text(traceback.format_exc())
        raise
