"""Independent physical/source/compiled closure, with direct host-boundary finding.

No author comparator, fixture, model or executor import. This is a frozen
historical review of r5, not acceptance of its claimed host-preservation scope.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,ntpath,re,struct,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-fp-numeric-max-integration'
OUT=BASE/'independent-session-closure-r4'
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
NINJA=Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe')
PINS={};COMMANDS=[];CHECKS=[]
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();key=str(p)
 if key in PINS:need(h is None or h==PINS[key],'Conflicting file version '+key);return p
 v=sha(p);need(h is None or h==v,'Physical version '+key);PINS[key]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def text(p,h=None):return pin(p,h).read_text(encoding='utf-8-sig')
def canon(p):return ntpath.normcase(ntpath.normpath(str(p)))
def filemap(p,h=None,replacements=None):
 m=read(p,h);replacements=replacements or {};changed=[]
 for path,v in m['files'].items():
  digest=v['sha256'] if isinstance(v,dict) else v;target=replacements.get(canon(path),path);pin(target,digest)
  if canon(target)!=canon(path):changed.append(dict(manifest=str(p),original_path=path,preserved_path=str(target),sha256=digest))
 return len(m['files']),changed
def check(name,**facts):CHECKS.append(dict(name=name,passed=True,**facts))
def run(argv,name):
 argv=list(map(str,argv));pin(argv[0]);r=subprocess.run(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60);p=OUT/name;p.write_bytes(r.stdout);pin(p);COMMANDS.append(dict(command=argv,exit_code=r.returncode,log=str(p),sha256=sha(p)));need(r.returncode==0,'Actual review step '+name);return r.stdout.decode(errors='replace')
def association_values(node,path):
 values=[]
 if isinstance(node,dict):
  for k,v in node.items():
   if canon(k)==canon(path):values.append(v.get('sha256') if isinstance(v,dict) else v)
  if canon(node.get('original_path',''))==canon(path):
   for k in ('sha256','expected_sha256'):values.append(node.get(k))
  for v in node.values():values+=association_values(v,path)
 elif isinstance(node,list):
  for v in node:values+=association_values(v,path)
 return values
def author_closure():
 a=read(BASE/'author-review-r1/report.json','e17867b6a788e02522cb65fbe1abab9a8dbea24e08e418bee72614b5b8ef31c3')
 n,_=filemap(BASE/'author-review-r1/pins.json','da6c70883e0d4565b5acd9993a170eeadfabe3d9ec98a6e4e9fb44e9cdc9bb90');need(n==3836,'Full physical author map extent')
 maps={};report_sibling_links=[]
 for x in a['literal_source_associations']:
  m=maps.setdefault(x['manifest'],read(x['manifest']))
  if x['expected_sha256'] not in association_values(m,x['original_path']):
   sibling=Path(x['manifest']).parent/'pins.json';s=read(sibling)
   need(x['expected_sha256'] in association_values(s,x['original_path']) or x['expected_sha256'] in association_values(s,x['preserved_path']),'Bare report uses exact sibling physical source map');report_sibling_links.append(dict(report=x['manifest'],source_map=str(sibling),original_path=x['original_path'],sha256=x['expected_sha256']))
  pin(x['preserved_path'],x['expected_sha256'])
 for x in a['historical_source_resolutions']:
  m=maps.setdefault(x['manifest'],read(x['manifest']));need(x['expected_sha256'] in association_values(m,x['original_path']),'Historical source associated with exact older map');pin(x['resolved_path'],x['expected_sha256'])
 for x in a['literal_sources']:pin(x['original_path'],x['sha256']);pin(x['preserved_path'],x['sha256'])
 need(len(a['literal_source_associations'])==213 and len(a['historical_source_resolutions'])==16,'All author source associations/history retained')
 b=read(BASE/'native-build-r5/build.json','ad8c4b5f2e869da3fe664dc835ef59e529a156e95e3917da3ea170aab092a9cc');need(b['passed'],'Exact final built candidate')
 for group in ('source_files','tools','artifacts'):
  for p,h in b[group].items():pin(p,h)
 for x in b['literal_sources']:pin(x['preserved_path'],x['sha256']);need(b['source_files'][x['original_path']]==x['sha256'],'Before-build source literal relationship')
 for lev in ('O0','O2'):
  log=text(BASE/f'native-build-r5/build-{lev}.log');actual=[canon(p.strip()) for p in re.findall(r'^\s*Note: including file:\s*(.+)$',log,re.M)];recorded=[canon(x['path']) for x in a['compiled_headers'] if x['level']==lev]
  need(collections.Counter(actual)==collections.Counter(recorded),'All repeated actual compiler-read header associations')
  lines=[s for s in log.splitlines() if 'clang-cl.exe' in s and ' -c -- ' in s];need(len(lines)==4 and all('/EHs ' in s and '/EHsc' not in s for s in lines),'Actual synchronous typed exception compiler flags')
 for x in a['compiled_headers']:pin(x['path'],x['sha256'])
 for p in a['prerequisites']:pin(p['report'],p['report_sha256']);pin(p['pins'],p['pins_sha256'])
 need(a['compiled_header_reads']==3296,'Header-read extent')
 check('All author/current build/source/history and actual compiler include-log associations',author_physical_bindings=n,literal_source_associations=213,bare_report_associations_resolved_through_sibling_pins=report_sibling_links,historical_source_resolutions=16,actual_compiler_header_reads=3296,current_source_files=len(b['source_files']),current_tools=len(b['tools']),current_artifacts=len(b['artifacts']),identity_scope='Post-build disk hashes and recorded command/include associations; no complete process-time dependency attestation')
 return a,b
def original_and_source():
 path=pin(ROOT/'tools/analysis/pe.py','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638');spec=importlib.util.spec_from_file_location('readonly_exact_pe',path);pe=importlib.util.module_from_spec(spec);spec.loader.exec_module(pe)
 gp=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');dp=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a');gb=gp.read_bytes();db=dp.read_bytes();game=pe.PEImage(gb);dll=pe.PEImage(db)
 owner=[(d['library'],i) for d in game.imports() for i in d['symbols'] if game.image_base+i['iat_rva']==0x5bb4fc]
 need(len(owner)==1 and owner[0][0].lower()=='msvcp50.dll' and owner[0][1]['name']=='?max@?$numeric_limits@M@std@@SAMXZ','Unique actual game named provider owner')
 export=[x for x in dll.exports() if '?max@?$numeric_limits@M@std@@SAMXZ' in x['names']];need(len(export)==1 and export[0]['ordinal']==1545 and dll.image_base+export[0]['rva']==0x780c10f0 and 'forwarder' not in export[0],'Actual named leaf export')
 spans=[]
 for image,raw,address,length,digest,role in ((game,gb,0x4c19f0,10,'1147d8ad778df578820c4be4a4719d35cc4a4c39e0d74043bfdbc57909a261cc','RX root'),(game,gb,0x4c1a00,117,'642aa130e093e1dc8e691b492ae650831cb9f60cf2428d2448e6c0a61fe1e3c5','RX body'),(dll,db,0x780c10f0,7,'31d3ed84e61450051bfba7bc7265523bc3e687f3c7e1a1cb237ec08494ec3d1d','RX leaf')):
  rva=address-image.image_base;off=image.rva_range(rva,length)[0];body=raw[off:off+length];need(hashlib.sha256(body).hexdigest()==digest,'Independent complete private source extent/hash')
  sec=[s for s in image.sections if s['virtual_address']<=rva and rva+length<=s['virtual_address']+s['raw_size']];need(len(sec)==1 and sec[0]['readable'] and sec[0]['executable'] and not sec[0]['writable'],'Actual source RX owner')
  decoded=run([LLVM/'llvm-objdump.exe','--disassemble',f'--start-address={hex(address)}',f'--stop-address={hex(address+length)}','--x86-asm-syntax=intel',gp if image is game else dp],f'source-{address:x}.txt');instructions=[]
  for line in decoded.splitlines():
   m=re.match(r'^\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)$',line)
   if m:
    pc=int(m[1],16);b=bytes.fromhex(m[2]);need(body[pc-address:pc-address+len(b)]==b,'Decode emitted bytes agree with private source');instructions.append(dict(pc=pc,length=len(b),mnemonic=m[3],operand=m[4].strip()))
  need(sum(i['length'] for i in instructions)==length,'Entire source decoded without lexical gap');spans.append(dict(address=address,bytes=length,sha256=digest,section=sec[0]['name'],instructions=instructions))
 raw=game.rva_u32(0x5bb4fc-game.image_base);need(raw==1963420,'Raw named-owning IAT exact retained value')
 need(dll.rva_u32(0x78115004-dll.image_base)==0x7f7fffff,'Actual provider RO binary32 max data')
 ds=[s for s in dll.sections if s['virtual_address']<=0x78115004-dll.image_base and 0x78115008-dll.image_base<=s['virtual_address']+s['raw_size']];need(len(ds)==1 and ds[0]['readable'] and not ds[0]['writable'] and not ds[0]['executable'],'Exact provider RO data owner')
 session=text(ROOT/'tools/m4-fp-numeric-max-integration/session.hpp','a3084c8d62164275c606630fdb152d80d595e9585e72eb728f9b3727c976469b')
 for literal in ('throw BridgeAbort{};','catch(const BridgeAbort&)','catch(...){running_=false;throw;}','if(!failed_){failed_=true;fault_=', 'thread_!=std::this_thread::get_id()','if(owner||v.failed_||','if(owns[i])try{m.unmap','r.register_service','r.register_translation','r_.call_direct({body},{0x4c19f8})','r_.call_import({slot},{0x4c1a09})'):
  need(literal in session,'Exact checked lifetime/typed fault/real routing relationship')
 need('longjmp' not in session and 'noexcept' not in session,'Real throwing typed bridges with no longjmp escape')
 need('register_service_continuation' not in session,'Separate MSVCP50 service unused r9 MSVCRT continuation helper')
 pin(ROOT/'tools/m4-runtime/runtime.hpp','41ed0a20e4f87cba3838127d943126ff88b453c39212c2ecdfe028242b4f3536');pin(ROOT/'tools/m4-runtime/runtime.cpp','48865157011deaa151dccbb598da3f5a8ed16ea1944d048549f97f66f32308f7')
 check('Independent private decode/metadata/source and Session ABI/lifetime assessment',game_owner=owner,raw_IAT=raw,provider_export=export[0],source_spans=spans,RO_input=0x78115004,default_binary32=0x7f7fffff,actual_provider_RET=0x4c1a09,owned_provider_pages=[0x780c1000,0x78115000],actual_WRAPPER_RET=True,public_full_source_instruction_spans=False,raw_memory_fault_limit='Raw source_check GuestMemory errors may propagate directly to r9 poison without a Session typed diagnostic; current stable mappings/metadata trusted. Typed checked access faults retain first Session error.',lifetime='Serial lexical borrower on constructing thread. Stable Runtime; no borrower copy/move. Discard Runtime after partial registry constructor failure; no registration rollback. No host executable provider pages or raw guest pointer casts.')
def own_controls():
 histories=[]
 for name in ('independent-compiled-session-r1','independent-compiled-session-r2','independent-compiled-session-r3'):
  d=BASE/name
  for p in d.rglob('*'):
   if p.is_file():pin(p)
  if name.endswith('r1'):
   need('typedef redefinition' in text(d/'O0-build.log') and "type 'Memory'" in text(d/'O0-build.log'),'Own literal alias-collision compilation failure retained');continue
  r=read(d/'report.json');need(r['passed'],'Prior own compiled pass retained')
  replacements={}
  for p in (d/'sources').iterdir():
   if p.is_file():replacements[canon(ROOT/'tools/m4-fp-numeric-max-session-independent'/p.name)]=p
  _,changed=filemap(d/'pins.json',None,replacements);histories+=changed
 r=read(BASE/'independent-compiled-session-r3/report.json','147e4f698f46449598936e9146339ea45b3e169c64c4867f59e40dcb6a85ae46');filemap(BASE/'independent-compiled-session-r3/pins.json','2cc94e8b17389e7fe6f9f034af3af403d5a674dfa420a39c09c2191df1c79f61')
 own=text(ROOT/'tools/m4-fp-numeric-max-session-independent/controls.cpp');need('#include "session.hpp"' in own and 'native.cpp' not in own and 'corpus.hpp' not in own and 'protocol.hpp' not in own,'Own compiled fixture independence')
 for lev in ('O0','O2'):
  result=next(x for x in r['results'] if x['level']==lev);need(result['result']['checks']==14985 and result['result']['scenarios']==238 and result['result']['positive_phases']==436 and result['result']['entered_faults']==result['result']['corrected_poison_retries']==12,'Exact own whole-State/fault extent')
  exe=pin(result['exe'],result['sha256']);actual=json.loads(run([exe,ROOT/'MW3/Mech3.exe',ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL',BASE/f'native-build-r5/native-{lev}.obj'],f'own-{lev}-causal-replay.log'));need(actual==result['result'],'Fresh unchanged independent causal replay')
 check('Own exact r5 compiled causal/whole-State/page/event/route tests and historical failures',checks_per_level=14985,scenarios_per_level=238,positive_phases_per_level=436,entered_faults_per_level=12,corrected_poison_retries_per_level=12,ownership_scenarios_per_level=6,nested_and_wrong_thread_controls_per_level=2,historical_source_replacements=histories,expected_model='Own dirty3504 hidden State seed, source-derived all four pages, independent22-access schedule/values, exact3routes and provider checkpoint; only caller ESP/EIP explicitly overridden between phases',host_claim='Earlier capture restores before observing; this stage proves harness cleanup, not numerical host boundary. Direct probe below supersedes that claim.',original_or_provider_executed=False)
def own_dependencies():
 associations=[]
 for directory in ('independent-compiled-session-r3','independent-direct-host-r1'):
  for level in ('O0','O2'):
   folder=BASE/directory/level;log=run([NINJA,'-C',folder,'-t','deps'],f'{directory}-{level}-actual-deps.txt')
   blocks=re.split(r'\r?\n\r?\n',log.strip());need(len(blocks)==4,'Actual four fresh independent C++ objects')
   for block in blocks:
    lines=block.splitlines();need('(VALID)' in lines[0],'Actual Ninja consumed dependency record valid')
    paths=[p.strip() for p in lines[1:] if p.strip()];m=re.search(r'#deps (\d+)',lines[0]);need(m and int(m[1])==len(paths),'Complete counted actual dependency block')
    for p in paths:pin(p);associations.append(dict(build=str(folder),object=lines[0].split(': #deps')[0],path=str(Path(p).resolve()),sha256=sha(p)))
   buildlog=text(BASE/directory/f'{level}-build.log');lines=[l for l in buildlog.splitlines() if ' -c -- ' in l and 'clang-cl.exe' in l];need(len(lines)==4 and all('/EHs ' in l and '/EHsc' not in l for l in lines),'Own actual exception flags')
   for p in folder.rglob('*'):
    if p.is_file():pin(p)
 for tool in ('clang-cl.exe','lld-link.exe','llvm-mt.exe','llvm-objdump.exe','llvm-readobj.exe'):pin(LLVM/tool)
 for p in (ROOT/'tools/m4-fp-numeric-max-session-independent').rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:pin(p)
 check('Actual independently compiled dependency DB associations and compiler/tool disks',actual_read_dependencies=len(associations),unique_dependency_versions=len({(x['path'],x['sha256']) for x in associations}),dependency_records=associations,scope='Ninja persisted compiler depfiles reflect source/header reads; post-build file hashes. Explicit linker command and imports retained; no complete library-open/process-time attestation.')
def object_checks(a,b):
 objects=a[next(k for k in a if 'objects' in k)]
 actual=[(x['path'],x['sha256'],'author') for x in objects]
 for lev in ('O0','O2'):
  for p in (BASE/f'independent-compiled-session-r3/{lev}/CMakeFiles/controls.dir').rglob('*.obj'):actual.append((str(p),sha(p),'own-controls'))
  p=BASE/f'independent-direct-host-r1/{lev}/CMakeFiles/probe.dir/probe.cpp.obj';actual.append((str(p),sha(p),'own-direct-probe'))
 need(len(actual)==22,'Twelve author incl two compiler probes plus eight own controls and two direct-probe boundaries')
 facts=[];handlers=[]
 for index,(p,h,role) in enumerate(actual):
  pin(p,h);d=run([LLVM/'llvm-objdump.exe','--disassemble','--reloc','--x86-asm-syntax=intel',p],f'object-{index:02d}-decode.txt');u=run([LLVM/'llvm-readobj.exe','--file-headers','--symbols','--unwind',p],f'object-{index:02d}-metadata.txt')
  need('IMAGE_FILE_MACHINE_AMD64' in u and 'file format coff-x86-64' in d,'Actual native AMD64 object')
  if Path(p).name.startswith('native-'):
   for name in ('mw34_nmx_entry_4c19f0','mw34_nmx_entry_4c1a00','mw34_nmx_entry_780c10f0','mw34_nmx_read32','mw34_nmx_readf32','mw34_nmx_write32','mw34_nmx_writef32','mw34_nmx_dispatch_body','mw34_nmx_call','mw34_nmx_return'):need(name in u and name in d,'Actual translated guest body/typed bridge relocation '+name)
   need('UnwindInfo' in u,'Actual LLVM Windows unwind metadata')
  if Path(p).name in ('native.cpp.obj','controls.cpp.obj','probe.cpp.obj'):
   blocks=u.split('  RuntimeFunction {')[1:];matches=[x for x in blocks if re.search(r'StartAddress: \?(?:enter_root|root_adapter)@Session@',x) and re.search(r'Handler: __CxxFrameHandler[34]',x)]
   need(matches,'Actual Session root owns typed C++ catch handler');handlers.append(dict(path=p,owning_handlers=[re.search(r'StartAddress: ([^\n]+)',x)[1] for x in matches]))
  facts.append(dict(path=p,sha256=h,role=role))
 check('Independent fresh actual object/typed relocations and Windows unwind owner checks',decoded_objects=len(facts),production_or_own_boundary_objects=20,auxiliary_compiler_include_probe_objects=2,objects=facts,Session_EH_owners=handlers)
def root_stages():
 r=read(BASE/'independent-final-raw-checkpoint-r1/report.json','56e3ba9876b7cc5571672ea369054b2c314b445d5bc051fd291070503bdaecf5');filemap(BASE/'independent-final-raw-checkpoint-r1/pins.json','d83ecfa29907f2371ebe2e3c18b00007b98375064425ad4bc452537dfaeea1a3')
 for s in r['stages']:
  d=BASE/s['directory'];report=read(d/'report.json',s['report_sha256']);filemap(d/'pins.json',s['pins_sha256']);need(report['passed'],'Exact final root independent review stage')
 need(r['native_persistent_phases']==864 and r['native_paired_replays']==14688 and r['observer_corruption_rejects']==328 and r['selected_joint_initializer_roots']==26,'Root full raw/model counts and joint scope')
 for p in ('static_review.py','persistent_model.py','replay_model.py'):
  source=text(ROOT/'tools/m4-fp-numeric-max-integration-independent'/p);need('tools/m4-fp-numeric-max-integration/observe.py' not in source,'No author primary comparison import')
 check('Root separately authored full private source/IR/layout/raw/input-derived model checkpoint',native_persistent_phases=864,persistent_State_carry=432,original_wrappers=7344,separate_paired_original_leaves=7344,native_wrapper_replays=14688,native_events=342144,native_routes=46656,independent_corruption_rejects=328,scope='No original AFTER or checkpoint used to execute/predict output. Original State/events unobserved. FX/ENV native software projection distinct from original actual hardware FX/FNSTENV and Windows CONTEXT. Final raw80 dead storage/undefined FP condition observations remain observational.',host_scope_correction='Root historical host buffer equality accurately checks recorded harness restore buffers. It cannot prove Session host preservation; direct actual boundary below finds clobber.',State_bytes=3504,CXX_alignment=16,LLVM_alignment=8,Runtime_alignment=64,selected_joint_roots=26,whole_M4_complete=False)
def direct_finding():
 d=BASE/'independent-direct-host-r1';r=read(d/'report.json','49a5d97801d3f6827a9d46e87b1f25e107961f9208ac905a3cf42417d649abaa');filemap(d/'pins.json','5aee2a2496ff83978dc2b023d92bbef7786a40ae4eabab7cdff898e46a6ac896');need(r['passed'],'Actual new direct-before/after probe')
 records=[]
 for lev in ('O0','O2'):
  raw=pin(d/f'{lev}.bin').read_bytes();need(len(raw)==6*1648,'Exact six actual full FX/ENV direct records')
  for i in range(6):
   record=raw[i*1648:(i+1)*1648];cw,mode,denied,reserved=struct.unpack_from('<4I',record);before=record[16:560];after=record[560:1104]
   bcw,bsw,btag=struct.unpack_from('<HHB',before);acw,asw,atag=struct.unpack_from('<HHB',after);benv=struct.unpack_from('<7I',before,512);aenv=struct.unpack_from('<7I',after,512)
   need(cw in (0x7f,0x37f,0xb7f) and mode==denied and reserved==0 and bcw==acw==cw and btag==atag==0xc0 and bsw&0x20 and not asw&0x20,'Independent direct caller PE removed on actual positive/fault route')
   need(benv[3:6]!=aenv[3:6],'Actual legacy x87 metadata clobber observed before harness restore')
   records.append(dict(level=lev,cw=cw,mode=mode,actual_denied=bool(denied),before_SW=bsw,after_SW=asw,before_ENV=list(benv),after_ENV=list(aenv),actual_FX_changed_offsets=[j for j in range(512) if before[j]!=after[j]]))
 source=text(ROOT/'tools/m4-fp-numeric-max-session-independent/direct-host-probe/probe.cpp');need(source.index('snap(r.after)')<source.index('restore(initial)'),'Direct after observation occurs before any explicit cleanup')
 author=text(ROOT/'tools/m4-fp-numeric-max-integration/native.cpp');own=text(ROOT/'tools/m4-fp-numeric-max-session-independent/controls.cpp');need('void capture(){restore();' in author and 'void capture(){restore();' in own,'Exact historical overstated host observer identified in both author and early own tests')
 check('Actual causal host-boundary defect found with unchanged r5 source/object',direct_records=12,successes=6,actual_output_write_faults=6,records=records,numerical_host_preservation_proved=False,historical_capture_scope='Explicit harness restoration before capture proves cleanup only. This limits author/root/early-own full-host restoration language; their numerical guest model and other causal results remain valid.',remediation='New production Session numerical FP boundary with save/restore on success and actual exception escape, plus direct-before/after tests. Author owns derivative; old r5/r3/raw/history frozen.',SIMD_scope='XMM0..5 are Windows caller-volatile; full XMM equality across ordinary C++ route is not required by this numerical boundary. No ABI claim inferred from their observed changes.')
 return records
def main():
 need(not OUT.exists(),'Fresh final closure namespace');OUT.mkdir(parents=True)
 try:
  sources=OUT/'sources';sources.mkdir()
  for p in (ROOT/'tools/m4-fp-numeric-max-session-independent').rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts:
    relative=p.relative_to(ROOT/'tools/m4-fp-numeric-max-session-independent');dst=sources/relative;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(p.read_bytes());pin(p);pin(dst)
  for prior in ('independent-session-closure-r1','independent-session-closure-r2','independent-session-closure-r3'):
   for p in (BASE/prior).rglob('*'):
    if p.is_file():pin(p)
  need('Literal source matches original recorded manifest' in text(BASE/'independent-session-closure-r1/failure.txt'),'Own prior report-schema assumption failure retained')
  need('Own literal alias-collision compilation failure retained' in text(BASE/'independent-session-closure-r2/failure.txt'),'Own prior compiler-error-log-location assumption retained')
  need('Actual four fresh independent C++ objects' in text(BASE/'independent-session-closure-r3/failure.txt'),'Own prior CRLF dependency-block split failure retained')
  a,b=author_closure();original_and_source();own_controls();own_dependencies();object_checks(a,b);root_stages();records=direct_finding();pin(sys.executable)
  report=dict(passed=False,technical_checks_passed=True,acceptance='Requires numerical host-boundary repair; frozen r5 independently reviewed as historical narrow guest-result evidence',checks=CHECKS,commands=COMMANDS,counts=dict(author_physical_bindings=3836,author_actual_header_reads=3296,fresh_object_decodes=22,own_compiled_checks_per_level=14985,own_compiled_scenarios_per_level=238,own_positive_phases_per_level=436,own_typed_faults_per_level=12,own_corrected_poison_retries_per_level=12,own_ownership_scenarios_per_level=6,own_borrow_controls_per_level=2,actual_direct_host_records=12,independent_raw_observer_rejects=328),unresolved_host_preservation_finding=True,unchanged_r9=True,selected_joint_initializer_roots=26,remaining_joint_roots=118,original_or_provider_execution=False,full_M4_complete=False,physical_bindings_before_report=len(PINS))
  p=OUT/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');pin(p)
  for p,h in PINS.items():need(sha(p)==h,'Final stable physical binding '+p)
  (OUT/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n');print(json.dumps(dict(technical_checks_passed=True,accepted=False,physical_bindings=len(PINS),report_sha256=sha(OUT/'report.json'),pins_sha256=sha(OUT/'pins.json'))))
 except Exception:(OUT/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
