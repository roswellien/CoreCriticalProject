"""Rebuild the recompiled MFC-stage objects with the bridge fast paths inlined (fast_bridges.cpp).

For each lifted function listed in mfc_objects.txt this takes the existing <stem>-host.ll, redirects the hot
bridge calls (__remill_{read,write}_memory_{8,16,32,64,f32,f64}, __remill_fpu_exception_{clear,test}) to the
mw34_fast_* fast paths, links the fast-path bitcode (llvm-link --only-needed --internalize), and compiles it
with the original recipe (clang --target=x86_64-pc-windows-msvc -O2 -c), then applies the component's recorded
symbol renames (llvm-objcopy --redefine-sym). Outputs go to a separate tree (reports/m4-crt-attach/inline-r1);
the original lift reports and objects are never modified. Writes the object list for build.ps1 -Inline.
With --merge-x87, each host.ll first goes through opt -passes=simplifycfg and merge_x87.py (x87 exception brackets
merged across straight-line runs; see that file) before the redirect. With --cleanup, each host.ll first goes through
ir_cleanup.py (identity flag/compare helper calls, undefined representatives and 10-byte x87 slot copies; see that file).
Usage: inline_objects.py <out-dir> [stem-filter] [--jobs N] [--merge-x87] [--no-inline] [--cleanup [--strict-x87]]
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import merge_x87,ir_cleanup,codec_timing
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
BRIDGES=[f'read_memory_{s}' for s in ('8','16','32','64','f32','f64')]+[f'write_memory_{s}' for s in ('8','16','32','64','f32','f64')]+['fpu_exception_clear','fpu_exception_test']
PATTERN=re.compile(r'@__remill_('+'|'.join(BRIDGES)+r')\b')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run(args):
    cp=subprocess.run([str(a) for a in args],capture_output=True,timeout=600)
    if cp.returncode:raise RuntimeError(' '.join(map(str,args))+'\n'+cp.stderr.decode(errors='replace')[-2000:])
def renames_for(stem,cache={}):
    rep=Path(stem).parent/'report.json';comp=Path(stem).name
    if rep not in cache:cache[rep]=json.loads(rep.read_text(encoding='utf-8-sig')).get('components',{})
    return cache[rep].get(comp,{}).get('renames',{})
MERGE='--merge-x87' in sys.argv
NO_INLINE='--no-inline' in sys.argv  # merged IR compiled with the out-of-line bridges (no fast-path bitcode)
CLEANUP='--cleanup' in sys.argv
STRICT='--strict-x87' in sys.argv  # with --cleanup: ir_cleanup.strict_x87
FLAT='--flat-mem' in sys.argv  # guest loads/stores as flat base + address (ir_cleanup step 8; host flat GuestMemory)
NOEXC='--x87-noexc' in sys.argv  # with --strict-x87: no x87 exception tracking in game-image bodies (ir_cleanup step 7)
def game_body(stem):
    m=re.match(r'm_([0-9a-f]+)$',Path(stem).name);return bool(m) and 0x401000<=int(m.group(1),16)<0x5bb000
def build(stem,out,fast):
    stem=Path(stem);dst=out/stem.parent.name;dst.mkdir(parents=True,exist_ok=True)
    obj=dst/(stem.name+'-O2.obj')
    if obj.exists():return str(obj),'kept',None
    stats=None;source=stem.parent/(stem.name+'-host.ll');cstats=None
    # Clock-observed codec work must survive every optimization recipe, even
    # when ordinary IR cleanup is disabled. Rebuild into a fresh output tree.
    text,timing_stats=codec_timing.transform(source.read_text())
    timing_source=None
    if CLEANUP:
        text,cstats=ir_cleanup.transform(text);source=dst/(stem.name+'-clean.ll');source.write_text(text)
    elif timing_stats['codec_timing_preserved']:
        source=timing_source=dst/(stem.name+'-timing.ll');source.write_text(text)
    if MERGE:
        cfg=dst/(stem.name+'-cfg.ll')
        run([LLVM/'opt.exe','-passes=simplifycfg','-S',source,'-o',cfg])
        text,stats=merge_x87.transform(cfg.read_text());cfg.unlink()
    else:text=source.read_text()
    if CLEANUP:
        source.unlink();text,astats=ir_cleanup.annotate(text);cstats|=astats
        if STRICT:text,sstats=ir_cleanup.strict_x87(text,NOEXC and game_body(stem));cstats|=sstats
        if FLAT:fst={};text=ir_cleanup.flat_mem(text,fst);cstats|=fst
    ll=dst/(stem.name+'-inline.ll');bc=dst/(stem.name+'-inline.bc')
    ll.write_text(text if NO_INLINE else PATTERN.sub(lambda m:'@mw34_fast_'+m.group(1),text))
    run([LLVM/'llvm-link.exe','--only-needed','--internalize',ll,'-o',bc] if NO_INLINE else [LLVM/'llvm-link.exe','--only-needed','--internalize',ll,fast,'-o',bc])
    tmp=obj.with_suffix('.tmp.obj')
    if CLEANUP:  # extra rounds: the -O2 pipeline runs DSE once, before later passes expose the dead State stores
        b1,b2=bc.with_suffix('.o1.bc'),bc.with_suffix('.o2.bc')
        run([LLVM/'opt.exe','-passes=default<O2>',bc,'-o',b1]);run([LLVM/'opt.exe','-passes=dse,gvn,dse,instcombine<no-verify-fixpoint>,simplifycfg,dse',b1,'-o',b2])
        run([LLVM/'clang.exe','--target=x86_64-pc-windows-msvc','-O2','-c',b2,'-o',tmp]);b1.unlink();b2.unlink()
    else:run([LLVM/'clang.exe','--target=x86_64-pc-windows-msvc','-O2','-c',bc,'-o',tmp])
    for old,new in renames_for(stem).items():run([LLVM/'llvm-objcopy.exe','--redefine-sym',old+'='+new,tmp])
    ll.unlink();bc.unlink();os.replace(tmp,obj)
    if timing_source:timing_source.unlink()
    return str(obj),'built',(stats or {})|(cstats or {})|timing_stats
def main():
    out=Path(sys.argv[1]).resolve();filt=sys.argv[2] if len(sys.argv)>2 and not sys.argv[2].startswith('--') else ''
    jobs=int(sys.argv[sys.argv.index('--jobs')+1]) if '--jobs' in sys.argv else os.cpu_count()
    out.mkdir(parents=True,exist_ok=True)
    src=HERE/'fast_bridges.cpp';fast=out/'fast.bc'
    run([LLVM/'clang.exe','--target=x86_64-pc-windows-msvc','-std=c++20','-O2','-fexceptions','-fcxx-exceptions','-emit-llvm','-c',src,'-I',HERE,'-o',fast])
    stems=[l.strip() for l in (HERE/'mfc_objects.txt').read_text().splitlines() if l.strip()]
    if filt:stems=[s for s in stems if filt in s]
    done=0;failed=[];totals=dict(brackets=0,mergeable=0,runs=0,merged=0,identity_calls=0,undefined_calls=0,fp80_copies=0,kept_calls=0,nounwind_bridges=0,uwtable_bodies=0,classify_ueq0=0,classify_inf=0,classify_lt=0,constrained=0,fences=0,strict_applied=0,codec_timing_preserved=0)
    with ThreadPoolExecutor(jobs) as ex:
        for f,stem in zip(ex.map(lambda s:_safe(s,out,fast),stems),stems):
            done+=1
            if isinstance(f,Exception):failed.append((stem,str(f)[:600]))
            elif f[2]:
                for k in totals:totals[k]+=f[2].get(k,0)
            if done%500==0:print(json.dumps(dict(progress=done,total=len(stems),failed=len(failed))),flush=True)
    objs=[str(Path(out/Path(s).parent.name/Path(s).name)).replace('\\','/') for s in stems]
    (out/'mfc_objects_inline.txt').write_text('\n'.join(objs)+'\n')
    rep=dict(objects=len(stems),failed=failed,fast_bridges_cpp_sha256=sha(src),fast_gate_hpp_sha256=sha(HERE/'fast_gate.hpp'),fast_bc_sha256=sha(fast),
             recipe='host.ll with bridge calls redirected to mw34_fast_*; llvm-link --only-needed --internalize fast.bc; clang --target=x86_64-pc-windows-msvc -O2 -c; recorded llvm-objcopy renames',
             originals_modified=False,inlined_fast_paths=not NO_INLINE,codec_timing_py_sha256=sha(HERE/'codec_timing.py'),codec_timing_preserved=totals['codec_timing_preserved'],merge_x87=MERGE,merge_x87_py_sha256=sha(HERE/'merge_x87.py') if MERGE else None,x87_merge_totals=totals if MERGE else None,
             cleanup=CLEANUP,ir_cleanup_py_sha256=sha(HERE/'ir_cleanup.py') if CLEANUP else None,cleanup_totals={k:totals[k] for k in ('identity_calls','undefined_calls','fp80_copies','kept_calls','nounwind_bridges','uwtable_bodies','classify_ueq0','classify_inf','classify_lt','constrained','fences','strict_applied')} if CLEANUP else None,strict_x87=STRICT,
             cleanup_recipe='ir_cleanup.transform before simplifycfg+merge_x87, ir_cleanup.annotate after; opt default<O2>, opt dse,gvn,dse,instcombine<no-verify-fixpoint>,simplifycfg,dse, clang -O2 -c' if CLEANUP else None)
    (out/'report.json').write_text(json.dumps(rep,indent=1)+'\n');print(json.dumps(dict(objects=len(stems),failed=len(failed))))
    if failed:sys.exit(1)
def _safe(s,out,fast):
    try:return build(s,out,fast)
    except Exception as e:return e
if __name__=='__main__':main()
