"""Actual final native worker and fresh-recipe filesystem admission controls."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
build=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();assert out.parent==ROOT/'reports/m4-fp-numeric-max-integration' and not out.exists();out.mkdir()
b=json.loads((build/'build.json').read_text(encoding='utf-8-sig'));assert b['passed'];pins={};rows=[]
def bind(p):pins[str(Path(p).resolve())]=sha(p)
def snapshot(p):return {str(q.relative_to(p)):sha(q) for q in p.rglob('*') if q.is_file()}
def run(name,args,reason,fixture=None,result=None):
 before=snapshot(fixture) if fixture is not None else None
 r=subprocess.run([str(x) for x in args],capture_output=True,timeout=45);(out/(name+'.stdout')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr)
 assert r.returncode==1 and reason.encode() in r.stderr,(name,r.returncode,r.stderr)
 if fixture is not None:assert snapshot(fixture)==before,(name,'changed existing evidence')
 if result is not None:assert not (result/'persistent.bin').exists() and not (result/'replay.bin').exists() and not (result/'controls.json').exists()
 rows.append({'name':name,'arguments':list(map(str,args)),'exit_code':r.returncode,'diagnostic':reason,'existing_fixture_unchanged':fixture is not None,'result_absent':result is not None})
for info in b['builds']:
 level=info['level'];exe=Path(info['worker']);obj=Path(info['object']);bind(exe);bind(obj)
 game=ROOT/'MW3/Mech3.exe';provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL';base=[exe,'--unit',game,provider,obj]
 run(level+'-bad-arguments',[exe],'Native integration --unit')
 run(level+'-unknown-mode',[exe,'--unknown',game,provider,obj,out/(level+'-unknown-result')],'Native integration --unit')
 run(level+'-missing-game',[exe,'--unit',out/'absent-game',provider,obj,out/(level+'-missing-game-result')],'Input unavailable')
 run(level+'-missing-provider',[exe,'--unit',game,out/'absent-provider',obj,out/(level+'-missing-provider-result')],'Input unavailable')
 run(level+'-missing-object',[exe,'--unit',game,provider,out/'absent-object',out/(level+'-missing-object-result')],'Input unavailable')
 fixture=out/(level+'-existing-result');fixture.mkdir();(fixture/'marker.bin').write_bytes(b'Prior evidence\x00\xff\x80')
 run(level+'-existing-result',base+[fixture],'Fresh native integration output directory',fixture)
 bad=out/(level+'-provider-mutated.dll');raw=bytearray(provider.read_bytes());raw[0]^=1;bad.write_bytes(raw);result=out/(level+'-provider-mutated-result');run(level+'-provider-identity',[exe,'--unit',game,bad,obj,result],'Exact MSVCP50 image ownership required',result=result)
 bad=out/(level+'-game-mutated.exe');raw=bytearray(game.read_bytes());raw[0]^=1;bad.write_bytes(raw);result=out/(level+'-game-mutated-result');run(level+'-game-identity',[exe,'--unit',bad,provider,obj,result],'Wrong M4 image identity',result=result)
 bad=out/(level+'-original-empty.bin');bad.write_bytes(b'');result=out/(level+'-original-empty-result');run(level+'-original-identity',[exe,'--replay',game,provider,obj,bad,result],'Exact frozen original input stream identity',result=result)
 # Actual final worker exercised CREATE_NEW publisher twice during final recipe.
 pub=build/f'publication-{level}';items=list(pub.iterdir());assert len(items)==2
 for p in items:assert p.read_bytes()==bytes((0x4d,0x57,0x33,0x34,0,0xff,0x80,0x42));bind(p)
 rows.append({'name':level+'-two-publisher-sentinels','actual_final_worker':True,'existing_output_and_stage_survived':True,'files':list(map(str,items))})
pwsh=Path('C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe');script=ROOT/'tools/m4-fp-numeric-max-integration/build.ps1';bind(pwsh);bind(script)
for mode in ('report','O0','O2'):
 name='recipe-admission-'+mode.lower()+'-r1';report=out.parent/name;trees={lv:ROOT/f'build/m4-nmx-integration-{name}-{lv}' for lv in ('O0','O2')};fixture=report if mode=='report' else trees[mode]
 assert not report.exists() and not any(p.exists() for p in trees.values());fixture.mkdir();(fixture/'marker.bin').write_bytes(b'Partial attempt retained\x00\xff')
 run('recipe-'+mode,[pwsh,'-NoProfile','-ExecutionPolicy','Bypass','-File',script,'-OutputDirectory',report],'Entire report/all derived builds must be fresh before mutation',fixture)
 assert all(p.exists()==(p==fixture) for p in (report,*trees.values()))
for p in out.rglob('*'):
 if p.is_file():bind(p)
for name in ('recipe-admission-report-r1','recipe-admission-o0-r1','recipe-admission-o2-r1'):
 for p in (out.parent/name,*(ROOT/f'build/m4-nmx-integration-{name}-{lv}' for lv in ('O0','O2'))):
  if p.exists():
   for q in p.rglob('*'):
    if q.is_file():bind(q)
bind(build/'build.json');bind(__file__);(out/'checker-source.py').write_bytes(Path(__file__).read_bytes());bind(out/'checker-source.py')
report={'passed':True,'worker_denials':18,'actual_publisher_preservation_checks':4,'recipe_no_mutation_controls':3,'rows':rows,'scope':'Final native worker and sequential ordinary private-path output/recipe admission only; no original process run; concurrent publication and reparse points excluded','original_executed':False}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bind(out/'report.json');(out/'pins.json').write_text(json.dumps({'files':pins},indent=2)+'\n');print(json.dumps(report))
