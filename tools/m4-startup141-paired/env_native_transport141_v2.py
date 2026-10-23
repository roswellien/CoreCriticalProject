"""Static review: native141 worker writes no host x87 metadata into guest State (v2).

v2 tightens v1 classification (v1 retained as failed): buffer `.data()`
destinations are State reads; every x87 write inside seed.hpp seed() is the epoch
input seed; execution.hpp copies are admitted only when that header is not
compiled into the r3 worker or no compiled TU calls initialize/execute.

Scans every source in the native141 build lineage (build-r3 files map) for
(a) writes to guest State x87 legacy metadata/FX members and (b) whole-State
copies. Every hit must match one reviewed class:
 - bootstrap seed from the genuine epoch input (seed.hpp);
 - numeric adapter FX copy that saves AND restores the 18 legacy metadata bytes;
 - unused static header helper (initialize/execute) with no call site in any
   compiled worker translation unit;
 - fixture/ancestor file not in the worker CMake source list;
 - whole-State copy whose destination is a record/snapshot (read of State).
Any unclassified hit fails. Emulated x87 instruction semantics (the only
runtime metadata writer) are not modified by this review. No credit.
"""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
BUILD=('reports/m4-startup141-runway/build-r3/build.json','ba1f699354fc2a14eb5dcc3bbfa4497e9ceb4ce01786e75cd95430f6c58de1bc')
ASSIGN=re.compile(r'x87\.fxsave\.(ip|dp|fop|cs|ds)(\.flat|\.dword)?\s*(=[^=]|\+=|\|=|&=)|memcpy\s*\(\s*&\s*[\w\.\->]*\.x87')
WHOLE=re.compile(r'memcpy\s*\(\s*(&\s*[\w\.\->]*(state|s_|\bs\b)[\w\.\->]*|[\w\.\->]*state[\w\.\->]*\.data\(\))\s*,[^;]*(3504|sizeof\s*\(\s*(State|s|state)\s*\))')
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 assert re.fullmatch('[A-Za-z0-9_-]{1,90}',name);out=R/'reports/m4-startup141-paired'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(str(p),v,h);assert pins.setdefault(str(p),v)==v;return p
 pin(__file__);B=json.loads(pin(R/BUILD[0],BUILD[1]).read_bytes());assert B['passed']is True
 files={str(Path(p).resolve()):h for p,h in B['files'].items()};src=[p for p in files if p.lower().endswith(('.cpp','.hpp','.inc','.h','.c'))]
 for p in src:pin(p,files[p])
 prep=(R/'reports/m4-startup141-runway/preparation-r3').resolve();cm=(prep/'CMakeLists.txt').read_text();pin(prep/'CMakeLists.txt',files.get(str(prep/'CMakeLists.txt')))
 compiled_tus=[str((prep/x).resolve())for x in('native_main.cpp','connected_component.cpp','derived/chain/runtime_adapter.cpp','derived/integer/runtime_adapter.cpp','chain_dispatch.cpp')]
 for t in compiled_tus:assert Path(t).name in cm and str(Path(t))in files,'Compiled worker TU in lineage: '+t
 tu_text='\n'.join(Path(t).read_text(errors='replace')for t in compiled_tus)
 compiled_headers={str((prep/'derived/chain/execution.hpp').resolve()),str((prep/'derived/integer/execution.hpp').resolve()),str((R/'tools/m4-initializer-chain/execution.hpp').resolve())}
 assert all(h in files for h in compiled_headers)
 classified=[];unclassified=[]
 for p in src:
  lines=Path(p).read_text(errors='replace').splitlines()
  for i,l in enumerate(lines,1):
   a=ASSIGN.search(l);w=WHOLE.search(l)
   if not(a or w):continue
   rel=p.split('MW34Recomp')[-1];cls=None
   if w and not a:
    dest=w.group(1)
    if dest.endswith('.data()')and not dest.startswith('&'):cls='whole_State_read_into_buffer'
   elif p.endswith('seed.hpp')and('in.env.data()'in l or'in.fx.data()'in l):cls='bootstrap_epoch_input_seed'
   elif p.endswith('runtime_adapter.cpp')and'memcpy(&s.x87,fx.data(),512)'in l.replace(' ',''):
    ctx='\n'.join(lines[max(0,i-3):i+3]).replace(' ','')
    if'if(seeded)std::memcpy(legacy_metadata.data(),reinterpret_cast<std::byte*>(&s.x87)+6'in ctx and'if(seeded)std::memcpy(reinterpret_cast<std::byte*>(&s.x87)+6,legacy_metadata.data()'in ctx:cls='adapter_copy_preserving_legacy_metadata'
   elif p.endswith('execution.hpp')and'memcpy(&s.x87,q.fx.data(),512)'in l.replace(' ',''):
    if p not in compiled_headers:cls='header_not_compiled_into_r3_worker'
    elif not re.search(r'\b(initialize\s*\(\s*s\s*,|execute\s*\(\s*(q|request)\b|execute_state\s*\()',tu_text):cls='unused_static_initialize_helper'
   elif'native-preparation-canonical-r1'in p and Path(p).name=='native.cpp'and'native-preparation-canonical-r1'not in cm:cls='fixture_not_in_worker_sources'
   (classified if cls else unclassified).append(dict(file=rel,line=i,text=l.strip()[:200],cls=cls))
 for p_,h in list(pins.items()):assert sha(p_)==h
 rp=out/'transport-review.json';rp.write_text(json.dumps(dict(classified=classified,unclassified=unclassified),indent=1)+'\n');pin(rp);pin(sys.executable)
 counts={}
 for c in classified:counts[c['cls']]=counts.get(c['cls'],0)+1
 report=dict(passed=not unclassified,scope='Static native141 lineage review: guest x87 metadata written only by bootstrap seed, emulated instructions and metadata-preserving adapter copy; no host metadata transport. Supports the ENV last-writer relation; no ENV policy admission or credit',
  lineage_sources=len(src),hits=len(classified)+len(unclassified),classified=counts,unclassified=len(unclassified),output=dict(path=str(rp),sha256=pins[str(rp.resolve())]),initializer_credit=0,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in('passed','lineage_sources','hits','classified','unclassified')}))
 if unclassified:print(json.dumps(unclassified[:10],indent=1));raise SystemExit(1)
if __name__=='__main__':main(sys.argv[1])
