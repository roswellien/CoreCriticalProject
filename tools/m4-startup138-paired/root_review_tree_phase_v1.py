"""ROOT exact chronology correction admission; all tree byte rules retained."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
pins={}
def pin(p,h=None):
 p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
p=pin(R/'reports/m4-startup138-paired/tree-phase-preflight-r1/report.json','c118dfb427f9804120de9c732b2f285514c998c3dc51c33bd22e42ca751f408e');v=json.loads(p.read_bytes())
assert v['passed'] and v['all_ordinary_readers_closed'] and v['raw_entries_authenticated']==54 and v['whole_before_tree_page_carries']==18 and v['activated_endpoint_adverses_refused']==24
for q,h in v['files'].items():pin(q,h)
old=R/'tools/m4-startup131-paired/tree_relations.py';new=R/'tools/m4-startup138-paired/tree_relations_v2.py'
assert old.read_text().count('TREE_PHASE = 79')==1 and new.read_text().replace('TREE_PHASE = 83','TREE_PHASE = 79')==old.read_text()
order=json.loads((R/'reports/m4-startup138-original/preparation-r8/report.json').read_bytes())['selected_order'];assert len(order)==138 and order[83]['entry']==0x4b7f70 and order[79]['entry']==0x4b5af0
assert len(v['rows'])==12 and {(r['level'],r['sequence'])for r in v['rows']}=={(l,s)for l in('O0','O2')for s in range(6)}
for r in v['rows']:
 assert r['actual_tree_phase']==83 and r['root_at_old_phase']==0x4b5af0 and r['address']==0x60b2f9 and r['write_PC']==0x4b7da6
 assert r['source_original_expected']==r['phase83_after_original'] and r['source_native_expected']==r['phase83_after_native']
pin(__file__);out=R/'reports/m4-startup138-paired/tree-phase-root-review-r1';assert not out.exists();out.mkdir()
d=dict(passed=True,independent_review=True,scope='ROOT reviewed exact tree constant inverse and measured current phase/source/raw endpoint preflight; full paired execution still pending',tree_phase=83,prior_accepted_tree_phase=79,source_static_owner_CPU_rules_unchanged=True,raw_entry_preflight_sha256=sha(p),raw_entries_authenticated_by_preflight=54,full_pair_executed=False,archive_reader_opened=False,initializer_credit=0,files=pins)
q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(sha(q))
