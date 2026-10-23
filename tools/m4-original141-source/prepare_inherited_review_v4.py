"""Bind current closed original141 source7; no reviewer or reader invocation."""
from pathlib import Path
import ast,difflib,hashlib,json
R=Path(__file__).resolve().parents[2];OUT=R/'reports/m4-original141-source/inherited-review-preparation-r4'
SOURCE=R/'reports/m4-original141-source/source-r7/report.json'
SOURCE_SHA='44a46bd0fda7776578232af60e2d9f0188275660350a239eb8c8def4790d9334'
CONFIG=R/'reports/m4-original141-source/configuration-preparation-r3/configuration.json'
CONFIG_SHA='451d19e8a30e68cb76e266ef00df3c080c19ea590a091a2a8a072b4f5123f5b0'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 assert not OUT.exists();OUT.mkdir();pins={};closure={};declaration_origins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 def include(path,h,origin):
  p=Path(path).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
  assert str(p)not in closure or closure[str(p)]==h;closure[str(p)]=h;declaration_origins.setdefault(str(p),[]).append(origin)
 def receipt(p,h=None):
  p=pin(p,h);d=json.loads(p.read_text());include(p,pins[str(p)],'physically examined bounded receipt')
  for q,v in d.get('files',{}).items():include(q,v,str(p))
  return d
 a=receipt(SOURCE,SOURCE_SHA);assert a['passed']and a['reader_closed']and a['counts']['phases']==846 and a['counts']['callbacks']==111
 receipt(CONFIG,CONFIG_SHA)
 for c in a['children']:
  child=receipt(c['receipt'],c['sha256']);assert child['passed']
 receipt(a['original_validation_path'],a['original_validation_sha256'])
 receipt(R/'reports/m4-startup131-original/inherited-source-preparation-r3/report.json','3f21fbc601dd3b8dfea3ea4354e425f3aa6a368f1e1ddd77f06958bed656be97')
 parent=pin(R/'tools/m4-original141-source/review_inherited141_v3.py');b=parent.read_text();orig=b
 changes=[("replay_original141_v7.py","replay_original141_v10.py"),(" C=read(configuration_path,configuration_sha)"," need(source_sha=='"+SOURCE_SHA+"'and Path(source_path).resolve()==R/'reports/m4-original141-source/source-r7/report.json'and configuration_sha=='"+CONFIG_SHA+"','Exactly sealed source7 and current configuration; no old original138 semantic row')\n C=read(configuration_path,configuration_sha)")]
 for old,new in changes:assert b.count(old)==1;b=b.replace(old,new)
 child=R/'tools/m4-original141-source/review_inherited141_v4.py';assert not child.exists();ast.parse(b);child.write_text(b);pin(child)
 inverse=b
 for old,new in reversed(changes):assert inverse.count(new)==1;inverse=inverse.replace(new,old)
 assert inverse==orig
 delta=[]
 for tag,i,j,k,l in difflib.SequenceMatcher(None,orig.splitlines(True),b.splitlines(True),autojunk=False).get_opcodes():
  if tag!='equal':delta.append(dict(parent_start=i,parent_stop=j,child_start=k,child_stop=l,parent=''.join(orig.splitlines(True)[i:j]),child=''.join(b.splitlines(True)[k:l])))
 inv=OUT/'inverse.json';inv.write_text(json.dumps(delta,indent=2)+'\n');pin(inv)
 for p in [SOURCE.parent/'original-Formatting-source-derivations.json',SOURCE.parent/'original-Tree-source-derivations.json']:
  assert str(p.resolve())in closure,'Current source7 exported scalar derivations already declared'
 for p in [child,parent,Path(__file__).resolve(),R/'tools/m4-original141-source/format_source141_v2.py',R/'tools/m4-original141-source/replay_original141_v10.py',R/'tools/m4-original141-source/retained_corpus141_v2.py',R/'tools/m4-original141-tree-source/tree_source_v3.py']+[R/'tools/m4-tree-review'/q for q in ('review_original130_combined.py','review_original130_combined_v2.py','derive_original130_combined_v2.py','derive_original130_combined_v3.py')]:
  include(p,sha(pin(p)),'Explicit complete cold scalar reviewer code dependency')
 cp=OUT/'ordinary-closure-declarations.json';cp.write_text(json.dumps(dict(scope='Non-authoritative declared ordinary closure for ROOT complete physical authentication; no current semantic original138 report row',original_source_path=str(SOURCE),original_source_sha256=SOURCE_SHA,configuration_path=str(CONFIG),configuration_sha256=CONFIG_SHA,source_record_only='original141/source-r7',historical131_proof_retained=True,declarations=closure,declaration_origins=declaration_origins,whole_declared_inputs_physically_rehashed=False),indent=2)+'\n');pin(cp)
 recipe=OUT/'ROOT-recipe.txt';recipe.write_text('UNEXECUTED. Independently review full v3→v4 inverse/current10 code and authenticate EVERY ordinary closure declaration by actual byte hash (index/payload included). No oldN/original138 source report as semantic source row; historical131 continuity and inherited code proofs remain dependencies. Create fresh ROOT admission scope_identity=original141_post_source_inherited_review, independent_review=true, configuration_sha256='+CONFIG_SHA+', original_source_sha256='+SOURCE_SHA+', files=complete physically authenticated closure plus preparation/currentreviewer/recipe dependencies. This preparation is NOT an admission. Run python -B tools/m4-original141-source/review_inherited141_v4.py ADMISSION ADMISSION_SHA '+str(CONFIG)+' '+CONFIG_SHA+' '+str(SOURCE)+' '+SOURCE_SHA+' inherited-review-r1. Reviewer uses ordinary scalar source summaries, full owned byteflows and FS/cdecl/TREE proof only; no archive or source machine evaluation. Canonical identity/physical transport deferred final acceptance union; no credit.\n');pin(recipe)
 report=OUT/'report.json';report.write_text(json.dumps(dict(prepared_only=True,exact_whole_parent_inverse=True,inverse_hunks=len(delta),semantic_delta='Current10 controller and exact current source7/config binding only; all v3 semantic predicates retained.',original_source_path=str(SOURCE),original_source_sha256=SOURCE_SHA,configuration_path=str(CONFIG),configuration_sha256=CONFIG_SHA,ordinary_declared_dependencies=len(closure),ordinary_declarations_not_ROOT_admitted=True,whole_declared_inputs_physically_rehashed=False,reviewer_executed=False,source_execution=False,canonical_reader_opened=False,ordinary_export_reader_opened=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(path=str(report),sha256=sha(report),dependencies=len(closure))))
if __name__=='__main__':main()
