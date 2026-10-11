"""Prepare additive literal four-root tools without editing accepted120 tools."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
T=ROOT/'tools/m4-lockit-source';R=ROOT/'reports/m4-lockit-source'
rec='25a04a5a9e4cec894c5272d398794850aeab968a22f77b21494706680015fa4d'
assert hashlib.sha256((R/'recovery-r1/report.json').read_bytes()).hexdigest()==rec
s=(ROOT/'tools/m4-next-source/lift.py').read_text()
s=s.replace('reports/m4-next-source/recovery-r1','reports/m4-lockit-source/recovery-r1').replace('99e59ac4b9adeb98f2227361f80db78e12eead87e35212d71b4147a8ba9effeb',rec).replace("out=ROOT/'reports/m4-next-source'","out=ROOT/'reports/m4-lockit-source'")
s=s.replace('# All accepted103 bodies remain unchanged; lift17 new literal entries only.','# All accepted120 bodies remain unchanged; lift10 additive literal entries only.')
assert "REC=ROOT/'reports/m4-lockit-source/recovery-r1'"in s
(T/'lift.py').write_text(s)
if __name__=='__main__':print('Prepared additive four-root literal lift; accepted tools untouched')
