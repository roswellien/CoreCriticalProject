"""Actual hook selects source site; sealed validator separately binds target CPU."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
p = HERE / 'controls_review.py'
s = p.read_text(encoding='utf-8')
old = """        need('api[2]!=0x7810a30b' in hooks and 'api[3]!=0x78146198' in hooks and
             'api[4]!=pc' in hooks and 'trigger_api=api' in hooks,
             'Mutation triggers actual target CPU and separately retained genuine source API site')"""
new = """        need('auto actual=snapshot(s);if(actual.api[2]!=0x7810a30b)return;' in hooks and
             'trigger_PC=pc;trigger=std::move(actual)' in hooks,
             'Actual hook selects first source API by its retained witness and records actual target CPU')
        validator2=pin(ROOT/'tools/m4-lockit-review/check_controls_v2.py').read_text(encoding='utf-8')
        need('identity[1]==api[4]' in validator2 and 'api[2:4]==(0x7810a30b,0x78146198)' in validator2,
             'Actual sealed validator separately checks target CPU and exact source site/IAT cell')"""
assert s.count(old) == 1
s = s.replace(old, new)
old = '        pin(__file__)'
new = "        pin(__file__); pin(ROOT/'tools/m4-lockit-review/controls_review.py')"
assert s.count(old) == 1
s = s.replace(old, new)
exec(compile(s, str(p), 'exec'), globals())
