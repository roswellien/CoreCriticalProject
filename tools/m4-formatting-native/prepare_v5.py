"""Anchor additive conservation adapter at the actual final execution line."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('prepare_v4.py');s=p.read_text();s=s.replace('anchor="exec(compile(s,str(p),\'exec\'),globals())"','anchor="\\nexec(compile(s,str(p),\'exec\'),globals())"');s=s.replace("pin(R/\\'tools/m4-formatting-native/prepare_v3.py\\')","pin(R/\\'tools/m4-formatting-native/prepare_v3.py\\');pin(R/\\'tools/m4-formatting-native/prepare_v4.py\\')")
exec(compile(s,str(p),'exec'),globals())
