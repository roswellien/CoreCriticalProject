"""Same immutable141 compiler; exact410object list moved to CMake cache file."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
parent=Path(__file__).with_name('build_full141.py')
source=parent.read_text()
needle="exec(compile(source,str(parent),'exec'),globals())"
assert source.count(needle)==1
extra=r'''
needle_final="exec(compile(text,str(parent),'exec'),globals())"
assert source.count(needle_final)==1
cache_edits=r"""
needle_cache="   run([cmake,'-G','Ninja',"
assert text.count(needle_cache)==1
cache_setup="   object_cache=out/(level+'-objects.cmake');object_cache.write_text('set(MW34_OBJECTS '+json.dumps(';'.join(str(Path(v)).replace(chr(92),'/')for v in p[\"objects\"][level]))+' CACHE STRING \"Exact inherited physical objects\" FORCE)'+chr(10));pin(object_cache)\n"
text=text.replace(needle_cache,cache_setup+needle_cache,1)
old_objects="f'-DMW34_OBJECTS={\";\".join(p[\"objects\"][level])}'"
assert text.count(old_objects)==1
text=text.replace(old_objects,"'-C',str(object_cache)",1)
"""
source=source.replace(needle_final,cache_edits+needle_final,1)
'''
source=source.replace(needle,extra+needle,1)
exec(compile(source,str(parent),'exec'),globals())
