"""Compare physical table pairs, excluding historical metadata-only phase."""
from pathlib import Path
import hashlib,json,sys
T=Path(__file__).resolve().parent;R=T.parents[1]
base=T/'seal_inherited_source.py';source=base.read_text()
old="current['selected_order'][:13]+current['selected_order'][14:]==old['selected_order']"
new="[(x['slot'],x['entry'])for x in current['selected_order'][:13]+current['selected_order'][14:]]==[(x['slot'],x['entry'])for x in old['selected_order']]"
assert source.count(old)==1;source=source.replace(old,new)
source=source.replace("'current_inherited_source.py'", "'current_inherited_source_v2.py'")
source=source.replace("    pin(__file__)", "    pin(ROOT/'tools/m4-startup131-original/seal_inherited_source.py');pin(ROOT/'tools/m4-startup131-original/derive_inherited_seal_v2.py');pin(__file__)")
target=T/'seal_inherited_source_v2.py';assert not target.exists();target.write_text(source)
aggregate=T/'current_inherited_source.py';text=aggregate.read_text();assert text.count('inherited-source-preparation-r2')==1;text=text.replace('inherited-source-preparation-r2','inherited-source-preparation-r3');new_aggregate=T/'current_inherited_source_v2.py';assert not new_aggregate.exists();new_aggregate.write_text(text)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
failed=R/'reports/m4-startup131-original/inherited-source-preparation-r2/report.json';assert not failed.exists();failed.write_text(json.dumps(dict(passed=False,scope='Unexecuted source-continuity preparation failed comparing entire selected_order metadata dictionaries: historical130 stores phase while current131 stores physical slot/entry only. No source bytes, schedule pair, worker or capture failure.',failure='Exactly130 original root table/order pairs survive insertion',files={str(base.resolve()):sha(base)},capture_reader_opened=False,source_comparison_executed=False,initializer_credit=0),indent=2)+'\n')
q=T/'inherited-seal-v2-lineage.json';q.write_text(json.dumps(dict(base=str(base),base_sha256=sha(base),generated=str(target),generated_sha256=sha(target),previous_aggregate=str(aggregate),previous_aggregate_sha256=sha(aggregate),aggregate=str(new_aggregate),aggregate_sha256=sha(new_aggregate),changes=['Physical table pair comparison excludes optional phase metadata only','Aggregate binds fresh successful preparation-r3'],literal_semantics_changed=False,capture_reader_opened=False),indent=2)+'\n');print(target)
