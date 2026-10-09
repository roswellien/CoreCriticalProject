"""Additive actual worker/publisher/recipe controls, no compiled-source mutation."""
from pathlib import Path
import hashlib,json,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-fp-numeric-max-carry'
build=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();assert out.parent==BASE and not out.exists();out.mkdir()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
pins={};rows=[]
def bind(p):pins[str(Path(p).resolve())]=sha(p)
def snapshot(p):return {str(q.relative_to(p)):sha(q) for q in p.rglob('*') if q.is_file()}
def run(name,args,reason,fixture=None,result=None):
 before=snapshot(fixture) if fixture is not None else None
 r=subprocess.run(list(map(str,args)),capture_output=True,timeout=45);(out/(name+'.stdout')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr)
 assert r.returncode==1 and reason.encode() in r.stderr,(name,r.returncode,r.stderr)
 if fixture is not None:assert snapshot(fixture)==before,(name,'mutated preexisting evidence')
 if result is not None:assert not any((result/name).exists() for name in ('carry.bin','persistent.bin','replay.bin','controls.json','compiled-controls.json','canonical-controls.bin','canonical-controls.json'))
 rows.append(dict(name=name,arguments=list(map(str,args)),exit_code=r.returncode,diagnostic=reason,existing_fixture_unchanged=fixture is not None,result_absent=result is not None))
try:
 b=json.loads((build/'build.json').read_text(encoding='utf-8-sig'));assert b['passed'];bind(build/'build.json')
 game=ROOT/'MW3/Mech3.exe';provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL';bind(game);bind(provider)
 for info in b['builds']:
  level=info['level'];obj=Path(info['object']);bind(obj)
  for kind in ('carry','legacy'):
   exe=Path(info['worker'] if kind=='carry' else info['legacy_worker']);bind(exe);prefix=level+'-'+kind;mode=[] if kind=='carry' else ['--unit'];base=[exe,*mode,game,provider,obj];usage='Authored carry native' if kind=='carry' else 'Native integration --unit';fresh='Fresh carry output required' if kind=='carry' else 'Fresh native integration output directory'
   run(prefix+'-arguments',[exe],usage);run(prefix+'-unknown-mode',[exe,'--unknown',game,provider,obj,out/(prefix+'-unknown-result')],usage)
   run(prefix+'-missing-game',[exe,*mode,out/'absent-game',provider,obj,out/(prefix+'-game-result')],'Input unavailable')
   run(prefix+'-missing-provider',[exe,*mode,game,out/'absent-provider',obj,out/(prefix+'-provider-result')],'Input unavailable')
   run(prefix+'-missing-object',[exe,*mode,game,provider,out/'absent-object',out/(prefix+'-object-result')],'Input unavailable')
   fixture=out/(prefix+'-existing');fixture.mkdir();(fixture/'marker.bin').write_bytes(b'Preexisting evidence\x00\xff\x80');run(prefix+'-existing-result',base+[fixture],fresh,fixture)
   bad=out/(prefix+'-provider-mutated.dll');data=bytearray(provider.read_bytes());data[0]^=1;bad.write_bytes(data);result=out/(prefix+'-provider-identity-result');run(prefix+'-provider-identity',[exe,*mode,game,bad,obj,result],'Exact MSVCP50 image ownership required',result=result)
   bad=out/(prefix+'-game-mutated.exe');data=bytearray(game.read_bytes());data[0]^=1;bad.write_bytes(data);result=out/(prefix+'-game-identity-result');run(prefix+'-game-identity',[exe,*mode,bad,provider,obj,result],'Wrong M4 image identity',result=result)
   if kind=='legacy':
    bad=out/(prefix+'-original-empty.bin');bad.write_bytes(b'');result=out/(prefix+'-original-empty-result');run(prefix+'-original-identity',[exe,'--replay',game,provider,obj,bad,result],'Exact frozen original input stream identity',result=result)
    pub=out/(prefix+'-publisher');r=subprocess.run([str(exe),'--check-publication',str(pub)],capture_output=True,timeout=45);(out/(prefix+'-publisher.stdout')).write_bytes(r.stdout);(out/(prefix+'-publisher.stderr')).write_bytes(r.stderr);assert r.returncode==0,(prefix,r.stderr)
    items=list(pub.iterdir());assert len(items)==2 and all(p.read_bytes()==bytes((0x4d,0x57,0x33,0x34,0,0xff,0x80,0x42)) for p in items);rows.append(dict(name=prefix+'-publisher',exit_code=0,existing_output_and_stage_unchanged=True,files=list(map(str,items))))
 pwsh=Path('C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe');script=ROOT/'tools/m4-fp-numeric-max-carry/build_canonical.ps1';bind(pwsh);bind(script)
 prep=BASE/'native-preparation-canonical-r1';gate=sha(prep/'preparation.json');bind(prep/'preparation.json');fixtures=[]
 for mode in ('report','O0','O2'):
  name='canonical-recipe-admission-'+mode.lower()+'-r1';report=BASE/name;trees={lv:ROOT/f'build/m4-nmx-carry-canonical-{name}-{lv}' for lv in ('O0','O2')};fixture=report if mode=='report' else trees[mode]
  assert not report.exists() and not any(p.exists() for p in trees.values());fixture.mkdir();(fixture/'marker.bin').write_bytes(b'Partial attempt retained\x00\xff');fixtures.append(fixture)
  run('recipe-'+mode,[pwsh,'-NoProfile','-ExecutionPolicy','Bypass','-File',script,'-OutputDirectory',report,'-PreparationDirectory',prep,'-PreparationSHA256',gate],'Entire report/all derived builds must be fresh before mutation',fixture)
  assert all(p.exists()==(p==fixture) for p in (report,*trees.values()))
 for p in out.rglob('*'):
  if p.is_file():bind(p)
 for directory in fixtures:
  for p in directory.rglob('*'):
   if p.is_file():bind(p)
 bind(__file__);(out/'checker-source.py').write_bytes(Path(__file__).read_bytes());bind(out/'checker-source.py')
 report=dict(passed=True,worker_denials=34,actual_publisher_preservation_checks=4,recipe_no_mutation_controls=3,rows=rows,scope='Final canonical worker native-only/offline admission and sequential ordinary private-path publication; no original process, concurrency or reparse credit',frozen_compiled_sources_changed=False,original_executed=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':pins},indent=2)+'\n');print(json.dumps(dict(passed=True,denials=34,publisher=4,recipe=3,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'))))
except BaseException:
 (out/'failure.txt').write_text(traceback.format_exc());(out/'failed-checker-source.py').write_bytes(Path(__file__).read_bytes());raise
