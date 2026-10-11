"""Repair the additive wrapper's nested quote delimiter; no candidate edits."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
q=Path(__file__).with_name('review_joint138_prelaunch_v3.py')
t=q.read_text()
assert t.count("extension=r'''")==1
t=t.replace("extension=r'''",'extension=r"""').replace("'''\nrecipe=recipe.replace",'"""\nrecipe=recipe.replace')
exec(compile(t,str(Path(__file__)),'exec'),globals())
