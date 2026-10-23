"""Finite original mode1 provider source footprint; ordinary sealed evidence only."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys,collections
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup138-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 def load(n,p):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 D=load('ordinary',R/'tools/m4-startup138-paired/diagnose_endpoint_cells.py');PE=load('physicalPE',R/'tools/analysis/pe.py');physical=pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');image=PE.PEImage(physical.read_bytes());contract=pin(R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json','9ab58b814dcc797f54b8929d7e2f8e9f9c022149b0daa40c2fe370884f6ab02d');program={r['pc']:r for r in json.loads(contract.read_bytes())['instructions']};assert len(program)==1404
 gatep=pin(R/'reports/m4-joint-startup138-source/combined-source-provider-r6/report.json','40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052');gate=json.loads(gatep.read_bytes());assert gate['passed']and gate['reader_closed'];e=next(v for v in gate['paired_exports']if v['branch']=='original');idx=pin(e['index_path'],e['index_sha256']);payload=pin(e['payload_path'],e['payload_sha256']);entries=D.entries(idx,re.compile(r'phase/[0-5]/\d+/(api-ledger|CRT-before/(2013483008|2013491200)).bin'));assert len(entries)==2484;counts=collections.Counter();facts=[];lock13=0x78037130
 with payload.open('rb')as f:
  def data(name):
   z=entries[name];f.seek(z['offset']);b=f.read(z['bytes']);assert len(b)==z['bytes']and hashlib.sha256(b).hexdigest()==z['sha256'];return b
  for seq in range(6):
   for phase in range(138):
    stem=f'phase/{seq}/{phase}/';mode=data(stem+f'CRT-before/{0x78035000}.bin');page=data(stem+f'CRT-before/{0x78037000}.bin');assert len(mode)==len(page)==4096 and struct.unpack_from('<I',mode,4)[0]==1 and struct.unpack_from('<I',page,0x5c)[0]==lock13;api=[]
    for v in struct.iter_unpack('<26I',data(stem+'api-ledger.bin')):
     kind=v[24];counts[kind]+=1;assert v[9]==v[19]==0
     if kind==0:assert v[10]>0 and 16<=v[22]<=768 and v[25]==0x78001385
     elif kind==2:assert v[10]>0 and v[22]>0 and v[25]==0x780015bb
     elif kind==3:assert v[10]>0 and v[22]>0 and 0<v[23]<=1024 and v[25]==0x78011c2d
     elif kind==5:assert v[20]==lock13 and v[25]==0x78001075
     elif kind==6:assert v[20]==lock13 and v[25]==0x780012b1
     else:raise AssertionError(('Unexpected original selected provider kind',kind))
     api.append(dict(kind=kind,actual_return_EAX=v[10],arguments=list(v[20:24]),source_return_word=v[25]))
    facts.append(dict(sequence=seq,phase=phase,actual_heap_mode=1,actual_lock13_pointer=lock13,provider_APIs=api))
 assert counts=={0:546,2:762,3:114,5:648,6:648}
 # Mode1 cuts only unsupported other-mode subheaps. Actual successful positive
 # APIs cut retry/error paths. Captured registrar metadata bounds old pointer/
 # requested size. Lock13 is the exact literal PUSH13 caller at78001514.
 prunes={0x7800130e:False,0x78001317:True,0x780013c2:False,0x780013cb:True,0x78001548:False,0x78001551:True,0x78001a34:False,0x78001a3d:True,0x7800106b:False,0x780012dc:False,0x78001a1b:False,0x78001a26:False,0x78011c0f:False,0x78011c2f:True};roots=[0x780012b3,0x78001390,0x78004a36];seen=set();todo=roots[:];missing=set();branch_rows=[]
 while todo:
  pc=todo.pop()
  if pc in seen:continue
  if pc not in program:missing.add(pc);continue
  seen.add(pc);row=program[pc];mn=row['mnemonic'];ops=row['decoded_operands'];following=pc+row['width'];raw=bytes.fromhex(row['bytes_hex']);off,_=image.rva_range(pc-image.image_base,len(raw));assert image.data[off:off+len(raw)]==raw
  if pc in prunes:
   assert mn.startswith('j')and ops[0]['kind']=='immediate';target=ops[0]['value']if prunes[pc]else following;branch_rows.append(dict(PC=pc,taken=prunes[pc],target=target,physical_bytes=row['bytes_hex']));todo.append(target);continue
  if mn not in('ret','jmp'):todo.append(following)
  if mn.startswith('j')or mn=='call':
   if ops and ops[0]['kind']=='immediate':todo.append(ops[0]['value'])
 assert len(seen)==229 and not missing
 direct=set();indirect=[]
 for pc in sorted(seen):
  row=program[pc]
  for n in set(row['explicit_memory_reads']+row['explicit_memory_writes']):
   operand=row['decoded_operands'][n]
   if operand['kind']!='memory':continue
   width=operand['bits']//8
   if not operand['terms']:
    if 0x78037000<=operand['displacement']<0x78038000:direct.update(range(operand['displacement']-0x78037000,operand['displacement']-0x78037000+width))
   elif all(t['register']not in('esp','ebp')for t in operand['terms']):
    assert pc in(0x7800105c,0x7800106d,0x780012a4,0x78004a67);indirect.append(dict(PC=pc,operand=operand,role='initialized_lock13_descriptor'if pc!=0x78004a67 else'actual_owned_registry_callback_store'))
 assert {r['PC']for r in indirect}=={0x7800105c,0x7800106d,0x780012a4,0x78004a67};direct.update(range(0x5c,0x60))
 oldp=pin(R/'reports/m4-startup138-paired/CRT-page-policy-r4/report.json','35fab86e1f2fe5199b69759cff6d995edd4a041ad40d9e99b8aece382c179f5e');old=json.loads(oldp.read_bytes());domains=json.loads(pin(old['domains_path'],old['domains_sha256']).read_bytes())
 for row in domains:assert not direct.intersection(row['unused_input_offsets'])
 # Separately retain complete current own original formatter/tree/widget/MFC/
 # four historical-owner source operands; no native branch substitution.
 original_sources=[]
 for folder,leaf,key in [('widget-complete-source-r1','source-derivations.json','source_accesses'),('mfc-source-r2','source-derivations.json','source_accesses'),('inherited-source-r5','original-Formatting-source-derivations.json','source_accesses'),('inherited-source-r5-old4','original-source-access-ledgers.json','rows')]:
  rp=pin(R/'reports/m4-startup138-original'/folder/'report.json');report=json.loads(rp.read_bytes());assert report['passed'];path=(rp.parent/leaf).resolve();rows=json.loads(pin(path,report['files'][str(path)]).read_bytes())
  for row in rows:
   unequal=set(next(d for d in domains if d['sequence']==row['sequence']and d['level']=='O0')['unused_input_offsets'])|set(next(d for d in domains if d['sequence']==row['sequence']and d['level']=='O2')['unused_input_offsets'])
   unequal-=set(range(0x8c,0x90))
   for pc,address,value,width,write in row[key]:assert not({p-0x78037000 for p in range(max(address,0x78037000),min(address+width,0x78038000))}&unequal)
  original_sources.append(dict(folder=folder,rows=len(rows),own_original_source_operand_key=key))
 treegatep=pin(R/'reports/m4-startup138-original/inherited-source-r5/report.json','7024af25138f109143adfd72db01b58f3bd58e9a22d8c772fda0e983d18d3eb4');treegate=json.loads(treegatep.read_bytes());treepath=treegatep.parent/'original-Tree-source-derivations.json';trees=json.loads(pin(treepath,treegate['files'][str(treepath.resolve())]).read_bytes());assert len(trees)==6
 for outer in trees:
  row=outer['source'];unequal=set().union(*(set(d['unused_input_offsets'])for d in domains if d['sequence']==outer['sequence']))-set(range(0x8c,0x90))
  for pc,address,value,width,write in row['source_accesses']:assert not({p-0x78037000 for p in range(max(address,0x78037000),min(address+width,0x78038000))}&unequal)
 original_sources.append(dict(folder='inherited-source-r5-tree',rows=6,own_original_source_operand_key='source/source_accesses'))
 assert sha(idx)==e['index_sha256']and sha(payload)==e['payload_sha256'];factp=out/'own-original-predicates.json';factp.write_text(json.dumps(facts,indent=2)+'\n');pin(factp);pin(__file__);pin(sys.executable);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Static source footprint229instruction mode1 malloc/free/onexit closure under actual current828 ownmode/lock and2718actualAPI witnesses including1422positiveHeapAlloc/HeapSize/HeapReAlloc results; current own original source operands additionally checked; not full original provider CPU execution or final paired admission',provider_entry_roots=roots,physical_reachable_PCs=sorted(seen),closed_successors=True,pruned_branches=branch_rows,finite_direct_CRT_data_offsets=sorted(direct),finite_indirect_roles=indirect,current_original_API_counts=dict(counts),whole_original_mode_lock_inputs=828,current_own_original_source_domains=original_sources,typed_lock25_offsets_excluded_from_unused=list(range(0x8c,0x90)),provider_full_CPU_executed=False,complete_selected138_original_provider_caller_closure_reviewed=False,complete_paired_policy_admitted=False,archive_reader_opened=False,ordinary_readers_closed=True,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
