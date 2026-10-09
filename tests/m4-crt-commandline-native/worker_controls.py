"""Actual worker source/identity and existing-output denials, serial private dirs."""
import hashlib,json,os,pathlib,subprocess,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main(out):
 out=pathlib.Path(out).resolve();assert out.parent==ROOT/'reports/m4-crt-commandline-native' and not out.exists();out.mkdir()
 ob=json.loads((ROOT/'reports/m4-crt-commandline-native/original-build-r3/build.json').read_text(encoding='utf-8-sig'));nb=json.loads((ROOT/'reports/m4-crt-commandline-native/native-build-r3/build.json').read_text(encoding='utf-8-sig'));workers={'original':pathlib.Path(ob['worker']),**{x:pathlib.Path(nb['workers'][x]).with_name('commandline_native.exe') for x in('O0','O2')}}
 originals={'GAME':ROOT/'MW3/Mech3.exe','PROVIDER':ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','PACK':ROOT/'reports/m4-crt-commandline-native/static-r1/pack.bin'}
 bad={}
 for key,p in originals.items():q=out/f'wrong-{key}.bin';b=bytearray(p.read_bytes());b[0]^=1;q.write_bytes(b);bad[key]=q
 rows=[];passed=False
 try:
  for kind,exe in workers.items():
   for mode in('GAME','PROVIDER','PACK','EXISTING_OUTPUT'):
    result=out/f'{kind}-{mode}.bin';env=os.environ.copy();env.pop('MW34_CMN_RESERVED_CHILD',None)
    env.update({f'MW34_CMN_{k}':str(bad[k] if k==mode else p) for k,p in originals.items()});env.update(MW34_CMN_OUTPUT=str(result),MW34_CMN_SUPPLIED='MW34_CMD_DENIAL')
    sentinel=b'Externally owned result sentinel survives worker denial\0'
    if mode=='EXISTING_OUTPUT':result.write_bytes(sentinel)
    before={str(p):sha(p) for p in out.iterdir() if p.is_file()};p=subprocess.run('MW34_CMD_DENIAL',executable=str(exe),env=env,cwd=ROOT,stdin=subprocess.DEVNULL,capture_output=True,timeout=180);assert p.returncode!=0,(kind,mode)
    for path,h in before.items():assert sha(path)==h,'Existing control evidence mutated'
    assert (result.read_bytes()==sentinel if mode=='EXISTING_OUTPUT' else not result.exists());assert not list(out.glob(result.name+'.cmd-stage-*'))
    log=out/f'{kind}-{mode}.log';log.write_bytes(p.stdout+p.stderr);rows.append(dict(kind=kind,mode=mode,exit=p.returncode,executable=str(exe),executable_sha256=sha(exe),log=str(log),log_sha256=sha(log),prior_files_preserved=len(before),result_or_sentinel_safe=True,stage_absent=True))
  passed=True
 finally:(out/'report.json').write_text(json.dumps(dict(passed=passed,rows=rows,scope='Actual12 worker denials and prior-file inventories; before-writer/query placement follows audited source, not independent API execution tracing',script_sha256=sha(__file__),files={str(p):sha(p) for p in out.iterdir() if p.is_file()}),indent=2))
if __name__=='__main__':main(sys.argv[1])
