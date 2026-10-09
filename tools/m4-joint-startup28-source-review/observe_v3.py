"""Independent new SPI BEFORE model plus unchanged frozen27 observation scope.

No execution bridge/author comparator is imported. New SPI effects are predicted
from its original BEFORE pages/CPU and actual finite API BOOL/RECT. Prior FP
roots retain the accepted separately measured raw numerical oracle boundary.
Original AFTER data are comparison observations, never reseeds of native input.
"""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback,collections
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-joint-startup28-source-review';PINS={}
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000)
COMMON,NATIVE,SUMMARY=141540,159716,147400
MEM0,MEM1=2276,71908
SB,SA,COUNTS,EVENTS,ROUTES=141540,145044,148548,148588,152428
NUMVIEW,NUMEVENT,NUMROUTE,NUMLABEL,SPI=152620,156704,157144,157204,157212
FRAME,BROKER,ENTRY,CALL,RESUME,IAT,OBJECT,OUTPUT=0x20001800,0x410a80,0x482cf0,0x482cdd,0x482ce3,0x5bb6dc,0x608f88,0x608fa0
CASES=((0,0x7f,0),(0,0x37f,7),(0,0xf7f,0),(1,0x47f,7),(1,0xa7f,0),(1,0xe7f,7))
def need(ok,s):
 if not ok:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Input identity '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable input');PINS[str(p)]=v;return p
