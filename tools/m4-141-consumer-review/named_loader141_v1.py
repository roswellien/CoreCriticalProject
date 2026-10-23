"""Current PE32 named CRT API inputs proven from genuine loaded module exports."""
from pathlib import Path
import re,struct
CELLS=(0x7802e094,0x7802e090,0x7802e1dc,0x7802e0b4,0x7802e03c,0x7802e044,0x7802e048,0x7802e040)
NAMES=('HeapAlloc','HeapFree','HeapSize','HeapReAlloc','InitializeCriticalSection','EnterCriticalSection','LeaveCriticalSection','DeleteCriticalSection')
ROOTS={13:0x4103f0,14:0x410440,39:0x459b40}
def need(v,s):
 if not v:raise ValueError(s)
def export_target(modules,declared,name):
 seen=set();chain=[];base=declared;symbol=name
 while True:
  need((base,symbol)not in seen and len(seen)<8,'Finite acyclic owning PE export/forwarder chain');seen.add((base,symbol));module=modules[base];exports=module['image'].exports();matches=[e for e in exports if (str(e['ordinal'])==symbol[1:]if symbol.startswith('#')else symbol in e['names'])];need(len(matches)==1,'Unique actual named/ordinal loaded PE export '+symbol);e=matches[0];chain.append(dict(base=base,name=module['name'],symbol=symbol,rva=e['rva'],forwarder=e.get('forwarder')))
  if 'forwarder'not in e:return base+e['rva'],base,chain
  dll,symbol=e['forwarder'].rsplit('.',1);dll=dll.upper()+('.DLL'if not dll.upper().endswith('.DLL')else'');matches=[b for b,m in modules.items()if m['name']==dll];need(len(matches)==1,'Actual captured forwarder module identity '+dll);base=matches[0]
def prove(records,PEImage,pin,shim_addresses,crt_image,patch_declarations):
 need(len(shim_addresses)==8 and len(set(shim_addresses))==8,'Eight unique current compiled CRT observer entries')
 imported={crt_image.image_base+x['iat_rva']:(g['library'],x)for g in crt_image.imports()for x in g['symbols']}
 for cell,name in zip(CELLS,NAMES):need(cell in imported and imported[cell][0].upper()=='KERNEL32.DLL'and imported[cell][1]['name']==name,'Exact physical staged CRT owning import cell/name')
 modules={};evidence=[]
 pattern=r'(lockit/modules|mfc-modules|widget/modules)/(\d+)/image\.bin'
 for key in records.entries:
  match=re.fullmatch(pattern,key)
  if not match:continue
  base=int(match[2]);path_key=key[:-9]+'path.bin';path=records.data(path_key).decode('utf-16-le').rstrip('\0');need(path and '\0'not in path,'Actual loader path UTF16 identity');image=records.data(key);disk=Path(re.sub(r'(?i)system32',lambda m:'SysWOW64',path))if path.lower().startswith('c:\\windows\\system32\\')else Path(path);need(pin(disk).read_bytes()==image,'Current actual32 module captured whole image equals its physical disk image');pe=PEImage(image);need(pe.machine==0x14c and base>0 and base%4096==0,'Actual x86 loaded module base/image');name=Path(path).name.upper()
  if base in modules:need(modules[base]['bytes']==image and modules[base]['name']==name,'Aliased loader captures bind identical whole module')
  else:modules[base]=dict(name=name,bytes=image,image=pe)
  evidence.append(dict(base=base,name=name,image_key=key,path_key=path_key,disk=str(disk)))
 need(modules,'Actual loaded declared and forwarder module inventory')
 raw=records.data('crt-api-targets.bin');need(len(raw)==32,'Whole genuine eight API target observation');targets=struct.unpack('<8I',raw);rows=[]
 for seq in range(6):
  for phase,root in ROOTS.items():
   stem=f'phase/{seq}/{phase}/';raw=records.data(stem+'constructor-input/named-API-bindings.bin');need(len(raw)==224,'Eight complete sevenDWORD named-binding rows')
   segment=records.data(stem+'constructor-input/segments-before.bin');need(len(segment)==136 and struct.unpack_from('<2I',segment)==(1,root),'Same own input phase/root descriptor identity')
   page=records.data(stem+'CRT-image/before/'+str(0x7802e000)+'.bin');need(len(page)==4096,'Own complete before CRT IAT page')
   for i,w in enumerate(struct.iter_unpack('<7I',raw)):
    kind,cell,actual,target,shim,declared,owner=w;need((kind,cell,actual,shim)==(i,CELLS[i],shim_addresses[i],shim_addresses[i])and target==targets[i]and declared in modules and owner in modules,'Same typed source input and current wholly linked observer IAT');need(modules[declared]['name']=='KERNEL32.DLL','Actual declared owning import library');need(struct.unpack_from('<I',page,cell%4096)[0]==actual,'Named input rejoined to complete own BEFORE rawcell')
    resolved,owner_base,chain=export_target(modules,declared,NAMES[i]);need(target==resolved and owner==owner_base,'Actual loaded named export including exact forwarder owner');rows.append(dict(sequence=seq,phase=phase,root=root,kind=i,cell=cell,raw=actual,target=target,shim=shim,declared=declared,owner=owner,export_chain=chain))
 patches=[]
 for d in patch_declarations:
  d=dict(d)
  if d['kind']=='registry-IAT':
   need(d['pc']in CELLS and d['original_hex']is None,'Only eight explicitly dynamic named target spans');i=CELLS.index(d['pc']);need(d['named_API']==NAMES[i]and d['instrumented_hex']==struct.pack('<I',shim_addresses[i]).hex(),'Same exact physical API declaration/current compiled entry');d['original_hex']=struct.pack('<I',targets[i]).hex()
  patches.append(d)
 need(len(patches)==13 and len(rows)==144,'Complete13 spans and18×8 same-own-input named identities')
 return patches,dict(passed=True,API_targets=list(targets),named_binding_rows=rows,loaded_modules=evidence,own_before_input=True,source_AFTER_seed=False)
