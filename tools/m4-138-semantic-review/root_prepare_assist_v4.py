from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-138-semantic-review/root_review_assist_v3.py';s=p.read_text()
old='sha=sha,importlib=importlib)';assert s.count(old)==1
s=s.replace(old,'sha=sha,importlib=importlib,Path=Path)')
old=' # Independently reconstruct complete physical provider pages';assert s.count(old)==1
addition=" supplement=pin(R/'tools/m4-138-semantic-review/owner_adverse_supplement_v1.py','16d0ea1d6f4187cc77b40f02b2a5c82c83bb0295490854ae6c508373007755f6');ss=importlib.util.spec_from_file_location('root_owner_adverses',supplement);su=importlib.util.module_from_spec(ss);ss.loader.exec_module(su);su.run(base,owner_api_fs,refused)\n"
s=s.replace(old,addition+old)
q=p.with_name('root_review_assist_v4.py');assert not q.exists();q.write_text(s)
c=(R/'tools/m4-138-semantic-review/root_run_assist_v1.py').read_text()
c=c.replace('root_review_assist_v3.py','root_review_assist_v4.py').replace('ff28cd61ccefb1ef3b05fb9857bde731007808d7062bc0f8603da9b8161d3e43',hashlib.sha256(q.read_bytes()).hexdigest()).replace('root-assist-controller-r1','root-assist-controller-r2').replace('root-ordinary-assist-r1','root-ordinary-assist-r2')
z=R/'tools/m4-138-semantic-review/root_run_assist_v2.py';assert not z.exists();z.write_text(c)
