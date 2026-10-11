"""Create additive four-root source lift and attribution tools from sealed116."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2];T=R/'tools/m4-next-source';B=R/'reports/m4-next-source'
rec='99e59ac4b9adeb98f2227361f80db78e12eead87e35212d71b4147a8ba9effeb'
assert hashlib.sha256((B/'recovery-r1/report.json').read_bytes()).hexdigest()==rec
s=(R/'tools/m4-container-source/lift_v2.py').read_text()
s=s.replace('reports/m4-container-source/recovery-r3','reports/m4-next-source/recovery-r1').replace('b078cff8698dfbefa8d4e45a0368d4820e72c7d659520161e4316e77d3c2f26b',rec).replace("out=ROOT/'reports/m4-container-source'","out=ROOT/'reports/m4-next-source'").replace('root_count=7','root_count=4')
assert "REC=ROOT/'reports/m4-next-source/recovery-r1'"in s
(T/'lift.py').write_text(s)
if __name__=='__main__':print('Prepared additive literal lift tool; no prior sources edited')
