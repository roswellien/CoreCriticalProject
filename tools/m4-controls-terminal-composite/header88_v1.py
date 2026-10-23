"""UNEXECUTED bounded header reader; no huge files-map/DB/payload read.

Whole88e0 physical authentication is owned by actual closed fullraw2a0086;
this reader only exposes its bounded already-authenticated semantic metadata.
"""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
SEMANTICS='88e0a18bc8b32fb70c3fd460c828c44127613662fd4467cf3385ae78b56861cb'
FULLRAW='2a0086d81039912923fb6f9ed294ea851098ae7e5078fc96faf5f0c246b63035'
def bounded_header(path):
 lines=[];count=0
 with Path(path).open('rb')as f:
  while True:
   line=f.readline(1000001);count+=len(line)
   if not line or count>1000000:raise ValueError('Exact bounded metadata header before files map')
   if line.rstrip(b'\r\n')==b'  "files": {':return json.loads(b''.join(lines)+b'  "files": {}\n}\n'),hashlib.sha256(b''.join(lines)).hexdigest()
   lines.append(line)
def main(admission,admission_sha,name):
 ap=Path(admission).resolve();data=ap.read_bytes();assert hashlib.sha256(data).hexdigest()==admission_sha;A=json.loads(data);assert A['passed']is True and A['bounded88_header_reader_admitted']is True;source=R/'reports/m4-joint-startup138/context-controls-verification-r1/report.json';full=R/'reports/m4-138-controls-review/full-raw-inventory-review-r1/report.json';assert A['files'][str(source)]==SEMANTICS and A['files'][str(full)]==FULLRAW;blob=full.read_bytes();assert len(blob)<32*1024*1024 and hashlib.sha256(blob).hexdigest()==FULLRAW;F=json.loads(blob);assert F['passed']is True and F['raw_export_readers_closed']is True and F['all_bounded_readers_closed']is True and F['controls_verification_sha256']==SEMANTICS and F['proof_inventory']['sqlite_closed_before_hash']is True
 H,prefix_sha=bounded_header(source);assert H['passed']is True and H['execution_sha256']=='43d8a2a8e56e6d6a0286236685b16fc6e36b806ebcc8fc6199d49c95e69e0863';out=R/'reports/m4-controls-terminal-composite'/name;assert not out.exists();out.mkdir();(out/'semantic-header.json').write_text(json.dumps(dict(header=H,semantic_report_sha256=SEMANTICS,actual_closed_fullraw_sha256=FULLRAW,whole_semantic_report_authentication_owned_by_fullraw=True,whole_semantic_report_rehashed_here=False,bounded_prefix_sha256=prefix_sha,files_map_opened=False,raw_or_SQLite_opened=False,accepted_function_credit=0),indent=2)+'\n')
if __name__=='__main__':main(*sys.argv[1:])
