"""Immutable generated-helper binding fix; no capture readers or workers."""
from pathlib import Path
import hashlib, json, sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
PARENT='d25d322684ca1697319c38273bad6b7e383e9195423736352ce5135a5fee399a'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 parent=ROOT/'reports/m4-joint-startup138-source/preparation-r1/report.json'
 assert sha(parent)==PARENT
 prior=json.loads(parent.read_bytes());out=parent.parent.parent/'preparation-r2'
 assert not out.exists();out.mkdir()
 files=dict(prior['files']);files[str(parent.resolve())]=PARENT
 for p,h in files.items():
  assert Path(p).suffix.lower()not in('.mwb','.zip','.mwi')
  assert sha(p)==h,p
 for name in ('continuity138.py','final_observer138.py','final_observer138_v2.py','paired_exports.py'):
  target=out/name;target.write_bytes((parent.parent/name).read_bytes());files[str(target.resolve())]=sha(target)
 source=Path(prior['entrypoint']).read_text()
 before='import paired_exports as EX'
 after="_paired_spec=importlib.util.spec_from_file_location('current138_paired_exports',Path(__file__).resolve().parent/'paired_exports.py')\nEX=importlib.util.module_from_spec(_paired_spec);_paired_spec.loader.exec_module(EX)"
 assert source.count(before)==1;source=source.replace(before,after)
 target=out/'compare_provider138.py';target.write_text(source);files[str(target.resolve())]=sha(target)
 files[str(Path(__file__).resolve())]=sha(__file__)
 report=dict(prior);report.update(entrypoint=str(target.resolve()),parent_preparation=str(parent.resolve()),parent_preparation_sha256=PARENT,
  scope='Unexecuted complete138 preparation with explicit binding of additive generated paired export helper',
  exact_delta=dict(before=before,after=after),source_changes=prior['source_changes']+[dict(label='Explicit generated current138 paired export helper',before=before,after=after)],files=files)
 receipt=out/'report.json';receipt.write_text(json.dumps(report,indent=2)+'\n')
 preflight=(ROOT/'tools/m4-joint-startup138/preflight_source.py').read_text()
 assert preflight.count("PREP='"+PARENT+"'")==1
 preflight=preflight.replace("PREP='"+PARENT+"'","PREP='"+sha(receipt)+"'").replace('preparation-r1/report.json','preparation-r2/report.json')
 marker="  need(module.FRAME==0x20001800 and module.BROKER==0x410a80,'Exact current caller interface')"
 addition="  need(Path(module.EX.__file__).resolve()==entry.parent/'paired_exports.py','Explicit physically generated current paired export helper')\n  need(module.EX.selected('sequence-0/Widget/root-4252240/carried-before/State.bin'),'Complete current Widget equality targets exported')"
 assert preflight.count(marker)==1;preflight=preflight.replace(marker,marker+'\n'+addition)
 check=ROOT/'tools/m4-138-source-review/preflight_helper_fix.py';check.write_text(preflight)
 print(json.dumps(dict(preparation=str(receipt),sha256=sha(receipt),preflight=str(check),preflight_sha256=sha(check),archive_reader_opened=False,worker_launched=False,initializer_credit=0)))
if __name__=='__main__':main()
