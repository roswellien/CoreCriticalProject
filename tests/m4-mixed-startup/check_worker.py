"""Actual worker admission/publication denials; no original or native body runs."""
from pathlib import Path
import argparse,hashlib,json,subprocess
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--worker',required=True);ap.add_argument('--image',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
 worker=Path(a.worker).absolute();image=Path(a.image).absolute();out=Path(a.output).absolute()
 root=Path(__file__).resolve().parents[2];out.relative_to(root/'reports/m4-mixed-startup');out.mkdir(parents=True,exist_ok=False)
 original=image.read_bytes();altered=bytearray(original);altered[0]^=1;(out/'changed.exe').write_bytes(altered);(out/'truncated.exe').write_bytes(original[:-1])
 sentinel=b'preexisting user output remains owned by caller\n';existing=out/'existing.bin';existing.write_bytes(sentinel)
 destination_directory=out/'destination-directory';destination_directory.mkdir();(destination_directory/'sentinel.txt').write_bytes(sentinel)
 cases=[('wrong-cli',[],None,'Usage:'),('missing-image',[str(out/'missing.exe'),str(out/'missing-output.bin')],out/'missing-output.bin','Admitted image unavailable'),
  ('changed-image',[str(out/'changed.exe'),str(out/'changed-output.bin')],out/'changed-output.bin','image'),
  ('truncated-image',[str(out/'truncated.exe'),str(out/'truncated-output.bin')],out/'truncated-output.bin','image'),
  ('existing-file',[str(image),str(existing)],None,'Fresh mixed output required'),('existing-directory',[str(image),str(destination_directory)],None,'Fresh mixed output required')]
 records=[]
 for name,args,destination,message in cases:
  command=[str(worker)]+args;p=subprocess.run(command,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);log=out/(name+'.log');log.write_bytes(p.stdout)
  if p.returncode!=1 or message.lower().encode() not in p.stdout.lower():raise ValueError('Wrong denial cause: '+name)
  if destination is not None and destination.exists():raise ValueError('Rejected worker published output: '+name)
  if existing.read_bytes()!=sentinel or (destination_directory/'sentinel.txt').read_bytes()!=sentinel:raise ValueError('Caller-owned sentinel changed')
  if list(out.glob('*.mixed-stage-*')):raise ValueError('Rejected worker leaked stage ownership')
  records.append(dict(name=name,command=command,exit_code=p.returncode,log=str(log),log_sha256=sha(log),cause=message))
 report=dict(passed=True,actual_worker_denials=6,scope='Admission/publication denials before original/native guest execution; no race/reparse/hardlink coverage',worker=dict(path=str(worker),sha256=sha(worker)),image=dict(path=str(image),sha256=sha(image)),source=dict(path=str(Path(__file__).resolve()),sha256=sha(Path(__file__).resolve())),cases=records)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=True,actual_worker_denials=6)))
if __name__=='__main__':main()
