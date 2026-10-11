"""Freeze seven actual caller-owned Session/Runtime routes, no writer."""
from pathlib import Path
import hashlib,json,shutil,struct,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-fps-native'/name;need(not out.exists(),'Fresh seven-route fixture');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact compiled/input identity '+str(p));pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 cp=R/'reports/m4-fps-native/component-preparation-r1/report.json';component=read(cp,'294ac018294dbb35b341d8c86e195d23b68ce0f249fa86aa02781e8c181c5a18');cbp=R/'reports/m4-fps-native/component-build-r1/build.json';cb=read(cbp,'ec46a763da58431d8300b5f9493af5ecec1b25f33ffca837684ef0f851a4415f');sp=R/'reports/m4-fps-native/service-preparation-r2/report.json';service=read(sp,'d3afbd1f20d9a286a0ae8565554845f897c4d7a051d60110bb64912fa15d77c2');prior_path=R/'reports/m4-widget-native/fixture-preparation-r16/report.json';prior=read(prior_path,'58c6d615dfc5c23acf56bd3f62b8635f5647831e623c956154b78986af0e5401');need(all(x['passed']for x in(component,cb,service,prior))and component['root_count']==7 and component['literal_bodies']==58,'Exact linked libraries and finite seven-root interface')
 for report in(component,cb,service):
  for p,h in report['files'].items():pin(p,h)
 cpp=pin(R/'tools/m4-fps-native/fixture_v1.cpp');shutil.copyfile(cpp,out/'fixture.cpp');inherited=pin(prior_path.parent/'inherited_main.cpp',prior['files'][str((prior_path.parent/'inherited_main.cpp').resolve())]);text=inherited.read_text();old=prior['native_include'].replace('\\','/')+'/session.hpp';new=service['native_include'].replace('\\','/')+'/session.hpp';need(text.count(old)==1,'One actual admitted Session include binding');text=text.replace(old,new);(out/'inherited_main.cpp').write_text(text)
 contract=read(cp.parent/'contracts.json',component['files'][str((cp.parent/'contracts.json').resolve())]);game_path=pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');raw=game_path.read_bytes();pe=struct.unpack_from('<I',raw,0x3c)[0];n=struct.unpack_from('<H',raw,pe+6)[0];opt=struct.unpack_from('<H',raw,pe+20)[0];base=struct.unpack_from('<I',raw,pe+24+28)[0];start=pe+24+opt;sections=[]
 for i in range(n):
  off=start+40*i;vs,rva,size,fo=struct.unpack_from('<4I',raw,off+8);flags=struct.unpack_from('<I',raw,off+36)[0];sections.append((base+rva,size,fo,flags))
 def physical(pc,size):
  owner=[v for v in sections if v[0]<=pc and pc+size<=v[0]+v[1]];need(len(owner)==1 and owner[0][3]&0x20000000,'One complete executable physical game source');v=owner[0];off=v[2]+pc-v[0];return raw[off:off+size],off
 h=['#pragma once','#include "component.hpp"','struct WidgetBinding {unsigned root,source_size;const char*source_sha256;mw34::m4_runtime::NativeEntry callback;};','inline constexpr std::array<WidgetBinding,7>widget_bindings{{'];spans=[]
 for root in contract['roots']:
  reg=root['registration'];call=reg['CALL_pc'];ret=reg['return_PC']+3;tail,_=physical(reg['return_PC'],4);need(reg['return_PC']==call+5 and tail==bytes.fromhex('83c404c3'),'Literal root registration return and RET');size=ret+1-root['root'];data,fo=physical(root['root'],size);digest=hashlib.sha256(data).hexdigest();h.append('{%d,%d,"%s",mw34::m4_widget_native::Component::entry_%x},'%(root['root'],size,digest,root['root']));spans.append(dict(root=root['root'],begin=root['root'],end_exclusive=ret+1,bytes=size,sha256=digest,bytes_hex=data.hex(),file_offset=fo,final_RET=ret,registration_CALL=call))
 h+=['}};'];(out/'widget_bindings.hpp').write_text('\n'.join(h)+'\n');q=out/'Runtime-physical-source-spans.json';q.write_text(json.dumps(spans,indent=2)+'\n');levels={}
 for level in('O0','O2'):
  inherited_level=prior['levels'][level];objects=[pin(p,prior['files'][str(Path(p).resolve())])for p in inherited_level['objects']];need(len(objects)==427,'Complete unchanged current130 literal/core/capture object lineage');library=pin(cb['levels'][level]['library'],cb['levels'][level]['library_sha256']);forced=pin(inherited_level['forced_registry_header'],prior['files'][str(Path(inherited_level['forced_registry_header']).resolve())]);levels[level]=dict(objects=[str(p)for p in objects],component_library=str(library),component_library_sha256=sha(library),forced_registry_header=str(forced),fixed_objects=427)
 for p in out.iterdir():pin(p)
 for p in [__file__,R/'tools/m4-fps-native/derive_fixture.py',R/'tools/m4-fps-native/fixture-source-relations.json',R/'tools/m4-fps-native/build_fixture.py',R/'tools/m4-fps-native/build_fixture.ps1']:pin(p)
 report=dict(passed=True,scope='Seven registered widget/FPS Runtime routes with literal formatter and actual caller-owned accepted onexit/heap/CS; compile recipe only',component_preparation_sha256=sha(cp),component_build_sha256=sha(cbp),service_preparation_sha256=sha(sp),native_library=service['native_library'],native_include=service['native_include'],component_include=str(cp.parent),parent_include=prior['parent_include'],levels=levels,files=pins,source_roots=component['roots'],root_count=7,literal_bodies=58,whole_Game_BEFORE_from_own_admitted_PE=True,authored_current_caller_CPU_initialization=True,original_CPU_or_GDI_seeds=False,per_root_State_or_page_seed=False,AFTER_machine_seed=False,host_vsprintf_substitution=False,finite_narrow_format_only=True,native_executed=False,initializer_credit=0)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
