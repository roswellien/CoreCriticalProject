"""Additive sealed copy correcting only the proven malloc owner kind."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
    old=R/'reports/m4-formatting-native/preparation-r9';rp=old/'report.json';assert sha(rp)=='a27d9e62eecd7dd13508cb5dd7bb90b87fc2076cb340c5634dff5e88738b114f';p=json.loads(rp.read_bytes());assert p['passed']
    out=R/'reports/m4-formatting-native'/name;assert not out.exists();out.mkdir(parents=True);pins=dict(p['files'])|{str(rp.resolve()):sha(rp)}
    for path,digest in pins.items():assert sha(path)==digest,path
    for path in old.iterdir():
        if path.suffix in('.cpp','.hpp','.inc'):(out/path.name).write_bytes(path.read_bytes())
    op=out/'formatting_operations.inc';s=op.read_text();assert s.count('a->kind!=2')==2;s=s.replace('a->kind!=2','a->kind!=1');op.write_text(s)
    pins[str(Path(__file__).resolve())]=sha(__file__)
    for path in out.iterdir():pins[str(path.resolve())]=sha(path)
    result=p|dict(native_library=str(out/'registry_library.cpp'),native_include=str(out),source_or_native_executed=False,files=pins,owner_kind=1,owner_kind_source='Native generic standalone source malloc; exact generation/request/capacity remain required',parent_preparation=str(rp),parent_preparation_sha256=sha(rp))
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
