"""Additive repair of generated-model workspace location after failed import."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
parent=R/'reports/m4-formatting-source/persistent-model-r2';assert sha(parent/'report.json')=='41c1146175a22bf0611b9bb51ada4e307983a96cba645c24fc952fbaa476282c'
old=json.loads((parent/'report.json').read_bytes());out=R/'reports/m4-formatting-source/persistent-model-r3';assert not out.exists();out.mkdir()
s=Path(old['model']).read_text();a='R=Path(__file__).resolve().parents[2]';assert s.count(a)==1;s=s.replace(a,'R=Path(__file__).resolve().parents[3]');model=out/'persistent_model.py';model.write_text(s)
report=old|dict(model=str(model),model_sha256=sha(model),files=old['files']|{str(parent/'report.json'):sha(parent/'report.json'),str(model):sha(model),str(Path(__file__).resolve()):sha(__file__)})
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
source=R/'tools/m4-formatting-source/compare_native_fixture.py';s=source.read_text();a="persistent-model-r2/report.json','41c1146175a22bf0611b9bb51ada4e307983a96cba645c24fc952fbaa476282c'";assert s.count(a)==1;s=s.replace(a,"persistent-model-r3/report.json','"+sha(out/'report.json')+"'")
target=R/'tools/m4-formatting-source/compare_native_fixture_v2.py';assert not target.exists();target.write_text(s)
print(json.dumps(dict(model_sha256=sha(out/'report.json'),tool=str(target))))
