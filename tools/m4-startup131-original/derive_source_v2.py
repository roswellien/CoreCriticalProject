from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
T=Path(__file__).resolve().parent;base=T/'compare_source.py';p=T/'compare_source_v2.py';assert not p.exists()
s=base.read_text();a="e=read(v['execution_path'],v['execution_sha256']);";assert s.count(a)==1
s=s.replace(a,"execution_report=Path(v['execution_path'])/'report.json';e=read(execution_report,v['execution_sha256']);")
p.write_text(s)
(T/'source-v2-lineage.json').write_text(json.dumps(dict(base=str(base),base_sha256=hashlib.sha256(base.read_bytes()).hexdigest(),generated=str(p),generated_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),change='Current full-original validation execution_path names its execution directory; use its exact externally pinned report.json, unlike historical one-root receipt file path. No model/predicate/input domain changes.',failed_receipt='reports/m4-startup131-original/source-r1/report.json',archive_reader_opened=False),indent=2)+'\n');print(p)
