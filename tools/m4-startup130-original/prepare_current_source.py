"""Prepare additive source readers; no capture archive is opened here."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main():
 old=R/'tools/m4-tree-source/compare_original125_prefix.py';new=R/'tools/m4-startup130-original/tree_source.py';need(not new.exists(),'Fresh tree derivative')
 text=old.read_text();hunks=[]
 def one(a,b):
  nonlocal text
  need(text.count(a)==1,'One source hunk '+a[:100]);text=text.replace(a,b);hunks.append(dict(old=a,new=b))
 one("ROOT=Path(__file__).resolve().parents[2];PINS={}","ROOT=Path(__file__).resolve().parents[2];PINS={};SHARED_READER=None")
 one("out=ROOT/'reports/m4-tree-source'/name","out=ROOT/'reports/m4-startup130-original'/name")
 one("ROOT/'reports/m4-tree-original/original125-validation-r1/report.json','5a7911dee3f77d504a5a28cf66de2be7cc0b159a15a4e81282368a24d3a45534'","ROOT/'reports/m4-startup130-original/validation-r2/report.json','91a3ca940214636b0d4c1a08c7ccf503a5c06127a3af4b26fdad50c876f1ffca'")
 one("reader=D.DirectSet(execution['original_capture'],pin)","reader=SHARED_READER;need(reader is not None and Path(reader.path).resolve()==Path(execution['original_capture']).resolve(),'One authenticated shared current-original130 session')")
 one("phase=reader.data(f'phase/{sequence}/77.bin');memory=normalized(phase[2276:178404]);actual_after=normalized(phase[178404:354532])","tree_phase=next(i for i,x in enumerate(preparation['selected_order'])if x['entry']==0x4b7f70);need(tree_phase==78,'Current physical tree slot after FCOS');phase=reader.data(f'phase/{sequence}/{tree_phase}.bin');memory=normalized(phase[2276:178404]);actual_after=normalized(phase[178404:354532]);pages=pages+preparation['extra_whole_source_pages'];memory.update({p:bytearray(reader.data(f'phase/{sequence}/{tree_phase}/extra-before/{p}.bin'))for p in preparation['extra_whole_source_pages']});actual_after.update({p:bytearray(reader.data(f'phase/{sequence}/{tree_phase}/extra-after/{p}.bin'))for p in preparation['extra_whole_source_pages']})")
 one("fs_raw=reader.data(f'phase/{sequence}/77/fs-events.bin')","fs_raw=reader.data(f'phase/{sequence}/{tree_phase}/fs-events.bin')")
 one("ROOT/'reports/m4-tree-original/original125-validation-r1/allocation-geometry.json'","ROOT/'reports/m4-startup130-original/validation-r2/allocation-geometry.json'")
 one("reader.data(f'phase/{sequence}/77/api-ledger.bin')","reader.data(f'phase/{sequence}/{tree_phase}/api-ledger.bin')")
 one("reader.data(f'phase/{sequence}/77/lockit-snapshots.bin')","reader.data(f'phase/{sequence}/{tree_phase}/lockit-snapshots.bin')")
 one("reader.data(f'phase/{sequence}/77/api-initial/{api_index}/bytes.bin')","reader.data(f'phase/{sequence}/{tree_phase}/api-initial/{api_index}/bytes.bin')")
 one("result['phase']=77","result['phase']=tree_phase")
 one("if reader is not None:reader.close();reader.entries.clear();reader.bundles.clear()","# The aggregate owns and closes the one genuine archive/index session.\n        reader=None")
 one("scope='Literal persistent tree prefix from genuine untouched original BEFORE and finite scalar/typed API boundaries; no tree AFTER effect seed'","scope='Current-original130 literal tree prefix from genuine untouched BEFORE and finite scalar/typed API boundaries; borrowed shared reader closed only by aggregate',reader_scope='Borrowed one authenticated current-original130 session; aggregate closure required'")
 new.write_text(text)
 out=R/'reports/m4-startup130-original/current-source-preparation-r1';need(not out.exists(),'Fresh prep');out.mkdir(parents=True)
 pins={str(p.resolve()):sha(p)for p in [old,new,Path(__file__),R/'tools/m4-tree-source/game_model_v4.py']}
 (out/'tree-hunks.json').write_text(json.dumps(hunks,indent=2)+'\n');pins[str((out/'tree-hunks.json').resolve())]=sha(out/'tree-hunks.json')
 report=dict(passed=True,scope='Prepared literal tree130 reader with current actual phase78 and three complete additional pages; no reader open',files=pins,hunks=len(hunks),capture_reader_opened=False,executed=False)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main()
