"""Strict physical GDI identity and call joins, with caller-owned logical I/O.

verify(getter, pin, *, prefix, source_records, manual_records, logical_names)
opens no archive or process. getter(name) returns the exact logical bytes;
pin(Path, expected_sha256) records and authenticates ordinary physical reads.
source_records is the complete current cumulative APIs.bin (1488-byte records).
manual_records is an ordered iterable of (row64, hardware1152) byte pairs.
logical_names is the complete caller-owned inventory, so extra identity rows
cannot hide behind a requested count. The caller retains source-semantic,
font-generation/lifetime and source-versus-original proof responsibilities.

Requested names must be actual non-forwarded exports of the measured final
owner at the measured target RVA. Same-name final owners reached through an
upstream forwarder are valid owning-export proofs, but no upstream forwarder
chain is claimed. Different names (for example NtGdi aliases) fail closed:
the present helper does not measure the origin module/forwarder chain.
"""
from pathlib import Path
import hashlib,re,struct

NAMES=('GetStockObject','DeleteObject','CreateFontA')
SOURCE_PCS=(0x5a013c,0x5a063f,0x5a074b)
ROOTS=frozenset((0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0))
OWNERS=frozenset(('gdi32.dll','gdi32full.dll','win32u.dll'))
API_BYTES=1488

def need(value,message):
 if not value:raise ValueError(message)
def equal(a,b,message):need(a==b,message)
def qwords(data,count):
 need(isinstance(data,bytes) and len(data)==8*count,'Complete fixed-width QWORD observation')
 return struct.unpack('<'+'Q'*count,data)

