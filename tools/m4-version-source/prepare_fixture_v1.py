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
  cp=R/'reports/m4-version-source/component-preparation-r1/report.json';component=read(cp,'04d6577108759bc23ca304a20d0affd74e910657775fb78ac4e54dab16288c61');bp=R/'reports/m4-version-source/component-build-r1/build.json';build=read(bp,'db59e600f4f2930328008b9f735ebc4d243c1ffa9300edc7feec5bbb41c9a62f');sp=R/'reports/m4-version-source/service-preparation-r3/report.json';service=read(sp,'e2b5f0b0cd96dfc1a395c9f0d4e41da4783540d174df857d1cd284d4b9f74318');sbp=R/'reports/m4-version-source/service-build-r3/build.json';sb=read(sbp,'c8e0c511a8fbf83e99151266fb9ca49b1c096acbd2b239dac9734a706127cb63');parentp=R/'reports/m4-widget-native/fixture-preparation-r16/report.json';parent=read(parentp,'58c6d615dfc5c23acf56bd3f62b8635f5647831e623c956154b78986af0e5401');need(all(x['passed']for x in(component,build,service,sb,parent)),'Actual libraries and complete immutable caller recipe')
  for d in(component,build,service,sb):
   for p,h in d['files'].items():pin(p,h)
  p=pin(parentp.parent/'inherited_main.cpp',parent['files'][str((parentp.parent/'inherited_main.cpp').resolve())]);s=p.read_text();old=parent['native_include'].replace('\\','/')+'/session.hpp';new=service['native_include'].replace('\\','/')+'/session.hpp';need(s.count(old)==1,'One concrete inherited service header binding');s=s.replace(old,new);(out/'inherited_main.cpp').write_text(s);shutil.copyfile(pin(R/'tools/m4-version-source/fixture_v1.cpp'),out/'fixture.cpp')
  sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
  pin(R/'tools/analysis/pe.py');game=pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');pe=PEImage(game.read_bytes());size=0x4af26e-0x4af240;off,_=pe.rva_range(0x4af240-pe.image_base,size);raw=pe.data[off:off+size];need(raw[-4:]==bytes.fromhex('83c404c3'),'Whole physical initializer final ADD/RET');digest=hashlib.sha256(raw).hexdigest();(out/'version_binding.hpp').write_text('#pragma once\nstruct VersionBinding {unsigned source_size;const char*source_sha;};\ninline constexpr VersionBinding version_binding{%d,"%s"};\n'%(size,digest))
  physical=dict(root=0x4af240,begin=0x4af240,end_exclusive=0x4af26e,bytes=size,sha256=digest,bytes_hex=raw.hex(),file_offset=off,registration_CALL=0x4af265,callback=0x4af270,callback_executed=False);(out/'Runtime-physical-source-span.json').write_text(json.dumps(physical,indent=2)+'\n');levels={}
  for level in ('O0','O2'):
   v=parent['levels'][level];objects=[pin(p,parent['files'][str(Path(p).resolve())])for p in v['objects']];need(len(objects)==427,'Unchanged427 inherited core/provider/literal COFFs');library=pin(build['levels'][level]['library'],build['levels'][level]['library_sha256']);service_library=pin(sb['levels'][level]['library'],sb['levels'][level]['library_sha256']);forced=pin(v['forced_registry_header'],parent['files'][str(Path(v['forced_registry_header']).resolve())]);levels[level]=dict(objects=[str(p)for p in objects],component_library=str(library),component_library_sha256=sha(library),service_library=str(service_library),service_library_sha256=sha(service_library),forced_registry_header=str(forced),fixed_objects=427)
  for p in out.iterdir():pin(p)
  pin(__file__)
  report=dict(passed=True,scope='One registered real version initializer with both complete native libraries, true VERSION.dll API providers, genuine MFC owner and source onexit callback; compile recipe only',component_include=str(cp.parent),native_include=str(sp.parent),parent_include=parent['parent_include'],levels=levels,root=0x4af240,root_count=1,literal_bodies=10,source_callback=0x4af270,callback_executed=False,worker_cwd=str((R/'MW3').resolve()),whole_Game_BEFORE_from_own_admitted_PE=True,authored_external_current_caller_initialization=True,original_CPU_or_output_seeds=False,AFTER_machine_seed=False,actual_VERSION_API_branches_retained=True,actual_file_CWD_identity_measured_by_service=True,native_executed=False,original_executed=False,initializer_credit=0,first_writer_admission_required=True,files=pins)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(sys.argv[1])
