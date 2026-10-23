"""Prepare-only record for root_admit_completed_review_v2; runs no admission.

Proves the exact v1->v2 delta and its inverse, then statically checks that every
module review_completed_composite_v3 loads through its admitted-pin check is
pinned by v2's pre-terminal plan (and that v1 omits one). Opens no composer
output, no SQLite database and no capture.
"""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
T=R/'tools/m4-controls-terminal-composite'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def loaded_targets(reviewer):
 """Static load(R/'...') targets plus the stream parser J; resolved paths."""
 out=set()
 for node in ast.walk(ast.parse(reviewer.read_text())):
  if isinstance(node,ast.Call)and getattr(node.func,'id',None)=='load'and node.args:
   arg=node.args[0]
   if isinstance(arg,ast.BinOp)and isinstance(arg.right,ast.Constant):out.add(str((R/arg.right.value).resolve()))
 return out
def plan(parent,reviewed,include_parser):
 pins={str(Path(p).resolve()):h for p,h in reviewed['files'].items()}
 if include_parser:
  parser=str((R/'tools/m4-138-controls-review/full_raw_review_v2.py').resolve())
  if parser not in parent['files']:raise ValueError('Parser absent from composer admission')
  pins[parser]=parent['files'][parser]
 return pins
def main():
 v1=T/'root_admit_completed_review_v1.py';v2=T/'root_admit_completed_review_v2.py';reviewer=T/'review_completed_composite_v3.py'
 b1=v1.read_bytes();b2=v2.read_bytes();assert b'\r\n'not in b1 and b'\r\n'not in b2
 doc_old=b'"""ROOT terminal-only admission recipe; refuses partial composer output."""\n'
 doc_new=b'"""ROOT terminal-only admission recipe v2; refuses partial composer output.\n\nv2 pins the composer-admitted stream parser that review_completed_composite_v3\nloads through its admitted-pin check (v1 omitted it, so the reviewer would refuse).\n"""\n'
 anchor=b" for path,h in reviewed['files'].items():pin(path,h)\n"
 added=(b" # The reviewer loads this streamed-metadata parser through its admitted-pin\n"
        b" # check; carry the exact composer-admitted SHA forward, never a fresh hash.\n"
        b" parser=str((R/'tools/m4-138-controls-review/full_raw_review_v2.py').resolve());assert parser in parent['files'];pin(parser,parent['files'][parser])\n")
 assert b2.count(doc_new)==1 and b2.count(anchor+added)==1
 assert b2.replace(anchor+added,anchor).replace(doc_new,doc_old)==b1,'Exact inverse v2->v1'
 parent_p=R/'reports/m4-controls-terminal-composite/root-composer-admission-r1/report.json'
 reviewed_p=R/'reports/m4-controls-terminal-composite/root-composite-reviewer-source-review-r1/report.json'
 assert sha(parent_p)=='83ea5b4d4e26c7054b30b70777c7eff2e4cc1b4e6f9e71ad6e1b1af059a9d373'
 assert sha(reviewed_p)=='236403d6caf13543178690c90c9aa5d833c5ea47cc057e1e92f62b6347f21018'
 parent=json.loads(parent_p.read_bytes());reviewed=json.loads(reviewed_p.read_bytes())
 targets=loaded_targets(reviewer);assert len(targets)==3,targets
 p1=plan(parent,reviewed,False);p2=plan(parent,reviewed,True)
 missing1=sorted(t for t in targets if t not in p1);missing2=sorted(t for t in targets if t not in p2)
 assert missing1==[str((R/'tools/m4-138-controls-review/full_raw_review_v2.py').resolve())],missing1
 assert missing2==[],missing2
 stale=[t for t in targets if sha(t)!=p2[t]];assert not stale,stale
 assert str(reviewer.resolve())in p2 and p2[str(reviewer.resolve())]==sha(reviewer)
 # Adverse controls on the pure plan: the corrected pin must refuse substitutes.
 adverse=[]
 bad_parent=dict(parent,files={k:v for k,v in parent['files'].items()if not k.endswith('full_raw_review_v2.py')})
 try:plan(bad_parent,reviewed,True)
 except ValueError:adverse.append('parser_absent_from_composer_admission_refused')
 else:raise AssertionError('absent parser admitted')
 parser=str((R/'tools/m4-138-controls-review/full_raw_review_v2.py').resolve())
 forged=dict(parent,files=dict(parent['files'],**{parser:'0'*64}))
 if plan(forged,reviewed,True)[parser]!=sha(parser):adverse.append('forged_parser_hash_detected_by_whole_byte_pin')
 else:raise AssertionError('forged hash matched')
 if missing1:adverse.append('v1_plan_reproduces_reviewer_refusal')
 out=R/'reports/m4-controls-terminal-composite/completed-review-admission-preparation-r1';assert not out.exists();out.mkdir()
 files={str(p.resolve()):sha(p)for p in(v1,v2,reviewer,parent_p,reviewed_p,Path(__file__))}
 files[parser]=p2[parser]
 value=dict(prepared_only=True,admission_executed=False,composer_output_opened=False,production_DB_opened=False,
  exact_v1_v2_delta_inverse=True,reviewer_admitted_pin_loads=sorted(targets),v1_missing_admitted_loads=missing1,v2_missing_admitted_loads=missing2,
  adverse_controls=adverse,parser_pin_source='root-composer-admission-r1 files (composer-admitted SHA)',accepted_function_credit=0,files=files)
 q=out/'report.json';q.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),adverse=len(adverse))))
if __name__=='__main__':main()
