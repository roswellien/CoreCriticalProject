"""ROOT bounded ordinary key selection; no source execution or archive reader."""
from pathlib import Path
import hashlib, importlib.util, json, sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 assert name=='root-CRT-key-selection-r3'
 code=R/'tools/m4-142-component-review/prepare_CRT_key_selection_v2.py'
 assert sha(code)=='03ce926601dabf6e56abf7b6c18a23a719d57aac7d779ae1adfe3a06dc85ebf4'
 preparation=R/'reports/m4-142-component-review/key-selector-preparation-r3/report.json'
 assert sha(preparation)=='7479bdd8675959470f321d52bd8e5c9b493de5e8b462f80d7942a5b06609f5c3'
 prepared=json.loads(preparation.read_bytes());back=code.read_text()
 for change in reversed(prepared['changes']):
  assert back.count(change['after'])==1;back=back.replace(change['after'],change['before'])
 assert back==(code.with_name('prepare_CRT_key_selection_v1.py')).read_text()
 for path,h in prepared['files'].items():assert sha(path)==h
 recipe=R/'reports/m4-142-component-review/prefix-recipe-r2/recipe.json'
 assert sha(recipe)=='d89bc88238f59a11979819a6a68ecd590b2d238c026783303554129801514efc'
 source=R/'reports/m4-startup141-source/combined-source-provider-r6/report.json'
 assert sha(source)=='8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3'
 S=json.loads(source.read_bytes());C=json.loads(recipe.read_bytes())
 assert S['passed'] is True and S['reader_closed'] is True
 pins={str(p):sha(p) for p in (code,recipe,source,Path(__file__).resolve())}
 rows=[v for v in C['exports'] if v['branch'] in ('O0','O2')]
 assert len(rows)==2 and {v['branch'] for v in rows}=={'O0','O2'}
 for row in rows:
  actual=next(v for v in S['paired_exports'] if v['branch']==row['branch'])
  for field in ('index_path','index_sha256','payload_path','payload_sha256','payload_bytes','logical_files'):
   assert row[field]==actual[field]
  for field in ('index','payload'):
   p=Path(row[field+'_path']).resolve();h=row[field+'_sha256']
   assert S['files'][str(p)]==h and sha(p)==h
   if field=='payload':assert p.stat().st_size==row['payload_bytes']
   pins[str(p)]=h
 out=R/'reports/m4-142-component-review'/name;assert not out.exists()
 spec=importlib.util.spec_from_file_location('ROOT_reviewed_CRT_keys',code)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 module.main(str(out))
 q=out/'report.json';d=json.loads(q.read_bytes())
 assert d['passed'] is True and d['canonical_reader_opened'] is False and d['source_executed'] is False and d['State_created'] is False and d['accepted_credit']==0
 assert set(d['exact_keys'])=={'O0','O2'} and all(len(v)==96 for v in d['exact_keys'].values())
 for p,h in pins.items():assert sha(p)==h
 evidence=dict(passed=True,scope='Independent ROOT fixed native141 ordinary export identity and bounded checkpoint key selection',selector_report_sha256=sha(q),whole_native_ordinary_exports_rehashed=True,canonical_reader_opened=False,source_executed=False,CRT_timing_proven=False,loaded_HYPOT_ownership_proven=False,accepted_function_credit=0,files=pins)
 (out/'ROOT-physical-review.json').write_text(json.dumps(evidence,indent=2)+'\n')
 print(sha(q));print(sha(out/'ROOT-physical-review.json'))
if __name__=='__main__':main(sys.argv[1])
