"""Independent physical admission for the bounded4AF240 observation fixture."""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PH='dfca62ad2dbae9045fc034a5fa3770606451b524fcfe31ce46f73792dcb5f62c'
BH='55a9c4b17f1413263607bf55fd30d722a63b6dcd4b56ce4caf3ccdb8472a0b45'
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir();pins={};counts=collections.Counter();links=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip')
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or v==h,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h=None):
  d=json.loads(pin(p,h).read_bytes());assert d['passed']
  for p,h in d['files'].items():pin(p,h)
  return d
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  base=R/'reports/m4-version-source';prepdir=base/'fixture-preparation-r2';compdir=base/'component-preparation-r2';service=base/'service-preparation-r4'
  p=read(prepdir/'report.json',PH);b=read(base/'fixture-build-r1/build.json',BH)
  c=read(compdir/'report.json','1143e3cef914a5582e93231a810dfd32cc0eabd94534ccaa7025045b0964ed4d');cb=read(base/'component-build-r2/build.json','3bca59f305044aa480117626ecd3718acb64694b5578ec88a87671a794284b52')
  sp=read(service/'report.json','f35a730b53c0299e42d0955a89d29ce2e3289569f5a47fbad538344f55a0dbc5');sb=read(base/'service-build-r4/build.json','9c9426e2e70b24c6b71ae102581c625a155ccc61acecc0c914dcc065904ea133')
  read(R/'reports/m4-tree-review/widget6-prelaunch-r9/report.json','7bdd78f7db9e775dfa59a3aca1410ef750144ac1f21e9e8ec9057db7454ed42b')
  assert b['preparation_sha256']==PH and p['root']==0x4af240 and p['literal_bodies']==10 and p['worker_cwd']==str(R/'MW3')
  assert not p['original_CPU_or_output_seeds']and not p['AFTER_machine_seed']and not p['native_executed']and not b['native_executed']
  assert len(c['namespace_relations'])==10
  for x in c['namespace_relations']:
   before=pin(x['original_IR'],x['original_sha256']).read_bytes();after=pin(x['component_IR'],x['component_sha256']).read_bytes();assert before.replace(b'mw34_onexit_game_',b'mw34_version_game_')==after;counts['whole_namespace_only_IR_relations']+=1
  for row in sp['source_relations']:
   a=pin(row['parent'],row['parent_sha256']).read_bytes();z=pin(row['child'],row['child_sha256']).read_bytes()
   if row['unchanged']:assert a==z;counts['whole_retained_service_sources']+=1
   else:assert Path(row['child']).name in ('session.hpp','session_impl.inc');counts['explicit_extended_service_sources']+=1
  assert counts['whole_retained_service_sources']==70 and counts['explicit_extended_service_sources']==2
  api=pin(service/'session_impl.inc').read_text();helper=pin(service/'native_version_api.hpp').read_text();component=pin(compdir/'component.cpp').read_text();fixture=pin(prepdir/'fixture.cpp').read_text()
  # The actual output ledger is observational. No API success or returned
  # resource size is authored into the guest State or buffer.
  for token in ['const auto source_error=errors.saved','SetLastError(source_error);const auto error_before=GetLastError();mw34_version_native_api(provider,args.data(),&rec.hardware);const auto error_after=GetLastError();','native_pointer-native_base<buffer.requested&&length<=buffer.requested-(native_pointer-native_base)','guest==r.memory().load<unsigned>({0x60b19c})','a->requested==bytes','guest==a->expected','binding->expected_store(a->guest+off,after.data()+off,n)','site==0x4af11a','site==0x4af1a8','ret==site+5','s.gpr.rip.dword==projected','r.memory().load<unsigned>({slot})==raw','case 0x4af240:callback=0x4af270;break;']:
   assert token in api,token
  for token in ['GetProcAddress(primary,name)==target','MEM_COMMIT','MEM_IMAGE','a+64<=start+region.RegionSize','v.primary_sha=m4::sha256','v.owner_sha=m4::sha256','info.nFileSizeLow==m4::admitted_image_size','v.sha==m4::admitted_image_hash']:assert token in helper,token
  for token in ['source_ROOT__never_used','set_fake_API_return']:assert token not in api
  assert fixture.count('version_initialize(r);')==1 and fixture.count('registry.bootstrap();')==1 and fixture.count('component.execute(hardware)')==1 and fixture.index('component.execute(hardware)')<fixture.index('registry.finish()')
  assert 'version_initialize(r)'not in component and 'AFTER'not in fixture
  for token in ['word(0x9a17f0)==UINT32_MAX','session.borrow_version_mfc(s,f.site,f.frame,f.ret)','session.borrow_version_api(s,f.site,f.frame,f.ret)','session.borrow_widget_onexit(s,0x4af240,f.frame,f.ret)','frames.empty()&&s.gpr.rip.dword==root_return&&s.gpr.rsp.dword==root_frame+4']:assert token in component,token
  S=load(R/'tools/analysis/pe.py','version_source_pe');game=S.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  def physical(address,size):return game.read(game.rva_range(address-game.image_base,size)[0],size)
  literals=pin(compdir/'literals.hpp').read_text();rows=re.findall(r'\{(\d+),(\d+),(true|false),(true|false),\{([0-9,]+)\}\}',literals);assert len(rows)==132
  for address,size,call,ret,values in rows:
   raw=bytes(int(x)for x in values.split(','));assert len(raw)==int(size)and physical(int(address),int(size))==raw;counts['complete_physical_literal_rows']+=1
  binding=pin(prepdir/'version_binding.hpp').read_text();match=re.search(r'version_binding\{(\d+),"([a-f0-9]+)"',binding);assert match and int(match[1])==46 and hashlib.sha256(physical(0x4af240,46)).hexdigest()==match[2]
  for pc,thunk,slot,raw in [(0x4af10e,0x4eac9c,0x5bb748,0x1de90c),(0x4af12c,0x4eac96,0x5bb74c,0x1de8f6),(0x4af167,0x4eac90,0x5bb750,0x1de8e4)]:
   call=physical(pc,5);assert call[0]==0xe8 and pc+5+struct.unpack_from('<i',call,1)[0]==thunk and physical(thunk,6)==b'\xff\x25'+struct.pack('<I',slot)and physical(slot,4)==struct.pack('<I',raw);counts['physical_direct_CALL_thunk_owning_IAT']+=1
  C=load(R/'tools/m4-tree-review/amd64_coff.py','version_coff');PE=load(R/'tools/m4-tree-review/review_mfc1168_native_prelaunch_v4.py','version_image');N=load(R/'tools/m4-tree-review/review_hypot_c1_controls_prelaunch_v2.py','version_directories')
  for level,worker in b['workers'].items():
   image=PE.AMD64Image(pin(worker['path'],worker['sha256']).read_bytes());objects=[pin(q['path'],q['sha256'])for q in cb['levels'][level]['objects']]+[pin(sb['levels'][level]['object'],sb['levels'][level]['object_sha256']),pin(sb['levels'][level]['actual_native_assembly'],sb['levels'][level]['actual_native_assembly_sha256']),pin(Path(worker['path']).parent/'fixture.obj')];definitions={}
   for q in objects:
    sy,se=C.parse(q.read_bytes())
    for s in sy.values():
     n=s['name']
     if q.name in('caller_hardware.obj','native_version_api.obj')and n in('mw34_version_hardware_call','mw34_version_native_api'):assert s['type']==0;s['type']=32
     if s['section']<=0 or s['type']!=32:continue
     selected=n.startswith('mw34_version_')or '@Component@m4_version_native@mw34@@'in n and not n.startswith('??$')or n=='main'or n.startswith(('?version_initialize@','?version_whole@','?borrow_version_','?commit_version_buffer@','?borrow_widget_onexit@'))or '@m4_version_api@mw34@@'in n and not n.startswith('??$')
     if not selected:continue
     assert n not in definitions,(n,q);raw,rels=C.function(sy,se,n);definitions[n]=(q,raw,rels,se)
   candidates={}
   for n,(q,raw,rels,se)in definitions.items():
    assert all(4<=x['type']<=9 or x['type']==11 and x['symbol']['section']>0 for x in rels),(level,n)
    matches=C.linked_candidates(image,raw,[dict(x,type=4)for x in rels]);assert matches,(level,n,len(raw));candidates[n]=matches
   for n,(q,raw,rels,se)in definitions.items():
    matches=candidates[n]
    for x in rels:
     target=x['symbol']['name']
     if 4<=x['type']<=9 and target in candidates:
      dest={a for a,_ in candidates[target]};matches=[(a,z)for a,z in matches if a+x['offset']+4+x['type']-4+struct.unpack_from('<i',z,x['offset'])[0]in dest];assert matches,(level,n,target);counts['actual_complete_linked_relations']+=1
    for address,actual in matches:
     for x in rels:
      if x['type']!=11:continue
      sym=x['symbol'];assert se[sym['section']]['bytes'][sym['value']:sym['value']+8]==bytes(8);offset=struct.unpack_from('<i',actual,x['offset'])[0]-struct.unpack_from('<i',raw,x['offset'])[0]-sym['value'];d=N.directories(image)[9];start,end,_,_,zero,_=struct.unpack('<4Q2I',N.image_bytes(image,image.image_base+d[0],40));assert offset>=0 and offset+sym['value']+8<=end-start+zero and N.image_bytes(image,start+offset+sym['value'],8)==bytes(8);counts['actual_initialized_TLS_cells']+=1
    links.append(dict(level=level,object=str(q),symbol=n,whole_bytes=len(raw),source_sha256=hashlib.sha256(raw).hexdigest(),addresses=[a for a,_ in matches]));counts['whole_linked_current_functions']+=1
   assert len([n for n in definitions if re.fullmatch('mw34_version_game_f_[a-f0-9]+_body',n)])==10
   for prefix in ('?borrow_version_mfc@SessionImpl@','?borrow_version_buffer@SessionImpl@','?commit_version_buffer@SessionImpl@','?borrow_version_api@SessionImpl@','?invoke@Impl@Component@'):
    assert any(n.startswith(prefix)for n in definitions),(level,prefix)
   # Independently join both genuine native hardware ASM functions and unwind.
   for q,n in[(objects[-2],'mw34_version_native_api'),(next(q for q in objects if q.name=='caller_hardware.obj'),'mw34_version_hardware_call')]:
    sy,se=C.parse(q.read_bytes());rows=[s for s in sy.values()if s['name']==n];assert len(rows)==1 and rows[0]['section']==1 and rows[0]['value']==0;raw=se[1]['bytes'];assert len(candidates[n])==1;address=candidates[n][0][0];d=N.directories(image)[3];entries=list(struct.iter_unpack('<3I',N.image_bytes(image,image.image_base+d[0],d[1])));actual=[e for e in entries if image.image_base+e[0]==address];assert len(actual)==1 and image.image_base+actual[0][1]==address+len(raw);unwind=se[4]['bytes'];assert N.image_bytes(image,image.image_base+actual[0][2],len(unwind))==unwind;counts['whole_native_ASM_unwind_relations']+=1
   commands=[x for x in b['commands']if x.get('expanded_response_arguments')and str(Path(worker['path']).parent)in' '.join(x['argv'])];assert len(commands)==1 and commands[0]['exit_code']==0;args={str(Path(x)).resolve().as_posix().casefold()for x in commands[0]['expanded_response_arguments']if not x.startswith('/')}
   for q in p['levels'][level]['objects']+[p['levels'][level]['component_library'],p['levels'][level]['service_library']]:assert Path(q).resolve().as_posix().casefold()in args
   counts['current_linker_selected_fixed_objects']+=427
   for q in worker['actual_compiler_header_dependencies']:assert str(pin(q))in b['files'];counts['current_compiler_header_paths']+=1
   assert str(pin(sb['levels'][level]['forced_registry_header']))in sb['levels'][level]['actual_header_dependencies']
   print(json.dumps(dict(level=level,whole_functions=len(definitions))),flush=True)
  pin(__file__);pin(sys.executable);pin(R/'tools/m4-version-source/run_fixture_v1.py')
  for q,h in pins.items():pin(q,h)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  q=out/'physical-links.json';q.write_text(json.dumps(links,indent=2)+'\n');pin(q);d=dict(passed=passed,scope='Bounded sole4AF240 native observation admission with actual named VERSION APIs, same-owner requested buffer alias, genuine source allocator frames and physical linked compiler/ASM provenance; original comparison and connected startup credit remain open',build_sha256=BH,preparation_sha256=PH,counts=dict(counts),actual_worker_launches=0,archive_reader_opened=False,initializer_credit=0,original_equivalence=False,carried_prefix_equivalence=False,files=pins);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=hashlib.sha256(q.read_bytes()).hexdigest(),counts=dict(counts),files=len(pins))))
if __name__=='__main__':main(sys.argv[1])
