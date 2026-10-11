"""Additive small proof retention and complete execution-source pin interface."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'tools/m4-lockit-source'
prior=BASE/'compare_provider124_v4.py';out=BASE/'compare_provider124_v5.py'
assert not out.exists()
s=prior.read_text()
s=s.replace('import final_observer124_v2 as F','import final_observer124_v2 as F\nimport identity_records as Q\nQ.install(F.S)')
s=s.replace('continuity_rows=[]','continuity_rows=[];executed_lineage={}')
s=s.replace("need(nr['passed'],'All current actual native124 sequences complete')","need(nr['passed'],'All current actual native124 sequences complete');executed_lineage=Q.lineage(native_report,nr,pin)")
s=s.replace("for file in ('string_observer124.py','final_observer124_v2.py','capture.py','responses.py'):","for file in ('string_observer124.py','final_observer124_v2.py','capture.py','responses.py','responses_v2.py','game_model.py','identity_records.py','continuity.py','header_derivations.py'):")
s=s.replace("  need(len(lockit_headers)==108,", "  for file in ('exact_equal.py','event_model.py','vtable_model.py'):pin(ROOT/'tools/m4-vtable-review'/file)\n  need(len(lockit_headers)==108,")
s=s.replace(" finally:\n  for filename", " finally:\n  (out/'API-identity-proofs.json').write_text(json.dumps(Q.value(),indent=2)+'\\n');pin(out/'API-identity-proofs.json')\n  for filename")
s=s.replace("report=dict(passed=passed,scope=", "report=dict(passed=passed,executed_lineage=executed_lineage,API_identity_proofs=str(out/'API-identity-proofs.json'),scope=")
assert 'executed_lineage=Q.lineage' in s and 'API-identity-proofs.json' in s
out.write_text(s)
receipt=ROOT/'reports/m4-lockit-source/provider-identity-preparation-r1';assert not receipt.exists();receipt.mkdir()
files={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in (prior,out,BASE/'identity_records.py',Path(__file__))}
(receipt/'report.json').write_text(json.dumps(dict(passed=True,scope='Additive preparation only; retains small physical identity/export proofs within the existing provider reader and explicitly binds current execution/build/joint/native preparation; no new execution or acceptance credit',native_executed=False,initializer_credit=False,entrypoint=str(out),files=files),indent=2)+'\n')
print(json.dumps(dict(passed=True,entrypoint=str(out),report_sha256=hashlib.sha256((receipt/'report.json').read_bytes()).hexdigest())))
