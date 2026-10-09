import hashlib,json,pathlib,sys
root=pathlib.Path(__file__).resolve().parents[2];run=root/'reports/m4-crt-control/original-run-r1/report.json';m=json.loads(run.read_text());p=root/'reports/m4-crt-control/research-r1/replay_spec.hpp';assert not p.exists() and m['passed'] and m['records']==3264
with open(m['raw']['path'],'rb')as f:h=hashlib.file_digest(f,'sha256').hexdigest()
assert h==m['raw']['sha256'];p.write_text('#pragma once\nnamespace mw34::m4_crt_control { inline constexpr char original_sha[]="'+h+'"; }\n');print(p)
