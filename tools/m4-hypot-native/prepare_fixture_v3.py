"""Require the current unified provider permission encoding before execution."""
from pathlib import Path
import hashlib
PREVIOUS=Path(__file__).with_name('prepare_fixture_v2.py')
PREVIOUS_SHA='271b036944a33e616186ff225a55cf9fa32e18b1d42c85f850d3722ef5d0ec80'
assert hashlib.sha256(PREVIOUS.read_bytes()).hexdigest()==PREVIOUS_SHA
generator=PREVIOUS.read_text()
terminal="exec(compile(text,str(BASE),'exec'),globals())"
assert generator.count(terminal)==1
generator=generator.replace(terminal,r'''
assert text.count("'inputs-r3/report.json'")==3
text=text.replace("'inputs-r3/report.json'","'inputs-r4/report.json'")
old='46e04c33ef7ca4f8ddcf8e59a4ecb1e6189f1f0410ad635fd471538c5458125d'
assert text.count(old)==1
text=text.replace(old,'2e06405a753a7cd1ec4fec34f85ea4af0cce5040c250d39b0c5ee3990bea5c8a')
before="        assert inputs['memory_pages_per_case']==190 and not inputs['numerical_results_seeded']"
assert text.count(before)==1
text=text.replace(before,before+"\n        assert inputs['permission_encoding']=={'0':'read execute','1':'read','2':'read write'}")
before='        pin(__file__);pin(sys.executable)'
assert text.count(before)==1
text=text.replace(before,"        pin(PREVIOUS,PREVIOUS_SHA);pin(ROOT/'tools/m4-hypot-native/normalize_input_permissions.py')\n"+before)
exec(compile(text,str(BASE),'exec'),globals())
''')
exec(compile(generator,str(PREVIOUS),'exec'),globals())
