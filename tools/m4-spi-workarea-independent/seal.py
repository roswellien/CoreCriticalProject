"""Independent artifact closure; no author analyzer or fixture helper imports."""
from pathlib import Path
import json,hashlib,subprocess
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/m4-spi-workarea/independent-review-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok,w):
    if not ok:raise AssertionError(w)
def bind(p):p=Path(p).resolve();return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha(p)}
def run():
    require(not (OUT/'report.json').exists() and not (OUT/'pins.json').exists(),'fresh final seal')
    authorpath=ROOT/'reports/m4-spi-workarea/author-review-r2/report.json';pinspath=authorpath.parent/'pins.json'
    require(sha(authorpath)=='f9c08427f0b7dffa3bec7cddc8821c412de810769db0e817b636a9b9e4c70c1b','final author report')
    require(sha(pinspath)=='98a6613a588d54496b2c82c2a09dec0ba0c4b4bb2be7db87eaf9cbbb15f2c47d','final author pins')
    author=json.loads(authorpath.read_text());pins=json.loads(pinspath.read_text())['bindings'];require(len(pins)==1249,'author physical pin count')
    for p,h in pins.items():require(sha(p)==h,'author physical '+p)
    historical=author['historical_replacements'];require(len(historical)==7,'seven literal historical replacements')
    resolution={}
    for row in historical:
        require(sha(row['preserved'])==row['sha256'],'historical literal')
        doc=json.loads(Path(row['owning_map']).read_text());require(doc['sources'][row['historical']]==row['sha256'],'historical owning map')
        resolution[(str(Path(row['owning_map']).resolve()).lower(),str(Path(row['historical']).resolve()).lower(),row['sha256'])]=row['preserved']
    associations=[];maps=[]
    for folder in (ROOT/'reports/m4-spi-workarea').iterdir():
        if not folder.is_dir() or folder.name.startswith(('independent','author')):continue
        for p in folder.glob('*.json'):
            doc=json.loads(p.read_text());records=[]
            for k in ('sources','tools','artifacts','bindings','files'):
                value=doc.get(k,{})
                if isinstance(value,dict):records.extend((x,y) for x,y in value.items() if isinstance(y,str) and len(y)==64)
            def walk(x):
                if isinstance(x,dict):
                    if isinstance(x.get('path'),str) and isinstance(x.get('sha256'),str):records.append((x['path'],x['sha256']))
                    for key,value in x.items():
                        if key.endswith('_path') and isinstance(value,str) and isinstance(x.get(key[:-5]+'_sha256'),str):records.append((value,x[key[:-5]+'_sha256']))
                    for value in x.values():walk(value)
                elif isinstance(x,list):
                    for value in x:walk(value)
            walk(doc)
            if records:maps.append({'map':bind(p),'recorded_bindings':len(records)})
            for path,h in records:
                actual=resolution.get((str(p.resolve()).lower(),str(Path(path).resolve()).lower(),h),path)
                require(sha(actual)==h,'recorded map association '+str(p)+' '+path)
                associations.append({'map':str(p.resolve()),'recorded_path':path,'recorded_sha256':h,'physical_path':str(Path(actual).resolve())})
    rawpath=OUT/'raw-r3/report.json';raw=json.loads(rawpath.read_text());require(raw['passed'] and raw['original_records']==144 and raw['native_records']==288,'own raw model')
    buildpath=OUT/'controls-r1/build.json';build=json.loads(buildpath.read_text());require(build['passed'],'own causal compile')
    for k in ('sources','tools','artifacts'):
        for p,h in build[k].items():require(sha(p)==h,'own controls binding '+p)
    causal=[]
    for level in ('O0','O2'):
        p=OUT/f'controls-r1/{level}/controls.log';r=json.loads(p.read_text().strip());require(r=={'passed':True,'checks':68,'scenarios':29,'corrected_unentered_contexts':5,'publication':3,'actual_provider_calls':0},'own actual controls')
        causal.append({'level':level,**r,'log':bind(p)})
    capture=json.loads((ROOT/'reports/m4-spi-workarea/capture-r4-normal-windows/capture.json').read_text())
    for command in capture['commands']:require(command['exit_code']==0 and sha(command['log'])==command['log_sha256'],'actual capture log binding')
    first=json.loads((OUT/'raw-r1/report.json').read_text());require(not first['passed'] and 'native-serviceSIMDcarry' in first['failure'],'initial checker failure retained')
    # Fresh actual object/relocation decoding; old author decodes remain frozen.
    od=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
    build4=json.loads((ROOT/'reports/m4-spi-workarea/build-r4/build.json').read_text())
    candidates=[]
    def search(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if isinstance(k,str) and k.endswith(('.obj','.o')) and ('native.cpp' in k or k.endswith('reference.obj') or 'reference_x86' in k):candidates.append(Path(k))
                search(v)
        elif isinstance(x,list):
            for v in x:search(v)
    search(build4)
    candidates += [OUT/f'controls-r1/{level}/controls.obj' for level in ('O0','O2')]
    candidates=list(dict.fromkeys(candidates));require(len(candidates)>=6,'original/native/fixture COFF coverage')
    decodes=[]
    for i,p in enumerate(candidates):
        dest=OUT/f'object-{i}.txt';require(not dest.exists(),'new decode');cmd=[str(od),'--disassemble','--reloc','--x86-asm-syntax=intel',str(p)]
        q=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True);dest.write_bytes(q.stdout);(OUT/f'object-{i}.stderr').write_bytes(q.stderr)
        require(b'file format coff' in q.stdout,'actual COFF object');decodes.append({'object':bind(p),'disassembly':bind(dest),'command':cmd})
    copies=[]
    for p in sorted((ROOT/'tools/m4-spi-workarea-independent').glob('*')):
        if not p.is_file():continue
        target=OUT/'sources'/p.name;target.parent.mkdir(exist_ok=True);require(not target.exists(),'new review literal');target.write_bytes(p.read_bytes());copies.append({'source':bind(p),'literal':bind(target)})
    observation_counts={}
    original=(ROOT/'reports/m4-spi-workarea/capture-r4-normal-windows/original.bin').read_bytes()
    for i in range(8):observation_counts['XMM'+str(i)+'_changed']=sum(original[24+j*36360+116+160+i*16:24+j*36360+116+176+i*16]!=original[24+j*36360+628+160+i*16:24+j*36360+628+176+i*16] for j in range(144))
    report={'passed':True,'scope':'Independent bounded22-instruction handwritten caller / actual host64 SPI_GETWORKAREA query gate; no Remill lift, provider machine-code translation or connected startup acceptance','author_report':bind(authorpath),'author_pins':bind(pinspath),'author_physical_bindings':1249,'historical_source_resolutions':historical,'recorded_maps':maps,'recorded_binding_associations':associations,'own_raw_model':bind(rawpath),'original_records':144,'native_records':288,'whole_State_bytes_compared':288*7008,'native_ordered_events':9792,'raw_results':raw['results'],'provider_identity':raw['providers'],'original_SIMD_observations':observation_counts,'own_actual_compiled_causal_controls':causal,'fresh_actual_COFF_decodes':decodes,'literal_review_sources':copies,'checker_versions':[{'version':1,'source':bind(OUT/'raw-r1/model-source.py'),'report':bind(OUT/'raw-r1/report.json'),'failure':bind(OUT/'raw-r1/failure.txt'),'issue':'Independent observer-control list alias appended original-only SIMD carry assertion into native list; invalid assertion rejected this checker, not the gate.'},{'version':2,'source':bind(OUT/'raw-r2/model-source.py'),'report':bind(OUT/'raw-r2/report.json'),'repair':'Distinct control list copies keep original observed SIMD separate from native host-query observations.'},{'version':3,'source':bind(OUT/'raw-r3/model-source.py'),'report':bind(rawpath),'extension':'Separate native hardware query FX/legacy coherence and discarded BOOL positive; no change to guest/API defined-output domain.'}],'context_contract_clarification':{'pre_entry_guard_failure':'does not consume or poison an unentered Context; corrected guard inputs can subsequently execute, proven by five causal corrections per level','entered_body_failure':'used/failed context remains rejected after its memory/input is repaired, proven by five causal entered-failure scenarios per level','existing_author_reuse_controls':'repeat unchanged invalid guard inputs; they demonstrate repeated denial, not blanket pre-entry poison'},'reviewed_contracts':['Actual22 source instructions and three tail-route roots hash/byte-bound to admitted game and real table slot5E0110','Exact action30 / zero / owned RECT16 / zero arguments, named IAT owner, guest frame and flat DF0 checked; no guest pointer cast into host API','Original32 actual provider on real Windows thread stack; hardwareCALLentry computed then actual postCALL ESP proves20 advance separately from logical guest cleanup16 projection','All original volatile ECX/EDX/flags and SIMD observations kept and carried to final caller; native representative policy separately checked, no fabricated cross-equality','All three whole pages before/after, full native3504 State and34 source-ordered typed guest memory events independently modeled','Outer host architectural FP/legacy restoration checked, original hardware versus native software guest projection versus native actual host-query snapshots separate','False and unusual nonzero BOOL, full signed RECT and no-write reply behavior proven only by own authored query fixtures','Exclusive CREATE_NEW stage ownership and prior-result/stage preservation verified separately from query behavior'],'official_sources':[{'url':'https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-systemparametersinfoa','supports':'Action0x0030 queries primary-display work area into RECT in physical pixels.'},{'url':'https://learn.microsoft.com/en-us/cpp/cpp/stdcall?view=msvc-170','supports':'x86 callee argument cleanup; x64 modifier has no separate stack cleanup convention.'}],'findings':[],'limitations':['Native caller is handwritten bounded translation, no Remill/startup table admission','GetProcAddress target pointer was not separately serialized; exact post-load USER32 disk identity, named export, compiled call source and broker provide bounded provenance rather than complete loaded-target execution attestation','Broker service PC fields are authored call/continuation metadata; logical guest ESP is instrumentation projection, physical provider ESP delta is separate actual evidence','Original State/per-access events unobserved; native State/events modeled against source and actual service outputs','Captured desktop actual RECT agrees across original/O0/O2; no hardcoded dimensions or future changed-desktop equality guarantee','x87/MXCSR/legacy unchanged observations here grant no general Windows service FP guarantee; XMM/ECX/EDX/arithmetic flags are unconsumed service-ABI outputs','Context orchestration is one worker thread with owned stable memory; no generic concurrent/cross-thread admission or thread-affinity guarantee','Initial six prefix stores check output-map writability before real query; deliberate concurrent permission replacement outside owned-context scope','Fresh sequential private ordinary filesystem directories; destination concurrency and reparse safety outside scope','No actual false-provider capture credit from authored BOOL fixtures; all actual original captures returned nonzero','Compiler/header/disk identities are post-build physical rehashes, not historical per-instruction process/module attestation'],'full_M4_complete':False}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    allpins={str(Path(p).resolve()):sha(p) for p in pins}
    for p in [authorpath,pinspath,od,buildpath]:allpins[str(p.resolve())]=sha(p)
    for p in OUT.rglob('*'):
        if p.is_file() and p.name!='pins.json':allpins[str(p.resolve())]=sha(p)
    for p in (ROOT/'tools/m4-spi-workarea-independent').glob('*'):
        if p.is_file():allpins[str(p.resolve())]=sha(p)
    for p in build['tools']:allpins[str(Path(p).resolve())]=sha(p)
    (OUT/'pins.json').write_text(json.dumps({'files':dict(sorted(allpins.items()))},indent=2)+'\n')
    print(json.dumps({'passed':True,'bindings':len(allpins),'report_sha256':sha(OUT/'report.json'),'pins_sha256':sha(OUT/'pins.json'),'own_causal_checks':136,'own_causal_scenarios':58,'own_negative_controls':126,'own_positive_controls':10,'COFF_decodes':len(decodes)}))
if __name__=='__main__':run()
