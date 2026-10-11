"""Freeze proof-only raw exports around the unchanged v3 control semantics."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=ROOT/'tools/m4-mfc1168-native/verify_connected_controls_v3.py'
assert sha(old)=='e8afb884449049c7ae11df617361b94c123694ac94bddbb1dbccdb3331885835'
exports=ROOT/'tools/m4-joint-startup131/paired_exports.py'
assert sha(exports)=='310e15f0771856c1da234ce0f69019b7620e9f27eb46a60b44a686cc6a263ce9'
text=old.read_text()
needle="exec(compile(text,str(parent),'exec'),globals())"
addition=r'''# These transformations add equality-target copies after every semantic
# predicate has run, before the same strict canonical reader is closed.
old="counts=collections.Counter();cases=[];proofs={};identities=[]"
new=old+";raw_exports=[]"
assert text.count(old)==1;text=text.replace(old,new)
old="  MF=load(ROOT/'tools/m4-joint-startup131/mfc_source.py','mfc_causal_control_literal_adapter');"
new="  X=load(ROOT/'tools/m4-joint-startup131/paired_exports.py','mfc_control_raw_exports');"+old.strip()
assert text.count(old)==1;text=text.replace(old,new)
old="a=DS.DirectSet(row['capture'],pin);closed=False"
new=old+";export=X.Export(out/'raw-controls',level,a.path,pin)"
assert text.count(old)==1;text=text.replace(old,new)
old="   finally:a.close();a.entries.clear();a.bundles.clear();del a;closed=True"
new="""    for key in sorted(a.entries):export.write(key,a.data(key))
    raw_exports.append(export.finish())
   finally:export.close();a.close();a.entries.clear();a.bundles.clear();del a;closed=True"""
assert text.count(old)==1;text=text.replace(old,new)
old="dict(passed=passed,execution=str(execution),execution_sha256=digest,scope="
new="dict(passed=passed,raw_exports=raw_exports,raw_exports_all_logical_entries=True,raw_export_readers_closed=closed,execution=str(execution),execution_sha256=digest,scope="
assert text.count(old)==1;text=text.replace(old,new)
text=text.replace("pin(ROOT/'tools/m4-mfc1168-native/verify_connected_controls_v3.py');", "pin(ROOT/'tools/m4-mfc1168-native/verify_connected_controls_v4.py');pin(ROOT/'tools/m4-mfc1168-native/verify_connected_controls_v3.py');")
exec(compile(text,str(parent),'exec'),globals())'''
assert text.count(needle)==1;text=text.replace(needle,addition)
target=ROOT/'tools/m4-mfc1168-native/verify_connected_controls_v4.py'
assert not target.exists();target.write_text(text)
out=ROOT/'reports/m4-mfc1168-native/connected-controls-checker-preparation-r4'
assert not out.exists();out.mkdir()
pins={str(p.resolve()):sha(p)for p in(old,exports,target,Path(__file__),ROOT/'tools/m4-mfc1168-native/verify_connected_controls.py')}
report=dict(passed=True,scope='Proof-only all logical equality-target exports from each existing canonical controls reader after unchanged v3 semantics and before close; no equality/source/refusal/lifecycle delta',parent=str(old.resolve()),parent_sha256=sha(old),checker=str(target.resolve()),checker_sha256=sha(target),raw_exports_schema='paired_exports Export contiguous payload/index; O0 and O2 branches, all 4345 logical entries each; no selection exclusions',semantic_predicates_changed=False,source_evaluator_changed=False,canonical_reader_changed=False,files=pins)
q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report=str(q),sha256=sha(q),checker_sha256=sha(target))))
