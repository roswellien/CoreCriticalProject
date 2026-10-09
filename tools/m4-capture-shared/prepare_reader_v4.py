"""Bound manifest read to held opened extent; avoid a MAX_INDEX allocation."""
from pathlib import Path
import hashlib,json,difflib
R=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
def main():
 p=H/'capture_shared_v3.py';old=p.read_text()
 needle="            self._manifest_stream=_locked_stream(self.path);raw=self._manifest_stream.read(MAX_INDEX+1)\n            _need(len(raw)<=MAX_INDEX and hashlib.sha256(raw).hexdigest()==expected_sha256,'External shared manifest SHA256 mismatch')"
 replacement="""            self._manifest_stream=_locked_stream(self.path)
            opened=os.fstat(self._manifest_stream.fileno())
            _need(stat.S_ISREG(opened.st_mode) and 1<=opened.st_size<=MAX_INDEX,'Invalid opened shared manifest type/size')
            raw=self._manifest_stream.read(opened.st_size+1)
            _need(len(raw)==opened.st_size and hashlib.sha256(raw).hexdigest()==expected_sha256,'External shared manifest SHA256 mismatch')"""
 assert old.count(needle)==1;new=old.replace(needle,replacement)
 target=H/'capture_shared_v4.py';assert not target.exists();target.write_text(new,encoding='utf-8',newline='\n')
 out=R/'reports/m4-capture-shared/reader-repair-r3';out.mkdir(parents=True,exist_ok=False)
 (out/'reader.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(p),tofile=str(target))))
 (out/'report.json').write_text(json.dumps({'passed':True,'old_reader_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'new_reader_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'difference':'Read exact bounded held-file manifest extent+one EOF byte, instead of allocating64MiB for every tiny manifest. Opened fstat regular-file/extent is independently admitted. Held ownership/hash/schema/canonical index unchanged.','basis':'Actual benchmark-r2 reader PeakWorkingSetSize exposed the temporary allocation.','native_executed':False,'format_adopted':False},indent=2)+'\n')
 # Observation-only validation/measurement derivatives; native writer/captures unchanged.
 for source,target_name in [('validate_pilot_v2.py','validate_pilot_v3.py'),('read_probe.py','read_probe_v2.py')]:
  text=(H/source).read_text().replace('from capture_shared_v3 import','from capture_shared_v4 import')
  if source.startswith('validate'):
   text=text.replace("'validate_pilot_v2.py','prepare_validation_v2.py'","'validate_pilot_v2.py','prepare_validation_v2.py','capture_shared_v4.py','prepare_reader_v4.py','validate_pilot_v3.py'")
   text=text.replace('    return build',"    pin(files,ROOT/'reports/m4-capture-shared/reader-repair-r3/report.json');pin(files,ROOT/'reports/m4-capture-shared/reader-repair-r3/reader.diff')\n    return build",1)
  target=H/target_name;assert not target.exists();target.write_text(text,encoding='utf-8',newline='\n')
if __name__=='__main__':main()
