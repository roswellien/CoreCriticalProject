"""Read-only finite borrowed-owner alias review; no worker or capture reader."""
from pathlib import Path
import hashlib, json, struct, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
O=R/'reports/m4-mfc1168-original/alias-domain-review-r1'
assert not O.exists();O.mkdir(parents=True)
files={}
def need(value,why):
 if not value:raise ValueError(why)
def pin(path,digest=None):
 path=Path(path).resolve()
 with path.open('rb') as stream:value=hashlib.file_digest(stream,'sha256').hexdigest()
 need(digest is None or digest==value,'Physical input '+str(path))
 need(str(path)not in files or files[str(path)]==value,'Stable physical input')
 files[str(path)]=value
 return path
def read(path,digest=None):return json.loads(pin(path,digest).read_bytes())
prep_path=R/'reports/m4-mfc1168-native/fixture-preparation-r2/report.json'
prep=read(prep_path,'55aa6aadb104ebdcda3a1e1a1fb6c53b1a8951da177e5ba4b3e9b25f31a97212')
build_path=R/'reports/m4-mfc1168-native/fixture-build-r3/build.json'
build=read(build_path)
need(prep['passed'] and build['passed'] and build['preparation_sha256']==files[str(prep_path.resolve())],'Exact current compiled fixture lineage')
for worker in build['workers'].values():pin(worker['path'],worker['sha256'])
def input_path(path):
 path=Path(path).resolve()
 return pin(path,prep['files'][str(path)])
contracts=read(input_path(R/'reports/m4-mfc1168-probe/native-contracts-r1/contracts.json'))
source=read(input_path(R/'reports/m4-mfc1168-probe/validation-r6/source-derivations.json'))
need(len(source['accesses'])==113 and len(contracts['borrowed_backings'])==5,'Finite actual source/borrowed extent inventory')
for path in (R/'reports/m4-mfc1168-native/fixture-preparation-r2/fixture.cpp',
             R/'reports/m4-mfc1168-native/fixture-preparation-r2/fixture_spec_O0.hpp',
             R/'reports/m4-mfc1168-native/fixture-preparation-r2/fixture_spec_O2.hpp',
             R/'tools/m4-startup/image_loader.cpp',R/'runtime/memory/guest_memory.cpp',R/'tools/m4-runtime/runtime.cpp'):
 input_path(path)
pack=input_path(prep['input_pack']).read_bytes()
need(pack[:8]==b'M4MFCNAT','Exact finite input pack')
n=struct.unpack_from('<I',pack,8)[0];at=12;blocks={}
for i in range(n):
 address,size,permissions=struct.unpack_from('<III',pack,at);at+=12
 need(address not in blocks and size>0 and at+size<=len(pack),'Complete disjoint pack extent')
 blocks[address]=dict(bytes=pack[at:at+size],permissions=permissions);at+=size
