"""Source-driven font ownership joins; never predicts an API handle or executes cleanup."""
import struct
def need(v,m):
 if not v:raise ValueError(m)
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
class Generations:
 def __init__(self,sequence):self.sequence=sequence;self.created=[];self.live={};self.stock={};self.pending={};self.joins=[]
 def gdi(self,model,before,after,phase,root):
  """Caller must first establish literal CALL/args and complete GDI CPU/FX/pages."""
  api=before['API'];instance=model.reg('esi');handle=after['CPU'][0]
  need(instance==before['CPU'][6]==after['CPU'][6]==before['header'][11]==after['header'][11],'Same source/API font instance')
  if api=='CreateFontA':
   need(handle and all(h!=handle for _,h in self.live),'Successful nonaliased finite font acquisition')
   row=dict(sequence=self.sequence,occurrence=len(self.created),phase=phase,root=root,instance=instance,handle=handle,created_event=after['index'],live=True,deleted_event=None,source_CALL_pc=0x5a074b,source_owning_store=None)
   self.created.append(row);self.live[(instance,handle)]=row;need(instance not in self.pending,'One unbound same-instance source acquisition');self.pending[instance]=row
  elif api=='GetStockObject':self.stock[instance]=handle
  elif api=='DeleteObject':
   arg=before['arguments'][0];need(words(model.bytes(instance+0x258,4))[0]==arg,'Literal current source owning field equals DeleteObject argument');key=(instance,arg)
   need(key in self.live or self.stock.get(instance)==arg,'Same-instance acquisition dominates source deletion')
   if key in self.live and handle:
    row=self.live.pop(key);need(row['source_owning_store']is not None,'Created handle source owning-store established before deletion');row.update(live=False,deleted_event=after['index'])
  else:raise ValueError('Exact named font services only')
 def store(self,model,pc,address,value,width,domain):
  if domain!='source'or pc!=0x5a0753:return
  instance=model.reg('esi');need(width==4 and address==instance+0x258 and value==model.reg('eax'),'Exact literal CreateFont return owning store')
  row=self.pending.pop(instance,None);need(row is not None and row['handle']==value,'Own finite response consumed by same-instance literal store');need(model.bytes(address,4)==struct.pack('<I',value),'Full owning field source store completed');row['source_owning_store']=dict(PC=pc,address=address,value=value,source_access_index=len(model.accesses)-1);self.joins.append(dict(row))
 def phase(self,raw):
  need(not self.pending and len(raw)==32*len(self.created),'Whole source occurrence inventory with every creation bound')
  for i,row in enumerate(self.created):
   expected=(1,i,row['root'],row['instance'],row['handle'],row['created_event'],int(row['live']),0xffffffff if row['live']else row['deleted_event']);need(words(raw,32*i,8)==expected,'Whole actual phase occurrence equals source generation/liveness')
 def cleanup(self,resources,read,lifetimes):
  need(not self.pending and len(resources)==32*len(self.created),'Whole same-sequence cleanup resource inventory');expected_lifetimes=[r for r in lifetimes if r['sequence']==self.sequence];need(len(expected_lifetimes)==len(self.created),'All current lifetime observations compared')
  for i,row in enumerate(self.created):
   h=words(resources,i*32,8);need(h[:6]==(1,i,row['root'],row['instance'],row['handle'],row['created_event']),'Exact source generation cleanup identity')
   if row['live']:
    c=read(i);need(len(c)==1112 and words(c,0,4)==(1,i,row['instance'],row['handle'])and words(c,16)[0]!=0 and words(c,28)[0]==1 and h[6:]==(0,0xfffffffe),'Successful same-instance owned-only manual cleanup');need(c[32:544]==c[544:1056]and c[1056:1084]==c[1084:1112],'Whole actual manual cleanup FX/ENV conserved')
    row.update(manual_cleanup_BOOL=words(c,16)[0],FX_BEFORE_hex=c[32:544].hex(),FX_AFTER_hex=c[544:1056].hex(),ENV_BEFORE_hex=c[1056:1084].hex(),ENV_AFTER_hex=c[1084:1112].hex())
   else:need(h[6:]==(0,row['deleted_event']),'Already source-deleted generation omitted from manual cleanup')
   observed=expected_lifetimes[i]
   for k,v in observed.items():need(row.get(k)==v,'Actual lifetime '+k+' equals source ownership plus typed manual cleanup')
  return dict(source_generations=len(self.created),source_owned_stores=len(self.joins),manual_cleanup_is_source_callback=False,source_shutdown_executed=False)
