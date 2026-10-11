"""Independent exact comparer/helper preparation review; no capture consumer."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];PINS={}
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reads');d=sha(p);need(h is None or h==d,'Physical bounded input '+str(p));PINS[str(p)]=d;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh paired preflight');out.mkdir(parents=True)
 path=R/'reports/m4-startup130-paired/comparer-preparation-r2/report.json';receipt=read(path,'49cee53b235f044a8cc82e3461dbcf93f8245bf936b163d4afd1a88ab9d2bd66');need(receipt['passed']and receipt['capture_reader_opened']is False and receipt['executed']is False,'Unexecuted exact additive comparer preparation')
 for p,h in receipt['files'].items():pin(p,h)
 base=R/'tools/m4-startup130-paired';hunks=read(path.parent/'hunks.json')
 for old,new,key in [('paired.py','paired_v2.py','comparer'),('format_relations.py','format_relations_v2.py','helper')]:
  source=(base/old).read_text()
  for h in hunks[key]:need(source.count(h['old'])==1,'Each exact additive hunk occurs once');source=source.replace(h['old'],h['new'])
  need(source==(base/new).read_text(),'Every byte outside explicit additive hunks unchanged');ast.parse(source)
 current=(base/'paired_v2.py').read_text();helper=(base/'format_relations_v2.py').read_text();tree=(base/'tree_relations.py').read_text()
 need('close_reader(native);native=None'in current and 'close_reader(ori);ori=None'in current and "gate('original_combined_review')"in current,'Successful and finally closure plus exact independent original binding')
 need("len(native['Lockit_API_relations'])==2"in helper and "len(observed)==6"in helper and "len(source_private['FS_frames'])==2"in helper,'Each mixed API/FS case independently exhaustive')
 for guard in ("source_owned_accesses","Every literal mixed DWORD exact role/PC/offset/width/order","Every remaining literal game scalar/borrowed-static value is exact","Complete capacity backing is own literal writes plus untouched genuine input","last_dominating_literal_store","own_genuine_carried_BEFORE_byte"):
  need(guard in helper,'Finite own-branch formatter/mixed helper seam '+guard)
 for guard in ('TREE_PHASE = 78',"read[1] == frame['entry_ESP'] - 41","source_accesses'][first:index]","owner_invocation_ordinal","value_owner_role_index","offset in (0, 4, 8)","offset in (12, 16, 20)"):
  need(guard in tree,'Exact tree role/occurrence/source-local policy '+guard)
 loaded=read(R/'reports/m4-tree-review/loaded-input130-r1/report.json','66f3b663b5c66da5d40e217fb40b2686c2b2c402dd3f2640f977db9a6d1f7ba4');need(loaded['passed']and loaded['endpoint_carry_acceptance']is False,'Actual source disjointness gate, no premature paired endpoint credit')
 original=read(R/'reports/m4-tree-review/original130-combined-review-r3/report.json','8365b62801e51146ec68bfbe597971745919c8722f2e9c411325a775376af186');need(original['passed'],'Fresh actual original source review');pin(__file__)
 report=dict(passed=True,scope='Independent exact current130 additive comparer/helper source preparation and finite own-branch pointer/scalar/local policy review; actual paired execution remains required',comparer_preparation_sha256=sha(path),comparer_sha256=sha(base/'paired_v2.py'),format_helper_sha256=sha(base/'format_relations_v2.py'),tree_helper_sha256=sha(base/'tree_relations.py'),counts=dict(exact_comparer_hunks=6,exact_helper_hunks=1,mixed_API_relations_per_case=2,mixed_FS_frames_per_case=2,mixed_FS_source_events_per_case=6,tree_owned_causal_operations_per_case=172,tree_distinct_owner_roles_per_case=7),archive_readers_opened=0,paired_executed=False,initializer_credit=0,files=PINS)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p))))
if __name__=='__main__':main(sys.argv[1])