need(at==len(pack),'No extra packed input')
image=pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes()
pe=struct.unpack_from('<I',image,60)[0];opt=pe+24
base=struct.unpack_from('<I',image,opt+28)[0]
table=opt+struct.unpack_from('<H',image,pe+20)[0]
sections=[]
for i in range(struct.unpack_from('<H',image,pe+6)[0]):
 a=table+40*i;vs,rva,raw,offset=struct.unpack_from('<4I',image,a+8)
 sections.append(dict(name=image[a:a+8].split(b'\0')[0].decode(),start=base+rva,
  mapped_end=base+rva+((max(vs,raw)+4095)//4096)*4096,
  virtual_end=base+rva+vs,raw_end=base+rva+raw,characteristics=struct.unpack_from('<I',image,a+36)[0]))
data=next(x for x in sections if x['name']=='.data')
accepted=read(R/'reports/m4-joint-startup130-root/acceptance-r1/report.json','12215395619ea72ee1a587763112bc3a2ed9aad15c9c99a5697f69c9658429aa')
need(accepted['passed'],'Physically accepted130 lineage')
accepted_preparation=read(R/'reports/m4-startup130-original/preparation-r2/report.json')
pages=accepted_preparation['observed_pages']+accepted_preparation['extra_whole_source_pages']
need(len(pages)==len(set(pages))==46,'Current accepted complete46-page inventory')
roles=contracts['borrowed_backings'];rows=[];footprint=set()
for owner in roles:
 address=owner['guest'];extent=owner['extent'];blob=blocks[address]['bytes']
 authentic=input_path(R/f'reports/m4-mfc1168-probe/execution-r6/trace/BEFORE/domain/{owner["role"]}/bytes.bin').read_bytes()
 need(len(blob)==extent and blob==authentic and hashlib.sha256(blob).hexdigest()==owner['initial_sha256'],'Exact original BEFORE backing')
 need(data['raw_end']<=address and address+extent<=data['mapped_end'],'Borrowed backing aliases admitted game zero-fill')
 overlapping=[p for p in pages if max(address,p)<min(address+extent,p+4096)]
 need(not overlapping,'Disjoint from accepted130 measured page inventory')
 footprint.update(range(address&~4095,((address+extent+4095)//4096)*4096,4096))
 uses=[dict(index=i,PC=row[0],address=row[1],value=row[2],width=row[3],writing=bool(row[4]),offset=row[1]-address)
       for i,row in enumerate(source['accesses']) if address<=row[1] and row[1]+row[3]<=address+extent]
 rows.append(dict(**owner,end=address+extent,game_section='.data',overlaps_accepted130_pages=overlapping,source_operand_relations=uses))
need(len(footprint)==3 and sum(x['extent']for x in roles)==4804,'Five exact owners occupying three game pages')
cells=[
 dict(cell=0x5f4cb018,role='manager-array',target=0x7c3448,source_access_indices=[],scope='Carried manager pointer only; not read by current113 source operands'),
 dict(cell=0x5f4cb01c,role='thread',target=0x7c2f90,source_access_indices=[],scope='Carried manager pointer only; not read by current113 source operands'),
 dict(cell=0x5f4cb040,role='global-object',target=0x7c3730,source_access_indices=[45,46],scope='Current literal cache pointer reads'),
 dict(cell=0x39fe1c,role='thread',target=0x7c2f90,source_access_indices=[],scope='Actual current-thread TLS slot; resolved by the typed named API, not a literal source operand'),
 dict(cell=0x7c2f9c,role='thread-array',target=0x7c2de0,source_access_indices=[18],scope='Current literal thread+0C pointer read'),
 dict(cell=0x7c2de4,role='thread-object',target=0x7c3560,source_access_indices=[19],scope='Current literal slot1 thread-array pointer read')]
def bytes_at(address,n):
 matches=[(a,b)for a,b in blocks.items()if a<=address and address+n<=a+len(b['bytes'])]
 need(len(matches)==1,'Unique physical input owner for typed pointer cell')
 a,b=matches[0];return b['bytes'][address-a:address-a+n]
for cell in cells:
 need(struct.unpack('<I',bytes_at(cell['cell'],4))[0]==cell['target'],'Actual complete DWORD pointer identity')
 for i in cell['source_access_indices']:
  pc,address,value,width,writing=source['accesses'][i]
  need((address,value,width,writing)==(cell['cell'],cell['target'],4,0),'Exact source consumed pointer identity')
  cell.setdefault('source_PCs',[]).append(pc)
need([x['role']for x in rows if not x['source_operand_relations']]==['manager-array'],'Only manager-array is unread by the literal normal prefix')
normal_policy={
 'isolated_fixture_admission':'Only this one registered root, exact initial4804B owner mirrors, immutable role identities and exact113 PC/address/width/direction operands; every extra access, lazy branch, pointer replacement or borrowed free must be denied',
 'connected_same_address_admission':False,
 'why_connected_blocked':'Runtime admits and owns the whole PE .data section; copying borrowed heap bytes into game BSS aliases that ownership even though the current46 measured pages are disjoint. That finite disjointness cannot establish unused global storage for later roots/gameplay.',
 'minimal_consumed_relocation':'Choose disjoint guest owner extents outside every PE/provider/stack/TEB/registered owned range; preserve role extent+initial bytes and replace only proven typed references: global cache DWORD, thread+0C DWORD, thread-array+4 DWORD, plus TlsGetValue typed guest result. Derive every affected source address/register value from those typed results.',
 'complete_five_role_carried_graph':'For whole provider/TEB input identity also rewrite the three measured carried pointer cells at5F4CB018,5F4CB01C,TEB+E1C. These are explicitly carried input relations and do not add literal-read closure. No scanning/replacing arbitrary equal integers is admitted.',
 'static_game_and_provider_cells_unchanged':['5F4CB000->5F4CB008 internal manager','5F4CB03C slot1','manager5F4CB008 source TLS index3','thread+8 length3','thread-object+4 NULL','5BB210 namedMFC1168 IAT','5BB674 named_setmbcp IAT','7803708C named lock25 guestCS association'],
 'nonpointer_source_effects':'Writes at5AE3B7/5AE3BA remain global-object+14 byte0 and global-object+1040 DWORD421; their destination changes only through the derived cached-pointer return. Preserve every other byte of each backing.',
 'host_resources':'Native TLS index and CS40 are separately owned; never put native host pointer/index into source pointer fields or memcpy opaqueCS24 into CS40. Clear/free only host TLS/CS associations, never borrowed game/provider inputs.',
 'connected_frame_prerequisite':'The fixture113 absolute operands include the genuine standalone stack and TEB. Connected integration must derive source stack/FS accesses from current connected frame/TEB and keep the other carried handler without AFTER reseeding.',
 'unadmitted_frontier':contracts['unproved']}
result=dict(sections=sections,borrowed_owners=rows,typed_pointer_cells=cells,borrowed_page_footprint=sorted(footprint),
 accepted130_observed_pages=pages,policy=normal_policy)
p=O/'alias-domain.json';p.write_text(json.dumps(result,indent=2)+'\n');pin(p);pin(__file__);pin(sys.executable)
report=dict(passed=True,scope='Read-only current fixtureprep2/build3 exact borrowed alias and finite source domain review; connected relocation prerequisite, no fixture execution or acceptance credit',
 fixture_preparation_sha256=files[str(prep_path.resolve())],fixture_build_sha256=files[str(build_path.resolve())],
 borrowed_extents=5,borrowed_bytes=4804,borrowed_game_BSS_pages=3,accepted130_pages_checked=46,
 source_operands_checked=113,literal_borrowed_operands=6,typed_pointer_cells=6,consumed_pointer_cell_relations=4,
 normal_typed_API_thread_return_required=True,connected_same_address_admitted=False,source_after_seed=False,
 capture_reader_opened=False,worker_executed=False,initializer_credit=0,files=files)
p=O/'report.json';p.write_text(json.dumps(report,indent=2)+'\n')
with p.open('rb')as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
print(json.dumps(dict(passed=True,sha256=digest,fixture_build_sha256=report['fixture_build_sha256'])))
