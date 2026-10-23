"""Preserve absent named CS24/TLS64 counters as pending, no inference."""
from pathlib import Path
p=Path(__file__).with_name('map_terminal_strict24_v3.py');s=p.read_text();a="ns={'__file__':str(Path(__file__).resolve()),'__name__':'metadata_only'};exec(compile(s,str(p),'exec'),ns);ns['main']('strict24-named-facet-mapping-r3')"
b="""a=\"count=field.split('.',1)[1];assert count in totals,(gate,count);value=totals[count];source='exact strict24 named counts.'+count\"
b=\"count=field.split('.',1)[1];value=totals[count]if count in totals else None;source='exact strict24 named counts.'+count if count in totals else 'MISSING actual named '+count+' facet; raw evidence needs substantive additional check'\"
assert s.count(a)==1;s=s.replace(a,b)
ns={'__file__':str(Path(__file__).resolve()),'__name__':'metadata_only'};exec(compile(s,str(p),'exec'),ns);ns['main']('strict24-named-facet-mapping-r4')"""
assert s.count(a)==1;s=s.replace(a,b);exec(compile(s,str(p),'exec'))
