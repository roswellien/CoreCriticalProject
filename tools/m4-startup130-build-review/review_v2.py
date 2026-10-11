"""Require the compound object's exact defined entry symbols separately."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
parent = Path(__file__).with_name('review.py')
text = parent.read_text()
before = "symbols=run.stdout.decode();assert symbols.count('_body')==1,(obj,symbols);new_symbols.append(dict(level=level,object=obj,defined_external_symbols=symbols.splitlines()))"
after = """symbols=run.stdout.decode()
   if str(Path(obj).resolve()).casefold()==str(Path(cosine['objects'][level]['path']).resolve()).casefold():
    defined={line.split()[-1]for line in symbols.splitlines()if line.split()[1]=='T'}
    assert defined=={'mw34_fp_entry_4b64f0','sub_4b64f0','mw34_compound___remill_flag_computation_sign','mw34_compound___remill_flag_computation_zero','mw34_compound___remill_undefined_8'},(obj,defined)
   else:assert symbols.count('_body')==1,(obj,symbols)
   new_symbols.append(dict(level=level,object=obj,defined_external_symbols=symbols.splitlines()))"""
assert text.count(before) == 1
text = text.replace(before, after)
before = "pin(__file__);pin(ROOT/'tools/m4-joint-startup130/derive_build_reviews.py')"
assert text.count(before) == 1
text = text.replace(before, "pin(__file__);pin(ROOT/'tools/m4-startup130-build-review/review.py');pin(ROOT/'tools/m4-joint-startup130/derive_build_reviews.py')")
exec(compile(text, str(parent), 'exec'), globals())
