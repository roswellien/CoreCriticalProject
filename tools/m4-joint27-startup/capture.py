"""Exact reviewed owned-byte native workers only; no original/UI execution."""
from pathlib import Path
import hashlib,json,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-joint27-startup'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=Path(sys.argv[1]).resolve();assert out.parent==BASE and not out.exists();out.mkdir()
build=BASE/'build-only-r1';receipt=build/'build.json';assert sha(receipt)=='695be2d5fc34e6f134a076f1457a2687867c9d3f13e07e0bfcbd9ddcbc25f5b5';b=json.loads(receipt.read_text());assert b['passed']and not b['worker_executed']
review=BASE/'root-preflight-r4/report.json';assert sha(review)=='38256df58f1f3a20c33e39b63210d39cee52fca277e44e358fce631ac95e08fc'
game=ROOT/'MW3/Mech3.exe';provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL';assert sha(game)=='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf';assert sha(provider)=='91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a'
bindings={str(receipt):sha(receipt),str(review):sha(review),str(review.with_name('pins.json')):sha(review.with_name('pins.json')),str(game):sha(game),str(provider):sha(provider),str(Path(__file__).resolve()):sha(__file__)}
for key in ('sources','tools','artifacts'):
 for p,h in b[key].items():assert sha(p)==h,(p,h);bindings[p]=h
commands=[]
for level in ('O0','O2'):
 exe=Path(b['workers'][level]);assert sha(exe)==b['artifacts'][str(exe)];commands.append(dict(level=level,arguments=[str(exe),str(game),str(provider),str(out/level)],worker_sha256=sha(exe)))
copy=out/'runner-source.py';copy.write_bytes(Path(__file__).read_bytes());bindings[str(copy)]=sha(copy)
recipe=dict(scope='Exact reviewed native owned GuestMemory container workers, fresh normalWindows directories; no original game/DLL initialization/UI',build_sha256=sha(receipt),root_preflight_sha256=sha(review),commands=commands,pre_execution_bindings=bindings,original_executed=False)
(out/'sealed-runner-recipe.json').write_text(json.dumps(recipe,indent=2)+'\n');recipe_sha=sha(out/'sealed-runner-recipe.json');(out/'sealed-runner-pins.json').write_text(json.dumps({'files':bindings,'recipe_sha256':recipe_sha},indent=2)+'\n')
results=[];failure=None
try:
 for c in commands:
  r=subprocess.run(c['arguments'],capture_output=True,timeout=180);(out/(c['level']+'.stdout')).write_bytes(r.stdout);(out/(c['level']+'.stderr')).write_bytes(r.stderr);results.append(dict(**c,exit_code=r.returncode,stdout=str(out/(c['level']+'.stdout')),stderr=str(out/(c['level']+'.stderr'))));assert r.returncode==0,(c['level'],r.returncode,r.stderr.decode(errors='replace'));print(json.dumps(dict(level=c['level'],exit_code=r.returncode)),flush=True)
 for p,h in bindings.items():assert sha(p)==h,('Input changed during capture',p)
except BaseException:
 failure=traceback.format_exc();(out/'failure.txt').write_text(failure);print(failure,flush=True)
finally:
 pins=dict(bindings)
 for p in out.rglob('*'):
  if p.is_file():pins[str(p.resolve())]=sha(p)
 report=dict(passed=failure is None,failure=failure,runner_recipe_sha256=recipe_sha,commands=results,actual_native_phases=2592 if failure is None else None,actual_complete_sequences=96 if failure is None else None,scope='Actual candidate native27 execution only; independent raw/fault/firstrefusal tests required before admission',original_executed=False,whole_M4_complete=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':pins},indent=2)+'\n');print(json.dumps(dict(passed=failure is None,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'))))
if failure:raise SystemExit(1)
