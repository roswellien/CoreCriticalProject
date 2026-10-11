"""Derive whole unchanged stage/reader implementations for explicit storage.

Only path-module imports change. No capture limits, hashes, decoding, close
checks, execution semantics, or worker binaries change.
"""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-capture-storage'/name;assert not out.exists();out.mkdir(parents=True)
 specs=[
  ('tools/m4-pipeline/stages.py','tools/m4-pipeline/stages_capture_storage.py',[
   ('import paths\nfrom paths import ROOT, publish_bytes, workspace_path','import paths_capture_storage as paths\nfrom paths_capture_storage import ROOT, publish_bytes, workspace_path')]),
  ('tools/m4-pipeline/capture_bundle.py','tools/m4-pipeline/capture_bundle_storage.py',[
   ('from paths import logical_name, publish_new_file, reject_reparse, workspace_path','from paths_capture_storage import logical_name, publish_new_file, reject_reparse, workspace_path')]),
  ('tools/m4-crt-allocation-root/run_v2.py','tools/m4-crt-allocation-root/run_storage.py',[
   ('from capture_bundle import CaptureBundle, sha_file','from capture_bundle_storage import CaptureBundle, sha_file'),
   ('from paths import publish_bytes, workspace_path','from paths_capture_storage import publish_bytes, workspace_path'),
   ('from stages import run_stage, verify_stage','from stages_capture_storage import run_stage, verify_stage')])]
 rows=[];pins={}
 for src,dst,changes in specs:
  src=R/src;dst=R/dst;assert not dst.exists();text=src.read_text()
  for before,after in changes:assert text.count(before)==1;text=text.replace(before,after)
  compile(text,str(dst),'exec');dst.write_text(text)
  rows.append(dict(parent=str(src),parent_sha256=sha(src),current=str(dst),current_sha256=sha(dst),exact_import_changes=changes))
  pins[str(src)]=sha(src);pins[str(dst)]=sha(dst)
 for p in [R/'tools/m4-pipeline/paths.py',R/'tools/m4-pipeline/paths_capture_storage.py',Path(__file__),Path(sys.executable)]:pins[str(p.resolve())]=sha(p)
 report=dict(passed=True,scope='Whole existing stage and strict CaptureBundle/DirectSet implementations with only import rebinding to one declared fixed local NTFS capture root',storage_root='G:/Projects/MW34Recomp-Captures',worker_binaries_changed=False,existing_outputs_moved=False,archives_opened=False,files=pins,relations=rows)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
