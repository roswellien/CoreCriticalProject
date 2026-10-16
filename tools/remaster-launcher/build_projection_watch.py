"""Build an isolated, fully observed original-code list for projection testing.

Uses the retained launcher's exact ordered object membership. Original lifts,
retained optimized objects and public launcher files are never modified.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import argparse, hashlib, json, os, sys, time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-crt-heap-carry'))
import inline_objects as recipe
import codec_timing, ir_cleanup, merge_x87
from apply_projection_bypass import transform as bypass
from flat_projection_watch import watched_flat_mem

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def build(task):
 out,original,stem,source=task;dst=out/stem.parent.name;dst.mkdir(parents=True,exist_ok=True)
 obj=dst/(stem.name+'-O2.obj');record=obj.with_suffix('.json');source_sha=sha(source)
 if obj.exists() and record.exists():
  r=json.loads(record.read_text())
  if r['source_sha256']!=source_sha or r['object_sha256']!=sha(obj):raise ValueError(f'Stale object {obj}')
  return r
 text,timing=codec_timing.transform(source.read_text())
 if stem.name=='m_53f2e0':text=bypass(text)
 text,cleanup=ir_cleanup.transform(text)
 ll=dst/(stem.name+'-watch.ll');cfg=ll.with_suffix('.cfg.ll');ll.write_text(text)
 recipe.run([recipe.LLVM/'opt.exe','-passes=simplifycfg','-S',ll,'-o',cfg])
 text,merged=merge_x87.transform(cfg.read_text());cfg.unlink()
 text,annotate=ir_cleanup.annotate(text);text,strict=ir_cleanup.strict_x87(text,False)
 watch={};text=watched_flat_mem(text,watch)
 if watch['flat_watch_unhandled_count']:raise ValueError(f'Unobserved accesses in {stem}: {watch}')
 ll.write_text(text);bc=ll.with_suffix('.bc');b1=ll.with_suffix('.o1.bc');b2=ll.with_suffix('.o2.bc');tmp=obj.with_suffix('.tmp.obj')
 recipe.run([recipe.LLVM/'llvm-link.exe','--only-needed','--internalize',ll,'-o',bc])
 recipe.run([recipe.LLVM/'opt.exe','-passes=default<O2>',bc,'-o',b1])
 recipe.run([recipe.LLVM/'opt.exe','-passes=dse,gvn,dse,instcombine<no-verify-fixpoint>,simplifycfg,dse',b1,'-o',b2])
 recipe.run([recipe.LLVM/'clang.exe','--target=x86_64-pc-windows-msvc','-O2','-c',b2,'-o',tmp])
 for old,new in recipe.renames_for(stem).items():recipe.run([recipe.LLVM/'llvm-objcopy.exe','--redefine-sym',old+'='+new,tmp])
 os.replace(tmp,obj)
 r={'original':str(original),'source':str(source),'source_sha256':source_sha,'object':str(obj),'object_sha256':sha(obj),'watch':watch,'strict':strict,'timing':timing}
 record.write_text(json.dumps(r,indent=1))
 for p in [ll,bc,b1,b2]:p.unlink()
 return r

def safe(task):
 try:return build(task)
 except Exception as e:return {'failed':str(task[2]),'error':str(e)}

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--out',type=Path,required=True)
 parser.add_argument('--objects',type=Path,default=ROOT/'local/remaster/gpu-native-perf-clean-r1/optimized-mfc-objects.txt')
 parser.add_argument('--jobs',type=int,default=8)
 parser.add_argument('--filter',default='')
 args=parser.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
 originals=[Path(s.strip()) for s in args.objects.read_text().splitlines() if s.strip()]
 stems={Path(s).name:Path(s) for s in (recipe.HERE/'mfc_objects.txt').read_text().splitlines() if s.strip()}
 tasks=[]
 for obj in originals:
  name=obj.name.removesuffix('-O2.obj');stem=stems.get(name,obj.parent/name)
  if args.filter and args.filter not in name:continue
  source=stem.parent/(name+'-host.ll')
  if not source.exists():raise FileNotFoundError(source)
  tasks.append((obj,stem,source))
 if not tasks:raise ValueError('No original objects selected')
 pins={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),Path(__file__).with_name('flat_projection_watch.py'),Path(__file__).with_name('apply_projection_bypass.py'),recipe.HERE/'ir_cleanup.py',recipe.HERE/'merge_x87.py',recipe.HERE/'codec_timing.py']}
 contract={'ordered_object_list_sha256':sha(args.objects),'tools':pins,'recipe':'cleanup, simplifycfg, merge_x87, annotate, strict_x87(noexc=false), watched_flat_mem, llvm-link only-needed internalize, default<O2>, dse/gvn/dse/instcombine/simplifycfg/dse, clang O2, recorded symbol renames','filter':args.filter}
 pin=out/'recipe.json'
 if pin.exists() and json.loads(pin.read_text())!=contract:raise ValueError('Existing output has a different recipe; use a new directory')
 pin.write_text(json.dumps(contract,indent=2))
 results=[];failures=[];start=time.monotonic()
 with ProcessPoolExecutor(max_workers=args.jobs) as pool:
  for r in pool.map(safe,[(out,*task) for task in tasks]):
   (failures if 'failed' in r else results).append(r)
   done=len(results)+len(failures)
   if done%100==0 or done==len(tasks):
    status={'done':done,'total':len(tasks),'failed':len(failures),'seconds':round(time.monotonic()-start,1)}
    (out/'progress.json').write_text(json.dumps(status));print(json.dumps(status),flush=True)
 report={'contract':contract,'objects':len(results),'failed':failures,'watch_totals':{k:sum(r['watch'].get(k,0) for r in results) for k in ['flat_reads','flat_writes','flat_watch_reads','flat_watch_writes','flat_watch_f80_reads','flat_watch_f80_writes','flat_watch_unhandled_count']}}
 (out/'report.json').write_text(json.dumps(report,indent=2))
 if failures:raise RuntimeError(f'{len(failures)} objects failed; see {out}/report.json')
 (out/'objects.txt').write_text('\n'.join(r['object'].replace('\\','/') for r in results)+'\n')

if __name__=='__main__':main()
