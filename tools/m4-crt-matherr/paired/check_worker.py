"""Actual native-only CLI/publication and recipe no-mutation controls."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[3]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise AssertionError(m)
def inventory(p):return {str(x.resolve()):sha(x) for x in p.rglob('*') if x.is_file()}
def main():
 out=Path(sys.argv[1]).resolve();need(not out.exists(),'Fresh worker-control directory');out.mkdir(parents=True);(out/'checker-source.py').write_bytes(Path(__file__).read_bytes())
 build=ROOT/'reports/m4-crt-matherr/paired-native-build-r7';b=json.loads((build/'build.json').read_text(encoding='utf-8-sig'))
 inputs=[ROOT/'MW3/Mech3.exe',ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',ROOT/'reports/m4-crt-matherr/preparation-r1/source.bin'];original=ROOT/'reports/m4-crt-matherr/paired-original-r1-normal-windows/original.bin'
 altered=[]
 for j,p in enumerate([*inputs,original]):
  target=out/f'altered-{j}.bin';raw=bytearray(p.read_bytes());raw[-1]^=1;target.write_bytes(raw);altered.append(target)
 cases=[];passed=False
 try:
  for item in b['builds']:
   worker=Path(item['worker']);level=item['level'];base=['--replay',*map(str,inputs),str(original)]
   for case in range(10):
    dest=out/f'{level}-case-{case}.bin';args=base+[str(dest)];expected_before=None
    if case==0:args=[]
    elif case==1:args+=['extra']
    elif case in (2,3,4):args[case-1]=str(altered[case-2])
    elif case==5:args[4]=str(altered[3])
    elif case==6:args[1]=str(out/'missing-game.bin')
    elif case==7:dest.write_bytes(b'preserve-preexisting-output\x00\xff');expected_before=inventory(out)
    elif case==8:dest.mkdir();(dest/'marker.bin').write_bytes(b'preserve-preexisting-directory\x00\xff');expected_before=inventory(dest)
    elif case==9:args[3]=str(out/'missing-leaf.bin')
    p=subprocess.run([str(worker),*args],capture_output=True,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
    (out/f'{level}-case-{case}.stdout').write_bytes(p.stdout);(out/f'{level}-case-{case}.stderr').write_bytes(p.stderr)
    need(p.returncode==1 and bool(p.stderr),'Actual intended native denial/diagnostic')
    if case==7:need(dest.read_bytes()==b'preserve-preexisting-output\x00\xff','Preexisting output bytes survived')
    elif case==8:need(inventory(dest)==expected_before,'Preexisting directory marker survived')
    else:need(not dest.exists(),'Failed native worker published output')
    need(not list(out.glob('*.crt-stage-*')),'Worker retained no staging file')
    cases.append({'level':level,'case':case,'argv':[str(worker),*args],'exit_code':p.returncode,'output_published':False,'preexisting_preserved':case in (7,8),'stderr_sha256':sha(out/f'{level}-case-{case}.stderr')})
  # Entire output and each derived build directory are checked before mutations.
  pwsh=Path('C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
  recipe=ROOT/'tools/m4-crt-matherr/paired/build_native.ps1'
  guards=[]
  for case in range(3):
   name=f'paired-fresh-directory-control-r1-{case}';report=ROOT/'reports/m4-crt-matherr'/name;trees=[ROOT/'build'/f'm4-crt-matherr-paired-{name}-{level}' for level in ('O0','O2')]
   fixture=report if case==0 else trees[case-1];need(not fixture.exists() and not report.exists() and all(not t.exists() for t in trees),'Guard fixtures must be new');fixture.mkdir(parents=True);(fixture/'marker.bin').write_bytes(b'partial-evidence-owned-before-invocation\x00\xff');before=inventory(fixture)
   p=subprocess.run([str(pwsh),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(recipe),'-OutputDirectory',str(report)],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
   (out/f'guard-{case}.stdout').write_bytes(p.stdout);(out/f'guard-{case}.stderr').write_bytes(p.stderr)
   need(p.returncode==1 and inventory(fixture)==before,'Fresh directory admission caused no mutation')
   need(all(t==fixture or not t.exists() for t in [report,*trees]),'Denied recipe created other output/build tree')
   guards.append({'case':case,'fixture':str(fixture),'unchanged_marker_sha256':sha(fixture/'marker.bin'),'exit_code':p.returncode,'stdout_sha256':sha(out/f'guard-{case}.stdout'),'stderr_sha256':sha(out/f'guard-{case}.stderr')})
  passed=True
 except Exception as e:(out/'failure.txt').write_text(str(e)+'\n');raise
 finally:
  report={'passed':passed,'scope':'Actual native worker and recipe denials only; no original process and callback data never invoked','worker_controls':cases,'fresh_directory_controls':locals().get('guards',[]),'workers':{i['worker']:sha(i['worker']) for i in b['builds']},'original_read_only_sha256':sha(original)}
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files=inventory(out);files.update({str(p):sha(p) for p in [Path(__file__),build/'build.json',ROOT/'tools/m4-crt-matherr/paired/build_native.ps1']});files.update({i['worker']:sha(i['worker']) for i in b['builds']});
  for g in locals().get('guards',[]):files.update(inventory(Path(g['fixture'])))
  (out/'pins.json').write_text(json.dumps({'files':files},indent=2)+'\n')
 print(json.dumps({'passed':True,'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json'),'worker_controls':len(cases),'recipe_controls':len(guards)}))
if __name__=='__main__':main()
