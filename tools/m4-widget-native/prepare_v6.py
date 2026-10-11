"""Preserve failed preparer5; avoid its inherited prior variable shadow."""
from pathlib import Path
R=Path(__file__).resolve().parents[2];generator=R/'tools/m4-widget-native/prepare_v5.py';s=generator.read_text();a='pin(__file__);pin(prior);';b="pin(__file__);pin(R/'tools/m4-widget-native/prepare_v5.py');pin(R/'tools/m4-widget-native/prepare_v4.py');";assert s.count(a)==1
exec(compile(s.replace(a,b),str(generator),'exec'),globals())
