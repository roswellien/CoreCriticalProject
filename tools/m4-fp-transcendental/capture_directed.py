"""Run only the exact built private directed original observer."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        while b:=f.read(1048576):h.update(b)
    return h.hexdigest()
def main():
    build,directory=map(lambda p:Path(p).resolve(),sys.argv[1:3])
    if not directory.is_relative_to(ROOT/'reports/m4-fp-transcendental') or directory.exists():raise ValueError('Fresh private capture directory required')
    metadata=json.loads(build.read_text());assert metadata['passed']
    for path,sha in metadata['bindings'].items():
        if digest(path)!=sha:raise ValueError('Directed build binding changed: '+path)
    worker=Path(metadata['original_worker']);assert worker.is_relative_to(ROOT/'build')
    directory.mkdir(parents=True);output=directory/'original.bin'
    command=[str(worker),str(ROOT/'reports/m4-fp-startup/research-r1/pages.bin'),str(ROOT/'MW3/Mech3.exe'),str(output)]
    result=subprocess.run(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=190)
    (directory/'stdout.log').write_bytes(result.stdout);(directory/'stderr.log').write_bytes(result.stderr)
    report={'passed_capture':result.returncode==0 and output.exists() and output.stat().st_size==24+6144*75988,
            'scope':'Actual directed original four-cosine only; all native equivalence remains unadmitted',
            'command':command,'working_directory':str(ROOT),'exit_code':result.returncode,
            'input_count':32,'root_count':4,'masked_CWs':12,'TOPs':[0,7],'repeats':2,'records':6144,
            'original_output_exists':output.exists(),'bindings':{str(build):digest(build),str(Path(__file__).resolve()):digest(__file__)}}
    for file in directory.iterdir():report['bindings'][str(file)]=digest(file)
    (directory/'capture.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='bindings'}))
    return 0 if report['passed_capture'] else 1
if __name__=='__main__':sys.exit(main())
