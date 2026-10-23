"""Bounded PE/message entry CFG recovery; never load or execute a target DLL."""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,subprocess,sys
R=Path(__file__).resolve().parents[2]
OBJDUMP=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main():
 out=R/'reports/m4-loader-message-review/physical-r1';need(not out.exists(),'Fresh immutable physical proof');out.mkdir(parents=True);pins={}
 def pin(p):p=Path(p).resolve();pins[str(p)]=sha(p);return p
 def emit(name,d):p=out/name;p.write_text(json.dumps(d,indent=2)+'\n');pin(p)
 pefile=pin(R/'tools/analysis/pe.py');spec=importlib.util.spec_from_file_location('message_physical_PE',pefile);PE=importlib.util.module_from_spec(spec);spec.loader.exec_module(PE)
 old=pin(R/'reports/m4-loader-source/service-obligations-r1/report.json');prior=json.loads(old.read_bytes());need(prior['passed'],'Prior loader obligations');pin(prior['service_contract']);pin(prior['caller_contract'])
 variants=[]
 for label,rel in [('current','MW3/Mech3Msg.dll'),('staged','local/mw3-staged/Program_Files/Mech3Msg.dll')]:
  path=pin(R/rel);image=PE.PEImage(path.read_bytes());base=image.image_base
  def bytes_va(va,n):return image.read(image.rva_range(va-base,n)[0],n)
  result=subprocess.run([str(pin(OBJDUMP)),'--disassemble','--x86-asm-syntax=intel',str(path)],capture_output=True,check=True);text=result.stdout.decode('utf8');p=out/(label+'-disassembly.txt');p.write_bytes(result.stdout);pin(p)
  rows={}
  for line in text.splitlines():
   m=re.match(r'^([0-9a-fA-F]+):\s+((?:[0-9a-fA-F]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*?)\s*$',line)
   if not m:continue
   pc=int(m[1],16);raw=bytes.fromhex(m[2]);need(bytes_va(pc,len(raw))==raw,'Every disassembled byte physically matches');rows[pc]=dict(pc=pc,bytes=raw.hex(),size=len(raw),mnemonic=m[3],operands=m[4])
  iats={base+s['iat_rva']:dict(library=lib['library'],**s)for lib in image.imports()for s in lib['symbols']}
  closures={}
  for name,entry in [('entry',base+image.entry_point_rva),('CRT',base+0x1a60),('DllMain',base+0x1710),('sort',base+0x1000),('ZLocGetID',base+0x1720)]:
   pending=[entry];seen=set();edges=[];unknown=[]
   while pending:
    pc=pending.pop()
    if pc in seen:continue
    need(pc in rows,'Complete physical instruction boundary');seen.add(pc);row=rows[pc];op=row['mnemonic'];nextpc=pc+row['size'];targets=[]
    if op.startswith('ret'):continue
    if op in('call','jmp')or op.startswith('j'):
     direct=re.match(r'0x([0-9a-fA-F]+)',row['operands'])
     if direct:targets.append(int(direct[1],16));edges.append(dict(pc=pc,target=targets[-1],kind='direct-call'if op=='call'else'branch'))
     else:
      slot=re.search(r'\[0x([0-9a-fA-F]+)\]',row['operands']);slot=int(slot[1],16)if slot else None
      if slot in iats:edges.append(dict(pc=pc,kind='import-boundary',slot=slot,import_symbol=iats[slot]))
      else:unknown.append(dict(pc=pc,mnemonic=op,operand=row['operands'],kind='data-dependent callback, not assumed resolved'))
     if op=='jmp':
      pending.extend(targets);continue
    targets.append(nextpc);pending.extend(targets)
   closures[name]=dict(entry=entry,physical_instruction_count=len(seen),physical_PCs=sorted(seen),edges=edges,unresolved_dynamic_edges=unknown,direct_CFG_closed=True,dynamic_CFG_closed=not unknown)
  emit(label+'-physical-CFG.json',dict(rows=list(rows.values()),closures=closures))
  rva,n=image.directories[5];cursor=0;relocations=[]
  while cursor<n:
   page,size=image.unpack('<II',image.rva_range(rva+cursor,8)[0]);need(size>=8 and size%2==0 and cursor+size<=n,'Whole relocation block');raw=image.read(image.rva_range(rva+cursor+8,size-8)[0],size-8)
   for (word,)in struct.iter_unpack('<H',raw):
    kind=word>>12;site=base+page+(word&4095)
    if kind:need(kind==3,'Only HIGHLOW relocation accepted');relocations.append(dict(va=site,kind=kind,source_word=struct.unpack('<I',bytes_va(site,4))[0]))
   cursor+=size
  relocation_sites={r['va']for r in relocations};table=[]
  for va in range(base+0x3010,base+0x6158,8):
   pointer,id=struct.unpack('<II',bytes_va(va,8));name=image.rva_string(pointer-base).encode('ascii');need(va in relocation_sites,'Every name pointer physically relocatable');table.append(dict(source_va=va,name_pointer=pointer,id=id,name=name.decode('ascii')))
  need(len(table)==1577 and len({r['name']for r in table})==1577,'Finite unique physical message table');ordered=sorted(table,key=lambda r:r['name'].encode('ascii'));projected=b''.join(struct.pack('<II',r['name_pointer'],r['id'])for r in ordered)
  p=out/(label+'-sorted-table-design.bin');p.write_bytes(projected);pin(p);emit(label+'-name-id-table.json',dict(rows=table,planned_sorted_source_indices=[(r['source_va']-(base+0x3010))//8 for r in ordered],whole_initial_table_sha256=hashlib.sha256(bytes_va(base+0x3010,1577*8)).hexdigest(),planned_sorted_table_sha256=sha(p),source_machine_executed=False,semantic_algorithm_equivalence_not_yet_proven=True,changed_slots=sum(x['source_va']!=base+0x3010+i*8 for i,x in enumerate(ordered))))
  # Resource tree is bounded and every leaf payload is retained physically.
  rr,rn=image.directories[2];resource_base=image.rva_range(rr,rn)[0];resources=[];directories=set()
  def resource_tree(offset,chain):
   need(offset not in directories and len(chain)<5,'Resource tree finite/no cycle');directories.add(offset);need(offset+16<=rn,'Whole directory header');named,ids=image.unpack('<HH',resource_base+offset+12)
   for i in range(named+ids):
    name,child=image.unpack('<II',resource_base+offset+16+8*i)
    if name&0x80000000:
     pos=name&0x7fffffff;length=image.u16(resource_base+pos);key=image.read(resource_base+pos+2,length*2).decode('utf-16-le')
    else:key=name
    if child&0x80000000:resource_tree(child&0x7fffffff,chain+[key])
    else:
     need(child+16<=rn,'Whole resource leaf entry');data_rva,size,codepage,reserved=image.unpack('<IIII',resource_base+child);data=image.read(image.rva_range(data_rva,size)[0],size);p=out/(label+'-resource-'+str(len(resources))+'.bin');p.write_bytes(data);pin(p);leaf=dict(path=chain+[key],rva=data_rva,bytes=size,codepage=codepage,reserved=reserved,payload_path=str(p),sha256=sha(p))
     if chain and chain[0]==11:
      blocks=struct.unpack_from('<I',data)[0];metadata=[]
      for j in range(blocks):
       low,high,offset=struct.unpack_from('<III',data,4+12*j);need(low<=high,'Finite message range');start=offset
       for id in range(low,high+1):
        length,flags=struct.unpack_from('<HH',data,offset);need(length>=4 and offset+length<=len(data),'Whole message entry');offset+=length
       metadata.append(dict(low=low,high=high,count=high-low+1,offset=start,end=offset))
      leaf['message_blocks']=metadata;leaf['message_count']=sum(x['count']for x in metadata)
     resources.append(leaf)
  resource_tree(0,[]);emit(label+'-resources.json',resources);emit(label+'-relocations.json',relocations)
  crt_initial={hex(va):bytes_va(va,4).hex()for va in [base+0x3000,base+0x3004,base+0xe2bc,base+0xe2c0,base+0xe2c4,base+0xe2c8,base+0xe2cc]};need(set(crt_initial.values())=={'00000000'},'Exact null static CRT frontiers')
  variants.append(dict(label=label,path=str(path),sha256=sha(path),bytes=path.stat().st_size,image_base=base,entry=base+image.entry_point_rva,sections=image.sections,directories=image.directories,imports=image.imports(),exports=image.exports(),TLS_present=bool(image.directories[9][0]),delay_imports_present=bool(image.directories[13][0]),relocation_count=len(relocations),resource_leaves=len(resources),message_counts=[x.get('message_count')for x in resources],CRT_initial_words=crt_initial,text_sha256=hashlib.sha256(bytes_va(base+0x1000,3046)).hexdigest(),data_sha256=hashlib.sha256(bytes_va(base+0x3000,45776)).hexdigest()))
 emit('variants.json',variants);pin(__file__);pin(sys.executable)
 report=dict(passed=True,scope='Complete physical message PE32 entry/sort/export direct CFG, imports/TLS/relocations/resource leaves and explicit dynamic-callback frontiers; no target executed',variants=variants,REA_status='Connected tool returned target_unavailable/no active program',installed_Ghidra_launcher_exists=(Path('C:/Users/jcbla/AppData/Local/Programs/REA/ghidra_12.1.4_PUBLIC/support/analyzeHeadless.bat')).is_file(),datafile_equals_executable_load=False,whole_dynamic_CFG_claim=False,sort_semantic_equivalence_claim=False,source_machine_executed=False,native_executed=False,capture_reader_opened=False,initializer_credit=0,files=pins);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q),variants=variants)))
if __name__=='__main__':main()
