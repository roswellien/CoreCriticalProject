"""Isolated static Ghidra pilot with actual body-byte checks and timing receipts."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'analysis'))
from pe import PEImage

GHIDRA = Path('C:/Users/jcbla/AppData/Local/Programs/REA/ghidra_12.1.4_PUBLIC')
JDK = Path('C:/Users/jcbla/AppData/Local/Programs/REA/jdk-21.0.12.1+1')
INVENTORY = ROOT / 'reports/m4-rea-evaluation/initializer-inventory-r1.json'
INVENTORY_SHA = '5ad06d70b0e15c3fdfccff249f99cd4e08ab8220df8de9e3007db9b4802e4226'
SCRIPT = Path(__file__).with_name('MW34GhidraPilot.java')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['provider','game'], required=True)
    ap.add_argument('--output', type=Path, required=True)
    args=ap.parse_args()
    output=args.output.resolve()
    output.mkdir(parents=True,exist_ok=False)
    target=ROOT / ('local/mw3-staged/Shared_DLLs/MSVCRT.DLL' if args.mode=='provider' else 'MW3/Mech3.exe')
    digest=sha(target)
    if sha(INVENTORY)!=INVENTORY_SHA: raise ValueError('inventory changed')
    scriptdir=output/'scripts';scriptdir.mkdir()
    (scriptdir/SCRIPT.name).write_bytes(SCRIPT.read_bytes())
    projectdir=output/'project';projectdir.mkdir()
    launcher=GHIDRA/'support/analyzeHeadless.bat'
    env=dict(os.environ, JAVA_HOME=str(JDK), GHIDRA_JAVA_HOME=str(JDK))
    report=dict(mode=args.mode,target=str(target),target_sha256=digest,script_sha256=sha(SCRIPT),
                script=str(scriptdir/SCRIPT.name),static_only=True,native_executed=False,
                initializer_credit=False,ghidra=str(GHIDRA),java_home=str(JDK),runs=[],passed=False)
    try:
        for warm in (False,True):
            name='warm' if warm else 'cold'
            exported=output/f'{name}-export.json'
            command=[str(launcher),str(projectdir),'MW34Pilot']
            command+=['-process',target.name,'-noanalysis','-readOnly'] if warm else ['-import',str(target),'-analysisTimeoutPerFile','300','-max-cpu','4']
            command+=['-scriptPath',str(scriptdir),'-postScript',SCRIPT.name,str(exported),args.mode,str(target),digest]
            if args.mode=='game': command += [str(INVENTORY),INVENTORY_SHA]
            command+=['-log',str(output/f'{name}-ghidra.log'),'-scriptlog',str(output/f'{name}-script.log')]
            started=time.perf_counter()
            with (output/f'{name}-console.log').open('wb') as log:
                proc=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
            elapsed=time.perf_counter()-started
            run=dict(name=name,command=command,wall_seconds=elapsed,exit_code=proc.returncode,export_present=exported.exists())
            report['runs'].append(run)
            if proc.returncode or not exported.exists(): raise RuntimeError(f'{name} Ghidra failed; inspect retained logs')
            data=json.loads(exported.read_text(encoding='utf-8'))
            if data['target_sha256']!=digest or data['imported_sha256'].lower()!=digest: raise ValueError('target identity changed')
            pe=PEImage(target.read_bytes())
            checked=0
            for function in data['exports']:
                if not function['present'] or not function['decompile_completed']: raise ValueError(f'function missing/decompile failed {function["entry"]:x}')
                for body in function['body_ranges']:
                    off,_=pe.rva_range(body['start']-pe.image_base,body['length'])
                    actual=pe.data[off:off+body['length']]
                    if actual.hex()!=body['bytes_hex'] or hashlib.sha256(actual).hexdigest()!=body['sha256']: raise ValueError('Ghidra body bytes differ from original PE')
                    checked+=len(actual)
            run.update(body_bytes_verified=checked,functions_exported=len(data['exports']),export_sha256=sha(exported),script_seconds=data['script_seconds'],exports_seconds=data['exports_seconds'])
            if args.mode=='game':
                table=data['table']
                if table['conflicts'] or table['existing_exact']+table['created']!=144: raise ValueError('not all initializer seeds admitted conservatively')
                run['table']=dict(existing_exact=table['existing_exact'],created=table['created'],conflicts=table['conflicts'],seed_seconds=table['seed_seconds'])
        if sha(target)!=digest: raise ValueError('original target changed')
        report['passed']=True
    except Exception as exc:
        report['error']=repr(exc)
    finally:
        report['files']={str(p):sha(p) for p in [target,SCRIPT,Path(__file__),INVENTORY,launcher,GHIDRA/'Ghidra/application.properties',JDK/'release']}
        report['elapsed_seconds']=sum(r['wall_seconds'] for r in report['runs'])
        (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(passed=report['passed'],report=str(output/'report.json'),sha256=sha(output/'report.json'),runs=report['runs'],error=report.get('error')),indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__': raise SystemExit(main())
