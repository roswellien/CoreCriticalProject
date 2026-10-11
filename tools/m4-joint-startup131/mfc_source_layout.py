"""Independent cached1168 extension for the single persistent131 source reader.

All new loader storage comes from the sealed chronological original BEFORE.
The pure literal phase receives the persistent computed machine, never a
candidate phase snapshot. Native observations are equality targets only.
"""
from pathlib import Path
import collections, hashlib, importlib.util, json, struct, sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]

def need(v, label):
 if not v: raise ValueError(label)
def eq(a, b, label): need(a == b, label + ' ' + str((a, b))[:400])
def module(path, name, pin):
 spec = importlib.util.spec_from_file_location(name, pin(path)); result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result

class Extension:
 def __init__(self, preparation, pin):
  self.pin = pin; self.inputs = preparation['inputs']; self.counts = collections.Counter(); self.rows = []; self.resources = []; self.identities = []; self.proofs = {}
  self.literal = module(ROOT/'tools/m4-mfc1168-native/persistent_source.py', 'joint131_mfc_literal', pin)
  self.physical = module(ROOT/'tools/m4-mfc1168-native/verify_resource_fixture.py', 'joint131_mfc_native_owners', pin)
  self.physical.PINS = {}  # Every physical file is joined to the outer pins below.
  self.pe = module(ROOT/'tools/analysis/pe.py', 'joint131_mfc_source_pe', pin)
  contracts = ROOT/'reports/m4-mfc1168-probe/native-contracts-r1/contracts.json'
  self.contracts = json.loads(pin(contracts, 'f7db9805f43e1eb7ef84ad8adb5ddb0f788b76844dbaadb736329787a410eb64').read_bytes())
  receipt = json.loads(pin(preparation['chronological_original'], self.inputs['original_prefix_receipt_sha256']).read_bytes())
  need(receipt['passed'], 'Genuine chronological original input passed')
  source = json.loads(pin(preparation['chronological_source'], self.inputs['source_domain_receipt_sha256']).read_bytes()); need(source['passed'] and not source['source_AFTER_seed'], 'Independent chronological literal source proof')
  self.normal_PCs = json.loads(pin(Path(preparation['chronological_source']).parent/'source-derivations.json').read_bytes())['source_PCs']
  retained = json.loads(pin(Path(preparation['chronological_original']).parent/'retained-actual-inputs.json').read_bytes())
  def genuine(key):
   need('/BEFORE/' in key, 'Only genuine chronological BEFORE input'); row = retained[key]; b = pin(row['path'], row['sha256']).read_bytes(); eq(len(b), row['bytes'], 'Complete genuine source backing'); return b
  self.new = {0x5f4cb000: bytearray(genuine('MFC1168/BEFORE/MFC/'+str(0x5f4cb000)+'.bin')), self.inputs['guest_CS']: bytearray(genuine('MFC1168/BEFORE/CRT-codepage-lock/bytes.bin'))}
  for o in self.inputs['role_owners']: self.new[o['new']] = bytearray(genuine('MFC1168/BEFORE/domain/'+o['role']+'/bytes.bin')); eq(len(self.new[o['new']]), o['extent'], 'Whole declared source role')
  mirror = 0x7ffdee1c; self.new[mirror] = bytearray(struct.pack('<I', self.inputs['pointer_cells'][3]['before']))
  for cell in self.inputs['pointer_cells']:
   owners = [(a, b) for a, b in self.new.items() if a <= cell['address'] and cell['address']+4 <= a+len(b)]; eq(len(owners), 1, 'Exactly one new typed pointer cell owner'); a, b = owners[0]; eq(struct.unpack_from('<I', b, cell['address']-a)[0], cell['before'], 'Genuine full backing pointer preimage'); struct.pack_into('<I', b, cell['address']-a, cell['projected'])
  self.images = [self.pe.PEImage(pin(ROOT/path, h).read_bytes()) for path, h in [('MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),('local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8'),('local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')]]
  for path in (Path(__file__), ROOT/'tools/m4-mfc1168-native/connected_component_v2.cpp', ROOT/'tools/m4-mfc1168-native/connected_entry.hpp', ROOT/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py', ROOT/'tools/m4-formatting-source/flag_domain.py'): pin(path)
 def page(self, address):
  image = next(im for im in self.images if im.image_base <= address < im.image_base+im.size_of_image); result = bytearray(4096)
  for section in image.sections:
   lo = max(address, image.image_base+section['virtual_address']); hi = min(address+4096, image.image_base+section['virtual_address']+section['raw_size'])
   if lo < hi: offset = section['raw_offset']+lo-image.image_base-section['virtual_address']; result[lo-address:hi-address] = image.data[offset:offset+hi-lo]
  return result
 def loader(self, before):
  """Authenticate declared additions, preserving all existing carried bytes."""
  memory = before['memory']
  for a, b in self.new.items():
   if a in memory: eq(bytes(memory[a]), bytes(b), 'Current bootstrap complete declared source input')
   memory[a] = bytes(b)
  # The current native constructor merges exactly these three cells into the
  # parent's raw CRT page before bootstrap. All other bytes are unchanged.
  expected = self.page(0x78037000)
  for cell in self.inputs['CRT_cells']:
   offset = cell['address']-0x78037000; eq(struct.unpack_from('<I', expected, offset)[0], cell['before'], 'Physical carried CRT cached cell preimage'); struct.pack_into('<I', expected, offset, cell['projected'])
  if 0x78037000 in memory: eq(bytes(memory[0x78037000]), bytes(expected), 'Whole source loader CRT page with only three proved merges')
  memory[0x78037000] = bytes(expected)
  for row in self.contracts['instructions']:
   address = row['pc'] & ~4095
   if address not in memory: memory[address] = bytes(self.page(address))
  for v in self.inputs['imports']:
   address = v['cell'] & ~4095
   if address not in memory: memory[address] = bytes(self.page(address))
   raw = struct.unpack_from('<I', memory[address], v['cell']-address)[0]; eq(raw, v['raw'], 'Unchanged current owning raw IAT value')
  return dict(new_regions=[(a,len(b),hashlib.sha256(b).hexdigest())for a,b in sorted(self.new.items())], CRT_page_sha256=hashlib.sha256(expected).hexdigest(), typed_pointer_cells=self.inputs['pointer_cells'], CRT_cells=self.inputs['CRT_cells'], source_AFTER_seed=False)
 def phase(self, machine, archive, level, sequence, phase):
  stem=f'sequence-{sequence}/MFC/'; cpu=struct.pack('<10I',*machine.projected_cpu()); state=bytes(machine.state); fx=machine.fx
  eq(state,archive.data(stem+'before/State.bin'),'Whole carried MFC source State entry');eq(cpu,archive.data(stem+'before/CPU.bin'),'Whole carried MFC CPU entry');eq(fx,archive.data(stem+'before/FX.bin'),'Whole carried MFC guest FX entry')
  regions = list(struct.iter_unpack('<3I',archive.data(stem+'before/memory/index.bin')))
  expected_regions=[(o['new'],o['extent'],3)for o in self.inputs['role_owners']]+[(0x5f4cb000,4096,3),(self.inputs['guest_CS'],24,3),(0x7ffdee1c,4,3),(0x78037000,4096,3),(0x7ffde000,4,3),(0x7ffde004,8,1),(0x7ffde018,4,1)]
  eq(regions,expected_regions,'Exact twelve whole source input/endpoints')
  for address,size,_ in regions:eq(machine.bytes(address,size),archive.data(stem+f'before/memory/{address}.bin'),'Whole persistent computed MFC BEFORE region')
  original_layout={a:len(b)for a,b in machine.memory.items()};literal_memory=dict(machine.memory);tib_layout=[]
  if 0x7ffde004 in literal_memory and 0x7ffde008 in literal_memory and len(literal_memory[0x7ffde004])==len(literal_memory[0x7ffde008])==4:
   first=machine.bytes(0x7ffde004,4);second=machine.bytes(0x7ffde008,4);joined=first+second
   eq(joined,machine.bytes(0x7ffde004,8),'Exact computed TIB two-DWORD BEFORE join')
   literal_memory[0x7ffde004]=joined;del literal_memory[0x7ffde008]
   tib_layout=[dict(address=0x7ffde004,original_parts=[dict(address=0x7ffde004,bytes=4,BEFORE_hex=first.hex()),dict(address=0x7ffde008,bytes=4,BEFORE_hex=second.hex())],literal_extent=8,joined_BEFORE_hex=joined.hex(),candidate_BEFORE_seed=False)]
  eq({a:bytes(b)for a,b in literal_memory.items()if a not in(0x7ffde004,0x7ffde008)},{a:bytes(b)for a,b in machine.memory.items()if a not in(0x7ffde004,0x7ffde008)},'Every nonTIB pure source BEFORE region unchanged')
  computed, source = self.literal.derive(state, fx, cpu, literal_memory, self.inputs, self.contracts)
  eq(source['source_PCs'],self.normal_PCs,'All142 admitted physical instructions in exact genuine reached order')
  actual=list(struct.iter_unpack('<IIQII',archive.data(stem+'after/accesses.bin')));eq(actual,computed.accesses,'All113 actual source operands independently computed')
  for filename,expected in [('State.bin',bytes(computed.state)),('CPU.bin',struct.pack('<10I',*computed.cpu_now())),('FX.bin',computed.fx)]:eq(expected,archive.data(stem+'after/'+filename),'Entire MFC literal endpoint '+filename)
  eq(archive.data(stem+'after/memory/index.bin'),archive.data(stem+'before/memory/index.bin'),'Same complete input/output region inventory')
  for address,size,_ in regions:eq(computed.bytes(address,size),archive.data(stem+f'after/memory/{address}.bin'),'Entire independently computed MFC region endpoint')
  actual_projects=list(struct.iter_unpack('<6I',archive.data(stem+'after/import-projections.bin')));eq([v[:5]for v in actual_projects],[(v['access_index'],v['PC'],v['cell'],v['raw'],v['projected'])for v in computed.projections],'All7 exact owning raw IAT projections')
  apis=archive.data(stem+'after/APIs.bin');eq(len(apis),4*352,'Four complete typed source API records');actual_APIs=[]
  for i,relation in enumerate(source['source_API_relations']):
   b=apis[352*i:352*(i+1)];w=struct.unpack_from('<16Q',b);spec=relation['spec'];eq(w[:8],(1,i,spec['source_PC'],relation['target'],spec['argc'],relation['CPU_before'][4],spec['return_PC'],relation['typed_result']),'Actual exact typed source call/API identity');eq(struct.unpack_from('<10I',b,128),tuple(relation['CPU_before']),'Entire source-derived API entry CPU40');eq(struct.unpack_from('<10I',b,168),tuple(relation['CPU_after']),'Entire source-derived API return CPU40');eq(b[208:272].hex(),relation['frame64_hex'],'Whole source-derived API frame64');eq(w[12],self.inputs['role_owners'][1]['new'],'Declared guest thread role');eq(w[13],relation['CS_depth_after'],'Source semantic lock depth')
   eq(self.physical.cs(b[272:312]),(relation['CS_depth_before'],w[9]if relation['CS_depth_before']else 0),'Whole native CS40 incoming source relation');eq(self.physical.cs(b[312:352]),(relation['CS_depth_after'],w[9]if relation['CS_depth_after']else 0),'Whole native CS40 outgoing source relation')
   if i==0:eq(w[8],w[11],'Actual TLS lookup returns current native association')
   if i==2:eq(w[8],1252,'Actual finite native GetACP1252')
   actual_APIs.append(dict(words=w,CPU_before_hex=b[128:168].hex(),CPU_after_hex=b[168:208].hex(),frame64_hex=b[208:272].hex(),nativeCS40_before_hex=b[272:312].hex(),nativeCS40_after_hex=b[312:352].hex()))
  # The MFC ledger is separate from the inherited registry provider ledger.
  # Preserve its exact own indices rather than offsetting inherited witnesses.
  machine.state=bytearray(computed.state);machine.fx=computed.fx;machine.cpu=struct.pack('<10I',*computed.cpu_now());machine.cursor=computed.cursor
  # Inverse projection into every original region preserves its exact extent.
  for address,size in original_layout.items():machine.store_bytes(address,computed.bytes(address,size))
  eq({a:len(b)for a,b in machine.memory.items()},original_layout,'Exact original persistent mapped-region layout restored')
  for row in tib_layout:
   row['source_AFTER_parts']=[dict(address=part['address'],bytes=4,source_AFTER_hex=computed.bytes(part['address'],4).hex())for part in row['original_parts']]
   row['source_AFTER_joined_hex']=computed.bytes(row['address'],8).hex();row['persistent_original_layout_restored']=True
  source['TIB_region_representation']=tib_layout
  source.update(level=level,sequence=sequence,phase=phase,actual_API_relations=actual_APIs,whole_regions=regions,inherited_registry_access_indices_unchanged=True)
  self.rows.append(source);self.counts.update(MFC_literal_phases=1,MFC_source_instructions=142,MFC_source_operands=113,MFC_typed_API_CPU_frame_relations=4,MFC_whole_region_BEFORE=12,MFC_whole_region_AFTER=12,MFC_whole_State_CPU_FX=1)
  self.resource(archive,stem,level,sequence)
  return source
 def resource(self,archive,stem,level,sequence):
  virtual=ROOT/'reports/m4-joint-startup131-source'/f'virtual-{level}-{sequence}';V=self.physical;old=V.raw
  def raw(path):
   path=Path(path).resolve()
   return archive.data(stem+path.relative_to(virtual).as_posix())if path.is_relative_to(virtual)else old(path)
  V.raw=raw;events=[];tls=None;association=0;section=None;depth=0;deleted=False;freed=False;thread=None
  try:
   context=archive.words(stem+'cleaned/resource-context.bin',12,'Q');eq(context[2:9],(0,0,0,0,0,113,4),'Actual current MFC resources terminal');eq(context[11],13,'All thirteen actual resource services')
   for serial in range(13):
    base=virtual/'resources'/str(serial);w=struct.unpack('<8Q',raw(base/'call.bin'));eq(w[:2],(1,serial),'Contiguous actual owned service order');kind,a0,a1,result,tid,error=w[2:];thread=tid if thread is None else thread;eq(tid,thread,'One actual owned current thread');identity=V.native_identity(base,kind,self.proofs);pre=raw(base/'CS-before40.bin');post=raw(base/'CS-after40.bin');eq(len(pre),40,'Whole actual native CS40 before');eq(len(post),40,'Whole actual native CS40 after')
    if kind==0:need(tls is None and result!=0xffffffff,'One successful actual TLS allocation');tls=result
    elif kind==1:eq(a0,tls,'Owned TLS set slot');need(not freed and result==1,'Actual live TLS set');association=a1
    elif kind==2:eq(a0,tls,'Owned TLS lookup slot');need(not freed,'Actual TLS lookup within lifetime');eq(result,association,'Actual native current association lookup')
    elif kind==3:eq(a0,tls,'Exact actual TLS release slot');need(not freed and not association and result==1,'Actual clear before TLS release');freed=True
    elif kind==4:need(section is None,'One native CS40 construction');section=a0;eq(V.cs(post),(0,0),'Native CS initialized and unowned')
    elif kind in(5,6):eq(a0,section,'Same actual owned native CS40');need(not deleted,'Native CS service within live lifetime');eq(V.cs(pre),(depth,thread if depth else 0),'Whole source-related CS before');depth+=1 if kind==5 else -1;need(depth in(0,1),'Finite native depth');eq(V.cs(post),(depth,thread if depth else 0),'Whole source-related CS after')
    elif kind==7:eq(a0,section,'Same actual native CS destruction');need(not deleted and not depth,'Native CS unheld at release');deleted=True
    elif kind==8:eq(result,1252,'Finite actual ACP1252');need(depth==1 and not deleted,'Actual query under owned native lock25')
    else:raise ValueError('Unknown native resource service')
    events.append(dict(words=w,CS_before_hex=pre.hex(),CS_after_hex=post.hex()));self.identities.append(dict(level=level,sequence=sequence,serial=serial,kind=kind,call_words=w,proof_identity=[kind,identity['actual_owner'],identity['RVA'],identity['entry64']]))
   eq([r['words'][2]for r in events],[0,2,1,4,2,5,8,6,2,7,1,2,3],'Complete exact current resource/lifecycle order');need(freed and deleted and not depth,'All actual owned MFC resources released');eq(archive.words(stem+'lifecycle.bin',8,'Q'),(1,thread,tls,4,0,1,1,1),'Source/resource lifecycle receipt')
   hardware=archive.data(f'sequence-{sequence}/MFC-caller-hardware.bin');eq(len(hardware),1632,'Three complete actual caller sides');eq(hardware[:512],hardware[1088:1600],'Entire actual caller FX512 restored');eq(hardware[512:540],hardware[1600:1628],'Entire actual caller ENV28 restored')
   self.resources.append(dict(level=level,sequence=sequence,events=events,whole_caller_hardware_hex=hardware.hex(),caller_scope='Complete selected131 invocation including MFC construction/source/release; parent registry construction/growth cleanup outside'))
   self.counts.update(MFC_owned_resource_lifecycles=1,MFC_actual_API_identity_CS40_sides=26,MFC_whole_actual_caller_FX512_ENV28=1)
  finally:V.raw=old
  for path,digest in V.PINS.items():self.pin(path,digest)
