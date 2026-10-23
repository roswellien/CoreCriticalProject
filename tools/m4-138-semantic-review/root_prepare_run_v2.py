from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-138-semantic-review/root_run_semantics_v1.py';s=p.read_text()
for old,new in [('root-semantic-execution-r1','root-semantic-execution-r2'),('root-admission-r1','root-admission-r2'),('72790014fab99fad38b91d9a404e47b6ac306b7ad52aa348cc6f1345c8ed7e38','501fadf59bd716c493614b6e953e53fe5486d043ef666876b699d691cbec4c95'),('review_paired138_v3.py','review_paired138_v4.py'),('semantic-review-r1','semantic-review-r2')]:
 assert old in s;s=s.replace(old,new)
q=p.with_name('root_run_semantics_v2.py');assert not q.exists();q.write_text(s)
