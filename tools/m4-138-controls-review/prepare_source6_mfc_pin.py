"""Add exact current paired-reader dependency binding; no invocation."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=R/'tools/m4-138-controls-review/review_source6_mfc.py';original=p.read_text();text=original;changes=[]
def one(a,b):
 global text
 assert text.count(a)==1;text=text.replace(a,b);changes.append(dict(before=a,after=b))
one("        assert source['passed']and source['reader_closed']and not source['candidate_AFTER_machine_seed']", "        assert source['passed']and source['reader_closed']and not source['candidate_AFTER_machine_seed']\n        paired_reader=R/'reports/m4-joint-startup138-source/preparation-r11/paired_exports.py'\n        pin(paired_reader,source['files'][str(paired_reader.resolve())])")
one("pin(__file__);pin(R/'tools/m4-joint-startup131/paired_exports.py')", "pin(__file__);pin(paired_reader,source['files'][str(paired_reader.resolve())])")
inverse=text
for c in reversed(changes):assert inverse.count(c['after'])==1;inverse=inverse.replace(c['after'],c['before'])
assert inverse==original;ast.parse(text)
q=R/'tools/m4-138-controls-review/review_source6_mfc_v2.py';assert not q.exists();q.write_text(text)
out=R/'reports/m4-138-controls-review/source6-mfc-reader-pin-preparation-r1';assert not out.exists();out.mkdir(parents=True)
paths=(p,q,Path(__file__),R/'reports/m4-138-controls-review/source6-review-preparation-r1/report.json',R/'reports/m4-joint-startup138-source/preparation-r11/paired_exports.py')
r=dict(passed=True,scope='Unexecuted source6 MFC review precise current paired Facade code pin; all inherited full byteflow/resource/type/closure gates retained',changes=changes,inverse_restores_parent=True,files={str(p.resolve()):sha(p)for p in paths},capture_archives_opened=0,reviewer_executed=False,initializer_credit=0)
f=out/'report.json';f.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(f),reviewer_sha256=sha(q))))
