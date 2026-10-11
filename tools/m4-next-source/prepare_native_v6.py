"""Bind final producer4 field convention and exact actual source prefixes."""
from pathlib import Path
T=Path(__file__).resolve().parent
p=T/'compare_connected_v5.py';q=T/'compare_connected_v6.py';assert not q.exists()
s=p.read_text()
a="      elif derived['CALL_pc']==0x59fdc5:need(w[10:14]==(0,binding['source_vtable'],0,0),'Absolute cell call has no fabricated instance-vptr read indices')"
b="      elif derived['CALL_pc']==0x59fdc5:need(w[10:12]==(binding['source_vtable'],binding['source_vtable'])and w[12]and w[13]==0,'Absolute cell call binds committed publication and has no fabricated instance-vptr read index')"
assert s.count(a)==1;s=s.replace(a,b)
a="     actual_calls=list(struct.iter_unpack('<32Q',a.data(stem+'vtable-call-witnesses.bin')));need(len(actual_calls)==6,'Six actual rooted native indirect CALL/RET records')"
b=a+";actual_source=list(struct.iter_unpack('<IIQII',a.data(stem+'locale-source-accesses.bin')))"
assert s.count(a)==1;s=s.replace(a,b)
a="      joins=[]"
b="""      need(w[8]==w[22]and actual_source[w[8]]==(derived['CALL_pc'],derived['slot'],derived['target'],4,0),'Actual exact physical cell read begins source prefix')
      equal([list(r)for r in actual_source[w[22]:w[23]]],derived['source_accesses'],'Entire actual native helper CALL/body/RET source access prefix from persistent BEFORE')
      if binding.get('source_vtable'):
       need(actual_source[w[12]]==(binding['dominating_vtable_store_PC'],binding['source_object'],binding['source_vtable'],4,1),'Actual dominating source vptr publication in exact source ledger')
       if derived['CALL_pc']==0x59ff6e:need(actual_source[w[13]]==(0x59ff64,binding['source_object'],binding['source_vtable'],4,0),'Actual subsequent source instance-vptr read before derived slot')
      derived['actual_native_source_access_prefix']=[list(r)for r in actual_source[w[22]:w[23]]];counts['whole_native_indirect_source_access_prefixes']+=1
      joins=[]"""
assert s.count(a)==1;s=s.replace(a,b)
compile(s,str(q),'exec');q.write_text(s)
