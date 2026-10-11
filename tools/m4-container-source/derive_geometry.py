"""Persistent six-root research BEFORE geometry, not actual execution credit.

Positive malloc facts use declared pointers and nonzero padding. Registration
is an explicitly abstract finite cdecl response after the literal constructor.
The shared game pages and all acquired owners carry between roots; no per-root
page reset or AFTER machine seed is used.
"""
from pathlib import Path
import hashlib, importlib.util, json, struct, sys, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-container-source'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,w):
 if not v:raise ValueError(w)

def main(name):
 out=BASE/name;need(not out.exists(),'Fresh persistent FS geometry');out.mkdir(parents=True)
 pins={};observations=[];allocations=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact research geometry input');pins[str(p)]=v;return p
 def own(p,n):
  sp=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
 try:
  rec=json.loads(pin(BASE/'recovery-r3/report.json','b078cff8698dfbefa8d4e45a0368d4820e72c7d659520161e4316e77d3c2f26b').read_bytes())
  contract=json.loads(pin(BASE/'recovery-r3/instruction-contracts.json').read_bytes())
  G=own(ROOT/'tools/m4-container-source/game_model.py','persistent_FS_geometry_model');P=own(ROOT/'tools/analysis/pe.py','persistent_FS_geometry_PE')
  program,callbacks=G.source_program();game=P.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  mfc=P.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8').read_bytes())
  def rawpage(image,base):
   raw=bytearray(4096)
   for s in image.sections:
    a=image.image_base+s['virtual_address'];lo=max(base,a);hi=min(base+4096,a+s['raw_size'])
    if hi>lo:off=s['raw_offset']+lo-a;raw[lo-base:hi-base]=image.data[off:off+hi-lo]
   return raw
  def static(address):return any(game.image_base+s['virtual_address']<=address<game.image_base+s['virtual_address']+max(s['raw_size'],s['virtual_size']) and s['writable'] for s in game.sections)
  memory={p:rawpage(game,p)for p in contract['source_data_pages']};memory[0x5f498000]=rawpage(mfc,0x5f498000);memory[0x5f4cc000]=rawpage(mfc,0x5f4cc000)
  memory[0x20001000]=bytearray(4096);memory[0x7ffde000]=bytearray(struct.pack('<I',0xffffffff))
  state=bytearray(3504)
  for offset,value in ((2312,0x20001800),(2248,0xa3c5e791),(2168,0x7ffde000),(2232,0x10293847),(2280,0x56473829),(2296,0xaabbccdd),(2328,0x92837465)):struct.pack_into('<I',state,offset,value)
  model=G.Machine(state,bytes(512),bytes(40),memory,program=program,callbacks=callbacks)
  def owner_address(address):
   owners=[a for a in allocations if a['declared_pointer']<=address<a['declared_pointer']+a['requested_size']]
   need(len(owners)<=1,'Unique acquired object address')
   if owners:return dict(owner_index=owners[0]['index'],root=owners[0]['root'],CALL_pc=owners[0]['CALL_pc'],offset=address-owners[0]['declared_pointer'])
   return None
  def malloc(machine,target):
   site=machine.PCs[-1];need(target==0x780012b3 and site in(0x5f401eb5,0x78010a7e),'Exact source MFC/string malloc frontier')
   request=int.from_bytes(machine.bytes(machine.reg('esp')+4,4),'little');frame=machine.call_stack[-2]
   need(frame[0]==(0x5abd26 if site==0x5f401eb5 else 0x78010a6d)and frame[3]in program,'Literal owning allocator/strdup CALL')
   pointer=0x36000000+len(allocations)*4096;extent=(request+15)&~15;need(0<extent<=1024,'Bounded research request')
   raw=bytes((k*17+0xcd)&255 for k in range(4096));machine.memory[pointer]=bytearray(raw)
   allocations.append(dict(index=len(allocations),root=current['entry'],CALL_pc=frame[3],requested_size=request,declared_pointer=pointer,rounded_extent=extent,source_frame=frame[1],source_return=frame[2],source_entry_ECX=machine.reg('ecx'),role='vector'if site==0x5f401eb5 else'string',initial_bytes_hex=raw[:extent].hex(),allocation_access_index=len(machine.accesses)))
   machine.api_return(site,0,pointer)
  for current in rec['roots']:
   start=len(model.accesses);pcs=len(model.PCs);old_count=len(allocations)
   frame=0x200017fc;model.write(frame,0x410a80,domain='research',pc=0x410a80);model.reg('esp',frame);model.word(2472,current['entry']);model.cursor=current['entry']
   model.call_stack.append((current['entry'],frame,0x410a80,0,model.reg('ebp'),model.reg('ebx'),model.reg('esi'),model.reg('edi'),0))
   before_cpu=list(model.projected_cpu());before_registry=int.from_bytes(model.bytes(0x60b888,4),'little')
   model.run(stop=lambda m:m.cursor==0x5ac140,api=malloc)
   callback=int.from_bytes(model.bytes(model.reg('esp')+4,4),'little');need(callback==current['registration']['callback'],'Literal exact callback PUSH')
   constructor_accesses=model.accesses[start:];local=[]
   for obj in allocations[old_count:]:
    p=obj['declared_pointer'];writes=[];publications=[]
    for pc,address,value,n,w in constructor_accesses:
     if w and p<=address<p+obj['requested_size']:writes.append(dict(pc=pc,address=address,value=value,bytes=n,owner_offset=address-p))
     if w and n==4 and p<=value<=p+obj['requested_size']:
      publications.append(dict(pc=pc,address=address,value=value,bytes=n,pointer_offset=value-p,address_owner=owner_address(address),static_address=static(address)))
    need(all(w['owner_offset']+w['bytes']<=obj['requested_size']for w in writes),'Exact owned constructor writes')
    obj.update(publications=publications,owned_source_writes=writes,owned_after_hex=model.bytes(p,obj['rounded_extent']).hex())
    backpointers=[w for w in writes if w['bytes']==4 and static(w['value'])]
    obj['static_object_backpointers']=backpointers
    local.append(obj)
   shared=int.from_bytes(model.bytes(0x60b888,4),'little')
   count=int.from_bytes(model.bytes(shared+8,4),'little') if shared else None
   old_writes=[dict(pc=pc,address=a,value=v,bytes=n,address_owner=owner_address(a)) for pc,a,v,n,w in constructor_accesses if w and owner_address(a) is not None and owner_address(a)['owner_index']<old_count]
   fs_events=[dict(pc=pc,address=a,value=v,bytes=n,write=bool(w))for pc,a,v,n,w in constructor_accesses if a==0x7ffde000]
   need(int.from_bytes(model.bytes(0x7ffde000,4),'little')==0xffffffff,'All normal FS frames restore research previous head')
   observations.append(dict(root=current['entry'],before_cpu=before_cpu,shared_BEFORE=before_registry,shared_AFTER=shared,shared_count=count,new_allocation_count=len(local),new_allocations=local,source_accesses=constructor_accesses,literal_PCs=model.PCs[pcs:],FS_events=fs_events,prior_owner_writes=old_writes,callback=callback,constructor_prefix_only=True))
   # Explicit research registration response supplies no registry owner/page effects.
   model.api_return(current['registration']['CALL_pc'],0,callback)
   model.run(stop=lambda m:m.cursor==0x410a80,api=malloc)
   need(not model.call_stack and model.reg('esp')==0x20001800,'Literal root return after abstract cdecl registration')
  need(len(allocations)==8 and len(observations)==7,'Eight source-derived positive allocations across seven persistent container/string roots')
  need([r['new_allocation_count']for r in observations]==[1,1,1,1,2,1,1],'Exact successful three-string/five-vector source allocation distribution')
  for filename,data in (('allocation-derivations.json',allocations),('root-derivations.json',observations)):(out/filename).write_text(json.dumps(data,indent=2)+'\n');pin(out/filename)
  pin(__file__);passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Persistent literal constructor geometry with one declared research BEFORE and positive finite malloc facts; abstract registration response only, no original/native execution credit',roots=len(observations),source_allocation_count=len(allocations),allocations=allocations,whole_root_registration_provider_modeled=False,per_root_page_reseed=False,AFTER_machine_seed=False,actual_original_observed=False,research_FS_base=0x7ffde000,research_prior_FS0=0xffffffff,research_entry_ECX=0xa3c5e791,files=pins)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),calls=len(allocations))))

if __name__=='__main__':main(sys.argv[1])
