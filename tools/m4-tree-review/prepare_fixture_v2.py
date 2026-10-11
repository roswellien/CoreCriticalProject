"""Carry43 ordinary pages plus21 extra source pages and lower stack explicitly."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).resolve().parent/'prepare_fixture.py'
s=p.read_text(encoding='utf-8')
s=s.replace("need(len(pages)==44,'Complete43 ordinary scope plus lower source stack')",
            "need(len(pages)==65,'Complete43 ordinary +21 extra source pages +lower stack')")
s=s.replace('ordinary_pages=43,separately_carried_lower_stack=1,current_pages=pages',
            'ordinary_pages=43,extra_source_pages=21,separately_carried_lower_stack=1,total_current_pages=65,current_pages=pages')
s=s.replace('pin(__file__)',"pin(__file__);pin(R/'tools/m4-tree-review/prepare_fixture.py')")
exec(compile(s,str(p),'exec'),globals())
