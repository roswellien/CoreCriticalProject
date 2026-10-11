"""Publish parameterized finite source contracts without chronological seeds.

No capture archive, source AFTER bytes, registry/input page mutations or worker
execution. The resolved address interface is checked against both independently
compared isolated levels; this does not admit a connected invocation.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader in interface preparation');a=sha(p);need(h is None or a==h,'Exact current physical input '+str(p));need(str(p)not in PINS or PINS[str(p)]==a,'Stable consumed input');PINS[str(p)]=a;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def text(p):return pin(p).read_text()
def main(name):
 out=R/'reports/m4-mfc1168-native'/name;need(not out.exists(),'Fresh interface output');out.mkdir();passed=False;counts=collections.Counter()
 try:
  acceptance=read(R/'reports/m4-joint-startup130-root/acceptance-r1/report.json','12215395619ea72ee1a587763112bc3a2ed9aad15c9c99a5697f69c9658429aa');need(acceptance['passed'],'Accepted parent130')
  joint=read(R/'reports/m4-joint-startup130/preparation-r2/report.json','060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c')
  native=Path(joint['native_include']);parent_sources={n:text(native/n)for n in('session_impl.inc','locale_batch_operations.inc','fs_operations.inc','source_contract.inc','registry_contract.inc','lockit_contract.inc','formatting_contract.inc')}
  gap=read(R/'reports/m4-mfc1168-native/connected-gap-r1/connected-domain-gap.json')
  c=read(R/'reports/m4-mfc1168-probe/native-contracts-r1/contracts.json','f7db9805f43e1eb7ef84ad8adb5ddb0f788b76844dbaadb736329787a410eb64')
  source=read(R/'reports/m4-mfc1168-native/resource-source-r1/report.json','9195e7107ec29ef8ee6b97694b1eae9a9c18aacdfe5a8aa27e5aca4d8f88d2aa');need(source['passed'],'Independent exact isolated source')
  rows=read(Path(R/'reports/m4-mfc1168-native/resource-source-r1/source-derivations.json'))
  alias=read(R/'reports/m4-mfc1168-native/resource-preparation-r3/relocation-proof.json')
  lift=read(R/'reports/m4-mfc1168-native/lifts-r2/report.json','55bb1c8fd59cf11f63ae199e93ea83220fa2cbc15d4d39e388946fc452f4664e')
  original=read(R/'reports/m4-mfc1168-probe/validation-r6/source-derivations.json')
  need(len(rows)==2 and [r['level']for r in rows]==['O0','O2'],'Both original-source-compared native levels')
  need(rows[0]['source_PCs']==rows[1]['source_PCs']==original['PCs']and len(original['PCs'])==142,'Exact reached142 physical source order')
  t=c['thread_contract'];old_frame=0x20008000;old_fs=t['source_TEB'];owners=alias['owners']
  need(len(owners)==5 and [r['extent']for r in owners]==[256,16,12,280,4240],'Five whole finite borrowed role extents')
  def address_contract(a,n):
   if old_frame-0x100<=a and a+n<=old_frame+4:return dict(role='entry-stack',offset=a-old_frame)
   if old_fs<=a and a+n<=old_fs+8192:return dict(role='guest-FS',offset=a-old_fs)
   for owner in owners:
    if owner['new']<=a and a+n<=owner['new']+owner['extent']:return dict(role=owner['role'],offset=a-owner['new'])
   return dict(role='absolute',offset=a)
  operands=[]
  for ordinal,(pc,a,_,width,writing)in enumerate(rows[0]['source_accesses']):
   other=rows[1]['source_accesses'][ordinal];need((pc,a,width,writing)==(other[0],other[1],other[3],other[4]),'Exact independently derived operand identity, observed value excluded')
   operands.append(dict(ordinal=ordinal,pc=pc,width=width,writing=bool(writing),**address_contract(a,width)))
  need(len(operands)==113,'Complete finite operand scope')
  domain={'entry-stack':old_frame,'guest-FS':old_fs,**{x['role']:x['new']for x in owners},'absolute':0}
  for op,original_access in zip(operands,rows[0]['source_accesses']):need(domain[op['role']]+op['offset']==original_access[1],'Reversible finite address classification');counts['isolated_operand_reverse_checks']+=1
  counts.update(collections.Counter('operand_role_'+r['role']for r in operands))
  need([r['ordinal']for r in operands if r['role']=='guest-FS']==[30,33,50],'Exactly source EH FS0 read/install/restore')
  need([r['ordinal']for r in operands if r['role']=='global-object' and r['writing']]==[57,58],'Exactly two cached provider writes')
  # Current file imports and original loaded targets are separate columns. The
  # connected reader/dispatcher must preserve the shared parent's raw cells.
  spec=importlib.util.spec_from_file_location('mfc_connected_pe',pin(R/'tools/analysis/pe.py'));pe=importlib.util.module_from_spec(spec);spec.loader.exec_module(pe)
  images={}
  for key,p,h in [('game',R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),('MFC',R/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8'),('CRT',R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')]:images[key]=pe.PEImage(pin(p,h).read_bytes())
  import_rows=[]
  declarations=[('game',0x5abed0,0x5bb210,0x5f401083),('game',0x5ae3c4,0x5bb674,0x78003ddb),('MFC',0x5f40107d,0x5f49815c,0x78001496)]
  api_cells=[('MFC',0x5f498330),('CRT',0x7802e044),('CRT',0x7802e0c8),('CRT',0x7802e048)]
  for a,(module,cell)in zip(c['normal_APIs'],api_cells):declarations.append((module,a['source_PC'],cell,a['source_target']))
  for module,pc,cell,resolved in declarations:
   image=images[module];off,_=image.rva_range(cell-image.image_base,4);value=struct.unpack_from('<I',image.data,off)[0]
   matches=[dict(library=library['library'],**s)for library in image.imports()for s in library['symbols']if image.image_base+s['iat_rva']==cell];need(len(matches)==1,'Unique physical owning import cell')
   import_rows.append(dict(module=module,source_pc=pc,cell=cell,file_raw=value,original_isolated_loaded_target=resolved,import_identity=matches[0],whole_cell_replace_admitted=False,owning_projection_required=True,current_parent_raw_cell_retained=True))
  enter=next(r for r in import_rows if r['source_pc']==0x7800106f);leave=next(r for r in import_rows if r['source_pc']==0x780012ab)
  need((enter['file_raw'],leave['file_raw'])==(214146,214170),"Exact existing parent's physical named raw inputs")
  need('{2013491200,3}'in parent_sources['lockit_contract.inc'],'Existing carried CRT78037000 source mapping')
  need('expected_pages_.push_back({p.address,b})'in parent_sources['locale_batch_operations.inc'],'Existing full page mirror ownership')
  need('if(research_standalone_)return;'in parent_sources['locale_batch_operations.inc'],'Standalone normal bootstrap leaves default locale helper unentered')
  need('Only an actual registered literal initializer root may enter'in parent_sources['session_impl.inc'],'Nonregistering entry needs separate NativeEntry')
  merges=[dict(cell=0x7803708c,width=4,role='codepage-lock25-association',new_value='Declared guest CS24 alias tied to a real owned nativeCS40',source_prior_read_inventory_pending=True),dict(cell=0x780379c0,width=4,role='cached-codepage',new_value='Genuine chronological cached BEFORE value, expected1252 only if observed',source_prior_read_inventory_pending=True),dict(cell=0x78037ae8,width=4,role='resolver-transient',new_value='Genuine chronological BEFORE flag, expected1 only if observed',source_prior_read_inventory_pending=True)]
  contract=dict(root=c['root'],slot=c['selected_slot'],phase=13,registers_callback=False,Runtime_entry_contract=dict(ABI='Cdecl',arguments=0,return_value=True,frame=0x20001800,persistent_State3504=True,persistent_FX512=True,initial_CPU_from_actual_current_Runtime=True,isolated_CPU_or_FX_seed=False),normal_instruction_order=original['PCs'],instructions=c['instructions'],normal_operand_order=operands,role_extents={x['role']:x['extent']for x in owners},role_aliases={x['role']:x['new']for x in owners},typed_carried_pointer_cells=alias['pointer_cells'],typed_guest_FS_policy=dict(base=0x7ffde000,head='Current Runtime source chain/sentinel',bounds='Current Runtime stack identity',self='Current Runtime TIB identity',TLS_mirror_offset=0xe1c,whole_Windows_TEB_copy_admitted=False),imports=import_rows,source_defined_EH=c['EH_contract'],field_writes=c['field_writes'],shared_CRT_page=dict(address=0x78037000,already_mapped_and_carried=True,whole_page_replace_admitted=False,proposed_new_input_cells=merges,preserve_registry_cells=[0x78037888,0x7803788c,0x78037890],changes_require_fresh_genuine_prefix_and_prior_operand_noninterference=True),new_manager_page=0x5f4cb000,normal_native_TLS_services=9,source_API_services=4,chronological_genuine_input_pending=True,connected_execution_admitted=False,initializer_credit=0)
  path=out/'connected-contracts.json';path.write_text(json.dumps(contract,indent=2)+'\n');pin(path)
  roles=['absolute','entry-stack','guest-FS']+[x['role']for x in owners];enum_names={r:r.replace('-','_')for r in roles}
  header=['#pragma once','#include <array>','#include <cstdint>','#include <stdexcept>','namespace mw34::m4_mfc1168_connected {','enum class AddressRole:unsigned {'+','.join(enum_names.values())+'};','struct AddressDomain {std::array<unsigned,8>bases{};};','struct Operand {unsigned ordinal,pc,width;bool writing;AddressRole role;std::int64_t offset;};','inline constexpr std::array<Operand,113>operands{{'+','.join('{'+','.join([str(r['ordinal']),str(r['pc']),str(r['width']),str(r['writing']).lower(),'AddressRole::'+enum_names[r['role']],str(r['offset'])])+'}'for r in operands)+'}};','inline unsigned resolve(const Operand&o,const AddressDomain&d){const auto a=std::int64_t(d.bases[unsigned(o.role)])+o.offset;if(a<0||std::uint64_t(a)+o.width>0x100000000ULL)throw std::runtime_error("Finite typed connected source address");return unsigned(a);}','inline bool matches(unsigned ordinal,unsigned pc,unsigned address,unsigned width,bool writing,const AddressDomain&d){if(ordinal>=operands.size())return false;const auto&o=operands[ordinal];return o.pc==pc&&o.width==width&&o.writing==writing&&resolve(o,d)==address;}','}']
  (out/'connected_address_contract.hpp').write_text('\n'.join(header)+'\n');pin(out/'connected_address_contract.hpp');(out/'connected_entry.hpp').write_bytes(pin(R/'tools/m4-mfc1168-native/connected_entry.hpp').read_bytes());pin(out/'connected_entry.hpp')
  (out/'interface_compile.cpp').write_text('#include "connected_entry.hpp"\n#include "connected_address_contract.hpp"\nstatic_assert(mw34::m4_mfc1168_connected::operands.size()==113);\nmw34::m4_runtime::NativeEntry mfc_connected_compiled_entry=&mw34::m4_mfc1168_connected::entry;\n');pin(out/'interface_compile.cpp')
  note='''# Connected MFC1168 interface: chronological admission pending

This artifact publishes the existing 142 literal source instructions, thirteen O0/O2 bodies, and 113 ordered operand identities with stack/FS/borrowed-role addresses expressed relative to the current invocation. Observed isolated operand values and AFTER bytes are absent from these executable contracts. Both isolated levels reverse-resolve every authored address descriptor exactly. The callbacks preserve the carried State and FX, projecting only the current Runtime CPU as the existing accepted callbacks do. The separate NativeEntry interface is compiled without a concrete resource implementation; it does not register or execute this initializer.

CRT78037000 is already a native source page and a complete checked Binding mirror, although the ordinary46 Record pages omit it. Whole-page import would overwrite the live callback registry. The proposed lock25/cached-codepage/transient cells must be separately authenticated by the fresh chronological original prefix, joined to a typed owned nativeCS40 association, and proved compatible with prior bootstrap/prefix reads. Their values are deliberately unresolved. The standalone bootstrap returns after four static locks, before its default-locale helper; this is not evidence that source lock25 already exists.

Shared CRT Enter/Leave IAT cells retain their original file representatives214146/214170. The genuine original isolated worker resolved different x86 API addresses. Exact source-owned import projections must bridge those representations at the admitted CALL/JMP PCs, with raw-cell and named provider identities retained. Game ordinal1168, _setmbcp and imported EH have their own explicit projections. No shared IAT/page replacement is admitted.

The native minimal TIB retains FS7FFDE000, source head, stack bounds and self identity. Only a separately declared TLS mirror cell at FS+E1C may refer to the five-role alias graph. It must reflect current typed hostTlsGetValue and the genuine BEFORE current-thread record, while the actual host TLS slot index and hostCS40 stay separate. A fresh chronological original worker owns discovery of that graph and caller State at frame20001800 after13 accepted roots. All input materialization, complete resource context implementation, execution and initializer credit remain pending.
'''
  (out/'interface.md').write_text(note);pin(out/'interface.md');pin(__file__);pin(sys.executable)
  for body in lift['source_bodies'].values():
   for obj in body['objects'].values():pin(obj['path'],obj['sha256'])
  for p,h in PINS.items():need(sha(p)==h,'Stable complete interface inputs')
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Parameterized native-use finite contracts and separate nonregistering Runtime entry interface only; chronological input and resource implementation pending',contracts=str(out/'connected-contracts.json'),contracts_sha256=sha(out/'connected-contracts.json')if(out/'connected-contracts.json').exists()else None,entry_header=str(out/'connected_entry.hpp'),address_header=str(out/'connected_address_contract.hpp'),lifts=str(R/'reports/m4-mfc1168-native/lifts-r2/report.json'),counts=dict(counts),files=PINS,capture_archive_reader_opened=False,whole_shared_page_import_admitted=False,connected_writer_prepared=False,connected_execution_admitted=False,initializer_credit=0)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
