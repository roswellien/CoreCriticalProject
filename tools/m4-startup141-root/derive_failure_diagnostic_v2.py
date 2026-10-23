"""Finite diagnostic-name addition; no worker rerun."""
from pathlib import Path
import hashlib
def main():
 p=Path(__file__).with_name('diagnose_failure_v1.py');t=p.read_text();a="'registry-exception-witness.bin')";b="'registry-exception-witness.bin','locale-summary.bin')";assert t.count(a)==1
 n=t.replace('failure-diagnostic-r1','failure-diagnostic-r2').replace(a,b);assert n.replace(b,a).replace('failure-diagnostic-r2','failure-diagnostic-r1')==t
 q=p.with_name('diagnose_failure_v2.py');assert not q.exists();q.write_text(n);print(hashlib.sha256(q.read_bytes()).hexdigest())
if __name__=='__main__':main()
