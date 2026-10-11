def ordinary_container(a,live,source,metrics):
 nulls=rows(a,live+'container-nullfree-witnesses.bin','<32Q');borrowed=rows(a,live+'container-borrowed-witnesses.bin','<32Q');stores=rows(a,live+'container-vector-stores.bin','<16Q')
 need(len(nulls)==5 and len(borrowed)==3 and len(stores)==17,'Five true null frees/three borrowed copies/seventeen vector stores')
 need(a.words(live+'container-active.bin',2)==(0,0)and a.words(live+'container-null-active.bin',1)==a.words(live+'container-borrowed-active.bin',1)==(0,),'All actual private constructor/null-free indexes returned')
 for w in nulls:
  need(w[4]==0x5f401782 and w[7]==0 and w[8:10]==(0x80000339,0x5abd1a)and w[11]==w[16]==0x78001390 and w[12]==w[5]-8 and w[13]==0x5f40178c and w[17]==w[18]==1,'Complete literal825→CRTfree NULL frame and RET')
  need(w[19]==w[20]==w[21]==w[22]==w[29]==w[30]and w[19]!=0xffffffff,'Literal void free retains actual nonzero outer FS0 in EAX; no invented zero result')
  need(w[23]==w[24]and w[25]==w[26]and w[10]==w[31],'Null free has zero native API/owner/generation effects')
  seq=source[w[27]:w[28]];F=w[12];head=F-20
  for row in [(0x7800139f,0x7ffde000,w[19],4,0),(0x780013a5,head,w[19],4,1),(0x7800139a,F-16,0x7800ef03,4,1),(0x78001395,F-12,0x7802e260,4,1),(0x780013a6,0x7ffde000,head,4,1),(0x780013b3,F+4,0,4,0),(0x78001416,F-20,w[19],4,0),(0x78001419,0x7ffde000,w[19],4,1),(0x78001424,F,0x5f40178c,4,0)]:need(row in seq,'Authentic complete nested CRT FS/zero argument/return source prefix')
  need(not any(r[0]==0x78001435 for r in seq),'Normal zero branch never reaches native HeapFree CALL')
 for w in borrowed:
  need(w[3]==0x5f4020b4 and w[8:10]==(0x8000021c,0x5abdb0)and w[10]==w[5]-8 and w[11]==0x5f4020bc and w[12]==w[13]==0x5f4ccb54 and w[14:20]==(0x5f4020bc,0x5f4cecec,w[7],0x5f4020be,0x5f4cecec,1),'Exact borrowed DWORD accessor and committed source object copy')
  need(w[20]==0x5f4020c3 and w[21]==w[7]and w[22]==1 and w[25]==w[26]and w[27]==w[28]and w[29]==w[30],'Borrowed constructor genuine object RET/no owner/API/chain change')
 footprint=[s for s in source if s[1]<0x5f4cd000 and s[1]+s[3]>0x5f4cc000]
 need(footprint==[(0x5f4020bc,0x5f4ccb54,0x5f4cecec,4,0)]*3,'Entire observed provider data-page source footprint is exactly three scalar reads')
 for w in stores:
  need(w[15]>0 and source[w[15]-1]==(w[3],w[4],w[6],4,1)and w[6]==w[9]+(w[11]if w[7]==3 else 0),'Every precise endpoint is a genuine owned source store')
 need({w[3]for w in stores if w[7]in(4,5)}=={0x5a8800,0x5a8803},'Both additional source-derived empty vector pointer fields')

