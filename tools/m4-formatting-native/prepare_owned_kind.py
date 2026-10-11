"""Sealed additive copy with the three measured generic malloc kind predicates."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def main(name):
    previous=R/'reports/m4-formatting-native/preparation-r9';receipt_path=previous/'report.json'
    assert sha(receipt_path)=='a27d9e62eecd7dd13508cb5dd7bb90b87fc2076cb340c5634dff5e88738b114f'
    prior=json.loads(receipt_path.read_bytes());assert prior['passed'];pins=prior['files']|{str(receipt_path.resolve()):sha(receipt_path)}
    for source_path,digest in pins.items():assert sha(source_path)==digest,source_path
    output=R/'reports/m4-formatting-native'/name;assert not output.exists();output.mkdir(parents=True)
    for source_path in previous.iterdir():
        if source_path.suffix in('.cpp','.hpp','.inc'):(output/source_path.name).write_bytes(source_path.read_bytes())
    operations=output/'formatting_operations.inc';text=operations.read_text();assert text.count('a->kind!=2')==3;operations.write_text(text.replace('a->kind!=2','a->kind!=1'))
    pins[str(Path(__file__).resolve())]=sha(__file__)
    for output_path in output.iterdir():pins[str(output_path.resolve())]=sha(output_path)
    result=prior|dict(native_library=str(output/'registry_library.cpp'),native_include=str(output),source_or_native_executed=False,files=pins,owner_kind=1,owner_kind_source='Native generic standalone source malloc; exact generation/request/capacity remain required',parent_preparation=str(receipt_path),parent_preparation_sha256=sha(receipt_path))
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(output/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
