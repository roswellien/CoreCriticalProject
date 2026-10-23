"""Finite source-predicted heap token/MODE input cut; never a whole-page witness."""
import struct
TOKEN=0x48450001
FIELDS=((0x78035000,TOKEN,0x780039d8,8,0x78001379),(0x78035004,1,0x780039eb,31,0x78001306))
def need(v,s):
 if not v:raise ValueError(s)
def overlap(v,a):return v[1]<a+4 and v[1]+v[3]>a
def prove(row,heap_raw,provider_raw,create_raw):
 need(row['source_seed']is False and row['AFTER_seed']is False and row['whole_native_component_journals_compared']is True and row['whole_native_State_CPU_FX_compared']is True and row['full_literal_journal_preserved_during_instruction_guards']is True,'Passed current whole carried constructor source authority')
 need(len(heap_raw)==2560 and len(create_raw)==128 and len(provider_raw)%24==0,'Exact physically produced ledger schemas')
 padded=list(struct.iter_unpack('<5I',heap_raw));firstzero=next((i for i,v in enumerate(padded)if not any(v)),len(padded));need(firstzero==36 and not any(any(v)for v in padded[firstzero:]),'Exactly36 bootstrap literal operands with zero unused output slots')
 heap=[list(v)for v in padded[:firstzero]];raw=[list(v)for v in struct.iter_unpack('<IIQII',provider_raw)];need(raw[:36]==heap,'Entire physical heap bootstrap equals first36 same-instance provider operands')
 w=struct.unpack('<16Q',create_raw);need(w[:6]==(1,0,1,0,4096,0)and w[6]>0xffffffff and w[7]==TOKEN and w[11]==w[6]and w[12:]==(0x20001848,0x780039d6,0x20001858,0x780039d6),'Actual owned HeapCreate result/token/frame; token predicted from physical source constant')
 provider=row['provider_source_accesses'];need(provider,'Nonempty complete provider scope');hits=[i for i in range(36,len(raw)-len(provider)+1)if raw[i]==provider[0]and raw[i:i+len(provider)]==provider];need(len(hits)==1,'Exactly one entire actual current constructor provider interval')
 cut=hits[0];whole=row['whole_literal_source_accesses'];fields=[]
 for address,predicted,publish_pc,publish_index,read_pc in FIELDS:
  publication=[publish_pc,address,predicted,4,1];need(heap[publish_index]==publication,'Exact literal initializer source publication, no measured value chosen as input')
  need(not any(v[4]and overlap(v,address)for v in raw[publish_index+1:cut]),'Entire actual prior provider chronology retains source-published field')
  indices=[i for i,v in enumerate(whole)if overlap(v,address)];need(indices,'Actual constructor consumes named heap field');first=indices[0];need(whole[first]==[read_pc,address,predicted,4,0]and not any(v[4]and overlap(v,address)for v in whole[:first]),'Exact first own source read before overlapping write corroborates initializer prediction')
  need(all(v==[v[0],address,predicted,4,0]for v in (whole[i]for i in indices)),'Entire current literal scope only reads exact declared DWORD')
  need(any(v==whole[first]for v in provider),'First own literal field operand belongs to wholly matched actual provider scope')
  fields.append(dict(address=address,bytes=4,predicted_value=predicted,publication_source_PC=publish_pc,bootstrap_access_index=publish_index,first_read_source_PC=read_pc,first_read_whole_source_index=first,no_prior_overlapping_source_write=True,actual_prior_provider_cut=cut))
 return dict(memory_hex=struct.pack('<2I',TOKEN,1).hex(),address=0x78035000,bytes=8,fields=fields,source_prediction='literal owned HeapCreate token then literal successful mode1 publication; actual first reads are corroboration',whole_page_claim=False,whole_TIB_claim=False,AFTER_input_used=False,source_bootstrap_count=36,actual_provider_interval_start=cut,actual_provider_interval_count=len(provider))
