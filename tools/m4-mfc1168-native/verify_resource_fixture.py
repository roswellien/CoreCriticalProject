"""Fresh actual native API/export/lifecycle, caller and causal-refusal proof.

No AFTER value is used to reconstruct source. This gate authenticates real
resources and bounded observation exports; the independent literal gate is
required separately. Every byte in same-session retry observations is retained.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={};CACHE={}
NAMES=['TlsAlloc','TlsSetValue','TlsGetValue','TlsFree','InitializeCriticalSection','EnterCriticalSection','LeaveCriticalSection','DeleteCriticalSection','GetACP']
ALIASES={4:['InitializeCriticalSection','RtlInitializeCriticalSection'],5:['EnterCriticalSection','RtlEnterCriticalSection'],6:['LeaveCriticalSection','RtlLeaveCriticalSection'],7:['DeleteCriticalSection','RtlDeleteCriticalSection']}
REASONS={1:'Exact causal source PC/operand/direction order',2:'Exact causal source PC/operand/direction order',3:'Exact causal source PC/operand/direction order',4:'Exact typed source TLS/borrowed CS argument',5:'Real native TlsGetValue returns current owned association',6:'Exact named source target/current frame',7:'Exact typed source TLS/borrowed CS argument',8:'Normal lock25 enter depth0',9:'Guest access permission denied',10:'Literal provider byte14 write',11:'Unobserved source branch/callback is denied',12:'Exact complete physical source span admission'}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def eq(a,b,s):need(a==b,s+' '+str((a,b))[:600])
def pin(p,h=None):
 p=Path(p).resolve();a=sha(p);need(h is None or a==h,'Exact physical input '+str(p));need(str(p)not in PINS or PINS[str(p)]==a,'Stable input');PINS[str(p)]=a;return p
def raw(p):return pin(p).read_bytes()
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def load(p,name):
 s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def words(p,count,kind='Q'):return struct.unpack('<'+kind*count,raw(p))
def pack(data):
 eq(data[:8],b'M4MFCNAT','BEFORE pack magic');count=struct.unpack_from('<I',data,8)[0];cursor=12;result={}
 for _ in range(count):
  address,size,permission=struct.unpack_from('<III',data,cursor);cursor+=12;need(size and address not in result and cursor+size<=len(data),'Finite unique BEFORE block');result[address]=(size,permission,data[cursor:cursor+size]);cursor+=size
 eq(cursor,len(data),'Complete exact BEFORE pack');return result
def relocation(prep):
 policy=read(prep['relocation_proof']);alias=read(prep['alias_review'],prep['alias_review_sha256']);need(alias['passed'],'Independent alias policy passed')
 source=read(R/'reports/m4-mfc1168-native/fixture-preparation-r2/report.json','55aa6aadb104ebdcda3a1e1a1fb6c53b1a8951da177e5ba4b3e9b25f31a97212')
 old=pack(raw(source['input_pack']));new=pack(raw(prep['input_pack']));eq(len(old),284,'Original complete284 BEFORE extents');eq(len(new),284,'Relocated complete284 BEFORE extents');need(len(policy['owners'])==5 and len(policy['pointer_cells'])==6,'Exact five roles/six typed cells')
 def relocate(a):
  for o in policy['owners']:
   if o['old']<=a<o['old']+o['extent']:return o['new']+a-o['old']
  return a
 expected={relocate(a):(n,p,bytearray(b))for a,(n,p,b)in old.items()}
 for cell in policy['pointer_cells']:
  eq(relocate(cell['cell']),cell['new_cell'],'Declared source cell relocation');eq(relocate(cell['old_target']),cell['new_target'],'Declared target role relocation')
  hits=[(a,b)for a,(n,_,b)in expected.items()if a<=cell['new_cell']and cell['new_cell']+4<=a+n];eq(len(hits),1,'Unique current typed cell backing');a,b=hits[0];eq(struct.unpack_from('<I',b,cell['new_cell']-a)[0],cell['old_target'],'Whole original BEFORE typed target');struct.pack_into('<I',b,cell['new_cell']-a,cell['new_target'])
 eq({a:(n,p,bytes(b))for a,(n,p,b)in expected.items()},new,'All284 complete input extents with ONLY six declared pointer rewrites')
 return policy,new
class PhysicalPE:
 def __init__(self,path):
  self.path=pin(path);self.data=raw(path);M=load(R/'tools/m4-tree-review/amd64_pe.py','mfc_resource_amd64_pe');self.pe=M.PEImage(self.data);nt=struct.unpack_from('<I',self.data,60)[0];self.opt=nt+24;self.edir,self.elen=struct.unpack_from('<II',self.data,self.opt+112);self.reloc,self.rlen=struct.unpack_from('<II',self.data,self.opt+112+5*8);self.exports={}
  if self.edir:
   b=self.bytes(self.edir,40);_,_,_,_,_,base,nf,nn,funcs,names,ords=struct.unpack('<IIHHIIIIIII',b);need(nf<=65536 and nn<=65536,'Bounded physical AMD64 export table')
   for i in range(nn):
    name=self.cstring(struct.unpack('<I',self.bytes(names+4*i,4))[0]);index=struct.unpack('<H',self.bytes(ords+2*i,2))[0];need(index<nf,'Bounded named export index');rva=struct.unpack('<I',self.bytes(funcs+4*index,4))[0];self.exports[name]=dict(rva=rva,ordinal=base+index,forwarder=self.cstring(rva)if self.edir<=rva<self.edir+self.elen else None)
 def bytes(self,rva,size):start,_=self.pe.rva_range(rva,size);return self.data[start:start+size]
 def cstring(self,rva):
  start,end=self.pe.rva_range(rva,1);stop=self.data.find(b'\0',start,min(end,start+1024));need(stop>=start,'Bounded physical name');return self.data[start:stop].decode('ascii')
 def entry(self,rva,owner):
  data=bytearray(self.bytes(rva,64));delta=owner-self.pe.image_base;cursor=0;applied=[]
  while cursor<self.rlen:
   page,size=struct.unpack('<II',self.bytes(self.reloc+cursor,8));need(size>=8 and size%2==0 and cursor+size<=self.rlen,'Exact physical relocation block')
   for entry in struct.unpack('<'+'H'*((size-8)//2),self.bytes(self.reloc+cursor+8,size-8)):
    typ,offset=entry>>12,entry&4095;a=page+offset
    if typ==0:continue
    width=8 if typ==10 else 4 if typ==3 else None
    if width is not None and a<rva+64 and a+width>rva:
     need(rva<=a and a+width<=rva+64,'Complete affected physical entry relocation');old=int.from_bytes(data[a-rva:a-rva+width],'little');value=(old+delta)&((1<<(width*8))-1);data[a-rva:a-rva+width]=value.to_bytes(width,'little');applied.append(dict(RVA=a,kind=typ,width=width))
    elif width is None:need(not rva<=a<rva+64,'Unsupported affected native entry relocation')
   cursor+=size
  eq(cursor,self.rlen,'Complete physical relocation directory');return bytes(data),applied
def native_identity(path,kind,proofs):
 before=words(path/'before-identity.bin',9);after=words(path/'after-identity.bin',9);eq(before,after,'Whole actual provider identity stable across call');version,k,target,owner,mbase,msize,state,protect,typ=before;eq((version,k,state,typ),(1,kind,0x1000,0x1000000),'Actual committed AMD64 image provider');need(owner>0 and mbase<=target and target+64<=mbase+msize,'Complete observed native entry64 image extent');need(protect&255 in(0x10,0x20,0x40,0x80)and not(protect&0x100),'Actual provider executable page and no guard')
 name=raw(path/'before-path.txt').decode();eq(raw(path/'after-path.txt').decode(),name,'Whole native module path stable');digest=raw(path/'before-sha256.txt').decode();eq(raw(path/'after-sha256.txt').decode(),digest,'Whole actual module physical SHA stable');module=Path(name).resolve();need(module.parent.name.lower()=='system32'and module.name.lower()in('kernel32.dll','kernelbase.dll','ntdll.dll'),'Actual native system owning image')
 key=(str(module),digest)
 if key not in CACHE:eq(sha(module),digest,'Fresh whole native provider physical image SHA');CACHE[key]=PhysicalPE(module)
 pe=CACHE[key];rva=target-owner;matches=[n for n in ALIASES.get(kind,[NAMES[kind]])if n in pe.exports and pe.exports[n]['rva']==rva and pe.exports[n]['forwarder']is None];need(matches,'Actual named or declared Rtl owning export RVA corresponds to real target')
 need(any(s['executable']and s['virtual_address']<=rva and rva+64<=s['virtual_address']+s['raw_size']for s in pe.pe.sections),'Whole physical owning export entry executable backing');expected,relocs=pe.entry(rva,owner);entry=raw(path/'before-entry64.bin');eq(entry,raw(path/'after-entry64.bin'),'Actual provider whole entry64 stable');eq(entry,expected,'Complete physical AMD64 relocated named export entry64')
 proof=dict(requested=NAMES[kind],actual_owner=str(module),physical_sha256=digest,owner=owner,target=target,RVA=rva,matched_exports=matches,entry64=entry.hex(),relocations=relocs,identity_words=before)
 proofs.setdefault((kind,str(module),rva,entry.hex()),proof)
 return proof
def cs(b):return struct.unpack_from('<I',b,12)[0],struct.unpack_from('<Q',b,16)[0]
def main(execution,digest,source_path,source_sha,name):
 out=R/'reports/m4-mfc1168-native'/name;need(not out.exists(),'Fresh resource verification');out.mkdir();passed=False;counts=collections.Counter();cases=[];proofs={};physical_rows=[]
 try:
  e=read(execution,digest);need(e['passed']and e['all_workers_terminal'],'All bounded actual workers terminal/pass');source=read(source_path,source_sha);need(source['passed']and source['execution_sha256']==digest,'Independent complete literal BEFORE source proof current execution');b=read(e['build'],e['build_sha256']);prep=read(b['preparation'],b['preparation_sha256']);policy,inputs=relocation(prep)
  for q,h in b['files'].items():pin(q,h)
  for q,h in prep['files'].items():pin(q,h)
  all_cases=list(e['runs'].values())+e['controls'];eq(len(all_cases),26,'Two positive/twenty-four actual refusals')
  global_pointer=next(x['new']for x in policy['owners']if x['role']=='global-object')
  for row in all_cases:
   p=Path(row['output']);mode=row['mode'];level=row['level']
   for q,h in row['outputs'].items():pin(q,h)
   status=words(p/'result/status.bin',6,'I');eq(status[:5],(mode,int(mode>0),int(mode>0),0,0),'Exact actual control and resources closed status');eq(raw(p/'COMPLETE.txt'),b'complete','Actual worker complete');serials=sorted([int(q.name)for q in(p/'resources').iterdir()]);eq(serials,list(range(status[5])),'All actual named calls with contiguous owned lifetime serials')
   tls=None;association=0;CSaddress=None;CSdepth=0;deleted=False;released=False;thread=None;events=[]
   for serial in serials:
    d=p/'resources'/str(serial);w=words(d/'call.bin',8);eq(w[:2],(1,serial),'Actual ordered service invocation');kind,a0,a1,result,tid,last_error=w[2:];need(kind<9,'Finite native named provider');thread=tid if thread is None else thread;eq(tid,thread,'Every owned resource call current host thread');identity=native_identity(d,kind,proofs);physical_rows.append(dict(level=level,mode=mode,serial=serial,kind=kind,call_words=w,proof_identity=[kind,identity['actual_owner'],identity['RVA'],identity['entry64']]))
    pre,post=raw(d/'CS-before40.bin'),raw(d/'CS-after40.bin');eq(len(pre),40,'Whole actual native CS before');eq(len(post),40,'Whole actual native CS after')
    if kind==0:need(tls is None and result!=0xffffffff,'One actual successful owned TLS allocation');tls=result
    elif kind==1:eq(a0,tls,'Own actual TLS Set index');need(not released and result==1,'Actual TLS Set succeeds before release');association=a1
    elif kind==2:eq(a0,tls,'Own actual TLS Get index');need(not released,'Actual TLS Get within own live lifetime');eq(result,association,'Actual TLS lookup equals current whole association')
    elif kind==3:eq(a0,tls,'Own actual TLS Free index');need(not released and association==0 and result==1,'Own actual TLS clear before successful free');released=True
    elif kind==4:need(CSaddress is None,'One native CS initialization');CSaddress=a0;eq(cs(post),(0,0),'Native CS initialized unowned')
    elif kind in(5,6):eq(a0,CSaddress,'Exact actual native CS40 object');need(not deleted,'Native CS operation only live');eq(cs(pre),(CSdepth,thread if CSdepth else 0),'Actual native CS before depth/current thread');CSdepth+=1 if kind==5 else -1;need(CSdepth in(0,1),'Finite balanced depth');eq(cs(post),(CSdepth,thread if CSdepth else 0),'Actual native CS after depth/current thread')
    elif kind==7:eq(a0,CSaddress,'Exact native CS object deletion');need(not deleted and CSdepth==0,'Own actual CS unheld before delete');deleted=True
    elif kind==8:eq(result,1252,'Actual native finite GetACP1252 result');need(CSdepth==1 and not deleted,'Source ACP query under actual native lock25 association')
    events.append(dict(serial=serial,service=NAMES[kind],words=w,CS_before_hex=pre.hex(),CS_after_hex=post.hex()));counts['actual_provider_identity_sides']+=2;counts['whole_native_CS40_sides']+=2
   need(tls is not None and released and CSaddress and deleted and CSdepth==0,'Complete owned TLS/native CS40 lifecycle with no live resource');counts['complete_owned_lifecycles']+=1
   if mode==0:eq([x['words'][2]for x in events],[0,2,1,4,2,5,8,6,2,1,2,3,7],'Complete normal actual resource service order')
   hardware=raw(p/'host-hardware.bin');eq(len(hardware),1632,'Complete actual host hardware observations');eq(hardware[:512],hardware[1088:1600],'Complete actual caller hardware FX512 restored');eq(hardware[512:540],hardware[1600:1628],'Complete actual caller hardware ENV28 restored');counts['whole_caller_FX512_ENV28_restored']+=1
   refusal=raw(p/'result/refusal.txt').decode();retry_files=[]
   if mode:
    need(refusal,'Actual precise refusal retained')
    if REASONS[mode]:eq(refusal,'memory_access site=0x005ae3e4 target=0x005ae3e4: Admitted native callback failed: '+REASONS[mode],'Exact causal control refusal reason')
    else:need('write'in refusal.lower()and('permission'in refusal.lower()or'permitted'in refusal.lower()),'Actual read-only guest CS transport write refusal')
    before=p/'retry/before';after=p/'retry/after';names={str(q.relative_to(before))for q in before.rglob('*')if q.is_file()};eq(names,{str(q.relative_to(after))for q in after.rglob('*')if q.is_file()},'Complete same-session retry file set')
    required={'State.bin','CPU.bin','FX.bin','RuntimeCPU.bin','private.bin','accesses.bin','APIs.bin','frames.bin','nativeCS40.bin','native-thread-mirror.bin','routes.bin','resource-context.bin'};need(required<=names,'Full caller/route/private/resource retry observations');eq(len(names),284+len(required),'All284 extents plus complete private retry observations')
    for item in sorted(names):eq(raw(before/item),raw(after/item),'Entire unchanged same poisoned Runtime retry '+item);retry_files.append(item)
    eq(len(raw(before/'State.bin')),3504,'Entire actual retry State3504');eq(len(raw(before/'nativeCS40.bin')),40,'Whole actual retry native CS40');eq(len(raw(before/'native-thread-mirror.bin')),16,'Whole actual retry current-thread mirror');counts['whole_same_session_immutable_retries']+=1;counts['whole_retry_file_joins']+=len(names)
    if mode==5:need(any(x['words'][2]==2 and x['words'][5]==0 and x['words'][1]>3 for x in events),'Control genuinely cleared owned TLS before actual GetNULL')
    if mode==9:need(any(x['words'][2]==5 for x in events)and any(x['words'][2]==6 for x in events),'Actual Enter before failed guest transport and genuine cleanup Leave')
    if mode==10:original=inputs[global_pointer][2];eq(raw(before/f'blocks/{global_pointer}.bin')[0x14],original[0x14],'Wrong byte value denied before committed backing mutation')
   else:eq(refusal,'','Positive actual invocation has no refusal')
   cases.append(dict(level=level,mode=mode,refusal=refusal,actual_resources_closed=True,services=events,host_hardware_sha256=sha(p/'host-hardware.bin'),caller_boundary='Runtime.invoke plus same-session retry and owned resource cleanup; construction outside boundary',caller_full_FX512_ENV28_equal=True,retry_complete_files=retry_files))
  (out/'actual-provider-identity-joins.json').write_text(json.dumps(physical_rows,indent=2)+'\n');(out/'unique-physical-API-proofs.json').write_text(json.dumps(list(proofs.values()),indent=2)+'\n');(out/'lifecycle-caller-refusal-relations.json').write_text(json.dumps(cases,indent=2)+'\n')
  for q in out.glob('*.json'):pin(q)
  pin(__file__);pin(sys.executable)
  for q,h in PINS.items():eq(sha(q),h,'All successful reads physically stable')
  counts['unique_actual_named_provider_proofs']=len(proofs);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Fresh bounded actual native named API owner/export/executable/relocated entry64, complete own TLS/CS40 lifecycles, caller wholeFX512/ENV28 invoke+retry+cleanup and twelve causal refusals per level; no connected initializer credit',execution=str(execution),execution_sha256=digest,source_comparison=str(source_path),source_comparison_sha256=source_sha,counts=dict(counts),files=PINS,initializer_credit=0,source_AFTER_seed=False,capture_archive_reader_opened=False,all_bounded_readers_closed=True,borrowed_guest_CS24_not_host_CS40=True,construction_outside_caller_hardware_boundary=True)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])
