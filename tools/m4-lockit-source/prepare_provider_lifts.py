"""Prepare two initialized-domain provider literal lifts and dispatch attribution."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[2];T=ROOT/'tools/m4-lockit-source';B=ROOT/'reports/m4-lockit-source'
rec='3b680223f22d6ac10cf440b885432909bef57b2f697d4df8afecb7f4ef814ad8'
assert hashlib.sha256((B/'provider-recovery-r1/report.json').read_bytes()).hexdigest()==rec
s=(T/'lift.py').read_text().replace('reports/m4-lockit-source/recovery-r1','reports/m4-lockit-source/provider-recovery-r1').replace('25a04a5a9e4cec894c5272d398794850aeab968a22f77b21494706680015fa4d',rec)
s=s.replace('MW3/Mech3.exe','local/mw3-staged/Shared_DLLs/MSVCP50.DLL').replace('95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a')
s=s.replace("re.fullmatch('lifts-r[1-9][0-9]*',name)","re.fullmatch('provider-lifts-r[1-9][0-9]*',name)").replace('root_count=4','root_count=0').replace('Exact game source/COFF preparation only, no initializer execution credit','Exact initialized state2 MSVCP source/COFF preparation only, no initializer execution credit')
s=s.replace('All accepted120 bodies remain unchanged; lift10 additive literal entries only.','All accepted120 bodies remain unchanged; lift two initialized-domain MSVCP entries only.')
(T/'provider_lift.py').write_text(s)
print('Prepared two exact initialized-domain provider lifts')
