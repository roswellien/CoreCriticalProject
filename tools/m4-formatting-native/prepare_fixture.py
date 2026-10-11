"""Actual Runtime fixture for three formatter roots over accepted125 Context."""
from pathlib import Path
import hashlib,json,re,shutil,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(native_path,digest,name):
    out=R/'reports/m4-formatting-native'/name;assert not out.exists();out.mkdir(parents=True);pins={}
    def pin(p,h=None):
        p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);pins[str(p)]=v;return p
    def read(p,h=None):return json.loads(pin(p,h).read_bytes())
    def one(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
    native=read(native_path,digest);assert native['passed'];native_prep=Path(native_path).parent
    for p,h in native['files'].items():
        if Path(p).parent==native_prep:pin(p,h)
    parent=R/'reports/m4-joint-startup125/preparation-r4';prior=read(parent/'report.json','243b6f4c86dc2b966789e23faed4a10fe2efa62ba51f43e854fa843acde392e7')
    derived=out/'connected';derived.mkdir()
    for folder in('derived','ancestors','O0','O2'):shutil.copytree(parent/folder,derived/folder)
    for p in parent.iterdir():
        if p.suffix in('.cpp','.hpp','.inc')or p.name=='CMakeLists.txt':shutil.copy2(p,derived/p.name)
    for p,h in prior['generated_sources'].items():pin(p,h)
    p=derived/'registration_contract.hpp';s=p.read_text();s=one(s,'std::array<unsigned,97> registration_roots{','std::array<unsigned,100> registration_roots{');s=one(s,'0x5968f0,0x4b7f70};','0x5968f0,0x4b7f70,0x4df610,0x4e0710,0x4e0810};');s=one(s,'std::array<unsigned,26> registration_pages{','std::array<unsigned,29> registration_pages{');s=one(s,'0x78145000,0x78146000};','0x78145000,0x78146000,0x5cd000,0x5e3000,0x5e9000};');p.write_text(s)
    p=derived/'joint_protocol.hpp';s,n=re.subn(r'constexpr std::array<std::uint32_t,125> entries\{[^\n]+\};','constexpr std::array<std::uint32_t,3> entries{0x4df610,0x4e0710,0x4e0810};',p.read_text());assert n==1;p.write_text(s)
    p=derived/'native_main.cpp';s=one(p.read_text(),'phase==125&&r_.calls().size()==128&&r_.translation_count()==126','phase==3&&r_.calls().size()==3&&r_.translation_count()==129');p.write_text(s)
    objects={}
    for level in('O0','O2'):
        appended=[b['objects'][level]['path']for b in native['formatting_bodies'].values()];objects[level]=prior['objects'][level]+appended;assert len(objects[level])==390 and len(set(objects[level]))==390
        for obj in objects[level]:pin(obj)
        p=derived/level/'registration_bindings.inc';s=p.read_text()
        for root in native['new_roots']:
            b=native['formatting_bodies'][str(root)];extent=b['source_bytes'];s+=f'\nr_.register_translation({{{{{hex(root)}}},{{m4_runtime::Abi::Cdecl,0,true}},&registration_entry,"Isolated literal formatter root",{{m4_runtime::Domain::admitted_game,m4::admitted_image_hash,{extent},"{b["source_sha256"]}","{b["objects"][level]["sha256"]}","{digest}"}}}});\n'
        p.write_text(s)
    pages=sorted(set(map(int,native['source_pages']))|set(native['game_pages'])|{0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x20000000})
    (out/'current_pages.hpp').write_text('#pragma once\nnamespace mw34_tree_fixture {inline constexpr std::array<unsigned,'+str(len(pages))+'>current_pages{'+','.join(hex(x)for x in pages)+'};}\n')
    template=pin(R/'tools/m4-tree-review/fixture_v2.inc');s=template.read_text();s=one(s,'constexpr unsigned tree_root=0x4b7f70;','constexpr unsigned tree_root=0x4df610;');s=one(s,'need(active_tree_task&&phase==0,"One actual tree before phase");dump(c,*active_tree_task->w,"actual-before-root/",active_tree_task->aliases);','need(active_tree_task&&phase<3,"Three actual formatting before phases");dump(c,*active_tree_task->w,"actual-before-root-"+std::to_string(phase)+"/",active_tree_task->aliases);');s=one(s,'need(active_tree_task&&phase==1,"One actual tree after phase");dump(c,*active_tree_task->w,"actual-after-root/",active_tree_task->aliases);','need(active_tree_task&&phase>=1&&phase<=3,"Three actual formatting after phases");dump(c,*active_tree_task->w,"actual-after-root-"+std::to_string(phase-1)+"/",active_tree_task->aliases);');s=one(s,'sizeof(Sample),3504,40,512,43','sizeof(Sample),3504,40,512,46');s=one(s,'result&&t.completed==1&&sample.tags[9]==7&&sample.tags[10]==7','result&&t.completed==3&&sample.tags[9]==0&&sample.tags[10]==0');s=s.replace('Isolated literal tree positive passed; connected125 acceptance is separate','Isolated literal formatting3 positive passed; connected family acceptance is separate')
    (out/'fixture.cpp').write_text('#define main frozen_connected125_worker_main\n#include "'+(derived/'native_main.cpp').as_posix()+'"\n#undef main\n'+s)
    capture=pin(R/'tools/m4-crt-allocation/capture.s');s=one(capture.read_text(),'  movdqu 256(%r9), %xmm6','  fxrstor64 (%r9)\n  fldenv 512(%r9)\n  movdqu 256(%r9), %xmm6');(out/'capture.s').write_text(s)
    s=one((derived/'CMakeLists.txt').read_text(),'"${MW34_PREP}/native_main.cpp"','"'+(out/'fixture.cpp').as_posix()+'"');s=one(s,'${MW34_OBJECTS} "${MW34_WRITER}"','${MW34_OBJECTS} "'+(out/'capture.obj').as_posix()+'" "${MW34_WRITER}"');(out/'CMakeLists.txt').write_text(s)
    pin(__file__);files={str(p.resolve()):sha(p)for p in out.rglob('*')if p.is_file()}
    report=dict(passed=True,scope='Isolated actual Runtime-selected formatting3 Context; source and lifecycle review pending',native_preparation=str(native_path),native_preparation_sha256=digest,native_library=native['native_library'],native_include=native['native_include'],connected_include=str(derived),objects=objects,selected_roots=native['new_roots'],literal_objects_per_level=390,current_pages=pages,ordinary_pages=46,Native_bytes=159716,actual_Runtime_selected_call=True,API_response_injection=False,native_executed=False,initializer_credit=0,sources=pins,files=files)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
