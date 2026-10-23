"""ROOT exact exporter delta review; no archive opened."""
from pathlib import Path
import hashlib,json,importlib.util
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
out=R/'reports/m4-startup141-source/export-root-review-r1';need(not out.exists(),'Fresh ROOT export review');out.mkdir(parents=True)
p=R/'reports/m4-startup141-source/export-preparation-r1/report.json';need(sha(p)=='c7984daefac2ee0247ef4065ce66ac41c6470659d1f8b182e4c4fc438694ccb7','Preparation identity');v=json.loads(p.read_bytes())
old=Path(v['parent']);new=Path(v['exporter']);need(sha(old)==v['parent_sha256'] and sha(new)==v['exporter_sha256'],'Whole exporter identities')
added=" if re.fullmatch(r'sequence-\\d+/Constructors/.*',key):return True\n if re.fullmatch(r'sequence-\\d+/phase-\\d+-(?:before|after)-constructor-global5F2000\\.bin',key):return True\n if re.fullmatch(r'sequence-\\d+/(?:fs-frame-witnesses|fs-record-bytes)\\.bin',key):return True\n"
s=new.read_text();need(s.count(added)==1 and s.replace(added,'')==old.read_text(),'Only three logical selection additions; unchanged payload and reader guards')
spec=importlib.util.spec_from_file_location('root_export_review',new);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
positive=['sequence-0/Constructors/root-4103F0.bin','sequence-5/phase-140-before-constructor-global5F2000.bin','sequence-0/phase-0-after-constructor-global5F2000.bin','sequence-1/fs-frame-witnesses.bin','sequence-2/fs-record-bytes.bin']
negative=['sequence-0/not-Constructors/root.bin','sequence-0/phase-1-before-constructor-global5F2000.bin.extra','sequence-x/fs-record-bytes.bin','sequence-0/fs-record-bytes.bin.extra']
need(all(m.selected(k) for k in positive) and not any(m.selected(k) for k in negative),'Bounded added-name predicates')
files={str(q.resolve()):sha(q) for q in [p,old,new,Path(__file__)]}
value=dict(passed=True,scope='Exact three exporter selection additions; retain canonical authentication and per-file/whole-payload checks',inverse_exact=True,positive_name_controls=len(positive),negative_name_controls=len(negative),canonical_reader_opened=False,consumer_execution_admitted=False,initializer_credit=0,files=files)
q=out/'report.json';q.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(dict(passed=True,report=str(q),sha256=sha(q))))
