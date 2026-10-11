"""Use the additive normalized CW source model; preserve failed first receipt."""
from pathlib import Path
import hashlib
BASE=Path(__file__).with_name('verify_whole_state.py')
text=BASE.read_text()
old="ROOT/'tools/m4-hypot-native/source_model.py'"
assert text.count(old)==1
text=text.replace(old,"ROOT/'tools/m4-hypot-native/source_model_v2.py'")
old='        pin(__file__);pin(sys.executable)'
assert text.count(old)==1
text=text.replace(old,"        pin(BASE);pin(ROOT/'tools/m4-hypot-native/source_model.py')\n"+old)
exec(compile(text,str(BASE),'exec'),globals())
