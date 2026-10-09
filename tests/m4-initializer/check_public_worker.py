"""Public worker CLI controls; private image execution is a separate gate."""
import argparse
from pathlib import Path
import subprocess
def main():
    p=argparse.ArgumentParser();p.add_argument('--worker',type=Path,required=True);p.add_argument('--native',action='store_true');a=p.parse_args()
    checks=[]
    for name,args,diagnostic in [('no-args',[],'input output code image'),('extra-arg',['a','b','c','d','e'],'input output code image'),
                                 ('unknown-control',['--unknown-control'],'input output code image')]:
        r=subprocess.run([str(a.worker.resolve()),*args],capture_output=True,timeout=30)
        if r.returncode!=1 or diagnostic not in r.stderr.decode(errors='replace'):raise ValueError('Wrong intended diagnostic '+name)
        checks.append(name)
    r=subprocess.run([str(a.worker.resolve()),'--check-protocol'],capture_output=True,timeout=30)
    if r.returncode or b'Protocol controls: 32' not in r.stdout:raise ValueError('Protocol controls did not reach all32 checks')
    checks.append('actual-compiled-protocol32')
    print('Public worker controls:',len(checks))
if __name__=='__main__':main()
