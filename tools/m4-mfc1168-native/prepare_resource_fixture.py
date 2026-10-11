"""Derive reviewed-role relocation and additive resource/control fixture."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;parent=p/'prepare_fixture_v2.py';s=parent.read_text()
s=s.replace("raw(R/'tools/m4-mfc1168-native/fixture_v2.cpp')", "raw(R/'tools/m4-mfc1168-native/fixture_resource.cpp')")
anchor="  pack=bytearray(b'M4MFCNAT'+struct.pack('<I',len(blocks)))"
replacement='''  alias_path=R/'reports/m4-mfc1168-original/alias-domain-review-r1/report.json'
  alias_receipt=read(alias_path,'3347e59191d21bd78046ec2722c3e62706d9580cae382a3edfc00d99325d143d');need(alias_receipt['passed'],'Independent five-role alias policy')
  alias=read(alias_path.parent/'alias-domain.json')
  import copy
  old_contracts=contracts;contracts=copy.deepcopy(contracts)
  map_rows=[dict(role=b['role'],old=b['guest'],new=0x33001000+index*0x1000,extent=b['extent'])for index,b in enumerate(old_contracts['borrowed_backings'])]
  def relocated(address):
   for row in map_rows:
    if row['old']<=address<row['old']+row['extent']:return row['new']+address-row['old']
   return address
  for b in blocks:b['address']=relocated(b['address'])
  rewrites=[]
  for cell in alias['typed_pointer_cells']:
   a=relocated(cell['cell']);target=relocated(cell['target']);matches=[b for b in blocks if b['address']<=a and a+4<=b['address']+b['size']];need(len(matches)==1,'Exactly one current declared pointer cell backing');b=matches[0];offset=a-b['address'];need(struct.unpack_from('<I',b['bytes'],offset)[0]==cell['target'],'Genuine typed pointer cell value before rewrite');value=bytearray(b['bytes']);struct.pack_into('<I',value,offset,target);b['bytes']=bytes(value);rewrites.append(dict(cell=cell['cell'],new_cell=a,role=cell['role'],old_target=cell['target'],new_target=target,scope=cell['scope']))
  need(len(rewrites)==6 and len(map_rows)==5,'Six declared pointer rewrites and five owner roles only')
  for b in contracts['borrowed_backings']:b['guest']=relocated(b['guest'])
  for row in contracts['field_writes']:
   if 'address'in row:row['address']=relocated(row['address'])
  accesses=[(pc,relocated(address),width,writing)for pc,address,width,writing in accesses]
  domain=list(domain);domain[4]=relocated(domain[4]);domain[7]=relocated(domain[7])
  (out/'contracts-relocated.json').write_text(json.dumps(contracts,indent=2)+'\\n')
  (out/'relocation-proof.json').write_text(json.dumps(dict(owners=map_rows,pointer_cells=rewrites,source_index_unchanged=3,complete_genuine_BEFORE_only=True,arbitrary_equal_integer_replacement=False),indent=2)+'\\n')
  pack=bytearray(b'M4MFCNAT'+struct.pack('<I',len(blocks)))'''
assert s.count(anchor)==1;s=s.replace(anchor,replacement)
s=s.replace("  (out/'CMakeLists.txt').write_text(cmake)", "  cmake=cmake.replace('${MW34_OBJECTS})','${MW34_OBJECTS} ${MW34_HARDWARE_OBJECT})')\n  (out/'CMakeLists.txt').write_text(cmake)\n  (out/'resource_witness.hpp').write_bytes(raw(R/'tools/m4-mfc1168-native/resource_witness.hpp'))\n  (out/'hardware_boundary.s').write_bytes(raw(R/'tools/m4-mfc1168-native/hardware_boundary.s'))")
s=s.replace("  for level in('O0','O2'):", '''  spans='struct SourceSpan {unsigned pc,size;std::array<std::byte,16>bytes;};\\ninline constexpr std::array<SourceSpan,142>source_spans{{'+','.join('{'+str(r['pc'])+'U,'+str(r['width'])+'U,{'+','.join('std::byte{'+str(v)+'}'for v in bytes.fromhex(r['bytes_hex']))+'}}'for r in contracts['instructions'])+'}};'
  prefix.append(spans)
  for level in('O0','O2'):''')
s=s.replace("for q in remill.rglob('*.h'):pin(q)", "for q in remill.rglob('*.h'):pin(q)\n  for q in(out/'contracts-relocated.json',out/'relocation-proof.json',out/'resource_witness.hpp',out/'hardware_boundary.s',R/'tools/m4-mfc1168-native/derive_resource_fixture.py',R/'tools/m4-mfc1168-native/prepare_fixture_v2.py'):pin(q)")
s=s.replace("objects=objects if'objects'in locals()else{},", "relocated_contracts=str(out/'contracts-relocated.json'),relocation_proof=str(out/'relocation-proof.json'),alias_review=str(alias_path),alias_review_sha256=sha(alias_path),objects=objects if'objects'in locals()else{},")
s=s.replace("scope='One registered admitted-image cached MFC1168 root; BEFORE-only input and13 literal bodies, compile/execute still pending'", "scope='One registered cached MFC1168 root with five disjoint relocated borrowed roles/six declared BEFORE pointer cells, actual native provider/lifecycle/hardware witnesses and12 finite controls; writer remains pending review'")
exec(compile(s,str(parent),'exec'),globals())
