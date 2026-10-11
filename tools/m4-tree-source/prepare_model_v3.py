"""Derive normal FS scope from its dominating literal source store."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];source=ROOT/'tools/m4-tree-source/game_model_v2.py';raw=source.read_text()
old="raw=self.bytes(frame['record'],12);I.need(struct.unpack('<3I',raw)==(frame['previous_head'],spec['handler'],0xffffffff),'Whole FS record predecessor/handler/scope preserved')"
new="raw=self.bytes(frame['record'],12);scope_stores=[(index,row)for index,row in enumerate(self.accesses)if row[4]and row[1]==frame['record']+8 and row[3]==4];I.need(scope_stores,'FS scope has a literal dominating source store');scope_index,scope_store=scope_stores[-1];I.need(struct.unpack('<3I',raw)==(frame['previous_head'],spec['handler'],scope_store[2]),'Whole FS record predecessor/handler/source-derived scope preserved');frame['restore_scope_source_store']=dict(index=scope_index,pc=scope_store[0],address=scope_store[1],value=scope_store[2],bytes=4)"
assert raw.count(old)==1
target=ROOT/'tools/m4-tree-source/game_model_v3.py';assert not target.exists();target.write_text(raw.replace(old,new))
out=ROOT/'reports/m4-tree-source/model-preparation-r3';assert not out.exists();out.mkdir(parents=True)
files={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest()for p in(source,target,Path(__file__))}
report=dict(passed=True,scope='Source-derived FS scope: outer map scope0 from4B7DC5, returned helper scopes from their literal stores; no observed scope seed',old=old,new=new,files=files)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest())))
