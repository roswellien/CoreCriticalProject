"""Literal additive mainargs composition, preserving accepted preceding sources."""
import hashlib,json,pathlib,shutil,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).resolve().parent;BASE=ROOT/'reports/m4-crt-mainargs';OLD=ROOT/'reports/m4-crt-entry-initterm/preparation-r3'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main(name):
 out=BASE/name;assert name.startswith('preparation-') and out.parent==BASE and not out.exists();out.mkdir(parents=True)
 for n in ('composition.cpp','main_v2.inc','observations.hpp','seed.hpp','matherr_context.hpp','control_context.hpp','initterm_context.hpp','initterm_binding.inc','control_binding.inc','crt_services.cpp','crt_services.hpp'):
  shutil.copyfile(OLD/n,out/(n+'.ancestor'));shutil.copyfile(HERE/n if (HERE/n).exists() else OLD/n,out/n)
 for n in ('mainargs_context.hpp','mainargs_binding.inc'):shutil.copyfile(HERE/n,out/n)
 source=BASE/'recovery-r3';pins=json.loads((source/'pins.json').read_text())['files']
 for p,h in pins.items():assert sha(p)==h,p
 files={str(source/'pins.json'):sha(source/'pins.json')};files.update(pins)
 for p in[*out.iterdir(),pathlib.Path(__file__),ROOT/'reports/m4-crt-entry-initterm/build-r3/build.json',ROOT/'reports/m4-crt-entry-initterm/author-submission-r1/report.json']:
  if p.is_file():files[str(p.resolve())]=sha(p)
 report=dict(passed=True,scope='Additive real compiled __getmainargs plus ordinary builder to first named OS import',State_reseed_after_writer=False,State_reseed_after_control=False,State_reseed_after_initterm=False,State_reseed_inside_mainargs=False,old_Runtime_modified=False,Session_derivative_changed=False,new_pages=[],borrowed_pages=16,source_identity_bytes=1140,provider_preparation=str(source/'report.json'),direct_provider_route='Strict typed internal source E8 frame; no generic Runtime provider translation',provider_import_route='Own typed unique literal provider PE import authority; public unresolved_import Fault, no generic Runtime provider IAT registration',next_stop_source_PC=0x7800bbd0,next_stop_iat=0x7802e018,argc_argv_environment_outputs_admitted=False,native_component_executed=False,whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,bindings=len(files),report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
