"""Keep failed preparations; distinguish entry objects from full connected link inputs."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('prepare_family4.py');s=p.read_text();a='assert len(rows)==230';assert s.count(a)==1;s=s.replace(a,'assert len(rows)==218')
a='assert len(objects)==2*expected_family_objects,(len(objects),expected_family_objects)';assert s.count(a)==1;s=s.replace(a,'assert len(objects)==len(parent["entry_objects"])+12,(len(objects),len(parent["entry_objects"]))')
a='literal_objects_per_level=396,ordinary_pages=46';assert s.count(a)==1;s=s.replace(a,'literal_objects_per_level=396,entry_objects_per_level=len(objects)//2,ordinary_pages=46')
s=s.replace('pin(__file__)',"pin(__file__);pin(R/'tools/m4-formatting-native/prepare_family4.py')")
exec(compile(s,str(p),'exec'),globals())
