"""Retain actual Runtime-entry BEFORE for each refused connected source case."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];parent=Path(__file__).parent/'connected_controls_v2.inc';target=parent.with_name('connected_controls_v3.inc');assert not target.exists()
text=parent.read_text();marker='static unsigned mfc_control_mode{};'
entry='''static void mfc_control_entry(mw34::m4_runtime::Runtime&r,State&s){
 auto put=[&](const std::string&name,const void*b,std::size_t n){mfc_sink("entry/"+name,std::span(static_cast<const std::byte*>(b),n),nullptr);};
 put("State.bin",&s,3504);put("CPU.bin",&r.cpu(),40);put("FX.bin",r.fx().data(),512);put("Native.bin",mw34::m4_mixed::observation,sizeof(mw34::m4_mixed::Native));
 std::vector<std::array<unsigned,2>>regions;auto add=[&](unsigned a,unsigned n){if(std::none_of(regions.begin(),regions.end(),[&](const auto&x){return x[0]==a&&x[1]==n;}))regions.push_back({a,n});};
 for(unsigned a:mw34::m4_mixed::registration_pages)add(a,4096);for(auto row:mc::literal::source_spans)add(row.pc&~4095U,4096);const auto i=mc::make_fixture_inputs();for(const auto&v:i.new_mappings)add(v.address,unsigned(v.before.size()));add(0x78037000,4096);add(r.fs_base().value,4);add(r.fs_base().value+4,8);add(r.fs_base().value+0x18,4);
 std::sort(regions.begin(),regions.end());put("memory-index.bin",regions.data(),regions.size()*sizeof(regions[0]));for(auto v:regions){std::vector<std::byte>b(v[1]);r.memory().read({v[0]},b);put("memory-"+std::to_string(v[0])+"-"+std::to_string(v[1])+".bin",b.data(),b.size());}
}
'''
assert text.count(marker)==1;text=text.replace(marker,entry+marker);target.write_text(text);print(json.dumps({'path':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))
