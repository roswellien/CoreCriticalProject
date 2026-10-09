"""New native-only three-service CRT prefix; frozen first-fault probe untouched."""
import hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/m4-crt-entry/prefix-preparation-r1'
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def replace(s,a,b):
    assert s.count(a)==1,a
    return s.replace(a,b)
assert not OUT.exists();OUT.mkdir(parents=True)
receipt=ROOT/'reports/m4-crt-entry/first-fault-build-r4/build.json';baseline=json.loads(receipt.read_text(encoding='utf-8-sig'))
files={str(receipt):sha(receipt)}
for name in ('first_fault.cpp','build-first-fault.ps1','first-fault/CMakeLists.txt'):
    p=ROOT/'tools/m4-crt-entry'/name;assert baseline['source_files'][str(p)]==sha(p)
    copy=OUT/(p.name+'.ancestor');copy.write_bytes(p.read_bytes());files[str(p)]=sha(p);files[str(copy)]=sha(copy)
gate=ROOT/'reports/m4-crt/provider-comparison-r1/report.json';assert sha(gate)=='09a6018bb2cd3a6daf79786ee0bd2485b25f6b8c78740a352989019a2511e42a';files[str(gate)]=sha(gate)
s=(ROOT/'tools/m4-crt-entry/first_fault.cpp').read_text()
s=replace(s,'#include "admission.hpp"','#include "admission.hpp"\n#include "crt_services.hpp"')
s=replace(s,'events_.push_back({s_.gpr.rip.dword,a,v,width,0});return v;','events_.push_back({s_.gpr.rip.dword,a,v,width,0});if(a==0x5bb508){require(s_.gpr.rip.dword==0x5ac408&&v==0,"Actual unpublished FDIV data import read");throw Fault(FaultReason::unresolved_import,{s_.gpr.rip.dword},{a},"Required initialized FDIV data import is not connected in this prefix");}return v;')
a=s.index(' void*call(State*s,unsigned target)');b=s.index('\n void invoke()',a)
s=s[:a]+''' void*call(State*s,unsigned target){guard();require(s==&s_&&events_.size()>=2,"Actual source CALL memory events");const auto&read=events_[events_.size()-2];const auto&write=events_.back();
  constexpr std::array<std::array<unsigned,3>,3>calls{{{0x5ac3cf,0x5bb5a4,0x5ac3d5},{0x5ac3ec,0x5bb57c,0x5ac3f2},{0x5ac3fa,0x5bb504,0x5ac400}}};
  const auto found=std::find_if(calls.begin(),calls.end(),[&](const auto&row){return row[0]==read.pc&&row[1]==read.address;});require(found!=calls.end()&&read.write==0&&read.value==target&&write.pc==read.pc&&write.write==1&&write.address==s_.gpr.rsp.dword&&write.value==(*found)[2],"Exact source-owned CRT import CALL/frame");
  r_.cpu()=cpu(s_);r_.cpu().esp+=4;r_.cpu().eip=read.pc;r_.call_import({read.address},{write.value});project(s_,r_.cpu());return this;
 }
''' +s[b:]
s=replace(s,'require(argc==4,"Usage: exact-image exact-entry-object fresh-output-directory");','require(argc==5,"Usage: exact-image exact-entry-object exact-provider fresh-output-directory");')
s=replace(s,'const std::filesystem::path directory=argv[3];','const std::filesystem::path directory=argv[4];')
s=replace(s,'auto r=Runtime::from_admitted_image(image,policy);Context c(r,m4::sha256(object));r.freeze_registry();','auto r=Runtime::from_admitted_image(image,policy);const auto provider=read_file(argv[3]);const auto own_worker=read_file(argv[0]);m4_crt::Session crt(r,provider,{Domain::admitted_game,m4::sha256(own_worker),"09a6018bb2cd3a6daf79786ee0bd2485b25f6b8c78740a352989019a2511e42a"});Context c(r,m4::sha256(object));r.freeze_registry();')
s=replace(s,'const std::array<unsigned,2>pages{0x20001000,0x5bb000};','const std::array<unsigned,4>pages{0x20001000,0x5bb000,0x736000,0x9a1000};')
s=replace(s,'auto capture=[&](const char*tag){','auto capture=[&](const char*tag){std::array<std::byte,12>globals{};r.memory().read({0x78038ee8},globals);output((directory/(std::string(tag)+"-crt-globals.bin")).string(),globals);')
s=replace(s,'fault_pc==0x5ac3cf&&fault_target==slot','fault_pc==0x5ac408&&fault_target==0x5bb508')
s=replace(s,'require(r.calls().size()==1&&!r.calls()[0].completed&&r.calls()[0].target.value==entry,"Entered root incomplete ledger");','require(r.calls().size()==4&&!r.calls()[0].completed&&r.calls()[0].target.value==entry,"Entered root incomplete ledger");for(unsigned i=1;i<4;++i)require(r.calls()[i].completed&&r.calls()[i].import,"Three real measured CRT services returned");')
s=s.replace('first missing-service','first missing-data-import').replace('first-service','three-service-prefix').replace('first required CRT service','three required CRT services and reached the unconnected FDIV data import')
s=s.replace('Native complete-entry first missing-service research','Native complete-entry three-service prefix research')
s=replace(s,'output((directory/"events.bin").string(),','output((directory/"calls.bin").string(),{});{std::ofstream calls(directory/"calls.json");calls<<"[";for(unsigned i=0;i<r.calls().size();++i){const auto&v=r.calls()[i];if(i)calls<<",";calls<<"{\\\"site\\\":"<<v.site.value<<",\\\"target\\\":"<<v.target.value<<",\\\"return_pc\\\":"<<v.return_pc.value<<",\\\"import\\\":"<<(v.import?"true":"false")<<",\\\"completed\\\":"<<(v.completed?"true":"false")<<"}";}calls<<"]\\n";}\n output((directory/"events.bin").string(),')
cpp=OUT/'prefix.cpp';cpp.write_text(s);files[str(cpp)]=sha(cpp)
cmake=(ROOT/'tools/m4-crt-entry/first-fault/CMakeLists.txt').read_text()
cmake=replace(cmake,'get_filename_component(MW34_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../.." ABSOLUTE)','get_filename_component(MW34_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../.." ABSOLUTE)')
cmake=replace(cmake,'add_executable(mw34_crt_entry_first_fault ../first_fault.cpp','add_executable(mw34_crt_entry_first_fault "${MW34_PREFIX_SOURCE}" "${MW34_ROOT}/tools/m4-crt/crt_services.cpp"')
cmake=replace(cmake,'target_include_directories(mw34_crt_entry_first_fault PRIVATE','target_include_directories(mw34_crt_entry_first_fault PRIVATE "${MW34_ROOT}/tools/m4-crt"')
tool=ROOT/'tools/m4-crt-entry/prefix';tool.mkdir();(tool/'CMakeLists.txt').write_text(cmake);files[str(tool/'CMakeLists.txt')]=sha(tool/'CMakeLists.txt')
ps=(ROOT/'tools/m4-crt-entry/build-first-fault.ps1').read_text()
ps=replace(ps,"first-fault-build-r1'","prefix-build-r1'")
ps=replace(ps,"$mwEntrySources=[ordered]@{}","$mwEntrySources=[ordered]@{}\n$mwEntryPrefix=Join-Path $mwEntryRoot 'reports/m4-crt-entry/prefix-preparation-r1/prefix.cpp'\nif((Get-MWEntrySHA $mwEntryPrefix) -ne '"+sha(cpp)+"'){throw 'Exact fresh prefix derivative required'}")
ps=replace(ps,"(Join-Path $PSScriptRoot 'first_fault.cpp'),$PSCommandPath,(Join-Path $PSScriptRoot 'first-fault/CMakeLists.txt')","$mwEntryPrefix,(Join-Path $mwEntryRoot 'tools/m4-crt/crt_services.cpp'),(Join-Path $mwEntryRoot 'tools/m4-crt/crt_services.hpp'),$PSCommandPath,(Join-Path $PSScriptRoot 'prefix/CMakeLists.txt')")
ps=replace(ps,"(Join-Path $PSScriptRoot 'first-fault')","(Join-Path $PSScriptRoot 'prefix')")
ps=replace(ps,'"-DMW34_ENTRY_OBJECT=$mwEntryObject"','"-DMW34_ENTRY_OBJECT=$mwEntryObject", "-DMW34_PREFIX_SOURCE=$mwEntryPrefix"')
ps=replace(ps,'$mwEntryObject,(Join-Path $mwEntryOut "$mwEntryLevel"))','$mwEntryObject,(Join-Path $mwEntryOut "$mwEntryLevel"))') if '$mwEntryObject,(Join-Path $mwEntryOut "$mwEntryLevel"))' in ps else ps
ps=replace(ps,'$mwEntryObject,(Join-Path $mwEntryOut "native-$mwEntryLevel"))','$mwEntryObject,(Join-Path $mwEntryRoot \'local/mw3-staged/Shared_DLLs/MSVCRT.DLL\'),(Join-Path $mwEntryOut "native-$mwEntryLevel"))')
ps=ps.replace('first missing CRT import','unconnected initialized FDIV data import after three reviewed CRT services').replace('first missing-service','three-service prefix')
builder=ROOT/'tools/m4-crt-entry/build-prefix.ps1';builder.write_text(ps);files[str(builder)]=sha(builder)
files[str(Path(__file__))]=sha(Path(__file__))
(OUT/'report.json').write_text(json.dumps(dict(passed=True,scope='New native-only prefix preparation; no execution or startup credit',files=files,exact_ancestor_sha256=baseline['source_files'][str(ROOT/'tools/m4-crt-entry/first_fault.cpp')],changes=['Connect exact reviewed original CRT service model with live Runtime ownership','Route three actual source import frames; project returned CPU into persistent State','Stop explicitly at unpublished FDIV data import before source MOV completes','Capture full source data pages and provider globals plus actual call ledger'],original_executed=False,full_CRT=False,whole_M4_complete=False),indent=2)+'\n')
print(json.dumps(dict(passed=True,report_sha256=sha(OUT/'report.json'),prefix_source_sha256=sha(cpp))))
