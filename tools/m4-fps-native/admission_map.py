"""Author-side bounded physical source/build inventory, not independent admission."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-fps-native'/name;need(not out.exists(),'Fresh author admission inventory');out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader');v=sha(p);need(h is None or h==v,'Physical current identity '+str(p));pins[str(p)]=v;return p
 def receipt(p,h):
  d=json.loads(pin(p,h).read_bytes());need(d['passed'],'Passed input');return d
 cp=receipt(R/'reports/m4-fps-native/component-preparation-r1/report.json','294ac018294dbb35b341d8c86e195d23b68ce0f249fa86aa02781e8c181c5a18');cb=receipt(R/'reports/m4-fps-native/component-build-r1/build.json','ec46a763da58431d8300b5f9493af5ecec1b25f33ffca837684ef0f851a4415f');fp=receipt(R/'reports/m4-fps-native/fixture-preparation-r1/report.json','e1c8294fe6159fda81a3000bbb1fdb481ccc21242a3b180d851137bdb288becc');fb=receipt(R/'reports/m4-fps-native/fixture-build-r1/build.json','fac59936840dcb9f79bc980e2a7dd439f013117f1d4a98a64e587a114de4c8c7');sp=receipt(R/'reports/m4-fps-native/service-preparation-r2/report.json','d3afbd1f20d9a286a0ae8565554845f897c4d7a051d60110bb64912fa15d77c2')
 for d in(cp,cb,fp,fb,sp):
  for p,h in d['files'].items():pin(p,h)
 tool=pin(R/'tools/m4-tree-review/amd64_coff.py');s=importlib.util.spec_from_file_location('fps_author_coff',tool);C=importlib.util.module_from_spec(s);s.loader.exec_module(C)
 functions=[];relocations=[];actual_commands=[]
 for level in('O0','O2'):
  leveldir=R/'reports/m4-fps-native/fixture-build-r1'/level
  objects=[leveldir/'fixture.obj',leveldir/'registry.obj',*[Path(v['path'])for v in cb['levels'][level]['objects']]]
  for p in objects:
   symbols,sections=C.parse(pin(p).read_bytes())
   for symbol in symbols.values():
    n=symbol['name']
    if symbol['section']<=0 or symbol['type']!=32:continue
    selected=(n=='main' or n.startswith(('?initialize_current_caller@','?whole_current_game@','?borrow_widget_onexit@')) or '@AcceptedServices@'in n or p.name=='component.obj'and('@Impl@Component@m4_widget_native@mw34@@'in n or '@Component@m4_widget_native@mw34@@'in n or '@literal@m4_widget_native@mw34@@'in n or n.startswith('mw34_widget_')) or n.startswith('mw34_widget_game_')and n.endswith('_body'))
    if not selected:continue
    raw,rels=C.function(symbols,sections,n)
    functions.append(dict(level=level,object=str(p),object_sha256=sha(p),symbol=n,bytes=len(raw),bytes_sha256=hashlib.sha256(raw).hexdigest(),relocation_count=len(rels)))
    for v in rels:
     if v['type']not in range(4,10):
      t=v['symbol'];relocations.append(dict(level=level,object=str(p),function=n,offset=v['offset'],type=v['type'],target=t['name'],target_section=t['section'],target_value=t['value'],kind='typed COFF SECREL TLS offset'if v['type']==11 else'other typed relocation',source_DWORD=struct.unpack_from('<I',raw,v['offset'])[0]))
  defs=[v for v in functions if v['level']==level]
  bodies=[v for v in defs if v['symbol'].startswith('mw34_widget_game_')and v['symbol'].endswith('_body')]
  need(len(bodies)==58,'Actual58 literal function definitions per level')
  for root in fp['source_roots']:need(any(v['symbol'].startswith('?entry_%x@'%root)for v in defs),'Compiled registered callback for each root')
  commands=[v for v in fb['commands']if str(leveldir)in' '.join(v['argv'])];need(commands and all(v['exit_code']==0 for v in commands),'Actual successful compile/link commands');actual_commands.extend(dict(level=level,command=v)for v in commands)
  need(all(str(p).lower()in{str(x).lower()for x in next(v for v in commands if v.get('expanded_response_arguments'))['expanded_response_arguments']}for p in fp['levels'][level]['objects']),'Every427 inherited actual final link input')
  need(all(v['type']==11 for v in relocations if v['level']==level),'Every selected non-REL32 relocation remains typed TLS SECREL; no absolute-target pretense')
 q=out/'actual-source-function-relocation-map.json';q.write_text(json.dumps(dict(functions=functions,non_REL32_relocations=relocations,actual_commands=actual_commands),indent=2)+'\n');pin(q)
 for p in(R/'tools/m4-fps-native/fixture_v1.cpp',R/'tools/m4-fps-native/component_v1.cpp',R/'tools/m4-fps-native/fixture-source-relations.json',R/'tools/m4-fps-native/component-source-relations.json',R/'tools/m4-fps-native/run_fixture.py',Path(__file__)):pin(p)
 report=dict(passed=True,scope='Author-side actual source/function/typed relocation inventory only; independent linked attribution and writer admission remain required',preparation_sha256=sha(R/'reports/m4-fps-native/fixture-preparation-r1/report.json'),build_sha256=sha(R/'reports/m4-fps-native/fixture-build-r1/build.json'),current_root_count=7,current_literal_bodies=58,declared_controller_worker_routes=14,actual_named_provider='Gdi32 GetStockObject/DeleteObject/CreateFontA',source_vsprintf_provider='Literal780230DD and _output7800FC9B through exact readonly index0→7800FE25',source_vsprintf_import=dict(CALL=0x5a2f68,IAT=0x5bb53c,target=0x780230dd,return_PC=0x5a2f6e),format_destination_instance_offset=0x34,format_frame_root_ESP_offset=-140,format_va_root_ESP_offset=-108,format_record_bytes=2528,compiled_functions_inventory=len(functions),typed_non_REL32_relocations=len(relocations),actual_worker_launches=0,archive_reader_opened=False,AFTER_or_original_CPU_or_handle_seed=False,host_vsprintf=False,source_shutdown_callbacks_modeled=False,independent_linked_attribution=False,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),passed=True,functions=len(functions),non_REL32_relocations=len(relocations))))
if __name__=='__main__':main(sys.argv[1])
