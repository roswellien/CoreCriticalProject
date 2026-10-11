"""Retain the unexecuted first controller; seal exact complete-success placement."""
from pathlib import Path
import ast,hashlib,json
P=Path(__file__).resolve().parent
old=P/'run_fixture.py'
before=old.read_text()
anchor="  for q,h in list(pins.items()):need(sha(q)==h,'All current inputs/observations unchanged after workers');passed=True"
replacement="  for q,h in list(pins.items()):need(sha(q)==h,'All current inputs/observations unchanged after workers')\n  passed=True"
assert before.count(anchor)==1
after=before.replace(anchor,replacement)
after=after.replace(" except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise", " except BaseException:\n  passed=False\n  (out/'failure.txt').write_text(traceback.format_exc());raise")
assert after.count('  passed=True')==1
ast.parse(after)
out=P/'run_fixture_v2.py'
assert not out.exists()
out.write_text(after)
print(json.dumps(dict(path=str(out),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),change='Success only after every input and observation rehash; explicit failure false',executed=False)))
