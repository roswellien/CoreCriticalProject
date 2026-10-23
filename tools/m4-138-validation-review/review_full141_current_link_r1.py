"""Inherited complete link gates plus exact current constructor functions."""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,sys,traceback,copy
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];O=R/'reports/m4-138-validation-review/full141-current-link-review-r1'
assert not O.exists();O.mkdir();pins={};counts=collections.Counter();links=[];passed=False
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or v==h,(str(p),h,v);pins[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def load(p,n):
 s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
try:
 source=read(R/'reports/m4-138-validation-review/full141-source-delta-review-r5/report.json','ad41a14303e37bc6fc4ab1cdf5878ad1adf61d3ee8443409aef5705205f42200');assert source['passed']and not source['selected_relation_metadata_correction_pending']
 p=read(R/'reports/m4-startup141-runway/preparation-r2/report.json','92b9ef5628be17e61070a3570d6faf8c0ff3235b1087210ed58a279e135f572c');b=read(R/'reports/m4-startup141-runway/build-r2/build.json','0c00c2fe8857e9785043c6946920287644521efafe4830a75787f1f6b26f6032');parent=read(p['parent_preparation'],p['parent_preparation_sha256'])
 a=read(R/'reports/m4-joint-startup138/admission-map-r3/report.json','e336c6a57bf1e84ec5146e9eb4c70079032df65b277b048dee79348da0300841');newroots=[x['root']for x in a['root_phase_map']]
 ctor=read(R/'reports/m4-138-validation-review/constructor-native37-prelaunch-r3/report.json','0812e8221ce134d74b4d872d379e7af24009679dabf533b0420bd72043c5e3a2');prior_constructor_symbols={level:{x['symbol']for x in ctor['whole_linked_functions']if x['level']==level and Path(x['object']).name!='native_main.cpp.obj'}for level in('O0','O2')}
 for rec in(source,p,b,ctor):
  for q,h in rec['files'].items():pin(q,h)
 for level,info in a['levels'].items():
  w=b['workers'][level];info['worker']=w['path'];info['worker_sha256']=w['sha256'];info['actual_CMake_objects']=[str(q)for q in Path(w['path']).parent.rglob('*.obj')if q.name!='main.obj'];info['actual_compiler_headers']=w['compiler_dependencies'];info['forced_registry_header']=str(R/'reports/m4-startup141-runway/preparation-r2'/level/'registry_build_bindings.hpp');info['widget_binding_header']=str(R/'reports/m4-startup141-runway/preparation-r2'/level/'widget_build_bindings.hpp');info['constructor_library']=p['constructor_libraries'][level];info['constructor_objects']=[str(q)for q in Path(info['constructor_library']).parent.glob('*.obj')]
 C=load(R/'tools/m4-tree-review/amd64_coff.py','joint138_coff');PE=load(R/'tools/m4-tree-review/review_mfc1168_native_prelaunch_v4.py','joint138_image');N=load(R/'tools/m4-tree-review/review_hypot_c1_controls_prelaunch_v2.py','joint138_directories')
 for level,info in a['levels'].items():
  image=PE.AMD64Image(pin(info['worker'],info['worker_sha256']).read_bytes());definitions={}
  parent_objects=[pin(q)for q in info['parent_literal_objects']];assert len(parent_objects)==410 and list(map(str,parent_objects))==list(map(lambda q:str(Path(q).resolve()),parent['objects'][level]))
  widgets=[pin(q['path'],q['sha256'])for q in info['widget_objects']];assert len(widgets)==60
  constructors=[pin(q)for q in info['constructor_objects']];assert len(constructors)==35
  objects=parent_objects+widgets+constructors+[pin(q)for q in info['actual_CMake_objects']if Path(q).name!='main.obj']+[pin(R/'reports/m4-startup141-runway/build-r2/connected_hardware_boundary.obj')]
  for q in objects:
   sy,se=C.parse(q.read_bytes());is_literal=q in parent_objects or q in widgets+constructors and q.name not in ('component.obj','native_api.obj')
   for s in sy.values():
    n=s['name']
    if q.name in ('native_api.obj','connected_hardware_boundary.obj')and n in ('mw34_widget_native_api','mw34_widget_hardware_call','mfc_connected_hardware_call','mw34_constructor_hardware_call'):assert s['type']in(0,32);s['type']=32
    if q.name in ('native_api.obj','connected_hardware_boundary.obj'):
     for label in sy.values():
      if label['name']in('mw34_widget_native_api','mw34_widget_hardware_call','mfc_connected_hardware_call','mw34_constructor_hardware_call')and label['section']>0:assert label['type']in(0,32);label['type']=32
    if s['section']<=0 or s['type']!=32:continue
    selected_function=(is_literal and n.startswith(('sub_','mw34_'))and not n.startswith('__remill'))or n in ('mw34_widget_native_api','mw34_widget_hardware_call','mfc_connected_hardware_call','mw34_constructor_hardware_call','mfc_connected_invoke_guarded','mw34_widget_invoke_guarded')or(q.name=='native_main.cpp.obj'and(n=='main'or '@Context@m4_mixed@mw34@@'in n and not n.startswith('??$')or '@AcceptedWidgetServices@@'in n and not n.startswith('??$')or n.startswith(('?map_current_formatter_sources','?widget_whole_checkpoint','?growth_and_cleanup'))))or(q.name=='component.obj'and(n.startswith('mw34_widget_')or '@Component@m4_widget_native@mw34@@'in n and not n.startswith(('??$','?size@','?data@'))))or n.startswith('?borrow_widget_onexit@')or 'observe_gdi_identity'in n or n.startswith('?provider_identity@')
    selected_function=selected_function or n in prior_constructor_symbols[level] or n.startswith('?constructor_entry@Context@')
    if not selected_function:continue
    raw,rels=C.function(sy,se,n)
    assert n not in definitions,(level,n,str(q))
    definitions[n]=(q,raw,rels,se)
  candidates={}
  for n,(q,raw,rels,se)in definitions.items():
   assert all(4<=x['type']<=9 or x['type']==11 and (x['symbol']['section']>0 or x['symbol']['name']=='_Init_thread_epoch' and x['symbol']['section']==0) for x in rels),(level,n,[(x['type'],x['symbol']['name'])for x in rels])
   matches=C.linked_candidates(image,raw,[dict(x,type=4)for x in rels]);assert matches,(level,n,len(raw));candidates[n]=matches
  for n,(q,raw,rels,se)in definitions.items():
   matches=candidates[n]
   for x in rels:
    target=x['symbol']['name']
    if 4<=x['type']<=9 and target in candidates:
     dest={a for a,_ in candidates[target]};matches=[(a,z)for a,z in matches if a+x['offset']+4+x['type']-4+struct.unpack_from('<i',z,x['offset'])[0]in dest];assert matches,(level,n,target);counts['exact_current_linked_targets']+=1
   for address,actual in matches:
    for x in rels:
     if x['type']!=11:continue
     sym=x['symbol']
     if sym['section']==0:
      assert sym['name']=='_Init_thread_epoch' and sym['value']==0
      epoch=pin(Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/crt/src/vcruntime/thread_safe_statics.cpp')).read_text()
      assert 'static int const epoch_start = INT_MIN;'in epoch and '__declspec(thread) int _Init_thread_epoch = epoch_start;'in epoch
      offset=struct.unpack_from('<i',actual,x['offset'])[0]-struct.unpack_from('<i',raw,x['offset'])[0]
      d=N.directories(image)[9];start,end,_,_,zero,_=struct.unpack('<4Q2I',N.image_bytes(image,image.image_base+d[0],40))
      assert offset>=0 and offset+4<=end-start+zero and N.image_bytes(image,start+offset,4)==struct.pack('<I',0x80000000)
      counts['actual_compiler_thread_epoch_TLS_cells']+=1
      continue
     assert se[sym['section']]['bytes'][sym['value']:sym['value']+8]==bytes(8)
     offset=struct.unpack_from('<i',actual,x['offset'])[0]-struct.unpack_from('<i',raw,x['offset'])[0]-sym['value']
     d=N.directories(image)[9];start,end,_,_,zero,_=struct.unpack('<4Q2I',N.image_bytes(image,image.image_base+d[0],40))
     assert offset>=0 and offset+sym['value']+8<=end-start+zero and N.image_bytes(image,start+offset+sym['value'],8)==bytes(8);counts['actual_initialized_current_TLS_relations']+=1
   candidates[n]=matches
   links.append(dict(level=level,object=str(q),symbol=n,whole_bytes=len(raw),source_sha256=hashlib.sha256(raw).hexdigest(),addresses=[a for a,_ in matches]));counts['whole_linked_current_functions']+=1
  assert len([n for n in definitions if re.fullmatch('mw34_constructor_game_f_[0-9a-f]+_body',n)])==33
  for marker in ('?constructor_entry@Context@','?borrow_entry@Component@m4_constructor_native@'):
   assert any(n.startswith(marker)for n in definitions),(level,marker)
  literals=[n for n in definitions if re.fullmatch('mw34_widget_game_f_[0-9a-f]+_body',n)];assert len(literals)==58
  for root in newroots:assert any(n.startswith('?entry_%x@'%root)for n in definitions)
  for marker in ('?widget_entry@Context@','?invoke_selected_body@Context@','?cleanup_widgets@Context@','?context_fault@Component@','?authority@AcceptedWidgetServices@','?cleanup_authority@AcceptedWidgetServices@','?borrow_widget_onexit@SessionImpl@'):
   assert any(n.startswith(marker)for n in definitions),(level,marker)
  # Current complete unwind attribution for unchanged assembly wrappers.
  for n in ('mw34_widget_native_api','mw34_widget_hardware_call','mfc_connected_hardware_call','mw34_constructor_hardware_call'):
   q,raw,rels,sections=definitions[n];assert len(candidates[n])==1
   sy,se=C.parse(q.read_bytes());d=N.directories(image)[3];entries=list(struct.iter_unpack('<3I',N.image_bytes(image,image.image_base+d[0],d[1])))
   address=candidates[n][0][0];actual=[e for e in entries if image.image_base+e[0]==address];assert len(actual)==1 and image.image_base+actual[0][1]==address+len(raw)
   pdata=se[5]['bytes'];records=list(struct.iter_unpack('<3I',pdata));labels=[s for s in sy.values()if s['name']==n];assert len(labels)==1;u=[e for e in records if e[0]==labels[0]['value']];assert len(u)==1
   offset=u[0][2];data=se[4]['bytes'];next_offsets=[e[2]for e in records if e[2]>offset];end=min(next_offsets,default=len(data));assert N.image_bytes(image,image.image_base+actual[0][2],end-offset)==data[offset:end]
   counts['whole_current_ASM_unwind_relations']+=1
  # Literal archive member provenance is byte exact, not a basename assertion.
  library=pin(info['widget_library'],info['widget_library_sha256']).read_bytes();assert library.startswith(b'!<arch>\n');at=8;member_hashes=[]
  while at<len(library):
   hdr=library[at:at+60];assert len(hdr)==60 and hdr[-2:]==b'`\n';size=int(hdr[48:58]);body=library[at+60:at+60+size];assert len(body)==size
   if hdr[:16].strip()not in (b'/',b'//'):member_hashes.append(hashlib.sha256(body).hexdigest())
   at+=60+size+(size&1)
  assert at==len(library)and collections.Counter(member_hashes)==collections.Counter(pins[str(q)]for q in widgets)
  counts['whole_static_library_object_relations']+=60
  library=pin(info['constructor_library']).read_bytes();assert library.startswith(b'!<arch>\n');at=8;member_hashes=[]
  while at<len(library):
   hdr=library[at:at+60];assert len(hdr)==60 and hdr[-2:]==b'`\n';size=int(hdr[48:58]);body=library[at+60:at+60+size];assert len(body)==size
   if hdr[:16].strip()not in(b'/',b'//'):member_hashes.append(hashlib.sha256(body).hexdigest())
   at+=60+size+(size&1)
  assert at==len(library)and collections.Counter(member_hashes)==collections.Counter(pins[str(q)]for q in constructors)
  counts['whole_constructor_static_library_object_relations']+=35
  for h in info['actual_compiler_headers']:assert str(pin(h))in b['files'];counts['current_consumed_header_paths']+=1
  assert str(pin(info['forced_registry_header']))in info['actual_compiler_headers']and str(pin(info['widget_binding_header']))in info['actual_compiler_headers']
  tree=Path(info['worker']).parent
  ninja=pin(tree/'build.ninja').read_text()
  lines=ninja.splitlines();rows=[x for x in lines if x.startswith('build mw34_joint_startup141.exe:')]
  assert len(rows)==1 and ': CXX_EXECUTABLE_LINKER__mw34_joint_startup141_Release 'in rows[0]
  actual=rows[0].replace('$:',':').split()
  assert all(str(q)in actual for q in parent_objects)
  libraries=[x for x in lines if x.startswith('  LINK_LIBRARIES = ')];assert len(libraries)==1 and info['widget_library']in libraries[0].split()and info['constructor_library']in libraries[0].split()
  builds=[x for x in b['commands']if '--build'in x['arguments']and str(tree)in x['arguments']];assert len(builds)==1 and builds[0]['exit_code']==0
  deps=[x for x in b['commands']if '-t'in x['arguments']and 'deps'in x['arguments']and str(tree)in x['arguments']];assert len(deps)==1 and deps[0]['exit_code']==0
  pin(tree/'.ninja_log');pin(tree/'.ninja_deps')
  counts['current_inherited_literal_inputs']+=410
  print(json.dumps(dict(level=level,whole_functions=len(definitions))),flush=True)
 passed=True
except BaseException:
 (O/'failure.txt').write_text(traceback.format_exc());raise
finally:
 pin(Path(__file__));d=dict(passed=passed,scope='Independent current141 inherited whole function/target/TLS/library/compiler/unwind gates extended to admitted constructor function inventory',preparation_sha256=hashlib.sha256((R/'reports/m4-startup141-runway/preparation-r2/report.json').read_bytes()).hexdigest(),build_sha256=hashlib.sha256((R/'reports/m4-startup141-runway/build-r2/build.json').read_bytes()).hexdigest(),counts=dict(counts),whole_linked_functions=links,archive_reader_opened=False,actual_worker_launches=0,initializer_credit=0,execution_admitted=False,current141_acceptance=False,files=pins)
 q=O/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,report=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest())))
