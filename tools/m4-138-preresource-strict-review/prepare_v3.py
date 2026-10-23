"""Correct report-resident root, require pre-import helpers, close physical pin delegation."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-preresource-strict-review/preparation-r3';assert not out.exists();out.mkdir()
 parent=R/'reports/m4-138-preresource-strict-review/preparation-r2/verify_case_v2.py';s=parent.read_text();d=[]
 def change(a,b):
  nonlocal s
  assert s.count(a)==1;s=s.replace(a,b);d.append(dict(before=a,after=b))
 change('ROOT=Path(__file__).resolve().parents[2]','ROOT=Path(__file__).resolve().parents[3]')
 change("V.PINS=pins", "V.PINS=pins;V.pin=pin")
 names=['tools/m4-138-preresource-strict-review/aggregate_v1.py','tools/m4-joint-startup131/mfc_source.py','tools/m4-mfc1168-native/persistent_source.py','tools/m4-mfc1168-native/verify_resource_fixture.py','tools/m4-crt-locale-batch-model-review/interpreter_v2.py','tools/m4-formatting-source/flag_domain.py','tools/m4-tree-review/amd64_pe.py','tools/analysis/pe.py']
 # The literal module's two eager child imports cannot bypass admission.
 inserted="  for q in "+repr(names)+":pin(ROOT/q)\n  pin(Path(__file__));pin(sys.executable)\n"
 change("  DS=load(",inserted+"  DS=load(")
 inverse=s
 for h in reversed(d):assert inverse.count(h['after'])==1;inverse=inverse.replace(h['after'],h['before'])
 assert inverse==parent.read_text();ast.parse(s);q=out/'verify_case_v3.py';q.write_text(s);(out/'exact-deltas.json').write_text(json.dumps(d,indent=2)+'\n')
 files={str(p):sha(p)for p in(parent,q,Path(__file__),out/'exact-deltas.json',*[R/n for n in names])}
 requirements=dict(pre_import_closure='Independent ROOT admission rehashes all ordinary files before helper import; strict external pin fails missing dependencies.',imports=names,ordinary_case_helper='reports/m4-138-preresource-strict-review/preparation-r2/ordinary_case_v2.py',python=str(Path(sys.executable).resolve()),runtime_reports=['current passed single-mode run_v3 execution report and every files entry','current producer independent prelaunch ROOT admission, required exact same producer_admission_sha256','build-r4/build.json and every ordinary files entry','preparation-r3/report.json and its exact parent preparation-r4/report.json','mfc_source.Extension constructor chronological_original/source receipts, retained-actual-inputs/source-derivations/whole genuine BEFORE files','contracts.json pinned f7db9805f43e1eb7ef84ad8adb5ddb0f788b76844dbaadb736329787a410eb64','every ordinary code/image dependency used by Extension.loader'],physical_native_API_modules='For every actual MFC/resources/N before-path/after-path identity, require exact whole System32 module/hash before V import (Kernel32/KernelBase/NTDLL finite whitelist); V.pin now delegates strict admitted lookup.',source_images=['MW3/Mech3.exe','local/mw3-staged/Shared_DLLs/MFC42.DLL','local/mw3-staged/Shared_DLLs/MSVCRT.DLL'],extra_Extension_reads=['tools/m4-mfc1168-native/connected_component_v2.cpp','tools/m4-mfc1168-native/connected_entry.hpp'],no_archive_allowance=True,root_admission_not_created=True)
 (out/'required-input-closure.json').write_text(json.dumps(requirements,indent=2)+'\n');files[str(out/'required-input-closure.json')]=sha(out/'required-input-closure.json')
 (out/'report.json').write_text(json.dumps(dict(passed=True,scope='Unexecuted strict checker root/path and full pre-import code/physical-API pin closure correction; ROOT admission still required',whole_parent_inverse=True,exact_hunks=3,worker_executed=False,actual_strict_checker_executed=False,initializer_credit=0,files=files),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main()
