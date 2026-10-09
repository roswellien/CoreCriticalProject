"""Literal/transitive author closure with preserved historical source resolution."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];PRIVATE=ROOT/'reports/m4-fp-numeric-max'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def bind(p):
 p=Path(p).resolve();return {'path':str(p),'size_bytes':p.stat().st_size,'sha256':sha(p)}
def require(ok,why):
 if not ok:raise ValueError(why)
def main():
 out=PRIVATE/'author-review-r1';require(not out.exists(),'Fresh author closure required');out.mkdir(parents=True)
 final=PRIVATE/'repaired-r2';original=PRIVATE/'original-r5-normal-windows';comparison=PRIVATE/'final-comparison-r2/report.json';controls=PRIVATE/'causal-controls-r1-normal-windows/report.json'
 for p in (final/'build.json',original/'report.json',comparison,controls):require(json.loads(p.read_text(encoding='utf-8-sig'))['passed'],'Final required evidence failed')
 files={};literals=[];resolutions=[];commands=[]
 def add(p):files[str(Path(p).resolve())]=bind(p)
 def copy(p,kind):
  p=Path(p).resolve();dst=out/'sources'/p.relative_to(ROOT) if p.is_relative_to(ROOT) else out/'sdk-sources'/(sha(p)+'-'+p.name)
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst);require(sha(dst)==sha(p),'Literal copy differs');add(dst);add(p);literals.append({'original_path':str(p),'preserved':bind(dst),'kind':kind})
 for directory in (ROOT/'tools/m4-fp-numeric-max',ROOT/'tests/m4-fp-numeric-max'):
  for p in directory.glob('*'):
   if p.is_file():copy(p,'current authored source')
 for p in (ROOT/'tools/lifting/host_adapter.py',ROOT/'tools/analysis/pe.py',ROOT/'runtime/memory/guest_memory.cpp',ROOT/'runtime/memory/guest_memory.hpp',ROOT/'runtime/core/guest_address.hpp'):copy(p,'exact frozen reused dependency')
 # Actual compiler read dependencies, captured additively after compilation.
 dependencies=set();ninja=Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe');llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
 for level in ('O0','O2'):
  args=[ninja,'-C',final/('build-'+level),'-t','deps'];r=subprocess.run(list(map(str,args)),capture_output=True);require(r.returncode==0,'Actual Ninja dependencies unavailable');log=out/('deps-'+level+'.txt');log.write_bytes(r.stdout);(out/('deps-'+level+'.stderr')).write_bytes(r.stderr);commands.append({'command':list(map(str,args)),'exit_code':r.returncode,'stdout':bind(log)})
  for line in r.stdout.decode().splitlines():
   if line.startswith('    '):
    p=Path(line.strip());require(p.is_file(),'Actual dependency unavailable '+str(p));dependencies.add(p.resolve())
 for build in (PRIVATE/'original-build-r5/build',final/'build-x86'):
  for log in build.rglob('*.read.1.tlog'):
   raw=log.read_bytes();text=raw.decode('utf-16' if raw.startswith(b'\xff\xfe') else 'utf-8')
   for line in text.splitlines():
    if not line or line.startswith('^'):continue
    p=Path(line)
    if p.is_file():dependencies.add(p.resolve())
 dependency_rows=[]
 for p in sorted(dependencies,key=lambda p:str(p).casefold()):
  row=bind(p);row['scope']='additive post-build rehash of actual compiler read dependency; not claimed precompile identity';dependency_rows.append(row);add(p)
  if (not p.is_relative_to(ROOT) or 'local/tools' in str(p).replace('\\','/')) and p.suffix.lower() not in ('.exe','.dll','.lib','.obj','.pch','.pdb') and p.stat().st_size<3000000:copy(p,'actual SDK/STL/compiler/Remill source dependency, post-build literal copy')
 # Every private historical artifact stays bound. Index literal copies before
 # resolving source paths that the authorized repairs superseded.
 index={}
 for p in PRIVATE.rglob('*'):
  if p.is_file() and not p.is_relative_to(out):
   add(p)
   if any(x in ('sources','source-copies') for x in p.parts):index.setdefault((p.name.casefold(),sha(p)),[]).append(p.resolve())
 def resolve(path,digest):
  p=Path(path)
  if p.is_file() and sha(p)==digest:physical=p.resolve()
  else:
   candidates=index.get((p.name.casefold(),digest),[]);require(bool(candidates),'No literal historical binding '+str(p));physical=candidates[0]
  add(physical);resolutions.append({'original_path':str(p),'sha256':digest,'physical_path':str(physical)})
 for p in PRIVATE.rglob('build.json'):
  if p.is_relative_to(out):continue
  doc=json.loads(p.read_text(encoding='utf-8-sig'))
  for path,digest in doc.get('bindings',{}).items():resolve(path,digest)
 for p in PRIVATE.rglob('report.json'):
  if p.is_relative_to(out):continue
  doc=json.loads(p.read_text(encoding='utf-8-sig'))
  for row in doc.get('sources',[]):
   if 'path' in row and 'sha256' in row:resolve(row['path'],row['sha256'])
 for item in json.loads((PRIVATE/'recovery-r1/pins.json').read_text())['bindings']:resolve(item['path'],item['sha256'])
 # Source-return/typed bridge paths are visible in actual fresh COFF decodes.
 objects=[final/f'native-{l}.obj' for l in ('O0','O2')]
 objects += [final/('build-'+l)/'CMakeFiles/mw34_numeric_native.dir/native.cpp.obj' for l in ('O0','O2')]
 objects += list((PRIVATE/'original-build-r5/build').rglob('reference.obj'))+list((PRIVATE/'original-build-r5/build').rglob('reference_x86.obj'))
 decodes=[]
 for i,obj in enumerate(objects):
  args=[llvm/'llvm-objdump.exe','--disassemble','--reloc','--x86-asm-syntax=intel',obj];r=subprocess.run(list(map(str,args)),capture_output=True);require(r.returncode==0,'Actual object decode failed');p=out/f'object-{i}.txt';p.write_bytes(r.stdout);(out/f'object-{i}.stderr').write_bytes(r.stderr);decodes.append({'object':bind(obj),'disassembly':bind(p),'command':list(map(str,args))});add(obj);add(p)
 add(ninja);add(llvm/'llvm-objdump.exe');add(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/lld-link.exe');add(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-mt.exe')
 reports=json.loads(comparison.read_text())['results'];result={'passed':True,'scope':'Author-reviewed standalone exact numeric-max initializer/provider prerequisite; independent review pending. Shared Runtime/MSVCP50 admission, full startup table and full M4 remain open.','final_build':bind(final/'build.json'),'actual_original_capture_report':bind(original/'report.json'),'final_comparison':bind(comparison),'causal_controls':bind(controls),'source_copies':literals,'actual_read_dependencies':dependency_rows,'historical_binding_resolutions':resolutions,'actual_COFF_decodes':decodes,'dependency_commands':commands,
 'counts':{'original_records':14688,'native_records':29376,'original_connected_checkpoints':7344,'ordered_native_events':352512,'native_call_RET_routes':29376,'compiled_context_controls':144,'original_protocol_checks':5,'actual_publisher_checks':6,'actual_worker_identity_denials':9,'recipe_no_mutation_checks':4,'observer_negatives':94,'observer_positives':12,'C1_directed_finite_each_level':9504,'C1_directed_observed_special_each_level':4320},
 'domain':'16 declared f32 words,12masked PC/RC CW,TOP0/7,contiguousdepth0/1/7,clean/DE/DE+PE,two repeats; canonical declared eight raw80 slots and fixed admitted mappings/frames; no arbitrary live-stack/exception priority/unmasked/overflow input credit',
 'checkpoint_provenance':'Literal actual stopped Windows x86 CONTEXT at INT3 continuation4C1A09 has EIP4C1A0A and zero FloatSave/FX metadata. Resume writes only CONTEXT_CONTROL. Direct leaf/wrapper FNSTENV remain hardware observations. Native checkpoint metadata is explicitly paired-leaf + static no-FP-route inference; no direct checkpoint ENV claim.',
 'repairs':'Only two typed checked physical FTW push/pop commits plus DE sticky accumulation; zero numerical or C1 changes.',
 'defined_scope':'All integer GPR/flags preserved apart from real frame/EIP; physical/logical tags, core exceptions and legacy metadata in bounded domain. Finite exact C1=0 subset only; C0/C2/C3,specialC1 and empty storage remain observations. Original State/events unobserved; native entireState and orderedevents independently projected against actual observations/source schedule.',
 'publication_scope':'Fresh sequential private ordinary directories with exclusive CREATE_NEW stage and no-replace publication; production concurrency/reparse exclusions remain.',
 'preserved_failures':['original-r1-normal-windows','original-r2-normal-windows','original-r3-normal-windows','original-r4-normal-windows','baseline-r1','baseline-comparison-r1'],'full_M4_complete':False,'physical_bindings_before_report':len(files),'current_literal_sources':len(literals)}
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');add(out/'report.json')
 for p in out.rglob('*'):
  if p.is_file():add(p)
 (out/'pins.json').write_text(json.dumps({'schema_version':1,'bindings':list(sorted(files.values(),key=lambda x:x['path'].casefold()))},indent=2)+'\n');print(json.dumps({'passed':True,'report':bind(out/'report.json'),'pins':bind(out/'pins.json'),'bindings':len(files),'literal_sources':len(literals),'dependencies':len(dependencies)}))
if __name__=='__main__':main()
