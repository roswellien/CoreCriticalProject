"""Correct inherited static body cardinality, retain failed r1 tool/output."""
from pathlib import Path
import json
T=Path(__file__).resolve().parent;R=T.parents[1]
s=(T/'symbol_attribution.py').read_text();old='len(mapping) == 22 and len(objects) == 44';assert s.count(old)==1;s=s.replace(old,'len(mapping) == 15 and len(objects) == 30');(T/'symbol_attribution_v2.py').write_text(s)
p=R/'reports/m4-next-source/symbol-attribution-r1';(p/'failure.json').write_text(json.dumps(dict(passed=False,reason='Inherited old22/44 cardinality assertion; all15/30 physical function checks had completed, no source or COFF changes. Additive v2 uses actual current family count.'))+'\n')
