"""Strict original/native version validation. Invoked only with reader admission.

Raw caller/provider/heap bytes are retained. The existing field policy keeps
provider volatile registers and scratch stack observational; no generic masks.
This isolated comparison never grants carried144 initializer credit.
"""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];IMAGE_SHA='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x5ca000,0x5ed000,0x5f4000,0x603000,0x606000,0x609000,0x638000,0x63c000,0x63d000,0x72c000,0x730000,0x9a1000,0x5e4000,0x5e5000,0x5e7000,0x72b000,0x731000,0x5f498000,0x736000,0x5f4cc000,0x5bc000,0x5cf000,0x5fc000,0x7810a000,0x78145000,0x78146000)
SITES=(0x4af10e,0x4af12c,0x4af167);RETS=(0x4af113,0x4af131,0x4af16c);ARGC=(2,4,4)
def need(v,m):
 if not v:raise ValueError(m)
def digest(b):return hashlib.sha256(b).hexdigest()
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def words(b,n,kind='I'):need(len(b)==struct.calcsize('<'+str(n)+kind),'Whole typed record extent');return struct.unpack('<'+str(n)+kind,b)
def cpu(b):return words(b,10)
def delta(a,b):return dict(original_bytes=len(a),native_bytes=len(b),original_sha256=digest(a),native_sha256=digest(b),equal=a==b,byte_differences=[dict(offset=i,original=x,native=y)for i,(x,y)in enumerate(zip(a,b))if x!=y])
def own_endpoint(before,after,ret):
 need(before[4]==0x20001800 and before[9]==0x4af240 and after[4]==before[4]+4 and after[9]==ret and after[0]==0x4af270,'Exact own source root caller/RET/registered callback')
 need(all(before[i]==after[i]for i in(3,5,6,7))and not(before[8]&0x400)and not(after[8]&0x400),'Whole own root nonvolatile registers and clearDF')
def fx_arch(f):return [f[:5],f[24:28]]+[f[32+16*i:42+16*i]for i in range(8)]+[f[160:288]]
def original_provider_validation(data):
 setup=words(data('version-provider/setup.bin'),10,'Q');need(setup[0]==1 and setup[3]==0x78000000 and setup[1]!=setup[2]and setup[2]!=setup[3]and setup[7:]==(8,2,1),'Actual isolated system VERSION CRT/legacy owners and closed context before source')
 IDs=words(data('version-provider/file-IDs.bin'),28,'Q');need(IDs[:7]==IDs[7:14]and IDs[14:21]==IDs[21:]and IDs[4]==28976,'Whole actual loaded VERSION and CRT file identities equal their exact physical copies');
 raw=data('version-provider/CRT-IAT.bin');bindings=list(struct.iter_unpack('<5Q',raw));need(len(bindings)==8,'Whole eight actual VERSION system CRT import cells')
 RVAs=(20796,20800,20804,20808,20812,20816,20820,20824)
 for i,b in enumerate(bindings):need(b[0]==RVAs[i]and b[1]==b[2]and b[1]and b[3]==setup[2]and b[4]==setup[3],'Every physical VERSION CRT import maps to its actual independently named system export')
 contexts=[]
 for i in range(2):
  b=data('version-provider/context-'+str(i)+'.bin');need(0<len(b)<=4096,'Whole actual private two-file DLL redirection record');contexts.append(dict(bytes=len(b),sha256=digest(b),whole_raw_hex=b.hex()))
 path=data('version-provider/VERSION-path.bin');CRT_path=data('version-provider/CRT-path.bin');need(path.decode('utf-16-le').replace(chr(92),'/').lower().endswith('/original-preparation-r5/system-version32/version.dll')and CRT_path.decode('utf-16-le').replace(chr(92),'/').lower().endswith('/original-preparation-r5/system-version32/msvcrt.dll'),'Actual frozen isolated system32 copied provider paths')
 return dict(setup=list(setup),whole_loaded_and_expected_provider_file_IDs=list(IDs),whole_CRT_IAT_bindings=[list(b)for b in bindings],context_records=contexts,VERSION_path_hex=path.hex(),CRT_path_hex=CRT_path.hex(),VERSION_physical_sha256='4f66b88731e84be8e1545eefc589a79e701cca426ce916e4ac9322e60ea9680b',CRT_physical_sha256='23a918921c545140d189ce6dc68590bacdeb0ab2f3e3a9a2d722c5aff45ce64f',legacy_CRT_retained=True,context_inactive_before_source=True)

