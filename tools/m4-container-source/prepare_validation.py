"""Additive116 structural validator, preserving the accepted109 checker."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];p=ROOT/'tools/m4-container-source/validate_original.py';assert not p.exists();s=(ROOT/'tools/m4-fs-source/validate_original.py').read_text()
s=s.replace("BASE=ROOT/'reports/m4-fs-source'","BASE=ROOT/'reports/m4-container-source'").replace('original109','original116').replace('original109','original116').replace('original-run-r2','original-execution-r1').replace('MW4J109O','MW4J116O').replace('(1,6,109,654,35,291456)','(1,6,116,696,37,307840)').replace('len(data)==291456','len(data)==307840').replace('data,290928','data,307312').replace('data,290944','data,307328').replace('<81I','<88I').replace('/108/','/115/').replace('phases=654','phases=696').replace('record_bytes=291456','record_bytes=307840').replace('persistent35observedpages','persistent37observedpages')
old="roots+=json.loads(pin(BASE/'recovery-r3/fs-roots.json').read_bytes());roots.sort"
new="roots+=json.loads(pin(ROOT/'reports/m4-fs-source/recovery-r3/fs-roots.json').read_bytes());roots+=json.loads(pin(BASE/'recovery-r3/container-roots.json').read_bytes());roots.sort"
assert s.count(old)==1;s=s.replace(old,new);p.write_text(s)
