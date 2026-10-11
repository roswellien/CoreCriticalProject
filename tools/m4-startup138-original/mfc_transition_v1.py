"""Exact observer remove/reinstall relations; no source output is supplied."""
import hashlib
def need(value,message):
 if not value:raise ValueError(message)
class Transition:
 def __init__(self,patches):
  need(len(patches)==13,'Exact eight IAT, three FS and two NULL observer transitions')
  self.patches=patches;self.rows=[];occupied=set()
  for patch in patches:
   pc=patch['pc'];a=bytes.fromhex(patch['original_hex']);z=bytes.fromhex(patch['instrumented_hex'])
   need(len(a)==len(z)>0 and (pc&4095)+len(a)<=4096,'Exact whole owning span geometry')
   for address in range(pc,pc+len(a)):
    need(address not in occupied,'Disjoint owning observer spans');occupied.add(address)
 def relation(self,previous,current,page,phase,sequence):
  need(len(previous)==len(current)==4096,'Complete4096 chronology endpoints')
  need(phase in(13,14),'Only explicitly attributed observer remove/reinstall transitions')
  install=phase==14;expected=bytearray(previous);owners=[]
  for patch in self.patches:
   if patch['pc']&~4095!=page:continue
   start=patch['pc']&4095
   prior=bytes.fromhex(patch['original_hex'if install else'instrumented_hex'])
   after=bytes.fromhex(patch['instrumented_hex'if install else'original_hex'])
   need(previous[start:start+len(prior)]==prior,'Exact actual prior observer mode at '+hex(patch['pc']))
   expected[start:start+len(after)]=after;owners.append(patch['symbol'])
  need(bytes(expected)==current,'Exact whole4096 chronological page with only owning observer transitions '+hex(page))
  self.rows.append(dict(sequence=sequence,phase=phase,page=page,install=install,owning_symbols=owners,previous_sha256=hashlib.sha256(previous).hexdigest(),expected_sha256=hashlib.sha256(expected).hexdigest(),actual_sha256=hashlib.sha256(current).hexdigest()))
