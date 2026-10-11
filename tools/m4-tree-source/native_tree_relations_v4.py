"""Generation/occurrence-exact native tree records joined to literal source."""
import collections,struct
TREE=0x4b7f70
def need(x,s):
 if not x:raise ValueError(s)
def equal(a,b,s):need(a==b,s+' '+str((a,b))[:500])
def rows(a,name,n):return list(struct.iter_unpack('<'+str(n)+'Q',a.data(name)))
def verify(a,stem,source,API_relations,C,index):
 counts=collections.Counter();mfc=[r for r in rows(a,stem+'mfc-allocation-witnesses.bin',32)if r[2]==TREE];owners=source['owners'];need(len(mfc)==len(owners)==7,'Seven actual allocation occurrences for tree')
 bygen={r[18]:r for r in mfc};model_byindex={r['index']:r for r in owners}
 for w,o in zip(mfc,owners):
  f=o['source_frame'];need(w[0]==1 and w[2]==TREE and w[3]==0x5f401ea0 and (w[4],w[5],w[6],w[7])==(o['CALL_pc'],f[1],f[2],24) and w[16:20]==(o['guest'],o['native'],o['generation'],o['capacity']) and w[20:22]==(o['guest'],1) and w[23]==1,'Exact actual source CALL/frame/result/current owner occurrence')
  need([p['allocation_invocation_ordinal']for p in source['publications']if p['generation']==o['generation']]==[o['per_site_invocation_ordinal']],'Exact same-call repeated site ordinal retained')
  counts['actual_generation_occurrence_joins']+=1
 actual=[r for r in rows(a,stem+'fs-owned-accesses.bin',16)if r[2]==TREE];need(len(actual)==len(source['owned_accesses'])==172,'All172 native/source owned access occurrences')
 for w,d in zip(actual,source['owned_accesses']):
  owner=model_byindex[d['owner_index']];m=bygen[owner['generation']]
  expected=(1,w[1],TREE,d['pc'],d['address'],d['bytes'],d['value'],int(d['write']),TREE,d['owner_CALL_pc'],owner['guest'],owner['generation'],owner['native'],d['offset'],m[1],d['source_access_index']+1)
  equal(w,expected,'Whole16Q source-owned read/write current generation/role/PC/frame order');counts['whole_owned_access_relations']+=1
 actual=[r for r in rows(a,stem+'fs-owned-publications.bin',16)if r[2]==TREE];need(len(actual)==len(source['publications'])==7,'All seven positive primary publications')
 for w,d in zip(actual,source['publications']):
  owner=model_byindex[d['owner_index']];m=bygen[owner['generation']];parent=model_byindex.get(d['target_owner_index'])
  expected=(1,w[1],TREE,d['pc'],d['address'],d['value'],owner['generation'],owner['native'],owner['CALL_pc'],parent['generation']if parent else 0,parent['guest']if parent else 0,d['target_owner_offset']or 0,d['source_access_index']+1,0x60b2f8,m[1],0)
  equal(w,expected,'Whole16Q same-generation child/parent publication');counts['whole_publication_relations']+=1
 frames=[r for r in rows(a,stem+'fs-frame-witnesses.bin',32)if r[2]==TREE];rawframes=rows(a,stem+'fs-record-bytes.bin',16);need(len(frames)==len(source['FS_frames'])==7,'All seven normal tree FS invocations')
 functions={f['index']:f for f in source['function_invocations']};native_frames={f['index']:w for f,w in zip(source['FS_frames'],frames)}
 for w,f in zip(frames,source['FS_frames']):
  function=functions[f['invocation']];call=function['frame'];need(w[0]==1 and w[2:11]==(TREE,f['entry'],call[3],f['entry_ESP'],call[2],f['read_PC'],f['previous_head'],f['record'],f['handler']) and w[11]==0xffffffff and w[12]==f['depth'] and w[14]==f['install_PC'] and w[15]==1 and w[18]==f['restore_PC'] and w[19]==w[21]==1 and w[22]==f['previous_head'] and w[23]==call[0] and w[26]==f['restore_scope_source_store']['value'],'Whole source frame invocation/predecessor/handler/read/install/restore/scope lifetime')
  for point,key in((81,'installed_hex'),(84,'restored_hex')):
   matches=[r for r in rawframes if r[2]==w[1] and r[4]==point];need(len(matches)==1,'One full12B FS observation for each source store');r=matches[0]
   need(r[0]==1 and r[3]==TREE and r[6]==f['record'] and r[7]==12,'Exact actual12B source record');equal(struct.pack('<3I',*r[8:11]).hex(),f[key],'Full12B source-derived FS bytes');counts['whole12B_FS_relations']+=1
 calls=[r for r in rows(a,stem+'lockit-calls.bin',16)if r[2]==TREE];contexts=rows(a,stem+'tree-lockit-contexts.bin',16);need(len(calls)==len(contexts)==len(source['Lockit_calls'])==26,'Exact26 paired tree scratch calls')
 relations=[r for r in API_relations if r['frame'] in {p['target_entry_ESP']-16 if p['role'].endswith('ctor')else p['target_entry_ESP']-8 for p in source['Lockit_calls']}]
 # CALL PC occurrences and actual provider API index bind independently below;
 # no scratch-offset union or newest-owner lookup supplies an invocation.
 relation_byindex={r['API_index']:r for r in API_relations};held=[]
 for w,c,p in zip(calls,contexts,source['Lockit_calls']):
  ctor=p['role'].endswith('ctor');f=max((f for f in source['FS_frames']if f['record']==p['entered']['FS0']and functions[f['invocation']]['source_access_index']<p['entered']['source_access_index']),key=lambda f:functions[f['invocation']]['source_access_index']);nf=native_frames[f['index']];function=functions[p['invocation']];frame=function['frame'];paired=0xffffffff if ctor else held[-1]
  equal(w[:10],(1,w[1],TREE,p['target'],p['CALL_pc'],p['target_entry_ESP'],struct.unpack_from('<I',bytes.fromhex(p['entered']['frame_hex']))[0],p['ECX'],struct.unpack_from('<I',bytes.fromhex(p['entered']['source_CS24_hex']),8)[0],p['entered']['source_access_index']),'Whole literal constructor/destructor native CALL prefix')
  relation=relation_byindex[w[10]];need(relation['depth']==struct.unpack_from('<I',bytes.fromhex(p['returned']['source_CS24_hex']),8)[0] and relation['return_pc']in(0x7810a311,0x7810a364) and w[11:16]==(1,p['returned']['CPU'][0],relation['depth'],p['returned']['source_access_index'],w[10]+1),'Exact real API index and source-derived postRET')
  expected=(1,w[1],p['CALL_pc'],int(ctor),p['ECX'],function['entry'],frame[1],nf[1]+1,len(held),paired,p['entered']['source_access_index'],1,relation['depth'],p['returned']['source_access_index'],0,0);equal(c,expected,'Whole16Q actual active FS invocation/same scratch/LIFO context')
  if ctor:held.append(w[1])
  else:held.pop()
  need(all('locale-api-'+str(w[10])+'-'+suffix in index for suffix in ('before','after')),'Every real source API relation has whole State/CPU/FX/page observations in this capture')
  counts['whole_native_scratch_contexts']+=1
 need(not held and not a.data(stem+'tree-lockit-held.bin'),'Every active actual scratch and matched constructor consumed');equal(a.words(stem+'tree-status.bin',8,'Q'),(1,1,1,0,26,85,172,7),'Whole actual finite tree completion status')
 return dict(counts)
