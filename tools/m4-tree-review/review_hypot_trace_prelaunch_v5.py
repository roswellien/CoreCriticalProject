"""Attribute retained optimized functions and the compiler's typed TLS offset."""
from pathlib import Path
import hashlib
import sys

sys.dont_write_bytecode = True
PREVIOUS = Path(__file__).with_name('review_hypot_trace_prelaunch_v4.py')
assert hashlib.sha256(PREVIOUS.read_bytes()).hexdigest() == 'a3551ce9e09a6d4c5c1c9ffb65ab3a1b3124b92bf3badd767a4ca8f078dbd84a'
text = PREVIOUS.read_text()
anchor = "exec(compile(source, str(PREVIOUS), 'exec'), {'__file__': str(Path(__file__).resolve()), '__name__': '__main__'})"
assert text.count(anchor) == 1
changes = '''replacements = [
    ("all(r['type'] in (6, 0x14) for r in relocs)",
     "all(r['type'] in (6,0x14) or (r['type']==11 and r['symbol']['name']=='__Init_thread_epoch' and r['symbol']['section']==0) for r in relocs)"),
    ("symbol_value=r['symbol']['value'],actual_symbol_address=value)",
     "symbol_value=r['symbol']['value'],actual_symbol_address=value,resolution_kind='TLS section-relative offset' if r['type']==11 else 'virtual address')"),
    ("    linked=[linked_function(worker,symbols,sections,n)for n in names]\\n    need(len(linked)==12,'Four tracer functions, seven actual observation helper lambdas, actual broker handler')",
     "    omitted=[n for n in names if n=='?hypot_trace_register@@YAIABU_CONTEXT@@I@Z' or any(n.startswith('??R<lambda_'+str(i)+'>') for i in (1,2,3,6))]\\n    need(len(names)==12 and len(omitted)==5,'Exact compiler-only inline/unreferenced helper definitions')\\n    need(not any(q['symbol']['name'] in omitted for n in names if n not in omitted for s in symbols.values() if s['name']==n and s['section']>0 for q in sections[s['section']]['relocations']),'No retained tracer has a call or relocation to an omitted helper')\\n    linked=[linked_function(worker,symbols,sections,n)for n in names if n not in omitted]\\n    need(len(linked)==7,'Three retained tracer functions, three out-of-line observation lambdas, actual broker handler')\\n    tls=[q for f in linked for q in f['relocations'] if q['type']==11]\\n    need(len(tls)==1 and tls[0]['symbol']=='__Init_thread_epoch','Exactly one compiler-owned TLS section-relative relocation')"),
    ("compiled_functions=len(linked),compiled_function_bytes=",
     "compiled_functions=len(linked),compiler_only_unreferenced_helpers=omitted,compiler_TLS_section_relative_relocations=tls,compiled_function_bytes=")
]
for old,new in replacements:
    assert source.count(old)==1,old
    source=source.replace(old,new)
'''
# Insert the changes before the v4 wrapper executes the v3 wrapper, immediately
# before that wrapper's final execution of the original reviewer source.
inner_anchor = "''' + anchor)"
assert text.count(inner_anchor) == 1
text = text.replace(inner_anchor, changes + inner_anchor)
exec(compile(text, str(PREVIOUS), 'exec'), {'__file__': str(Path(__file__).resolve()), '__name__': '__main__'})
