"""Create additive independent fixture from only our frozen first-fault helpers."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent;OLD=ROOT/'tools/m4-crt-entry-first-fault-independent/compiled/controls.cpp'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not (OUT/'controls.cpp').exists()
 s=OLD.read_text();head=s[:s.index('class Context;')]
 head=head.replace('#include "admission.hpp"','#include "admission.hpp"\n#include "crt_services.hpp"')
 head=head.replace('unsigned checks{},scenarios{},source_rows{},faults{},retries{},unentered{};','unsigned checks{},scenarios{},source_rows{},faults{},retries{},unentered{},construction_controls{};\nstd::string crt_native_sha;')
 bridge=s[s.index('extern "C" unsigned __remill_read_memory_32'):s.index('struct Fixture{')]
 source=head+(OUT/'context.inc').read_text()+bridge+(OUT/'model_controls.inc').read_text()
 (OUT/'controls.cpp').write_text(source)
 cm=(ROOT/'tools/m4-crt-entry-first-fault-independent/compiled/CMakeLists.txt').read_text().replace('${CMAKE_CURRENT_SOURCE_DIR}/../../..','${CMAKE_CURRENT_SOURCE_DIR}/../..').replace('controls.cpp "${MW34_GUEST_OBJECT}"','controls.cpp "${MW34_GUEST_OBJECT}"\n "${WORKSPACE}/tools/m4-crt/crt_services.cpp"').replace('PRIVATE "${WORKSPACE}/tools/m4-runtime"','PRIVATE "${WORKSPACE}/tools/m4-crt" "${WORKSPACE}/tools/m4-runtime"')
 (OUT/'CMakeLists.txt').write_text(cm)
 (OUT/'derivation.json').write_text(json.dumps(dict(prior_own_frozen_source=str(OLD),prior_own_source_sha256=sha(OLD),retained_parts='Only own checked CPU/State/file helpers, typed throwing bridge declarations and policy. New Context composition/model/control files independently authored.',new_sources={str(p):sha(p)for p in OUT.iterdir()if p.is_file()and p.name!='derivation.json'},author_model_fixture_executor_imported=False),indent=2)+'\n')
 print(json.dumps(dict(controls_sha256=sha(OUT/'controls.cpp'))))
if __name__=='__main__':main()
