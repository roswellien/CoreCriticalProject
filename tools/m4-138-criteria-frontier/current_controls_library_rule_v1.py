"""Exact current Ninja worker rule/implicit input/LINK_LIBRARIES agreement."""
from pathlib import Path
def prove(graph,worker,library):
 worker=Path(worker).resolve();library=Path(library).resolve()
 assert worker.name=='mw34_widget_context_controls.exe'
 lines=graph.splitlines();matches=[i for i,line in enumerate(lines)if line.startswith('build '+worker.name+': ')]
 assert len(matches)==1;at=matches[0];rule=lines[at]
 prefix='build '+worker.name+': CXX_EXECUTABLE_LINKER__mw34_widget_context_controls_Release '
 assert rule.startswith(prefix)
 parts=rule[len(prefix):].split(' | ');assert len(parts)==2 and ' || 'not in rule
 implicit=parts[1].split();assert len(implicit)==1
 assert Path(implicit[0].replace('$:',':')).resolve()==library
 block=[]
 for line in lines[at+1:]:
  if not line.startswith('  '):break
  block.append(line)
 properties=[line for line in block if line.startswith('  LINK_LIBRARIES = ')]
 assert len(properties)==1
 tokens=properties[0][len('  LINK_LIBRARIES = '):].split()
 assert Path(tokens[0]).resolve()==library
 assert tokens[1:]==['bcrypt.lib','user32.lib','kernel32.lib','user32.lib','gdi32.lib','winspool.lib','shell32.lib','ole32.lib','oleaut32.lib','uuid.lib','comdlg32.lib','advapi32.lib']
 assert sum(Path(t.replace('$:',':')).resolve()==library for t in tokens)==1
 return dict(worker=str(worker),whole_rule=rule,implicit_library=implicit[0],whole_LINK_LIBRARIES=properties[0],owning_library=str(library),SDK_libraries=tokens[1:])
