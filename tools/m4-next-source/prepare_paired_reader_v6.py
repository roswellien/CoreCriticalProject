"""Release consumed closed archive indexes before next additive paired reader."""
from pathlib import Path
import ast,hashlib
T=Path(__file__).resolve().parent
source=T/'compare_paired_policy_v5.py';target=T/'compare_paired_policy_v6.py'
assert not target.exists()
s=source.read_text();old='   native.close()';assert s.count(old)==1
s=s.replace(old,'   native.close();del native')
ast.parse(s);target.write_text(s)
print(hashlib.sha256(target.read_bytes()).hexdigest())
