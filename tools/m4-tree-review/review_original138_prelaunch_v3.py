"""Resolve identical observer bodies through actual whole-linked callers."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_original138_prelaunch_v2.py')
scope={'__file__':str(p),'__name__':'materialize_original138_target_review'}
exec(compile(p.read_text(),str(p),'exec'),scope)
t=scope['t']
a="        C=module(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','original138_coff')"
assert t.count(a)==1
t=t.replace(a,a+'''
        import inspect
        helper=inspect.getsource(C.linked_function)
        guard="    need(len(candidates) == 1, 'Unique whole linked nonrelocated function bytes ' + name)"
        assert helper.count(guard)==1
        helper=helper.replace(guard,"    if name in incoming: candidates=[v for v in candidates if v[0]==incoming[name]]\\n"+guard,1)
        C.incoming={}
        exec(compile(helper,str(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py'),'exec'),C.__dict__)
''',1)
a='''        for n in names:
            proof=C.linked_function(worker,sy,se,n)
            links.append(dict(proof,family='CPP'))
            counts['whole_linked_CPP_functions']+=1'''
assert t.count(a)==1
b='''        pending=list(names)
        while pending:
            progress=False
            for row in links:
                for rel in row['relocations']:
                    if rel['symbol_section']==0 and rel['resolution_kind']=='virtual address':
                        n,a=rel['symbol'],rel['actual_symbol_address']
                        assert n not in C.incoming or C.incoming[n]==a,(n,C.incoming.get(n),a)
                        C.incoming[n]=a
            for n in list(pending):
                try:
                    proof=C.linked_function(worker,sy,se,n)
                except ValueError as error:
                    assert str(error)=='Unique whole linked nonrelocated function bytes '+n
                    continue
                if n in C.incoming:
                    assert proof['address']==C.incoming[n]
                    counts['whole_functions_joined_to_actual_incoming_targets']+=1
                links.append(dict(proof,family='CPP'))
                counts['whole_linked_CPP_functions']+=1
                pending.remove(n)
                progress=True
            assert progress, pending'''
t=t.replace(a,b,1)
a='        pin(parent)'
assert t.count(a)==1
t=t.replace(a,"        pin(R/'tools/m4-tree-review/review_original138_prelaunch_v2.py')\n"+a,1)
exec(compile(t,str(Path(__file__)),'exec'),globals())
