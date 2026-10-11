"""Bind Runtime root extent to genuine contiguous PE bytes, not sparse lift fill."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('prepare_fixture.py');s=p.read_text();a='objects={}';assert s.count(a)==1
s=s.replace(a,"""import importlib.util
    pe_path=pin(R/'tools/analysis/pe.py');spec=importlib.util.spec_from_file_location('formatter_fixture_physical_pe',pe_path);P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P);physical_game=P.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
    objects={}""")
a="b['source_bytes'];s+=";assert s.count(a)==1;s=s.replace(a,"b['source_bytes'];physical_root_sha=hashlib.sha256(physical_game.read(physical_game.rva_range(root-physical_game.image_base,extent)[0],extent)).hexdigest();s+=")
s=s.replace('{b["source_sha256"]}','{physical_root_sha}');s=s.replace('pin(__file__);files=',"pin(__file__);pin(R/'tools/m4-formatting-native/prepare_fixture.py');files=")
exec(compile(s,str(p),'exec'),globals())
