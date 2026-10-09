"""Preserve prefix r1; remove its unused first-service slot constant only."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OLD=ROOT/'reports/m4-crt-entry/prefix-preparation-r1'
OUT=ROOT/'reports/m4-crt-entry/prefix-preparation-r2'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not OUT.exists();OUT.mkdir(parents=True)
source=OLD/'prefix.cpp';assert sha(source)=='2df20ad8432bd7b442599e97b1793d2727e3b40664194d0c6e506d83f5af6412'
(OUT/'prefix.cpp.ancestor').write_bytes(source.read_bytes())
text=source.read_text();assert text.count(',slot=0x5bb5a4;')==1
new=OUT/'prefix.cpp';new.write_text(text.replace(',slot=0x5bb5a4;',';'))
builder=ROOT/'tools/m4-crt-entry/build-prefix.ps1';(OUT/'build-prefix.ps1.ancestor').write_bytes(builder.read_bytes())
text=builder.read_text().replace("prefix-build-r1'","prefix-build-r2'").replace('prefix-preparation-r1/prefix.cpp','prefix-preparation-r2/prefix.cpp').replace(sha(source),sha(new))
new_builder=ROOT/'tools/m4-crt-entry/build-prefix-v2.ps1';assert not new_builder.exists();new_builder.write_text(text)
files={str(p):sha(p) for p in (source,new,builder,new_builder,OUT/'prefix.cpp.ancestor',OUT/'build-prefix.ps1.ancestor',OLD/'report.json',ROOT/'reports/m4-crt-entry/prefix-build-r1/build.json',ROOT/'reports/m4-crt-entry/prefix-build-r1/build-O0.log',Path(__file__))}
(OUT/'report.json').write_text(json.dumps(dict(passed=True,scope='Additive unused-variable compilation repair; no source execution or runtime semantic change',files=files,production_change='Remove unused first-service slot constant; routes still literal in checked call table',whole_M4_complete=False),indent=2)+'\n')
print(json.dumps(dict(passed=True,source_sha256=sha(new),report_sha256=sha(OUT/'report.json'))))
