"""ROOT terminal-only admission recipe v3; refuses partial composer output.

v3 = v2 plus the reviewer v4 pin (reviewer v3 refused hashing four declared .pyc
physical inputs; see reviewer-v4-preparation-r1). v4 identity is taken from that
preparation record, which proves the exact v4->v3 inverse and hook controls.
"""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 root=R/'reports/m4-controls-terminal-composite/terminal-composite-r1'
 marker=root/'independent-review-required.json';assert marker.is_file(),'Composer has not emitted a terminal marker'
 receipt=json.loads(marker.read_bytes());assert receipt['prepared']is True and receipt['accepted_function_credit']==0
 pins={}
 def pin(rel,h):
  p=(R/rel).resolve();assert sha(p)==h;assert str(p)not in pins or pins[str(p)]==h;pins[str(p)]=h;return p
 def read(rel,h):return json.loads(pin(rel,h).read_bytes())
 parent=read('reports/m4-controls-terminal-composite/root-composer-admission-r1/report.json','83ea5b4d4e26c7054b30b70777c7eff2e4cc1b4e6f9e71ad6e1b1af059a9d373')
 reviewed=read('reports/m4-controls-terminal-composite/root-composite-reviewer-source-review-r1/report.json','236403d6caf13543178690c90c9aa5d833c5ea47cc057e1e92f62b6347f21018')
 assert parent['passed']is True and parent['terminal_controls_composer_admitted']is True
 assert reviewed['passed']is True and reviewed['exact_v1_v2_v3_inverses']is True and reviewed['final_full_union_and_direct_input_conservation_reviewed']is True
 assert reviewed['pure_domain_adverses']==20 and reviewed['pure_final_mutation_adverses']==3
 for path,h in reviewed['files'].items():pin(path,h)
 # The reviewer loads this streamed-metadata parser through its admitted-pin
 # check; carry the exact composer-admitted SHA forward, never a fresh hash.
 parser=str((R/'tools/m4-138-controls-review/full_raw_review_v2.py').resolve());assert parser in parent['files'];pin(parser,parent['files'][parser])
 prep4=read('reports/m4-controls-terminal-composite/reviewer-v4-preparation-r1/report.json','0c2766c4e8d0fe6b3a5a0b6e47629fa0cbc038fe546fa873165f06335a6e3784')
 assert prep4['prepared_only']is True and prep4['exact_v4_v3_inverse']is True and len(prep4['adverse_controls'])==5 and not prep4['production_review_executed']
 reviewer4=str((R/'tools/m4-controls-terminal-composite/review_completed_composite_v4.py').resolve());pin(reviewer4,prep4['files'][reviewer4])
 reviewer3=str((R/'tools/m4-controls-terminal-composite/review_completed_composite_v3.py').resolve());assert prep4['files'][reviewer3]==pins[reviewer3],'v4 derived from the same reviewed v3'
 mp='reports/m4-controls-terminal-composite/completed-input-preparation-r4/completed-input-manifest.json';mh='e8e3c1ecd45784a51355e7f89fc30b7eb7977ed85598d0f85746823d77cf0251';M=read(mp,mh)
 assert M['actual_terminals_complete']is True and len(M['roles'])==14
 for row in M['roles'].values():assert parent['files'][row['path']]==row['sha256'];pin(row['path'],row['sha256'])
 # No active database read, SQL connection or inferred receipt from file growth.
 gate_hashes={};gates={}
 for label,leaf in [('controls_preparation','controls-preparation.json'),('controls_prelaunch','controls-prelaunch.json'),('controls','controls.json')]:
  p=root/leaf;assert p.is_file()and p.stat().st_size<2*1024*1024;h=sha(p);g=json.loads(p.read_bytes());assert g['passed']is True;pin(p,h);gate_hashes[label]=h;gates[label]=g
 c=gates['controls'];assert receipt['controls_sha256']==gate_hashes['controls'] and Path(receipt['controls_path']).resolve()==(root/'controls.json').resolve()
 assert c['raw_export_readers_closed']is True and c['all_bounded_readers_closed']is True and c['raw_exports_all_logical_entries']is True and c['initializer_credit']==0
 i=c['proof_inventory'];assert i['sqlite_closed_before_hash']is True and i['every_row_whole_byte_rehashed']is True
 database=Path(i['path']).resolve();assert database==root/'whole-ordinary-union.sqlite' and database.stat().st_size==i['bytes']
 assert not Path(str(database)+'-journal').exists(),'Database transaction still active'
 pin(database,i['sha256']);pin(marker,sha(marker));pin(sys.executable,'4942b86a6597e5aee0128daa00050ed79bc21f6e709a78eb19cbfeb0c2f39ac9')
 fields={}
 for key,rel,h in [('mapping45','reports/m4-138-criteria-frontier/terminal45-typed-recipe-r1/pending45-terminal-field-mapping.json','79d6141deea3f2a7cc7faa58d2a1ada78a3122f3147d5fa90dbddb8b5ddce756'),('field_disposition','reports/m4-controls-terminal-composite/field-disposition-r1/per-field-disposition.json','fbc42704a584377455d0d85593127c547ccfaf47e04f73c4714cbf1b972137c7'),('proposal6','reports/m4-138-controls-review/root-criterion-delta-proposal-r6/report.json','626c590fdde8e2077b4fa1fa2decdd76ef07f762466c0aad92a8fd81fe447505')]:
  p=pin(rel,h);fields[key]=dict(path=str(p),sha256=h)
 for p,h in list(pins.items()):assert sha(p)==h,p
 pins[str(Path(__file__).resolve())]=sha(__file__)
 out=R/'reports/m4-controls-terminal-composite/root-completed-review-admission-r2';assert not out.exists();out.mkdir()
 value=dict(passed=True,independent_review=True,scope_identity='completed_controls_composite_independent_review',controls_sha256=gate_hashes['controls'],reviewed_role_bindings=M['roles'],composite_gate_hashes=gate_hashes,files=pins,accepted_function_credit=0,acceptance_admitted=False,**fields)
 p=out/'report.json';p.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(dict(admission=str(p),sha256=sha(p),controls_sha256=gate_hashes['controls'],manifest_path=str(R/mp),manifest_sha256=mh)))
if __name__=='__main__':main()
