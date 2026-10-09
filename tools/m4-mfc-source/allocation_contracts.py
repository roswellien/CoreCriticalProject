"""Literal constructor BEFORE derivation with declared positive research facts.

This establishes call/request/publication geometry and byte provenance. The
declared positive pointers and nonzero initial padding are research inputs,
not original allocation observations, native results, or execution credit.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-mfc-source'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,w):
 if not v:raise ValueError(w)
def main(name):
 out=BASE/name;need(not out.exists(),'Fresh allocation geometry output');out.mkdir(parents=True);pins={};observations=[];allocations=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Pinned source derivation input');pins[str(p)]=v;return p
 def own(p,n):
  spec=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 try:
  rec=json.loads(pin(BASE/'recovery-r4/report.json','b50217399d254eddc620ab39bf8d934fd2cc30233e575356a9d8c40761c33e0f').read_bytes());contract=json.loads(pin(BASE/'recovery-r4/instruction-contracts.json').read_bytes())
  G=own(ROOT/'tools/m4-mfc-source/game_model.py','allocation_geometry_game');PE=own(ROOT/'tools/analysis/pe.py','allocation_geometry_pe');program,callbacks=G.source_program()
  game=PE.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes());mfc=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes())
  def rawpage(image,base):
   data=bytearray(4096)
   for s in image.sections:
    a=image.image_base+s['virtual_address'];lo=max(base,a);hi=min(base+4096,a+s['raw_size'])
    if lo<hi:data[lo-base:hi-base]=image.data[s['raw_offset']+lo-a:s['raw_offset']+hi-a]
   return data
  def section(a):return next((s for s in game.sections if game.image_base+s['virtual_address']<=a<game.image_base+s['virtual_address']+max(s['raw_size'],s['virtual_size'])),None)
  for index,r in enumerate(rec['roots']):
   memory={p:rawpage(game,p)for p in contract['source_data_pages']};memory[0x5f498000]=rawpage(mfc,0x5f498000);memory[0x20001000]=bytearray(4096)
   state=bytearray(3504);struct.pack_into('<I',state,2312,0x20001800);struct.pack_into('<I',state,2248,0xa3c5e791)
   model=G.Machine(state,bytes(512),bytes(40),memory,program=program,callbacks=callbacks);model.invoke_external(r['entry'],0x410a80);objects=[]
   def malloc(machine,target):
    need(target==0x780012b3 and machine.PCs[-1]==0x5f401eb5,'Literal positive MFC allocator call frontier')
    request=int.from_bytes(machine.bytes(machine.reg('esp')+4,4),'little');frame=machine.call_stack[-2];site=frame[3];need(frame[0]==0x5abd26 and site in program and program[site]['mnemonic']=='call','Actual owning game allocator CALL frame')
    pointer=0x36000000+(index*4+len(objects))*4096;extent=(request+15)&~15;need(0<extent<=512,'Bounded positive object size')
    raw=bytes(((k*17+0xcd)&255)for k in range(4096));machine.memory[pointer]=bytearray(raw)
    objects.append(dict(root=r['entry'],CALL_pc=site,requested_size=request,declared_pointer=pointer,rounded_extent=extent,source_frame=frame[1],source_return=frame[2],entry_ECX=frame[5] if False else machine.reg('ecx'),initial_bytes_hex=raw[:extent].hex(),ledger_start=len(machine.accesses)))
    machine.api_return(0x5f401eb5,0,pointer)
   model.run(stop=lambda m:m.cursor==0x5ac140,api=malloc)
   need(int.from_bytes(model.bytes(model.reg('esp')+4,4),'little')==r['registration']['callback'],'Literal registered callback from source BEFORE')
   for obj in objects:
    pointer=obj['declared_pointer'];pubs=[(pc,a,v,n)for pc,a,v,n,write in model.accesses if write and n==4 and v==pointer and section(a)and section(a)['writable']]
    need(len(pubs)==1,'One actual source object publication '+hex(r['entry'])+' '+str(pubs));pc,a,v,n=pubs[0];obj.update(publication=a,publication_pc=pc,object=a-4,owned_after_hex=model.bytes(pointer,obj['rounded_extent']).hex())
    need(any(o['address']==a-4 for o in r['objects']),'Publication identifies original constructor header')
    writes=[dict(pc=pc,address=addr,value=value,bytes=n)for pc,addr,value,n,w in model.accesses if w and pointer<=addr<pointer+obj['rounded_extent']]
    obj['owned_source_writes']=writes;need(writes and all(w['address']+w['bytes']<=pointer+obj['requested_size']for w in writes),'Only exact source owned writes in actual request')
    allocations.append(obj)
   headers=[]
   for candidate in r['objects']:
    matches=[(pc,a,v,n)for pc,a,v,n,w in model.accesses if w and a==candidate['address']and n==1]
    for pc,a,v,n in matches:
     idx=model.PCs.index(pc);prior_reads=[(rp,ra,rv,rn)for rp,ra,rv,rn,w in model.accesses if not w and rn==1 and 0x20001000<=ra<0x20002000 and model.PCs.index(rp)<=idx]
     headers.append(dict(object=a,write_pc=pc,value=v,caller_stack_reads=[dict(pc=rp,address=ra,value=rv,bytes=rn)for rp,ra,rv,rn in prior_reads]))
   observations.append(dict(root=r['entry'],allocation_count=len(objects),allocations=objects,header_provenance=headers,literal_PCs=model.PCs,source_accesses=model.accesses,import_projections=model.import_projections,provider_stack=model.call_stack,callback=r['registration']['callback']))
  need(len(allocations)==35 and len(observations)==32,'Actual source-derived35 positive CALLs across32 roots')
  simple=[{k:r[k]for k in('root','CALL_pc','requested_size','object','publication')}for r in allocations];(out/'allocation-inputs.json').write_text(json.dumps(simple,indent=2)+'\n');(out/'derivations.json').write_text(json.dumps(observations,indent=2)+'\n')
  for p in out.iterdir():
   if p.is_file():pin(p)
  for p in (BASE/'loader-identity-r1/report.json',BASE/'game-callbacks-r1/callbacks.json',ROOT/'reports/m4-mfc-review/interface-r1/instruction-contracts.json',Path(__file__),Path(sys.executable)):pin(p)
  passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Exact literal constructor positive BEFORE derivation; declared research allocation facts only, no original/native execution credit',root_count=len(observations),source_allocation_count=len(allocations),allocations=allocations,allocation_inputs_sha256=sha(out/'allocation-inputs.json')if(out/'allocation-inputs.json').exists()else None,AFTER_machine_seed=False,real_original_allocation_observed=False,research_input_ECX=0xa3c5e791,research_padding='Nonzero arithmetic byte pattern; exact unwritten bytes retained',files=pins)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),calls=len(allocations))))
if __name__=='__main__':main(sys.argv[1])
