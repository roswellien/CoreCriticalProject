"""Final checked-writer compatibility; reuse the frozen workload, no new flat tree."""
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
import review
from review import CaptureBundle, need, publish_bytes, read_set, run_stage, sha_file, verify_manifest, verify_stage, workspace_path


def main(directory):
    out = workspace_path(directory,reports=True)
    need(out.parent == ROOT/'reports/m4-capture-direct-root' and not out.exists(),'Fresh final transport review')
    files = {}
    def pin(path,digest=None):
        path = Path(path).absolute(); actual = sha_file(path)
        need(digest is None or actual == digest,'Fixed current input: '+str(path))
        files[str(path)] = actual
        return path
    build_path = pin(ROOT/'reports/m4-capture-direct/build-r4/build.json',
                     '909955901c310e5fcf5eb0713e48a20bf896d13ea335e9d8093dec25ba232e96')
    controls_path = pin(ROOT/'reports/m4-capture-direct/controls-r3/report.json',
                        '770a8a2a4f57fc17b32cffca59ac1267286c4f529ed9c5939661e42848c4681c')
    build,controls = json.loads(build_path.read_bytes()),json.loads(controls_path.read_bytes())
    need(build['passed'] is True and controls['passed'] is True and
         controls['hardware_pairs'] == 108 and controls['refusals'] == 54,
         'Checked API native preservation controls')
    for category in ('sources','tools','artifacts','libraries','compiler_read_headers'):
        for path,digest in build.get(category,{}).items():pin(path,digest)
    for path,digest in controls['files'].items():pin(path,digest)
    expected = {}
    for label,digest in review.FROZEN:
        path = pin(ROOT/'reports/m4-pipeline/benchmark-r3'/(label+'.mwb'),digest)
        with CaptureBundle(path,digest) as reader:
            for name in reader.names():expected[label+'/'+name] = reader.read_bytes(name)
    need(len(expected)==2945,'Same independently frozen logical workload')
    input_path = pin(ROOT/'reports/m4-capture-direct-root/review-r1/representative.records')
    need(input_path.read_bytes()==review.record_input(list(reversed(list(expected.items())))),
         'Exact reused reversed workload input')
    for path in (Path(__file__),Path(review.__file__),Path(sys.executable)):
        pin(path)
    out.mkdir(parents=True); levels = {}
    for level in ('O0','O2'):
        driver = Path(build['workers'][level]); pin(driver,build['artifacts'][str(driver)])
        target,stage = out/level,out/('stage-'+level)
        result = run_stage([str(driver),'replay',str(input_path),str(target)],stage,
                           timeout_seconds=60,inputs=list(files),required_outputs=[target/'transport.json'])
        digest = sha_file(stage/'stage.json')
        verify_stage(stage,digest)
        need(result['passed'],'Actual final native driver compatibility')
        value = read_set(target,expected)
        for path in target.iterdir():pin(path)
        for name in ('stage.json','stdout.bin','stderr.bin'):pin(stage/name)
        levels[level] = dict(stage=str(stage),stage_sha256=digest,native_seconds=result['elapsed_seconds'],**value)
    report = dict(passed=True,scope='Final checked API writer and unchanged strict-reader compatibility',
                  transport_only=True,native_transport_executed=True,game_executed=False,
                  levels=levels,checked_control_hardware_pairs=108,checked_control_refusals=54,
                  same_frozen_logical_files=2945,flat_capture_trees_created=0,
                  new_speedup_benchmark_claimed=False,files=files,current_physical_closure=verify_manifest(files))
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k not in ('files',)}))


if __name__=='__main__':main(*sys.argv[1:])
