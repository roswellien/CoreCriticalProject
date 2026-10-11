"""Correct observer targeting: actual CPU is API target; source CALL site is in witness."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=ROOT/'reports/m4-lockit-review/controls-source-r2';assert not out.exists();out.mkdir(parents=True)
old=ROOT/'reports/m4-lockit-review/controls-source-r1';h=(old/'hooks.hpp').read_text();f=(old/'fixture.inc').read_text()
h=h.replace('struct Snapshot{std::vector<std::array<std::uint64_t,16>>calls;};','struct Snapshot{std::vector<std::array<std::uint64_t,16>>calls;std::array<std::uint64_t,32>api{};};')
needle='inline void snapshot_sink(std::string_view name,std::span<const std::byte>b,void*context){if(name=="lockit-calls.bin")'
new='inline void snapshot_sink(std::string_view name,std::span<const std::byte>b,void*context){if(name.starts_with("locale-api-")&&name.ends_with("-witness.bin")){check(b.size()==256,"Actual complete API frame witness");std::memcpy(static_cast<Snapshot*>(context)->api.data(),b.data(),256);}if(name=="lockit-calls.bin")'
assert h.count(needle)==1;h=h.replace(needle,new)
needle=' if(point!=(after?41U:40U)||pc!=0x7810a30b)return;\n ++hits;trigger_point=point;trigger_PC=pc;trigger=snapshot(s);'
new=' if(point!=(after?41U:40U))return;auto actual=snapshot(s);if(actual.api[2]!=0x7810a30b)return;\n ++hits;trigger_point=point;trigger_PC=pc;trigger=std::move(actual);'
assert h.count(needle)==1;h=h.replace(needle,new)
needle=' w.append(p+"calls.bin",trigger.calls.data(),trigger.calls.size()*128);'
assert f.count(needle)==1;f=f.replace(needle,needle+'w.append(p+"api-witness.bin",trigger.api.data(),sizeof(trigger.api));')
(out/'hooks.hpp').write_text(h);(out/'fixture.inc').write_text(f)
builder=(HERE/'build_controls.py').read_text().replace('reports/m4-lockit-review/controls-source-r1','reports/m4-lockit-review/controls-source-r2');(HERE/'build_controls_v2.py').write_text(builder)
wrapper=(HERE/'build_controls.ps1').read_text().replace("'build_controls.py'","'build_controls_v2.py'");(HERE/'build_controls_v2.ps1').write_text(wrapper)
paths=[Path(__file__),old/'hooks.hpp',old/'fixture.inc',out/'hooks.hpp',out/'fixture.inc',HERE/'build_controls.py',HERE/'build_controls_v2.py',HERE/'build_controls_v2.ps1']
(out/'report.json').write_text(json.dumps({'passed':True,'scope':'Corrected actual API target CPU versus retained source CALL-site witness; native bodies unchanged','cases':16,'files':{str(p):sha(p) for p in paths}},indent=2)+'\n');print(json.dumps({'passed':True,'sha256':sha(out/'report.json')}))
