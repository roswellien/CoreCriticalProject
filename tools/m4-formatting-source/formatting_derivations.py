"""Bounded source-only formatting exports and complete new mixed private joins."""
import struct
ROOTS=(0x4df610,0x4e0710,0x4e0810,0x4e1ca0)
REQUESTS=dict(zip(ROOTS,(8,10,12,11)))
BYTE_BINDINGS=((0x60b74c,0x49cc89,0x49cc8b),(0x60b758,0x4e22b7,0x4e22c4),(0x60b760,0x4e52e6,0x4e52f4),(0x60b761,0x4e52ea,0x4e5303))
OBJECTS={0x49cc8d:0x60b74c,0x4e5325:0x60b668,0x4e535b:0x60b668}
def need(x,s):
 if not x:raise ValueError(s)
def rows(a,name,n):
 raw=a.data(name);need(len(raw)%(8*n)==0,'Whole private row '+name);return list(struct.iter_unpack('<'+str(n)+'Q',raw))
def equal(a,b,s):need(a==b,s+' '+str((a,b))[:650])
def byte_provenance(local,start,before_pages,pages):
 out=[]
 for field,rpc,wpc in BYTE_BINDINGS:
  writes=[(i,r)for i,r in enumerate(local)if r[0]==wpc and r[1]==field and r[3:]==(1,1)];need(len(writes)==1,'One finite mixed local-byte store');wi,w=writes[0]
  reads=[(i,r)for i,r in enumerate(local[:wi])if r[0]==rpc and r[3:]==(1,0)];need(len(reads)==1,'One exact physical mixed byte read');ri,r=reads[0];need(r[2]==w[2],'Literal same-register byte copy')
  stores=[(i,v)for i,v in enumerate(local[:ri])if v[4]and v[1]<=r[1]<v[1]+v[3]]
  if stores:
   si,v=stores[-1];need((v[2]>>(8*(r[1]-v[1])))&255==r[2],'Exact last overlapping source store supplies byte');origin=dict(kind='dominating_source_store',source_access_index=start+si,PC=v[0],address=v[1],width=v[3],value=v[2],extracted_byte_offset=r[1]-v[1])
  else:
   page=r[1]&~4095;need(page in pages,'Mixed byte supplied by complete carried BEFORE page');value=before_pages[pages.index(page)*4096+(r[1]&4095)];need(value==r[2],'Carried BEFORE byte equals literal read');origin=dict(kind='carried_source_BEFORE_byte',address=r[1],value=value,no_prior_root_overlapping_store=True)
  out.append(dict(field=field,read_PC=rpc,write_PC=wpc,read_address=r[1],value=w[2],source_access_read_index=start+ri,source_access_write_index=start+wi,provenance=origin))
 return out
def derive(m,responses,observer,root,start,pcstart,allocstart,relationstart,before_pages,pages,level,seq,phase,FS):
 local=m.accesses[start:];allocations=responses.allocations[allocstart:];need(root in ROOTS and len(allocations)==(4 if root==0x4e1ca0 else 1),'Exact literal formatting allocation occurrence extent');owner=allocations[0]
 need(owner.get('formatter')and owner['requested']==REQUESTS[root]and owner['extent']==16,'Actual formatter source request/capacity and caller role')
 def owned(a):return [r for r in local if a['guest']<=r[1]and r[1]+r[3]<=a['guest']+a['extent']]
 def export(a):return a|dict(initial=a['initial'].hex(),source_final_hex=m.bytes(a['guest'],a['extent']).hex(),source_owned_accesses=owned(a))
 calls=[]
 for row in observer.formatting_calls:
  if row[1]!=root:continue
  need(row[14]and row[6]in(1,2,4),'Completed literal cdecl call');calls.append(dict(root=root,PC=row[2],target=row[3],frame=row[4],args=row[7:7+row[6]],returned=True,result=row[15],returned_ESP=row[4]+4))
 need(len(calls)==3,'Three literal formatter CALL/RET occurrences')
 mixed=[]
 if root==0x4e1ca0:
  for role,(a,site,request)in enumerate(zip(allocations[1:],(0x49cc8d,0x4e5325,0x4e535b),(12,24,24))):
   need(a.get('kind')==4 and a['requested']==request and a['extent']==(16 if request==12 else 32),'Literal mixed MFC role/request and actual capacity')
   source=[r for r in observer.mfc if r['words'][18]==a['generation']];need(len(source)==1 and source[0]['words'][4]==site,'One exact source MFC occurrence for mixed role')
   mixed.append(export(a)|dict(owner_role=role,allocation_CALL_pc=site,source_MFC_index=source[0]['words'][1],source_MFC_words=list(source[0]['words'])))
   need(m.bytes(a['guest']+request,a['extent']-request)==a['initial'][request:],'Every requested-to-capacity tail byte retains actual acquired value')
 need(m.bytes(owner['guest']+owner['requested'],16-owner['requested'])==owner['initial'][owner['requested']:],'Formatter full capacity tail retains acquired input')
 result=dict(level=level,sequence=seq,phase=phase,root=root,source_PCs=m.PCs[pcstart:],source_accesses=local,calls=calls,owner=export(owner),mixed_owners=mixed,owned_accesses=owned(owner),dispatches=[d for d in m.output_dispatches if d['source_access_index']>=start],FS_frames=[f for f in FS if f['root']==root],Lockit_API_relations=list(responses.lockit_relations[relationstart:]),source_access_start=start,API_index=responses.index,static_field_writes=[r for r in local if r[4]and 0x400000<=r[1]<0x10000000])
 if root==0x4e1ca0:
  result['byte_provenance']=byte_provenance(local,start,before_pages,pages)
  need(0x4e52cc in result['source_PCs']and [r for r in local if r[0]==0x4e5309]==[(0x4e5309,0x60b768,0,1,1)],'Literal XOR EBX supplies mixed +256 byte zero')
  result['literal_zero_byte']=dict(field=0x60b768,write_PC=0x4e5309,value=0,definition_PC=0x4e52cc)
 return result
