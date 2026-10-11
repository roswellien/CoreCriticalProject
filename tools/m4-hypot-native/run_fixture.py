"""One independently reviewed finite native writer, with closed subprocesses."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import time
import traceback
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'reports/m4-hypot-native'


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main(build_path,build_sha,review_path,review_sha,name):
    assert re.fullmatch('fixture-execution-r[1-9][0-9]*',name)
    out=AREA/name;assert not out.exists();out.mkdir()
    pins={};runs=[];passed=False;began=time.perf_counter()
    def pin(p,h=None):
        p=Path(p).resolve();assert p.suffix.lower() not in ('.mwb','.zip')
        actual=sha(p);assert h is None or actual==h,p
        assert str(p) not in pins or pins[str(p)]==actual;pins[str(p)]=actual;return p
    def load(p,h=None):return json.loads(pin(p,h).read_bytes())
    try:
        review=load(review_path,review_sha);assert review['passed']
        build=load(build_path,build_sha);assert build['passed'] and set(build['workers'])=={'O0','O2'}
        # The current review must physically bind this exact build receipt.
        assert review['files'][str(Path(build_path).resolve())]==build_sha
        for q,h in review['files'].items():pin(q,h)
        prep=load(build['preparation'],build['preparation_sha256']);assert prep['passed']
        for q,h in prep['files'].items():pin(q,h)
        input_report=load(prep['inputs'],prep['inputs_sha256']);assert input_report['passed']
        states=pin(Path(prep['inputs']).parent/'input-state.bin')
        image=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
        assert len(input_report['cases'])==6 and not input_report['numerical_results_seeded']
        pin(__file__);pin(sys.executable)
        for level in ('O0','O2'):
            worker=pin(build['workers'][level]['path'],build['workers'][level]['sha256'])
            for case in input_report['cases']:
                seq=case['sequence'];pack=pin(case['pack'],case['pack_sha256'])
                native=out/(level+'-'+str(seq));args=list(map(str,[worker,image,pack,states,seq,native]))
                start=time.perf_counter()
                r=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=30,creationflags=0x08000000)
                stem=level+'-'+str(seq);(out/(stem+'.stdout')).write_bytes(r.stdout);(out/(stem+'.stderr')).write_bytes(r.stderr)
                run=dict(level=level,sequence=seq,argv=args,exit_code=r.returncode,seconds=time.perf_counter()-start,
                    process_closed=True,output=str(native),complete=(native/'COMPLETE.txt').exists())
                runs.append(run);print(json.dumps(run),flush=True)
                assert r.returncode==0 and run['complete'],'Native numeric '+stem
        for q,h in pins.items():assert sha(q)==h,q
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        report=dict(passed=passed,scope='Actual finite registered native numeric root writer; source comparison remains separate',
            build=str(build_path),build_sha256=build_sha,review=str(review_path),review_sha256=review_sha,
            runs=runs,files=pins,artifacts={str(p):sha(p) for p in out.rglob('*') if p.is_file()},
            all_processes_closed=all(r['process_closed'] for r in runs),archive_reader_opened=False,
            source_after_seed=False,numerical_expected_seed=False,native_executed=bool(runs),
            source_native_equivalence=False,initializer_credit=0,seconds=time.perf_counter()-began)
        p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(passed=passed,sha256=sha(p),closed_runs=len(runs))))


if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])
