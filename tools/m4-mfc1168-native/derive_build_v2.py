from pathlib import Path
import hashlib
p=Path(__file__).parent;s=(p/'build_fixture.py').read_text();s=s.replace("pin(__file__);os.environ", "pin(__file__);pin(R/'tools/m4-mfc1168-native/build_fixture.py');pin(R/'tools/m4-mfc1168-native/derive_build_v2.py');pin(R/'tools/m4-mfc1168-native/build_fixture.ps1');os.environ")
(p/'build_fixture_v2.py').write_text(s);print(hashlib.sha256((p/'build_fixture_v2.py').read_bytes()).hexdigest())
