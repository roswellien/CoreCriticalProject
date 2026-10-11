"""Attribute identical FPS/GDI entry bytes through their actual observer CALL."""
from pathlib import Path
V3=Path(__file__).with_name('review_fps_original_prelaunch_v3.py')
program=V3.read_text()
addition=r'''
  cpp_symbols,cpp_sections=C.coff(blob(release/'reference.obj'))
  cpp_fps=C.linked_function(worker,cpp_symbols,cpp_sections,'_fps_observe');cpp_widget=C.linked_function(worker,cpp_symbols,cpp_sections,'_widget_observe')
  actual_observers={'_fps_entry':('_fps_observe',cpp_fps['address']),'_widget_stock_entry':('_widget_observe',cpp_widget['address'])}
  import ast
  helper_source=pin(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py').read_text();tree=ast.parse(helper_source);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='linked_function')
  function='\n'.join(helper_source.splitlines()[node.lineno-1:node.end_lineno])
  needle="    need(len(candidates) == 1, 'Unique whole linked nonrelocated function bytes ' + name)"
  attribution="    if name in actual_observers:\n        symbol,target=actual_observers[name]\n        calls=[r for r in relocs if r['type']==0x14 and r['symbol']['name']==symbol]\n        need(len(calls)==1,'One exact physical observer CALL')\n        i=calls[0]['offset'];original=struct.unpack_from('<I',raw,i)[0]\n        candidates=[(a,b)for a,b in candidates if (a+i+4+struct.unpack_from('<I',b,i)[0]-original)&0xffffffff==target]\n"
  assert function.count(needle)==1
  namespace=dict(C.__dict__,actual_observers=actual_observers);exec(compile(function.replace(needle,attribution+needle),'physical_observer_attribution','exec'),namespace)
  original_link=C.linked_function;C.linked_function=namespace['linked_function']
'''
anchor='exec(compile(program,str(BASE),\'exec\'),globals())'
assert program.count(anchor)==1
injection="\nprogram=program.replace(\"  symbols,sections=C.coff(blob(release/'fps_observer_x86.obj'))\",addition+\"  symbols,sections=C.coff(blob(release/'fps_observer_x86.obj'))\")\nprogram=program.replace('pin(V2);pin(BASE);pin(R/','pin(V3);pin(V2);pin(BASE);pin(R/')\n"
program=program.replace(anchor,injection+anchor)
exec(compile(program,str(V3),'exec'),globals())
