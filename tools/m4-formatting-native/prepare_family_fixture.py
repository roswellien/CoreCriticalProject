"""Actual four-root Runtime fixture; preserve executed three-root generator."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('prepare_fixture.py');s=p.read_text()
def one(a,b):
    global s
    assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
one('objects={}',"""import importlib.util
    pe_path=pin(R/'tools/analysis/pe.py');spec=importlib.util.spec_from_file_location('formatter4_fixture_physical_pe',pe_path);P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P);physical_game=P.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
    objects={} """)
one("b['source_bytes'];s+=","b['source_bytes'];physical_root_sha=hashlib.sha256(physical_game.read(physical_game.rva_range(root-physical_game.image_base,extent)[0],extent)).hexdigest();s+=")
s=s.replace('{b["source_sha256"]}','{physical_root_sha}')
one('std::array<unsigned,100> registration_roots{','std::array<unsigned,101> registration_roots{')
one('0x5968f0,0x4b7f70,0x4df610,0x4e0710,0x4e0810};','0x5968f0,0x4b7f70,0x4df610,0x4e0710,0x4e0810,0x4e1ca0};')
one('constexpr std::array<std::uint32_t,3> entries{0x4df610,0x4e0710,0x4e0810};','constexpr std::array<std::uint32_t,4> entries{0x4df610,0x4e0710,0x4e0810,0x4e1ca0};')
one('phase==3&&r_.calls().size()==3&&r_.translation_count()==129','phase==4&&r_.calls().size()==4&&r_.translation_count()==130')
s=s.replace('390','396')
one('phase<3,"Three actual formatting before phases"','phase<4,"Four actual formatting before phases"')
one('phase>=1&&phase<=3,"Three actual formatting after phases"','phase>=1&&phase<=4,"Four actual formatting after phases"')
one('result&&t.completed==3&&sample.tags[9]==0&&sample.tags[10]==0','result&&t.completed==4&&sample.tags[9]==2&&sample.tags[10]==3')
one('pin(__file__);files=',"pin(__file__);pin(R/'tools/m4-formatting-native/prepare_fixture.py');files=")
s=s.replace('formatting3','formatting4').replace('three formatter roots','four formatter roots')
exec(compile(s,str(p),'exec'),globals())
