"""Add exact literal registration epilogues beyond the observed prefix boundary."""
from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent;R=p.parents[1];previous=p/'prepare_v2.py';text=previous.read_text()
marker="exec(compile(s,str(base),'exec'),globals())"
addition='''
old="instructions=contracts['instructions'];byPC={row['pc']:row for row in instructions};need(len(byPC)==1093,'1093 exact six-root physical rows')"
new=old+"""
 epilogues=[]
 for root,observed in zip(roots,font):
  need(root['root']==observed['root'],'Exact six normal prefix/epilogue association')
  reg=root['registration'];call=reg.get('CALL_pc',reg.get('registration_CALL_pc'));need(type(call)is int,'Literal current registration CALL PC')
  pcs=[0x5ac124,0x5ac127,0x5ac14a,0x5ac14d,0x5ac14f,0x5ac151,0x5ac153,0x5ac154,call+5,call+8]
  expected=[('add','esp, 0x4'),('ret',''),('add','esp, 0x4'),('neg','eax'),('sbb','eax, eax'),('neg','eax'),('dec','eax'),('ret',''),('add','esp, 0x4'),('ret','')]
  need([(byPC[q]['mnemonic'],byPC[q]['operands'])for q in pcs]==expected,'Exact physical straight-line integer/stack epilogue')
  need(observed['source_PCs'][-1]==0x5ac11e and observed['source_accesses'][-1][:2]==[0x5ac11e,root_frame-24],'Original proof stops at the actual source provider CALL')
  accesses=[[0x5ac127,root_frame-16,0,4,False],[0x5ac154,root_frame-8,0,4,False],[call+8,root_frame,0,4,False]]
  epilogues.append(dict(root=root['root'],provider_return_PC=0x5ac124,source_PCs=pcs,source_read_PC_and_frame_offsets=[[a[0],a[1]-root_frame,a[3],a[4]]for a in accesses],value_oracle=False,observed_prefix_tail_extended_by_literal_physical_source=True))
  observed['source_PCs']=observed['source_PCs']+pcs;observed['source_accesses']=observed['source_accesses']+accesses
 """
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("'schema':'mw34-widget-native-source-contracts-v1'", "'schema':'mw34-widget-native-source-contracts-v2','registration_epilogues':epilogues")
s=s.replace("'causal_operands':oi", "'causal_operands':oi,'observed_prefix_operands':24625,'literal_epilogue_read_operands':18,'literal_epilogue_instruction_occurrences':60")
s=s.replace("for p in [base,Path(__file__).resolve(),", "for p in [base,previous,Path(__file__).resolve(),")
'''
assert text.count(marker)==1;text=text.replace(marker,addition+'\n'+marker)
exec(compile(text,str(previous),'exec'),globals())
