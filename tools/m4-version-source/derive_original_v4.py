"""Explicit reports root permits genuine relative-filename APIs with MW3 cwd."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
p=P/'prepare_original_v3.py';s=p.read_text()
a=";(out/'reference.cpp').write_text(ref)"
b=";ref=once(ref,'mw34::capture_direct::Writer out(argv[4]);','mw34::capture_direct::Options version_transport_options{};version_transport_options.reports_root=std::filesystem::path('+json.dumps(str((R/\"reports\").resolve()).replace(\"\\\\\",\"/\"))+');mw34::capture_direct::Writer out(argv[4],std::move(version_transport_options));')"+a
s=once(s,a,b)
s=once(s,"  pin(T/'derive_original_v3.py')","  pin(T/'derive_original_v4.py');pin(R/'reports/m4-version-source/original-preparation-r3/report.json','2dce0c09329f5d76b8cd87fd4eaa0200e110fe4d0cd3be0a191e2869995081b0');pin(R/'reports/m4-version-source/original-build-r3/build.json','1c2b011dd089327143bbf4d4c691c39d018cbf1f58a9dc3041920fa294edf63a');pin(T/'derive_original_v3.py')")
s=once(s,"[T/'prepare_original_v3.py'","[T/'prepare_original_v4.py',T/'prepare_original_v3.py'")
s=once(s,'source_return_observer_spans=3,','source_return_observer_spans=3,explicit_writer_reports_root=str((R/"reports").resolve()),required_process_cwd=str((R/"MW3").resolve()),')
q=P/'prepare_original_v4.py';assert not q.exists();q.write_text(s);compile(s,str(q),'exec');print(json.dumps(dict(recipe=str(q),sha256=sha(q),original_executed=False)))
