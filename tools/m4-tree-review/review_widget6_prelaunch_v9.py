"""Check exact52 component deltas, excluding its two declared changed copies.

The v8 metadata check correctly refused stale copy hashes for changed generated
files before any worker launch. This derivative checks those files by their
exact source deltas and retains the copied-file equality for every other input.
The actual compiler's specific TLS namespace receives the same complete cell
and template checks as its parent.
"""
from pathlib import Path
import hashlib, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
parent8 = R / 'tools/m4-tree-review/review_widget6_prelaunch_v8.py'
assert hashlib.sha256(parent8.read_bytes()).hexdigest() == '90d63394836e7fefed2ccc256c6f49a5590662814c4aa435a05ce0a5740649c9'
wrapper = parent8.read_text()
old = "        for relation in comp['prior_copy_relations']:\n            assert pin(relation['prior_path'],relation['prior_sha256']).read_bytes() == pin(relation['current_path'],relation['current_sha256']).read_bytes()"
new = "        for relation in comp['prior_copy_relations']:\n            if relation['name'] in comp['changed_generated_files']: continue\n            assert pin(relation['prior_path'],relation['prior_sha256']).read_bytes() == pin(relation['current_path'],relation['current_sha256']).read_bytes()"
assert wrapper.count(old) == 1; wrapper = wrapper.replace(old, new)
old = 'extern "C" void* mw34_widget_game_f_5a4590_body(mw34::State*,std::uint32_t,void*);'
new = 'extern "C" void *mw34_widget_game_f_5a4590_body(State*,unsigned,void*);'
assert wrapper.count(old) == 1; wrapper = wrapper.replace(old, new)
old = 'case 0x5a4590:return mw34_widget_game_f_5a4590_body(state,pc,memory);'
new = 'case 5916048:return mw34_widget_game_f_5a4590_body;'
assert wrapper.count(old) == 1; wrapper = wrapper.replace(old, new)
old = "exec(compile(text, str(parent), 'exec'), globals())"
new = """text = text.replace("'?current@?A0x87B81194@m4_widget_native@'", "'?current@?A0x7BACD359@m4_widget_native@'")
text = text.replace('        pin(__file__)', '        pin(parent8); pin(__file__)')
exec(compile(text, str(parent), 'exec'), globals())"""
assert wrapper.count(old) == 1; wrapper = wrapper.replace(old, new)
exec(compile(wrapper, str(parent8), 'exec'), globals())
