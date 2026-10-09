"""Literal MFC causal checks over frozen actual captures; no candidate AFTER oracle."""
import struct

def need(value,why):
 if not value:raise ValueError(why)
def rows(a,path,fmt):return list(struct.iter_unpack(fmt,a.data(path)))
def check_mfc(a,c,records,allocations,metrics,causes):
 live=f'case-{c}/first-live/';clean=f'case-{c}/first-cleaned/'
 w=a.words(f'case-{c}/first-trigger-mfc.bin',32,'Q');probe=a.words(f'case-{c}/first-trigger-store.bin',8,'Q')
 qs=rows(a,live+'mfc-allocation-witnesses.bin','<32Q');done=rows(a,clean+'mfc-allocation-witnesses.bin','<32Q')
 stores=rows(a,live+'mfc-store-ledger.bin','<8Q');imports=rows(a,live+'mfc-import-ledger.bin','<8Q')
 summary=a.words(live+'registry-summary.bin',32,'Q');fault=a.words(live+'locale-fault.bin',4)
 reason=a.data(live+'registry-exception-message.bin').decode()
 causal=f'case-{c}/first-causal-';state=a.data(causal+'state.bin');stack=a.data(causal+'stack.bin')
 inputs=a.words(causal+'inputs.bin',3);probes=rows(a,causal+'probe-inputs.bin','<7Q')
 need(len(state)==3504 and len(stack)==4096,'Entire immediate fault State and source stack captured before cleanup')
 if c==0:
  need(len(qs)==len(done)==35 and len(allocations)==52,'35 genuine MFC,16 accepted strings and one real registry owner')
  need(sum(p[6]==4 for p in allocations)==35 and all(p[10] and not p[11]for p in allocations),'All ordinary private owners actually source-freed')
  for q in done:
   need(q[21]==q[23]==q[30]==1 and q[16]==q[20] and q[17] and not q[31] and q[25]==0x5f401782 and q[27]==q[26]-8 and q[28:30]==(0x7800138a,0x78001390),'Genuine object publication and literal825/CRTfree original cdecl geometry')
  metrics['normal_MFC_source_frees']=metrics.get('normal_MFC_source_frees',0)+35
  need(not any(w) and not probes,'No ordinary fabricated intervention')
  return
 need(summary[3]==1 and fault[0]==1 and summary[16:18]==fault[1:3],'Actual immediate first-fault PC/address captured')
 causes[f'{c}-{metrics["ordinary_sequences"]}']=dict(case=c,pc=summary[16],address=summary[17],stage=fault[3],message=reason)
 if c==1:
  need(not any(w) and not qs and not any(p[6]==4 for p in allocations),'Changed raw owning game ordinal refuses before MFC allocation')
  need(inputs[1]==0x5f401ea0,'Actual wrong raw ordinal mutation retained')
 else:
  need(w[0]==1 and w[3]==0x5f401ea0 and w[7]==(128 if c==20 else 12),'Exact literal source allocator request')
  need(w[2]==(0x4a8c20 if c==20 else 0x40ffe0) and qs and qs[w[1]][:8]==w[:8],'Actual intended source root/site/frame retained')
  q=qs[w[1]]
  if c in (2,3,8,9):need(not any(p[6]==4 for p in allocations) and not q[16],'Actual early refusal precedes object HeapAlloc')
  else:need(q[16] and q[17] and any(p[5]==q[18] and p[6]==4 for p in allocations),'Actual full-width native object owner generation acquired')
  if c in (4,5,6,7,10,11,12,13):need(sum(p[6]==4 for p in allocations)==1,'Only first genuine object acquired before failure')
  if c in(5,6,7,12,13,20):
   extent=q[19];stem=live+f'locale-allocation-{q[18]}'
   initial=a.data(stem+'-initial.bin');expected=a.data(stem+'-expected.bin');owned=a.data(stem+'-owned-page.bin')
   count={5:0,6:4,7:8,12:0,13:4,20:4}[c]
   need(q[24]==count and q[23]==int(c==20) and expected==owned,'Exactly committed source bytes and entire guest owner mirror; zero-fill object already published by4A8C47')
   want=bytearray(initial)
   if c==20:want[:4]=bytes(4)
   elif count:want[:count]=struct.pack('<I',q[16])*(count//4)
   need(len(initial)==extent and expected[:extent]==want and expected[extent:]==bytes(len(expected)-extent),'Entire source-derived initialized prefix, untouched native remainder and mapped zero padding')
   need(a.data(f'case-{c}/first-trigger-native-before.bin')==want,'Full actual native extent at interruption agrees with committed literal stores')
   ownstores=[s for s in stores if s[1]==q[1]and s[7]==1]
   need(sum(s[5]for s in ownstores)==count,'Actual exact committed private source-store ledger')
   if c in(6,13,20):metrics['partial_transfer_faults']+=1
  if c==4:
   before=a.data(f'case-{c}/first-trigger-native-before.bin');after=a.data(f'case-{c}/first-trigger-native-after.bin');want=bytearray(before);want[0]^=0x55
   need(len(before)==q[19] and after==want and q[21]==q[23]==q[24]==0,'Actual full-width single backing-byte flip before allocator return/publication')
  if c==3:need(inputs[2]==0,'Actual changed owned handler value retained; whole-page guard, no handler execution')
  if c==7:need(inputs[0]==0,'Original zero BSS publication pointer remains unchanged after refused store')
  if 14<=c<=19:
   need(records[0][4]==1 and q[21]==q[23]==1 and q[24]==8,'One genuine constructor fully returned before research probe')
   need(len(probes)==(2 if c==18 else 1) and records[0][22]==len(probes),'Every actual research probe input retained')
   for n,p in enumerate(probes):
    argument=q[16]+4 if c==16 else 0x603fd8 if c==17 else 1048577 if c==19 else q[16]
    need(p[0]==1 and p[1]==(0x5f401ea0 if c==19 else 0x5f401782) and p[2]==p[3] and p[4]==argument and p[5]==0xffffff40 and p[6]==p[2]-4,'True CPU/State ESP, original argument memory and declared research frame/marker')
   last=probes[-1];frame=last[6];offset=frame-0x20001000
   need(stack[offset:offset+8]==struct.pack('<II',0xffffff40,last[4]),'Actual committed external source CALL marker and genuine alias/request argument')
   metrics['actual_research_probe_inputs']=metrics.get('actual_research_probe_inputs',0)+len(probes)
  if c in(15,18):need(q[30]==1 and q[31]==0 and q[25]==0x5f401782 and q[27]==q[26]-8,'One genuine source free/unmap retained before later refusal')
  if c in(14,16,17,19):need(q[30]==0 and next(p for p in allocations if p[5]==q[18])[11]==1,'Refused sourcefree retains exact owner until actual private cleanup')
  if c==20:need(struct.unpack_from('<I',state,2216)[0]==q[16]+4 and struct.unpack_from('<I',state,2248)[0]==31,'Original DWORD MOV/ADD/DEC/JNE loop advanced EAX4/ECX31 at refused next store')
 owner_address=qs[w[1]][16]if qs else None
 expectations={
 1:(0x5abd26,0x5bb4bc,45,'Exact game MFC ordinal823 source import relocation'),
 2:(0x5f401eb5,0x780039bf,71,'Heap creation observer changed State/FX or ownership/lifecycle ledgers'),
 3:(0x5f401ea0,0x5f498000,70,'Only committed source/API/research effects may change owned locale pages'),
 4:(0x5f401eb7,owner_address,72,'Checked complete current guest/native allocation backing and private generation required'),
 5:(0x4c7b91,owner_address,73,'Checked actual source locale/parser store fault'),
 6:(0x4c7b93,owner_address+4 if owner_address else None,73,'Checked actual source locale/parser store fault'),
 7:(0x4c7b99,0x603fdc,73,'Checked actual source locale/parser store fault'),
 16:(0x5f401782,owner_address+4 if owner_address else None,45,'MFC free entry requires exact live whole private object and generation'),
 17:(0x5f401782,0x603fd8,45,'MFC free entry requires exact live whole private object and generation'),
 18:(0x5f401782,owner_address,45,'MFC free entry requires exact live whole private object and generation'),
 19:(0x5f401ea0,probes[-1][6]if probes else None,45,'Exact root/site/request for original MFC allocator CALL'),
 20:(0x4a8c55,owner_address+4 if owner_address else None,73,'Checked actual source locale/parser store fault')}
 observer={8:(0x5f401ea0,70),9:(0x5f401eb5,71),10:(0x5f401eb7,72),11:(0x4c7b91,75),12:(0x4c7b91,73),13:(0x4c7b91,74),14:(0x78001390,76),15:(0xffffff40,77)}
 if c in observer:
  pc,stage=observer[c];expectations[c]=(pc,0,stage,'Independent deliberate MFC source boundary observer failure')
 expected_pc,expected_address,expected_stage,expected_reason=expectations[c]
 need((summary[16],summary[17],fault[3],reason)==(expected_pc,expected_address,expected_stage,expected_reason),'Exact intended immediate cause '+str((c,causes)))
 if c in(8,9,10):need(q[21]==q[24]==q[23]==0,'Specific entry/CALL/mallocRET incomplete source prefix')
 if c==11:need(q[21]==1 and q[24]==q[23]==0,'Genuine MFC allocatorRET before any object initialization')
 if c==14:need(q[27]==q[26]-8 and q[28:30]==(0x7800138a,0x78001390),'Exact genuine825 to CRTfree imported cdecl source frame')
 metrics['actual_MFC_control_faults']=metrics.get('actual_MFC_control_faults',0)+1
