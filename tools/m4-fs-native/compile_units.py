"""Compile the changed immutable native units without linking/running root109."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2]
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name,expected):
 prep=ROOT/'reports/m4-fs-native'/name
 assert sha(prep/'report.json')==expected
 out=ROOT/'reports/m4-fs-native'/('compile-'+name)
 assert not out.exists();out.mkdir()
 p=json.loads((prep/'report.json').read_text());pins=dict(p['files']);assert p['passed']
 for q,h in pins.items():assert sha(q)==h,q
 commands=[];objects={};passed=True
 for level in('O0','O2'):
  for source in('registry_library.cpp','crt_services.cpp'):
   output=out/(source[:-4]+'-'+level+'.obj')
   includes=[ROOT/'reports/m4-joint-startup103/preparation-r1',ROOT/'reports/m4-joint-startup103/preparation-r1'/level,prep,ROOT/'tools/m4-runtime',ROOT/'tools/m4-startup',ROOT/'runtime',ROOT/'tools/m4-fp-numeric-max',ROOT/'tools/m4-crt',ROOT/'tools/m4-crt-fdiv',ROOT/'tools/m4-crt-commandline-native',ROOT/'tools/m4-guest-cw']
   args=[str(LLVM/'clang-cl.exe'),'/nologo','/c','/std:c++20','/MD','/EHs','/Od'if level=='O0'else'/O2','/clang:-frounding-math','/DADDRESS_SIZE_BITS=32','/DHAS_FEATURE_AVX=0','/DHAS_FEATURE_AVX512=0','-Wno-invalid- offsetof'.replace('- offsetof','-offsetof')]
   args+=['/I'+str(i)for i in includes]+['-imsvc'+str(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/include'),'/FI'+str(ROOT/'reports/m4-joint-startup103/preparation-r1'/level/'registry_build_bindings.hpp'),'/Fo'+str(output),str(prep/source)]
   start=time.perf_counter();r=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=180);log=out/(source[:-4]+'-'+level+'.log');log.write_bytes(r.stdout+r.stderr)
   commands.append(dict(arguments=args,exit_code=r.returncode,log=str(log),elapsed_seconds=time.perf_counter()-start));passed=passed and r.returncode==0
   if output.exists():objects[str(output)]=sha(output)
   print(json.dumps(dict(level=level,source=source,exit_code=r.returncode)),flush=True)
   if r.returncode:print(r.stderr.decode(errors='replace')[-8000:]);break
  if not passed:break
 for q,h in pins.items():assert sha(q)==h,q
 report=dict(passed=passed,scope='Changed unit COFF compilation only with inherited103 build bindings; no root109 link/run credit',preparation_sha256=expected,commands=commands,objects=objects,files=pins|{str(Path(__file__).resolve()):sha(__file__),str(LLVM/'clang-cl.exe'):sha(LLVM/'clang-cl.exe')})
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'))))
 if not passed:raise RuntimeError('Native unit compilation failed; preserve receipt')
if __name__=='__main__':main(*sys.argv[1:])