class PhysicalPE:
 """Bounded complete ordinary AMD64 PE export and DIR64 reader."""
 def __init__(self,data):
  need(isinstance(data,bytes) and 0<len(data)<=64*1024*1024 and len(data)>=64 and data[:2]==b'MZ','Finite whole physical native image')
  self.data=data;nt=struct.unpack_from('<I',data,60)[0]
  need(nt>=64 and nt+24<=len(data) and data[nt:nt+4]==b'PE\0\0','Complete physical NT header')
  machine,count,_,_,_,optional,_=struct.unpack_from('<HHIIIHH',data,nt+4);opt=nt+24
  need(machine==0x8664 and 0<count<=96 and optional>=160 and opt+optional+count*40<=len(data),'Bounded complete AMD64 section directory')
  need(struct.unpack_from('<H',data,opt)[0]==0x20b,'Native PE32+ optional header')
  self.base=struct.unpack_from('<Q',data,opt+24)[0];self.image_bytes=struct.unpack_from('<I',data,opt+56)[0]
  dirs=struct.unpack_from('<I',data,opt+108)[0];need(6<=dirs<=16 and optional>=112+8*dirs,'Complete native data-directory header')
  self.export_rva,self.export_bytes=struct.unpack_from('<II',data,opt+112);self.reloc_rva,self.reloc_bytes=struct.unpack_from('<II',data,opt+152)
  need(self.base and self.image_bytes and self.image_bytes%4096==0,'Bounded physical preferred base and image extent')
  self.sections=[]
  for index in range(count):
   at=opt+optional+index*40;vs,va,size,start=struct.unpack_from('<IIII',data,at+8);flags=struct.unpack_from('<I',data,at+36)[0]
   need(start+size<=len(data) and va+max(vs,size)<=self.image_bytes,'Whole raw and virtual physical section extents')
   self.sections.append((va,size,start,flags))
  need(self.export_rva and self.export_bytes>=40 and self.export_rva+self.export_bytes<=self.image_bytes,'Whole physical export directory extent')
  self.bytes(self.export_rva,self.export_bytes)
  _,_,_,_,_,ordinal_base,nf,nn,funcs,names,ords=struct.unpack('<IIHHIIIIIII',self.bytes(self.export_rva,40))
  need(0<nn<=nf<=65536,'Bounded complete physical named export extent')
  functions=struct.unpack('<'+'I'*nf,self.bytes(funcs,4*nf));name_rows=struct.unpack('<'+'I'*nn,self.bytes(names,4*nn));ordinals=struct.unpack('<'+'H'*nn,self.bytes(ords,2*nn));self.exports={}
  for name_rva,index in zip(name_rows,ordinals):
   name=self.cstring(name_rva);need(index<nf and name and name not in self.exports,'Unique complete bounded physical named export')
   rva=functions[index];need(0<rva<self.image_bytes,'Bounded actual named export RVA')
   forwarder=self.cstring(rva) if self.export_rva<=rva<self.export_rva+self.export_bytes else None
   self.exports[name]={'rva':rva,'ordinal':ordinal_base+index,'forwarder':forwarder}
  need(bool(self.reloc_rva)==bool(self.reloc_bytes) and self.reloc_rva+self.reloc_bytes<=self.image_bytes,'Complete physical relocation-directory extent')
  self.relocations=[];cursor=0;seen=set()
  while cursor<self.reloc_bytes:
   need(cursor+8<=self.reloc_bytes,'Complete physical relocation block header');page,size=struct.unpack('<II',self.bytes(self.reloc_rva+cursor,8))
   need(page%4096==0 and size>=8 and size%2==0 and cursor+size<=self.reloc_bytes,'Bounded complete physical relocation block')
   entries=struct.unpack('<'+'H'*((size-8)//2),self.bytes(self.reloc_rva+cursor+8,size-8))
   for entry in entries:
    kind,offset=entry>>12,entry&4095
    if kind==0:continue
    address=page+offset;need(kind==10 and address not in seen and address+8<=self.image_bytes,'Unique bounded actual AMD64 DIR64 relocation')
    seen.add(address);self.relocations.append(address)
   cursor+=size
  equal(cursor,self.reloc_bytes,'Whole exact physical relocation directory consumed')
 def range(self,rva,size):
  need(isinstance(rva,int) and isinstance(size,int) and rva>=0 and size>=0 and rva+size<=self.image_bytes,'Bounded physical RVA request')
  matches=[(start+rva-va,start+length,flags) for va,length,start,flags in self.sections if va<=rva and rva+size<=va+length]
  need(len(matches)==1,'Unique complete physical raw RVA backing');return matches[0]
 def bytes(self,rva,size):
  start,_,_=self.range(rva,size);return self.data[start:start+size]
 def cstring(self,rva):
  start,end,_=self.range(rva,1);stop=self.data.find(b'\0',start,min(end,start+1024))
  need(stop>=start,'Complete bounded physical terminated export text');return self.data[start:stop].decode('ascii')
 def entry64(self,rva,owner):
  _,_,flags=self.range(rva,64);need(flags&0x20000000 and flags&0x40000000,'Whole owning export entry64 readable executable physical backing')
  need(owner and owner%65536==0 and owner+self.image_bytes<=1<<64,'Whole actual owning image virtual extent')
  data=bytearray(self.bytes(rva,64));delta=owner-self.base;applied=[]
  for address in self.relocations:
   if address<rva+64 and address+8>rva:
    need(rva<=address and address+8<=rva+64,'Entire affected DIR64 within observed entry64')
    old=struct.unpack_from('<Q',data,address-rva)[0];value=(old+delta)&((1<<64)-1);struct.pack_into('<Q',data,address-rva,value)
    applied.append({'rva':address,'kind':10,'width':8,'physical_value':old,'loaded_value':value})
  return bytes(data),applied

def parse_source_records(data):
 need(isinstance(data,bytes) and len(data)%API_BYTES==0,'Complete cumulative physical ApiRecord1488 input')
 rows=[];cursors={};closed=set();previous=None
 for offset in range(0,len(data),API_BYTES):
  record=data[offset:offset+API_BYTES];w=struct.unpack_from('<16Q',record)
  need(w[0]==1 and w[1] in ROOTS and w[3]<3 and w[2]==SOURCE_PCS[w[3]],'Exact source GDI root/service/CALL PC record')
  if previous is not None and w[1]!=previous:closed.add(previous)
  need(w[1] not in closed,'Source GDI roots occur in a single contiguous current invocation')
  previous=w[1];equal(w[4],cursors.get(w[1],0),'Exact source root GDI cursor');cursors[w[1]]=w[4]+1
  argc=14 if w[3]==2 else 1;equal(w[7],argc,'Whole typed native GDI argument count')
  need(0<w[5]<=0xffffffff and w[6]==w[2]+6 and 0<w[8]<=0xffffffff and w[11] and w[12] and w[13]<=0xffffffff and w[14]<=0xffffffff,'Complete literal source frame/instance/native target/thread bounds')
  args=struct.unpack_from('<14I',record,208);frame=struct.unpack_from('<16I',record,264)
  equal(frame[0],w[6],'Source saved return word agrees with ApiRecord');equal(frame[1:1+argc],args[:argc],'Whole actual source argument words agree with saved frame')
  equal(struct.unpack_from('<Q',record,912)[0],w[10],'Actual native full RAX agrees with complete ApiHardware output')
  rows.append({'metadata':w,'record_sha256':hashlib.sha256(record).hexdigest()})
 return rows

def verify(getter,pin,*,prefix,source_records,manual_records,logical_names,expected_thread=None):
 """Return strict joins; require caller supplies full logical inventory.

 This authenticates physical identities/call observations. Source semantics,
 stock/owned handle generations and lifetime closure remain separate gates.
 All ordinary physical module bytes are reauthenticated before returning.
 """
 need(callable(getter) and callable(pin),'Caller-owned logical getter and physical pin callbacks')
 need(isinstance(prefix,str) and (not prefix or prefix.endswith('/')),'Canonical logical widget prefix')
 source=parse_source_records(source_records);manual=[]
 for row,hardware in manual_records:
  w=qwords(row,8);need(isinstance(hardware,bytes) and len(hardware)==1152,'Whole manual native GDI ApiHardware1152')
  need(0<w[1]<=128 and w[0]==0x72001000+16*w[1] and w[2] and w[3] in ROOTS and w[4] and w[5] and w[6] and w[7]==1,'Actual successful typed manual font cleanup row')
  equal(struct.unpack_from('<Q',hardware,8)[0],w[4],'Actual manual native DeleteObject RCX owns recorded font');equal(struct.unpack_from('<Q',hardware,576)[0],w[6],'Full actual manual DeleteObject RAX agrees with cleanup row')
  manual.append({'words':w,'row_sha256':hashlib.sha256(row).hexdigest(),'hardware_sha256':hashlib.sha256(hardware).hexdigest()})
 stem=prefix+'GDI-provider/';count=len(source)+len(manual);need(count<=4096,'Finite bounded complete GDI call extent')
 suffixes=('call.bin','before-identity.bin','after-identity.bin','before-path.txt','after-path.txt','before-sha256.txt','after-sha256.txt','before-entry64.bin','after-entry64.bin')
 expected={stem+str(n)+'/'+s for n in range(count) for s in suffixes};actual={name for name in logical_names if name.startswith(stem)};equal(actual,expected,'All and only complete contiguous actual GDI identity records')
 cache={};proofs={};calls=[];thread=expected_thread
 for serial in range(count):
  local=stem+str(serial)+'/';call=qwords(getter(local+'call.bin'),11);need(call[:2]==(1,serial) and call[2]<3 and call[3]==int(serial>=len(source)),'Exact serial/type/source-versus-manual GDI call row')
  kind=call[2];before=qwords(getter(local+'before-identity.bin'),9);equal(before,qwords(getter(local+'after-identity.bin'),9),'Whole actual GDI provider identity stable across actual call')
  version,k,target,owner,region,size,state,protect,typ=before;equal((version,k,target,state,typ),(1,kind,call[8],0x1000,0x1000000),'Exact actual kind/target/MEM_COMMIT/MEM_IMAGE provider relation')
  need(owner and owner<=region<=target and size and region%4096==0 and size%4096==0 and target+64<=region+size<=1<<64,'Whole actual GDI native executable entry64 extent')
  need((protect&255) in(0x10,0x20,0x40,0x80) and not(protect&0x100),'Actual executable native provider memory without guard')
  pbytes=getter(local+'before-path.txt');equal(pbytes,getter(local+'after-path.txt'),'Whole actual native owning path stable');need(isinstance(pbytes,bytes) and pbytes and len(pbytes)<32768 and b'\0' not in pbytes,'Whole finite native module path bytes')
  observed=pbytes.decode('ascii');path=Path(observed);need(path.is_absolute(),'Actual absolute physical owning path');path=path.resolve(strict=True)
  need(path.parent.name.lower()=='system32' and path.name.lower() in OWNERS,'Measured native GDI system owning module')
  digest=getter(local+'before-sha256.txt');equal(digest,getter(local+'after-sha256.txt'),'Whole observed physical module SHA stable');need(isinstance(digest,bytes) and re.fullmatch(b'[0-9a-f]{64}',digest),'Exact full lowercase physical SHA256 observation');digest=digest.decode('ascii');key=(str(path),digest)
  if key not in cache:
   data=path.read_bytes();equal(hashlib.sha256(data).hexdigest(),digest,'Fresh whole physical measured GDI owner bytes');pin(path,digest);cache[key]=PhysicalPE(data)
  pe=cache[key];rva=target-owner;need(0<=rva and target+64<=owner+pe.image_bytes and region+size<=owner+pe.image_bytes,'Native target/observed region within whole physical owning image')
  named=pe.exports.get(NAMES[kind]);aliases=[name for name,row in pe.exports.items() if row['rva']==rva and row['forwarder'] is None]
  need(named is not None and named['forwarder'] is None and named['rva']==rva,'Exact requested named final owning export required; different-name aliases need measured origin-forwarder evidence: '+repr(aliases))
  expected_entry,relocations=pe.entry64(rva,owner);entry=getter(local+'before-entry64.bin');equal(entry,getter(local+'after-entry64.bin'),'Whole current native GDI entry64 stable');equal(entry,expected_entry,'Every byte of whole physical DIR64-relocated named GDI entry64')
  need(call[9],'Actual native GDI current thread is nonzero');thread=call[9] if thread is None else thread;equal(call[9],thread,'All actual native GDI calls use same current component thread')
  if serial<len(source):
   w=source[serial]['metadata'];equal(call,(1,serial,w[3],0,w[1],w[2],w[5],w[8],w[11],w[12],w[10]),'All11 source call QWORDs join actual complete ApiRecord metadata')
  else:
   w=manual[serial-len(source)]['words'];equal(call,(1,serial,1,1,w[3],0,0,w[2],target,w[5],w[6]),'All11 manual DeleteObject call QWORDs join actual complete cleanup row')
  proof_key=(kind,str(path),digest,owner,target,entry.hex());proofs.setdefault(proof_key,{'requested':NAMES[kind],'actual_owner':str(path),'physical_sha256':digest,'owner':owner,'target':target,'rva':rva,'ordinal':named['ordinal'],'matched_owning_export':NAMES[kind],'same_rva_named_exports':aliases,'entry64':entry.hex(),'DIR64_relocations':relocations,'origin_forwarder_chain_verified':False})
  calls.append({'serial':serial,'call_words':call,'identity_words':before,'requested':NAMES[kind],'physical_owner':str(path),'physical_sha256':digest,'rva':rva,'source_record_sha256':source[serial]['record_sha256'] if serial<len(source) else None,'manual_row_sha256':manual[serial-len(source)]['row_sha256'] if serial>=len(source) else None})
 for (path,digest) in cache:
  equal(hashlib.sha256(Path(path).read_bytes()).hexdigest(),digest,'Every whole physical GDI file unchanged at verifier completion');pin(Path(path),digest)
 return {'passed':True,'scope':'Exact named final physical owning export, whole DIR64-relocated entry64 and complete current source/manual native-call joins; source semantics/font lifetime remain independent','actual_source_calls':len(source),'actual_manual_calls':len(manual),'whole_identity_sides':2*count,'whole_named_entry64_sides':2*count,'unique_named_provider_proofs':list(proofs.values()),'calls':calls,'host_thread':thread,'archive_reader_opened':False,'game_worker_executed':False,'origin_forwarder_chain_verified':False,'different_name_aliases_admitted':False,'source_output_equivalence_claimed':False,'font_lifetime_closure_claimed':False,'initializer_credit':0}
