"""Pure carried widget/GDI response and component-journal derivations.

The caller owns the source machine, current response bytes and physical API
identity admission. This module never opens an archive or launches a worker.
It writes no State, page, stack or FX observation into the source machine.
Only measured native GDI return scalars enter at their literal API boundary;
guest handles are independently derived from the live typed native mapping.
"""
from pathlib import Path
import copy,hashlib,re,struct

ROOTS=(0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0)
SITES=(0x5a013c,0x5a063f,0x5a074b)
SLOTS=(0x5bb070,0x5bb074,0x5bb068)
TARGETS=(0x71f00010,0x71f00020,0x71f00030)
NAMES=('GetStockObject','DeleteObject','CreateFontA')
IMPORT_SITES=SITES+(0x517287,0x5ac11e,0x5ac580,0x5a2f68)
IMPORT_SLOTS=SLOTS+(0x5bb064,0x5bb52c,0x5bb530,0x5bb53c)
BROKER=0x410a80
API_BYTES=1488
ARITH=('CF','PF','AF','ZF','SF','OF')
BITS={'CF':0,'PF':2,'AF':4,'ZF':6,'SF':7,'OF':11}

def need(value,message):
 if not value:raise ValueError(message)
def equal(left,right,message):
 if left!=right:raise ValueError(message)
def words(data,n,offset=0):
 need(len(data)>=offset+n*4,'Whole required source/API DWORD record');return struct.unpack_from('<'+'I'*n,data,offset)
def rows(data,size,fmt):
 need(isinstance(data,bytes) and len(data)%size==0,'Complete measured fixed-width component rows');return [struct.unpack_from(fmt,data,p)for p in range(0,len(data),size)]
def load_api_input(source,logical=None):
 """Read bytes, an ordinary path, or a caller-owned authenticated getter."""
 if isinstance(source,bytes):return source
 if callable(source):
  need(isinstance(logical,str) and logical,'Explicit current logical API name');result=source(logical);need(isinstance(result,bytes),'Measured logical API byte payload');return result
 path=Path(source);need(path.suffix.lower()not in('.mwb','.zip'),'Adapter never opens an archive');return path.read_bytes()
def table(text,kind):
 m=re.search(r'inline constexpr '+kind+r' \w+\[\]\{(.*?)\n\};',text,re.S);need(m,'Whole current literal '+kind+' table');return m[1]

class ContractGeometry:
 """Current physical source geometry, with no observed runtime input."""
 def __init__(self,contracts,literals):
  need(isinstance(contracts,dict) and isinstance(literals,str),'Caller supplies authenticated current source contracts/literals')
  self.contracts=contracts;self.roots={v['root']:v for v in contracts['roots']};equal(tuple(self.roots),ROOTS,'Exact seven current source invocation roots')
  rs=[]
  for line in table(literals,'Root').splitlines():
   if line.strip():
    row=tuple(map(int,re.findall(r'\d+',line)));need(len(row)==13,'Whole source Root13 geometry');rs.append(row)
  equal(tuple(v[0]for v in rs),ROOTS,'Literal roots retain table-sorted selected order');self.slices={v[0]:v for v in rs}
  self.operands=[]
  for line in table(literals,'Operand').splitlines():
   if line.strip():
    m=re.fullmatch(r'\{(\d+),(\d+),(-?\d+),(\d+),(true|false)\},',line.strip());need(m,'Complete physical source Operand5');self.operands.append((int(m[1]),int(m[2]),int(m[3]),int(m[4]),m[5]=='true'))
  self.instructions={int(pc):(int(size),call=='true',ret=='true')for pc,size,call,ret,bb in re.findall(r'\{(\d+),(\d+),(true|false),(true|false),\{([^}]*)\}\}',table(literals,'Instruction'))}
  fm=re.search(r'inline constexpr unsigned char fps_format\[\]\{([^}]*)\};',literals);need(fm,'Complete physical finite source format table');self.fps_format=bytes(map(int,re.findall(r'\d+',fm[1])));equal(len(self.fps_format),16,'Whole physical narrow fps format extent')
  for root,s in self.slices.items():
   c=self.roots[root];need((c['slot'],c['object'])==(s[1],s[2]) and len(c['GDI_calls'])==s[6] and len(c['virtual_calls'])==s[8] and len(c['FS_operations'])==s[10],'Complete literal/current root source association')
   need(s[11]+s[12]<=len(self.operands),'Complete root operand slice')
   for ordinal,api in enumerate(c['GDI_calls']):
    equal(api['order'],ordinal,'Exact root-local GDI source call order');need(api['service']in NAMES and api['CALL_pc']==SITES[NAMES.index(api['service'])] and api['return_pc']==api['CALL_pc']+6,'Exact typed physical source API site/return')
  self.api_count=sum(v[6]for v in rs);self.access_count=sum(v[12]for v in rs);self.virtual_count=sum(v[8]for v in rs);self.FS_count=sum(v[10]for v in rs)
  equal((self.api_count,self.access_count,self.virtual_count,self.FS_count),(149,25003,511,588),'Exact whole seven-root physical source extents')
 def summary(self):
  return {'source_GDI_calls':self.api_count,'source_component_operands':self.access_count,'source_virtual_rows':self.virtual_count,'source_FS_rows':self.FS_count,'per_root':[{'root':root,'source_GDI_calls':s[6],'source_virtual_rows':s[8],'source_FS_rows':s[10],'literal_operand_begin':s[11],'source_operand_count':s[12]}for root,s in self.slices.items()],'literal_storage_order_is_not_invocation_order':True}

