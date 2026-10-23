"""ROOT code and completed role admission; composer integrity grants no credit."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 base=R/'reports/m4-controls-terminal-composite';manifest=base/'completed-input-preparation-r4/completed-input-manifest.json'
 assert sha(manifest)=='e8e3c1ecd45784a51355e7f89fc30b7eb7977ed85598d0f85746823d77cf0251'
 M=json.loads(manifest.read_bytes());assert M['actual_terminals_complete']is True
 pins={str(manifest):sha(manifest)}
 for role,row in M['roles'].items():
  p=Path(row['path']).resolve();assert sha(p)==row['sha256'];pins[str(p)]=row['sha256']
 builder=R/'tools/m4-controls-terminal-composite/build_v7.py';assert sha(builder)=='1d02e694331cdab180492149c051fe75f5bd2e3baca08015c6849d8d654be063'
 for p in(builder,R/'tools/m4-138-controls-review/full_raw_review_v2.py',R/'tools/m4-138-controls-review/expand_proof_inventory.py',Path(__file__).resolve()):pins[str(p)]=sha(p)
 for p,h in((R/'reports/m4-controls-strict-bridge/root-machinery-review-r1/report.json','b0c54d3f8a578d637da65e5e11bb499e2a9b0e51a7859fdb3841ebac3825e166'),(base/'root-role-rawroot-controls-r1/report.json','1f145dea07b5f0eb57039600f88f532488ce191fb534489ad0992cb4c052ed99')):
  assert sha(p)==h;pins[str(p)]=h
 bindings={k:M['roles'][k]for k in('current16_fullraw','current16_semantic_review','current8_scope_review')}
 for k,h in dict(current16_fullraw='2a0086d81039912923fb6f9ed294ea851098ae7e5078fc96faf5f0c246b63035',current16_semantic_review='9f2b37cb7412c845b49846b45533e4e5b94cd65323c09435acfcfc5c046aa4a9',current8_scope_review='9c79f74002c7b8630e699b4687fc987e7edfcd12d31f3ec53f9be5deae9fa6e3').items():assert bindings[k]['sha256']==h
 complete=M['roles']['legacy_prelaunch_complete_review'];assert complete['sha256']=='4a88d2c69f550221f553267af1a2eb5a569ccb8c1c9d7cf1ed4be859c8616212'
 out=base/'root-composer-admission-r1';assert not out.exists();out.mkdir();q=out/'report.json'
 q.write_text(json.dumps(dict(passed=True,terminal_controls_composer_admitted=True,independent_ROOT_source_and_role_review=True,reviewed_role_bindings=bindings,legacy_complete7_report=complete['path'],legacy_complete7_sha256=complete['sha256'],terminal_rows_still_require_composer_revalidation=True,actual_composite_DB_created=False,acceptance_admitted=False,accepted_function_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main()
