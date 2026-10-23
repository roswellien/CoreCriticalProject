"""ROOT-executed only: fail-closed single-case ordinary strict-input admission.

No model import, worker, capture reader, helper execution, or acceptance call.
Author prepares this file; ROOT must inspect it before choosing to execute it.
"""
from pathlib import Path
import argparse,ast,hashlib,json,os,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PRODUCER_SHA='8dfa8a7f753a692f3d47a3a5f4d6a7ca9700da25ed26910f2fd79e5235bca426'
BUILD_SHA='9a65633f858e7c06c5ca09a8191a41051321cf2848c1a25b4318bd4c61c08a9f'
PREP3_SHA='8a322602c066931f5dd3ced2b9319f6907b0b01413828e2d72dd482c5ce09b2c'
POSITIVE_SHA='a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a'
STRICT_PREPS=['28f6c7b23cc4cdcf9c7db09163ef1e2cd99287168ba853f4d255efa2cc410fcc','ffdf60c8be8d6cdf158bc4d9b770ec82ba9fd384321040dc735e117c1f847820','33e28ac4430a5fc74aa6a632f1371b378bd7f5788fa41cb07dc86198bc8225e5','b30f479ddedae272549417c4b764d59e252ae918973d1ffd114ea0bc13b01a77','d2224c8bd5bd2a0371a9c518051f959dc6f5eaa1eb7304cdea147a8efe305d9c']
ADVERSE_SHA='8f0f2aeafe42966034613618ff4cf6577692fd6f74031cd35b429ac5a03b8328'
CODE=(
 'tools/m4-138-preresource-strict-review/aggregate_v1.py',
 'reports/m4-138-preresource-strict-review/preparation-r2/ordinary_case_v2.py',
 'reports/m4-138-preresource-strict-review/preparation-r5/verify_case_v5.py',
 'tools/m4-joint-startup131/mfc_source.py',
 'tools/m4-mfc1168-native/persistent_source.py',
 'tools/m4-mfc1168-native/verify_resource_fixture.py',
 'tools/m4-crt-locale-batch-model-review/interpreter_v2.py',
 'tools/m4-formatting-source/flag_domain.py',
 'tools/m4-tree-review/amd64_pe.py','tools/analysis/pe.py',
 'tools/m4-mfc1168-native/connected_component_v2.cpp',
 'tools/m4-mfc1168-native/connected_entry.hpp',
 'tools/m4-138-preresource-strict-review/preflight_v1.py',
 'tools/m4-138-preresource-strict-review/preflight_v2.py')

def need(v,label):
 if not v:raise ValueError(label)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def no_duplicate_pairs(pairs):
 d={}
 for k,v in pairs:need(k not in d,'No duplicate JSON field '+k);d[k]=v
 return d

