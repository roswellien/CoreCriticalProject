"""Scope two unreferenced emitted helpers to their reviewed inlined callers."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_original138_prelaunch_v3.py')
scope={'__file__':str(p),'__name__':'materialize_original138_inlined_review'}
exec(compile(p.read_text(),str(p),'exec'),scope)
t=scope['t']
a="        pending=list(names)"
assert t.count(a)==1
b='''        omitted={'_widget_fs_observe_before','?constructor_capacity@@YAIII@Z'}
        assert omitted <= set(names)
        for q in release.glob('*.obj'):
            osy,ose=C.coff(pin(q).read_bytes())
            for section in ose.values():
                for rel in section['relocations']:
                    if rel['symbol']['name'] in omitted:
                        assert not section['flags']&0x20000000
                        counts['unreferenced_helpers_nonexecuting_metadata_relations']+=1
        for n in omitted:
            assert any(v['name']==n and v['section']>0 and v['type']==0x20 for v in sy.values())
        assert '_fs_observe_before' in names and '_main' in names
        names=[n for n in names if n not in omitted]
        counts['explicit_unreferenced_emitted_helpers_scoped_to_whole_callers']=2
        pending=list(names)'''
t=t.replace(a,b,1)
a="        pin(R/'tools/m4-tree-review/review_original138_prelaunch_v2.py')"
assert t.count(a)==1
t=t.replace(a,"        pin(R/'tools/m4-tree-review/review_original138_prelaunch_v3.py')\n"+a,1)
exec(compile(t,str(Path(__file__)),'exec'),globals())
