"""Audit successful files separately from failed Python bytecode probes."""
from pathlib import Path
import hashlib,json
p=Path(__file__).with_name('old4_source_v2.py');s=p.read_text()
old="for path in sorted(AUDITED_READS):pin(path)\n  dependency_paths=sorted(AUDITED_READS)"
new="""existing={path for path in AUDITED_READS if Path(path).is_file()}
  missing=sorted(AUDITED_READS-existing);need(all('__pycache__'in path and path.endswith('.pyc')for path in missing),'Only failed optional Python bytecode reads are excluded')
  for path in sorted(existing):pin(path)
  dependency_paths=sorted(existing)"""
assert s.count(old)==1;s=s.replace(old,new)
old="pin(ROOT/'tools/m4-tree-original/derive_old4_source_v2.py')"
new="pin(ROOT/'tools/m4-tree-original/derive_old4_source_v2.py');pin(ROOT/'tools/m4-tree-original/old4_source_v2.py');pin(ROOT/'tools/m4-tree-original/derive_old4_source_v3.py')"
assert s.count(old)==1;s=s.replace(old,new)
old="audited_input_paths=len(AUDITED_READS)"
new="audited_input_paths=len(dependency_paths)if'dependency_paths'in locals()else0,failed_optional_bytecode_read_attempts=missing if'missing'in locals()else[]"
new=new.replace('else0','else 0').replace('else[]','else []')
assert s.count(old)==1;s=s.replace(old,new)
out=p.with_name('old4_source_v3.py');assert not out.exists();out.write_text(s);print(json.dumps(dict(sha256=hashlib.sha256(out.read_bytes()).hexdigest())))