def verify_mixed(a,stem,result,all_FS,all_accesses,interface):
 root=result['root'];need(root==0x4e1ca0,'Only new mixed family seam');counts={};owners=result['mixed_owners'];owned=[]
 actual_all=rows(a,stem+'fs-owned-accesses.bin',16);need(all(w[1]==i for i,w in enumerate(actual_all)),'Physical private owned row ordinals contiguous');actual=[w for w in actual_all if w[2]==root]
 for i,r in enumerate(all_accesses):
  if i<result['source_access_start']:continue
  pc,address,value,width,writing=r
  for owner in owners:
   if owner['guest']<=address and address+width<=owner['guest']+owner['extent']:
    need(writing and address+width<=owner['guest']+owner['requested'],'Mixed literal writes remain within requested owner')
    owned.append((pc,address,value,width,writing,owner,i))
 need(len(actual)==len(owned)==10,'Exact ten private mixed owner operands')
 for w,(pc,address,value,width,writing,o,i)in zip(actual,owned):
  expected=(1,w[1],root,pc,address,width,value,writing,root,o['allocation_CALL_pc'],o['guest'],o['generation'],o['native'],address-o['guest'],o['source_MFC_index'],i+1);equal(w,expected,'Whole16Q mixed private owned operand source relation')
 actual_pubs_all=rows(a,stem+'fs-owned-publications.bin',16);need(all(w[1]==i for i,w in enumerate(actual_pubs_all)),'Physical private publication ordinals contiguous');actual_pubs=[w for w in actual_pubs_all if w[2]==root];need(len(actual_pubs)==3,'Three whole mixed publication occurrences');pubs=[]
 for w,spec,o in zip(actual_pubs,interface['publication_contracts'],owners):
  matches=[(i,r)for i,r in enumerate(all_accesses)if i>=result['source_access_start']and r[0]==spec['publication_pc']and r[1]==spec['publication_address']and r[3:]==(4,1)];need(len(matches)==1,'One literal primary mixed owner publication');i,r=matches[0];need(r[2]==o['guest'],'Publication value is same actual source owner')
  expected=(1,w[1],root,r[0],r[1],r[2],o['generation'],o['native'],o['allocation_CALL_pc'],0,0,0,i+1,OBJECTS[o['allocation_CALL_pc']],0,0);equal(w,expected,'Complete16Q mixed publication from actual source occurrence');pubs.append(dict(observed=list(w),source_access_index=i,owner_role=o['owner_role']))
 actual_frames=rows(a,stem+'fs-frame-witnesses.bin',32);raw_frames=rows(a,stem+'fs-record-bytes.bin',16);active=[];findex=0;sourceframes=[];specs={f['function']:f for f in interface['FS_frame_contracts']}
 for event in all_FS:
  if event['kind']==0:
   frame=dict(index=findex,depth=len(active),parent=active[-1]['index']+1 if active else 0,read=event);findex+=1;active.append(frame)
  elif event['kind']==1:active[-1]['install']=event
  else:
   frame=active.pop();frame['restore']=event
   if event['root']!=root:continue
   read=frame['read'];install=frame['install'];spec=specs[read['group_entry']];call=read['source_call_frame'];ESP=read['entry_ESP'];installed=struct.unpack('<3I',bytes.fromhex(install['record_hex']));restored=struct.unpack('<3I',bytes.fromhex(event['record_hex']));need(installed==(read['before_head'],spec['handler'],0xffffffff)and restored[:2]==installed[:2],'Whole source-generated twelve-byte mixed FS predecessor/handler')
   saves=[r for r in all_accesses if r[0]==spec['saved_predecessor_read_pc']and r[1]==ESP-12 and r[3:]==(4,0)];need(len(saves)==1 and saves[0][2]==read['before_head'],'Literal same-frame saved predecessor read')
   returns=[r for r in all_accesses if r[0]==spec['return_pc']and r[1]==ESP and r[3:]==(4,0)];need(len(returns)==1 and returns[0][2]==call[2],'Literal same invocation RET reads its actual source return word')
   expected=(1,frame['index'],root,spec['function'],call[3],ESP,call[2],spec['read_pc'],read['before_head'],ESP-12,spec['handler'],0xffffffff,frame['depth'],frame['parent'],spec['install_pc'],1,spec['saved_predecessor_read_pc'],read['before_head'],spec['restore_pc'],1,spec['return_pc'],1,read['before_head'],call[0],0x7ffde000,0xffffffff,restored[2],*installed,restored[0],restored[1]);need(len(expected)==32,'Complete normal FS32Q schema');equal(actual_frames[frame['index']],expected,'Whole32Q mixed FS source invocation and lifetime')
   for point,ev,raw in((81,install,installed),(84,event,restored)):
    matches=[w for w in raw_frames if w[2]==frame['index']and w[4]==point];need(len(matches)==1,'One complete mixed raw FS record at each literal commit');w=matches[0];need(w[:8]==(1,w[1],frame['index'],root,point,ev['PC'],ESP-12,12)and w[8:11]==raw and w[15]==0,'Actual complete12B mixed raw predecessor/handler/scope relation')
   sourceframes.append(dict(observed=list(expected),read=read,install=install,restore=event))
 need(not active and len(sourceframes)==2,'Two complete nested mixed FS frames close')
 calls=[w for w in rows(a,stem+'lockit-calls.bin',16)if w[2]==root];imports=[w for w in rows(a,stem+'lockit-imports.bin',8)if w[1]==root];relations=[];need(len(calls)==len(imports)==2,'One source-normal mixed constructor/destructor pair')
 for w,im,spec in zip(calls,imports,interface['Lockit_scratch_contracts']):
  site=spec['CALL_pc'];pushes=[(i,r)for i,r in enumerate(all_accesses)if r[0]==site and r[3:]==(4,1)];reads=[(i,r)for i,r in enumerate(all_accesses)if r[0]==site and r[1]==spec['owning_IAT']and r[3:]==(4,0)];need(len(pushes)==len(reads)==1,'Exact source raw IAT read and actual committed CALL return push');pi,p=pushes[0];ri,r=reads[0];ctor=spec['source_target']==0x7810a290;retpc=0x7810a315 if ctor else 0x7810a364;rets=[(i,r)for i,r in enumerate(all_accesses)if r[0]==retpc and r[1]==p[1]and r[3:]==(4,0)];need(len(rets)==1 and rets[0][1][2]==spec['return_pc'],'Literal provider RET reads same mixed source CALL return');ei,er=rets[0]
  api=[v for v in result['Lockit_API_relations']if v['frame']==p[1]-(16 if ctor else 8)];need(len(api)==1,'One actual typed API relation joins source provider frame');api=api[0];scratch=p[1]+48
  expected=(1,w[1],root,spec['source_target'],site,p[1],spec['return_pc'],scratch,api['depth']+(-1 if ctor else 1),pi+1,api['API_index'],1,scratch if ctor else api['actual_API_words'][9],api['depth'],ei+1,api['API_index']+1);equal(w,expected,'Complete16Q mixed literal CALL/API/postRET source relation')
  equal(im,(1,root,site,spec['owning_IAT'],r[2],spec['source_target'],ri+1,0),'Complete8Q mixed raw named owning import witness');relations.append(dict(call=list(w),import_witness=list(im),source_API=api))
 result['mixed_private_relations']=dict(owned=[list(w)for w in actual],publications=pubs,FS_frames=sourceframes,Lockit_calls=relations)
 return dict(whole_mixed_private_owned_operands=10,whole_mixed_private_publications=3,whole_mixed_private_FS32Q_frames=2,whole_mixed_private_raw12B_records=4,whole_mixed_private_Lockit16Q_calls=2,whole_mixed_private_raw8Q_imports=2)
