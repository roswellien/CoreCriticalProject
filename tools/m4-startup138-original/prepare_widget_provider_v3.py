"""Correct exact literal EnterCriticalSection PC in frozen unexecuted v2."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
base=Path(__file__).with_name('compare_widget_source_v2.py');target=base.with_name('compare_widget_source_v3.py');old=base.read_text();assert old.count('0x78001091')==1
text=old.replace('0x78001091','0x7800106f');ast.parse(text);assert text.replace('0x7800106f','0x78001091')==old;assert not target.exists();target.write_text(text)
out=R/'reports/m4-startup138-original/widget-provider-preparation-r2';assert not out.exists();out.mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
contract=R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json';rows=json.loads(contract.read_bytes())['instructions'];assert any(r['pc']==0x7800106f and r['mnemonic']=='call'and '7802e044'in r['operands']for r in rows)
report=dict(passed=True,source_execution=False,exact_reverse_delta=True,delta='Only EnterCriticalSection literal CALL PC 78001091 -> actual recovered 7800106f',files={str(p.resolve()):sha(p)for p in(base,target,Path(__file__),contract)},complete_widget_gate=False);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(q,sha(q))
