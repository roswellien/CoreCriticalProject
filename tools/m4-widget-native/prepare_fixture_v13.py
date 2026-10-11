"""Bind the added precise lower-tail body and exact52 metadata, guards fixed."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
prior=R/'tools/m4-widget-native/prepare_fixture_v10.py';code=prior.read_text()
changes=[('reports/m4-widget-native/preparation-r3','reports/m4-widget-native/preparation-r4'),('69a29eddf46f6c189edc462e5f5734a96e3d98c2c1f37778a54d36c0fd62eae5','e14facb79ef65c71502564223c034447b68ff58af1ae26e3d7efee8160d2bae0'),('reports/m4-widget-native/build-r5','reports/m4-widget-native/build-r6'),('9c053306dbf44a3a65ac1945dd4c2b0949ef064842004e05bf2e6cc29a22fada','b2cdf1f8e13dd6b655f8015ca8ea1ab6b49bf375ad14f0b0ffa9a81f36b5748a')]
for a,b in changes:code=code.replace(a,b)
anchor="exec(compile(s,str(previous),'exec'),globals())"
extra="""s=s.replace('reports/m4-widget-native/service-preparation-r2','reports/m4-widget-native/service-preparation-r3').replace('d10b800a817dd3fc684f276d5df19154748b2b0735137d062d9bff05376a1fca','3fdc66a791fd81437fe56500b2d3a8340e45149fd97a4980add749135a9845fd')
s=s.replace('fixture_v4.cpp','fixture_v5.cpp').replace("'literal_bodies':51", "'literal_bodies':52")
s=s.replace("previous,R/'tools/m4-widget-native/prepare_fixture_v9.py'", "previous,R/'tools/m4-widget-native/prepare_fixture_v9.py',R/'tools/m4-widget-native/prepare_fixture_v10.py',R/'tools/m4-widget-native/prepare_fixture_v11.py',R/'tools/m4-widget-native/prepare_fixture_v12.py',R/'tools/m4-widget-native/derive_fixture_v9.py',R/'tools/m4-widget-native/fixture_v4.cpp'")
s=s.replace("'fixture_code_changed':False", "'fixture_code_changed':True,'fixture_metadata_literal_count_changed':True,'fixture_semantic_guards_changed':False,'normal_backward_tail_added':5916048")
exec(compile(s,str(previous),'exec'),globals())"""
assert code.count(anchor)==1
exec(compile(code.replace(anchor,extra),str(prior),'exec'),globals())
