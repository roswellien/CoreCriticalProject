"""Join actual response-file inputs and linker MAP to complete physical bodies."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_version_original_prelaunch_v7.py');scope={'__file__':str(p),'__name__':'materialize_rsp_MAP'}
exec(compile(p.read_text(),str(p),'exec'),scope);t=scope['t']
a="  args=link[0]['argv'];assert '/MACHINE:X86'in args and all(any(str(Path(o['path']).resolve()).casefold()==a.casefold()for a in args)for o in build['objects'])"
b="""  args=link[0]['argv'];assert len(args)==2 and args[1].startswith('@')
  response=pin(args[1][1:]);lines=response.read_text().splitlines();assert lines and all(line.startswith('"')and line.endswith('"')for line in lines)
  expanded=[line[1:-1]for line in lines];assert '/machine:x86'in expanded and '/base:0x18000000'in expanded and '/dynamicbase:no'in expanded
  assert all(any(str(Path(o['path']).resolve()).casefold()==str(Path(a).resolve()).casefold()for a in expanded if a.lower().endswith('.obj'))for o in build['objects'])
  mapping=text(bf/'original-worker.map');actual_map={}
  for line in mapping.splitlines():
   match=re.match(r'\\s+[0-9a-fA-F]{4}:[0-9a-fA-F]{8}\\s+(\\S+)\\s+([0-9a-fA-F]{8})\\s+',line)
   if match:actual_map[match[1]]=int(match[2],16)
  for proof in links:
   if proof['symbol']in names:assert actual_map[proof['symbol']]==proof['address'];counts['actual_linker_MAP_function_joins']+=1
  for c in build['commands']:
   if Path(c['argv'][0]).name.lower()=='cl.exe':assert all(arg in c['argv']for arg in('/O2','/W4','/WX','/MD','/showIncludes'))
"""
assert t.count(a)==1;t=t.replace(a,b)
t=t.replace("pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v6.py');","pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v7.py');pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v6.py');")
exec(compile(t,str(Path(__file__)),'exec'),globals())
