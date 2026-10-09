"""Execute only isolated hash-bound filename workers using frozen original BEFORE projections."""
import hashlib,json,pathlib,subprocess,sys,time,traceback
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-filename'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def main(build_name,out_name):
 build=BASE/build_name;out=BASE/out_name;assert not out.exists() and out.parent==BASE
 manifest=read(build/'build.json');assert manifest['passed'];files={str(pathlib.Path(__file__).resolve()):sha(__file__)}
 for category in ('sources','libraries','entry_objects','compiler_read_headers'):
  for p,h in manifest[category].items():assert sha(p)==h,p;files[p]=h
 out.mkdir();commands=[];passed=False;start=time.perf_counter()
 try:
  for level in ('O0','O2'):
   worker=pathlib.Path(manifest['workers'][level]);args=[str(worker),str(ROOT/'MW3/Mech3.exe'),str(ROOT/f'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-{level}.obj'),str(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'),str(ROOT/'reports/m4-crt-fdiv/native-derived-r1/pack.bin'),str(ROOT/'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin'),str(out/level)]
   for p in args[:-1]:files[p]=sha(p)
   began=time.perf_counter();cp=subprocess.run(args,capture_output=True,timeout=120)
   (out/f'{level}.stdout').write_bytes(cp.stdout);(out/f'{level}.stderr').write_bytes(cp.stderr)
   commands.append(dict(arguments=args,exit_code=cp.returncode,seconds=time.perf_counter()-began,stdout_sha256=sha(out/f'{level}.stdout'),stderr_sha256=sha(out/f'{level}.stderr')))
   assert cp.returncode==0 and(out/level/'COMPLETE').read_bytes()==b'COMPLETE'
   for index in range(36):
    r=read(out/level/f'row-{index}/result.json');assert r['passed'] and r['scenario']==index and r['control']==(0 if index<24 else index+37)
  for p,h in files.items():assert sha(p)==h,p
  passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  artifacts={str(p):sha(p)for p in out.rglob('*')if p.is_file()}
  report=dict(passed=passed,scope='Actual isolated native filename service plus literal builder continuation to uninitialized command-line producer, no game launch',build_path=str(build/'build.json'),build_sha256=sha(build/'build.json'),input_files=files,artifacts=artifacts,commands=commands,native_rows=72 if passed else 0,positive_sequences=48 if passed else 0,causal_negative_sequences=24 if passed else 0,seconds=time.perf_counter()-start,whole_M4_complete=False,original_executed=False,guest_TEB_LastError_written=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
  if passed:print(json.dumps({k:v for k,v in report.items()if k not in('input_files','artifacts','commands')}))
if __name__=='__main__':main(*sys.argv[1:])
