"""Reuse historical archive identities in local iterations; final union rehash required."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
HERE=Path(__file__).parent;ROOT=HERE.parents[1]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def one(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def main():
 build=(HERE/'build.py').read_text()
 build=one(build,'for pp,h in pins.items():assert sha(pp)==h,(pp,h)',"inherited_archives={pp:h for pp,h in pins.items() if Path(pp).suffix=='.mwb'}\n for pp,h in pins.items():\n  if pp not in inherited_archives:assert sha(pp)==h,(pp,h)")
 build=one(build,"for pp,h in sources.items():assert sha(pp)==h,('Source changed',pp)","for pp,h in sources.items():\n   if pp not in inherited_archives:assert sha(pp)==h,('Source changed',pp)")
 build=one(build,"'guest_executed':False,", "'inherited_capture_payload_hashes_reused':inherited_archives,'full_dependency_acceptance_rehash_required':True,'guest_executed':False,")
 run=(HERE/'run.py').read_text()
 run=one(run,'pins={};rows=[];passed=False;launched=0','pins={};inherited_archives={};rows=[];passed=False;launched=0')
 run=one(run,"for p,h in json.loads(pin(Path(buildpath).parent/'pins.json').read_bytes())['files'].items():pin(p,h)","for p,h in json.loads(pin(Path(buildpath).parent/'pins.json').read_bytes())['files'].items():\n   if Path(p).suffix=='.mwb':\n    assert len(h)==64 and all(c in '0123456789abcdef' for c in h) and Path(p).is_file();assert str(Path(p).resolve()) not in pins or pins[str(Path(p).resolve())]==h;inherited_archives[str(Path(p).resolve())]=h;pins[str(Path(p).resolve())]=h\n   else:pin(p,h)")
 run=one(run,'inputs=list(pins)', 'inputs=[p for p in pins if p not in inherited_archives]')
 run=one(run,"for p,h in pins.items():assert sha(p)==h,('Unchanged input',p)","for p,h in pins.items():\n    if p not in inherited_archives:assert sha(p)==h,('Unchanged input',p)")
 run=one(run,'initializer_credit=False,whole_M4_complete=False','inherited_capture_payload_hashes_reused=inherited_archives,full_dependency_acceptance_rehash_required=True,initializer_credit=False,whole_M4_complete=False')
 for name,s in [('build_v2.py',build),('run_v2.py',run)]:
  p=HERE/name;assert not p.exists();compile(s,str(p),'exec');p.write_text(s)
 out=ROOT/'reports/m4-joint-startup124/local-iteration-preparation-r1';assert not out.exists();out.mkdir(parents=True)
 r=dict(passed=True,scope='Local compile/execution reuse only; historical .mwb evidence is never read by native worker. Fresh worker outputs remain fully validated. Final acceptance must conflict-normalize and physically rehash all retained dependencies.',initializer_credit=False,full_dependency_acceptance_rehash_required=True,files={str(p.resolve()):sha(p) for p in [Path(__file__),HERE/'build.py',HERE/'run.py',HERE/'build_v2.py',HERE/'run_v2.py']})
 (out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main()
