from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];old=ROOT/'tools/m4-container-source/derive_geometry.py';new=ROOT/'tools/m4-container-source/derive_geometry_v2.py';assert not new.exists();s=old.read_text()
anchor="  model=G.Machine(state,bytes(512),bytes(40),memory,program=program,callbacks=callbacks)"
addition='''  nullfrees=[];borrowed=[]
  def observer(machine,event,data):
   if event=='control'and data['op']=='call'and data['target']in(0x5abd1a,0x5abdb0):
    frame=machine.reg('esp');row=dict(root=current['entry'],CALL_pc=data['site'],frame=frame,return_pc=int.from_bytes(machine.bytes(frame,4),'little'),entry_ECX=machine.reg('ecx'),FS0=int.from_bytes(machine.bytes(0x7ffde000,4),'little'),cpu_after_CALL=list(machine.projected_cpu()))
    if data['target']==0x5abd1a:row['argument']=int.from_bytes(machine.bytes(frame+4,4),'little');need(row['argument']==0,'Normal literal game freeNULL argument');nullfrees.append(row)
    else:row['object']=machine.reg('ecx');borrowed.append(row)
   if event=='control'and data['op']=='call'and data['site']==0x5f401786:
    row=nullfrees[-1];need(row['root']==current['entry'],'Exact active original nullfree');row['CRT_frame']=machine.reg('esp');row['CRT_return_pc']=int.from_bytes(machine.bytes(machine.reg('esp'),4),'little');row['CRT_argument']=int.from_bytes(machine.bytes(machine.reg('esp')+4,4),'little')
   if event=='returned'and data['site']==0x5f40178d:
    row=nullfrees[-1];need(data['target']==row['return_pc']and data['frame']==row['frame'],'Exact literal MFCfreeNULL RET');row['returned_cpu']=list(machine.projected_cpu());row['returned_FS0']=int.from_bytes(machine.bytes(0x7ffde000,4),'little');need(row['returned_FS0']==row['FS0'],'Nested CRTfreeNULL normal chain restored')
   if event=='read-after'and data['pc']==0x5f4020bc:
    row=borrowed[-1];row['read_PC']=data['pc'];row['read_address']=data['address'];row['borrowed_value']=data['value']
  model=G.Machine(state,bytes(512),bytes(40),memory,program=program,callbacks=callbacks,hook=observer)'''
assert s.count(anchor)==1;s=s.replace(anchor,addition)
anchor="  for filename,data in (('allocation-derivations.json',allocations),('root-derivations.json',observations))"
assert s.count(anchor)==1;s=s.replace(anchor,"  need(len(nullfrees)==5 and len(borrowed)==3 and all(r['read_address']==0x5f4ccb54 and r['borrowed_value']==0x5f4cecec for r in borrowed),'Five source nullfrees and three exact borrowed reads')\n  for filename,data in (('allocation-derivations.json',allocations),('root-derivations.json',observations),('nullfree-derivations.json',nullfrees),('borrowed-derivations.json',borrowed))")
compile(s,str(new),'exec');new.write_text(s)
