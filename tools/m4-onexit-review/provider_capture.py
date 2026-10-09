"""Strict capture adapter: BEFORE machine inputs and finite API facts only."""
import struct
import provider_bridge as P
def checkpoints(archive,stem):
 return {archive.data(logical).decode():logical[:-9]for logical in archive.entries if logical.startswith(stem+'registry-checkpoint-')and logical.endswith('-name.bin')}
def checkpoint(archive,index,name):
 prefix=index[name]
 return dict(state=archive.data(prefix+'-state.bin'),fx=archive.data(prefix+'-fx.bin'),cpu=archive.data(prefix+'-cpu.bin'),runtime_cpu=archive.data(prefix+'-runtime-cpu.bin'),
             memory={int(logical[len(prefix)+6:-4]):archive.data(logical)for logical in archive.entries if logical.startswith(prefix+'-page-')})
def api_facts(archive,stem):
 contracts=P.R.B.contracts();contracts.update(P.R.NEW_CONTRACTS);facts=[];growth={}
 for logical in archive.entries:
  if logical.startswith(stem+'registry-growth-')and logical.endswith('-witness.bin'):
   words=archive.words(logical,32,'Q');P.I.need(words[1]not in growth,'One actual growth row per genuine typed API');growth[words[1]]=words
 for index in range(archive.words(stem+'locale-summary.bin',32)[18]):
  prefix=stem+'locale-api-'+str(index);words=archive.words(prefix+'-witness.bin',32,'Q');inputs=[];outputs=[]
  for suffix,target in (('input',inputs),('output',outputs)):
   k=0
   while prefix+'-'+suffix+'-'+str(k)+'.bin'in archive.entries:target.append(archive.data(prefix+'-'+suffix+'-'+str(k)+'.bin'));k+=1
  if words[31]:name='HeapFree'if words[3]==0x7802e090 else'LeaveCriticalSection'if words[3]==0x7802e048 else'DeleteCriticalSection'
  else:name=contracts[words[2]]['name']
  buffers=archive.data(prefix+'-buffers.bin');P.I.need(len(buffers)%16==0,'Complete finite source API buffer records')
  fact=dict(words=words,inputs=inputs,outputs=outputs,name=name,buffers=list(struct.iter_unpack('<4I',buffers)))
  if index in growth:fact['growth']=growth[index]
  facts.append(fact)
 return facts
def bootstrap_inputs(archive,stem,index=None):
 index=index or checkpoints(archive,stem)
 before=checkpoint(archive,index,'registry-bootstrap-before')
 heap=dict(create=archive.words(stem+'heap-create-witness.bin',16,'Q'),registry=archive.words(stem+'heap-create-registry.bin',18,'Q'),query=archive.words(stem+'heap-query-witness.bin',20,'Q'),input=archive.data(stem+'heap-query-input.bin'),output=archive.data(stem+'heap-query-output.bin'))
 projections=archive.data(stem+'registry-research-projections.bin');P.I.need(len(projections)%32==0,'Complete declared registry research projections')
 rows=list(struct.iter_unpack('<8I',projections));P.I.need(rows and rows[0][0]==1 and rows[0][3:5]==(0x5bb514,0x20001860),'Declared source import/stack bootstrap projection')
 return before,api_facts(archive,stem),heap,rows[0][1],rows[0][2]
