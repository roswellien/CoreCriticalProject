"""Focused physical FCOS initializer recovery and six genuine original endpoint probes."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];OLD=ROOT/'reports/m4-lockit-original/original-preparation-r4';FOCUS=ROOT/'reports/m4-next-review/decoded-r1';BASE=ROOT/'reports/m4-cosine-original'
sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def one(s,a,b):
 need(s.count(a)==1,'One exact cosine source edit '+a[:60]);return s.replace(a,b,1)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh focused cosine preparation');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix!='.mwb','No inherited payload reader');v=sha(p);need(h is None or h==v,'Exact source '+str(p));pins[str(p)]=v;return p
 def text(p):return pin(p).read_text(encoding='utf-8-sig')
 old=json.loads(pin(OLD/'report.json','6a25b9b16ccdbfefe30488ea6b87afd5c266489fd63f2b5710c05c04a14fd68b').read_bytes())
 for p,h in old['files'].items():pin(p,h)
 frontier=json.loads(pin(ROOT/'reports/m4-joint-startup124-root/next-frontier-r1/remaining-roots.json').read_bytes());root=next(r for r in frontier if r['entry']==0x4b64f0);need(root['slot']==0x5e0160,'Existing source-root frontier identity')
 for ext in('txt','obj','s'):pin(FOCUS/f'4b64f0.{ext}')
 game=PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());rows=[]
 spec=importlib.util.spec_from_file_location('cosine_physical_contracts',pin(ROOT/'tools/m4-crt-locale-batch-recovery/recover_v2.py'));D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
 for line in text(FOCUS/'4b64f0.txt').splitlines():
  m=re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)',line)
  if not m:continue
  local=int(m[1],16)
  if local>=0x79 or 5<=local<0x10:continue
  pc=0x4b64f0+local;code=bytes.fromhex(m[2]);offset,_=game.rva_range(pc-game.image_base,len(code));need(game.data[offset:offset+len(code)]==code,'Every actual physical cosine source instruction')
  args=m[4].split(' <')[0].strip()
  if m[3]=='jmp':need(code==bytes.fromhex('e90b000000'),'Exact source entry jump');args='0x4b6500'
  rows.append(D.instruction_contract(dict(pc=pc,width=len(code),bytes_hex=code.hex(),mnemonic=m[3],operands=args)))
 need(len(rows)==19 and sum(r['width']for r in rows)==110 and [r['mnemonic']for r in rows].count('fcos')==3,'Exact19 reachable source rows110B/3FCOS')
 need(rows[0]['pc']==0x4b64f0 and rows[1]['pc']==0x4b6500 and rows[-1]['pc']==0x4b6568,'Source gap is padding, not executed instructions')
 raw=pin(OLD/'pages.bin',old['pack_sha256']).read_bytes();records={struct.unpack_from('<I',raw,12+i*4104)[0]:(struct.unpack_from('<I',raw,16+i*4104)[0],bytearray(raw[20+i*4104:4116+i*4104]))for i in range(struct.unpack_from('<I',raw,8)[0])};spans=list(old['source_spans']);known={r['pc']:r for r in spans}
 section=next(s for s in game.sections if game.image_base+s['virtual_address']<=0x5e8000<game.image_base+s['virtual_address']+max(s['raw_size'],s['virtual_size']));need(section['writable'],'Physical original game data section is writable');records[0x5e8000]=(2,records[0x5e8000][1])
 for r in rows:
  pc=r['pc'];code=bytes.fromhex(r['bytes_hex']);offset,_=game.rva_range(pc-game.image_base,len(code))
  if pc in known:need(known[pc]['size']==len(code)and known[pc]['image_offset']==offset,'Shared exact cosine source agreement');continue
  page=pc&~4095
  if page not in records:records[page]=(1,bytearray(b'\xcc'*4096))
  records[page][1][pc&4095:(pc&4095)+len(code)]=code;spans.append(dict(pc=pc,size=len(code),image_offset=offset,origin=0));known[pc]=spans[-1]
 inputs=[]
 for a in(0x5c93d0,0x5c93d8,0x5c93e0):
  offset,_=game.rva_range(a-game.image_base,8);b=game.data[offset:offset+8];need(bytes(records[a&~4095][1][a&4095:(a&4095)+8])==b,'Accepted raw game input page has exact untouched default double');inputs.append(dict(address=a,bytes_hex=b.hex(),bits=struct.unpack('<Q',b)[0],value=struct.unpack('<d',b)[0]))
 out.mkdir(parents=True);pack=b'MW4J124P'+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',p,permission)+data for p,(permission,data)in records.items());(out/'pages.bin').write_bytes(pack)
 spec=text(OLD/'spec.hpp');spec=re.sub(r'pack_sha\[\]="[0-9a-f]+"','pack_sha[]="'+sha(out/'pages.bin')+'"',spec);spec=re.sub(r'pack_size=\d+','pack_size='+str(len(pack)),spec)
 for field,values in [('entries',[0x4b64f0]),('table_slots',[0x5e0160]),('page_bases',list(records)),('page_permissions',[p for p,d in records.values()])]:spec=re.sub(r'inline constexpr std::array<std::uint32_t,\d+> '+field+r'\{[^;]+;',f'inline constexpr std::array<std::uint32_t,{len(values)}> '+field+'{'+','.join(hex(v)for v in values)+'};',spec)
 spec=re.sub(r'inline constexpr std::array<CodeBinding,\d+> code_bindings\{\{[^;]+;',f'inline constexpr std::array<CodeBinding,{len(spans)}> code_bindings{{{{'+','.join('{'+','.join(hex(r[k])for k in('pc','size','image_offset','origin'))+'}'for r in spans)+'}};',spec);(out/'spec.hpp').write_text(spec)
 (out/'protocol.hpp').write_text(text(OLD/'protocol.hpp').replace('sequences=6, roots=124','sequences=6, roots=1'))
 broker=text(OLD/'original_broker.hpp');bases=list(dict.fromkeys([int(v,16)for v in re.search(r'bases\{([^;]+)\};',broker)[1].split(',')]+[p&~65535 for p in records]));broker=re.sub(r'std::array<std::uint32_t,\d+> bases\{[^;]+;',f'std::array<std::uint32_t,{len(bases)}> bases'+'{'+','.join(hex(v)for v in bases)+'};',broker);(out/'original_broker.hpp').write_text(broker)
 ref=text(OLD/'reference.cpp');ref=re.sub(r'std::array<void\*,118> pages',f'std::array<void*,{len(records)}> pages',ref)
 start=ref.index('            const auto mfcbase=');end=ref.index('            const auto lockbase=',start);ref=ref[:start]+ref[end:]
 start=ref.index('            const auto stringbase=');end=ref.index('            out.append("phase/"',start);ref=ref[:start]+ref[end:]
 ref=one(ref,'require(*crtnext-*crtbegin==96*4,"Exact96callback vectorextent");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),96*4);','require(*crtnext==*crtbegin,"Actual FCOS root registers no callback");out.append("cleanup/"+std::to_string(sequence)+"/registry.bin",reinterpret_cast<void*>(*crtbegin),0);')
 start=ref.index('        require(lockit_allocation_count==8,');end=ref.index('original_free(reinterpret_cast<void*>(*crtbegin));',start);ref=ref[:start]+'        require(!lockit_allocation_count&&!container_allocation_count&&!fs_allocation_count,"Actual cosine prefix has no owned allocation observations");'+ref[end:]
 ref=ref.replace('6 connected sequences /744 actual original initializer phases captured; full ledger and native equivalence remain open','Six genuine FCOS initializer hardware endpoints captured; source/native comparison remains separate');(out/'reference.cpp').write_text(ref)
 for fn in('reference_x86.asm','preserve_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm','fs_observer_x86.asm','fs-hook-bindings.json','CMakeLists.txt'):(out/fn).write_text(text(OLD/fn))
 scalar=[r for r in rows if r['mnemonic']=='mov'and r['explicit_memory_writes']];need(len(scalar)==7,'Seven physically decoded scalar MOV stores; three additional FSTP stores')
 contract=dict(schema='mw34-cosine-original-source-v1',root=0x4b64f0,slot=0x5e0160,instructions=rows,source_span={'start':0x4b64f0,'end_exclusive':0x4b6569,'span_bytes':121,'reachable_bytes':110,'padding_bytes':11},inputs=inputs,FCOS_PCs=[r['pc']for r in rows if r['mnemonic']=='fcos'],scalar_MOV_store_count=7,source_FP_store_count=3,source_imports=[],normal_FS_sites=[],callbacks_registered=0,source_after_seed=False)
 (out/'instruction-contracts.json').write_text(json.dumps(contract,indent=2)+'\n');pin(__file__)
 for p in out.iterdir():pin(p)
 report=dict(passed=True,scope='Exact19-row original cosine initializer physical recovery and six authentic CW/TOP endpoint probes; no predicted trigonometric output supplied to observations',root=0x4b64f0,slot=0x5e0160,parent_preparation_sha256=sha(OLD/'report.json'),source_spans=spans,pack_sha256=sha(out/'pages.bin'),observed_pages=old['observed_pages'],original_sequences=6,original_phases=6,record_bytes=356992,source_instruction_rows=19,source_instruction_bytes=110,source_default_inputs=inputs,source_CW_TOP_cases=[[0,0x7f,0],[0,0x37f,7],[0,0xf7f,0],[1,0x47f,7],[1,0xa7f,0],[1,0xe7f,7]],predicted_outputs_supplied_to_execution=False,host_cos_expected_output_used=False,source_after_seed=False,source_imports=[],source_callbacks=0,scalar_MOV_store_count=7,source_FP_stores=3,source_permission_update={"page":0x5e8000,"from":0,"to":2,"basis":"Actual physical game data section writable; literal source stores require RW instead of inherited research read-only optimization"},native_executed=False,initializer_credit=False,inherited_capture_reader_opened=False,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),rows=19,inputs=inputs)))
if __name__=='__main__':main(sys.argv[1])
