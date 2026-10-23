"""Current supplemented original37 own BEFORE pages/descriptors/API observations only."""
import struct,re,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('original_pages_parent',Path(__file__).with_name('constructor_original_input_v2.py'));P=importlib.util.module_from_spec(s);s.loader.exec_module(P);PAGES=P.PAGES;need=P.need
def rows(b,n):
 need(len(b)%(4*n)==0,'Exact bounded observation width');return list(struct.iter_unpack('<'+str(n)+'I',b))
def build(a,seq,root,program,provider_proof):
 need(provider_proof['passed']and list(a.words('constructor/provider-entries.bin',7))==provider_proof['provider_entry_expected'],'Actual current loaded owning MFC/CRT provider-entry identities');targets=provider_proof['targets']
 phase={0x4103f0:13,0x410440:14,0x459b40:36}[root];stem=f'phase/{seq}/{phase}';raw=a.data(stem+'.bin');need(len(raw)==356992,'Whole own current original Record');memory={page:raw[2276+i*4096:2276+(i+1)*4096]for i,page in enumerate(PAGES)}
 for key in a.entries:
  if key.startswith(stem+'/extra-before/'):memory[int(key.rsplit('/',1)[1][:-4])]=a.data(key)
 prefix=stem+'/CRT-image/';metadata=rows(a.data(prefix+'metadata.bin'),3);need({0x7802e000,0x78035000,0x78037000}<={w[0]for w in metadata},'Complete needed own CRT input pages')
 for page,flags,typ in metadata:
  b=a.data(prefix+'before/'+str(page)+'.bin');need(0x78000000<=page<0x78040000 and page%4096==0 and len(b)==4096 and typ==0x1000000 and not flags&0x101,'Actual readable own CRT whole page');memory[page]=b
 graph='constructor-prerequisites/'+stem+'/';memory[0x5f2000]=a.data(graph+'BEFORE-constructor/5F2000.bin');owners=[]
 for key in sorted(a.entries):
  if not(key.startswith(graph+'BEFORE-owners/')and key.endswith('/meta.bin')):continue
  w=a.words(key,12);b=a.data(key[:-8]+'bytes.bin');need(w[0]==1 and w[9]==1 and len(b)==w[8]and w[6]<=len(b),'Complete current live own backing');memory[w[7]]=b;owners.append(dict(guest=w[7],requested=w[6],extent=w[8],mapped_bytes=w[8],initial_hex=b.hex(),mapped_tail_hex='',generation=w[1],kind=w[4],capacity=w[8],live=True))
 for side in ('BEFORE-constructor','BEFORE-member'):
  n=a.words(graph+side+'/nodes-count.bin',1)[0]
  for i in range(n):
   w=a.words(graph+side+f'/node-{i}/meta.bin',10);b=a.data(graph+side+f'/node-{i}/bytes.bin');need(w[:2]==(1,i)and len(b)==w[3],'Complete own graph node');memory[w[2]]=b
 segment=a.words(stem+'/constructor-input/segments-before.bin',34);need(segment[:2]==(1,root)and segment[2],'Own original actual descriptor identity');bases={name:segment[5+5*i]for i,name in enumerate(('cs','ds','es','ss','fs','gs'))};need(bases['ds']==bases['es']==bases['ss']==bases['cs']==0 and bases['fs'],'Actual flat used segments and FS base');first=a.data(stem+'/fs-events.bin')[:1216];f=struct.unpack_from('<8I',first);need(f[:2]==(1,root)and f[3]==0 and f[4]==f[5]==segment[3],'Direct own FS-head observation before any source read/write');memory[bases['fs']]=struct.pack('<I',segment[3])
 named=rows(a.data(stem+'/constructor-input/named-API-bindings.bin'),7);need(len(named)==8 and [v[0]for v in named]==list(range(8)),'Complete own named API/shim identities');bycell={w[1]:w for w in named};imports=[dict(PC=pc,address=address,raw=int.from_bytes(memory[address&~4095][address%4096:address%4096+4],'little'),target=target,owning_named_input=True)for pc,address,target in((0x5abd1a,0x5bb4c8,targets['825']),(0x5abd26,0x5bb4bc,targets['823']),(0x5ac11e,0x5bb52c,targets['_onexit']),(0x5f401786,0x5f498148,targets['free']),(0x5f401ea1,0x5f49814c,targets['malloc']))]
 for fact in imports:need(fact['raw']==fact['target'],'Exact actual owning loaded import equals independently resolved named target')
 for pc,row in sorted(program.items()):
  if row['mnemonic']!='call' or len(row['decoded_operands'])!=1:continue
  operand=row['decoded_operands'][0]
  if operand['kind']!='memory' or operand.get('terms'):continue
  cell=operand.get('displacement')
  if cell not in bycell:continue
  kind,cell,rawcell,target,shim,declared,owner=bycell[cell];need(rawcell==shim and target and declared and owner and int.from_bytes(memory[cell&~4095][cell%4096:cell%4096+4],'little')==rawcell,'Exact own observed patched import cell/named target');imports.append(dict(PC=pc,address=cell,raw=rawcell,target=target,owning_named_input=True,observer_projection=True,API_kind=kind))
 occurrences=rows(a.data(graph+'occurrences.bin'),12);APIs=[]
 for index,w in enumerate(rows(a.data(stem+'/api-ledger.bin'),26)):
  kind=w[24];argc=3 if kind in(0,1,2)else 4 if kind==3 else 1;need(w[9]==w[19]==0,'Actual nine DWORD CPU projection: raw PC exactly zero');candidates=[row for pc,row in program.items()if row['mnemonic']=='call'and pc+row['width']==w[25]];need(len(candidates)==1,'Unique literal API CALL/return');row=candidates[0];cell=row['decoded_operands'][0]['displacement'];binding=bycell[cell];need(binding[0]==kind,'Typed owning named API kind');after=list(w[10:20]);after[9]=w[25];fact=dict(site=row['pc'],target=binding[3],argc=argc,args=list(w[20:20+argc]),before_cpu=list(w[:10]),after_cpu=after,raw_CPU_PC_zero=True,modeled_return_PC_separate=w[25],initial_allocations=[],input_buffers=[],output_buffers=[])
  if kind==0:
   matches=[v for v in occurrences if v[2:5]==(phase,index,0)];need(len(matches)==1,'Exact typed current allocation occurrence');v=matches[0];b=a.data(stem+f'/api-initial/{index}/bytes.bin');need(v[5:9]==(w[20],w[22],w[10],len(b))and len(b)==a.words(stem+f'/api-initial/{index}/size.bin',1)[0],'Actual own initial full capacity/request/result');fact['initial_allocations']=[dict(guest=v[7],requested=v[6],actual_API_requested=v[6],extent=v[8],mapped_bytes=v[8],initial_hex=b.hex(),mapped_tail_hex='',generation=v[1],kind=v[4],capacity=v[8],live=True)]
  elif kind in(5,6):
   cp=stem+f'/constructor-input/CS-API/{index}/';need(a.words(cp+'identity.bin',5)==(1,index,kind,w[20],w[25]),'Exact typed current source API CS24 occurrence');before=a.data(cp+'before.bin');afterbuf=a.data(cp+'after.bin');need(len(before)==len(afterbuf)==24,'Full actual Win32 CS opaque input/output');fact['input_buffers']=[dict(address=w[20],bytes=24,hex=before.hex())];fact['output_buffers']=[dict(address=w[20],bytes=24,hex=afterbuf.hex())]
  else:need(kind==2,'Only literal closed constructor HeapAlloc/HeapSize/Enter/Leave domain')
  APIs.append(fact)
 return dict(branch='original',root=root,BEFORE_CPU_hex=raw[36:76].hex(),BEFORE_FX_hex=raw[116:628].hex(),BEFORE_ENV28_hex=raw[2164:2192].hex(),BEFORE_segment_bases=bases,BEFORE_memory={str(k):v.hex()for k,v in memory.items()},owners=owners,APIs=APIs,imports=imports,original_State_observed=False,source_AFTER_seed=False,FS_base_directly_observed=True,FS_head_directly_observed=True,whole_TIB_claim=False,whole_State_claim=False,thread_ID=segment[2])
