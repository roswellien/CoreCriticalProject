"""Bounded additive review: current source and loaded inputs, inherited captures stay delegated."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
parent=(HERE/'native_integration_review.py').read_text(encoding='utf-8')
old="    for p,h in n['files'].items():pin(p,h)"
new="    for p,h in n['files'].items():\n        if Path(p).resolve().parent==np.resolve():pin(p,h)\n    pin(HERE/'native_integration_review.py')"
assert parent.count(old)==1
exec(compile(parent.replace(old,new),str(HERE/'native_integration_review.py'),'exec'),globals())
