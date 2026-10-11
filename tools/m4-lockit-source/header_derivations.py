"""Exact branch-local byte read/store provenance for nine new header fields."""
BINDINGS={
 0x411010:((0x6040b8,0x4125c1,0x4125c5),(0x6040b9,0x4125c7,0x4125ce)),
 0x4dc140:((0x60b5a8,0x4dc178,0x4dc18e),(0x60b5a9,0x4dc180,0x4dc186)),
 0x500660:((0x60bf90,0x500685,0x50068b),(0x60bfa0,0x500cf1,0x500cf5),(0x60bfa1,0x500cf7,0x500cfe)),
 0x5968f0:((0x731868,0x596b18,0x596b2e),(0x731869,0x596b20,0x596b26)),
}
def need(v,s):
 if not v:raise ValueError(s)
def derive(machine,start,root,before_pages,pages,cpu,level,seq,phase):
 answer=[];local=machine.accesses[start:]
 for address,rpc,wpc in BINDINGS.get(root,()):
  writes=[(i,r)for i,r in enumerate(local)if r[0]==wpc and r[1]==address and r[3:]==(1,1)];need(len(writes)==1,'One exact new source header byte publication');wi,write=writes[0];reads=[(i,r)for i,r in enumerate(local[:wi])if r[0]==rpc and r[3:]==(1,0)];need(len(reads)==1,'Exact local operand source byte read');ri,read=reads[0];need(read[2]==write[2],'Exact unchanged source byte copied to new header');stores=[(i,r)for i,r in enumerate(local[:ri])if r[4]and r[1]<=read[1]<r[1]+r[3]]
  if stores:
   si,store=stores[-1];need((store[2]>>(8*(read[1]-store[1])))&255==read[2],'Source header byte follows last exact dominating store');provenance=dict(kind='dominating_source_store',index=si,pc=store[0],address=store[1],value=store[2],width=store[3],extracted_byte_offset=read[1]-store[1])
  else:
   page=read[1]&~4095;need(page in pages,'Header byte comes from complete carried source BEFORE page');offset=pages.index(page)*4096+(read[1]&4095);need(before_pages[offset]==read[2],'Exact source carried BEFORE header operand byte');provenance=dict(kind='carried_source_BEFORE_byte',address=read[1],value=before_pages[offset],no_root_source_store_before_read=True)
  need(0x20001000<=read[1]<0x20002000,'Only physically recovered branch-local guest stack byte input admitted');answer.append(dict(level=level,sequence=seq,phase=phase,root=root,field=address,write_pc=wpc,value=write[2],read_pc=rpc,read_address=read[1],source_root_BEFORE_cpu=list(cpu),source_access_read_index=start+ri,source_access_write_index=start+wi,provenance=provenance))
 return answer
