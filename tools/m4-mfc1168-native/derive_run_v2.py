from pathlib import Path
import hashlib
p=Path(__file__).parent;s=(p/'run_fixture.py').read_text()
s=s.replace("b=json.loads(pin(build,digest).read_bytes());assert b['passed'];prep=", "review_path=R/'reports/m4-tree-review/mfc1168-native-prelaunch-r4/report.json';review=json.loads(pin(review_path,'f440e891805bca226f5106d0b33cfef884ad6abcbcc93c753cf06f3347d4289f').read_bytes());assert review['passed']and review['build_sha256']==digest\n  b=json.loads(pin(build,digest).read_bytes());assert b['passed']and review['preparation_sha256']==b['preparation_sha256'];prep=")
s=s.replace("pin(__file__);pin(sys.executable);image=", "pin(__file__);pin(R/'tools/m4-mfc1168-native/run_fixture.py');pin(R/'tools/m4-mfc1168-native/derive_run_v2.py');pin(sys.executable);image=")
s=s.replace("runs=runs,files=pins,native_executed=passed", "runs=runs,files=pins,admission_review=str(review_path),admission_review_sha256='f440e891805bca226f5106d0b33cfef884ad6abcbcc93c753cf06f3347d4289f',native_executed=passed")
(p/'run_fixture_v2.py').write_text(s);print(hashlib.sha256((p/'run_fixture_v2.py').read_bytes()).hexdigest())
