"""Bind this CMake builder's actual Ninja inputs instead of a different schema."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
parent=Path(__file__).with_name('review_joint138_prelaunch_v2.py')
recipe=parent.read_text()
anchor="exec(compile(source,str(Path(__file__)),'exec'),globals())"
assert recipe.count(anchor)==1
extension=r'''
old=source[source.index("   cmds=[x for x in b['commands']"):source.index("   counts['current_inherited_literal_inputs']+=410")]
new='''   tree=Path(info['worker']).parent
   ninja=pin(tree/'build.ninja').read_text()
   lines=ninja.splitlines();rows=[x for x in lines if x.startswith('build mw34_joint_startup138.exe:')]
   assert len(rows)==1 and ': CXX_EXECUTABLE_LINKER__mw34_joint_startup138_Release 'in rows[0]
   actual=rows[0].replace('$:',':').split()
   assert all(str(q)in actual for q in parent_objects)
   libraries=[x for x in lines if x.startswith('  LINK_LIBRARIES = ')];assert len(libraries)==1 and info['widget_library']in libraries[0].split()
   builds=[x for x in b['commands']if '--build'in x['arguments']and str(tree)in x['arguments']];assert len(builds)==1 and builds[0]['exit_code']==0
   deps=[x for x in b['commands']if '-t'in x['arguments']and 'deps'in x['arguments']and str(tree)in x['arguments']];assert len(deps)==1 and deps[0]['exit_code']==0
   pin(tree/'.ninja_log');pin(tree/'.ninja_deps')
'''
assert source.count(old)==1;source=source.replace(old,new)
source=source.replace('  pin(p);pin(__file__);pin(sys.executable)',"  pin(R/'tools/m4-tree-review/review_joint138_prelaunch.py');pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v2.py');pin(__file__);pin(sys.executable)")
'''
recipe=recipe.replace(anchor,extension+'\n'+anchor)
exec(compile(recipe,str(Path(__file__)),'exec'),globals())
