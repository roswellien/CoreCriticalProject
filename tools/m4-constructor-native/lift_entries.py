"""Reuse the exact physical literal lifting pipeline for two new entry points."""
from pathlib import Path
import hashlib,sys
R=Path(__file__).resolve().parents[2];p=R/'tools/m4-remaining-service-source/lift_v2.py';s=p.read_text();q=R/'reports/m4-constructor-native/entry-preparation-r1/report.json';h=hashlib.sha256(q.read_bytes()).hexdigest()
for a,b in [("ROOT/'reports/m4-remaining-service-source/preparation-r2'","ROOT/'reports/m4-constructor-native/entry-preparation-r1'"),("REC_SHA='e137cf7e923009c39de1ba3b6135e0e8ca5b43826f0ec993396f77bd82acc2c4'","REC_SHA='"+h+"'"),("ROOT/'reports/m4-remaining-service-source'/name","ROOT/'reports/m4-constructor-native'/name"),("re.fullmatch('lifts-r[1-9][0-9]*',name)","re.fullmatch('entry-lifts-r[1-9][0-9]*',name)"),("root_count=5","root_count=0"),("pin(ROOT/'tools/m4-remaining-service-source/lift.py');","pin(ROOT/'tools/m4-constructor-native/lift_entries.py');pin(ROOT/'tools/m4-remaining-service-source/lift_v2.py');pin(ROOT/'tools/m4-remaining-service-source/lift.py');")]:
 if s.count(a)!=1:raise ValueError('Exact tail compiler derivative hunk '+a)
 s=s.replace(a,b,1)
exec(compile(s,str(p),'exec'),globals())
