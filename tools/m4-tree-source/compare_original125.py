"""Serialize six bounded original source cases and seal their aggregate proof."""
from pathlib import Path
import collections,hashlib,json,subprocess,sys,traceback
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=ROOT/'reports/m4-tree-source'/name;assert not out.exists();out.mkdir(parents=True);passed=False;files={};counts=collections.Counter();cases=[]
 try:
  for sequence in range(6):
   case=name+'-sequence-'+str(sequence);r=subprocess.run([sys.executable,'-B',str(ROOT/'tools/m4-tree-source/compare_original125_prefix.py'),case,'tools/m4-tree-source/game_model_v4.py',str(sequence)],cwd=ROOT,capture_output=True,creationflags=0x08000000);(out/f'sequence-{sequence}.stdout').write_bytes(r.stdout);(out/f'sequence-{sequence}.stderr').write_bytes(r.stderr);assert r.returncode==0,(sequence,r.stderr.decode())
   receipt=ROOT/'reports/m4-tree-source'/case/'report.json';report=json.loads(receipt.read_bytes());assert report['passed'];files[str(receipt.resolve())]=sha(receipt);cases.append(dict(sequence=sequence,receipt=str(receipt),sha256=sha(receipt)));counts.update(report['counts']);print(json.dumps(dict(sequence=sequence,passed=True)),flush=True)
  for p in(ROOT/'tools/m4-tree-source/compare_original125_prefix.py',ROOT/'tools/m4-tree-source/game_model_v4.py',Path(__file__)):files[str(p.resolve())]=sha(p)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Six genuine original125 tree phases reconstructed literally from their own actual carried BEFORE and finite API leaves; no AFTER seed and no native acceptance credit',counts=dict(counts),cases=cases,readers_serialized_and_closed=True,candidate_AFTER_seed=False,initializer_credit=False,files=files);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
