"""Additive whole-loop host boundary before the large body's stack probe."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def one(s,a,b):assert s.count(a)==1,repr(a);return s.replace(a,b)
def main(out):
 out=Path(out).resolve();assert out.parent==ROOT/'reports/m4-joint-startup27' and not out.exists();out.mkdir(parents=True)
 parent=ROOT/'tools/m4-joint27-startup/native_main.cpp';assert sha(parent)=='b9b3980be51a2dafbc5032d69d52539747b9b465ba3163d270d519b717930511'
 s=parent.read_text()
 s=one(s,' bool invoke_selected_table(unsigned sequence,unsigned repeat,unsigned top,std::vector<Native>&records)noexcept{\n  ni::NumericHostBoundary boundary(admitted_cw_);bool ok=false;unsigned phase=0;',' [[clang::noinline]] bool invoke_selected_table(unsigned sequence,unsigned repeat,unsigned top,std::vector<Native>&records)noexcept{\n  // Save caller numerical/legacy state before the private large frame probes.\n  ni::NumericHostBoundary boundary(admitted_cw_);return invoke_selected_body(sequence,repeat,top,records);\n }\n [[clang::noinline]] bool invoke_selected_body(unsigned sequence,unsigned repeat,unsigned top,std::vector<Native>&records)noexcept{\n  bool ok=false;unsigned phase=0;')
 (HERE/'native_main.cpp').write_text(s)
 controls=HERE/'controls';controls.mkdir(exist_ok=True)
 fixture=ROOT/'tools/m4-joint27-startup/controls/fixture.cpp';body=fixture.read_text()
 # Preserve a diagnostic version of the old boundary and a semantic-identical
 # repair-control fixture. Only pre-seed kind labels are added in diagnostic.
 (controls/'fixture.cpp').write_text(body)
 diagnostic=one(body,'#include "../native_main.cpp"','#include "'+parent.as_posix()+'"')
 diagnostic=one(diagnostic,' Host caller(static_cast<std::uint16_t>(cw));bool result=', ' std::cerr<<"CONTROL_START kind="<<kind<<" cw="<<cw<<" retry="<<retry<<"\\n";\n Host caller(static_cast<std::uint16_t>(cw));bool result=')
 (controls/'diagnostic.cpp').write_text(diagnostic)
 oldcmake=ROOT/'tools/m4-joint27-startup/controls/CMakeLists.txt';cmake=oldcmake.read_text()
 cmake=cmake.replace('project(MW34Joint27Controls LANGUAGES CXX)','project(MW34JointStartup27Controls LANGUAGES CXX)')
 cmake=one(cmake,'add_executable(mw34_joint27_controls fixture.cpp ${MW34_FP_CPP}','set(MW34_FIXTURE fixture.cpp)\nif(MW34_DIAGNOSTIC)\n set(MW34_FIXTURE diagnostic.cpp)\nendif()\nadd_executable(mw34_joint27_controls ${MW34_FIXTURE} ${MW34_FP_CPP}')
 (controls/'CMakeLists.txt').write_text(cmake)
 report={'passed':True,'scope':'Boundary ownership moved into a small noinline public wrapper before unchanged large noinline body; no guest/State/domain/events/route mutations','ancestors':{str(p):sha(p)for p in(parent,fixture,oldcmake)},'generated':{str(p):sha(p)for p in(HERE/'native_main.cpp',controls/'fixture.cpp',controls/'diagnostic.cpp',controls/'CMakeLists.txt')},'diagnostic_only':'CONTROL_START kind/CW/retry label before Host seed, frozen large Context boundary retained','semantic_repair':'Save host before large body stack probe; catch/refusal retained inside original body; restored wrapper returns status','native_execution':False,'whole_M4_complete':False}
 (out/'derivation.json').write_text(json.dumps(report,indent=2)+'\n');(out/'pins.json').write_text(json.dumps({'files':report['ancestors']|report['generated']|{str(Path(__file__).resolve()):sha(__file__)}},indent=2)+'\n')
 print(json.dumps({'passed':True,'boundary_derivative':str(HERE/'native_main.cpp')}))
if __name__=='__main__':main(sys.argv[1])
