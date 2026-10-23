"""ROOT bounded existing capture admission; extraction only, no worker or model."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-startup141-paired/root-owner-export-admission-r3';assert not out.exists();files={}
 def pin(p,h=None):
  p=Path(p).resolve()
  assert p.is_relative_to(R) or p.is_relative_to(Path(sys.prefix).resolve()) or p.is_relative_to(Path('C:/Program Files/Microsoft Visual Studio/18/Community')) or p.is_relative_to(Path('C:/Program Files (x86)/Windows Kits/10')) or p.is_relative_to(Path('G:/Projects/MW34Recomp-Captures/reports/m4-startup141-root/execution-r2'))
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or h==v,(str(p),h,v);assert files.setdefault(str(p),v)==v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 base=read(R/'reports/m4-startup141-paired/root-native36-admission-r1/report.json','8f34c2bea39b3d231469339393e1ff386dec7bd3d7cefd1ff14e3407bc321bdd')
 assert base['passed']and base['independent_review']and not base['reader_opened']
 for p,h in base['files'].items():pin(p,h)
 source=read(R/'reports/m4-startup141-source/combined-source-provider-r6/report.json','8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3')
 execution=read(R/'reports/m4-startup141-root/execution-r2/report.json','536eeb8c62c9de8276e46d727907faea417b91a22c2cbae2b3cdbca80da7c2b6')
 assert source['passed']and source['reader_closed']and source['paired_export_readers_closed']and execution['passed']and execution['all_workers_terminal']
 physical={str(Path(p).resolve()):h for p,h in source['files'].items()};captures=[]
 for level in ('O0','O2'):
  row=next(v for v in source['paired_exports']if v['branch']==level);capture=Path(execution['runs'][level]['capture']).resolve()
  assert capture==Path(row['transport_path']).resolve() and physical[str(capture)]==row['transport_sha256']
  transport=read(capture,row['transport_sha256']);assert transport['passed']and transport['transport_only']and transport['native_executed']is False and transport['format']=='mw34.capture.direct.v1'
  names={'transport.json'}
  for part in transport['parts']:
   assert Path(part['bundle']).name==part['bundle']and part['bundle'].endswith('.mwb')and part['bundle']not in names
   names.add(part['bundle']);p=capture.parent/part['bundle'];assert physical[str(p)]==part['sha256'];pin(p,part['sha256'])
  assert {p.name for p in capture.parent.iterdir()}==names
  captures.append(dict(level=level,capture=str(capture),sha256=row['transport_sha256'],parts=len(transport['parts'])))
 pin(Path(sys.prefix)/'Lib/encodings/utf_8_sig.py','21a95bb95448f2f064f08aa2c89e843b87a20a5a13c45c6c47c288f2be5219a4')
 for rel in ('tools/m4-crt-allocation-root/run_storage.py','tools/m4-pipeline/capture_bundle_storage.py','tools/m4-pipeline/stages_capture_storage.py','tools/m4-pipeline/paths_capture_storage.py'):
  pin(R/rel,physical[str((R/rel).resolve())])
 specs=[('tools/m4-crt-allocation-root/run_v2.py','tools/m4-crt-allocation-root/run_storage.py',[('from capture_bundle import CaptureBundle, sha_file','from capture_bundle_storage import CaptureBundle, sha_file'),('from paths import publish_bytes, workspace_path','from paths_capture_storage import publish_bytes, workspace_path'),('from stages import run_stage, verify_stage','from stages_capture_storage import run_stage, verify_stage')]),('tools/m4-pipeline/capture_bundle.py','tools/m4-pipeline/capture_bundle_storage.py',[('from paths import logical_name, publish_new_file, reject_reparse, workspace_path','from paths_capture_storage import logical_name, publish_new_file, reject_reparse, workspace_path')]),('tools/m4-pipeline/stages.py','tools/m4-pipeline/stages_capture_storage.py',[('import paths\nfrom paths import ROOT, publish_bytes, workspace_path','import paths_capture_storage as paths\nfrom paths_capture_storage import ROOT, publish_bytes, workspace_path')])]
 for parent,child,changes in specs:
  original=pin(R/parent).read_text();inverse=pin(R/child).read_text()
  for before,after in reversed(changes):assert inverse.count(after)==1;inverse=inverse.replace(after,before)
  assert inverse==original
 parent=pin(R/'tools/m4-startup141-paired/export_native_owner_cuts_v1.py').read_text();child=pin(R/'tools/m4-startup141-paired/export_native_owner_cuts_v2.py').read_text();assert child.count('tools/m4-crt-allocation-root/run_storage.py')==1 and child.replace('tools/m4-crt-allocation-root/run_storage.py','tools/m4-crt-allocation-root/run_v2.py')==parent
 script=pin(R/'tools/m4-startup141-paired/export_native_owner_cuts_v1.py');ast.parse(script.read_text())
 pin(R/'reports/m4-startup141-source/preparation-r6/paired_exports.py','9bab30621ceb058b99bdf1df39da384919b537dd4c8c0623f91b029bc4528988')
 pin(__file__);pin(sys.executable)
 out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,independent_review=True,scope_identity='native141_constructor_owner_cut_export',existing_current_captures=captures,canonical_reader_opened=False,source_execution=False,native_worker_launched=False,initializer_credit=0,accepted_function_credit=0,files=files),indent=2)+'\n')
 with q.open('rb')as f:print(json.dumps(dict(path=str(q),sha256=hashlib.file_digest(f,'sha256').hexdigest(),files=len(files))))
if __name__=='__main__':main()
