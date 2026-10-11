"""Freeze the exact successful current130 pairing inputs, without archives."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-startup130-paired/configuration-r1';assert not out.exists();out.mkdir(parents=True)
 paths={
 'native_execution':'reports/m4-joint-startup130-root/execution-r2/report.json',
 'native_source':'reports/m4-formatting-source/native130-provider-r1/report.json',
 'original_old4_source':'reports/m4-startup130-original/old-Lockit-source-r1/report.json',
 'original_compiled_review':'reports/m4-tree-review/original130-prelaunch-r7/report.json',
 'original_combined_source':'reports/m4-startup130-original/combined-source-r3/report.json',
 'original_combined_review':'reports/m4-tree-review/original130-combined-review-r3/report.json',
 'loaded_inputs':'reports/m4-tree-review/loaded-input130-r1/report.json',
 'paired_policy':'reports/m4-startup130-paired/preparation-r2/report.json',
 'comparer_preparation':'reports/m4-startup130-paired/comparer-preparation-r2/report.json'}
 files={};config=dict(scope='current130-paired-frozen-gates')
 for name,rel in paths.items():
  p=(R/rel).resolve();v=json.loads(p.read_bytes());assert v['passed'];h=sha(p);files[str(p)]=h;config[name]=dict(path=str(p),sha256=h)
 for name in ('paired_v2.py','format_relations_v2.py','tree_relations.py'):
  p=R/'tools/m4-startup130-paired'/name;files[str(p)]=sha(p)
 files[str(Path(__file__).resolve())]=sha(__file__)
 p=out/'configuration.json';p.write_text(json.dumps(config,indent=2)+'\n');files[str(p)]=sha(p)
 report=dict(passed=True,scope='Exact current130 successful report and code identity configuration only; no paired reader or new initializer credit',configuration=str(p),configuration_sha256=sha(p),files=files,capture_reader_opened=False,initializer_credit=0)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(report_sha256=sha(q),configuration_sha256=sha(p))))
if __name__=='__main__':main()
