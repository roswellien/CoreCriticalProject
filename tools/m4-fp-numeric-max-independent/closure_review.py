"""Additive closure of the frozen root native review; no author code imports."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import traceback

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];GATE=ROOT/'reports/m4-fp-numeric-max';PINS={}

def need(ok,why):
    if not ok:raise ValueError(why)

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def bind(p,expected=None):
    p=Path(p).resolve();got=sha(p);need(expected is None or got==expected,'Exact physical closure identity '+str(p))
    need(str(p) not in PINS or PINS[str(p)]==got,'Conflicting closure identity');PINS[str(p)]=got;return p

def read(p,h=None):return json.loads(bind(p,h).read_text(encoding='utf-8-sig'))

def execute(command,stem):
    cp=subprocess.run([str(x) for x in command],capture_output=True)
    stem.with_suffix('.stdout').write_bytes(cp.stdout);stem.with_suffix('.stderr').write_bytes(cp.stderr)
    bind(stem.with_suffix('.stdout'));bind(stem.with_suffix('.stderr'))
    return cp

def load_review():
    p=bind(ROOT/'tools/m4-fp-numeric-max-independent/native_review.py')
    previous=read(GATE/'independent-native-review-r6/pins.json')
    need(previous['files'][str(p)]==sha(p),'Frozen passing review source')
    spec=importlib.util.spec_from_file_location('own_root_native_review',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main(out):
    need(not out.exists() and out.is_relative_to(GATE),'Fresh additive independent closure')
    out.mkdir(parents=True);(out/'closure-source.py').write_bytes(Path(__file__).read_bytes());bind(out/'closure-source.py')
    try:
        r=read(GATE/'independent-native-review-r6/report.json','a93a0fa4d858701180fd8f7874e0db7f162d5ae38f5a095f9ac342c8076f98d1')
        pins=read(GATE/'independent-native-review-r6/pins.json','888d7838cccba2d14a3dfb2734b2064a575b5d2107ecad85c2d06c3eb3c3c599')
        for p,h in pins['files'].items():bind(p,h)
        need(r['passed'] and r['native_records']==29376 and r['native_ordered_events']==352512 and r['native_routes']==29376,'Frozen whole raw native pass')
        own=load_review();failed=[]
        for n in range(1,6):
            directory=GATE/f'independent-native-review-r{n}'
            for p in directory.rglob('*'):
                if p.is_file():bind(p)
            failed.append({'attempt':n,'literal_source':str(directory/'review-source.py'),'source_sha256':sha(directory/'review-source.py'),'diagnostic':str(directory/'failure.txt')})
        seal=read(GATE/'author-review-r1/report.json','93e1d9f1ffb72592a2d36bbcaad934e8a9af98af2884a7280ba71b418c662563')
        resolution={}
        for row in seal['historical_binding_resolutions']:
            key=(str(Path(row['original_path']).resolve()).casefold(),row['sha256']);actual=bind(row['physical_path'],row['sha256'])
            need(key not in resolution or resolution[key]==actual,'Unambiguous historical literal identity');resolution[key]=actual
        copies=0
        for row in seal['source_copies']:
            x=row['preserved'];p=bind(x['path'],x['sha256']);need(p.stat().st_size==x['size_bytes'],'Exact literal source extent');copies+=1
        need(copies==547 and len(seal['actual_read_dependencies'])==570,'Complete source/read dependency inventory')
        for row in seal['actual_read_dependencies']:
            p=bind(row['path'],row['sha256']);need(p.stat().st_size==row['size_bytes'],'Read dependency extent')
        maps=0;historical=0
        # Revisit every build/identity map referenced by the seal, resolving only
        # explicit old literal copies rather than changed public sources.
        for p in sorted((GATE).rglob('*.json')):
            if 'independent-native' in str(p) or 'independent-original' in str(p) or 'independent-closure' in str(p):continue
            if p.name not in ('build.json','manifest.json','report.json','pins.json'):continue
            j=json.loads(p.read_text(encoding='utf-8-sig'));maps+=1;bind(p)
            for key in ('sources','bindings','files','source_files','tool_files','artifacts'):
                value=j.get(key,{})
                if not isinstance(value,dict):continue
                for original,h in value.items():
                    if not isinstance(h,str) or not re.fullmatch('[0-9a-f]{64}',h):continue
                    if Path(original).is_file() and sha(original)==h:bind(original,h)
                    else:
                        rk=(str(Path(original).resolve()).casefold(),h);need(rk in resolution,'Explicit literal historical map resolution '+original);bind(resolution[rk],h);historical+=1
        module_checks=[]
        for entry in (0x4c19f0,0x4c1a00,0x780c10f0):
            guest=bind(GATE/f'recovery-r1/{entry:x}.ll').read_text()
            # Use tuple capture explicitly: PC-load SSA and source length.
            increments=[int(length) for _,length in re.findall(r'%([0-9]+) = load i32, ptr %NEXT_PC, align 4\n  store i32 %\1, ptr %PC, align 4\n  %\d+ = add i32 %\1, (\d+)\n  store i32 %\d+, ptr %NEXT_PC, align 4',guest)]
            expected=(1,2,5,1,1) if entry==0x4c19f0 else (1,2,6,6,*([10]*10),1,1) if entry==0x4c1a00 else (6,1)
            need(tuple(increments)==expected,'Own lifted source PC/length schedule')
            repaired=bind(GATE/f'repaired-r2/{entry:x}-repaired.ll').read_text()
            for name in ('linked.ll','verified.ll'):
                module=bind(GATE/'repaired-r2'/name).read_text()
                need(own.canonical(own.body(module,entry))==own.canonical(own.body(repaired,entry)),'Exact compiled-module body '+name)
                need('target triple = "x86_64-pc-windows-msvc"' in module and '__remill_missing_block' not in module,'Complete AMD64 module without missing blocks')
            module_checks.append({'entry':entry,'source_instructions':len(increments),'PC_increments':increments,'linked_and_verified_equal':True})
        actual=[];pack=bind(GATE/'recovery-r1/pages.bin');game=bind(ROOT/'MW3/Mech3.exe');provider=bind(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL')
        changed={}
        for label,p in (('pack',pack),('game',game),('provider',provider)):
            b=bytearray(p.read_bytes());b[100]^=1;q=out/f'changed-{label}.bin';q.write_bytes(b);changed[label]=bind(q)
        for level in ('O0','O2'):
            exe=bind(GATE/f'repaired-r2/build-{level}/mw34_numeric_native.exe')
            cp=execute([exe,'--check-context',pack,game,provider],out/f'{level}-context')
            need(cp.returncode==0 and cp.stderr==b'' and cp.stdout.strip()==b'Compiled controls positives=12 pre-entry denials=29 poisoned reuse=28 typed bridge faults=3 total=72','Fresh actual72 compiled context checks')
            actual.append({'level':level,'kind':'72 actual compiled context controls','passed':True})
            publication=out/f'publication-{level}'
            cp=execute([exe,'--check-publication',publication],out/f'{level}-publication')
            need(cp.returncode==0 and cp.stderr==b'' and cp.stdout.strip()==b'2 actual publisher admission controls passed','Fresh actual publisher denials')
            actual.append({'level':level,'kind':'2 actual nonoverwrite publisher controls','passed':True})
            for label in changed:
                args=[pack,game,provider];args[('pack','game','provider').index(label)]=changed[label];dest=out/f'{level}-denied-{label}.bin'
                cp=execute([exe,*args,dest],out/f'{level}-denied-{label}')
                diagnostic=('Exact '+label+' identity rejected').encode()
                need(cp.returncode==1 and cp.stdout==b'' and cp.stderr.strip()==diagnostic and not dest.exists(),'Actual changed '+label+' denied before output/body')
                actual.append({'level':level,'kind':'actual changed-'+label+' entry denial','diagnostic':diagnostic.decode(),'passed':True})
        causal=read(GATE/'causal-controls-r1-normal-windows/report.json','69e376d51a9b37486e74c7fe0ae99684b83799d6cbc5869050c0ec845175cec7')
        need(causal['passed'] and causal['observer_negative_count']==94 and causal['observer_positive_count']==12 and causal['actual_identity_denials']==9 and causal['actual_publication_checks']==6 and len(causal['recipe_no_mutation_controls'])==4,'Recorded author causal closure counts')
        for p in out.rglob('*'):
            if p.is_file():bind(p)
        report={'passed':True,'scope':'Independent accepted bounded standalone numeric-max prerequisite; source/native/identity/failure closure. Shared Runtime/MSVCP50 integration and full M4 remain open.',
            'raw_review_path':str(GATE/'independent-native-review-r6/report.json'),'raw_review_sha256':sha(GATE/'independent-native-review-r6/report.json'),
            'native_records':29376,'original_records':14688,'ordered_events':352512,'routes':29376,'actual_original_checkpoints':7344,
            'complete_native_State_bytes':3504,'source_module_checks':module_checks,'additional_actual_controls':actual,
            'literal_sources':copies,'actual_read_dependencies':570,'historical_maps_checked':maps,'historical_source_resolutions_used':historical,
            'preserved_reviewer_failures':failed,'reviewer_failure_scope':'All failures were reviewer cache/schema/label canonicalization assumptions; actual author production sources and guest artifacts unchanged.',
            'shared_Runtime_integrated':False,'whole_M4_complete':False,'limitations':r['limitations']}
        rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');bind(rp);bind(Path(__file__))
        (out/'pins.json').write_text(json.dumps({'files':dict(sorted(PINS.items()))},indent=2)+'\n')
        print(json.dumps({'passed':True,'report_sha256':sha(rp),'pins_sha256':sha(out/'pins.json'),'bindings':len(PINS)}))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
