"""Select current corrected final-store execution and additive source model."""
from pathlib import Path
import hashlib
BASE=Path(__file__).with_name('verify_whole_state.py')
text=BASE.read_text()
changes=[
 ("ROOT/'tools/m4-hypot-native/source_model.py'","ROOT/'tools/m4-hypot-native/source_model_v3.py'"),
 ("AREA/'fixture-comparison-r1/report.json'","AREA/(sys.argv[2]+'/report.json')"),
 ("'3aa19148ad564700afcc84b459ad8aa8f9c6b7034063396db09ddf6f1a93d863'","sys.argv[3]"),
 ('        pin(__file__);pin(sys.executable)',"        pin(BASE);pin(ROOT/'tools/m4-hypot-native/source_model.py')\n        pin(__file__);pin(sys.executable)"),
]
for old,new in changes:
    assert text.count(old)==1
    text=text.replace(old,new)
exec(compile(text,str(BASE),'exec'),globals())
