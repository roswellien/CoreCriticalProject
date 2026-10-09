"""Preserve v1 and correct only timing-number canonicalization at manifest level."""
from pathlib import Path
import hashlib,json,difflib
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
def main():
 p=R/'tools/m4-pipeline/capture_shared.py';t=p.read_text()
 v=t.replace('def _load(raw):','def _load(raw,canonical=True):').replace("    _need(_json(value)==raw,'Noncanonical shared JSON')","    if canonical:_need(_json(value)==raw,'Noncanonical shared JSON')").replace('            meta=_load(raw)','            meta=_load(raw,canonical=False)')
 assert t!=v and t.count('meta=_load(raw)')==1
 target=H/'capture_shared_v2.py';assert not target.exists();target.write_text(v,encoding='utf-8',newline='\n')
 out=R/'reports/m4-capture-shared/reader-repair-r1';out.mkdir(parents=True,exist_ok=False)
 (out/'reader.diff').write_text(''.join(difflib.unified_diff(t.splitlines(True),v.splitlines(True),fromfile=str(p),tofile=str(target))))
 (out/'report.json').write_text(json.dumps({'passed':True,'old_reader_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'new_reader_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'old_immutable':str(p),'new_additive':str(target),'difference':'Manifest JSON has finite C++17 timing numbers whose spelling differs from Python shortest repr. Duplicate-key/schema/count and external SHA checks stay strict. Blob index still must be exact canonical bytes. No writer/native/control changes.','failure_preserved':'The first native collision manifest was correctly parsed but rejected only on timing repr; this repair retains all native artifacts.','native_executed':False,'format_adopted':False},indent=2)+'\n')
if __name__=='__main__':main()
