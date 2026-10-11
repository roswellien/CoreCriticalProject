"""Concrete one-route real VERSION/MFC/onexit fixture; first writer still unadmitted."""
from pathlib import Path
import hashlib,json,shutil,sys,traceback
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-version-source'/name;need(not out.exists(),'Fresh version fixture preparation');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact fixture source/artifact '+str(p));pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 try:
  cp=R/'reports/m4-version-source/component-preparation-r2/report.json';component=read(cp,'1143e3cef914a5582e93231a810dfd32cc0eabd94534ccaa7025045b0964ed4d');bp=R/'reports/m4-version-source/component-build-r2/build.json';build=read(bp,'3bca59f305044aa480117626ecd3718acb64694b5578ec88a87671a794284b52');sp=R/'reports/m4-version-source/service-preparation-r4/report.json';service=read(sp,'f35a730b53c0299e42d0955a89d29ce2e3289569f5a47fbad538344f55a0dbc5');sbp=R/'reports/m4-version-source/service-build-r4/build.json';sb=read(sbp,'9c9426e2e70b24c6b71ae102581c625a155ccc61acecc0c914dcc065904ea133');parentp=R/'reports/m4-widget-native/fixture-preparation-r16/report.json';parent=read(parentp,'58c6d615dfc5c23acf56bd3f62b8635f5647831e623c956154b78986af0e5401');need(all(x['passed']for x in(component,build,service,sb,parent)),'Actual libraries and complete immutable caller recipe')
  for d in(component,build,service,sb):
   for p,h in d['files'].items():pin(p,h)
  p=pin(parentp.parent/'inherited_main.cpp',parent['files'][str((parentp.parent/'inherited_main.cpp').resolve())]);s=p.read_text();old=parent['native_include'].replace('\\','/')+'/session.hpp';new=service['native_include'].replace('\\','/')+'/session.hpp';need(s.count(old)==1,'One concrete inherited service header binding');s=s.replace(old,new);(out/'inherited_main.cpp').write_text(s);shutil.copyfile(pin(R/'tools/m4-version-source/fixture_v1.cpp'),out/'fixture.cpp')
  sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
  pin(R/'tools/analysis/pe.py');game=pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');pe=PEImage(game.read_bytes());size=0x4af26e-0x4af240;off,_=pe.rva_range(0x4af240-pe.image_base,size);raw=pe.data[off:off+size];need(raw[-4:]==bytes.fromhex('83c404c3'),'Whole physical initializer final ADD/RET');digest=hashlib.sha256(raw).hexdigest();(out/'version_binding.hpp').write_text('#pragma once\nstruct VersionBinding {unsigned source_size;const char*source_sha;};\ninline constexpr VersionBinding version_binding{%d,"%s"};\n'%(size,digest))
  physical=dict(root=0x4af240,begin=0x4af240,end_exclusive=0x4af26e,bytes=size,sha256=digest,bytes_hex=raw.hex(),file_offset=off,registration_CALL=0x4af265,callback=0x4af270,callback_executed=False);(out/'Runtime-physical-source-span.json').write_text(json.dumps(physical,indent=2)+'\n');levels={}
  for level in ('O0','O2'):
   v=parent['levels'][level];objects=[pin(p,parent['files'][str(Path(p).resolve())])for p in v['objects']];need(len(objects)==427,'Unchanged427 inherited core/provider/literal COFFs');library=pin(build['levels'][level]['library'],build['levels'][level]['library_sha256']);service_library=pin(sb['levels'][level]['library'],sb['levels'][level]['library_sha256']);forced=pin(v['forced_registry_header'],parent['files'][str(Path(v['forced_registry_header']).resolve())]);levels[level]=dict(objects=[str(p)for p in objects],component_library=str(library),component_library_sha256=sha(library),service_library=str(service_library),service_library_sha256=sha(service_library),forced_registry_header=str(forced),fixed_objects=427)
  for p in out.iterdir():pin(p)
  pin(__file__);pin(R/'tools/m4-version-source/prepare_fixture_v1.py','d36fc0bc22e83857e4731d4f4ff6c6f0ebb9c6a5780c6efc97c3dc09beeeb7a5');pin(R/'tools/m4-version-source/derive_fixture_v2.py')
  report=dict(passed=True,scope='One registered real version initializer with both complete native libraries, true VERSION.dll API providers, genuine MFC owner and source onexit callback; compile recipe only',component_include=str(cp.parent),native_include=str(sp.parent),parent_include=parent['parent_include'],levels=levels,root=0x4af240,root_count=1,literal_bodies=10,source_callback=0x4af270,callback_executed=False,worker_cwd=str((R/'MW3').resolve()),whole_Game_BEFORE_from_own_admitted_PE=True,authored_external_current_caller_initialization=True,original_CPU_or_output_seeds=False,AFTER_machine_seed=False,actual_VERSION_API_branches_retained=True,actual_file_CWD_identity_measured_by_service=True,native_executed=False,original_executed=False,initializer_credit=0,first_writer_admission_required=True,files=pins)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(sys.argv[1])
