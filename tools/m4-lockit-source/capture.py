"""Typed API/capture adapter adds explicit MSVCP resource association lifecycle."""
from pathlib import Path
import importlib.util,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-onexit-review'))
import provider_capture as C
P=C.P
checkpoints=C.checkpoints;checkpoint=C.checkpoint
LOCKIT_NAMES={0x7810a30b:'EnterCriticalSection',0x7810a35e:'LeaveCriticalSection'}
def api_facts(archive,stem):
 contracts=P.R.B.contracts();contracts.update(P.R.NEW_CONTRACTS);facts=[];growth={}
 for logical in archive.entries:
  if logical.startswith(stem+'registry-growth-')and logical.endswith('-witness.bin'):
   w=archive.words(logical,32,'Q');P.I.need(w[1]not in growth,'One genuine actual growth per API');growth[w[1]]=w
 for index in range(archive.words(stem+'locale-summary.bin',32)[18]):
  prefix=stem+'locale-api-'+str(index);w=archive.words(prefix+'-witness.bin',32,'Q');inputs=[];outputs=[]
  for suffix,target in(('input',inputs),('output',outputs)):
   k=0
   while prefix+'-'+suffix+'-'+str(k)+'.bin'in archive.entries:target.append(archive.data(prefix+'-'+suffix+'-'+str(k)+'.bin'));k+=1
  if w[31]:
   if w[3]==0x78146190:name='InitializeCriticalSection'
   elif w[3]==0x7802e090:name='HeapFree'
   elif w[3]in(0x7802e048,0x78146184):name='LeaveCriticalSection'
   else:name='DeleteCriticalSection'
  elif w[2]in LOCKIT_NAMES:name=LOCKIT_NAMES[w[2]]
  else:name=contracts[w[2]]['name']
  buffers=archive.data(prefix+'-buffers.bin');P.I.need(len(buffers)%16==0,'Complete typed API buffer rows')
  fact=dict(words=w,inputs=inputs,outputs=outputs,name=name,buffers=list(struct.iter_unpack('<4I',buffers)))
  if index in growth:fact['growth']=growth[index]
  facts.append(fact)
 return facts
def bootstrap_inputs(archive,stem,index=None):
 index=index or checkpoints(archive,stem);before=checkpoint(archive,index,'registry-bootstrap-before')
 heap=dict(create=archive.words(stem+'heap-create-witness.bin',16,'Q'),registry=archive.words(stem+'heap-create-registry.bin',18,'Q'),query=archive.words(stem+'heap-query-witness.bin',20,'Q'),input=archive.data(stem+'heap-query-input.bin'),output=archive.data(stem+'heap-query-output.bin'))
 rows=list(struct.iter_unpack('<8I',archive.data(stem+'registry-research-projections.bin')));P.I.need(rows and rows[0][0]==1 and rows[0][3:5]==(0x5bb514,0x20001860),'Declared source import/stack bootstrap projection')
 return before,api_facts(archive,stem),heap,rows[0][1],rows[0][2]
