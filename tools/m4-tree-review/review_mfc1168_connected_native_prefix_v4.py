"""Current connected14 first-writer review, including exact TLS and ASM cells."""
from pathlib import Path
import ast
PREVIOUS=Path(__file__).with_name('review_mfc1168_connected_native_prefix_v3.py')
tree=ast.parse(PREVIOUS.read_text())
values={n.targets[0].id:ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)and n.targets[0].id in('old','new')}
generator=PREVIOUS.with_name('review_mfc1168_connected_native_prefix_v2.py').read_text()
assert generator.count(values['old'])==1
generator=generator.replace(values['old'],values['new'])
helper=r'''
  TLS_names={'?observation@m4_mixed@mw34@@3PEAUNative@12@EA','?active_context@Context@m4_mixed@mw34@@2PEAV123@EA'}
  def linked_candidates(image,raw,relocs):
   assert all(4<=r['type']<=9 or(r['type']==11 and r['symbol']['name']in TLS_names and r['symbol']['section']>0)for r in relocs)
   assert all(0<=r['offset'] and r['offset']+4<=len(raw)for r in relocs)
   # All permitted physical relocations occupy precisely four bytes. This
   # matcher masks those fields only; their kind/target is checked separately.
   return C.linked_candidates(image,raw,[dict(r,type=4)for r in relocs])
  def TLS_relations(image,raw,actual,relocs,sections):
   for row in relocs:
    if row['type']!=11:continue
    sym=row['symbol'];assert sym['value']==0 and sections[sym['section']]['bytes']==bytes(8)
    i=row['offset'];value=struct.unpack_from('<i',actual,i)[0]-struct.unpack_from('<i',raw,i)[0]
    d=N.directories(image)[9];assert d[1]>=40
    start,end,_,_,zero,_=struct.unpack('<4Q2I',N.image_bytes(image,image.image_base+d[0],40))
    assert value>=0 and value+8<=end-start+zero and N.image_bytes(image,start+value,8)==bytes(8)
    links.append(dict(kind='initialized_TLS_SECREL',symbol=sym['name'],section_offset=value,template_start=start,template_end=end,runtime_address_claim=False));counts['actual_compiler_TLS_cells']+=1
'''
extra=r'''
  assert 'const Inputs input;'in component and 'input(i)'in component
  assert 'for(const auto&row:input.new_mappings)observed(row.address,unsigned(row.before.size()),row.permissions)'in component
  assert 'observed(0x78037000,4096,3)'in component
  assert 'mfc_connected_hardware_call(&guarded,mfc_hardware.data())'in main and 'writer.append(prefix+"MFC-caller-hardware.bin"'in main
  asm=pin(folder/'connected_hardware_boundary.s').read_text();historical=pin(R/'tools/m4-mfc1168-native/hardware_boundary.s').read_text()
  assert historical.replace('mfc_hardware_call','mfc_connected_hardware_call').replace('mfc_invoke_guarded','mfc_connected_invoke_guarded')==asm
  boundary=pin(folder/'connected_hardware_boundary.obj');bs,bsec=C.parse(boundary.read_bytes());br,brels=C.function(bs,bsec,'mfc_connected_hardware_call')
  assert br.hex()=='534883ec204889d3480fae03d9b300020000d9a300020000e800000000480fae8320020000d9b320040000d9a320040000480fae0bd9a300020000480fae8340040000d9b340060000d9a3400600004883c4205bc3'
  assert len(brels)==1 and(brels[0]['offset'],brels[0]['type'],brels[0]['symbol']['name'])==(25,4,'mfc_connected_invoke_guarded')
  assert bsec[4]['bytes']==bytes.fromhex('0105020005320130') and bsec[5]['bytes']==struct.pack('<3I',0,85,0)
'''
inside=r'''
   assert str(boundary.resolve()).casefold()in linked
   sy,se=C.parse(blob(bf/'CMakeFiles/mw34_mfc1168_connected.dir/native_main.cpp.obj'))
   wr,wrrels=C.function(sy,se,'mfc_connected_invoke_guarded');wm=linked_candidates(image,wr,wrrels);assert len(wm)==1
   bm=linked_candidates(image,br,brels);assert len(bm)==1;address,actual=bm[0];target=address+29+struct.unpack_from('<i',actual,25)[0];assert target==wm[0][0]
   ex=N.directories(image)[3];table=N.image_bytes(image,image.image_base+ex[0],ex[1]);entries=[struct.unpack_from('<3I',table,i)for i in range(0,len(table),12)]
   uw=[v for v in entries if image.image_base+v[0]==address];assert len(uw)==1 and image.image_base+uw[0][1]==address+85 and N.image_bytes(image,image.image_base+uw[0][2],8)==bsec[4]['bytes']
   links.append(dict(level=level,symbol='mfc_connected_hardware_call',address=address,whole_bytes=85,actual_guarded_target=target,unwind_hex=bsec[4]['bytes'].hex()));counts['whole_hardware_caller_boundaries']+=1
'''
edits=[
 ("'1f8fac0b491ee99e39a966bf2c03e5059e7f541d2d5ed862c9310b8be1b304ba'","'7f426089ae1c974d4e2b5c3e5500efe283d8634a54e6d934a428710fe078d309'"),
 ("'278be74db3998e7396ba46696a59f5e6fbd9acc43f71e0ca1eaedd272822ce4f'","'a7985e57a3a437fe6b19a600507ebeac33dac79ea0bae825b35133095f3f8924'"),
 ("connected-fixture-build-r1/build.json","connected-fixture-build-r2/build.json"),
 ('C.linked_candidates(', 'linked_candidates('),
 ("a+r['offset']+4+struct.unpack_from", "a+r['offset']+4+max(0,r['type']-4)+struct.unpack_from"),
 ("  lift=read(R/'reports/m4-mfc1168-native/lifts-r2/report.json')", "  N=module(R/'tools/m4-tree-review/review_hypot_c1_controls_prelaunch_v2.py','mfc_prefix_boundary')\n"+helper+extra+"  lift=read(R/'reports/m4-mfc1168-native/lifts-r2/report.json')"),
 ("   db=pin(bf/'.ninja_deps')",inside+"   db=pin(bf/'.ninja_deps')"),
 ("     links.append(dict(level=level,symbol=candidates[0]", "     TLS_relations(image,raw,matches[0][1],relocs,sections)\n     links.append(dict(level=level,symbol=candidates[0]"),
 ('whole_new_manager_CRT_TIB_endpoint_observations=False','whole_new_manager_CRT_TIB_endpoint_observations_declared=True'),
 ('Independent first positive connected14 prefix prelaunch only','Independent current connected14 prefix prelaunch with whole added domains and exact hardware boundary'),
 ("  pin(BASE);", "  pin(PREVIOUS);pin(BASE);")
]
injection="\nfor old,new in edits:\n assert old in text,old\n text=text.replace(old,new)\n"
anchor="exec(compile(text,str(BASE),'exec'),globals())"
assert generator.count(anchor)==1
generator=generator.replace(anchor,injection+anchor)
exec(compile(generator,str(PREVIOUS),'exec'),globals())
