"""Use corrected extent-before/measured-capacity-after caller service only."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
prior=R/'tools/m4-widget-native/prepare_fixture_v10.py';code=prior.read_text()
anchor="exec(compile(s,str(previous),'exec'),globals())"
replacement="""s=s.replace('reports/m4-widget-native/service-preparation-r2','reports/m4-widget-native/service-preparation-r3').replace('d10b800a817dd3fc684f276d5df19154748b2b0735137d062d9bff05376a1fca','3fdc66a791fd81437fe56500b2d3a8340e45149fd97a4980add749135a9845fd')
s=s.replace(\"previous,R/'tools/m4-widget-native/prepare_fixture_v9.py'\",\"previous,R/'tools/m4-widget-native/prepare_fixture_v9.py',prior\")
exec(compile(s,str(previous),'exec'),globals())"""
assert code.count(anchor)==1
exec(compile(code.replace(anchor,replacement),str(prior),'exec'),globals())
