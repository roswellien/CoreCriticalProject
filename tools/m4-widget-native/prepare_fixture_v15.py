"""Bind actual52 DLL component; keep precise fixture5 semantics immutable."""
from pathlib import Path
R=Path(__file__).resolve().parents[2];generator=R/'tools/m4-widget-native/prepare_fixture_v13.py';code=generator.read_text()
changes=[('reports/m4-widget-native/preparation-r4','reports/m4-widget-native/preparation-r6'),('e14facb79ef65c71502564223c034447b68ff58af1ae26e3d7efee8160d2bae0','714a5f0093a62e68911f78c93a07d34e4bd9f4b39e79e0931a4812bee6877ed9'),('reports/m4-widget-native/build-r6','reports/m4-widget-native/build-r7'),('b2cdf1f8e13dd6b655f8015ca8ea1ab6b49bf375ad14f0b0ffa9a81f36b5748a','7bba3319abef8202d154229ba4243dadd6e2693381c86abcbd41bf41007d20bf')]
for a,b in changes:assert code.count(a)==1;code=code.replace(a,b)
a="R/'tools/m4-widget-native/derive_fixture_v9.py',R/'tools/m4-widget-native/fixture_v4.cpp'"
b="R/'tools/m4-widget-native/derive_fixture_v9.py',R/'tools/m4-widget-native/derive_fixture_v10.py',R/'tools/m4-widget-native/prepare_fixture_v13.py',R/'tools/m4-widget-native/prepare_fixture_v14.py',R/'tools/m4-widget-native/fixture_v4.cpp'"
assert code.count(a)==1
exec(compile(code.replace(a,b),str(generator),'exec'),globals())
