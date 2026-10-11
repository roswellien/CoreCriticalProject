"""Current controller accepts only component3 exact pre-store CALL observations."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
p=P/'run_fixture_v1.py';s=p.read_text()
for a,b in [('55a9c4b17f1413263607bf55fd30d722a63b6dcd4b56ce4caf3ccdb8472a0b45','d4959b4e37c2a8f38919545bcb3689d568f111bfe0495d639f5b029f3b20ee42'),('dfca62ad2dbae9045fc034a5fa3770606451b524fcfe31ce46f73792dcb5f62c','ba1a85aea023afd7ef61608aa84656c10f431b44e0b097bf5e09778278aa18ee'),('fixture-build-r1','fixture-build-r2'),('fixture-preparation-r2','fixture-preparation-r3')]:
 assert a in s;s=s.replace(a,b)
s=once(s,"  inputs=[pin(","  timing_path=R/'reports/m4-version-source/component-preparation-r3/call-store-timing-relations.json';timing_rows=read(timing_path,prep['files'][str(timing_path.resolve())]);timing={v['pc']:v for v in timing_rows};need(len(timing)==14,'All fourteen exact physical/SSA CALL pre-store timing admissions')\n  inputs=[pin(")
s=once(s,"  pin(__file__);pin(sys.executable)","  pin(R/'tools/m4-version-source/run_fixture_v1.py','"+sha(p)+"');pin(R/'tools/m4-version-source/derive_run_fixture_v2.py');pin(__file__);pin(sys.executable)")
checks='''   # Validate the complete private dynamic ledger against actual source Access occurrences.
   ep=capture/'phase-0'/'after';access_bytes=pin(ep/'accesses.bin').read_bytes();timing_bytes=pin(ep/'call-store-timing.bin').read_bytes();need(len(access_bytes)%24==0 and len(timing_bytes)%32==0,'Whole typed current source Access and CALL timing ledgers')
   accesses=list(struct.iter_unpack('<IIQII',access_bytes));observations=list(struct.iter_unpack('<8I',timing_bytes));seen=[]
   for obs in observations:
    pc,pre,F,ret,ss,size,index,spare=obs;need(pc in timing and size==timing[pc]['size']and not ss and not spare and pre>=4 and F==pre-4 and 0x20001000<=F and F+4<=0x20002000 and ret==pc+size and index<len(accesses),'Exact observed flatSS preESP-minus4 physical CALL saved return and current owned frame')
    need(accesses[index]==(pc,F,ret,4,1),'Same full actual Access occurrence as private pre-store timing record');seen.append(index)
   expected_indices=[n for n,v in enumerate(accesses)if v[0]in timing and v[4]];need(seen==expected_indices and len(seen)==len(set(seen)),'Every and only dynamic physical CALL source store is observed once in execution order')
   component_status=struct.unpack('<8I',pin(ep/'status.bin').read_bytes());need(component_status[0]==1 and component_status[2:5]==(0,0,1)and component_status[7]==0 and not pin(ep/'frames.bin').read_bytes(),'Actual completed source route retains committed-ESP routing/saved-return checks and closes every nested frame')
   before_cpu=struct.unpack('<10I',pin(capture/'phase-0'/'before'/'CPU.bin').read_bytes());after_cpu=struct.unpack('<10I',pin(ep/'CPU.bin').read_bytes());need(after_cpu[4]==before_cpu[4]+4 and after_cpu[9]==component_status[6]and component_status[5]==before_cpu[4],'Actual final root RET matches the same current authored caller frame')
   provider_bytes=pin(ep/'calls.bin').read_bytes();need(len(provider_bytes)%32==0,'Whole typed genuine provider committed-frame return ledger');providers=list(struct.iter_unpack('<8I',provider_bytes))
   for pc,target,F,ret,argc,x,y,z in providers:need(not(x or y or z)and any(v[0]==pc and v[2]==F and v[3]==ret for v in observations),'Each actual genuine provider return retains the precise committed source CALL frame occurrence')
'''
s=once(s,"   API_files=sorted(",checks+"   API_files=sorted(")
s=once(s,"measured_native_API_calls=len(API_files))","measured_native_API_calls=len(API_files),whole_CALL_store_observations=len(observations),genuine_provider_committed_frame_returns=len(providers),all_physical_CALL_occurrences_checked=True)")
q=P/'run_fixture_v2.py';assert not q.exists();q.write_text(s);print(json.dumps(dict(controller=str(q),sha256=sha(q),executed=False)))