def main(a):
 need(re.fullmatch(r'[A-Za-z0-9_-]{1,90}',a.name),'Fresh simple output name')
 out=R/'reports/m4-138-preresource-strict-review'/a.name;need(not out.exists(),'Fresh immutable ROOT admission')
 files={};path_spellings={};case_files={};reads=[];owners=[];inverses=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();need(p.is_file()and not p.is_symlink(),'Exact physical ordinary file '+str(p));need(p.suffix.lower()not in('.mwb','.mwi','.zip','.gz','.7z')and p.name!='transport.json','No capture/archive/transport dependency')
  key=str(p);fold=key.casefold();need(path_spellings.setdefault(fold,key)==key,'One canonical path spelling')
  actual=sha(p);need(h is None or actual==h,'Exact physically current file '+key);need(files.setdefault(key,actual)==actual,'No conflicting path digest')
  return p
 def blob(p,h=None):
  p=pin(p,h);reads.append(str(p));return p.read_bytes()
 def read(p,h=None):return json.loads(blob(p,h),object_pairs_hook=no_duplicate_pairs)
 def absorb(v):
  need(isinstance(v,dict),'Exact named filemap')
  for p,h in v.items():need(re.fullmatch('[0-9a-f]{64}',h)is not None,'Exact lowercase SHA256');pin(p,h)
 def source_text(p):
  return blob(p).decode().replace('\r\n','\n')
 def invert(text,deltas):
  for d in reversed(deltas):
   need(isinstance(d['before'],str)and isinstance(d['after'],str)and text.count(d['after'])==1,'One exact retained inverse occurrence')
   text=text.replace(d['after'],d['before'])
  return text
 # Preparation/current build and every actual one-case file close before any
 # helper imports or source-model work (this builder never imports helpers).
 e=read(a.execution,a.execution_sha);need(e['passed']is True and e['worker_closed']is True and e['worker_executed']is True and e['facts']['exit_code']==0,'Actual terminal passed ordinary producer case')
 level=e['level'];mode=e['mode'];need(level in('O0','O2')and type(mode)is int and 1<=mode<=12,'Exact future reusable finite case parameter')
 need(re.fullmatch(r'execution-'+level+'-mode'+str(mode)+r'-r[1-9][0-9]*',Path(a.execution).resolve().parent.name),'Exact current producer case folder')
 case_files=dict(e['files']);absorb(case_files)
 args=e['facts']['arguments'];need(len(args)==8 and args[-1]==str(mode)and args[-2]==PRODUCER_SHA,'Exact producer case invocation/admission')
 folder=Path(args[-3]).resolve();need(folder==Path(a.execution).resolve().parent/'payload','Own current case payload')
 actual={};total=0
 for p in folder.rglob('*'):
  if not p.is_file():continue
  need(not p.is_symlink()and p.resolve().is_relative_to(folder),'No external output path')
  n=p.stat().st_size;need(n<=32*1024*1024,'Bounded individual actual output');total+=n
  actual[str(p.resolve())]=case_files.get(str(p.resolve()));need(actual[str(p.resolve())]is not None,'Every actual payload file sealed by producer')
  need(len(actual)<=100000 and total<=512*1024*1024,'Bounded exact single-case complete inventory')
 need({p for p in case_files if Path(p).is_relative_to(folder)}==set(actual),'No omitted/extra ordinary payload file relation')
 need(blob(folder/'admission.txt').decode()==PRODUCER_SHA,'Whole actual payload admission')
 need((folder/'COMPLETE.txt').is_file()and not(folder/'FAILED.txt').exists(),'Actual complete current payload')
 producer=R/'reports/m4-138-preresource-root-review/root-run-admission-r1/report.json';prad=read(producer,PRODUCER_SHA);need(prad['passed']is True and prad['scope_identity']=='current138_preresource_legacy12'and prad['ordinary_outputs_only']is True and prad['modes']==list(range(1,13))and prad['levels']==['O0','O2'],'Independently passed exact producer prelaunch')
 required=('complete_source_inverse','exact_real64byte_MFC_entry_frame','bounded14prefix_no_reseed','complete_private_and_public_retry_inventory','current_MFC_and_widget_fault_cleanup','whole_linked_current_context_and_provider_inputs','typed_COFF_CALL_TLS_ownership','whole85byte_boundary_target_and_unwind')
 need(set(prad['prelaunch_checks'])==set(required)and all(prad['prelaunch_checks'][k]is True for k in required),'All precise independent producer admission obligations')
 b=read(R/'reports/m4-138-preresource-controls/build-r4/build.json',BUILD_SHA);need(b['passed']and b['worker_executed']is False,'Exact current build-only facts');absorb(b['files'])
 cp=read(b['preparation'],PREP3_SHA);need(cp['passed']and cp['whole_parent_main_inverse']and cp['whole_legacy_controls_inverse'],'Current precise phase13 emitted input recipe');absorb(cp['files'])
 positive=read(cp['parent_preparation'],POSITIVE_SHA);need(positive['passed'],'Current positive parent declaration');need(args[0]==b['workers'][level]['path'],'Current actual requested compiler worker')
 for i,row in enumerate(cp['source_images']):need(args[i+1]==row['path']and Path(row['path']).stat().st_size==row['bytes'],'Exact actual physical provider invocation')
 # Only actual Extension reads below; no recursive unrelated report union.
 original=read(positive['chronological_original'],positive['inputs']['original_prefix_receipt_sha256']);need(original['passed'],'Genuine chronological original input gate')
 source=read(positive['chronological_source'],positive['inputs']['source_domain_receipt_sha256']);need(source['passed']and source['source_AFTER_seed']is False,'Independent current borrowed source declaration')
 derived=read(Path(positive['chronological_source']).parent/'source-derivations.json');need(isinstance(derived['source_PCs'],list)and len(derived['source_PCs'])==142,'Exact source PC declaration used by Extension')
 retained=read(Path(positive['chronological_original']).parent/'retained-actual-inputs.json')
 keys=['MFC1168/BEFORE/MFC/'+str(0x5f4cb000)+'.bin','MFC1168/BEFORE/CRT-codepage-lock/bytes.bin']+['MFC1168/BEFORE/domain/'+r['role']+'/bytes.bin'for r in positive['inputs']['role_owners']]
 need(len(keys)==len(set(keys))==7,'Exactly seven genuine own BEFORE input backings')
 for key in keys:
  need('/BEFORE/'in key and key in retained,'Exact genuine BEFORE name');v=retained[key];p=pin(v['path'],v['sha256']);need(p.stat().st_size==v['bytes'],'Whole genuine input extent');reads.append(str(p))
 contracts=read(R/'reports/m4-mfc1168-probe/native-contracts-r1/contracts.json','f7db9805f43e1eb7ef84ad8adb5ddb0f788b76844dbaadb736329787a410eb64');need(len(contracts['instructions'])==142,'Exact finite source contract')
 for p,h in [('MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),('local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8'),('local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')]:pin(R/p,h)
 # Whole inverse of every immutable source helper/checker preparation.
 for n,h in enumerate(STRICT_PREPS,1):
  report=read(R/f'reports/m4-138-preresource-strict-review/preparation-r{n}/report.json',h);need(report['passed'],'Strict preparation passed');absorb(report['files'])
 prep=R/'reports/m4-138-preresource-strict-review'
 v1=source_text(prep/'preparation-r1/verify_case_v1.py');base=source_text(R/'tools/m4-mfc1168-native/verify_connected_controls.py')
 ds=read(prep/'preparation-r1/exact-deltas.json');need(len(ds)==14 and invert(v1,ds)==base,'All14 strict1 inverse hunks preserve retained source/API/lifetime checker');inverses.append(14)
 h1=source_text(R/'tools/m4-138-preresource-strict-review/ordinary_case.py');h2=source_text(prep/'preparation-r2/ordinary_case_v2.py');ds=read(prep/'preparation-r2/exact-deltas.json');need(len(ds)==5 and invert(h2,ds)==h1,'Exact current FPS bootstrap namespace helper inverse');inverses.append(5)
 v2=source_text(prep/'preparation-r2/verify_case_v2.py');old="ROOT/'tools/m4-138-preresource-strict-review/ordinary_case.py'";new="ROOT/'reports/m4-138-preresource-strict-review/preparation-r2/ordinary_case_v2.py'";need(v2.count(new)==1 and v2.replace(new,old)==v1,'Exact helper binding inverse');inverses.append(1)
 v3=source_text(prep/'preparation-r3/verify_case_v3.py');ds=read(prep/'preparation-r3/exact-deltas.json');need(len(ds)==3 and invert(v3,ds)==v2,'Exact report-root/physical pin/code-child inverse');inverses.append(3)
 v4=source_text(prep/'preparation-r4/verify_case_v4.py');ds=read(prep/'preparation-r4/exact-deltas.json');need(len(ds)==2 and invert(v4,ds)==v3,'Exact own BEFORE and typed TLS API relation inverse');inverses.append(2)
 v5=source_text(prep/'preparation-r5/verify_case_v5.py');ds=read(prep/'preparation-r5/exact-deltas.json');need(len(ds)==1 and invert(v5,ds)==v4,'Exactly one current ROOT admission own-path+SHA pin exception inverse');inverses.append(1)
 need("(p==admission_path and v==admission_sha)or p.is_relative_to(out.resolve())or admitted.get(str(p))==v"in v5,'Only exact already-authenticated current admission exception')
 need("for q,h in pins.items():eq(sha(q),h"in v5,'Every final entire physical dependency rehash retained')
 need('ROOT=Path(__file__).resolve().parents[3]'in v4 and 'V.PINS=pins;V.pin=pin'in v4 and "V.raw=raw"in v4,'No report-root or physical raw pin fallback')
 for q in CODE:
  text=blob(R/q).decode()
  if q.endswith('.py'):ast.parse(text)
 fixture=source_text(R/'tools/m4-mfc1168-native/verify_resource_fixture.py');need('PINS={};CACHE={}'in fixture,'Fresh module cache initially empty')
 literal=source_text(R/'tools/m4-mfc1168-native/persistent_source.py');need("I=module(R/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py'"in literal and "F=module(R/'tools/m4-formatting-source/flag_domain.py'"in literal,'Exactly two eager literal child imports closed')
 helper=source_text(R/'tools/m4-joint-startup131/mfc_source.py');need('callbacks={}'in literal and 'program=program,callbacks={}'in literal and 'callbacks={}'in v4,'All actual source paths supply explicit program/callbacks without interpreter file fallback')
 adverse=read(prep/'schema-preflight-r2/report.json',ADVERSE_SHA);need(adverse['passed']and adverse['count']==40 and not adverse['actual_case_review_executed'],'Exact40 synthetic schema adverses; no runtime success substitution');absorb(adverse['files'])
 # Read the bounded actual native ownership facts, not a model's guessed DLL.
 stem=folder/f'control-{mode}/MFC';terminal=struct.unpack('<13I',blob(folder/f'control-{mode}/terminal-facts.bin'));need(terminal[:7]==(1,mode,0,1,1,13,13)and terminal[7]in(0,1),'Actual precise phase13/current component extent')
 resource_dir=stem/'resources'
 if terminal[7]:
  context=struct.unpack('<12Q',blob(stem/'cleaned/resource-context.bin'));count=context[11];need(0<count<=16,'Finite actual complete owned resource serial count')
  need({p.name for p in resource_dir.iterdir()if p.is_dir()}=={str(n)for n in range(count)},'Exact contiguous actual owned resource directories')
 else:
  count=0;need(not resource_dir.exists(),'Exact constructor refusal has no native owned resource event domain')
 system32=(Path(os.environ['SystemRoot'])/'System32').resolve();modules={}
 for n in range(count):
  p=resource_dir/str(n);call=struct.unpack('<8Q',blob(p/'call.bin'));need(call[:2]==(1,n)and call[2]<8,'Exact actual finite resource service serial/kind')
  left=blob(p/'before-path.txt');need(left==blob(p/'after-path.txt'),'Whole observed native owner path stable');name=Path(left.decode()).resolve();need(name.parent==system32 and name.name.lower()in('kernel32.dll','kernelbase.dll','ntdll.dll'),'Exact observed owning System32 image whitelist')
  h=blob(p/'before-sha256.txt').decode();need(h==blob(p/'after-sha256.txt').decode()and re.fullmatch('[0-9a-f]{64}',h),'Exact whole observed native owner SHA before/after');pin(name,h);need(modules.setdefault(str(name),h)==h,'No conflicting actual native module digest')
  ib=blob(p/'before-identity.bin');need(ib==blob(p/'after-identity.bin'),'Whole actual ownership identity stable');identity=struct.unpack('<9Q',ib);need(identity[:2]==(1,call[2]),'Actual native identity belongs to same service kind');entry=blob(p/'before-entry64.bin');need(len(entry)==64 and entry==blob(p/'after-entry64.bin'),'Whole actual observed64byte API entry stable')
  owners.append(dict(serial=n,kind=call[2],path=str(name),sha256=h,identity_words=list(identity),entry64_sha256=hashlib.sha256(entry).hexdigest()))
 pin(sys.executable);pin(__file__)
 # Rehash final entire admitted ordinary dependency frontier. No import or
 # checker/worker launch has occurred in this builder.
 for q,h in files.items():need(sha(q)==h,'Every admitted dependency stable at final boundary')
 out.mkdir();(out/'actual-native-owner-preimport-joins.json').write_text(json.dumps(owners,indent=2)+'\n')
 report=dict(passed=True,scope_identity='current138_preresource_strict_outputs',scope='ROOT single-case complete physically rehashed ordinary read/import frontier; strict semantic checker still unexecuted',producer_admission_sha256=PRODUCER_SHA,execution=str(Path(a.execution).resolve()),execution_sha256=a.execution_sha,level=level,mode=mode,strict_checker=str(prep/'preparation-r5/verify_case_v5.py'),strict_checker_sha256=sha(prep/'preparation-r5/verify_case_v5.py'),whole_source_preparations_inverse=inverses,synthetic_adverses=40,genuine_BEFORE_backings=7,actual_native_service_count=count,actual_native_modules=modules,case_payload_files=len(actual),case_payload_bytes=total,helpers_imported=False,source_model_executed=False,worker_executed=False,capture_reader_opened=False,strict_semantic_gate_passed=False,initializer_credit=0,accepted_function_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,files=len(files),sha256=sha(out/'report.json'))))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('execution');p.add_argument('execution_sha');p.add_argument('name');main(p.parse_args())
