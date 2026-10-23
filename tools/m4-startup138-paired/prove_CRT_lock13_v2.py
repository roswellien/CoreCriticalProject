"""Finite actual CS13 API ownership and whole own guest descriptor relation.
Only sealed ordinary export files; no source machine or capture archive reader.
"""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
CS=0x78037130
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 def receipt(path,h):
  p=pin(R/path,h);g=json.loads(p.read_bytes());assert g['passed'];return p,g
 dp,dg=receipt('reports/m4-startup138-paired/CRT-lock25-domain-r1/report.json','974053dfbd2dc7b4808e1f09b14efcdc57a968e29c0a7539d2e99fb8cd61eae1');domains=json.loads(pin(dg['domains_path'],dg['domains_sha256']).read_bytes())
 gp,g=receipt('reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052');assert g['reader_closed']
 ordinary=pin(R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');spec=importlib.util.spec_from_file_location('ordinary',ordinary);D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
 for leaf in('locale_batch.hpp','locale_batch_operations.inc'):
  p=(R/'reports/m4-fps-native/service-preparation-r3'/leaf).resolve();pin(p,g['files'][str(p)])
 model=(R/'tools/m4-crt-locale-batch-model-review/batch.py').resolve();pin(model,g['files'][str(model)])
 # Physical source producer distinguishes the immutable guest descriptor from
 # the separately owned initialized native40 resource. Opaque API internals
 # are not inferred from endpoint carry.
 producer=(R/'reports/m4-fps-native/service-preparation-r3/locale_batch_operations.inc').read_text()
 for literal in('api.inputs.push_back(guest_bytes(guest,24))','::InitializeCriticalSection(&section->native)','::EnterCriticalSection(&section->native)','::LeaveCriticalSection(&section->native)','::DeleteCriticalSection(&p.native)','section->owner_thread!=thread_','api_return(frame,argc,preserve_eax)'):assert literal in producer
 bundles={}
 for e in g['paired_exports']:
  i=pin(e['index_path'],e['index_sha256']);p=pin(e['payload_path'],e['payload_sha256']);branch=e['branch']
  pattern=re.compile(r'phase/[0-5]/\d+/(?:api-ledger|CRT-(?:before|after)/2013491200).bin')if branch=='original'else re.compile(r'sequence-[0-5]/(?:(?:selected/locale-(?:api-\d+-(?:witness|input-0)|critical-sections)|cleaned/locale-critical-sections|phase-\d+-(?:before|after)-page-2013491200)).bin')
  bundles[branch]=(i,p,D.entries(i,pattern))
 def data(f,es,k,n=None):
  z=es[k];assert n is None or z['bytes']==n;f.seek(z['offset']);b=f.read(z['bytes']);assert len(b)==z['bytes']and hashlib.sha256(b).hexdigest()==z['sha256'];return b
 originals=[];original_counts=[0,0]
 i,p,es=bundles['original']
 with p.open('rb')as f:
  for seq in range(6):
   count=[0,0];depth=0;apis=[]
   for phase in range(138):
    stem=f'phase/{seq}/{phase}/';a=data(f,es,stem+'CRT-before/2013491200.bin',4096);b=data(f,es,stem+'CRT-after/2013491200.bin',4096);cs=a[0x130:0x148]
    assert b[0x130:0x148]==cs and struct.unpack('<6I',cs)==(0xffffffff,0xffffffff,0,0,0,0x020007d0);assert struct.unpack_from('<I',a,0x5c)[0]==CS
    for index,v in enumerate(struct.iter_unpack('<26I',data(f,es,stem+'api-ledger.bin'))):
     if v[24]not in(5,6):continue
     kind=v[24];assert v[20]==CS and v[9]==v[19]==0 and v[25]==(0x78001075 if kind==5 else 0x780012b1)
     # Complete measured CPU10 retained; exact stdcall stack/nonvolatile ABI.
     assert v[14]==v[4]+8 and all(v[k]==v[k+10]for k in(3,5,6,7));assert v[0]==13 if kind==5 else True
     depth+=1 if kind==5 else -1;assert depth in(0,1);count[kind-5]+=1
     apis.append(dict(phase=phase,index=index,kind=kind,arguments=list(v[20:24]),saved_return=v[25],CPU_before=list(v[:10]),CPU_after=list(v[10:20]),schema_absent_PC_exact_zero=True,depth_after=depth))
   assert depth==0 and count==[108,108];original_counts=[a+b for a,b in zip(original_counts,count)];originals.append(dict(sequence=seq,APIs=apis,counts=count))
 assert original_counts==[648,648]
 rows=[]
 for level in('O0','O2'):
  i,p,es=bundles[level]
  with p.open('rb')as f:
   for seq in range(6):
    domain=next(r for r in domains if r['level']==level and r['sequence']==seq);ao=bytes.fromhex(domain['original_inputs'][str(0x78037000)]);bo=bytes.fromhex(domain['native_inputs'][str(0x78037000)]);assert bo[0x130:0x148]==bytes(24)
    stem=f'sequence-{seq}/selected/';apis=[];native_ptr=None;depth=0;counts=[0,0];init=0
    witness_names=sorted((k for k in es if k.startswith(stem+'locale-api-')and k.endswith('-witness.bin')),key=lambda k:int(k.split('locale-api-')[1].split('-')[0]))
    for k in witness_names:
     v=struct.unpack('<32Q',data(f,es,k,256));index=int(k.split('locale-api-')[1].split('-')[0]);assert v[:2]==(1,index)
     if v[20]!=CS or v[7]!=1:continue
     assert v[14]==v[15]==1 and v[8]==v[12]==0 and v[16]and v[17]==40 and v[9]==v[11]and v[19]==0;assert data(f,es,stem+f'locale-api-{index}-input-0.bin',24)==bo[0x130:0x148]
     if v[3]==0x7802e03c:
      assert init==0 and depth==0;init+=1;native_ptr=v[16]
     elif v[3]in(0x7802e044,0x7802e048):
      assert init==1 and native_ptr==v[16];kind=5 if v[3]==0x7802e044 else 6;depth+=1 if kind==5 else -1;counts[kind-5]+=1;assert depth in(0,1)
      assert v[2]==(0x7800106f if kind==5 else 0x780012ab)and v[6]==(0x78001075 if kind==5 else 0x780012b1)
      apis.append(dict(index=index,kind=kind,witness=list(v),whole_guest_API_input_hex=bo[0x130:0x148].hex()))
     else:raise AssertionError(('Unexpected CS13 API',v))
     assert v[18]==depth
    assert init==1 and counts==[108,108]and depth==0 and len(apis)==216
    secs=list(struct.iter_unpack('<16Q',data(f,es,stem+'locale-critical-sections.bin')));section=next(v for v in secs if v[1]==CS);assert section[3:10]==(108,108,0,1,0,1,0)and section[10]==native_ptr and section[11]==40
    terminal=next(v for v in struct.iter_unpack('<16Q',data(f,es,f'sequence-{seq}/cleaned/locale-critical-sections.bin'))if v[1]==CS);assert terminal[2]==section[2]and terminal[3:10]==(109,109,0,1,1,1,1)and terminal[10:12]==(native_ptr,40)
    for phase in range(138):
     for side in('before','after'):
      page=data(f,es,f'sequence-{seq}/phase-{phase}-{side}-page-2013491200.bin',4096);assert page[0x130:0x148]==bo[0x130:0x148]
    cells=[dict(offset=0x130,size=24,role='initialized_lock13_opaque_API_resource',guest_address=CS,original_initial_hex=ao[0x130:0x148].hex(),native_initial_hex=bo[0x130:0x148].hex(),native_resource_extent=40,native_resource_pointer=native_ptr,original_enter_leave=[108,108],native_enter_leave=counts,native_initializations=1,opaque_API_internals_equivalent=False)]
    domain['typed_CRT_lock13_objects']=cells;domain['unused_input_offsets']=[v for v in domain['unused_input_offsets']if v not in range(0x130,0x148)];assert not set(range(0x130,0x148))&set(domain['unused_input_offsets']);rows.append(dict(level=level,sequence=seq,typed_object=cells[0],native_APIs=apis,original_APIs=originals[seq]['APIs']))
 for i,p,es in bundles.values():assert sha(i)==pins[str(i)]and sha(p)==pins[str(p)]
 dp=out/'domains.json';dp.write_text(json.dumps(domains,indent=2)+'\n');pin(dp);rp=out/'relations.json';rp.write_text(json.dumps(rows,indent=2)+'\n');pin(rp);pin(__file__);pin(sys.executable)
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Finite current lock13 original initialized OS CS24 and native immutable guest24/owned actual CS40 association; complete measured original CPU10/stdcall ABI and native source6 typed actual API witnesses; balanced same-instance ownership and whole original phase endpoints',domains_path=str(dp),domains_sha256=sha(dp),typed_lock13_object_relations=12,original_enter_leave=original_counts,native_enter_leave=[1296,1296],whole_original_descriptor_phase_cells=1656,whole_native_guest_descriptor_API_inputs=2604,whole_native_descriptor_phase_cells=3312,same_native_resource_cleaned_terminal_relations=12,cleanup_scope='Selected108 balanced; one later growth acquisition yields cleaned109 balanced and single delete',unused_excluded_offsets=list(range(0x130,0x148)),native_source_CPU_and_guest_carry_gate_sha256=sha(gp),opaque_Win32_transient_internals_equivalent=False,provider_full_CPU_executed=False,complete_paired_policy_admitted=False,archive_reader_opened=False,ordinary_readers_closed=True,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
