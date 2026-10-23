from pathlib import Path
p=Path(__file__).with_name('root_review_format_module_v1.py')
s=p.read_text()
a=" for q,s in v['files'].items():pin(q,s)"
b=" for q,s in v['files'].items():\n  if Path(q).suffix.lower() in ('.mwb','.mwi','.zip') or Path(q).name=='transport.json':continue\n  pin(q,s)"
assert s.count(a)==1;s=s.replace(a,b)
s=s.replace('format-module-root-measured-r1','format-module-root-measured-r3').replace('format-module-root-review-r1','format-module-root-review-r3')
a='archive_reader_opened=False,initializer_credit=0,files=pins'
b='archive_reader_opened=False,capture_hashes_deferred_to_final_acceptance_union=True,initializer_credit=0,files=pins'
assert s.count(a)==1;s=s.replace(a,b)
q=p.with_name('root_review_format_module_v3.py');assert not q.exists();q.write_text(s)
