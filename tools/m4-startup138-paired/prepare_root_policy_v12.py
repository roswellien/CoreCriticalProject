from pathlib import Path
p=Path(__file__).with_name('root_seal_current_policy_v11.py')
s=p.read_text()
for a,b in [('import hashlib','import hashlib,sys\nprepared_sha=sys.argv.pop(1)\nassert len(prepared_sha)==64'),('root-policy-admission-r7','root-policy-admission-r8'),('root-definition-preflight-r7','root-definition-preflight-r8'),('comparer-preparation-r13','comparer-preparation-r15'),('preflight_comparer_v13.py','preflight_comparer_v15.py'),("'84f047b2d83c54ef678e60ba645cd9cf46d3f95737baaa3c70f4d7a7948e3d9c'",'prepared_sha'),('format-module-root-review-r1','format-module-root-review-r3'),('39a98c818eed260d830f1cc646553b66407c9477b0554e5d41d4a2ad959f8f00','97fceac99e6d05cd2263fefa482d5205a93b711f2471352903dbcf611ec933f7')]:
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
q=p.with_name('root_seal_current_policy_v12.py');assert not q.exists();q.write_text(s)
