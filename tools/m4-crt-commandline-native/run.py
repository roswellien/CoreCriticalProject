"""Explicit executable/common raw Windows command line; only child-local task env."""
import argparse,hashlib,json,os,pathlib,subprocess,sys
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main():
 a=argparse.ArgumentParser();a.add_argument('--original-build',type=pathlib.Path,required=True);a.add_argument('--native-build',type=pathlib.Path,required=True);a.add_argument('--output',type=pathlib.Path,required=True);args=a.parse_args()
 out=args.output.resolve();assert out.parent==ROOT/'reports/m4-crt-commandline-native' and not out.exists();out.mkdir()
 ob=json.loads(args.original_build.read_text(encoding='utf-8-sig'));nb=json.loads(args.native_build.read_text(encoding='utf-8-sig'));assert ob['passed'] and nb['passed']
 original=pathlib.Path(ob['worker']);native={level:pathlib.Path(nb['workers'][level]).with_name('commandline_native.exe') for level in ('O0','O2')}
 for build_path,b in ((args.original_build,ob),(args.native_build,nb)):
  for key in ('source_files','sources'):
   for p,h in b.get(key,{}).items():
    copied=build_path.parent/'sources'/pathlib.Path(p).relative_to(ROOT)
    assert copied.is_file() and sha(copied)==h,(p,'literal built source changed')
 fixtures=['MW34_CMD_FIXTURE','MW34_CMD_FIXTURE --plain alpha','"MW34 CMD FIXTURE" "two words" ""','MW34_CMD_FIXTURE\t--tabs\t" a b "','MW34_CMD_FIXTURE --slashes "C:\\logical\\path\\" back\\slash','MW34_CMD_FIXTURE --literal "%PATH%" "$()" "&|<>"','MW34_CMD_FIXTURE --long '+('ABc09_'*683),'MW34_CMD_FIXTURE --quoted \\"quoted\\" tail']
 commands=[];passed=False
 try:
  for index,fixture in enumerate(fixtures):
   for kind,exe in [('original',original),*native.items()]:
    env=os.environ.copy()
    env.update(MW34_CMN_GAME=str(ROOT/'MW3/Mech3.exe'),MW34_CMN_PROVIDER=str(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'),MW34_CMN_PACK=str(ROOT/'reports/m4-crt-commandline-native/static-r1/pack.bin'),MW34_CMN_OUTPUT=str(out/f'{kind}-{index}.bin'),MW34_CMN_SUPPLIED=fixture)
    env.pop('MW34_CMN_RESERVED_CHILD',None)
    # Windows Popen uses explicit lpApplicationName=executable and raw lpCommandLine.
    p=subprocess.run(fixture,executable=str(exe),env=env,cwd=ROOT,capture_output=True,timeout=180,stdin=subprocess.DEVNULL)
    log=out/f'{kind}-{index}.log';log.write_bytes(p.stdout+p.stderr)
    commands.append(dict(kind=kind,index=index,executable=str(exe),executable_sha256=sha(exe),supplied_logical_commandline=fixture,explicit_lpApplicationName=True,exit=p.returncode,log=str(log),log_sha256=sha(log),result=str(out/f'{kind}-{index}.bin')))
    assert p.returncode==0,(kind,index,p.returncode,p.stderr[-2000:])
  passed=True
 finally:
  (out/'capture.json').write_text(json.dumps(dict(passed=passed,commands=commands,scope='Actual original/native own OS bytes; common explicit logical inputs; no forced equality or connected startup',script_sha256=sha(__file__),input_builds={str(args.original_build.resolve()):sha(args.original_build),str(args.native_build.resolve()):sha(args.native_build)},files={str(p):sha(p) for p in out.iterdir() if p.is_file()}),indent=2))
if __name__=='__main__':main()
