"""Join literal BEFORE-derived helper machines to actual boundary snapshots."""
from pathlib import Path
import hashlib,json
T=Path(__file__).resolve().parent;ROOT=T.parents[1];pins={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def one(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def write(name,s):
 p=T/name;assert not p.exists();compile(s,str(p),'exec');p.write_text(s);pins[str(p.resolve())]=sha(p)

p=T/'compare_connected_v4.py';pins[str(p.resolve())]=sha(p);s=p.read_text()
old="     need(not stack and index==15,'All normal nested game frames close');need(not machine.indirect_pending and len(machine.indirect_derivations)==6,'All six literal fixed indirect CALL/RET prefixes');indirect_rows+=machine.indirect_derivations;counts['literal_indirect_CALL_RET_derivations']+=6;counts['persistent120_sequences']+=1"
new="""     need(not stack and index==15,'All normal nested game frames close');need(not machine.indirect_pending and len(machine.indirect_derivations)==6,'All six literal fixed indirect CALL/RET prefixes')
     actual_calls=list(struct.iter_unpack('<32Q',a.data(stem+'vtable-call-witnesses.bin')));need(len(actual_calls)==6,'Six actual rooted native indirect CALL/RET records')
     for vi,derived in enumerate(machine.indirect_derivations):
      w=actual_calls[vi];binding=V.INPUTS[(derived['root'],derived['CALL_pc'])]
      need(w[:8]==(1,vi,derived['root'],derived['CALL_pc'],derived['slot'],derived['target'],derived['target'],derived['CALL_pc'])and w[9]==binding['entry_ECX']and w[14:22]==(derived['ENTRY_BEFORE']['ESP'],derived['return_pc'],binding['argument']or0,binding['RET_cleanup'],derived['RET_AFTER']['ESP'],derived['RET_AFTER']['CPU'][0],derived['RET_pc'],1),'Actual native cell/source CALL/RET/frame/argument/cleanup result joins literal prefix')
      if derived['CALL_pc']==0x59ff6e:need(w[10:12]==(binding['source_vtable'],binding['source_vtable'])and w[12]and w[13],'Derived-slot call has genuine committed vptr publication and actual source read indices')
      elif derived['CALL_pc']==0x59fdc5:need(w[10:14]==(0,binding['source_vtable'],0,0),'Absolute cell call has no fabricated instance-vptr read indices')
      else:need(w[10:14]==(0,0,0,0),'Fixed standalone cell has no instance-vptr observation')
      need(w[24]==w[25]==derived['ENTRY_BEFORE']['FS0']==derived['RET_AFTER']['FS0']and w[26]==w[27]and w[28]==w[29]and w[30:]==(0,0),'Actual indirect prefix produces no API/owner/FS effects')
      joins=[]
      for suffix,key in(('entered','ENTRY_BEFORE'),('returned','RET_AFTER')):
       checkpoint_name=f'vtable-call-{vi}-{suffix}';actual=C.checkpoint(a,index,checkpoint_name);prediction=derived[key]
       equal(actual['state'].hex(),prediction['State_hex'],'Entire actual indirect boundary State from persistent BEFORE source');equal(actual['cpu'],struct.pack('<10I',*prediction['CPU']),'Entire actual indirect boundary CPU GPR/flags/PC');equal(actual['fx'].hex(),prediction['FX_hex'],'Whole actual indirect boundary FX from persistent source')
       equal(actual['memory'][0x20001000][prediction['ESP']-0x20001000:prediction['ESP']-0x20001000+16].hex(),prediction['frame_hex'],'Actual complete indirect source CALL/RET stack words');joins.append(dict(name=checkpoint_name,state_sha256=hashlib.sha256(actual['state']).hexdigest(),CPU_hex=actual['cpu'].hex(),FX_sha256=hashlib.sha256(actual['fx']).hexdigest()));counts['actual_native_indirect_full_State_CPU_FX_boundary_joins']+=1
      derived['actual_native_witness']=list(w);derived['actual_native_checkpoints']=joins
     indirect_rows+=machine.indirect_derivations;counts['literal_indirect_CALL_RET_derivations']+=6;counts['actual_native_indirect_CALL_RET_joins']+=6;counts['persistent120_sequences']+=1""".replace("binding['argument']or0","(binding['argument'] or 0)")
s=one(s,old,new);write('compare_connected_v5.py',s)

p=T/'compare_original_game_v4.py';pins[str(p.resolve())]=sha(p);s=p.read_text().replace("ORIG/'preparation-r1/report.json'","ORIG/'preparation-r3/report.json'")
old="      need(not machine.indirect_pending,'Every genuine original indirect helper returns');indirectrows+=machine.indirect_derivations;counts['literal_indirect_CALL_RET_derivations']+=len(machine.indirect_derivations)"
new="""      need(not machine.indirect_pending,'Every genuine original indirect helper returns');snapshots=reader.data(f'phase/{seq}/{phase}/vtable-snapshots.bin');need(len(snapshots)==len(machine.indirect_derivations)*1320,'All actual target entry/preRET snapshots have literal source-derived calls')
      for vi,derived in enumerate(machine.indirect_derivations):
       binding=V.INPUTS[(derived['root'],derived['CALL_pc'])];actuals=[]
       for point,key in((0,'ENTRY_BEFORE'),(1,'RET_BEFORE')):
        actual=snapshots[(vi*2+point)*660:(vi*2+point+1)*660];meta=words(actual,0,16);prediction=derived[key];actual_cpu=words(actual,64,10)
        need(meta[:9]==(1,vi*2+point,entry,point,prediction['CPU'][9],derived['target'],derived['CALL_pc'],derived['slot'],derived['target'])and meta[9]==prediction['FS0']and meta[10]==binding['source_object']and meta[11]==binding.get('source_vtable',0)and meta[12:15]==(prediction['ESP'],derived['return_pc'],binding['RET_cleanup']),'Authentic actual original target/source-cell/vptr/FS/frame/return metadata joins prefix')
        need(tuple(prediction['CPU'])==actual_cpu,'All actual original target entry/preRET CPU GPR/flags/PC from genuine root BEFORE');need(prediction['FX_hex']==actual[104:616].hex()and prediction['ENV_hex']==actual[616:644].hex(),'Entire actual original target entry/preRET FX/ENV from genuine root BEFORE');need(prediction['frame_hex']==actual[644:660].hex(),'Actual complete original16B helper frame from source pushes')
        actuals.append(dict(point=point,meta=list(meta),CPU=list(actual_cpu),snapshot_sha256=hashlib.sha256(actual).hexdigest()));counts['actual_original_indirect_full_CPU_FX_ENV_boundary_joins']+=1
       need(actuals[0]['meta'][15]==actuals[1]['meta'][15],'Actual pure helper makes zero API calls between source boundaries');derived['actual_original_snapshots']=actuals;counts['actual_original_indirect_CALL_preRET_joins']+=1
      indirectrows+=machine.indirect_derivations;counts['literal_indirect_CALL_RET_derivations']+=len(machine.indirect_derivations)"""
s=one(s,old,new);write('compare_original_game_v5.py',s)

# The actual compiled worker and observer inventory come from the final
# original producer revision, preserving all prior syntax-only readers.
p=T/'compare_paired_policy_v3.py';pins[str(p.resolve())]=sha(p);s=p.read_text().replace('reports/m4-vtable-original/preparation-r1/','reports/m4-vtable-original/preparation-r3/').replace('reports/m4-vtable-original/build-r1/','reports/m4-vtable-original/build-r2/')
write('compare_paired_policy_v4.py',s)
pins[str(Path(__file__).resolve())]=sha(Path(__file__))
out=ROOT/'reports/m4-next-source/boundary-proof-preparation-r1';assert not out.exists();out.mkdir()
(out/'report.json').write_text(json.dumps(dict(passed=True,scope='Actual observation joins added to120 source readers; syntax checked, final captures pending',files=pins),indent=2)+'\n')
print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),files=pins)))
