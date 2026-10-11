"""Additive UTF-8 text output correction; physical source domains unchanged."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
old=R/'tools/m4-mfc1168-original/recover.py';new=old.with_name('recover_v2.py')
need=lambda v,m:None if v else (_ for _ in()).throw(ValueError(m))
need(not new.exists(),'Fresh derivative')
body=old.read_text(encoding='utf-8');a="p=out/'next-probe.md';p.write_text(plan);pin(p)";b="p=out/'next-probe.md';p.write_text(plan,encoding='utf-8');pin(p)";need(body.count(a)==1,'Exact text correction');new.write_text(body.replace(a,b),encoding='utf-8')
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
failed=R/'reports/m4-mfc1168-original/recovery-r1';need(not(failed/'report.json').exists(),'Freeze failed attempt')
(failed/'report.json').write_text(json.dumps(dict(passed=False,reason='The completed static recovery reached prose output, whose Unicode minus sign was rejected by Windows cp1252. No guest or archive execution.',failure_type='UnicodeEncodeError',physical_source_changed=False,files={str(p.resolve()):sha(p)for p in [old,*failed.iterdir()]if p.is_file()},capture_reader_opened=False,original_executed=False,native_executed=False,initializer_credit=0),indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(source_sha256=sha(old),derivative_sha256=sha(new),failed_report_sha256=sha(failed/'report.json'))))
