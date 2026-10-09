"""Additive physical author closure. Independent reviewers are excluded."""
from pathlib import Path
import hashlib,json,re,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[3];REPORTS=ROOT/'reports/m4-crt-matherr'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(ok,msg):
 if not ok:raise AssertionError(msg)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def main():
 out=Path(sys.argv[1]).resolve();need(not out.exists(),'Fresh author seal');out.mkdir(parents=True);(out/'seal-source.py').write_bytes(Path(__file__).read_bytes())
 files={};history=[];associations=[];headers=[];maps=[];commands=[]
 def bind(p,expected=None):
  p=Path(p).resolve();need(p.is_file(),f'Missing physical {p}');s=sha(p);need(expected is None or s==expected,f'Physical mismatch {p}');files[str(p)]=s;return s
 def copies_from(r):
  for c in r.get('literal_sources',[]):yield c['original_path'],c['preserved_path'],c['sha256']
 archives={}
 names=['preparation-r1','abi-r1','native-build-r1','native-build-r2','preflight-seal-r1','preflight-seal-r2','paired-preparation-r1','paired-context-derivation-r1','paired-original-build-r1-normal-windows','paired-original-r1-normal-windows','paired-comparison-r1','paired-worker-controls-r1']+[f'paired-native-build-r{i}' for i in range(1,8)]
 dirs=[REPORTS/n for n in names]
 for d in dirs:
  for p in d.rglob('*.json'):
   try:r=read(p)
   except (ValueError,UnicodeError):continue
   if isinstance(r,dict):
    for original,preserved,s in copies_from(r):archives.setdefault((str(Path(original).resolve()),s),[]).append(Path(preserved))
 try:
  for d in dirs:
   need(d.is_dir(),f'Missing frozen evidence {d}')
   for p in d.rglob('*'):
    if p.is_file() and 'compiler-temp' not in p.parts:bind(p)
   for p in d.rglob('*.json'):
    try:r=read(p)
    except (ValueError,UnicodeError):continue
    if not isinstance(r,dict):continue
    for group in ['files','sources','source_files','tools','tool_files','artifacts']:
     m=r.get(group)
     if not isinstance(m,dict):continue
     for path,s in m.items():
      if not isinstance(s,str) or not re.fullmatch('[0-9a-f]{64}',s):continue
      original=Path(path).resolve();need('independent' not in str(original).lower(),'Author map unexpectedly consumes independent review')
      actual=original
      if not actual.is_file() or sha(actual)!=s:
       candidates=archives.get((str(original),s),[]);need(bool(candidates),f'No literal historical association {original} {s}');actual=candidates[0];history.append({'map':str(p),'group':group,'original_path':str(original),'sha256':s,'literal_path':str(actual.resolve())})
      bind(actual,s);associations.append({'map':str(p),'group':group,'original_path':str(original),'sha256':s,'resolved_physical_path':str(actual.resolve())})
     maps.append({'path':str(p),'group':group,'entries':len(m)})
    for original,preserved,s in copies_from(r):bind(preserved,s)
  build=REPORTS/'paired-native-build-r7/build.json';r=read(build);need(r['passed'],'Final build did not pass')
  # Actual compiler-consumed paths, resolved against literal snapshots by build version.
  for d in [REPORTS/f'paired-native-build-r{i}' for i in range(1,8)]+[REPORTS/'paired-original-build-r1-normal-windows']:
   for log in list(d.glob('build-*.log'))+list(d.glob('build.log')):
    text=log.read_text(encoding='utf-8-sig');version=read(d/'build.json')
    source_map={str(Path(a).resolve()):Path(b) for a,b,s in copies_from(version)}
    for path in sorted(set(re.findall(r'Note: including file:\s+([^\r\n]+)',text))):
     original=Path(path.strip()).resolve();actual=source_map.get(str(original),original);s=bind(actual);headers.append({'log':str(log),'original_path':str(original),'literal_or_current_path':str(actual.resolve()),'sha256':s,'provenance':'actual compiler include log with exact build-source version'})
  tools=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';objdump=tools/'llvm-objdump.exe';readobj=tools/'llvm-readobj.exe';bind(objdump);bind(readobj)
  decode=out/'object-audit';decode.mkdir();object_rows=[]
  for item in r['builds']:
   objects=[Path(item['object']),*Path(item['directory']).rglob('*.obj')]
   for index,p in enumerate(objects):
    bind(p);stem=f"{item['level']}-{index}";dest=decode/f'{stem}.decode.txt';uw=decode/f'{stem}.unwind.txt'
    for program,args,target in [(objdump,['--disassemble','--reloc','--x86-asm-syntax=intel',str(p)],dest),(readobj,['--unwind','--coff-directives',str(p)],uw)]:
     completed=subprocess.run([str(program),*args],capture_output=True,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW);target.write_bytes(completed.stdout);(target.with_suffix(target.suffix+'.stderr')).write_bytes(completed.stderr);need(completed.returncode==0,'Fresh final COFF inspection failed');bind(target);bind(target.with_suffix(target.suffix+'.stderr'));commands.append({'program':str(program),'arguments':args,'exit_code':completed.returncode,'output':str(target),'sha256':sha(target)})
    object_rows.append({'level':item['level'],'object':str(p),'sha256':sha(p),'decode':str(dest),'unwind':str(uw)})
  # Explicit final object/local-catch evidence, with unchanged guest source IR.
  for level in ('O0','O2'):
   need('StartAddress: sub_7800b38f' in (decode/f'{level}-0.unwind.txt').read_text(),'Actual guest frame unwind absent')
  need('/EHsc' not in re.search(r'\[\d+/\d+\].*native_paired\.cpp[^\r\n]*', (REPORTS/'paired-native-build-r7/build-O0.log').read_text(encoding='utf-8-sig')).group(),'Inherited external-C no-throw assumption persisted')
  # Linker input libraries: explicitly bind the named/default SDK/MSVC inputs.
  sdk=Path('C:/Program Files (x86)/Windows Kits/10/Lib/10.0.26100.0');vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231/lib/x64')
  libs=[]
  for p in [*(sdk/'um/x64'/n for n in ['bcrypt.lib','kernel32.lib','user32.lib','gdi32.lib','winspool.lib','shell32.lib','ole32.lib','oleaut32.lib','uuid.lib','comdlg32.lib','advapi32.lib']),sdk/'ucrt/x64/ucrt.lib',*(vc/n for n in ['msvcrt.lib','msvcprt.lib','vcruntime.lib','oldnames.lib'])]:libs.append({'path':str(p),'sha256':bind(p),'association':'named final link/default object library; post-build physical binding'})
  current=[]
  for p in (ROOT/'tools/m4-crt-matherr/paired').rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts:
    dest=out/'sources'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes());bind(p);bind(dest);current.append({'original_path':str(p),'preserved_path':str(dest),'sha256':sha(p)})
  doc=ROOT/'docs/m4-crt-matherr-paired-variant.md';dest=out/'sources'/doc.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(doc.read_bytes());bind(doc);bind(dest)
  units=[read(REPORTS/f'paired-native-build-r7/unit-{l}.json') for l in ['O0','O2']]
  need(all(u['passed'] and u['positive_cases']==1536 and u['fault_scenarios']==21 and u['poisoned_retries']==17 and u['checks']==1692 for u in units),'Final actual unit summary inconsistent')
  need(read(REPORTS/'paired-comparison-r1/report.json')['passed'] and read(REPORTS/'paired-worker-controls-r1/report.json')['passed'],'Author controls/comparison incomplete')
  report={'passed':True,'scope':'Native-only paired candidate author closure. Frozen original evidence is read-only input/provenance; no original process was executed in this native task. Original/reference earlier captures retain their distinct provenance. Independent review pending; no ordinary game/callback invocation or full startup claim.',
   'final_build':str(build),'final_build_sha256':sha(build),'literal_sources':current,'all_source_map_associations':associations,'historical_source_associations':history,'actual_read_header_associations':headers,'consumed_maps':maps,'object_audits':object_rows,'object_audit_commands':commands,'link_input_bindings':libs,
   'native_records':3072,'original_read_only_records':1536,'actual_native_positive_unit_cases':3072,'actual_native_unit_assertions':3384,'actual_native_fault_scenarios':42,'corrected_poisoned_retries':34,'native_worker_denials':20,'recipe_no_mutation_controls':3,'author_observer_controls':282,
   'raw_records':[{'level':i['level'],'path':i['observations'],'sha256':sha(i['observations']),'size':Path(i['observations']).stat().st_size} for i in r['builds']],
   'attempts_preserved':{'r1':'External-C no-unwind assumption removed local catch; Runtime caught/poisoned, Context active remained true','r2':'Diagnostic output added; same actual caught Runtime error','r3':'Appending /EHs did not remove inherited /EHsc assumption','r4':'Removed inherited /EHsc; actual typed catch passes; test incorrectly expected NV closure denial before fifth access','r5':'Fixed NV assertion; test incorrectly expected revalidation of unexecuted game CALL bytes','r6':'Test incorrectly expected host-mutated game permissions to replace immutable admitted metadata','r7':'Final compiled EAX/NV/RET/access/routing/error/reuse/host controls and BEFORE-only replay passed'},
   'original_after_as_execution_input':False,'original_AF':'Undefined only in relational CPU AFTER; native chosen zero checked in full State model','capture_PC_projection':{'original_instrumentation':0x10000100,'native_real_return':0x5ac42e},'native_ENV_after':'Preserved input serialization, not guest hardware capture; actual whole State separately proves legacy field preservation','shared_Runtime':'Exact frozen r9; trusted stable owner/metadata, serial private ordinary paths; deliberate mapping replacement/permission mutation and concurrent publication excluded','independent_acceptance':False,'callback_invoked':False,'whole_M4_complete':False}
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');bind(out/'seal-source.py');bind(Path(__file__))
  for p,s in files.items():need(sha(p)==s,f'Closure changed during seal {p}')
  (out/'pins.json').write_text(json.dumps({'files':dict(sorted(files.items()))},indent=2)+'\n')
  print(json.dumps({'passed':True,'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json'),'bindings':len(files),'history':len(history),'source_associations':len(associations),'compiler_reads':len(headers),'objects':len(object_rows),'current_literal_sources':len(current)}))
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