def own(p,name,h=None):
 sp=importlib.util.spec_from_file_location(name,pin(p,h));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def w(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def mem(b,after=False):return b[MEM1:COMMON]if after else b[MEM0:MEM1]
def st(b,after=False):return b[SA:COUNTS]if after else b[SB:SA]
def mo(a):need(a&~4095 in PAGES,'Owned observedpage');return PAGES.index(a&~4095)*4096+(a&4095)
def put(b,o,v,n=4):b[o:o+n]=v.to_bytes(n,'little')
def project_original(o,raw_numeric,raw_spi,original_spi_shim):
 b=bytearray(o[:COMMON])
 for off in(MEM0,MEM1):
  need(w(b,off+mo(0x5bb4fc))[0]==0x780c10f0,'Actual numeric owningIAT');put(b,off+mo(0x5bb4fc),raw_numeric)
  need(w(b,off+mo(IAT))[0]==original_spi_shim,'Actual SPI owningIAT');put(b,off+mo(IAT),raw_spi)
 return bytes(b)
def spi_goal(cpu,before,service,native):
 need(len(service)==1212,'Exact SPI ABI record');p=bytearray(before);events=[];transports=[];c=list(cpu)
 def e(pc,a,v,op):
  if op:put(p,mo(a),v)
  else:need(w(p,mo(a))[0]==v,'Source SPI read')
  events.append((pc,a,v,4,op))
 # The 3 literal entries transfer only PC until this source helper starts.
 for pc,a,v in((0x482cc0,FRAME-4,c[3]),(0x482cc3,FRAME-8,c[6]),(0x482cc4,FRAME-12,c[7]),(0x482cc8,FRAME-16,0),(0x482cd6,FRAME-20,OUTPUT),(0x482cd7,FRAME-24,0),(0x482cd9,FRAME-28,0x30)):e(pc,a,v,1)
 for i in range(6):v=w(p,mo(0x5e6000+4*i))[0];e(0x482cdb,0x5e6000+4*i,v,0);e(0x482cdb,OBJECT+4*i,v,1)
 e(CALL,IAT,0x1df20c,0);e(CALL,FRAME-32,RESUME,1)
 expected_before=(OUTPUT,0,c[2],OBJECT,FRAME-32,c[5],0x5e6018,OUTPUT,c[8],CALL)
 need(w(service,0,10)==expected_before,'Complete independently predicted actual SPI entry CPU')
 after=w(service,40,10);called,boolean,cleanup,pesp0,pesp1=w(service,1192,5)
 need(called==1 and boolean==after[0] and cleanup==16,'Measured finite actual API BOOL/cleanup')
 need(tuple(after[i]for i in(3,4,5,6,7,9))==(OBJECT,FRAME-12,c[5],0x5e6018,OUTPUT,RESUME)and not after[8]&0x400,'SPI nonvolatile/DF ABI')
 if native:need(after[1:3]==(0,c[2])and after[8]==c[8]and pesp0==pesp1==0,'Native explicit bounded representative ABI')
 else:need(pesp0 and pesp0+20==pesp1 and pesp0!=FRAME-32,'Measured actual32 physical stdcall16')
 need(service[1160:1176]==p[mo(OUTPUT):mo(OUTPUT)+16],'Actual RECTbeforeextent')
 for i,v in enumerate((RESUME,0x30,0,OUTPUT,0)):transports.append((CALL,FRAME-32+4*i,v,4,0))
 if native:
  for i in range(4):transports.append((CALL,OUTPUT+4*i,w(service,1160+4*i)[0],4,0))
  for i in range(4):transports.append((CALL,OUTPUT+4*i,w(service,1160+4*i)[0],4,1))
 for i in range(4):v=w(service,1176+4*i)[0];put(p,mo(OUTPUT+4*i),v);transports.append((CALL,OUTPUT+4*i,v,4,1))
 for pc,a,v in((RESUME,FRAME-12,c[7]),(0x482ce6,FRAME-8,c[6]),(0x482ce7,FRAME-4,c[3]),(0x482ce8,FRAME,BROKER)):e(pc,a,v,0)
 final=(OBJECT,after[1],after[2],c[3],FRAME+4,c[5],c[6],c[7],after[8],BROKER)
 return dict(after=final,pages=bytes(p),events=[x[1:]for x in events],pc_events=events,transports=transports,routes=[],counts=(25,11,14,0,0,1,0,0,1,0))
def first_memory(prep,raw_spi,raw_numeric):
 pack=pin(prep/'pages.bin').read_bytes();need(pack[:8]==b'MW4J28P1' and w(pack,8)[0]==29,'Original exactpack')
 pages={a:pack[20+i*4104:4116+i*4104]for i in range(29)for a,p in[w(pack,12+i*4104,2)]};b=bytearray(b''.join(pages[p]for p in PAGES));put(b,mo(FRAME),BROKER);put(b,mo(IAT),raw_spi);put(b,mo(0x5bb4fc),raw_numeric);return bytes(b)
def closure(report):
 r=json.loads(pin(report).read_text(encoding='utf-8-sig'));need(r['passed'],'Passed stage')
 p=Path(report).parent/'pins.json'
 if p.exists():
  for a,h in json.loads(pin(p).read_text(encoding='utf-8-sig'))['files'].items():pin(a,h)
 return r
def check_original(m,o,literal,tag,cpu,before,goal,previous):
 need(w(o,0,9)==tag,'Actual originalphase tag');mask=0xcd5 if tag[2]<=2 else 0xcc5
 # Carry is compared within the actual x86 branch, including every API-volatile field.
 m.equalcpu(w(o,36,10),cpu,mask,'Original CPU BEFORE carry');m.equalcpu(w(o,76,10),goal['after'],mask,'Original literal source CPU/RET')
 need(mem(o)==before and mem(o,True)==goal['pages'],'Whole17 originalpages/BEFORE-sourceeffects');m.hostcheck(o,False)
 if previous is not None:need(o[116:628]==previous[628:1140] and o[2164:2192]==previous[2192:2220],'Actual original fullFX/ENVcarry')
 if tag[4]==ENTRY:
  service=literal[142260:];need(service[80:592]==o[116:628]and service[592:1104]==o[628:1140],'Actual fullSPIserviceFXcarry');need(service[1104:1132]==o[2164:2192]and service[1132:1160]==o[2192:2220],'Actual fullSPIserviceENVcarry')
 elif tag[4]not in m.FP and tag[4]!=0x4c19f0:need(o[116:628]==o[628:1140]and o[2164:2192]==o[2192:2220],'Integer originalpreserves FP')
 need(literal[COMMON:142260]==bytes(720),'Primarydirect numericdebuggerfieldsinactive')
def native_phase(J,m,c,n,tag,cpu,before,goal,sb,sa,o,cp=None,pc_events=None):
 need(len(n)==NATIVE and w(n,0,8)==tag[:8],'Nativeexactphase tag');mask=0xcd5 if tag[2]<=2 else 0xcc5
 m.equalcpu(w(n,36,10),cpu,mask,'Native ownbranch CPU BEFORE');m.equalcpu(w(n,76,10),goal['after'],mask,'Native source CPU AFTER')
 need(mem(n)==before and mem(n,True)==goal['pages'],'Entire17nativepages fromBEFORE');need(st(n)==sb and st(n,True)==sa,'Entire3504State includingopaque/highregisters')
 J.projection(m,n,sb);J.projection(m,n,sa,True)
 need(w(n,COUNTS,10)==goal['counts'],'Literal counters')
 ev=b''.join(struct.pack('<IQII',*row)for row in goal['events']);need(n[EVENTS:ROUTES]==ev+bytes(3840-len(ev)),'All source events andinactive storage')
 if tag[4]==ENTRY:
  need(w(n,SPI+1212,3)==(1,25,17),'Actual SPI ledger counts');packed=b''.join(struct.pack('<5I',*e)for e in goal['pc_events']);need(n[SPI+1224:]==packed+bytes(1280-len(packed)),'AllPCbearingSPIevents')
  need(n[NUMVIEW:NUMROUTE]==bytes(4524)and w(n,NUMLABEL,2)==(0,3),'Numeric tailinactive forSPI');need(n[ROUTES:NUMVIEW]==bytes(192),'No fabricatedhelperCALLroutes')
  need(w(n,NUMROUTE,15)==(BROKER,ENTRY,BROKER,0,1,CALL,IAT,RESUME,1,1)+(0,)*5,'Actual2SPI RuntimeCALLroutes')
  need(n[116:628]==n[628:1140] and n[2164:2192]==n[2192:2220],'Native representativenumericalcarry');m.hostcheck(n,True)
 else:
  need(n[SPI:]==bytes(2504),'SPI tailinactive')
  if tag[4]==0x4c19f0:
   need(n[NUMVIEW:NUMEVENT]==c.P.view(cp),'FullnumericBEFOREoracle checkpoint');need(n[NUMEVENT:NUMROUTE]==pc_events,'Numeric22PCevents');need(w(n,NUMLABEL,2)==(1,2),'Numericlabels');need(w(n,NUMROUTE,15)==(BROKER,0x4c19f0,BROKER,0,1,0x4c19f3,0x4c1a00,0x4c19f8,0,1,0x4c1a03,0x5bb4fc,0x4c1a09,1,1),'Numeric3runtimeCALLroutes');need(n[ROUTES:NUMVIEW]==bytes(192),'Numerichelperrouteinactive')
  else:
   need(w(n,NUMLABEL,2)==(0,1) and n[NUMVIEW:NUMROUTE]==bytes(4524),'Nonnumericlabel/tail');need(w(n,NUMROUTE,15)==(BROKER,tag[4],BROKER,0,1)+(0,)*10,'Exact Runtime rootCALL')
   for i,r in enumerate(goal['routes']):
    off=ROUTES+96*i;need(w(n,off,4)==r[:4],'Sourcehelperroute');m.equalcpu(w(n,off+16,10),r[4],mask,'SourcehelperBEFORE');m.equalcpu(w(n,off+56,10),r[5],mask,'SourcehelperAFTER')
   need(n[ROUTES+96*len(goal['routes']):NUMVIEW]==bytes(192-96*len(goal['routes'])),'Unusedhelperroutebytes');m.hostcheck(n,True)
 # x86 API ENV metadata changes have no source consumer: following FLD overwrites it.
 # Numeric core/raw80 still equal; full metadata comparison resumes after that root.
 for off,env,s in((116,2164,sb),(628,2192,sa)):
  fx,_=m.proj(s);need(m.hardwarefx(fx)==o[off:off+512],'Portable numericalcore/fullhardwareFX')
  if not(tag[4]==ENTRY or tag[4]==0x4adb50 and off==116):need(o[env:env+28]==n[env:env+28],'FulllegacyENV exceptunconsumedrealSPI metadata')
def main(original_report,native_report,name):
 out=BASE/name;need(not out.exists(),'Freshreview');out.mkdir(parents=True);counts=collections.Counter();corruptions=[];passed=False
 try:
  J=own(ROOT/'tools/m4-joint-startup27-review/observe.py','independent_accepted27');m,c,inst,schedule=J.models();m.PAGES=list(PAGES);J.PAGES=PAGES;J.COMMON=COMMON;J.MEM0=MEM0;J.MEM1=MEM1;J.SB=SB;J.SA=SA;J.COUNTS=COUNTS
  ds=own(ROOT/'tools/m4-crt-allocation-root/run_v2.py','strict28');orr=closure(original_report);nr=closure(native_report)
  original=ds.DirectSet(orr['original_capture'],pin);native_sets={level:ds.DirectSet(Path(native_report).parent/level/'transport.json',pin)for level in('O0','O2')}
  game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes();pe=own(ROOT/'tools/analysis/pe.py','peer28pe').PEImage(game)
  def raw(a):o,_=pe.rva_range(a-0x400000,4);return w(game,o)[0]
  rawspi,rawnumeric=raw(IAT),raw(0x5bb4fc);need(rawspi==0x1df20c,'ExactsourceIAT')
  prep=Path(orr['build_path']).parent;build=json.loads(pin(orr['build_path'],orr['build_sha256']).read_text(encoding='utf-8-sig'));prep=Path(build['preparation']);order=json.loads(pin(prep/'report.json',build['preparation_sha256']).read_bytes())['order'];initial=first_memory(prep,rawspi,rawnumeric)
  api_pe=own(ROOT/'tools/m4-spi-workarea-independent/model.py','independent_spi_pe');provider=api_pe.PE(original.data('user32-image.bin'));need(provider.machine==0x14c,'Measured32providerPE');ordinal,rva,forwarded=provider.export('SystemParametersInfoA');need(not forwarded,'Physical32requestedexport');identity=w(original.data('spi-identity.bin'),0,3);need(identity[0]+rva==identity[1],'Actual32requestedexport pointer');shim=w(original.data('phase/0/0.bin'),MEM0+mo(IAT))[0];need(identity[2]==IAT,'ActualSPIidentityIAT')
  need(original.data('header.bin')[:8]==b'MW4J28O1'and w(original.data('header.bin'),8,6)==(1,6,28,168,17,143472),'Exactdirectoriginalheader')
  for level,reader in native_sets.items():need(w(reader.data('native-header.bin'),0,6)==(1,6,28,168,17,NATIVE),'Nativefullschema')
  for seq,(repeat,cw,top)in enumerate(CASES):
   previous_o=None;previous_native={l:None for l in native_sets};previous_mem_o=initial;previous_mem_n={l:initial for l in native_sets};previous_s={l:None for l in native_sets}
   for phase,row in enumerate(order):
    entry=row['entry'];tag=(seq,repeat,phase,row['slot'],entry,cw,top,0,1);literal=original.data(f'phase/{seq}/{phase}.bin');o=project_original(literal,rawnumeric,rawspi,shim);ocpu=w(o,36,10)
    expected=list(w(previous_o,76,10))if previous_o else[0x13579bdf,0x2468ace0,0x81726354,0x10293847,FRAME,0x92837465,0x56473829,0xaabbccdd,0x202,entry];expected[4]=FRAME;expected[9]=entry;need(ocpu==tuple(expected),'Every actual originalCPU field carriedexactly')
    if entry==ENTRY:og=spi_goal(ocpu,previous_mem_o,literal[142260:],False)
    elif entry==0x4c19f0:
     # Numerical leaf's arithmetic does not read the x86 API-volatile fields.
     tmp=bytes(m.seed(ocpu,repeat,cw,top));og,_,_,_=J.numeric_goal(c,tmp,previous_mem_o)
    else:og=m.phasegoal(entry,ocpu,previous_mem_o,mem(o,True),inst[entry],schedule)
    check_original(m,o,literal,tag,expected,previous_mem_o,og,previous_o)
    for level,reader in native_sets.items():
     n=reader.data(f'sequence-{seq}/phase-{phase}.bin');ncpu=w(n,36,10);p=previous_native[level]
     ne=list(w(p,76,10))if p else list(expected);ne[4]=FRAME;ne[9]=entry;need(ncpu==tuple(ne),'Every nativeCPU field carriedexactly')
     if phase==0:sb=bytes(m.seed(ncpu,repeat,cw,top))
     elif entry==0x4c19f0:s=bytearray(previous_s[level]);m.statecpu(s,ncpu);sb=bytes(s)
     else:sb=bytes(m.beforestate(previous_s[level],ncpu,entry))
     cp=ev=None
     if entry==ENTRY:
      g=spi_goal(ncpu,previous_mem_n[level],n[SPI:SPI+1212],True);s=bytearray(sb);m.statecpu(s,g['after'],False);sa=bytes(s)
      need(n[SPI+1176:SPI+1192]==literal[142260+1176:142260+1192],'Actual32/64definedRECT outputs agree in captureddesktop')
      transitions=reader.data(f'sequence-{seq}/spi-transports.bin');need(transitions==b''.join(struct.pack('<5I',*e)for e in g['transports']),'EverycheckedAPItransport distinctfromsource')
      av=reader.data(f'sequence-{seq}/spi-api-before.bin');bv=reader.data(f'sequence-{seq}/spi-api-after.bin');need(len(av)==len(bv)==4056,'ExacttypedAPI State/FX/CPU views')
      asb=bytearray(sb);m.statecpu(asb,w(n,SPI,10),False);# Actual CALL changeslogical PC to IAT for Runtime dispatch.
      put(asb,2472,IAT);need(av[:3504]==asb,'FullAPIentryState fromoriginalBEFOREsource')
      asa=bytearray(asb);after=w(n,SPI+40,10);m.statecpu(asa,after,False);need(bv[:3504]==asa,'FullAPIreturnState onlyactualBOOL+typedcleanup')
     elif entry==0x4c19f0:g,sa,cp,ev=J.numeric_goal(c,sb,previous_mem_n[level])
     else:g=m.phasegoal(entry,ncpu,previous_mem_n[level],mem(o,True),inst[entry],schedule);sa=bytes(m.afterstate(sb,g['after'],entry,o,inst[entry]))
     native_phase(J,m,c,n,tag,ne,previous_mem_n[level],g,sb,sa,o,cp,ev)
     if entry==ENTRY:
      # New SPI-only read-only causal controls; no historical worker replays.
      def changed_native(data):
       changed_goal=spi_goal(ncpu,previous_mem_n[level],data[SPI:SPI+1212],True)
       changed_state=bytearray(sb);m.statecpu(changed_state,changed_goal['after'],False)
       native_phase(J,m,c,data,tag,ne,previous_mem_n[level],changed_goal,sb,bytes(changed_state),o)
       need(transitions==b''.join(struct.pack('<5I',*e)for e in changed_goal['transports']),'SPI causal measured transport')
      for at in(0,36,76,92,112,MEM0+mo(OBJECT),MEM1+mo(OUTPUT),SB+3433,SA+3433,SA+2220,COUNTS,EVENTS,ROUTES,NUMROUTE,SPI,SPI+1192,SPI+1212,SPI+1224):
       altered=bytearray(n);altered[at]^=1
       try:changed_native(bytes(altered))
       except(ValueError,AssertionError,struct.error):corruptions.append(dict(sequence=seq,level=level,offset=at,rejected=True))
       else:raise ValueError('New SPI causal observer missed offset '+str(at))

     # All source-defined memory stays shared; only unconsumed CPU and observed ENV metadata differ.
     need(g['pages']==og['pages'],'Crossarchitecturedefined17page effects');previous_s[level]=sa;previous_mem_n[level]=g['pages'];previous_native[level]=n;counts['native_phases']+=1;counts['source_events']+=len(g['events']);counts['whole_State_checks']+=2
    previous_o=o;previous_mem_o=og['pages'];counts['original_phases']+=1
   for level,reader in native_sets.items():
    summary=reader.data(f'sequence-{seq}/summary.bin');need(len(summary)==SUMMARY and w(summary,0,12)==(seq,repeat,cw,top,1,28,0,0,0,0,0,0),'Completedconnectedsummary');J.outer_host(summary);need(summary[4632:8136]==previous_s[level]and summary[77768:]==previous_mem_n[level],'OutsidefinalState/pagesboundtoactualcarriedchain')
   counts['connected_sequences']+=1
  original.close()
  for r in native_sets.values():r.close()
  for dep in(J,m,c,c.P,c.R,c.O):
   for p,v in dep.PINS.items():pin(p,v['sha256']if isinstance(v,dict)else v)
  pin(__file__);passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='New literal SPI effects strictly originalBEFORE+actualfiniteBOOL/RECT; persistent28 ownbranchcarry; prior27 numericalrawobserver scope unchanged',counts=dict(counts),selected_roots=28,new_SPI_corruption_rejections=len(corruptions),per_phase_reseed=False,all_original_volatile_outputs_retained=True,native_representative_policy_explicit=True,localized_ENV_comparison='Actual32SPImetadata unconsumed; following4ADB50FLD overwrites before source consumers; rawABIwitness preserved',prior_FP_oracle_policy='Accepted originalhardwareoutput/raw80/status observations retained for10priorFP roots; no newBEFORE-onlynumerical proofclaimed',original_software_State_observed=False,whole_M4_complete=False,files=PINS)
  (out/'corruptions.json').write_text(json.dumps(corruptions,indent=2)+'\n');pin(out/'corruptions.json');(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3])
