"""Run the reviewed numeric worker's actual eight causal refusal seams."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,struct,subprocess,sys,time,traceback
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'reports/m4-hypot-native'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(build_path,build_sha,review_path,review_sha,name):
 assert re.fullmatch('fixture-refusals-r[1-9][0-9]*',name)
 out=AREA/name;assert not out.exists();out.mkdir();pins={};runs=[];counts=Counter();passed=False;began=time.perf_counter()
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower() not in('.mwb','.zip');v=sha(p);assert h is None or h==v,(p,h,v)
  assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def blob(p):return pin(p).read_bytes()
 try:
  review=read(review_path,review_sha);assert review['passed']
  build=read(build_path,build_sha);assert build['passed'] and set(build['workers'])=={'O0','O2'}
  assert review['files'][str(Path(build_path).resolve())]==build_sha
  for p,h in review['files'].items():pin(p,h)
  prep=read(build['preparation'],build['preparation_sha256']);assert prep['passed']
  for p,h in prep['files'].items():pin(p,h)
  inputs=read(prep['inputs'],prep['inputs_sha256']);assert inputs['passed'] and len(inputs['cases'])==6 and not inputs['numerical_results_seeded']
  first=inputs['cases'][0];assert first['sequence']==0
  pack=pin(first['pack'],first['pack_sha256']);states=pin(Path(prep['inputs']).parent/'input-state.bin')
  image=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
  catalog=['first read address','first access width','first read State PC','first CALL target','guest CW authority','control State identity','exception mask','literal return PC']
  for level in('O0','O2'):
   worker=pin(build['workers'][level]['path'],build['workers'][level]['sha256'])
   for mode,label in enumerate(catalog,1):
    native=out/f'{level}-{mode}';args=list(map(str,[worker,image,pack,states,0,native,mode]));start=time.perf_counter()
    r=subprocess.run(args,cwd=ROOT,capture_output=True,timeout=30,creationflags=0x08000000)
    (out/f'{level}-{mode}.stdout').write_bytes(r.stdout);(out/f'{level}-{mode}.stderr').write_bytes(r.stderr)
    run=dict(level=level,mode=mode,seam=label,argv=args,exit_code=r.returncode,process_closed=True,output=str(native),seconds=time.perf_counter()-start)
    runs.append(run);assert r.returncode==0 and(native/'COMPLETE.txt').is_file(),(level,mode,r.stderr)
    assert struct.unpack('<5I',blob(native/'result/status.bin'))==(mode,1,1,0,1)
    refusal=blob(native/'result/refusal.txt').decode();assert refusal
    before=native/'retry/before';after=native/'retry/after'
    b={p.relative_to(before).as_posix():p for p in before.rglob('*')if p.is_file()}
    a={p.relative_to(after).as_posix():p for p in after.rglob('*')if p.is_file()};assert b.keys()==a.keys()
    assert {'State.bin','CPU.bin','RuntimeCPU.bin','RuntimeFX.bin','context.bin','routes.bin','frames.bin','APIs.bin','accesses.bin'}<=b.keys()
    assert len([k for k in b if k.startswith('pages/')])==190
    assert len(blob(b['State.bin']))==3504 and len(blob(b['RuntimeFX.bin']))==512 and len(blob(b['context.bin']))==128
    for k in b:assert blob(b[k])==blob(a[k]),(level,mode,k);counts['whole_same_Runtime_retry_blocks']+=1
    private=struct.unpack('<16Q',blob(b['context.bin']));assert private[7]==1 and private[8]==0 and private[12:]==(private[13],private[13],private[14],private[15])
    # All context/State/Runtime identities are non-null and the active pointer
    # equals its exact Context during both snapshots; after retry cleanup is
    # separately attested by status[4].
    assert all(private[i]for i in(6,12,13,14,15))
    hw=blob(native/'host-hardware.bin');assert len(hw)==1632
    assert hw[:512]==hw[1088:1600],(level,mode,'full caller FX512')
    assert hw[512:540]==hw[1600:1628],(level,mode,'full caller ENV28')
    run.update(refusal=refusal,unchanged_retry_blocks=len(b),cursor=private[1],source_return_count=private[5],caller_FX512_restored=True,caller_ENV28_restored=True)
    counts['actual_poisoned_refusals']+=1;counts['same_Runtime_retry_refusals']+=1;counts['whole_caller_FX512_restorations']+=1;counts['whole_caller_ENV28_restorations']+=1
    print(json.dumps({k:run[k]for k in('level','mode','refusal','cursor','unchanged_retry_blocks')}),flush=True)
  pin(__file__);pin(sys.executable)
  for p,h in pins.items():assert sha(p)==h,p
  passed=True
 except BaseException:
  (out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  artifacts={str(p):sha(p)for p in out.rglob('*')if p.is_file()}
  report=dict(passed=passed,scope='Actual reviewed compiled numeric refusal seams and same poisoned Runtime retries',build=str(build_path),build_sha256=build_sha,review=str(review_path),review_sha256=review_sha,runs=runs,counts=dict(counts),files=pins,artifacts=artifacts,all_processes_closed=all(r['process_closed']for r in runs),archive_reader_opened=False,source_AFTER_seed=False,initializer_credit=0,seconds=time.perf_counter()-began)
  p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(p),closed_runs=len(runs),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4],sys.argv[5])
