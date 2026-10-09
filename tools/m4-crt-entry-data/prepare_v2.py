"""Retain first probe; explicit undefined TEST AF and entry ABI checkpoint."""
import hashlib,json,pathlib,shutil,sys
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-entry-data'
def sha(p):
 with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def replace(s,a,b):
 assert s.count(a)==1,a
 return s.replace(a,b)
def main(out):
 out=pathlib.Path(out).resolve();assert out.parent==BASE and not out.exists()
 previous=BASE/'preparation-r1';files={}
 for p,h in json.loads((previous/'pins.json').read_text())['files'].items():assert sha(p)==h,p;files[p]=h
 s=(previous/'composition.cpp').read_text();s=replace(s,'struct Event{unsigned pc,address,value,width,write;};','struct Event{unsigned pc,address,value,width,write;};\nvoid entry_checkpoint(Runtime&);')
 s=replace(s,'running_=true;try{(void)sub_5ac3a0','running_=true;try{entry_checkpoint(r_);(void)sub_5ac3a0')
 s=replace(s,'extern "C" unsigned char mw34_fdiv_entry_undefined_8() noexcept(false) {throw std::runtime_error("Unreached undefined flag representative");}','extern "C" unsigned char mw34_fdiv_entry_undefined_8() noexcept(false) {require(owner,"Undefined representative needs active owner");owner->guard();require(owner->state().gpr.rip.dword==0x5ac41f,"Only original TEST undefined AF admitted");return 0;}')
 s=replace(s,'#include "main.inc"','#include "main_v2.inc"')
 main_source=(ROOT/'tools/m4-crt-entry-data/main.inc').read_text()
 main_source=replace(main_source,'#include "observations.hpp"','#include "observations.hpp"\nnamespace {thread_local std::filesystem::path checkpoint_directory;void entry_checkpoint(Runtime&r){snapshot(r,checkpoint_directory,"entry-projected");}}')
 main_source=replace(main_source,'auto row=directory/("row-"+std::to_string(scenario));','auto row=directory/("row-"+std::to_string(scenario));checkpoint_directory=row;')
 main_source=replace(main_source,'snapshot(r,row,"entry-after-fault");fresh_output','snapshot(r,row,"entry-after-fault");raw_output(row/"entry-job.bin",entry_job);fresh_output')
 out.mkdir()
 for name in ('seed.hpp','observations.hpp'):shutil.copyfile(previous/name,out/name)
 shutil.copyfile(previous/'composition.cpp',out/'composition-ancestor.cpp')
 (out/'composition.cpp').write_text(s);(out/'main_v2.inc').write_text(main_source)
 report=dict(passed=True,scope='Additive observed TEST undefined-AF site representative and explicit entry checkpoint',State_reseed_after_writer=False,State_bytes=3504,
  undefined_AF_policy='AF=0 only at source TEST0x5AC41F; architecturally undefined, no original AF equality or preservation credit',
  arithmetic_or_CFG_rewritten=False,entry_checkpoint='Runtime source frame and State outer ESP/EIP projection captured immediately before actual translated entry',
  failed_probe=str(BASE/'probe-r1-O0'),failed_probe_sha256=sha(BASE/'probe-r1-O0/row-0/entry-after-fault/state.bin'),
  full_CRT=False,whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 for p in out.iterdir():files[str(p)]=sha(p)
 for p in (pathlib.Path(__file__).resolve(),ROOT/'tools/m4-crt-entry-data/main.inc',previous/'report.json',previous/'pins.json'):files[str(p)]=sha(p)
 for p in (BASE/'probe-r1-O0').rglob('*'):
  if p.is_file():files[str(p)]=sha(p)
 (out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main(sys.argv[1])
