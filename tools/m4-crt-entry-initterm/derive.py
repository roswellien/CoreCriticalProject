"""Additive literals and minimal CRT publication seam; frozen gates unchanged."""
import hashlib,json,pathlib,shutil,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).resolve().parent;BASE=ROOT/'reports/m4-crt-entry-initterm';OLD=ROOT/'reports/m4-crt-entry-control/preparation-r5'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main(name):
 out=BASE/name;assert out.parent==BASE and not out.exists();out.mkdir(parents=True)
 for n in ('composition.cpp','main_v2.inc','observations.hpp','seed.hpp','matherr_context.hpp','control_context.hpp'):
  shutil.copyfile(OLD/n,out/(n+'.ancestor'));shutil.copyfile(HERE/n if (HERE/n).exists()else OLD/n,out/n)
 for n in ('initterm_context.hpp','initterm_binding.inc','control_binding.inc'):shutil.copyfile(HERE/n,out/n)
 old=ROOT/'tools/m4-crt/crt_services.cpp';text=old.read_text();a='namespace mw34::m4_crt {';assert text.count(a)==1;text=text.replace(a,a+'\nvoid compiled_initterm(m4_runtime::Runtime&);')
 a='slots.initterm,"_initterm",initterm,8';assert text.count(a)==1;text=text.replace(a,'slots.initterm,"_initterm",compiled_initterm,8');a='r.register_service_continuation(provider,std::move(c));';assert text.count(a)==1;text=text.replace(a,'// First-null gate admits no callback continuation; complete provider source is owned by its literal full page.');(out/'crt_services.cpp').write_text(text);shutil.copyfile(old,out/'crt_services.cpp.ancestor');shutil.copyfile(ROOT/'tools/m4-crt/crt_services.hpp',out/'crt_services.hpp')
 source=ROOT/'reports/m4-crt-entry-initterm/provider-preparation-r3';p=source/'pins.json';pins=json.loads(p.read_text())['files']
 for f,h in pins.items():assert sha(f)==h,f
 files={str(p):sha(p)};files.update(pins)
 for p in[*out.iterdir(),pathlib.Path(__file__),ROOT/'reports/m4-crt-entry-control/build-r6/build.json',ROOT/'reports/m4-crt-entry-control/root-acceptance-r1/report.json']:
  if p.is_file():files[str(p.resolve())]=sha(p)
 report=dict(passed=True,scope='Actual first null-only _initterm additive source composition preparation',State_reseed_after_writer=False,State_reseed_after_control=False,State_reseed_after_initterm=False,old_Session_modified=False,Session_derivative='One callback registration pointer replaced with compiled_initterm plus matching declaration; old callback continuation publication withheld for first-null gate; all other body logic/globals/three preceding services unchanged',old_callback_continuation_admitted=False,provider_preparation=str(source/'report.json'),new_page=0x78001000,borrowed_table_page=0x5e0000,total_pages=16,actual_interval=[0x5e0248,0x5e024c],callback_success_admitted=False,next_stop_source_PC=0x5ac468,next_stop_iat=0x5bb514,native_component_executed=False,whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main(sys.argv[1])
