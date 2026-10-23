"""Strict additional typed original37 input capture geometry; no source execution."""
import struct
EXACT_SHIMS=(671271164, 671271211, 671271258, 671271305, 671271352, 671271399, 671271443, 671271487)
CELLS=(0x7802e094,0x7802e090,0x7802e1dc,0x7802e0b4,0x7802e03c,0x7802e044,0x7802e048,0x7802e040)
def words(b,n=None):
 assert len(b)%4==0
 if n is not None:assert len(b)==4*n
 return struct.unpack('<'+'I'*(len(b)//4),b)
def validate(reader,stem,root,counts,shim_addresses):
 assert root in(0x4103f0,0x410440,0x459b40);prefix=stem+'/CRT-image/';meta=reader.data(prefix+'metadata.bin');assert len(meta)%12==0 and meta;rows=list(struct.iter_unpack('<3I',meta));pages=[v[0]for v in rows];assert len(set(pages))==len(pages)and pages==sorted(pages)and all(0x78000000<=a<0x78040000 and a%4096==0 and not(flags&0x101)and typ==0x1000000 for a,flags,typ in rows);assert {0x7802e000,0x78035000,0x78037000}<=set(pages)
 before={};after={}
 for a,flags,typ in rows:
  before[a]=reader.data(prefix+'before/'+str(a)+'.bin');after[a]=reader.data(prefix+'after/'+str(a)+'.bin');assert len(before[a])==len(after[a])==4096
  if flags in(2,0x10,0x20):assert before[a]==after[a]
  counts['own_whole_CRT_input_endpoint_pages']+=2
 assert before[0x7802e000]==after[0x7802e000]
 binding=words(reader.data(stem+'/constructor-input/named-API-bindings.bin'),56)
 for i in range(8):
  kind,cell,raw,target,shim,declared,owner=binding[7*i:7*i+7];assert kind==i and cell==CELLS[i]and raw==shim==shim_addresses[i]and target and declared and owner and shim==EXACT_SHIMS[i];assert words(before[0x7802e000][cell%4096:cell%4096+4],1)[0]==raw;counts['own_actual_named_API_observer_bindings']+=1
 segments=words(reader.data(stem+'/constructor-input/segments-before.bin'),34);assert segments[:2]==(1,root)and segments[2];bases={}
 for i,name in enumerate(('cs','ds','es','ss','fs','gs')):
  selector,base,limit,high,observed=segments[4+5*i:9+5*i];assert observed==1
  if selector:assert base==((high>>24)<<24)|(((high>>0)&255)<<16)|(base&65535)
  else:assert base==limit==high==0
  bases[name]=base
 assert bases['cs']==bases['ds']==bases['es']==bases['ss']==0 and bases['fs']and bases['fs']%4096==0
 first=reader.data(stem+'/fs-events.bin')[:1216];event=words(first[:32],8);assert event[:2]==(1,root)and event[3]==0 and event[4]==event[5]==segments[3];counts['own_descriptor_FS_before_head_joins']+=1
 ledger=reader.data(stem+'/api-ledger.bin');assert len(ledger)%104==0;selected=[]
 for index,api in enumerate(struct.iter_unpack('<26I',ledger)):
  if api[24]not in(5,6):continue
  identity=words(reader.data(stem+'/constructor-input/CS-API/'+str(index)+'/identity.bin'),5);assert identity==(1,index,api[24],api[20],api[25]);assert len(reader.data(stem+'/constructor-input/CS-API/'+str(index)+'/before.bin'))==len(reader.data(stem+'/constructor-input/CS-API/'+str(index)+'/after.bin'))==24;selected.append(index);counts['actual_whole_CRT_CS_API_joins']+=1
 return dict(root=root,bases=bases,thread=segments[2],head=segments[3],CRT_pages=pages,CS_API_indices=selected)
