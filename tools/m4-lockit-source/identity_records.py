"""Retain small actual identity proofs without opening a second capture reader."""
from pathlib import Path
import hashlib,json

PROOFS={}
OBSERVATIONS=[]

def install(observer_module):
 original=observer_module.Observer.identities
 def identities(self,stem,facts):
  original(self,stem,facts)
  def keep(name,before_prefix,after_prefix,index=None,export=False):
   before=self.a.data(before_prefix+'.bin');after=self.a.data(after_prefix+'.bin')
   observer_module.equal(before,after,'Retained whole actual API identity before/after')
   owner_path=self.a.data(before_prefix+'-module-path.bin').decode('utf-16-le').split('\0',1)[0]
   owner_sha=self.a.data(before_prefix+'-module-sha.bin').decode('ascii')
   self.pin(owner_path,owner_sha)
   proof=dict(name=name,identity_before_hex=before.hex(),identity_after_hex=after.hex(),owner_path=owner_path,owner_sha256=owner_sha)
   if export:
    raw=self.a.data(before_prefix.removesuffix('-identity-before')+'-export-before.bin')
    end=self.a.data(after_prefix.removesuffix('-identity-after')+'-export-after.bin')
    observer_module.equal(raw,end,'Retained actual full export proof before/after')
    proof['export_before_hex']=raw.hex();proof['export_after_hex']=end.hex()
   canonical=json.dumps(proof,sort_keys=True,separators=(',',':')).encode()
   key=hashlib.sha256(canonical).hexdigest();PROOFS.setdefault(key,proof)
   observation=dict(level=self.level,sequence=self.seq,API_index=index,requested=name,proof_sha256=key)
   if index is not None:observation['witness_words']=list(facts[index]['words'])
   else:observation['service']={'HeapCreate':'create','GetVersionExA':'query','HeapDestroy':'destroy'}[name]
   OBSERVATIONS.append(observation)
  for n,fact in enumerate(facts):
   p=stem+f'locale-api-{n}';keep(fact['name'],p+'-identity-before',p+'-identity-after',n,True)
  for service,name in (('create','HeapCreate'),('query','GetVersionExA'),('destroy','HeapDestroy')):
   p=stem+'heap-'+service+'-api-';keep(name,p+'before',p+'after')
 observer_module.Observer.identities=identities

def lineage(native_report,nr,pin):
 """Explicitly bind the executed build and both current native preparations."""
 result=dict(execution=str(Path(native_report).resolve()))
 build=pin(nr['build_path'],nr['build_sha256']);b=json.loads(build.read_bytes())
 joint=pin(b['preparation'],b['preparation_sha256']);p=json.loads(joint.read_bytes())
 native=pin(Path(p['native_library']).parent/'report.json',p['native_preparation_sha256'])
 for key,path in (('build',build),('joint_preparation',joint),('native_preparation',native)):
  result[key]=str(path);result[key+'_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
 return result

def value():
 return dict(scope='Actual full before/after11Q executable-owner identities; unique whole4624B typed API export proofs; all case/API references; direct lifecycle export identities',proofs=PROOFS,observations=OBSERVATIONS)
