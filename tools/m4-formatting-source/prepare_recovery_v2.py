"""Additive correction of the formatter transition-table static extent."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
    p=R/'tools/m4-formatting-source/recover_provider.py'
    assert sha(p)=='442c9f5370fd97ddad3f195f679205198593d91e8700ebd80adcb386200b2c04', 'Exact source preparer input'
    text=p.read_text();old="(0x7802e2f0,64,'state transition nibble table')";assert text.count(old)==1
    q=p.with_name('recover_provider_v2.py');assert not q.exists();q.write_text(text.replace(old,"(0x7802e2f0,128,'state transition nibble table')"))
    out=R/'reports/m4-formatting-source'/name;assert not out.exists();out.mkdir(parents=True)
    report=dict(passed=True,scope='Static table extent correction only; normal type s class8 needs offset64+state',source=str(q),source_sha256=sha(q),files={str(p.resolve()):sha(p),str(q.resolve()):sha(q),str(Path(__file__).resolve()):sha(__file__)},executed=False)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
