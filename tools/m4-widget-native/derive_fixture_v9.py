"""Reflect the actual52 literal entries in the final structural status only."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;a=P/'fixture_v4.cpp';s=a.read_text();old='status{1,1,6,51,0,0,0,0}';new='status{1,1,6,52,0,0,0,0}'
assert s.count(old)==1
q=P/'fixture_v5.cpp';assert not q.exists();q.write_text(s.replace(old,new));print(json.dumps(dict(source=str(a),source_sha256=hashlib.sha256(a.read_bytes()).hexdigest(),output=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),only_change=[old,new],worker_executed=False)))
