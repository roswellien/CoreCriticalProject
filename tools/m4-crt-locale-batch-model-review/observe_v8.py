"""Read-only whole-unit original BEFORE/source and finite API observation.

No captured AFTER machine supplies expected registers, flags, stack or pages.
Actual API scalar/output witnesses supply only declared finite transport effects.
Native execution is authenticated from its separate completed worker stage.
"""
import argparse,copy,hashlib,json,re,struct,sys,time,traceback,types,collections
from pathlib import Path
sys.dont_write_bytecode=True
import before_bridge as BB
import batch as B
import interpreter_v2 as I
ROOT=I.ROOT
sys.path.insert(0,str(ROOT/'tools/m4-crt-allocation-model-review'))
from transport import StrictUnion
from exports import PhysicalExports,terminated
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import normalized,unique_object,verify_manifest
from paths import workspace_path,publish_bytes
from stages import verify_stage

def sha(path):
 with Path(path).open('rb') as s:return hashlib.file_digest(s,'sha256').hexdigest()
def read(path):return json.loads(Path(path).read_bytes(),object_pairs_hook=unique_object)
def numbers(raw,width=4):
 I.need(len(raw)%width==0,'Complete typed binary scalar array')
 return struct.unpack('<'+str(len(raw)//width)+('I' if width==4 else 'Q'),raw)
def records(raw,fmt):
 size=struct.calcsize('<'+fmt);I.need(len(raw)%size==0,'Complete typed binary record array')
 return [struct.unpack_from('<'+fmt,raw,n) for n in range(0,len(raw),size)]
def scalar_bytes(rows,fmt):return b''.join(struct.pack('<'+fmt,*v) for v in rows)

class APIs:
 """Physical requested DLL export and owner alias, independent of native helper."""
 def __init__(self,add,eq):self.add=add;self.eq=eq;self.pe=PhysicalExports(add);self.evidence=[]
 def identity(self,reader,stem,name):
  a=reader.read_bytes(stem+'-before.bin');z=reader.read_bytes(stem+'-after.bin');self.eq(z,a,'Actual API stable full-width identity '+name)
  v=numbers(a,8);I.need(len(v)==11,'Full 11Q native API identity')
  target,named,owner,alias,base,size,allocation,state,typ,protect,allocation_protect=v
  I.need(target==named==alias and owner==allocation and owner and allocation<=base<=target<base+size<=2**64 and state==0x1000 and typ==0x1000000 and protect&0xf0 and not protect&0x101,'Actual committed executable physical API owner')
  suffix='.bin' if name=='GetCommandLineA' else ''
  p=reader.read_bytes(stem+'-before'+suffix+'-module-path.bin');h=reader.read_bytes(stem+'-before'+suffix+'-module-sha.bin')
  self.eq(reader.read_bytes(stem+'-after'+suffix+'-module-path.bin'),p,'API physical module path stable');self.eq(reader.read_bytes(stem+'-after'+suffix+'-module-sha.bin'),h,'API physical module digest stable')
  I.need(len(h)==64,'Physical API module SHA256 extent');path=Path(p.decode('utf-16-le'));digest=h.decode('ascii')
  self.add(path,digest);return v,path,digest
 def proof(self,reader,stem,name,identity_stem=None):
  v,path,digest=self.identity(reader,identity_stem or stem+'-identity',name)
  raw=reader.read_bytes(stem+'-export-before.bin');self.eq(reader.read_bytes(stem+'-export-after.bin'),raw,'Physical requested export proof stable '+name)
  I.need(len(raw)==4624,'Complete physical requested/owner export proof')
  version,namedbase,target,namedresolved,owner,ownerresolved=numbers(raw[:48],8)
  requested=terminated(raw[48:80]);forwarder=terminated(raw[80:336]);alias=terminated(raw[336:400]);namedsha=raw[400:464].decode('ascii');ownersha=raw[464:528].decode('ascii')
  namedpath=Path(terminated(raw[528:2576],'utf-16-le'));ownerpath=Path(terminated(raw[2576:4624],'utf-16-le'))
  I.need(version==1 and requested==name and namedbase and target==namedresolved==ownerresolved==v[0] and owner==v[2] and namedpath.name.casefold()=='kernel32.dll' and ownerpath==path and ownersha==digest,'Requested Kernel32 export binds same full physical owner and target')
  nr,nf,ns=self.pe.get(namedpath,namedsha,name);r,f,s=self.pe.get(ownerpath,ownersha,alias)
  I.need(nf==forwarder and not f and owner+r==target and owner<=target<owner+s<=2**64 and namedbase+ns<=2**64,'Independent requested forwarder and direct physical owner alias/RVA')
  if forwarder:
   module,dot,export=forwarder.rpartition('.')
   I.need(dot and export==alias and ownerpath.stem.casefold()==module.casefold(),'Exact finite physical named forwarding module/alias')
  else:I.need(alias==name and owner==namedbase and namedpath==ownerpath and namedsha==ownersha and target==namedbase+nr,'Exact direct requested native export')
  item=dict(name=name,target=target,owner=owner,requested_path=str(namedpath),requested_sha256=namedsha,owner_path=str(ownerpath),owner_sha256=ownersha,forwarder=forwarder,owner_export=alias,owner_RVA=r)
  if item not in self.evidence:self.evidence.append(item)
  return item
 def commandline(self,reader,stem):
  v,path,digest=self.identity(reader,stem+'/commandline-api','GetCommandLineA')
  r,f,s=self.pe.get(path,digest,'GetCommandLineA');I.need(not f and v[2]+r==v[0] and v[0]<v[2]+s,'Independent command-line named direct owner export')

def api_facts(reader,stem,APIs):
 summary=numbers(reader.read_bytes(stem+'/locale-summary.bin'));I.need(len(summary)==32,'Private-derived 32DWORD unit summary')
 facts=[]
 for n in range(summary[18]):
  p=stem+'/locale-api-'+str(n);w=numbers(reader.read_bytes(p+'-witness.bin'),8);I.need(len(w)==32 and w[0]==1 and w[1]==n,'Complete indexed actual API witness')
  inputs=[];outputs=[];k=0
  while reader.exists(p+'-input-'+str(k)+'.bin'):inputs.append(reader.read_bytes(p+'-input-'+str(k)+'.bin'));k+=1
  k=0
  while reader.exists(p+'-output-'+str(k)+'.bin'):outputs.append(reader.read_bytes(p+'-output-'+str(k)+'.bin'));k+=1
  buffers=records(reader.read_bytes(p+'-buffers.bin'),'4I')
  if w[31]:name='HeapFree' if w[3]==0x7802e090 else 'LeaveCriticalSection' if w[3]==0x7802e048 else 'DeleteCriticalSection'
  else:
   I.need(w[2] in B.contracts(),'Recovered source API site');name=B.contracts()[w[2]]['name']
  APIs.proof(reader,p,name)
  prefix=p.rsplit('/',1)[1]
  captures={logical.rsplit('/',1)[1][len(prefix):]:reader.read_bytes(logical) for logical in reader.names() if logical.startswith(p+'-') and '/' not in logical[len(p)+1:]}
  facts.append(dict(words=w,buffers=buffers,inputs=inputs,outputs=outputs,name=name,captures=captures))
 return facts

def machine_fields(s,pages,consumer):
 if 'memory' in s:
  state=s['state'];fx=s['fx'];cpu=s['cpu'];memory=s['memory'];f={'page-'+str(p)+'.bin':bytes(memory[p]) for p in pages}
 else:
  state=s['state.bin'];fx=s['fx.bin'];cpu=s['runtime-cpu.bin'];f={name:s[name] for name in ('page-'+str(p)+'.bin' for p in pages)}
 f.update({'state.bin':state,'fx.bin':fx,'runtime-cpu.bin':cpu,'state-cpu.bin':consumer.M.D.cpu(state)})
 fs=struct.unpack_from('<I',state,I.BASE['fs'])[0]
 if 'memory' in s:chain=int.from_bytes(B.OwnedMachine(state,fx,cpu,memory).bytes(fs,4),'little')
 else:chain=int.from_bytes(s['tib-0.bin'],'little')
 f['tib.bin']=struct.pack('<5I',fs,chain,0x20002000,0x20001000,fs)
 f['pages-index.bin']=struct.pack('<'+str(len(pages))+'I',*pages);f['page-addresses.bin']=struct.pack('<Q',len(pages))
 return f

def fixed_rows(raw,expected,fmt,eq,why):
 decoded=records(raw,fmt);I.need(len(expected)<=len(decoded),'Bounded fixed typed ledger')
 zero=tuple(0 for _ in decoded[0]) if decoded else ()
 eq(decoded,list(expected)+[zero]*(len(decoded)-len(expected)),why)

def new_metadata(reader,stem,phase,stage,result,eq,handle):
 accesses=result['accesses'];n=stage['source_accesses']
 if phase in ('allocation-caller-before','allocation-caller-after'):n=0
 # The separate source command-line writer is appended to the batch ledger
 # only at its explicit admission. Its effects are already modeled earlier.
 if phase.startswith('commandline-'):n=result['phases']['locale-commandline-suspended']['source_accesses']
 eq(reader.read_bytes(stem+'/locale-source-accesses.bin'),scalar_bytes(accesses[:n],'IIQII'),'Exact independent ordered byte/WORD/DWORD/REP source accesses '+phase)
 eq(reader.read_bytes(stem+'/locale-api-transports.bin'),scalar_bytes(result['transports'][:stage['transports']],'IIQII'),'Exact independent finite API transport ledger '+phase)
 eq(reader.read_bytes(stem+'/locale-research-accesses.bin'),scalar_bytes(result['external_accesses'][:stage['external_accesses']],'IIQII'),'Separate explicit research frame stores '+phase)
 eq(reader.read_bytes(stem+'/locale-research-projections.bin'),scalar_bytes(result['projections'][:stage['projections']],'8I'),'Separate explicit scheduling effects '+phase)
 raw_targets={c['raw'] for c in B.contracts().values()};frames=[x for x in stage['call_stack'] if x[0] not in raw_targets]
 if phase in ('locale-parser-sizing-before','locale-parser-output-before'):I.need(frames[-1][0]==0x7800bc48,'Authentic parser-before call contract');frames=frames[:-1]
 eq(reader.read_bytes(stem+'/locale-call-frames.bin'),scalar_bytes(frames,'9I'),'Independent complete source caller/probe frames '+phase)
 fixed_rows(reader.read_bytes(stem+'/heap-api-accesses.bin'),result['API_reads'][:stage['API_reads']],'5I',eq,'All separate authentic stdcall return reads '+phase)
 fixed_rows(reader.read_bytes(stem+'/heap-undefined-sites.bin'),[(pc,) for pc,_,_ in result['undefined'][:stage['undefined']]],'I',eq,'Actual generated callbacks with exact source multiplicity '+phase)
 sections=stage['sections'];actual=records(reader.read_bytes(stem+'/locale-critical-sections.bin'),'16Q')
 expected=[]
 for guest,s in sections.items():expected.append((1,guest,s['generation'],s['enters'],s['leaves'],s['depth'],int(s['initialized']),s['deletes'],int(s['initialized']),int(bool(s['deletes'])),s['native'],40,0,0,0,0))
 eq(actual,expected,'Full opaque native CS generation/acquisition/release metadata '+phase)
 actual=records(reader.read_bytes(stem+'/locale-allocations.bin'),'16Q');expected=[]
 for a in stage['allocations']:
  guest=a['guest'];mapped=guest in stage['memory'];sourcefreed=not a['live'];request=24 if a['generation']==5 else result['sizing_chars']+4*result['sizing_slots'];kind=1 if a['generation']==5 else 2
  expected.append((1,guest,request,a['extent'],a['mapped'],a['generation'],kind,a['native'],a['native'] if a['live'] else 0,int(mapped),int(sourcefreed),0,handle,0,0,0))
  prefix=stem+'/locale-allocation-'+str(a['generation'])
  eq(reader.read_bytes(prefix+'-initial.bin'),a['initial'],'Immutable actual native initial allocation bytes '+phase)
  if mapped:
   current=bytes(stage['memory'][guest]);eq(reader.read_bytes(prefix+'-expected.bin'),current,'Source-derived complete private allocation mirror '+phase);eq(reader.read_bytes(prefix+'-owned-page.bin'),current,'Source-derived complete actual allocation page '+phase)
  else:
   I.need(not reader.exists(prefix+'-owned-page.bin'),'No claimed owned page before admission or after release')
   if a['live']:eq(reader.read_bytes(prefix+'-expected.bin'),a['initial']+bytes(a['mapped']-a['extent']),'Prepublication allocation expected backing '+phase)
 eq(actual,expected,'Full native/guest allocation generation, requested/rounded extent and ownership '+phase)
 summary=numbers(reader.read_bytes(stem+'/locale-summary.bin'))
 eq(summary[16:18],(n,stage['transports']),'Private actual source/transport counts '+phase)
 eq(summary[19:22],(len(frames),stage['external_accesses'],stage['projections']),'Private source frames/research seam counts '+phase)
 eq(summary[18],stage['api_count'],'Private actual source API count '+phase)
 for index in range(stage['api_count']):
  fact=result['responses'].facts[index];expected=dict(fact['captures']);w=list(fact['words'])
  tag='locale-api-'+str(index)
  if phase.startswith(tag+'-'):
   where=phase[len(tag)+1:]
   if where=='before':
    for key in (8,10,11,12,13,14,15,18):w[key]=0
    for key in list(expected):
     if key.startswith('-output-'):del expected[key]
    expected['-export-after.bin']=bytes(4624);expected['-identity-after.bin']=bytes(88)
    expected['-identity-after-module-path.bin']=b'';expected['-identity-after-module-sha.bin']=b''
   elif where=='after':
    w[15]=0
    if fact['name']=='HeapAlloc':w[12]=w[13]=0
    elif 'CriticalSection' not in fact['name'] and fact['name']!='HeapFree':w[13]=0
   elif where=='output-after':w[15]=0
   elif where!='returned':raise ValueError('Unadmitted API capture phase')
  expected['-witness.bin']=struct.pack('<32Q',*w)
  for suffix,value in expected.items():eq(reader.read_bytes(stem+'/'+tag+suffix),value,'Complete independent API witness/immutable scratch history '+phase+'/'+tag+suffix)
  actual_names={n.rsplit('/',1)[1][len(tag):] for n in reader.names() if n.startswith(stem+'/'+tag+'-') and '/' not in n[len(stem+'/'+tag)+1:]}
  eq(actual_names,set(expected),'Exact API phase payload/identity inventory '+phase+'/'+tag)
 eq(summary[29],int.from_bytes(B.OwnedMachine(stage['state'],stage['fx'],stage['cpu'],stage['memory']).bytes(struct.unpack_from('<I',stage['state'],I.BASE['fs'])[0],4),'little'),'Private FS chain agrees with independently modeled source '+phase)
 return len(expected)

def validate_cleanup(reader,row,allfacts,result,eq,handle):
 sourcecount=result['responses'].index;later=allfacts[sourcecount:]
 subjects=[s['native'] for s in reversed(list(result['responses'].sections.values()))]
 expected=[('DeleteCriticalSection',0x7802e040,0x3446a,p) for p in subjects]
 expected += [('HeapFree',0x7802e090,0x345ba,a['native']) for a in reversed(result['responses'].allocations) if a['live']]
 eq(len(later),len(expected),'Exact cleanup API inventory, separate from source calls')
 for fact,(name,slot,raw,subject) in zip(later,expected):
  w=fact['words'];eq(fact['name'],name,'Dependency-order real cleanup API name');eq((w[2],w[3],w[4],*w[5:8],w[16],w[31]),(0,slot,raw,0,0,0,subject,1),'Host-only cleanup identity, subject and zero guest frame')
  I.need(w[8]==w[14]==w[15]==1 and w[9]==w[11] and w[9]<=0xffffffff and w[10]<=0xffffffff,'Actual successful cleanup/restored error');eq((fact['inputs'],fact['outputs'],fact['buffers']),([],[],[]),'Cleanup has no invented guest scratch transport')
 after=result['phases']['locale-builder-returned'];clean=copy.deepcopy(after)
 for a in result['responses'].allocations:clean['memory'].pop(a['guest'],None)
 for phase in ('locale-batch-cleaned','final'):
  stem=row+'/'+phase
  allocations=records(reader.read_bytes(stem+'/locale-allocations.bin'),'16Q')
  for actual,a in zip(allocations,result['responses'].allocations):
   I.need(actual[8]==actual[9]==actual[10]==0 and actual[11]==1 and actual[7]==a['native'] and actual[12]==handle,'Real same private full allocation cleanup and revoked guest page')
   prefix=stem+'/locale-allocation-'+str(a['generation']);I.need(not reader.exists(prefix+'-owned-page.bin'),'No post-release owned allocation capture');eq(reader.read_bytes(prefix+'-expected.bin'),bytes(after['memory'][a['guest']]),'Historical source-derived backing retained after revocation')
  sections=records(reader.read_bytes(stem+'/locale-critical-sections.bin'),'16Q')
  for a,s in zip(sections,result['responses'].sections.values()):I.need(a[5]==0 and a[6:10]==(1,1,1,1) and a[10]==s['native'],'Actual same CS deleted once after genuine leave')
  summary=numbers(reader.read_bytes(stem+'/locale-summary.bin'));eq(summary[14:16],(0,0),'All allocation/CS ownership released');I.need(summary[23]==1 and summary[30]==summary[31]==0,'Finished research batch and no heap/fault ownership')
  registry=numbers(reader.read_bytes(stem+'/heap-create-registry.bin'),8);I.need(registry[7]==0 and registry[8:11]==(1,1,1) and registry[15]==1 and registry[16]==handle,'Same real initialized heap destroyed after all dependents')
 return clean

def main(args):
 t=time.perf_counter();out=workspace_path(ROOT/'reports/m4-crt-locale-batch-model-review'/args.name,reports=True)
 I.need(re.fullmatch('(?:observe|development)-r[1-9][0-9]*',args.name) and not out.exists(),'Fresh independent observation revision');out.mkdir(parents=True)
 files={};checks=0;rows=[];passed=False
 def add(path,digest=None):
  p=Path(path).absolute();h=sha(p);I.need(digest is None or h==digest,'Exact physical current source dependency '+str(p));key=normalized(str(p));I.need(key not in files or files[key]==h,'Consistent immutable physical source');files[key]=h;return p
 def eq(actual,expected,why):
  nonlocal checks;checks+=1
  if actual!=expected:
   if isinstance(actual,bytes) and isinstance(expected,bytes):why+=' byte '+str(next((i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b),min(len(actual),len(expected))))+' lengths '+str((len(actual),len(expected)))
   raise ValueError(why+' actual='+str(actual)[:500]+' expected='+str(expected)[:500])
 try:
  ep=add(args.execution,args.execution_sha);execution=read(ep);I.need(execution['passed'] and execution['schema']=='mw34-m4-locale-batch-native-execution-v1' and not execution['State_reseed_after_writer'] and not execution['actual_API_results_injected'],'Completed genuine current native execution')
  build=read(add(execution['build_path'],execution['build_sha256']));I.need(build['passed'],'Pinned successful current compiled worker build')
  add(__file__)
  for name in ('batch.py','before_bridge.py','interpreter_v2.py'):add(Path(__file__).parent/name)
  add(sys.executable);add(ROOT/'tools/m4-crt-allocation-model-review/transport.py');add(ROOT/'tools/m4-crt-allocation-model-review/exports.py')
  for path,h in ((ROOT/'reports/m4-crt-locale-batch-recovery/recovery-r2/report.json','2d1c4a3f41505358df0ba8aaf4ed31c4b90a08d18b8bdf5cf1ed3eed2d996170'),(ROOT/'reports/m4-crt-locale-batch-recovery/interface-r1/instruction-contracts.json','194e2ca814869c500fd2948d9cc801d3ad7a8aef2367166379a5d0ad87e5a624'),(ROOT/'reports/m4-crt-locale-batch-recovery/callbacks-union-r1/callbacks.json','ce770b98b2dc1f25fa759b2ffa287d3870f367852a5ac406e86bf50e21774c1a')):add(path,h)
  APIs_checker=APIs(add,eq);(out/'source-material').mkdir();before=BB.Before(out/'source-material',add)
  for level,receipt in execution['levels'].items():
   I.need(level in ('O0','O2') and receipt['passed'],'Actual optimization-level receipt')
   worker=add(build['workers'][level]);sp=add(receipt['stage_path'],receipt['stage_sha256']);verify_stage(sp.parent,receipt['stage_sha256']);stage=read(sp)
   I.need(stage['argv'][0].casefold()==str(worker).casefold(),'Actual stage invokes current owning worker')
   manifest=add(receipt['transport_path'],receipt['transport_sha256']);artifacts={normalized(p):h for p,h in stage['artifact_sha256'].items()};I.need(artifacts=={normalized(str(manifest)):receipt['transport_sha256']},'Completed native stage owns exact strict transport publication')
   with StrictUnion(manifest,receipt['transport_sha256'],add) as reader:
    eq(reader.read_bytes('COMPLETE'),b'COMPLETE','Actual semantic completion marker');I.need(not reader.exists('INCOMPLETE'),'No incomplete native admission')
    for index in range(6):
     row='row-'+str(index);end=row+'/locale-builder-returned';result_record=json.loads(reader.read_bytes(row+'/result.json'),object_pairs_hook=unique_object)
     I.need(result_record['passed'] and result_record['control']==0 and result_record['builder_returned'] and not result_record['State_reseed_after_writer'] and not result_record['full_CRT'],'Actual whole-unit row scope')
     pages=numbers(reader.read_bytes(end+'/pages-index.bin'));I.need(len(pages)==len(set(pages)) and list(pages)==sorted(pages),'Unique full captured original/declared page domain')
     hw=numbers(reader.read_bytes(end+'/heap-create-witness.bin'),8);hr=numbers(reader.read_bytes(end+'/heap-create-registry.bin'),8);q=numbers(reader.read_bytes(end+'/heap-query-witness.bin'),8)
     I.need(hw[:6]==(1,0,1,0,4096,0) and hw[6]!=0 and hw[7]==0x48450001 and hr[4]==hw[6] and hr[7]==1,'Real unchanged initialized live private heap and opaque guest token')
     qi=reader.read_bytes(end+'/heap-query-input.bin');qo=reader.read_bytes(end+'/heap-query-output.bin');I.need(q[:3]==(1,1,1) and q[3]!=0 and len(qi)==len(qo)==148 and int.from_bytes(qi[:4],'little')==148,'Actual noninjected complete finite version response')
     _,major,minor,versionbuild,platform=struct.unpack_from('<5I',qo);I.need(platform==2 and major>=5,'Actual finite query output qualifies source mode1')
     allfacts=api_facts(reader,row+'/final',APIs_checker);facts=[x for x in allfacts if not x['words'][31]]
     commandline=reader.read_bytes(end+'/commandline-host-bytes.bin');host=numbers(reader.read_bytes(end+'/commandline-host-witness.bin'),8);I.need(len(host)==3 and host[0]!=0 and host[1]==len(commandline) and host[2]>0,'Actual full borrowed command-line pointer and complete owned copy')
     eq(reader.read_bytes(end+'/commandline-owned.bin'),commandline,'Immutable actual owned command-line bytes');APIs_checker.commandline(reader,end)
     logical=before.consumer.F.LogicalPath(reader,row);initial,earlier,extras=before.row(logical,index,level,dict(input=qi,output=qo,result=q[3]),pages)
     predicted=B.predict(initial,facts,commandline,extras)
     predicted['sizing_chars']=int.from_bytes(predicted['phases']['locale-parser-sizing-returned']['memory'][0x20001000][0x84c:0x850],'little')
     predicted['sizing_slots']=int.from_bytes(predicted['phases']['locale-parser-sizing-returned']['memory'][0x20001000][0x850:0x854],'little')
     models={**earlier,**initial['phases'],**predicted['phases']};models['entry-after-stop']=predicted['phases']['locale-builder-returned']
     cleaned=validate_cleanup(reader,row,allfacts,predicted,eq,hw[6]);models['locale-batch-cleaned']=cleaned;models['final']=cleaned
     observed={name.split('/')[1] for name in reader.names() if name.startswith(row+'/') and name.endswith('/state.bin')}
     unmatched=observed-set(models)
     I.need(not unmatched,'Every complete observed phase has independent source expectation '+str(sorted(unmatched)))
     whole=0;new=0
     for phase in sorted(observed):
      stem=row+'/'+phase;s=models[phase]
      for name,expected in machine_fields(s,pages,before.consumer).items():eq(reader.read_bytes(stem+'/'+name),expected,'Full original BEFORE/source-derived machine '+level+'/'+row+'/'+phase+'/'+name)
      whole+=1
      if phase in predicted['phases']:
       new_metadata(reader,stem,phase,s,predicted,eq,hw[6]);new+=1
     eq(result_record['argc'],predicted['argc'],'Independent published argc');eq(result_record['argv'],predicted['argv'],'Independent published argv')
     summary=numbers(reader.read_bytes(end+'/locale-summary.bin'));eq(summary[3:7],(1,1,2,1),'Whole source static/default/parser/builder success predicates')
     eq(summary[7:9],(predicted['argc'],predicted['argv']),'Private source publication count/pointer');eq(summary[26:28],(predicted['sizing_chars'],predicted['sizing_slots']),'Independent sizing output counters')
     rows.append(dict(level=level,index=index,whole_machine_phases=whole,new_source_phases=new,pages=len(pages),interpreted_new_source_PCs=len(predicted['PCs']),chained_source_accesses=len(predicted['accesses']),source_API_calls=len(facts),source_API_name_counts=dict(collections.Counter(f['name'] for f in facts)),cleanup_API_calls=len(allfacts)-len(facts),actual_API_return_reads=len(predicted['API_reads']),source_CALLs=len(predicted['calls']),source_RETs=len(predicted['returns']),generated_callbacks=len(predicted['undefined']),argc=predicted['argc'],argv=predicted['argv'],argv_strings=[x.decode('latin1') for x in predicted['argv_strings']],source_input_SHA256=hashlib.sha256(commandline).hexdigest(),query_major=major,query_minor=minor,query_build=versionbuild,API_mode_predicate_measured=True))
  # Only source modules reached through the frozen original BEFORE interpreter
  # and their exact static inputs are retained. This does not expand old native
  # captures or accept historical worker closures.
  pending=[before.consumer,before.before,before.prefix];visited=set()
  while pending:
   module=pending.pop()
   if id(module) in visited:continue
   visited.add(id(module));path=getattr(module,'__file__',None)
   if not path or not Path(path).absolute().is_relative_to(ROOT/'tools'):continue
   add(path)
   for field in ('PINS','PHYSICAL'):
    for path,h in getattr(module,field,{}).items():
     if isinstance(path,str) and re.fullmatch('[0-9a-f]{64}',str(h)):add(path,h)
   pending.extend(v for v in vars(module).values() if isinstance(v,types.ModuleType))
  for p in (out/'source-material').iterdir():
   if p.is_file():add(p)
  I.need(len(rows)==12 and {r['level'] for r in rows}=={'O0','O2'},'All twelve ordinary complete native cases observed')
  passed=True
 except Exception:
  publish_bytes(out/'failure.txt',traceback.format_exc().encode());raise
 finally:
  report=dict(schema='mw34-m4-locale-batch-source-observer-v1',passed=passed,execution_path=str(Path(args.execution).absolute()),execution_sha256=args.execution_sha,ordinary_cases=len(rows),checks=checks,rows=rows,files=files,physical_closure=verify_manifest(files),native_executed_by_observer=False,API_executed_by_observer=False,AFTER_machine_seed=False,author_expected_machine_used=False,static_helper_RET_proved=passed,default_locale_RET_proved=passed,both_parser_passes_proved=passed,argv_builder_RET_proved=passed,mainargs_export_RET_proved=False,full_CRT=False,whole_M4_complete=False,original_API_internals_equivalent=False,original_stack_growth_proved=False,declared_lower_stack_only=True,seconds=time.perf_counter()-t)
  publish_bytes(out/'report.json',(json.dumps(report,sort_keys=True,indent=2)+'\n').encode());files[normalized(str(out/'report.json'))]=sha(out/'report.json');publish_bytes(out/'pins.json',(json.dumps(dict(schema='mw34-m4-locale-batch-source-observer-pins-v1',files=files),sort_keys=True,indent=2)+'\n').encode());print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'),cases=len(rows),checks=checks,seconds=report['seconds'])))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--execution',required=True);p.add_argument('--execution-sha',required=True);p.add_argument('--name',required=True);main(p.parse_args())
