"""Exact current109 shared-owner typed relation, preserving branch padding."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fs-source';PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Immutable source input '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable source input');PINS[str(p)]=v;return p
def load(p,n):
 s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def words(b,n):return struct.unpack('<'+'I'*n,b)
def rows(b,n):need(len(b)%(n*8)==0,'Whole typed QWORD rows');return list(struct.iter_unpack('<'+'Q'*n,b))
def main(native_report,name):
 out=BASE/name;need(not out.exists(),'Fresh independent owner relation');out.mkdir(parents=True);passed=False;counts=collections.Counter();observations=[]
 try:
  pin(__file__);need(json.loads(pin(native_report).read_bytes())['passed'],'Final native109 execution');need(json.loads(pin(BASE/'original-game-source-r4/report.json','e81470844c869f8d31d4995a150a3c689990321710010faeff0550a568029001').read_bytes())['passed'],'Current literal original owner byteflow');need(json.loads(pin(BASE/'connected-native-source-r1/report.json').read_bytes())['passed'],'Current persistent native owner byteflow');D=load(ROOT/'tools/m4-crt-allocation-root/run_v2.py','owned_original_archive');ori=D.DirectSet(BASE/'original-run-r2/original/transport.json',pin)
  bindings=json.loads(pin(BASE/'allocation-interface-r1/allocation-inputs.json','a3fb27e6f16c12bbc7499c912415b2c294d74e97c7600dbaeb3be4770ab492ff').read_bytes());geometry=json.loads(pin(BASE/'geometry-r1/allocation-derivations.json').read_bytes());traces=json.loads(pin(BASE/'geometry-r1/root-derivations.json').read_bytes());program={r['pc']:r for r in json.loads(pin(BASE/'recovery-r3/instruction-contracts.json').read_bytes())['instructions']};order=json.loads(pin(BASE/'recovery-r3/instruction-contracts.json').read_bytes())['selected_order'];phases={r['entry']:i for i,r in enumerate(order)};need(len(bindings)==len(geometry)==10,'Ten exact independent source owner identities')
  def owner(address,n=1):
   found=[r for r in geometry if r['declared_pointer']<=address and address+n<=r['declared_pointer']+r['requested_size']];need(len(found)<=1,'Unique declared source geometry owner');return found[0]if found else None
  for level in('O0','O2'):
   native=D.DirectSet(Path(native_report).parent/level/'transport.json',pin)
   try:
    for seq in range(6):
     stem=f'sequence-{seq}/selected/';mfc=rows(native.data(stem+'mfc-allocation-witnesses.bin'),32);need(len(mfc)==45,'Full current45 owner witness');registry={};original={};predicted_original={};predicted_native={};initial_hashes={};initial_native={}
     for fi,binding in enumerate(bindings):
      r=next(w for w in mfc if w[2]==binding['root']and w[4]==binding['CALL_pc']);need(r[0]==1 and r[3]==0x5f401ea0 and r[7]==r[13]==binding['requested_size']and r[16]==r[20]and r[21]and r[23]==1,'Actual positive allocator/request/return and one committed publication');need(r[8:12]==(0x78001498,0x780012b3,0x5f401ea1,0x5f401eb5)and r[14:16]==(0x5f498970,0xffffffff),'Exact MFC allocator owning-IAT/handler source reads')
      phase=phases[binding['root']];meta=words(ori.data(f'phase/{seq}/{phase}/fs-allocation/{fi}/meta.bin'),9);need(meta[:5]==(1,fi,binding['root'],binding['CALL_pc'],binding['requested_size']),'Genuine original owner/site/request');original[fi]=meta;registry[fi]=r
      initial=ori.data(f'phase/{seq}/{phase}/api-initial/{meta[6]}/bytes.bin');need(len(initial)==meta[8],'Original true entire API BEFORE extent');predicted_original[fi]=bytearray(initial);initial_hashes[fi]=hashlib.sha256(initial).hexdigest()
      raw=native.data(stem+f'locale-allocation-{r[18]}-initial.bin');need(len(raw)==r[19]==(binding['requested_size']+15)&~15,'Native true acquired BEFORE extent');initial_native[fi]=raw;predicted_native[fi]=bytearray(raw+bytes(4096-len(raw)))
     # All owned writes come from physically authenticated executed geometry.
     # Pointer values are delivered through an exact owner/root/CALL identity,
     # never inferred from a field that a later append is allowed to overwrite.
     write_rows=[]
     for trace in traces:
      for pc,address,value,n,w in trace['source_accesses']:
       if not w:continue
       a=owner(address,n)
       if a is None:continue
       need(pc in program and program[pc]['mnemonic']in('mov','inc'),'Physical game owned store PC');fi=a['index'];offset=address-a['declared_pointer'];pointer=owner(value)if n==4 else None
       av=original[pointer['index']][7]+value-pointer['declared_pointer']if pointer else value;bv=registry[pointer['index']][16]+value-pointer['declared_pointer']if pointer else value
       predicted_original[fi][offset:offset+n]=av.to_bytes(n,'little');predicted_native[fi][offset:offset+n]=bv.to_bytes(n,'little');write_rows.append(dict(root=trace['root'],PC=pc,owner_index=fi,offset=offset,width=n,original_value=av,native_value=bv,value_owner_index=pointer['index']if pointer else None));counts['exact_typed_owned_writes']+=1
     for fi,binding in enumerate(bindings):
      meta=original[fi];r=registry[fi];source_original=bytes(predicted_original[fi]);source_native=bytes(predicted_native[fi]);need(source_original==ori.data(f'phase/{seq}/108/fs-allocation/{fi}/bytes.bin'),'Every actual final original byte independently from API BEFORE and exact typed owned source writes');need(source_original==ori.data(f'cleanup/{seq}/fs-allocation-{fi}-owned.bin'),'Whole original cleanup owner join');need(ori.data(f'cleanup/{seq}/fs-allocation-{fi}-returned.bin')==struct.pack('<I',1),'Original genuine MFC825/CRTfree call returned')
      for endpoint in('selected','grown','cleaned'):
       prefix=f'sequence-{seq}/{endpoint}/';record=next(w for w in rows(native.data(prefix+'mfc-allocation-witnesses.bin'),32)if w[2]==binding['root']and w[4]==binding['CALL_pc']);ledger=next(w for w in rows(native.data(prefix+'locale-allocations.bin'),16)if w[5]==r[18]);need(record[:25]==r[:25]and ledger[:8]==(1,r[16],binding['requested_size'],r[19],4096,r[18],4,r[17]),'Exact owner generation/full-width acquired API identity carried');need(native.data(prefix+f'locale-allocation-{r[18]}-initial.bin')==initial_native[fi],'Entire native acquired BEFORE retained');need(native.data(prefix+f'locale-allocation-{r[18]}-expected.bin')==source_native,'Complete independent native4096 source backing at each endpoint')
       if endpoint!='cleaned':need(ledger[8]==r[17]and ledger[9:12]==(1,0,0)and not any(record[25:]),'Exact live native owner state');need(native.data(prefix+f'locale-allocation-{r[18]}-owned-page.bin')==source_native,'Entire actual native mapped guest page equals source prediction')
       else:need(ledger[8:12]==(0,0,1,0)and record[25]==0x5f401782 and record[28:32]==(0x7800138a,0x78001390,1,0),'Exact genuine literal MFC825/CRTfree owner cleanup and unmapping');need(prefix+f'locale-allocation-{r[18]}-owned-page.bin'not in native.entries,'Freed guest owner has no mapped-page capture')
       counts['complete_native_shared_owner_endpoint_relations']+=1
      observations.append(dict(level=level,sequence=seq,index=fi,root=binding['root'],CALL_pc=binding['CALL_pc'],requested=binding['requested_size'],original_pointer=meta[7],original_capacity=meta[8],native_guest=r[16],native_acquired_full=r[17],native_generation=r[18],native_extent=r[19],original_initial_sha256=initial_hashes[fi],original_source_final_sha256=hashlib.sha256(source_original).hexdigest(),native_source_final_sha256=hashlib.sha256(source_native).hexdigest(),source_writes=[w for w in write_rows if w['owner_index']==fi]));counts['complete_original_shared_owner_relations']+=1
     # Independent complete circular list relation, including all static
     # backpointers; original pointers and native aliases remain separate.
     append=[2,5,6,7,8]
     for branch,allocs,getptr in(('original',predicted_original,lambda i:original[i][7]),('native',predicted_native,lambda i:registry[i][16])):
      need(struct.unpack_from('<I',allocs[0],4)[0]==getptr(1)and struct.unpack_from('<I',allocs[0],8)[0]==5,'Literal final shared registry sentinel/count');need(struct.unpack_from('<I',allocs[1],4)[0]==getptr(8)and struct.unpack_from('<I',allocs[1],0)[0]==getptr(2),'Exact closed circular sentinel links')
      for i,index in enumerate(append):
       prior=1 if i==len(append)-1 else append[i+1];following=1 if i==0 else append[i-1];need(struct.unpack_from('<3I',allocs[index],0)==(getptr(prior),getptr(following),bindings[index]['object']),'Every literal initialized node link/static-object backpointer');counts['closed_typed_node_relations']+=1
     counts['paired_shared_owner_sequences']+=1
   finally:native.close()
  ori.close();passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  (out/'owner-relations.json').write_text(json.dumps(observations,indent=2)+'\n');pin(out/'owner-relations.json');report=dict(passed=passed,scope='Independent current109 typed relation for ten newly reached shared/private owners per sequence: exact root/CALL/API/generation identities, all initialized typed links/count/static backpointers, complete own-branch API initial backing plus source writes, selected/grown/cleaned native whole guest backing and genuine source cleanup identity.',counts=dict(counts),AFTER_machine_seed=False,caller_field_used_to_forge_owner_identity=False,publication_is_exact_commit_event=True,crossbranch_private_padding_equality=False,production_native_current_physical_bytes_dumped=False,production_native_physical_backing_scope='Actual acquired initial extent is dumped; full guest expected/mapped4096 pages are dumped. Existing source bridge guard reads and compares the current physical native extent; it is not a separate current-byte dump.',FS_handler_execution=False,files=PINS);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2])
