"""Independently attribute the corrected complete contracts-file relation."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_version_original_prelaunch_v9.py')
scope={'__file__':str(p),'__name__':'materialize_corrected_isolation_relations'}
exec(compile(p.read_text(),str(p),'exec'),scope)
t=scope['t']
a="   before=pin(row['parent'],row.get('parent_sha256',row['sha256'])).read_bytes();after=pin(row['child'],row['sha256']).read_bytes()"
assert t.count(a)==1
t=t.replace(a,"""   if Path(row['child']).name=='contracts.json':
    before=read(row['parent'],'fae34c1c41a7a4832488300a93bba234fea192fa53721077fb276d6cd8b3ec36')
    after=read(row['child'],'6e5ed33530b2dad06f0424ba86ea7b8193a3121460a900f8f11dbefb75bd5a4f')
    extra={'actual_loaded_and_expected_provider_whole_file_IDs':True,'independent_same_physical_provider_file_equivalence':True,'raw_loaded_provider_paths_retained':True}
    assert set(after)-set(before)==set(extra) and after==dict(before,**extra)
    counts['explicit_corrected_contracts_whole_file_relation']+=1
    continue
   before=pin(row['parent'],row.get('parent_sha256',row['sha256'])).read_bytes();after=pin(row['child'],row['sha256']).read_bytes()""")
a="len(changed)==1 and counts['whole_retained_original_inputs']==17"
assert t.count(a)==1;t=t.replace(a,"len(changed)==1 and counts['whole_retained_original_inputs']==16 and counts['explicit_corrected_contracts_whole_file_relation']==1")
a="  changed=[]"
assert t.count(a)==1
t=t.replace(a,"  correction=read(R/'reports/m4-version-source/original6-relation-correction-r1/report.json','298b8ba1c253a3bd82e514757112dc25199ebfe6d8962d69806421d1a09cbac7');assert correction['passed']\n"+a)
a="sorted(x.attrib for x in root.findall(ns+'file'))"
assert t.count(a)==1;t=t.replace(a,"sorted([x.attrib for x in root.findall(ns+'file')],key=lambda x:x['name'])")
a="pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v8.py');"
assert t.count(a)==1;t=t.replace(a,"pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v9.py');"+a)
exec(compile(t,str(Path(__file__)),'exec'),globals())
