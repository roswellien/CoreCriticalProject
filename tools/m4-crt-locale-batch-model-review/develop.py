"""Read-only development comparisons; no native admission or completion credit."""
import hashlib,json,struct,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
import before_bridge as BB
import batch
import interpreter_v2 as I
ROOT=I.ROOT
sys.path.insert(0,str(ROOT/'tools/m4-crt-allocation-model-review'))
from transport import StrictUnion

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def add(p,h=None):
 p=Path(p).absolute();I.need(h is None or sha(p)==h,'Physical development source pin');return p
def arrays(raw,width):
 I.need(len(raw)%width==0,'Typed dynamic record array');return [struct.unpack_from('<'+('I' if width==4 else 'Q'),raw,n)[0] for n in range(0,len(raw),width)]
def facts(reader,stem):
 summary=arrays(reader.read_bytes(stem+'/locale-summary.bin'),4);answer=[]
 for n in range(summary[18]):
  p=stem+'/locale-api-'+str(n);w=tuple(arrays(reader.read_bytes(p+'-witness.bin'),8))
  if w[31]:continue
  bu=reader.read_bytes(p+'-buffers.bin');inputs=[];outputs=[];k=0
  while reader.exists(p+'-input-'+str(k)+'.bin'):inputs.append(reader.read_bytes(p+'-input-'+str(k)+'.bin'));k+=1
  k=0
  while reader.exists(p+'-output-'+str(k)+'.bin'):outputs.append(reader.read_bytes(p+'-output-'+str(k)+'.bin'));k+=1
  answer.append(dict(words=w,buffers=[struct.unpack_from('<4I',bu,j) for j in range(0,len(bu),16)],inputs=inputs,outputs=outputs))
 return answer
def fields(stage,pages):
 return {'state.bin':stage['state'],'fx.bin':stage['fx'],'runtime-cpu.bin':stage['cpu'],**{'page-'+str(p)+'.bin':bytes(stage['memory'][p]) for p in pages}}
def run(path,out,index=0):
 out=Path(out);I.need(not out.exists(),'Fresh development material output');out.mkdir(parents=True)
 B=BB.Before(out,add)
 with StrictUnion(Path(path),sha(path),add) as reader:
  row=B.consumer.F.LogicalPath(reader,'row-'+str(index));stem='row-'+str(index)
  pages=arrays(reader.read_bytes(stem+'/locale-builder-returned/pages-index.bin'),4)
  q=arrays(reader.read_bytes(stem+'/locale-builder-returned/heap-query-witness.bin'),8)
  response=dict(input=reader.read_bytes(stem+'/locale-builder-returned/heap-query-input.bin'),output=reader.read_bytes(stem+'/locale-builder-returned/heap-query-output.bin'),result=q[3])
  initial,earlier,extras=B.row(row,index,'O0',response,pages)
  commandline=reader.read_bytes(stem+'/locale-builder-returned/commandline-host-bytes.bin')
  predicted=batch.predict(initial,facts(reader,stem+'/locale-builder-returned'),commandline,extras)
  count=0
  for phase,stage in predicted['phases'].items():
   I.need(reader.exists(stem+'/'+phase+'/state.bin'),'Actual source phase '+phase)
   for name,expected in fields(stage,pages).items():
    actual=reader.read_bytes(stem+'/'+phase+'/'+name)
    if actual!=expected:
     first=next((i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b),min(len(actual),len(expected)))
     raise ValueError('Source difference '+phase+'/'+name+' byte '+str(first)+' actual '+actual[max(0,first-8):first+16].hex()+' expected '+expected[max(0,first-8):first+16].hex())
    count+=1
   allocs=reader.read_bytes(stem+'/'+phase+'/locale-allocations.bin')
   for p,b in stage['memory'].items():
    if not 0x31000000<=p<0x32000000:continue
    candidates=[struct.unpack_from('<16Q',allocs,k) for k in range(0,len(allocs),128)]
    a=next(x for x in candidates if x[1]==p and x[9])
    for kind in ('expected','owned-page'):
     I.need(reader.read_bytes(stem+'/'+phase+'/locale-allocation-'+str(a[5])+'-'+kind+'.bin')==bytes(b),'Independent owned allocation page '+phase);count+=1
  print(json.dumps(dict(development_only=True,checks=count,phases=len(predicted['phases']),argc=predicted['argc'],argv_strings=[s.decode('latin1') for s in predicted['argv_strings']],source_PCs=len(predicted['PCs']),source_accesses=len(predicted['accesses']),APIs=predicted['responses'].index)))
if __name__=='__main__':run(*sys.argv[1:])