def original_validation(data):
 provider=original_provider_validation(data)
 h=words(data('header.bin')[8:],6);need(data('header.bin')[:8]==b'MW4J124O'and h==(1,1,1,1,43,356992),'Exact one-root ordinary original header')
 rec=data('phase/0/0.bin');need(len(rec)==356992,'Whole own original CPU/FX/ENV/pages record');tag=words(rec[:36],9);need(tag==(0,0,0,0x5e0140,0x4af240,0x7f,0,0,1),'Exact root/corpus/status/host-restored association')
 before=cpu(rec[36:76]);after=cpu(rec[76:116]);own_endpoint(before,after,0x410a80)
 need(fx_arch(rec[1140:1652])==fx_arch(rec[1652:2164])and rec[2220:2248]==rec[2248:2276],'Independently verified existing original host hardware restoration policy')
 for k,page in enumerate(PAGES):
  if not 0x400000<=page<0x1000000:continue
  a=rec[2276+k*4096:2276+(k+1)*4096];b=rec[178404+k*4096:178404+(k+1)*4096]
  need(all(x==y or 0x60b198<=page+j<0x60b198+60 for j,(x,y)in enumerate(zip(a,b))),'Every original ordinary Game page byte changes only within literal60-byte object')
 need(data('COMPLETE.txt')==b'complete'and data('cleanup/0/registry.bin')==struct.pack('<I',0x4af270),'Whole source registration data and completed original route')
 stem='phase/0/0/version';count=words(data(stem+'/count.bin'),1)[0];need(3<=count<=9 and count%3==0 and words(data(stem+'/error.bin'),1)==(0,),'Measured complete original API triplets with no forced success count')
 alloc_raw=data(stem+'/allocations.bin');need(len(alloc_raw)%40==0,'Whole private original allocation occurrences');allocations=list(struct.iter_unpack('<10I',alloc_raw));API_raw=data('phase/0/0/api-ledger.bin');need(len(API_raw)%104==0,'Whole true original heap API ledger');ledger=list(struct.iter_unpack('<26I',API_raw));need(words(data('phase/0/0/api-count.bin'),1)[0]==len(ledger),'Actual original API ledger occurrence count')
 rows=[]
 for n in range(count):
  p=stem+'/observation-'+str(n);raw=data(p+'/snapshot.bin');need(len(raw)==185224,'Whole original source/API snapshot including43pages/sourcepages/owner');w=words(raw[:64],16);c=cpu(raw[64:104]);owner=words(raw[185144:185224],10,'Q');i=n//3;side=n%3;need(w[0:5]==(1,n,0x4af240,i,side)and w[5:7]==(c[9],c[4])and w[11]==ARGC[i],'Actual same source root/index/direction/CPU snapshot')
  F=c[4];need(0x20001000<=F and F+64<=0x20002000 and not(c[8]&0x400),'Whole source committed frame64 and forward direction');frame=raw[644:708];obj=raw[708:768];owned=data(p+'/owner-bytes.bin')
  if side==0:need(c[9]==w[10]and struct.unpack_from('<I',frame)[0]==RETS[i],'Exact actual original named API entry/source saved RET')
  else:need(c[9]==RETS[i]and F==rows[3*i]['CPU'][4]+4*(ARGC[i]+1),'Exact actual source stdcall return consumes declared args')
  identity=words(data(p+'/identity.bin'),13,'Q');need(identity[0]==w[10]and identity[6:8]==(0x1000,0x1000000)and identity[10]==64 and len(data(p+'/entry64.bin'))==64,'Actual executable original VERSION export owner/entry64')
  need(identity[1]==provider['setup'][1]and data(p+'/primary-path.bin').hex()==provider['VERSION_path_hex']and data(p+'/primary-sha.bin').decode()==provider['VERSION_physical_sha256'],'Actual source API uses the frozen byte-identical Windows VERSION primary module');need(data(p+'/file-sha.bin').decode()==IMAGE_SHA and len(data(p+'/file-identity.bin'))==56,'Actual whole source relative filename file identity')
  if i:
   need(owner[0]==1 and owner[1]<len(ledger)and owner[3]<=owner[4]<=owner[5]<=1024*1024 and owner[7]==owner[8]+104 and len(owned)==owner[5],'Whole actual requested/sourceHeapAllocextent/measuredcapacity original owner')
   a=allocations[0];need(tuple(owner[:9])==tuple(a[:9])and a[9]==0x4af11f,'Same private captured actual MFC823 source return occurrence');l=ledger[owner[1]];need(l[24]==0 and l[10]==owner[2]and l[20:23]==(owner[6],0,owner[4]),'Actual original HeapAlloc request/heap/returned owner provenance')
  else:need(not any(owner)and not owned,'Size API has no fabricated allocation owner')
  rows.append(dict(index=i,side=side,CPU=c,words=w,owner=owner,snapshot=raw,frame=frame,object=obj,owned=owned,path=p,identity=identity))
 for i in range(count//3):
  triple=rows[3*i:3*i+3];entry=triple[0];err=words(data(stem+'/API-'+str(i)+'/LastError.bin'),3);hardware=data(stem+'/API-'+str(i)+'/hardware.bin');need(len(hardware)==1184 and err[0]==err[1],'Whole actual original hardware and restored incoming LastError');hb=cpu(hardware[:40]);ha=cpu(hardware[592:632]);need(hb[9]==entry['identity'][0]and ha[4]==hb[4]+4*(ARGC[i]+1)and all(hb[k]==ha[k]for k in(3,5,6,7)),'Actual original stdcall machine stack/nonvolatile ABI');post=triple[1];need(all(post['CPU'][k]==ha[k]for k in(0,1,2,3,5,6,7,8))and post['snapshot'][104:616]==hardware[640:1152]and post['snapshot'][616:644]==hardware[1152:1180]and post['words'][8]==err[2],'Whole actual original GPR/flags/FX/ENV/LastError projection')
  for suffix in('/identity.bin','/entry64.bin','/primary-path.bin','/owner-path.bin','/primary-sha.bin','/owner-sha.bin','/file-identity.bin','/file-path.bin','/file-sha.bin','/cwd.bin'):need(data(entry['path']+suffix)==data(post['path']+suffix)==data(triple[2]['path']+suffix),'Actual original named provider and physical file identities conserved')
  if i==2:
   pointer=post['owner'][9];base=post['owner'][2];length=post['words'][15];need(not post['CPU'][0]or pointer,'Actual successful original query pointer');need(not pointer or(base<=pointer and pointer-base<post['owner'][3]and length<=post['owner'][3]-(pointer-base)),'Whole returned original alias within requested current owner')
   need(entry['owner'][:9]==rows[4]['owner'][:9]and entry['owned']==rows[4]['owned'],'Same whole original owner capacity bytes carry from fill to query without unobserved writes')
 return dict(record=rec,before=before,after=after,rows=rows,allocations=allocations,API_count=count//3,provider=provider)
def native_validation(data):
 need(words(data('cleanup/status.bin'),8)==(1,1,1,10,0,0,0,0),'Actual isolated native route with all ten bodies and no poison');before=cpu(data('phase-0/before/CPU.bin'));after=cpu(data('phase-0/after/CPU.bin'));own_endpoint(before,after,0xfffffff0)
 for side in('before','after'):
  for f,n in(('State.bin',3504),('CPU.bin',40),('FX.bin',512),('stack.bin',4096),('TIB.bin',20)):need(len(data('phase-0/'+side+'/'+f))==n,'Whole own current native endpoint '+f)
 accesses=list(struct.iter_unpack('<IIQII',data('phase-0/after/accesses.bin')));timing=list(struct.iter_unpack('<8I',data('phase-0/after/call-store-timing.bin')))
 for pc,pre,F,ret,ss,size,index,spare in timing:need(not(ss or spare)and F==pre-4 and ret==pc+size and accesses[index]==(pc,F,ret,4,1),'Same actual native CALL pre-store Access/return occurrence')
 need(not data('phase-0/after/frames.bin'),'All source CALL frames closed')
 rows=[]
 for i in range(3):
  p='phase-0/version-api-'+str(i)
  try:w=words(data(p+'-words.bin'),16,'Q')
  except FileNotFoundError:break
  need(w[0:3]==(1,SITES[i],i)and w[4:6]==(RETS[i],ARGC[i]),'Actual native physical source CALL/API/RET chronology');F=w[3];frame=data(p+'-frame.bin');need(len(frame)==64 and struct.unpack_from('<I',frame)[0]==RETS[i],'Whole actual committed native source frame');b=cpu(data(p+'-CPU-before.bin'));a=cpu(data(p+'-CPU-after.bin'));need(b[4]==F and a[4]==F+4*(ARGC[i]+1)and a[9]==RETS[i],'Actual native source stdcall consumption and RET');err=words(data(p+'-last-error.bin'),3,'Q');need(err[0]==err[1]and err[1:]==w[8:10],'Actual native LastError boundary capture/restoration');alias=words(data(p+'-owner-alias.bin'),8,'Q');need(alias[2]<=alias[3]and alias[1]==w[14]and alias[3]==w[15],'Same actual native generation/requested/sourceextent owner');need(i!=2 or not alias[5]or(alias[5]>=alias[4]and alias[6]==alias[5]-alias[4]and alias[6]<alias[2]and alias[7]<=alias[2]-alias[6]),'Whole actual native root-query alias')
  for suffix,n in(('-hardware.bin',1152),('-args.bin',16)):need(len(data(p+suffix))==n,'Whole typed native actual API witness')
  machine=data(p+'-hardware.bin');ha=struct.unpack_from('<4Q',machine,576);need(a[0:3]==tuple(v&0xffffffff for v in ha[:3])and a[8]&0x8d5==ha[3]&0x8d5 and all(a[k]==b[k]for k in(3,5,6,7)),'Actual Win64 return/volatile/arithmetic-flag projection and source nonvolatile preservation')
  identity=words(data(p+'-0-identity.bin'),13,'Q');need(identity[0]>=identity[4]and identity[0]+64<=identity[4]+identity[5]and identity[6:8]==(0x1000,0x1000000)and identity[10]==64 and identity[8]&0xf0 and len(data(p+'-0-entry64.bin'))==64,'Actual native executable named VERSION provider owner and complete entry64')
  for suffix in('-identity.bin','-entry64.bin','-primary-path.bin','-owner-path.bin','-primary-sha.bin','-owner-sha.bin','-file-identity.bin','-file-path.bin','-file-sha.bin','-cwd.bin'):need(data(p+'-0'+suffix)==data(p+'-1'+suffix),'Actual native provider/file identities conserved')
  need(data(p+'-0-file-sha.bin').decode()==IMAGE_SHA,'Same complete native physical game file');rows.append(dict(index=i,words=w,before=b,after=a,alias=alias,frame=frame,path=p))
 need(rows,'Actual source size API executed')
 return dict(before=before,after=after,rows=rows,API_count=len(rows))
def common_caller_validation(original,native,o,n):
 expected=(0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xaabbccdd,0x202,0x4af240);need(o['before']==n['before']==expected,'Both actual complete root BEFORE CPUs equal the single independent common recipe')
 recipe={}
 for key,extent in [('CPU',40),('FX',512),('ENV',28),('stack',4096)]:
  a=original('common-caller/authored-'+key+'.bin');b=native('common-caller/authored-'+key+'.bin');need(len(a)==len(b)==extent and a==b,'Whole identical independently authored caller '+key);recipe[key]=a
 need(cpu(recipe['CPU'])==expected and original('common-caller/header-sha.txt')==native('common-caller/header-sha.txt')==b'bdef49734a96c155a3e6a4e2e0a098bfcdc326746e16276dd219541882895182','Same frozen caller header consumed by both actual fixtures')
 need(words(original('common-caller/application.bin'),8)==(1,1,0x4af240,0x20001800,0x410a80,512,28,4096)and words(native('common-caller/application.bin'),8)==(1,1,0x4af240,0x20001800,0xfffffff0,512,28,4096),'Each own real bootstrap is followed by exactly one authored caller application and its own terminal token')
 OF=o['record'][116:628];NF=native('phase-0/before/FX.bin');need(fx_arch(OF)==fx_arch(NF)==fx_arch(recipe['FX']),'Both actual BEFORE floating-point architectural fields equal the common authored recipe; raw hardware capability/reserved bytes retained')
 OE=o['record'][2164:2192];NE=native('phase-0/before/ENV-from-State.bin');need(OE==NE==recipe['ENV'],'Whole original guest ENV and explicit native persistent-State ENV fields equal the independently authored caller')
 page=PAGES.index(0x20001000);OS=o['record'][2276+page*4096:2276+(page+1)*4096];NS=native('phase-0/before/stack.bin');base=bytearray(recipe['stack']);offset=0x20001800-0x20001000;ob=base[:];nb=base[:];struct.pack_into('<I',ob,offset,0x410a80);struct.pack_into('<I',nb,offset,0xfffffff0);need(OS==ob and NS==nb,'Every whole caller stack byte equals its authored recipe with only the independently witnessed terminal word correspondence')
 need(len(original('common-caller/bootstrap-CPU.bin'))==40 and len(original('common-caller/bootstrap-FX.bin'))==512 and len(original('common-caller/bootstrap-ENV.bin'))==28 and len(original('common-caller/bootstrap-pages.bin'))==176128,'Whole original own real bootstrap BEFORE retained before projection')
 for f,size in [('CPU.bin',40),('FX.bin',512),('State.bin',3504),('stack.bin',4096),('ENV-from-State.bin',28)]:need(len(native('common-caller/bootstrap/'+f))==size,'Whole own native actual bootstrap BEFORE retained')
 return dict(complete_common_CPU_before=True,architectural_FX_before=True,whole_ENV_before=True,whole_stack_before=True,one_application_per_branch=True,terminal_tokens=dict(original=0x410a80,native=0xfffffff0),recipe_header_sha256='bdef49734a96c155a3e6a4e2e0a098bfcdc326746e16276dd219541882895182',native_ENV_role='Typed projection of actual persistent guest State under empty-tag guard; raw State/FX/API hardware retained',source_after_seed=False,per_source_reseed=False,whole_native_ENV_after=delta(o['record'][2192:2220],native('phase-0/after/ENV-from-State.bin')))

def main(original_report,original_sha,native_report,native_sha,admission,admission_sha,name):
 out=R/'reports/m4-version-source'/name;need(not out.exists(),'Fresh strict version comparison');pins={};reader=None;opened=False;closed=False;validation_passed=False;comparisons=[];error=None
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact externally admitted comparison physical input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable reopened comparison physical input');pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 try:
  oe=read(original_report,original_sha);ne=read(native_report,native_sha);gate=read(admission,admission_sha);need(oe['passed']and ne['passed']and oe['all_workers_terminal']and ne['all_workers_terminal'],'Both actual worker branches terminal before strict reader');need(gate['passed']and gate['original_execution_sha256']==original_sha and gate['native_execution_sha256']==native_sha and gate['comparison_tool_sha256']==sha(__file__),'Independent exact capture/tool reader admission')
  need(gate['sole_original_reader_lease']is True and gate['original_input_role']=='single_original8_common_transport'and gate['native_input_role']=='direct_ordinary_closed_native3_common','Explicit independent sole original reader and direct closed-native3 common input roles')
  need(oe['preparation_sha256']=='fafc198f6a20184cf3cc3bec67710e8f22eb7408789568eacefb73c90163d48f'and oe['build_sha256']=='14e3040ee8aa42f014a07d042bf3bab06d3565006b9ce5a2dfb39cf952893b52'and ne['preparation_sha256']=='d42a831e4d123021470ba99bc6589081f90dbf1f3e3bab5664c76356ab630bc6'and ne['build_sha256']=='5cfc72f299317152c64b2d196dc1e6318e69fb89387a98603ba32d56d509372a','Exact isolated original8/native3 common frozen source/candidate roles')
  need(gate['common_caller_recipe_sha256']=='ca7f036b3693ef71bbbe5ce7a0af4ae3cb98755550d1bd1dcd8da955ab311281'and oe['common_caller_recipe_sha256']==ne['common_caller_recipe_sha256']=='ca7f036b3693ef71bbbe5ce7a0af4ae3cb98755550d1bd1dcd8da955ab311281'and oe['role']=='single_original8_common_transport'and ne['role']=='direct_ordinary_closed_native3_common','Explicit matched caller execution/reader roles and complete independent recipe');pin(R/'reports/m4-version-source/common-caller-preparation-r1/report.json','ca7f036b3693ef71bbbe5ce7a0af4ae3cb98755550d1bd1dcd8da955ab311281');
  transport=pin(Path(oe['run']['capture'])/'transport.json',oe['run']['transport_sha256']);metadata=json.loads(transport.read_bytes());need(metadata['logical_files']<=2048 and metadata['payload_bytes']<=256*1024*1024 and len(metadata['parts'])<=8,'Bounded single-root original payload before sole strict reader opens')
  pin(R/'tools/m4-version-source/compare_v1.py','9d7a908af4f983bef68e3e7ec9b545930e6cf9737e83f67181ba33e4bee876ef');pin(R/'tools/m4-version-source/derive_compare_v2.py');pin(R/'tools/m4-version-source/compare_v2.py','385329543daff1416cf45ac9311f98057e8ad2dd9dd8a83f6d3758908b8085eb');pin(R/'tools/m4-version-source/derive_compare_v3.py');pin(R/'tools/m4-version-source/compare_v3.py','2b4f22cf66d0fe3e0f757de56be58b6f272c4240bc0c8f5dc4d39704d2e396c3');pin(R/'tools/m4-version-source/derive_compare_v4.py');pin(R/'tools/m4-version-source/compare_v4.py','85c294f281d96756f2dc5e2319fd32f748da68a3e3d566af5d8f408c129322ea');pin(R/'tools/m4-version-source/prepare_common_controllers_v1.py');pin(__file__);helper=pin(R/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('version_exact_direct',helper);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);reader=m.DirectSet(Path(oe['run']['capture'])/'transport.json',pin);opened=True
  def original(n):return reader.data(n)
  o=original_validation(original);out.mkdir(parents=True)
  for level in('O0','O2'):
   root=Path(ne['runs'][level]['capture']);need(ne['runs'][level]['passed']and root.parent==Path(native_report).resolve().parent and root.name==level,'Exact closed ordinary native3 common optimization-level capture role');manifest_path=pin(ne['runs'][level]['output_manifest'],ne['runs'][level]['output_manifest_sha256']);manifest=json.loads(manifest_path.read_bytes())
   def native(n):
    need(n in manifest and Path(n).suffix.lower()not in('.mwb','.zip'),'Required direct ordinary native witness from exact controller output manifest');p=pin(root/n,manifest[n]['sha256']);b=p.read_bytes();need(len(b)==manifest[n]['bytes'],'Whole native manifest-bound witness extent');return b
   n=native_validation(native);common=common_caller_validation(original,native,o,n);need(o['API_count']==n['API_count'],'Same actual source API branch count');entry=dict(level=level,complete_common_caller=common,original_isolated_provider=o['provider'],caller_before=dict(original=list(o['before']),native=list(n['before'])),caller_after=dict(original=list(o['after']),native=list(n['after'])),raw_CPU_before=delta(o['record'][36:76],native('phase-0/before/CPU.bin')),raw_CPU_after=delta(o['record'][76:116],native('phase-0/after/CPU.bin')),raw_FX_before=delta(o['record'][116:628],native('phase-0/before/FX.bin')),raw_FX_after=delta(o['record'][628:1140],native('phase-0/after/FX.bin')),raw_stack_before=delta(o['record'][2276+PAGES.index(0x20001000)*4096:2276+(PAGES.index(0x20001000)+1)*4096],native('phase-0/before/stack.bin')),raw_stack_after=delta(o['record'][178404+PAGES.index(0x20001000)*4096:178404+(PAGES.index(0x20001000)+1)*4096],native('phase-0/after/stack.bin')),API_correspondences=[])
   hw=native('phase-0/caller-hardware.bin');need(len(hw)==1632,'Whole native caller hardware envelope');need(fx_arch(hw[:512])==fx_arch(hw[1088:1600])and hw[512:540]==hw[1600:1628],'Own restored native caller hardware under the existing field contract');entry['whole_original_ENV_before_hex']=o['record'][2164:2192].hex();entry['whole_original_ENV_after_hex']=o['record'][2192:2220].hex();entry['whole_native_host_ENV_before_hex']=hw[512:540].hex();entry['whole_native_host_ENV_after_hex']=hw[1600:1628].hex();entry['native_guest_ENV_separate_capture']=False;entry['whole_native_source_State_before_sha256']=digest(native('phase-0/before/State.bin'));entry['whole_native_source_State_after_sha256']=digest(native('phase-0/after/State.bin'));entry['native_whole_Game_regions']=[]
   for f in(root/'phase-0'/'before').glob('game-region-*.bin'):
    base=int(f.stem.removeprefix('game-region-'));a=native('phase-0/before/'+f.name);b=native('phase-0/after/'+f.name);need(len(a)==len(b)and all(x==y or 0x60b198<=base+j<0x60b198+60 for j,(x,y)in enumerate(zip(a,b))),'Every complete own native Game region byte changes only within literal60-byte object');entry['native_whole_Game_regions'].append(dict(base=base,bytes=len(a),before_sha256=digest(a),after_sha256=digest(b),only_literal_object_changed=True))
   for i,r in enumerate(n['rows']):
    a=o['rows'][3*i];b=o['rows'][3*i+1];need(b['CPU'][0]==r['after'][0],'Actual same-file API return DWORD');need(original(a['path']+'/file-identity.bin')==native(r['path']+'-0-file-identity.bin'),'Same actual physical file ID/size/timestamp');row=dict(index=i,source_CALL=SITES[i],source_RET=RETS[i],actual_original_API_target=a['identity'][0],actual_native_API_target=words(native(r['path']+'-0-identity.bin'),13,'Q')[0],return_DWORD=b['CPU'][0],original_frame=a['CPU'][4],native_frame=r['words'][3],actual_same_file_SHA=IMAGE_SHA,provider_volatiles='Retained independently under existing actual API field policy; no x86/Win64 hardware coincidence required')
    if i:
     owner=b['owner'];alias=r['alias'];need(owner[3]==alias[2]and owner[4]==alias[3],'Same genuine source requested and HeapAlloc extent; measured HeapSize capacity stays distinct');lease=words(native('phase-0/version-buffer-'+str(i-1)+'-lease.bin'),6,'Q');need(lease[0:5]==(alias[0],alias[1],SITES[i],alias[2],alias[3])and lease[5]==alias[4],'Same actual private native API lease/generation/extent/base');nb=native('phase-0/version-buffer-'+str(i-1)+'-native-before.bin');na=native('phase-0/version-buffer-'+str(i-1)+'-native-after.bin');need(len(nb)==len(na)==alias[3],'Whole actual native source extent before/after');row.update(original_owner=list(owner),native_owner_alias=list(alias),whole_source_extent_after=delta(b['owned'][:owner[4]],na),original_whole_capacity_bytes=len(b['owned']),native_whole_source_extent_bytes=len(na),separate_owner_capacity_not_equated=True)
     # Whole bytes stay in the receipt. Private uninitialized allocation padding
     # is not a cross-branch value promise under the frozen existing field policy.
     row['whole_source_extent_crossbranch_equality_claimed']=False
     if i==2:
      need(b['words'][15]==alias[7]and(not owner[9]or owner[9]-owner[2]==alias[6]),'Actual returned pointer offset and whole alias length correspondence')
      copied=min(b['words'][15],52)if b['CPU'][0]else 0;offset=owner[9]-owner[2]if owner[9]else 0;original_copied=b['owned'][offset:offset+copied];native_copied=na[alias[6]:alias[6]+copied];need(len(original_copied)==len(native_copied)==copied and original_copied==native_copied,'Every actual literal 4AF174 clamp/REP copied source resource byte');row.update(literal_copy_PC=0x4af174,literal_maximum=52,actual_copied_bytes=copied,actual_copied_sha256=digest(original_copied),whole_returned_alias=delta(b['owned'][offset:offset+b['words'][15]],na[alias[6]:alias[6]+alias[7]]))
    entry['API_correspondences'].append(row)
   oi=178404+PAGES.index(0x60b000)*4096+0x198;original_object=o['record'][oi:oi+60]
   regions=[]
   for f in(root/'phase-0'/'after').glob('game-region-*.bin'):
    base=int(f.stem.removeprefix('game-region-'));length=f.stat().st_size
    if base<=0x60b198 and 0x60b198+60<=base+length:regions.append((base,f))
   need(len(regions)==1,'One complete native own game region owns the exact60-byte version object');base,p=regions[0];region=native(str(p.relative_to(root)).replace('\\','/'));native_object=region[0x60b198-base:0x60b198-base+60];need(original_object[:4]==native_object[:4]and original_object[8:]==native_object[8:],'Every actual initialized version size and52-byte inline object field')
   op=struct.unpack_from('<I',original_object,4)[0];np=struct.unpack_from('<I',native_object,4)[0]
   if op or np:
    need(o['allocations']and len(n['rows'])>=2 and op==o['allocations'][-1][2]and np==n['rows'][-1]['alias'][0],'Exact original/native published MFC buffer correspondence from actual captured owner occurrences')
   else:need(op==np==0,'Same actual source null publication')
   entry['complete_object']=dict(original_hex=original_object.hex(),native_hex=native_object.hex(),bytes=60,source_pointer_field=0x60b19c,original_owner_pointer=op,native_owner_guest=np,all_other_bytes_equal=True)
   comparisons.append(entry)
  validation_passed=True
 except BaseException:error=traceback.format_exc()
 finally:
  if reader is not None:reader.close();closed=True
  out.mkdir(parents=True,exist_ok=True)
  if error:(out/'failure.txt').write_text(error)
  d=dict(passed=validation_passed,scope='Strict isolated actual source/API/owner/caller validation and explicit raw endpoint/resource comparison; no carried prefix or initializer credit',comparisons=comparisons,original_execution_sha256=original_sha,native_execution_sha256=native_sha,archive_reader_opened=opened,all_archive_readers_closed=closed or not opened,sole_original_reader=True,original_payload_bound_bytes=256*1024*1024,native_payload_role='direct ordinary manifest-bound native3 common',existing_field_policy=str(R/'tools/m4-next-source/compare_paired_policy_v7.py'),raw_bytes_modified=False,blanket_masks=False,source_original_equivalence=False,common_authored_caller_pair_required_for_endpoint_equivalence=False,matched_common_caller_checked=validation_passed,initializer_credit=0,files=pins,error=error);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=validation_passed,path=str(q),sha256=sha(q),archive_readers_closed=d['all_archive_readers_closed'])));sys.exit(int(not validation_passed))
if __name__=='__main__':main(*sys.argv[1:])
