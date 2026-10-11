"""Emit compact provider progress only after a whole lifecycle case passes."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'tools/m4-lockit-source';prior=BASE/'compare_provider124_v7.py';out=BASE/'compare_provider124_v8.py';assert not out.exists()
s=prior.read_text();anchor="counts['persistent124_sequences']+=1;F.finish(machine,responses,expected_callbacks,G)";assert s.count(anchor)==1
s=s.replace(anchor,anchor+";print(json.dumps(dict(provider_case_passed=True,level=level,sequence=seq,API_count=responses.index)),flush=True)")
out.write_text(s)
receipt=ROOT/'reports/m4-lockit-source/provider-progress-preparation-r1';assert not receipt.exists();receipt.mkdir()
(receipt/'report.json').write_text(json.dumps(dict(passed=True,scope='Preparation only: progress print after each complete existing lifecycle comparison; no semantic/candidate changes',native_executed=False,initializer_credit=False,files={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in(prior,out,Path(__file__))}),indent=2)+'\n')
print(json.dumps(dict(passed=True,report_sha256=hashlib.sha256((receipt/'report.json').read_bytes()).hexdigest())))
