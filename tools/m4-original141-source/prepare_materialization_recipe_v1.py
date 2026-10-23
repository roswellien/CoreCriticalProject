"""Prepare explicit ordinary-only ROOT input materialization closure, no readers."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-original141-source/input-materialization-preparation-r1';assert not out.exists();out.mkdir()
 vpath=R/'reports/m4-original141/root-capture-validation-r3/report.json';assert sha(vpath)=='e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c'
 v=json.loads(vpath.read_bytes());assert v['passed']and v['reader_closed'];files={}
 paths=[vpath,R/'tools/m4-original141-source/materialize_current_inputs_v1.py',R/'tools/m4-startup138-original/export_reader_r2.py',R/'tools/analysis/pe.py',R/'reports/m4-original141-source/root-input-metadata-r1/report.json',vpath.parent/'current-named-CRT-inputs.json',R/'reports/m4-original141/transition-preparation-r3/patch-declarations.json',R/'reports/m4-original141/root-compiled-review-r2/report.json',R/'reports/m4-original141/root-compiled-review-r2/physical-links.json',R/'local/mw3-staged/Shared_DLLs/MFC42.DLL',R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',R/'MW3/Mech3.exe',Path(__file__).resolve()]
 for p in paths:assert p.is_file();files[str(p.resolve())]=sha(p)
 exports=v['paired_exports'];assert len(exports)==1 and exports[0]['branch']=='original';e=exports[0]
 assert e['index_sha256']=='ed0cc1d43b26c067f0af85dd153f5ce5fd38ae07f789d893bcbad812b97c13ae'and e['payload_sha256']=='8a23f0a6be87e38ff50f9591f57988fa5e87850e4429655a2357aa98f599331b'
 required=dict(files);required[e['index_path']]=e['index_sha256'];required[e['payload_path']]=e['payload_sha256']
 q=out/'required-ordinary-files.json';q.write_text(json.dumps(required,indent=2)+'\n');files[str(q)]=sha(q)
 recipe='ROOT must independently inspect materializer and all physical helper/PE dependencies, then physically rehash every required-ordinary-files.json entry before minting a fresh admission. The two sealed exports are declared here from strict3; preparation did NOT open or hash them. Admission: passed:true, independent_review:true, scope_identity:original141_current_input_materialization, files: exact required map. Invoke Python -B tools/m4-original141-source/materialize_current_inputs_v1.py ROOT_ADMISSION ROOT_SHA FRESH_OUTPUT. This stage opens one ordinary ExportReader only, never transport/archive/native worker; final source controller still requires separate whole model/data admission and tree6 gate. Preserve failures.\n'
 (out/'ROOT-recipe.txt').write_text(recipe);files[str(out/'ROOT-recipe.txt')]=sha(out/'ROOT-recipe.txt')
 q=out/'report.json';q.write_text(json.dumps(dict(prepared_only=True,canonical_reader_opened=False,ordinary_export_opened=False,source_execution=False,imports_executed=False,initializer_credit=0,original_validation_sha256=sha(vpath),ordinary_code_inputs_physically_hashed=len(paths),sealed_export_whole_hashes_deferred_to_ROOT_admission=True,required_closure=str(out/'required-ordinary-files.json'),files=files),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q))))
if __name__=='__main__':main()
