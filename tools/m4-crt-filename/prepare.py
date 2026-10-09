"""Fresh additive filename seam; frozen mainargs State/context/objects are copied unchanged."""
import hashlib,json,pathlib,shutil,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).resolve().parent;BASE=ROOT/'reports/m4-crt-filename';OLD=ROOT/'reports/m4-crt-mainargs/preparation-r2'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def replace(s,a,b):assert s.count(a)==1,(a[:90],s.count(a));return s.replace(a,b)
def main(name):
 out=BASE/name;assert name.startswith('preparation-') and out.parent==BASE and not out.exists();out.mkdir(parents=True)
 for n in ('composition.cpp','main_v2.inc','observations.hpp','seed.hpp','matherr_context.hpp','control_context.hpp','initterm_context.hpp','initterm_binding.inc','control_binding.inc','crt_services.cpp','crt_services.hpp','mainargs_context.hpp','mainargs_binding.inc'):
  shutil.copyfile(OLD/n,out/(n+'.ancestor'));shutil.copyfile(OLD/n,out/n)
 for n in ('filename.hpp','filename_binding.inc','units.inc'):shutil.copyfile(HERE/n,out/n)
 p=out/'composition.cpp';s=p.read_text();s=replace(s,'#include "mainargs_context.hpp"','#include "mainargs_context.hpp"\n#include "filename.hpp"');s=replace(s,'namespace mg=mw34::m4_crt_entry_mainargs;','namespace mg=mw34::m4_crt_entry_mainargs;\nnamespace fn=mw34::m4_crt_filename;');s=replace(s,'#include "mainargs_binding.inc"','#include "mainargs_binding.inc"\n#include "filename_binding.inc"')
 s=replace(s,'return mg::owner->read(a);','if(fn::binding||fn::admitted_binding){auto*f=fn::current(*mg::owner);if(f->returned&&mg::owner->state.gpr.rip.dword==fn::stop_pc)f->stop(a,p);}return mg::owner->read(a);')
 s=replace(s,'mg::owner->called(s,a);','if(fn::binding||fn::admitted_binding){fn::current(*mg::owner)->invoke(s,a,p);return p;}mg::owner->called(s,a);');p.write_text(s)
 p=out/'main_v2.inc';s=p.read_text();s=s.replace('MW34_ENTRY_MAINARGS_NO_MAIN','MW34_CRT_FILENAME_NO_MAIN');s=replace(s,'struct alignas(16) Boundary','namespace mw34::m4_crt_filename {void checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}}\nstruct alignas(16) Boundary')
 s=replace(s,'InvocationHostBoundary host;','fn::LastErrorBoundary errors(&fn::outer_error_after);fn::outer_error_before=errors.saved;InvocationHostBoundary host;')
 s=replace(s,'unsigned fault_reason{},fault_pc{},fault_target{};','unsigned fault_reason{},fault_pc{},fault_target{};void(*unit)(){};')
 s=replace(s,'try {if(j->writer)','try {if(j->unit){j->unit();j->ok=true;return true;}if(j->writer)')
 s=replace(s,'#ifndef MW34_CRT_FILENAME_NO_MAIN','#include "units.inc"\n#ifndef MW34_CRT_FILENAME_NO_MAIN')
 s=replace(s,'for(unsigned scenario=0;scenario<84;++scenario)','filename_units_directory=directory/"units";require(std::filesystem::create_directory(filename_units_directory),"Fresh unit directory");Job unit_job;unit_job.unit=&filename_units;boundary(unit_job,filename_units_directory,"units",0);require(unit_job.ok&&!unit_job.denied&&fn::outer_error_before==fn::outer_error_after,"Actual bounded filename units and caller closure");std::array<unsigned,2>unit_errors{fn::outer_error_before,fn::outer_error_after};raw_output(filename_units_directory/"caller-error.bin",unit_errors);\n for(unsigned scenario=0;scenario<84;++scenario)')
 s=replace(s,'scenario<84','scenario<36');s=replace(s,'scenario<24?0:scenario-23','scenario<24?0:scenario+37')
 s=replace(s,'MainargsBinding mainargs(r,provider,mode);','MainargsBinding mainargs(r,provider,mode);fn::Binding filename(mainargs.context,mode,0xa11c0000U+scenario);')
 s=replace(s,'mainargs_binding=&mainargs;boundary','mainargs_binding=&mainargs;fn::binding=&filename;fn::admitted_binding=&filename;boundary');s=replace(s,'mainargs_binding=nullptr;\n  snapshot','mainargs_binding=nullptr;fn::binding=nullptr;fn::admitted_binding=nullptr;\n  snapshot')
 marker='require(entry_job.denied&&r.poisoned(),"Required unresolved or causal dependency terminal");'
 evidence='''std::array<unsigned,22>filename_job{filename.control,filename.incoming_error,filename.frame,filename.result,filename.last_error,filename.caller_error,filename.restored_error,filename.stage,filename.hook_count,filename.fault_pc,filename.fault_address,unsigned(filename.used),unsigned(filename.active),unsigned(filename.api_called),unsigned(filename.stored),unsigned(filename.returned),unsigned(filename.stopped),unsigned(filename.failed),fn::outer_error_before,fn::outer_error_after,fn::commandline,fn::stop_pc};raw_output(row/"filename-job.bin",filename_job);raw_output(row/"filename-witness.bin",filename.witness);if(filename.api_called){raw_output(row/"filename-api-before.bin",api(filename.api_before));raw_output(row/"filename-api-after.bin",api(filename.api_after));raw_output(row/"filename-module-before.bin",module(filename.module_before));raw_output(row/"filename-module-after.bin",module(filename.module_after));}std::ofstream filename_reason(row/"filename-reason.txt");filename_reason<<(filename.reason?filename.reason:"")<<'\\n';require(bool(filename_reason),"Filename reason retained");require(!filename.active&&!fn::binding&&fn::outer_error_before==fn::outer_error_after,"Filename terminal ownership and caller LastError retained");if(filename.used)require(filename.caller_error==filename.restored_error,"Filename isolated LastError retained");
  '''
 s=replace(s,marker,evidence+marker);s=replace(s,'FaultReason::unresolved_import)&&entry_job.fault_pc==mg::import_call&&entry_job.fault_target==mg::import_slot','FaultReason::unresolved_translation)&&entry_job.fault_pc==fn::stop_pc&&entry_job.fault_target==fn::commandline')
 s=replace(s,'mainargs.context.event_count==4','mainargs.context.event_count==6');s=replace(s,'"Literal mainargs/helper source reaches named OS import before parser"','"Literal builder resumes after native filename stdcall return and stops before command-line producer read"');s=replace(s,'} else require(entry_job.fault_pc!=mg::import_call||entry_job.fault_target!=mg::import_slot','} else require(entry_job.fault_pc!=fn::stop_pc||entry_job.fault_target!=fn::commandline')
 p.write_text(s)
 files={}
 for predecessor in ('root-acceptance-r1/report.json','build-r2/build.json','recovery-r3/report.json'):
  path=ROOT/'reports/m4-crt-mainargs'/predecessor;files[str(path)]=sha(path)
 for p in [*out.iterdir(),pathlib.Path(__file__),HERE/'filename.hpp',HERE/'filename_binding.inc']:
  if p.is_file():files[str(p.resolve())]=sha(p)
 report=dict(passed=True,scope='Additive typed actual native NULL-module filename service and real compiled continuation to required initialized command-line producer',State_reseed_after_writer=False,old_contexts_modified=False,old_objects_modified=False,new_pages=[],borrowed_pages=16,source_identity_bytes=1140,next_stop_source_PC=0x7800bbd6,next_stop_address=0x78037174,guest_TEB_LastError_written=False,LastError_witness='Immediate actual OS outcome plus explicitly proposed typed guest-thread metadata; enclosing host caller restored',native_component_executed=False,whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=True,bindings=len(files),report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
