"""Guard the authentic producer ledger before exporting any bounded array."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];T=R/'tools/m4-widget-original';P=R/'reports/m4-widget-original/preparation-r6/report.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=T/'prepare_v5.py';d=json.loads(P.read_text())
if sha(P)!='9c1e134f72c11bbff17454dccb0d397680e21af2225c9bad941f1c036f53c5f3'or sha(p)!=d['files'][str(p.resolve())]:raise ValueError('Immutable source')
s=p.read_text()
a='''        out.append("bootstrap/"+std::to_string(sequence)+"/producer-api-count.bin",&registry_API_count,4);out.append("bootstrap/"+std::to_string(sequence)+"/producer-api-ledger.bin",registry_API_ledger,registry_API_count*sizeof(RegistryAPIEntry));
        require(registry_API_count<=256,"Bounded actual source producer API ledger");'''
b='''        require(!fs_error&&registry_API_count<=256,"Bounded actual source producer API ledger before export");
        out.append("bootstrap/"+std::to_string(sequence)+"/producer-api-count.bin",&registry_API_count,4);out.append("bootstrap/"+std::to_string(sequence)+"/producer-api-ledger.bin",registry_API_ledger,registry_API_count*sizeof(RegistryAPIEntry));'''
if s.count(a)!=1:raise ValueError('Exact producer export guard')
s=s.replace(a,b,1)
a=" pin(__file__);pin(R/'tools/m4-widget-original/derive_prepare_v5.py');"
b=" pin(__file__);pin(R/'tools/m4-widget-original/derive_prepare_v6.py');pin(R/'tools/m4-widget-original/prepare_v5.py');pin(R/'reports/m4-widget-original/preparation-r6/report.json','9c1e134f72c11bbff17454dccb0d397680e21af2225c9bad941f1c036f53c5f3');pin(R/'tools/m4-widget-original/derive_prepare_v5.py');"
if s.count(a)!=1:raise ValueError('Exact lineage')
s=s.replace(a,b,1);q=T/'prepare_v6.py'
if q.exists():raise ValueError('Fresh source')
q.write_text(s);print(json.dumps(dict(passed=True,source=str(q),sha256=sha(q))))
