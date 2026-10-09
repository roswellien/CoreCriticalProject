"""Direct original/native observations, keeping every defined/observed difference."""
from pathlib import Path
from collections import Counter
import hashlib,json,mmap,struct,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def bind(p):
 p=Path(p).resolve();return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha(p)}
class Raw:
 def __init__(self,p,magic,stride):
  self.path=Path(p);self.f=self.path.open('rb');self.raw=mmap.mmap(self.f.fileno(),0,access=mmap.ACCESS_READ)
  assert self.raw[:8]==magic and struct.unpack_from('<I',self.raw,8)[0]==1
  self.count,self.stride,self.pages=struct.unpack_from('<3I',self.raw,12);assert self.stride==stride and self.pages==4 and len(self.raw)==24+self.count*stride
 def record(self,i):return self.raw[24+i*self.stride:24+(i+1)*self.stride]
def fx_parts(f):return [f[:5],f[24:28]]+[f[32+i*16:42+i*16] for i in range(8)]+[f[160:288]]
def checkpoint_cpu(c):
 return struct.pack('<10I',*(struct.unpack_from('<I',c,o)[0] for o in (176,172,168,164,196,180,160,156,192)),0x4c1a09)
def compare(o,n):
 failures=[]
 def equal(name,a,b):
  if a!=b:failures.append(name)
 equal('tags',o[:40],n[:40]);equal('CPU_before',o[40:80],n[40:80]);equal('CPU_after',o[80:120],n[80:120])
 for suffix,off in [('before',120),('after',632)]:
  of,nf=o[off:off+512],n[off:off+512];equal('FX_core_'+suffix,fx_parts(of)[:2],fx_parts(nf)[:2]);equal('FX_raw80_'+suffix,fx_parts(of)[2:10],fx_parts(nf)[2:10]);equal('FX_XMM_'+suffix,of[160:288],nf[160:288])
  equal('hardware_FX_metadata_'+suffix,of[6:24],bytes(18))
 equal('ENV_before',o[2168:2196],n[2168:2196]);equal('ENV_after',o[2196:2224],n[2196:2224]);equal('whole_memory_before',o[2280:18664],n[2280:18664]);equal('whole_memory_after',o[18664:35048],n[18664:35048])
 for label,b in [('original',o),('native',n)]:
  equal(label+'_host_FX_restore',fx_parts(b[1144:1656]),fx_parts(b[1656:2168]));equal(label+'_host_ENV_restore',b[2224:2252],b[2252:2280])
 if struct.unpack_from('<I',o,8)[0]==0x4c19f0:
  oc=o[35048:35764];nc=n[42772:46856];equal('checkpoint_CPU',checkpoint_cpu(oc),nc[:40]);equal('checkpoint_FX_core',fx_parts(oc[204:716])[:2],fx_parts(nc[40:552])[:2]);equal('checkpoint_raw80',fx_parts(oc[204:716])[2:10],fx_parts(nc[40:552])[2:10]);equal('checkpoint_XMM',oc[364:492],nc[200:328])
  equal('checkpoint_real_trap_EIP',struct.unpack_from('<I',oc,184)[0],0x4c1a0a)
  # Windows debugger CONTEXT metadata is a measured separate projection.
  equal('checkpoint_FloatSave_metadata_observed_zero',oc[40:56],bytes(16));equal('checkpoint_FX_metadata_observed_zero',oc[210:228],bytes(18))
 return failures
def main():
 original,build,out=map(lambda p:Path(p).resolve(),sys.argv[1:4]);assert out.is_relative_to(ROOT/'reports/m4-fp-numeric-max') and not out.exists();out.mkdir(parents=True)
 reports=[]
 for mode in ('default','directed'):
  o=Raw(original/(mode+'.bin'),b'MW4NMO01',35764)
  for level in ('O0','O2'):
   n=Raw(build/(mode+'-'+level+'.bin'),b'MW4NMN01',47432);assert o.count==n.count
   failures=Counter();samples=[];bad=0
   for i in range(o.count):
    a,b=o.record(i),n.record(i);diff=compare(a,b)
    if diff:bad+=1;failures.update(diff)
    if diff and len(samples)<80:samples.append({'index':i,'tag':struct.unpack_from('<10I',a),'differences':diff})
   reports.append({'mode':mode,'level':level,'records':o.count,'different_records':bad,'difference_counts':dict(failures),'samples':samples,'original':bind(o.path),'native':bind(n.path)})
 report={'passed':not any(x['different_records'] for x in reports),'scope':'Direct measured CPU/page/x87/legacy/connected-CONTEXT comparison only; State/events require separate authored model','comparisons':reports,'source':bind(__file__),'metadata_provenance':'Actual original FX zero metadata and debugger FloatSave zero metadata are retained separately from direct leaf/wrapper FNSTENV; native legacy fields remain independent State storage','full_M4_complete':False}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps([{'mode':x['mode'],'level':x['level'],'bad':x['different_records'],'differences':x['difference_counts']} for x in reports]))
if __name__=='__main__':main()