class GDIAdapter:
 def __init__(self,contracts,literals,actual_apis,flag_domain,*,logical=None):
  self.geometry=ContractGeometry(contracts,literals);self.flags=flag_domain;need(callable(flag_domain.project),'Explicit independently admitted defined-flag projector')
  self.api_bytes=load_api_input(actual_apis,logical);equal(len(self.api_bytes),self.geometry.api_count*API_BYTES,'Whole current cumulative ApiRecord1488 inventory')
  self.apis=[];expected=[(root,ordinal,a)for root,c in self.geometry.roots.items()for ordinal,a in enumerate(c['GDI_calls'])];thread=None;targets={}
  for serial,(root,ordinal,a)in enumerate(expected):
   b=self.api_bytes[serial*API_BYTES:(serial+1)*API_BYTES];w=struct.unpack_from('<16Q',b);kind=NAMES.index(a['service']);argc=len(a['argument_contract'])
   need(w[:5]==(1,root,a['CALL_pc'],kind,ordinal) and w[6]==a['return_pc'] and w[7]==argc and w[8]==self.geometry.roots[root]['object']+a['instance_root_offset'],'Exact complete current measured API source owner/order/context')
   need(argc==(14 if kind==2 else 1) and w[5]<=0xffffffff and w[9]<=0xffffffff and w[11]and w[12] and w[13]<=0xffffffff and w[14]<=0xffffffff,'Typed finite current API payload/thread/target/error fields')
   thread=w[12]if thread is None else thread;equal(w[12],thread,'Same measured current native API thread');targets.setdefault(kind,w[11]);equal(w[11],targets[kind],'Same current named native target per typed API')
   hardware=b[336:1488];equal(struct.unpack_from('<Q',hardware,576)[0],w[10],'Full measured native RAX joins complete metadata')
   self.apis.append({'serial':serial,'bytes':b,'words':w,'before':words(b,10,128),'after':words(b,10,168),'args':words(b,14,208),'frame':b[264:328],'hardware':hardware,'source':a})
  self.thread=thread;self.native_targets=targets;self.api_cursor=0;self.selected=0;self.active=False;self.suspended=False;self.pending_api=False
  self.root=None;self.root_frame=0;self.saved_return=0;self.FS_head=0;self.FS_invocation=0;self.generation=0;self.fonts=[];self.frames=[];self.FS_frames=[];self.array_frames=[];self.vptrs={}
  self.accesses=[];self.imports=[];self.virtuals=[];self.arrays=[];self.FS_events=[];self.dispatches=[];self.formats=[];self.responses=[];self.proofs=[];self.raw_imports={};self.starts={}

 def configure_imports(self,machine):
  """Project only the source machine's own current raw import operands."""
  imports={}
  for k,(pc,slot)in enumerate(zip(IMPORT_SITES,IMPORT_SLOTS)):
   raw=int.from_bytes(machine.bytes(slot,4),'little');need(raw,'Own admitted raw source IAT is nonzero');target=TARGETS[k]if k<3 else 0x78004a36 if k==4 else 0x780230dd if k==6 else raw
   self.raw_imports[(pc,slot)]=(raw,target,k);imports[(pc,slot)]={'raw_value':raw,'target':target}
  need(hasattr(machine,'widget_imports'),'Literal widget model import interface');machine.widget_imports.update(imports);return imports

 def begin_root(self,machine,root,undefined):
  need(not self.active and self.selected<len(ROOTS) and root==ROOTS[self.selected] and machine.cursor==root,'One real table-ordered carried source widget entry')
  if not self.raw_imports:self.configure_imports(machine)
  self.root=self.geometry.roots[root];self.root_frame=machine.reg('esp');self.saved_return=int.from_bytes(machine.bytes(self.root_frame,4),'little')
  need(self.saved_return==BROKER and machine.call_stack and machine.call_stack[-1][:3]==(root,self.root_frame,self.saved_return),'Actual committed persistent root frame and scheduler return; no external marker seed')
  need(machine.word(2184)==machine.word(2136)==machine.word(2120)==0 and not machine.flag('DF'),'Actual flat source segments and forward DF')
  self.TIB=machine.word(2168);self.stack_low=int.from_bytes(machine.bytes(self.TIB+8,4),'little');self.stack_top=int.from_bytes(machine.bytes(self.TIB+4,4),'little');need(self.stack_low<=self.root_frame and self.root_frame+4<=self.stack_top,'Current source-owned root stack extent')
  self.FS_head=int.from_bytes(machine.bytes(self.TIB,4),'little');self.initial_FS=self.FS_head;need(not self.frames and not self.FS_frames and not self.array_frames,'Balanced carried source context before selected root')
  self.frames=[{'target':root,'frame':self.root_frame,'ret':self.saved_return,'site':0}];self.active=True;self.suspended=False;self.local_api=self.local_virtual=self.local_FS=self.local_operand=0
  self.starts={k:len(getattr(self,k))for k in('accesses','imports','virtuals','arrays','FS_events','dispatches','formats','responses')};self.api_start=self.api_cursor;self.entry_FX=bytes(machine.fx)
  self.entry_context={'root':root,'selected':self.selected,'frame':self.root_frame,'ret':self.saved_return,'TIB':self.TIB,'FS_head':self.FS_head,'CPU':tuple(machine.projected_cpu()),'undefined':copy.deepcopy(undefined),'State_sha256':hashlib.sha256(bytes(machine.state)).hexdigest(),'FX_sha256':hashlib.sha256(bytes(machine.fx)).hexdigest()}

 def _word(self,machine,address):return int.from_bytes(machine.bytes(address,4),'little')

 def record_access(self,machine,row,component_access_index):
  """Consume a committed source row at an explicit component-local ordinal.

  The caller excludes accepted onexit body accesses, but includes both literal
  raw-IAT and CALL-push rows. WG len(machine.accesses) indexes are never used.
  """
  need(self.active and not self.suspended,'Component journal never consumes provider body operations');row=tuple(row);need(len(row)==5,'Whole independently derived source operand row');pc,address,value,width,writing=row
  equal(component_access_index,len(self.accesses),'Explicit complete component cumulative access ordinal');s=self.geometry.slices[self.root['root']];need(self.local_operand<s[12],'Finite exact current component operand extent')
  ep,role,offset,ew,write=self.geometry.operands[s[11]+self.local_operand];expected=self.root_frame+offset if role==1 else self.TIB if role==2 else offset
  equal((pc,address,width,bool(writing)),(ep,expected,ew,write),'Each real component operation joins physical source PC/role/offset/width/direction');need(0<=value<1<<(8*width),'Whole finite source scalar value');self.accesses.append(row);self.local_operand+=1
  if address==self.TIB:self._FS(machine,pc,value,width,bool(writing))
  if writing:
   for base in list(self.vptrs):
    if address<base+4 and base<address+width:del self.vptrs[base]
   for root,c in self.geometry.roots.items():
    for v in c['virtual_calls']:
     if width==4 and pc==v['source_store_PC'] and value==v['source_vptr']:
      self.vptrs[address]={'pc':pc,'value':value,'root':self.root['root'],'access':component_access_index};break
   for f in self.FS_frames:
    if address<f['frame']+12 and f['frame']<address+width:
     equal(self._word(machine,f['frame']),f['previous'],'Active source FS predecessor conserved');f['handler']=self._word(machine,f['frame']+4);f['scope']=self._word(machine,f['frame']+8)
   return
  if self.local_virtual<len(self.root['virtual_calls']):
   v=self.root['virtual_calls'][self.local_virtual]
   if pc==v['CALL_pc']:
    instance=self.root['object']+v['instance_root_offset'];token=self.vptrs.get(instance)
    need(width==4 and address==v['readonly_slot'] and value==v['target'] and machine.reg('ecx')==instance and token is not None,'Current instance actual ordered source virtual read')
    equal((token['root'],token['pc'],token['value']),(self.root['root'],v['source_store_PC'],v['source_vptr']),'Same current instance root-specific literal vptr store');equal(self._word(machine,instance),v['source_vptr'],'Current carried complete vptr bytes')
    equal(machine.reg('esp')-self.root_frame,v['frame_minus_root_frame'],'Literal virtual caller ESP at the actual slot read before CALL push')
    self.virtuals.append((self.root['root'],pc,instance,token['pc'],token['value'],address,value,component_access_index));self.local_virtual+=1
  if (pc,address)in self.raw_imports:
   raw,target,k=self.raw_imports[(pc,address)];need(width==4 and value==raw and self._word(machine,address)==raw,'Same carried complete own import raw operand')
   need(k not in(3,5),'Unconsumed cold widget CRT imports remain denied');self.imports.append((self.root['root'],pc,address,raw,target,len(self.frames),component_access_index,k))
  if pc==0x7800fcef:
   need(self.root['root']==0x40f000 and address==0x780103fa and width==4 and value==0x7800fe25 and machine.reg('eax')==0 and self.frames and self.frames[-1]['target']==0x7800fc9b and self.frames[-1]['site']==0x78023105,'Literal fps index0 full readonly output dispatch and current output frame')
   count=len(self.dispatches)-self.starts['dispatches'];self.dispatches.append((self.root['root'],pc,address,value,count,self.frames[-1]['frame'],component_access_index,machine.reg('eax')))

 def _FS(self,machine,pc,value,width,writing):
  need(width==4 and self.local_FS<len(self.root['FS_operations']),'Finite current source FS DWORD operation');expected=self.root['FS_operations'][self.local_FS];equal((pc,writing),(expected['PC'],expected['writing']),'Exact current source FS direction/order');old=self.FS_head;kind=0
  if writing:
   if self.FS_frames and value==self.FS_frames[-1]['previous']:
    f=self.FS_frames[-1];equal(old,f['frame'],'Current literal FS restore owns active frame');equal(machine.bytes(f['frame'],12),struct.pack('<3I',f['previous'],f['handler'],f['scope']),'Whole active source FS record before restoration');self.FS_frames.pop();kind=2
   else:
    need(value==machine.reg('esp') and self.stack_low<=value and value+12<=self.stack_top and len(self.FS_frames)<32,'Actual source FS install frame from current ESP');equal(self._word(machine,value),old,'Source-written complete FS predecessor');self.FS_invocation+=1;self.FS_frames.append({'frame':value,'previous':old,'handler':self._word(machine,value+4),'scope':self._word(machine,value+8),'invocation':self.FS_invocation});kind=1
   self.FS_head=value
  else:equal(value,old,'Complete real source FS head read')
  self.FS_events.append((self.root['root'],pc,int(writing),old,value,kind,self.local_FS,len(self.FS_frames)));self.local_FS+=1

 def control(self,machine,event,data,undefined=None):
  if not self.active:return
  if undefined is None:undefined=getattr(machine,'_source_undefined_flags',None)
  if self.suspended:
   if event=='returned' and self.frames and data.get('frame')==self.frames[-1]['frame'] and data.get('target')==self.frames[-1]['ret']:
    f=self.frames[-1];need(f['target']==0x78004a36 and f['site']==0x5ac11e and machine.cursor==f['ret'] and machine.reg('esp')==f['frame']+4,'Actual accepted provider returned to same committed widget CALL')
    for fs in self.FS_frames:equal(machine.bytes(fs['frame'],12),struct.pack('<3I',fs['previous'],fs['handler'],fs['scope']),'Borrowed provider conserves complete active widget FS frame')
    equal(self._word(machine,self.TIB),self.FS_head,'Borrowed provider conserves current widget FS head');self.frames.pop();self.suspended=False
   return
  if event=='control' and data.get('op')=='call':
   site,target=data['site'],data['target'];need(self.accesses and self.geometry.instructions[site][1],'Physical current source CALL instruction');last=self.accesses[-1];frame=machine.reg('esp');ret=site+self.geometry.instructions[site][0]
   equal((last[0],last[1],last[2],last[3],last[4]),(site,frame,ret,4,1),'Actual literal committed CALL return word');equal(self._word(machine,frame),ret,'Complete same current CALL backing bytes');need(len(self.frames)<96,'Current finite native source CALL frame bound');self.frames.append({'target':target,'frame':frame,'ret':ret,'site':site})
   if target==0x78004a36:
    need(site==0x5ac11e,'One genuine widget onexit source import');self.suspended=True;return
   if target==0x5ac2a0:
    candidates=[a for a in self.root['array_invocations']if a['CALL_pc']==site];need(len(candidates)==1,'Exact current source vector helper caller');a=candidates[0];base=self._word(machine,frame+4)
    equal(frame-self.root_frame,a['frame_minus_root_frame'],'Current source vector helper relative frame');equal(base,self.root['object']+a['base_root_offset'],'Same current source vector base object');equal(words(machine.bytes(frame+8,16),4),(a['stride'],a['count'],a['constructor'],a['cold_destructor']),'Whole original source stride/count/constructor/destructor argument words');self.array_frames.append({'frame':frame,'base':base,'site':site,'contract':a,'iteration':0})
   if site==0x5ac2db:
    need(self.array_frames,'Current literal vector iteration frame');a=self.array_frames[-1];c=a['contract'];i=a['iteration'];need(i<c['count'] and machine.reg('esi')==i and machine.reg('ebp')==a['frame']-4 and machine.reg('ecx')==a['base']+i*c['stride'] and target==c['constructor'] and self._word(machine,machine.reg('ebp')+20)==target,'Same helper frame ordered source element callback');self.arrays.append((self.root['root'],a['site'],a['frame'],a['base'],i,machine.reg('ecx'),target,frame));a['iteration']+=1
   if target==0x780230dd:self._format_enter(machine,self.frames[-1],undefined)
  elif event=='returned':
   need(self.frames,'Actual source RET owns widget frame');f=self.frames[-1];need(data['frame']==f['frame'] and data['target']==f['ret'] and self.accesses[-1]==(data['site'],f['frame'],f['ret'],4,0),'Whole actual literal RET saved word and current frame')
   if data['site']==0x5ac30c:
    need(self.array_frames and self.array_frames[-1]['frame']==f['frame'],'Current source vector RET owns helper');a=self.array_frames.pop();need(a['iteration']==a['contract']['count'] and machine.reg('esp')==f['frame']+24,'Complete literal vector count and RET14 frame')
   if f['target']==0x780230dd:self._format_return(machine,f,data,undefined)
   self.frames.pop()
  elif event=='api-returned':
   need(self.pending_api and self.frames,'Exactly one typed source GDI response return');f=self.frames.pop();need(f['site']==data['site'] and f['frame']==data['frame'] and f['ret']==data['target'],'Measured GDI response consumes current genuine source CALL frame')

 def _format_enter(self,machine,f,undefined):
  need(self.root['root']==0x40f000 and not self.formats and f['site']==0x5a2f68 and f['ret']==0x5a2f6e and f['frame']==self.root_frame-140 and undefined is not None,'Exact current source fps formatter CALL context and flag domain')
  destination,fmt,va=words(machine.bytes(f['frame']+4,12),3);need(destination==self.root['object']+0x34 and fmt==0x5e1590 and va==self.root_frame-108 and machine.reg('esi')==self.root['object'],'Complete literal format destination/format/va context');equal(machine.bytes(fmt,16),self.geometry.fps_format,'All physical finite source fps format input bytes')
  self.formats.append({'metadata':(1,self.root['root'],f['site'],0x780230dd,f['frame'],f['ret'],destination,fmt,va,512,16,64),'thread':self.thread,'before':self._format_side(machine,f,undefined),'format':machine.bytes(fmt,16),'complete':False})
 def _format_side(self,machine,f,undefined):
  return {'CPU':tuple(machine.projected_cpu()),'undefined':copy.deepcopy(undefined),'FX':bytes(machine.fx),'frame':machine.bytes(f['frame'],64),'destination':machine.bytes(self.root['object']+0x34,512),'va':machine.bytes(self.root_frame-108,64)}
 def _format_return(self,machine,f,data,undefined):
  need(len(self.formats)==1 and not self.formats[-1]['complete'] and data['site']==0x7802311e and machine.cursor==f['ret'] and machine.reg('esp')==f['frame']+4 and undefined is not None,'Full literal formatter cdecl RET context and known defined-flag domain');v=self.formats[-1];count=len(self.dispatches)-self.starts['dispatches'];equal(count,3,'Exactly three literal fps character dispatches');v['after']=self._format_side(machine,f,undefined);v['metadata']+=(machine.reg('eax'),self.thread,count,1);v['complete']=True

 def _font(self,guest):
  found=[f for f in self.fonts if f['guest']==guest and f['live']];need(len(found)==1,'One current live typed guest/native font generation');return found[0]
 def _handle(self,native,owned,instance):
  need(native,'Measured successful GDI handle return; failure source remains unadmitted')
  if not owned:
   found=[f for f in self.fonts if not f['owned']and f['live']and f['native']==native]
   if found:return found[0]['guest']
  need(len(self.fonts)<128,'Finite exact current source font mapping');self.generation+=1;guest=0x72001000+16*self.generation;self.fonts.append({'guest':guest,'generation':self.generation,'instance':instance,'root':self.root['root'],'native':native,'owned':bool(owned),'live':True});return guest

 def external(self,machine,target,undefined):
  """Apply only current measured native scalars at a genuine typed CALL."""
  need(self.active and not self.suspended and target in TARGETS and self.api_cursor<len(self.apis),'No unresolved or unmeasured widget GDI response');a=self.apis[self.api_cursor];w=a['words'];kind=TARGETS.index(target);c=a['source'];site=SITES[kind]
  need(w[1]==self.root['root'] and w[3]==kind and w[4]==self.local_api and machine.cursor==target and self.frames and self.frames[-1]['site']==site and self.frames[-1]['target']==target,'Exact current literal typed GDI source order')
  frame=machine.reg('esp');need(frame==w[5]==self.root_frame+c['frame_minus_root_frame'] and self._word(machine,frame)==w[6] and w[8]==self.root['object']+c['instance_root_offset'],'Current API source frame/return/instance geometry')
  need(self.imports and self.imports[-1][:3]==(self.root['root'],site,SLOTS[kind]) and self.imports[-1][4]==target,'Same complete literal source owning GDI raw import and typed route')
  equal(tuple(self.flags.project(machine.projected_cpu(),undefined)),tuple(self.flags.project(a['before'],undefined)),'Whole defined source API-entry CPU40');equal(machine.bytes(frame,64),a['frame'],'Whole genuine source API frame64')
  args=words(machine.bytes(frame+4,4*w[7]),w[7]);equal(args,a['args'][:w[7]],'All literal source API argument DWORDs');equal(a['args'][w[7]:],(0,)*(14-w[7]),'Every unused initialized API argument DWORD')
  font=None
  for value,arg in zip(args,c['argument_contract']):
   if arg['kind']=='literal_constant':equal(value,arg['value'],'Exact physical literal API argument')
   else:
    need(arg['kind']=='source_instance_live_handle','No untyped source API pointer/handle argument');address=self.root['object']+arg['instance_root_offset']+arg['field_offset'];equal(value,self._word(machine,address),'Same current source object font-field argument');font=self._font(value)
  hw=a['hardware'];before_native=struct.unpack_from('<4Q',hw,0);after_native=struct.unpack_from('<4Q',hw,576);need(after_native[0]==w[10],'Measured full native GDI RAX identity')
  rcx=font['native']if kind==1 else args[0]if args[0]<0x80000000 else args[0]|0xffffffff00000000;rdx=(args[1]if args[1]<0x80000000 else args[1]|0xffffffff00000000)if kind==2 else 0;equal(before_native[1:3],(rcx,rdx),'Actual full native RCX/RDX derive from source literal or live typed handle')
  if kind!=2:equal(before_native[0],0,'Actual native ASM RAX retains zero initialized argument13 for stock/delete')
  face=None
  if kind==2:
   for count in range(256):
    if machine.bytes(args[13]+count,1)==b'\0':face=machine.bytes(args[13],count);break
   need(face is not None,'Bounded genuine source face string')
  result=self._handle(after_native[0],kind==2,w[8])if kind in(0,2)else after_native[0]&0xffffffff
  if kind==1:
   need(font is not None,'Actual DeleteObject guest argument has current typed native mapping')
   if font['owned']and result:font['live']=False
  equal((w[9],w[15]),(result,self.generation),'Guest scalar/token and complete generation independently derived from measured native response')
  before_FX=bytes(machine.fx);self.pending_api=True
  try:machine.api_return(site,w[7],result)
  finally:self.pending_api=False
  machine.reg('ecx',after_native[1]);machine.reg('edx',after_native[2])
  for flag,bit in BITS.items():machine.flag(flag,(after_native[3]>>bit)&1)
  new_undefined={k:copy.deepcopy(v)for k,v in undefined.items()if k not in ARITH};equal(tuple(self.flags.project(machine.projected_cpu(),new_undefined)),tuple(self.flags.project(a['after'],new_undefined)),'Whole defined source CPU after explicit measured native volatile projection');equal(bytes(machine.fx),before_FX,'Every guest FX512 byte unchanged by native GDI response')
  self.responses.append({'serial':a['serial'],'root':self.root['root'],'ordinal':self.local_api,'CALL_pc':site,'source_frame':frame,'instance':w[8],'service':NAMES[kind],'source_arguments':args,'guest_result_derived':result,'native_RAX':after_native[0],'native_RCX':after_native[1],'native_RDX':after_native[2],'native_RFLAGS':after_native[3],'native_target':w[11],'thread':w[12],'LastError_before_after_observed_not_transported':w[13:15],'generation':self.generation,'source_face_hex':None if face is None else face.hex(),'host_face_pointer_identity_observed':False,'native_full_call_argument_capture_claimed':False,'full_guest_FX_unchanged':True,'API_record_sha256':hashlib.sha256(a['bytes']).hexdigest()});self.api_cursor+=1;self.local_api+=1;return new_undefined

 def end_root(self,machine,getter,prefix):
  need(callable(getter) and isinstance(prefix,str) and prefix.endswith('/') and self.active and not self.suspended and not self.pending_api,'Caller-owned current cumulative source component getter and closed root')
  root=self.root['root'];s=self.geometry.slices[root];need((self.local_api,self.local_virtual,self.local_FS,self.local_operand)==(s[6],s[8],s[10],s[12]) and not self.frames and not self.FS_frames and not self.array_frames,'Whole finite literal prefix/provider/tail root closure')
  need(machine.cursor==self.saved_return and machine.reg('esp')==self.root_frame+4 and self._word(machine,self.TIB)==self.initial_FS,'Complete actual persistent scheduler return and source FS conservation')
  stem=prefix+'root-'+str(root)+'/after/'
  def get(name):
   result=getter(stem+name);need(isinstance(result,bytes),'Actual authenticated complete current component byte payload');return result
  equal(get('APIs.bin'),self.api_bytes[:self.api_cursor*API_BYTES],'Every complete cumulative current native GDI record belongs to the same response stream')
  for name,attr,size,fmt in(('accesses.bin','accesses',24,'<IIQII'),('imports.bin','imports',32,'<8I'),('virtuals.bin','virtuals',32,'<8I'),('arrays.bin','arrays',32,'<8I'),('FS-events.bin','FS_events',32,'<8I'),('format-dispatches.bin','dispatches',32,'<8I')):equal(rows(get(name),size,fmt),getattr(self,attr),'All complete current component '+name+' independently derived cumulative rows')
  equal(get('frames.bin'),b'','No live source CALL frame after actual root RET');equal(get('FS-frames.bin'),b'','No live source FS record after actual root RET')
  fonts=get('fonts.bin');expected=[(f['guest'],f['generation'],f['instance'],f['root'],f['native'],int(f['owned']),int(f['live']))for f in self.fonts];equal(rows(fonts,32,'<IIIIQBB6x'),expected,'Every typed source/native font generation/instance/ownership/live field')
  status=get('status.bin');equal(len(status),96,'Whole current private component12Q status');equal(struct.unpack('<12Q',status),(self.thread,self.selected+1,root,self.root_frame,0,0,0,self.local_api,self.local_virtual,self.local_FS,self.generation,self.FS_invocation),'All complete private source component context status fields')
  format_raw=get('formats.bin');equal(len(format_raw),len(self.formats)*2528,'Whole cumulative source formatter context record extent')
  for ordinal,v in enumerate(self.formats):
   need(v['complete'],'Complete source-derived formatter lifetime');b=format_raw[ordinal*2528:(ordinal+1)*2528];equal(struct.unpack_from('<16Q',b),v['metadata'],'All current16Q literal formatter context metadata')
   for side,offset in(('before',128),('after',168)):equal(tuple(self.flags.project(words(b,10,offset),v[side]['undefined'])),tuple(self.flags.project(v[side]['CPU'],v[side]['undefined'])),'Whole defined source formatter CPU40 '+side)
   for field,offset,size in(('FX',208,512),('destination',1232,512),('frame',2256,64),('va',2384,64)):
    for side,i in(('before',0),('after',1)):equal(b[offset+i*size:offset+(i+1)*size],v[side][field],'Complete literal formatter '+field+' '+side)
   equal(b[2512:2528],v['format'],'Every physical finite source format input byte')
  proof={'root':root,'selected':self.selected,'actual_source_count':self.local_api,'source_counts':{'operands':self.local_operand,'virtual':self.local_virtual,'FS':self.local_FS,'array_rows':len(self.arrays)-self.starts['arrays'],'imports':len(self.imports)-self.starts['imports']},'component_access_begin':self.starts['accesses'],'component_access_end':len(self.accesses),'root_frame':self.root_frame,'scheduler_return':self.saved_return,'source_entry_context':self.entry_context,'computed_final_State_sha256':hashlib.sha256(bytes(machine.state)).hexdigest(),'computed_final_FX_sha256':hashlib.sha256(bytes(machine.fx)).hexdigest(),'API_response_derivations':copy.deepcopy(self.responses[self.starts['responses']:]),'font_padding_observed_but_not_source_defined':[fonts[p+26:p+32].hex()for p in range(0,len(fonts),32)],'source_order_verified':True,'component_context_verified':True,'native_physical_API_identity_verified_by_adapter':False,'whole_root_State_or_memory_comparison_owned_by_caller':True,'AFTER_State_or_memory_seed':False,'guest_FX_transport':False,'original_GDI_handle_seed':False,'WG_global_access_indexes_used_for_witness_equality':False,'accepted_onexit_provider_body_owned_by_caller':True,'source_callback_teardown_executed':False,'initializer_credit':0};self.proofs.append(proof);self.active=False;self.root=None;self.selected+=1;return proof

 def finish(self):
  need(not self.active and self.selected==7 and self.api_cursor==len(self.apis)==149 and len(self.accesses)==25003 and len(self.virtuals)==511 and len(self.FS_events)==588,'All exact actual measured responses and independently derived source rows exhausted')
  owned=[copy.deepcopy(f)for f in reversed(self.fonts)if f['owned']and f['live']];need(len(owned)==15,'Actual current literal path leaves exactly fifteen owned live source-created fonts for manual cleanup')
  return {'passed':True,'source_counts':self.geometry.summary(),'roots':copy.deepcopy(self.proofs),'source_owned_live_fonts_in_manual_cleanup_order':owned,'expected_manual_cleanup_serials':list(range(149,164)),'manual_font_cleanup_verified_by_adapter':False,'manual_owned_font_cleanup_comparison_owned_by_caller':True,'native_physical_API_identity_verified_by_adapter':False,'source_registration_provider_comparison_owned_by_caller':True,'whole_root_State_or_memory_comparison_owned_by_caller':True,'source_callback_teardown_executed':False,'archive_reader_opened_by_adapter':False,'worker_executed_by_adapter':False,'AFTER_State_or_memory_seed':False,'initializer_credit':0}