def cause_checks(a,c,live,source,frames,tib,active,metrics,causes):
 if not c:return
 p=f'case-{c}/first-trigger/';null=a.words(p+'nullfree.bin',32,'Q');borrowed=a.words(p+'borrowed.bin',32,'Q');string=a.words(p+'string.bin',32,'Q');vec=a.words(p+'vector.bin',16,'Q');mf=a.words(p+'mfc.bin',32,'Q');frame=a.words(p+'frame.bin',32,'Q');identity=a.words(p+'identity.bin',3)
 fault=a.words(live+'locale-fault.bin',4);reason=a.data(live+'locale-fault-reason.bin').decode();tags=struct.unpack_from('<32Q',a.data(f'case-{c}/first.bin'))
 store='Checked actual source locale/parser store fault';private='Container observer changed private import/borrowed/null-free/store witnesses';observer='Deliberate precise container/borrowed/null-free boundary observer failure';page='Only committed source/API/research effects may change owned locale pages'
 expected={1:(0x5abd1a,0x5bb4c8,75,'Exact container game owning ordinal source import relocation'),2:(0x5abdb0,0x5bb454,55,'Exact container game owning ordinal source import relocation'),3:(0x5f4020b4,0x5f4cc000,94,page),4:(0x5f4020be,borrowed[7],97,store),5:(0x5f401782,0x20001000,90,page),6:(0x78001390,0,91,observer),7:(0x5f40178c,0,92,observer),8:(0x780013a6,0x7ffde000,91,store),9:(0x4ad8eb,0x60b11c,100,store),10:(0x4ad90c,0x60b114,73,store),11:(0x4ad91a,0x60b118,100,store),12:(0x78002fde,string[10]+4,53,store),13:(0x4ad8eb,mf[16],101,'Checked complete current guest/native allocation backing and private generation required'),14:(0x482b4e,0x7ffde000,81,store),15:(0x4ad91f,0x7ffde000,83,store)}
 for k,pc,point in [(16,0x5f4020be,97),(17,0x78001390,91),(18,0x5f4020b4,94),(19,0x4ad8eb,100),(20,0x4ad8eb,101),(21,0x5f401782,90)]:expected[k]=(pc,pc,point,private)
 points={90:0x5f401782,91:0x78001390,92:0x5f40178c,93:0x4ad8dd,94:0x5f4020b4,95:0x5f4020bc,96:0x5f4020bc,97:0x5f4020be,98:0x5f4020be,99:0x482b7b,100:0x4ad8eb,101:0x4ad8eb}
 if c>=22:point=90+c-22;expected[c]=(points[point],0,point,observer)
 need((fault[1],fault[2],fault[3],reason)==expected[c]and tags[12:14]==fault[1:3],'Exact actual reached cause/stage/source PC/address '+str(c))
 need(50<=identity[0]<=101 and identity[1]!=0,'Actual observed trigger boundary/source PC identity')
 if c in(4,8,9,10,11,12,14,15):need(not any(s[0]==fault[1]and s[1]==fault[2]and s[4]for s in source),'First refused source store never committed')
 if c in(9,10,11,13,32,33):
  need(mf[17]and len(a.data(p+'native-before.bin'))==mf[19]and not any(s[4]and mf[16]<=s[1]<mf[16]+mf[7]for s in source),'Actual full vector backing retained with no fabricated initialization/relocation')
  need(a.data(p+'native-before.bin')==a.data(live+f'locale-allocation-{mf[18]}-initial.bin'),'Full native vector backing remains genuine acquired initial bytes')
  if c==13:
   want=bytearray(a.data(p+'native-before.bin'));want[-1]^=0x55;need(a.data(p+'native-after.bin')==want==a.data(live+f'native-full-{mf[18]}.bin'),'True entire rounded native backing and exact last-byte corruption')
  metrics['full_native_prefix_controls']+=1
 if c==12:
  need(string[16]==4 and len(a.data(p+'native-before.bin'))==string[13],'Actual genuine four-byte string copy prefix')
  initial=a.data(live+f'locale-allocation-{string[12]}-initial.bin');want=bytearray(initial);want[:4]=a.data(live+'string-0-input.bin')[:4]
  need(a.data(p+'native-before.bin')==bytes(want)==a.data(live+f'native-full-{string[12]}.bin'),'Exactly four real copied bytes and all untouched initial trailing native backing')
  metrics['full_native_prefix_controls']+=1
 if c in(6,7,8,17,21,22,23,24,25):need(null[19]==frame[9]and frame[15]and not frame[19]and tib[1]==frame[9],'Actual null-free source boundary retains genuine active game outer record')
 if c==7 or c==24:need(null[17]and not null[18]and null[21]==frame[9]and null[23]==a.words(live+'registry-summary.bin',32,'Q')[12],'Actual literal CRT null RET precedes MFC RET and has no API effect')
 if c in(16,17,18,19,20,21):
  need(identity[2]==1,'Exactly one actual private span/scalar mutation')
  if c==16:need(rows(a,live+'container-borrowed-witnesses.bin','<32Q')[-1][18]==borrowed[18]^1,'Genuine private borrowed witness word flipped')
  if c==17:need(rows(a,live+'container-nullfree-witnesses.bin','<32Q')[-1][7]==null[7]^1,'Genuine private zero-argument witness flipped')
  if c==18:need(rows(a,live+'container-import-ledger.bin','<8Q')[-1][6]==0x5f4020b4^1,'Genuine last import relocation witness flipped')
  if c==19:need(a.words(live+'container-vector-probe.bin',16,'Q')[6]==vec[6]^1,'Genuine private source endpoint probe flipped')
  if c==20:need(rows(a,live+'container-vector-stores.bin','<16Q')[-1][6]==vec[6]^1 and source[-1]==(vec[3],vec[4],vec[6],4,1),'Only private committed ledger changes; actual source store stays genuine')
  if c==21:need(a.words(live+'container-null-active.bin',1)==(1^1,),'Genuine private active scalar changed')
 causes.append(dict(case=c,pc=fault[1],address=fault[2],stage=fault[3],message=reason,trigger_point=identity[0],trigger_PC=identity[1],completed_roots=tags[4]));metrics['causal_faults']+=1
